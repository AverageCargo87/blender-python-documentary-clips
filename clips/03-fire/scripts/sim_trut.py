# Bake the flame in the tinder nest (scene D): nothing at first, then a small tongue, then a steady flame.
#   blender -b --factory-startup --python sim_trut.py -- <root> [name] [res]
import sys, os
A = sys.argv[sys.argv.index('--') + 1:]; ROOT = A[0]; IMYA = A[1] if len(A) > 1 else 'trut'; RES = int(A[2]) if len(A) > 2 else 120
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obshchee; obshchee.FPS = 24
from obshchee import *
NF = 150
ochistit(); sc = bpy.context.scene; sc.render.fps = 24; sc.frame_start, sc.frame_end = 1, NF
tex = bpy.data.textures.new('shum', 'CLOUDS'); tex.noise_scale = .03; tex.noise_depth = 2
for i, (x, y, r) in enumerate(((0, 0, .03), (.03, .015, .022), (-.025, .02, .02))):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=r, location=(x, y, .025)); ist = bpy.context.object; ist.scale = (1, 1, .6)
    f = istochnik(ist, 'BOTH', toplivo=0.0, temp=1.3, plotn=.35, dist=.4, tex=tex); f.texture_size = .06
    for fr, v in ((1, 0.0), (18 + 10 * i, 0.0), (44 + 12 * i, .45), (95, 1.0), (NF, 1.15)):
        f.fuel_amount = v; f.keyframe_insert('fuel_amount', frame=fr)
    f.texture_offset = float(i); f.keyframe_insert('texture_offset', frame=1); f.texture_offset = 9.0 + i; f.keyframe_insert('texture_offset', frame=NF)
d = domen('dom', (0, 0, .4), (.5, .5, .8), res=RES, kesh=f'{ROOT}/sim/{IMYA}', f0=1, f1=int(os.environ.get('SIM_KADROV', NF)), noise=0, vort=.5, burn=.9,
          flame_smoke=.5, flame_vort=.9, beta=1.1, dissolve=18, max_shagov=4)
pech(d)
