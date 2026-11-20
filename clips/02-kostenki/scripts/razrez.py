# Clip 2: 'site section', a volumetric block of earth like a museum diorama. Blender 5.2, EEVEE.
# Section face: layers from top to bottom (data in RAZREZ below), every layer boundary is wavy; the face is uneven (real relief,
# soft layers slightly recessed, chalk protrudes), the layers hold bones, flints and hearth charcoal; a white lens of volcanic ash.
# Grass on top. The camera slowly descends along the face. On-screen layer positions -> metki-S.json (labels in the edit).
#   blender -b --factory-startup --python razrez.py -- <root> <vse|1,2,3|metki> [--proba]
import bpy, bmesh, math, json, sys, os
import numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

A = sys.argv[sys.argv.index('--') + 1:]
ROOT, REZHIM = A[0], A[1]; PROBA = '--proba' in A
FPS = 30
# -- layers from top to bottom: (key, thickness m, sRGB colour, roughness, recess m, note for the label)
RAZREZ = json.load(open(f'{ROOT}/dannye/razrez.json'))
SL = RAZREZ['sloi']
DLIT = RAZREZ.get('dlit', 9.0); NF = int(FPS * DLIT)
W_, D_ = RAZREZ.get('shirina', 4.2), 2.2                                   # section width and block depth, m
H_ = sum(s['tol'] for s in SL)
sc = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.render.resolution_percentage = 50 if PROBA else 100
sc.render.fps = FPS; sc.frame_start, sc.frame_end = 1, NF
sc.eevee.taa_render_samples = 16 if PROBA else 48
try: sc.eevee.use_raytracing = True
except Exception: pass
sc.view_settings.view_transform = 'AgX'
try: sc.view_settings.look = 'AgX - Medium High Contrast'
except Exception: pass
sc.render.image_settings.file_format = 'PNG'
def L(h):
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [((x + .055) / 1.055) ** 2.4 if x > .04045 else x / 12.92 for x in c]
rng = np.random.default_rng(3)
def shum1(n, sig):
    from math import ceil
    z = rng.standard_normal(n + 200); k = np.exp(-np.arange(-int(3 * sig), int(3 * sig) + 1) ** 2 / (2 * sig * sig)); k /= k.sum()
    z = np.convolve(z, k, 'same')[100:100 + n]; return z / (z.std() + 1e-6)
def shum2(ny, nx, sig, seed):
    r = np.random.default_rng(seed).standard_normal((ny + 40, nx + 40)).astype(np.float32)
    k = np.exp(-np.arange(-int(3 * sig), int(3 * sig) + 1) ** 2 / (2 * sig * sig)); k /= k.sum()
    r = np.apply_along_axis(lambda v: np.convolve(v, k, 'same'), 0, r); r = np.apply_along_axis(lambda v: np.convolve(v, k, 'same'), 1, r)
    r = r[20:20 + ny, 20:20 + nx]; return r / (r.std() + 1e-6)

# -- layer boundaries: wavy lines z(x) (0 = surface, negative = down)
NX = 420 if PROBA else 900
NZ = int(round(NX * sum(s_['tol'] for s_ in SL) / W_))      # equal step across width and height so blotches stay round
xs = np.linspace(-W_ / 2, W_ / 2, NX)
granicy = []; z = 0.0
for i, s in enumerate(SL):
    z -= s['tol']
    vol = s.get('volna', .05)
    g = z + vol * (.6 * np.sin(xs * 1.3 + i * 1.7) + .4 * shum1(NX, 40)) if i < len(SL) - 1 else np.full(NX, -H_ - .2)
    granicy.append(g)
def sloy_v(x_i, zz_):                                # layer index at a point of the section
    k = 0
    for i, g in enumerate(granicy):
        if zz_ < g[x_i]: k = i + 1
    return min(k, len(SL) - 1)

# -- section face: a dense mesh with real relief and per-vertex colour
zs = np.linspace(0, -H_, NZ)
X, Z = np.meshgrid(xs, zs)
G = np.stack(granicy[:-1], 0)                         # (layers-1, NX)
idx = (Z[None, :, :] < G[:, None, :]).sum(0)          # layer index at every vertex
idx = np.minimum(idx, len(SL) - 1)
# texture by soil type: loam is a cleaned face with fine bedding and vertical cracks;
# soil and humus are lumpy with root traces; ash is dense and protrudes slightly; chalk is rubble
f1, f2, f3 = shum2(NZ, NX, 1.0, 5), shum2(NZ, NX, 2.5, 6), shum2(NZ, NX, 7.0, 7)
tip = np.array([s.get('faktura', 'suglinok') for s in SL])[idx]
utop = np.array([s.get('utop', 0) for s in SL])[idx]
disp = np.zeros_like(X); cmod = np.ones_like(X)
m_ = tip == 'suglinok'
treshchiny = np.exp(-((np.sin(X * 23 + 1.5 * f3) * 3) ** 2)) * (f2 > -.3)          # vertical cracks
disp += m_ * (.0025 * f1 + .004 * f3 - .005 * treshchiny)
cmod *= np.where(m_, 1 + .045 * np.sin(Z * 140 + 2 * f3) - .12 * treshchiny, 1)
m_ = tip == 'kroshka'
korni = np.exp(-((np.sin(X * 37 + 3 * f3) * 4) ** 2)) * (f2 > .3)
disp += m_ * (.006 * f2 + .003 * f1 + .006 * f3)
cmod *= np.where(m_, 1 + .12 * f2 - .25 * korni, 1)
m_ = tip == 'pepel'
disp += m_ * (.0015 * f1 + .006)
cmod *= np.where(m_, 1 + .04 * f1, 1)
m_ = tip == 'shcheben'
kuski = np.clip(f2 * 1.2, -1, 1.6); disp += m_ * (.018 * kuski + .004 * f1 + .006 * f3)
cmod *= np.where(m_, 1 + .14 * kuski - .1 * (f1 < -1.2), 1)
# soft boundaries: colour and recess blend over ~6 mm along the wavy line itself, no mesh stepping
CV = np.array([L(s['cvet']) for s in SL], np.float32); UT = np.array([s.get('utop', 0) for s in SL], np.float32)
col = np.broadcast_to(CV[0], X.shape + (3,)).copy(); utop = np.full(X.shape, UT[0], np.float32)
for i in range(len(SL) - 1):
    t = np.clip((G[i][None, :] - Z) / .012 + .5, 0, 1); t = t * t * (3 - 2 * t)
    col = col * (1 - t[..., None]) + CV[i + 1] * t[..., None]; utop = utop * (1 - t) + UT[i + 1] * t
Yd = -(utop - disp)
# blotches of a second colour (gleying, burnt clay, chalk), bands in loams, breaks in the ash lenses
C2 = np.array([L(s.get('cvet2', s['cvet'])) for s in SL], np.float32)[idx]; PY = np.array([s.get('pyatna', 0) for s in SL])[idx]
pm = np.clip((shum2(NZ, NX, 1.8, 31) - (1.5 - 1.6 * PY)) * 3, 0, 1) * (PY > 0)
col = col * (1 - pm[..., None]) + C2 * pm[..., None]
POL = np.array([L(s.get('polosy', s['cvet'])) for s in SL], np.float32)[idx]; ESTP = np.array(['polosy' in s for s in SL])[idx]
bands = np.clip(np.sin(Z * 11 + .25 * f3) * 4 - 3.1, 0, 1) * ESTP
col = col * (1 - bands[..., None] * .45) + POL * bands[..., None] * .45
col *= (cmod * (1 + .05 * f3))[..., None]
_verh = [0] + [g.mean() for g in granicy[:-1]]
for si_, x_, gl_, vid_, razm_, rot_ in RAZREZ.get('nahodki', []):
    z0_ = _verh[si_] - SL[si_]['tol'] * gl_
    if vid_ == 'ochag':      # charcoal lens with a red burnt rim below
        e = ((X - x_) / razm_) ** 2 + ((Z - z0_) / (razm_ * .22)) ** 2
        kraj = np.clip(1.25 - e, 0, 1) * np.clip(1 - ((Z - z0_ + razm_ * .12) / (razm_ * .18)) ** 2, 0, 1)
        col = col * (1 - kraj[..., None] * .85) + np.array(L('#a8452c'), np.float32) * kraj[..., None] * .85
        yadro = np.clip((1 - e) * 4, 0, 1) * (1 + .15 * f1 > .9)
        col = col * (1 - yadro[..., None] * .92) + np.array(L('#141110'), np.float32) * yadro[..., None] * .92
    if vid_ == 'ugol':       # scattered charcoal
        for k_ in range(14):
            cx_, cz_ = x_ + rng.normal(0, .12), z0_ + rng.normal(0, .025); r_ = abs(rng.normal(.008, .004)) + .004
            sp = np.clip(1.3 - (((X - cx_) ** 2 + (Z - cz_) ** 2) / r_ ** 2), 0, 1)
            col = col * (1 - sp[..., None] * .9) + np.array(L('#121010'), np.float32) * sp[..., None] * .9
P = np.stack([X, Yd, Z], -1).reshape(-1, 3).astype(np.float32)
ids = np.arange(NZ * NX).reshape(NZ, NX)
F = np.stack([ids[:-1, :-1], ids[1:, :-1], ids[1:, 1:], ids[:-1, 1:]], -1).reshape(-1).astype(np.int32)   # normal faces the viewer (-Y)
me = bpy.data.meshes.new('srez'); me.vertices.add(NZ * NX); me.vertices.foreach_set('co', P.ravel())
nf = len(F) // 4; me.loops.add(nf * 4); me.loops.foreach_set('vertex_index', F)
me.polygons.add(nf); me.polygons.foreach_set('loop_start', np.arange(0, nf * 4, 4, dtype=np.int32))
try: me.update(calc_edges=True)
except TypeError: me.update()
ca = me.color_attributes.new('cvet', 'FLOAT_COLOR', 'POINT')
ca.data.foreach_set('color', np.concatenate([col.reshape(-1, 3), np.ones((NZ * NX, 1), np.float32)], 1).ravel())
me.polygons.foreach_set('use_smooth', np.ones(nf, bool))
srez = bpy.data.objects.new('srez', me); sc.collection.objects.link(srez)
m = bpy.data.materials.new('srez'); m.use_nodes = True; N = m.node_tree.nodes; ln = m.node_tree.links.new; p = N['Principled BSDF']
at = N.new('ShaderNodeVertexColor'); at.layer_name = 'cvet'; ln(at.outputs['Color'], p.inputs['Base Color'])
p.inputs['Roughness'].default_value = .92
tc = N.new('ShaderNodeTexCoord'); nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 60; nz.inputs['Detail'].default_value = 8
ln(tc.outputs['Object'], nz.inputs['Vector']); bu = N.new('ShaderNodeBump'); bu.inputs['Strength'].default_value = .18; bu.inputs['Distance'].default_value = .003
ln(nz.outputs['Fac'], bu.inputs['Height']); ln(bu.outputs[0], p.inputs['Normal'])
srez.data.materials.append(m)

# -- side face and top (continuing the layers), the bottom is a shadow on the stand
def bok():
    ny = 160 if not PROBA else 80; ys_ = np.linspace(0, D_, ny)
    Xb, Zb = np.meshgrid(ys_, zs)
    xi = NX - 1
    idb = np.minimum((Zb[None] < G[:, xi][:, None, None]).sum(0), len(SL) - 1)
    nb = shum2(NZ, ny, 2.0, 21)
    Pb = np.stack([np.full_like(Xb, W_ / 2) + (np.array([s.get('utop', 0) for s in SL])[idb] + .01 * nb) * 0, Xb, Zb], -1)
    Pb[..., 0] = W_ / 2 - np.array([s.get('sher', .01) for s in SL])[idb] * nb * .6
    cb = np.array([L(s['cvet']) for s in SL], np.float32)[idb] * (1 + .1 * nb[..., None]) * .93
    P2 = Pb.reshape(-1, 3).astype(np.float32); ids2 = np.arange(NZ * ny).reshape(NZ, ny)
    F2 = np.stack([ids2[:-1, :-1], ids2[1:, :-1], ids2[1:, 1:], ids2[:-1, 1:]], -1).reshape(-1).astype(np.int32)
    mb = bpy.data.meshes.new('bok'); mb.vertices.add(len(P2)); mb.vertices.foreach_set('co', P2.ravel())
    n2 = len(F2) // 4; mb.loops.add(n2 * 4); mb.loops.foreach_set('vertex_index', F2)
    mb.polygons.add(n2); mb.polygons.foreach_set('loop_start', np.arange(0, n2 * 4, 4, dtype=np.int32))
    try: mb.update(calc_edges=True)
    except TypeError: mb.update()
    c2 = mb.color_attributes.new('cvet', 'FLOAT_COLOR', 'POINT')
    c2.data.foreach_set('color', np.concatenate([cb.reshape(-1, 3), np.ones((len(P2), 1), np.float32)], 1).ravel())
    mb.polygons.foreach_set('use_smooth', np.ones(n2, bool))
    o = bpy.data.objects.new('bok', mb); sc.collection.objects.link(o); o.data.materials.append(m)
bok()
# top: turf with grass
bpy.ops.mesh.primitive_grid_add(x_subdivisions=120, y_subdivisions=60, size=1, location=(0, D_ / 2, .0))
verh = bpy.context.object; verh.scale = (W_, D_, 1); bpy.ops.object.transform_apply(scale=True)
mv = bpy.data.materials.new('dern'); mv.use_nodes = True; pv = mv.node_tree.nodes['Principled BSDF']; pv.inputs['Base Color'].default_value = (*L('#5b6b3a'), 1); pv.inputs['Roughness'].default_value = .95
verh.data.materials.append(mv)
ps = verh.modifiers.new('trava', 'PARTICLE_SYSTEM').particle_system; st = ps.settings
st.type = 'HAIR'; st.count = 9000 if PROBA else 26000; st.hair_length = .12; st.use_advanced_hair = True
st.render_type = 'PATH'; st.child_type = 'INTERPOLATED'; st.child_percent = 6 if PROBA else 12; st.rendered_child_count = st.child_percent
st.root_radius = .004; st.tip_radius = .0005; st.radius_scale = 1
st.kink = 'CURL'; st.kink_amplitude = .01; st.roughness_1 = .03; st.roughness_endpoint = .02
mt_tr = bpy.data.materials.new('trava'); mt_tr.use_nodes = True; ptr = mt_tr.node_tree.nodes['Principled BSDF']; ptr.inputs['Base Color'].default_value = (*L('#7a8a46'), 1); ptr.inputs['Roughness'].default_value = .8
verh.data.materials.append(mt_tr); st.material = 2
# stand and background
bpy.ops.mesh.primitive_plane_add(size=40, location=(0, 0, -H_ - .01)); pod = bpy.context.object
mp = bpy.data.materials.new('pod'); mp.use_nodes = True; mp.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.03, .035, .04, 1); pod.data.materials.append(mp)
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (*L('#1a2026'), 1); w.node_tree.nodes['Background'].inputs[1].default_value = .6

# -- finds in the layers (bones, flints, charcoal) from RAZREZ['nahodki']: (layer, x, depth in layer 0..1, kind, size, rotation)
def kamen(razm, seed):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=1, radius=razm)
    r = np.random.default_rng(seed)
    for v in bm.verts: v.co = v.co * float(r.uniform(.6, 1.3)); v.co.z *= .45
    me_ = bpy.data.meshes.new('k'); bm.to_mesh(me_); bm.free(); return me_
def kost_(dl, r_, seed):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=r_, radius2=r_ * .8, depth=dl)
    for sgn in (-1, 1):
        res = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=r_ * 1.5); bmesh.ops.translate(bm, verts=res['verts'], vec=(0, 0, sgn * dl / 2))
    me_ = bpy.data.meshes.new('kost'); bm.to_mesh(me_); bm.free(); return me_
def oblomok(dl, r_, seed):       # bone fragment: irregular, slightly bent, broken ends
    rr = np.random.default_rng(seed); bm = bmesh.new()
    res = bmesh.ops.create_cone(bm, cap_ends=True, segments=9, radius1=r_, radius2=r_ * rr.uniform(.7, 1.0), depth=dl)
    for v in bm.verts:
        t = v.co.z / dl; ang = math.atan2(v.co.y, v.co.x)
        k = 1 + .18 * math.sin(ang * 3 + seed) + .1 * rr.standard_normal()
        if abs(t) > .45: k *= rr.uniform(.55, 1.05); v.co.z += rr.uniform(-.25, .25) * r_ * 2     # ragged edge
        v.co.x *= k; v.co.y *= k; v.co.x += .12 * dl * (t * t - .25)                              # bend
    me_ = bpy.data.meshes.new('oblomok'); bm.to_mesh(me_); bm.free()
    for p_ in me_.polygons: p_.use_smooth = True
    return me_
MAT = {}
def mat(imya, c, rough=.8):
    if imya in MAT: return MAT[imya]
    mm = bpy.data.materials.new(imya); mm.use_nodes = True; pp = mm.node_tree.nodes['Principled BSDF']; pp.inputs['Base Color'].default_value = (*L(c), 1); pp.inputs['Roughness'].default_value = rough
    MAT[imya] = mm; return mm
verh_sloya = [0] + [g.mean() for g in granicy[:-1]]
bpy.ops.wm.obj_import(filepath=f'{ROOT}/modeli/bedro0.obj', forward_axis='Y', up_axis='Z')
_b = bpy.context.selected_objects[0]; KOST = _b.data
for v in KOST.vertices: v.co.z -= .57          # recentre
bpy.data.objects.remove(_b, do_unlink=True)
for p_ in KOST.polygons: p_.use_smooth = True
for k, (si, x, gl, vid, razm, rot) in enumerate(RAZREZ.get('nahodki', [])):
    if vid in ('ochag', 'ugol'): continue           # drawn into the face
    z0 = verh_sloya[si] - SL[si]['tol'] * gl
    if vid == 'kost':
        me_ = oblomok(razm, razm * .075, k); me_.transform(__import__('mathutils').Matrix.Diagonal((1, .6, 1, 1))); mm = mat('kost', '#b9a47f', .7)   # a fragment lying flat in the wall
    elif vid == 'ochag':
        me_ = kamen(razm, k); me_.transform(__import__('mathutils').Matrix.Diagonal((1, .35, .3, 1))); mm = mat('ochag', '#120f0d', .95)
        k2 = kamen(razm * 1.25, k + 99); k2.transform(__import__('mathutils').Matrix.Diagonal((1, .3, .42, 1))); k2.materials.append(mat('glina', '#a8452c', .9))
        o2 = bpy.data.objects.new(f'glina{k}', k2); sc.collection.objects.link(o2); o2.location = (x, .005, verh_sloya[si] - SL[si]['tol'] * gl)
    elif vid == 'kremen': me_ = kamen(razm, k); mm = mat('kremen', '#3c3a38', .35)
    elif vid == 'ugol': me_ = kamen(razm, k); mm = mat('ugol', '#141210', .9)
    else: me_ = kamen(razm, k); mm = mat('mel', '#ece6d6', .9)
    me_.materials.append(mm); o = bpy.data.objects.new(f'nahodka{k}', me_); sc.collection.objects.link(o)
    o.location = (x, (.004 * razm if vid == 'kost' else .004), z0); o.rotation_euler = (math.radians(rot[0]), math.radians(rot[1]), math.radians(rot[2]))   # half buried in the wall

# -- light: soft key from the upper left, fill from the right, rim light from behind
for nm, en, rot, sz in (('key', 900, (58, 0, -38), 5), ('fill', 260, (72, 0, 52), 7), ('rim', 500, (60, 0, 175), 4)):
    d = bpy.data.lights.new(nm, 'AREA'); d.energy = en; d.size = sz; o = bpy.data.objects.new(nm, d); sc.collection.objects.link(o)
    o.rotation_euler = tuple(math.radians(a) for a in rot); o.location = Vector((0, D_ / 2, -H_ / 2)) + o.rotation_euler.to_matrix() @ Vector((0, 0, 8))
# -- camera: from above and to the side onto the surface -> slowly down along the face
cam_d = bpy.data.cameras.new('kamera'); cam_d.lens = 38; cam_d.dof.use_dof = not PROBA; cam_d.dof.aperture_fstop = 5.6
cam = bpy.data.objects.new('kamera', cam_d); sc.collection.objects.link(cam); sc.camera = cam
cel = bpy.data.objects.new('cel', None); sc.collection.objects.link(cel); cam_d.dof.focus_object = cel
tcn = cam.constraints.new('TRACK_TO'); tcn.target = cel; tcn.track_axis = 'TRACK_NEGATIVE_Z'; tcn.up_axis = 'UP_Y'
KAM = RAZREZ['kamera']
for t, p_, c_ in KAM:
    f = 1 + round(t * FPS); cam.location = p_; cam.keyframe_insert('location', frame=f); cel.location = c_; cel.keyframe_insert('location', frame=f)
# -- label points: the middle of each layer at the right edge of the face
tochki = {s['kl']: Vector((W_ * .28, 0, verh_sloya[i] - SL[i]['tol'] * .5)) for i, s in enumerate(SL)}
out = {}
for f in range(1, NF + 1):
    sc.frame_set(f); row = {}
    for k_, pnt in tochki.items():
        v = world_to_camera_view(sc, cam, pnt); row[k_] = [round(v.x * 1920, 1), round((1 - v.y) * 1080, 1)]
    out[f] = row
json.dump({'kadry': out}, open(f'{ROOT}/metki-S.json', 'w'))
if REZHIM == 'metki': sys.exit(0)
papka = f'{ROOT}/kadry/S' if not PROBA else f'{ROOT}/proba/S'
os.makedirs(papka, exist_ok=True)
spisok = list(range(1, NF + 1)) if REZHIM == 'vse' else [int(x) for x in REZHIM.split(',')]
for f in spisok:
    sc.frame_set(f); sc.render.filepath = f'{papka}/{f:04d}.png'
    if REZHIM == 'vse' and os.path.exists(sc.render.filepath): continue
    bpy.ops.render.render(write_still=True)
print('done S', len(spisok))
