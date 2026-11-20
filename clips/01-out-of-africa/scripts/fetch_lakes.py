# Download Natural Earth 1:10m lakes (public domain) as GeoJSON for the globe textures (tekstury.py).
#   python fetch_lakes.py <root>          -> <root>/dannye/ne_10m_lakes.geojson (~5 MB)
import os, sys, urllib.request

URL = os.environ.get('NE_LAKES_URL', 'https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_lakes.geojson')
out = os.path.join(sys.argv[1], 'dannye', 'ne_10m_lakes.geojson')
os.makedirs(os.path.dirname(out), exist_ok=True)
if os.path.exists(out) and os.path.getsize(out) > 1_000_000:
    print('exists', out)
else:
    req = urllib.request.Request(URL, headers={'User-Agent': 'blender-python-documentary-clips'})
    with urllib.request.urlopen(req, timeout=120) as r, open(out + '.part', 'wb') as f:
        f.write(r.read())
    os.replace(out + '.part', out)
    print('ok', out, os.path.getsize(out), 'bytes')
