# Clip 2: a 3D mammoth-bone dwelling (Kostenki 11, complex 1, the one under the museum roof). Blender 5.2, EEVEE.
# From the research brief: a bone ring ~9 m across, floor sunk 0.3-0.5 m, wall ~1 m above the floor; wall sections stand
# on pairs of skulls (frontal part inwards, tusk sockets down, by analogy with Mezhyrich), long bones as posts and
# ties, scapulae; along the outer edge a chain of upturned mandibles; a hearth inside; 5 storage pits around.
# No roof was found: a frame of poles with hides is shown semi-transparent as 'a scientists' guess'.
# Animation: the ring assembles section by section, then the hearth lights up and the hypothetical roof fades in.
#   blender -b --factory-startup --python zhilishche.py -- <root> <vse|1,2,3|metki> [--proba]
import bpy, bmesh, math, json, sys, os
import numpy as np
from mathutils import Vector, Matrix, Euler
from bpy_extras.object_utils import world_to_camera_view

A = sys.argv[sys.argv.index('--') + 1:]
ROOT, REZHIM = A[0], A[1]; PROBA = '--proba' in A
FPS = 30; DLIT = 16.0; NF = int(FPS * DLIT)
rng = np.random.default_rng(7)
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
    return tuple(((x + .055) / 1.055) ** 2.4 if x > .04045 else x / 12.92 for x in c) + (1,)
ease = lambda u: 0 if u <= 0 else (1 if u >= 1 else 1 - (1 - u) ** 3)

# -- ground: snow, gentle slope to the east (+X), sunken floor, earth bank, storage pits
YAMY = [(6.3, 25), (6.0, 95), (6.6, 160), (6.2, 230), (6.4, 300)]   # (radius, angle deg)
def vysota(x, y):
    r = math.hypot(x, y)
    z = -.06 * x                                                          # slope
    t = min(1, max(0, (r - 3.3) / .6)); z -= .42 * (1 - t * t * (3 - 2 * t))   # sunken floor
    z += .22 * math.exp(-((r - 4.35) / .45) ** 2)                         # earth bank under the bones
    for rr, a in YAMY:
        px, py = rr * math.cos(math.radians(a)), rr * math.sin(math.radians(a))
        z -= .35 * math.exp(-((x - px) ** 2 + (y - py) ** 2) / .28)
    return z
NG = 160 if PROBA else 320; S = 36.0
xs = np.linspace(-S / 2, S / 2, NG); X, Y = np.meshgrid(xs, xs)
Zg = np.vectorize(vysota)(X, Y) + .03 * np.sin(X * 1.7) * np.cos(Y * 1.3)
P = np.stack([X, Y, Zg], -1).reshape(-1, 3).astype(np.float32)
ids = np.arange(NG * NG).reshape(NG, NG)
F = np.stack([ids[:-1, :-1], ids[:-1, 1:], ids[1:, 1:], ids[1:, :-1]], -1).reshape(-1).astype(np.int32)
me = bpy.data.meshes.new('zemlya'); me.vertices.add(NG * NG); me.vertices.foreach_set('co', P.ravel())
nf = len(F) // 4; me.loops.add(nf * 4); me.loops.foreach_set('vertex_index', F)
me.polygons.add(nf); me.polygons.foreach_set('loop_start', np.arange(0, nf * 4, 4, dtype=np.int32))
try: me.update(calc_edges=True)
except TypeError: me.update()
me.polygons.foreach_set('use_smooth', np.ones(nf, bool))
zem = bpy.data.objects.new('zemlya', me); sc.collection.objects.link(zem)
def mat_sneg():
    m = bpy.data.materials.new('sneg'); m.use_nodes = True; N = m.node_tree.nodes; ln = m.node_tree.links.new; p = N['Principled BSDF']
    tc = N.new('ShaderNodeTexCoord'); nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = .6; nz.inputs['Detail'].default_value = 6
    ln(tc.outputs['Object'], nz.inputs['Vector'])
    # dwelling floor and pits: trodden earth with snow
    gv = N.new('ShaderNodeSeparateXYZ'); ln(tc.outputs['Object'], gv.inputs[0])
    dl = N.new('ShaderNodeVectorMath'); dl.operation = 'LENGTH'; cxy = N.new('ShaderNodeCombineXYZ'); ln(gv.outputs['X'], cxy.inputs['X']); ln(gv.outputs['Y'], cxy.inputs['Y']); ln(cxy.outputs[0], dl.inputs[0])
    mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 3.0; mr.inputs['From Max'].default_value = 3.8; ln(dl.outputs['Value'], mr.inputs['Value'])
    cr = N.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = L('#8c7d6c'); cr.color_ramp.elements[1].color = L('#eef2f6'); ln(mr.outputs[0], cr.inputs[0])
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; mx.inputs['Factor'].default_value = .25
    ln(cr.outputs[0], mx.inputs['A']); ln(nz.outputs['Color'], mx.inputs['B']); ln(mx.outputs['Result'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = .55
    try: p.inputs['Subsurface Weight'].default_value = .25; p.inputs['Subsurface Radius'].default_value = (.06, .08, .1)
    except Exception: pass
    bu = N.new('ShaderNodeBump'); n2 = N.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 9; n2.inputs['Detail'].default_value = 8
    ln(tc.outputs['Object'], n2.inputs['Vector']); ln(n2.outputs['Fac'], bu.inputs['Height']); bu.inputs['Strength'].default_value = .22; ln(bu.outputs[0], p.inputs['Normal'])
    return m
zem.data.materials.append(mat_sneg())

# -- bone materials: bone, dusted with snow on top
def mat_kost(imya, cvet_a, cvet_b, sneg=.55):
    m = bpy.data.materials.new(imya); m.use_nodes = True; N = m.node_tree.nodes; ln = m.node_tree.links.new; p = N['Principled BSDF']
    tc = N.new('ShaderNodeTexCoord'); nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 7; nz.inputs['Detail'].default_value = 6
    ln(tc.outputs['Object'], nz.inputs['Vector'])
    cr = N.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = L(cvet_a); cr.color_ramp.elements[1].color = L(cvet_b)
    cr.color_ramp.elements[0].position = .35; cr.color_ramp.elements[1].position = .7; ln(nz.outputs['Fac'], cr.inputs[0])
    ao = N.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = .1
    inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1; ln(ao.outputs['AO'], inv.inputs[1])
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; ln(inv.outputs[0], mx.inputs['Factor'])
    ln(cr.outputs[0], mx.inputs['A']); mx.inputs['B'].default_value = L('#5a4a3a')
    ge = N.new('ShaderNodeNewGeometry'); sz = N.new('ShaderNodeSeparateXYZ'); ln(ge.outputs['Normal'], sz.inputs[0])
    nsn = N.new('ShaderNodeTexNoise'); nsn.inputs['Scale'].default_value = 14; ln(tc.outputs['Object'], nsn.inputs['Vector'])
    ad = N.new('ShaderNodeMath'); ad.operation = 'ADD'; ln(sz.outputs['Z'], ad.inputs[0]); ln(nsn.outputs['Fac'], ad.inputs[1])
    mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 1.15; mr.inputs['From Max'].default_value = 1.45; ln(ad.outputs[0], mr.inputs['Value'])
    sm_ = N.new('ShaderNodeMath'); sm_.operation = 'MULTIPLY'; sm_.inputs[1].default_value = sneg; ln(mr.outputs[0], sm_.inputs[0])
    mx2 = N.new('ShaderNodeMix'); mx2.data_type = 'RGBA'; ln(sm_.outputs[0], mx2.inputs['Factor']); ln(mx.outputs['Result'], mx2.inputs['A']); mx2.inputs['B'].default_value = L('#f1f4f7')
    ln(mx2.outputs['Result'], p.inputs['Base Color']); p.inputs['Roughness'].default_value = .62
    bu = N.new('ShaderNodeBump'); nb = N.new('ShaderNodeTexNoise'); nb.inputs['Scale'].default_value = 160; nb.inputs['Detail'].default_value = 4
    ln(tc.outputs['Object'], nb.inputs['Vector']); ln(nb.outputs['Fac'], bu.inputs['Height']); bu.inputs['Strength'].default_value = .25; bu.inputs['Distance'].default_value = .002
    ln(bu.outputs[0], p.inputs['Normal']); return m
MK = mat_kost('kost', '#7d6a52', '#cdbb9a'); MK2 = mat_kost('kost_svetl', '#9a876a', '#ddd0b6'); MBIV = mat_kost('biven', '#b8a27e', '#e9dcc0', .35)

MESH = {}
def setka(imya):
    if imya in MESH: return MESH[imya]
    bpy.ops.wm.obj_import(filepath=f'{ROOT}/modeli/{imya}.obj', forward_axis='Y', up_axis='Z')
    o = bpy.context.selected_objects[0]; bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    if PROBA:
        d = o.modifiers.new('d', 'DECIMATE'); d.ratio = .25; bpy.ops.object.modifier_apply(modifier='d')
    for p_ in o.data.polygons: p_.use_smooth = True
    me_ = o.data; me_.materials.clear(); me_.materials.append(MBIV if 'biven' in imya else (MK if 'cherep' in imya or 'chelyust' in imya else MK2))
    bpy.data.objects.remove(o, do_unlink=True); MESH[imya] = me_; return me_
def oblomok(dl, r_, seed):
    rr = np.random.default_rng(seed); bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=9, radius1=r_, radius2=r_ * rr.uniform(.7, 1.0), depth=dl)
    for v in bm.verts:
        t = v.co.z / dl; ang = math.atan2(v.co.y, v.co.x)
        k = 1 + .18 * math.sin(ang * 3 + seed) + .1 * rr.standard_normal()
        if abs(t) > .45: k *= rr.uniform(.55, 1.05); v.co.z += rr.uniform(-.25, .25) * r_ * 2
        v.co.x *= k; v.co.y *= k; v.co.x += .12 * dl * (t * t - .25)
    me_ = bpy.data.meshes.new('oblomok'); bm.to_mesh(me_); bm.free()
    for p_ in me_.polygons: p_.use_smooth = True
    me_.materials.append(MK2); return me_
OBL = [oblomok(rng.uniform(.25, .6), rng.uniform(.03, .06), i) for i in range(8)]

VSE = []   # (object, appear time, kind)
def postavit(me_, loc, rot, t_poyav, vid, mash=1.0):
    o = bpy.data.objects.new(vid, me_); sc.collection.objects.link(o)
    o.rotation_mode = 'XYZ'; o.rotation_euler = rot; o.scale = (mash,) * 3
    o.location = loc; VSE.append((o, t_poyav, vid)); return o

R_W = 4.1; N_SEC = 18
T0, T1 = 1.0, 8.4                                                           # the wall assembles over this interval
for i in range(N_SEC):
    a = 2 * math.pi * i / N_SEC + rng.uniform(-.03, .03)
    t_sec = T0 + (T1 - T0) * i / N_SEC
    na_centr = math.atan2(-math.sin(a), -math.cos(a))                      # 'facing' the centre
    for k, da in enumerate((-.055, .055)):                                  # a pair of skulls: the base of a section
        aa = a + da; r = R_W + rng.uniform(-.08, .08)
        x, y = r * math.cos(aa), r * math.sin(aa)
        z = vysota(x, y) - .14
        rot = (math.radians(rng.uniform(-6, 6)), math.radians(rng.uniform(-6, 6)), na_centr - math.pi / 2 + rng.uniform(-.15, .15))
        postavit(setka('skan_cherep_d'), (x, y, z), rot, t_sec + .1 * k, 'cherep', rng.uniform(.74, .88))
    # between sections: posts of long bones, a tie on top, a scapula and fragments at the foot
    am = a + math.pi / N_SEC
    for k in range(2):
        aa = am + (k - .5) * .07; r = R_W + rng.uniform(-.1, .1); x, y = r * math.cos(aa), r * math.sin(aa)
        rot = (math.radians(rng.uniform(-8, 8)), math.radians(rng.uniform(-8, 8)), rng.uniform(0, 6.28))
        postavit(setka(('skan_bedro_d', 'skan_golen_d', 'skan_predpl_d')[int(rng.integers(0, 3))]), (x, y, vysota(x, y) - .2), rot, t_sec + .45 + .1 * k, 'stolb', rng.uniform(.9, 1.1))
    x, y = R_W * math.cos(am), R_W * math.sin(am)
    postavit(setka('skan_bedro_d'), (x, y, vysota(x, y) + .82), (0, math.radians(90), am + math.pi / 2), t_sec + .75, 'svyaz', .95)
    x, y = (R_W + .45) * math.cos(am + .05), (R_W + .45) * math.sin(am + .05)
    postavit(setka('skan_predpl_d' if i % 2 else 'skan_golen_d'), (x, y, vysota(x, y) - .05), (math.radians(-28), 0, am - math.pi / 2), t_sec + .6, 'naklon', rng.uniform(.9, 1.05))
    for k in range(6):
        aa = a + rng.uniform(-.15, .15); r = R_W + rng.uniform(-.35, .5); x, y = r * math.cos(aa), r * math.sin(aa)
        postavit(OBL[int(rng.integers(0, len(OBL)))], (x, y, vysota(x, y) + .02), tuple(rng.uniform(0, 6.28, 3)), t_sec + rng.uniform(.2, .9), 'oblomok')
# chain of upturned mandibles along the outer edge (eastern half), chin up, nested into each other
for k in range(26):
    a = math.radians(-80 + 160 * k / 25); r = 5.0 + rng.uniform(-.06, .06)
    x, y = r * math.cos(a), r * math.sin(a)
    rot = (math.radians(180 + rng.uniform(-8, 8)), math.radians(rng.uniform(-10, 10)), a + math.radians(rng.uniform(-10, 10)))
    postavit(setka('skan_chelyust_d'), (x, y, vysota(x, y) + .55), rot, 6.6 + 2.0 * k / 25, 'chelyust', rng.uniform(.9, 1.05))
# inside: scapulae on the floor
for k in range(5):
    a = rng.uniform(0, 6.28); r = rng.uniform(1.0, 2.6); x, y = r * math.cos(a), r * math.sin(a)
    postavit(setka('skan_golen_d') if k % 2 else OBL[k], (x, y, vysota(x, y) + .1), (math.radians(90), 0, rng.uniform(0, 6.28)), 8.8 + .15 * k, 'kost_pol', .9)
for k, (bx_, by_, ug_) in enumerate(((-1.6, .9, 35), (1.2, -1.5, -110))):
    postavit(setka('skan_bivenR_d' if k == 0 else 'skan_bivenL_d'), (bx_, by_, vysota(bx_, by_) - .05), (math.radians(90), 0, math.radians(ug_)), 9.0 + .3 * k, 'biven', .95)
# bones in the pits
for rr, ag in YAMY:
    for k in range(4):
        x = rr * math.cos(math.radians(ag)) + rng.uniform(-.3, .3); y = rr * math.sin(math.radians(ag)) + rng.uniform(-.3, .3)
        postavit(OBL[int(rng.integers(0, len(OBL)))], (x, y, vysota(x, y) + .03), tuple(rng.uniform(0, 6.28, 3)), 9.2, 'oblomok')

# -- appear animation: a bone drops into place from above (~0.6 s) and settles slightly
for o, t, vid in VSE:
    f0 = 1 + round(t * FPS); f1 = f0 + 18
    cel_ = o.location.copy(); s_ = o.scale.copy()
    o.location = cel_ + Vector((0, 0, 1.4)); o.scale = s_ * .001; o.keyframe_insert('location', frame=max(1, f0 - 1)); o.keyframe_insert('scale', frame=max(1, f0 - 1))
    o.scale = s_; o.keyframe_insert('scale', frame=f0 + 2)
    o.location = cel_; o.keyframe_insert('location', frame=f1)

# -- hearth: stones, fire (emission) and light
ochag_c = Vector((0, 0, vysota(0, 0)))
for k in range(9):
    a = 2 * math.pi * k / 9; bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=2, radius=.12)
    for v in bm.verts: v.co.z *= .6
    me_ = bpy.data.meshes.new('kamen'); bm.to_mesh(me_); bm.free(); me_.materials.append(MK)
    o = bpy.data.objects.new('kamen', me_); sc.collection.objects.link(o); o.location = ochag_c + Vector((.45 * math.cos(a), .45 * math.sin(a), .03))
mf = bpy.data.materials.new('ogon'); mf.use_nodes = True; Nf = mf.node_tree.nodes
for x in list(Nf):
    if x.type != 'OUTPUT_MATERIAL': Nf.remove(x)
emf = Nf.new('ShaderNodeEmission'); emf.inputs[0].default_value = L('#ff8a2a'); emf.inputs[1].default_value = 0
mf.node_tree.links.new(emf.outputs[0], Nf['Material Output'].inputs[0])
for f, e in ((1 + round(9.6 * FPS), 0), (1 + round(10.4 * FPS), 9)): emf.inputs[1].default_value = e; emf.inputs[1].keyframe_insert('default_value', frame=f)
for k in range(5):
    bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=.12, radius2=0, depth=rng.uniform(.35, .6))
    me_ = bpy.data.meshes.new('plamya'); bm.to_mesh(me_); bm.free(); me_.materials.append(mf)
    o = bpy.data.objects.new('plamya', me_); sc.collection.objects.link(o); o.location = ochag_c + Vector((rng.uniform(-.12, .12), rng.uniform(-.12, .12), .22)); o.rotation_euler = (rng.uniform(-.2, .2), rng.uniform(-.2, .2), 0)
lp = bpy.data.lights.new('ochag', 'POINT'); lp.color = (1.0, .55, .2); lp.shadow_soft_size = .3
lo = bpy.data.objects.new('ochag', lp); sc.collection.objects.link(lo); lo.location = ochag_c + Vector((0, 0, .5))
for t in np.arange(9.6, DLIT + .2, .2):
    lp.energy = 0 if t < 9.7 else (220 + 70 * math.sin(t * 9.1) + 40 * math.sin(t * 23.7)) * ease((t - 9.6) / .8); lp.keyframe_insert('energy', frame=1 + round(t * FPS))

# -- hypothetical roof: poles in a cone + hides, semi-transparent
mh = bpy.data.materials.new('shkury'); mh.use_nodes = True; Nh = mh.node_tree.nodes; lh = mh.node_tree.links.new; ph = Nh['Principled BSDF']
ph.inputs['Base Color'].default_value = L('#8a6a4c'); ph.inputs['Roughness'].default_value = .9
tr = Nh.new('ShaderNodeBsdfTransparent'); mxh = Nh.new('ShaderNodeMixShader'); lh(tr.outputs[0], mxh.inputs[1]); lh(ph.outputs[0], mxh.inputs[2]); lh(mxh.outputs[0], Nh['Material Output'].inputs[0])
mxh.inputs[0].default_value = 0
for f, v in ((1 + round(12.0 * FPS), 0), (1 + round(13.6 * FPS), .5)): mxh.inputs[0].default_value = v; mxh.inputs[0].keyframe_insert('default_value', frame=f)
try: mh.surface_render_method = 'DITHERED'
except Exception: pass
bm = bmesh.new(); res = bmesh.ops.create_cone(bm, cap_ends=False, segments=48, radius1=R_W + .1, radius2=.35, depth=2.6)
bmesh.ops.translate(bm, verts=res['verts'], vec=(0, 0, .9 + 1.3))
for v in bm.verts:   # hides sag between the poles
    a = math.atan2(v.co.y, v.co.x); h = (v.co.z - .9) / 2.6
    if 0 < h < .95: r = math.hypot(v.co.x, v.co.y); k = 1 - .05 * abs(math.sin(a * 8)) * math.sin(h * math.pi); v.co.x *= k; v.co.y *= k
# cut-out on the camera side (azimuth ~290 deg): the 'guess' roof does not hide how the dwelling is built
uz = [f for f in bm.faces if abs(((math.degrees(math.atan2(f.calc_center_median().y, f.calc_center_median().x)) - 290 + 180) % 360) - 180) < 62]
bmesh.ops.delete(bm, geom=uz, context='FACES')
me_ = bpy.data.meshes.new('krysha'); bm.to_mesh(me_); bm.free(); me_.materials.append(mh)
for p_ in me_.polygons: p_.use_smooth = True
krysha = bpy.data.objects.new('krysha', me_); sc.collection.objects.link(krysha)
mw = bpy.data.materials.new('zherdi'); mw.use_nodes = True; mw.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = L('#4a3828')
for k in range(8):
    a = 2 * math.pi * k / 8 + .2; bm = bmesh.new(); bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=.05, radius2=.03, depth=3.4)
    me_ = bpy.data.meshes.new('zherd'); bm.to_mesh(me_); bm.free(); me_.materials.append(mw)
    o = bpy.data.objects.new('zherd', me_); sc.collection.objects.link(o)
    bot = Vector(((R_W - .1) * math.cos(a), (R_W - .1) * math.sin(a), .8)); top = Vector((0, 0, 3.6))
    o.location = (bot + top) / 2; o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = Vector((0, 0, 1)).rotation_difference((top - bot).normalized())
    for f, s_ in ((1 + round((11.2 + .1 * k) * FPS), .001), (1 + round((12.0 + .1 * k) * FPS), 1)): o.scale = (1, 1, s_); o.keyframe_insert('scale', frame=f)

# -- distant hills in haze, sky, sun
MH = bpy.data.materials.new('holmy'); MH.use_nodes = True; Nm = MH.node_tree.nodes; lm = MH.node_tree.links.new; pm = Nm['Principled BSDF']
pm.inputs['Base Color'].default_value = L('#e6ebf0'); pm.inputs['Roughness'].default_value = .7
cdm = Nm.new('ShaderNodeCameraData'); exm = Nm.new('ShaderNodeMath'); exm.operation = 'MULTIPLY'; exm.inputs[1].default_value = -.012; lm(cdm.outputs['View Distance'], exm.inputs[0])
epm = Nm.new('ShaderNodeMath'); epm.operation = 'EXPONENT'; lm(exm.outputs[0], epm.inputs[0])
ivm = Nm.new('ShaderNodeMath'); ivm.operation = 'SUBTRACT'; ivm.inputs[0].default_value = 1; lm(epm.outputs[0], ivm.inputs[1])
fgm = Nm.new('ShaderNodeEmission'); fgm.inputs[0].default_value = L('#c9d3dc'); mxm = Nm.new('ShaderNodeMixShader')
lm(ivm.outputs[0], mxm.inputs[0]); lm(pm.outputs[0], mxm.inputs[1]); lm(fgm.outputs[0], mxm.inputs[2]); lm(mxm.outputs[0], Nm['Material Output'].inputs[0])
for k in range(9):
    a = math.radians(rng.uniform(0, 360)); d = rng.uniform(95, 170)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=1, location=(d * math.cos(a), d * math.sin(a), -7))
    o = bpy.context.object; o.scale = (rng.uniform(30, 55), rng.uniform(30, 55), rng.uniform(9, 13)); o.data.materials.append(MH)
    for p_ in o.data.polygons: p_.use_smooth = True
w = bpy.data.worlds.new('mir'); sc.world = w; w.use_nodes = True; wn = w.node_tree.nodes; bg = wn['Background']
wtc = wn.new('ShaderNodeTexCoord'); wsz = wn.new('ShaderNodeSeparateXYZ'); w.node_tree.links.new(wtc.outputs['Generated'], wsz.inputs[0])
wcr = wn.new('ShaderNodeValToRGB'); wcr.color_ramp.elements[0].color = L('#d3dce4'); wcr.color_ramp.elements[1].color = L('#8aa2b8'); wcr.color_ramp.elements[1].position = .4
w.node_tree.links.new(wsz.outputs['Z'], wcr.inputs[0]); w.node_tree.links.new(wcr.outputs[0], bg.inputs[0]); bg.inputs[1].default_value = .9
sd = bpy.data.lights.new('solnce', 'SUN'); sd.energy = 3.6; sd.color = (1.0, .9, .78); sd.angle = math.radians(1.5)
so = bpy.data.objects.new('solnce', sd); sc.collection.objects.link(so); so.rotation_euler = (math.radians(90 - 14), 0, math.radians(320))

# -- camera: orbit around the dwelling, closer towards the end
cam_d = bpy.data.cameras.new('kamera'); cam_d.lens = 32; cam_d.clip_start = .05; cam_d.clip_end = 600
cam_d.dof.use_dof = not PROBA; cam_d.dof.aperture_fstop = 8
cam = bpy.data.objects.new('kamera', cam_d); sc.collection.objects.link(cam); sc.camera = cam
cel = bpy.data.objects.new('cel', None); sc.collection.objects.link(cel); cam_d.dof.focus_object = cel
tc = cam.constraints.new('TRACK_TO'); tc.target = cel; tc.track_axis = 'TRACK_NEGATIVE_Z'; tc.up_axis = 'UP_Y'
for t in np.arange(0, DLIT + .01, .5):
    u = t / DLIT; a = math.radians(215 + 95 * u); r = 12.5 - 4.0 * u; h = 6.0 - 2.6 * u
    f = 1 + round(t * FPS); cam.location = (r * math.cos(a), r * math.sin(a), h); cam.keyframe_insert('location', frame=f)
    cel.location = (0, 0, .35 + .4 * u); cel.keyframe_insert('location', frame=f)

# -- label points
TOCH = {'cherep': [o for o, t, v in VSE if v == 'cherep'][24].location, 'stolb': [o for o, t, v in VSE if v == 'stolb'][25].location + Vector((0, 0, .7)),
        'chelyust': [o for o, t, v in VSE if v == 'chelyust'][1].location, 'ochag': ochag_c + Vector((0, 0, .3)),
        'yama': Vector((YAMY[4][0] * math.cos(math.radians(YAMY[4][1])), YAMY[4][0] * math.sin(math.radians(YAMY[4][1])), -.1)), 'krysha': Vector((1.2, -1.0, 2.6))}
TOCH.update({f'yama{i}': Vector((rr * math.cos(math.radians(ag)), rr * math.sin(math.radians(ag)), -.1)) for i, (rr, ag) in enumerate(YAMY)})
TOCH.update({f'chel{i}': o.location.copy() for i, o in enumerate([o for o, t, v in VSE if v == 'chelyust'])})
TOCH = {k: Vector(v) for k, v in TOCH.items()}
out = {}
for f in range(1, NF + 1):
    sc.frame_set(f); row = {}
    for k, p_ in TOCH.items():
        v = world_to_camera_view(sc, cam, p_); row[k] = [round(v.x * 1920, 1), round((1 - v.y) * 1080, 1)]
    out[f] = row
json.dump({'kadry': out}, open(f'{ROOT}/metki-H.json', 'w'))
print('bones', len(VSE))
if REZHIM == 'metki': sys.exit(0)
papka = f'{ROOT}/kadry/H' if not PROBA else f'{ROOT}/proba/H'
os.makedirs(papka, exist_ok=True)
spisok = list(range(1, NF + 1)) if REZHIM == 'vse' else [int(x) for x in REZHIM.split(',')]
for f in spisok:
    sc.frame_set(f); sc.render.filepath = f'{papka}/{f:04d}.png'
    if REZHIM == 'vse' and os.path.exists(sc.render.filepath): continue
    bpy.ops.render.render(write_still=True)
print('done H', len(spisok))
