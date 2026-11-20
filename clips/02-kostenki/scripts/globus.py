# Clip 2 'Kostenki', scene A: the globe from clip 1 (real relief) flying from Africa and Europe to the Don. Blender 5.2, EEVEE.
#   blender -b --factory-startup --python globus.py -- <clip-2 root> [vse | 1,2,3 | metki] [--proba]
# Frames -> <root>/kadry/A/, on-screen position of the Kostenki marker -> <root>/metki-A.json (labels are drawn by montazh2.py).
import bpy, bmesh, math, json, sys, os
from mathutils import Vector, Euler, Quaternion
from bpy_extras.object_utils import world_to_camera_view

A = sys.argv[sys.argv.index('--') + 1:]
ROOT = A[0]; TEX = os.environ.get('GLOBE_TEX', ROOT + '/../01-out-of-africa/tex'); REZHIM = A[1] if len(A) > 1 else 'proba'; PROBA = '--proba' in A
FPS, DLIT = 30, 11.6
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
img_h = bpy.data.images.load(f'{TEX}/vysota_8192.png'); img_h.colorspace_settings.name = 'Non-Color'
tx = bpy.data.textures.new('vysota', 'IMAGE'); tx.image = img_h; tx.extension = 'EXTEND'
dm = glob.modifiers.new('rel_ef', 'DISPLACE'); dm.texture = tx; dm.texture_coords = 'UV'; dm.uv_layer = 'UV'
dm.direction = 'NORMAL'; dm.mid_level = 1000 / 9000; dm.strength = 0.016

mt = bpy.data.materials.new('globus'); mt.use_nodes = True; nt = mt.node_tree; N = nt.nodes
pb = N['Principled BSDF']
uvn = N.new('ShaderNodeUVMap'); uvn.uv_map = 'UV'
tc = N.new('ShaderNodeTexImage'); tc.image = bpy.data.images.load(f'{TEX}/cvet_8192.png'); tc.interpolation = 'Cubic'
to = N.new('ShaderNodeTexImage'); to.image = bpy.data.images.load(f'{TEX}/okean_8192.png'); to.image.colorspace_settings.name = 'Non-Color'
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

# camera keys: (sec, lat, lon, distance, tilt deg, side offset, lift), from Africa and Europe to the Don near Voronezh
KAM = [(0, 32, 22, 6.6, 2, -.55), (4.0, 40, 30, 5.6, 6, -.45), (7.4, 49, 37, 3.0, 14, 0), (11.6, 51.39, 39.04, 1.95, 6, 0)]
def kluch(t, lat, lon, dist, naklon, sdvig=0.0, podyom=0.0):
    f = 1 + round(t * FPS)
    piv.rotation_euler = Euler((0, math.radians(-lat), math.radians(lon)), 'XYZ'); piv.keyframe_insert('rotation_euler', frame=f)
    a = math.radians(naklon)
    cam.location = (dist * math.cos(a), 0, -dist * math.sin(a) * .55); cam.keyframe_insert('location', frame=f)
    cel.location = (R_GL * .98, sdvig, podyom); cel.keyframe_insert('location', frame=f)
for k in KAM: kluch(*k)

# -- Kostenki marker: ring and dot
KLAT, KLON = 51.39, 39.04
n = ll(KLAT, KLON).normalized(); pos = n * (R_GL + .012)
mm = bpy.data.materials.new('metka'); mm.use_nodes = True; nn = mm.node_tree.nodes
for x in list(nn):
    if x.type != 'OUTPUT_MATERIAL': nn.remove(x)
em = nn.new('ShaderNodeEmission'); em.inputs[0].default_value = L('#ff6a3d'); em.inputs[1].default_value = 1.3
mm.node_tree.links.new(em.outputs[0], nn['Material Output'].inputs[0])
ring = bpy.data.objects.new('metka', bpy.data.meshes.new('metka')); sc.collection.objects.link(ring)
bm = bmesh.new()
for k in range(48):
    a1, a2 = 2 * math.pi * k / 48, 2 * math.pi * (k + 1) / 48
    bm.faces.new([bm.verts.new((r * math.cos(a), r * math.sin(a), 0)) for r, a in ((.0105, a1), (.0128, a1), (.0128, a2), (.0105, a2))])
bm.to_mesh(ring.data); bm.free(); ring.data.materials.append(mm)
ring.location = pos; ring.rotation_mode = 'QUATERNION'; ring.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(n)
for f, s_ in ((1 + round(4.6 * FPS), 0), (1 + round(5.4 * FPS), 1.0)): ring.scale = (s_, s_, s_); ring.keyframe_insert('scale', frame=f)
ring.visible_shadow = False
ring.hide_render = True   # the ring is no longer rendered: a crisp marker is drawn in the edit

GOROD = {'voronezh': (51.672, 39.184), 'moskva': (55.756, 37.617)}
GP = {k: ll(a, b).normalized() * (R_GL + .012) for k, (a, b) in GOROD.items()}
out, tch = {}, {}
for f in range(1, NF + 1):
    sc.frame_set(f); v = world_to_camera_view(sc, cam, pos)
    out[f] = [round(v.x * 1920, 1), round((1 - v.y) * 1080, 1)]
    row = {}
    for k, p in GP.items():
        q = world_to_camera_view(sc, cam, p)
        vid = (p.normalized().dot((cam.matrix_world.translation - p).normalized()) > .15)   # on the visible side of the sphere
        row[k] = [round(q.x * 1920, 1), round((1 - q.y) * 1080, 1), 1 if vid else 0]
    tch[f] = row
json.dump({'kadry': out, 'tochki': tch}, open(f'{ROOT}/metki-A.json', 'w'))
if REZHIM == 'metki': sys.exit(0)
os.makedirs(f'{ROOT}/kadry/A', exist_ok=True)
spisok = list(range(1, NF + 1)) if REZHIM == 'vse' else [int(x) for x in REZHIM.split(',')]
for f in spisok:
    sc.frame_set(f); sc.render.filepath = f'{ROOT}/kadry/A/{f:04d}.png'
    if REZHIM == 'vse' and os.path.exists(sc.render.filepath): continue
    bpy.ops.render.render(write_still=True)
print('done A', len(spisok))
