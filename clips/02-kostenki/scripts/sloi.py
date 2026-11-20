# Clip 2: split a picture into layers for a 'volumetric picture' without torn edges (like a '3D photo').
# The near layer is an object with a soft per-pixel mask (BiRefNet) or the foreground by a depth threshold.
# Each layer is inpainted only from ITS OWN pixels (behind the dwelling: ground, behind the slope: the valley),
# depth under removed parts is smooth (push-pull) and always behind the layer in front. Nothing for the mesh to tear.
#   python sloi.py <root> <C|D1|D2> [--list]
# -> <root>/sloi/<scene>-L<i>.png (RGBA, 0 = farthest) and <scene>-L<i>-glub.png (16 bit, like the source depth).
import sys, json, numpy as np, cv2
from PIL import Image
from scipy import ndimage

ROOT, SC = sys.argv[1], sys.argv[2]; LIST = '--list' in sys.argv
CFG = {   # picture, depth, near layers from the nearest: ('maska', file) or ('porog', depth threshold)
    'C': dict(img='stoyanka', glub='stoyanka-glub', sloi=[('maska', 'stoyanka-maska'), ('porog', .38)]),
    'D1': dict(img='nahodki', glub='nahodki-glub', sloi=[('maska', 'nahodki-maska')]),
    'D2': dict(img='venera-v2', glub='venera-v-glub', sloi=[('maska', 'venera-maska')]),
}[SC]
I = np.asarray(Image.open(f"{ROOT}/kartinki/{CFG['img']}.png").convert('RGB'))
H, W = I.shape[:2]
D = np.asarray(Image.open(f"{ROOT}/kartinki/{CFG['glub']}.png")).astype(np.float32) / 65535   # 1 = near, 0 = far
GH, GW = D.shape
k = W / GW
vniz = lambda m: cv2.resize(m.astype(np.float32), (GW, GH), interpolation=cv2.INTER_AREA)
vverh = lambda m: cv2.resize(m.astype(np.float32), (W, H), interpolation=cv2.INTER_LINEAR)
def krug(r): return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2 * r + 1, 2 * r + 1))

def pushpull(d, w):                  # smooth fill: keep known values (w>0), fill holes from coarse pyramid levels
    if w.min() > 0 or min(d.shape) < 3:
        return np.where(w > 0, d, (d * w).sum() / max(w.sum(), 1e-6)).astype(np.float32)
    h, ww = d.shape; sz = (max(1, ww // 2), max(1, h // 2))
    num = cv2.resize(d * w, sz, interpolation=cv2.INTER_AREA); den = cv2.resize(w, sz, interpolation=cv2.INTER_AREA)
    m = np.where(den > 1e-6, num / np.maximum(den, 1e-6), 0).astype(np.float32)
    grubo = pushpull(m, (den > 1e-6).astype(np.float32))
    up = cv2.resize(grubo, (ww, h), interpolation=cv2.INTER_LINEAR)
    return (d * w + up * (1 - w)).astype(np.float32)
def zalit_glub(d, dyra):
    z = pushpull(d.astype(np.float32), (~dyra).astype(np.float32))
    s = cv2.GaussianBlur(z, (0, 0), 3)
    return np.where(dyra, s, z)
def zalit_cvet(img, svoi):           # everything that is not the layer's own pixels is inpainted from its own pixels
    return cv2.inpaint(img, (~svoi).astype(np.uint8) * 255, 6, cv2.INPAINT_TELEA)
def prodlit(d, yadro):               # core depth extended outwards by nearest point: the layer edge is not pulled towards the background
    _, (iy, ix) = ndimage.distance_transform_edt(~yadro, return_indices=True)
    return np.where(yadro, d, cv2.GaussianBlur(d[iy, ix], (0, 0), 1.5))
def ochistit_kraj(img, a):           # colour of the semi-transparent edge comes from inside the object, without the old background bleeding in
    polosa = (a < .97) & (cv2.dilate((a > .02).astype(np.uint8), krug(4)) > 0)
    return cv2.inpaint(img, polosa.astype(np.uint8) * 255, 4, cv2.INPAINT_TELEA)

sloi = []                            # (rgba, depth) from near to far
d = D.copy()
ubrano = np.zeros((H, W), bool)      # what has already gone into nearer layers (with margin)
pered = None                         # depth of the nearest layer in front of the current one (for ordering)
for vid, arg in CFG['sloi']:
    if vid == 'maska':
        a = np.asarray(Image.open(f'{ROOT}/sloi/{arg}.png').convert('L')).astype(np.float32) / 255
        if a.shape != (H, W): a = cv2.resize(a, (W, H), interpolation=cv2.INTER_LINEAR)
        a = cv2.GaussianBlur(a, (0, 0), .7)
        cvet = ochistit_kraj(I, a)
    else:                            # foreground by depth threshold, edge from the picture contour
        m = np.clip((d - arg) / .05 + .5, 0, 1)
        a = cv2.ximgproc.guidedFilter(cv2.cvtColor(I, cv2.COLOR_RGB2GRAY), vverh(m), 10, 1e-3)
        a = np.clip((a - .5) * 1.6 + .5, 0, 1); a = cv2.GaussianBlur(a, (0, 0), .7)
        cvet = zalit_cvet(I, (a > .02) & ~ubrano)   # at a soft seam keep the source pixels, not a smeared inpaint
    yadro = cv2.erode((vniz(a) > .5).astype(np.uint8), krug(3)) > 0
    gl = prodlit(d, yadro)
    if pered is not None: gl = np.minimum(gl, pered - .015)     # a layer never pokes in front of the nearer one
    sloi.append((np.dstack([cvet, (a * 255 + .5).astype(np.uint8)]), gl))
    if vid == 'maska': ubrano |= cv2.dilate((a > .04).astype(np.uint8), krug(max(4, int(4 * k)))) > 0   # object with a margin, no halo
    else: ubrano |= cv2.erode((a > .98).astype(np.uint8), krug(2)) > 0   # foreground: only the core; in the soft seam the far layer keeps the source
    dyra = cv2.dilate((vniz(ubrano) > .3).astype(np.uint8), krug(2)) > 0
    d = zalit_glub(d, dyra)
    d = np.where(dyra, np.minimum(d, gl - .02), d)              # behind an object: farther than the object
    if vid == 'porog': d = np.where(dyra, np.minimum(d, arg - .03), d)
    pered = np.where(dyra, np.minimum(gl, pered) if pered is not None else gl, pered if pered is not None else 9)
d = cv2.GaussianBlur(d, (0, 0), 8)   # far layer is smooth: at a sharp edge (velvet/floor) the mesh does not go jagged
if pered is not None: d = np.minimum(d, pered - .02)
sloi.append((np.dstack([zalit_cvet(I, ~ubrano), np.full((H, W), 255, np.uint8)]), d))
sloi = sloi[::-1]                    # 0 = farthest
for i, (rgba, g) in enumerate(sloi):
    Image.fromarray(rgba, 'RGBA').save(f'{ROOT}/sloi/{SC}-L{i}.png')
    Image.fromarray((np.clip(g, 0, 1) * 65535 + .5).astype(np.uint16)).save(f'{ROOT}/sloi/{SC}-L{i}-glub.png')
json.dump({'sloi': len(sloi), 'img': CFG['img']}, open(f'{ROOT}/sloi/{SC}.json', 'w'))
if LIST:   # contact sheet: each layer on a checkerboard + its depth
    rows = []
    for i, (rgba, g) in enumerate(sloi):
        h = 300; w = int(W * h / H)
        ch = ((np.indices((H, W)).sum(0) // 24) % 2 * 60 + 90).astype(np.uint8)[..., None].repeat(3, 2)
        al = rgba[..., 3:4] / 255.; v = (rgba[..., :3] * al + ch * (1 - al)).astype(np.uint8)
        gc = cv2.applyColorMap((np.clip(g, 0, 1) * 255).astype(np.uint8), cv2.COLORMAP_TURBO)[..., ::-1]
        r = Image.new('RGB', (2 * w, h)); r.paste(Image.fromarray(v).resize((w, h)), (0, 0)); r.paste(Image.fromarray(gc).resize((w, h)), (w, 0)); rows.append(r)
    s = Image.new('RGB', (rows[0].width, 300 * len(rows)))
    for i, r in enumerate(rows): s.paste(r, (0, 300 * i))
    s.save(f'{ROOT}/_sloi-{SC}.jpg', quality=88)
print('layers', len(sloi), SC)
