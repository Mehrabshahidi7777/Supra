"""Music analysis for beat-synced edits.

Usage:
  python3 beats.py song.wav [--from 0.5] [--to 18.5] [--drop 5.57] [--json beats.json] [--plot audio.png]

Prints/saves: tempo candidates, onset events with strength (0..1), kick times,
and a fitted beat grid (period + first beat). Cut on every 1, 2 or 4 grid beats.
Tips:
  * Screen recordings often carry ~0.05-0.1 s of A/V offset: trust the audio grid,
    not the reference video's visual cut times.
  * --drop: give the time of the big hit if you know it; the grid is anchored there.
"""
import argparse, json
import numpy as np
import scipy.io.wavfile as wf
import scipy.signal as ss


def load_mono(path):
    sr, x = wf.read(path)
    x = x.astype(np.float32)
    if x.ndim > 1:
        x = x.mean(1)
    x /= 32768.0 if np.abs(x).max() > 2 else 1.0
    return sr, x


def band_flux(S, f, lo, hi):
    b = S[(f >= lo) & (f < hi)]
    L = np.log1p(200 * b)
    d = np.maximum(0, np.diff(L, axis=1)).sum(0)
    return np.r_[0, d]


def norm(a):
    a = ss.savgol_filter(a, 7, 2)
    a = np.maximum(a, 0)
    return a / (np.percentile(a, 99.7) + 1e-9)


def analyze(path, t_from=0.0, t_to=None, drop=None):
    sr, x = load_mono(path)
    hop, n = 256, 2048
    f, t, Z = ss.stft(x, fs=sr, nperseg=n, noverlap=n - hop, boundary=None, padded=False)
    S = np.abs(Z)
    fps = sr / hop
    low = band_flux(S, f, 30, 150)
    full = band_flux(S, f, 30, 16000)
    high = band_flux(S, f, 3000, 16000)
    comb = 0.5 * norm(low) + 0.3 * norm(full) + 0.2 * norm(high)
    t_to = t_to or t[-1]
    sel = (t >= t_from) & (t <= t_to)
    # tempo candidates
    seg = comb[sel] - comb[sel].mean()
    ac = np.correlate(seg, seg, 'full')[len(seg) - 1:]
    ac /= ac[0] + 1e-9
    lags = np.arange(len(ac)) / fps
    m = (lags > 0.25) & (lags < 1.6)
    L, A = lags[m], ac[m]
    cands = []
    for i in np.argsort(A)[::-1]:
        if all(abs(L[i] - c[0]) > 0.03 for c in cands):
            cands.append((float(L[i]), float(A[i])))
        if len(cands) >= 5:
            break
    # beat grid fit around the best candidate in 0.3-0.75 s
    p0 = next((c[0] for c in cands if 0.3 <= c[0] <= 0.75), cands[0][0])
    best = None
    anchor = drop if drop is not None else t_from
    for P in np.arange(p0 * 0.97, p0 * 1.03, 0.0002):
        for ph in np.arange(-P / 2, P / 2, 0.004):
            g = np.arange(anchor + ph, t_to, P)
            g = g[g >= t_from]
            idx = np.clip((g * fps).astype(int), 0, len(comb) - 1)
            sc = comb[idx].sum() + 0.5 * norm(low)[idx].sum()
            if best is None or sc > best[0]:
                best = (sc, P, anchor + ph)
    _, P, b0 = best
    k0 = int(np.floor((t_from - b0) / P))
    grid = [b0 + k * P for k in range(k0, int((t_to - b0) / P) + 1) if b0 + k * P >= t_from]
    pk, _ = ss.find_peaks(comb, distance=int(0.12 * fps), prominence=0.15)
    events = [(round(float(t[p]), 3), round(float(comb[p]), 2)) for p in pk if t_from <= t[p] <= t_to]
    kp, _ = ss.find_peaks(norm(low), distance=int(0.15 * fps), prominence=0.25)
    kicks = [round(float(t[p]), 3) for p in kp if t_from <= t[p] <= t_to]
    return dict(sr=sr, tempo_candidates=[(round(l, 4), round(60 / l, 1), round(a, 2)) for l, a in cands],
                period=round(float(P), 5), bpm=round(60 / P, 2), first_beat=round(float(b0), 4),
                grid=[round(float(g), 4) for g in grid], events=events, kicks=kicks), (t, comb, x, sr, S, f)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('wav')
    ap.add_argument('--from', dest='t_from', type=float, default=0.0)
    ap.add_argument('--to', dest='t_to', type=float, default=None)
    ap.add_argument('--drop', type=float, default=None)
    ap.add_argument('--json')
    ap.add_argument('--plot')
    a = ap.parse_args()
    res, (t, comb, x, sr, S, f) = analyze(a.wav, a.t_from, a.t_to, a.drop)
    print('tempo candidates (lag s, bpm, score):', res['tempo_candidates'])
    print(f"grid: period {res['period']} s = {res['bpm']} BPM, anchor beat {res['first_beat']}")
    print('grid beats:', res['grid'])
    print('events (t, strength):', res['events'])
    if a.json:
        json.dump(res, open(a.json, 'w'), indent=1)
    if a.plot:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(3, 1, figsize=(20, 9), sharex=True)
        hop = sr // 20
        rms = np.array([np.sqrt(np.mean(x[i:i + hop] ** 2)) for i in range(0, len(x), hop)])
        ax[0].plot(np.arange(len(rms)) / 20, rms); ax[0].set_title('rms')
        ax[1].plot(t, comb); ax[1].set_title('onset strength')
        ax[2].pcolormesh(t, f[f < 6000], np.log1p(100 * S[f < 6000]), shading='auto')
        for axx in ax[:2]:
            axx.vlines(res['grid'], 0, 1, colors='r', lw=0.6, transform=axx.get_xaxis_transform())
            axx.grid(alpha=.3)
        plt.tight_layout(); plt.savefig(a.plot, dpi=60)


if __name__ == '__main__':
    main()
