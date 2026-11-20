# Clip 2: procedural mammoth bones for the 3D dwelling, 'sculpted' with signed distance fields (SDF) + marching cubes -> OBJ.
# Skull (high dome, tusk sockets, nasal opening, orbits, occiput), mandible (U-shape, ascending rami),
# femur, scapula. Surface with pores and small cracks. Several variants of each so there are no clones.
# Axes: +Y forward (snout), +Z up, metres.   python kosti.py <root> [--malo]
import sys, os, numpy as np
from skimage import measure
R = sys.argv[1]; MALO = '--malo' in sys.argv
os.makedirs(f'{R}/modeli', exist_ok=True)
VOX = .012 if MALO else .0055

def setka(lo, hi):
    xs = [np.arange(lo[i], hi[i] + VOX, VOX, dtype=np.float32) for i in range(3)]
    X, Y, Z = np.meshgrid(*xs, indexing='ij'); return X, Y, Z, xs
def ell(X, Y, Z, c, r):                 # approximate distance to an ellipsoid
    k0 = np.sqrt(((X - c[0]) / r[0]) ** 2 + ((Y - c[1]) / r[1]) ** 2 + ((Z - c[2]) / r[2]) ** 2)
    return (k0 - 1) * min(r)
def kaps(X, Y, Z, a, b, ra, rb):        # capsule tapering from ra to rb
    a, b = np.array(a, np.float32), np.array(b, np.float32); ba = b - a; L2 = float(ba @ ba)
    px, py, pz = X - a[0], Y - a[1], Z - a[2]
    h = np.clip((px * ba[0] + py * ba[1] + pz * ba[2]) / L2, 0, 1)
    dx, dy, dz = px - ba[0] * h, py - ba[1] * h, pz - ba[2] * h
    return np.sqrt(dx * dx + dy * dy + dz * dz) - (ra + (rb - ra) * h)
def smu(a, b, k):                        # smooth union
    h = np.clip(.5 + .5 * (b - a) / k, 0, 1); return b * (1 - h) + a * h - k * h * (1 - h)
def sms(a, b, k):                        # smooth subtraction of b from a
    h = np.clip(.5 - .5 * (a + b) / k, 0, 1); return a * (1 - h) + (-b) * h + k * h * (1 - h)
def shum3(shape, sig, seed):
    from scipy import ndimage
    g = np.random.default_rng(seed).standard_normal(shape).astype(np.float32)
    g = ndimage.gaussian_filter(g, sig); return g / (g.std() + 1e-6)
def poverhnost(D, xs, imya, seed, tresh=0):
    # almost smooth surface: a gentle wave + rare cracks; pores are in the material
    n2 = shum3(D.shape, 5.0 * .0055 / VOX, seed + 1)
    D = D + .0025 * n2
    if tresh:
        tr = np.abs(shum3(D.shape, 3.0 * .0055 / VOX, seed + 2)); D = D + .005 * np.clip(.08 - tr, 0, None) / .08
    v, f, nrm, _ = measure.marching_cubes(D, 0.0, spacing=(VOX, VOX, VOX))
    v += np.array([xs[0][0], xs[1][0], xs[2][0]], np.float32)
    with open(f'{R}/modeli/{imya}.obj', 'w') as fo:
        fo.write(f'o {imya}\n')
        fo.write(''.join(f'v {a:.4f} {b:.4f} {c:.4f}\n' for a, b, c in v))
        fo.write(''.join(f'f {a+1} {b+1} {c+1}\n' for a, b, c in f))   # Blender recomputes the normals
    print(imya, len(v), 'vertices')

def cherep(var):
    # mammoth skull profile: high dome at the back and top, forehead sloping to the nasal opening,
    # massive tusk sockets low at the front, running down and forward; widest at the cheekbones
    rg = np.random.default_rng(100 + var); j = lambda s=1: 1 + rg.uniform(-.05, .05) * s
    X, Y, Z, xs = setka((-.5, -.56, -.3), (.5, .62, 1.05))
    d = ell(X, Y, Z, (0, -.08, .6), (.27 * j(), .35 * j(), .38 * j()))                  # dome
    d = smu(d, ell(X, Y, Z, (0, -.22, .42), (.33, .24, .3)), .08)                        # occipital part
    d = smu(d, ell(X, Y, Z, (0, .1, .42), (.37 * j(), .2, .32)), .08)                    # facial plate: the widest part
    d = smu(d, ell(X, Y, Z, (0, .27, .2), (.26 * j(), .17, .34 * j())), .09)                             # premaxillary 'column': single and wide
    for s_ in (-1, 1):
        d = smu(d, kaps(X, Y, Z, (s_ * .12, .29, .12), (s_ * .2 * j(), .37 * j(), -.14 * j()), .13, .12), .07)   # tusk sockets: short, at the bottom
        d = smu(d, kaps(X, Y, Z, (s_ * .33, .12, .38), (s_ * .31, -.16, .27), .036, .03), .03)               # zygomatic arches
        d = smu(d, ell(X, Y, Z, (s_ * .12, -.02, .12), (.075, .16, .085)), .06)                               # molars
        d = smu(d, ell(X, Y, Z, (s_ * .08, -.42, .2), (.06, .05, .06)), .03)                                  # occipital condyles
    d = sms(d, kaps(X, Y, Z, (0, .45, .3), (0, .5, -.22), .035, .03), .03)                                    # groove between the sockets
    d = sms(d, ell(X, Y, Z, (0, .3, .64), (.16, .14, .1)), .035)                                               # nasal opening
    for s_ in (-1, 1):
        d = sms(d, ell(X, Y, Z, (s_ * .34, .15, .49), (.085, .08, .075)), .025)                               # orbits
        d = sms(d, kaps(X, Y, Z, (s_ * .2, .39, -.16), (s_ * .15, .33, .06), .08, .075), .02)                 # empty sockets
    d = sms(d, ell(X, Y, Z, (0, -.47, .24), (.065, .06, .06)), .02)                                            # foramen magnum
    if var == 2: d = sms(d, ell(X, Y, Z, (.26, -.1, .92), (.2, .2, .16)), .05)                               # broken edge of the dome
    poverhnost(d, xs, f'cherep{var}', 10 + var, tresh=1)

def chelyust(var):
    # massive U-shaped mandible: thick body, fused chin with a 'spout', wide ascending rami
    rg = np.random.default_rng(200 + var); j = lambda: 1 + rg.uniform(-.05, .05)
    X, Y, Z, xs = setka((-.36, -.4, -.16), (.36, .4, .5))
    d = np.full(X.shape, 9, np.float32)
    for s_ in (-1, 1):
        d = smu(d, ell(X, Y, Z, (s_ * .16, .02, .08), (.11 * j(), .23, .13)), .06)                     # mandible body: thick
        d = smu(d, ell(X, Y, Z, (s_ * .19, -.19, .24), (.065, .16 * j(), .2 * j())), .08)               # ascending ramus: a plate
        zub = ell(X, Y, Z, (s_ * .16, .03, .17), (.055, .17, .04))                                      # molar: lamellae
        zub = zub + .006 * np.sin(Y * 90)
        d = smu(d, zub, .02)
    d = smu(d, ell(X, Y, Z, (0, .19, .05), (.17, .11, .1)), .07)                                        # chin
    d = smu(d, kaps(X, Y, Z, (0, .25, .02), (0, .34, -.08), .055, .04), .05)                            # 'spout'
    d = sms(d, ell(X, Y, Z, (0, -.08, .16), (.11, .22, .14)), .04)                                      # between the rami
    poverhnost(d, xs, f'chelyust{var}', 20 + var, tresh=1)

def bedro(var):
    X, Y, Z, xs = setka((-.16, -.16, -.03), (.16, .16, 1.17))
    d = kaps(X, Y, Z, (0, 0, .15), (0, .01, .97), .07, .065)
    d = smu(d, ell(X, Y, Z, (.04, 0, 1.04), (.11, .09, .09)), .05)          # head
    d = smu(d, ell(X, Y, Z, (-.08, 0, 1.0), (.06, .06, .08)), .04)          # trochanter
    d = smu(d, ell(X, Y, Z, (.06, 0, .07), (.07, .09, .08)), .04)           # condyles
    d = smu(d, ell(X, Y, Z, (-.06, 0, .07), (.07, .09, .08)), .04)
    poverhnost(d, xs, f'bedro{var}', 30 + var)

def lopatka(var):
    X, Y, Z, xs = setka((-.36, -.1, -.03), (.36, .1, .8))
    tri = np.maximum(np.maximum(-Z, Z - .75 + np.abs(X) * 0) , np.abs(X) - (.06 + .38 * Z / .75))   # wedge
    d = np.maximum(tri, np.abs(Y) - .018)
    d = smu(d, kaps(X, Y, Z, (0, .02, .06), (.02, .06, .66), .02, .012), .02)   # scapular spine
    d = smu(d, ell(X, Y, Z, (0, 0, .02), (.09, .07, .06)), .03)               # glenoid cavity
    poverhnost(d, xs, f'lopatka{var}', 40 + var)

for v in range(3): cherep(v)
for v in range(3): chelyust(v)
for v in range(2): bedro(v)
for v in range(2): lopatka(v)
print('ok')
