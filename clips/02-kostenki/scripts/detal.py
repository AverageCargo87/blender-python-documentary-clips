# Clip 2: detailed patch of the valley around Kostenki (14x14 km, 8 m grid instead of 24 m) + Ice Age trees.
# Small-scale relief that the elevation data does not have is synthesised plausibly, following slope physics:
#   rills down the slope (stretched along the flow), hummocks, snow filling gully floors, wind sastrugi on the plateau,
#   rough chalk outcrops. At the patch border everything blends smoothly into the base relief (no seams).
# Ice Age trees: spruce and pine (and bare birch) in clumps only on gully floors, from the mask made by tekstury2.py.
#   python detal.py <root> <led|leto>
# -> dannye/uchastok-<var>.npy (heights, m), dannye/uchastok.json (window), dannye/derevya-led.npz
import sys, json, numpy as np, cv2
from scipy import ndimage
R, VAR = sys.argv[1], sys.argv[2]
X0, Y0, NPX, K = 470, 460, 584, 3              # window in relief pixels (24 m) and the grid refinement factor
n = NPX * K + 1; m = 24.0 / K                  # 1753 nodes, 8 m
E = np.load(f'{R}/dannye/rel_ef_don-{VAR}.npy').astype(np.float32)
rng = np.random.default_rng(21)
# -- base: cubic (smooth) inside, linear at the border (matches the edges of the coarse grid)
gx_, gy_ = np.meshgrid(X0 + np.arange(n, dtype=np.float32) / K, Y0 + np.arange(n, dtype=np.float32) / K)
osn_c = cv2.GaussianBlur(cv2.remap(E, gx_, gy_, cv2.INTER_CUBIC, borderMode=cv2.BORDER_REFLECT), (0, 0), 1.6)   # no ripples from upsampling
osn_l = cv2.remap(E, gx_, gy_, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
ii, jj = np.meshgrid(np.arange(n), np.arange(n))
kraj = np.minimum(np.minimum(ii, jj), np.minimum(n - 1 - ii, n - 1 - jj)).astype(np.float32)
sm = lambda x: np.clip(x, 0, 1) ** 2 * (3 - 2 * np.clip(x, 0, 1))
w = sm(kraj / 24)                               # ~190 m towards the border: details fade out
osn = osn_l * (1 - w) + osn_c * w
# -- slope, flow direction, curvature
z = cv2.GaussianBlur(osn_c, (0, 0), 1.5)
gy, gx = np.gradient(z, m); uklon = np.hypot(gx, gy)
dx, dy = -gx / (uklon + 1e-6), -gy / (uklon + 1e-6)          # flow direction (downhill), in grid pixels
kriv = cv2.Laplacian(cv2.GaussianBlur(osn_c, (0, 0), 18), cv2.CV_32F) / m ** 2 * 1e3
balka = sm((kriv - .01) / .05)
def shum(sig):
    a = cv2.GaussianBlur(rng.standard_normal((n, n)).astype(np.float32), (0, 0), sig); return a / (a.std() + 1e-6)
def lic(src, vx, vy, shagov, shag=1.0):        # smear noise along a direction field (line integral convolution)
    X0g, Y0g = ii.astype(np.float32), jj.astype(np.float32)
    acc = src.copy(); cnt = 1
    for s in (1, -1):
        X, Y = X0g.copy(), Y0g.copy()
        for _ in range(shagov):
            ux = cv2.remap(vx, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            uy = cv2.remap(vy, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
            X += s * ux * shag; Y += s * uy * shag
            acc += cv2.remap(src, X, Y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT); cnt += 1
    a = acc / cnt; return a / (a.std() + 1e-6)
# rills: zero-crossings of flow-aligned noise -> parallel runnels down the slope
L = lic(shum(1.7), dx.astype(np.float32), dy.astype(np.float32), 18)
promoiny = -sm(1 - np.abs(L) / .45) ** 1.5
na_sklone = sm((uklon - .03) / .12) * (1 - .6 * balka)
h = 2.8 * promoiny * na_sklone
# hummocks and hollows at three scales
h += (.35 * shum(2) + .6 * shum(6) + .9 * shum(18)) * (.6 + .6 * na_sklone)
# chalk: rough outcrops with small ledges
mel = cv2.imread(f'{R}/sputnik/maska-mel.png', cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
px7 = 7168 / 1792                               # satellite pixels per relief pixel
mel = cv2.remap(mel, (gx_ * px7).astype(np.float32), (gy_ * px7).astype(np.float32), cv2.INTER_LINEAR)
mel = cv2.GaussianBlur(mel, (0, 0), 1.2)
skaly = np.abs(shum(1.2)) * 1.4 + .6 * np.abs(shum(3))
h += 1.8 * mel * skaly
if VAR == 'led':
    h = h * (1 - .45 * balka) + 1.3 * sm(balka * 1.3)                # snow fills gully floors: flatter and higher
    nk = 13; ker = np.zeros((nk, nk), np.float32); cv2.line(ker, (0, nk - 1), (nk - 1, 0), 1.0, 1); ker = cv2.GaussianBlur(ker, (0, 0), .8); ker /= ker.sum()
    zastrugi = cv2.filter2D(shum(1.0), -1, ker); zastrugi /= zastrugi.std() + 1e-6   # wind from the north-east
    h += .12 * zastrugi * (1 - na_sklone) * (1 - balka)   # short and weak, otherwise the floodplain looks ploughed
reka_u = cv2.imread(f'{R}/sputnik/maska-reka.png', cv2.IMREAD_GRAYSCALE).astype(np.float32) / 255
reka_u = cv2.GaussianBlur(cv2.remap(reka_u, (gx_ * px7).astype(np.float32), (gy_ * px7).astype(np.float32), cv2.INTER_LINEAR), (0, 0), 1.5)
h -= 1.6 * reka_u                                                 # channel slightly incised: the ice sits below the banks
h *= w
vys = osn + h
np.save(f'{R}/dannye/uchastok-{VAR}.npy', vys.astype(np.float32))
json.dump({'x0': X0, 'y0': Y0, 'npx': NPX, 'k': K, 'n': n}, open(f'{R}/dannye/uchastok.json', 'w'))
print('patch', VAR, n, 'detail range, m: %.2f..%.2f' % (h.min(), h.max()))

if VAR == 'led':   # -- trees: clumps on gully floors
    les = cv2.imread(f'{R}/sputnik/maska-les-led.png', cv2.IMREAD_GRAYSCALE)
    reka = cv2.imread(f'{R}/sputnik/maska-reka.png', cv2.IMREAD_GRAYSCALE)
    les = (les > 0) & ~(cv2.dilate(reka, np.ones((7, 7), np.uint8)) > 0)
    x0s, y0s = int(X0 * px7), int(Y0 * px7); ns = int(NPX * px7)
    win = les[y0s:y0s + ns, x0s:x0s + ns]
    ys, xs = np.nonzero(win)
    keep = rng.random(len(xs)) < .2
    xs, ys = xs[keep] + rng.random(keep.sum()), ys[keep] + rng.random(keep.sum())
    # relief-pixel coordinates -> height from the patch
    pxr, pyr = X0 + xs / px7, Y0 + ys / px7
    hi = ndimage.map_coordinates(vys, [(pyr - Y0) * K, (pxr - X0) * K], order=1, mode='nearest')
    vid = (rng.random(len(xs)) < .25).astype(np.int8)           # 0 = spruce/pine, 1 = bare birch, 2 = willow scrub
    rost = rng.uniform(.75, 1.25, len(xs)).astype(np.float32)
    ivy = cv2.imread(f'{R}/sputnik/maska-ivy.png', cv2.IMREAD_GRAYSCALE)[y0s:y0s + ns, x0s:x0s + ns] > 0   # willow on the floodplain
    kl = cv2.GaussianBlur(rng.standard_normal(ivy.shape).astype(np.float32), (0, 0), 6); kl /= kl.std()   # scrub grows in clumps
    yb, xb = np.nonzero(ivy & (kl > .6)); kb = rng.random(len(xb)) < .12
    xb, yb = xb[kb] + rng.random(kb.sum()), yb[kb] + rng.random(kb.sum())
    pxb, pyb = X0 + xb / px7, Y0 + yb / px7
    hb = ndimage.map_coordinates(vys, [(pyb - Y0) * K, (pxb - X0) * K], order=1, mode='nearest')
    pxr, pyr, hi = np.concatenate([pxr, pxb]), np.concatenate([pyr, pyb]), np.concatenate([hi, hb])
    vid = np.concatenate([vid, np.full(len(xb), 2, np.int8)]); rost = np.concatenate([rost, rng.uniform(.7, 1.3, len(xb)).astype(np.float32)])
    xs = pxr
    # sparse trees over the rest of the map too, so the square patch border is invisible from above
    lesv = (cv2.imread(f'{R}/sputnik/maska-les-led.png', cv2.IMREAD_GRAYSCALE) > 0)
    lesv[y0s:y0s + ns, x0s:x0s + ns] = False
    yd, xd = np.nonzero(lesv); kd = rng.random(len(xd)) < .04
    xd, yd = xd[kd] + rng.random(kd.sum()), yd[kd] + rng.random(kd.sum())
    pxd, pyd = xd / px7, yd / px7
    hd = ndimage.map_coordinates(E, [pyd, pxd], order=1, mode='nearest')
    pxr, pyr, hi = np.concatenate([pxr, pxd]), np.concatenate([pyr, pyd]), np.concatenate([hi, hd])
    vid = np.concatenate([vid, (rng.random(len(xd)) < .25).astype(np.int8)]); rost = np.concatenate([rost, rng.uniform(.8, 1.3, len(xd)).astype(np.float32)])
    xs = pxr
    np.savez(f'{R}/dannye/derevya-led.npz', px=pxr.astype(np.float32), py=pyr.astype(np.float32), h=hi.astype(np.float32), vid=vid, rost=rost)
    print('trees', len(xs), 'birches', int((vid == 1).sum()), 'willows', int((vid == 2).sum()))
