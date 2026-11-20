# Mammoth skeleton scan (Smithsonian NMNH paleobiology 3447777, CC0), step 3: cut out individual bones -> modeli/skan_*.obj
# Scan axes: X width, Y height, Z forward (snout). Convert to ours, forward +Y, up +Z: (x, y, z) -> (-x, z, y).
#   python -I skan_kosti.py <root>
import sys, numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
R = sys.argv[1]
V = np.load(f'{R}/skan/v.npy', mmap_mode='r'); F = np.load(f'{R}/skan/f.npy', mmap_mode='r')
def vyrezat(z=(-9, 9), y=(-9, 9), x=(-9, 9), skolko=1, min_v=2000):
    vin = (V[:, 2] >= z[0]) & (V[:, 2] <= z[1]) & (V[:, 1] >= y[0]) & (V[:, 1] <= y[1]) & (V[:, 0] >= x[0]) & (V[:, 0] <= x[1])
    fin = vin[F[:, 0]] & vin[F[:, 1]] & vin[F[:, 2]]
    Fs = np.asarray(F[fin]); idx = np.unique(Fs); rm = -np.ones(len(V), np.int64); rm[idx] = np.arange(len(idx)); Fl = rm[Fs]; n = len(idx)
    e = np.concatenate([Fl[:, [0, 1]], Fl[:, [1, 2]], Fl[:, [2, 0]]])
    nc, lab = connected_components(coo_matrix((np.ones(len(e), np.int8), (e[:, 0], e[:, 1])), shape=(n, n)), directed=False)
    cnt = np.bincount(lab); out = []
    for k in np.argsort(-cnt)[:skolko]:
        if cnt[k] < min_v: break
        vm = lab == k; fm = vm[Fl[:, 0]]
        sub = np.nonzero(vm)[0]; r2 = -np.ones(n, np.int64); r2[sub] = np.arange(len(sub))
        out.append((np.asarray(V[idx[sub]]), r2[Fl[fm]]))
    return out
def k_nashim(P):   # (x, y, z) scan -> (-x, z, y)
    return np.stack([-P[:, 0], P[:, 2], P[:, 1]], 1)
def zapisat(imya, P, Fc, dlinnaya=False):
    P = k_nashim(P).astype(np.float64)
    if dlinnaya:     # long bone axis along Z (principal component)
        c = P.mean(0); U, S, Vt = np.linalg.svd(P[::max(1, len(P) // 50000)] - c, full_matrices=False); ax = Vt[0]
        if ax[2] < 0: ax = -ax
        z_ = np.array([0, 0, 1.0]); v_ = np.cross(ax, z_); s_ = np.linalg.norm(v_); c_ = ax @ z_
        if s_ > 1e-6:
            vx = np.array([[0, -v_[2], v_[1]], [v_[2], 0, -v_[0]], [-v_[1], v_[0], 0]]); Rm = np.eye(3) + vx + vx @ vx * ((1 - c_) / s_ ** 2)
            P = (P - c) @ Rm.T + c
    lo, hi = P.min(0), P.max(0)
    P[:, 0] -= (lo[0] + hi[0]) / 2; P[:, 1] -= (lo[1] + hi[1]) / 2; P[:, 2] -= lo[2]
    with open(f'{R}/modeli/{imya}.obj', 'w') as fo:
        fo.write(f'o {imya}\n'); fo.write(''.join(f'v {a:.5f} {b:.5f} {c:.5f}\n' for a, b, c in P))
        fo.write(''.join(f'f {a+1} {b+1} {c+1}\n' for a, b, c in Fc))
    print(imya, len(P), 'vertices', 'size', np.round(P.max(0) - P.min(0), 2))
# skull: without the neck vertebrae (z < .56) and without the tusks (z > 1.10); tusk stubs stay in the sockets
(P, Fc), = vyrezat(z=(.56, 1.20), y=(.3, 1.8), skolko=1); zapisat('skan_cherep', P, Fc)
# mandible: a separate piece
(P, Fc), = vyrezat(z=(.6, 1.06), y=(.5, 1.15), x=(-.25, .35), skolko=1); zapisat('skan_chelyust', P, Fc)
# tusks: from the socket forward, left and right
for nm, xr in (('skan_bivenR', (0, 1)), ('skan_bivenL', (-1, 0))):
    res = vyrezat(z=(1.20, 2.6), y=(.1, 1.3), x=xr, skolko=1, min_v=20000)
    if res: zapisat(nm, *res[0], dlinnaya=False)
# leg bones (right side): femur and tibia at the back, humerus and forearm at the front
for nm, kw in (('skan_bedro', dict(z=(-2.2, -1.6), y=(-.6, .42), x=(.18, .85))), ('skan_golen', dict(z=(-2.35, -1.55), y=(-1.38, -.66), x=(.05, .85))),
               ('skan_predpl', dict(z=(-.4, .38), y=(-1.36, -.52), x=(.05, .85)))):
    res = vyrezat(skolko=1, min_v=20000, **kw)
    if res: zapisat(nm, *res[0], dlinnaya=True)
# ribs: cut off from the spine they fall apart into separate pieces

print('ok')
