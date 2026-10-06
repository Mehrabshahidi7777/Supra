"""Night 4 — 'slide your finger along the rhythm' (heavier version of the user's reference).

The dot moves exactly like the reference's white dot: one slide per beat along the bottom and the right edge
(top-right -> bottom-right -> bottom-left -> bottom-right -> top-right ...). The viewer's finger follows it,
and the finger is what brings the cars:
  * intro (0 -> drop): neon orb + swipe trail, lane rails, corner targets (next one lit), shockwave + sparks +
    shake on every landing, smoky stage lit by the orb, riser speed lines; the last slide paints the first car in
    from the dot and lands on the drop (flash, big shockwave, glitch);
  * montage: a smaller dot keeps sliding on every beat and each swipe paints the next car in from the dot
    (brush reveal with a neon edge); landing = cut: punch, shake, neon edges, flash / glitch variations;
  * outro: the last swipe paints in MEHRAB.7w7 (font flicker), the dot rests top-right, rails + text come back
    -> the last frame equals the first one (seamless loop).

  WORK=$WORK python3 render4.py extract                 # per-shot frames -> $WORK/seg/<shot>/ (with pre-roll)
  WORK=$WORK python3 render4.py frames 0.5 7.8 8.2       # stills -> $WORK/check/N4_<T>.png
  WORK=$WORK python3 render4.py range out.mp4 0.08 9.0   # quick preview of a time range
  WORK=$WORK python3 render4.py video $WORK/n4_noaudio.mp4
"""
import sys, os, time, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
KIT = os.path.normpath(os.path.join(HERE, '..', '..', 'kit'))
WORK = os.environ.get('WORK', '/home/claude/work_edit')
sys.path.insert(0, KIT)
sys.path.insert(0, HERE)
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont
from lib import hexc, smoothstep, ease_out_cubic, fractal_noise, text_mask, FONT, FONT_REG
from framing import crop_window
import shots as S

cv2.setNumThreads(1)
W, H = 1080, 1920
FPS = int(os.environ.get('N4_FPS', '60'))      # 60 fps master (house rule: smooth); 30 for quick tests
W4, H4 = W // 4, H // 4
NF = int(round((S.T_END - S.S0) * FPS))
ACC = hexc(S.ACCENT)
WHITE = np.ones(3, np.float32)
POPPINS = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
NSHOT = len(S.SHOTS)


def smoother(t):
    t = np.clip(t, 0, 1)
    return t * t * t * (t * (t * 6 - 15) + 10)


def mix(a, b, k):
    return a * (1 - k) + b * k


def col(c):
    return tuple(float(v) for v in c)


def P16(p):
    return (int(round(p[0] * 16)), int(round(p[1] * 16)))


def Q16(p):          # full-res point -> quarter-res fixed point
    return (int(round(p[0] / 4 * 16)), int(round(p[1] / 4 * 16)))


# ================================================================== the finger path
TR, BR, BL = (np.array(p, np.float32) for p in (S.TR, S.BR, S.BL))
_END = {'down': BR, 'left': BL, 'right': BR, 'up': TR}
NMOVE = 24                                   # move 24 lands on the outro
CORNER = [TR]
for _k in range(1, NMOVE + 1):
    CORNER.append(_END[S.MOVES[(_k - 1) % 4]])
LAND = [S.beat(k) for k in range(1, NMOVE + 1)]          # LAND[k-1] = landing time of move k
NI = S.INTRO_BEATS


def travel(k):
    return S.TRAVEL_INTRO if k <= NI else S.TRAVEL_MONT


def move_state(T):
    """(k, q): move k in progress with progress q in [0,1); or (k, None) resting after move k"""
    for k in range(1, NMOVE + 1):
        tb = S.beat(k)
        t0 = tb - travel(k)
        if T < t0:
            return k - 1, None
        if T < tb:
            return k, (T - t0) / (tb - t0)
    return NMOVE, None


def dot_pos(T):
    k, q = move_state(T)
    if q is None:
        return CORNER[k].copy()
    e = smoother(q)
    return CORNER[k - 1] * (1 - e) + CORNER[k] * e


def decay(T, times, tau, amp=1.0):
    v = 0.0
    for t in times:
        dt = T - t
        if 0 <= dt < 7 * tau:
            v += amp * np.exp(-dt / tau)
    return v


# ================================================================== static stuff
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
_rr = np.hypot((xx - W / 2) / (W * 0.62), (yy - H / 2) / (H * 0.56))
VIG = (1 - 0.70 * smoothstep(0.35, 1.15, _rr))[..., None].astype(np.float32)
_rr2 = np.hypot((xx - W / 2) / (W * 0.62), (yy - H / 2) / (H * 0.58))
EDGE = smoothstep(0.55, 1.15, _rr2)[..., None].astype(np.float32)
TOPDARK = (0.80 + 0.20 * smoothstep(0.0, 0.36, yy / H))[..., None].astype(np.float32)
del yy, xx, _rr, _rr2
y4, x4 = np.mgrid[0:H4, 0:W4].astype(np.float32)
x4f = x4 * 4 + 2
y4f = y4 * 4 + 2
SMK_A = fractal_noise(640, 360, 31, octaves=5, base=4).astype(np.float32)
SMK_B = fractal_noise(640, 360, 32, octaves=4, base=3).astype(np.float32)
GRAIN = [np.random.default_rng(40 + i).normal(0, 1, (H, W)).astype(np.float16) for i in range(6)]
BASE4 = np.zeros((H4, W4, 3), np.float32) + hexc('#020309')
BASE4 += hexc('#06101c') * smoothstep(1.0, 0.0, np.abs(y4f - 1050) / 1100)[..., None]

# dust (closed form)
NDUST = 90
_r = np.random.default_rng(7)
D_X0 = _r.uniform(0, W, NDUST); D_Y0 = _r.uniform(0, H, NDUST)
D_VX = _r.uniform(-12, 12, NDUST); D_VY = _r.uniform(10, 45, NDUST)
D_SZ = _r.uniform(0.8, 2.6, NDUST); D_BR = _r.uniform(0.10, 0.45, NDUST)
D_TW = _r.uniform(1.0, 4.0, NDUST); D_PH = _r.uniform(0, 6.28, NDUST)

# sparks per landing (big burst on the drop, small ones in the montage)
SPARKS = []
for _k in range(1, NMOVE + 1):
    rs = np.random.default_rng(500 + _k)
    if _k == NI:
        n, sp, life = 48, rs.uniform(650, 1900, 48), rs.uniform(0.40, 0.95, 48)
    elif _k < NI:
        n, sp, life = 16, rs.uniform(320, 980, 16), rs.uniform(0.22, 0.50, 16)
    else:
        n, sp, life = 9, rs.uniform(260, 700, 9), rs.uniform(0.18, 0.36, 9)
    ang = rs.uniform(0, 2 * np.pi, n)
    x0, y0 = CORNER[_k]
    SPARKS.append((LAND[_k - 1], x0, y0, np.cos(ang) * sp, np.sin(ang) * sp - 150, life))
TAU_S, G_S = 0.20, 1100.0


def spark_xy(x0, y0, vx, vy, t):
    k = TAU_S * (1 - np.exp(-t / TAU_S))
    return x0 + vx * k, y0 + vy * k + 0.5 * G_S * t * t


# riser speed lines (radial from screen centre)
NSL = 46
_r2 = np.random.default_rng(11)
SL_ANG = _r2.uniform(0, 2 * np.pi, NSL); SL_PH = _r2.random(NSL); SL_SP = _r2.uniform(1.2, 2.4, NSL)
SL_LEN = _r2.uniform(140, 360, NSL); SL_BR = _r2.uniform(0.4, 1.0, NSL)


# ================================================================== text + watermark
def text_block(lines, size, font=POPPINS, lh=1.18, track=0.0, cx=W / 2):
    f = ImageFont.truetype(font, size)
    hh = int(size * lh * len(lines) + size)
    im = Image.new('L', (W, hh), 0)
    d = ImageDraw.Draw(im)
    for i, ln in enumerate(lines):
        wd = sum(f.getlength(c) for c in ln) + track * (len(ln) - 1)
        x = cx - wd / 2
        for c in ln:
            d.text((x, int(size * 0.25 + i * size * lh)), c, font=f, fill=255)
            x += f.getlength(c) + track
    m = np.asarray(im, np.float32) / 255
    ys = np.where(m.max(1) > 0)[0]
    return m[max(0, ys.min() - 40):ys.max() + 40]


TXT = text_block(['slide your finger', 'along the rhythm'], 62, track=1.0, cx=470)
TXT_CY = 945
TXT_SH = cv2.GaussianBlur(TXT, (0, 0), 6)

_wm = Image.new('L', (W, 110), 0); _d = ImageDraw.Draw(_wm)
_f = ImageFont.truetype(FONT_REG, 44); _tx = 'MEHRAB.7w7'
_tw = sum(_f.getlength(c) for c in _tx) + 3 * (len(_tx) - 1); _xx = (W - _tw) / 2
for c in _tx:
    _d.text((_xx, 30), c, font=_f, fill=255); _xx += _f.getlength(c) + 3
WM = np.asarray(_wm, np.float32) / 255
WM_SH = cv2.GaussianBlur(WM, (0, 0), 4)
_wr = np.where(WM.max(1) > 0.5)[0]
WM_Y = int(S.WM_CY - (_wr.min() + _wr.max()) / 2)   # line centred on S.WM_CY


def put_mask(f, m, cy, colr, alpha=1.0, scale=1.0, shadow=None, sh_k=0.6, cx=470):
    h = m.shape[0]
    if scale != 1.0:
        M = np.float32([[scale, 0, cx * (1 - scale)], [0, scale, h / 2 * (1 - scale)]])
        m = cv2.warpAffine(m, M, (W, h), flags=cv2.INTER_LINEAR)
        if shadow is not None:
            shadow = cv2.warpAffine(shadow, M, (W, h), flags=cv2.INTER_LINEAR)
    y0 = int(cy - h / 2)
    y0c, y1c = max(0, y0), min(H, y0 + h)
    reg = f[y0c:y1c]
    mm = m[y0c - y0:y1c - y0, :, None] * alpha
    if shadow is not None:
        reg *= 1 - shadow[y0c - y0:y1c - y0, :, None] * sh_k * alpha
    reg[:] = reg * (1 - mm) + colr[None, None] * mm


def glow_from_block(G4, m, cy, colr, k):
    h = m.shape[0]
    y0 = int(cy - h / 2)
    full = np.zeros((H, W), np.float32)
    y0c, y1c = max(0, y0), min(H, y0 + h)
    full[y0c:y1c] = m[y0c - y0:y1c - y0]
    G4 += cv2.resize(full, (W4, H4), interpolation=cv2.INTER_AREA)[..., None] * colr[None, None] * k


def blur_glow(G4):
    return (cv2.GaussianBlur(G4, (0, 0), 1.3) * 1.0 + cv2.GaussianBlur(G4, (0, 0), 4.5) * 0.85
            + cv2.GaussianBlur(G4, (0, 0), 13) * 0.75)


def up(a4):
    return cv2.resize(a4, (W, H), interpolation=cv2.INTER_LINEAR)


def soft_clip(f):
    return np.where(f < 0.82, f, 0.82 + 0.18 * np.tanh((f - 0.82) / 0.18))


def finish(f, fi, shake=(0.0, 0.0), grain=0.018):
    reg = f[WM_Y:WM_Y + 110]
    reg[:] = reg * (1 - WM_SH[..., None] * 0.55)
    reg[:] = reg * (1 - WM[..., None] * 0.95) + WM[..., None] * 0.95
    f = f + (GRAIN[fi % 6].astype(np.float32) * grain)[..., None]
    img = (np.clip(soft_clip(f), 0, 1) * 255 + 0.5).astype(np.uint8)
    if abs(shake[0]) + abs(shake[1]) > 0.3:
        M = np.float32([[1, 0, shake[0]], [0, 1, shake[1]]])
        img = cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
    return img


# ================================================================== drawing layers
def draw_orb(C, G4, T, scale=1.0, inten=1.0, R0=30, pos_fn=dot_pos, ring=True):
    R = R0 * scale
    nsub = 8
    subs = np.array([pos_fn(T - j / (FPS * nsub)) for j in range(nsub)], np.float32)
    x0 = int(max(0, subs[:, 0].min() - R - 4)); x1 = int(min(W, subs[:, 0].max() + R + 5))
    y0 = int(max(0, subs[:, 1].min() - R - 4)); y1 = int(min(H, subs[:, 1].max() + R + 5))
    if x1 > x0 and y1 > y0:          # motion-blurred core (additive soft discs)
        py, px = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        acc = np.zeros(py.shape, np.float32)
        for q in subs:
            acc += np.clip(R - np.hypot(px - q[0], py - q[1]) + 0.7, 0, 1)
        C[y0:y1, x0:x1] += (acc * inten * 1.15 / nsub)[..., None]
    p = pos_fn(T)
    tail = [pos_fn(T - j * 0.018) for j in range(16)]       # swipe trail
    for j in range(len(tail) - 1):
        a = (1 - j / 15) ** 1.6
        th = max(1, int(round(R / 4 * 1.7 * (1 - j / 16))))
        cv2.line(G4, Q16(tail[j]), Q16(tail[j + 1]), col(mix(ACC, WHITE, 0.3) * 1.3 * a * inten), th, cv2.LINE_AA, shift=4)
    cv2.circle(G4, Q16(p), int(R / 4 * 2.3 * 16), col((ACC * 1.5 + 0.5) * inten), -1, cv2.LINE_AA, shift=4)
    cv2.ellipse(G4, Q16(p), (int(42 * scale * 16), int(1.0 * 16)), 0, 0, 360, col(mix(ACC, WHITE, 0.25) * 0.35 * inten), -1, cv2.LINE_AA, shift=4)
    if ring:     # thin 'touch here' ring that breathes
        rr_ = R + 24 * scale + 6 * np.sin(T * 9.0)
        cv2.circle(C, P16(p), int(rr_ * 16), col(mix(ACC, WHITE, 0.5) * 0.30 * inten), 2, cv2.LINE_AA, shift=4)
    return p


def draw_ring(C, G4, cx, cy, t, dur, r0, r1, k=1.0, width=4):
    if t < 0 or t > dur:
        return
    q = t / dur
    r = r0 + (r1 - r0) * ease_out_cubic(q)
    a = (1 - q) ** 1.5 * k
    c_ = mix(WHITE, ACC, min(1, q * 1.5))
    cv2.circle(C, P16((cx, cy)), int(r * 16), col(c_ * a), max(1, int(width * (1 - 0.6 * q))), cv2.LINE_AA, shift=4)
    cv2.circle(G4, Q16((cx, cy)), int(r / 4 * 16), col(ACC * 1.4 * a), 2, cv2.LINE_AA, shift=4)


def draw_sparks(C, G4, T, ks, k=1.0):
    for kk in ks:
        ta, x0, y0, vx, vy, life = SPARKS[kk - 1]
        t = T - ta
        if t < 0 or t > life.max():
            continue
        alive = t < life
        xa, ya = spark_xy(x0, y0, vx[alive], vy[alive], t)
        xb, yb = spark_xy(x0, y0, vx[alive], vy[alive], max(0, t - 0.03))
        age = t / life[alive]
        for j in range(len(xa)):
            a = (1 - age[j]) ** 1.2 * k
            c_ = mix(WHITE * 1.3, ACC, min(1, age[j] * 1.6)) * a
            cv2.line(C, P16((xb[j], yb[j])), P16((xa[j], ya[j])), col(c_), 2, cv2.LINE_AA, shift=4)
            cv2.line(G4, Q16((xb[j], yb[j])), Q16((xa[j], ya[j])), col(c_ * 1.2), 1, cv2.LINE_AA, shift=4)


def draw_dust(C, T, k=1.0):
    x = (D_X0 + D_VX * T + 14 * np.sin(T * 0.7 + D_PH)) % W
    y = (D_Y0 - D_VY * T) % H
    br = D_BR * (0.55 + 0.45 * np.sin(T * D_TW + D_PH)) * k
    for j in range(NDUST):
        cv2.circle(C, P16((x[j], y[j])), int(D_SZ[j] * 16), col(mix(WHITE, ACC, 0.5) * br[j]), -1, cv2.LINE_AA, shift=4)


def draw_rails(C, G4, T, alpha=1.0):
    """faint lanes along the finger path; the stretch just slid lights up; corner targets, the next one lit"""
    if alpha < 0.01:
        return
    for a_, b_ in ((BL, BR), (BR, TR)):
        cv2.line(C, P16(a_), P16(b_), col(mix(ACC, WHITE, 0.3) * 0.10 * alpha), 2, cv2.LINE_AA, shift=4)
        cv2.line(G4, Q16(a_), Q16(b_), col(ACC * 0.22 * alpha), 1, cv2.LINE_AA, shift=4)
    k, q = move_state(T)
    if q is not None:                        # lit stretch behind the dot
        p = dot_pos(T)
        cv2.line(C, P16(CORNER[k - 1]), P16(p), col(mix(ACC, WHITE, 0.5) * 0.55 * alpha), 3, cv2.LINE_AA, shift=4)
        cv2.line(G4, Q16(CORNER[k - 1]), Q16(p), col(ACC * 0.9 * alpha), 2, cv2.LINE_AA, shift=4)
        nxt = CORNER[k]
    else:
        if k >= 1:                           # the stretch fades after landing
            fade = np.exp(-(T - LAND[k - 1]) / 0.25)
            if fade > 0.02:
                cv2.line(C, P16(CORNER[k - 1]), P16(CORNER[k]), col(mix(ACC, WHITE, 0.5) * 0.55 * fade * alpha), 3, cv2.LINE_AA, shift=4)
                cv2.line(G4, Q16(CORNER[k - 1]), Q16(CORNER[k]), col(ACC * 0.9 * fade * alpha), 2, cv2.LINE_AA, shift=4)
        nxt = CORNER[min(k + 1, NMOVE)]
    pulse = 0.5 + 0.5 * np.cos((T - S.B0) / S.B * 2 * np.pi)
    for c_ in (TR, BR, BL):
        is_next = np.allclose(c_, nxt)
        a = (0.55 + 0.35 * pulse if is_next else 0.14) * alpha
        rr_ = 46 + (8 * pulse if is_next else 0)
        cv2.circle(C, P16(c_), int(rr_ * 16), col(mix(ACC, WHITE, 0.4) * a), 2, cv2.LINE_AA, shift=4)
        cv2.circle(G4, Q16(c_), int(rr_ / 4 * 16), col(ACC * a * 1.1), 1, cv2.LINE_AA, shift=4)


def smoke_bg(T, light_xy, light_k, beat_k, dark=1.0):
    oy = int((T * 9) % 160); ox = int(40 + 30 * np.sin(T * 0.21))
    a = SMK_A[oy:oy + H4, ox:ox + W4]
    oy2 = int((T * 5 + 60) % 160); ox2 = int(50 - 30 * np.sin(T * 0.17))
    b = SMK_B[oy2:oy2 + H4, ox2:ox2 + W4]
    sm = np.clip(a * 1.25 - 0.35, 0, 1) ** 1.6 * (0.6 + 0.8 * b)
    lx, ly = light_xy
    L = np.exp(-((x4f - lx) ** 2 + (y4f - ly) ** 2) / (2 * 330.0 ** 2))
    lev = 0.10 + 0.55 * L * light_k + 0.10 * beat_k
    return BASE4 * dark + sm[..., None] * lev[..., None] * mix(ACC, WHITE, 0.15)[None, None] * 0.55 * dark


def reveal_mask(T, k, q, power, rmax=1480.0, r0=26.0, feather=42.0):
    """brush reveal painted from the finger: region within r(q) of the stretch slid so far (quarter res)"""
    A = CORNER[k - 1]
    D = dot_pos(T)
    d = D - A
    L2 = float(d @ d)
    if L2 < 1e-6:
        t = np.zeros_like(x4f)
    else:
        t = np.clip(((x4f - A[0]) * d[0] + (y4f - A[1]) * d[1]) / L2, 0, 1)
    dist = np.hypot(x4f - (A[0] + t * d[0]), y4f - (A[1] + t * d[1]))
    r = r0 + (rmax - r0) * q ** power
    m4 = smoothstep(r + feather, r - feather, dist)
    ring4 = np.exp(-((dist - r) / 16.0) ** 2) * (1 - q ** 8)
    return up(m4.astype(np.float32))[..., None], up(ring4.astype(np.float32))[..., None]


def blend_reveal(f_out, f_in, T, k, q, power, ring_k=1.0):
    m, ring = reveal_mask(T, k, q, power)
    f = f_out * (1 - m) + f_in * m
    return f + ring * mix(ACC, WHITE, 0.35)[None, None] * 0.95 * ring_k


# ================================================================== intro
BEATS_INTRO = [S.beat(k) for k in range(0, NI)]


def intro_frame(T, fi, orb_out=None):
    """orb_out: pass a list to get the orb layers back instead of composited (drawn on top of the car reveal)"""
    rng = np.random.default_rng(300 + fi)
    k, q = move_state(T)
    landed = k if q is None else k - 1
    energy = landed / NI
    rise = smoothstep(S.T_RISE, S.T_DROP, T)
    land = decay(T, LAND[:NI - 1], 0.10)
    bk = decay(T, BEATS_INTRO + LAND[:NI - 1], 0.16)
    p = dot_pos(T)
    G4 = np.zeros((H4, W4, 3), np.float32)
    C = np.zeros((H, W, 3), np.float32)
    draw_rails(C, G4, T, 0.85 + 0.6 * energy + 0.8 * rise)
    for kk in range(1, NI):                                   # landing shockwaves
        draw_ring(C, G4, *CORNER[kk], T - LAND[kk - 1], 0.42, 34, 260, 0.9)
    draw_ring(C, G4, *TR, T - S.beat(0), 0.42, 34, 220, 0.6)  # beat 0 ping at the start point
    draw_sparks(C, G4, T, range(1, NI))
    G4o = np.zeros((H4, W4, 3), np.float32)
    Co = np.zeros((H, W, 3), np.float32)
    draw_orb(Co, G4o, T, 1 + 0.4 * rise ** 2 + 0.22 * land + 0.10 * energy, 1.0 + 0.5 * rise)
    if orb_out is None:
        G4 += G4o; C += Co
    else:
        orb_out.append((G4o, Co))
    draw_dust(C, T, 1 + 0.6 * bk)
    if rise > 0.01:                                           # riser speed lines
        cx, cy = 540, 960
        for j in range(NSL):
            ph = (SL_PH[j] + (T - S.T_RISE) * SL_SP[j] * (0.6 + 1.4 * rise)) % 1.0
            r0 = 260 + 1300 * ph ** 1.6
            r1 = r0 + SL_LEN[j] * (0.5 + rise)
            d = np.array([np.cos(SL_ANG[j]), np.sin(SL_ANG[j])])
            a = SL_BR[j] * rise ** 1.4 * 0.55 * smoothstep(0.0, 0.15, ph)
            c_ = mix(ACC, WHITE, 0.5) * a
            pa, pb = (cx + d[0] * r0, cy + d[1] * r0), (cx + d[0] * r1, cy + d[1] * r1)
            cv2.line(C, P16(pa), P16(pb), col(c_), 2, cv2.LINE_AA, shift=4)
            cv2.line(G4, Q16(pa), Q16(pb), col(ACC * a), 1, cv2.LINE_AA, shift=4)
    tp = 1 + 0.03 * decay(T, BEATS_INTRO + LAND[:NI - 1], 0.09)
    glow_from_block(G4, TXT, TXT_CY, ACC, 0.30 + 0.30 * min(bk, 1.2))
    suck = smoothstep(S.T_DROP - 0.16, S.T_DROP, T)
    bg4 = smoke_bg(T, p, 1.0 + 0.8 * land + 1.2 * rise, bk, dark=1 - 0.5 * suck)
    f = up(bg4 + blur_glow(G4)) + C
    put_mask(f, TXT, TXT_CY, WHITE * 0.97, 1.0, tp, shadow=TXT_SH)
    f *= VIG
    shake = rng.normal(0, 1, 2) * (7 * land + 9 * rise ** 2)
    return f, shake


# ================================================================== footage
SEG = f'{WORK}/seg' if FPS == 30 else f'{WORK}/seg{FPS}'


def pre(i):
    return S.PRE.get(S.SHOTS[i][0], S.TRAVEL_MONT)


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
        if len(_cache) > 8:
            _cache.clear()
        _cache[key] = cv2.cvtColor(cv2.imread(f'{SEG}/{name}/{lst[idx]}'), cv2.COLOR_BGR2RGB)
    return _cache[key]


def shot_frame(i, T, extra_zoom=1.0, shift=(0, 0), rot=0.0):
    nm, car, clip, src, z, cx, cy, box = S.SHOTS[i]
    t0, t1 = S.CUTS[i], S.CUTS[i + 1]
    sp = S.SPEED.get(nm, 1.0)
    im = load(nm, (T - (t0 - pre(i))) * FPS * sp)
    prog = np.clip((T - t0) / (t1 - t0), 0, 1)
    zz = z * (1 + 0.05 * (prog * prog * (3 - 2 * prog))) * extra_zoom
    X, Y, ww, wh = crop_window(im.shape, zz, cx, cy)
    s = W / ww
    M = cv2.getRotationMatrix2D((X, Y), rot, s)
    M[0, 2] += W / 2 - X + shift[0]
    M[1, 2] += H / 2 - Y + shift[1]
    return cv2.warpAffine(im, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT).astype(np.float32) / 255.0


def zoom_blur(img, amount, n=6):
    if amount < 0.005:
        return img
    h, w = img.shape[:2]
    sm = cv2.resize(img, (w // 2, h // 2), interpolation=cv2.INTER_AREA)
    acc = np.zeros_like(sm)
    for k in range(n):
        M = cv2.getRotationMatrix2D((w / 4, h / 4), 0, 1 + amount * k / (n - 1))
        acc += cv2.warpAffine(sm, M, (w // 2, h // 2), borderMode=cv2.BORDER_REFLECT)
    return cv2.resize(acc / n, (w, h), interpolation=cv2.INTER_LINEAR)


_x = np.arange(256) / 255.0
_c = 1 / (1 + np.exp(-(_x - 0.5) * 6.4))
_c = (_c - _c[0]) / (_c[-1] - _c[0])
_c = 0.65 * _c + 0.35 * _x
_c = np.clip((_c - 0.04) / 0.96, 0, 1) ** 1.10
LUT = (_c * 255).astype(np.uint8)


def grade(f, ca=0.0):
    u8 = cv2.LUT((np.clip(f, 0, 1) * 255).astype(np.uint8), LUT)
    f = u8.astype(np.float32) / 255.0
    g = f.mean(2, keepdims=True)
    f = np.clip(g + (f - g) * 1.30, 0, 1)
    f = f * TOPDARK
    sm = cv2.resize(f, (W // 6, H // 6), interpolation=cv2.INTER_AREA)
    bl = cv2.resize(cv2.GaussianBlur(sm, (0, 0), 2.2), (W, H), interpolation=cv2.INTER_LINEAR)
    f = f * (1 - EDGE * 0.85) + bl * (EDGE * 0.85)
    f = f + 0.35 * (f - cv2.GaussianBlur(f, (0, 0), 1.3))
    a = 0.0025 + ca
    for ch, sg in ((0, 1), (2, -1)):
        M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, 1 + sg * a)
        f[..., ch] = cv2.warpAffine(np.ascontiguousarray(f[..., ch]), M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return f


def rgb_split(f, amt, vertical=False):
    if amt < 0.5:
        return f
    o = f.copy()
    d = (0, amt) if vertical else (amt, 0)
    M1 = np.float32([[1, 0, d[0]], [0, 1, d[1]]]); M2 = np.float32([[1, 0, -d[0]], [0, 1, -d[1]]])
    o[..., 0] = cv2.warpAffine(np.ascontiguousarray(f[..., 0]), M1, (W, H), borderMode=cv2.BORDER_REFLECT)
    o[..., 2] = cv2.warpAffine(np.ascontiguousarray(f[..., 2]), M2, (W, H), borderMode=cv2.BORDER_REFLECT)
    return o


def glitch(f, rng, n=7, amp=60):
    o = f.copy()
    for _ in range(n):
        y = rng.integers(0, H - 40); h = rng.integers(12, 90)
        o[y:y + h] = np.roll(o[y:y + h], int(rng.normal(0, amp)), axis=1)
        if rng.random() < 0.4:
            o[y:y + h] *= mix(WHITE, ACC, 0.6)[None, None] * 1.3
    return o


def neon_edges(f, k):
    """the frame's own lines light up in neon on the beat (Sobel edges at half res + bloom)"""
    if k < 0.02:
        return f
    g = cv2.GaussianBlur(cv2.resize(f.mean(2), (W // 2, H // 2), interpolation=cv2.INTER_AREA), (0, 0), 1.0)
    e = np.hypot(cv2.Sobel(g, cv2.CV_32F, 1, 0, ksize=3), cv2.Sobel(g, cv2.CV_32F, 0, 1, ksize=3))
    e = np.clip((e - np.percentile(e, 88)) / (np.percentile(e, 99.3) - np.percentile(e, 88) + 1e-6), 0, 1)
    gl = up(cv2.GaussianBlur(cv2.resize(e, (W4, H4), interpolation=cv2.INTER_AREA), (0, 0), 3.0))
    e = up(e)
    return f * (1 - 0.35 * k) + (e[..., None] * mix(ACC, WHITE, 0.45) * 1.1 + gl[..., None] * ACC * 1.4) * k


def leak(i, lt):
    ang = [0.6, 2.4, 1.1, 2.0][i % 4]
    d = (x4f * np.cos(ang) + y4f * np.sin(ang)) / 2200.0
    pos = -0.55 + 1.6 * (lt / S.B)
    band = np.exp(-((d - pos) / 0.10) ** 2) + 0.5 * np.exp(-((d - pos + 0.18) / 0.05) ** 2)
    return up(band.astype(np.float32))[..., None] * mix(ACC, WHITE, 0.35)[None, None]


def shot_graded(i, T, fi):
    """shot i at time T, graded; cut effects only once it has landed (T >= its cut)"""
    rng = np.random.default_rng(900 + fi * 31 + i)
    lt = T - S.CUTS[i]
    mv = S.MOVES[(NI + i - 1) % 4]          # the slide that brought this shot
    if lt < 0:
        return grade(shot_frame(i, T)) * VIG
    sh = rng.normal(0, 1, 2) * (18 * np.exp(-lt / 0.08) + 2.5) * (0.35 if lt > 0.25 else 1.0)
    rot = rng.normal(0, 1) * 0.6 * np.exp(-lt / 0.09)
    punch = 1 + 0.09 * np.exp(-lt / 0.07)
    if lt >= S.B / 2:
        punch *= 1 + 0.022 * np.exp(-(lt - S.B / 2) / 0.06)
    f = shot_frame(i, T, extra_zoom=punch, shift=sh, rot=rot)
    if mv == 'up' and lt < 0.12:
        f = zoom_blur(f, 0.20 * (1 - lt / 0.12))
    f = grade(f, 0.006 * np.exp(-lt / 0.07))
    ne = (0.95 if i % 2 == 0 else 0.55) * np.exp(-lt / 0.10)
    if lt >= S.B / 2:
        ne += 0.35 * np.exp(-(lt - S.B / 2) / 0.08)
    if i > 0:
        f = neon_edges(f, ne)
    if i % 2 == 1:
        f = f + leak(i, lt) * 0.22
    f = f * (1 + 0.10 * np.exp(-lt / 0.10)) + mix(ACC, WHITE, 0.3)[None, None] * 0.05 * np.exp(-lt / 0.12)
    if i == 0:                                    # the drop
        G4 = np.zeros((H4, W4, 3), np.float32)
        C = np.zeros((H, W, 3), np.float32)
        draw_ring(C, G4, *CORNER[NI], lt, 0.6, 40, 1600, 1.4, 7)
        draw_ring(C, G4, *CORNER[NI], lt - 0.06, 0.55, 30, 950, 0.9, 4)
        draw_sparks(C, G4, T, [NI], 1.2)
        f = f + up(blur_glow(G4)) + C + 1.15 * np.exp(-lt / 0.06)
        if lt < 0.12:
            f = glitch(f, rng)
        f = rgb_split(f, 28 * np.exp(-lt / 0.10))
    else:
        if mv == 'right':
            f = f + 0.85 * np.exp(-lt / 0.055)
        if mv == 'left' and lt < 0.10:
            f = glitch(f, rng, 9, 80)
        f = rgb_split(f, 16 * np.exp(-lt / 0.08), vertical=mv in ('up', 'down'))
    return f * VIG


# ================================================================== outro
FLICK_FONTS = [FONT, '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf',
               '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyreheroscn-bold.otf',
               '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrechorus-mediumitalic.otf',
               POPPINS, '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
               '/usr/share/texmf/fonts/opentype/public/lm/lmroman10-bold.otf',
               '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyreadventor-bold.otf']
FLICK = []
for _i, _fp in enumerate(FLICK_FONTS):
    _m = text_mask('MEHRAB.7w7', 200, font=_fp, stretch=(1.0, 1.0) if _i else (0.9, 1.25), skew=0.0, pad=40)
    _ys, _xs = np.where(_m > 0.02); _m = _m[_ys.min():_ys.max() + 1, _xs.min():_xs.max() + 1]
    _s = (960 if _i % 2 == 0 else 760) / _m.shape[1]
    FLICK.append(cv2.resize(_m, (int(_m.shape[1] * _s), max(1, int(_m.shape[0] * _s))), interpolation=cv2.INTER_AREA))
LOGO_CY = 960
T_LOGO = 0.36                    # flicker time; then the logo dissolves and the intro comes back


def paste_mask(m, cx, cy, scale=1.0):
    h, w = m.shape
    M = np.float32([[scale, 0, cx - w * scale / 2], [0, scale, cy - h * scale / 2]])
    return cv2.warpAffine(m, M, (W, H), flags=cv2.INTER_LINEAR)


def outro_frame(T, fi):
    lt = T - S.T_OUT
    dur = S.T_END - S.T_OUT
    rng = np.random.default_rng(77 + fi)
    Tl = T - (S.T_END - S.S0)            # intro clock: smoke / dust / rails continue across the loop seam
    G4 = np.zeros((H4, W4, 3), np.float32)
    C = np.zeros((H, W, 3), np.float32)
    canvas = np.zeros((H, W), np.float32)
    if 0 <= lt < T_LOGO:
        idx = int(lt * FPS / 2) % len(FLICK)
        canvas = paste_mask(FLICK[idx], 540 + rng.normal(0, 4), LOGO_CY, 1.0 + 0.04 * rng.normal())
    elif lt >= T_LOGO:
        qq = (lt - T_LOGO) / (dur - T_LOGO)
        canvas = paste_mask(FLICK[0], 540, LOGO_CY, 1.0 + 0.12 * qq) * (1 - smoothstep(0.0, 0.75, qq))
    G4 += cv2.resize(canvas, (W4, H4), interpolation=cv2.INTER_AREA)[..., None] * mix(ACC, WHITE, 0.2)[None, None] * 1.1
    back = smoothstep(T_LOGO - 0.05, dur, lt)          # intro elements come back for the loop
    draw_rails(C, G4, Tl if lt > 0 else T, 0.85 * back)
    sc = 0.6 + 0.4 * smoothstep(0.0, dur, lt)
    draw_orb(C, G4, T, sc, 1.0)
    glow_from_block(G4, TXT, TXT_CY, ACC, 0.30 * back)
    bg4 = smoke_bg(Tl, dot_pos(T), 1.0, 0.0)
    f = up(bg4 + blur_glow(G4)) + C
    f += np.array([1.0, 0.98, 0.96], np.float32) * canvas[..., None] * 0.95
    dd = np.zeros((H, W, 3), np.float32)
    draw_dust(dd, Tl)
    f += dd
    if back > 0.01:
        put_mask(f, TXT, TXT_CY, WHITE * 0.97, back, 1.0, shadow=TXT_SH)
    if lt >= 0:
        f += 1.1 * np.exp(-lt / 0.05)
    return f * VIG


# ================================================================== montage overlay (the small finger dot)
def dot_overlay(f, T):
    G4 = np.zeros((H4, W4, 3), np.float32)
    C = np.zeros((H, W, 3), np.float32)
    shrink = smoothstep(S.T_DROP, S.T_DROP + 0.25, T)
    draw_orb(C, G4, T, 1.0 - 0.4 * shrink, 0.85)
    for kk in range(NI + 1, NMOVE + 1):
        draw_ring(C, G4, *CORNER[kk], T - LAND[kk - 1], 0.32, 22, 170, 0.75, 3)
    draw_sparks(C, G4, T, range(NI + 1, NMOVE + 1), 0.9)
    return f + up(blur_glow(G4)) * 0.85 + C


# ================================================================== frame
def render(fi):
    T = S.S0 + fi / FPS
    k, q = move_state(T)
    if T < S.T_DROP:
        if k == NI and q is not None and q > 0.15:          # the last slide paints the first car in
            orb = []
            f, shake = intro_frame(T, fi, orb)
            f = blend_reveal(f, shot_graded(0, T, fi), T, k, q, 4.0)
            G4o, Co = orb[0]
            f = f + up(blur_glow(G4o)) * VIG + Co
        else:
            f, shake = intro_frame(T, fi)
        return finish(f, fi, shake)
    if T < S.T_OUT:
        i = max(j for j in range(NSHOT) if S.CUTS[j] <= T + 1e-9)
        f = shot_graded(i, T, fi)
        if q is not None and k > NI:                         # swipe in progress -> paint in the next shot
            nxt = k - NI
            f_in = shot_graded(nxt, T, fi) if nxt < NSHOT else outro_frame(T, fi)
            f = blend_reveal(f, f_in, T, k, q, 1.8)
        return finish(dot_overlay(f, T), fi)
    return finish(outro_frame(T, fi), fi)


def clean_plate(path, search):
    """remove the white letters of a dark (dealer) plate inside the search box: the plate's bright top edge gives
    its position, every letter-sized bright blob inside it is inpainted (the plate stays, blank)"""
    im = cv2.imread(path)
    x0, y0, x1, y1 = search
    reg = im[y0:y1, x0:x1]
    g = cv2.cvtColor(reg, cv2.COLOR_BGR2GRAY)
    n, lab, st, _ = cv2.connectedComponentsWithStats((g > 110).astype(np.uint8))
    edges = [j for j in range(1, n) if st[j, 2] > 200 and st[j, 3] < 30]
    if not edges:
        return
    e = max(edges, key=lambda j: st[j, 2])
    px, py, pw = st[e, 0], st[e, 1], st[e, 2]
    ph = int(pw / 4.3)
    m = np.zeros(g.shape, np.uint8)
    for j in range(1, n):
        x, y, w, h, a = st[j]
        if j != e and x >= px - 4 and x + w <= px + pw + 4 and y >= py + 6 and y + h <= py + ph + 8 and h < 45:
            m[lab == j] = 255
    m = cv2.dilate(m, np.ones((7, 7), np.uint8))
    # fill the letters with the plate's own colour (median of the plate face), soft edges
    ys, xs = slice(py + 6, py + ph + 4), slice(px + 4, px + pw - 4)
    face = reg[ys, xs].reshape(-1, 3)[(m[ys, xs] == 0).reshape(-1)]
    if len(face) < 50:
        return
    fill = np.median(face, 0).astype(np.float32)
    a = cv2.GaussianBlur((m > 0).astype(np.float32), (0, 0), 1.5)[..., None]
    noise = np.random.default_rng(3).normal(0, 2.0, reg.shape).astype(np.float32)
    reg[:] = np.clip(reg.astype(np.float32) * (1 - a) + (fill + noise) * a, 0, 255).astype(np.uint8)
    cv2.imwrite(path, im, [cv2.IMWRITE_JPEG_QUALITY, 96])


def extract():
    for i, (nm, car, clip, src, z, cx, cy, box) in enumerate(S.SHOTS):
        dur = (pre(i) + S.CUTS[i + 1] - S.CUTS[i]) * S.SPEED.get(nm, 1.0)
        d = f'{SEG}/{nm}'
        os.makedirs(d, exist_ok=True)
        for fn in os.listdir(d):
            os.remove(f'{d}/{fn}')
        x0, y0, x1, y1 = box
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{src:.3f}', '-i', f'{WORK}/clips/{clip}.mp4', '-t', f'{dur + 0.15:.3f}',
                        '-vf', f'crop={x1 - x0}:{y1 - y0}:{x0}:{y0},fps={FPS}', '-q:v', '2', f'{d}/%04d.jpg'], check=True)
        if nm in getattr(S, 'CLEAN', {}):
            for fn in sorted(os.listdir(d)):
                clean_plate(f'{d}/{fn}', S.CLEAN[nm])
        print(nm, clip, f'{src:.2f}-{src + dur:.2f}', len(os.listdir(d)), 'frames')


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'extract':
        extract()
    elif mode == 'frames':
        os.makedirs(f'{WORK}/check', exist_ok=True)
        for tok in sys.argv[2:]:
            T = float(tok); fi = int(round((T - S.S0) * FPS))
            t1 = time.time(); img = render(fi)
            print(f'T={T} fi={fi} {time.time() - t1:.2f}s', file=sys.stderr)
            cv2.imwrite(f'{WORK}/check/N4_{T:06.3f}.png', cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
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
