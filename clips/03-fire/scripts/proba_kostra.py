# Campfire test: simulation and emission variants. Bakes (if there is no cache) and renders a couple of frames in Cycles.
#   blender -b --factory-startup --python proba_kostra.py -- <root> <variant> [frames: 50,70] [view: AgX|Filmic|Standard] [look]
import sys, os, time
A = sys.argv[sys.argv.index('--') + 1:]; ROOT = A[0]; VAR = A[1]; KADRY = [int(x) for x in (A[2] if len(A) > 2 else '50,70').split(',')]
VID = A[3] if len(A) > 3 else 'AgX'; LOOK = A[4] if len(A) > 4 else None
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obshchee; obshchee.FPS = 24
from obshchee import *
VARIANTY = {
    'a': dict(res=160, noise=0, toplivo=1.0, temp=2.0, burn=.7, fv=.75, vort=.4, beta=2.0, fs=.15, r=.10, sila=5, dym=3),
    'b': dict(res=100, noise=2, toplivo=1.0, temp=2.0, burn=.7, fv=.75, vort=.4, beta=2.0, fs=.15, r=.10, sila=5, dym=3),
    'c': dict(res=160, noise=0, toplivo=.7, temp=3.0, burn=.55, fv=1.0, vort=.6, beta=3.0, fs=.1, r=.08, sila=5, dym=3),
    'd': dict(res=128, noise=2, toplivo=.7, temp=3.0, burn=.55, fv=1.0, vort=.6, beta=3.0, fs=.1, r=.08, sila=5, dym=3),
}
V = VARIANTY[VAR]
ochistit()
NF = 80
bpy.ops.mesh.primitive_plane_add(size=30); zem = bpy.context.object; zem.data.materials.append(mat_prostoy('zem', L('#3a2f25'), .95))
rng = np.random.default_rng(2)
mp = mat_prostoy('poleno', L('#2a1c12'), .9)
for i in range(7):
    a = i / 7 * 2 * math.pi + rng.uniform(-.2, .2)
    bpy.ops.mesh.primitive_cylinder_add(radius=rng.uniform(.03, .05), depth=rng.uniform(.5, .7), vertices=14, location=(math.cos(a) * .16, math.sin(a) * .16, .15))
    o = bpy.context.object; o.rotation_euler = (0, math.radians(60 + rng.uniform(-8, 8)), a + math.pi); o.data.materials.append(mp)
# source: a ring of several small spheres (flame tongues from different logs) + a noise texture travelling over time
tex = bpy.data.textures.new('shum', 'CLOUDS'); tex.noise_scale = .08; tex.noise_depth = 3
for i in range(5):
    a = i / 5 * 2 * math.pi; rr = .07 if i else 0
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=V['r'] * (.8 if i else 1.0), location=(math.cos(a) * rr, math.sin(a) * rr, .12 + .03 * (i % 2)))
    ist = bpy.context.object; ist.scale = (1, 1, .55); ist.hide_render = True
    f = istochnik(ist, 'BOTH', toplivo=V['toplivo'], temp=V['temp'], plotn=.3, dist=.5, tex=tex); f.texture_size = .2
    f.texture_offset = 0.0; f.keyframe_insert('texture_offset', frame=1); f.texture_offset = 4.0 + i; f.keyframe_insert('texture_offset', frame=NF)
kesh = f'{ROOT}/sim/proba-{VAR}'
d = domen('dom', (0, 0, .9), (1.2, 1.2, 1.8), res=V['res'], kesh=kesh, f0=1, f1=NF, noise=V['noise'], vort=V['vort'], burn=V['burn'],
          flame_smoke=V['fs'], flame_vort=V['fv'], beta=V['beta'], dissolve=18, time_scale=1.0)
MAT = os.environ.get('MAT', 'ramp')
if MAT == 'ramp': d.data.materials.append(mat_ognya('ogon', sila=float(os.environ.get('SILA', V['sila'])), dym=float(os.environ.get('DYM', V['dym']))))
else: d.data.materials.append(mat_ognya_bb('ogon', temp=float(os.environ.get('OG_T', 1700)), yark=float(os.environ.get('YARK', 1)), dym=float(os.environ.get('DYM', 2)), attr_t=os.environ.get('ATTR', 'temperature')))
if not kesh_gotov(kesh, NF): pech(d)
svet_kostra('svet', (0, 0, .4), sila=150, nf=NF)
bpy.context.scene.world = bpy.data.worlds.new('mir'); bpy.context.scene.world.use_nodes = True
bpy.context.scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.004, .006, .012, 1)
k = kamera(lens=50, dof=2.2, fstop=4); k.location = (1.9, -.95, .55); smotret(k, (0, 0, .62))
sc = dvizhok('CYCLES', proc=50, samples=64, nf=NF)
sc.view_settings.view_transform = VID
if LOOK:
    try: sc.view_settings.look = LOOK
    except Exception as e: print('no look', e, [x.identifier for x in type(sc.view_settings).bl_rna.properties['look'].enum_items][:30])
else:
    try: sc.view_settings.look = 'None'
    except Exception: pass
for n in KADRY:
    sc.frame_set(n); sc.render.filepath = f'{ROOT}/proba/kost-{VAR}-{os.environ.get("TAG", VID)}-{n}.png'; t = time.time()
    bpy.ops.render.render(write_still=True); print('frame', n, f'{time.time() - t:.1f} s'); sys.stdout.flush()
