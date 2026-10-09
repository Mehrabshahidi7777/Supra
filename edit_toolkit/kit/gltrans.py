"""gltrans.py — scene transitions ported from gl-transitions (GLSL) to numpy + OpenCV.

Source: https://github.com/gl-transitions/gl-transitions (MIT License,
Copyright (c) 2017-present gl-transitions contributors; each port names its original author below).
page_curl is "InvertedPageCurl", Copyright (c) 2010 Hewlett-Packard Development Company, L.P., BSD 3-Clause
(redistribution must keep that notice — it is kept here). _snoise_x is Ashima Arts' simplex noise (MIT).
The GLSL math is kept 1:1 (uv origin bottom-left, y up) so results match the originals; only the
sampling runs on the CPU with cv2.remap. No GPU, no pip installs: numpy + opencv only.

Use in a renderer:
    from gltrans import transition, NAMES
    out = transition('cube', frame_a, frame_b, p)      # p = 0..1, uint8 HxWx3 in, uint8 out
    out = transition('crosswarp', a, b, p, ease='inout')   # optional easing on p

Quick look from the shell (two clips -> short preview mp4, or a contact sheet):
    python3 kit/gltrans.py demo A.mp4 2.0 B.mp4 5.0 cube out.mp4 [--dur 0.6 --fps 60 --size 1080x1920]
    python3 kit/gltrans.py sheet A.mp4 2.0 B.mp4 5.0 cube sheet.jpg
    python3 kit/gltrans.py list

All ports avoid white flashes and particles (house taste). Frames are any size; renders are usually 1080x1920
and upscaled later by finish4k.sh. Typical length: 0.4–0.8 s, cut so p = 0.5 lands on the beat.
"""
import sys
import numpy as np
import cv2

# ----------------------------------------------------------------------------- core helpers
_GRID = {}


def _grid(h, w):
    """GL-style uv for pixel centres: u right, v UP (0 at bottom)."""
    k = (h, w)
    if k not in _GRID:
        u = (np.arange(w, dtype=np.float32) + 0.5) / w
        v = 1.0 - (np.arange(h, dtype=np.float32) + 0.5) / h
        U, V = np.meshgrid(u, v)
        _GRID[k] = (U, V)
    return _GRID[k]


_BORDER = {'clamp': cv2.BORDER_REPLICATE, 'black': cv2.BORDER_CONSTANT, 'wrap': cv2.BORDER_WRAP}


def samp(img, u, v, border='clamp'):
    """Sample img (uint8 HxWx3) at GL uv arrays -> float32 HxWx3 in 0..255 (bilinear)."""
    h, w = img.shape[:2]
    mx = (u * w - 0.5).astype(np.float32)
    my = ((1.0 - v) * h - 0.5).astype(np.float32)
    out = cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=_BORDER[border], borderValue=(0, 0, 0))
    return out.astype(np.float32)


def mix(a, b, m):
    """GLSL mix for images: m scalar or HxW mask."""
    if np.isscalar(m):
        return a + (b - a) * np.float32(m)
    return a + (b - a) * m[..., None]


def where(mask, a, b):
    return np.where(mask[..., None], a, b)


def inb(u, v):
    return (u > 0) & (u < 1) & (v > 0) & (v < 1)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def step(edge, x):
    return (np.asarray(x) >= edge).astype(np.float32)


def _f(img):
    return img.astype(np.float32)


def _u8(x):
    return np.clip(x + 0.5, 0, 255).astype(np.uint8)


def _ratio(img):
    return img.shape[1] / img.shape[0]


def _hash(x, y):
    """GLSL rand(vec2): fract(sin(dot(co, vec2(12.9898, 78.233))) * 43758.5453)."""
    s = np.sin(x * 12.9898 + y * 78.233) * 43758.5453
    return s - np.floor(s)


# ----------------------------------------------------------------------------- 3D / perspective
def cube(a, b, p, persp=0.7, unzoom=0.3, reflection=0.4, floating=3.0, bg=None):
    """3D cube turning from A to B. Author: gre."""
    U, V = _grid(*a.shape[:2])
    uz = unzoom * 2.0 * (0.5 - abs(0.5 - p))
    X = -uz * 0.5 + (1 + uz) * U
    Y = -uz * 0.5 + (1 + uz) * V

    def xskew(px, py, pr, center):
        x = px if center < 0.5 else 1.0 - px
        y = (py - 0.5 * (1.0 - pr) * x) / (1.0 + (pr - 1.0) * x)
        return (x, y) if center < 0.5 else (1.0 - x, y)

    fu, fv = xskew((X - p) / (1.0 - p), Y, 1.0 - p * (1.0 - persp), 0.0)
    tu, tv = xskew(X / p, Y, p * p * (1.0 - persp) + persp, 1.0)
    return _persp_compose(a, b, (fu, fv), (tu, tv), reflection, floating, bg, p)


def _persp_compose(a, b, fp, tp, reflection, floating, bg, p, to_first=False):
    fu, fv = fp
    tu, tv = tp
    base = _background(a, b, p, bg)
    # floor reflection (y is mirrored below the image, fading with height)
    for img, (qu, qv) in ((a, fp), (b, tp)):
        ru, rv = qu, -1.2 * qv - floating / 100.0
        m = inb(ru, rv)
        if m.any() and reflection > 0:
            w = (reflection * (1.0 - rv)) * m
            base = base + samp(img, ru, rv) * w[..., None]
    mf, mt = inb(fu, fv), inb(tu, tv)
    out = base
    if to_first:
        out = where(mf, samp(a, fu, fv), out)
        out = where(mt, samp(b, tu, tv), out)
    else:
        out = where(mt, samp(b, tu, tv), out)
        out = where(mf, samp(a, fu, fv), out)
    return _u8(out)


def _background(a, b, p, bg):
    """None/'black' = original black stage; 'blur' = dark blurred mix of both shots (cleaner on vertical)."""
    if bg in (None, 'black'):
        return np.zeros(a.shape, np.float32)
    if bg == 'blur':
        h, w = a.shape[:2]
        sm = cv2.resize(_u8(mix(_f(a), _f(b), p)), (w // 8, h // 8), interpolation=cv2.INTER_AREA)
        sm = cv2.GaussianBlur(sm, (0, 0), 6)
        return cv2.resize(sm, (w, h), interpolation=cv2.INTER_LINEAR).astype(np.float32) * 0.45
    return np.zeros(a.shape, np.float32) + np.float32(bg)


def doorway(a, b, p, reflection=0.4, perspective=0.4, depth=3.0, bg=None):
    """A opens like two doors, B comes forward from behind. Author: gre."""
    U, V = _grid(*a.shape[:2])
    slit = 2.0 * np.abs(U - 0.5) - p
    open_ = slit > 0
    fu = U + np.where(U > 0.5, -1.0, 1.0) * 0.5 * p
    d = 1.0 / (1.0 + perspective * p * (1.0 - slit))
    fv = (V - d / 2) * d + d / 2
    fu = np.where(open_, fu, -1.0)
    fv = np.where(open_, fv, -1.0)
    size = 1.0 + (depth - 1.0) * (1.0 - p)
    tu = (U - 0.5) * size + 0.5
    tv = (V - 0.5) * size + 0.5
    base = _background(a, b, p, bg)
    ru, rv = tu, -1.2 * tv - 0.02
    m = inb(ru, rv)
    if m.any():
        base = base + samp(b, ru, rv) * (reflection * (1.0 - rv) * m)[..., None]
    out = where(inb(tu, tv), samp(b, tu, tv), base)
    out = where(inb(fu, fv), samp(a, fu, fv), out)
    return _u8(out)


def swap(a, b, p, reflection=0.4, perspective=0.2, depth=3.0, bg=None):
    """Cards swap in 3D: A swings back-left, B comes in from the right. Author: gre."""
    U, V = _grid(*a.shape[:2])
    size = 1.0 + (depth - 1.0) * p
    ps = perspective * p
    fu = U * (size / (1.0 - perspective * p))
    fv = (V - 0.5) * (size / (1.0 - size * ps * U)) + 0.5
    size2 = 1.0 + (depth - 1.0) * (1.0 - p)
    ps2 = perspective * (1.0 - p)
    tu = (U - 1.0) * (size2 / (1.0 - perspective * (1.0 - p))) + 1.0
    tv = (V - 0.5) * (size2 / (1.0 - size2 * ps2 * (0.5 - U))) + 0.5
    return _persp_compose(a, b, (fu, fv), (tu, tv), reflection, 2.0, bg, p, to_first=(p >= 0.5))


def book_flip(a, b, p):
    """Page turn from right to left, with page shading. Author: hong."""
    U, V = _grid(*a.shape[:2])
    e = 1e-4
    dr = 0.5 - p if abs(0.5 - p) > e else e
    dl = p - 0.5 if abs(p - 0.5) > e else e
    rx = (U - p) / dr * 0.5
    ry = (V - 0.5) / (0.5 + p * (U - 0.5) / 0.5) * 0.5 + 0.5
    lx = (U - 0.5) / dl * 0.5 + 0.5
    ly = (V - 0.5) / (0.5 + (1.0 - p) * (0.5 - U) / 0.5) * 0.5 + 0.5
    shade = max(0.7, abs(p - 0.5) * 2.0)
    pr = step(1.0 - p, U)
    left = U < 0.5
    A, B = _f(a), _f(b)
    out_l = mix(A, samp(b, lx, ly) * shade, pr)
    out_r = mix(samp(a, rx, ry) * shade, B, pr)
    return _u8(where(left, out_l, out_r))


def grid_flip(a, b, p, cols=3, rows=5, pause=0.1, divider=0.05, randomness=0.1):
    """Tiles flip one by one like cards (black grid lines). Author: TimDonselaar. Default grid fits 9:16."""
    U, V = _grid(*a.shape[:2])
    sx, sy = float(cols), float(rows)
    rw, rh = 1.0 / sx, 1.0 / sy
    px, py = np.floor(sx * U), np.floor(sy * V)
    minx = np.minimum(np.abs(U - rw * px), np.abs(U - rw * (px + 1)))
    miny = np.minimum(np.abs(V - rh * (py + 1)), np.abs(V - rh * py))
    on_div = np.minimum(minx, miny) < min(rw, rh) * divider
    A, B = _f(a), _f(b)
    black = np.zeros_like(A)
    if p < pause:
        al = np.where(on_div, 1.0 - p / pause, 1.0).astype(np.float32)
        return _u8(mix(black, A, al))
    if p >= 1.0 - pause:
        al = np.where(on_div, (p - 1.0 + pause) / pause, 1.0).astype(np.float32)
        return _u8(mix(black, B, al))
    cp_ = (p - pause) / (1.0 - 2 * pause)
    r = _hash(px, py) - randomness
    cp = smoothstep(0.0, 1.0 - r, cp_)
    delta = px * rw
    off = rw / 2 + delta
    k = np.maximum(np.abs(cp - 0.5), 1e-4)
    qu = (U - off) / k * 0.5 + off
    fa, fb = samp(a, qu, V), samp(b, qu, V)
    s = (k >= np.abs(sx * (U - delta) - 0.5)).astype(np.float32)
    face = where(cp <= 0.5, fa, fb)
    out = mix(black, face, s)
    out = where(on_div, black, out)
    return _u8(out)


# ----------------------------------------------------------------------------- warps
def crosswarp(a, b, p):
    """Left-to-right warp: A shrinks into the right edge, B grows out of the left. Author: Eke Péter."""
    U, V = _grid(*a.shape[:2])
    x = smoothstep(0.0, 1.0, p * 2.0 + U - 1.0)
    A = samp(a, (U - 0.5) * (1 - x) + 0.5, (V - 0.5) * (1 - x) + 0.5)
    B = samp(b, (U - 0.5) * x + 0.5, (V - 0.5) * x + 0.5)
    return _u8(mix(A, B, x))


def directional_warp(a, b, p, direction=(-1.0, 1.0), smoothness=0.1):
    """Diagonal warp wipe (default: towards the top-left). Author: pschroen."""
    U, V = _grid(*a.shape[:2])
    vx, vy = np.array(direction, np.float32) / np.linalg.norm(direction)
    s = abs(vx) + abs(vy)
    vx, vy = vx / s, vy / s
    d = vx * 0.5 + vy * 0.5
    m = 1.0 - smoothstep(-smoothness, 0.0, vx * U + vy * V - (d - 0.5 + p * (1.0 + smoothness)))
    A = samp(a, (U - 0.5) * (1 - m) + 0.5, (V - 0.5) * (1 - m) + 0.5)
    B = samp(b, (U - 0.5) * m + 0.5, (V - 0.5) * m + 0.5)
    return _u8(mix(A, B, m))


def swirl(a, b, p, radius=1.0, turns=4.0):
    """Whirlpool twist in the middle of the cut. Author: Sergey Kosarevsky (port by gre).
    turns: original 8 (very heavy); 4 keeps the car readable longer."""
    U, V = _grid(*a.shape[:2])
    x, y = U - 0.5, V - 0.5
    dist = np.sqrt(x * x + y * y)
    pct = np.clip((radius - dist) / radius, 0, None)
    amt = p / 0.5 if p <= 0.5 else 1.0 - (p - 0.5) / 0.5
    th = pct * pct * amt * turns * np.pi
    c, s = np.cos(th), np.sin(th)
    qx = x * c - y * s
    qy = x * s + y * c
    qx = np.where(dist < radius, qx, x) + 0.5
    qy = np.where(dist < radius, qy, y) + 0.5
    return _u8(mix(samp(a, qx, qy), samp(b, qx, qy), p))


def ripple(a, b, p, amplitude=100.0, speed=50.0):
    """Water ripple from the centre. Author: gre."""
    U, V = _grid(*a.shape[:2])
    dx, dy = U - 0.5, V - 0.5
    dist = np.sqrt(dx * dx + dy * dy)
    k = (np.sin(p * dist * amplitude - p * speed) + 0.5) / 30.0 * p
    A = samp(a, U + dx * k, V + dy * k)
    return _u8(mix(A, _f(b), float(smoothstep(0.2, 1.0, p))))


def morph(a, b, p, strength=0.1):
    """Colours push the pixels: A melts into B along its own shapes. Author: paniq."""
    U, V = _grid(*a.shape[:2])
    A, B = _f(a) / 255.0, _f(b) / 255.0
    oa_x, oa_y = A[..., 0] + A[..., 2] - 1.0, A[..., 1] + A[..., 2] - 1.0
    ob_x, ob_y = B[..., 0] + B[..., 2] - 1.0, B[..., 1] + B[..., 2] - 1.0
    ox, oy = (oa_x + ob_x) * 0.5 * strength, (oa_y + ob_y) * 0.5 * strength
    w0, w1 = p, 1.0 - p
    fa = samp(a, U + ox * w0, V + oy * w0)
    fb = samp(b, U - ox * w1, V - oy * w1)
    return _u8(mix(fa, fb, p))


def kaleidoscope(a, b, p, speed=1.0, angle=1.0, power=1.5):
    """Mirror-kaleidoscope burst at the middle of the cut. Author: nwoeanhinnogaehr."""
    U, V = _grid(*a.shape[:2])
    t = (p ** power) * speed
    x, y = U - 0.5, V - 0.5
    for _ in range(7):
        x, y = np.sin(t) * x + np.cos(t) * y, np.sin(t) * y - np.cos(t) * x
        t += angle
        x = np.abs(np.mod(x, 2.0) - 1.0)
        y = np.abs(np.mod(y, 2.0) - 1.0)
    plain = mix(_f(a), _f(b), p)
    kal = mix(samp(a, x, y), samp(b, x, y), p)
    return _u8(mix(plain, kal, 1.0 - 2.0 * abs(p - 0.5)))


def flyeye(a, b, p, size=0.04, zoom=50.0, separation=0.3):
    """Insect-eye lens grid with RGB split. Author: gre."""
    U, V = _grid(*a.shape[:2])
    inv = 1.0 - p
    dx, dy = size * np.cos(zoom * U), size * np.sin(zoom * V)
    to = samp(b, U + inv * dx, V + inv * dy)
    fr = np.empty_like(to)
    for ch, k in ((0, 1.0 - separation), (1, 1.0), (2, 1.0 + separation)):
        fr[..., ch] = samp(a, U + p * dx * k, V + p * dy * k)[..., ch]
    return _u8(to * p + fr * inv)


def squeeze(a, b, p, separation=0.04):
    """A squeezes flat to a line (with RGB split), revealing B. Author: gre."""
    U, V = _grid(*a.shape[:2])
    if p >= 1:
        return b.copy()
    y = 0.5 + (V - 0.5) / (1.0 - p)
    inside = (y >= 0) & (y <= 1)
    off = p * separation
    c = samp(a, U, y)
    out = c.copy()
    out[..., 0] = samp(a, U, y - off)[..., 0]
    out[..., 2] = samp(a, U, y + off)[..., 2]
    return _u8(where(inside, out, _f(b)))


# ----------------------------------------------------------------------------- spins / pushes with motion blur
def revolve(a, b, p, center=(0.46, 0.52), direction=-1.0, max_rot=1.95, peak_zoom=2.22, swirl_amt=2.85,
            barrel=0.38, blur=1.0, switch=(0.30, 0.50), shadow=0.16, samples=9):
    """Spin + zoom + lens barrel with real motion blur — a heavy, smooth 'revolve' cut. Author: Revolve_Left.

    samples: motion-blur taps (original 17; 9 looks the same at 1080p and is 2x faster)."""
    if p <= 0:
        return a.copy()
    if p >= 1:
        return b.copy()
    U, V = _grid(*a.shape[:2])
    ratio = _ratio(a)
    sat = lambda x: min(max(x, 0.0), 1.0)
    ease = lambda x: sat(x) * sat(x) * (3 - 2 * sat(x))
    env = lambda t: ease((t - 0.10) / 0.33) * (1.0 - ease((t - 0.43) / 0.29))
    cx, cy = center
    X0 = (U - cx) * ratio
    Y0 = V - cy
    R0 = np.sqrt(X0 * X0 + Y0 * Y0)
    core = np.power(1.0 - np.clip(R0 / 0.96, 0, 1), 1.55)

    def warp(t):
        e = env(t)
        ang = direction * (max_rot * e + swirl_amt * e * core)
        c, s = np.cos(-ang), np.sin(-ang)
        x, y = c * X0 - s * Y0, s * X0 + c * Y0
        sc = 1.0 + (peak_zoom - 1.0) * e ** 0.85
        x, y = x / sc, y / sc
        rr2 = x * x + y * y
        k = 1.0 + barrel * e * rr2 * 2.8
        x, y = x * k / ratio, y * k
        return np.clip(x + cx, 0.001, 0.999), np.clip(y + cy, 0.001, 0.999)

    e = env(p)
    span = 0.060 * blur * e
    n = max(1, samples // 2)
    acc, tot = 0.0, 0.0
    taps = [0.0] if span < 1e-4 else [i / n for i in range(-n, n + 1)]
    for x in taps:
        w = (1.0 - abs(x)) ** 2 + 0.01
        t = sat(p + x * span)
        qu, qv = warp(t)
        rv = float(smoothstep(switch[0], switch[1], t))
        col = samp(a, qu, qv) if rv <= 0 else (samp(b, qu, qv) if rv >= 1 else mix(samp(a, qu, qv), samp(b, qu, qv), rv))
        acc = acc + col * w
        tot += w
    col = acc / tot
    qx, qy = (U - 0.5) * ratio, V - 0.5
    vig = 1.0 - shadow * e * smoothstep(0.35, 0.95, np.sqrt(qx * qx + qy * qy))
    return _u8(col * vig[..., None])


def _keyspline(x, x1, y1, x2, y2):
    A = lambda a1, a2: 1 - 3 * a2 + 3 * a1
    B = lambda a1, a2: 3 * a2 - 6 * a1
    C = lambda a1: 3 * a1
    bez = lambda t, a1, a2: ((A(a1, a2) * t + B(a1, a2)) * t + C(a1)) * t
    slope = lambda t, a1, a2: 3 * A(a1, a2) * t * t + 2 * B(a1, a2) * t + C(a1)
    t = x
    for _ in range(4):
        sl = slope(t, x1, x2)
        if sl == 0:
            break
        t -= (bez(t, x1, x2) - x) / sl
    return bez(t, y1, y2)


def tangent_blur(a, b, p, samples=12, seed=0):
    """A swings away around the corner with heavy motion blur, B swings in. Author: chenkai."""
    h, w = a.shape[:2]
    U, V = _grid(h, w)
    ratio = _ratio(a)
    et = _keyspline(p, .68, .01, .17, .98)
    blur = np.exp(-20.0 * (et - 0.5) ** 2)
    rot = np.pi

    def rot_uv(t):
        r = rot * t if t <= 0.5 else -rot + rot * t
        y = V / ratio
        c, s = np.cos(r), np.sin(r)
        x0, y0 = U - 1.0, y
        x1 = c * x0 + s * y0
        y1 = -s * x0 + c * y0
        return x1 + 1.0, y1 * ratio

    cu, cv_ = rot_uv(et)
    dt = 0.0167 * 2.0
    nu, nv = rot_uv(et + dt)
    spu, spv = (nu - cu) / dt * blur * 0.5, (nv - cv_) / dt * blur * 0.5
    src = a if et <= 0.5 else b
    rng = np.random.default_rng(seed)
    off = rng.random((h, w), dtype=np.float32)
    acc = np.zeros((h, w, 3), np.float32)
    tot = 0.0
    for i in range(samples + 1):
        pc = (i + off) / samples
        wt = 4.0 * (pc - pc * pc)
        qu, qv = cu + spu * pc, cv_ + spv * pc
        qu, qv = qu - np.floor(qu), qv - np.floor(qv)
        acc += samp(src, qu, qv, 'wrap') * wt[..., None]
        tot = tot + wt
    return _u8(acc / tot[..., None])


def push_scaled(a, b, p, direction=(0.0, 1.0), scale=0.7):
    """A pushes out as a shrinking card while B pushes in (default: upwards). Author: Thibaut Foussard."""
    U, V = _grid(*a.shape[:2])
    ep = np.sin(p * np.pi / 2) ** 3
    sx, sy = np.sign(direction[0]), np.sign(direction[1])
    px, py = U + ep * sx, V + ep * sy
    fx, fy = px - np.floor(px), py - np.floor(py)
    s = 1.0 - (1.0 - 1.0 / scale) * np.sin(p * np.pi)
    fx, fy = (fx - 0.5) * s + 0.5, (fy - 0.5) * s + 0.5
    on_a = (px >= 0) & (px <= 1) & (py >= 0) & (py <= 1)
    col = where(on_a, samp(a, fx, fy), samp(b, fx, fy))
    border = (fx >= 0) & (fx <= 1) & (fy >= 0) & (fy <= 1)
    return _u8(col * border[..., None])


def window_slice(a, b, p, count=6.0, smoothness=0.5):
    """Venetian-blind slices sweep across. Author: gre. count=6 suits 9:16."""
    U, V = _grid(*a.shape[:2])
    pr = smoothstep(-smoothness, 0.0, U - p * (1.0 + smoothness))
    fr = count * U
    s = (fr - np.floor(fr) >= pr).astype(np.float32)
    return _u8(mix(_f(a), _f(b), s))


# ============================================================================= pack 2 (numbers 25-48)
def _h1(n):
    s = np.sin(n) * 43758.5453123
    return s - np.floor(s)


def _h2(x, y, k=(127.1, 311.7)):
    s = np.sin(x * k[0] + y * k[1]) * 43758.5453123
    return s - np.floor(s)


def _fract(x):
    return x - np.floor(x)


def page_curl(a, b, p, back='image'):
    """Page curls away, with the curl's shadow on the next page. back='image': the back of the page shows A
    darkened (house taste, no white sheet); back='paper': the original light-grey paper back.
    Inverted Page Curl, Copyright (c) 2010 Hewlett-Packard Development Company, L.P. (BSD 3-Clause)."""
    U, V = _grid(*a.shape[:2])
    A, B = _f(a) / 255.0, _f(b) / 255.0
    PI = np.pi
    R = 1.0 / PI / 2.0
    amount = p * (1.5 + 0.16) - 0.16
    cyl_c, cyl_a = amount, 2 * PI * amount
    ang = 100.0 * PI / 180.0
    c1, s1 = np.cos(-ang), np.sin(-ang)
    c2, s2 = np.cos(ang), np.sin(ang)
    px = c1 * U - s1 * V - 0.801            # rotation * (p, 1), GLSL mat3 is column-major
    py = s1 * U + c1 * V + 0.89

    def hit(hit_angle, qx):
        qy = hit_angle / (2 * PI)
        return c2 * qx - s2 * qy + 0.985, s2 * qx + c2 * qy + 0.985

    def d_edge(x, y):
        dx = np.where(x > 0.5, 1.0 - x, x)
        dy = np.where(y > 0.5, 1.0 - y, y)
        dx = np.where(x < 0, -x, np.where(x > 1, x - 1, dx))
        dy = np.where(y < 0, -y, np.where(y > 1, y - 1, dy))
        out_x, out_y = (x < 0) | (x > 1), (y < 0) | (y > 1)
        return np.where(out_x & out_y, np.sqrt(dx * dx + dy * dy), np.minimum(np.abs(dx), np.abs(dy)))

    def aa(c1_, c2_, d):
        d = d * 512.0
        dd = np.power(np.clip(1.0 - d / 2.0, 0, 1), 3.0)[..., None]
        out = (c2_ - c1_) * dd + c1_
        return np.where((d < 0)[..., None], c2_, np.where((d > 2)[..., None], c1_, out))

    def s_from(x, y):
        return samp(a, x, y) / 255.0

    yc = py - cyl_c
    acos_ = np.arccos(np.clip(yc / R, -1, 1))
    # see-through (used for the curl region and its shadow)
    ha_s = PI - (acos_ - cyl_a)
    sx, sy = hit(ha_s, px)
    oob_s = (sx < 0) | (sy < 0) | (sx > 1) | (sy > 1)
    st = aa(s_from(sx, sy), np.zeros_like(A), d_edge(sx, sy))
    st = where(yc > 0, A, where((yc <= 0) & oob_s, B, st))
    # front of the curl
    ha = acos_ + cyl_a - PI
    hx, hy = hit(ha, px)
    shadow = (1.0 - d_edge(hx, hy) * 30.0) / 3.0
    shadow = np.where(shadow < 0, 0.0, shadow * amount)
    st_sh = st - shadow[..., None]
    col = s_from(hx, hy)
    curv = np.power(np.maximum(0.0, 1.0 - np.abs(yc / R)), 0.2)
    if back == 'paper':
        gray = col.sum(-1) / 15.0 + 0.8 * (curv / 2 + 0.5)
        back = np.repeat(gray[..., None], 3, -1)
    else:
        back = col * (0.35 + 0.3 * curv)[..., None]
    sh2 = (1.0 - np.sqrt((hx - 0.5) ** 2 + (hy - 0.5) ** 2) / 0.71) * np.power(np.maximum(-yc / R, 0), 3) * 0.5
    other = where(yc < 0, np.zeros_like(A) * sh2[..., None], A)
    front = aa(back, other, R - np.abs(yc))
    front = aa(front, st_sh, d_edge(hx, hy))
    hmod = np.mod(ha, 2 * PI)
    see = ((hmod > PI) & (amount < 0.5)) | ((hmod > PI / 2) & (amount < 0.0))
    oob_h = (hx < 0) | (hy < 0) | (hx > 1) | (hy > 1)
    mid = where(see, st, where(oob_h, st_sh, front))
    # behind the curl: next page with the curl's shadow
    safe = max(amount, 1e-4) if amount >= 0 else min(amount, -1e-4)
    yc2 = -R - R - yc
    ha2 = np.arccos(np.clip(yc2 / R, -1, 1)) + cyl_a - PI
    bx, by = hit(ha2, px)
    ok = (yc2 < 0) & (bx >= 0) & (by >= 0) & (bx <= 1) & (by <= 1) & ((ha2 < PI) | (amount > 0.5))
    sh3 = (1.0 - np.sqrt((bx - 0.5) ** 2 + (by - 0.5) ** 2) / 0.71) * np.power(np.maximum(-yc2 / R, 0), 3) * 0.5
    behind = B - np.where(ok, sh3, 0.0)[..., None]
    out = where(yc < -R, behind, where(yc > R, A, mid))
    return _u8(np.clip(out, 0, 1) * 255.0)


def shatter(a, b, p, pieces=10, seed=0.0):
    """A breaks into Voronoi shards that fly away, revealing B. Author: Dmitrii (gl-transitions 'fragment')."""
    U, V = _grid(*a.shape[:2])

    def rnd(x, y):
        return _fract(np.sin(x * 12.9898 + y * 78.233) * 43758.5453)

    def rnd2(x, y):
        r = rnd(x, y)
        return r, rnd(x + r, y + r)

    pts = [rnd2(float(i) + seed, float(i) + seed) for i in range(pieces)]
    t = p * 8.0
    out = _f(b)
    done = np.zeros(U.shape, bool)
    for i in range(pieces):
        dx, dy = rnd2(float(i) + seed, float(i) + 11.0 + seed)
        n = np.hypot(dx, dy) + 1e-9
        dx, dy = dx / n, dy / n
        v = (1.0 + rnd(dx, dy) * 0.5) * 0.2
        k = min(max(t - 0.5, 0.0), 8.0) * v
        qx, qy = U - dx * k, V - dy * k
        inside = (qx >= 0) & (qx <= 1) & (qy >= 0) & (qy <= 1)
        di = (qx - pts[i][0]) ** 2 + (qy - pts[i][1]) ** 2
        closest = np.ones(U.shape, bool)
        for j in range(pieces):
            if j != i:
                closest &= ((qx - pts[j][0]) ** 2 + (qy - pts[j][1]) ** 2) >= di
        m = inside & closest & ~done
        if m.any():
            out = where(m, samp(a, qx, qy), out)
            done |= m
    return _u8(out)


def mosaic(a, b, p, endx=2, endy=-1):
    """Camera pulls back over a wall of rotated tiles of both shots and lands on B. Author: Xaychru."""
    U, V = _grid(*a.shape[:2])
    x, y = U - 0.5, V - 0.5
    rpr = p * 2.0 - 1.0
    z = abs(-(rpr * rpr * 2.0) + 3.0)
    ci = (-np.cos(p * np.pi) / 2 + 0.5) ** 2
    rx = x * z + 0.5 + (endx + 0.5 - 0.5) * ci
    ry = y * z + 0.5 + (endy + 0.5 - 0.5) * ci
    fx, fy = np.floor(rx), np.floor(ry)
    mx, my = rx - fx, ry - fy
    on_end = (fx == endx) & (fy == endy)
    r = _fract(np.sin(fx * 12.9898 + fy * 78.233) * 43758.5453)
    angl = np.floor(r * 4.0) * 0.5 * np.pi
    c, s = np.cos(angl), np.sin(angl)
    qx, qy = mx - 0.5, my - 0.5
    rx2, ry2 = c * qx + s * qy + 0.5, -s * qx + c * qy + 0.5
    mx, my = np.where(on_end, mx, rx2), np.where(on_end, my, ry2)
    use_b = on_end | (r > 0.5)
    return _u8(where(use_b, samp(b, mx, my), samp(a, mx, my)))


def doom_melt(a, b, p, bars=30, amplitude=2.0, noise=0.1, frequency=0.5, drip=0.5):
    """Columns of A melt down at different speeds (the DOOM screen wipe). Author: Zeh Fernando."""
    U, V = _grid(*a.shape[:2])
    n = np.arange(bars, dtype=np.float64)
    rnd = _fract(np.mod(n * 67123.313, 12.0) * np.sin(n * 10.3) * np.cos(n))
    fn = n * frequency * 0.1 * bars
    wave = np.cos(fn * 0.5) * np.cos(fn * 0.13) * np.sin((fn + 10.0) * 0.3) / 2.0 + 0.5
    pos = (wave if noise == 0 else wave + (rnd - wave) * noise) + np.sin(n / (bars - 1) * np.pi) * drip
    bar = np.clip((U * bars).astype(int), 0, bars - 1)
    phase = (p * (1.0 + pos * amplitude))[bar].astype(np.float32)
    keep = phase + V < 1.0
    return _u8(where(keep, samp(a, U, V + phase), _f(b)))


def datamosh(a, b, p, strength=1.0, bars=42.0, slits=18.0, tear=0.18, chroma=0.032, residue=0.62, noise=0.06,
             scan=0.13, hairlines=0.12):
    """Broadcast datamosh: torn scan bands, time-slice smear, channel split. Author: StripDatamoshGlitch.
    House taste: the original's strobe flash is removed; noise and white hairlines are turned down."""
    U, V = _grid(*a.shape[:2])
    ratio = _ratio(a)
    sat = lambda x: np.clip(x, 0, 1)
    b_ = max(0.0, np.sin(p * np.pi)) ** 0.42 * strength
    frame = np.floor(p * 30.0)

    def stripe(coord, density, sd, mn, mxw, k_c, k_w, edge, cshift):
        y = coord * density + sd * cshift
        idx = np.floor(y)
        f = y - idx
        c = _h2(idx, sd + k_c)
        w = mn + (mxw - mn) * _h2(idx + k_w[0], sd + k_w[1])
        return 1.0 - smoothstep(w, w + edge, np.abs(f - c))

    sty = lambda d, sd, mn, mx: stripe(V, d, sd, mn, mx, 0.0, (9.17, 2.31), 0.018, 0.137)
    stx = lambda d, sd, mn, mx: stripe(U, d, sd, mn, mx, 41.0, (4.7, 8.9), 0.012, 0.091)

    def gate(row, rnd, fr):
        segs = 1.0 + 8.0 * _h2(row, fr + 44.0)
        return step(0.16, _h2(np.floor(U * segs), row + fr * 3.0 + rnd))

    r1 = np.floor((V + _h1(frame) * 0.031) * bars * 0.38)
    r2 = np.floor((V + _h1(frame + 2) * 0.013) * bars)
    r3 = np.floor((V + _h1(frame + 7) * 0.006) * bars * 3.4)
    thick = sty(bars * 0.38, frame + 1, 0.035, 0.22) * step(0.42, _h2(r1, frame + 10))
    midl = sty(bars, frame + 4, 0.014, 0.11) * step(0.48, _h2(r2, frame + 20))
    hair = sty(bars * 3.4, frame + 9, 0.004, 0.035) * step(0.62, _h2(r3, frame + 30))
    thick *= gate(r1, _h2(r1, frame), frame)
    midl *= gate(r2, _h2(r2, frame), frame + 3)
    h = sat(np.maximum(thick, np.maximum(midl, hair)))
    col_i = np.floor((U + _h1(frame + 12) * 0.017) * slits)
    v = sat(stx(slits, frame + 13, 0.01, 0.075) * step(0.66, _h2(col_i, frame + 19)))
    glitch = sat(np.maximum(h, v * 0.75))
    row = np.floor(V * bars)
    row_r = _h2(row, frame + 5)
    reveal = smoothstep(0.18, 0.84, p + (row_r - 0.5) * 0.30 * h)
    spx, spy = chroma * b_ * (1 + 1.7 * glitch), chroma * 0.22 * b_ * v

    def distort(d):
        rr = _h2(row, frame)
        cr = _h2(np.floor(U * slits), frame + 27)
        xt = (rr - 0.5) * 2 * tear * b_ * h + np.sin(V * 120 + p * 95) * 0.006 * b_
        yd = (cr - 0.5) * 0.13 * b_ * v
        mic = (_h2(row, np.floor(U * slits) + frame) - 0.5) * 0.018 * b_ * np.maximum(h, v)
        return U + xt * d + mic, V + yd

    def chroma_s(img, x, y, sx, sy, sign):
        x, y = np.clip(x, 0, 1), np.clip(y, 0, 1)
        out = samp(img, x, y)
        out[..., 0] = samp(img, np.clip(x + sign * sx, 0, 1), np.clip(y + sign * sy, 0, 1))[..., 0]
        out[..., 2] = samp(img, np.clip(x - sign * sx, 0, 1), np.clip(y - sign * sy, 0, 1))[..., 2]
        return out / 255.0

    fx, fy = distort(1.0)
    tx, ty = distort(-1.0)
    colr = mix(chroma_s(a, fx, fy, spx, spy, 1), chroma_s(b, tx, ty, spx, spy, -1), reveal)
    smx = U + (row_r - 0.5) * 0.46 * b_ * h
    smy = V + (_h2(row, frame + 31) - 0.5) * 0.045 * b_ * h
    srev = smoothstep(0.28, 0.78, p + (row_r - 0.5) * 0.22)
    slice_c = mix(chroma_s(a, smx, smy, spx * 1.65, spy * 1.65, 1),
                  chroma_s(b, smx - (row_r - 0.5) * 0.18 * b_, smy, spx * 1.65, spy * 1.65, -1), srev)
    colr = mix(colr, slice_c, h * b_ * residue)
    hl = sty(190.0, frame + 55, 0.002, 0.012) * step(0.70, _h2(np.floor(V * 190.0), frame + 56))
    colr = colr + np.float32([0.72, 0.90, 1.0]) * (hl * b_ * hairlines)[..., None]
    sc = 0.5 + 0.5 * np.sin(V * 980.0 + p * 130.0)
    colr = colr * (1.0 - scan * b_ * sc)[..., None]
    nn = _h2(np.floor(U * 360.0 * ratio) + frame * 7, np.floor(V * 210.0) + frame * 13)
    colr = colr + ((nn - 0.5) * noise * b_ * (0.55 + glitch))[..., None]
    lum = colr @ np.float32([0.299, 0.587, 0.114])
    colr = mix(colr, np.repeat(lum[..., None], 3, -1), 0.18 * b_ * glitch)
    return _u8(np.clip(colr, 0, 1) * 255.0)


def _snoise_x(x):
    """GLSL 2D simplex noise (Ashima / Ian McEwan, MIT) evaluated at (x, 0) — vectorised."""
    C = (0.211324865405187, 0.366025403784439, -0.577350269189626, 0.024390243902439)
    vx, vy = x, np.zeros_like(x)
    mod289 = lambda q: q - np.floor(q * (1.0 / 289.0)) * 289.0
    perm = lambda q: mod289(((q * 34.0) + 1.0) * q)
    s = (vx + vy) * C[1]
    ix, iy = np.floor(vx + s), np.floor(vy + s)
    t = (ix + iy) * C[0]
    x0, y0 = vx - ix + t, vy - iy + t
    i1x = (x0 > y0).astype(np.float64)
    i1y = 1.0 - i1x
    x12 = [x0 + C[0] - i1x, y0 + C[0] - i1y, x0 + C[2], y0 + C[2]]
    ix, iy = mod289(ix), mod289(iy)
    pp = [perm(perm(iy + o_y) + ix + o_x) for o_y, o_x in ((0.0, 0.0), (i1y, i1x), (1.0, 1.0))]
    m = [np.maximum(0.5 - (x0 * x0 + y0 * y0), 0), np.maximum(0.5 - (x12[0] ** 2 + x12[1] ** 2), 0),
         np.maximum(0.5 - (x12[2] ** 2 + x12[3] ** 2), 0)]
    m = [q ** 4 for q in m]
    g = 0.0
    for k, (gx_, gy_) in enumerate(((x0, y0), (x12[0], x12[1]), (x12[2], x12[3]))):
        xx = 2.0 * _fract(pp[k] * C[3]) - 1.0
        hh = np.abs(xx) - 0.5
        a0 = xx - np.floor(xx + 0.5)
        mk = m[k] * (1.79284291400159 - 0.85373472095314 * (a0 * a0 + hh * hh))
        g = g + mk * (a0 * gx_ + hh * gy_)
    return 130.0 * g


def luma_melt(a, b, p, threshold=0.8, above=False):
    """Dark parts of A melt away first (by luminance) in noisy drips. Author: 0gust1."""
    U, V = _grid(*a.shape[:2])
    A, B = _f(a), _f(b)
    xs = U[0].astype(np.float64)
    sn = np.exp(_snoise_x(xs))[None, :]
    rr = _fract(np.sin(xs * 12.9898 + 0.1 * 78.233) * 43758.5453)[None, :]
    dist = np.sqrt((1.0 - U) ** 2 + (1.0 - V) ** 2) - p * sn
    r = p - rr
    lum = (A @ np.float32([0.299, 0.587, 0.114])) / 255.0
    cond = (dist <= r) & ((lum > threshold) if above else (lum < threshold))
    m = np.where(cond, 1.0, p ** 3).astype(np.float32)
    return _u8(mix(A, B, m))


def bounce(a, b, p, shadow_alpha=0.6, shadow_height=0.075, bounces=3.0):
    """A drops out of the frame bouncing, with a soft shadow on B. Author: Adrian Purser."""
    U, V = _grid(*a.shape[:2])
    st = np.sin(p * np.pi / 2)
    y = abs(np.cos(p * np.pi * bounces)) * (1.0 - st)
    d = V - y
    fade = float(smoothstep(0.95, 1.0, p))
    k = (shadow_height >= d) * (1.0 - (((d / shadow_height) * shadow_alpha + (1 - shadow_alpha)) * (1 - fade) + fade))
    inner = mix(_f(b), np.zeros_like(_f(b)), k.astype(np.float32))
    return _u8(where(d <= 0, samp(a, U, V + (1.0 - y)), inner))


def dreamy(a, b, p):
    """Wavy dream dissolve. Author: mikolalysenko."""
    U, V = _grid(*a.shape[:2])
    off = lambda pr, x: 0.03 * pr * np.cos(10.0 * (pr + x))
    return _u8(mix(samp(a, U, V + off(p, U)), samp(b, U, V + off(1 - p, U)), p))


_DEFOCUS = ((-0.326, -0.406), (-0.840, -0.074), (-0.696, 0.457), (-0.203, 0.621), (0.962, -0.195), (0.473, -0.480),
            (0.519, 0.767), (0.185, -0.893), (0.507, 0.064), (0.896, 0.412), (-0.322, -0.933), (-0.792, -0.598))


def defocus(a, b, p, blur=0.02):
    """Lens goes out of focus on A and comes back in focus on B. Author: Jacobo Fernandez."""
    U, V = _grid(*a.shape[:2])
    D = blur * (p / 0.5 if p < 0.5 else 1.0 - (p - 0.5) / 0.5)
    ca, cb = _f(a).copy(), _f(b).copy()
    for ox, oy in _DEFOCUS:
        ca += samp(a, U + ox * D, V + oy * D)
        cb += samp(b, U + ox * D, V + oy * D)
    return _u8(mix(ca / 13.0, cb / 13.0, p))


def cross_zoom(a, b, p, strength=0.4, samples=16, seed=1):
    """Classic zoom-blur cross: blur rushes towards a moving centre while the shots swap. Author: rectalogic."""
    h, w = a.shape[:2]
    U, V = _grid(h, w)
    cx = 0.25 + 0.5 * p
    if p == 0:
        dis = 0.0
    else:
        tt = p / 0.5
        dis = 0.5 * 2 ** (10 * (tt - 1)) if tt < 1 else 0.5 * (-2 ** (-10 * (tt - 1)) + 2)
    st = -strength / 2.0 * (np.cos(np.pi * p / 0.5) - 1.0)
    tx, ty = cx - U, 0.5 - V
    off = np.random.default_rng(seed).random((h, w), dtype=np.float32)
    acc = np.zeros((h, w, 3), np.float32)
    tot = np.zeros((h, w), np.float32)
    for i in range(samples + 1):
        pc = (i + off) / samples
        wt = 4.0 * (pc - pc * pc)
        qx, qy = U + tx * pc * st, V + ty * pc * st
        acc += mix(samp(a, qx, qy), samp(b, qx, qy), dis) * wt[..., None]
        tot += wt
    return _u8(acc / tot[..., None])


def zoom_circles(a, b, p):
    """Rings around the centre zoom at different speeds, then burst open onto B. Author: dycm8009."""
    U, V = _grid(*a.shape[:2])
    ratio = _ratio(a)
    rx, ry = 2 * (U - 0.5), 2 * (V - 0.5) / ratio
    L = np.sqrt(rx * rx + ry * ry)
    pro = p / 0.8
    z, t = pro * 0.2, 0.0
    if pro > 1.0:
        z = 0.2 + (pro - 1.0) * 5.0
        t = min(max((p - 0.8) / 0.07, 0.0), 1.0)
    zoomf = np.where(L < 0.5 + z, 1.0, np.where(L < 0.8 + z * 1.5, 1 - 0.15 * pro,
                                                  np.where(L < 1.2 + z * 2.5, 1 - 0.2 * pro, 1 - 0.25 * pro)))
    tt = np.where(L < 0.5 + z, t, np.where(L < 0.8 + z * 1.5, t * 0.5, np.where(L < 1.2 + z * 2.5, t * 0.2, 0.0)))
    qx, qy = 0.5 + (U - 0.5) * zoomf, 0.5 + (V - 0.5) * zoomf
    return _u8(mix(samp(a, qx, qy), samp(b, qx, qy), tt.astype(np.float32)))


def rotate_vanish(a, b, p):
    """A spins one full turn while shrinking into the centre; B fades in. Author: Mark Craig."""
    U, V = _grid(*a.shape[:2])
    ratio = _ratio(a)
    th = -2 * np.pi * p
    c, s = np.cos(th), np.sin(th)
    rad = max(1e-5, 1.0 - p)
    x1, y1 = (U - 0.5) * ratio, V - 0.5
    x2, y2 = (x1 * c - y1 * s) / rad + ratio / 2, (x1 * s + y1 * c) / rad + 0.5
    inside = (x2 >= 0) & (x2 <= ratio) & (y2 >= 0) & (y2 <= 1)
    col = where(inside, samp(a, x2 / ratio, y2), np.zeros_like(_f(a)))
    return _u8((1 - p) * col + p * _f(b))


def fold(a, b, p):
    """B unfolds from the left while A is squashed to the right. Author: nwoeanhinnogaehr."""
    U, V = _grid(*a.shape[:2])
    A = samp(a, (U - p) / (1.0 - p), V)
    B = samp(b, U / p, V)
    return _u8(where(U <= p, B, A))


def tiles_wave(a, b, p, cols=6, rows=10, flip_x=True, flip_y=False):
    """Tiles turn over one after another in a wave. Author: Gernot Plank. 6x10 tiles suit 9:16."""
    U, V = _grid(*a.shape[:2])
    tw, th = 1.0 / cols, 1.0 / rows
    tx, ty = np.floor(U * cols), np.floor(V * rows)
    px, py = _fract(U * cols), _fract(V * rows)
    count = cols * rows
    off = (ty + tx * rows) / count
    to = np.clip((p - off) * count, 0.0, 0.5)
    st = 1.0 - np.abs(np.cos(_fract(to) * np.pi))
    first = st <= 0.5
    k = 0.5 - st
    k = np.where(np.abs(k) < 1e-4, 1e-4, k)
    out_x = (px < st) | (px > 1 - st)
    out_y = (py < st) | (py > 1 - st)
    in_x2 = (px > st) | (px < 1 - st)
    in_y2 = (py > st) | (py < 1 - st)
    cx = np.where(px < 0.5, (px - st) * 0.5 / k, (px - 0.5) * 0.5 / k + 0.5)
    cy = np.where(py < 0.5, (py - st) * 0.5 / k, (py - 0.5) * 0.5 / k + 0.5)
    qx = cx if flip_x else px
    qy = cy if flip_y else py
    qx2 = 1.0 - cx if flip_x else px
    qy2 = 1.0 - cy if flip_y else py
    fa = samp(a, tx * tw + qx * tw, ty * th + qy * th)
    fb = samp(b, tx * tw + qx2 * tw, ty * th + qy2 * th)
    A, B = _f(a), _f(b)
    keep_a = (out_x if flip_x else False) | (out_y if flip_y else False)
    keep_b = (in_x2 if flip_x else False) | (in_y2 if flip_y else False)
    first_c = where(keep_a, A, fa) if np.any(keep_a) else fa
    second_c = where(keep_b, B, fb) if np.any(keep_b) else fb
    return _u8(where(first, first_c, second_c))


def hexagonalize(a, b, p, steps=50, hexagons=20.0):
    """Shots dissolve through growing hexagon cells. Author: Fernando Kuteken."""
    U, V = _grid(*a.shape[:2])
    ratio = _ratio(a)
    dist = 2.0 * min(p, 1.0 - p)
    dist = np.ceil(dist * steps) / steps if steps > 0 else dist
    if dist <= 0:
        return _u8(mix(_f(a), _f(b), p))
    size = (np.sqrt(3.0) / 3.0) * dist / hexagons
    x, y = (U - 0.5) / size, (V / ratio - 0.5) / size
    q, r = (np.sqrt(3.0) / 3.0) * x - y / 3.0, 2.0 / 3.0 * y
    s = -q - r
    rq, rr, rs = np.floor(q + 0.5), np.floor(r + 0.5), np.floor(s + 0.5)
    dq, dr, ds = np.abs(rq - q), np.abs(rr - r), np.abs(rs - s)
    c1 = (dq > dr) & (dq > ds)
    c2 = ~c1 & (dr > ds)
    rq = np.where(c1, -rr - rs, rq)
    rr = np.where(c2, -rq - rs, rr)
    px = (np.sqrt(3.0) * rq + (np.sqrt(3.0) / 2.0) * rr) * size + 0.5
    py = ((3.0 / 2.0) * rr * size + 0.5) * ratio
    return _u8(mix(samp(a, px, py), samp(b, px, py), p))


def perlin(a, b, p, scale=4.0, smoothness=0.01, seed=12.9898):
    """Organic cloud-noise dissolve. Author: Rich Harris."""
    U, V = _grid(*a.shape[:2])

    def rnd(x, y):
        dt = x * seed + y * 78.233
        return _fract(np.sin(np.mod(dt, 3.14)) * 43758.5453)

    sx, sy = U * scale, V * scale
    ix, iy = np.floor(sx), np.floor(sy)
    fx, fy = sx - ix, sy - iy
    ra, rb, rc, rd = rnd(ix, iy), rnd(ix + 1, iy), rnd(ix, iy + 1), rnd(ix + 1, iy + 1)
    ux, uy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    n = ra + (rb - ra) * ux + (rc - ra) * uy * (1 - ux) + (rd - rb) * ux * uy
    pp = -smoothness + (1 + 2 * smoothness) * p
    q = smoothstep(pp - smoothness, pp + smoothness, n)
    return _u8(mix(_f(a), _f(b), (1.0 - q).astype(np.float32)))


def burn_out(a, b, p, smoothness=0.03, center=(0.5, 0.5), color=(0, 0, 0)):
    """An undulating dark-rimmed hole burns open from the centre. Author: pthrasher."""
    U, V = _grid(*a.shape[:2])
    dx, dy = U - center[0], V - center[1]
    dist = np.sqrt(dx * dx + dy * dy)
    degs = (np.degrees(np.arctan2(dy, dx)) + 180.0) * ((np.pi * 30.0) / 360.0)
    mag = 0.02 + 0.07 * float(smoothstep(0, 1, p))
    offs = 40.0 - 10.0 * float(smoothstep(0, 1, p))
    sd = np.sin(degs)
    q = np.where(sd < 0.5, 2 * sd * sd, -2 * sd * sd + 4 * sd - 1)
    r = p + q * mag * np.sin(p * offs)
    d = r - dist
    g = np.where((d >= -0.005) & (d <= 0.01), -1.0 - (d >= 0.005), smoothstep(-smoothness, 0.0, r - dist * (1 + smoothness)))
    A, B = _f(a), _f(b)
    base = mix(A, B, np.clip(g, 0, 1).astype(np.float32))
    rim = mix(A, np.zeros_like(A) + np.float32(color), 0.75)
    return _u8(where(g <= -2.0, rim, base))


def power_kaleido(a, b, p, scale=2.0, z=1.5, speed=5.0):
    """Spinning triangle-mirror kaleidoscope between the shots. Author: Boundless."""
    U, V = _grid(*a.shape[:2])
    ratio = _ratio(a)
    dist = scale / 10.0
    deg = 120.0 / 180.0 * np.pi

    def rot(x, y, ox, oy, ang):
        c, s = np.cos(ang), np.sin(ang)
        x, y = x - ox, y - oy
        return ox + c * x + s * y, oy - s * x + c * y

    x, y = (U - 0.5) * ratio * z, (V - 0.5) * z
    x, y = rot(x, y, 0.0, 0.0, p * speed)
    angles = [i * deg for i in range(3)]
    for _ in range(10):
        for i in angles:
            ts = np.sign(np.arcsin(np.cos(i))) == 1.0
            lhs = y - dist * np.cos(i)
            rhs = np.tan(i) * (x + dist * np.sin(i))
            m = (lhs > rhs) if ts else (lhs < rhs)
            px, py = x + np.sin(i) * dist * 2.0, y - np.cos(i) * dist * 2.0
            nx, ny = np.cos(i), np.sin(i)
            dd = px * nx + py * ny
            rx, ry = 2 * nx * dd - px, 2 * ny * dd - py
            x, y = np.where(m, rx, x), np.where(m, ry, y)
    x, y = x + 0.5, y + 0.5
    x, y = rot(x, y, 0.5, 0.5, -p * speed)
    x, y = (x - 0.5) / ratio + 0.5, y
    x = 2 * np.abs(x / 2 - np.floor(x / 2 + 0.5))
    y = 2 * np.abs(y / 2 - np.floor(y / 2 + 0.5))
    k = np.cos(p * np.pi * 2) / 2 + 0.5
    qx, qy = x + (U - x) * k, y + (V - y) * k
    return _u8(mix(samp(a, qx, qy), samp(b, qx, qy), np.cos((p - 1) * np.pi) / 2 + 0.5))


def edge_glow(a, b, p, thickness=0.001, brightness=8.0):
    """A turns into its own glowing edges, which become B's edges, then B fills in. Author: Woohyun Kim."""
    U, V = _grid(*a.shape[:2])

    def edges(img):
        c = [samp(img, U + thickness * (i - 1), V + thickness * (j - 1)) / 255.0 for i in range(3) for j in range(3)]
        dx = 2 * np.abs(c[7] - c[1]) + np.abs(c[2] - c[6]) + np.abs(c[8] - c[0])
        dy = 2 * np.abs(c[3] - c[5]) + np.abs(c[6] - c[8]) + np.abs(c[0] - c[2])
        delta = np.sqrt((((dx + dy) * 0.125) ** 2).sum(-1))
        return np.clip(brightness * delta, 0, 1)[..., None] * c[4] * 255.0

    A, B = _f(a), _f(b)
    start = mix(A, edges(a), min(1.0, 2 * p)) if p < 1 else B
    end = mix(edges(b), B, min(max(2 * (p - 0.5), 0.0), 1.0))
    return _u8(mix(start, end, p))


def butterfly(a, b, p, amplitude=1.0, waves=30.0, separation=0.3):
    """Butterfly-wing wave distortion with RGB split. Author: mandubian."""
    U, V = _grid(*a.shape[:2])
    ox = U * np.sin(p * amplitude) - 0.5
    th = np.arccos(np.clip(ox, -1, 1)) * waves
    s = np.sin((2 * th - np.pi) / 24.0)
    disp = (np.exp(np.cos(th)) - 2 * np.cos(4 * th) + s ** 5) / 10.0
    inv = 1.0 - p
    to = samp(b, U + inv * disp, V + inv * disp)
    fr = np.empty_like(to)
    for ch, k in ((0, 1 - separation), (1, 1.0), (2, 1 + separation)):
        fr[..., ch] = samp(a, U + p * disp * k, V + p * disp * k)[..., ch]
    return _u8(to * p + fr * inv)


def glitch_memories(a, b, p):
    """Jittery RGB offsets while the shots cross-fade (VHS memory glitch). Author: Gunnar Roth."""
    U, V = _grid(*a.shape[:2])
    nx, ny = np.floor(p * 1200.0) / 64.0, np.floor(p * 3500.0) / 64.0
    dx, dy = (_fract(nx) - 0.5) * 0.3 * (1 - p), (_fract(ny) - 0.5) * 0.3 * (1 - p)
    out = np.empty(a.shape, np.float32)
    for ch, k in ((0, 0.2), (1, 0.3), (2, 0.5)):
        x, y = U + dx * k, V + dy * k
        out[..., ch] = mix(samp(a, x, y), samp(b, x, y), p)[..., ch]
    return _u8(out)


def split_slide(a, b, p, reverse=False):
    """Top half slides one way and the bottom half the other. Author: haiyoucuv."""
    U, V = _grid(*a.shape[:2])
    mod = np.where(V > 0.5, 1.0, -1.0) * (-1.0 if reverse else 1.0)
    fx = U + p * mod
    inside = (fx > 0) & (fx < 1) & (V > 0) & (V < 1)
    return _u8(where(inside, samp(a, fx, V), samp(b, fx - mod, V)))


def zoom_in_out(a, b, p, max_zoom=0.8):
    """Punch into A, cross at the peak, settle out of B. Author: Nicholas Miller.
    max_zoom: the original zooms to a single pixel (1.0); 0.8 keeps the car readable."""
    U, V = _grid(*a.shape[:2])
    zf = float(smoothstep(0, 1, p * 2)) * max_zoom
    zt = float(smoothstep(0, 1, (1 - p) * 2)) * max_zoom
    cf = float(smoothstep(0.4, 0.6, p))
    A = samp(a, 0.5 + (U - 0.5) * (1 - zf), 0.5 + (V - 0.5) * (1 - zf)) if zf < 1 else None
    B = samp(b, 0.5 + (U - 0.5) * (1 - zt), 0.5 + (V - 0.5) * (1 - zt)) if zt < 1 else None
    if A is None:
        A = samp(a, np.full_like(U, 0.5), np.full_like(V, 0.5))
    if B is None:
        B = samp(b, np.full_like(U, 0.5), np.full_like(V, 0.5))
    return _u8(mix(A, B, cf))


def wind(a, b, p, size=0.2, reverse=False):
    """B blows in as ragged horizontal streaks. Author: gre."""
    U, V = _grid(*a.shape[:2])
    x = 1.0 - U if reverse else U
    r = _fract(np.sin(V * 78.233) * 43758.5453)
    m = smoothstep(0.0, -size, x * (1.0 - size) + size * r - p * (1.0 + size))
    return _u8(mix(_f(a), _f(b), m.astype(np.float32)))


# ----------------------------------------------------------------------------- registry + easing
TRANSITIONS = {
    # name: (function, suggested seconds, one-line description)
    'cube': (cube, 0.7, '3D cube turn (black stage + floor reflection; bg="blur" for a cleaner stage)'),
    'doorway': (doorway, 0.7, 'A opens like doors, B flies forward'),
    'swap': (swap, 0.7, '3D cards swap places'),
    'book_flip': (book_flip, 0.7, 'page turn with shading'),
    'grid_flip': (grid_flip, 0.9, 'tiles flip like cards'),
    'crosswarp': (crosswarp, 0.5, 'warp wipe left -> right'),
    'directional_warp': (directional_warp, 0.5, 'diagonal warp wipe'),
    'swirl': (swirl, 0.6, 'whirlpool twist'),
    'ripple': (ripple, 0.6, 'water ripple'),
    'morph': (morph, 0.6, 'colour-driven melt'),
    'kaleidoscope': (kaleidoscope, 0.7, 'mirror burst'),
    'flyeye': (flyeye, 0.5, 'insect-eye lens + RGB split'),
    'squeeze': (squeeze, 0.4, 'squeeze to a line + RGB split'),
    'revolve': (revolve, 0.8, 'spin + zoom + barrel with motion blur (heavy)'),
    'tangent_blur': (tangent_blur, 0.6, 'swing around the corner with motion blur'),
    'push_scaled': (push_scaled, 0.6, 'card push upwards with scale'),
    'window_slice': (window_slice, 0.5, 'blinds sweep'),
    # pack 2
    'page_curl': (page_curl, 0.9, 'page curls away from the corner (BSD-3, HP)'),
    'shatter': (shatter, 0.8, 'A breaks into shards that fly off'),
    'mosaic': (mosaic, 1.0, 'pull back over a wall of rotated tiles, land on B'),
    'doom_melt': (doom_melt, 0.8, 'columns melt down (DOOM wipe)'),
    'datamosh': (datamosh, 0.6, 'torn scan bands + time-slice smear (no strobe)'),
    'luma_melt': (luma_melt, 0.8, 'dark parts melt away first'),
    'bounce': (bounce, 0.9, 'A drops out bouncing, soft shadow'),
    'dreamy': (dreamy, 0.6, 'wavy dream dissolve'),
    'defocus': (defocus, 0.6, 'out of focus -> in focus'),
    'cross_zoom': (cross_zoom, 0.6, 'zoom blur rushing to a moving centre'),
    'zoom_circles': (zoom_circles, 0.8, 'rings zoom at different speeds, burst open'),
    'rotate_vanish': (rotate_vanish, 0.7, 'A spins one turn and shrinks away'),
    'fold': (fold, 0.5, 'B unfolds from the left'),
    'tiles_wave': (tiles_wave, 0.9, 'tiles turn over in a wave'),
    'hexagonalize': (hexagonalize, 0.6, 'dissolve through hexagon cells'),
    'perlin': (perlin, 0.6, 'cloud-noise dissolve'),
    'burn_out': (burn_out, 0.8, 'undulating dark-rimmed hole opens'),
    'power_kaleido': (power_kaleido, 0.8, 'spinning triangle-mirror kaleidoscope'),
    'edge_glow': (edge_glow, 0.8, 'A turns into glowing edges, then B'),
    'butterfly': (butterfly, 0.6, 'butterfly-wing wave + RGB split'),
    'glitch_memories': (glitch_memories, 0.5, 'jittery RGB offsets'),
    'split_slide': (split_slide, 0.5, 'top and bottom halves slide apart'),
    'zoom_in_out': (zoom_in_out, 0.5, 'punch in, swap, settle out'),
    'wind': (wind, 0.5, 'ragged horizontal streak wipe'),
}
NAMES = list(TRANSITIONS)

# The numbers the user picks effects by (showcase reels 1 and 2). Transitions live here, effects in vfx.py.
NUMBERS = {
    1: 'cube', 2: 'crosswarp', 3: 'doorway', 4: 'swirl', 5: 'swap', 6: 'directional_warp', 7: 'revolve', 8: 'ripple',
    9: 'book_flip', 10: 'morph', 11: 'tangent_blur', 12: 'squeeze', 13: 'grid_flip', 14: 'flyeye', 15: 'push_scaled',
    16: 'window_slice', 17: 'kaleidoscope',
    18: 'vfx.ramp_frames', 19: 'vfx.Clip.at (slow-mo)', 20: 'vfx.tilt3d', 21: 'vfx.shake', 22: 'vfx.lens_warp',
    23: 'vfx.echo', 24: 'vfx.light_leak',
    25: 'page_curl', 26: 'shatter', 27: 'mosaic', 28: 'doom_melt', 29: 'datamosh', 30: 'luma_melt', 31: 'bounce',
    32: 'dreamy', 33: 'defocus', 34: 'cross_zoom', 35: 'zoom_circles', 36: 'rotate_vanish', 37: 'fold',
    38: 'tiles_wave', 39: 'hexagonalize', 40: 'perlin', 41: 'burn_out', 42: 'power_kaleido', 43: 'edge_glow',
    44: 'butterfly', 45: 'glitch_memories', 46: 'split_slide', 47: 'zoom_in_out', 48: 'wind',
    49: 'vfx.reflection', 50: 'vfx.tilt_shift', 51: 'vfx.crt', 52: 'vfx.old_film', 53: 'vfx.ascii_art',
    54: 'vfx.cross_hatch', 55: 'vfx.emboss', 56: 'vfx.twist', 57: 'vfx.lens_blur', 58: 'vfx.ink', 59: 'vfx.edge_work',
}


def ease_p(p, kind):
    if kind in (None, 'linear'):
        return p
    if kind == 'in':
        return p * p * p
    if kind == 'out':
        return 1 - (1 - p) ** 3
    if kind == 'inout':
        return 4 * p ** 3 if p < 0.5 else 1 - (-2 * p + 2) ** 3 / 2
    raise ValueError(kind)


def transition(name, a, b, p, ease=None, **kw):
    """Run transition `name` at progress p (0..1). a, b: uint8 HxWx3 of the same size."""
    p = float(min(max(ease_p(float(p), ease), 0.0), 1.0))
    if p <= 0:
        return a.copy()
    if p >= 1:
        return b.copy()
    return TRANSITIONS[name][0](a, b, p, **kw)


# ----------------------------------------------------------------------------- CLI previews
def _read_at(path, t, size):
    import subprocess
    w, h = size
    cmd = ['ffmpeg', '-v', 'error', '-ss', str(t), '-i', path, '-frames:v', '1',
           '-vf', f'scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3).copy()


def _read_range(path, t, n, fps, size):
    import subprocess
    w, h = size
    cmd = ['ffmpeg', '-v', 'error', '-ss', str(t), '-i', path, '-frames:v', str(n),
           '-vf', f'fps={fps},scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h}',
           '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    if len(fr) < n:  # hold the last frame if the source is short
        fr = np.concatenate([fr, np.repeat(fr[-1:], n - len(fr), 0)])
    return fr


def _main(argv):
    import argparse
    import subprocess
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('cmd', choices=['demo', 'sheet', 'list'])
    ap.add_argument('args', nargs='*')
    ap.add_argument('--dur', type=float, default=None)
    ap.add_argument('--fps', type=int, default=60)
    ap.add_argument('--size', default='1080x1920')
    ap.add_argument('--hold', type=float, default=0.5, help='seconds of A before and B after (demo)')
    ap.add_argument('--ease', default=None)
    o = ap.parse_args(argv)
    if o.cmd == 'list':
        for k, (_, d, desc) in TRANSITIONS.items():
            print(f'{k:18s} {d:.1f}s  {desc}')
        return
    A, ta, B, tb, name, out = o.args
    ta, tb = float(ta), float(tb)
    size = tuple(int(x) for x in o.size.split('x'))
    dur = o.dur or TRANSITIONS[name][1]
    if o.cmd == 'sheet':
        a, b = _read_at(A, ta, size), _read_at(B, tb, size)
        ps = [0.0, 0.15, 0.3, 0.45, 0.55, 0.7, 0.85, 1.0]
        tiles = [cv2.resize(transition(name, a, b, q, ease=o.ease), (size[0] // 4, size[1] // 4),
                            interpolation=cv2.INTER_AREA) for q in ps]
        img = np.concatenate(tiles, axis=1)
        cv2.imwrite(out, cv2.cvtColor(img, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, 88])
        print(out)
        return
    nh, nt = int(round(o.hold * o.fps)), int(round(dur * o.fps))
    fa = _read_range(A, ta, nh + nt, o.fps, size)
    fb = _read_range(B, tb, nt + nh, o.fps, size)
    w, h = size
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{w}x{h}',
                            '-r', str(o.fps), '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '17',
                            '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for i in range(nh):
        enc.stdin.write(fa[i].tobytes())
    for i in range(nt):
        q = (i + 0.5) / nt
        enc.stdin.write(transition(name, fa[nh + i], fb[i], q, ease=o.ease).tobytes())
    for i in range(nh):
        enc.stdin.write(fb[nt + i].tobytes())
    enc.stdin.close()
    enc.wait()
    print(out)


if __name__ == '__main__':
    _main(sys.argv[1:])
