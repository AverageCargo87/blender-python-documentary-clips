# Smooth the flame grid of a finished cache: flames on the tree are sheets one voxel thick and EEVEE renders them as 'hatching'.
# Blur the grid by ~1.4 voxels and write a new cache (noise/detail files only, flame grid only).
#   blender -b --factory-startup --python sglazhivanie.py -- <sim/derevo> <sim/derevo-gl> [gain=2.2] [passes=2]
import sys, os, json, time, shutil
import numpy as np
import openvdb as vdb
A = sys.argv[sys.argv.index('--') + 1:]
SRC, DST = A[0], A[1]; GAIN = float(A[2]) if len(A) > 2 else 2.2; PROH = int(A[3]) if len(A) > 3 else 2
os.makedirs(DST + '/noise', exist_ok=True)
K = np.array([1, 4, 6, 4, 1], np.float32) / 16
def razmyt(a):
    for _ in range(PROH):
        for os_ in range(3):
            b = np.zeros_like(a)
            for i, w in enumerate(K):
                s = i - 2
                src = [slice(None)] * 3; dst = [slice(None)] * 3
                if s < 0: src[os_] = slice(0, s); dst[os_] = slice(-s, None)
                elif s > 0: src[os_] = slice(s, None); dst[os_] = slice(0, -s)
                b[tuple(dst)] += a[tuple(src)] * w
            a = b
    return a
files = sorted(f for f in os.listdir(SRC + '/noise') if f.endswith('.vdb')); P = 3 * PROH; t0 = time.time()
for n, f in enumerate(files):
    grids, _ = vdb.readAll(f'{SRC}/noise/{f}'); g = [x for x in grids if x.name == 'flame_noise'][0]
    ng = vdb.FloatGrid(); ng.name = 'flame_noise'; ng.transform = g.transform.deepCopy(); ng.gridClass = vdb.GridClass.FOG_VOLUME
    if g.activeVoxelCount() > 0:
        (i0, j0, k0), (i1, j1, k1) = g.evalActiveVoxelBoundingBox()
        o = (i0 - P, j0 - P, k0 - P); a = np.zeros((i1 - i0 + 1 + 2 * P, j1 - j0 + 1 + 2 * P, k1 - k0 + 1 + 2 * P), np.float32)
        g.copyToArray(a, ijk=o); b = np.clip(razmyt(a) * GAIN, 0, 1.0)
        ng.copyFromArray(b, ijk=o, tolerance=.004)
        if n % 40 == 0 or n == 142:
            v0, v1 = a[a > .02], b[b > .02]
            print(f, a.shape, 'before: max %.2f p90 %.2f sum %.0f | after: max %.2f p90 %.2f sum %.0f' % (a.max(), np.percentile(v0, 90) if len(v0) else 0, a.sum(), b.max(), np.percentile(v1, 90) if len(v1) else 0, b.sum())); sys.stdout.flush()
    vdb.write(f'{DST}/noise/{f}', grids=[ng])
d = json.load(open(SRC + '/gotovo.txt')); d['sglazheno'] = dict(gain=GAIN, prohodov=PROH); json.dump(d, open(DST + '/gotovo.txt', 'w'))
print('done', len(files), 'frames in', round(time.time() - t0), 's')
