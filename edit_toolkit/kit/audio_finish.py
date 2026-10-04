"""Finish the soundtrack: trim on the beat, optional tape-stop ("deep / slowed") ending,
anti-click fades, loudness to -14 LUFS.

  python3 audio_finish.py song.wav out.wav --start 1.12 --end 19.1914 [--tapestop 18.0868] [--lufs -14]

--start/--end are times in song.wav (pick beats from beats.py so the loop seam stays in time).
--tapestop: time in song.wav where the outro starts; from there to --end the song slows and
            drops in pitch (rate 1.0 -> 0.30) with a low-pass sweep. The user liked this
            ending on Night 3 ("آخرش صدای آهنگ کلفت بشه").
"""
import argparse, subprocess, re
import numpy as np
import scipy.io.wavfile as wf
import scipy.signal as ss


def lufs(path):
    out = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-af', 'ebur128', '-f', 'null', '-'],
                         capture_output=True, text=True).stderr
    m = re.findall(r'I:\s+(-?\d+\.\d) LUFS', out)
    return float(m[-1])


def tapestop(y, sr, i0, rate_end=0.30, lp_end=2200.0):
    n_total = len(y)
    n_out = n_total - i0
    u = np.arange(n_out) / n_out
    rate = 1.0 - (1.0 - rate_end) * u ** 0.55
    pos = i0 + np.cumsum(rate) - rate[0]
    idx = np.arange(n_total)
    seg = np.stack([np.interp(pos, idx, y[:, c]) for c in range(y.shape[1])], 1)
    blk, zi, out = 480, None, np.zeros_like(seg)
    for b in range(0, n_out, blk):
        fc = 12000 * (lp_end / 12000) ** (b / n_out)
        bb, aa = ss.butter(2, fc / (sr / 2))
        if zi is None:
            zi = np.stack([ss.lfilter_zi(bb, aa) * seg[0, c] for c in range(seg.shape[1])], 1)
        res, nz = [], []
        for c in range(seg.shape[1]):
            r, z = ss.lfilter(bb, aa, seg[b:b + blk, c], zi=zi[:, c]); res.append(r); nz.append(z)
        out[b:b + blk] = np.stack(res, 1); zi = np.stack(nz, 1)
    g = np.ones(n_out)
    tail = int(0.25 * sr); g[-tail:] *= np.linspace(1, 0.55, tail)
    y = y.copy(); y[i0:] = out * g[:, None]
    return y


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('out')
    ap.add_argument('--start', type=float, required=True)
    ap.add_argument('--end', type=float, required=True)
    ap.add_argument('--tapestop', type=float, default=None)
    ap.add_argument('--lufs', type=float, default=-14.0)
    a = ap.parse_args()
    sr, x = wf.read(a.src)
    x = x.astype(np.float64) / 32768.0
    if x.ndim == 1:
        x = np.stack([x, x], 1)
    y = x[int(round(a.start * sr)):int(round(a.end * sr))]
    if a.tapestop is not None:
        y = tapestop(y, sr, int(round((a.tapestop - a.start) * sr)))
    fi, fo = int(0.006 * sr), int(0.015 * sr)
    y[:fi] *= np.linspace(0, 1, fi)[:, None]
    y[-fo:] *= np.linspace(1, 0, fo)[:, None]
    wf.write(a.out, sr, (np.clip(y, -1, 1) * 32767).astype(np.int16))
    cur = lufs(a.out)
    gain = 10 ** ((a.lufs - cur) / 20)
    y = np.clip(y * gain, -0.98, 0.98)
    wf.write(a.out, sr, (y * 32767).astype(np.int16))
    print(f'{a.out}: {len(y) / sr:.3f} s, {cur:.1f} -> {lufs(a.out):.1f} LUFS')


if __name__ == '__main__':
    main()
