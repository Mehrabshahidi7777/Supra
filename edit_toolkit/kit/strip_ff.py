"""Time strip of a clip range decoded with ffmpeg (accurate timestamps).
  python3 strip_ff.py <clip> <t0> <t1> <step> <out.png> [cols]       (clip = $WORK/clips/<clip>.mp4, pin box crop)

Why: phone screen recordings are variable-frame-rate (r_frame_rate 120, avg ~30-36 fps, frames bunched unevenly).
OpenCV's CAP_PROP_POS_MSEC seek and index/fps times (strip.py, clips.py sheet/cuts) drift by 0.1-0.8 s from the real
timestamps on such files, while extraction (ffmpeg -ss) uses the real ones. Pick in-points on THIS strip (Night 6 lesson:
a STOP sign that was "gone at 8.00" on an OpenCV strip was still in frame at ffmpeg 8.00).
"""
import os, sys, subprocess, numpy as np, cv2
WORK = os.environ.get('WORK', '/home/claude/work_edit')


def strip(clip, t0, t1, step, out, cols=14, w=96, crop=(20, 96, 1060, 1936)):
    x0, y0, x1, y1 = crop
    h = int(round(w * (y1 - y0) / (x1 - x0)))
    h += h % 2
    cmd = ['ffmpeg', '-v', 'error', '-ss', f'{t0:.3f}', '-to', f'{t1 + 1e-3:.3f}', '-i', f'{WORK}/clips/{clip}.mp4',
           '-vf', f'fps={1 / step:.6f}:round=near,crop={x1 - x0}:{y1 - y0}:{x0}:{y0},scale={w}:{h}', '-f', 'rawvideo',
           '-pix_fmt', 'bgr24', '-']
    raw = subprocess.run(cmd, capture_output=True).stdout
    n = len(raw) // (w * h * 3)
    fr = np.frombuffer(raw[:n * w * h * 3], np.uint8).reshape(n, h, w, 3)
    ims = []
    for k in range(n):
        im = fr[k].copy()
        cv2.putText(im, f'{t0 + k * step:.2f}', (2, 11), cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 255, 255), 1)
        ims.append(im)
    while len(ims) % cols:
        ims.append(np.zeros((h, w, 3), np.uint8))
    cv2.imwrite(out, np.vstack([np.hstack(ims[i:i + cols]) for i in range(0, len(ims), cols)]))
    return n


if __name__ == '__main__':
    a = sys.argv
    print(strip(a[1], float(a[2]), float(a[3]), float(a[4]), a[5], int(a[6]) if len(a) > 6 else 14), 'frames')
