"""Tools for phone screen recordings (YouTube Shorts / Instagram / Pinterest).

  python3 clips.py box   rec.mp4                      -> video area inside the app UI (x0 y0 x1 y1)
  python3 clips.py sheet rec.mp4 out.png [--step 1]   -> timeline sheet of the video area
  python3 clips.py cuts  rec.mp4 [t0 t1]              -> scene cuts (s) inside the video area
  python3 clips.py audio rec.mp4 out.wav              -> 48 kHz stereo wav
  python3 clips.py extract <project_dir>              -> per-shot JPEG frames into $WORK/seg/<shot>/
                                                         (reads SHOTS / CUTS / SPEED from <project_dir>/shots.py)
Notes
  * The video area is found from temporal change (static app UI is excluded).
    Recordings of 9:16 pins in Pinterest: box ~ (23, 95, 1058, 1935) on a 1080x2340 screen.
  * Things to avoid when choosing in-points: Pinterest back button (top-left of the video),
    pause icon + time bar right after a tap (first ~0.8 s), "More to explore" grids,
    phone notification banners, the end of a pin where the next one starts.
  * The first ~0.3 s of a Shorts recording can still be the previous video.
"""
import os, sys, subprocess
import numpy as np, cv2

WORK = os.environ.get('WORK', '/home/claude/work_edit')


def video_box(path, samples=40, thr=6.0):
    cap = cv2.VideoCapture(path)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames = []
    for k in np.linspace(int(n * 0.05), int(n * 0.95), samples).astype(int):
        cap.set(cv2.CAP_PROP_POS_FRAMES, int(k))
        ok, fr = cap.read()
        if ok:
            frames.append(cv2.resize(cv2.cvtColor(fr, cv2.COLOR_BGR2GRAY), None, fx=0.25, fy=0.25).astype(np.float32))
    st = np.std(np.array(frames), 0)
    act = st > thr
    rows = np.where(act.mean(1) > 0.25)[0]
    cols = np.where(act.mean(0) > 0.25)[0]
    # largest contiguous run of rows
    runs, s, p = [], rows[0], rows[0]
    for y in rows[1:]:
        if y != p + 1:
            runs.append((s, p)); s = y
        p = y
    runs.append((s, p))
    r0, r1 = max(runs, key=lambda r: r[1] - r[0])
    return int(cols.min() * 4), int(r0 * 4), int((cols.max() + 1) * 4), int((r1 + 1) * 4)


def sheet(path, out, step=1.0, box=None, cols=12, w=117):
    box = box or video_box(path)
    x0, y0, x1, y1 = box
    cap = cv2.VideoCapture(path)
    dur = cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 30)
    h = int(w * (y1 - y0) / (x1 - x0))
    ims, t = [], 0.0
    while t < dur - 0.05:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, fr = cap.read()
        if not ok:
            break
        im = cv2.resize(fr[y0:y1, x0:x1], (w, h), interpolation=cv2.INTER_AREA)
        cv2.putText(im, f'{t:.1f}', (2, 12), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
        ims.append(im); t += step
    while len(ims) % cols:
        ims.append(np.zeros_like(ims[0]))
    cv2.imwrite(out, np.vstack([np.hstack(ims[i:i + cols]) for i in range(0, len(ims), cols)]))


def cuts(path, t0=0.0, t1=1e9, box=None, thr=14.0):
    box = box or video_box(path)
    x0, y0, x1, y1 = box
    cap = cv2.VideoCapture(path)
    cap.set(cv2.CAP_PROP_POS_MSEC, t0 * 1000)
    prev, out = None, []
    while True:
        ok, fr = cap.read()
        if not ok:
            break
        t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        if t > t1:
            break
        g = cv2.resize(cv2.cvtColor(fr[y0:y1, x0:x1], cv2.COLOR_BGR2GRAY), (64, 112)).astype(np.float32)
        if prev is not None:
            d = float(np.abs(g - prev).mean())
            if d > thr:
                out.append((round(t, 3), round(d, 1)))
        prev = g
    return out


def extract(project_dir):
    sys.path.insert(0, project_dir)
    from shots import SHOTS, CUTS
    try:
        from shots import SPEED
    except ImportError:
        SPEED = {}
    for i, (nm, car, clip, src, z, cx, cy, box) in enumerate(SHOTS):
        dur = (CUTS[i + 1] - CUTS[i]) * SPEED.get(nm, 1.0)
        d = f'{WORK}/seg/{nm}'
        os.makedirs(d, exist_ok=True)
        x0, y0, x1, y1 = box
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', f'{src:.3f}', '-i', f'{WORK}/clips/{clip}.mp4', '-t', f'{dur + 0.12:.3f}',
                        '-vf', f'crop={x1 - x0}:{y1 - y0}:{x0}:{y0},fps=30', '-q:v', '2', f'{d}/%04d.jpg'], check=True)
        print(nm, f'{CUTS[i]:.3f}-{CUTS[i + 1]:.3f}', len(os.listdir(d)), 'frames')


if __name__ == '__main__':
    a = sys.argv
    if a[1] == 'box':
        print(video_box(a[2]))
    elif a[1] == 'sheet':
        st = float(a[a.index('--step') + 1]) if '--step' in a else 1.0
        sheet(a[2], a[3], st)
    elif a[1] == 'cuts':
        t0 = float(a[3]) if len(a) > 3 else 0.0
        t1 = float(a[4]) if len(a) > 4 else 1e9
        print(cuts(a[2], t0, t1))
    elif a[1] == 'audio':
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', a[2], '-vn', '-ac', '2', '-ar', '48000', '-c:a', 'pcm_s16le', a[3]], check=True)
    elif a[1] == 'extract':
        extract(a[2])
