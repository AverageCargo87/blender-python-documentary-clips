# Mammoth skeleton scan, step 2: find connected mesh pieces (individual bones) inside a box and describe them.
#   python -I skan_kuski.py <root> <region_name> zmin zmax ymin ymax xmin xmax
# -> skan/kuski-<name>.npz (piece labels) and a list: id, vertices, faces, bounds, for choosing bones.
import sys, numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
R, IMYA = sys.argv[1], sys.argv[2]; zmin, zmax, ymin, ymax, xmin, xmax = map(float, sys.argv[3:9])
V = np.load(f'{R}/skan/v.npy', mmap_mode='r'); F = np.load(f'{R}/skan/f.npy', mmap_mode='r')
vin = (V[:, 2] >= zmin) & (V[:, 2] <= zmax) & (V[:, 1] >= ymin) & (V[:, 1] <= ymax) & (V[:, 0] >= xmin) & (V[:, 0] <= xmax)
fin = vin[F[:, 0]] & vin[F[:, 1]] & vin[F[:, 2]]
Fs = np.asarray(F[fin]); idx = np.unique(Fs); remap = -np.ones(len(V), np.int64); remap[idx] = np.arange(len(idx))
Fl = remap[Fs]; n = len(idx)
e = np.concatenate([Fl[:, [0, 1]], Fl[:, [1, 2]], Fl[:, [2, 0]]])
G = coo_matrix((np.ones(len(e), np.int8), (e[:, 0], e[:, 1])), shape=(n, n))
nc, lab = connected_components(G, directed=False)
cnt = np.bincount(lab); order = np.argsort(-cnt)
Vs = np.asarray(V[idx])
print('region', IMYA, 'vertices', n, 'faces', len(Fl), 'pieces', nc)
for k in order[:25]:
    m = lab == k; p = Vs[m]
    print(f'piece {k:6d}: vertices {cnt[k]:8d}  z {p[:,2].min():+.2f}..{p[:,2].max():+.2f}  y {p[:,1].min():+.2f}..{p[:,1].max():+.2f}  x {p[:,0].min():+.2f}..{p[:,0].max():+.2f}')
np.savez(f'{R}/skan/kuski-{IMYA}.npz', idx=idx, lab=lab, F=Fl)
