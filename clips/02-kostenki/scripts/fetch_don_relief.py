# Clip 2: elevation of the Don valley around Kostenki from AWS Terrarium tiles (Mapzen Terrain Tiles, open data).
# A 7x7 block of z12 tiles (x 2489-2495, y 1361-1367, Web Mercator) -> 1792x1792 grid, ~24 m per pixel at this latitude.
# The block matches the grid that sputnik.py reprojects the Sentinel-2 image onto, so relief and imagery line up pixel for pixel.
#   python fetch_don_relief.py <root>     -> <root>/dannye/tayly/*.png, <root>/dannye/rel_ef_don.npy (float32 metres)
import os, sys, concurrent.futures as cf, urllib.request
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..'))
from lib.geo import terrarium_decode, mosaic

Z, X0, Y0, N = 12, 2489, 1361, 7
D = os.path.join(sys.argv[1], 'dannye'); T = os.path.join(D, 'tayly'); os.makedirs(T, exist_ok=True)


def get(xy):
    x, y = xy; f = f'{T}/{Z}_{x}_{y}.png'
    if not os.path.exists(f):
        for i in range(5):
            try:
                with urllib.request.urlopen(f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{Z}/{x}/{y}.png', timeout=30) as r:
                    open(f, 'wb').write(r.read()); break
            except Exception:
                if i == 4: raise
    return f


with cf.ThreadPoolExecutor(8) as ex:
    list(ex.map(get, [(x, y) for x in range(X0, X0 + N) for y in range(Y0, Y0 + N)]))
tiles = {(x - X0, y - Y0): terrarium_decode(np.asarray(Image.open(f'{T}/{Z}_{x}_{y}.png').convert('RGB')))
         for x in range(X0, X0 + N) for y in range(Y0, Y0 + N)}
E = mosaic(tiles, N, N)
np.save(os.path.join(D, 'rel_ef_don.npy'), E)
print('ok', E.shape, float(E.min()), float(E.max()))
