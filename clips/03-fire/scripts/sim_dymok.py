# Bake a wisp of smoke (scene D): a thin trail from the friction point / smouldering tinder, thicker over time.
#   blender -b --factory-startup --python sim_dymok.py -- <root> [name] [res]
import sys, os
A = sys.argv[sys.argv.index('--') + 1:]; ROOT = A[0]; IMYA = A[1] if len(A) > 1 else 'dymok'; RES = int(A[2]) if len(A) > 2 else 128
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obshchee; obshchee.FPS = 24
from obshchee import *
NF = 240
ochistit(); sc = bpy.context.scene; sc.render.fps = 24; sc.frame_start, sc.frame_end = 1, NF
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=.008, location=(0, 0, .012)); ist = bpy.context.object
f = istochnik(ist, 'SMOKE', toplivo=0.0, temp=.55, plotn=0.0, dist=.6)
for fr, v in ((1, 0.0), (14, 0.0), (50, .5), (150, 1.0), (200, 2.2), (NF, 2.6)):
    f.density = v; f.keyframe_insert('density', frame=fr)
bpy.ops.object.effector_add(type='TURBULENCE', location=(0, 0, .3)); e = bpy.context.object; e.field.strength = .12; e.field.size = .12; e.field.noise = 1.0; e.field.flow = .3
d = domen('dom', (0, 0, .36), (.4, .4, .72), res=RES, kesh=f'{ROOT}/sim/{IMYA}', f0=1, f1=int(os.environ.get('SIM_KADROV', NF)), noise=0, vort=.75, burn=.9,
          flame_smoke=0, flame_vort=0, beta=1.0, dissolve=90, max_shagov=4)
pech(d)
