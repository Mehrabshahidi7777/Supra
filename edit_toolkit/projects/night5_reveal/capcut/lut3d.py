import numpy as np
N = 33
def build(src_list, dst_list, step=3):
    """3D LUT (N^3 x 3) mapping src RGB -> dst RGB, from lists of (H,W,3) uint8 frames; empty cells filled by diffusion"""
    sums = np.zeros((N ** 3, 3), np.float64); cnt = np.zeros(N ** 3, np.float64)
    for s, d in zip(src_list, dst_list):
        s = s[::step, ::step].reshape(-1, 3).astype(np.float32) / 255 * (N - 1)
        d = d[::step, ::step].reshape(-1, 3).astype(np.float64) / 255
        i = np.rint(s).astype(np.int64)
        idx = (i[:, 0] * N + i[:, 1]) * N + i[:, 2]
        cnt += np.bincount(idx, minlength=N ** 3)
        for c in range(3):
            sums[:, c] += np.bincount(idx, weights=d[:, c], minlength=N ** 3)
    lut = np.zeros((N ** 3, 3)); ok = cnt > 2
    lut[ok] = sums[ok] / cnt[ok, None]
    # identity as a weak prior + diffusion into empty cells
    g = np.stack(np.meshgrid(*[np.linspace(0, 1, N)] * 3, indexing='ij'), -1).reshape(-1, 3)
    L = lut.reshape(N, N, N, 3); K = ok.reshape(N, N, N)
    filled = np.where(K[..., None], L, g.reshape(N, N, N, 3))
    for _ in range(60):
        acc = np.zeros_like(filled); w = np.zeros(K.shape)
        for ax in range(3):
            for sh in (1, -1):
                acc += np.roll(filled, sh, axis=ax); w += 1
        avg = acc / w[..., None]
        filled = np.where(K[..., None], L, avg)
    return filled, K
def apply(lut, img):
    """trilinear lookup; img float (..,3) in 0..1"""
    x = np.clip(img, 0, 1) * (N - 1)
    i0 = np.floor(x).astype(np.int32); i0 = np.clip(i0, 0, N - 2); f = x - i0
    out = 0
    for dr in (0, 1):
        for dg in (0, 1):
            for db in (0, 1):
                w = ((f[..., 0] if dr else 1 - f[..., 0]) * (f[..., 1] if dg else 1 - f[..., 1]) * (f[..., 2] if db else 1 - f[..., 2]))
                out = out + w[..., None] * lut[i0[..., 0] + dr, i0[..., 1] + dg, i0[..., 2] + db]
    return out
