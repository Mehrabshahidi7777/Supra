import sys, json, time, os, subprocess
import os as _os
KIT = _os.path.normpath(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '..', '..', 'kit'))
WORK = _os.environ.get('WORK', '/home/claude/work_edit')
HERE = _os.path.dirname(_os.path.abspath(__file__))
sys.path.insert(0, KIT)
import numpy as np, cv2
from lib import *

cv2.setNumThreads(1)
FPS = 30
OFF = 1.24                       # start mid-flight of the SMASH slam (strong first second)
AUD_END = 15.747                 # end ~1.2s into the outro, cut on the beat so it loops
NF = int((AUD_END - OFF) * FPS)  # frames
W4, H4 = W // 4, H // 4

# ---------------------------------------------------------------- music data
EV = [(t, s / 1.06) for t, s in json.load(open(f'{HERE}/events.json')) if t > 0.95]
rms60 = np.load(f'{HERE}/rms60.npy')
rms60 = cv2.GaussianBlur(rms60.reshape(1, -1).astype(np.float32), (0, 0), 3).ravel()
rms60 = rms60 / np.percentile(rms60, 98)

# ---- spectrum per video frame (attack/decay smoothed)
import scipy.io.wavfile as _wf
_sr, _x = _wf.read(f'{WORK}/music_raw.wav'); _x = _x.astype(np.float32).mean(1) / 32768
NBANDS = 36
_edges = np.geomspace(55, 11000, NBANDS + 1)
_nf = int((AUD_END - OFF) * FPS)
_win = np.hanning(4096).astype(np.float32)
_fr = np.fft.rfftfreq(4096, 1 / _sr)
_spec = np.zeros((_nf, NBANDS), np.float32)
for _i in range(_nf):
    _c = int((OFF + _i / FPS) * _sr)
    _seg = _x[max(0, _c - 2048):_c + 2048]
    if len(_seg) < 4096:
        _seg = np.pad(_seg, (0, 4096 - len(_seg)))
    _m = np.abs(np.fft.rfft(_seg * _win))
    for _b in range(NBANDS):
        _sel = (_fr >= _edges[_b]) & (_fr < _edges[_b + 1])
        _spec[_i, _b] = _m[_sel].mean() if _sel.any() else 0
_spec = 20 * np.log10(_spec + 1e-4)
_spec = np.clip((_spec - np.percentile(_spec, 30)) / (np.percentile(_spec, 99.5) - np.percentile(_spec, 30)), 0, 1)
_spec *= np.linspace(0.85, 1.25, NBANDS)[None]
SPEC = np.zeros_like(_spec)
_prev = np.zeros(NBANDS, np.float32)
for _i in range(_nf):
    _cur = _spec[_i]
    _prev = np.where(_cur > _prev, _cur, _prev * 0.80 + _cur * 0.20)
    SPEC[_i] = _prev
SPEC = np.clip(SPEC, 0, 1.15)

T_SMASH, T_OR, T_PASS = 1.317, 2.075, 2.672
T_DIM0, T_BACK = 3.40, 4.08
T_BUILD, T_DROP = 6.0, 7.019
T_ALT0, T_ALT1 = 11.05, 14.48
T_OUT = 14.539
T_FADE = AUD_END - 0.35

BIG = {2.672, 4.501, 4.955, 7.237, 8.864, 9.504, 9.984, 10.88, 14.539}
GLITCH = [4.501, 4.955, 6.0, 8.864, 9.984, 10.88, 12.491, 13.637]
INVERT = [4.955, 9.984]
LIGHT = [(T_SMASH, 2), (T_PASS, 2), (T_DROP, 3), (7.237, 2), (9.504, 2), (10.88, 2), (13.227, 1), (T_OUT, 3)]
SHOCK = [T_SMASH, T_PASS, T_DROP, 9.984, T_OUT]
SPARK = [(T_SMASH, 700), (T_PASS, 1060), (T_DROP, 880), (7.237, 880), (9.504, 880), (10.88, 880)]
SHINE = [3.28, 5.739, 8.251, 10.176, 15.232]
ALT_EVENTS = [t for t, s in EV if T_ALT0 <= t < T_ALT1]


def energy(T):
    i = int(np.clip(T * 60, 0, len(rms60) - 1))
    return float(np.clip(rms60[i], 0, 1.2))


def decay_sum(T, items, tau):
    v = 0.0
    for t, a in items:
        dt = T - t
        if 0 <= dt < 8 * tau:
            v += a * np.exp(-dt / tau)
    return v


def pulse(T):
    return decay_sum(T, [(t, s ** 1.5) for t, s in EV], 0.11)


def last_event(T, lst):
    best = None
    for t in lst:
        if t <= T:
            best = t
    return best


# ---------------------------------------------------------------- plates
t0 = time.time()
TS = 255
m_smash = text_mask('SMASH', TS)
m_pass = text_mask('PASS', TS)
P_SMASH = build_plate(m_smash, seed=1)
P_PASS = build_plate(m_pass, seed=2)

# OR neon (with flanking bars)
m_or = text_mask('OR', 112, stretch=(1.0, 1.04), skew=-0.13, pad=40)
oh, ow = m_or.shape
ORW = 760
or_canvas = np.zeros((oh, ORW), np.float32)
ox0 = (ORW - ow) // 2
or_canvas[:, ox0:ox0 + ow] = m_or
tube = np.clip(dilate(or_canvas, 3) - erode(or_canvas, 3), 0, 1)
core = np.clip(dilate(or_canvas, 1) - erode(or_canvas, 1), 0, 1)
bars = np.zeros_like(or_canvas)
cyb = oh // 2 + 2
ink = np.where(or_canvas.max(0) > 0.1)[0]
il, ir = ink.min(), ink.max()
cv2.line(bars, (il - 190, cyb), (il - 34, cyb), 1.0, 7, cv2.LINE_AA)
cv2.line(bars, (ir + 34, cyb), (ir + 190, cyb), 1.0, 7, cv2.LINE_AA)
bars_core = np.zeros_like(or_canvas)
cv2.line(bars_core, (il - 188, cyb), (il - 36, cyb), 1.0, 2, cv2.LINE_AA)
cv2.line(bars_core, (ir + 36, cyb), (ir + 188, cyb), 1.0, 2, cv2.LINE_AA)
BAR_X = (il, ir, cyb)


def or_plate(bar_frac):
    """neon OR with bars grown to bar_frac (0..1)"""
    if bar_frac < 1:
        mask_x = np.zeros(ORW, np.float32)
        L = 190 * bar_frac
        xs = np.arange(ORW)
        mask_x = ((xs >= il - 34 - L) & (xs <= ir + 34 + L)).astype(np.float32)
        b = bars * mask_x[None]
        bc = bars_core * mask_x[None]
    else:
        b, bc = bars, bars_core
    t_ = np.clip(tube + b, 0, 1)
    c_ = np.clip(core + bc, 0, 1)
    rgb = hexc('#ff1e18')[None, None] * t_[..., None] + (hexc('#ffe2da') - hexc('#ff1e18'))[None, None] * (c_[..., None] * 0.9)
    return rgb * 1.0, t_


# end-card handle plate
m_h = text_mask('MEHRAB.7w7', 150)
P_HANDLE = build_plate(m_h, depth=16, stroke=6, seed=3)
inkx = np.where(m_h.max(0) > 0.1)[0]
HANDLE_SCALE = 880 / (inkx.max() - inkx.min())

POS = {'SMASH': (540, 700), 'OR': (540, 882), 'PASS': (540, 1062)}
print('plates ready', round(time.time() - t0, 2), 'handle scale', round(HANDLE_SCALE, 3), file=sys.stderr)

# ---------------------------------------------------------------- static background maps
yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
CX, CY = W / 2, 880
rr = np.hypot((xx - CX) / W, (yy - CY) / W)
BASE = np.zeros((H, W, 3), np.float32) + hexc('#040001')
BASE += hexc('#1a0003') * smoothstep(1.2, 0.0, np.abs(yy - CY) / H * 2)[..., None]
RADIAL = (np.exp(-(rr / 0.40) ** 2))[..., None] * hexc('#8a0010')
VIG = (1 - 0.78 * smoothstep(0.30, 1.08, np.hypot((xx - W / 2) / (W * 0.62), (yy - H / 2) / (H * 0.56))))[..., None]
del yy, xx, rr

# quarter-res polar grids
y4, x4 = np.mgrid[0:H4, 0:W4].astype(np.float32)
x4f = (x4 + 0.5) * 4; y4f = (y4 + 0.5) * 4
TH4 = np.arctan2(y4f - CY, x4f - CX)
R4 = np.hypot((x4f - CX) / W, (y4f - CY) / W)
NB = 3600
rng = np.random.default_rng(5)
prof = np.zeros(NB, np.float32)
ii = np.arange(NB)
for k in range(30):
    c = rng.random() * NB; wdt = rng.uniform(12, 60); amp = rng.uniform(0.3, 1)
    d = np.minimum(np.abs(ii - c), NB - np.abs(ii - c))
    prof += amp * np.exp(-(d / wdt) ** 2)
RAY_LUT = prof / prof.max()
RAY_RAD = (np.exp(-R4 / 0.6) * smoothstep(0.03, 0.22, R4)).astype(np.float32)
# speed lines: per-angle-bin lines
NSB = 900
sb_on = (rng.random(NSB) < 0.33).astype(np.float32) * rng.uniform(0.4, 1.0, NSB).astype(np.float32)
sb_ph = rng.random(NSB).astype(np.float32)
sb_sp = rng.uniform(0.8, 1.6, NSB).astype(np.float32)
SB_IDX = (((TH4 + np.pi) / (2 * np.pi)) * (NSB - 1)).astype(np.int32)
SL_RAD = smoothstep(0.18, 0.75, R4).astype(np.float32)
# smoke textures
SMOKE_A = fractal_noise(900, 520, 11, octaves=5, base=4)
SMOKE_B = fractal_noise(900, 520, 12, octaves=4, base=3)
# grain
GRAIN = [np.random.default_rng(100 + i).normal(0, 1, (H, W)).astype(np.float16) for i in range(6)]

# embers (closed-form motion)
NE = 160
er = np.random.default_rng(21)
E_X0 = er.uniform(0, W, NE); E_Y0 = er.uniform(0, H + 200, NE)
E_V = er.uniform(40, 170, NE); E_SZ = er.uniform(1.0, 3.6, NE)
E_WOB = er.uniform(10, 50, NE); E_WF = er.uniform(0.3, 1.4, NE); E_PH = er.uniform(0, 6.28, NE)
E_BR = er.uniform(0.35, 1.0, NE); E_FL = er.uniform(3, 11, NE)
E_FRONT = er.random(NE) < 0.25

# sparks
SPARKS = []
for i, (ts, sy) in enumerate(SPARK):
    sr_ = np.random.default_rng(300 + i)
    n = 90 if ts in (T_DROP,) else 60
    ang = sr_.uniform(0, 2 * np.pi, n)
    sp = sr_.uniform(500, 2100, n) * (1.25 if ts == T_DROP else 1.0)
    x0 = 540 + sr_.uniform(-380, 380, n); y0 = sy + sr_.uniform(-70, 70, n)
    life = sr_.uniform(0.35, 0.95, n)
    SPARKS.append((ts, x0, y0, np.cos(ang) * sp, np.sin(ang) * sp * 0.75 - 250, life))

# heart curve
tt_ = np.linspace(0, 2 * np.pi, 400)
HX = 16 * np.sin(tt_) ** 3
HY = -(13 * np.cos(tt_) - 5 * np.cos(2 * tt_) - 2 * np.cos(3 * tt_) - np.cos(4 * tt_))
hy_mid = (HY.min() + HY.max()) / 2
HY = HY - hy_mid
NOTCH_Y = -5 - hy_mid; TIP_Y = 17 - hy_mid
zz = np.linspace(NOTCH_Y, TIP_Y, 9)
ZX = np.array([0, 1.4, -1.2, 1.5, -1.4, 1.2, -1.5, 1.0, 0])

# watermark
from PIL import Image, ImageDraw, ImageFont
_wm = Image.new('L', (W, 110), 0); _d = ImageDraw.Draw(_wm)
_f = ImageFont.truetype(FONT_REG, 44)
_tx = 'MEHRAB.7w7'
_tw = sum(_f.getlength(c) for c in _tx) + 3 * (len(_tx) - 1)
_x = (W - _tw) / 2
for c in _tx:
    _d.text((_x, 30), c, font=_f, fill=255); _x += _f.getlength(c) + 3
WM = np.asarray(_wm, np.float32) / 255
WM_GLOW = cv2.GaussianBlur(WM, (0, 0), 6)
WM_Y = 1688


# ---------------------------------------------------------------- drawing helpers
def bolt(rng, p0, p1, disp, depth):
    pts = [np.array(p0, np.float32), np.array(p1, np.float32)]
    for _ in range(depth):
        new = [pts[0]]
        for a, b in zip(pts[:-1], pts[1:]):
            m = (a + b) / 2
            d = b - a
            nrm = np.array([-d[1], d[0]], np.float32)
            nrm /= (np.linalg.norm(nrm) + 1e-6)
            m = m + nrm * rng.normal(0, disp)
            new += [m, b]
        pts = new
        disp *= 0.55
    return np.array(pts, np.float32)


def heart_layers(lay_core, lay_tube, scale, cx, cy, split, alpha):
    """draw neon heart at full-res (core) / quarter (tube glow handled by blur)"""
    def tr(x, y, side):
        # split: halves move apart and tilt around tip
        ang = side * split * 0.22
        px, py = x, y - TIP_Y
        rx = px * np.cos(ang) - py * np.sin(ang)
        ry = px * np.sin(ang) + py * np.cos(ang) + TIP_Y
        return cx + (rx + side * split * 2.2) * scale, cy + ry * scale
    if split < 0.02:
        pts = np.stack([cx + HX * scale, cy + HY * scale], 1)
        polys = [pts]
    else:
        right = tt_ <= np.pi
        rx_, ry_ = np.r_[HX[right], ZX[::-1]], np.r_[HY[right], zz[::-1]]
        left = tt_ >= np.pi
        lx_, ly_ = np.r_[HX[left], -ZX], np.r_[HY[left], zz]
        polys = [np.stack(tr(rx_, ry_, 1), 1), np.stack(tr(lx_, ly_, -1), 1)]
    for p in polys:
        pi = (p * 4).astype(np.int32).reshape(-1, 1, 2)
        cv2.polylines(lay_core, [pi], True, alpha, 5, cv2.LINE_AA, shift=2)
        cv2.polylines(lay_tube, [(p / 4 * 4).astype(np.int32).reshape(-1, 1, 2)], True, alpha, 3, cv2.LINE_AA, shift=2)


# ---------------------------------------------------------------- frame renderer
def word_state(T, name):
    """returns (visible, scale, angle, dx, dy, alpha, blur_scales) for SMASH / PASS"""
    ts = T_SMASH if name == 'SMASH' else T_PASS
    LEAD = 0.13
    if T < ts - LEAD:
        return None
    if T < ts:
        p = (T - (ts - LEAD)) / LEAD
        sc = 1 + 2.6 * (1 - p) ** 2
        ang = (-9 if name == 'SMASH' else 9) * (1 - p) ** 2
        return dict(scale=sc, angle=ang, alpha=min(1, p * 1.6), blur=True, prev=1 + 2.6 * (1 - max(0, p - 0.25)) ** 2)
    dt = T - ts
    sc = 1 - 0.07 * np.exp(-dt / 0.07) * np.cos(dt * 38)
    return dict(scale=sc, angle=0.0, alpha=1.0, blur=False)


def render(fi):
    T = OFF + fi / FPS
    rng = np.random.default_rng(1000 + fi)
    e = energy(T)
    pu = pulse(T)
    pu_c = min(pu, 1.4)
    post_drop = T >= T_DROP
    in_alt = T_ALT0 <= T < T_ALT1
    out_t = T - T_OUT

    # ---- global light level (power flicker, intro)
    light = smoothstep(0.85, 1.25, T)
    if T_DIM0 <= T < T_BACK:
        k = (T - T_DIM0) / (T_BACK - T_DIM0)
        fl = 0.35 + 0.25 * (rng.random() > 0.5) - 0.2 * k
        light *= fl
    build = smoothstep(T_BUILD, T_DROP, T) if T < T_DROP else 0.0

    # ================= quarter-res background effects =================
    q = np.zeros((H4, W4, 3), np.float32)
    # rays
    if T < T_BUILD:
        rot = 0.06 * T
    elif T < T_DROP:
        x_ = T - T_BUILD
        rot = 0.06 * T_BUILD + 0.06 * x_ + 0.45 * x_ ** 3
    else:
        rot = 0.06 * T_BUILD + 0.06 + 0.45 + 0.16 * (T - T_DROP)
    idx = (((TH4 + rot) % (2 * np.pi)) / (2 * np.pi) * (NB - 1)).astype(np.int32)
    ray_i = (0.10 + 0.14 * e + 0.30 * pu_c + 0.25 * build) * (1.5 if post_drop else 1.0) * light
    q += hexc('#ff2412')[None, None] * (RAY_LUT[idx] * RAY_RAD * ray_i)[..., None]
    # smoke (drifting up)
    oy = int((T * 22) % 400); ox = int(60 + 30 * np.sin(T * 0.3))
    sa = SMOKE_A[oy:oy + H4, ox:ox + W4]
    oy2 = int((T * 38 + 150) % 400); ox2 = int(120 + 40 * np.cos(T * 0.23))
    sb = SMOKE_B[oy2:oy2 + H4, ox2:ox2 + W4]
    smoke = (sa * sb) ** 1.6
    q += hexc('#ff1a0e')[None, None] * (smoke * (0.55 + 0.6 * e + 0.6 * pu_c) * light * 0.55)[..., None]
    # speed lines after drop
    if post_drop and out_t < 0.25:
        tl = T - T_DROP
        ph = R4 * 2.2 - (tl * 1.6) * sb_sp[SB_IDX] + sb_ph[SB_IDX]
        dash = smoothstep(0.55, 0.8, np.sin(ph * 2 * np.pi * 1.5) * 0.5 + 0.5)
        sl = sb_on[SB_IDX] * dash * SL_RAD
        sli = (0.18 + 0.45 * pu_c) * smoothstep(0, 0.15, tl) * (1 - smoothstep(-0.1, 0.2, out_t))
        q += hexc('#ff5040')[None, None] * (sl * sli)[..., None]
    # shockwaves
    for ts in SHOCK:
        dt = T - ts
        if 0 <= dt < 0.6:
            r = 60 + 2400 * dt ** 0.75
            a = np.exp(-dt / 0.2)
            th = max(1, int((22 - 30 * dt) / 4))
            cv2.circle(q, (int(CX / 4), int((700 if ts == T_SMASH else (1062 if ts == T_PASS else CY)) / 4)), int(r / 4),
                       tuple(float(v) for v in hexc('#ff4a30') * a * 1.6), th, cv2.LINE_AA)
    # embers (glow part)
    if post_drop:
        etime = T_DROP + 2.3 * (T - T_DROP)
    else:
        etime = T
    ex = (E_X0 + E_WOB * np.sin(E_WF * T + E_PH)) % W
    ey = (E_Y0 - E_V * etime) % (H + 200) - 100
    eb = E_BR * (0.6 + 0.4 * np.sin(E_FL * T + E_PH * 3)) * (0.4 + 0.6 * smoothstep(0.0, 1.0, T)) * (0.6 + 0.4 * light)
    ember_core = np.zeros((H, W), np.float32)
    for i in range(NE):
        cv2.circle(ember_core, (int(ex[i] * 4), int(ey[i] * 4)), int(E_SZ[i] * 4), float(eb[i]), -1, cv2.LINE_AA, shift=2)

    # upsample background effects
    bgfx = cv2.resize(q, (W, H), interpolation=cv2.INTER_LINEAR)
    frame = BASE + RADIAL * ((0.35 + 0.35 * e + 0.5 * pu_c + 0.3 * build) * light) + bgfx

    # ---- neon heart (behind text) from drop until outro
    heart_a = 0.0
    if post_drop:
        dt = T - T_DROP
        heart_a = smoothstep(0, 0.05, dt) * (0.55 + 0.25 * e + 0.6 * pu_c)
        if dt < 0.25:
            heart_a *= 0.4 + 0.6 * (rng.random() > 0.35)
        if out_t > 0:
            heart_a *= 1 - smoothstep(0, 0.15, out_t)
    if heart_a > 0.01:
        split = 0.0
        lit = None
        if in_alt:
            le = last_event(T, ALT_EVENTS)
            if le is not None:
                n = ALT_EVENTS.index(le)
                lit = 'SMASH' if n % 2 == 0 else 'PASS'
                if lit == 'PASS':
                    split = smoothstep(0, 0.06, T - le)
                    heart_a *= 0.75
        hsc = 29 * (1 + 0.05 * pu_c)
        hc = np.zeros((H, W), np.float32); ht = np.zeros((H, W), np.float32)
        heart_layers(hc, ht, hsc, CX, CY + 10, split, 1.0)
        hglow = cv2.resize(cv2.GaussianBlur(cv2.resize(hc, (W4, H4), interpolation=cv2.INTER_AREA), (0, 0), 3.0), (W, H))
        frame += (hexc('#ff1f14')[None, None] * (hglow * 2.2 + hc * 0.9)[..., None]
                  + hexc('#ffd0c8')[None, None] * (hc * 0.35)[..., None]) * heart_a

    # embers behind text
    ember_back = ember_core * (~E_FRONT).astype(np.float32).mean() if False else ember_core
    eg = cv2.resize(cv2.GaussianBlur(cv2.resize(ember_core, (W4, H4), interpolation=cv2.INTER_AREA), (0, 0), 2.0), (W, H))
    frame += hexc('#ff3a12')[None, None] * (eg * 3.0)[..., None] + hexc('#ffb080')[None, None] * (ember_core * 0.8)[..., None]

    # ================= text =================
    trgb = np.zeros((H, W, 3), np.float32); ta = np.zeros((H, W), np.float32)
    lit = None
    if in_alt:
        le = last_event(T, ALT_EVENTS)
        if le is not None:
            n = ALT_EVENTS.index(le)
            lit = ('SMASH' if n % 2 == 0 else 'PASS', le)
    title_out = out_t >= -0.06
    tsc_out = 1.0
    if title_out:
        p = np.clip((out_t + 0.06) / 0.22, 0, 1)
        tsc_out = 1 + 3.5 * p ** 2
        title_alpha = 1 - smoothstep(0.3, 1.0, p)
    else:
        title_alpha = 1.0
    if title_alpha > 0.01:
        for name, P in (('SMASH', P_SMASH), ('PASS', P_PASS)):
            st = word_state(T, name)
            if st is None:
                continue
            cx_, cy_ = POS[name]
            bob = 3 * np.sin(T * 2.1 + (0 if name == 'SMASH' else 2.0))
            sc = st['scale'] * (1 + 0.035 * pu_c)
            bright = 1.0
            if lit is not None:
                dtl = T - lit[1]
                if lit[0] == name:
                    sc *= 1 + 0.07 * np.exp(-dtl / 0.12)
                    bright = 1.15
                else:
                    bright = 0.42
                    sc *= 0.97
            # outro: scale from title center
            cyo = cy_
            if title_out:
                cyo = 880 + (cy_ - 880) * tsc_out
                sc *= tsc_out
            prgb, pa = P[0], P[1]
            # shine sweep
            for tsh in SHINE:
                dsh = T - tsh
                if 0 <= dsh < 0.45:
                    hh, ww = pa.shape
                    gx = np.arange(ww, dtype=np.float32)[None, :]
                    gy = np.arange(hh, dtype=np.float32)[:, None]
                    pos = -300 + (ww + 600) * (dsh / 0.45)
                    band = np.exp(-(((gx + 0.45 * gy) - pos) / 38) ** 2)
                    prgb = prgb + (hexc('#ffd8cc')[None, None] * (band * P[2] * 0.85)[..., None])
            if bright != 1.0:
                prgb = prgb * bright
            if st.get('blur'):
                ns = 7
                acc_r = np.zeros_like(trgb); acc_a = np.zeros_like(ta)
                for k in range(ns):
                    s_ = st['prev'] + (st['scale'] - st['prev']) * k / (ns - 1)
                    r_, a_ = place(np.zeros_like(trgb), np.zeros_like(ta), prgb, pa, cx_, cy_ + bob, s_, st['angle'], st['alpha'])
                    acc_r += r_; acc_a += a_
                trgb, ta = over(trgb, ta, acc_r / ns, acc_a / ns)
            else:
                trgb, ta = place(trgb, ta, prgb, pa, cx_, cyo + bob, sc, st['angle'], st['alpha'] * title_alpha)
        # OR neon
        if T >= T_OR:
            dto = T - T_OR
            seq = [1, 0, 0, 1, 1, 0, 1, 0.4, 1]
            fo = seq[min(int(dto * FPS), len(seq) - 1)]
            if T_DIM0 <= T < T_BACK:
                fo *= 0.3 + 0.7 * (rng.random() > 0.45)
            bar = ease_out_cubic(dto / 0.3)
            o_rgb, o_a = or_plate(bar)
            sc = 1 + 0.05 * pu_c
            cyo = POS['OR'][1]
            if title_out:
                sc *= tsc_out
            if lit is not None:
                o_rgb = o_rgb * 0.8
            trgb, ta = place(trgb, ta, o_rgb * fo, o_a * fo, POS['OR'][0], cyo, sc, 0, title_alpha)

    # ---- end card handle
    if out_t >= 0:
        dt = out_t
        app = smoothstep(0.02, 0.10, dt)
        sc = HANDLE_SCALE * (1 + 0.6 * np.exp(-dt / 0.06)) * (1 + 0.03 * pu_c)
        prgb, pa = P_HANDLE[0], P_HANDLE[1]
        dsh = T - 15.232
        if 0 <= dsh < 0.5:
            hh, ww = pa.shape
            gx = np.arange(ww, dtype=np.float32)[None, :]
            gy = np.arange(hh, dtype=np.float32)[:, None]
            pos = -300 + (ww + 600) * (dsh / 0.5)
            band = np.exp(-(((gx + 0.45 * gy) - pos) / 38) ** 2)
            prgb = prgb + hexc('#ffd8cc')[None, None] * (band * P_HANDLE[2] * 0.85)[..., None]
        if dt < 0.25 and rng.random() < 0.5:
            app *= 0.5
        trgb, ta = place(trgb, ta, prgb, pa, 540, 880, sc, 0, app)
        # neon underline
        ul = ease_out_cubic((dt - 0.12) / 0.35)
        if ul > 0:
            Lh = 440 * ul
            u_c = np.zeros((H, W), np.float32)
            cv2.line(u_c, (int((540 - Lh) * 4), int(1010 * 4)), (int((540 + Lh) * 4), int(1010 * 4)), 1.0, 6, cv2.LINE_AA, shift=2)
            u_rgb = hexc('#ff1e18')[None, None] * u_c[..., None]
            trgb, ta = over(trgb, ta, u_rgb, u_c)

    # ---- text glow
    gsrc = cv2.resize(np.clip(trgb[..., 0] * 0.8 + trgb[..., 1] * 0.4, 0, 1.5), (W4, H4), interpolation=cv2.INTER_AREA)
    g1 = cv2.GaussianBlur(gsrc, (0, 0), 3.0)
    g2 = cv2.GaussianBlur(gsrc, (0, 0), 14.0)
    gi = (0.55 + 0.35 * e + 0.9 * pu_c + 0.4 * build) * light
    glow = cv2.resize(g1 * 0.9 + g2 * 1.6, (W, H), interpolation=cv2.INTER_LINEAR) * gi
    frame += hexc('#ff1608')[None, None] * glow[..., None]
    tl_ = 0.35 + 0.65 * light
    frame = trgb * tl_ + frame * (1 - ta[..., None])

    # ---- music spectrum (mirrored bars)
    if T >= 0.95:
        sp = SPEC[min(fi, len(SPEC) - 1)]
        sp_a = smoothstep(0.95, 1.1, T) * (1 - smoothstep(-0.05, 0.15, out_t)) * (0.45 + 0.55 * light)
        if sp_a > 0.01:
            lay = np.zeros((300, W), np.float32)
            ycen = 150
            span = 820; x0b = 540 - span / 2; step = span / (NBANDS * 2 - 1)
            vals = np.r_[sp[::-1], sp]
            for b, v in enumerate(vals):
                hgt = 6 + 118 * v ** 1.3
                xb = x0b + b * step
                cv2.line(lay, (int(xb * 4), int((ycen - hgt / 2) * 4)), (int(xb * 4), int((ycen + hgt / 2) * 4)),
                         float(0.55 + 0.45 * v), 7, cv2.LINE_AA, shift=2)
            Y0 = 1330
            lg = cv2.resize(cv2.GaussianBlur(cv2.resize(lay, (W // 4, 75), interpolation=cv2.INTER_AREA), (0, 0), 2.0), (W, 300))
            reg = frame[Y0:Y0 + 300]
            reg += (hexc('#ff1a10')[None, None] * (lg * 2.0)[..., None]) * sp_a
            reg[:] = reg * (1 - lay[..., None] * 0.85 * sp_a) + (hexc('#ff2a22')[None, None] * lay[..., None] +
                                                              hexc('#ffb4a8')[None, None] * (np.clip(lay - 0.8, 0, 1) * 2)[..., None]) * sp_a

    # ================= front FX =================
    fx = np.zeros((H, W), np.float32)
    # sparks
    for ts, x0, y0, vx, vy, life in SPARKS:
        dt = T - ts
        if 0 <= dt < 1.0:
            k = 3.2; g = 1400
            f_ = (1 - np.exp(-k * dt)) / k
            px = x0 + vx * f_
            py = y0 + (vy + g / k) * f_ - g * dt / k
            dt2 = max(0, dt - 0.022)
            f2 = (1 - np.exp(-k * dt2)) / k
            qx = x0 + vx * f2
            qy = y0 + (vy + g / k) * f2 - g * dt2 / k
            al = np.clip(1 - dt / life, 0, 1)
            for j in range(len(px)):
                if al[j] > 0:
                    cv2.line(fx, (int(qx[j] * 4), int(qy[j] * 4)), (int(px[j] * 4), int(py[j] * 4)), float(al[j] * 1.4), 2, cv2.LINE_AA, shift=2)
    # lightning
    for ts, nb in LIGHT:
        dt = T - ts
        if 0 <= dt < 0.16:
            if int(dt * FPS) % 2 == 1 and dt > 0.04:
                continue
            for b in range(nb):
                br = np.random.default_rng(int(ts * 1000) + 7 * b + 31 * fi)
                side = br.choice([-1, 1])
                p0 = (540 + side * br.uniform(250, 560), br.uniform(150, 560))
                p1 = (540 + side * br.uniform(60, 330), br.uniform(640, 1100))
                pts = bolt(br, p0, p1, 70, 6)
                cv2.polylines(fx, [(pts * 4).astype(np.int32).reshape(-1, 1, 2)], False, 1.3, 3, cv2.LINE_AA, shift=2)
                # branch
                k0 = len(pts) // 3
                pb = pts[k0]
                p2 = pb + np.array([side * br.uniform(60, 200), br.uniform(80, 260)], np.float32)
                pts2 = bolt(br, pb, p2, 35, 4)
                cv2.polylines(fx, [(pts2 * 4).astype(np.int32).reshape(-1, 1, 2)], False, 0.9, 2, cv2.LINE_AA, shift=2)
    if fx.max() > 0:
        fg = cv2.resize(cv2.GaussianBlur(cv2.resize(fx, (W4, H4), interpolation=cv2.INTER_AREA), (0, 0), 2.5), (W, H))
        frame += hexc('#ff2a14')[None, None] * (fg * 3.5)[..., None] + hexc('#ffd9cf')[None, None] * fx[..., None]
    # anamorphic flare on hits
    fl_amt = decay_sum(T, [(t, s ** 2) for t, s in EV if t in BIG or t in (T_SMASH, T_DROP)], 0.12)
    if fl_amt > 0.03:
        yv = np.arange(H, dtype=np.float32)
        prof_y = np.exp(-((yv - 880) / 5) ** 2) * 1.0 + np.exp(-((yv - 880) / 40) ** 2) * 0.25
        xv = np.arange(W, dtype=np.float32)
        prof_x = np.exp(-np.abs(xv - 540) / 420)
        frame += (hexc('#ff4030')[None, None] * (prof_y[:, None] * prof_x[None, :] * fl_amt * 0.9)[..., None])

    # ================= camera =================
    Z = 1.04 + 0.10 * (build ** 3) + 0.014 * pu_c
    if post_drop:
        Z += 0.18 * np.exp(-(T - T_DROP) / 0.10)
    if out_t >= 0:
        Z += 0.12 * np.exp(-out_t / 0.08)
    shake_items = []
    for t, s in EV:
        if t in (T_SMASH, T_PASS):
            a = 30
        elif t == T_DROP:
            a = 46
        elif t in BIG:
            a = 22 * s ** 2
        else:
            a = 11 * s ** 2
        shake_items.append((t, a))
    sh = decay_sum(T, shake_items, 0.11) + 9 * build ** 2
    dx, dy = rng.normal(0, 1, 2) * sh * 0.7
    rotd = rng.normal(0, 1) * sh * 0.025
    if post_drop and out_t < 0:
        rotd += 0.7 * np.sin(2 * np.pi * (T - T_DROP) / 2.4)
    M = cv2.getRotationMatrix2D((CX, CY), rotd, Z)
    M[0, 2] += dx; M[1, 2] += dy
    frame = cv2.warpAffine(frame, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

    # chromatic aberration
    ca = decay_sum(T, [(t, s ** 2) for t, s in EV if t in BIG] + [(T_DROP, 1.4), (T_SMASH, 0.8), (T_PASS, 0.8)], 0.10)
    if ca > 0.05:
        a = 0.010 * min(ca, 1.6)
        for ch, sgn in ((0, 1), (2, -1)):
            Mc = cv2.getRotationMatrix2D((CX, CY), 0, 1 + sgn * a)
            frame[..., ch] = cv2.warpAffine(np.ascontiguousarray(frame[..., ch]), Mc, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

    # glitch slices
    gl = last_event(T, GLITCH)
    if (gl is not None and T - gl < 0.13) or (0 <= out_t < 0.2):
        gr = np.random.default_rng(5000 + fi)
        nsl = gr.integers(5, 12)
        for _ in range(nsl):
            y0 = gr.integers(0, H - 20); hgt = gr.integers(6, 90)
            sh_ = int(gr.normal(0, 60))
            frame[y0:y0 + hgt] = np.roll(frame[y0:y0 + hgt], sh_, axis=1)
            if gr.random() < 0.3:
                frame[y0:y0 + hgt, :, 0] = np.roll(frame[y0:y0 + hgt, :, 0], int(gr.normal(0, 25)), axis=1)
        # thin noise lines
        for _ in range(gr.integers(2, 6)):
            y0 = gr.integers(0, H - 3)
            frame[y0:y0 + 2] += hexc('#ff6050') * 0.5

    # invert-red flash (1-2 frames)
    for ti in INVERT:
        if 0 <= T - ti < 2.0 / FPS:
            lum = frame.mean(2, keepdims=True)
            frame = np.clip(1 - lum * 1.4, 0, 1) * hexc('#ff2a20')[None, None]

    # flash
    fla = decay_sum(T, [(T_SMASH, 0.85), (T_PASS, 0.95), (T_DROP, 1.3), (T_OUT, 1.2), (T_BACK, 0.4)]
                    + [(t, 0.28 * s ** 2) for t, s in EV if t in BIG], 0.055)
    if fla > 0.01:
        frame = frame * (1 + 1.3 * fla) + (np.array([1.0, 0.55, 0.5], np.float32) * (0.16 * fla))[None, None]

    # grade: vignette, grain, gentle curve
    frame *= VIG
    frame = frame / (1 + 0.35 * np.maximum(frame - 0.75, 0))  # soft shoulder
    frame += (GRAIN[fi % 6].astype(np.float32) * 0.018)[..., None]
    # intro fade from black / end fade
    fade = 1.0  # no fades: loop-friendly, no black frames
    frame *= fade

    # watermark (static, over everything)
    wm_a = (1 - smoothstep(0.0, 0.12, out_t))
    if wm_a > 0.01:
        sl = frame[WM_Y:WM_Y + 110]
        sl += hexc('#ff2015')[None, None] * (WM_GLOW * 0.75 * wm_a)[..., None]
        sl[:] = sl * (1 - WM[..., None] * 0.9 * wm_a) + (WM[..., None] * 0.95 * wm_a)
    return (np.clip(frame, 0, 1) * 255 + 0.5).astype(np.uint8)


if __name__ == '__main__':
    mode = sys.argv[1]
    if mode == 'frames':
        os.makedirs(f'{WORK}/check', exist_ok=True)
        for tok in sys.argv[2:]:
            T = float(tok)
            fi = int(round((T - OFF) * FPS))
            t1 = time.time()
            img = render(fi)
            print(f'T={T} fi={fi} {time.time() - t1:.2f}s', file=sys.stderr)
            cv2.imwrite(f'{WORK}/check/T{T:06.3f}.png', cv2.cvtColor(img, cv2.COLOR_RGB2BGR))
    elif mode == 'video':
        out = sys.argv[2]
        from multiprocessing import Pool
        ff = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                               '-i', '-', '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p',
                               '-tune', 'grain', out], stdin=subprocess.PIPE)
        t1 = time.time()
        with Pool(2) as pool:
            for i, img in enumerate(pool.imap(render, range(NF), chunksize=4)):
                ff.stdin.write(img.tobytes())
                if i % 30 == 0:
                    print(f'frame {i}/{NF}  {time.time() - t1:.1f}s', file=sys.stderr, flush=True)
        ff.stdin.close(); ff.wait()
        print('done', time.time() - t1, file=sys.stderr)
