# Mammoth skeleton scan (Smithsonian NMNH, CC0), step 1: read all vertices and faces into numpy (fast, in chunks),
# render an 'X-ray' in three projections with a coordinate grid to locate the skull, mandible, tusks and leg bones.
#   python -I skan_razbor.py <root>   -> skan/v.npy, skan/f.npy, _skan-*.jpg
import sys, os, numpy as np
from PIL import Image, ImageDraw
R = sys.argv[1]; SRC = f'{R}/skan/mammoth-master_model.obj'
if not os.path.exists(f'{R}/skan/v.npy'):
    import warnings; warnings.filterwarnings('ignore')
    Vc, Fcs, vb, fb = [], [], [], []
    def sbros():
        global vb, fb
        if vb: Vc.append(np.fromstring(b''.join(vb), sep=' ', dtype=np.float32).reshape(-1, 3)); vb = []
        if fb: Fcs.append((np.fromstring(b''.join(fb).replace(b'//', b' '), sep=' ', dtype=np.int64).reshape(-1, 6)[:, ::2] - 1).astype(np.int32)); fb = []
    with open(SRC, 'rb') as fo:
        for line in fo:
            c = line[:2]
            if c == b'v ': vb.append(line[2:])
            elif c == b'f ': fb.append(line[2:])
            if len(vb) >= 2_000_000 or len(fb) >= 2_000_000: sbros()
    sbros()
    V = np.concatenate(Vc); Fc = np.concatenate(Fcs); del Vc, Fcs
    print('vertices', len(V), 'faces', len(Fc))
    np.save(f'{R}/skan/v.npy', V); np.save(f'{R}/skan/f.npy', Fc)
V = np.load(f'{R}/skan/v.npy'); print('vertices', len(V), 'bounds', V.min(0), V.max(0))
def proekciya(a, b, imya, n=1400):
    P = V[::7]; lo, hi = V.min(0), V.max(0)
    sx = (n - 40) / max(hi[a] - lo[a], hi[b] - lo[b])
    img = np.zeros((int((hi[b] - lo[b]) * sx) + 40, int((hi[a] - lo[a]) * sx) + 40), np.float32)
    xi = ((P[:, a] - lo[a]) * sx + 20).astype(int); yi = (img.shape[0] - 20 - (P[:, b] - lo[b]) * sx).astype(int)
    np.add.at(img, (yi, xi), 1)
    img = np.log1p(img); img = (img / img.max() * 255).astype(np.uint8)
    im = Image.fromarray(255 - img).convert('RGB'); d = ImageDraw.Draw(im)
    for k in np.arange(np.floor(lo[a]), hi[a] + 1, 0.5 if hi[a] - lo[a] < 8 else 1):
        x = (k - lo[a]) * sx + 20; d.line([(x, 0), (x, im.height)], fill=(255, 160, 160)); d.text((x + 2, 2), f'{k:g}', fill=(200, 0, 0))
    for k in np.arange(np.floor(lo[b]), hi[b] + 1, 0.5 if hi[b] - lo[b] < 8 else 1):
        y = im.height - 20 - (k - lo[b]) * sx; d.line([(0, y), (im.width, y)], fill=(160, 160, 255)); d.text((2, y + 2), f'{k:g}', fill=(0, 0, 200))
    im.save(f'{R}/_skan-{imya}.jpg', quality=88)
proekciya(0, 1, 'xy'); proekciya(0, 2, 'xz'); proekciya(2, 1, 'zy')
print('ok')
