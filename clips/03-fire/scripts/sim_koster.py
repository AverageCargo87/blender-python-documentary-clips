# Bake the campfire (simulation only, no render). Later the cache is opened as a volume (obyom_iz_kesha).
#   blender -b --factory-startup --python sim_koster.py -- <root> <cache name> <res> <frames> [key=value ...]
import sys, os
A = sys.argv[sys.argv.index('--') + 1:]; ROOT, IMYA, RES, NF = A[0], A[1], int(A[2]), int(A[3])
P = dict(beta=1.2, temp=1.5, toplivo=1.2, burn=.9, fv=1.0, vort=.6, fs=.1, r=.07, kolco=.15, n_ist=7, shum=.06, beg=8.0, turb=0.0, noise=0,
         razmer=(1.3, 1.3, 1.7), dissolve=14, plotn=.25, max_temp=1.75, ignition=1.25, shagov=4, veter=0.0, vsp_kadr=0, vsp_sila=2.2)
for a in A[4:]:
    k, v = a.split('='); P[k] = type(P[k])(float(v)) if not isinstance(P[k], tuple) else tuple(float(x) for x in v.split(','))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obshchee; obshchee.FPS = 24
from obshchee import *
ochistit(); bpy.context.scene.render.fps = 24; bpy.context.scene.frame_start, bpy.context.scene.frame_end = 1, NF
tex = bpy.data.textures.new('shum', 'CLOUDS'); tex.noise_scale = P['shum']; tex.noise_depth = 3
rng = np.random.default_rng(5)
for i in range(int(P['n_ist']) + 1):
    a = i / P['n_ist'] * 2 * math.pi; rr = P['kolco'] * rng.uniform(.6, 1.0) if i else 0
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=P['r'] * rng.uniform(.8, 1.2), location=(math.cos(a) * rr, math.sin(a) * rr, .10 + .05 * rng.uniform()))
    ist = bpy.context.object; ist.scale = (1, 1, .6)
    f = istochnik(ist, 'BOTH', toplivo=P['toplivo'], temp=P['temp'], plotn=P['plotn'], dist=.5, tex=tex); f.texture_size = .18
    f.texture_offset = float(i); f.keyframe_insert('texture_offset', frame=1); f.texture_offset = P['beg'] + i; f.keyframe_insert('texture_offset', frame=NF)
    if P['vsp_kadr'] > 0:                           # flare: half a second of extra fuel (a branch fell into the fire)
        k0 = int(P['vsp_kadr'])
        for fr, mul in ((k0 - 2, 1.0), (k0 + 4, P['vsp_sila']), (k0 + 14, P['vsp_sila'] * .8), (k0 + 40, 1.0)):
            f.fuel_amount = P['toplivo'] * mul; f.keyframe_insert('fuel_amount', frame=fr)
if P['turb'] > 0:
    bpy.ops.object.effector_add(type='TURBULENCE', location=(0, 0, .5)); e = bpy.context.object; e.field.strength = P['turb']; e.field.size = .25; e.field.noise = 1.0; e.field.flow = .5
if P['veter'] > 0:
    bpy.ops.object.effector_add(type='WIND', location=(-1, 0, .5), rotation=(0, math.radians(90), 0)); e = bpy.context.object; e.field.strength = P['veter']; e.field.noise = .6
rz = P['razmer']
d = domen('dom', (0, 0, rz[2] / 2), rz, res=RES, kesh=f'{ROOT}/sim/{IMYA}', f0=1, f1=NF, noise=int(P['noise']), vort=P['vort'], burn=P['burn'],
          flame_smoke=P['fs'], flame_vort=P['fv'], beta=P['beta'], dissolve=int(P['dissolve']), max_temp=P['max_temp'], ignition=P['ignition'], max_shagov=int(P['shagov']))
pech(d)
