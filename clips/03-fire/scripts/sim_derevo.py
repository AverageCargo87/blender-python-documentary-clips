# Bake the fire on the tree (scene A): simulation frame 1 = the lightning strike. Fire spreads from the split trunk along dry branches and the grass at the roots.
#   blender -b --factory-startup --python sim_derevo.py -- <root> [cache name] [res] [noise]
import sys, os
A = sys.argv[sys.argv.index('--') + 1:]; ROOT = A[0]; IMYA = A[1] if len(A) > 1 else 'derevo'; RES = int(A[2]) if len(A) > 2 else 128; NOISE = int(A[3]) if len(A) > 3 else 2
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obshchee; obshchee.FPS = 24
from obshchee import *
from obshchee_a import *
ochistit(); sc = bpy.context.scene; sc.render.fps = 24; sc.frame_start, sc.frame_end = 1, NF_SIM
zem, z0, der, VERH, RAZV = osnova()
tex = bpy.data.textures.new('shum', 'CLOUDS'); tex.noise_scale = .5; tex.noise_depth = 3
n_ist = 0
for i, t_on, top in goryashchie(der, VERH, RAZV):
    pts, rad, ur = der['vetki'][i]
    if ur == 0: pts = pts[len(pts) // 2:]; rad = rad[len(rad) // 2:] * .5          # crack in the upper half of the trunk
    cu = bpy.data.curves.new(f'ist{i}', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 1.0; cu.bevel_resolution = 1
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1); sp.points.foreach_set('co', np.concatenate([pts, np.ones((len(pts), 1))], 1).ravel())
    sp.points.foreach_set('radius', np.maximum(rad * 1.5, .09))
    o = bpy.data.objects.new(f'ist{i}', cu); sc.collection.objects.link(o)
    aktivnyy(o); bpy.ops.object.convert(target='MESH'); o = bpy.context.object
    f = istochnik(o, 'BOTH', toplivo=0.0, temp=2.0, plotn=.5, dist=.5, tex=tex); f.texture_size = 1.2
    f0 = int(t_on * FPS) + 1
    f.fuel_amount = 0.0; f.keyframe_insert('fuel_amount', frame=max(1, f0 - 1)); f.fuel_amount = top; f.keyframe_insert('fuel_amount', frame=f0 + 16)
    f.texture_offset = float(i); f.keyframe_insert('texture_offset', frame=1); f.texture_offset = 6.0 + i; f.keyframe_insert('texture_offset', frame=NF_SIM)
    n_ist += 1
# grass at the roots: an uneven ring, catches after 2 s
bpy.ops.mesh.primitive_torus_add(major_radius=1.6, minor_radius=.5, major_segments=40, minor_segments=8, location=(RAZV[0] * .3, RAZV[1] * .3, z0 + .1)); tr = bpy.context.object
tr.scale = (1.25, .9, .35)
f = istochnik(tr, 'BOTH', toplivo=0.0, temp=1.6, plotn=.6, dist=.6, tex=tex); f.texture_size = .7
f.keyframe_insert('fuel_amount', frame=int(2.0 * FPS)); f.fuel_amount = .8; f.keyframe_insert('fuel_amount', frame=int(4.5 * FPS))
f.texture_offset = 0; f.keyframe_insert('texture_offset', frame=1); f.texture_offset = 5.0; f.keyframe_insert('texture_offset', frame=NF_SIM)
print('sources', n_ist + 1, 'frames', NF_SIM); sys.stdout.flush()
# wind: a weak side gust so flame and smoke drift
bpy.ops.object.effector_add(type='WIND', location=(-12, -4, z0 + 5), rotation=(0, math.radians(90), math.radians(18))); e = bpy.context.object
e.field.strength = 1.3; e.field.noise = 1.0; e.field.flow = 0
cx, cy = (VERH[0] + RAZV[0]) / 2, (VERH[1] + RAZV[1]) / 2
d = domen('dom', (cx + .8, cy + .3, z0 + 8.5), (15.0, 14.0, 17.4), res=RES, kesh=f'{ROOT}/sim/{IMYA}', f0=1, f1=int(os.environ.get('SIM_KADROV', NF_SIM)), noise=NOISE, vort=.6, burn=.75,
          flame_smoke=1.0, flame_vort=.9, beta=2.0, dissolve=60, max_shagov=3)
pech(d)
