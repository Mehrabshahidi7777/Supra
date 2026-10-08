"""Night 6 car cutouts (GrabCut) for the multiverse portal and the CCTV ghost.
  WORK=$WORK python3 make_cuts6.py [key ...]   -> $WORK/cut6/<key>_img.png + <key>_mask.npy, sheet $WORK/sheets/cuts6.jpg
Rects are fractions of the 1040x1840 pin crop (x0, y0, x1, y1).  Optional polygon hints (pin px) refine leaks:
  'bg' polygons are forced background, 'fg' polygons forced foreground.
"""
import sys, os, subprocess, numpy as np, cv2
WORK = os.environ.get('WORK', '/home/claude/work_edit')
CUTS = {   # key: (clip, time, rect_frac, hints)
    'e30': ('n04', 4.00, (0.22, 0.44, 0.82, 0.64), {}),
    'e36': ('n12', 3.00, (0.05, 0.40, 0.94, 0.66), {}),
    'm2': ('n06', 8.80, (0.02, 0.36, 0.82, 0.60), {}),
    'm4d': ('n14', 3.40, (0.07, 0.34, 0.89, 0.54), {}),
    'm3g': ('n10', 0.90, (0.14, 0.41, 0.74, 0.60), {}),
}


def grab(clip, t):
    cmd = ['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', f'{WORK}/clips/{clip}.mp4', '-frames:v', '1',
           '-vf', 'crop=1040:1840:20:96', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-']
    return np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.uint8).reshape(1840, 1040, 3).copy()


def _img2pin(pts, x0, y0, s):
    return [(int(round(x / s + x0)), int(round(y / s + y0))) for x, y in pts]


# hand-traced outlines (pin px): outer = probable car, inner = sure car, everything else = sure background
POLY = {
    'e30': ([(290, 1015), (320, 965), (370, 928), (610, 926), (660, 955), (720, 985), (765, 995), (790, 1020), (868, 1032),
             (885, 1060), (885, 1185), (870, 1212), (600, 1215), (505, 1228), (440, 1228), (340, 1190), (288, 1150)],
            [(315, 1040), (345, 985), (390, 950), (590, 948), (650, 980), (725, 1020), (850, 1055), (868, 1080), (865, 1180),
             (600, 1195), (500, 1205), (450, 1205), (345, 1165), (305, 1110)]),
    'e36': (_img2pin([(45, 180), (60, 165), (140, 115), (185, 108), (430, 108), (470, 130), (525, 180), (640, 208), (705, 222),
                      (750, 240), (760, 262), (760, 400), (700, 412), (470, 425), (365, 425), (340, 380), (140, 340), (80, 330),
                      (60, 300), (42, 240)], 0, 680, 760 / 1040),
            _img2pin([(70, 200), (150, 130), (420, 125), (510, 190), (640, 225), (740, 258), (745, 390), (480, 400), (380, 405),
                      (350, 370), (150, 325), (90, 310), (65, 260)], 0, 680, 760 / 1040)),
    'm2': (_img2pin([(30, 262), (40, 230), (80, 205), (150, 195), (250, 180), (300, 150), (330, 118), (440, 104), (600, 100),
                     (690, 118), (740, 170), (760, 240), (760, 385), (720, 400), (565, 410), (555, 462), (470, 462), (425, 440),
                     (60, 442), (32, 410)], 0, 600, 760 / 900),
           _img2pin([(50, 270), (90, 222), (250, 198), (310, 165), (345, 135), (590, 118), (680, 135), (725, 180), (740, 250),
                     (745, 370), (560, 390), (540, 445), (480, 445), (420, 420), (70, 420), (48, 380)], 0, 600, 760 / 900)),
    'm4d': (_img2pin([(60, 250), (90, 205), (160, 170), (215, 145), (330, 112), (430, 112), (560, 112), (760, 118), (765, 170),
                      (755, 340), (720, 360), (540, 362), (390, 395), (290, 395), (230, 350), (130, 350), (62, 340)], 30, 560, 0.8),
            _img2pin([(85, 255), (170, 190), (230, 165), (330, 135), (430, 140), (600, 150), (735, 175), (740, 320), (540, 340),
                      (380, 375), (300, 375), (240, 335), (120, 330), (80, 320)], 30, 560, 0.8)),
    'm3g': (_img2pin([(52, 160), (85, 122), (170, 82), (250, 70), (445, 72), (515, 95), (545, 138), (575, 160), (650, 198),
                      (708, 218), (712, 340), (690, 368), (360, 372), (290, 372), (130, 330), (68, 300), (50, 260)], 120, 780, 1.0),
            _img2pin([(75, 170), (110, 140), (180, 100), (250, 92), (440, 95), (505, 115), (530, 160), (650, 218), (695, 240),
                      (695, 335), (365, 352), (300, 355), (140, 315), (80, 285), (70, 220)], 120, 780, 1.0)),
}


def cut(im, rect, hints, iters=10, key=None):
    H, W = im.shape[:2]
    x0, y0, x1, y1 = rect
    mask = np.full((H, W), cv2.GC_BGD, np.uint8)
    if key in POLY:
        outer, inner = POLY[key]
        cv2.fillPoly(mask, [np.array(outer, np.int32)], cv2.GC_PR_FGD)
        cv2.fillPoly(mask, [np.array(inner, np.int32)], cv2.GC_FGD)
    else:
        mask[int(H * y0):int(H * y1), int(W * x0):int(W * x1)] = cv2.GC_PR_FGD
    for poly in hints.get('bg', []):
        cv2.fillPoly(mask, [np.array(poly, np.int32)], cv2.GC_BGD)
    for poly in hints.get('fg', []):
        cv2.fillPoly(mask, [np.array(poly, np.int32)], cv2.GC_FGD)
    bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(im, mask, None, bgd, fgd, iters, cv2.GC_INIT_WITH_MASK)
    m = ((mask == 1) | (mask == 3)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n > 1:
        m = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    inv = (1 - m).astype(np.uint8)                       # fill small holes (windows stay if large)
    n2, lab2, st2, _ = cv2.connectedComponentsWithStats(inv, 4)
    for j in range(1, n2):
        x, y, ww, hh, a = st2[j]
        if x > 0 and y > 0 and x + ww < W and y + hh < H and a < 0.004 * W * H:
            m[lab2 == j] = 1
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.1)
    return np.clip((m - 0.5) * 3 + 0.5, 0, 1)


if __name__ == '__main__':
    os.makedirs(f'{WORK}/cut6', exist_ok=True); os.makedirs(f'{WORK}/sheets', exist_ok=True)
    keys = sys.argv[1:] or list(CUTS)
    tiles = []
    for k in keys:
        clip, t, rect, hints = CUTS[k]
        im = grab(clip, t)
        m = cut(im, rect, hints, key=k)
        cv2.imwrite(f'{WORK}/cut6/{k}_img.png', im)
        np.save(f'{WORK}/cut6/{k}_mask.npy', m.astype(np.float16))
        vis = im.astype(np.float32) * (0.2 + 0.8 * m[..., None])
        vis[..., 1] += (1 - m) * 70
        ys, xs = np.where(m > 0.5)
        y0, y1, x0, x1 = max(0, ys.min() - 30), ys.max() + 30, max(0, xs.min() - 30), xs.max() + 30
        v = np.clip(vis[y0:y1, x0:x1], 0, 255).astype(np.uint8)
        v = cv2.resize(v, (640, int(640 * v.shape[0] / v.shape[1])))
        cv2.putText(v, k, (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
        tiles.append(v)
        print(k, 'mask px', int((m > 0.5).sum()), 'bbox', x0, y0, x1, y1, flush=True)
    wmax = max(t.shape[1] for t in tiles)
    cv2.imwrite(f'{WORK}/sheets/cuts6.jpg', np.vstack([cv2.copyMakeBorder(t, 0, 4, 0, wmax - t.shape[1], cv2.BORDER_CONSTANT) for t in tiles]),
                [cv2.IMWRITE_JPEG_QUALITY, 90])
