"""Find logos / watermarks burned into a screen-recorded clip: edges that stay put across different shots.
  python3 overlay_find.py <clip> <t0> <t1> [std_thr=6] [grad_thr=40]   (clip = $WORK/clips/<clip>.mp4, pin box crop)
Prints boxes (x, y, w, h, area) in screen pixels and writes $WORK/sheets/ov_<clip>_<t0>.png (red = static, green = boxes).
Static-camera shots also light up -> always look at the image; faint logos may need std_thr 10 / grad_thr 14.
Night 5: found the "LD" logo (luxe_drive) at the bottom right; the user had flagged a crest logo at the bottom centre.
"""
import os, sys, subprocess, numpy as np, cv2
WORKDIR = os.environ.get('WORK', '/home/claude/work_edit')
nm, a, b = sys.argv[1], float(sys.argv[2]), float(sys.argv[3])
W, H = 520, 922
cmd = ['ffmpeg', '-v', 'error', '-ss', str(a), '-to', str(b), '-i', f'{WORKDIR}/clips/{nm}.mp4',
       '-vf', 'fps=5,crop=1040:1844:20:96,scale=520:922', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-']
fr = np.frombuffer(subprocess.run(cmd, capture_output=True).stdout, np.uint8).reshape(-1, H, W, 3)
g = fr.mean(3).astype(np.float32)
d = np.abs(np.diff(g, axis=0)).mean((1, 2))
cuts = [0] + [i + 1 for i in np.where(d > 18)[0]] + [len(fr)]
mids = sorted(set((cuts[i] + cuts[i + 1]) // 2 for i in range(len(cuts) - 1) if cuts[i + 1] - cuts[i] >= 2))
if len(mids) < 6:
    mids = list(np.linspace(0, len(fr) - 1, 8).astype(int))
S = g[mids]
std = S.std(0)
mean = S.mean(0)
gx = cv2.Sobel(mean, cv2.CV_32F, 1, 0); gy = cv2.Sobel(mean, cv2.CV_32F, 0, 1)
grad = np.hypot(gx, gy)
m = ((std < float(sys.argv[4]) if len(sys.argv)>4 else std<6) & (grad > (float(sys.argv[5]) if len(sys.argv)>5 else 40))).astype(np.uint8)
m[:70, :70] = 0                      # back button
m[:, :6] = 0; m[:, -6:] = 0; m[-6:, :] = 0; m[:6, :] = 0   # pin border
m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8))
n, lab, st, _ = cv2.connectedComponentsWithStats(cv2.dilate(m, np.ones((7, 7), np.uint8)))
boxes = sorted([(int(s[0]*2+20), int(s[1]*2+96), int(s[2]*2), int(s[3]*2), int(s[4])) for s in st[1:] if s[4] > 80], key=lambda r: -r[4])[:5]
print(f'{nm} {a:.0f}-{b:.0f}s shots={len(mids)} overlay boxes(x,y,w,h,area)={boxes}', flush=True)
vis = fr[mids[len(mids)//2]].copy()
vis[m > 0] = (0, 0, 255)
for (x, y, w, h, ar) in boxes:
    cv2.rectangle(vis, ((x-20)//2, (y-96)//2), ((x-20+w)//2, (y-96+h)//2), (0, 255, 0), 2)
cv2.imwrite(f'{WORKDIR}/sheets/ov_{nm}_{int(a)}.png', vis)
