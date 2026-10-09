"""Re-render frame ranges of an engine edit and splice them into the finished silent render (fast fixes).

  python3 kit/splice.py projects/x/recipe.py 0:66 664:724 800:819     # then re-run audio + finish (below)

Reads $WORK/<name>/video_noaudio.mp4, replaces the listed frame ranges with fresh engine frames, writes it back,
then re-muxes the existing audio.wav into the 4K master and the 1080p copy (finish4k.sh).
"""
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import engine as E  # noqa: E402


def main(argv):
    R = E.load_recipe(argv[0])
    ranges = [tuple(int(x) for x in a.split(':')) for a in argv[1:]]
    ed = E.Edit(R)
    d = R['_dir']
    src = os.path.join(d, 'video_noaudio.mp4')
    tmp = os.path.join(d, 'video_spliced.mp4')
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', src, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                           stdout=subprocess.PIPE)
    enc = E._encoder(tmp)
    n = E.W * E.H * 3
    fi = 0
    while True:
        raw = dec.stdout.read(n)
        if len(raw) < n:
            break
        if any(a <= fi < b for a, b in ranges):
            raw = ed.frame(fi).tobytes()
        enc.stdin.write(raw)
        fi += 1
    enc.stdin.close()
    enc.wait()
    dec.wait()
    os.replace(tmp, src)
    name = R['name']
    subprocess.run(['bash', os.path.join(E.KIT, 'finish4k.sh'), src, os.path.join(d, 'audio.wav'),
                    os.path.join(d, f'{name}_4K_60fps.mp4'), os.path.join(d, f'{name}_1080p_60fps.mp4')], check=True)
    print('spliced', fi, 'frames;', ranges)


if __name__ == '__main__':
    main(sys.argv[1:])
