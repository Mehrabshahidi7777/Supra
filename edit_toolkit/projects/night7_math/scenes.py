"""Night 7 "Math ahh edit" graphics: drawn shots + footage effects for engine.py.

Reference (@miot7 "Math ahh edit"): glowing creator title -> neon logo outlines floating in space -> on the drop a
math equation built from brand logos (radical, times, fraction ...) the camera dollies along, answer = BMW -> zoom
into the BMW roundel -> 3D "BMW M3 ... Evolution" line chart with a red glowing frame, the roundel rides the line and
the M3 generations pop on it -> a white M3 tumbles through space -> velocity part (B&W -> colour pop, zoom blur,
spin, red ghost) -> glowing name -> loop.
Our version: title OLD SCHOOL / M3 MATH over a dark teal E46; Mercedes + Jaguar neon outlines; equation
sqrt(Mercedes x Audi) + McLaren / (Tesla - Lexus) x Jaguar = BMW; "BMW M3 Power Evolution" chart with the launch
outputs from BMW M (E30 1986 195 PS, E36 1992 286 PS, E46 2000 343 PS); white E36 tumbling; old-school velocity
part with film grain. House taste: dark fog instead of the reference's star dots, no white flashes.
All functions take the engine ctx (q, u, ls, dur, t, fi, beat) and return / transform uint8 1080x1920 RGB.
"""
import os
import sys
from functools import lru_cache

import numpy as np
import cv2
from PIL import Image, ImageDraw, ImageFont

KIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit')
sys.path.insert(0, KIT)
import vfx  # noqa: E402
from lib import fractal_noise, text_mask, dilate, hexc, ease_out_back  # noqa: E402

W, H = 1080, 1920
WORK = os.environ.get('WORK', '/home/claude/work_edit')
A = f'{WORK}/n7/assets'
BEAT = 0.59384
F_COND = '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyreheroscn-bold.otf'
F_MATH = '/usr/share/texmf/fonts/opentype/public/lm-math/latinmodern-math.otf'
F_BLACK = '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'
F_BOLD = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
TEAL = np.float32([0.25, 1.0, 0.82])


def sm(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def ease_io(x):
    x = min(max(x, 0.0), 1.0)
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


# ============================================================================ shared pieces
def periodic_noise(h, w, seed, beta=2.0, fmin=1.5):
    """Tileable smoke noise (1/f^beta spectrum, random phases) -> rolls without seams. 0..1."""
    rng = np.random.default_rng(seed)
    fy = np.fft.fftfreq(h)[:, None] * h
    fx = np.fft.rfftfreq(w)[None] * w
    f = np.sqrt(fx * fx + fy * fy)
    amp = np.where(f < fmin, 0.0, 1.0 / np.maximum(f, 1e-6) ** beta)
    spec = amp * np.exp(2j * np.pi * rng.random(amp.shape))
    n = np.fft.irfft2(spec, s=(h, w)).astype(np.float32)
    return (n - n.min()) / (n.max() - n.min())


@lru_cache(None)
def _fog_fields():
    return [periodic_noise(480, 270, s) for s in (11, 23, 37)]


def fog(t, tint=(0.10, 0.16, 0.17), amount=1.0, speed=1.0):
    """Dark drifting smoke (no dots): three noise fields sliding at different speeds, quarter-res, upscaled."""
    f = _fog_fields()
    acc = np.zeros((480, 270), np.float32)
    for i, (fld, vx, vy, w) in enumerate(zip(f, (9, -6, 4), (2, 3, -2), (0.55, 0.35, 0.25))):
        acc += w * np.roll(fld, (int(t * vy * speed * 3), int(t * vx * speed * 3)), (0, 1)) ** 2.2
    acc = cv2.resize(acc, (W, H), interpolation=cv2.INTER_CUBIC)
    Y = np.linspace(-1, 1, H, dtype=np.float32)[:, None]
    X = np.linspace(-1, 1, W, dtype=np.float32)[None]
    vig = np.clip(1.15 - 0.55 * (X * X + 0.6 * Y * Y), 0, 1)
    return (acc * vig * amount)[..., None] * np.float32(tint) * 1.6 + 0.012


def bloom(f, k=(0.55, 0.35), sig=(6, 22)):
    s = cv2.resize(f, (W // 4, H // 4), interpolation=cv2.INTER_AREA)
    out = f.copy()
    for kk, sg in zip(k, sig):
        out += kk * cv2.resize(cv2.GaussianBlur(s, (0, 0), sg / 4), (W, H), interpolation=cv2.INTER_LINEAR)
    return out


def to8(f):
    f = np.where(f < 0.85, f, 0.85 + 0.15 * np.tanh((f - 0.85) / 0.15))
    return (np.clip(f, 0, 1) * 255 + 0.5).astype(np.uint8)


@lru_cache(None)
def rgba(name):
    im = cv2.imread(f'{A}/{name}.png', cv2.IMREAD_UNCHANGED)
    return cv2.cvtColor(im, cv2.COLOR_BGRA2RGBA).astype(np.float32) / 255.0


def place_rgba(f, layer, cx, cy, scale=1.0, angle=0.0, alpha=1.0, add=False):
    """Composite an RGBA float layer centred at (cx, cy)."""
    h, w = layer.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, scale)
    M[0, 2] += cx - w / 2
    M[1, 2] += cy - h / 2
    warped = cv2.warpAffine(layer, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    a = warped[..., 3:4] * alpha
    if add:
        return f + warped[..., :3] * a
    return f * (1 - a) + warped[..., :3] * a


def glitch_bands(f, rng, k, n=12):
    """Horizontal band displacement + channel split (Spider-Verse style, no white)."""
    if k <= 0.01:
        return f
    out = f.copy()
    for _ in range(int(n * k) + 1):
        y0 = rng.integers(0, H - 40)
        hh = rng.integers(8, 90)
        dx = int(rng.normal(0, 70 * k))
        out[y0:y0 + hh] = np.roll(f[y0:y0 + hh], dx, 1)
    s = int(14 * k)
    if s:
        out[..., 0] = np.roll(out[..., 0], s, 1)
        out[..., 2] = np.roll(out[..., 2], -s, 1)
    return out


# ============================================================================ S0 title over footage
def _text_rgba(text, font, size, stretch=(1.0, 1.0), skew=0.0, track=0.0):
    m = text_mask(text, size, font=font, stretch=stretch, skew=skew, pad=90, tracking=track)
    return m


@lru_cache(None)
def title_layers():
    top = _text_rgba('OLD SCHOOL', F_BLACK, 150, stretch=(0.92, 1.0), skew=-0.12, track=0.02)
    bot = _text_rgba('M3 MATH', F_COND, 270, stretch=(0.86, 1.25), track=0.03)
    smoke = fractal_noise(top.shape[0], top.shape[1], 5, octaves=4, base=4)
    return top, bot, smoke


def title_fx(img, c):
    """Dark teal grade of the footage + OLD SCHOOL (smoky teal neon) / M3 MATH (white glow); glitches in and out."""
    f = img.astype(np.float32) / 255.0
    g = f.mean(2, keepdims=True)
    f = (g * 0.45 + f * 0.25) * np.float32([0.55, 0.95, 1.0]) * 0.9
    t = c['ls']
    rng = np.random.default_rng(3000 + c['fi'])
    top, bot, smoke = title_layers()
    on = 1.0
    flick = 0.45 if (0.30 < t < 0.62 and rng.random() < 0.18) else 1.0
    # OLD SCHOOL: teal neon with a smoky edge (noise eats into the glow, not into the letters)
    th, tw = top.shape
    edge = np.clip(dilate(top, 9) - top, 0, 1) * (0.4 + 0.6 * smoke)
    lay = np.zeros((th, tw, 4), np.float32)
    lay[..., :3] = TEAL[None, None] * np.clip(top * 1.05 + edge * 0.9, 0, 1.4)[..., None]
    lay[..., 3] = np.clip(top + edge * 0.8, 0, 1)
    s = 0.96 + 0.04 * sm(0, 0.8, t)
    canvas = np.zeros((H, W, 3), np.float32)
    canvas = place_rgba(canvas, lay, W / 2, 0.30 * H, scale=s * min(1.0, 0.92 * W / tw), alpha=on * flick, add=True)
    bh, bw = bot.shape
    blay = np.zeros((bh, bw, 4), np.float32)
    blay[..., :3] = np.float32([0.92, 1.0, 0.98])
    blay[..., 3] = bot
    canvas = place_rgba(canvas, blay, W / 2, 0.47 * H, scale=min(1.0, 0.86 * W / bw) * (0.98 + 0.03 * sm(0, 0.8, t)),
                        alpha=flick, add=True)
    f = f * (1 - np.clip(canvas.max(2, keepdims=True), 0, 1) * 0.6) + bloom(canvas, (0.9, 0.6), (8, 28))
    # glitch in / out
    gk = max((t - (c['dur'] - 0.16)) / 0.16, 0.0)
    f = glitch_bands(f, rng, min(gk, 1.0))
    return to8(f)


# ============================================================================ S1 / S2 neon logo outlines
@lru_cache(None)
def outline_layer(name, height=430):
    L = rgba(name)
    s = height / L.shape[0]
    L = cv2.resize(L, (int(L.shape[1] * s), height), interpolation=cv2.INTER_AREA)
    a = L[..., 3]
    lum = cv2.cvtColor((L[..., :3] * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY)
    ed = cv2.Canny(cv2.GaussianBlur(lum, (0, 0), 1.2), 40, 110).astype(np.float32) / 255 * (a > 0.5)
    rim = np.clip(cv2.dilate(a, np.ones((3, 3), np.uint8)) - cv2.erode(a, np.ones((5, 5), np.uint8)), 0, 1)
    line = np.clip(rim + ed * 0.8, 0, 1)
    line = cv2.GaussianBlur(line, (0, 0), 0.8)
    pad = 80
    line = np.pad(line, pad)
    fill = np.pad(a, pad)
    return line, fill


def outline_scene(name, color, drift=(1, 0), tint=(0.10, 0.16, 0.17)):
    def draw(c):
        t, q = c['ls'] + 0.2, c['q']
        f = fog(c['t'] + 3.0, tint)
        line, fill = outline_layer(name)
        h, w = line.shape
        col = np.float32(color)
        lay = np.zeros((h, w, 4), np.float32)
        lay[..., :3] = col * 1.25
        lay[..., 3] = np.clip(line * 1.2 + fill * 0.10, 0, 1)
        # slow 3D float: render flat then swing with tilt3d
        canvas = np.zeros((H, W, 3), np.float32)
        on = sm(0.0, 0.25, c['ls'])
        canvas = place_rgba(canvas, lay, W / 2 + drift[0] * 40 * (q - 0.5), 0.43 * H + drift[1] * 30 * (q - 0.5),
                            scale=0.92 + 0.10 * q, angle=-4 + 8 * q, alpha=on, add=True)
        canvas = vfx.tilt3d((np.clip(canvas, 0, 1) * 255).astype(np.uint8), yaw=-16 + 22 * q, pitch=6 - 6 * q,
                            cover=False).astype(np.float32) / 255
        f = f + bloom(canvas, (1.1, 0.8), (6, 26))
        # a soft light streak passing behind (reference has a thin light trail) — a line, not dots
        k = sm(0.2, 0.6, q) * (1 - sm(0.6, 0.95, q))
        if k > 0.01:
            st = np.zeros((H, W), np.float32)
            x0 = int(W * (0.15 + 0.7 * q))
            cv2.line(st, (x0 + 160, int(0.30 * H)), (x0 - 160, int(0.58 * H)), 1.0, 3, cv2.LINE_AA)
            st = cv2.GaussianBlur(st, (0, 0), 2) * k
            f = f + st[..., None] * col * 0.8
        return to8(f)
    draw.__name__ = f'outline_{name}'
    return draw


# ============================================================================ S3 the equation
EQ_H = 230   # logo height in the equation


GLYPH_FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'


@lru_cache(None)
def equation_world():
    """The equation written in four rows (vertical frame), world px with x centred on 0:
         sqrt( Mercedes x Audi )
       +   McLaren / ( Tesla - Lexus )
       x   Jaguar
       =   BMW
    Returns [(layer RGBA, cx, cy, appear_beat)], bmw (x, y)."""
    items = []

    def logo(name, h, cx, cy, beat, maxw=None):
        L = rgba(name)
        s = h / L.shape[0]
        if maxw and L.shape[1] * s > maxw:
            s = maxw / L.shape[1]
        L = cv2.resize(L, (int(L.shape[1] * s), int(L.shape[0] * s)), interpolation=cv2.INTER_AREA)
        items.append((L, cx, cy, beat))
        return L.shape[1]

    def glyph(ch, size, cx, cy, beat):
        f = ImageFont.truetype(GLYPH_FONT, size)
        bb = f.getbbox(ch)
        im = Image.new('L', (bb[2] - bb[0] + 40, bb[3] - bb[1] + 40), 0)
        ImageDraw.Draw(im).text((20 - bb[0], 20 - bb[1]), ch, font=f, fill=255)
        m = np.asarray(im, np.float32) / 255
        L = np.zeros(m.shape + (4,), np.float32)
        L[..., :3] = 1.0
        L[..., 3] = m
        items.append((L, cx, cy, beat))

    def lines(pts_list, th, beat):
        allp = np.concatenate([np.float32(p) for p in pts_list])
        x0, y0 = allp.min(0) - 30
        x1, y1 = allp.max(0) + 30
        L = np.zeros((int(y1 - y0), int(x1 - x0), 4), np.float32)
        for p in pts_list:
            q = (np.float32(p) - [x0, y0]).astype(np.int32)
            cv2.polylines(L, [q], False, (1, 1, 1, 1), th, cv2.LINE_AA)
        items.append((L, (x0 + x1) / 2, (y0 + y1) / 2, beat))

    # row 1: sqrt( Mercedes x Audi )
    y1 = -620
    lines([[(-505, y1 + 20), (-470, y1 - 5), (-420, y1 + 150), (-360, y1 - 175), (500, y1 - 175)]], 16, 0.0)
    logo('logo_mercedes', 270, -200, y1, 0.0)
    glyph('×', 130, 30, y1, 0.5)
    logo('logo_audi', 150, 290, y1, 0.5, maxw=380)
    # row 2: + McLaren / ( Tesla - Lexus )
    y2 = -150
    glyph('+', 150, -420, y2, 1.0)
    logo('logo_mclaren', 150, 80, y2 - 130, 1.0)
    lines([[(-270, y2), (440, y2)]], 15, 1.0)
    glyph('(', 220, -250, y2 + 150, 1.5)
    logo('logo_tesla', 140, -120, y2 + 150, 1.5)
    glyph('−', 120, 40, y2 + 150, 1.5)
    logo('logo_lexus', 140, 220, y2 + 150, 1.5, maxw=200)
    glyph(')', 220, 380, y2 + 150, 1.5)
    # row 3: x Jaguar
    y3 = 290
    glyph('×', 150, -300, y3, 2.0)
    logo('logo_jaguar', 180, 110, y3, 2.0, maxw=480)
    # row 4: = BMW
    y4 = 680
    glyph('=', 160, -250, y4, 2.5)
    logo('logo_bmw', 380, 110, y4, 3.0)
    return items, (110.0, float(y4))


def equation(c):
    q, t = c['q'], c['ls']
    bt = t / BEAT                         # beats into the scene
    items, (bx, by) = equation_world()
    rng = np.random.default_rng(4000 + c['fi'])
    f = fog(c['t'] * 1.2 + 9.0, (0.09, 0.12, 0.14), amount=0.85)
    keys = [(0.0, -560), (0.9, -420), (1.4, -180), (2.0, 60), (2.6, 330), (3.2, by)]
    camy = float(np.interp(bt, [k[0] for k in keys], [k[1] for k in keys]))
    camx = float(np.interp(bt, [0, 3.2], [-20, bx]))
    zoom = 1.0 + 0.12 * sm(2.6, 3.3, bt)
    dive = sm(3.35, 4.0, bt)
    zoom *= 1.0 + 7.0 * dive ** 2.2
    canvas = np.zeros((H, W, 3), np.float32)
    for L, cx, cy, ab in items:
        if bt < ab:
            continue
        a_t = (bt - ab) * BEAT
        pop = float(0.55 + 0.45 * ease_out_back(min(a_t / 0.20, 1.0)))
        al = float(min(a_t / 0.10, 1.0))
        sx = W / 2 + (cx - camx) * zoom
        sy = 0.47 * H + (cy - camy) * zoom
        if sy < -900 or sy > H + 900:
            continue
        canvas = place_rgba(canvas, L, sx, sy, scale=pop * zoom, alpha=al)
    f = f * (1 - np.clip(canvas.max(2, keepdims=True) * 1.5, 0, 1)) + canvas
    f = bloom(f, (0.35, 0.25), (6, 24))
    img = to8(f)
    k = 1 - sm(2.4, 3.3, bt)
    img = vfx.tilt3d(img, yaw=-10 * k, pitch=12 * k, roll=-2 * k)
    if dive > 0.01:
        img = _zoom_blur(img, 0.30 * dive)
    if bt < 0.25:                                   # drop glitch from the previous shot
        img = to8(glitch_bands(img.astype(np.float32) / 255, rng, 1 - bt / 0.25))
    return img


def _zoom_blur(img, k, cx=0.5, cy=0.45, n=8):
    acc = img.astype(np.float32)
    for i in range(1, n):
        s = 1.0 + k * i / n
        M = cv2.getRotationMatrix2D((cx * W, cy * H), 0, s)
        acc += cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return np.clip(acc / n + 0.5, 0, 255).astype(np.uint8)


# ============================================================================ S4 the chart
CH_W, CH_H = 1500, 1150
DATA = [('E30', 1986, 195, 'car_e30'), ('E36', 1992, 286, 'car_e36'), ('E46', 2000, 343, 'car_e46')]
X0, X1, Y0, Y1 = 1984, 2002, 150, 400
PLOT = (190, 170, 1440, 1020)   # left, top, right, bottom in chart px


def chart_xy(year, ps):
    l, t, r, b = PLOT
    return l + (year - X0) / (X1 - X0) * (r - l), b - (ps - Y0) / (Y1 - Y0) * (b - t)


@lru_cache(None)
def chart_base():
    im = Image.new('RGB', (CH_W, CH_H), (246, 245, 242))
    d = ImageDraw.Draw(im)
    l, t, r, b = PLOT
    ft = ImageFont.truetype(F_BOLD, 58)
    fs = ImageFont.truetype(F_BOLD, 30)
    fa = ImageFont.truetype(F_BOLD, 34)
    d.text((CH_W / 2, 70), 'BMW M3 Power Evolution', font=ft, fill=(20, 20, 24), anchor='mm')
    for ps in range(Y0, Y1 + 1, 50):
        _, y = chart_xy(X0, ps)
        d.line([(l, y), (r, y)], fill=(214, 214, 214), width=2)
        d.text((l - 18, y), str(ps), font=fs, fill=(70, 70, 76), anchor='rm')
    for yr in range(X0, X1 + 1, 2):
        x, _ = chart_xy(yr, Y0)
        d.line([(x, t), (x, b)], fill=(228, 228, 228), width=1)
        d.text((x, b + 34), str(yr), font=fs, fill=(70, 70, 76), anchor='mm')
    d.line([(l, t), (l, b), (r, b)], fill=(30, 30, 34), width=5)
    d.text((CH_W / 2, b + 92), 'Year', font=fa, fill=(40, 40, 46), anchor='mm')
    lab = Image.new('RGBA', (500, 60), (0, 0, 0, 0))
    ImageDraw.Draw(lab).text((250, 30), 'Power (PS)', font=fa, fill=(40, 40, 46, 255), anchor='mm')
    lab = lab.rotate(90, expand=True)
    im.paste(lab, (40, int((t + b) / 2 - 250)), lab)
    return np.asarray(im, np.float32) / 255


@lru_cache(None)
def chart_path():
    """Smooth path through the three launch points (Catmull-Rom), sampled densely: (N, 2) chart px."""
    P = np.array([chart_xy(y, p) for _, y, p, _ in DATA], np.float32)
    P = np.vstack([P[0] - (P[1] - P[0]) * 0.6, P, P[-1] + (P[-1] - P[-2]) * 0.35])
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for s in np.linspace(0, 1, 120, endpoint=False):
            s2, s3 = s * s, s * s * s
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * s + (2 * p0 - 5 * p1 + 4 * p2 - p3) * s2 +
                              (-p0 + 3 * p1 - 3 * p2 + p3) * s3))
    out.append(P[-2])
    return np.array(out, np.float32)


def chart(c):
    q, t = c['q'], c['ls']
    bt = t / BEAT
    base = chart_base().copy()
    path = chart_path()
    n = len(path)
    # the roundel draws the line: point k of 3 reached at beat k (0.15 -> 3.0)
    seg = [0, 120, 240, n - 1]
    prog = float(np.interp(bt, [0.15, 1.0, 2.0, 3.0], seg))
    k = int(prog)
    lay = (base * 255).astype(np.uint8).copy()
    if k > 1:
        pts = path[:k + 1].astype(np.int32)
        cv2.polylines(lay, [pts], False, (25, 25, 30), 15, cv2.LINE_AA)
        cv2.polylines(lay, [pts], False, (70, 70, 80), 5, cv2.LINE_AA)
    img = lay.astype(np.float32) / 255
    # points + car sprites + labels
    for i, (gen, yr, ps, car) in enumerate(DATA):
        a_t = (bt - (i + 0.98)) * BEAT if i else (bt - 0.2) * BEAT
        if a_t < 0:
            continue
        px, py = chart_xy(yr, ps)
        pop = float(0.5 + 0.5 * ease_out_back(min(a_t / 0.22, 1.0)))
        cv2.circle(img, (int(px), int(py)), 13, (0.08, 0.08, 0.1), -1, cv2.LINE_AA)
        S = rgba(car)
        sw = 400 / S.shape[1]
        sw = 470 / S.shape[1]
        S2 = cv2.resize(S, (470, int(S.shape[0] * sw)), interpolation=cv2.INTER_AREA)
        if i == 2:                                  # E46 sits top right: put it under the line
            cx, cy = px - 250, py + S2.shape[0] / 2 + 70
        else:
            cx, cy = px + (130 if i == 0 else -60), py - S2.shape[0] / 2 - 40
        sh = np.zeros_like(S2)
        sh[..., 3] = cv2.GaussianBlur(S2[..., 3], (0, 0), 10) * 0.35
        img = _place_chart(img, sh, cx + 8, cy + 18, pop)
        img = _place_chart(img, S2, cx, cy, pop)
        tag = _label(f'{gen}  ·  {ps} PS')
        ty = cy + S2.shape[0] / 2 + 36 if i < 2 else cy + S2.shape[0] / 2 + 36
        img = _place_chart(img, tag, cx, ty, pop)
    # BMW roundel riding the head of the line
    hx, hy = path[min(k, n - 1)]
    R = rgba('logo_bmw')
    rs = 84 / R.shape[0]
    R2 = cv2.resize(R, (84, 84), interpolation=cv2.INTER_AREA)
    ang = -prog * 2.2
    img = _place_chart(img, R2, hx, hy, 1.0, angle=ang)
    del rs
    # into the frame: paper -> perspective in red fog with a glowing red frame
    paper = (np.clip(img, 0, 1) * 255).astype(np.uint8)
    f = fog(c['t'] + 20.0, (0.30, 0.04, 0.06), amount=1.2)
    yaw = -30 + 24 * ease_io(q)
    pitch = 16 - 10 * ease_io(q)
    roll = -9 + 6 * q
    scale = 0.80 + 0.12 * ease_io(q)
    f = _paper_into(f, paper, yaw, pitch, roll, scale)
    rng = np.random.default_rng(5000 + c['fi'])
    if bt < 0.35:
        f = glitch_bands(f, rng, (0.35 - bt) / 0.35 * 0.7)
    return to8(f)


@lru_cache(None)
def _label(text):
    f = ImageFont.truetype(F_BLACK, 40)
    bb = f.getbbox(text)
    w, h = bb[2] - bb[0] + 44, bb[3] - bb[1] + 26
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w - 1, h - 1], radius=h // 2, fill=(205, 16, 34, 255))
    d.text((22 - bb[0], 13 - bb[1]), text, font=f, fill=(255, 255, 255, 255))
    return np.asarray(im, np.float32) / 255


def _place_chart(img, L, cx, cy, scale, angle=0.0):
    h, w = L.shape[:2]
    M = cv2.getRotationMatrix2D((w / 2, h / 2), angle, scale)
    M[0, 2] += cx - w / 2
    M[1, 2] += cy - h / 2
    wp = cv2.warpAffine(L, M, (CH_W, CH_H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    a = wp[..., 3:4]
    return img * (1 - a) + wp[..., :3] * a


def _paper_into(f, paper, yaw, pitch, roll, scale):
    h, w = paper.shape[:2]
    fl = (H / 2) / np.tan(np.radians(25))
    R = vfx._rot(yaw, pitch, roll)
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    c = (src - [w / 2, h / 2]) * scale * (W / w) * 1.45
    P = (R @ np.c_[c, np.zeros(4)].T).T
    dst = fl * P[:, :2] / (fl + P[:, 2:3]) + [W / 2, H * 0.47]
    M = cv2.getPerspectiveTransform(src, np.float32(dst))
    warped = cv2.warpPerspective(paper, M, (W, H), flags=cv2.INTER_LINEAR).astype(np.float32) / 255
    mask = cv2.warpPerspective(np.ones((h, w), np.float32), M, (W, H), flags=cv2.INTER_LINEAR)
    # red glowing frame around the sheet
    edge = np.zeros((H, W), np.float32)
    cv2.polylines(edge, [dst.astype(np.int32)], True, 1.0, 12, cv2.LINE_AA)
    glow = cv2.GaussianBlur(edge, (0, 0), 16) * 1.6 + cv2.GaussianBlur(edge, (0, 0), 50) * 1.2
    redk = np.float32([1.0, 0.10, 0.16])
    f = f + glow[..., None] * redk
    f = f * (1 - mask[..., None]) + warped * mask[..., None]
    rim = cv2.GaussianBlur(edge, (0, 0), 3) * 0.9
    f = f * (1 - rim[..., None] * 0.6) + rim[..., None] * np.float32([1.0, 0.35, 0.38])
    return f


# ============================================================================ S5 white E36 tumbling in space
def tumble(c):
    q, t = c['q'], c['ls']
    f = fog(c['t'] + 40.0, (0.07, 0.08, 0.10), amount=1.1)
    # orange light beams crossing (the reference's orange crane, as clean light lines)
    beams = np.zeros((H, W), np.float32)
    for i, (y0, sl, off) in enumerate([(0.22, 0.35, 0.0), (0.27, 0.32, 0.3), (0.80, -0.25, 0.6)]):
        x = int(W * (1.2 - 1.6 * ((q * 0.8 + off) % 1.0)))
        cv2.line(beams, (x - 600, int(H * (y0 - sl * 0.3))), (x + 600, int(H * (y0 + sl * 0.3))), 1.0, 4, cv2.LINE_AA)
    beams = cv2.GaussianBlur(beams, (0, 0), 2.0) * 0.8 + cv2.GaussianBlur(beams, (0, 0), 14) * 0.9
    f = f + beams[..., None] * np.float32([1.0, 0.42, 0.12]) * 0.7
    S = rgba('car_e36')
    acc = np.zeros((H, W, 3), np.float32)
    acc_a = np.zeros((H, W, 1), np.float32)
    for sub in (-0.5, 0.0, 0.5):                     # motion blur over the frame interval
        qq = q + sub / (c['dur'] * 60)
        e = ease_io(qq)
        roll = -35 + 230 * e
        yaw = 28 * np.sin(np.pi * qq * 1.3) - 8
        pitch = -22 + 30 * e
        sc = 0.92 + 0.30 * e
        cx = W * (0.42 + 0.16 * np.sin(np.pi * qq))
        cy = H * (0.52 - 0.10 * qq)
        rgb_s, a_s = _sprite3d(S, yaw, pitch, roll, sc, cx, cy)
        acc += rgb_s * a_s
        acc_a += a_s
    a = np.clip(acc_a / 3, 0, 1)
    col = acc / np.maximum(acc_a, 1e-6)
    # cool rim light + slight bloom on the white body
    f = f * (1 - a) + col * a * 1.05
    f = bloom(f, (0.25, 0.15), (5, 20))
    return to8(f)


def _sprite3d(S, yaw, pitch, roll, scale, cx, cy):
    h, w = S.shape[:2]
    fl = (H / 2) / np.tan(np.radians(28))
    R = vfx._rot(yaw, pitch, roll)
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    base = W * 0.95 / w
    c = (src - [w / 2, h / 2]) * base * scale
    P = (R @ np.c_[c, np.zeros(4)].T).T
    dst = fl * P[:, :2] / (fl + P[:, 2:3]) + [cx, cy]
    M = cv2.getPerspectiveTransform(src, np.float32(dst))
    wp = cv2.warpPerspective(S, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT)
    return wp[..., :3], wp[..., 3:4]


# ============================================================================ velocity part effects
def bw_pop(img, c):
    """Cold B&W first, colour pops in on the half beat with a zoom-blur burst (reference 10.0 -> 10.6)."""
    t = c['ls']
    k = sm(0.5 * BEAT - 0.05, 0.5 * BEAT + 0.08, t)
    f = img.astype(np.float32)
    g = f.mean(2, keepdims=True)
    cold = g * np.float32([0.92, 0.98, 1.04]) * 1.05 + 8
    f = cold * (1 - k) + f * k
    out = np.clip(f, 0, 255).astype(np.uint8)
    burst = np.exp(-max(t - 0.5 * BEAT, 0) / 0.09) * (t >= 0.5 * BEAT - 0.02)
    if burst > 0.02:
        out = _zoom_blur(out, 0.22 * burst, cy=0.5)
    return out


def red_ghost(img, c):
    """Red / cyan ghost copies trailing the motion (reference 11.2 - 11.8)."""
    q = c['q']
    k = 0.5 + 0.5 * np.sin(np.pi * q)
    f = img.astype(np.float32)
    M = cv2.getRotationMatrix2D((W / 2, H / 2), 0, 1.0 + 0.05 * k)
    M[0, 2] += 60 * k
    gh = cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    f[..., 0] = np.maximum(f[..., 0], gh[..., 0] * (0.55 + 0.4 * k))
    M2 = cv2.getRotationMatrix2D((W / 2, H / 2), 0, 1.0 - 0.03 * k)
    M2[0, 2] -= 22 * k
    gc = cv2.warpAffine(img, M2, (W, H), borderMode=cv2.BORDER_REFLECT).astype(np.float32)
    f[..., 1:] = f[..., 1:] * (1 - 0.25 * k) + gc[..., 1:] * 0.25 * k
    return np.clip(f, 0, 255).astype(np.uint8)


def velocity_grade(img, c):
    """Cool, slightly desaturated forest / road grade like the reference, before the film look."""
    f = img.astype(np.float32) / 255
    g = f.mean(2, keepdims=True)
    f = g + (f - g) * 0.85
    f = f * np.float32([0.96, 1.0, 1.03])
    f = np.clip((f - 0.5) * 1.10 + 0.5, 0, 1)
    return (f * 255 + 0.5).astype(np.uint8)


def radial_punch(img, c):
    """Zoom-blur burst on the beat inside a shot."""
    e = c['env']
    return _zoom_blur(img, 0.16 * e, cy=0.5) if e > 0.08 else img


OLD_FILM = dict(n=52, mix=0.55, sepia=0.22, scratch_density=0.45, noise=0.07, vignetting=0.18, vignetting_alpha=0.6)
