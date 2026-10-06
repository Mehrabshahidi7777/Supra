"""Night 5 — MEHRAB.7w7 Reveal, built on the reference's mechanism (YouTube template @Zs3riyx, ELA PEIDA FUNK Slowed):

  intro (0 -> drop 4.336): blue GT3 RS, 3 calm shots, cold snowy grade + falling snow, white exposure flashes on the
      vocal accents; just before the drop two orange P1 stickers slide into the snowy shot;
  drop: heavy zoom blur + flash into real footage; from here one cut per beat, every shot enters with a strong
      directional blur, punch + shake on the kick, orange fire embers over everything;
  each car 4 beats, on its last beat the NEXT car pops in as a sticker (P1 -> black Turbo S -> silver GT3);
  beat 8: white flash + spiky chrome MEHRAB.7w7 slams over the silver GT3, holds 4 beats (reflections move on the
      beat), turns black chrome on its last beat while a silver sticker pops in; gone on beat 12;
  end: chrome MEHRAB.7w7 end card on black with embers on the last kick, tape-stop song tail, white flash that
      matches the opening flash -> seamless loop.
House look: dark band over the top ~20 % (reference), MEHRAB.7w7 line at ~3/4 height on the whole video.

  WORK=$WORK python3 render5.py extract
  WORK=$WORK python3 render5.py frames 0.5 4.4 8.6 12.9
  WORK=$WORK python3 render5.py range out.mp4 3.5 5.5
  WORK=$WORK python3 render5.py video $WORK/n5_noaudio.mp4
"""
import sys, os, time, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.normpath(os.path.join(HERE, '..', '..', 'kit'))
WORK = os.environ.get('WORK', '/home/claude/work_edit')
sys.path.insert(0, KIT)
sys.path.insert(0, HERE)
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from lib import hexc, smoothstep, ease_out_back, ease_out_cubic, fractal_noise, FONT_REG
from framing import crop_window
import shots5 as S
from logo5 import Logo

cv2.setNumThreads(1)
W, H = 1080, 1920
FPS = int(os.environ.get('N5_FPS', str(S.FPS_OUT)))
W4, H4 = W // 4, H // 4
NF = int(round((S.T_END - S.S0) * FPS))
NSHOT = len(S.SHOTS)
SEG = f'{WORK}/seg5'
WHITE = np.ones(3, np.float32)
EMBER = hexc('#ff6a14')
EMBER_CORE = hexc('#ffd48a')
INTRO_N = 3


def mix(a, b, k):
    return a * (1 - k) + b * k


def up(a4):
    return cv2.resize(a4, (W, H), interpolation=cv2.INTER_LINEAR)


def decay(T, items, tau):
    v = 0.0
    for t, s in items:
        dt = T - t
        if 0 <= dt < 8 * tau:
            v += s * np.exp(-dt / tau)
    return v


# ================================================================== static fields
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
_rr = np.hypot((xx - W / 2) / (W * 0.62), (yy - H / 2) / (H * 0.58))
VIG = (1 - 0.60 * smoothstep(0.45, 1.25, _rr))[..., None].astype(np.float32)
EDGE = smoothstep(0.55, 1.15, _rr)[..., None].astype(np.float32)
BANDM = (1 - smoothstep(S.BAND_Y * H - 14, S.BAND_Y * H + 10, yy))[..., None].astype(np.float32)
FOG = (0.55 + 0.45 * smoothstep(0.25 * H, 0.75 * H, yy))[..., None].astype(np.float32)
FROST = smoothstep(0.62, 1.20, _rr)[..., None].astype(np.float32)
del yy, xx, _rr
GRAIN = [np.random.default_rng(40 + i).normal(0, 1, (H, W)).astype(np.float16) for i in range(6)]
SMOKE = fractal_noise(720, 405, 51, octaves=5, base=4).astype(np.float32)
BAND_Y = int(S.BAND_Y * H)

# ================================================================== footage
FRAME_LIST = {}
for _s in S.SHOTS:
    _d = f'{SEG}/{_s[0]}'
    FRAME_LIST[_s[0]] = sorted(os.listdir(_d)) if os.path.isdir(_d) else []
_cache = {}


def load(name, idx):
    lst = FRAME_LIST[name]
    idx = int(np.clip(idx, 0, len(lst) - 1))
    key = (name, idx)
    if key not in _cache:
        if len(_cache) > 10:
            _cache.clear()
        _cache[key] = cv2.cvtColor(cv2.imread(f'{SEG}/{name}/{lst[idx]}'), cv2.COLOR_BGR2RGB)
    return _cache[key]


def ext_fps(name):
    return 120 if name in S.INTERP else 60


def shot_frame(i, T, extra_zoom=1.0, shift=(0, 0), rot=0.0, push=0.05):
    nm, ch, clip, src, z, cx, cy, sp = S.SHOTS[i]
    t0, t1 = S.CUTS[i], S.CUTS[i + 1]
    im = load(nm, (T - t0) * ext_fps(nm) * sp)
    prog = np.clip((T - t0) / (t1 - t0), 0, 1)
    zz = z * (1 + push * (prog * prog * (3 - 2 * prog))) * extra_zoom
    X, Y, ww, wh = crop_window(im.shape, zz, cx, cy)
    s = W / ww
    M = cv2.getRotationMatrix2D((X, Y), rot, s)
    M[0, 2] += W / 2 - X + shift[0]
    M[1, 2] += H / 2 - Y + shift[1]
    return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32) / 255.0


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
    """zoom-through: scale about (cx, cy) by 1 + zmax*s with a radial blur that grows with s (s = 0..1)"""
    if s < 0.002:
        return f
    sc = 1 + zmax * s
    M = np.float32([[sc, 0, cx * (1 - sc)], [0, sc, cy * (1 - sc)]])
    g = cv2.warpAffine(f, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return zoom_blur(g, blur * s ** 1.3, n=9, cx=cx, cy=cy)


def spin_fx(f, s, sign=1.0, amax=34.0, zmax=0.40, n=9):
    """spin: rotate by sign*amax*s about the centre (zoomed to hide the corners) with a spin blur that grows with s"""
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


def trans_fx(f, kind, s, centre, phase):
    if kind == 'zoom':
        cx, cy = centre if (centre is not None and phase == 'out') else (W / 2, H / 2)
        return zoom_fx(f, s, cx, cy)
    if kind == 'spin':
        return spin_fx(f, s, sign=1.0 if phase == 'out' else -1.0)
    return f


def ease_in(q):
    q = float(np.clip(q, 0, 1))
    return q * q * q


def ease_out_rev(q):
    """1 at the cut, easing out to 0"""
    q = float(np.clip(q, 0, 1))
    return (1 - q) ** 3


def apply_trans(f, T, i):
    """scene transitions of shot i: 'out' toward the next cut, 'in' after its own cut (see shots5.TRANS)"""
    nxt = S.TRANS.get(i + 1)
    if nxt is not None:
        kind, d_out, d_in, centre = nxt
        t_cut = S.CUTS[i + 1]
        if d_out > 0 and T >= t_cut - d_out:
            f = trans_fx(f, kind, ease_in((T - (t_cut - d_out)) / d_out), centre, 'out')
    cur = S.TRANS.get(i)
    if cur is not None:
        kind, d_out, d_in, centre = cur
        if d_in > 0 and T < S.CUTS[i] + d_in:
            f = trans_fx(f, kind, ease_out_rev((T - S.CUTS[i]) / d_in), centre, 'in')
    return f


def has_trans(i):
    return i in S.TRANS


def rgb_split(f, amt, vertical=False):
    if amt < 0.5:
        return f
    o = f.copy()
    d = (0, amt) if vertical else (amt, 0)
    M1 = np.float32([[1, 0, d[0]], [0, 1, d[1]]]); M2 = np.float32([[1, 0, -d[0]], [0, 1, -d[1]]])
    o[..., 0] = cv2.warpAffine(np.ascontiguousarray(f[..., 0]), M1, (W, H), borderMode=cv2.BORDER_REFLECT)
    o[..., 2] = cv2.warpAffine(np.ascontiguousarray(f[..., 2]), M2, (W, H), borderMode=cv2.BORDER_REFLECT)
    return o


# ================================================================== grades
_x = np.arange(256) / 255.0
_c = 1 / (1 + np.exp(-(_x - 0.5) * 6.6))
_c = (_c - _c[0]) / (_c[-1] - _c[0])
_c = 0.62 * _c + 0.38 * _x
_c = np.clip((_c - 0.035) / 0.965, 0, 1) ** 1.08
LUT_WARM = (_c * 255).astype(np.uint8)
_c2 = 1 / (1 + np.exp(-(_x - 0.5) * 4.0))
_c2 = (_c2 - _c2[0]) / (_c2[-1] - _c2[0])
LUT_COLD = (np.clip(0.5 * _c2 + 0.5 * _x, 0, 1) * 255).astype(np.uint8)


def grade_warm(f, ca=0.0):
    u8 = cv2.LUT((np.clip(f, 0, 1) * 255).astype(np.uint8), LUT_WARM)
    f = u8.astype(np.float32) / 255.0
    g = f.mean(2, keepdims=True)
    f = np.clip(g + (f - g) * 1.32, 0, 1)
    f = f * np.array([1.03, 1.0, 0.95], np.float32)               # a touch warmer (fire embers)
    sm = cv2.resize(f, (W // 6, H // 6), interpolation=cv2.INTER_AREA)
    bl = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 2.2), (W, H), interpolation=cv2.INTER_LINEAR)
    f = f * (1 - EDGE * 0.85) + bl * (EDGE * 0.85)
    f = f + 0.35 * (f - cv2.GaussianBlur(f, (0, 0), 1.3))
    a = 0.0022 + ca
    for ch, sg in ((0, 1), (2, -1)):
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, 1 + sg * a)
        f[..., ch] = cv2.warpAffine(np.ascontiguousarray(f[..., ch]), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return f * VIG


def grade_cold(f):
    """snowy look: everything goes milky white-grey, the blue paint stays saturated"""
    u8 = cv2.LUT((np.clip(f, 0, 1) * 255).astype(np.uint8), LUT_COLD)
    f = u8.astype(np.float32) / 255.0
    r, g, b = f[..., 0], f[..., 1], f[..., 2]
    lum = (0.30 * r + 0.55 * g + 0.15 * b)[..., None]
    blue = np.clip((b - np.maximum(r, g * 0.92)) * 5.0, 0, 1)[..., None]
    f = lum + (f - lum) * (0.18 + 0.95 * blue)
    f = f * np.array([0.93, 0.985, 1.07], np.float32)
    f = 0.13 + 0.87 * f                                            # lifted, misty blacks
    f = f * (1 - 0.20 * FOG) + np.array([0.86, 0.90, 0.96], np.float32) * 0.20 * FOG
    f = f * (1 - 0.35 * FROST) + 0.95 * 0.35 * FROST               # frosty white edges
    f = f + 0.25 * (f - cv2.GaussianBlur(f, (0, 0), 1.4))
    return f


# ================================================================== particles
NSN = 420
_r = np.random.default_rng(5)
SN_X0 = _r.uniform(0, W, NSN); SN_Y0 = _r.uniform(0, H + 100, NSN)
SN_V = _r.uniform(110, 330, NSN); SN_D = _r.uniform(0.3, 1.0, NSN)
SN_WOB = _r.uniform(6, 26, NSN); SN_WF = _r.uniform(0.6, 1.8, NSN); SN_PH = _r.uniform(0, 6.28, NSN)
NBIG = 26
SB_X0 = _r.uniform(0, W, NBIG); SB_Y0 = _r.uniform(0, H + 300, NBIG); SB_V = _r.uniform(380, 620, NBIG)
SB_R = _r.uniform(7, 17, NBIG)


def draw_snow(f, T, k=1.0):
    C = np.zeros((H, W), np.float32)
    x = (SN_X0 + 38 * T * SN_D + SN_WOB * np.sin(SN_WF * T + SN_PH)) % W
    y = (SN_Y0 + SN_V * T) % (H + 100) - 50
    for j in range(NSN):
        r = 1.2 + 3.0 * SN_D[j]
        L = SN_V[j] / FPS * 0.6
        cv2.line(C, (int(x[j] * 16), int((y[j] - L) * 16)), (int(x[j] * 16), int(y[j] * 16)), 0.55 + 0.45 * SN_D[j],
                 max(1, int(round(r))), cv2.LINE_AA, shift=4)
    B4 = np.zeros((H4, W4), np.float32)
    bx = (SB_X0 + 70 * T) % W
    by = (SB_Y0 + SB_V * T) % (H + 300) - 150
    for j in range(NBIG):
        cv2.circle(B4, (int(bx[j] / 4 * 16), int(by[j] / 4 * 16)), int(SB_R[j] / 4 * 16), 0.55, -1, cv2.LINE_AA, shift=4)
    B4 = cv2.GaussianBlur(B4, (0, 0), 1.6)
    a = np.clip(C + up(B4), 0, 1)[..., None] * k
    return f * (1 - a * 0.85) + np.array([0.97, 0.98, 1.0], np.float32) * a


NE = 120
_e = np.random.default_rng(21)
E_X0 = _e.uniform(0, W, NE); E_Y0 = _e.uniform(0, H + 200, NE)
E_V = _e.uniform(70, 230, NE); E_SZ = _e.uniform(1.4, 4.2, NE)
E_WOB = _e.uniform(14, 60, NE); E_WF = _e.uniform(0.4, 1.5, NE); E_PH = _e.uniform(0, 6.28, NE)
E_BR = _e.uniform(0.35, 1.0, NE); E_FL = _e.uniform(4, 13, NE)
NEB = 14
EB_X0 = _e.uniform(0, W, NEB); EB_Y0 = _e.uniform(0, H + 300, NEB); EB_V = _e.uniform(120, 260, NEB)
EB_R = _e.uniform(14, 34, NEB); EB_PH = _e.uniform(0, 6.28, NEB)


def draw_embers(f, T, k=1.0):
    if k < 0.01:
        return f
    core = np.zeros((H, W), np.float32)
    x = (E_X0 + E_WOB * np.sin(E_WF * T + E_PH) + 25 * T) % W
    y = (E_Y0 - E_V * T) % (H + 200) - 100
    br = E_BR * (0.55 + 0.45 * np.sin(E_FL * T + E_PH * 3))
    for j in range(NE):
        L = E_V[j] / FPS * 1.2
        cv2.line(core, (int(x[j] * 16), int((y[j] + L) * 16)), (int(x[j] * 16), int(y[j] * 16)), float(br[j]),
                 max(1, int(round(E_SZ[j]))), cv2.LINE_AA, shift=4)
    big = np.zeros((H4, W4), np.float32)
    bx = (EB_X0 + 30 * np.sin(0.7 * T + EB_PH) + 20 * T) % W
    by = (EB_Y0 - EB_V * T) % (H + 300) - 150
    for j in range(NEB):
        cv2.circle(big, (int(bx[j] / 4 * 16), int(by[j] / 4 * 16)), int(EB_R[j] / 4 * 16),
                   0.45 + 0.25 * np.sin(5 * T + EB_PH[j]), -1, cv2.LINE_AA, shift=4)
    big = cv2.GaussianBlur(big, (0, 0), 2.4)
    glow = cv2.GaussianBlur(cv2.resize(core, (W4, H4), interpolation=cv2.INTER_AREA), (0, 0), 2.0)
    add = (EMBER[None, None] * (up(glow) * 2.6 + up(big) * 0.9)[..., None]
           + EMBER_CORE[None, None] * (core * 0.95)[..., None]) * k
    return f + add


# ================================================================== stickers (car cutouts)
def clean_rect(img, x0, y0, x1, y1):
    reg = img[y0:y1, x0:x1]
    ring = np.concatenate([img[y0 - 4:y0, x0:x1].reshape(-1, 3), img[y1:y1 + 4, x0:x1].reshape(-1, 3)])
    fill = np.median(ring, 0)
    reg[:] = fill
    img[y0 - 6:y1 + 6, x0 - 6:x1 + 6] = cv2.GaussianBlur(img[y0 - 6:y1 + 6, x0 - 6:x1 + 6], (0, 0), 2.0)


PLATES = {'p1b': (296, 1162, 368, 1193), 'p1a': (310, 1114, 372, 1131)}
SPR = {}


def sprite(key, flip=False):
    if (key, flip) in SPR:
        return SPR[(key, flip)]
    img = cv2.cvtColor(cv2.imread(f'{WORK}/cut/{key}_img.png'), cv2.COLOR_BGR2RGB)
    if key in PLATES:
        clean_rect(img, *PLATES[key])
    m = np.load(f'{WORK}/cut/{key}_mask.npy').astype(np.float32)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    ys, xs = np.where(m > 0.5)
    pad = 40
    y0, y1 = max(0, ys.min() - pad), min(m.shape[0], ys.max() + pad)
    x0, x1 = max(0, xs.min() - pad), min(m.shape[1], xs.max() + pad)
    img = img[y0:y1, x0:x1].astype(np.float32) / 255; m = m[y0:y1, x0:x1]
    u8 = cv2.LUT((img * 255).astype(np.uint8), LUT_WARM).astype(np.float32) / 255
    g = u8.mean(2, keepdims=True); img = np.clip(g + (u8 - g) * 1.22, 0, 1)
    if flip:
        img = img[:, ::-1].copy(); m = m[:, ::-1].copy()
    # contact shadow: bottom part of the silhouette squashed + blurred
    sh = np.zeros_like(m)
    hh = m.shape[0]
    sq = cv2.resize(m, (m.shape[1], max(2, hh // 5)))
    yb = int(ys.max() - y0 - hh // 10)
    sh[max(0, yb):max(0, yb) + sq.shape[0]] = sq[:max(0, min(sq.shape[0], hh - yb))]
    sh = cv2.GaussianBlur(sh, (0, 0), 14)
    rim = np.clip(cv2.dilate((m > 0.5).astype(np.float32), np.ones((7, 7), np.uint8)) - m, 0, 1)
    SPR[(key, flip)] = (img * m[..., None], m, sh, cv2.GaussianBlur(rim, (0, 0), 1.2))
    return SPR[(key, flip)]


def place(f, key, flip, cx, cy, width, rot=0.0, alpha=1.0, flash=0.0, tint=None, blur=0.0, shadow=0.7):
    rgb, a, sh, rim = sprite(key, flip)
    h, w = a.shape
    s = width / w
    M = cv2.getRotationMatrix2D((w / 2, h / 2), rot, s)
    M[0, 2] += cx - w / 2
    M[1, 2] += cy - h / 2
    rr = cv2.warpAffine(rgb, M, (W, H), flags=cv2.INTER_LINEAR)
    aa = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR) * alpha
    ss = cv2.warpAffine(sh, M, (W, H), flags=cv2.INTER_LINEAR) * alpha
    if blur > 1:
        rr = dir_blur(rr, blur, 0); aa = dir_blur(aa[..., None].repeat(3, 2), blur, 0)[..., 0]
    if tint is not None:
        rr = rr * tint
    f = f * (1 - shadow * ss[..., None])
    if flash > 0.01:
        rm = cv2.warpAffine(rim, M, (W, H), flags=cv2.INTER_LINEAR) * alpha
        rr = rr + aa[..., None] * flash * 0.9
        f = f + rm[..., None] * flash * 1.5
    return rr * alpha + f * (1 - aa[..., None])


def stickers(f, T, cold=False):
    for key, t_in, t_end, x, y, wd, mode, flip in S.STICKERS:
        if not (t_in <= T < t_end):
            continue
        q = T - t_in
        if mode == 'slide':
            e = ease_out_back(min(1.0, q / 0.24), 1.25)
            cx = x + (1 - e) * 820
            vel = 820 * (1 - min(1.0, q / 0.24)) ** 2
            f = place(f, key, flip, cx, y, wd, rot=-5 * (1 - e), blur=vel * 0.08,
                      tint=np.array([0.92, 0.96, 1.04], np.float32) if cold else None, shadow=0.55)
        else:
            e = ease_out_back(min(1.0, q / 0.13), 2.2)
            sc = 0.25 + 0.75 * e
            f = place(f, key, flip, x, y, wd * sc, rot=-8 * (1 - e), alpha=min(1.0, q / 0.03),
                      flash=0.0, shadow=0.6)
    return f


# ================================================================== logo
LOGO = Logo(f'{WORK}/logo/logo5.npz')
LOGO_SH = cv2.GaussianBlur(LOGO.m, (0, 0), 13)
LOGO_STROKE = cv2.GaussianBlur(cv2.dilate((LOGO.m > 0.3).astype(np.float32), np.ones((9, 9), np.uint8)), (0, 0), 1.6)
KICKS = [S.beat(k) for k in range(0, 19)]


def logo_layer(f, T, cy, t_in, dark=0.0, base_scale=0.93, env_k=0.12, glow_k=1.0):
    """composite the chrome logo centred at (540, cy); slam at t_in"""
    q = T - t_in
    slam = ease_out_cubic(min(1.0, q / 0.11))
    sc = base_scale * (1.55 - 0.55 * slam)
    for kt in KICKS:                                     # punch on every kick after the slam
        if t_in + 0.2 < kt <= T:
            sc *= 1 + 0.035 * np.exp(-(T - kt) / 0.08)
    sc *= 1 + 0.012 * np.sin(2 * np.pi * (T - t_in) / (4 * S.B))
    off = 0.10 * (T - t_in) / (4 * S.B) + 0.05 * np.sin(2 * np.pi * (T - t_in) / (2 * S.B))
    sweep = None
    for st in (t_in + 2 * S.B, t_in + 6 * S.B):           # light band sweeps across on two beats
        if st <= T < st + 0.35:
            sweep = -0.1 + 1.25 * (T - st) / 0.35
    rgb, a = LOGO.shade(off, dark, sweep)
    lh, lw = a.shape
    M = np.float32([[sc, 0, 540 - lw * sc / 2], [0, sc, cy - lh * sc / 2]])
    al = min(1.0, q / 0.035)
    rr = cv2.warpAffine(rgb, M, (W, H), flags=cv2.INTER_LINEAR) * al
    aa = cv2.warpAffine(a, M, (W, H), flags=cv2.INTER_LINEAR) * al
    sh = cv2.warpAffine(LOGO_SH, M, (W, H), flags=cv2.INTER_LINEAR) * al
    sh = np.roll(np.roll(sh, 18, 0), 8, 1)
    stk = cv2.warpAffine(LOGO_STROKE, M, (W, H), flags=cv2.INTER_LINEAR) * al
    if env_k > 0:                                         # chrome reflects the scene a little
        env = cv2.GaussianBlur(cv2.resize(f, (W4, H4), interpolation=cv2.INTER_AREA), (0, 0), 3)
        nx = cv2.warpAffine(LOGO.nx, M, (W4 * 4, H4 * 4))[::4, ::4]
        ny = cv2.warpAffine(LOGO.ny, M, (W4 * 4, H4 * 4))[::4, ::4]
        gy, gx = np.mgrid[0:H4, 0:W4].astype(np.float32)
        refl = cv2.remap(env, gx + nx * 40, gy + ny * 40 - 30, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
        rr = rr * (1 - env_k) + up(refl) * aa[..., None] * env_k * (1.25 - dark)
    f = f * (1 - 0.72 * sh[..., None])
    f = f * (1 - 0.80 * stk[..., None])
    if slam < 1:
        rr = zoom_blur(rr, 0.20 * (1 - slam), cx=540, cy=cy)
        aa = zoom_blur(aa[..., None].repeat(3, 2), 0.20 * (1 - slam), cx=540, cy=cy)[..., 0]
    glow = cv2.GaussianBlur(cv2.resize(aa, (W4, H4), interpolation=cv2.INTER_AREA), (0, 0), 5)
    f = f + up(glow)[..., None] * np.array([0.75, 0.82, 1.0], np.float32) * (0.25 + 0.6 * np.exp(-q / 0.12)) * (1 - 0.7 * dark) * glow_k
    return rr + f * (1 - aa[..., None])


def logo_glitch(f, rng, n=8, amp=50, y0=380, y1=1020):
    o = f.copy()
    for _ in range(n):
        y = int(rng.integers(y0, y1 - 30)); h = int(rng.integers(8, 46))
        o[y:y + h] = np.roll(o[y:y + h], int(rng.normal(0, amp)), axis=1)
    return o


# ================================================================== watermark
_wm = Image.new('L', (W, 110), 0); _d = ImageDraw.Draw(_wm)
_f = ImageFont.truetype(FONT_REG, 44); _tx = 'MEHRAB.7w7'
_tw = sum(_f.getlength(c) for c in _tx) + 3 * (len(_tx) - 1); _xx = (W - _tw) / 2
for c in _tx:
    _d.text((_xx, 30), c, font=_f, fill=255); _xx += _f.getlength(c) + 3
WM = np.asarray(_wm, np.float32) / 255
WM_SH = cv2.GaussianBlur(WM, (0, 0), 4)
_wr = np.where(WM.max(1) > 0.5)[0]
WM_Y = int(S.WM_CY - (_wr.min() + _wr.max()) / 2)


def soft_clip(f):
    return np.where(f < 0.82, f, 0.82 + 0.18 * np.tanh((f - 0.82) / 0.18))


def finish(f, fi, shake=(0.0, 0.0), band_line=0.0, band=True):
    if band and S.BAND:
        sm = cv2.resize(f[:BAND_Y + 40], (W // 8, (BAND_Y + 40) // 8), interpolation=cv2.INTER_AREA)
        bl = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 1.5), (W, BAND_Y + 40), interpolation=cv2.INTER_LINEAR)
        reg = f[:BAND_Y + 40]
        bm = BANDM[:BAND_Y + 40]
        reg[:] = reg * (1 - bm) + (bl * 0.34 + 0.025) * bm
        if band_line > 0.02:                                 # violet edge line on flashes (reference)
            yl = BAND_Y
            col = np.array([0.62, 0.50, 1.0], np.float32) * band_line
            f[yl - 2:yl + 3] += col
            f[yl - 14:yl + 15] += col * 0.25
    reg = f[WM_Y:WM_Y + 110]
    reg[:] = reg * (1 - WM_SH[..., None] * 0.55)
    reg[:] = reg * (1 - WM[..., None] * 0.95) + WM[..., None] * 0.95
    f = f + (GRAIN[fi % 6].astype(np.float32) * 0.016)[..., None]
    img = (np.clip(soft_clip(f), 0, 1) * 255 + 0.5).astype(np.uint8)
    if abs(shake[0]) + abs(shake[1]) > 0.3:
        M = np.float32([[1, 0, shake[0]], [0, 1, shake[1]]])
        img = cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return img


# ================================================================== frames
FL = [(t, s) for t, s in S.FLASHES]


def intro_frame(T, fi):
    rng = np.random.default_rng(300 + fi)
    i = max(j for j in range(INTRO_N) if S.CUTS[j] <= T + 1e-9)
    lt = T - S.CUTS[i]
    fk = decay(T, FL, 0.06)                                         # (FLASHES is empty: no white blinks)
    f = shot_frame(i, T, push=0.06)
    f = grade_cold(f)
    f = stickers(f, T, cold=True)
    if S.SNOW:
        f = draw_snow(f, T, 1.0)
    f = apply_trans(f, T, i)                                        # zoom / spin into the next scene
    if fk > 0.01:
        f = f + min(fk, 1.4) * (f * 1.7 + 0.42)
        f = rgb_split(f, 14 * min(fk, 1.0))
    t_cut = S.CUTS[i + 1]
    near = max(0.0, 1 - abs(T - t_cut) / 0.12) if i + 1 in S.TRANS else 0.0
    shake = rng.normal(0, 1, 2) * (4 * min(fk, 1.0) + 6 * near)
    return f, shake, 0.0


WHIP = [0, 0, 0, 0, 200, 25, 160, 270, 340, 90, 200, 0, 160, 300, 20, 250, 110, 330, 190]


def montage_frame(T, fi):
    rng = np.random.default_rng(900 + fi)
    i = max(j for j in range(NSHOT) if S.CUTS[j] <= T + 1e-9)
    lt = T - S.CUTS[i]
    rem = S.CUTS[i + 1] - T
    ch = S.SHOTS[i][1]
    ch_start = i == INTRO_N or S.SHOTS[i - 1][1] != ch
    sh = rng.normal(0, 1, 2) * (18 * np.exp(-lt / 0.08) + 2.2) * (0.4 if lt > 0.25 else 1.0)
    rot = rng.normal(0, 1) * 0.7 * np.exp(-lt / 0.09)
    punch = 1 + 0.08 * np.exp(-lt / 0.07)
    if lt >= S.B / 2:
        punch *= 1 + 0.02 * np.exp(-(lt - S.B / 2) / 0.06)
    # same-car cuts: the new shot slides in fast with a strong directional blur (reference) and the old one whips out;
    # new-car cuts (shots5.TRANS): zoom-through / spin transitions instead
    special_in = has_trans(i)
    special_out = has_trans(i + 1)
    ang = WHIP[i]
    d = np.array([np.cos(np.radians(ang)), np.sin(np.radians(ang))])
    kin = 0.0 if special_in else max(0.0, 1 - lt / 0.20) ** 2
    off = 210 * kin
    f = shot_frame(i, T, extra_zoom=punch, shift=(sh[0] - off * d[0], sh[1] - off * d[1]), rot=rot)
    if kin > 0.003:
        f = dir_blur(f, 190 * kin, ang)
    if not special_out and rem < 0.075 and i + 1 < NSHOT:          # whip-out toward the next shot
        k = 1 - rem / 0.075
        d2 = np.array([np.cos(np.radians(WHIP[i + 1])), np.sin(np.radians(WHIP[i + 1]))])
        M = np.float32([[1, 0, 90 * k * d2[0]], [0, 1, 90 * k * d2[1]]])
        f = cv2.warpAffine(f, M, (W, H), borderMode=cv2.BORDER_REFLECT)
        f = dir_blur(f, 120 * k, WHIP[i + 1])
    f = grade_warm(f, 0.006 * np.exp(-lt / 0.07))
    f = stickers(f, T)
    f = apply_trans(f, T, i)
    if S.MID_LOGO and S.LOGO_IN <= T < S.LOGO_OFF:
        dark = smoothstep(S.LOGO_DARK, S.LOGO_DARK + 0.05, T)
        f = logo_layer(f, T, S.LOGO_CY, S.LOGO_IN, dark=dark)
        if S.LOGO_DARK <= T < S.LOGO_DARK + 0.07:
            f = logo_glitch(f, rng)
    if S.EMBERS:
        f = draw_embers(f, T, smoothstep(S.T_DROP, S.T_DROP + 0.12, T))
    # no white flashes (user): impact = punch + shake + a short colour fringe
    if ch_start:
        f = rgb_split(f, 14 * np.exp(-lt / 0.09))
    else:
        f = rgb_split(f, 8 * np.exp(-lt / 0.07), vertical=(i % 2 == 1))
    return f, sh * 0.0, 0.0


def outro_frame(T, fi):
    rng = np.random.default_rng(77 + fi)
    lt = T - S.T_OUT
    dur = S.T_END - S.T_OUT
    oy = int((T * 14) % 200); ox = int(40 + 30 * np.sin(T * 0.3))
    sm = SMOKE[oy:oy + H4, ox:ox + W4]
    bg4 = np.zeros((H4, W4, 3), np.float32) + hexc('#040405')
    bg4 += (np.clip(sm * 1.3 - 0.45, 0, 1) ** 1.5)[..., None] * hexc('#3a1a0a')[None, None] * 0.9
    f = up(bg4)
    yy = np.linspace(0, 1, H, dtype=np.float32)[:, None, None]
    f = f + EMBER[None, None] * 0.10 * smoothstep(0.55, 1.0, yy)
    f = logo_layer(f, T, S.END_CY, S.T_OUT, dark=0.0, base_scale=0.95, env_k=0.0, glow_k=0.45)
    if S.EMBERS:
        f = draw_embers(f, T, 1.25)
    f = rgb_split(f, 12 * np.exp(-lt / 0.09))                      # slam: colour fringe + shake, no white flash
    t0 = dur - S.LOOP_OUT                                          # loop: the end card zooms through, then a clean
    if lt >= t0:                                                   # cut to frame 0 (on the song's loop point)
        f = zoom_fx(f, ease_in((lt - t0) / S.LOOP_OUT), W / 2, S.END_CY)
    shake = rng.normal(0, 1, 2) * 16 * np.exp(-lt / 0.09)
    return f, shake


def render(fi):
    T = S.S0 + fi / FPS
    if T < S.T_DROP:
        f, shake, bl = intro_frame(T, fi)
        return finish(f, fi, shake, band_line=bl)
    if T < S.T_OUT:
        f, shake, bl = montage_frame(T, fi)
        return finish(f, fi, shake, band_line=bl)
    f, shake = outro_frame(T, fi)
    return finish(f, fi, shake, band=False)


# ================================================================== extraction
def remove_red_sign(path, search, pole=70):
    """house rule (clean frames, no text): inpaint a red street sign (STOP) and its pole inside search (pin coords)"""
    im = cv2.imread(path)
    x0, y0, x1, y1 = search
    reg = im[y0:y1, x0:x1].astype(int)
    b, g, r = reg[..., 0], reg[..., 1], reg[..., 2]
    red = ((r > 120) & (r - g > 60) & (r - b > 50)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(red)
    if n < 2:
        return
    k = 1 + int(np.argmax(st[1:, 4]))
    x, y, w, h, a = st[k]
    if a < 120:
        return
    cx = x0 + x + w // 2
    sx0, sy0, sx1, sy1 = x0 + x - 12, y0 + y - 19, x0 + x + w + 12, y0 + y + h + 15        # sign + white rim
    # sign: copy the wall texture from above, shifted by the offset whose border matches best (stripes line up)
    best = None
    for dy in range(30, 110):
        if sy0 - dy - 8 < 0:
            break
        a_ = im[sy0 - 8:sy1 + 8, sx0 - 8:sx1 + 8].astype(np.float32)
        b_ = im[sy0 - 8 - dy:sy1 + 8 - dy, sx0 - 8:sx1 + 8].astype(np.float32)
        ring = np.ones(a_.shape[:2], bool); ring[8:-8, 8:-8] = False
        e = float(np.abs(a_ - b_)[ring].mean())
        if best is None or e < best[0]:
            best = (e, dy)
    dy = best[1]
    out = im.copy()
    patch = im[sy0 - dy - 8:sy1 - dy + 8, sx0 - 8:sx1 + 8].astype(np.float32)
    fm = np.zeros(patch.shape[:2], np.float32); fm[8:-8, 8:-8] = 1
    fm = cv2.GaussianBlur(fm, (0, 0), 3)[..., None]
    dst = out[sy0 - 8:sy1 + 8, sx0 - 8:sx1 + 8].astype(np.float32)
    out[sy0 - 8:sy1 + 8, sx0 - 8:sx1 + 8] = np.clip(dst * (1 - fm) + patch * fm, 0, 255).astype(np.uint8)
    # pole: thin inpaint
    m = np.zeros(im.shape[:2], np.uint8)
    cv2.rectangle(m, (cx - 6, sy1 - 2), (cx + 6, y0 + y + h + pole), 255, -1)
    out = cv2.inpaint(out, m, 6, cv2.INPAINT_TELEA)
    cv2.imwrite(path, out, [cv2.IMWRITE_JPEG_QUALITY, 96])


def blank_plate(path, box, thr=160, delta=40):
    """house rule (clean frames, no text): blank a white / lit plate (dealer plate or licence plate) inside box (pin
    coords). The plate = the biggest plate-shaped bright blob; its inside is replaced by the plate's own shading,
    estimated from the non-letter pixels (normalised blur), so it reads as a clean blank plate."""
    im = cv2.imread(path)
    x0, y0, x1, y1 = box
    reg = im[y0:y1, x0:x1]
    g = cv2.cvtColor(reg, cv2.COLOR_BGR2GRAY).astype(np.float32)
    bright = cv2.morphologyEx((g > thr).astype(np.uint8), cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(bright)
    cand = []
    for j in range(1, n):
        bw, bh = st[j, 2], st[j, 3]
        if not (1.6 < bw / max(1, bh) < 6.5 and 24 < bw < 260 and bh > 8):
            continue
        cnts, _ = cv2.findContours((lab == j).astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        hull = cv2.convexHull(max(cnts, key=cv2.contourArea))
        if cv2.contourArea(hull) > 0.70 * bw * bh:          # plate-shaped (letters make holes, the hull doesn't care)
            cand.append((st[j, 4], j, hull))
    if not cand:
        return False
    _, k, hull = max(cand, key=lambda c: c[0])
    hm = np.zeros(g.shape, np.uint8)
    cv2.fillConvexPoly(hm, hull, 1)
    hm = cv2.erode(hm, np.ones((5, 5), np.uint8))
    inside = hm > 0
    vals = g[inside & (g > thr)]
    if len(vals) < 30:
        return False
    text = (inside & (g < np.median(vals) - delta)).astype(np.uint8)
    text = cv2.dilate(text, np.ones((3, 3), np.uint8)) > 0
    w = (inside & ~text).astype(np.float32)
    sig = max(3.0, 0.30 * st[k, 3])
    f = reg.astype(np.float32)
    num = cv2.GaussianBlur(f * w[..., None], (0, 0), sig)
    den = cv2.GaussianBlur(w, (0, 0), sig)[..., None]
    smooth = num / np.maximum(den, 1e-3)
    a = cv2.GaussianBlur(hm.astype(np.float32), (0, 0), 0.8)[..., None]
    noise = np.random.default_rng(1).normal(0, 1.5, f.shape).astype(np.float32)
    reg[:] = np.clip(f * (1 - a) + (smooth + noise) * a, 0, 255).astype(np.uint8)
    cv2.imwrite(path, im, [cv2.IMWRITE_JPEG_QUALITY, 96])
    return True


def extract(only=None):
    for i, (nm, ch, clip, src, z, cx, cy, sp) in enumerate(S.SHOTS):
        if only and nm not in only:
            continue
        dur = (S.CUTS[i + 1] - S.CUTS[i]) * sp + 0.12
        d = f'{SEG}/{nm}'
        os.makedirs(d, exist_ok=True)
        for fn in os.listdir(d):
            os.remove(f'{d}/{fn}')
        x0, y0, x1, y1 = S.PBOX
        if nm in S.INTERP:
            vf = f'crop={x1 - x0}:{y1 - y0}:{x0}:{y0},fps=30,minterpolate=fps=120:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1'
        else:
            vf = f'crop={x1 - x0}:{y1 - y0}:{x0}:{y0},fps=60'
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{src:.3f}', '-i', f'{WORK}/clips/{clip}.mp4', '-t', f'{dur:.3f}',
                        '-vf', vf, '-q:v', '2', f'{d}/%04d.jpg'], check=True)
        if nm in getattr(S, 'CLEAN', {}):
            for fn in sorted(os.listdir(d)):
                remove_red_sign(f'{d}/{fn}', S.CLEAN[nm])
        if nm in getattr(S, 'PLATES', {}):
            ok = 0
            for fn in sorted(os.listdir(d)):
                for (bx0, by0, bx1, by1, thr, delta) in S.PLATES[nm]:
                    ok += blank_plate(f'{d}/{fn}', (bx0, by0, bx1, by1), thr, delta)
            print(nm, 'plates blanked in', ok, 'frames')
        print(nm, clip, f'{src:.2f}-{src + dur:.2f}', len(os.listdir(d)), 'frames', flush=True)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'extract':
        extract(sys.argv[2:])
    elif mode == 'frames':
        os.makedirs(f'{WORK}/check5', exist_ok=True)
        for tok in sys.argv[2:]:
            T = float(tok); fi = int(round((T - S.S0) * FPS))
            t1 = time.time(); img = render(fi)
            print(f'T={T} fi={fi} {time.time() - t1:.2f}s', file=sys.stderr)
            cv2.imwrite(f'{WORK}/check5/N5_{T:06.3f}.png', cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    elif mode in ('range', 'video'):
        out = sys.argv[2]
        if mode == 'range':
            f0 = int(round((float(sys.argv[3]) - S.S0) * FPS)); f1 = int(round((float(sys.argv[4]) - S.S0) * FPS))
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
