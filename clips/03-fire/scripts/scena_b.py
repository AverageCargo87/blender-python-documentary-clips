# Clip 3 'Fire', scene B: fire is carried into a cave and kept alive. EEVEE, 24 fps.
# B1: a burning firebrand is carried through the grass (the camera walks alongside, the tree burns in the distance). B2: a rock with a cave: the light goes inside,
# the cave glows from within; night turns to day and back to night, and the fire inside keeps burning.
#   blender -b --factory-startup --python scena_b.py -- <root> <B1|B2> <vse|frames|metki> [--proba]
import sys, os, json, time
A = sys.argv[sys.argv.index('--') + 1:]; ROOT, PLAN, REZHIM = A[0], A[1], A[2]; PROBA = '--proba' in A
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import obshchee; obshchee.FPS = 24
from obshchee import *
from priroda import *
from kamni import *
from iskry import Iskry
from mathutils import noise
from bpy_extras.object_utils import world_to_camera_view
import obshchee_a as OA, obshchee_b as OB
FPS = 24; DL = {'B1': OB.DL_B1, 'B2': 6.4}; DLIT = DL[PLAN]; NF = int(round(DLIT * FPS))
def mat_golovni():
    # charred branch: embers glow in the cracks only near the end (the end is at the object origin)
    m = mat_dereva('golovnya', cvet=('#030201', '#0a0705'), ugol=.6, zhar=0.0); nt = m.node_tree; b = nt.nodes['Principled BSDF']; k = nt.links.new
    b.inputs['Roughness'].default_value = 1.0
    try: b.inputs['Specular IOR Level'].default_value = 0.0          # next to the light the specular highlight made the stick look whitish
    except Exception: pass
    tc = nt.nodes.new('ShaderNodeTexCoord'); ln = nt.nodes.new('ShaderNodeVectorMath'); ln.operation = 'LENGTH'
    mr = nt.nodes.new('ShaderNodeMapRange'); mr.inputs['From Min'].default_value = .2; mr.inputs['From Max'].default_value = .02; mr.inputs['To Min'].default_value = 0; mr.inputs['To Max'].default_value = 1
    ns = nt.nodes.new('ShaderNodeTexNoise'); ns.inputs['Scale'].default_value = 40; ns.inputs['Detail'].default_value = 5
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].position = .42; cr.color_ramp.elements[0].color = (0, 0, 0, 1); cr.color_ramp.elements[1].position = .62; cr.color_ramp.elements[1].color = (1, 1, 1, 1)
    ml = nt.nodes.new('ShaderNodeMath'); ml.operation = 'MULTIPLY'; m2 = nt.nodes.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'; m2.inputs[1].default_value = 9.0
    k(tc.outputs['Object'], ln.inputs[0]); k(ln.outputs['Value'], mr.inputs['Value']); k(tc.outputs['Object'], ns.inputs['Vector']); k(ns.outputs['Fac'], cr.inputs['Fac'])
    k(mr.outputs['Result'], ml.inputs[0]); k(cr.outputs['Color'], ml.inputs[1]); k(ml.outputs[0], m2.inputs[0]); k(m2.outputs[0], b.inputs['Emission Strength'])
    b.inputs['Emission Color'].default_value = (1.0, .26, .03, 1)
    return m
ochistit()
sc = dvizhok('EEVEE', w=1920, h=1080, proc=50 if PROBA else 100, samples=20 if PROBA else 48, nf=NF)
rng = np.random.default_rng(11)
sm_ = lambda u: (lambda x: x * x * (3 - 2 * x))(max(0., min(1., u)))
def proj(v):
    c = world_to_camera_view(sc, kam, Vector(v)); return [round(c.x, 4), round(1 - c.y, 4), round(c.z, 3)]
def nebo_cil(R_=1400., H_=640., baza=.34, sdvig_x=.92, mash=2.6):
    bpy.ops.mesh.primitive_cylinder_add(radius=R_, depth=H_, vertices=96, end_fill_type='NOTHING', location=(0, 0, H_ / 2 - 70)); o = bpy.context.object; o.name = 'nebo'
    bpy.ops.object.shade_smooth()
    m = bpy.data.materials.new('nebo'); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; N.clear(); k = nt.links.new
    out = N.new('ShaderNodeOutputMaterial'); em = N.new('ShaderNodeEmission'); tc = N.new('ShaderNodeTexCoord')
    img = N.new('ShaderNodeTexImage'); img.image = bpy.data.images.load(f'{ROOT}/kartinki/nebo.png'); img.extension = 'MIRROR'
    mp = N.new('ShaderNodeMapping'); mp.name = 'sdvig'; mp.inputs['Scale'].default_value = (mash, 1.0, 1.0); mp.inputs['Location'].default_value = (sdvig_x, 0, 0)
    ton = N.new('ShaderNodeMix'); ton.data_type = 'RGBA'; ton.blend_type = 'MULTIPLY'; ton.name = 'ton'; ton.inputs['Factor'].default_value = 1.0; ton.inputs['B'].default_value = (1, 1, 1, 1)
    k(tc.outputs['UV'], mp.inputs['Vector']); k(mp.outputs[0], img.inputs['Vector']); k(img.outputs['Color'], ton.inputs['A']); k(ton.outputs['Result'], em.inputs['Color'])
    em.inputs['Strength'].default_value = baza; em.name = 'svet'; k(em.outputs[0], out.inputs['Surface'])
    o.data.materials.append(m); o.visible_shadow = False
    return o, em.inputs['Strength'], ton.inputs['B'], mp.inputs['Location']
mir = bpy.data.worlds.new('mir'); sc.world = mir; mir.use_nodes = True
bg = mir.node_tree.nodes['Background']; bg.inputs[0].default_value = (.03, .042, .075, 1); bg.inputs[1].default_value = 2.0 if PLAN == 'B1' else .9

if PLAN == 'B1':
    # -- the savanna from scene A: the same tree in the distance, burning
    zem, z0, der, VERH, RAZV = OA.osnova()
    zem.ob.data.materials[0] = mat_zemli(mokro=.25, cvet=('#33291d', '#5a4a33'))
    Y0 = -62.0; X0 = -9.0                                       # path: runs along +X at a distance from the tree
    zt = float(zem.z(X0 + 3.4, Y0)); DZ = .35                    # ground height on the path; firebrand lift above the simulated height
    def golovnya(t):
        x, y, z = OB.put_golovni(t); return np.array([X0 + x, Y0 + y, zt + z + DZ])
    nebo_cil(mash=2.0, sdvig_x=.78)
    # fire on the distant tree: the last frames of its simulation, looped
    kd = f'{ROOT}/sim/derevo'
    if os.path.exists(kd + '/gotovo.txt'):
        nk = json.load(open(kd + '/gotovo.txt'))['kadrov']
        obyom_iz_kesha(kd, imya='ogon-derevo', mat=mat_ognya('ogon-d', sila=18, dym=0.0, shum=True), sdvig=nk - NF - 2, rezhim='EXTEND', shum=True)
        try: sc.eevee.volumetric_tile_size = '2'; sc.eevee.volumetric_samples = 256; sc.eevee.volumetric_end = 95.0; sc.eevee.volumetric_sample_distribution = .92
        except Exception: pass
    else: print('NO TREE CACHE')
    for j, p in enumerate(((RAZV + np.array([-.6, -.8, 1.2])), ((VERH + RAZV) / 2 + np.array([-.5, -1.2, 1.5])))):
        svet_kostra(f'derevo-svet{j}', tuple(p + np.array([-1.0, -1.6, .4])), sila=2400, cvet=(1.0, .5, .2), seed=j, nf=NF + 2, radius=.8, glubina=.3)
    # the camera walks beside the fire, slightly slower; the flame crosses the frame from left to right
    kam = kamera(lens=50, dof=3.3, fstop=2.0)
    for n in range(1, NF + 1):
        t = (n - 1) / FPS; g = golovnya(t); e = t / DLIT
        kam.location = (g[0] + 1.0 - 2.1 * e, Y0 - 3.3, zt + 1.22 + .012 * math.sin(t * 5.5)); smotret(kam, (g[0] + .15 - .9 * e, Y0 + 2.0, zt + 1.5))
        kam.keyframe_insert('location', frame=n); kam.keyframe_insert('rotation_euler', frame=n)
    # grass: along the path (both sides, the path itself is clear), sparse further out up to the tree
    xs_ = rng.uniform(X0 - 5, X0 + 14, 2600); ys_ = Y0 + rng.normal(0, 1, 2600) * 3.2; ok = np.abs(ys_ - Y0) > .32
    c1 = np.stack([xs_[ok], ys_[ok]], 1)
    c2 = np.stack([rng.uniform(X0 - 30, X0 + 40, 2600), rng.uniform(Y0 + 6, Y0 + 60, 2600)], 1)
    g2 = np.array([noise.fractal(Vector((x * .15, y * .15, 2.0)), 1, 2, 3) for x, y in c2]); c2 = c2[g2 > -.2]
    tr1 = trava('trava-bl', c1, vys=(.55, 1.15), v_kochke=(20, 44), seed=5, z_fn=zem.z); tr2 = trava('trava-dal', c2, vys=(.5, 1.0), v_kochke=(8, 18), shir=.014, seed=6, z_fn=zem.z)
    veter(tr1, sila=.1, poryv=(.6, .25, 0), skorost=.9); veter(tr2, sila=.1, poryv=(.6, .25, 0), imya='veter2', skorost=.9)
    # firebrand: a thick branch, a red-hot end, flame from the simulation, light, sparks
    m_g = mat_golovni()
    gol = suk('golovnya', (-.42, 0, -.2), (0, 0, 0), r=.03, seed=4, mat=m_g, izgib=.04, utonenie=.2)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=.028); ug = bpy.context.object; ug.name = 'ugol'; ug.scale = (1.4, .9, .9)
    mu = bpy.data.materials.new('ugol'); mu.use_nodes = True; Nu = mu.node_tree.nodes; Nu.clear(); ou = Nu.new('ShaderNodeOutputMaterial'); eu = Nu.new('ShaderNodeEmission')
    eu.inputs['Color'].default_value = (1.0, .3, .04, 1); eu.inputs['Strength'].default_value = 9; mu.node_tree.links.new(eu.outputs[0], ou.inputs['Surface']); ug.data.materials.append(mu)
    sv = svet_kostra('svet', (0, 0, 0), sila=110, cvet=(1.0, .55, .22), seed=3, nf=NF + 2, radius=.07, glubina=.3)
    sv.animation_data_clear()
    kd = f'{ROOT}/sim/golovnya'; og = None
    if os.path.exists(kd + '/gotovo.txt'):
        og = obyom_iz_kesha(kd, mat=mat_ognya('ogon', sila=30, dym=0.0), sdvig=22, rezhim='EXTEND')       # source inside the domain: (.75, .25, .12) from its corner
    else: print('NO FIREBRAND CACHE')
    # the person: a figure waist-deep in grass; the fist is at the lower end of the firebrand
    CH = 1.72; CW = CH * 1380 / 2240
    ch = kartochka('chelovek', f'{ROOT}/kartinki/chelovek-cvet.png', CH, (0, 0, 0), svet=float(os.environ.get('OG_CH_SVET', .03)), diffuz=float(os.environ.get('OG_CH_DIF', .62)))   # painted figure, lit by the firebrand (v3)
    ch.scale = (-1, 1, 1)        # mirrored: walks to the right
    isk = Iskry('iskry', sila=60.)
    for n in range(0, NF + 2):
        t = (n - 1) / FPS; g = golovnya(t)
        gol.location = tuple(g); gol.keyframe_insert('location', frame=n); ug.location = tuple(g); ug.keyframe_insert('location', frame=n)
        if og is not None: og.location = (g[0] - .75, g[1] - .25, g[2] - .12); og.keyframe_insert('location', frame=n)
        sv.location = (g[0] - .05, g[1] - .22, g[2] + .3); sv.keyframe_insert('location', frame=n)
        kul = g + np.array([-.42, 0, -.2])                                          # fist
        ch.location = (kul[0] - (.925 - .5) * CW, Y0 + .05, kul[2] - (1 - .203) * CH); ch.keyframe_insert('location', frame=n)
    for k_ in range(70):
        tk = -.2 + k_ * (DLIT + .2) / 70; g = golovnya(tk)
        isk.vsplesk(tk, tuple(g), napr=(-1, 0, .5), n=5, skorost=(.2, 1.3), konus=.8, zhizn=(.4, 1.4), g=1.0, drag=2.0, r=.0028, yark=1.0, turb=3.0, pod=1.6, dlit=.08)
    TOCH = lambda n: dict(ogon=proj(tuple(golovnya((n - 1) / FPS))))
else:
    # -- B2: a rock outcrop with a cave in the savanna
    zem = Zemlya(razmer=260, n=260, ampl=1.0, seed=14, ploshchadka=(0, 0, 9), mat=mat_zemli(mokro=.1, cvet=('#3a3023', '#66553c')))
    z0 = float(zem.z(0, 0))
    m_kam = mat_kamnya('skala', cvet=('#3d362d', '#7a705f'), mash=1.3, bugry=1.0, treshch=0.0)
    m_vn = mat_kamnya('skala-vnutri', cvet=('#14120f', '#2e2a24'), mash=1.3, bugry=1.0, treshch=0.0)
    AZ = 228.                                                    # direction the entrance faces, deg
    pe = peshchera(a=5.0, b=5.0, h=3.3, vhod=(AZ, 30, 46), mat=m_kam, seed=6, ampl=.6, naruzhu=(3.2, 3.6, 2.6), ampl_n=1.5, nt=260, nf=90, mat_vnutri=m_vn); pe.location = (0, 0, z0 - .2)
    vx, vy = math.cos(math.radians(AZ)), math.sin(math.radians(AZ))
    P_VHOD = np.array([vx * 8.6, vy * 8.6])                      # at the entrance
    for i, (x, y, s_) in enumerate(((9.5, -3.5, 1.5), (-7.5, 7.5, 1.9), (10.5, 4.5, 1.6), (4.0, -10.3, .8), (-10.4, -2.0, .9), (-11.5, -8.0, .45), (-1.0, 11.0, 1.8), (8.2, 8.2, 1.9), (-4.5, -11.5, .35), (-8.8, -10.4, .28), (1.5, -12.5, .3), (-13.0, -4.5, .5))):
        kamen(f'glyba{i}', (x, y, float(zem.z(x, y)) + .3 * s_), razmer=(1.6 * s_, 1.3 * s_, 1.05 * s_), seed=80 + i, mat=m_kam, podr=4)
    for i, (x, y, s_) in enumerate([(-38, 46, 1.0), (30, 70, .9), (62, 24, 1.1), (-70, 95, 1.2)]):
        derevo(seed=40 + i, osnova=(x, y, float(zem.z(x, y)) - .2), vys=8.5 * s_, stvol=3.4 * s_, m=1.35 * s_, r0=.36, imya=f'dal{i}', plotn_listvy=.6)
    neb, neb_s, neb_ton, neb_loc = nebo_cil(baza=.34, sdvig_x=.3)
    # camera: looks into the entrance, slowly approaches
    kam = kamera(lens=35, dof=None)
    K0 = np.array([vx * 22.0 + 2.5, vy * 22.0 - 1.0]); K1 = np.array([vx * 18.0 + 2.0, vy * 18.0 - .8])
    for n in range(1, NF + 1):
        e = sm_((n - 1) / (NF - 1)); p = K0 * (1 - e) + K1 * e
        kam.location = (p[0], p[1], float(zem.z(*p)) + 1.35); smotret(kam, (vx * 3.0, vy * 3.0, z0 + 2.3))
        kam.keyframe_insert('location', frame=n); kam.keyframe_insert('rotation_euler', frame=n)
    # grass around (trampled right at the entrance)
    c = np.stack([rng.uniform(-45, 30, 5200), rng.uniform(-50, 30, 5200)], 1)
    d_v = np.linalg.norm(c - P_VHOD, axis=1); d_c = np.linalg.norm(c, axis=1)
    g_ = np.array([noise.fractal(Vector((x * .13, y * .13, 5.0)), 1, 2, 3) for x, y in c])
    c = c[(d_c > 10.5) & (d_v > 2.2) & (g_ > -.35)]
    tr = trava('trava', c, vys=(.4, .95), v_kochke=(14, 34), seed=4, z_fn=zem.z); veter(tr, sila=.08, poryv=(.5, .2, 0), skorost=.8)
    # timing: 0-2.4 s the light walks to the entrance; 2.4-3.4 a fire flares up inside; 3.4-5.8 a day flies by; then night again
    T_VHOD, T_KOST, T_DEN0, T_DEN1 = 2.4, 2.5, 3.3, 5.95
    def sutki(t):                                                # 0 night .. 1 day .. 0 night
        return 0.0 if t < T_DEN0 or t > T_DEN1 else math.sin((t - T_DEN0) / (T_DEN1 - T_DEN0) * math.pi) ** 1.5          # exponent > 1: sunrise and sunset without a jump
    sol = bpy.data.lights.new('solnce', 'SUN'); sol.angle = math.radians(1.5); so = bpy.data.objects.new('solnce', sol); sc.collection.objects.link(so)
    def mix3(a, b, u): return tuple(a[i] * (1 - u) + b[i] * u for i in range(3))
    NOCH, ZARYA, DEN = (.03, .042, .075), (.42, .26, .2), (.24, .31, .46)
    for n in range(0, NF + 2):
        t = (n - 1) / FPS; s_ = sutki(t); f = (t - T_DEN0) / (T_DEN1 - T_DEN0)          # f: 0 sunrise .. 1 sunset
        nizko = 1 - min(1, s_ / .45)                                                 # 1 at the horizon (dawn), 0 in daytime
        cv = mix3(mix3(NOCH, ZARYA, min(1, s_ / .25)), DEN, sm_((s_ - .2) / .5))
        bg.inputs[0].default_value = (*cv, 1); bg.inputs[0].keyframe_insert('default_value', frame=n)
        bg.inputs[1].default_value = .9 + .15 * s_; bg.inputs[1].keyframe_insert('default_value', frame=n)
        neb_s.default_value = .34 + 2.2 * s_; neb_s.keyframe_insert('default_value', frame=n)
        tn = mix3((1, 1, 1), mix3((1.0, .62, .45), (.95, 1.0, 1.08), 1 - nizko), min(1, s_ * 4))
        neb_ton.default_value = (*tn, 1); neb_ton.keyframe_insert('default_value', frame=n)
        neb_loc.default_value = (.3 + .32 * sm_((t - T_DEN0 + .3) / (T_DEN1 - T_DEN0 + .6)), 0, 0); neb_loc.keyframe_insert('default_value', frame=n)   # clouds drift
        sol.energy = 2.6 * s_ ** 1.2; sol.color = mix3((1.0, .5, .3), (1.0, .84, .66), 1 - nizko)
        sol.keyframe_insert('energy', frame=n); sol.keyframe_insert('color', frame=n)
        az = math.radians(AZ - 80 + 160 * max(0, min(1, f))); vys = math.radians(6 + 24 * s_)       # the sun moves in an arc above the entrance
        so.location = (0, 0, 50); smotret(so, (-math.cos(az) * math.cos(vys) * 50, -math.sin(az) * math.cos(vys) * 50, 50 - math.sin(vys) * 50))
        so.keyframe_insert('rotation_euler', frame=n)
    # fire inside (near the entrance, visible from outside) and its light
    P_K = np.array([vx * 3.4, vy * 3.4]); zk = float(zem.z(*P_K))
    rost_k = lambda n: sm_(((n - 1) / FPS - T_KOST) / 1.3)
    ogs, _m = koster_petlya(f'{ROOT}/sim/koster', sila=24, dym=.5, nf=NF, mnozh=rost_k, mesto=(P_K[0], P_K[1], zk), masshtab=1.15)
    for o in ogs:
        for n in range(0, NF + 2):
            m_ = .3 + .85 * rost_k(n); o.scale = (m_, m_, m_); o.location = (P_K[0] - .65 * m_, P_K[1] - .65 * m_, zk)
            o.keyframe_insert('scale', frame=n); o.keyframe_insert('location', frame=n)
    for j, (z, s_, r_) in enumerate(((.5, 300., .1), (1.0, 110., .3))):
        svet_kostra(f'svet{j}', (P_K[0], P_K[1], zk + z), sila=s_, cvet=(1.0, .55, .23), seed=j + 1, nf=NF + 2, radius=r_, glubina=.25, mnozh=lambda n: sm_(((n - 1) / FPS - T_KOST) / 1.3))
    m_suk = mat_dereva('suk', ugol=.8, zhar=0.0)
    for i in range(8):
        a = i / 8 * 2 * math.pi; suk(f'suk{i}', (P_K[0] + math.cos(a) * .36, P_K[1] + math.sin(a) * .36, zk + .03), (P_K[0], P_K[1], zk + .32), r=.024, seed=i, mat=m_suk)
    # the person with the firebrand walks to the entrance and disappears inside
    CH = 1.72; CW = CH * 1380 / 2240
    ch = kartochka('chelovek', f'{ROOT}/kartinki/chelovek-cvet.png', CH, (0, 0, 0), svet=float(os.environ.get('OG_CH_SVET2', .12)), diffuz=1.0); ch.scale = (-1, 1, 1)
    P0 = P_VHOD + np.array([-vy * 4.2 + vx * 1.2, vx * 4.2 + vy * 1.2]) * 1.0; P1 = P_K + np.array([vx * 1.1, vy * 1.1])
    m_g = mat_golovni(); gol = suk('golovnya', (-.42, 0, -.2), (0, 0, 0), r=.03, seed=4, mat=m_g, izgib=.04, utonenie=.2)
    sv = svet_kostra('svet-g', (0, 0, 0), sila=160, cvet=(1.0, .55, .22), seed=3, nf=NF + 2, radius=.07, glubina=.3, mnozh=lambda n: 1 - sm_(((n - 1) / FPS - T_VHOD) / .5)); sv_fc = sv
    kt = f'{ROOT}/sim/trut'
    ogt = obyom_iz_kesha(kt, imya='ogon-g', mat=mat_ognya('ogon-g', sila=30, dym=.4), sdvig=92, rezhim='EXTEND') if os.path.exists(kt + '/gotovo.txt') else None
    isk = Iskry('iskry', sila=60.)
    ug_a = math.atan2(K0[1], K0[0])                              # card faces the camera
    for n in range(0, NF + 2):
        t = (n - 1) / FPS; e = min(1.15, t / T_VHOD); p = P0 * (1 - e) + P1 * e
        shag = .03 * math.sin(2 * math.pi * 1.75 * t)
        zz = float(zem.z(*p))
        ch.location = (p[0], p[1], zz - .05 + shag); ch.rotation_euler = (0, 0, ug_a + math.pi / 2); ch.keyframe_insert('location', frame=n); ch.keyframe_insert('rotation_euler', frame=n)
        ch.hide_render = t > T_VHOD + .5; ch.keyframe_insert('hide_render', frame=n)
        # the fist and the end of the firebrand lie in the card plane
        ex = np.array([math.cos(ug_a + math.pi / 2), math.sin(ug_a + math.pi / 2)]) * -1.0
        kul = np.array([p[0], p[1]]) + ex * ((.925 - .5) * CW); zk_ = zz - .05 + shag + (1 - .203) * CH
        g = np.array([kul[0] + ex[0] * .42, kul[1] + ex[1] * .42, zk_ + .2])
        gol.location = tuple(g); gol.rotation_euler = (0, 0, ug_a + math.pi / 2 + math.pi); gol.hide_render = t > T_VHOD + .5
        for pth in ('location', 'rotation_euler', 'hide_render'): gol.keyframe_insert(pth, frame=n)
        sv.location = (g[0], g[1], g[2] + .1); sv.keyframe_insert('location', frame=n)
        if ogt is not None:
            ogt.location = (g[0] - .25 * .8, g[1] - .25 * .8, g[2] - .02); ogt.scale = (.8, .8, .8); ogt.hide_render = t > T_VHOD + .4
            ogt.keyframe_insert('location', frame=n); ogt.keyframe_insert('hide_render', frame=n)
        if t <= T_VHOD + .3 and n % 2 == 0:
            isk.vsplesk(t, tuple(g), napr=(0, 0, 1), n=4, skorost=(.2, 1.2), konus=.9, zhizn=(.4, 1.2), g=1.0, drag=2.0, r=.006, yark=1.0, turb=3.0, pod=1.6, dlit=.08)
    isk.vsplesk(T_KOST + .4, (P_K[0], P_K[1], zk + .4), napr=(0, 0, 1), n=90, skorost=(.3, 1.6), konus=.5, zhizn=(1.0, 3.0), g=0, drag=1.2, r=.004, yark=.9, razbros_mesta=.1, turb=2.2, pod=1.3, dlit=DLIT)
    TOCH = lambda n: dict(vhod=proj((P_VHOD[0], P_VHOD[1], z0 + 2.6)), koster=proj((P_K[0], P_K[1], zk + .6)), sutki=round(sutki((n - 1) / FPS), 3))

if REZHIM in ('vse', 'metki'):
    M = dict(kadry=[], fps=FPS, dlit=DLIT)
    for n in range(1, NF + 1):
        sc.frame_set(n); M['kadry'].append(TOCH(n))
    json.dump(M, open(f'{ROOT}/metki-{PLAN}.json', 'w'))
    if REZHIM == 'metki': sys.exit(0)
out = f'{ROOT}/kadry/{PLAN}' + ('-proba' if PROBA else ''); os.makedirs(out, exist_ok=True)
for n in spisok_kadrov(REZHIM, NF):
    f = f'{out}/{n:04d}.png'
    if os.path.exists(f) and not PROBA: continue
    sc.frame_set(n); isk.obnovit((n - 1) / FPS, vyderzhka=1 / 50)
    sc.render.filepath = f; t = time.time(); bpy.ops.render.render(write_still=True); print(f'frame {n} {time.time() - t:.1f} s'); sys.stdout.flush()
