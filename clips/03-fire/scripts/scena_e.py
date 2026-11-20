# Clip 3 'Fire', scene E (finale): a campfire at a cave entrance. Food, warmth, light, protection; an animal's eyes shine from the dark,
# the fire flares and the animal backs away and leaves. Cycles, 24 fps.
#   blender -b --factory-startup --python scena_e.py -- <root> <vse|frames|metki> [--proba] [--kesh=name]
import sys, os, json, time
A = sys.argv[sys.argv.index('--') + 1:]; ROOT, REZHIM = A[0], A[1]; PROBA = '--proba' in A
KESH = ([a.split('=')[1] for a in A if a.startswith('--kesh=')] or ['koster'])[0]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obshchee; obshchee.FPS = 24
from obshchee import *
from priroda import *
from kamni import *
from mathutils import noise
from iskry import Iskry
from bpy_extras.object_utils import world_to_camera_view
FPS = 24; DLIT = 18.0; NF = int(DLIT * FPS)
T_GLAZA, T_VSP, T_POVOROT, T_UHOD = 10.3, 12.2, 14.1, 15.9
RAZ = [a.split('=')[1] for a in A if a.startswith('--razmer=')]
W_, H_ = (int(x) for x in RAZ[0].split('x')) if RAZ else (1920, 1080)
ochistit()
DV = ([a.split('=')[1] for a in A if a.startswith('--dvizhok=')] or ['EEVEE'])[0]
sc = dvizhok(DV, w=W_, h=H_, proc=50 if PROBA else 100, samples=(24 if PROBA else 48) if DV == 'EEVEE' else (40 if PROBA else 80), nf=NF)
rng = np.random.default_rng(3)

# -- ground, cave, sky
zem = Zemlya(razmer=70, n=260, ampl=.22, seed=8, ploshchadka=(0, 0, 4.5), mat=mat_zemli(mokro=.15, cvet=('#3a3026', '#5b4b3a')))
m_kam = mat_kamnya('skala', cvet=('#4a463f', '#8d867b'), mash=1.6, bugry=1.0, treshch=0.0)
m_och = mat_kamnya('ochag', cvet=('#24211d', '#4d4841'), mash=9, bugry=.5, treshch=0.0, sloi=.1, kopot=(0, 0, .15, .7))
m_och.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .9
pe = peshchera(a=4.6, b=5.4, h=3.3, vhod=(90, 40, 52), mat=m_kam, seed=4, naruzhu=(1.6, 1.6, 1.4), ampl_n=.8, nt=260, nf=90); pe.location = (0, -1.5, -.15)
mir = bpy.data.worlds.new('mir'); sc.world = mir; mir.use_nodes = True
bg = mir.node_tree.nodes['Background']; bg.inputs[0].default_value = (.010, .016, .034, 1); bg.inputs[1].default_value = .5
# sky outside: dark clouds with a break (a picture), faintly emissive
bpy.ops.mesh.primitive_cylinder_add(radius=400, depth=260, vertices=64, end_fill_type='NOTHING', location=(0, 0, 110)); nb = bpy.context.object
bpy.ops.object.shade_smooth()
mn = bpy.data.materials.new('nebo'); mn.use_nodes = True; N = mn.node_tree.nodes; N.clear()
o_ = N.new('ShaderNodeOutputMaterial'); em = N.new('ShaderNodeEmission'); ti = N.new('ShaderNodeTexImage'); ti.image = bpy.data.images.load(f'{ROOT}/kartinki/nebo.png')
tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (2, 1, 1); ti.extension = 'MIRROR'
mn.node_tree.links.new(tc.outputs['UV'], mp.inputs['Vector']); mn.node_tree.links.new(mp.outputs[0], ti.inputs['Vector'])
mn.node_tree.links.new(ti.outputs['Color'], em.inputs['Color']); em.inputs['Strength'].default_value = .16
mn.node_tree.links.new(em.outputs[0], o_.inputs['Surface']); nb.data.materials.append(mn); nb.visible_shadow = False
# cold night light from outside (rim)
ln = bpy.data.lights.new('luna', 'SUN'); ln.energy = .09; ln.color = (.55, .68, 1.0); ln.angle = math.radians(4)
lo = bpy.data.objects.new('luna', ln); sc.collection.objects.link(lo); lo.location = (0, 30, 20); smotret(lo, (2, 0, 0))

# -- campfire: a ring of stones, sticks in a tipi, fire from the cache
for i in range(9):
    a = i / 9 * 2 * math.pi + rng.uniform(-.12, .12); r = rng.uniform(.5, .58)
    kamen(f'ochag{i}', (math.cos(a) * r, math.sin(a) * r, .04), razmer=(rng.uniform(.11, .17), rng.uniform(.09, .14), rng.uniform(.07, .1)), seed=10 + i, mat=m_och, podr=3)
m_suk = mat_dereva('suk', cvet=('#0b0705', '#22160d'), ugol=.5, zhar=.55); m_suk2 = mat_dereva('suk-svezhiy', ugol=.35)
m_suk.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = 1.0
m_suk.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value = 0.0          # no specular: next to the fire a highlight turns charred sticks cream-coloured
for i in range(9):
    a = i / 9 * 2 * math.pi + rng.uniform(-.25, .25); r = rng.uniform(.3, .4)
    suk(f'suk{i}', (math.cos(a) * r, math.sin(a) * r, .03), (math.cos(a + 3.3) * .04, math.sin(a + 3.3) * .04, rng.uniform(.26, .36)), r=rng.uniform(.018, .03), seed=i, mat=m_suk)
for i in range(4):
    a = rng.uniform(0, 6.28); suk(f'lezhit{i}', (math.cos(a) * .3, math.sin(a) * .3, .035), (math.cos(a + 2.6) * .28, math.sin(a + 2.6) * .28, .05), r=.022, seed=40 + i, mat=m_suk)
# a branch that burns through and settles, causing the flare
pad = suk('padaet', (.02, -.3, .05), (-.05, .06, .46), r=.026, seed=77, mat=m_suk)
f_v = int(T_VSP * FPS) + 1
pad.keyframe_insert('rotation_euler', frame=f_v - 2); pad.keyframe_insert('location', frame=f_v - 2)
pad.rotation_euler = (math.radians(38), math.radians(-14), 0); pad.location = (0, .05, -.03)
pad.keyframe_insert('rotation_euler', frame=f_v + 5); pad.keyframe_insert('location', frame=f_v + 5)
def vsp(t):                                     # light multiplier during the flare
    d = t - T_VSP
    return 1.0 if d < 0 else 1 + 1.1 * math.exp(-((d - .35) / .5) ** 2) + .25 * math.exp(-d / 1.5)
# fire: a seamless loop of the baked campfire; during the flare the flame is brighter and taller
kd = f'{ROOT}/sim/{KESH}'
NIZ = tuple(float(x) for x in os.environ.get('OG_NIZ', '.04,.4,.12').split(','))          # weaker flame right at the logs: the sticks stay dark instead of cream
og, m_og = koster_petlya(kd, sila=float(os.environ.get('OG_SILA', 22)), dym=.5, nf=NF, mnozh=lambda n: vsp((n - 1) / FPS) ** .8, niz=NIZ if NIZ[2] < 1 else None)
for o in og:
    for n in range(0, NF + 2):
        v = vsp((n - 1) / FPS); o.scale = (1 + .12 * (v - 1), 1 + .12 * (v - 1), 1 + .3 * (v - 1)); o.location = (-.65 * o.scale[0], -.65 * o.scale[1], 0)
        o.keyframe_insert('scale', frame=n); o.keyframe_insert('location', frame=n)
K_TEN = float(os.environ.get('OG_TEN', .45))     # v3 fix ('people's shadows are too black'): share of campfire light for which the people silhouettes cast no shadow
PODSVET = []
for j, (z, s_, r_) in enumerate(((.45, 170., .06), (.8, 45., .25))):
    svet_kostra(f'svet{j}', (0, 0, z), sila=s_ * (1 - K_TEN), cvet=(1.0, .55, .23), seed=j + 1, nf=NF + 2, radius=r_, glubina=.28, mnozh=lambda n: vsp((n - 1) / FPS))
    PODSVET.append(svet_kostra(f'podsvet{j}', (0, 0, z), sila=s_ * K_TEN, cvet=(1.0, .55, .23), seed=j + 1, nf=NF + 2, radius=r_, glubina=.28, mnozh=lambda n: vsp((n - 1) / FPS)))
# embers and sparks
isk = Iskry('iskry', sila=60.)
isk.vsplesk(0, (0, 0, .35), napr=(0, 0, 1), n=300, skorost=(.3, 1.6), konus=.5, zhizn=(1.0, 3.2), g=0, drag=1.2, r=.0016, yark=.9,
            razbros_mesta=.1, turb=2.2, pod=1.3, dlit=DLIT, ostyv=1.2)
isk.vsplesk(T_VSP + .08, (0, 0, .3), napr=(0, 0, 1), n=200, skorost=(.8, 4.2), konus=.75, zhizn=(.7, 2.6), g=2.5, drag=1.1, r=.002, yark=1.1,
            razbros_mesta=.08, turb=3.0, pod=1.8, dlit=.25)

# -- food: meat on a sharpened stick at the edge of the fire
palka = suk('palka', (.62, -.5, -.03), (.3, -.24, .43), r=.011, seed=5, mat=m_suk2, izgib=.03, utonenie=.5)
bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1, location=(.322, -.258, .405)); mya = bpy.context.object; mya.name = 'myaso'
import kamni as _k
for v in mya.data.vertices:
    c = v.co; kk = 1 + .35 * math.sin(c.x * 2.6 + .5) * (1 if c.z > 0 else .6)          # an irregular piece: one side thicker
    v.co = Vector((c.x * .1, c.y * .05 * kk, c.z * .05 * kk))
_k._shum(mya.data, .011, 22, 3, okt=4, greben=.3); bpy.ops.object.shade_smooth(); mya.rotation_euler = (.1, -.95, .75)
mm = bpy.data.materials.new('myaso'); mm.use_nodes = True; b_ = mm.node_tree.nodes['Principled BSDF']
nsm = mm.node_tree.nodes.new('ShaderNodeTexNoise'); nsm.inputs['Scale'].default_value = 45; nsm.inputs['Detail'].default_value = 8
crm = mm.node_tree.nodes.new('ShaderNodeValToRGB'); crm.color_ramp.elements[0].position = .35; crm.color_ramp.elements[0].color = (*L('#3a0f07'), 1)
crm.color_ramp.elements[1].position = .7; crm.color_ramp.elements[1].color = (*L('#8a3216'), 1)
bmm = mm.node_tree.nodes.new('ShaderNodeBump'); bmm.inputs['Strength'].default_value = .7; bmm.inputs['Distance'].default_value = .004
mm.node_tree.links.new(nsm.outputs['Fac'], crm.inputs['Fac']); mm.node_tree.links.new(crm.outputs['Color'], b_.inputs['Base Color'])
mm.node_tree.links.new(nsm.outputs['Fac'], bmm.inputs['Height']); mm.node_tree.links.new(bmm.outputs[0], b_.inputs['Normal'])
b_.inputs['Roughness'].default_value = .62; mya.data.materials.append(mm)
try: b_.inputs['Specular IOR Level'].default_value = .25
except Exception: pass
kost_m = suk('kost-myasa', (.36, -.29, .385), (.455, -.36, .345), r=.009, seed=8, mat=mat_prostoy('kost-m', L('#b8ab92'), .5), izgib=.02, utonenie=-.5)
# a flat stone with burnt bones
kamen('plita', (.95, -.85, .02), razmer=(.28, .2, .05), seed=31, mat=m_kam, ploskiy=.5)
m_kost = mat_prostoy('kost', L('#3a322a'), .6)
for i in range(3): suk(f'kost{i}', (.85 + .08 * i, -.9 + .05 * i, .075), (.98 + .06 * i, -.8 - .03 * i, .08), r=.011, seed=60 + i, mat=m_kost, izgib=.02, utonenie=-.3)

# -- warmth: a hide to sit on by the fire
def shkura(mesto, razm=(1.3, .9), seed=2):
    nr, na = 26, 120; V = [(0, 0, .03)]; F = []
    for j in range(1, nr + 1):
        for i in range(na):
            a = i / na * 2 * math.pi; u = j / nr
            kr = 1 + .16 * math.sin(a * 4 + 1) + .10 * math.sin(a * 7 + 2.2) + .07 * noise.noise(Vector((math.cos(a) * 2.5, math.sin(a) * 2.5, seed)))
            x, y = math.cos(a) * razm[0] / 2 * u * kr, math.sin(a) * razm[1] / 2 * u * kr
            z = .012 + .03 * (1 - u ** 3) + .018 * noise.fractal(Vector((x * 3.5, y * 3.5, seed)), 1, 2, 4) + float(zem.z(mesto[0] + x, mesto[1] + y)) - mesto[2]
            V.append((x, y, z))
    for i in range(na): F.append((0, 1 + i, 1 + (i + 1) % na))
    for j in range(1, nr):
        for i in range(na):
            a0, a1 = 1 + (j - 1) * na + i, 1 + (j - 1) * na + (i + 1) % na; F.append((a0, a0 + na, a1 + na, a1))
    me = bpy.data.meshes.new('shkura'); me.from_pydata(V, [], F); me.update()
    me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool))
    o = bpy.data.objects.new('shkura', me); sc.collection.objects.link(o); o.location = mesto
    m = bpy.data.materials.new('shkura'); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']
    ns = nt.nodes.new('ShaderNodeTexNoise'); ns.inputs['Scale'].default_value = 140; ns.inputs['Detail'].default_value = 8
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 5; n2.inputs['Detail'].default_value = 4
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (*L('#0e0805'), 1); cr.color_ramp.elements[1].color = (*L('#33210f'), 1)
    bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = 1.0; bm.inputs['Distance'].default_value = .012
    nt.links.new(n2.outputs['Fac'], cr.inputs['Fac']); nt.links.new(cr.outputs['Color'], b.inputs['Base Color'])
    nt.links.new(ns.outputs['Fac'], bm.inputs['Height']); nt.links.new(bm.outputs[0], b.inputs['Normal']); b.inputs['Roughness'].default_value = 1.0
    me.materials.append(m); return o
shk = shkura((-1.05, -.75, float(zem.z(-1.05, -.75))))

# -- light: a work spot by the wall, white quartz flakes and a hammerstone pebble on a flat stone; people's shadows on the wall
kamen('rab-plita', (-2.35, -1.75, .05), razmer=(.42, .3, .08), seed=41, mat=m_kam, ploskiy=.45)
m_kv = mat_prostoy('kvarc', L('#d9d6cf'), .35)
for i in range(7):
    kamen(f'otshchep{i}', (-2.35 + rng.uniform(-.25, .25), -1.75 + rng.uniform(-.16, .16), .105), razmer=(rng.uniform(.018, .04), rng.uniform(.012, .025), .006), seed=50 + i, mat=m_kv, podr=1)
kamen('otboynik', (-2.1, -1.62, .13), razmer=(.05, .04, .035), seed=59, mat=mat_kamnya('galka', cvet=('#4a4640', '#8b857b'), mash=8, bugry=.2), podr=3)
for i, (f, vys, y) in enumerate((('lyudi-1', 1.0, -.55), ('lyudi-2', .62, .28), ('lyudi-3', .98, 1.05))):
    kartochka(f'ten{i}', f'{ROOT}/kartinki/{f}.png', vys * 1.15, (-2.75, y * 1.25 + .2, .0), povorot_z=math.pi / 2, tolko_ten=True)

# -- grass outside at the entrance
cen = np.stack([rng.uniform(-9, 10, 2600), rng.uniform(3.9, 26, 2600)], 1)
gust = np.array([noise.fractal(Vector((x * .22, y * .22, 4.0)), 1, 2, 3) for x, y in cen])       # patches: grass where the noise is high
cen = cen[(gust > -.05) & ((np.abs(cen[:, 0] - .9) > 1.1) | (cen[:, 1] > 8.6))]            # the way to the fire and the animal's spot stay clear
cen = np.concatenate([cen, np.array([[.3, 5.2], [1.8, 5.3], [.0, 6.0], [2.1, 6.2], [1.15, 5.0]])])
tr = trava('trava', cen, vys=(.3, .85), v_kochke=(14, 36), seed=4, z_fn=zem.z)
# distant hills: a dark rim on the horizon
xs_ = np.linspace(-140, 140, 120); Vh = []; Fh = []
for i, x in enumerate(xs_):
    hh = 5 + 9 * (noise.fractal(Vector((x * .012, 3.3, 0)), 1, 2, 4) * .5 + .5) + 2 * noise.fractal(Vector((x * .06, 1.1, 0)), 1, 2, 3)
    Vh += [(x, 120 - abs(x) * .25, -2), (x, 120 - abs(x) * .25, hh)]
    if i: Fh.append((2 * i - 2, 2 * i, 2 * i + 1, 2 * i - 1))
meh = bpy.data.meshes.new('holmy'); meh.from_pydata(Vh, [], Fh); meh.update(); oh = bpy.data.objects.new('holmy', meh); sc.collection.objects.link(oh)
oh.data.materials.append(mat_prostoy('holmy', (.004, .005, .008), 1.0))

# -- the animal: two cards (front and profile) + glowing eyes
GH = 1.143; GW = GH * 2528 / 1696
P_AN = np.array([1.0, 5.6]); P_OT = np.array([1.35, 7.4]); P_PR0 = np.array([1.75, 7.5]); P_PR1 = np.array([4.0, 10.2])
an = kartochka('giena-anfas', f'{ROOT}/kartinki/giena-anfas.png', GH, (P_AN[0], P_AN[1], float(zem.z(*P_AN)) - .04), svet=2.0)
pr = kartochka('giena-profil', f'{ROOT}/kartinki/giena-profil.png', GH * 1.02, (P_PR0[0], P_PR0[1], float(zem.z(*P_PR0)) - .04), svet=3.0)
glaza = []
mg = bpy.data.materials.new('glaz'); mg.use_nodes = True; Ng = mg.node_tree.nodes; Ng.clear()
og_ = Ng.new('ShaderNodeOutputMaterial'); eg = Ng.new('ShaderNodeEmission'); eg.inputs['Color'].default_value = (*L('#E6D060'), 1)
mg.node_tree.links.new(eg.outputs[0], og_.inputs['Surface'])
for px, py in ((682, 707), (877, 700)):
    bpy.ops.mesh.primitive_circle_add(vertices=20, radius=.0165, fill_type='NGON', location=(0, 0, 0)); g = bpy.context.object
    g.rotation_euler = (math.radians(90), 0, 0); g.parent = an; g.location = ((px / 2528 - .5) * GW, -.012, (1 - py / 1696) * GH)
    g.data.materials.append(mg); g.visible_shadow = False; glaza.append(g)
def kl(obj_sock, val, n): obj_sock.default_value = val; obj_sock.keyframe_insert('default_value', frame=n)
s_an = an.data.materials[0].node_tree.nodes['sila'].outputs[0]; p_an = an.data.materials[0].node_tree.nodes['prozr'].outputs[0]
s_pr = pr.data.materials[0].node_tree.nodes['sila'].outputs[0]; p_pr = pr.data.materials[0].node_tree.nodes['prozr'].outputs[0]
sg = eg.inputs['Strength']
rg = np.random.default_rng(9); drozh = np.convolve(rg.standard_normal(NF + 40), np.ones(5) / 5, 'same')
sm_ = lambda u: (lambda x: x * x * (3 - 2 * x))(max(0., min(1., u)))
for n in range(0, NF + 2):
    t = (n - 1) / FPS
    # front view: steps out of the dark to the edge of the light, after the flare crouches and backs away, then dissolves
    vyh = sm_((t - (T_GLAZA - .9)) / 1.6); ot = sm_((t - (T_VSP + .25)) / 1.7); ischez = sm_((t - T_POVOROT) / .4)
    p = np.array([1.25, 7.0]) * (1 - vyh) + P_AN * vyh; p = p * (1 - ot) + P_OT * ot
    prised = -.07 * math.exp(-((t - (T_VSP + .45)) / .28) ** 2)
    an.location = (p[0], p[1], float(zem.z(*p)) - .04 + prised); an.keyframe_insert('location', frame=n)
    kl(p_an, (1 - ischez) * sm_((t - (T_GLAZA - 1.2)) / .8), n)
    svet = (.55 + .45 * vyh) * (1 - .45 * ot) * vsp(t) ** 1.3 * (1 + .1 * drozh[n])
    kl(s_an, 2.0 * svet, n)
    # eyes: light up, 'breathe', blink, flare with the fire, go out when the head turns
    gl = sm_((t - T_GLAZA) / .35) * (1 - sm_((t - (T_POVOROT - .25)) / .3))
    for tm in (11.45, 13.35):
        if abs(t - tm) < .07: gl *= .04
    kl(sg, 34 * gl * (1 + .22 * drozh[n + 20]) * vsp(t) ** 1.5 * (1 - .35 * ot), n)
    # profile: turns and walks off to the right into the dark
    u = sm_((t - T_POVOROT) / (T_UHOD - T_POVOROT)); q = P_PR0 * (1 - u) + P_PR1 * u
    pr.location = (q[0], q[1], float(zem.z(*q)) - .04); pr.keyframe_insert('location', frame=n)
    kl(p_pr, sm_((t - (T_POVOROT + .05)) / .4) * (1 - sm_((t - (T_UHOD - 1.1)) / 1.1)), n)
    kl(s_pr, 3.2 * (1 - .7 * u) * (1 + .1 * drozh[n]), n)

# -- camera: keys (time, position, target, focus)
KL = [(0.0, (1.0, -1.05, .43), (.28, -.2, .37), 1.05), (3.6, (1.0, -1.7, .62), (.05, -.1, .4), 1.9), (6.3, (.7, -3.0, 1.0), (-.7, -.1, .45), 3.2),
      (8.9, (.75, -3.0, 1.08), (-3.4, .5, 1.55), 4.6), (11.3, (.85, -2.3, .96), (.95, 5.6, .7), 8.0), (15.6, (.85, -1.7, .92), (1.2, 6.4, .66), 8.6),
      (18.0, (.8, -3.7, 1.25), (.6, 5.0, .9), 4.2)]
kam = kamera(lens=40, dof=1.0, fstop=2.4)
def interp(t):
    for i in range(len(KL) - 1):
        if t <= KL[i + 1][0]:
            u = sm_((t - KL[i][0]) / (KL[i + 1][0] - KL[i][0]))
            return [np.array(KL[i][k]) * (1 - u) + np.array(KL[i + 1][k]) * u for k in (1, 2, 3)]
    return [np.array(KL[-1][k]) for k in (1, 2, 3)]
for n in range(1, NF + 1):
    p, c, fk = interp((n - 1) / FPS); kam.location = p; smotret(kam, c); kam.data.dof.focus_distance = float(fk)
    t_ = (n - 1) / FPS; kam.data.lens = 40 + 16 * sm_((t_ - 9.6) / 4.5) - 14 * sm_((t_ - 16.2) / 1.8); kam.data.keyframe_insert('lens', frame=n)
    kam.keyframe_insert('location', frame=n); kam.keyframe_insert('rotation_euler', frame=n); kam.data.dof.keyframe_insert('focus_distance', frame=n)

# -- label points for the edit: caption anchors on screen
TOCHKI = dict(eda=(.325, -.262, .46), teplo=(-1.0, -.7, .12), svet=(-3.9, .4, 1.7), ogon=(0, 0, .5))
def proj(v):
    c = world_to_camera_view(sc, kam, Vector(v)); return [round(c.x, 4), round(1 - c.y, 4), round(c.z, 3)]
if REZHIM in ('vse', 'metki'):
    M = dict(kadry=[], fps=FPS, dlit=DLIT, t=dict(glaza=T_GLAZA, vsp=T_VSP, povorot=T_POVOROT, uhod=T_UHOD))
    for n in range(1, NF + 1):
        sc.frame_set(n); d = {k: proj(v) for k, v in TOCHKI.items()}
        d['glaza'] = proj(tuple(glaza[0].matrix_world.translation * .5 + glaza[1].matrix_world.translation * .5)); d['vsp'] = round(vsp((n - 1) / FPS), 3)
        M['kadry'].append(d)
    json.dump(M, open(f'{ROOT}/metki-E.json', 'w'))
    if REZHIM == 'metki': sys.exit(0)
# doubles of the campfire lights: everything casts shadows except the people silhouettes (ten0-ten2), so their shadows on the wall are not black
_blok = bpy.data.collections.new('bez-lyudey')
for o in sc.objects:
    if o.type == 'MESH' and not o.name.startswith('ten'): _blok.objects.link(o)
for o in PODSVET: o.light_linking.blocker_collection = _blok
out = f'{ROOT}/kadry/E' + ('-proba' if PROBA else ''); os.makedirs(out, exist_ok=True)
for n in spisok_kadrov(REZHIM, NF):
    f = f'{out}/{n:04d}.png'
    if os.path.exists(f) and not PROBA: continue
    sc.frame_set(n); isk.obnovit((n - 1) / FPS, vyderzhka=1 / 70)
    sc.render.filepath = f; t = time.time(); bpy.ops.render.render(write_still=True); print(f'frame {n} {time.time() - t:.1f} s'); sys.stdout.flush()
