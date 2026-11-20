# Clip 3 'Fire': stones, rocks, the cave, branches, silhouette cards.
import bpy, bmesh, math
import numpy as np
from mathutils import noise, Vector
from obshchee import L, aktivnyy

def mat_kamnya(imya='kamen', cvet=('#3b3833', '#6d675d'), mash=3.0, bugry=.6, sheroh=.82, treshch=.5, sloi=.35, kopot=None):
    """Limestone: mottled grey-brown, gentle bedding, small bumps and rare cracks. kopot=(x, y, z, r): soot near a fire."""
    m = bpy.data.materials.new(imya); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; k = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord')
    n1 = nt.nodes.new('ShaderNodeTexNoise'); n1.inputs['Scale'].default_value = mash * .45; n1.inputs['Detail'].default_value = 12; n1.inputs['Roughness'].default_value = .68
    n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = mash * 7; n2.inputs['Detail'].default_value = 10; n2.inputs['Roughness'].default_value = .7
    n3 = nt.nodes.new('ShaderNodeTexNoise'); n3.inputs['Scale'].default_value = mash * 1.3; n3.inputs['Detail'].default_value = 6
    mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (.25, .25, 5.0)
    n4 = nt.nodes.new('ShaderNodeTexNoise'); n4.inputs['Scale'].default_value = mash * 1.1; n4.inputs['Detail'].default_value = 5; n4.inputs['Distortion'].default_value = .6
    cr = nt.nodes.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].position = .28; cr.color_ramp.elements[0].color = (*L(cvet[0]), 1)
    cr.color_ramp.elements[1].position = .75; cr.color_ramp.elements[1].color = (*L(cvet[1]), 1)
    tr = nt.nodes.new('ShaderNodeMapRange'); tr.inputs['From Min'].default_value = .485; tr.inputs['From Max'].default_value = .5
    tr2 = nt.nodes.new('ShaderNodeMapRange'); tr2.inputs['From Min'].default_value = .5; tr2.inputs['From Max'].default_value = .515; tr2.inputs['To Min'].default_value = 1; tr2.inputs['To Max'].default_value = 0
    tm = nt.nodes.new('ShaderNodeMath'); tm.operation = 'MINIMUM'
    h1 = nt.nodes.new('ShaderNodeMath'); h1.operation = 'MULTIPLY_ADD'; h1.inputs[1].default_value = .22
    h2 = nt.nodes.new('ShaderNodeMath'); h2.operation = 'MULTIPLY_ADD'; h2.inputs[1].default_value = sloi
    h3 = nt.nodes.new('ShaderNodeMath'); h3.operation = 'MULTIPLY_ADD'; h3.inputs[1].default_value = -treshch
    bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = bugry; bm.inputs['Distance'].default_value = .08
    for n_ in (n1, n2, n3): k(tc.outputs['Object'], n_.inputs['Vector'])
    k(tc.outputs['Object'], mp.inputs['Vector']); k(mp.outputs[0], n4.inputs['Vector'])
    k(n3.outputs['Fac'], tr.inputs['Value']); k(n3.outputs['Fac'], tr2.inputs['Value']); k(tr.outputs['Result'], tm.inputs[0]); k(tr2.outputs['Result'], tm.inputs[1])
    k(n2.outputs['Fac'], h1.inputs[0]); k(n1.outputs['Fac'], h1.inputs[2]); k(n4.outputs['Fac'], h2.inputs[0]); k(h1.outputs[0], h2.inputs[2])
    k(tm.outputs[0], h3.inputs[0]); k(h2.outputs[0], h3.inputs[2]); k(h3.outputs[0], bm.inputs['Height']); k(bm.outputs[0], b.inputs['Normal'])
    mxc = nt.nodes.new('ShaderNodeMix'); mxc.data_type = 'RGBA'; mxc.blend_type = 'MULTIPLY'; mxc.inputs['Factor'].default_value = .55
    k(n1.outputs['Fac'], cr.inputs['Fac']); k(cr.outputs['Color'], mxc.inputs['A']); k(n4.outputs['Fac'], mxc.inputs['B'])
    col = mxc.outputs['Result']
    if kopot:
        geo = nt.nodes.new('ShaderNodeNewGeometry'); ds = nt.nodes.new('ShaderNodeVectorMath'); ds.operation = 'DISTANCE'; ds.inputs[1].default_value = kopot[:3]
        kr = nt.nodes.new('ShaderNodeMapRange'); kr.inputs['From Min'].default_value = kopot[3]; kr.inputs['From Max'].default_value = kopot[3] * .4
        kr.inputs['To Min'].default_value = 0; kr.inputs['To Max'].default_value = .82
        mk = nt.nodes.new('ShaderNodeMix'); mk.data_type = 'RGBA'; mk.inputs['B'].default_value = (.012, .011, .010, 1)
        k(geo.outputs['Position'], ds.inputs[0]); k(ds.outputs['Value'], kr.inputs['Value']); k(kr.outputs['Result'], mk.inputs['Factor']); k(col, mk.inputs['A']); col = mk.outputs['Result']
    k(col, b.inputs['Base Color'])
    b.inputs['Roughness'].default_value = sheroh
    return m

def _shum(me, ampl, mash, seed=0, okt=5, greben=0.0):
    off = Vector((seed * 13.7, seed * 7.1, seed * 3.3))
    for v in me.vertices:
        p = v.co * mash + off
        n = noise.fractal(p, 1.0, 2.0, okt)
        if greben: n = (1 - greben) * n + greben * (noise.ridged_multi_fractal(p * .7, 1.0, 2.0, 4, 1.0, 2.0) - 1.0)
        v.co += v.normal * n * ampl

def kamen(imya, mesto, razmer=(.3, .25, .18), seed=1, mat=None, podr=3, ploskiy=0.0, povorot=None):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=podr, radius=1, location=(0, 0, 0)); o = bpy.context.object; o.name = imya
    me = o.data
    for v in me.vertices:
        v.co = Vector((v.co.x * razmer[0], v.co.y * razmer[1], v.co.z * razmer[2]))
    me.update(); _shum(me, min(razmer) * .32, 1.6 / max(razmer), seed, okt=4, greben=.4)
    if ploskiy:
        for v in me.vertices:
            if v.co.z > razmer[2] * ploskiy: v.co.z = razmer[2] * ploskiy + (v.co.z - razmer[2] * ploskiy) * .12
    rng = np.random.default_rng(seed)
    o.location = mesto; o.rotation_euler = povorot if povorot is not None else (rng.uniform(-.25, .25), rng.uniform(-.25, .25), rng.uniform(0, 6.28))
    bpy.ops.object.shade_smooth()
    if mat: me.materials.append(mat)
    return o

def suk(imya, a, b, r=.03, seed=1, mat=None, izgib=.06, n=10, utonenie=.45):
    """A broken branch from point a to b: slightly crooked, with ragged ends."""
    rng = np.random.default_rng(seed); a, b = np.array(a, float), np.array(b, float); d = b - a; ln = np.linalg.norm(d)
    e1 = np.cross(d, [0, 0, 1.0]); e1 = e1 / (np.linalg.norm(e1) + 1e-9); e2 = np.cross(d / ln, e1)
    ph = rng.uniform(0, 6.28, 2); pts = []
    for i in range(n + 1):
        u = i / n; off = izgib * ln * (math.sin(u * math.pi + ph[0]) * .6 + math.sin(u * 2.3 * math.pi + ph[1]) * .25) * (u * (1 - u) * 4) ** .5
        pts.append(a + d * u + e1 * off + e2 * off * .5)
    cu = bpy.data.curves.new(imya, 'CURVE'); cu.dimensions = '3D'; cu.bevel_depth = 1.0; cu.bevel_resolution = 3; cu.use_fill_caps = True
    sp = cu.splines.new('POLY'); sp.points.add(n); sp.points.foreach_set('co', np.concatenate([np.array(pts), np.ones((n + 1, 1))], 1).ravel())
    sp.points.foreach_set('radius', r * (1 - utonenie * np.linspace(0, 1, n + 1)) * rng.uniform(.9, 1.1, n + 1)); sp.use_smooth = True
    o = bpy.data.objects.new(imya, cu); bpy.context.scene.collection.objects.link(o)
    if mat: cu.materials.append(mat)
    return o

def mat_dereva(imya='suk', cvet=('#1c130d', '#4b3626'), ugol=0.0, zhar=0.0):
    """Dry wood; ugol 0..1: charring; zhar > 0: smouldering cracks (patchy glow)."""
    m = bpy.data.materials.new(imya); m.use_nodes = True; nt = m.node_tree; b = nt.nodes['Principled BSDF']; k = nt.links.new
    tc = nt.nodes.new('ShaderNodeTexCoord'); mp = nt.nodes.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1, 1, .08)
    ns = nt.nodes.new('ShaderNodeTexNoise'); ns.inputs['Scale'].default_value = 28; ns.inputs['Detail'].default_value = 8
    cr = nt.nodes.new('ShaderNodeValToRGB')
    c0, c1 = L(cvet[0]), L(cvet[1]); c0 = [c * (1 - .8 * ugol) for c in c0]; c1 = [c * (1 - .85 * ugol) for c in c1]
    cr.color_ramp.elements[0].color = (*c0, 1); cr.color_ramp.elements[1].color = (*c1, 1)
    bm = nt.nodes.new('ShaderNodeBump'); bm.inputs['Strength'].default_value = .8; bm.inputs['Distance'].default_value = .01
    k(tc.outputs['Object'], mp.inputs['Vector']); k(mp.outputs[0], ns.inputs['Vector']); k(ns.outputs['Fac'], cr.inputs['Fac'])
    k(cr.outputs['Color'], b.inputs['Base Color']); k(ns.outputs['Fac'], bm.inputs['Height']); k(bm.outputs[0], b.inputs['Normal'])
    b.inputs['Roughness'].default_value = .85
    if zhar > 0:
        n2 = nt.nodes.new('ShaderNodeTexNoise'); n2.inputs['Scale'].default_value = 14; n2.inputs['Detail'].default_value = 5; n2.name = 'zhar-shum'
        k(tc.outputs['Object'], n2.inputs['Vector'])
        r2 = nt.nodes.new('ShaderNodeValToRGB'); r2.color_ramp.elements[0].position = .52; r2.color_ramp.elements[0].color = (0, 0, 0, 1)
        r2.color_ramp.elements[1].position = .7; r2.color_ramp.elements[1].color = (1.0, .28, .03, 1)
        k(n2.outputs['Fac'], r2.inputs['Fac']); k(r2.outputs['Color'], b.inputs['Emission Color']); b.inputs['Emission Strength'].default_value = zhar
    return m

def peshchera(imya='peshchera', a=4.4, b=5.2, h=3.1, vhod=(90, 36, 50), mat=None, seed=3, nt=300, nf=110, ampl=.55, tolshch=None, naruzhu=None, ampl_n=1.0, mat_vnutri=None, kolec=7):
    """Grotto: an ellipsoid dome with bumps inside (normals inwards); the opening is an arch by azimuth (centre deg, half-width deg) of height vhod[2] deg.
    The opening edge is smooth. naruzhu=(dx, dy, dz): also build the outer rock (an ellipsoid larger by these amounts, own bumps)
    and join it to the inner wall along the opening edge, giving a rocky hill with a cave. tolshch: the old way (Solidify)."""
    c0, hw, hv = math.radians(vhod[0]), math.radians(vhod[1]), math.radians(vhod[2])
    def kray(ph):
        if ph >= hv: return 0.0
        return hw * (1 - (ph / hv) ** 2.4) ** .5 * (1 + .07 * noise.noise(Vector((ph * 7, seed, 1.3))))
    TH = np.zeros((nf + 1, nt)); PH = np.zeros((nf + 1, nt)); VN = np.zeros((nf + 1, nt), bool)
    for j in range(nf + 1):
        ph = (j / nf) * (math.pi / 2); kr = kray(ph)
        for i in range(nt):
            th = i / nt * 2 * math.pi; d = (th - c0 + math.pi) % (2 * math.pi) - math.pi
            TH[j, i], PH[j, i] = th, ph
            if abs(d) < kr:
                VN[j, i] = True; TH[j, i] = c0 + math.copysign(kr, d)
    def tochki(a_, b_, h_, am, sd, grubo):
        V = []
        for j in range(nf + 1):
            for i in range(nt):
                th, ph = TH[j, i], PH[j, i]
                p = Vector((a_ * math.cos(ph) * math.cos(th), b_ * math.cos(ph) * math.sin(th), h_ * math.sin(ph)))
                nrm = Vector((p.x / a_ ** 2, p.y / b_ ** 2, p.z / h_ ** 2)).normalized()
                q = p * (.35 if not grubo else .16) + Vector((sd * 11.3, 0, 0))
                d = am * (noise.fractal(q, 1.0, 2.0, 5) * .9 + .6 * (noise.ridged_multi_fractal(q * .6, 1.0, 2.0, 4, 1.0, 2.0) - 1.0))
                d += .10 * noise.fractal(p * 2.3, 1.0, 2.0, 4) + .03 * noise.fractal(p * 7.0, 1.0, 2.0, 3)
                if grubo: d += am * .5 * noise.fractal(p * .6 + Vector((0, sd, 0)), 1.0, 2.0, 4)
                V.append(p + nrm * d)
        return V
    V = tochki(a, b, h, ampl, seed, False)
    def idx(i, j): return j * nt + (i % nt)
    F = []; kletki = []
    for j in range(nf):
        for i in range(nt):
            if VN[j, i] and VN[j, (i + 1) % nt] and VN[j + 1, i] and VN[j + 1, (i + 1) % nt]: continue
            kletki.append((i, j)); F.append((idx(i, j), idx(i, j + 1), idx(i + 1, j + 1), idx(i + 1, j)))
    n_vnutri = len(F)
    if naruzhu:
        N0 = len(V); V += tochki(a + naruzhu[0], b + naruzhu[1], h + naruzhu[2], ampl_n, seed + 5, True)
        est = set(kletki); mid = {}
        def kolco(v, k):                              # vertex on the entrance arch: between the inner (k=0) and outer (k=kolec) rim, with bumps
            if k == 0: return v
            if k == kolec: return N0 + v
            if (v, k) not in mid:
                u = k / kolec; pp = V[v] * (1 - u) + V[N0 + v] * u
                d = Vector((noise.fractal(pp * .9 + Vector((seed, 0, 0)), 1, 2, 4), noise.fractal(pp * .9 + Vector((0, seed, 7)), 1, 2, 4), noise.fractal(pp * .9 + Vector((3, 0, seed)), 1, 2, 4)))
                mid[(v, k)] = len(V); V.append(pp + d * (.32 * math.sin(u * math.pi) ** .7))
            return mid[(v, k)]
        for i, j in kletki:
            F.append((N0 + idx(i, j), N0 + idx(i + 1, j), N0 + idx(i + 1, j + 1), N0 + idx(i, j + 1)))       # outer side: normals point outwards
            for (di, dj), (e0, e1) in (((-1, 0), ((i, j + 1), (i, j))), ((1, 0), ((i + 1, j), (i + 1, j + 1))), ((0, -1), ((i, j), (i + 1, j))), ((0, 1), ((i + 1, j + 1), (i, j + 1)))):
                ni, nj = (i + di) % nt, j + dj
                if nj < 0 or nj >= nf: continue
                if (ni, nj) not in est:
                    v0, v1 = idx(*e0), idx(*e1)
                    for k in range(kolec): F.append((kolco(v0, k), kolco(v1, k), kolco(v1, k + 1), kolco(v0, k + 1)))
    me = bpy.data.meshes.new(imya); me.from_pydata([tuple(v) for v in V], [], F); me.update()
    me.polygons.foreach_set('use_smooth', np.ones(len(me.polygons), bool))
    o = bpy.data.objects.new(imya, me); bpy.context.scene.collection.objects.link(o)
    if mat: me.materials.append(mat)
    if mat_vnutri:
        me.materials.append(mat_vnutri); mi = np.zeros(len(me.polygons), np.int32); mi[:n_vnutri] = 1; me.polygons.foreach_set('material_index', mi)
    if tolshch and not naruzhu:
        sm = o.modifiers.new('tol', 'SOLIDIFY'); sm.thickness = -tolshch; sm.offset = 1
    return o

def pol(imya='pol', R=14., n=160, ampl=.12, seed=5, mat=None, yama=None):
    """Round floor with small bumps; yama=(x, y, r, depth): a shallow bowl (fire pit)."""
    xs = np.linspace(-R, R, n); V = [];
    for y in xs:
        for x in xs:
            z = ampl * noise.fractal(Vector((x * .35, y * .35, seed)), 1.0, 2.0, 5) + .02 * noise.fractal(Vector((x * 2.5, y * 2.5, seed + 3)), 1.0, 2.0, 3)
            if yama:
                d2 = ((x - yama[0]) ** 2 + (y - yama[1]) ** 2) / yama[2] ** 2
                z = z * min(1, d2 * .6) - yama[3] * math.exp(-d2)
            V.append((x, y, z))
    F = [(j * n + i, j * n + i + 1, (j + 1) * n + i + 1, (j + 1) * n + i) for j in range(n - 1) for i in range(n - 1)]
    me = bpy.data.meshes.new(imya); me.from_pydata(V, [], F); me.update()
    for p in me.polygons: p.use_smooth = True
    o = bpy.data.objects.new(imya, me); bpy.context.scene.collection.objects.link(o)
    if mat: me.materials.append(mat)
    return o

def kartochka(imya, fayl, vys, mesto, k_kamere=None, povorot_z=0.0, svet=1.0, tolko_ten=False, cvet_teni=None, diffuz=0.0):
    """A flat card with an RGBA picture. svet > 0: emits its own picture (strength node 'sila'), alpha is transparency.
    tolko_ten: invisible to the camera, only casts a shadow (people silhouettes). The bottom of the card stands at mesto."""
    img = bpy.data.images.load(fayl); w, h = img.size; shir = vys * w / h
    me = bpy.data.meshes.new(imya)
    me.from_pydata([(-shir / 2, 0, 0), (shir / 2, 0, 0), (shir / 2, 0, vys), (-shir / 2, 0, vys)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new();
    for i, c in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))): uv.data[i].uv = c
    me.update(); o = bpy.data.objects.new(imya, me); bpy.context.scene.collection.objects.link(o); o.location = mesto; o.rotation_euler = (0, 0, povorot_z)
    m = bpy.data.materials.new(imya); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; N.clear(); k = nt.links.new
    out = N.new('ShaderNodeOutputMaterial'); ti = N.new('ShaderNodeTexImage'); ti.image = img; ti.extension = 'CLIP'
    tr = N.new('ShaderNodeBsdfTransparent'); mix = N.new('ShaderNodeMixShader')
    if diffuz > 0 and not tolko_ten:      # the scene lights the picture (diffuz = paint brightness), svet = faint self-illumination
        df = N.new('ShaderNodeBsdfDiffuse'); hs = N.new('ShaderNodeHueSaturation'); hs.inputs['Value'].default_value = diffuz
        k(ti.outputs['Color'], hs.inputs['Color']); k(hs.outputs[0], df.inputs['Color'])
        em = N.new('ShaderNodeEmission'); sila = N.new('ShaderNodeValue'); sila.name = 'sila'; sila.outputs[0].default_value = max(svet, 0.)
        k(ti.outputs['Color'], em.inputs['Color']); k(sila.outputs[0], em.inputs['Strength'])
        sh = N.new('ShaderNodeAddShader'); k(df.outputs[0], sh.inputs[0]); k(em.outputs[0], sh.inputs[1])
    elif tolko_ten or svet <= 0:
        sh = N.new('ShaderNodeBsdfDiffuse'); sh.inputs['Color'].default_value = (*(cvet_teni or (0.004, 0.004, 0.004)), 1)
    else:
        sh = N.new('ShaderNodeEmission'); sila = N.new('ShaderNodeValue'); sila.name = 'sila'; sila.outputs[0].default_value = svet
        k(ti.outputs['Color'], sh.inputs['Color']); k(sila.outputs[0], sh.inputs['Strength'])
    pr = N.new('ShaderNodeValue'); pr.name = 'prozr'; pr.outputs[0].default_value = 1.0
    ml = N.new('ShaderNodeMath'); ml.operation = 'MULTIPLY'; k(ti.outputs['Alpha'], ml.inputs[0]); k(pr.outputs[0], ml.inputs[1])
    k(ml.outputs[0], mix.inputs['Fac']); k(tr.outputs[0], mix.inputs[1]); k(sh.outputs[0], mix.inputs[2]); k(mix.outputs[0], out.inputs['Surface'])
    me.materials.append(m)
    try: m.use_transparent_shadow = True; m.surface_render_method = 'DITHERED'
    except Exception: pass
    if tolko_ten: o.visible_camera = False; o.visible_glossy = False; o.visible_diffuse = False
    return o
