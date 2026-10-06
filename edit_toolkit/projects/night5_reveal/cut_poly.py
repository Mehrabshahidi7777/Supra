import os, sys, numpy as np, cv2
WORK = os.environ.get('WORK', '/home/claude/work_edit')
POLY = {   # (outer probable-FG polygon, inner sure-FG polygon) in pin coords
    'blk': ([(40,255),(150,232),(300,222),(520,222),(655,292),(880,362),(940,420),(940,602),(800,628),(520,628),(440,618),(150,522),(55,505),(38,420)],
            [(110,335),(300,268),(520,268),(640,335),(850,400),(895,470),(895,580),(520,592),(170,480),(90,450)], 640),
    'slv': ([(118,300),(178,248),(278,196),(545,196),(655,278),(862,312),(912,398),(918,518),(700,532),(380,542),(300,534),(128,482),(112,400)],
            [(175,335),(292,232),(520,232),(628,302),(838,346),(878,420),(878,500),(400,510),(175,452)], 560),
}
for k in sys.argv[1:]:
    outer, inner, oy = POLY[k]
    im = cv2.imread(f'{WORK}/cut/{k}_img.png')
    H, W = im.shape[:2]
    mask = np.full((H, W), cv2.GC_BGD, np.uint8)
    cv2.fillPoly(mask, [np.array([(x, y + oy) for x, y in outer], np.int32)], cv2.GC_PR_FGD)
    cv2.fillPoly(mask, [np.array([(x, y + oy) for x, y in inner], np.int32)], cv2.GC_FGD)
    bgd = np.zeros((1, 65), np.float64); fgd = np.zeros((1, 65), np.float64)
    cv2.grabCut(im, mask, None, bgd, fgd, 8, cv2.GC_INIT_WITH_MASK)
    m = ((mask == 1) | (mask == 3)).astype(np.uint8)
    n, lab, st, _ = cv2.connectedComponentsWithStats(m, 8)
    if n > 1:
        m = (lab == 1 + np.argmax(st[1:, cv2.CC_STAT_AREA])).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    m = cv2.GaussianBlur(m.astype(np.float32), (0, 0), 1.1)
    m = np.clip((m - 0.5) * 3 + 0.5, 0, 1)
    np.save(f'{WORK}/cut/{k}_mask.npy', m.astype(np.float16))
    print(k, int((m > 0.5).sum()))
