# Bake the firebrand flame (scene B1): a small static domain, the source stays put while gas leaves backwards at walking speed,
# so the flame leans back and up like a torch in a walking hand. In the scene the volume travels with the firebrand.
#   blender -b --factory-startup --python sim_golovnya.py -- <root> [name] [res]
import sys, os
A = sys.argv[sys.argv.index('--') + 1:]; ROOT = A[0]; IMYA = A[1] if len(A) > 1 else 'golovnya'; RES = int(A[2]) if len(A) > 2 else 144
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obshchee; obshchee.FPS = 24
from obshchee import *
NF = 150
ochistit(); sc = bpy.context.scene; sc.render.fps = 24; sc.frame_start, sc.frame_end = 1, NF
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=.045, location=(.25, 0, .12)); ist = bpy.context.object; ist.scale = (1.5, .8, .8)
tex = bpy.data.textures.new('shum', 'CLOUDS'); tex.noise_scale = .04; tex.noise_depth = 2
f = istochnik(ist, 'BOTH', toplivo=1.1, temp=1.6, plotn=.5, dist=.4, tex=tex, skorost=(-1.3, 0, .15)); f.texture_size = .08
f.texture_offset = 0; f.keyframe_insert('texture_offset', frame=1); f.texture_offset = 9.0; f.keyframe_insert('texture_offset', frame=NF)
d = domen('dom', (0, 0, .45), (1.0, .5, .9), res=RES, kesh=f'{ROOT}/sim/{IMYA}', f0=1, f1=int(os.environ.get('SIM_KADROV', NF)), noise=0, vort=.55, burn=.85,
          flame_smoke=.5, flame_vort=.9, beta=1.5, dissolve=14, max_shagov=4)
for k_ in ('use_collision_border_front', 'use_collision_border_back', 'use_collision_border_left', 'use_collision_border_right', 'use_collision_border_top', 'use_collision_border_bottom'):
    pass
pech(d)
