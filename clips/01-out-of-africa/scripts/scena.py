# Clip 1 'Out of Africa' globe scene: real relief, migration paths, find-site markers. Blender 5.2, EEVEE.
#   blender -b --factory-startup --python scena.py -- <clip root> [frames 1,2,3 | vse | metki] [--proba]
# Frames (PNG) -> <root>/kadry/, on-screen marker positions -> <root>/metki.json (labels are drawn later by post.py).
import bpy, bmesh, math, json, sys, os
from mathutils import Vector, Euler, Quaternion
from bpy_extras.object_utils import world_to_camera_view

A = sys.argv[sys.argv.index('--') + 1:]
ROOT = A[0]; REZHIM = A[1] if len(A) > 1 else 'proba'; PROBA = '--proba' in A
FPS, DLIT = 30, 69.0
NF = int(FPS * DLIT)
R_GL = 1.0

sc = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc.render.engine = 'BLENDER_EEVEE'
sc.render.resolution_x, sc.render.resolution_y = (1920, 1080)
sc.render.resolution_percentage = 50 if PROBA else 100
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, NF
sc.eevee.taa_render_samples = 24 if PROBA else 32
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.render.film_transparent = False
sc.render.image_settings.file_format = 'PNG'

def L(h):  # sRGB hex -> linear
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((x + .055) / 1.055) ** 2.4 if x > .04045 else x / 12.92 for x in c) + (1,)

def ll(lat, lon, r=1.0):
    la, lo = math.radians(lat), math.radians(lon)
    return Vector((r * math.cos(la) * math.cos(lo), r * math.cos(la) * math.sin(lo), r * math.sin(la)))

# -- world: dark blue-grey background
w = bpy.data.worlds.new('mir'); sc.world = w; w.use_nodes = True
bg = w.node_tree.nodes['Background']; bg.inputs[0].default_value = L('#0c161b'); bg.inputs[1].default_value = 1.0

# -- globe: custom grid with UV = (longitude, latitude) so markers and texture line up exactly
NU, NV = (720, 360) if PROBA else (1440, 720)
me = bpy.data.meshes.new('globus'); bm = bmesh.new()
uvl = bm.loops.layers.uv.new('UV')
verts = []
for j in range(NV + 1):
    lat = -90 + 180 * j / NV
    row = []
    for i in range(NU + 1):
        lon = -180 + 360 * i / NU
        row.append(bm.verts.new(ll(lat, lon)))
    verts.append(row)
for j in range(NV):
    for i in range(NU):
        f = bm.faces.new((verts[j][i], verts[j][i + 1], verts[j + 1][i + 1], verts[j + 1][i]))
        for lp, (ii, jj) in zip(f.loops, ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1))):
            lp[uvl].uv = (ii / NU, jj / NV)
bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
bm.to_mesh(me); bm.free()
for p in me.polygons: p.use_smooth = True
glob = bpy.data.objects.new('globus', me); sc.collection.objects.link(glob)
img_h = bpy.data.images.load(f'{ROOT}/tex/vysota_8192.png'); img_h.colorspace_settings.name = 'Non-Color'
tx = bpy.data.textures.new('vysota', 'IMAGE'); tx.image = img_h; tx.extension = 'EXTEND'
dm = glob.modifiers.new('rel_ef', 'DISPLACE'); dm.texture = tx; dm.texture_coords = 'UV'; dm.uv_layer = 'UV'
dm.direction = 'NORMAL'; dm.mid_level = 1000 / 9000; dm.strength = 0.016

mt = bpy.data.materials.new('globus'); mt.use_nodes = True; nt = mt.node_tree; N = nt.nodes
pb = N['Principled BSDF']
uvn = N.new('ShaderNodeUVMap'); uvn.uv_map = 'UV'
tc = N.new('ShaderNodeTexImage'); tc.image = bpy.data.images.load(f'{ROOT}/tex/cvet_8192.png'); tc.interpolation = 'Cubic'
to = N.new('ShaderNodeTexImage'); to.image = bpy.data.images.load(f'{ROOT}/tex/okean_8192.png'); to.image.colorspace_settings.name = 'Non-Color'
th = N.new('ShaderNodeTexImage'); th.image = img_h
for t in (tc, to, th): nt.links.new(uvn.outputs[0], t.inputs[0])
nt.links.new(tc.outputs[0], pb.inputs['Base Color'])
nt.links.new(tc.outputs[0], pb.inputs['Emission Color']); pb.inputs['Emission Strength'].default_value = .17
rough = N.new('ShaderNodeMapRange'); rough.inputs[3].default_value = .9; rough.inputs[4].default_value = .6
nt.links.new(to.outputs[0], rough.inputs[0]); nt.links.new(rough.outputs[0], pb.inputs['Roughness'])
spec = N.new('ShaderNodeMapRange'); spec.inputs[3].default_value = .1; spec.inputs[4].default_value = .3
nt.links.new(to.outputs[0], spec.inputs[0]); nt.links.new(spec.outputs[0], pb.inputs['Specular IOR Level'])
bump = N.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = .35; bump.inputs['Distance'].default_value = .004
nt.links.new(th.outputs[0], bump.inputs['Height']); nt.links.new(bump.outputs[0], pb.inputs['Normal'])
glob.data.materials.append(mt)

# -- atmosphere: thin rim glow
atm = bpy.data.objects.new('atmosfera', bpy.data.meshes.new('atm')); sc.collection.objects.link(atm)
bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=128, v_segments=64, radius=1.03); bm.to_mesh(atm.data); bm.free()
for p in atm.data.polygons: p.use_smooth = True
ma = bpy.data.materials.new('atm'); ma.use_nodes = True; na = ma.node_tree; Na = na.nodes
for n in list(Na):
    if n.type != 'OUTPUT_MATERIAL': Na.remove(n)
lw = Na.new('ShaderNodeLayerWeight'); lw.inputs[0].default_value = .18
cr = Na.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].position = .35; cr.color_ramp.elements[0].color = (0, 0, 0, 1)
cr.color_ramp.elements[1].position = 1.0; cr.color_ramp.elements[1].color = (1, 1, 1, 1)
em = Na.new('ShaderNodeEmission'); em.inputs[0].default_value = L('#9cc9d8'); em.inputs[1].default_value = .9
tr = Na.new('ShaderNodeBsdfTransparent'); mix = Na.new('ShaderNodeMixShader')
na.links.new(lw.outputs['Facing'], cr.inputs[0]); na.links.new(cr.outputs[0], mix.inputs[0])
na.links.new(tr.outputs[0], mix.inputs[1]); na.links.new(em.outputs[0], mix.inputs[2]); na.links.new(mix.outputs[0], Na['Material Output'].inputs[0])
ma.surface_render_method = 'BLENDED'; ma.use_backface_culling = True
atm.data.materials.append(ma)

# -- camera on a pivot: the pivot faces (lat, lon), the camera sits at distance dist with a tilt
piv = bpy.data.objects.new('sharnir', None); sc.collection.objects.link(piv); piv.rotation_mode = 'XYZ'
cam_d = bpy.data.cameras.new('kamera'); cam_d.lens = 50; cam_d.clip_start = .01; cam_d.clip_end = 100
cam = bpy.data.objects.new('kamera', cam_d); sc.collection.objects.link(cam); cam.parent = piv; sc.camera = cam
cel = bpy.data.objects.new('cel', None); sc.collection.objects.link(cel); cel.parent = piv
tc_ = cam.constraints.new('TRACK_TO'); tc_.target = cel; tc_.track_axis = 'TRACK_NEGATIVE_Z'; tc_.up_axis = 'UP_Y'
# the sun travels with the camera: light always from the upper left, no night side in frame
def svet(name, energy, color, otkuda):
    d = bpy.data.lights.new(name, 'SUN'); d.energy = energy; d.angle = math.radians(2); d.color = color
    o = bpy.data.objects.new(name, d); sc.collection.objects.link(o); o.parent = piv; o.rotation_mode = 'QUATERNION'
    o.rotation_quaternion = Vector((0, 0, -1)).rotation_difference(-Vector(otkuda).normalized()); return o
sun = svet('solnce', 3.6, (1.0, .95, .88), (1.0, -0.75, 0.85))
fill = svet('podsvet', .6, (.72, .84, 1.0), (0.6, 1.0, -0.4))

# camera keys: (sec, lat, lon, distance to centre, tilt deg[, side offset, lift])
# While a label is visible its marker moves no faster than ~40 px/s; moves go through a wide shot; the finale flies on to the Americas.
KAM = [(0, 8, 14, 6.8, 0, -.62), (4.5, 6, 20, 6.0, 4, -.5), (9, 0, 24, 3.6, 12), (12.5, -20, 25, 2.7, 20), (15.6, -19, 26, 2.62, 20),
       (19.0, -5, 34, 2.5, 22), (24.6, -4, 36, 2.45, 22), (28.6, 6, 76, 4.8, 10), (32.2, 14, 110, 3.85, 16), (37.8, 16, 110, 4.1, 12),
       # flight to Europe: 5 s through a medium shot, the push-in is stretched
       (40.2, 32, 62, 5.4, 7), (42.0, 44, 22, 4.6, 12), (43.8, 46, 14, 3.3, 18), (45.9, 46, 11, 3.2, 19),
       # H. sapiens: 3 s back to East Africa, then the camera follows the path north
       (48.8, 24, 31, 4.0, 8), (51.1, 33, 28, 4.2, 10), (53.6, 41, 12, 3.9, 13), (54.8, 41, 11, 3.85, 13),
       # pull-out centred on France (the Cro-Magnon label barely moves), then the camera leads the paths:
       # Asia and Australia -> Beringia -> the Americas; the globe is lifted above the end captions
       (56.2, 42, 14, 5.2, 8, 0, -.08), (58.6, 20, 78, 7.8, 3, 0, -.16), (60.4, 13, 108, 8.4, 2, 0, -.18),
       (62.8, 50, 180, 8.4, 1, 0, -.2), (65.4, 22, 258, 7.8, 0, 0, -.2), (69.0, 21, 261, 7.7, 0, 0, -.2)]
def kluch(t, lat, lon, dist, naklon, sdvig=0.0, podyom=0.0):
    f = 1 + round(t * FPS)
    piv.rotation_euler = Euler((0, math.radians(-lat), math.radians(lon)), 'XYZ'); piv.keyframe_insert('rotation_euler', frame=f)
    a = math.radians(naklon)
    # camera is offset south and looks slightly north: north at the top of the frame, planet edge at the top, like a map
    cam.location = (dist * math.cos(a), 0, -dist * math.sin(a) * .55); cam.keyframe_insert('location', frame=f)
    # sdvig: sideways look offset (-Y = left), the globe moves the other way to leave room for a title; podyom < 0 lifts the globe
    cel.location = (R_GL * .98, sdvig, podyom); cel.keyframe_insert('location', frame=f)
for k in KAM: kluch(*k)

cl = lambda x, a=0., b=1.: max(a, min(b, x))
sgl = lambda u: u * u * (3 - 2 * u)
def F(t): return 1 + round(t * FPS)

# -- 'light' material: colour and emission strength, opacity k (animated), fades out past the horizon
def mat_svet(name, hexc, s, alfa=1.0, gorizont=(.0, .12)):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; n = nt.nodes
    for x in list(n):
        if x.type != 'OUTPUT_MATERIAL': n.remove(x)
    e = n.new('ShaderNodeEmission'); e.inputs[0].default_value = L(hexc); e.inputs[1].default_value = s
    tr = n.new('ShaderNodeBsdfTransparent'); mx = n.new('ShaderNodeMixShader')
    geo = n.new('ShaderNodeNewGeometry')
    nrm = n.new('ShaderNodeVectorMath'); nrm.operation = 'NORMALIZE'
    dot = n.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
    mr = n.new('ShaderNodeMapRange'); mr.inputs[1].default_value, mr.inputs[2].default_value = gorizont; mr.clamp = True
    k = n.new('ShaderNodeValue'); k.name = 'k'; k.outputs[0].default_value = alfa
    mul = n.new('ShaderNodeMath'); mul.operation = 'MULTIPLY'
    ln = nt.links.new
    ln(geo.outputs['Position'], nrm.inputs[0]); ln(nrm.outputs['Vector'], dot.inputs[0]); ln(geo.outputs['Incoming'], dot.inputs[1])
    # a point raised above the sphere leaves the disc already at dot < sqrt(1 - 1/r^2): fade relative to that threshold
    dl_ = n.new('ShaderNodeVectorMath'); dl_.operation = 'LENGTH'; ln(geo.outputs['Position'], dl_.inputs[0])
    p2 = n.new('ShaderNodeMath'); p2.operation = 'POWER'; p2.inputs[1].default_value = -2; ln(dl_.outputs['Value'], p2.inputs[0])
    sb = n.new('ShaderNodeMath'); sb.operation = 'SUBTRACT'; sb.inputs[0].default_value = 1; ln(p2.outputs[0], sb.inputs[1])
    mx0 = n.new('ShaderNodeMath'); mx0.operation = 'MAXIMUM'; mx0.inputs[1].default_value = 0; ln(sb.outputs[0], mx0.inputs[0])
    sq = n.new('ShaderNodeMath'); sq.operation = 'SQRT'; ln(mx0.outputs[0], sq.inputs[0])
    rz = n.new('ShaderNodeMath'); rz.operation = 'SUBTRACT'; ln(dot.outputs['Value'], rz.inputs[0]); ln(sq.outputs[0], rz.inputs[1])
    ln(rz.outputs[0], mr.inputs[0]); ln(mr.outputs[0], mul.inputs[0]); ln(k.outputs[0], mul.inputs[1])
    ln(mul.outputs[0], mx.inputs[0]); ln(tr.outputs[0], mx.inputs[1]); ln(e.outputs[0], mx.inputs[2])
    ln(mx.outputs[0], n['Material Output'].inputs[0])
    m.surface_render_method = 'BLENDED'; m.use_backface_culling = True
    return m
def k_kluchi(m, pary):
    k = m.node_tree.nodes['k'].outputs[0]
    for t, v in pary: k.default_value = v; k.keyframe_insert('default_value', frame=F(t))

# -- migration paths: over land (checked against the ocean mask and elevation), arcs above the surface, drawn over time
VYS, GORB = .0075, .006
def slerp(a, b, t):
    a, b = a.normalized(), b.normalized(); om = math.acos(max(-1, min(1, a.dot(b))))
    if om < 1e-6: return a
    return (a * math.sin((1 - t) * om) + b * math.sin(t * om)) / math.sin(om)
def napravleniya(U, n_seg=24):
    # Chaikin smoothing of the waypoints on the sphere -> dense great-circle sampling
    for _ in range(4):
        V = [U[0]]
        for p, q in zip(U[:-1], U[1:]): V += [(p * .75 + q * .25).normalized(), (p * .25 + q * .75).normalized()]
        V.append(U[-1]); U = V
    D = []
    for p, q in zip(U[:-1], U[1:]):
        for k in range(n_seg): D.append(slerp(p, q, k / n_seg))
    D.append(U[-1]); return D
def dliny(P):
    dl = [0.0]
    for a, b in zip(P[:-1], P[1:]): dl.append(dl[-1] + (b - a).length)
    return dl
def ss_obr(f):  # inverse of smoothstep
    a, b = 0.0, 1.0
    for _ in range(40):
        m = (a + b) / 2
        if sgl(m) < f: a = m
        else: b = m
    return (a + b) / 2
HOD = {'ss': sgl, 'mix': lambda x: (x + sgl(x)) / 2}   # how the path head advances: eased, or more even (the long path to the Americas)

M_ER = mat_svet('put-erectus', '#c0602a', 1.0)                       # H. erectus: flat terracotta, no glow
M_ER_H = mat_svet('put-erectus-halo', '#c0602a', 1.0, .2)
M_SAP = mat_svet('put-sapiens', '#f6d27e', 1.25)                    # H. sapiens: glowing gold
M_SAP_H = mat_svet('put-sapiens-halo', '#f6d27e', 1.0, .24)
# H. erectus paths dim when the story moves to Europe and come back in the summary shot
k_kluchi(M_ER, [(38.2, 1.0), (39.7, .45), (60.4, .45), (61.6, .12)])
k_kluchi(M_ER_H, [(38.2, .2), (39.7, .09), (60.4, .09), (61.6, .03)])
k_kluchi(M_SAP_H, [(60.4, .24), (61.6, .36)])
_es = M_SAP.node_tree.nodes['Emission'].inputs[1]
for _t, _v in ((60.4, 1.25), (61.6, 1.7)): _es.default_value = _v; _es.keyframe_insert('default_value', frame=F(_t))

PUTI = [  # name, waypoints, start (None = when the parent head passes the branch point), end, species, parent, easing
    # every path was checked with proverka_putey.py (data/puti.json): over land (water only at straits, the Sunda shelf, the crossings
    # to Australia and the Bering Strait), above 2500 m only in a few short stretches (East African highlands, Zagros, Alaska).
    # The path to the Americas starts last, as it was settled last.
    ('er-yava', [(-3, 36), (9, 37), (20, 32.5), (30, 31.5), (33, 40), (30, 50), (27, 58), (26, 66), (26, 76), (25.5, 86), (22, 93), (19.5, 96.3), (16, 98.6), (12.5, 99.4), (10.5, 98.9), (8.5, 99.3), (6, 100.6), (3, 101.8), (1, 103), (-3, 104.5), (-5.8, 105.7), (-6.6, 107.5), (-7.4, 111.4)], 25.2, 31.8, 'er', None, 'ss'),
    ('er-kitay', [(19.5, 96.3), (20.6, 100), (21, 104), (21.5, 107), (22.6, 110.5), (24, 113.2), (27.5, 114), (30.5, 114.2), (34, 114.3), (37, 115), (39.7, 115.9)], None, 32.9, 'er', 'er-yava', 'ss'),
    ('sap-evropa', [(5.4, 35.9), (9, 35), (13, 34), (17, 33.5), (21, 32), (26, 32.6), (30, 31.3), (30.6, 32.3), (30.8, 34), (32.5, 35.2), (34.5, 36.5), (36.8, 36.4), (37.3, 35), (37.7, 34.4), (38.6, 33), (39.8, 30.5), (41, 28.5), (43.5, 24), (45, 19), (48, 14), (48, 8), (44.9, 1)], 48.2, 53.6, 'sap', None, 'ss'),
    ('sap-aziya', [(34.5, 36.5), (33.5, 41), (31.5, 46), (31.5, 49), (29.5, 52.5), (28, 56), (26, 64), (23, 78), (23.8, 86), (23.2, 91.5), (19.8, 95.6), (16.5, 98.4), (12.8, 99.5), (10.5, 98.9), (8.5, 99.3), (6.3, 100.7), (3.3, 101.6), (1.2, 103.2), (-2, 104), (-5.5, 105.4), (-6.9, 108), (-7.6, 111.5), (-8.5, 117), (-9, 124), (-14, 131), (-22, 133)], 55.0, 61.0, 'sap', 'sap-evropa', 'mix'),
    ('sap-amerika', [(33.5, 41), (34.6, 44), (34.4, 47), (35, 49), (35.2, 51.5), (35.5, 53.5), (36.1, 55.5), (36.2, 57.7), (35.6, 59.3), (36, 61), (37.6, 61.8), (42, 67), (45, 75), (46.5, 79.5), (46, 81.6), (45.3, 82.6), (45.2, 86.5), (45.2, 90.5), (44.6, 93.5), (43.6, 96.5), (42.6, 100), (43.6, 104.5), (46, 107), (49.5, 107.2), (52, 108), (58, 130), (66, 172), (66, -168), (63, -155), (62, -135), (55, -118), (49, -110), (40, -100), (30, -99), (22.5, -98.5), (19.5, -97), (18.2, -95.5), (17.6, -93.5), (17.2, -91), (15.5, -88.5), (13.8, -86.5), (12.6, -85.1), (11.3, -84.4), (10.2, -83.7), (9.3, -82.4), (8.9, -80.5), (8.9, -79.3), (8.4, -77.6), (8.8, -75.5), (9.5, -74.2), (10.4, -73.2), (11.3, -72.5), (11.2, -71), (11, -69.5), (10.2, -68), (8.5, -66.5), (4, -64.5), (-0.5, -62), (-3.5, -60)], 57.4, 66.6, 'sap', 'sap-aziya', 'mix'),
]
GOTOVO = {}   # name -> (3D points, lengths, t0, t1, easing)
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'
for name, pts, t0, t1, vid, rod, hod in PUTI:
    U = [ll(la, lo).normalized() for la, lo in pts]
    h0 = 0.0
    if rod:
        # a branch starts exactly on its parent arc: nearest parent point, its height, the moment the parent head passes it
        Pr, dlr, r0, r1, rh = GOTOVO[rod]
        k = min(range(len(Pr)), key=lambda i: (Pr[i].normalized() - U[0]).length)
        U[0] = Pr[k].normalized(); h0 = Pr[k].length - (R_GL + VYS)
        xr = ss_obr(dlr[k] / dlr[-1]) if rh == 'ss' else dlr[k] / dlr[-1]
        t_pr = r0 + (r1 - r0) * xr
        if t0 is None or t0 < t_pr: t0 = t_pr + .05
        print(f'branch {name}: from {rod}, offset {math.degrees((Pr[k].normalized() - ll(*pts[0]).normalized()).length):.2f}°, start {t0:.2f} s')
    D = napravleniya(U)
    dl = [0.0]
    for p, q in zip(D[:-1], D[1:]): dl.append(dl[-1] + p.angle(q))
    tot = dl[-1]; amp = GORB * min(1.0, tot / 1.2)
    P = []
    for u, d in zip(D, dl):
        s = d / tot; gorb = amp * math.sin(math.pi * s) ** .8
        w = 1 - sgl(cl(s / .35))
        P.append(u * ((R_GL + VYS + gorb + (h0 - gorb) * w) if rod else (R_GL + VYS + gorb)))
    dlP = dliny(P); GOTOVO[name] = (P, dlP, t0, t1, hod)
    m, mh = (M_SAP, M_SAP_H) if vid == 'sap' else (M_ER, M_ER_H)
    f0, f1 = F(t0), F(t1)
    for imya, bev, mat in ((name, .0026 if vid == 'sap' else .0022, m), (name + '-halo', .0085 if vid == 'sap' else .0068, mh)):
        cu = bpy.data.curves.new(imya, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = bev; cu.bevel_resolution = 3
        cu.use_fill_caps = True; cu.bevel_factor_mapping_end = 'SPLINE'
        sp = cu.splines.new('POLY'); sp.points.add(len(P) - 1)
        for p, v in zip(sp.points, P): p.co = (v.x, v.y, v.z, 1)
        ob = bpy.data.objects.new(imya, cu); sc.collection.objects.link(ob); cu.materials.append(mat)
        for f in range(f0 - 1, f1 + 2):
            cu.bevel_factor_end = HOD[hod](cl((f - f0) / (f1 - f0))); cu.keyframe_insert('bevel_factor_end', frame=f)
    # path 'head': a glowing dot in front of the line, moving along the same length
    hd = bpy.data.objects.new(name + '-golova', bpy.data.meshes.new(name + '-g')); sc.collection.objects.link(hd)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=.0072 if vid == 'sap' else .006)
    bm.to_mesh(hd.data); bm.free(); hd.data.materials.append(m)
    for f in range(f0 - 1, f1 + 2):
        u = HOD[hod](cl((f - f0) / (f1 - f0)))
        s = u * dlP[-1]; k = next((i for i in range(1, len(dlP)) if dlP[i] >= s), len(dlP) - 1)
        tt = (s - dlP[k - 1]) / max(1e-9, dlP[k] - dlP[k - 1]); hd.location = P[k - 1].lerp(P[k], tt)
        hd.keyframe_insert('location', frame=f)
        sc_ = 1.0 if f0 <= f <= f1 else 0.0
        hd.scale = (sc_, sc_, sc_); hd.keyframe_insert('scale', frame=f)
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'BEZIER'

# -- find-site markers: ring + dot; appear without overshoot, three calm pulses, dim after their section
METKI = [  # name, lat, lon, appear time, dim time (None = stays lit to the end)
    ('avstralopitek', -27.6, 24.7, 11.0, 25.0), ('olduvay', -2.99, 35.35, 18.6, 25.0), ('yava', -7.37, 111.36, 31.6, 38.2),
    ('kitay', 39.69, 115.93, 33.0, 38.2), ('neandertal', 51.23, 6.95, 43.2, 46.6), ('kromanon', 44.94, 1.01, 53.5, None),
]
# extinct species stay dim: by the end only our species glows
def kolco_mesh(name):
    me_ = bpy.data.meshes.new(name); bm = bmesh.new()
    for k in range(48):
        a1, a2 = 2 * math.pi * k / 48, 2 * math.pi * (k + 1) / 48
        bm.faces.new([bm.verts.new((r * math.cos(a), r * math.sin(a), 0)) for r, a in ((.0255, a1), (.0295, a1), (.0295, a2), (.0255, a2))])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-6); bm.to_mesh(me_); bm.free(); return me_
def kolco(name, lat, lon, t0, t_gas):
    n = ll(lat, lon).normalized(); pos = n * (R_GL + .017)
    mm = mat_svet('metka-' + name, '#ff6a3d', 1.3, 1.0, gorizont=(.0, .14))
    ob = bpy.data.objects.new(name, kolco_mesh(name)); sc.collection.objects.link(ob); ob.data.materials.append(mm)
    ob.location = pos; ob.rotation_mode = 'QUATERNION'; ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(n)
    f0 = F(t0)
    kl = [(f0 - 1, 0.0), (f0 + 20, 1.0)]
    if t_gas:
        kl += [(F(t_gas), 1.0), (F(t_gas + 1), .7)]
        k_kluchi(mm, [(t_gas, 1.0), (t_gas + 1, .4), (60.4, .4), (61.6, .2)])
    for f, s in kl: ob.scale = (s, s, s); ob.keyframe_insert('scale', frame=f)
    # pulse: a second ring expands and fades, three times
    pu = bpy.data.objects.new(name + '-puls', kolco_mesh(name + '-p')); sc.collection.objects.link(pu)
    pm = mat_svet('puls-' + name, '#ff6a3d', 1.3, 0.0, gorizont=(.0, .14)); pu.data.materials.append(pm)
    pu.location = pos; pu.rotation_mode = 'QUATERNION'; pu.rotation_quaternion = ob.rotation_quaternion
    kk = [(t0 - .1, 0.0)]
    for i in range(3):
        fa = f0 + 20 + i * 54
        for f, s in ((fa - 1, 1.0), (fa, 1.0), (fa + 40, 1.8)): pu.scale = (s, s, s); pu.keyframe_insert('scale', frame=f)
        kk += [((fa - 1 - 1) / FPS, 0.0), ((fa - 1) / FPS, .4), ((fa + 39) / FPS, 0.0)]
    k_kluchi(pm, kk)
    # centre dot
    dt = bpy.data.objects.new(name + '-tochka', bpy.data.meshes.new(name + '-t')); sc.collection.objects.link(dt)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=.0065); bm.to_mesh(dt.data); bm.free(); dt.data.materials.append(mm)
    dt.location = pos
    for f, s in ((f0 - 1, 0), (f0 + 10, 1.0)): dt.scale = (s, s, s); dt.keyframe_insert('scale', frame=f)
    return pos, n
POS = {name: kolco(name, la, lo, t0, tg) for name, la, lo, t0, tg in METKI}

for o in sc.objects:
    if o.name.startswith(('er-', 'sap-')) or o.name in POS or o.name.endswith(('-puls', '-tochka')): o.visible_shadow = False

# -- on-screen marker positions per frame (for the labels): x, y, facing the camera, depth
def metki_json():
    out = {'w': 1920, 'h': 1080, 'fps': FPS, 'kadry': {}}
    for f in range(1, NF + 1):
        sc.frame_set(f); cw = cam.matrix_world; cpos = cw.translation; row = {}
        for name, (pos, n) in POS.items():
            v = world_to_camera_view(sc, cam, pos); vid = n.dot((cpos - pos).normalized())
            row[name] = [round(v.x * 1920, 1), round((1 - v.y) * 1080, 1), round(vid, 3), round(v.z, 3)]
        for pn, *_ in PUTI:
            g = bpy.data.objects[pn + '-golova']; p = g.matrix_world.translation.copy()
            v = world_to_camera_view(sc, cam, p); vid = p.normalized().dot((cpos - p).normalized())
            pn_ = p.normalized()
            row['g:' + pn] = [round(v.x * 1920, 1), round((1 - v.y) * 1080, 1), round(vid, 3), round(g.scale[0], 2),
                              round(math.degrees(math.asin(max(-1, min(1, pn_.z)))), 1), round(math.degrees(math.atan2(pn_.y, pn_.x)), 1)]
        # disc bottom: outline of the r = 1.03 sphere (with atmosphere) from tangent points, lowest point on screen
        dd = cpos.length; u = cpos.normalized(); rr_ = 1.03
        e1 = u.orthogonal().normalized(); e2 = u.cross(e1); c0 = u * (rr_ * rr_ / dd); rk = rr_ * math.sqrt(max(0, 1 - rr_ * rr_ / (dd * dd)))
        kont = [world_to_camera_view(sc, cam, c0 + (e1 * math.cos(a) + e2 * math.sin(a)) * rk) for a in [2 * math.pi * i / 72 for i in range(72)]]
        row['niz'] = round(max((1 - v.y) * 1080 for v in kont), 1)
        cx = sum(v.x for v in kont) / 72 * 1920; cy = sum(1 - v.y for v in kont) / 72 * 1080
        row['disk'] = [round(cx, 1), round(cy, 1), round(sum(math.hypot(v.x * 1920 - cx, (1 - v.y) * 1080 - cy) for v in kont) / 72, 1)]
        cd = (cpos).normalized(); row['kam'] = [round(math.degrees(math.asin(max(-1, min(1, cd.z)))), 1), round(math.degrees(math.atan2(cd.y, cd.x)), 1)]
        out['kadry'][f] = row
    json.dump(out, open(f'{ROOT}/metki.json', 'w'))
metki_json()
if REZHIM == 'metki': sys.exit(0)

# -- render
os.makedirs(f'{ROOT}/kadry', exist_ok=True)
if REZHIM == 'vse': spisok = list(range(1, NF + 1))
else: spisok = [int(x) for x in REZHIM.split(',')]
for f in spisok:
    sc.frame_set(f); sc.render.filepath = f'{ROOT}/kadry/{f:04d}.png'
    if os.path.exists(sc.render.filepath) and REZHIM == 'vse': continue
    bpy.ops.render.render(write_still=True)
print('done', len(spisok))
