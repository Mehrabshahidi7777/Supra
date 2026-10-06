"""Spiky chrome MEHRAB.7w7 logo (Night 5 reveal; the reference's creator logo "ZS3" style).

Letters are drawn as blades (Catmull-Rom centre lines, fat in the middle, sharp at both ends) whose ends run out
into thorns, plus a few barbs, then shaded as liquid chrome (bevel height from the distance transform, normals,
gradient map with sharp horizon bands + specular). Two lines: "MEHRAB" / ".7w7".

  python3 logo5.py            -> $WORK/logo/logo5.npz (mask + normals at video scale) + preview PNGs
Import:  from logo5 import Logo ; L = Logo() ; rgb, a = L.shade(offset, dark=0.0)
"""
import os, sys
import numpy as np, cv2

WORK = os.environ.get('WORK', '/home/claude/work_edit')
SS = 3                     # supersampling for the vector drawing


# ------------------------------------------------------------------ geometry
def catmull(pts, n=60):
    pts = np.asarray(pts, np.float64)
    P = np.vstack([2 * pts[0] - pts[1], pts, 2 * pts[-1] - pts[-2]])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        t = np.linspace(0, 1, n, endpoint=(i == len(P) - 3))[:, None]
        out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t ** 2
                          + (-p0 + 3 * p1 - 3 * p2 + p3) * t ** 3))
    return np.vstack(out)


def extend(pts, a=0.22, b=0.22, curl_a=0.0, curl_b=0.0):
    """add thorn tips beyond both ends along the tangent (curl in radians bends the tip)"""
    pts = [np.asarray(p, np.float64) for p in pts]
    def tip(p_end, p_prev, L, curl):
        d = p_end - p_prev
        d /= np.linalg.norm(d) + 1e-9
        c, s = np.cos(curl), np.sin(curl)
        d2 = np.array([c * d[0] - s * d[1], s * d[0] + c * d[1]])
        mid = p_end + d * L * 0.5
        return [mid, mid + d2 * L * 0.5]
    head = tip(pts[0], pts[1], a, curl_a)[::-1] if a > 0 else []
    tail = tip(pts[-1], pts[-2], b, curl_b) if b > 0 else []
    return head + pts + tail


def blade(path, wmax, s_a=0.0, s_b=1.0, p_tip=0.85, end_taper=0.07, bulge=0.12):
    """polygon of a blade along a dense path: full width between s_a and s_b (the drawn stroke), tapering to sharp
    thorn tips over the extensions [0, s_a] and [s_b, 1]; ends without extension get a short taper"""
    path = np.asarray(path)
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)])
    s /= s[-1] + 1e-12
    sa = max(s_a, end_taper); sb = min(s_b, 1 - end_taper)
    f = np.ones_like(s)
    lo = s < sa; hi = s > sb
    f[lo] = (s[lo] / sa) ** p_tip
    f[hi] = ((1 - s[hi]) / (1 - sb)) ** p_tip
    core = np.clip((s - sa) / max(1e-6, sb - sa), 0, 1)
    f = f * (1 + bulge * np.sin(np.pi * core))
    w = wmax * f
    tg = np.gradient(path, axis=0)
    tg /= np.linalg.norm(tg, axis=1, keepdims=True) + 1e-12
    nrm = np.stack([-tg[:, 1], tg[:, 0]], 1)
    left = path + nrm * (w[:, None] / 2)
    right = path - nrm * (w[:, None] / 2)
    return np.vstack([left, right[::-1]])


def arc_frac(path, p):
    """arc-length fraction of the path point nearest to p"""
    path = np.asarray(path)
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)]); s /= s[-1] + 1e-12
    return float(s[np.argmin(np.linalg.norm(path - np.asarray(p), axis=1))])


def barb(path, s0, side, L, ang, wbase):
    """small thorn growing out of a stroke at parameter s0"""
    path = np.asarray(path)
    seg = np.linalg.norm(np.diff(path, axis=0), axis=1)
    s = np.concatenate([[0], np.cumsum(seg)]); s /= s[-1]
    i = int(np.clip(np.searchsorted(s, s0), 1, len(path) - 2))
    P = path[i]; tg = path[i + 1] - path[i - 1]; tg /= np.linalg.norm(tg) + 1e-12
    c, sn = np.cos(ang * side), np.sin(ang * side)
    d = np.array([c * tg[0] - sn * tg[1], sn * tg[0] + c * tg[1]])
    nrm = np.array([-d[1], d[0]])
    tip = P + d * L
    mid = P + d * L * 0.45 + nrm * L * 0.10 * side
    poly = np.array([P + nrm * wbase / 2, mid + nrm * wbase * 0.18, tip, mid - nrm * wbase * 0.12, P - nrm * wbase / 2])
    return poly


# ------------------------------------------------------------------ glyphs (cap height 1, y down, baseline y = 1)
# stroke = dict(pts, w, ext=(head, tail) thorn lengths, curl=(head, tail) radians, barbs=[(s0, side, L, ang)])
W_MAIN, W_THIN = 0.165, 0.105
G = {
    'M': (0.90, [
        dict(pts=[(0.08, 1.00), (0.06, 0.52), (0.10, 0.03)], w=W_MAIN, ext=(0.30, 0.24), curl=(0.45, -0.55)),
        dict(pts=[(0.10, 0.04), (0.27, 0.37), (0.44, 0.70)], w=W_THIN, ext=(0.0, 0.0)),
        dict(pts=[(0.44, 0.70), (0.61, 0.37), (0.78, 0.04)], w=W_THIN, ext=(0.0, 0.0)),
        dict(pts=[(0.78, 0.03), (0.82, 0.52), (0.80, 1.00)], w=W_MAIN, ext=(0.24, 0.30), curl=(0.55, -0.45)),
        dict(pts=[(0.44, 0.66), (0.44, 0.80), (0.43, 0.92)], w=0.075, ext=(0.0, 0.14), curl=(0, 0.2)),
    ]),
    'E': (0.72, [
        dict(pts=[(0.11, 0.01), (0.09, 0.50), (0.12, 0.99)], w=W_MAIN, ext=(0.16, 0.16), curl=(-0.5, 0.5),
             barbs=[(0.50, -1, 0.22, 1.9)]),
        dict(pts=[(0.10, 0.03), (0.38, 0.00), (0.64, -0.05)], w=W_THIN, ext=(0.0, 0.26), curl=(0, -0.45)),
        dict(pts=[(0.12, 0.50), (0.34, 0.49), (0.54, 0.47)], w=W_THIN * 0.9, ext=(0.0, 0.18), curl=(0, 0.2)),
        dict(pts=[(0.12, 0.97), (0.40, 1.00), (0.66, 1.05)], w=W_THIN, ext=(0.0, 0.26), curl=(0, 0.45)),
    ]),
    'H': (0.82, [
        dict(pts=[(0.10, 0.00), (0.08, 0.50), (0.11, 1.00)], w=W_MAIN, ext=(0.24, 0.24), curl=(0.45, -0.45)),
        dict(pts=[(0.71, 0.00), (0.73, 0.50), (0.70, 1.00)], w=W_MAIN, ext=(0.24, 0.24), curl=(-0.45, 0.45)),
        dict(pts=[(0.09, 0.52), (0.41, 0.47), (0.72, 0.50)], w=W_THIN, ext=(0.16, 0.16), curl=(0.35, -0.35)),
    ]),
    'R': (0.80, [
        dict(pts=[(0.11, 0.01), (0.09, 0.50), (0.12, 1.00)], w=W_MAIN, ext=(0.16, 0.26), curl=(-0.5, 0.45)),
        dict(pts=[(0.11, 0.04), (0.42, 0.00), (0.66, 0.19), (0.52, 0.43), (0.13, 0.50)], w=W_THIN * 1.15, ext=(0.0, 0.0)),
        dict(pts=[(0.36, 0.50), (0.55, 0.74), (0.74, 1.00)], w=W_MAIN * 0.9, ext=(0.0, 0.30), curl=(0, -0.45)),
    ]),
    'A': (0.86, [
        dict(pts=[(0.03, 1.00), (0.22, 0.50), (0.43, 0.02)], w=W_MAIN * 0.95, ext=(0.24, 0.0), curl=(0.5, 0)),
        dict(pts=[(0.43, 0.02), (0.63, 0.50), (0.82, 1.00)], w=W_MAIN * 0.95, ext=(0.0, 0.24), curl=(0, -0.5)),
        dict(pts=[(0.18, 0.63), (0.43, 0.58), (0.70, 0.62)], w=W_THIN * 0.9, ext=(0.14, 0.14), curl=(0.5, -0.5)),
        dict(pts=[(0.43, 0.14), (0.43, -0.06), (0.44, -0.22)], w=0.085, ext=(0.0, 0.16), curl=(0, 0.25)),
    ]),
    'B': (0.76, [
        dict(pts=[(0.11, 0.01), (0.09, 0.50), (0.12, 0.99)], w=W_MAIN, ext=(0.18, 0.18), curl=(-0.5, 0.5)),
        dict(pts=[(0.11, 0.04), (0.44, 0.01), (0.62, 0.21), (0.46, 0.44), (0.13, 0.48)], w=W_THIN * 1.15, ext=(0.0, 0.0)),
        dict(pts=[(0.13, 0.50), (0.52, 0.50), (0.71, 0.74), (0.50, 0.98), (0.11, 0.97)], w=W_THIN * 1.25, ext=(0.0, 0.0),
             barbs=[(0.40, -1, 0.20, 1.1)]),
    ]),
    '.': (0.32, [
        dict(pts=[(0.15, 0.78), (0.16, 0.91), (0.15, 1.04)], w=0.15, ext=(0.08, 0.08)),
        dict(pts=[(0.02, 0.92), (0.16, 0.91), (0.30, 0.90)], w=0.09, ext=(0.05, 0.05)),
    ]),
    '7': (0.76, [
        dict(pts=[(0.03, 0.05), (0.37, 0.01), (0.71, -0.02)], w=W_THIN * 1.2, ext=(0.20, 0.08), curl=(0.5, 0)),
        dict(pts=[(0.70, 0.00), (0.52, 0.48), (0.33, 1.00)], w=W_MAIN, ext=(0.0, 0.32), curl=(0, 0.45)),
        dict(pts=[(0.31, 0.52), (0.50, 0.50), (0.68, 0.49)], w=0.075, ext=(0.10, 0.12)),
    ]),
    'w': (1.00, [
        dict(pts=[(0.02, 0.31), (0.15, 0.66), (0.26, 1.00)], w=W_MAIN * 0.9, ext=(0.24, 0.0), curl=(0.45, 0)),
        dict(pts=[(0.26, 1.00), (0.38, 0.70), (0.49, 0.41)], w=W_THIN, ext=(0.0, 0.12)),
        dict(pts=[(0.49, 0.41), (0.61, 0.70), (0.72, 1.00)], w=W_THIN, ext=(0.0, 0.0)),
        dict(pts=[(0.72, 1.00), (0.84, 0.66), (0.97, 0.31)], w=W_MAIN * 0.9, ext=(0.0, 0.24), curl=(0, -0.45)),
        dict(pts=[(0.26, 0.94), (0.26, 1.06), (0.25, 1.16)], w=0.065, ext=(0.0, 0.08)),
        dict(pts=[(0.72, 0.94), (0.72, 1.06), (0.73, 1.16)], w=0.065, ext=(0.0, 0.08)),
    ]),
}
TRACK = 0.06


def line_polys(text, cap, x0, y0, slant=0.10):
    """polygons (in pixels) for one line of text with cap height `cap`, top-left at (x0, y0); slant = italic lean"""
    polys = []
    x = x0
    for ch in text:
        adv, strokes = G[ch]
        gl = []
        for st in strokes:
            ea, eb = st.get('ext', (0.2, 0.2)); ca, cb = st.get('curl', (0, 0))
            path = catmull(extend(st['pts'], ea, eb, ca, cb), 40)
            s_a = arc_frac(path, st['pts'][0]) if ea > 0 else 0.0
            s_b = arc_frac(path, st['pts'][-1]) if eb > 0 else 1.0
            gl.append(blade(path, st['w'], s_a, s_b))
            base = catmull(st['pts'], 40)
            for (s0, side, L, ang) in st.get('barbs', []):
                gl.append(barb(base, s0, side, L, ang, st['w'] * 0.75))
        for P in gl:
            polys.append(np.stack([x + (P[:, 0] + slant * (1 - P[:, 1])) * cap, y0 + P[:, 1] * cap], 1))
        x += (adv + TRACK) * cap
    return polys, x - TRACK * cap


def build_mask(cap1=196, cap2=196, gap=64, width=1080, height=760):
    """two-line logo mask at video scale (float 0..1), centred"""
    S = SS
    # measure
    _, w1 = line_polys('MEHRAB', cap1 * S, 0, 0)
    _, w2 = line_polys('.7w7', cap2 * S, 0, 0)
    cw, ch = width * S, height * S
    top = (ch - (cap1 + gap + cap2) * S) / 2
    p1, _ = line_polys('MEHRAB', cap1 * S, (cw - w1) / 2, top)
    p2, _ = line_polys('.7w7', cap2 * S, (cw - w2) / 2 + 0.02 * cw, top + (cap1 + gap) * S)
    m = np.zeros((ch, cw), np.uint8)
    for P in p1 + p2:
        cv2.fillPoly(m, [np.round(P * 4).astype(np.int32)], 255, cv2.LINE_AA, shift=2)
    m = m.astype(np.float32) / 255
    # liquid joins: a touch of blur + re-threshold (keeps the tips sharp)
    mb = cv2.GaussianBlur(m, (0, 0), 3.2 * S / 3)
    m = np.maximum(m, np.clip((mb - 0.40) * 5, 0, 1))
    return cv2.resize(m, (width, height), interpolation=cv2.INTER_AREA)


# ------------------------------------------------------------------ chrome shading
def _gradmap(stops):
    xs = np.array([s[0] for s in stops], np.float32)
    cs = np.array([[int(s[1][i:i + 2], 16) / 255 for i in (1, 3, 5)] for s in stops], np.float32)
    lut = np.stack([np.interp(np.linspace(0, 1, 1024), xs, cs[:, c]) for c in range(3)], 1).astype(np.float32)
    return lut


CHROME = _gradmap([(0.00, '#050608'), (0.08, '#1b2028'), (0.18, '#8c96a3'), (0.26, '#f2f6fb'), (0.33, '#ffffff'),
                   (0.40, '#9aa4b1'), (0.47, '#2b313a'), (0.53, '#07090c'), (0.60, '#343b45'), (0.70, '#a9b3bf'),
                   (0.80, '#eef3f9'), (0.88, '#ffffff'), (0.95, '#c9d2dc'), (1.00, '#8d97a3')])
DARK = _gradmap([(0.00, '#000000'), (0.25, '#040507'), (0.40, '#20242b'), (0.47, '#5a626e'), (0.52, '#050608'),
                 (0.66, '#14171c'), (0.80, '#3d434c'), (0.90, '#aab3be'), (1.00, '#ffffff')])


class Logo:
    def __init__(self, path=None):
        path = path or f'{WORK}/logo/logo5.npz'
        if not os.path.exists(path):
            build_and_save(path)
        z = np.load(path)
        self.m = z['m'].astype(np.float32)
        self.nx, self.ny, self.h = z['nx'], z['ny'], z['h']
        self.ry = z['ry']
        self.H, self.W = self.m.shape
        self.edge = z['edge']

    def shade(self, offset=0.0, dark=0.0, sweep=None):
        """premultiplied rgb + alpha of the chrome logo. offset shifts the reflections, dark 0..1 -> black chrome,
        sweep = position (0..1) of a bright diagonal light band or None"""
        L = 0.50 + 0.36 * self.ny * -1 + 0.10 * self.nx + 0.30 * (self.ry - 0.5) * -1 + offset
        L = L + 0.10 * self.h
        idx = np.clip((L % 1.0) * 1023, 0, 1023).astype(np.int32)
        col = CHROME[idx]
        if dark > 0:
            col = col * (1 - dark) + DARK[idx] * dark
        # specular from upper left
        lx, ly, lz = -0.45, -0.65, 0.62
        nz = np.sqrt(np.clip(1 - self.nx ** 2 - self.ny ** 2, 0, 1))
        spec = np.clip(self.nx * lx + self.ny * ly + nz * lz, 0, 1) ** 38
        col = col + spec[..., None] * (1.1 - 0.5 * dark)
        if sweep is not None:
            yy, xx = np.mgrid[0:self.H, 0:self.W].astype(np.float32)
            d = (xx / self.W * 0.8 + yy / self.H * 0.6) / 1.4
            band = np.exp(-((d - sweep) / 0.035) ** 2)
            col = col + band[..., None] * self.m[..., None] * 0.9
        col = col * (1 - 0.55 * self.edge[..., None])             # dark rim at the silhouette
        return col * self.m[..., None], self.m


def build_and_save(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    m = build_mask()
    H, W = m.shape
    big = cv2.resize(m, (W * 2, H * 2), interpolation=cv2.INTER_LINEAR)
    d = cv2.distanceTransform((big > 0.5).astype(np.uint8), cv2.DIST_L2, 5) / 2.0
    d = cv2.resize(d, (W, H), interpolation=cv2.INTER_AREA)
    r = 11.0
    h = np.sqrt(np.clip(1 - (1 - np.clip(d / r, 0, 1)) ** 2, 0, 1))
    h = cv2.GaussianBlur(h, (0, 0), 1.2) * (m > 0.02)
    gx = cv2.Sobel(h, cv2.CV_32F, 1, 0, ksize=3) / 8 * r * 1.6
    gy = cv2.Sobel(h, cv2.CV_32F, 0, 1, ksize=3) / 8 * r * 1.6
    n = np.sqrt(gx ** 2 + gy ** 2 + 1)
    nx, ny = -gx / n, -gy / n
    # position term: each line gets its own top->bottom gradient (classic chrome lettering)
    yy = np.mgrid[0:H, 0:W][0].astype(np.float32)
    rows = np.where(m.max(1) > 0.5)[0]
    mid = (rows.min() + rows.max()) / 2
    ry = np.where(yy < mid, (yy - rows.min()) / (mid - rows.min()), (yy - mid) / (rows.max() - mid))
    ry = np.clip(ry, 0, 1)
    edge = np.clip(1 - d / 2.2, 0, 1) * (m > 0.02)
    np.savez_compressed(path, m=m.astype(np.float16), nx=nx.astype(np.float32), ny=ny.astype(np.float32),
                        h=h.astype(np.float32), ry=ry.astype(np.float32), edge=edge.astype(np.float32))
    print('logo saved', path, m.shape, 'ink rows', rows.min(), rows.max())


if __name__ == '__main__':
    p = f'{WORK}/logo/logo5.npz'
    build_and_save(p)
    L = Logo(p)
    bg = cv2.imread(sys.argv[1])[..., ::-1].astype(np.float32) / 255 if len(sys.argv) > 1 else None
    outs = []
    for off, dk in ((0.0, 0.0), (0.18, 0.0), (0.0, 1.0)):
        rgb, a = L.shade(off, dk, sweep=0.55 if off else None)
        if bg is None:
            base = np.zeros((L.H, L.W, 3), np.float32) + np.array([0.20, 0.33, 0.50], np.float32)
        else:
            base = cv2.resize(bg, (L.W, L.H))
        sh = cv2.GaussianBlur(a, (0, 0), 6)
        sh = np.roll(np.roll(sh, 10, 0), 6, 1)
        f = base * (1 - 0.55 * sh[..., None])
        f = rgb + f * (1 - a[..., None])
        outs.append((np.clip(f, 0, 1)[..., ::-1] * 255).astype(np.uint8))
    cv2.imwrite(f'{WORK}/logo/preview.png', np.vstack(outs))
