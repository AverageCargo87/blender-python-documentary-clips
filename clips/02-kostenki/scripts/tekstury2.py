# Clip 2: detailed colour maps of the Don valley (7168^2, ~6 m per pixel) from a Sentinel-2 image and the relief.
#  leto: 'today', the image itself (2025-08-30), brightened and slightly sharpened.
#  led:  the Ice Age, ~25-20 thousand years ago: take ONLY nature from the image (the Don channel, chalk, woods in gullies and by the river);
#        fields, villages, roads, the reservoir and ponds are anachronisms and are removed. Thin wind-blown snow with
#        dry grass and wormwood showing through; drifts in gullies and behind edges; conifer clumps and birch only on gully floors and by the river.
#  bump-*: fine relief for shading.
#   python tekstury2.py <root> [--malo]   (--malo: 1792^2 test size)
import sys, numpy as np, cv2
from PIL import Image
from scipy import ndimage
Image.MAX_IMAGE_PIXELS = None
R = sys.argv[1]; MALO = '--malo' in sys.argv
S = cv2.cvtColor(cv2.imread(f'{R}/sputnik/tci-2025-08-30.png', cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
if MALO: S = cv2.resize(S, (1792, 1792), interpolation=cv2.INTER_AREA)
N = S.shape[0]; px = 43008.0 / N                      # metres per ground pixel (24 m for the 1792^2 relief)
k = N / 1792                                          # how many times finer the image is than the relief
E0 = np.load(f'{R}/dannye/rel_ef_don.npy').astype(np.float32); E0 = np.clip(E0, 75, 240)
# clean relief: remove narrow straight ridges (road embankments, shelter belts, since SRTM measures tree tops) and noise ripple
kr = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)) > 0          # ~70 m: anything narrower is an embankment, a shelter belt or a cutting
E = ndimage.grey_closing(ndimage.grey_opening(E0, footprint=kr), footprint=kr)
E = cv2.GaussianBlur(ndimage.median_filter(E, size=5), (0, 0), 1.0)
up = lambda a: cv2.resize(a, (N, N), interpolation=cv2.INTER_CUBIC) if a.shape[0] != N else a
Eu = up(E)
rng = np.random.default_rng(11)
def shum(sig, n=N):
    z = cv2.GaussianBlur(rng.standard_normal((n, n)).astype(np.float32), (0, 0), sig); return z / (z.std() + 1e-6)
def shum_m(sig_m):                     # noise with blob size in metres; large scales are computed coarse and upsampled
    s = sig_m / px
    if s < 6: return shum(s)
    n0 = max(64, int(N / (s / 3))); z = shum(3.0, n0); z = cv2.resize(z, (N, N), interpolation=cv2.INTER_CUBIC); return z / (z.std() + 1e-6)
def poloski(sig_dl, sig_pop, ugol, n=1792):   # wind streaks: noise stretched along the wind (on the relief grid, then upsampled)
    z = np.random.default_rng(3).standard_normal((n, n)).astype(np.float32)
    kk = int(sig_dl * 3) * 2 + 1; ker = cv2.getGaussianKernel(kk, sig_dl) @ cv2.getGaussianKernel(kk, sig_pop).T
    M = cv2.getRotationMatrix2D((kk / 2, kk / 2), ugol, 1); ker = cv2.warpAffine(ker, M, (kk, kk)); ker /= ker.sum()
    z = cv2.filter2D(z, -1, ker); z = up(z); return z / (z.std() + 1e-6)
def mix(a, c, t): return a * (1 - t[..., None]) + np.asarray(c, np.float32)[None, None] / 255 * t[..., None]
sm = lambda x: np.clip(x, 0, 1) ** 2 * (3 - 2 * np.clip(x, 0, 1))

# -- relief (slope and curvature on the relief grid in metres, then upsampled to the image)
gy, gx = np.gradient(cv2.GaussianBlur(E, (0, 0), .7), 24.0); uklon = up(np.hypot(gx, gy))        # m/m
krivizna = up(cv2.Laplacian(cv2.GaussianBlur(E, (0, 0), 6), cv2.CV_32F) / 24.0 ** 2 * 1e3)       # >0 concave (gully), <0 convex (edge)
vys = np.clip((Eu - 85) / 110, 0, 1)

# -- classes from the image
f = S.astype(np.float32) / 255; r, g, b = f[..., 0], f[..., 1], f[..., 2]
v = f.mean(-1); sat = f.max(-1) - f.min(-1)
scl = cv2.imread(f'{R}/sputnik/scl-2025-08-30.png', cv2.IMREAD_GRAYSCALE)      # Sentinel-2 scene classification: 6 = water
if scl.shape[0] != N: scl = cv2.resize(scl, (N, N), interpolation=cv2.INTER_NEAREST)
voda = cv2.GaussianBlur((scl == 6).astype(np.float32), (0, 0), N / 7168 * 4) > .5   # smooth out the steps of 20 m pixels
# wide water (reservoir, cooling pond, quarries) is an anachronism for the Ice Age; the river stays
dv = ndimage.distance_transform_edt(voda)
shir = max(6, N / 240)                                                  # half-width ~180 m: the river is narrower, lakes are wider
ozera = ndimage.binary_dilation(dv > shir, iterations=int(shir) + 2) & voda
reka = voda & ~ozera
reka = ndimage.binary_closing(reka, iterations=2)
lab_, nlab = ndimage.label(reka)                                     # only the Don itself: the largest connected water body (quarries and ponds are dropped)
if nlab > 1: reka = lab_ == (np.bincount(lab_.ravel())[1:].argmax() + 1)
les = (v < .2) & (g > r * 1.08) & (g > b * 1.15)
les = ndimage.binary_opening(les, iterations=1)
nizina = Eu < 102                                                       # floodplain and low terraces
balka = sm((krivizna - .01) / .05)                                      # gully floors and thalwegs
kupy = shum_m(54)
les_led = les & (balka > .45) & (kupy > -.1)                            # conifer clumps only on gully floors
les_led = ndimage.binary_opening(les_led, iterations=1)
ivy = les & nizina & ~les_led & (kupy > .5)                             # willow and alder on the floodplain, in sparse thickets
print('shares: river %.3f forest %.3f ice-age forest %.3f' % (reka.mean(), les.mean(), les_led.mean()))
# relief for the scenes: cleaned, the same for both periods
np.save(f'{R}/dannye/rel_ef_don-leto.npy', E.astype(np.float32))
np.save(f'{R}/dannye/rel_ef_don-led.npy', E.astype(np.float32))   # no 'canopy' subtraction: the green mask also catches fields -> steps along their borders

# -- SUMMER: the image with a gentle correction (L2A TCI is dark and greenish)
lab = cv2.cvtColor(S, cv2.COLOR_RGB2LAB).astype(np.float32)
L = lab[..., 0] / 255
lo, hi = np.percentile(L, (1, 99.5)); L = np.clip((L - lo) / (hi - lo), 0, 1) ** .78
lab[..., 0] = L * 255; lab[..., 1] = (lab[..., 1] - 128) * .92 + 128; lab[..., 2] = (lab[..., 2] - 128) * 1.05 + 128
leto = cv2.cvtColor(np.clip(lab, 0, 255).astype(np.uint8), cv2.COLOR_LAB2RGB).astype(np.float32) / 255
bl = cv2.GaussianBlur(leto, (0, 0), 1.6); leto = np.clip(leto + (leto - bl) * .55, 0, 1)   # slightly sharper
vl = leto.mean(-1); satl = leto.max(-1) - leto.min(-1)
mel = (vl > .62) & (satl < .16) & (uklon > .04) & ~voda                # white chalk outcrops on slopes
mel = ndimage.binary_opening(mel, iterations=1)
print('chalk %.4f' % mel.mean())
if not MALO:   # masks for the detailed relief and trees (detal.py)
    for imya, m in (('les-led', les_led), ('mel', mel), ('reka', reka), ('ivy', ivy)):
        cv2.imwrite(f'{R}/sputnik/maska-{imya}.png', m.astype(np.uint8) * 255)

# -- ICE AGE: snow, grass through snow, drifts, chalk, conifer clumps, river ice
n1 = shum(1.2)                                                           # finest grain (~7 m on the full image)
nm, n2, n3 = shum_m(29), shum_m(120), shum_m(720)                        # tussocks/crowns, patches, large swirls
veter = poloski(14, 1.6, -35)                                            # north-east wind: drifting-snow streaks
otkryto = sm(.45 + .9 * np.clip(-krivizna / .05, 0, 1) + .25 * n3 + .35 * veter * .5 - 1.2 * balka)   # where the snow is blown off
otkryto *= (1 - .5 * nizina)
trava = sm((otkryto - .6 + .22 * n2 + .26 * nm + .12 * n1) / .4)        # dry grass shows through the thin snow in places
led = np.empty((N, N, 3), np.float32); led[:] = np.array((233, 237, 241), np.float32) / 255
led = mix(led, (218, 220, 218), sm(.5 + .4 * n3) * .45)                  # snow with loess dust, greyish in places
led = mix(led, (246, 248, 252), sm(balka * 1.4) * .8)                    # drifts in gullies: clean white
led = mix(led, (192, 184, 160), trava * .33)                             # dry grasses
led = mix(led, (150, 136, 108), trava * sm(.5 + .5 * n1) * .3)           # wormwood, dark shrubs
led = mix(led, (196, 182, 146), sm((n1 - 1.4) / .5) * .35)               # single stems across the snow
led = mix(led, (225, 230, 236), sm((veter - .6) / .8) * .45)             # sastrugi
m_mel = cv2.GaussianBlur(mel.astype(np.float32), (0, 0), 1.2)
led = mix(led, (205, 200, 190), m_mel * .8)                              # chalk scree
led = mix(led, (175, 170, 160), m_mel * sm(.5 + .6 * n1) * .35)
m_les = cv2.GaussianBlur(les_led.astype(np.float32), (0, 0), 1.0)
krona = sm((n1 + .4) / 1.2)                                              # individual crowns and gaps
led = mix(led, (44, 56, 50), m_les * krona * .9)                         # spruce, pine
led = mix(led, (120, 112, 104), m_les * (1 - krona) * .5)                # birch, alder: bare grey-brown
led = mix(led, (238, 240, 244), m_les * sm((n1 - 1.2) / .6) * .7)        # snow on the crowns
m_ivy = cv2.GaussianBlur(ivy.astype(np.float32), (0, 0), 1.0)
led = mix(led, (132, 118, 102), m_ivy * sm((n1 + .2) / .8) * .55)        # willow and alder scrub on the floodplain: bare brown twigs
m_reka = cv2.GaussianBlur(reka.astype(np.float32), (0, 0), 1.0)
led = mix(led, (162, 182, 196), m_reka * .95)                            # ice: grey-blue, darker than snow
led = mix(led, (120, 140, 156), m_reka * sm((n2 - .3) / .8) * .45)       # open leads and dark clear ice
led = mix(led, (226, 232, 238), m_reka * sm((veter - .2) / .8) * .55)    # snow on the ice in streaks
led = np.clip(led * (1 + .025 * n1[..., None]), 0, 1)

# -- fine relief for shading (0.5 = flat)
def norm(x): return np.clip(.5 + x, 0, 1)
hp = lambda x, s: x - cv2.GaussianBlur(x, (0, 0), s)
bump_leto = norm(hp(cv2.cvtColor((leto * 255).astype(np.uint8), cv2.COLOR_RGB2GRAY).astype(np.float32) / 255, 3) * 1.6)
bump_led = norm(.10 * n1 + .025 * veter + .18 * m_les * krona + .12 * m_mel * n1 + .05 * trava * n1)

suf = '-malo' if MALO else ''
for imya, c in (('leto', leto), ('led', led)):
    Image.fromarray((np.clip(c, 0, 1) * 255 + .5).astype(np.uint8)).save(f'{R}/tex/dolina2-{imya}{suf}.png')
for imya, c in (('leto', bump_leto), ('led', bump_led)):
    Image.fromarray((c * 255 + .5).astype(np.uint8)).save(f'{R}/tex/dolina2-bump-{imya}{suf}.png')
# contact sheet for eyeballing: around Kostenki (824, 794 in relief pixels)
k = N / 1792; cx, cy, h = int(824 * k), int(794 * k), int(330 * k)
crop = lambda a: Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).crop((cx - h, cy - h, cx + h, cy + h)).resize((900, 900))
s = Image.new('RGB', (1800, 900)); s.paste(crop(leto), (0, 0)); s.paste(crop(led), (900, 0)); s.save(f'{R}/_tekstury2{suf}.jpg', quality=88)
print('ok', N)
