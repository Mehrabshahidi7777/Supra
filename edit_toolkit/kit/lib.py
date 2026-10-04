import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
FONT = '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'
FONT_REG = '/usr/share/fonts/opentype/inter/Inter-Black.otf'


def hexc(h):
    h = h.lstrip('#')
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


# ---------------------------------------------------------------- text masks
def text_mask(text, size, font=FONT, stretch=(0.88, 1.10), skew=-0.13, pad=160, tracking=0.0):
    """Antialiased alpha mask (float32 0..1) of text, stretched + italic skewed, padded."""
    f = ImageFont.truetype(font, size)
    # draw letter by letter to allow tracking
    widths = []
    for ch in text:
        bb = f.getbbox(ch)
        widths.append(f.getlength(ch))
    total = sum(widths) + tracking * size * (len(text) - 1)
    asc, desc = f.getmetrics()
    im = Image.new('L', (int(total + 2 * pad), int(asc + desc + 2 * pad)), 0)
    d = ImageDraw.Draw(im)
    x = pad
    for ch, w in zip(text, widths):
        d.text((x, pad), ch, font=f, fill=255)
        x += w + tracking * size
    m = np.asarray(im, np.float32) / 255.0
    # crop to ink + pad
    ys, xs = np.where(m > 0.01)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    m = m[y0:y1, x0:x1]
    h, w = m.shape
    nw, nh = int(round(w * stretch[0])), int(round(h * stretch[1]))
    m = cv2.resize(m, (nw, nh), interpolation=cv2.INTER_AREA if stretch[0] < 1 else cv2.INTER_CUBIC)
    # skew (italic): x' = x + skew*(y - h/2) ; negative skew -> lean right
    extra = int(abs(skew) * nh) + 4
    M = np.float32([[1, skew, extra / 2 - skew * nh / 2 + pad], [0, 1, pad]])
    out = cv2.warpAffine(m, M, (nw + extra + 2 * pad, nh + 2 * pad), flags=cv2.INTER_CUBIC)
    return np.clip(out, 0, 1)


def shift(m, dx, dy):
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    return cv2.warpAffine(m, M, (m.shape[1], m.shape[0]), flags=cv2.INTER_LINEAR)


def dilate(m, r):
    if r <= 0:
        return m
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    return cv2.dilate(m, k)


def erode(m, r):
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))
    return cv2.erode(m, k)


def over(dst_rgb, dst_a, src_rgb, src_a):
    """premultiplied 'over'"""
    return src_rgb + dst_rgb * (1 - src_a[..., None]), src_a + dst_a * (1 - src_a)


def build_plate(mask, depth=22, ext_dir=(0.35, 1.0), stroke=7, top='#ff5040', mid='#ff0d18',
                low='#d8000e', bottom='#7a0009', ext_near='#6a0008', ext_far='#100002',
                seed=1, grit=0.05):
    """Return premultiplied rgb (h,w,3), alpha (h,w), face mask (h,w)"""
    h, w = mask.shape
    rgb = np.zeros((h, w, 3), np.float32)
    a = np.zeros((h, w), np.float32)
    # --- outer dark stroke around face+extrusion silhouette
    sil = mask.copy()
    dxu, dyu = ext_dir
    n = np.hypot(dxu, dyu); dxu, dyu = dxu / n, dyu / n
    for i in range(1, depth + 1):
        sil = np.maximum(sil, shift(mask, dxu * i, dyu * i))
    outer = dilate(sil, stroke)
    outer = cv2.GaussianBlur(outer, (0, 0), 1.0)
    rgb, a = over(rgb, a, hexc('#070000')[None, None] * outer[..., None], outer)
    # --- extrusion (back to front)
    cn, cf = hexc(ext_near), hexc(ext_far)
    for i in range(depth, 0, -1):
        s = shift(mask, dxu * i, dyu * i)
        tt = (i - 1) / max(1, depth - 1)
        col = cn * (1 - tt) + cf * tt
        # slight side-light banding
        col = col * (1.0 + 0.25 * (1 - tt))
        rgb, a = over(rgb, a, col[None, None] * s[..., None], s)
    # --- thin dark stroke right around the face
    fs = dilate(mask, 3)
    fs = cv2.GaussianBlur(fs, (0, 0), 0.8)
    rgb, a = over(rgb, a, hexc('#1a0002')[None, None] * fs[..., None], fs)
    # --- face gradient
    ys, xs = np.where(mask > 0.5)
    y0, y1 = ys.min(), ys.max()
    yy = np.clip((np.arange(h, dtype=np.float32) - y0) / max(1, (y1 - y0)), 0, 1)[:, None]
    ct, cm, cl, cb = hexc(top), hexc(mid), hexc(low), hexc(bottom)
    g = np.zeros((h, 1, 3), np.float32)
    up = yy < 0.5
    t1 = np.clip(yy / 0.5, 0, 1)
    t2 = np.clip((yy - 0.5) / 0.5, 0, 1)
    g = np.where(up[..., None], ct * (1 - t1[..., None]) + cm * t1[..., None],
                 cl * (1 - t2[..., None]) + cb * t2[..., None])
    face = np.broadcast_to(g, (h, w, 3)).copy()
    # grit
    rng = np.random.default_rng(seed)
    nz = cv2.GaussianBlur(rng.random((h, w)).astype(np.float32), (0, 0), 1.2)
    nz2 = cv2.resize(cv2.GaussianBlur(rng.random((h // 8 + 1, w // 8 + 1)).astype(np.float32), (0, 0), 1.0), (w, h))
    face *= (1.0 + grit * (nz - nz.mean()) * 4 + grit * (nz2 - 0.5))[..., None]
    # inner rim light
    rim = np.clip(mask - erode(mask, 3), 0, 1)
    rim = cv2.GaussianBlur(rim, (0, 0), 1.0)
    face = face + hexc('#ff5a48')[None, None] * (rim[..., None] * 0.30)
    # top-edge highlight (bevel)
    hi = np.clip(mask - shift(mask, 0, 5), 0, 1)
    hi = cv2.GaussianBlur(hi, (0, 0), 1.2)
    face = face + hexc('#ffc2b0')[None, None] * (hi[..., None] * 0.85)
    # bottom inner shadow
    lo = np.clip(mask - shift(mask, 0, -6), 0, 1)
    lo = cv2.GaussianBlur(lo, (0, 0), 1.5)
    face = face * (1 - 0.45 * lo[..., None])
    rgb, a = over(rgb, a, face * mask[..., None], mask)
    return np.clip(rgb, 0, 2), np.clip(a, 0, 1), mask


def outline_mask(mask, r_out, width):
    return np.clip(dilate(mask, r_out) - dilate(mask, max(0, r_out - width)), 0, 1)


# ---------------------------------------------------------------- noise
def fractal_noise(h, w, seed, octaves=5, base=6, persistence=0.55):
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, tot = 1.0, 0.0
    for o in range(octaves):
        gh, gw = base * 2 ** o + 1, int(base * 2 ** o * w / h) + 1
        g = rng.random((gh, gw)).astype(np.float32)
        out += amp * cv2.resize(g, (w, h), interpolation=cv2.INTER_CUBIC)
        tot += amp
        amp *= persistence
    out /= tot
    out = (out - out.min()) / (out.max() - out.min())
    return out


# ---------------------------------------------------------------- helpers
def place(canvas_rgb, canvas_a, prgb, pa, cx, cy, scale=1.0, angle=0.0, alpha=1.0):
    """warp a premultiplied plate into canvas centered at (cx,cy)"""
    h, w = pa.shape
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, scale)
    M[0, 2] += cx - w / 2
    M[1, 2] += cy - h / 2
    Hc, Wc = canvas_a.shape
    r = cv2.warpAffine(prgb, M, (Wc, Hc), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    aa = cv2.warpAffine(pa, M, (Wc, Hc), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    if alpha < 1:
        r *= alpha; aa *= alpha
    return over(canvas_rgb, canvas_a, r, aa)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def ease_out_back(t, s=1.70158):
    t = np.clip(t, 0, 1) - 1
    return t * t * ((s + 1) * t + s) + 1


def ease_out_cubic(t):
    t = np.clip(t, 0, 1)
    return 1 - (1 - t) ** 3
