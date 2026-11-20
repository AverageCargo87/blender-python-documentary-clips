# Clip 2: a real satellite image of the Don valley for the 'today' scene (and nature masks for the Ice Age).
# Copernicus Sentinel-2 L2A, TCI true colour at 10 m, open data on AWS (Element84 STAC catalogue). The Copernicus licence is free,
# commercial use included, with the credit: 'Contains modified Copernicus Sentinel data 2025'.
# The image is reprojected onto the same grid as the relief (z12 tiles x 2489-2495, y 1361-1367, Web Mercator).
#   python sputnik.py <root> [date=2025-08-30] [scale=4] [layer=visual|scl]   (scl = scene classes, 6 = water)
import sys, os, json, math, urllib.request
import numpy as np
from PIL import Image
os.environ.update(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', CPL_VSIL_CURL_ALLOWED_EXTENSIONS='.tif', GDAL_HTTP_MULTIRANGE='YES',
                  GDAL_HTTP_MERGE_CONSECUTIVE_RANGES='YES', VSI_CACHE='TRUE', GDAL_HTTP_MAX_RETRY='4', GDAL_HTTP_RETRY_DELAY='2')
import rasterio
from rasterio.warp import reproject, Resampling, transform_bounds
from rasterio.transform import from_bounds

ROOT = sys.argv[1]; DATA = sys.argv[2] if len(sys.argv) > 2 else '2025-08-30'; K = int(sys.argv[3]) if len(sys.argv) > 3 else 4; SLOY = sys.argv[4] if len(sys.argv) > 4 else 'visual'
Z, X0, Y0, N = 12, 2489, 1361, 7
R = 20037508.342789244
def merc_x(x): return x / 2 ** Z * 2 * R - R
def merc_y(y): return R - y / 2 ** Z * 2 * R
L, T, Rr, B = merc_x(X0), merc_y(Y0), merc_x(X0 + N), merc_y(Y0 + N)
lon0, lat0, lon1, lat1 = transform_bounds('EPSG:3857', 'EPSG:4326', L, B, Rr, T)
print('bbox', round(lon0, 3), round(lat0, 3), round(lon1, 3), round(lat1, 3))

q = json.dumps({'collections': ['sentinel-2-l2a'], 'bbox': [lon0, lat0, lon1, lat1],
                'datetime': f'{DATA}T00:00:00Z/{DATA}T23:59:59Z', 'limit': 50}).encode()
req = urllib.request.Request('https://earth-search.aws.element84.com/v1/search', data=q, headers={'Content-Type': 'application/json', 'User-Agent': 'blender-render-script'})
items = json.load(urllib.request.urlopen(req, timeout=60))['features']
items.sort(key=lambda f: f['properties'].get('eo:cloud_cover', 99))
for f in items: print(f['id'], 'cloud cover', f['properties'].get('eo:cloud_cover'))

Wd = Hd = 256 * N * K
dst_tr = from_bounds(L, B, Rr, T, Wd, Hd)
NB = 3 if SLOY == 'visual' else 1
out = np.zeros((NB, Hd, Wd), np.uint8)
for f in items:
    url = f['assets'][SLOY]['href']
    print('reading', url)
    with rasterio.open('/vsicurl/' + url) as src:
        tmp = np.zeros((NB, Hd, Wd), np.uint8)
        for b in range(NB):
            reproject(rasterio.band(src, b + 1), tmp[b], src_transform=src.transform, src_crs=src.crs,
                      dst_transform=dst_tr, dst_crs='EPSG:3857', resampling=Resampling.lanczos if SLOY == 'visual' else Resampling.nearest, src_nodata=0, dst_nodata=0)
    pust = out.sum(0) == 0
    out[:, pust] = tmp[:, pust]
    print('  filled', round(100 * (out.sum(0) > 0).mean(), 1), '%')
    if (out.sum(0) > 0).mean() > .9999: break
os.makedirs(f'{ROOT}/sputnik', exist_ok=True)
if SLOY == 'visual':
    Image.fromarray(out.transpose(1, 2, 0)).save(f'{ROOT}/sputnik/tci-{DATA}.png')
    Image.fromarray(out.transpose(1, 2, 0)).resize((1792, 1792), Image.LANCZOS).save(f'{ROOT}/_sputnik.jpg', quality=90)
else:
    Image.fromarray(out[0]).save(f'{ROOT}/sputnik/{SLOY}-{DATA}.png')
if SLOY == 'visual': json.dump({'data': DATA, 'sceny': [f['id'] for f in items], 'razmer': Wd, 'podpis': 'Contains modified Copernicus Sentinel data 2025'},
          open(f'{ROOT}/sputnik/info.json', 'w'), ensure_ascii=False)
print('done', Wd)
