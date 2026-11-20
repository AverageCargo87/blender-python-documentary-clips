# Clip 2: a 'volumetric picture' made of LAYERS (prepared by sloi.py): each layer is a continuous surface at its own depth,
# opacity comes from the picture's soft mask, so object edges stay clean, without the jagged 'saw' of cut mesh cells.
# The camera mostly pushes in and turns slightly, which reveals less of the space behind objects.
#   blender -b --factory-startup --python proekciya2.py -- <root> <C|D1|D2> <vse|1,2,3|metki> [--proba]
# Label points (fractions of the picture) -> <root>/metki-<scene>.json.
import bpy, math, json, sys, os
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

A = sys.argv[sys.argv.index('--') + 1:]
ROOT, SC, REZHIM = A[0], A[1], A[2]; PROBA = '--proba' in A; TEST = '--test' in A   # --test: full size, but into the proba folder
FPS = 30
# camera motion: [(sec, x, y, z, yaw deg, pitch deg, lens zoom)]
# The camera barely moves: rotating in place and zooming the lens do not distort the picture at all (they are an exact
# image transform); the forward dolly is tiny, just enough for a hint of depth between layers.
CFG = {
    'C': dict(near=3.2, far=60, dlit=11.0, n=(688, 384),
              kam=[(0, 0, 0, 0, -1.3, 0, 1.12), (11.0, 0, 0, -.22, 1.1, .25, 1.30)], tochki={'zhilishche': (.60, .40), 'ogon': (.645, .655), 'cherep': (.535, .715), 'bivni': (.705, .52), 'don': (.36, .38), 'sosedi': (.85, .36)}),
    'D1': dict(near=2.6, far=5.2, dlit=12.0, n=(688, 384),
               kam=[(0, 0, 0, 0, -1.5, -.6, 1.12), (12.0, 0, 0, -.12, 1.5, .5, 1.26)], tochki={'orudiya': (.30, .365), 'ukrasheniya': (.72, .50), 'igla': (.40, .40), 'shilo': (.445, .44), 'lopatochka': (.385, .62), 'kremen': (.52, .62), 'busy': (.75, .47), 'podveski': (.69, .66)}),
    'D2': dict(near=2.2, far=4.0, dlit=14.0, n=(448, 600),
               kam=[(0, 0, 0, 0, -1.6, 0, 1.12), (14.0, 0, 0, -.12, 1.6, .4, 1.28)], tochki={'figurka': (.63, .31), 'poyas': (.60, .40), 'ruki': (.42, .52), 'golova': (.50, .17)}),
}[SC]
INFO = json.load(open(f'{ROOT}/sloi/{SC}.json'))
NF = int(FPS * CFG['dlit'])
sc = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.resolution_percentage = 50 if PROBA else 100
sc.render.fps = FPS; sc.frame_start, sc.frame_end = 1, NF
sc.eevee.taa_render_samples = 16 if PROBA else 32
sc.view_settings.view_transform = 'Standard'; sc.view_settings.look = 'None'
sc.render.image_settings.file_format = 'PNG'
w = bpy.data.worlds.new('mir'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (0, 0, 0, 1)

def png16(path):
    im = bpy.data.images.load(path); im.colorspace_settings.name = 'Non-Color'
    W_, H_ = im.size; g = np.array(im.pixels[:], np.float32).reshape(H_, W_, 4)[::-1, :, 0]
    bpy.data.images.remove(im); return g
img0 = bpy.data.images.load(f"{ROOT}/sloi/{SC}-L0.png"); IW, IH = img0.size
LENS = 35.0; fovx = 2 * math.atan(18 / LENS); w1 = 2 * math.tan(fovx / 2); h1 = w1 * 9 / 16
if IW / IH < 16 / 9: ph, pw = h1, h1 * IW / IH
else: pw, ph = w1, w1 * IH / IW
near, far = CFG['near'], CFG['far']
a_, b_ = 1 / far, 1 / near - 1 / far
def dist(d): return 1 / (a_ + b_ * d)

def sloy(i):
    G = png16(f'{ROOT}/sloi/{SC}-L{i}-glub.png'); GH, GW = G.shape
    nx, ny = CFG['n']
    u = np.linspace(0, 1, nx + 1); v = np.linspace(0, 1, ny + 1); U, V = np.meshgrid(u, v)
    # depth at the vertices: bilinear from the layer's depth map
    gx = np.clip(U * (GW - 1), 0, GW - 1); gy = np.clip(V * (GH - 1), 0, GH - 1)
    x0, y0 = np.floor(gx).astype(int), np.floor(gy).astype(int); x1, y1 = np.minimum(x0 + 1, GW - 1), np.minimum(y0 + 1, GH - 1)
    fx, fy = gx - x0, gy - y0
    d = G[y0, x0] * (1 - fx) * (1 - fy) + G[y0, x1] * fx * (1 - fy) + G[y1, x0] * (1 - fx) * fy + G[y1, x1] * fx * fy
    r = dist(d) * (1 - .0015 * i)                 # the nearer layer is a hair closer: no flicker at the seam
    P = np.stack([(U - .5) * pw * r, (.5 - V) * ph * r, -r], -1).reshape(-1, 3)
    idx = np.arange((ny + 1) * (nx + 1)).reshape(ny + 1, nx + 1)
    F = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]], -1).reshape(-1, 4)
    me = bpy.data.meshes.new(f'sloy{i}'); me.from_pydata(P.tolist(), [], F.tolist())
    uv = me.uv_layers.new(name='UV'); li = np.zeros(len(me.loops), np.int64); me.loops.foreach_get('vertex_index', li)
    UVv = np.stack([U, 1 - V], -1).reshape(-1, 2); uv.data.foreach_set('uv', UVv[li].ravel())
    ob = bpy.data.objects.new(f'sloy{i}', me); sc.collection.objects.link(ob)
    mt = bpy.data.materials.new(f'sloy{i}'); mt.use_nodes = True; N = mt.node_tree.nodes; ln = mt.node_tree.links.new
    for x in list(N):
        if x.type != 'OUTPUT_MATERIAL': N.remove(x)
    tx = N.new('ShaderNodeTexImage'); tx.image = img0 if i == 0 else bpy.data.images.load(f'{ROOT}/sloi/{SC}-L{i}.png')
    tx.image.alpha_mode = 'STRAIGHT'; tx.interpolation = 'Cubic'; tx.extension = 'EXTEND'
    em = N.new('ShaderNodeEmission'); ln(tx.outputs['Color'], em.inputs[0]); em.inputs[1].default_value = 1.0
    if i == 0: ln(em.outputs[0], N['Material Output'].inputs[0])
    else:
        tr = N.new('ShaderNodeBsdfTransparent'); mx = N.new('ShaderNodeMixShader')
        ln(tx.outputs['Alpha'], mx.inputs[0]); ln(tr.outputs[0], mx.inputs[1]); ln(em.outputs[0], mx.inputs[2])
        ln(mx.outputs[0], N['Material Output'].inputs[0])
        try: mt.surface_render_method = 'DITHERED'
        except Exception: pass
    me.materials.append(mt)
for i in range(INFO['sloi']): sloy(i)

cam_d = bpy.data.cameras.new('kamera'); cam_d.lens = LENS * 1.12   # frame slightly narrower than the picture so the edges never show
cam_d.sensor_width = 36; cam_d.sensor_fit = 'HORIZONTAL'; cam_d.clip_start = .05; cam_d.clip_end = 500
cam = bpy.data.objects.new('kamera', cam_d); sc.collection.objects.link(cam); sc.camera = cam; cam.rotation_mode = 'XYZ'
for t, x, y, z, ry, rx, zoom in CFG['kam']:
    f = 1 + round(t * FPS)
    cam.location = (x, y, z); cam.rotation_euler = (math.radians(rx), math.radians(ry), 0)
    cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f)
    cam_d.lens = LENS * zoom; cam_d.keyframe_insert('lens', frame=f)
for fc in (cam.animation_data.action.fcurves if hasattr(cam.animation_data.action, 'fcurves') else []):
    for k in fc.keyframe_points: k.interpolation = 'BEZIER'; k.easing = 'AUTO'

# label points use the original depth (inside an object it equals its layer depth)
G0 = png16(f"{ROOT}/kartinki/{ {'C': 'stoyanka', 'D1': 'nahodki', 'D2': 'venera-v'}[SC] }-glub.png"); GH0, GW0 = G0.shape
def tochka(u, v):
    d = float(G0[min(GH0 - 1, int(v * GH0)), min(GW0 - 1, int(u * GW0))]); r = dist(d)
    return Vector(((u - .5) * pw, (.5 - v) * ph, -1)) * r
TOCHKI = {k: tochka(u, v) for k, (u, v) in CFG['tochki'].items()}
out = {}
for f in range(1, NF + 1):
    sc.frame_set(f); row = {}
    for k, p in TOCHKI.items():
        v = world_to_camera_view(sc, cam, p); row[k] = [round(v.x * 1920, 1), round((1 - v.y) * 1080, 1)]
    out[f] = row
json.dump({'kadry': out}, open(f'{ROOT}/metki-{SC}.json', 'w'))
if REZHIM == 'metki': sys.exit(0)
papka = f'{ROOT}/kadry/{SC}' if not (PROBA or TEST) else f'{ROOT}/proba/{SC}'
os.makedirs(papka, exist_ok=True)
spisok = list(range(1, NF + 1)) if REZHIM == 'vse' else [int(x) for x in REZHIM.split(',')]
for f in spisok:
    sc.frame_set(f); sc.render.filepath = f'{papka}/{f:04d}.png'
    if REZHIM == 'vse' and os.path.exists(sc.render.filepath): continue
    bpy.ops.render.render(write_still=True)
print('done', SC, len(spisok))
