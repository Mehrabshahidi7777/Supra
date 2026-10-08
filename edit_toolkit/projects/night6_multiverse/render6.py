"""Night 6 — BMW Multiverse 🕷️ (Spider-Verse template, reference YouTube Short @miot7 / miot.vfx), see shots6.py.

  home Earth (0 -> 3.51): black M4 in the snow at night, 5 shots, Spider-Verse glitches, comic tags "???..." then
      "BMW Multiverse?"; zoom-through the red headlight into
  the portal (3.51 -> 5.19): red vortex, one small car per Earth (E30 red / E36 purple / M2 blue / M4 dark), each with
      an orange "Earth-XX" tag + car tag, spin transitions, the last two Earths on half beats (acceleration);
  Earth-??? (5.19 -> 5.75): a torn-paper hole opens onto the white world and swallows the frame on the kick;
  Earth-67 (5.75 -> 8.00): high-key white world, blue M4 with a red outline + red/cyan fringes; ink smear -> camera roll;
  CCTV (8.00 -> 10.24): black & white security cam (REC / CAM 03 / timestamp), the grey M4 drifts past, a teal ghost of
      the next car materialises and the frame zooms through it into
  Earth-928 (10.24 -> 12.49): teal comic world (duotone + light halftone + bloom), one cut per beat, "M3" / "G80" flash
      on the last beat (reference: the creator's name);
  outro (12.49 -> 13.80): glowing flickering MEHRAB.7w7 on black (reference: miot.vfx), then the first frame appears
      from the dark brightest-first (taillights first) -> seamless loop.
  House rules: no white flashes, no particles, no top band, MEHRAB.7w7 line at ~3/4 height on the whole video.

  WORK=$WORK python3 render6.py extract [I1 ...]
  WORK=$WORK python3 render6.py frames 0.5 3.8 5.4 6.2 9.9 11.0 13.0
  WORK=$WORK python3 render6.py range out.mp4 3.3 6.0
  WORK=$WORK python3 render6.py video $WORK/n6_noaudio.mp4
"""
import sys, os, time, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.normpath(os.path.join(HERE, '..', '..', 'kit'))
WORK = os.environ.get('WORK', '/home/claude/work_edit')
sys.path.insert(0, KIT)
sys.path.insert(0, HERE)
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from lib import hexc, smoothstep, ease_out_back, ease_out_cubic, FONT_REG
from framing import crop_window
import shots6 as S

cv2.setNumThreads(1)
W, H = 1080, 1920
FPS = int(os.environ.get('N6_FPS', str(S.FPS_OUT)))
NF = int(round(S.T_END * FPS))
SEG = f'{WORK}/seg6'
CUT = f'{WORK}/cut6'
F_TAG = '/usr/share/fonts/truetype/google-fonts/Poppins-BoldItalic.ttf'
F_MONO = '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf'
F_NAME = '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrebonum-bold.otf'
F_FLASH = '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyreheroscn-bold.otf'


def mix(a, b, k):
    return a * (1 - k) + b * k


def ease_in(q):
    q = float(np.clip(q, 0, 1))
    return q * q * q


def ease_out_rev(q):
    q = float(np.clip(q, 0, 1))
    return (1 - q) ** 3


# ================================================================== static fields
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
_rr = np.hypot((xx - W / 2) / (W * 0.62), (yy - H / 2) / (H * 0.58))
VIG = (1 - 0.55 * smoothstep(0.45, 1.25, _rr))[..., None].astype(np.float32)
VIG_CCTV = (1 - 0.75 * smoothstep(0.35, 1.15, _rr))[..., None].astype(np.float32)
SCAN = (1 - 0.07 * ((np.arange(H) % 3) == 0).astype(np.float32))[:, None, None]
# barrel distortion map for the CCTV lens
_nx = (xx - W / 2) / (W / 2); _ny = (yy - H / 2) / (W / 2)
_r2 = _nx * _nx + _ny * _ny
_k = 1 - 0.055 * _r2
BAR_X = (W / 2 + _nx * _k * (W / 2) * 0.965).astype(np.float32)
BAR_Y = (H / 2 + _ny * _k * (W / 2) * 0.965).astype(np.float32)
del _nx, _ny, _r2, _k, _rr
GRAIN = [np.random.default_rng(60 + i).normal(0, 1, (H, W)).astype(np.float16) for i in range(6)]
NOISE_CCTV = [np.random.default_rng(90 + i).normal(0, 1, (H // 2, W // 2)).astype(np.float32) for i in range(8)]


# ================================================================== footage
FRAME_LIST = {}
for _n in S.SHOTS:
    _d = f'{SEG}/{_n}'
    FRAME_LIST[_n] = sorted(os.listdir(_d)) if os.path.isdir(_d) else []
_cache = {}


def load(name, idx):
    lst = FRAME_LIST[name]
    idx = int(np.clip(idx, 0, len(lst) - 1))
    key = (name, idx)
    if key not in _cache:
        if len(_cache) > 12:
            _cache.clear()
        _cache[key] = cv2.cvtColor(cv2.imread(f'{SEG}/{name}/{lst[idx]}'), cv2.COLOR_BGR2RGB)
    return _cache[key]


def shot_frame(name, T, extra_zoom=1.0, shift=(0, 0), rot=0.0, push=0.05, centre=None):
    clip, src, t0, t1, z, cx, cy, sp = S.SHOTS[name]
    im = load(name, (T - t0) * 60 * sp)
    prog = float(np.clip((T - t0) / (t1 - t0), 0, 1))
    zz = z * (1 + push * prog * prog * (3 - 2 * prog)) * extra_zoom
    if centre is not None:
        cx, cy = centre
    X, Y, ww, wh = crop_window(im.shape, zz, cx, cy)
    s = W / ww
    M = cv2.getRotationMatrix2D((X, Y), rot, s)
    M[0, 2] += W / 2 - X + shift[0]
    M[1, 2] += H / 2 - Y + shift[1]
    return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32) / 255.0


# ================================================================== generic fx
def dir_blur(img, L, ang):
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


def zoom_blur(img, amount, n=7, cx=None, cy=None):
    if amount < 0.004:
        return img
    h, w = img.shape[:2]
    cx = w / 2 if cx is None else cx
    cy = h / 2 if cy is None else cy
    sm = cv2.resize(img, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    acc = np.zeros_like(sm)
    for k in range(n):
        M = cv2.getRotationMatrix2D((cx / 2, cy / 2), 0, 1 + amount * k / (n - 1))
        acc += cv2.warpAffine(sm, M, (w // 2, h // 2), borderMode=cv2.BORDER_REFLECT)
    return cv2.resize(acc / n, (w, h), interpolation=cv2.INTER_LINEAR)


def zoom_fx(f, s, cx=W / 2, cy=H / 2, zmax=0.60, blur=0.32):
    if s < 0.002:
        return f
    sc = 1 + zmax * s
    M = np.float32([[sc, 0, cx * (1 - sc)], [0, sc, cy * (1 - sc)]])
    g = cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return zoom_blur(g, blur * s ** 1.3, n=9, cx=cx, cy=cy)


def spin_fx(f, s, sign=1.0, amax=34.0, zmax=0.40, n=9):
    if s < 0.002:
        return f
    ang = sign * amax * s
    sc = 1 + zmax * s
    spread = 18.0 * s
    M = cv2.getRotationMatrix2D((W / 2, H / 2), ang, sc)
    sharp = cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    k = float(np.clip(spread / 5.0, 0, 1))
    if k < 0.02:
        return sharp
    sm = cv2.resize(f, (W // 2, H // 2), interpolation=cv2.INTER_AREA)
    acc = np.zeros_like(sm)
    for j in range(n):
        Mj = cv2.getRotationMatrix2D((W / 4, H / 4), ang - sign * spread * j / (n - 1), sc)
        acc += cv2.warpAffine(sm, Mj, (W // 2, H // 2), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    bl = cv2.resize(acc / n, (W, H), interpolation=cv2.INTER_LINEAR)
    return sharp * (1 - k) + bl * k


def rgb_split(f, amt, vertical=False):
    if amt < 0.5:
        return f
    o = f.copy()
    d = (0, amt) if vertical else (amt, 0)
    M1 = np.float32([[1, 0, d[0]], [0, 1, d[1]]]); M2 = np.float32([[1, 0, -d[0]], [0, 1, -d[1]]])
    o[..., 0] = cv2.warpAffine(np.ascontiguousarray(f[..., 0]), M1, (W, H), borderMode=cv2.BORDER_REFLECT)
    o[..., 2] = cv2.warpAffine(np.ascontiguousarray(f[..., 2]), M2, (W, H), borderMode=cv2.BORDER_REFLECT)
    return o


def punch(T, times, k=0.07, tau=0.07):
    z = 1.0
    for t in times:
        if 0 <= T - t < 6 * tau:
            z *= 1 + k * np.exp(-(T - t) / tau)
    return z


def since(T, times):
    d = [T - t for t in times if T >= t]
    return min(d) if d else 99.0


def glitch(f, rng, amt, n=12, y0=0, y1=H, maxshift=110, pix=True):
    """Spider-Verse style glitch: misaligned bands with red / cyan channel splits and blocky pixel chunks"""
    if amt < 0.03:
        return f
    o = f.copy()
    for _ in range(int(n * amt) + 1):
        h = int(rng.integers(8, 70))
        y = int(rng.integers(y0, max(y0 + 1, y1 - h)))
        x0 = int(rng.integers(0, W - 160)); x1 = min(W, x0 + int(rng.integers(160, W)))
        d = int(rng.normal(0, maxshift * amt))
        band = np.roll(f[y:y + h], d, axis=1)[:, x0:x1].copy()
        s = int(3 + 14 * amt * rng.random())
        band[..., 0] = np.roll(band[..., 0], s, axis=1)
        band[..., 2] = np.roll(band[..., 2], -s, axis=1)
        r = rng.random()
        if pix and r < 0.35:                                   # blocky pixels
            q = int(rng.integers(8, 22))
            hb, wb = band.shape[:2]
            band = cv2.resize(cv2.resize(band, (max(1, wb // q), max(1, hb // q)), interpolation=cv2.INTER_AREA),
                              (wb, hb), interpolation=cv2.INTER_NEAREST)
        if r < 0.22:
            band = band * np.array([1.30, 0.50, 0.58], np.float32)
        elif r < 0.44:
            band = band * np.array([0.45, 1.05, 1.25], np.float32)
        o[y:y + h, x0:x1] = band
    return o


def soft_clip(f):
    return np.where(f < 0.82, f, 0.82 + 0.18 * np.tanh((f - 0.82) / 0.18))


def bloom(f, thr=0.62, k=0.55, sig=18):
    hi = np.clip(f - thr, 0, None)
    sm = cv2.resize(hi, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    b = cv2.resize(cv2.GaussianBlur(sm, (0, 0), sig / 4), (W, H), interpolation=cv2.INTER_LINEAR)
    return f + b * k


# ================================================================== grades
_x = np.arange(256) / 255.0
_c = 1 / (1 + np.exp(-(_x - 0.5) * 6.0)); _c = (_c - _c[0]) / (_c[-1] - _c[0])
LUT_S = (np.clip(0.6 * _c + 0.4 * _x, 0, 1) * 255).astype(np.uint8)


def lut(f, L):
    return cv2.LUT((np.clip(f, 0, 1) * 255).astype(np.uint8), L).astype(np.float32) / 255.0


def grade_night(f):
    """home Earth: cold snowy night, everything desaturated except the red lights (reference intro: grey city, red)"""
    f = lut(f, LUT_S)
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    lum = (0.30 * r + 0.58 * g + 0.12 * b)[..., None]
    red = np.clip((r - np.maximum(g, b) * 1.15) * 4.0, 0, 1)[..., None]
    f = lum + (f - lum) * (0.22 + 1.15 * red)
    f = f * np.array([0.95, 0.99, 1.07], np.float32)
    f = 0.025 + 0.975 * f
    f = f + 0.30 * (f - cv2.GaussianBlur(f, (0, 0), 1.3))
    f = bloom(f, 0.55, 0.45, 22)
    return f * VIG


def blue_mask(f):
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    return np.clip((b - np.maximum(r, g * 0.95)) * 6.0, 0, 1)


def grade_white(f, ca=6.0):
    """Earth-67: high-key white world, the blue M4 stays deep blue, red outline + red/cyan fringes (reference)"""
    bm = cv2.GaussianBlur(blue_mask(f), (0, 0), 2.0)
    car = np.clip(bm * 1.4, 0, 1)
    sm = cv2.resize(car, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    car = cv2.resize(cv2.dilate(sm, np.ones((5, 5), np.uint8)), (W, H), interpolation=cv2.INTER_LINEAR)
    car = cv2.GaussianBlur(car, (0, 0), 3.0)
    lum = (0.30 * f[..., 0] + 0.59 * f[..., 1] + 0.11 * f[..., 2])[..., None]
    hk = 1 - (1 - np.clip(lum * 1.12, 0, 1)) ** 2.6                 # background -> white
    bg = np.clip(hk * 0.96 + 0.06, 0, 1) * np.array([0.985, 0.985, 1.0], np.float32)
    bg = bg + (f - lum) * 0.12
    carc = lut(f, LUT_S)
    cl = carc.mean(2, keepdims=True)
    carc = np.clip(cl + (carc - cl) * 1.35, 0, 1) * 0.92
    out = mix(bg, carc, car[..., None])
    # red outline around the car silhouette + comic ink edges
    edge = np.clip(cv2.dilate(car, np.ones((9, 9), np.uint8)) - car, 0, 1)
    glow = cv2.GaussianBlur(edge, (0, 0), 6.0)
    out = out * (1 - 0.35 * edge[..., None]) + hexc('#ff1f2e')[None, None] * (glow[..., None] * 1.25 + edge[..., None] * 0.55)
    gx = cv2.Sobel(cl[..., 0], cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(cl[..., 0], cv2.CV_32F, 0, 1, ksize=3)
    ink = np.clip(np.hypot(gx, gy) * 1.6 - 0.25, 0, 1) * car
    out = out * (1 - 0.55 * ink[..., None])
    out = rgb_split(out, ca)
    return out


DUO_T = np.array([0.0, 0.28, 0.55, 0.80, 1.0], np.float32)
DUO_C = np.stack([hexc('#00161a'), hexc('#015a62'), hexc('#12bdb5'), hexc('#bffff7'), hexc('#ffffff')])
_l = np.linspace(0, 1, 256)
LUT_DUO = np.stack([np.interp(_l, DUO_T, DUO_C[:, c]) for c in range(3)], 1).astype(np.float32)
# halftone dot screen (45 deg, 11 px pitch) for the comic print look in the teal world (light, shadows only)
_u = (xx + yy) / np.sqrt(2) / 11.0; _v = (xx - yy) / np.sqrt(2) / 11.0
HT_D = np.hypot(_u - np.round(_u), _v - np.round(_v)).astype(np.float32)        # 0 centre .. 0.707
del _u, _v


def grade_teal(f):
    """Earth-928: teal comic duotone, bloom, cyan edges, light halftone in the shadows"""
    lum = 0.30 * f[..., 0] + 0.59 * f[..., 1] + 0.11 * f[..., 2]
    lum = np.clip((lum - 0.04) * 1.15, 0, 1)
    duo = LUT_DUO[(lum * 255).astype(np.uint8)]
    teal = np.clip((f[..., 1] + f[..., 2]) * 0.5 - f[..., 0], 0, 1)[..., None] * 2.5
    out = mix(duo, np.clip(f * np.array([0.75, 1.05, 1.08], np.float32), 0, 1), np.clip(teal, 0, 0.55))
    dark = 1 - smoothstep(0.15, 0.55, lum)
    dot = (HT_D < 0.18 + 0.30 * dark).astype(np.float32)
    out = out * (1 - 0.22 * dark[..., None] * (1 - dot[..., None]))
    gx = cv2.Sobel(lum, cv2.CV_32F, 1, 0, ksize=3); gy = cv2.Sobel(lum, cv2.CV_32F, 0, 1, ksize=3)
    e = np.clip(np.hypot(gx, gy) * 1.3 - 0.35, 0, 1)
    out = out + hexc('#5ffff0')[None, None] * cv2.GaussianBlur(e, (0, 0), 1.5)[..., None] * 0.35
    out = bloom(out, 0.60, 0.65, 26)
    return out * VIG


def grade_cctv(f, T, fi):
    """black & white security camera: crushed contrast, noise, scanlines, barrel lens, vignette, rolling bar"""
    lum = 0.30 * f[..., 0] + 0.59 * f[..., 1] + 0.11 * f[..., 2]
    lum = np.clip((lum - 0.02) * 1.55, 0, 1) ** 0.92
    nz = cv2.resize(NOISE_CCTV[fi % 8], (W, H), interpolation=cv2.INTER_LINEAR)
    lum = lum + nz * 0.045
    bar = ((T * 260) % (H + 400)) - 200
    lum = lum + 0.05 * np.exp(-((np.arange(H, dtype=np.float32) - bar) / 90.0) ** 2)[:, None]
    out = np.repeat(lum[..., None], 3, 2) * np.array([0.96, 1.0, 0.98], np.float32)
    out = cv2.remap(out, BAR_X, BAR_Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    out = cv2.GaussianBlur(out, (0, 0), 0.7)
    return out * SCAN * VIG_CCTV


# ================================================================== comic tags
def _tag(parts, size, pad=(28, 14), skew=-0.10, rot=-2.0, box=('#d98634', '#9a4f19'), edge='#2b1405', shadow=True):
    """orange Spider-Verse caption box. parts = [(text, colour)] -> (rgb premultiplied, alpha)"""
    s2 = 2
    f = ImageFont.truetype(F_TAG, size * s2)
    widths = [f.getlength(t) for t, _ in parts]
    asc, desc = f.getmetrics()
    tw, th = int(sum(widths)), asc + desc
    px, py = pad[0] * s2, pad[1] * s2
    bw, bh = tw + 2 * px, int(th * 0.92) + 2 * py
    M = 40 * s2
    can = Image.new('RGBA', (bw + 2 * M, bh + 2 * M), (0, 0, 0, 0))
    d = ImageDraw.Draw(can)
    if shadow:
        d.rounded_rectangle((M + 8 * s2, M + 10 * s2, M + bw + 8 * s2, M + bh + 10 * s2), radius=10 * s2, fill=(0, 0, 0, 120))
    d.rounded_rectangle((M, M, M + bw, M + bh), radius=10 * s2, fill=(*[int(c * 255) for c in hexc(edge)], 255))
    grad = Image.new('RGBA', (bw - 8 * s2, bh - 8 * s2))
    c0, c1 = hexc(box[0]), hexc(box[1])
    ga = np.linspace(0, 1, bh - 8 * s2)[:, None, None]
    garr = (c0 * (1 - ga) + c1 * ga) * 255
    garr = np.broadcast_to(garr, (bh - 8 * s2, bw - 8 * s2, 3))
    grad = Image.fromarray(np.dstack([garr, np.full(garr.shape[:2], 255)]).astype(np.uint8), 'RGBA')
    gm = Image.new('L', grad.size, 0); ImageDraw.Draw(gm).rounded_rectangle((0, 0, grad.size[0] - 1, grad.size[1] - 1), radius=7 * s2, fill=255)
    can.paste(grad, (M + 4 * s2, M + 4 * s2), gm)
    d.line((M + 14 * s2, M + 8 * s2, M + bw - 14 * s2, M + 8 * s2), fill=(255, 214, 160, 150), width=2 * s2)
    x = M + px
    ty = M + py - int(desc * 0.25)
    for (t, col), wdt in zip(parts, widths):
        cc = tuple(int(c * 255) for c in hexc(col))
        d.text((x + 3 * s2, ty + 3 * s2), t, font=f, fill=(20, 8, 2, 200))                  # drop
        d.text((x, ty), t, font=f, fill=cc + (255,), stroke_width=2 * s2, stroke_fill=(*[int(c * 255) for c in hexc(edge)], 255))
        x += wdt
    arr = np.asarray(can).astype(np.float32) / 255
    arr = cv2.resize(arr, (arr.shape[1] // s2, arr.shape[0] // s2), interpolation=cv2.INTER_AREA)
    h, w = arr.shape[:2]
    Mk = np.float32([[1, skew, -skew * h / 2], [0, 1, 0]])
    Rm = cv2.getRotationMatrix2D((w / 2, h / 2), rot, 1.0)
    A = np.vstack([Rm, [0, 0, 1]]) @ np.vstack([Mk, [0, 0, 1]])
    arr = cv2.warpAffine(arr, A[:2].astype(np.float32), (w, h), flags=cv2.INTER_LINEAR)
    a = arr[..., 3]
    return arr[..., :3] * a[..., None], a


RED_T, BLUE_T, DARK_T = '#ff3b2f', '#3ab8ff', '#2b1405'
TAGS = {}


def tag(key):
    if key not in TAGS:
        if key == 'q':
            TAGS[key] = _tag([('???...', DARK_T)], 74, pad=(34, 12), rot=3.0)
        elif key == 'mv':
            TAGS[key] = _tag([('BMW ', DARK_T), ('Multiverse?', DARK_T)], 64, rot=-3.0)
        elif key.startswith('E:'):
            TAGS[key] = _tag([('Earth-', RED_T), (key[2:], BLUE_T)], 62, rot=-2.0)
        elif key.startswith('C:'):
            TAGS[key] = _tag([(key[2:], DARK_T)], 40, pad=(24, 9), rot=1.5, box=('#e09a44', '#a85d20'))
    return TAGS[key]


def put(f, rgb, a, x, y, scale=1.0, alpha=1.0, anchor='lt'):
    h, w = a.shape
    if anchor == 'c':
        x, y = x - w * scale / 2, y - h * scale / 2
    elif anchor == 'rt':
        x = x - w * scale
    M = np.float32([[scale, 0, x], [0, scale, y]])
    rr = cv2.warpAffine(rgb, M, (W, H), flags=cv2.INTER_LINEAR)
    aa = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR) * alpha
    return rr * alpha + f * (1 - aa[..., None])


def tag_anim(f, key, T, t_in, t_out, x, y, rng, anchor='lt', float_amp=4.0):
    """pop in (scale + glitch jitter), slight float; returns f"""
    if not (t_in <= T < t_out):
        return f
    q = T - t_in
    e = ease_out_back(min(1.0, q / 0.13), 2.0)
    sc = 0.55 + 0.45 * e
    jx = rng.normal(0, 14) if q < 0.07 else 0.0
    rgb, a = tag(key)
    yy_ = y + float_amp * np.sin(2 * np.pi * (T - t_in) / 1.1)
    hh, ww = a.shape
    if anchor == 'lt':           # scale about the tag centre
        cx, cy = x + ww / 2, yy_ + hh / 2
    else:
        cx, cy = x - ww / 2, yy_ + hh / 2
    g = put(f, rgb, a, cx + jx, cy, sc, min(1.0, q / 0.03), anchor='c')
    if q < 0.09:                 # chromatic jitter on entry
        g = rgb_split(g, 6 * (1 - q / 0.09))
    return g


TAG_X, TAG_Y, CTAG_Y = 56, 276, 386      # Earth tag top-left, car tag right under it (clear of the app overlays)


# ================================================================== sprites (portal cars, ghost)
def blank_plate(img, box, thr=150, delta=40):
    """licence / dealer plate -> blank plate (letters replaced by the plate's own shading). Only low-saturation blobs
    count as plate, so red taillights next to a dim night plate are never touched."""
    x0, y0, x1, y1 = box
    reg = img[y0:y1, x0:x1]
    g = cv2.cvtColor(reg, cv2.COLOR_BGR2GRAY).astype(np.float32)
    sat = cv2.cvtColor(reg, cv2.COLOR_BGR2HSV)[..., 1]
    bright = cv2.morphologyEx(((g > thr) & (sat < 110)).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((11, 23), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(bright)
    if n < 2:
        return False
    k = 1 + int(np.argmax(st[1:, 4]))
    kx, ky, kw, kh = st[k, :4]
    keep = np.zeros(g.shape, np.uint8)            # the plate may break into pieces at the letters: merge nearby ones
    for j in range(1, n):
        x, y, w_, h_, ar = st[j]
        if j == k or (ar > 0.04 * st[k, 4] and x < kx + kw + 25 and x + w_ > kx - 25 and y < ky + kh + 12 and y + h_ > ky - 12):
            keep[lab == j] = 1
    cnts, _ = cv2.findContours(keep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    hull = cv2.convexHull(np.vstack(cnts))
    hm = np.zeros(g.shape, np.uint8); cv2.fillConvexPoly(hm, hull, 1)
    hm = cv2.erode(hm, np.ones((5, 5), np.uint8))
    inside = hm > 0
    vals = g[inside & (g > thr)]
    if len(vals) < 20:
        return False
    text = cv2.dilate((inside & (g < np.median(vals) - delta)).astype(np.uint8), np.ones((3, 3), np.uint8)) > 0
    w = (inside & ~text).astype(np.float32)
    sig = max(3.0, 0.30 * st[k, 3])
    fl = reg.astype(np.float32)
    num = cv2.GaussianBlur(fl * w[..., None], (0, 0), sig)
    den = cv2.GaussianBlur(w, (0, 0), sig)[..., None]
    a = cv2.GaussianBlur(hm.astype(np.float32), (0, 0), 0.8)[..., None]
    reg[:] = np.clip(fl * (1 - a) + (num / np.maximum(den, 1e-3)) * a, 0, 255).astype(np.uint8)
    return True


SPR = {}


def sprite(key):
    if key in SPR:
        return SPR[key]
    img = cv2.imread(f'{CUT}/{key}_img.png')
    for box in S.SPRITE_PLATES.get(key, []):
        blank_plate(img, box)
    for (x0, y0, x1, y1) in S.SPRITE_PAINT.get(key, []):
        m = np.zeros(img.shape[:2], np.uint8); m[y0:y1, x0:x1] = 255
        img = cv2.inpaint(img, m, 5, cv2.INPAINT_TELEA)
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    m = np.load(f'{CUT}/{key}_mask.npy').astype(np.float32)
    ys, xs = np.where(m > 0.5)
    pad = 50
    y0, y1 = max(0, ys.min() - pad), min(m.shape[0], ys.max() + pad)
    x0, x1 = max(0, xs.min() - pad), min(m.shape[1], xs.max() + pad)
    img = img[y0:y1, x0:x1].astype(np.float32) / 255; m = m[y0:y1, x0:x1]
    if key == 'm4d':                                  # matte black car on a dark vortex: lift it so it reads
        img = np.clip(img * 1.9 + 0.035, 0, 1) ** 0.85
    img = lut(img, LUT_S)
    g = img.mean(2, keepdims=True); img = np.clip(g + (img - g) * 1.25, 0, 1)
    halo = cv2.GaussianBlur(cv2.dilate((m > 0.4).astype(np.float32), np.ones((13, 13), np.uint8)), (0, 0), 9)
    rim = np.clip(cv2.dilate((m > 0.5).astype(np.float32), np.ones((5, 5), np.uint8)) - (m > 0.5), 0, 1)
    SPR[key] = (img * m[..., None], m, halo, cv2.GaussianBlur(rim, (0, 0), 1.0))
    return SPR[key]


def place_car(f, key, cx, cy, width, rot=0.0, alpha=1.0, outline='#ff3a2e', glow_k=1.0, blur=0.0, tint=None):
    rgb, a, halo, rim = sprite(key)
    h, w = a.shape
    s = width / w
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, s)
    M[0, 2] += cx - w / 2
    M[1, 2] += cy - h / 2
    rr = cv2.warpAffine(rgb, M, (W, H), flags=cv2.INTER_LINEAR)
    aa = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR) * alpha
    hh = cv2.warpAffine(halo, M, (W, H), flags=cv2.INTER_LINEAR) * alpha
    ri = cv2.warpAffine(rim, M, (W, H), flags=cv2.INTER_LINEAR) * alpha
    if blur > 1.5:
        rr = zoom_blur(rr, blur / 600, cx=cx, cy=cy)
        aa = zoom_blur(aa[..., None].repeat(3, 2), blur / 600, cx=cx, cy=cy)[..., 0]
    col = hexc(outline)
    f = f * (1 - 0.55 * hh[..., None]) + col[None, None] * (hh[..., None] * 0.95 * glow_k)
    if tint is not None:
        rr = tint
    out = rr * alpha + f * (1 - aa[..., None])
    return out + col[None, None] * ri[..., None] * 1.6 * glow_k


# ================================================================== portal (red vortex)
def _periodic_noise(n, seed, cutoff):
    rng = np.random.default_rng(seed)
    z = rng.normal(0, 1, (n, n)) + 1j * rng.normal(0, 1, (n, n))
    fy = np.fft.fftfreq(n)[:, None]; fx = np.fft.fftfreq(n)[None, :]
    filt = np.exp(-(fx ** 2 + fy ** 2) / (2 * cutoff ** 2))
    a = np.real(np.fft.ifft2(z * filt)).astype(np.float32)
    return (a - a.min()) / (a.max() - a.min())


VTX = 0.6 * _periodic_noise(256, 7, 0.035) + 0.4 * _periodic_noise(256, 8, 0.11)
PW, PH = W // 2, H // 2
_py, _px = np.mgrid[0:PH, 0:PW].astype(np.float32)
PCX, PCY = PW / 2, PH * 0.47
_dx, _dy = _px - PCX, _py - PCY
P_R = np.hypot(_dx, _dy) + 1.0
P_TH = np.arctan2(_dy, _dx)
P_LR = np.log(P_R)
del _px, _py, _dx, _dy
VC_T = np.array([0.0, 0.35, 0.58, 0.80, 0.93, 1.0], np.float32)
VC_C = np.stack([hexc('#000000'), hexc('#2a0004'), hexc('#8c0010'), hexc('#ff2a22'), hexc('#ff9a6a'), hexc('#ffe1cc')])
_lv = np.linspace(0, 1, 256)
LUT_VTX = np.stack([np.interp(_lv, VC_T, VC_C[:, c]) for c in range(3)], 1).astype(np.float32)


def vortex(T, spin=0.0, tint=None):
    """procedural red swirl tunnel: streaks along log-spirals flowing outward, rotating (all smooth, no particles)"""
    ang = P_TH + 0.85 * P_LR + 1.1 * T + spin
    u = (ang / (2 * np.pi)) * 256 * 3
    v = P_LR * 120 - T * 160
    s1 = cv2.remap(VTX, (u % 256).astype(np.float32), (v % 256).astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_WRAP)
    s2 = cv2.remap(VTX, ((u * 0.5 + 64) % 256).astype(np.float32), ((v * 0.6 + 30) % 256).astype(np.float32), cv2.INTER_LINEAR,
                   borderMode=cv2.BORDER_WRAP)
    s = np.clip((s1 * 0.65 + s2 * 0.35 - 0.38) * 2.2, 0, 1) ** 1.6
    rr = P_R / (PW * 0.5)
    ring = np.exp(-((rr - 0.95 - 0.06 * np.sin(T * 3)) / 0.28) ** 2) * 0.55 + smoothstep(0.25, 1.4, rr) * 0.35
    core = np.exp(-(rr / 0.55) ** 2)
    val = np.clip(s * (0.35 + ring) + core * 0.22 + 0.04, 0, 1)
    rgb = LUT_VTX[(val * 255).astype(np.uint8)]
    if tint is not None:
        rgb = rgb * tint
    return cv2.resize(rgb, (W, H), interpolation=cv2.INTER_LINEAR)


def portal_frame(T, fi):
    rng = np.random.default_rng(500 + fi)
    i = max(j for j in range(len(S.PORTAL)) if S.PORTAL[j][1] <= T + 1e-9) if T < S.T_HOLE else len(S.PORTAL) - 1
    key, t0, t1, earth, name, col = S.PORTAL[i]
    q = T - t0
    f = vortex(T, spin=1.6 * since(T, [p[1] for p in S.PORTAL]) ** 0.5 * 0)
    dur = t1 - t0
    e = ease_out_cubic(min(1.0, q / 0.16))
    wd = (700 if key != 'm4d' else 760) * (0.55 + 0.45 * e) * (1 + 0.04 * q / max(dur, 0.2))
    rot = -22 * (1 - e) + 4 * np.sin(2 * np.pi * q / 1.4) * (1 if i % 2 else -1)
    bob = 10 * np.sin(2 * np.pi * (T - t0) / 0.9)
    f = place_car(f, key, 540, 880 + bob, wd, rot=rot, outline=col, blur=260 * (1 - e) ** 2)
    f = tag_anim(f, 'E:' + earth, T, t0, t1 if i < len(S.PORTAL) - 1 else S.T_WHITE, TAG_X, TAG_Y, rng)
    f = tag_anim(f, 'C:' + name, T, t0 + 0.04, t1, TAG_X + 6, CTAG_Y, rng)
    # spin transition between Earths (peaks on the cut), not into the hole
    if i + 1 < len(S.PORTAL) and T > t1 - 0.12:
        f = spin_fx(f, ease_in((T - (t1 - 0.12)) / 0.12) * 0.8, sign=1.0)
    if i > 0 and q < 0.16:
        f = spin_fx(f, ease_out_rev(q / 0.16) * 0.8, sign=-1.0)
    f = rgb_split(f, 9 * np.exp(-q / 0.08))
    if q < 0.10:
        f = glitch(f, rng, 0.6 * (1 - q / 0.10), n=10)
    return f, rng.normal(0, 1, 2) * 10 * np.exp(-q / 0.07)


# ================================================================== torn hole (Earth-???)
_th = np.linspace(0, 2 * np.pi, 720, endpoint=False)
_r = np.random.default_rng(13)
HOLE_R = 1 + sum(_r.uniform(0.02, 0.09) / (k ** 0.6) * np.sin(k * _th + _r.uniform(0, 6.28)) for k in range(2, 26))
HOLE_R2 = HOLE_R * (1 + 0.035 + 0.025 * np.sin(37 * _th + 1.3) + 0.02 * _r.normal(0, 1, len(_th)))     # paper rim


def hole_radius(T):
    q = T - S.T_HOLE
    a = 300 * ease_out_back(min(1.0, q / 0.20), 1.4)
    b = 30 * smoothstep(0.20, 0.47, q)
    c = 1700 * ease_in(np.clip((q - 0.40) / (S.T_WHITE - S.T_HOLE - 0.40), 0, 1)) if q > 0.40 else 0.0
    return a + b + c


def hole_masks(T, cx=540, cy=900):
    R = hole_radius(T)
    rot = 0.25 * (T - S.T_HOLE)
    pts = np.stack([cx + R * HOLE_R * np.cos(_th + rot) * 0.92, cy + R * HOLE_R * np.sin(_th + rot) * 1.08], 1)
    pts2 = np.stack([cx + R * HOLE_R2 * np.cos(_th + rot) * 0.92, cy + R * HOLE_R2 * np.sin(_th + rot) * 1.08], 1)
    m = np.zeros((H, W), np.uint8); m2 = np.zeros((H, W), np.uint8)
    cv2.fillPoly(m2, [np.round(pts2 * 4).astype(np.int32)], 255, cv2.LINE_AA, shift=2)
    cv2.fillPoly(m, [np.round(pts * 4).astype(np.int32)], 255, cv2.LINE_AA, shift=2)
    return m.astype(np.float32) / 255, m2.astype(np.float32) / 255


PAPER = None


def hole_frame(T, fi):
    global PAPER
    rng = np.random.default_rng(700 + fi)
    if PAPER is None:
        PAPER = (0.90 + 0.08 * cv2.GaussianBlur(np.random.default_rng(4).random((H, W)).astype(np.float32), (0, 0), 1.2))[..., None] \
            * np.array([1.0, 0.985, 0.95], np.float32)
    f = vortex(T)
    key, t0, t1, earth, name, col = S.PORTAL[-1]
    q0 = T - S.T_HOLE
    if q0 < 0.10:                                         # the last car is pulled into the hole
        e = q0 / 0.10
        f = place_car(f, key, 540, 880, 600 * (1 - 0.8 * e), rot=40 * e, alpha=1 - e, outline=col, blur=200 * e)
    inner = white_frame(T, fi, in_hole=True)
    m, m2 = hole_masks(T)
    sh = cv2.GaussianBlur(m2, (0, 0), 16)
    f = f * (1 - 0.65 * sh[..., None])
    rim = np.clip(m2 - m, 0, 1)
    f = f * (1 - rim[..., None]) + PAPER * rim[..., None]
    curl = cv2.GaussianBlur(rim, (0, 0), 3.0) * (1 - m2)
    f = f * (1 - 0.3 * curl[..., None])
    f = f * (1 - m[..., None]) + inner * m[..., None]
    f = tag_anim(f, 'E:???', T, S.T_HOLE, S.T_WHITE, TAG_X, TAG_Y, rng)
    if q0 < 0.08:
        f = glitch(f, rng, 0.5, n=8)
    return f, rng.normal(0, 1, 2) * 8 * np.exp(-q0 / 0.08)


# ================================================================== white world (Earth-67)
KICKS = [S.beat(k) for k in np.arange(10, 14, 0.5)]


def white_frame(T, fi, in_hole=False):
    if T < S.T_W2 or in_hole:
        z = punch(T, KICKS, 0.05, 0.08) if not in_hole else 1.0
        f = shot_frame('W1', T, extra_zoom=z, push=0.10)
    else:
        f = shot_frame('W2', T, extra_zoom=punch(T, KICKS, 0.05, 0.08), push=0.04)
    q = T - S.T_WHITE
    ca = 6 + 10 * np.exp(-max(0.0, q) / 0.10) + 6 * np.exp(-since(T, KICKS) / 0.06)
    return grade_white(f, ca)


# ink smear (reference 6.61-7.14): three thick curved brush strokes of black ink sweep diagonally across the white
# world (tapered tips, bristle striations, dry-brush gaps at the edges, ragged wet edges); cut W1 -> W2 on beat 12
# while the ink covers most of the frame, then the strokes are pulled out from their tails.
W2_, H2_ = W // 2, H // 2
_y2, _x2 = np.mgrid[0:H2_, 0:W2_].astype(np.float32)
_ri = np.random.default_rng(31)
BRUSH = []
for k, (ang, v0, wd, A, lam, dl) in enumerate([(-22, -250, 250, 55, 330, 0.00), (-31, 30, 300, 70, 420, 0.04),
                                               (-25, 300, 240, 45, 360, 0.075)]):
    a = np.radians(ang)
    U = (_x2 - W2_ / 2) * np.cos(a) + (_y2 - H2_ / 2) * np.sin(a)
    V = -(_x2 - W2_ / 2) * np.sin(a) + (_y2 - H2_ / 2) * np.cos(a)
    ph = _ri.uniform(0, 6.28)
    Vc = V - (v0 + A * np.sin(U / lam + ph))
    en = np.interp(np.arange(-1400, 1401), np.arange(-1400, 1401, 18), _ri.normal(0, 1, len(range(-1400, 1401, 18))))
    st = cv2.GaussianBlur(_ri.random((1, 260)).astype(np.float32), (0, 0), 0.9)[0]
    bri = np.interp(np.arange(0, 601), np.arange(0, 601, 7), _ri.random(len(range(0, 601, 7))))
    BRUSH.append(dict(U=U.astype(np.float32), Vc=Vc.astype(np.float32), wd=wd, dl=dl, en=en.astype(np.float32),
                      st=st, bri=bri.astype(np.float32), u0=float(U.min()) - 40, u1=float(U.max()) + 40))
del _y2, _x2


def ink_mask(T):
    m = np.zeros((H2_, W2_), np.float32)
    tex = np.zeros((H2_, W2_), np.float32)
    for b in BRUSH:
        p_in = np.clip((T - S.T_INK0 - b['dl']) / 0.17, 0, 1)
        p_out = np.clip((T - (S.T_W2 + 0.03) - b['dl']) / 0.19, 0, 1)
        if p_in <= 0 or p_out >= 1:
            continue
        head = b['u0'] + (b['u1'] - b['u0']) * (1 - (1 - p_in) ** 2.2)
        tail = b['u0'] + (b['u1'] - b['u0']) * p_out ** 1.8
        U, Vc = b['U'], b['Vc']
        s = np.clip((U - tail) / max(head - tail, 1.0), 0, 1)
        half = b['wd'] / 2 * (0.30 + 0.70 * np.sin(np.pi * s) ** 0.45)          # tapered tips
        ui = np.clip(U + 1400, 0, 2800).astype(np.int32)
        dv = np.abs(Vc) + b['en'][ui] * 3.5
        body = smoothstep(half + 2.0, half - 2.0, dv)
        vr = np.clip(Vc / np.maximum(half, 1) * 0.5 + 0.5, 0, 1)                 # 0..1 across the stroke
        stri = b['st'][(vr * 259).astype(np.int32)]
        edge = smoothstep(0.62, 0.95, np.abs(vr - 0.5) * 2)
        body = body * (1 - edge * (stri < 0.5))                                    # dry-brush gaps at the edges
        br = b['bri'][(vr * 600).astype(np.int32)] * 26
        along = smoothstep(head + 4 - br, head - 10 - br, U) * smoothstep(tail - 6 + br, tail + 8 + br, U)
        mk = body * along
        tex = np.where(mk > m, stri, tex)
        m = np.maximum(m, mk)
    up = lambda a: cv2.resize(a, (W, H), interpolation=cv2.INTER_LINEAR)
    return up(m), up(tex)


INK_TEX = None


def white_world(T, fi):
    global INK_TEX
    rng = np.random.default_rng(800 + fi)
    f = white_frame(T, fi)
    q = T - S.T_WHITE
    if S.T_INK0 <= T < S.T_INK1:
        if INK_TEX is None:
            INK_TEX = (0.02 + 0.05 * cv2.GaussianBlur(np.random.default_rng(9).random((H, W)).astype(np.float32), (0, 0), 2))[..., None]
        m, tex = ink_mask(T)
        m = m[..., None]
        ink = INK_TEX * 0.6 + (0.012 + 0.07 * tex ** 2)[..., None] * np.array([1.0, 1.0, 1.05], np.float32)   # wet bristle sheen
        f = f * (1 - m) + ink * m
    if q < 0.25:                                    # the hole finishes swallowing the frame: zoom settles
        f = zoom_fx(f, ease_out_rev(q / 0.25) * 0.5, 540, 900)
    f = tag_anim(f, 'E:' + S.EARTH_WHITE[0], T, S.T_WHITE - 0.001, S.T_CCTV, TAG_X, TAG_Y, rng) if T >= S.T_WHITE else f
    f = tag_anim(f, 'C:' + S.EARTH_WHITE[1], T, S.T_WHITE + 0.04, S.T_CCTV, TAG_X + 6, CTAG_Y, rng)
    if T > S.T_CCTV - 0.09:                         # glitch out into the CCTV
        f = glitch(f, rng, (T - (S.T_CCTV - 0.09)) / 0.09, n=16)
    return f, rng.normal(0, 1, 2) * (9 * np.exp(-since(T, KICKS) / 0.06))


# ================================================================== CCTV night + ghost
def _txt(text, size, font=F_MONO, color=(235, 235, 235)):
    f = ImageFont.truetype(font, size)
    l, t, r, b = f.getbbox(text)
    im = Image.new('RGBA', (r - l + 16, b - t + 16), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((8 - l, 8 - t), text, font=f, fill=color + (255,))
    a = np.asarray(im).astype(np.float32) / 255
    return a[..., :3] * a[..., 3:4], a[..., 3]


CCTV_T = {}


def cctv_overlay(f, T):
    if not CCTV_T:
        CCTV_T['rec'] = _txt('REC', 44)
        CCTV_T['cam'] = _txt('CAM 03', 40)
        CCTV_T['ch'] = _txt('CH-04', 30, color=(200, 200, 200))
    rgb, a = CCTV_T['rec']; f = put(f, rgb, a, 132, 258)
    if int(T * 2) % 2 == 0:
        cv2.circle(f, (100, 285), 17, (0.95, 0.12, 0.10), -1, cv2.LINE_AA)
    rgb, a = CCTV_T['cam']; f = put(f, rgb, a, 1010, 258, anchor='rt')
    rgb, a = CCTV_T['ch']; f = put(f, rgb, a, 1010, 316, anchor='rt')
    sec = 35 + int(T - S.T_CCTV)
    stamp = f'16-10-2026  02:39:{sec:02d}'
    if stamp not in CCTV_T:
        CCTV_T[stamp] = _txt(stamp, 36)
    rgb, a = CCTV_T[stamp]; f = put(f, rgb, a, 74, 1290)
    c = (0.85, 0.85, 0.85)
    for (x, y, sx, sy) in ((60, 220, 1, 1), (1020, 220, -1, 1), (60, 1360, 1, -1), (1020, 1360, -1, -1)):
        cv2.line(f, (x, y), (x + sx * 70, y), c, 3, cv2.LINE_AA); cv2.line(f, (x, y), (x, y + sy * 70), c, 3, cv2.LINE_AA)
    cv2.line(f, (540 - 26, 900), (540 + 26, 900), c, 2, cv2.LINE_AA); cv2.line(f, (540, 900 - 26), (540, 900 + 26), c, 2, cv2.LINE_AA)
    return f


GHOST_TEAL = hexc('#3df2e2')


def ghost(f, T, rng):
    q = T - S.T_GHOST
    if q < 0:
        return f
    dur = S.T_TEAL - S.T_GHOST
    e = np.clip(q / dur, 0, 1)
    fl = 0.55 + 0.45 * float(rng.random() > 0.25)
    alpha = smoothstep(0.0, 0.30, q) * fl
    wd = 430 + 520 * e ** 2.2
    rgb, a, halo, rim = sprite('m3g')
    lum = rgb.mean(2, keepdims=True)
    tint = None
    f2 = place_car(f, 'm3g', 540, 1090 - 120 * e ** 2, wd, alpha=alpha, outline='#2ef5e0', glow_k=1.3)
    # teal hologram look: re-colour the car pixels
    h, w = a.shape
    s = wd / w
    M = cv2.getRotationMatrix2D((w / 2, h / 2), 0, s); M[0, 2] += 540 - w / 2; M[1, 2] += 1090 - 120 * e ** 2 - h / 2
    aa = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR) * alpha
    ll = cv2.warpAffine(lum[..., 0] / np.maximum(a, 1e-3), M, (W, H), flags=cv2.INTER_LINEAR)
    holo = GHOST_TEAL[None, None] * (0.35 + 0.95 * ll[..., None]) * (0.85 + 0.15 * SCAN)
    f2 = f2 * (1 - aa[..., None] * 0.75) + holo * aa[..., None] * 0.75
    if rng.random() < 0.5:
        f2 = glitch(f2, rng, 0.5, n=6, y0=800, y1=1300, pix=False)
    return f2


def cctv_frame(T, fi):
    rng = np.random.default_rng(1100 + fi)
    q = T - S.T_CCTV
    f = shot_frame('C1', T, push=0.06)
    f = grade_cctv(f, T, fi)
    if q < 0.12:                                    # digital static burst on the cut (no white)
        f = glitch(f, rng, 1.0 - q / 0.12, n=18, maxshift=160)
        f = f * (0.55 + 0.45 * q / 0.12)
    if rng.random() < 0.06:
        f = glitch(f, rng, 0.35, n=6, pix=False)
    f = ghost(f, T, rng)
    f = cctv_overlay(f, T)
    if T > S.T_TEAL - 0.13:                         # zoom-through the ghost into the teal world
        s = ease_in((T - (S.T_TEAL - 0.13)) / 0.13)
        f = zoom_fx(f, s, 540, 1000, zmax=0.9, blur=0.4)
        f = mix(f, f * np.array([0.3, 1.0, 0.95], np.float32), s * 0.6)
    return f, rng.normal(0, 1, 2) * (14 * np.exp(-q / 0.07) + 1.2)


# ================================================================== teal world (Earth-928)
TEAL_CUTS = [S.T_TEAL, S.T_T2, S.T_T3, S.T_T4]
TEAL_SHOTS = ['T1', 'T2', 'T3', 'T4']
TEAL_KICKS = [S.beat(k) for k in np.arange(18, 22.01, 0.5)]
FLASH_T = {}


def flash_text(key):
    if key not in FLASH_T:
        f = ImageFont.truetype(F_FLASH, 430)
        l, t, r, b = f.getbbox(key)
        im = Image.new('L', (r - l + 120, b - t + 120), 0)
        ImageDraw.Draw(im).text((60 - l, 60 - t), key, font=f, fill=255)
        m = np.asarray(im).astype(np.float32) / 255
        FLASH_T[key] = m
    return FLASH_T[key]


def flash_layer(f, key, T, t_in, rng):
    q = T - t_in
    m = flash_text(key)
    h, w = m.shape
    sc = 1.0 * (1.25 - 0.25 * ease_out_cubic(min(1.0, q / 0.08)))
    M = cv2.getRotationMatrix2D((w / 2, h / 2), 6.0, sc)
    M[0, 2] += 540 - w / 2 + rng.normal(0, 3); M[1, 2] += 860 - h / 2
    a = cv2.warpAffine(m, M, (W, H), flags=cv2.INTER_LINEAR)
    fl = 0.80 + 0.20 * float(rng.random() > 0.2)
    sm = cv2.resize(a, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    g1 = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 4), (W, H)); g2 = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 14), (W, H))
    ol = np.clip(cv2.dilate(a, np.ones((11, 11), np.uint8)) - a, 0, 1)
    f = f * (1 - 0.55 * g2[..., None]) + hexc('#2ff2e2')[None, None] * (g1[..., None] * 1.1 + g2[..., None] * 0.9) * fl
    f = f * (1 - 0.85 * ol[..., None]) + hexc('#003a3e')[None, None] * ol[..., None] * 0.85
    f = f * (1 - a[..., None]) + np.array([1.08, 1.12, 1.12], np.float32) * a[..., None] * fl
    return f


def teal_frame(T, fi):
    rng = np.random.default_rng(1300 + fi)
    i = max(j for j in range(4) if TEAL_CUTS[j] <= T + 1e-9)
    q = T - TEAL_CUTS[i]
    z = punch(T, TEAL_KICKS, 0.06, 0.07)
    sh = rng.normal(0, 1, 2) * 12 * np.exp(-q / 0.07)
    kin = max(0.0, 1 - q / 0.16) ** 2 if i > 0 else 0.0
    ang = [0, 200, 340, 160][i]
    d = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))])
    f = shot_frame(TEAL_SHOTS[i], T, extra_zoom=z, shift=(sh[0] - 180 * kin * d[0], sh[1] - 180 * kin * d[1]), push=0.07)
    if kin > 0.003:
        f = dir_blur(f, 160 * kin, ang)
    f = grade_teal(f)
    if i == 0 and q < 0.28:                          # out of the ghost zoom
        f = zoom_fx(f, ease_out_rev(q / 0.28) * 0.9, 540, 1000)
    if S.T_FL1 <= T < S.T_FL2:
        f = flash_layer(f, 'M3', T, S.T_FL1, rng)
    elif S.T_FL2 <= T < S.T_OUT0 + 0.02:
        f = flash_layer(f, 'G80', T, S.T_FL2, rng)
    f = tag_anim(f, 'E:' + S.EARTH_TEAL[0], T, S.T_TEAL, S.T_OUT0, TAG_X, TAG_Y, rng)
    f = tag_anim(f, 'C:' + S.EARTH_TEAL[1], T, S.T_TEAL + 0.04, S.T_OUT0, TAG_X + 6, CTAG_Y, rng)
    f = rgb_split(f, 10 * np.exp(-since(T, TEAL_KICKS) / 0.07))
    if T > S.T_OUT0 - 0.07:
        f = glitch(f, rng, (T - (S.T_OUT0 - 0.07)) / 0.07, n=14)
    return f, sh


# ================================================================== outro: glowing flickering MEHRAB.7w7
NAME = 'MEHRAB.7w7'
NAME_M = None
LETTERS = None


def name_masks():
    global NAME_M, LETTERS
    if NAME_M is None:
        f = ImageFont.truetype(F_NAME, 128)
        widths = [f.getlength(c) for c in NAME]
        trk = 4
        tw = int(sum(widths) + trk * (len(NAME) - 1))
        asc, desc = f.getmetrics()
        hh = asc + desc + 80
        LETTERS = []
        full = np.zeros((hh, tw + 120), np.float32)
        x = 60
        for c, wdt in zip(NAME, widths):
            im = Image.new('L', (tw + 120, hh), 0)
            ImageDraw.Draw(im).text((x, 40), c, font=f, fill=255)
            m = np.asarray(im).astype(np.float32) / 255
            LETTERS.append(m); full = np.maximum(full, m)
            x += wdt + trk
        NAME_M = full
    return NAME_M, LETTERS


_rf = np.random.default_rng(77)
FLICK = [(_rf.uniform(0, 1.2), _rf.uniform(0.04, 0.12), _rf.uniform(0.05, 0.6)) for _ in range(26)]


def outro_frame(T, fi):
    rng = np.random.default_rng(1500 + fi)
    full, letters = name_masks()
    q = T - S.T_NAME
    f = np.zeros((H, W, 3), np.float32) + hexc('#020203')
    if T < S.T_NAME:                                 # 12.49 -> 12.62: the teal world glitches out into black
        return f, (0.0, 0.0)
    # per-letter brightness: staggered switch-on + random flicker dips (reference: miot.vfx letters flicker)
    h, w = full.shape
    acc = np.zeros_like(full)
    for j, m in enumerate(letters):
        on = smoothstep(0.02 * j, 0.02 * j + 0.06, q)
        b = on
        for (t0, d, dip) in FLICK:
            if (j * 7 + int(t0 * 10)) % len(letters) == j % len(letters) and t0 <= q < t0 + d:
                b *= dip
        if rng.random() < 0.04:
            b *= 0.35
        acc = np.maximum(acc, m * b)
    sc = 1.0 + 0.05 * q / (S.T_NAME_END - S.T_NAME)
    M = cv2.getRotationMatrix2D((w / 2, h / 2), 7.0, sc)
    M[0, 2] += 540 - w / 2; M[1, 2] += 880 - h / 2 - 14 * q
    a = cv2.warpAffine(acc, M, (W, H), flags=cv2.INTER_LINEAR)
    dots = (HT_D < 0.34).astype(np.float32)
    core = a * (0.78 + 0.22 * dots)
    sm = cv2.resize(a, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    g1 = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 3), (W, H)); g2 = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 12), (W, H))
    f = f + np.array([0.92, 0.95, 1.0], np.float32) * (core[..., None] * 1.0 + g1[..., None] * 0.55 + g2[..., None] * 0.35)
    if q < 0.10:
        f = glitch(f, rng, 1 - q / 0.10, n=10, y0=700, y1=1100)
        f = rgb_split(f, 14 * (1 - q / 0.10))
    if T > S.T_NAME_END - 0.10:                      # glitch out to black
        k = np.clip((T - (S.T_NAME_END - 0.10)) / 0.10, 0, 1)
        f = glitch(f, rng, k, n=10, y0=700, y1=1100) * (1 - k)
    if T >= S.T_NAME_END:
        f = np.zeros((H, W, 3), np.float32) + hexc('#020203')
    return f, rng.normal(0, 1, 2) * 2.0


FRAME0 = None


def reveal_frame(T, fi):
    """black -> the first frame appears brightest-first (red taillights, then the snow), ends exactly on frame 0"""
    global FRAME0
    if FRAME0 is None:
        g, sh = intro_frame(0.0, 0)
        FRAME0 = (g, cv2.GaussianBlur(g.mean(2), (0, 0), 2.5))
    g, lum = FRAME0
    t_last = (NF - 1) / FPS
    p = np.clip((T - S.T_REVEAL) / (t_last - S.T_REVEAL), 0, 1)
    th = 1.05 - 1.12 * (1 - (1 - p) ** 1.6)
    nz = cv2.resize(NOISE_CCTV[3][:120, :68], (W, H), interpolation=cv2.INTER_LINEAR) * 0.05
    m = smoothstep(th, th + 0.10, lum + nz)
    base = np.zeros((H, W, 3), np.float32) + hexc('#020203')
    return base * (1 - m[..., None]) + g * m[..., None], (0.0, 0.0)


# ================================================================== home Earth (intro)
INTRO = [('I1', 0.0), ('I2', S.T_I2), ('I3', S.T_I3), ('I4', S.T_I4), ('I5', S.T_I5)]
INTRO_ONSETS = [1.488, 1.765, 2.0, 2.251, 2.384, 2.747, 3.003, 3.259]


def intro_frame(T, fi):
    rng = np.random.default_rng(300 + fi)
    i = max(j for j in range(len(INTRO)) if INTRO[j][1] <= T + 1e-9)
    name, t0 = INTRO[i]
    q = T - t0
    z = punch(T, INTRO_ONSETS, 0.045, 0.08)
    f = shot_frame(name, T, extra_zoom=z, push=0.07 if i else 0.05)
    f = grade_night(f)
    # Spider-Verse glitch: on every cut + small bursts on the vocal onsets
    g = 0.0
    if i > 0:
        g = max(g, 0.9 * np.exp(-q / 0.07))
    g = max(g, 0.45 * np.exp(-since(T, INTRO_ONSETS) / 0.05))
    if i == 0 and 1.30 < T:                           # glitch smear out of the first shot (reference)
        g = max(g, (T - 1.30) / (S.T_I2 - 1.30))
        f = dir_blur(f, 140 * ((T - 1.30) / (S.T_I2 - 1.30)) ** 2, 0)
    f = glitch(f, rng, g, n=14)
    f = rgb_split(f, 3.0 + 10 * g)
    f = tag_anim(f, 'q', T, S.T_I2, S.T_I4, 1010, 300, rng, anchor='rt')
    f = tag_anim(f, 'mv', T, S.T_I4, S.T_PORTAL, TAG_X, 300, rng)
    if T > S.T_PORTAL - 0.26:                         # zoom-through the red angel eye into the portal
        s = ease_in((T - (S.T_PORTAL - 0.26)) / 0.26)
        f = zoom_fx(f, s, 420, 1010, zmax=1.2, blur=0.45)
        f = mix(f, f * np.array([1.25, 0.35, 0.30], np.float32), s * 0.7)
    return f, rng.normal(0, 1, 2) * 9 * np.exp(-q / 0.07) * (1 if i else 0)


def portal_in(f, T):
    q = T - S.T_PORTAL
    if q < 0.22:
        f = zoom_fx(f, ease_out_rev(q / 0.22) * 1.0, 540, 880, zmax=0.9)
    return f


# ================================================================== watermark + finish
_wm = Image.new('L', (W, 110), 0); _dw = ImageDraw.Draw(_wm)
_f = ImageFont.truetype(FONT_REG, 44); _tx = 'MEHRAB.7w7'
_tw = sum(_f.getlength(c) for c in _tx) + 3 * (len(_tx) - 1); _xx = (W - _tw) / 2
for c in _tx:
    _dw.text((_xx, 30), c, font=_f, fill=255); _xx += _f.getlength(c) + 3
WM = np.asarray(_wm, np.float32) / 255
WM_SH = cv2.GaussianBlur(WM, (0, 0), 4)
WM_OL = np.clip(cv2.GaussianBlur(cv2.dilate(WM, np.ones((5, 5), np.uint8)), (0, 0), 1.0) - WM, 0, 1)   # dark rim
_wr = np.where(WM.max(1) > 0.5)[0]
WM_Y = int(S.WM_CY - (_wr.min() + _wr.max()) / 2)


def finish(f, fi, shake=(0.0, 0.0)):
    reg = f[WM_Y:WM_Y + 110]
    bgl = float(reg[20:90, 300:780].mean())                  # bright background (white world): stronger shadow + rim
    kb = float(smoothstep(0.50, 0.85, bgl))
    reg[:] = reg * (1 - WM_SH[..., None] * (0.55 + 0.40 * kb))
    if kb > 0.01:
        reg[:] = reg * (1 - WM_OL[..., None] * 0.85 * kb)
    reg[:] = reg * (1 - WM[..., None] * 0.95) + WM[..., None] * 0.95
    f = f + (GRAIN[fi % 6].astype(np.float32) * 0.014)[..., None]
    img = (np.clip(soft_clip(f), 0, 1) * 255 + 0.5).astype(np.uint8)
    if abs(shake[0]) + abs(shake[1]) > 0.3:
        M = np.float32([[1, 0, shake[0]], [0, 1, shake[1]]])
        img = cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return img


def compose(T, fi):
    if T < S.T_PORTAL:
        return intro_frame(T, fi)
    if T < S.T_HOLE:
        f, sh = portal_frame(T, fi)
        return portal_in(f, T), sh
    if T < S.T_WHITE:
        return hole_frame(T, fi)
    if T < S.T_CCTV:
        return white_world(T, fi)
    if T < S.T_TEAL:
        return cctv_frame(T, fi)
    if T < S.T_OUT0:
        return teal_frame(T, fi)
    if T < S.T_REVEAL:
        if T < S.T_NAME:
            f, sh = teal_frame(min(T, S.T_OUT0 - 1e-3), fi)
            k = (T - S.T_OUT0) / (S.T_NAME - S.T_OUT0)
            rng = np.random.default_rng(1700 + fi)
            f = glitch(f, rng, 1.0, n=20) * (1 - k) ** 1.5
            return f, sh
        return outro_frame(T, fi)
    return reveal_frame(T, fi)


def render(fi):
    T = fi / FPS
    f, sh = compose(T, fi)
    return finish(f, fi, sh)


# ================================================================== extraction
def extract(only=None):
    for name, (clip, src, t0, t1, z, cx, cy, sp) in S.SHOTS.items():
        if only and name not in only:
            continue
        dur = (t1 - t0) * sp + 0.15
        d = f'{SEG}/{name}'
        os.makedirs(d, exist_ok=True)
        for fn in os.listdir(d):
            os.remove(f'{d}/{fn}')
        x0, y0, x1, y1 = S.PBOX
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{src:.3f}', '-i', f'{WORK}/clips/{clip}.mp4', '-t', f'{dur:.3f}',
                        '-vf', f'crop={x1 - x0}:{y1 - y0}:{x0}:{y0},fps=60', '-q:v', '2', f'{d}/%04d.jpg'], check=True)
        if name in getattr(S, 'PLATES', {}):
            ok = 0
            for fn in sorted(os.listdir(d)):
                im = cv2.imread(f'{d}/{fn}')
                for (bx0, by0, bx1, by1, thr, delta) in S.PLATES[name]:
                    ok += bool(blank_plate(im, (bx0, by0, bx1, by1), thr, delta))
                cv2.imwrite(f'{d}/{fn}', im, [cv2.IMWRITE_JPEG_QUALITY, 96])
            print(name, 'plates blanked in', ok, 'frames')
        print(name, clip, f'{src:.2f}-{src + dur:.2f}', len(os.listdir(d)), 'frames', flush=True)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'extract':
        extract(sys.argv[2:])
    elif mode == 'frames':
        os.makedirs(f'{WORK}/check6', exist_ok=True)
        for tok in sys.argv[2:]:
            T = float(tok); fi = int(round(T * FPS))
            t1 = time.time(); img = render(fi)
            print(f'T={T} fi={fi} {time.time() - t1:.2f}s', file=sys.stderr)
            cv2.imwrite(f'{WORK}/check6/N6_{T:06.3f}.png', cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    elif mode in ('range', 'video'):
        out = sys.argv[2]
        if mode == 'range':
            f0 = int(round(float(sys.argv[3]) * FPS)); f1 = int(round(float(sys.argv[4]) * FPS))
            enc = ['-preset', 'veryfast', '-crf', '18']
        else:
            f0, f1 = 0, NF
            enc = ['-preset', 'medium', '-crf', '14']
        from multiprocessing import Pool
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                               '-i', '-'] + enc + ['-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        t1 = time.time()
        with Pool(2) as pool:
            for n, img in enumerate(pool.imap(render, range(f0, f1), chunksize=2)):
                ff.stdin.write(img.tobytes())
                if n % 60 == 0:
                    print(f'frame {n}/{f1 - f0} {time.time() - t1:.1f}s', file=sys.stderr, flush=True)
        ff.stdin.close(); ff.wait()
        print('done', time.time() - t1, file=sys.stderr)
