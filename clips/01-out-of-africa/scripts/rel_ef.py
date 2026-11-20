# Earth elevation for the globe: AWS Terrarium tiles (open data) at z5 -> equirectangular 8192x4096 grid in metres (float32 .npy)
#   python rel_ef.py <root>/dannye        (TERRARIUM_ZOOM=3 for a fast preview download)
# Data: Mapzen Terrain Tiles on the AWS Registry of Open Data (Terrarium encoding), see docs/ATTRIBUTION in the README.
import os, sys, math, io, concurrent.futures as cf, urllib.request
import numpy as np
from PIL import Image
D = sys.argv[1]; Z = int(os.environ.get('TERRARIUM_ZOOM', 5)); N = 2 ** Z   # z5 = 1024 tiles; a lower zoom is a quick preview at the same output size
os.makedirs(f'{D}/tiles', exist_ok=True)
def get(xy):
    x, y = xy; f = f'{D}/tiles/{Z}_{x}_{y}.png'
    if not os.path.exists(f):
        for i in range(5):
            try:
                with urllib.request.urlopen(f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{Z}/{x}/{y}.png', timeout=30) as r: open(f, 'wb').write(r.read()); break
            except Exception as e:
                if i == 4: raise
    return f
with cf.ThreadPoolExecutor(16) as ex: list(ex.map(get, [(x, y) for x in range(N) for y in range(N)]))
merc = np.zeros((N * 256, N * 256), np.float32)
for x in range(N):
    for y in range(N):
        a = np.asarray(Image.open(f'{D}/tiles/{Z}_{x}_{y}.png').convert('RGB')).astype(np.float32)
        merc[y * 256:(y + 1) * 256, x * 256:(x + 1) * 256] = a[..., 0] * 256 + a[..., 1] + a[..., 2] / 256 - 32768
W, H = 8192, 4096
lat = 90 - (np.arange(H) + .5) / H * 180
latc = np.clip(lat, -85.05, 85.05)
yy = (1 - np.log(np.tan(np.pi / 4 + np.radians(latc) / 2)) / np.pi) / 2 * merc.shape[0]
xx = (np.arange(W) + .5) / W * merc.shape[1]
yi = np.clip(yy.astype(int), 0, merc.shape[0] - 1); xi = np.clip(xx.astype(int), 0, merc.shape[1] - 1)
eq = merc[yi[:, None], xi[None, :]]
# poles outside the Web Mercator range: Antarctica is ice, the Arctic is ocean
eq[lat < -85.05, :] = 2600.0
eq[lat > 85.05, :] = -3000.0
np.save(f'{D}/rel_ef_8192.npy', eq.astype(np.float32))
print('ok', eq.min(), eq.max())
