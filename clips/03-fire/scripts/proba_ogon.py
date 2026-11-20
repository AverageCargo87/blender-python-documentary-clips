# Test: campfire (Mantaflow), bake and one frame in Cycles and EEVEE, timed.
#   blender -b --factory-startup --python proba_ogon.py -- <root> [res] [engine]
import sys, os, time
A = sys.argv[sys.argv.index('--') + 1:]; ROOT = A[0]; RES = int(A[1]) if len(A) > 1 else 96; ENG = A[2] if len(A) > 2 else 'oba'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from obshchee import *
ochistit()
NF = 70
# ground and logs
bpy.ops.mesh.primitive_plane_add(size=30); zem = bpy.context.object; zem.data.materials.append(mat_prostoy('zem', L('#3a2f25'), .95))
rng = np.random.default_rng(2)
mp = mat_prostoy('poleno', L('#2a1c12'), .9)
pol = []
for i in range(7):
    a = i / 7 * 2 * math.pi + rng.uniform(-.2, .2)
    bpy.ops.mesh.primitive_cylinder_add(radius=rng.uniform(.035, .06), depth=rng.uniform(.5, .75), vertices=14,
                                        location=(math.cos(a) * .17, math.sin(a) * .17, .16))
    o = bpy.context.object; o.rotation_euler = (0, math.radians(58 + rng.uniform(-8, 8)), a + math.pi); o.data.materials.append(mp); pol.append(o)
# source: a flattened sphere in the heart of the fire
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=.14, location=(0, 0, .14)); ist = bpy.context.object; ist.scale = (1.25, 1.25, .6)
ist.hide_render = True
tex = bpy.data.textures.new('shum', 'CLOUDS'); tex.noise_scale = .12; tex.noise_depth = 2
f = istochnik(ist, 'BOTH', toplivo=1.3, temp=2.0, plotn=.5, dist=.8, tex=tex)
f.texture_size = .25
ist.keyframe_insert('location', frame=1)
kesh = f'{ROOT}/sim/test{RES}'
d = domen('dom', (0, 0, 1.0), (1.5, 1.5, 2.0), res=RES, kesh=kesh, f0=1, f1=NF, noise=2, vort=.35, burn=.8, flame_smoke=.35,
          flame_vort=.6, dissolve=25, time_scale=1.0)
d.data.materials.append(mat_ognya('ogon', sila=18, dym=5))
if not kesh_gotov(kesh, NF): pech(d)
else: print('cache exists')
svet_kostra('svet', (0, 0, .45), sila=220, nf=NF)
bpy.context.scene.world = bpy.data.worlds.new('mir'); bpy.context.scene.world.use_nodes = True
bpy.context.scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.004, .006, .012, 1)
k = kamera(lens=40, dof=2.6, fstop=2.8); k.location = (2.4, -1.2, .75); smotret(k, (0, 0, .55))
for eng in (['CYCLES', 'EEVEE'] if ENG == 'oba' else [ENG]):
    sc = dvizhok(eng, proc=100, samples=64, nf=NF)
    for n in (40, 62):
        sc.frame_set(n); sc.render.filepath = f'{ROOT}/proba/test-{eng}-{RES}-{n}.png'; t = time.time()
        bpy.ops.render.render(write_still=True); print(eng, 'frame', n, f'{time.time() - t:.1f} s'); sys.stdout.flush()
