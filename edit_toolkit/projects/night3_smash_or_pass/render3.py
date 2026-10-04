import sys, os, time, subprocess
import os as _os
KIT = _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'kit'))
WORK = _os.environ.get('WORK', '/home/claude/work_edit')
sys.path.insert(0, KIT)
sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from lib import text_mask, build_plate, hexc, over, smoothstep, ease_out_back, ease_out_cubic, dilate, FONT, FONT_REG
from shots import SHOTS, CUTS, CARS, S0, T_OUT, T_END, SPEED, B
from framing import crop_window

cv2.setNumThreads(1)
W, H, FPS = 1080, 1920, 30
NF = int(round((T_END - S0) * FPS))
SEG = f'{WORK}/seg'
NSHOT = len(SHOTS)
POP = B  # pop transition length = one beat

# ------------------------------------------------------------------ helpers
def rgb_hex(h):
    return hexc(h)

def lighten(c, k):
    return np.clip(c + (1 - c) * k, 0, 1)

def darken(c, k):
    return np.clip(c * (1 - k), 0, 1)

def to_hex(c):
    c = np.clip(np.asarray(c) * 255, 0, 255).astype(int)
    return '#%02x%02x%02x' % tuple(c)

FRAME_LIST = {s[0]: sorted(os.listdir(f'{SEG}/{s[0]}')) for s in SHOTS}
_cache = {}

def load(name, idx):
    lst = FRAME_LIST[name]
    idx = int(np.clip(idx, 0, len(lst) - 1))
    key = (name, idx)
    if key not in _cache:
        if len(_cache) > 6:
            _cache.clear()
        im = cv2.imread(f'{SEG}/{name}/{lst[idx]}')
        _cache[key] = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    return _cache[key]

def shot_frame(i, T, extra_zoom=1.0, shift=(0, 0), rot=0.0):
    nm, car, clip, src, z, cx, cy, box = SHOTS[i]
    t0, t1 = CUTS[i], CUTS[i + 1]
    lt = T - t0
    dur = t1 - t0
    sp = SPEED.get(nm, 1.0)
    im = load(nm, lt * FPS * sp)
    # slow push-in over the shot + punch at the start
    prog = np.clip(lt / dur, 0, 1)
    zz = z * (1 + 0.055 * (prog * prog * (3 - 2 * prog))) * extra_zoom
    X, Y, ww, wh = crop_window(im.shape, zz, cx, cy)
    s = W / ww
    M = cv2.getRotationMatrix2D((X, Y), rot, s)
    M[0, 2] += W / 2 - X + shift[0]
    M[1, 2] += H / 2 - Y + shift[1]
    out = cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return out.astype(np.float32) / 255.0

def dir_blur(img, L, ang):
    """directional motion blur at half resolution"""
    if L < 2:
        return img
    h, w = img.shape[:2]
    sm = cv2.resize(img, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    L2 = max(3, int(L / 2) | 1)
    k = np.zeros((L2, L2), np.float32)
    k[L2 // 2, :] = 1.0
    R = cv2.getRotationMatrix2D((L2 / 2 - 0.5, L2 / 2 - 0.5), ang, 1.0)
    k = cv2.warpAffine(k, R, (L2, L2))
    k /= k.sum() + 1e-6
    b = cv2.filter2D(sm, -1, k, borderType=cv2.BORDER_REFLECT)
    return cv2.resize(b, (w, h), interpolation=cv2.INTER_LINEAR)

def zoom_blur(img, amount, n=6):
    if amount < 0.005:
        return img
    acc = np.zeros_like(img)
    h, w = img.shape[:2]
    sm = cv2.resize(img, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    acc = np.zeros_like(sm)
    for k in range(n):
        s = 1 + amount * k / (n - 1)
        M = cv2.getRotationMatrix2D((w / 4, h / 4), 0, s)
        acc += cv2.warpAffine(sm, M, (w // 2, h // 2), borderMode=cv2.BORDER_REFLECT)
    return cv2.resize(acc / n, (w, h), interpolation=cv2.INTER_LINEAR)

# ------------------------------------------------------------------ grade
_x = np.arange(256) / 255.0
_curve = np.clip(_x, 0, 1)
_curve = 1 / (1 + np.exp(-(_curve - 0.5) * 6.2))
_curve = (_curve - _curve[0]) / (_curve[-1] - _curve[0])
_curve = 0.65 * _curve + 0.35 * _x
_curve = np.clip((_curve - 0.035) / 0.965, 0, 1) ** 1.08
LUT = (_curve * 255).astype(np.uint8)

yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
rr = np.hypot((xx - W / 2) / (W * 0.62), (yy - H / 2) / (H * 0.58))
VIG = (1 - 0.62 * smoothstep(0.45, 1.25, rr))[..., None].astype(np.float32)
EDGE = smoothstep(0.55, 1.15, rr)[..., None].astype(np.float32)
TOPDARK = (0.80 + 0.20 * smoothstep(0.0, 0.36, yy / H))[..., None].astype(np.float32)
del yy, xx, rr
GRAIN = [np.random.default_rng(40 + i).normal(0, 1, (H, W)).astype(np.float16) for i in range(6)]

def grade(f, ca=0.0):
    u8 = (np.clip(f, 0, 1) * 255).astype(np.uint8)
    u8 = cv2.LUT(u8, LUT)
    f = u8.astype(np.float32) / 255.0
    g = f.mean(2, keepdims=True)
    f = np.clip(g + (f - g) * 1.28, 0, 1)
    f = f * TOPDARK
    # lens edge blur
    sm = cv2.resize(f, (W // 6, H // 6), interpolation=cv2.INTER_AREA)
    bl = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 2.2), (W, H), interpolation=cv2.INTER_LINEAR)
    f = f * (1 - EDGE * 0.85) + bl * (EDGE * 0.85)
    # sharpen
    f = f + 0.35 * (f - cv2.GaussianBlur(f, (0, 0), 1.3))
    # chromatic aberration (radial)
    a = 0.0025 + ca
    for ch, sg in ((0, 1), (2, -1)):
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, 1 + sg * a)
        f[..., ch] = cv2.warpAffine(np.ascontiguousarray(f[..., ch]), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    f = f * VIG
    return f

# ------------------------------------------------------------------ sprites (car cutouts with colored outline)
POP_SPRITE = {}
for car, key in ((2, 'pink'), (3, 'bmw'), (4, 'orange'), (5, 'red')):
    img = cv2.cvtColor(cv2.imread(f'{WORK}/cut/{key}_img.png'), cv2.COLOR_BGR2RGB).astype(np.float32) / 255
    m = np.load(f'{WORK}/cut/{key}_mask.npy').astype(np.float32)
    ys, xs = np.where(m > 0.5)
    pad = 70
    y0, y1 = max(0, ys.min() - pad), min(m.shape[0], ys.max() + pad)
    x0, x1 = max(0, xs.min() - pad), min(m.shape[1], xs.max() + pad)
    img = img[y0:y1, x0:x1]; m = m[y0:y1, x0:x1]
    # pad canvas so glow fits
    P = 60
    img = cv2.copyMakeBorder(img, P, P, P, P, cv2.BORDER_CONSTANT, value=0)
    m = cv2.copyMakeBorder(m, P, P, P, P, cv2.BORDER_CONSTANT, value=0)
    acc = rgb_hex(CARS[car][1])
    ring = np.clip(dilate((m > 0.5).astype(np.float32), 9) - m, 0, 1)
    ring = cv2.GaussianBlur(ring, (0, 0), 1.0)
    glow = cv2.GaussianBlur(ring, (0, 0), 14) * 2.2
    # grade the car pixels a bit
    u8 = cv2.LUT((img * 255).astype(np.uint8), LUT).astype(np.float32) / 255
    g = u8.mean(2, keepdims=True); u8 = np.clip(g + (u8 - g) * 1.25, 0, 1)
    rgb = u8 * m[..., None]
    rgb = rgb * (1 - ring[..., None]) + lighten(acc, 0.35)[None, None] * ring[..., None]
    a = np.clip(np.maximum(m, ring), 0, 1)
    POP_SPRITE[car] = (rgb.astype(np.float32), a.astype(np.float32), (acc[None, None] * glow[..., None]).astype(np.float32))

def place_sprite(frame, spr, cx, cy, width, rot=0.0, alpha=1.0, glow_k=1.0):
    rgb, a, gl = spr
    h, w = a.shape
    s = width / w
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, s)
    M[0, 2] += cx - w / 2
    M[1, 2] += cy - h / 2
    r = cv2.warpAffine(rgb, M, (W, H), flags=cv2.INTER_LINEAR)
    aa = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR) * alpha
    gg = cv2.warpAffine(gl, M, (W, H), flags=cv2.INTER_LINEAR) * alpha * glow_k
    frame = frame + gg
    return r * alpha + frame * (1 - aa[..., None])

# ------------------------------------------------------------------ text plates
def plate_scaled(rgb, a, target_w):
    ys, xs = np.where(a > 0.02)
    rgb = rgb[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    a = a[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    s = target_w / a.shape[1]
    nw, nh = int(a.shape[1] * s), int(a.shape[0] * s)
    return cv2.resize(rgb, (nw, nh), interpolation=cv2.INTER_AREA), cv2.resize(a, (nw, nh), interpolation=cv2.INTER_AREA)

m_title = text_mask('SMASH OR PASS?', 150, pad=80)
_tr, _ta, _ = build_plate(m_title, depth=14, stroke=6, seed=7)
TITLE = plate_scaled(_tr, _ta, 930)

NUM = {}
for car, (name, col) in CARS.items():
    c = rgb_hex(col)
    m = text_mask(str(car), 230, pad=60, stretch=(0.95, 1.05))
    r, a, _ = build_plate(m, depth=12, stroke=6, top=to_hex(lighten(c, 0.55)), mid=to_hex(lighten(c, 0.15)),
                          low=to_hex(c), bottom=to_hex(darken(c, 0.45)), ext_near=to_hex(darken(c, 0.62)),
                          ext_far='#060606', seed=car)
    ys, xs = np.where(a > 0.02)
    hh = ys.max() - ys.min()
    s = 170 / hh
    NUM[car] = plate_scaled(r, a, a[ys.min():ys.max() + 1, xs.min():xs.max() + 1].shape[1] * s)

def name_plate(txt, size=50, track=5):
    f = ImageFont.truetype(FONT_REG, size)
    wid = int(sum(f.getlength(ch) for ch in txt) + track * (len(txt) - 1) + 40)
    im = Image.new('L', (wid, size + 40), 0); d = ImageDraw.Draw(im)
    x = 20
    for ch in txt:
        d.text((x, 14), ch, font=f, fill=255); x += f.getlength(ch) + track
    m = np.asarray(im, np.float32) / 255
    return m
NAMES = {car: name_plate(n) for car, (n, c) in CARS.items()}

# watermark
_wm = Image.new('L', (W, 110), 0); _d = ImageDraw.Draw(_wm)
_f = ImageFont.truetype(FONT_REG, 44); _tx = 'MEHRAB.7w7'
_tw = sum(_f.getlength(c) for c in _tx) + 3 * (len(_tx) - 1); _xx = (W - _tw) / 2
for c in _tx:
    _d.text((_xx, 30), c, font=_f, fill=255); _xx += _f.getlength(c) + 3
WM = np.asarray(_wm, np.float32) / 255
WM_SH = cv2.GaussianBlur(WM, (0, 0), 4)
WM_Y = 1688

# outro font flicker
FLICK_FONTS = [FONT, '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
               '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyreheroscn-bold.otf',
               '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrechorus-mediumitalic.otf',
               '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf',
               '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
               '/usr/share/texmf/fonts/opentype/public/lm/lmroman10-bold.otf',
               '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyreadventor-bold.otf']
FLICK = []
for i, fp in enumerate(FLICK_FONTS):
    big = i % 2 == 0
    m = text_mask('MEHRAB.7w7', 200, font=fp, stretch=(1.0, 1.0) if i else (0.9, 1.25), skew=0.0, pad=40)
    ys, xs = np.where(m > 0.02); m = m[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    tw = 960 if big else 760
    s = tw / m.shape[1]
    FLICK.append(cv2.resize(m, (int(m.shape[1] * s), max(1, int(m.shape[0] * s))), interpolation=cv2.INTER_AREA))

def paste_mask(canvas, m, cx, cy, scale=1.0):
    h, w = m.shape
    M = np.float32([[scale, 0, cx - w * scale / 2], [0, scale, cy - h * scale / 2]])
    return np.maximum(canvas, cv2.warpAffine(m, M, (W, H), flags=cv2.INTER_LINEAR))

# ------------------------------------------------------------------ timing helpers
CAR_OF = [s[1] for s in SHOTS]
CAR_START = {}
CAR_END = {}
for i, c in enumerate(CAR_OF):
    CAR_START.setdefault(c, CUTS[i]); CAR_END[c] = CUTS[i + 1]
WHIP_DIRS = [0, 160, 25, 200, 90, 335, 180, 20, 270, 150]

def is_car_change(i):
    return i > 0 and CAR_OF[i] != CAR_OF[i - 1]

def render(fi):
    T = S0 + fi / FPS
    rng = np.random.default_rng(900 + fi)
    if T >= T_OUT:
        return outro(T, fi)
    i = max(k for k in range(NSHOT) if CUTS[k] <= T + 1e-9)
    lt = T - CUTS[i]
    rem = CUTS[i + 1] - T
    # shake / punch at cut
    sh_amp = 16 * np.exp(-lt / 0.09) + 3
    sh = rng.normal(0, 1, 2) * sh_amp * (0.35 if lt > 0.25 else 1.0)
    rot = rng.normal(0, 1) * 0.5 * np.exp(-lt / 0.09)
    punch = 1 + 0.07 * np.exp(-lt / 0.07)
    # mid-shot beat pulse (odd beats)
    mid = CUTS[i] + B
    if T >= mid and CUTS[i + 1] - CUTS[i] < 0.8:
        punch *= 1 + 0.018 * np.exp(-(T - mid) / 0.06)
    f = shot_frame(i, T, extra_zoom=punch, shift=sh, rot=rot)
    ca = 0.006 * np.exp(-lt / 0.07)
    # ---- incoming transition
    if lt < 3.5 / FPS and i > 0:
        k = lt * FPS  # 0..3
        if is_car_change(i):
            f = zoom_blur(f, 0.18 * (1 - k / 3.5))
            acc = rgb_hex(CARS[CAR_OF[i]][1])
            f = f + acc[None, None] * (0.30 * (1 - k / 3.5))
        else:
            ang = WHIP_DIRS[i % len(WHIP_DIRS)]
            L = 110 * (1 - k / 3.5) ** 1.5
            off = 140 * (1 - k / 3.5) ** 2
            d = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))])
            M = np.float32([[1, 0, off * d[0]], [0, 1, off * d[1]]])
            f = cv2.warpAffine(f, M, (W, H), borderMode=cv2.BORDER_REFLECT)
            f = dir_blur(f, L, ang)
    # ---- outgoing whip (same-car cuts)
    nxt = i + 1
    if nxt < NSHOT and not is_car_change(nxt) and rem < 2.5 / FPS:
        k = (2.5 / FPS - rem) * FPS  # 0..2.5
        ang = WHIP_DIRS[nxt % len(WHIP_DIRS)]
        d = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))])
        off = -60 * k
        M = np.float32([[1, 0, off * d[0]], [0, 1, off * d[1]]])
        f = cv2.warpAffine(f, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        f = dir_blur(f, 30 + 40 * k, ang)
        ca += 0.004 * k
    f = grade(f, ca)
    # ---- pop transition to next car (cutout grows out of the shot)
    if nxt < NSHOT and is_car_change(nxt) and rem < POP:
        p = 1 - rem / POP  # 0..1
        car_n = CAR_OF[nxt]
        spr = POP_SPRITE[car_n]
        f = f * (1 - 0.35 * smoothstep(0, 0.3, p))
        e = ease_out_back(min(1, p / 0.85), 1.3)
        wdt = 180 + (700 - 180) * e
        cy = 1500 - (1500 - 980) * ease_out_cubic(min(1, p / 0.7))
        rot_s = -10 * (1 - ease_out_cubic(min(1, p / 0.8)))
        if p > 0.82:
            q = (p - 0.82) / 0.18
            wdt *= 1 + 1.6 * q ** 2
        al = smoothstep(0, 0.12, p)
        f = place_sprite(f, spr, 540, cy, wdt, rot_s, al, glow_k=0.9 + 0.6 * np.sin(p * 12) ** 2)
        if p > 0.82:
            f = zoom_blur(f, 0.25 * ((p - 0.82) / 0.18))
    # ---- texts
    car = CAR_OF[i]
    # hook title
    t_title_end = CUTS[2]
    if T < t_title_end:
        tl = T - S0
        sc = 1 + 0.10 * np.exp(-tl / 0.07)
        if T - CUTS[1] >= 0:
            sc *= 1 + 0.06 * np.exp(-(T - CUTS[1]) / 0.08)
        out_k = smoothstep(t_title_end - 0.12, t_title_end, T)
        sc *= 1 + 0.5 * out_k
        al = 1 - out_k
        r, a = TITLE
        hh, ww = a.shape
        M = np.float32([[sc, 0, 540 - ww * sc / 2 + (rng.normal(0, 6) if out_k > 0 else 0)], [0, sc, 330 - hh * sc / 2]])
        rr_ = cv2.warpAffine(r, M, (W, H)); aa = cv2.warpAffine(a, M, (W, H)) * al
        glow = cv2.GaussianBlur(cv2.resize(aa, (W // 4, H // 4)), (0, 0), 6)
        f = f + hexc('#ff1a10')[None, None] * cv2.resize(glow, (W, H))[..., None] * 0.9
        f = rr_ * al + f * (1 - aa[..., None])
    # car number + name (top-left)
    if T >= max(CAR_START[car], t_title_end if car == 1 else 0):
        t_in = max(CAR_START[car], t_title_end if car == 1 else 0)
        tl = T - t_in
        out_k = smoothstep(CAR_END[car] - POP - 0.02, CAR_END[car] - POP + 0.12, T) if car < 5 else smoothstep(T_OUT - 0.1, T_OUT, T)
        sc = 0.55 + 0.45 * ease_out_back(min(1, tl / 0.2), 2.0)
        al = min(1, tl / 0.06) * (1 - out_k)
        if al > 0.01:
            r, a = NUM[car]
            hh, ww = a.shape
            x0, y0 = 70, 205
            M = np.float32([[sc, 0, x0], [0, sc, y0 + hh * (1 - sc) / 2]])
            rr_ = cv2.warpAffine(r, M, (W, H)); aa = cv2.warpAffine(a, M, (W, H)) * al
            acc = rgb_hex(CARS[car][1])
            gl = cv2.resize(cv2.GaussianBlur(cv2.resize(aa, (W // 4, H // 4)), (0, 0), 5), (W, H))
            f = f + acc[None, None] * gl[..., None] * 0.8
            f = rr_ * al + f * (1 - aa[..., None])
            nm = NAMES[car]
            nh, nw = nm.shape
            nx = x0 + int(ww * sc) + 18
            ny = y0 + int(hh * 0.5) - nh // 2 + 18
            sl = (slice(ny, ny + nh), slice(nx, nx + nw))
            sh_ = cv2.GaussianBlur(nm, (0, 0), 5) * 0.85 * al
            reg = f[sl]
            reg[:] = reg * (1 - sh_[..., None])
            reg[:] = reg * (1 - nm[..., None] * al) + nm[..., None] * al * 0.97
    # watermark
    reg = f[WM_Y:WM_Y + 110]
    reg[:] = reg * (1 - WM_SH[..., None] * 0.55) + hexc('#ff2a1a')[None, None] * 0
    reg[:] = reg * (1 - WM[..., None] * 0.95) + WM[..., None] * 0.95
    # grain
    f = f + (GRAIN[fi % 6].astype(np.float32) * 0.016)[..., None]
    return (np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8)


def outro(T, fi):
    lt = T - T_OUT
    dur = T_END - T_OUT
    rng = np.random.default_rng(77 + fi)
    f = np.zeros((H, W, 3), np.float32)
    nfl = len(FLICK)
    fl_end = 0.50
    if lt < fl_end:
        idx = int(lt * FPS / 2) % nfl
        m = FLICK[idx]
        sc = 1.0 + 0.04 * rng.normal()
        canvas = paste_mask(np.zeros((H, W), np.float32), m, 540 + rng.normal(0, 4), 960, sc)
    else:
        q = (lt - fl_end) / (dur - fl_end)  # 0..1
        m = FLICK[0]
        canvas = paste_mask(np.zeros((H, W), np.float32), m, 540, 960, 1.0 + 0.10 * q)
        # warp: tilt + horizontal smear increasing at the end
        src = np.float32([[0, 0], [W, 0], [W, H], [0, H]])
        tilt = 160 * q ** 1.5
        dst = np.float32([[0 + tilt, 0 + tilt * 0.6], [W - tilt * 0.3, 0 - tilt * 0.3], [W + tilt * 0.2, H], [0 - tilt * 0.4, H]])
        Mp = cv2.getPerspectiveTransform(src, dst)
        canvas = cv2.warpPerspective(canvas, Mp, (W, H))
        canvas = dir_blur(canvas[..., None].repeat(3, 2), 6 + 70 * q ** 2, -12)[..., 0]
    glow = cv2.resize(cv2.GaussianBlur(cv2.resize(canvas, (W // 4, H // 4), interpolation=cv2.INTER_AREA), (0, 0), 7), (W, H))
    glow2 = cv2.resize(cv2.GaussianBlur(cv2.resize(canvas, (W // 8, H // 8), interpolation=cv2.INTER_AREA), (0, 0), 6), (W, H))
    f += np.array([1.0, 0.97, 0.95], np.float32) * (canvas[..., None] * 0.95 + glow[..., None] * 0.75 + glow2[..., None] * 0.45)
    # opening white flash
    fl = np.exp(-lt / 0.05) * 1.1
    f += fl
    # final frames: brighten toward the loop flash
    endk = smoothstep(dur - 0.25, dur, lt)
    f = f * (1 - 0.55 * endk)
    f = f + (GRAIN[fi % 6].astype(np.float32) * 0.02)[..., None]
    return (np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'frames':
        os.makedirs(f'{WORK}/check', exist_ok=True)
        for tok in sys.argv[2:]:
            T = float(tok); fi = int(round((T - S0) * FPS))
            t1 = time.time(); img = render(fi)
            print(f'T={T} fi={fi} {time.time() - t1:.2f}s', file=sys.stderr)
            cv2.imwrite(f'{WORK}/check/T{T:06.3f}.png', cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    elif mode == 'video':
        out = sys.argv[2]
        from multiprocessing import Pool
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                               '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        t1 = time.time()
        with Pool(2) as pool:
            for k, img in enumerate(pool.imap(render, range(NF), chunksize=3)):
                ff.stdin.write(img.tobytes())
                if k % 30 == 0:
                    print(f'frame {k}/{NF} {time.time() - t1:.1f}s', file=sys.stderr, flush=True)
        ff.stdin.close(); ff.wait()
        print('done', time.time() - t1, file=sys.stderr)
