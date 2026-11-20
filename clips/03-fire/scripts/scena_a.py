# Clip 3 'Fire', scene A: night, a storm over the savanna, lightning strikes a dry acacia and the tree catches fire. EEVEE, 24 fps.
# Two shots: A1 wide (slow push-in, the strike, the tree catches), A2 closer and from below (fire runs along the branches, a burning branch falls).
#   blender -b --factory-startup --python scena_a.py -- <root> <A1|A2> <vse|frames 1,50,120-130|metki> [--proba] [--kesh=name]
import sys, os, json, time
A = sys.argv[sys.argv.index('--') + 1:]; ROOT, PLAN, REZHIM = A[0], A[1], A[2]; PROBA = '--proba' in A
KESH = ([a.split('=')[1] for a in A if a.startswith('--kesh=')] or ['derevo'])[0]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obshchee; obshchee.FPS = 24
from obshchee import *
from priroda import *
from kamni import suk, mat_dereva
from iskry import Iskry
from obshchee_a import *
from mathutils import noise
from bpy_extras.object_utils import world_to_camera_view
T0_ = T0[PLAN]; NF = int(round(DL[PLAN] * FPS))
ochistit()
sc = dvizhok('EEVEE', w=1920, h=1080, proc=50 if PROBA else 100, samples=20 if PROBA else 48, nf=NF)
try: sc.eevee.volumetric_tile_size = os.environ.get('OG_TILE', '2'); sc.eevee.volumetric_samples = int(os.environ.get('OG_VSAMP', 160))         # the fire on the tree is thin: the volume needs fine slices
except Exception: pass
rng = np.random.default_rng(7)
sm_ = lambda u: (lambda x: x * x * (3 - 2 * x))(max(0., min(1., u)))

# -- ground, tree, distant trees, hills
zem, z0, der, VERH, RAZV = osnova()
zem.ob.data.materials[0] = mat_zemli(mokro=.25, cvet=('#33291d', '#5a4a33'))
for i, (x, y, s_) in enumerate([(-80, 160, 1.0), (105, 230, .9), (180, 140, 1.15), (-210, 280, 1.2), (50, 360, 1.0), (-140, 110, .8), (260, 320, 1.3), (-30, 250, .95)]):
    derevo(seed=20 + i, osnova=(x, y, float(zem.z(x, y)) - .2), vys=8.5 * s_, stvol=3.4 * s_, m=1.35 * s_, r0=.36, imya=f'dal{i}', plotn_listvy=.6)

# -- camera
kam = kamera(lens=32 if PLAN == 'A1' else 30, dof=None)
def put_kamery(t):                               # t in s from the scene start
    if PLAN == 'A1':
        e = sm_(t / DL['A1'])
        p = np.array([-34.0, -42.0]) * (1 - e) + np.array([-29.0, -35.0]) * e
        return (p[0], p[1], float(zem.z(p[0], p[1])) + 1.15), (1.5 * (1 - e), 0, z0 + 6.0 + .8 * e)
    e = sm_((t - T0_) / DL['A2'])
    a = math.radians(-124 + 15 * e); r = 21.0 - 2.5 * e
    p = (math.cos(a) * r, math.sin(a) * r)
    return (p[0], p[1], float(zem.z(p[0], p[1])) + .85), (.5, 0, z0 + 5.6)
for n in range(1, NF + 1):
    pk, cel = put_kamery(T0_ + (n - 1) / FPS); kam.location = pk; smotret(kam, cel)
    kam.keyframe_insert('location', frame=n); kam.keyframe_insert('rotation_euler', frame=n)

# -- grass: dry tussocks in the field of view (denser near the camera), sparse up to the tree and beyond
def kochki(n, rmin, rmax, seed, ugol=40, st=1.6):
    r_ = np.random.default_rng(seed); out = []
    for tt in (T0_, T0_ + DL[PLAN]):
        pk, cel = put_kamery(tt); az = math.atan2(cel[1] - pk[1], cel[0] - pk[0])
        rr = rmin + (rmax - rmin) * r_.uniform(0, 1, n // 2) ** st; aa = az + np.radians(r_.uniform(-ugol, ugol, n // 2))
        out.append(np.stack([pk[0] + np.cos(aa) * rr, pk[1] + np.sin(aa) * rr], 1))
    c = np.concatenate(out)
    g = np.array([noise.fractal(Vector((x * .15, y * .15, 2.0)), 1, 2, 3) for x, y in c])
    return c[g > -.25]
NK = 1300 if PROBA else 3000
tr1 = trava('trava-bl', kochki(NK, 1.0, 26, 1), vys=(.45, 1.05), v_kochke=(20, 46), seed=5, z_fn=zem.z)
tr2 = trava('trava-dal', kochki(NK * 2, 22, 120, 2, ugol=34, st=1.2), vys=(.5, 1.0), v_kochke=(8, 18), shir=.014, seed=6, z_fn=zem.z)
veter(tr1, sila=.2, poryv=(.9, .35, 0), skorost=1.3); veter(tr2, sila=.2, poryv=(.9, .35, 0), imya='veter2', skorost=1.3)

# -- sky: a cylinder with a storm-cloud picture; brightness = base + flash (stronger near the strike)
def nebo():
    R_, H_ = 1400., 640.
    bpy.ops.mesh.primitive_cylinder_add(radius=R_, depth=H_, vertices=96, end_fill_type='NOTHING', location=(0, 0, H_ / 2 - 70)); o = bpy.context.object; o.name = 'nebo'
    bpy.ops.object.shade_smooth()
    m = bpy.data.materials.new('nebo'); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; N.clear(); k = nt.links.new
    out = N.new('ShaderNodeOutputMaterial'); em = N.new('ShaderNodeEmission'); tc = N.new('ShaderNodeTexCoord')
    img = N.new('ShaderNodeTexImage'); img.image = bpy.data.images.load(f'{ROOT}/kartinki/nebo.png'); img.extension = 'MIRROR'
    mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (2.0, 1.0, 1.0); mp.inputs['Location'].default_value = (.78, 0, 0)   # even scale: the cylinder seam is not visible
    k(tc.outputs['UV'], mp.inputs['Vector']); k(mp.outputs[0], img.inputs['Vector'])
    val = N.new('ShaderNodeValue'); val.name = 'vsp'; val.outputs[0].default_value = 0
    geo = N.new('ShaderNodeNewGeometry'); ds = N.new('ShaderNodeVectorMath'); ds.operation = 'DISTANCE'; ds.inputs[1].default_value = (150, 1390, 260)
    mr = N.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = 0; mr.inputs['From Max'].default_value = 1300
    mr.inputs['To Min'].default_value = 1.0; mr.inputs['To Max'].default_value = .1
    k(geo.outputs['Position'], ds.inputs[0]); k(ds.outputs['Value'], mr.inputs['Value'])
    m1 = N.new('ShaderNodeMath'); m1.operation = 'MULTIPLY'; k(val.outputs[0], m1.inputs[0]); k(mr.outputs['Result'], m1.inputs[1])
    m2 = N.new('ShaderNodeMath'); m2.operation = 'ADD'; m2.inputs[1].default_value = .62; k(m1.outputs[0], m2.inputs[0])
    k(img.outputs['Color'], em.inputs['Color']); k(m2.outputs[0], em.inputs['Strength']); k(em.outputs[0], out.inputs['Surface'])
    o.data.materials.append(m); o.visible_shadow = False
    return val.outputs[0]
neb = nebo()
mir = bpy.data.worlds.new('mir'); sc.world = mir; mir.use_nodes = True
bg = mir.node_tree.nodes['Background']; bg.inputs[0].default_value = (.03, .042, .075, 1); bg.inputs[1].default_value = 2.4
# light haze in the air: depth and a halo around the lightning and the fire
vs = mir.node_tree.nodes.new('ShaderNodeVolumeScatter'); vs.inputs['Density'].default_value = .0016; vs.inputs['Anisotropy'].default_value = .55
vs.inputs['Color'].default_value = (.75, .8, .9, 1)
mir.node_tree.links.new(vs.outputs[0], mir.node_tree.nodes['World Output'].inputs['Volume'])
try: sc.eevee.volumetric_end = float(os.environ.get('OG_VEND', 260.0))
except Exception: pass

# -- lightning and flashes
p_obl = np.array([VERH[0] + 30, VERH[1] + 150, 430.0])
mol, mol_v, kanal = molniya(p_obl, VERH, seed=5, r=.05, vetvey=9, sila=900., vidno=75.)
sv = bpy.data.lights.new('vsp', 'SUN'); sv.angle = math.radians(2.5); sv.color = (.72, .8, 1.0)
svo = bpy.data.objects.new('vsp', sv); sc.collection.objects.link(svo); svo.location = (0, 0, 100)
d_ = np.array([-20.0, -150.0, -75.0]); smotret(svo, tuple(np.array(svo.location) + d_))       # lightning light from behind and to the side, low: grass and tree get a rim
svt = bpy.data.lights.new('vsp-t', 'POINT'); svt.color = (.72, .8, 1.0); svt.shadow_soft_size = 1.5
svto = bpy.data.objects.new('vsp-t', svt); sc.collection.objects.link(svto); svto.location = kanal[int(len(kanal) * .9)]
ZARNICY = ((1.4, .10, .32), (3.3, .16, .36), (9.3, .07, .3), (11.8, .05, .3))                  # distant flickers in the clouds: time, strength, duration
UDAR = ((0, 1.0), (1 / 24, .8), (2 / 24, .32), (3 / 24, .55), (4 / 24, .4), (5 / 24, .22), (6 / 24, .12), (7 / 24, .06), (8 / 24, .03))   # strike: discharge, repeat, decay
def vspyshka(t):
    v = sum(s_ * math.exp(-((t - tz) / dl) ** 2) for tz, s_, dl in ZARNICY); d = t - T_UDAR
    for td, s_ in UDAR:
        if abs(d - td) < .5 / 24: v += s_
    return v
def udar(t):
    d = t - T_UDAR
    for td, s_ in ((0, 1.0), (1 / 24, .75), (2 / 24, .18), (3 / 24, .55), (4 / 24, .25), (5 / 24, .06)):
        if abs(d - td) < .5 / 24: return s_
    return 0.0
em_m = mol.data.materials[0].node_tree.nodes['Emission'].inputs['Strength']; em_v = mol_v.data.materials[0].node_tree.nodes['Emission'].inputs['Strength']
for n in range(0, NF + 2):
    t = T0_ + (n - 1) / FPS; v = vspyshka(t); u = udar(t)
    neb.default_value = 1.9 * v; neb.keyframe_insert('default_value', frame=n)
    sv.energy = 3.2 * max(0, v - .02); sv.keyframe_insert('energy', frame=n)
    svt.energy = 2.5e5 * u; svt.keyframe_insert('energy', frame=n)
    em_m.default_value = 700 * u; em_m.keyframe_insert('default_value', frame=n)
    vv = u if (t - T_UDAR) < 2.5 / 24 else 0
    em_v.default_value = 320 * vv; em_v.keyframe_insert('default_value', frame=n)
    mol.hide_render = u <= 0; mol.keyframe_insert('hide_render', frame=n); mol_v.hide_render = vv <= 0; mol_v.keyframe_insert('hide_render', frame=n)

# -- crack in the trunk: glows with heat after the strike
stv = der['vetki'][0][0]; kk = stv[len(stv) // 3:] + np.array([-.3, -.3, 0]) * .9
cu = bpy.data.curves.new('treshchina', 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = .035; cu.bevel_resolution = 1
sp = cu.splines.new('POLY'); sp.points.add(len(kk) - 1); sp.points.foreach_set('co', np.concatenate([kk + rng.normal(0, .03, kk.shape), np.ones((len(kk), 1))], 1).ravel())
tro = bpy.data.objects.new('treshchina', cu); sc.collection.objects.link(tro)
mt = bpy.data.materials.new('zhar'); mt.use_nodes = True; Nt = mt.node_tree.nodes; Nt.clear(); ot = Nt.new('ShaderNodeOutputMaterial'); et = Nt.new('ShaderNodeEmission')
et.inputs['Color'].default_value = (1.0, .32, .05, 1); mt.node_tree.links.new(et.outputs[0], ot.inputs['Surface']); cu.materials.append(mt)
for n in range(0, NF + 2):
    d = T0_ + (n - 1) / FPS - T_UDAR
    et.inputs['Strength'].default_value = 0 if d < 0 else (60 * math.exp(-d * 6) + 9 * (1 + .3 * math.sin(d * 7.3)) * min(1, d * 2))
    et.inputs['Strength'].keyframe_insert('default_value', frame=n)

# -- sparks from the strike, embers from the fire, sparks from the falling branch
isk = Iskry('iskry', sila=70.)
isk.vsplesk(T_UDAR, VERH, napr=(-.2, -.3, .5), n=120, skorost=(3, 12), konus=.9, zhizn=(.4, 1.5), g=14, drag=1.3, pol=z0, otskok=.25, r=.012, yark=1.3)     # no 'fireworks': fewer sparks, they fly sideways and drop fast
isk.vsplesk(T_UDAR + .1, RAZV + np.array([0, 0, .5]), napr=(-.4, -.6, .25), n=110, skorost=(2, 8), konus=.7, zhizn=(.5, 1.8), g=14, drag=1.0, pol=z0, otskok=.3, r=.012, yark=1.0)
isk.vsplesk(T_UDAR + .5, (VERH + RAZV) / 2 + np.array([0, 0, 1.0]), napr=(.25, .1, 1), n=1700, skorost=(.6, 3.6), konus=.8, zhizn=(1.4, 4.2), g=1.2, drag=1.2,
            r=.012, yark=.85, razbros_mesta=2.0, veter=(2.2, .7, 1.4), turb=6.0, pod=2.4, dlit=9.6, ostyv=1.0)
# the falling burning branch
P_V0 = VERH + np.array([-1.6, -1.2, -1.4]); P_V1 = np.array([P_V0[0] - .9, P_V0[1] - 1.3, z0 + .12]); T_PAD = .95
vet = suk('vetka', (-.75, 0, 0), (.75, 0, 0), r=.05, seed=9, mat=mat_dereva('vetka', ugol=.8, zhar=14.0), izgib=.1)
lv = bpy.data.lights.new('vetka-svet', 'POINT'); lv.color = (1.0, .5, .18); lv.shadow_soft_size = .3; lvo = bpy.data.objects.new('vetka-svet', lv); sc.collection.objects.link(lvo)
for n in range(0, NF + 2):
    d = T0_ + (n - 1) / FPS - T_VETKA; u = max(0, min(1, d / T_PAD))
    p = P_V0 * (1 - u) + P_V1 * u; p[2] = P_V0[2] + (P_V1[2] - P_V0[2]) * u * u                 # falls with acceleration
    vet.location = p; vet.rotation_euler = (.6 * u * 4, .5 + 1.9 * u, .3 + 2.2 * u); vet.hide_render = d < -.05
    for pth in ('location', 'rotation_euler', 'hide_render'): vet.keyframe_insert(pth, frame=n)
    lvo.location = (p[0], p[1], p[2] + .25); lvo.keyframe_insert('location', frame=n)
    lv.energy = 0 if d < 0 else 900 * (1 + .25 * math.sin(d * 23)); lv.keyframe_insert('energy', frame=n)
isk.vsplesk(T_VETKA, P_V0, napr=(0, 0, -1), n=160, skorost=(.5, 3), konus=1.2, zhizn=(.4, 1.3), drag=1.5, pol=z0, otskok=.2, r=.02, yark=1.0, dlit=T_PAD)
isk.vsplesk(T_VETKA + T_PAD, P_V1, napr=(0, 0, 1), n=260, skorost=(1.5, 7), konus=1.1, zhizn=(.4, 1.5), drag=1.0, pol=z0, otskok=.3, r=.022, yark=1.3)

# -- fire on the tree: simulation frame 1 = the strike
kd = f'{ROOT}/sim/{KESH}'
if os.path.exists(kd + '/gotovo.txt'):
    f_udar = int(round((T_UDAR - T0_) * FPS)) + 1
    VID = os.environ.get('OG_FIRE', 'noise')          # what to show: the coarse simulation grids (data), the detail (noise) or both layers
    S1, S2 = float(os.environ.get('OG_S1', 14)), float(os.environ.get('OG_S2', 18))
    if VID in ('data', 'oba'): obyom_iz_kesha(kd, imya='ogon-krupno', mat=mat_ognya('ogon', sila=S1, dym=1.4, cvet_dyma=(.03, .028, .027)), nachalo=f_udar, rezhim='CLIP')
    if VID in ('noise', 'oba'): obyom_iz_kesha(kd, imya='ogon-melko', mat=mat_ognya('ogon-m', sila=S2, dym=0.0, shum=True), nachalo=f_udar, rezhim='CLIP', shum=True)
else: print('NO FIRE CACHE', kd)
for j, (p, s_) in enumerate((((RAZV + np.array([-1.6, -2.2, 1.6])), 1.0), (((VERH + RAZV) / 2 + np.array([-1.2, -2.4, 1.8])), .9), ((VERH + np.array([-1.4, -1.8, -.6])), .7),
                             ((RAZV[0] - 1.2, RAZV[1] - 1.6, z0 + .8), .45))):
    def rost(n, j=j):
        d = T0_ + (n - 1) / FPS - T_UDAR
        if j == 3: return 0 if d < 2.2 else sm_((d - 2.2) / 3.5) * .8                             # the grass at the roots catches later
        return 0 if d < 0 else (min(1, d / 1.0) ** 2 * .1 + sm_((d - .6) / 6.5) ** 1.3 * .9)
    svet_kostra(f'ogon-svet{j}', tuple(p), sila=2600 * s_, cvet=(1.0, .5, .2), seed=j, nf=NF + 2, radius=.8, glubina=.3, mnozh=rost)

# -- label points for the edit
if REZHIM in ('vse', 'metki'):
    M = dict(kadry=[], fps=FPS, dlit=DL[PLAN], t_udar=T_UDAR, t0=T0_)
    for n in range(1, NF + 1):
        sc.frame_set(n); t = T0_ + (n - 1) / FPS
        c = world_to_camera_view(sc, kam, Vector((0, 0, z0 + 5.5))); cm = world_to_camera_view(sc, kam, Vector(tuple(VERH)))
        M['kadry'].append(dict(vsp=round(vspyshka(t), 3), udar=round(udar(t), 3), derevo=[round(c.x, 4), round(1 - c.y, 4)], verh=[round(cm.x, 4), round(1 - cm.y, 4)], t=round(t, 3)))
    json.dump(M, open(f'{ROOT}/metki-{PLAN}.json', 'w'))
    if REZHIM == 'metki': sys.exit(0)
out = f'{ROOT}/kadry/{PLAN}' + ('-proba' if PROBA else ''); os.makedirs(out, exist_ok=True)
VFOK = float(os.environ.get('OG_VFOK', 0))
if VFOK > 0: sc.eevee.volumetric_sample_distribution = float(os.environ.get('OG_VDIST', 0))
for n in spisok_kadrov(REZHIM, NF):
    f = f'{out}/{n:04d}.png'
    if os.path.exists(f) and not PROBA: continue
    sc.frame_set(n); isk.obnovit(T0_ + (n - 1) / FPS, vyderzhka=1 / 40)
    if VFOK > 0:                              # volume slices only around the tree: thin flames without hatching
        d_ = (kam.matrix_world.translation - Vector((0, 0, z0 + 6.0))).length
        sc.eevee.volumetric_start = max(.1, d_ - VFOK); sc.eevee.volumetric_end = d_ + VFOK
    sc.render.filepath = f; t = time.time(); bpy.ops.render.render(write_still=True); print(f'frame {n} {time.time() - t:.1f} s'); sys.stdout.flush()
