"""Night 7 assets: brand logos (from the user's images) and M3 cutouts -> $WORK/n7/assets/*.png (RGBA).

  python3 assets.py            # builds everything + a check sheet $WORK/n7/assets/check.jpg

Inputs (copied from the chat to $WORK/n7/in): img1 BMW (fake checkerboard bg), img2 Mercedes (Pinterest screenshot,
white bg), img3 Audi (screenshot, black bg), img4 grid screenshot (Lexus, Jaguar, Tesla tiles), img5 E30 M3 studio
side photo, img7 McLaren speedmark on black; rec8 = white E36 M3 in a dark garage, rec6 = black E46 M3 on a highway.
"""
import os
import sys
import subprocess

import numpy as np
import cv2

KIT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit')
sys.path.insert(0, KIT)
from cutout import segment  # noqa: E402

WORK = os.environ.get('WORK', '/home/claude/work_edit')
IN = f'{WORK}/n7/in'
OUT = f'{WORK}/n7/assets'


def save(name, rgb, a):
    a8 = (np.clip(a, 0, 1) * 255).astype(np.uint8)
    ys, xs = np.where(a8 > 8)
    y0, y1, x0, x1 = max(0, ys.min() - 6), ys.max() + 7, max(0, xs.min() - 6), xs.max() + 7
    rgba = np.dstack([rgb[y0:y1, x0:x1], a8[y0:y1, x0:x1]])
    cv2.imwrite(f'{OUT}/{name}.png', cv2.cvtColor(rgba, cv2.COLOR_RGBA2BGRA))
    return rgba


def load(path):
    return cv2.cvtColor(cv2.imread(path), cv2.COLOR_BGR2RGB)


def flood_alpha(img, tol=14, feather=1.0):
    """Alpha = everything not connected to the image border by similar colour (white / black backgrounds)."""
    h, w = img.shape[:2]
    mask = np.zeros((h + 2, w + 2), np.uint8)
    im = img.copy()
    for (x, y) in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1), (w // 2, 0), (w // 2, h - 1), (0, h // 2),
                   (w - 1, h // 2)]:
        if mask[y + 1, x + 1] == 0:
            cv2.floodFill(im, mask, (x, y), (0, 0, 0), (tol,) * 3, (tol,) * 3,
                          cv2.FLOODFILL_MASK_ONLY | 4 | (255 << 8))
    bg = mask[1:-1, 1:-1] > 0
    a = (~bg).astype(np.float32)
    a = cv2.morphologyEx(a, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    return cv2.GaussianBlur(a, (0, 0), feather)


def bmw():
    im = load(f'{IN}/img1.jpg')
    g = cv2.medianBlur(cv2.cvtColor(im, cv2.COLOR_RGB2GRAY), 5)
    c = cv2.HoughCircles(g, cv2.HOUGH_GRADIENT, 1.2, 400, param1=120, param2=40, minRadius=220, maxRadius=330)
    cx, cy, r = c[0][0] if c is not None else (343, 328, 262)
    h, w = g.shape
    Y, X = np.mgrid[0:h, 0:w]
    a = np.clip((r - 2 - np.hypot(X - cx, Y - cy)) / 1.5 + 0.5, 0, 1).astype(np.float32)
    return save('logo_bmw', im, a), (cx, cy, r)


def chrome_alpha(im, thr=10, close=7, hole_frac=0.012):
    """Logo on a light background: pixels that differ from the border colour, closed, small holes filled
    (chrome highlights), big holes (ring interiors) kept transparent."""
    border = np.concatenate([im[0], im[-1], im[:, 0], im[:, -1]]).astype(np.float32)
    bg = np.median(border, 0)
    d = np.abs(im.astype(np.float32) - bg).max(2)
    m = (d > thr).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (close, close)))
    inv = (1 - m).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(inv, 4)
    h, w = m.shape
    for j in range(1, n):
        x, y, ww, hh, a = st[j]
        if x > 0 and y > 0 and x + ww < w and y + hh < h and a < hole_frac * h * w:
            m[lab == j] = 1
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n > 2:
        big = st[1:, cv2.CC_STAT_AREA].max()
        m = np.isin(lab, [j for j in range(1, n) if st[j, cv2.CC_STAT_AREA] > 0.06 * big]).astype(np.uint8)
    return cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.0)


def mercedes():
    im = load(f'{IN}/img2.jpg')[270:985, 180:900]
    return save('logo_mercedes', im, chrome_alpha(im))


def audi():
    im = load(f'{IN}/img3.jpg')[860:1200, 110:985]
    lum = im.max(2).astype(np.float32)
    a = np.clip((lum - 18) / 40, 0, 1)
    rgb = np.clip(im.astype(np.float32) * 1.15, 0, 255).astype(np.uint8)
    return save('logo_audi', rgb, cv2.GaussianBlur(a, (0, 0), 0.8))


def tile(name, box, invert=False):
    x0, y0, x1, y1 = box
    im = load(f'{IN}/img4.jpg')[y0:y1, x0:x1]
    a = chrome_alpha(im)
    if invert:                                   # black logo -> light silver so it reads on the dark fog
        g = 255 - cv2.cvtColor(im, cv2.COLOR_RGB2GRAY)
        im = np.dstack([g, g, g]).astype(np.uint8)
        im = np.clip(im.astype(np.float32) * 0.92 + 12, 0, 255).astype(np.uint8)
    return save(name, im, a)


def mclaren():
    im = load(f'{IN}/img7.jpg')
    hsv = cv2.cvtColor(im, cv2.COLOR_RGB2HSV).astype(np.float32)
    a = np.clip((hsv[..., 1] - 60) / 60, 0, 1) * np.clip((hsv[..., 2] - 60) / 60, 0, 1)
    return save('logo_mclaren', im, cv2.GaussianBlur(a, (0, 0), 0.8))


def frame(rec, t, box=(20, 96, 1060, 1936)):
    x0, y0, x1, y1 = box
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', f'{IN}/{rec}.mp4', '-frames:v', '1', '-vf',
                          f'crop={x1 - x0}:{y1 - y0}:{x0}:{y0}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(y1 - y0, x1 - x0, 3).copy()


def e36_cut(im):
    """White E36 on a dark wall / grey floor: GrabCut from a mask; dark wheels kept by filling the lower hull."""
    crop = im[730:1100].copy()
    h, w = crop.shape[:2]
    lum = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    gm = np.full((h, w), cv2.GC_PR_BGD, np.uint8)
    gm[18:350, 50:] = cv2.GC_PR_FGD
    gm[lum > 165] = cv2.GC_FGD
    gm[:16] = cv2.GC_BGD
    gm[:, :45] = cv2.GC_BGD
    gm[352:] = cv2.GC_BGD
    bgd = np.zeros((1, 65), np.float64)
    fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(cv2.cvtColor(crop, cv2.COLOR_RGB2BGR), gm, None, bgd, fgd, 10, cv2.GC_INIT_WITH_MASK)
    m = ((gm == 1) | (gm == 3)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    big = st[1:, cv2.CC_STAT_AREA].max()
    m = np.isin(lab, [j for j in range(1, n) if st[j, cv2.CC_STAT_AREA] > 0.02 * big]).astype(np.uint8)
    # lower body band (below the belt line): convex hull fills the black wheels / stripes
    band = m.copy()
    band[:150] = 0
    pts = cv2.findNonZero(band)
    if pts is not None:
        hull = cv2.convexHull(pts)
        hm = np.zeros_like(m)
        cv2.fillConvexPoly(hm, hull, 1)
        hm[:150] = 0
        m = np.maximum(m, hm)
    inv = (1 - m).astype(np.uint8)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, 4)
    for j in range(1, n2):
        x, y, ww, hh, a = st2[j]
        if x > 0 and y > 0 and x + ww < w and y + hh < h and a < 0.12 * w * h:
            m[lab2 == j] = 1
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    a = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.0)
    # blank the licence plate (white plate area right of the headlights)
    pm = np.zeros(crop.shape[:2], np.uint8)
    pm[222:288, 952:1018] = 255
    crop = cv2.inpaint(crop, pm, 9, cv2.INPAINT_TELEA)
    return save('car_e36', crop, a)


def car(name, im, rect, cut_below=None):
    m = segment(cv2.cvtColor(im, cv2.COLOR_RGB2BGR), rect, iters=10)
    if cut_below is not None:                         # drop floor reflections under the tyres
        m[int(cut_below * im.shape[0]):] = 0
    return save(name, im, m)


def main():
    os.makedirs(OUT, exist_ok=True)
    out = {}
    out['bmw'], circ = bmw()
    out['mercedes'] = mercedes()
    out['audi'] = audi()
    out['lexus'] = tile('logo_lexus', (25, 245, 520, 620))
    out['jaguar'] = tile('logo_jaguar', (548, 235, 1062, 440))
    out['tesla'] = tile('logo_tesla', (625, 715, 990, 1075), invert=True)
    out['mclaren'] = mclaren()
    e30 = load(f'{IN}/img5.jpg')
    out['e30'] = car('car_e30', e30, (0.02, 0.15, 0.97, 0.74))
    out['e36'] = e36_cut(frame('rec8', 1.5))
    e46 = frame('rec6', 6.75)
    out['e46'] = car('car_e46', e46, (0.13, 0.43, 0.70, 0.575), cut_below=0.566)
    # check sheet on a mid-grey + dark checker so halos show
    tiles = []
    for k, rgba in out.items():
        h, w = rgba.shape[:2]
        s = 240 / max(h, w)
        r = cv2.resize(rgba, (max(1, int(w * s)), max(1, int(h * s))), interpolation=cv2.INTER_AREA)
        bg = np.zeros((250, 250, 3), np.uint8) + 90
        bg[::20, :] = 60
        y, x = (250 - r.shape[0]) // 2, (250 - r.shape[1]) // 2
        a = r[..., 3:4] / 255.0
        bg[y:y + r.shape[0], x:x + r.shape[1]] = (r[..., :3] * a + bg[y:y + r.shape[0], x:x + r.shape[1]] * (1 - a))
        cv2.putText(bg, k, (4, 16), 0, 0.5, (255, 255, 0), 1)
        tiles.append(bg)
    cv2.imwrite(f'{OUT}/check.jpg', cv2.cvtColor(np.concatenate(tiles, 1), cv2.COLOR_RGB2BGR))
    print('bmw circle', circ, {k: v.shape for k, v in out.items()})


if __name__ == '__main__':
    main()
