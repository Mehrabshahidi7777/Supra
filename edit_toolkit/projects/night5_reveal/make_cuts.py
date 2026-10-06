import sys, os, subprocess, numpy as np, cv2
sys.path.insert(0, os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'kit')))
from cutout import segment
WORK = os.environ.get('WORK', '/home/claude/work_edit')
CUTS = {  # key: (clip, time, rect_frac)
    'p1a': ('p06', 11.70, (0.20, 0.47, 0.86, 0.70)),
    'p1b': ('p06', 18.90, (0.16, 0.47, 0.86, 0.72)),
    'blk': ('q3', 0.50, (0.0, 0.42, 0.94, 0.73)),
    'slv': ('p10', 4.90, (0.07, 0.37, 0.93, 0.64)),
    'slvf': ('p10', 13.20, (0.04, 0.31, 0.98, 0.67)),
}
keys = sys.argv[1:] or list(CUTS)
tiles = []
for k in keys:
    clip, t, rect = CUTS[k]
    cmd = ['ffmpeg', '-v', 'error', '-ss', f'{t:.3f}', '-i', f'{WORK}/clips/{clip}.mp4', '-frames:v', '1',
           '-vf', 'crop=1040:1840:20:96', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-']
    im = np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.uint8).reshape(1840, 1040, 3).copy()
    m = segment(im, rect, iters=10)
    cv2.imwrite(f'{WORK}/cut/{k}_img.png', im)
    np.save(f'{WORK}/cut/{k}_mask.npy', m.astype(np.float16))
    vis = im.astype(np.float32) * (0.25 + 0.75 * m[..., None])
    vis[..., 2] += (1 - m) * 60
    ys, xs = np.where(m > 0.5)
    y0, y1, x0, x1 = max(0, ys.min() - 40), ys.max() + 40, max(0, xs.min() - 40), xs.max() + 40
    v = np.clip(vis[y0:y1, x0:x1], 0, 255).astype(np.uint8)
    v = cv2.resize(v, (560, int(560 * v.shape[0] / v.shape[1])))
    cv2.putText(v, k, (8, 26), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    tiles.append(v)
    print(k, 'mask px', int((m > 0.5).sum()), 'bbox', x0, y0, x1, y1)
hmax = max(t.shape[0] for t in tiles)
tiles = [cv2.copyMakeBorder(t, 0, hmax - t.shape[0], 0, 4, cv2.BORDER_CONSTANT) for t in tiles]
cv2.imwrite(f'{WORK}/sheets/cuts_check.jpg', np.hstack(tiles), [cv2.IMWRITE_JPEG_QUALITY, 90])
