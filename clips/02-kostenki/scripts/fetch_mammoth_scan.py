# Clip 2: the woolly mammoth skeleton scan, Smithsonian National Museum of Natural History (Paleobiology catalogue no. 3447777), CC0.
# The full-resolution OBJ package is ~646 MB zipped and ~2.9 GB unpacked. Smithsonian 3D download links are per-asset, so the
# URL is not hard-coded: open the model page on 3d.si.edu (search "woolly mammoth"), choose Download -> full resolution OBJ,
# and pass the link (or the already downloaded zip).
#   python fetch_mammoth_scan.py <root> <zip URL or local .zip>   -> <root>/skan/mammoth-master_model.obj
#   (or set SI_MAMMOTH_URL)
import os, shutil, sys, urllib.request, zipfile

root = sys.argv[1]; src = sys.argv[2] if len(sys.argv) > 2 else os.environ.get('SI_MAMMOTH_URL', '')
dst = os.path.join(root, 'skan'); os.makedirs(dst, exist_ok=True)
obj = os.path.join(dst, 'mammoth-master_model.obj')
if os.path.exists(obj):
    sys.exit(print('exists', obj))
if not src:
    sys.exit('pass the Smithsonian zip URL or a local zip path (see the header of this script)')
zp = src if os.path.exists(src) else os.path.join(dst, 'woolly-mammoth-full_resolution-obj_std.zip')
if not os.path.exists(zp):
    req = urllib.request.Request(src, headers={'User-Agent': 'blender-python-documentary-clips'})
    with urllib.request.urlopen(req, timeout=600) as r, open(zp + '.part', 'wb') as f:
        shutil.copyfileobj(r, f, 1 << 22)
    os.replace(zp + '.part', zp)
with zipfile.ZipFile(zp) as z:
    name = next(n for n in z.namelist() if n.lower().endswith('.obj'))
    with z.open(name) as s, open(obj, 'wb') as d:
        shutil.copyfileobj(s, d, 1 << 22)
print('ok', obj, os.path.getsize(obj), 'bytes')
