# Clip 2 'Kostenki': the Don valley from real elevation and a satellite image. Blender 5.2, EEVEE.
#   blender -b --factory-startup --python dolina.py -- <root> <led|leto> <vse|1,2,3> [--proba]
# led = Ice Age (scene B, descent from above to the site, dusk); leto = today (scene E, rise to a wide shot, daylight).
# Frames -> <root>/kadry/<B|E>/NNNN.png; on-screen positions of label points -> <root>/metki-<B|E>.json.
import bpy, bmesh, math, json, sys, os
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

A = sys.argv[sys.argv.index('--') + 1:]
ROOT, VAR, REZHIM = A[0], A[1], A[2]; PROBA = '--proba' in A; TEST = '--test' in A   # --test: full size, frames go to proba/
SC = 'B' if VAR == 'led' else 'E'
FPS = 30; DLIT = 11.0 if VAR == 'led' else 16.0; NF = int(FPS * DLIT)
sc = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.resolution_percentage = 50 if PROBA else 100
sc.render.fps = FPS; sc.frame_start, sc.frame_end = 1, NF
sc.eevee.taa_render_samples = 16 if PROBA else 32
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception as e: print('look', e)
sc.render.image_settings.file_format = 'PNG'
def L(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + .055) / 1.055) ** 2.4 if x > .04045 else x / 12.92 for x in c) + (1,)

# -- relief: 1 unit = 1 km; height x4 so gullies read, but no 'canyon' (the real relief is ~100 m)
# coarse 24 m grid (cleaned relief from tekstury2.py) with a hole for the 14x14 km detail patch on an 8 m grid (detal.py)
E = np.load(f'{ROOT}/dannye/rel_ef_don-{VAR}.npy').astype(np.float32); E = np.clip(E, 70, 240)
U = json.load(open(f'{ROOT}/dannye/uchastok.json')); X0, Y0, NPX, KU = U['x0'], U['y0'], U['npx'], U['k']
Zu = np.load(f'{ROOT}/dannye/uchastok-{VAR}.npy').astype(np.float32)
EX = 4.0; HALF = E.shape[0] / 2
def xy(px, py): return (px - HALF) * .024, (HALF - py) * .024
def zz(e): return (e - 90) / 1000 * EX
def setka(imya, Z, PXc, PYc, ostavit=None):
    ny, nx = Z.shape
    P = np.stack([(PXc - HALF) * .024, (HALF - PYc) * .024, zz(Z)], -1).reshape(-1, 3).astype(np.float32)
    idx = np.arange(ny * nx).reshape(ny, nx)
    Q = np.stack([idx[:-1, :-1], idx[1:, :-1], idx[1:, 1:], idx[:-1, 1:]], -1)
    if ostavit is not None: Q = Q[ostavit]
    F = Q.reshape(-1).astype(np.int32); nf = len(F) // 4
    me = bpy.data.meshes.new(imya)
    me.vertices.add(ny * nx); me.vertices.foreach_set('co', P.ravel())
    me.loops.add(nf * 4); me.loops.foreach_set('vertex_index', F)
    me.polygons.add(nf); me.polygons.foreach_set('loop_start', np.arange(0, nf * 4, 4, dtype=np.int32))
    try: me.update(calc_edges=True)
    except TypeError: me.update()
    uv = me.uv_layers.new(name='UV')
    UVv = np.stack([PXc / (2 * HALF - 1), 1 - PYc / (2 * HALF - 1)], -1).reshape(-1, 2).astype(np.float32)
    uv.data.foreach_set('uv', UVv.reshape(-1, 2)[F].ravel())
    me.polygons.foreach_set('use_smooth', np.ones(nf, bool))
    ob = bpy.data.objects.new(imya, me); sc.collection.objects.link(ob); return ob
S = 1 if not PROBA else 2
Es = E[::S, ::S]; jj, ii = np.mgrid[0:Es.shape[0], 0:Es.shape[1]]
qi, qj = ii[:-1, :-1] * S, jj[:-1, :-1] * S
v_okne = (qi >= X0) & (qi + S <= X0 + NPX) & (qj >= Y0) & (qj + S <= Y0 + NPX)
dol = setka('dolina', Es, (ii * S).astype(np.float32), (jj * S).astype(np.float32), ~v_okne)
nU = Zu.shape[0]; ju, iu = np.mgrid[0:nU, 0:nU].astype(np.float32)
uch = setka('uchastok', Zu, X0 + iu / KU, Y0 + ju / KU)
mt = bpy.data.materials.new('dolina'); mt.use_nodes = True; N = mt.node_tree.nodes; pb = N['Principled BSDF']; ln = mt.node_tree.links.new
# 7168^2 colour map (~6 m): 'today' is the Sentinel-2 image, the Ice Age is nature from the image + snow (tekstury2.py)
tx = N.new('ShaderNodeTexImage'); tx.image = bpy.data.images.load(f'{ROOT}/tex/dolina2-{VAR}.png'); tx.interpolation = 'Cubic'
# fine texture on top (in metres, stays crisp close up): snow / grass grain
tc_ = N.new('ShaderNodeTexCoord')
nz1 = N.new('ShaderNodeTexNoise'); nz1.inputs['Scale'].default_value = 160; nz1.inputs['Detail'].default_value = 5; ln(tc_.outputs['Object'], nz1.inputs['Vector'])
nz2 = N.new('ShaderNodeTexNoise'); nz2.inputs['Scale'].default_value = 900; nz2.inputs['Detail'].default_value = 3; ln(tc_.outputs['Object'], nz2.inputs['Vector'])
m1 = N.new('ShaderNodeMath'); m1.operation = 'MULTIPLY_ADD'; m1.inputs[1].default_value = .16; m1.inputs[2].default_value = .92; ln(nz1.outputs['Fac'], m1.inputs[0])
mul = N.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'; mul.inputs['Factor'].default_value = 1.0
ln(tx.outputs['Color'], mul.inputs['A']); ln(m1.outputs[0], mul.inputs['B']); ln(mul.outputs['Result'], pb.inputs['Base Color'])
tb = N.new('ShaderNodeTexImage'); tb.image = bpy.data.images.load(f'{ROOT}/tex/dolina2-bump-{VAR}.png'); tb.image.colorspace_settings.name = 'Non-Color'; tb.interpolation = 'Cubic'
bu = N.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = .45 if VAR == 'leto' else .35; bu.inputs['Distance'].default_value = .004
ln(tb.outputs[0], bu.inputs['Height'])
bu2 = N.new('ShaderNodeBump'); bu2.inputs['Strength'].default_value = .25 if VAR == 'leto' else .4; bu2.inputs['Distance'].default_value = .0008
ad = N.new('ShaderNodeMath'); ad.operation = 'ADD'; ln(nz1.outputs['Fac'], ad.inputs[0]); ln(nz2.outputs['Fac'], ad.inputs[1])
ln(ad.outputs[0], bu2.inputs['Height']); ln(bu.outputs[0], bu2.inputs['Normal']); ln(bu2.outputs[0], pb.inputs['Normal'])
pb.inputs['Roughness'].default_value = .85 if VAR == 'leto' else .62
pb.inputs['Specular IOR Level'].default_value = .2 if VAR == 'leto' else .4
dol.data.materials.append(mt); uch.data.materials.append(mt)
try: bpy.context.preferences.system.anisotropic_filter = 'FILTER_16'   # oblique views of the texture without blur
except Exception as e: print('aniso', e)
try: sc.eevee.use_raytracing = True                                   # shading in gullies and under trees
except Exception as e: print('rt', e)

# -- sky, haze, light
w = bpy.data.worlds.new('mir'); sc.world = w; w.use_nodes = True; wn = w.node_tree.nodes
bg = wn['Background']
sky_c = '#8fa2b5' if VAR == 'led' else '#a9c6e0'
bg.inputs[0].default_value = L(sky_c); bg.inputs[1].default_value = .75 if VAR == 'led' else 1.1
# sky: lighter towards the horizon
wtc = wn.new('ShaderNodeTexCoord'); wsz = wn.new('ShaderNodeSeparateXYZ'); w.node_tree.links.new(wtc.outputs['Generated'], wsz.inputs[0])
wcr = wn.new('ShaderNodeValToRGB'); wcr.color_ramp.elements[0].position = 0.0; wcr.color_ramp.elements[1].position = .35
wcr.color_ramp.elements[0].color = L('#c9d4de' if VAR == 'led' else '#d6e4ef'); wcr.color_ramp.elements[1].color = L('#7f98b0' if VAR == 'led' else '#8fb3d4')
w.node_tree.links.new(wsz.outputs['Z'], wcr.inputs[0]); w.node_tree.links.new(wcr.outputs[0], bg.inputs[0])
# distance haze inside the material (the world volume in EEVEE 5 is infinite and eats the image); kept weak to avoid mush
cd_ = N.new('ShaderNodeCameraData'); ex = N.new('ShaderNodeMath'); ex.operation = 'MULTIPLY'; ex.inputs[1].default_value = -(.009 if VAR == 'led' else .007)
ln(cd_.outputs['View Distance'], ex.inputs[0])
ep = N.new('ShaderNodeMath'); ep.operation = 'EXPONENT'; ln(ex.outputs[0], ep.inputs[0])
inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1; ln(ep.outputs[0], inv.inputs[1])
fog = N.new('ShaderNodeEmission'); fog.inputs[0].default_value = L('#9fb0c0' if VAR == 'led' else '#c8d8e6'); fog.inputs[1].default_value = 1.0
mx = N.new('ShaderNodeMixShader'); ln(inv.outputs[0], mx.inputs[0]); ln(pb.outputs[0], mx.inputs[1]); ln(fog.outputs[0], mx.inputs[2])
ln(mx.outputs[0], N['Material Output'].inputs[0])
def svet(energy, color, az, el, ugol=1.2):
    d = bpy.data.lights.new('solnce', 'SUN'); d.energy = energy; d.color = color; d.angle = math.radians(ugol)
    o = bpy.data.objects.new('solnce', d); sc.collection.objects.link(o)
    o.rotation_euler = (math.radians(90 - el), 0, math.radians(az)); return o
if VAR == 'led': svet(4.6, (1.0, .94, .86), 325, 7)          # low winter sun from the south-west, beside the camera: long shadows model the slopes
else: svet(4.0, (1.0, .96, .9), 335, 36)                      # summer sun from the south-south-west

# -- Ice Age trees: snowy spruce/pine and bare birch in clumps on gully floors (detal.py)
def derevo_el(H):
    bm = bmesh.new()
    for r, z0, h in ((.36, .10, .42), (.29, .34, .36), (.21, .56, .30), (.12, .76, .26)):
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=7, radius1=r * H * .55, radius2=0, depth=h * H)
        bmesh.ops.translate(bm, verts=res['verts'], vec=(0, 0, (z0 + h / 2) * H))
    me = bpy.data.meshes.new('el'); bm.to_mesh(me); bm.free(); return me
def derevo_bereza(H):
    bm = bmesh.new(); res = bmesh.ops.create_uvsphere(bm, u_segments=7, v_segments=5, radius=.5)
    bmesh.ops.scale(bm, verts=res['verts'], vec=(H * .5, H * .5, H * .75)); bmesh.ops.translate(bm, verts=res['verts'], vec=(0, 0, H * .55))
    me = bpy.data.meshes.new('bereza'); bm.to_mesh(me); bm.free(); return me
def mat_derevo(imya, temn, sneg_sila):
    m = bpy.data.materials.new(imya); m.use_nodes = True; n = m.node_tree.nodes; p = n['Principled BSDF']; l = m.node_tree.links.new
    ge = n.new('ShaderNodeNewGeometry'); sz = n.new('ShaderNodeSeparateXYZ'); l(ge.outputs['Normal'], sz.inputs[0])
    oi = n.new('ShaderNodeObjectInfo')
    mr = n.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = .2; mr.inputs['From Max'].default_value = .75; l(sz.outputs['Z'], mr.inputs['Value'])
    mm_ = n.new('ShaderNodeMath'); mm_.operation = 'MULTIPLY'; mm_.inputs[1].default_value = sneg_sila; l(mr.outputs[0], mm_.inputs[0])
    cr = n.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = temn; cr.color_ramp.elements[1].color = (temn[0] * 1.6, temn[1] * 1.5, temn[2] * 1.4, 1)
    l(oi.outputs['Random'], cr.inputs[0])
    mx_ = n.new('ShaderNodeMix'); mx_.data_type = 'RGBA'; l(mm_.outputs[0], mx_.inputs['Factor']); l(cr.outputs[0], mx_.inputs['A'])
    mx_.inputs['B'].default_value = (.82, .86, .92, 1); l(mx_.outputs['Result'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = .9; return m
if VAR == 'led':
    T = np.load(f'{ROOT}/dannye/derevya-led.npz')
    keep = (np.arange(len(T['px'])) % 2 == 0) if PROBA else np.ones(len(T['px']), bool)
    MAT = {0: mat_derevo('el', (.025, .045, .033, 1), .75), 1: mat_derevo('bereza', (.16, .13, .115, 1), .25), 2: mat_derevo('iva', (.24, .2, .17, 1), .35)}
    for vid in (0, 1, 2):
        for b_, (lo, hi_) in enumerate(((.0, .9), (.9, 1.1), (1.1, 9))):
            sel = keep & (T['vid'] == vid) & (T['rost'] >= lo) & (T['rost'] < hi_)
            if not sel.any(): continue
            x, y = xy(T['px'][sel], T['py'][sel]); z = zz(T['h'][sel]) - .001
            pts = bpy.data.meshes.new(f'tochki{vid}{b_}'); pts.vertices.add(int(sel.sum()))
            pts.vertices.foreach_set('co', np.stack([x, y, z], -1).astype(np.float32).ravel()); pts.update()
            po = bpy.data.objects.new(f'tochki{vid}{b_}', pts); sc.collection.objects.link(po)
            po.instance_type = 'VERTS'; po.show_instancer_for_render = False
            H = (.030, .022, .008)[vid] * (.85, 1.0, 1.18)[b_]      # spruce ~20 m, birch ~15 m, willow ~5 m: slightly larger than life
            me_ = derevo_el(H) if vid == 0 else derevo_bereza(H); me_.materials.append(MAT[vid])
            for p_ in me_.polygons: p_.use_smooth = vid == 1
            d_ = bpy.data.objects.new(f'derevo{vid}{b_}', me_); sc.collection.objects.link(d_); d_.parent = po
    print('trees', int(keep.sum()))

# -- Kostenki marker: ring on the surface
KPX, KPY = 824, 794
kx, ky = xy(KPX, KPY); cu, cv = int((KPX - X0) * KU), int((KPY - Y0) * KU)
kz = zz(float(Zu[cv - 18:cv + 19, cu - 18:cu + 19].max())) + .03
ring = bpy.data.objects.new('metka', bpy.data.meshes.new('metka')); sc.collection.objects.link(ring)
bm = bmesh.new()
for k in range(64):
    a1, a2 = 2 * math.pi * k / 64, 2 * math.pi * (k + 1) / 64
    bm.faces.new([bm.verts.new((r * math.cos(a), r * math.sin(a), 0)) for r, a in ((.19, a1), (.26, a1), (.26, a2), (.19, a2))])
bm.to_mesh(ring.data); bm.free()
mm = bpy.data.materials.new('metka'); mm.use_nodes = True; n = mm.node_tree.nodes
for x in list(n):
    if x.type != 'OUTPUT_MATERIAL': n.remove(x)
em = n.new('ShaderNodeEmission'); em.inputs[0].default_value = L('#ff6a3d'); em.inputs[1].default_value = 2.5
mm.node_tree.links.new(em.outputs[0], n['Material Output'].inputs[0]); ring.data.materials.append(mm)
ring.location = (kx, ky, kz)
T0 = 1.6 if VAR == 'led' else 0.0
for f, s in ((1 + round(T0 * FPS) - 1, 0), (1 + round((T0 + .7) * FPS), 1.0)): ring.scale = (s, s, s); ring.keyframe_insert('scale', frame=max(1, f))
ring.visible_shadow = False
ring.hide_render = True   # the ring is no longer rendered: a crisp marker is drawn in the edit

# -- camera keys: (sec, position relative to Kostenki, look-at point relative to Kostenki)
cam_d = bpy.data.cameras.new('kamera'); cam_d.lens = 35; cam_d.clip_start = .05; cam_d.clip_end = 200
cam = bpy.data.objects.new('kamera', cam_d); sc.collection.objects.link(cam); sc.camera = cam
cel = bpy.data.objects.new('cel', None); sc.collection.objects.link(cel)
tc = cam.constraints.new('TRACK_TO'); tc.target = cel; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
if VAR == 'led':   # from above (cut from the globe) -> oblique view from the floodplain to the high bank and gullies
    KAM = [(0, (0, -0.4, 26), (0, 0, 0)), (3.4, (4.5, -7, 7), (0, .3, 0)), (7.0, (4.2, -3.6, 1.6), (-.6, .4, .2)), (11.0, (3.3, -2.6, .95), (-.7, .5, .15))]   # lower and closer: gullies and trees are visible
else:              # today: from the site, a slow rise to a wide shot of the valley
    KAM = [(0, (5.4, -4.0, 2.5), (-.8, .5, .35)), (6.0, (7.4, -6.4, 3.9), (-.6, .8, .3)), (16.0, (13, -13, 9), (-2, 2.5, 0))]
for t, p, c in KAM:
    f = 1 + round(t * FPS)
    cam.location = (kx + p[0], ky + p[1], kz + p[2]); cam.keyframe_insert('location', frame=f)
    cel.location = (kx + c[0], ky + c[1], kz + c[2]); cel.keyframe_insert('location', frame=f)

# -- on-screen marker position per frame (for labels)
# label points (dannye/tochki.json, relief pixels) -> world coordinates on the surface
TJ = json.load(open(f'{ROOT}/dannye/tochki.json'))
def na_zemle(px, py):
    if X0 <= px <= X0 + NPX and Y0 <= py <= Y0 + NPX:
        h = float(Zu[int(round((py - Y0) * KU)), int(round((px - X0) * KU))])
    else:
        h = float(E[int(round(min(py, E.shape[0] - 1))), int(round(min(px, E.shape[1] - 1)))])
    x, y = xy(px, py); return Vector((x, y, zz(h) + .004))
TP = {k: na_zemle(*v) for k, v in TJ.items()}
out, tch = {}, {}
for f in range(1, NF + 1):
    sc.frame_set(f); v = world_to_camera_view(sc, cam, Vector((kx, ky, kz)))
    out[f] = [round(v.x * 1920, 1), round((1 - v.y) * 1080, 1), round(v.z, 3)]
    row = {}
    for k, p in TP.items():
        q = world_to_camera_view(sc, cam, p); row[k] = [round(q.x * 1920, 1), round((1 - q.y) * 1080, 1), round(q.z, 3)]
    tch[f] = row
json.dump({'kadry': out, 'tochki': tch}, open(f'{ROOT}/metki-{SC}.json', 'w'))
if REZHIM == 'metki': sys.exit(0)
PAPKA = f'{ROOT}/kadry/{SC}' if not (PROBA or TEST) else f'{ROOT}/proba/{SC}'
os.makedirs(PAPKA, exist_ok=True)
spisok = list(range(1, NF + 1)) if REZHIM == 'vse' else [int(x) for x in REZHIM.split(',')]
for f in spisok:
    sc.frame_set(f); sc.render.filepath = f'{PAPKA}/{f:04d}.png'
    if REZHIM == 'vse' and os.path.exists(sc.render.filepath): continue
    bpy.ops.render.render(write_still=True)
print('done', SC, len(spisok))
