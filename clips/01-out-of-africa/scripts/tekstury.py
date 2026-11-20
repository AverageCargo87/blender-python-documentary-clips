# Globe textures in the lesson palette: colour (relief + hillshade + coastline), 16-bit heights for displacement, ocean mask.
import sys, numpy as np
from PIL import Image
from scipy import ndimage
D = sys.argv[1]
E = np.load(f'{D}/dannye/rel_ef_8192.npy').astype(np.float32)          # metres, 8192x4096
H, W = E.shape
# lakes (Natural Earth 10m): water even where the surface is above sea level (Victoria, Tanganyika, Baikal, Great Lakes)
import json
from PIL import ImageDraw
oz = Image.new('L', (W, H), 0); dz = ImageDraw.Draw(oz)
for f in json.load(open(f'{D}/dannye/ne_10m_lakes.geojson', encoding='utf-8'))['features']:
    g = f['geometry']; polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
    for poly in polys:
        for k, ring in enumerate(poly):
            pts = [((lon + 180) / 360 * W, (90 - lat) / 180 * H) for lon, lat in ring]
            if len(pts) > 2: dz.polygon(pts, fill=0 if k else 255)
ozero = np.asarray(oz) > 127
land = (E > 0) & ~ozero
# land colour: warm lesson palette (sand -> ochre -> umber -> cream peaks)
def ramp(x, stops):
    xs = np.array([s[0] for s in stops], np.float32); cs = np.array([s[1] for s in stops], np.float32) / 255
    out = np.empty(x.shape + (3,), np.float32)
    for c in range(3): out[..., c] = np.interp(x, xs, cs[:, c])
    return out
suscha = ramp(E, [(0, (206, 190, 140)), (250, (196, 176, 118)), (700, (182, 150, 96)), (1500, (160, 122, 80)), (2600, (138, 106, 74)), (4000, (148, 124, 98)), (5600, (178, 164, 144)), (7200, (232, 224, 208))])
okean = ramp(E, [(-7000, (13, 37, 46)), (-4000, (18, 50, 60)), (-1500, (26, 70, 78)), (-200, (44, 98, 100)), (0, (66, 122, 118))])
# Antarctic and Greenland ice by elevation and latitude
lat = 90 - (np.arange(H) + .5) / H * 180
polar = (np.abs(lat)[:, None] > 60) & land & (E > 800)
# hillshade: light from the north-west at 40 deg altitude; one pixel is ~4.9 km
px = 40075000 / W
z = ndimage.gaussian_filter(E, 1.2)
gy = np.gradient(z, axis=0) / px
gx = np.gradient(z, axis=1) / (px * np.cos(np.radians(np.clip(lat, -80, 80))))[:, None]
ex = 14.0                                                   # relief exaggeration for readability
sx, sy = gx * ex, gy * ex
az, alt = np.radians(315), np.radians(40)
lx, ly, lz = np.cos(alt) * np.sin(az), np.cos(alt) * np.cos(az), np.sin(alt)
nz = 1 / np.sqrt(1 + sx * sx + sy * sy)
shade = (-sx * nz) * lx + (sy * nz) * ly + nz * lz           # y grows downwards (south)
shade = np.clip(shade / lz, 0, 1.6)
mult = np.where(land, .55 + .55 * shade, .85 + .15 * shade)[..., None]
voda_oz = np.array([52, 104, 104], np.float32) / 255
okean = np.where(ozero[..., None], voda_oz, okean)
col = np.where(land[..., None], suscha, okean) * mult
col[polar] = col[polar] * .35 + np.array([.93, .91, .86]) * .65
# coastline: a thin dark rim on land and a light shelf band
kray = land & ~ndimage.binary_erosion(land, iterations=1)
col[kray] *= .62
shelf = (~land) & ndimage.binary_dilation(land, iterations=3) & (E > -400)
col[shelf] = col[shelf] * .8 + np.array([.42, .6, .58]) * .2
img = Image.fromarray((np.clip(col, 0, 1) * 255).astype(np.uint8))
img.save(f'{D}/tex/cvet_8192.png'); img.resize((2048, 1024), Image.LANCZOS).save(f'{D}/tex/cvet_2048.jpg', quality=88)
# heights for displacement: land as is, sea floor compressed 10x; 0..1 -> 16 bit
v = np.where(land, E, E * .1)
v = np.clip((v + 1000) / 9000, 0, 1)
Image.fromarray((v * 65535).astype(np.uint16)).save(f'{D}/tex/vysota_8192.png')
Image.fromarray((~land * 255).astype(np.uint8)).save(f'{D}/tex/okean_8192.png')
print('ok')
