# Test: a baked campfire (volume) with its material, several frames on one sheet.
#   blender -b --factory-startup --python proba_vol.py -- <root> <cache> <tag> <frames 40,55,70>   (MAT/SILA/DYM via the environment)
import sys, os, time
A = sys.argv[sys.argv.index('--') + 1:]; ROOT = A[0]; KESH = A[1]; TAG = A[2]; KADRY = [int(x) for x in A[3].split(',')]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obshchee; obshchee.FPS = 24
from obshchee import *
ochistit()
m = mat_ognya('ogon', sila=float(os.environ.get('SILA', 40)), dym=float(os.environ.get('DYM', .5)))
vo = obyom_iz_kesha(f'{ROOT}/sim/{KESH}', mat=m, rezhim='REPEAT', shum=os.environ.get('SHUM') == '1')
bpy.ops.mesh.primitive_plane_add(size=30); zem = bpy.context.object; zem.data.materials.append(mat_prostoy('zem', L('#3a2f25'), .95))
rng = np.random.default_rng(2); mp = mat_prostoy('poleno', L('#2a1c12'), .9)
for i in range(7):
    a = i / 7 * 2 * math.pi + rng.uniform(-.2, .2)
    bpy.ops.mesh.primitive_cylinder_add(radius=rng.uniform(.03, .05), depth=rng.uniform(.5, .7), vertices=14, location=(math.cos(a) * .2, math.sin(a) * .2, .12))
    o = bpy.context.object; o.rotation_euler = (0, math.radians(68 + rng.uniform(-8, 8)), a + math.pi); o.data.materials.append(mp)
svet_kostra('svet', (0, 0, .55), sila=90, nf=80, radius=.2)
bpy.context.scene.world = bpy.data.worlds.new('mir'); bpy.context.scene.world.use_nodes = True
bpy.context.scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.004, .006, .012, 1)
k = kamera(lens=42, dof=2.4, fstop=4); k.location = (2.1, -1.05, .6); smotret(k, (0, 0, .6))
sc = dvizhok('CYCLES', proc=50, samples=48, nf=80)
fs = []
for n in KADRY:
    sc.frame_set(n); f = f'{ROOT}/proba/vol-{TAG}-{n}.png'; sc.render.filepath = f; t = time.time()
    bpy.ops.render.render(write_still=True); print('frame', n, f'{time.time() - t:.1f} s'); fs.append(f)
