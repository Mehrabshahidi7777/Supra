import numpy as np
def feats(x, deg):
    r, g, b = x[:, 0], x[:, 1], x[:, 2]
    f = [np.ones_like(r), r, g, b]
    if deg >= 2:
        f += [r * r, g * g, b * b, r * g, r * b, g * b]
    if deg >= 3:
        f += [r ** 3, g ** 3, b ** 3, r * r * g, r * r * b, g * g * r, g * g * b, b * b * r, b * b * g, r * g * b]
    return np.stack(f, 1)
def fit(src, dst, deg=2, iters=3, keep=0.8, lam=1e-3):
    """robust least squares: src, dst (N,3) in 0..1 -> coefficient matrix (F,3)"""
    X = feats(src, deg); Y = dst
    w = np.ones(len(X), bool)
    for _ in range(iters):
        A = X[w]; B = Y[w]
        C = np.linalg.solve(A.T @ A + lam * np.eye(A.shape[1]), A.T @ B)
        res = np.abs(X @ C - Y).sum(1)
        thr = np.quantile(res, keep)
        w = res <= thr
    return C
def apply(C, img, deg=2):
    h, w_, _ = img.shape
    out = feats(img.reshape(-1, 3), deg) @ C
    return np.clip(out.reshape(h, w_, 3), 0, 1.2)
