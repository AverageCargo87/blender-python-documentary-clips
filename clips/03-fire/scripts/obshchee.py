# Clip 3 'Fire': shared helpers for the Blender 5.2 scenes (engine setup, materials, fire simulation, campfire light).
#   import sys; sys.path.insert(0, <scripts dir>); from obshchee import *
import bpy, bmesh, math, os, sys, json, time
import numpy as np
from mathutils import Vector, Matrix, Euler

FPS = 30

def L(h):
    """sRGB '#rrggbb' -> linear RGB."""
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return [((x + .055) / 1.055) ** 2.4 if x > .04045 else x / 12.92 for x in c]

def ochistit():
    for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
    for coll in (bpy.data.meshes, bpy.data.materials, bpy.data.images, bpy.data.lights, bpy.data.cameras, bpy.data.curves):
        for b in list(coll):
            if b.users == 0: coll.remove(b)

def dvizhok(engine='CYCLES', w=1920, h=1080, proc=100, samples=64, nf=1, denoise=True, vol_step=1.0, bounces=4):
    sc = bpy.context.scene
    sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = w, h, proc
    sc.render.fps = FPS; sc.frame_start, sc.frame_end = 1, nf
    sc.render.image_settings.file_format = 'PNG'; sc.render.image_settings.color_mode = 'RGB'
    sc.render.image_settings.compression = 15
    sc.view_settings.view_transform = 'AgX'
    try: sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception: pass
    if engine == 'CYCLES':
        sc.render.engine = 'CYCLES'
        pr = bpy.context.preferences.addons['cycles'].preferences
        for tip in ('OPTIX', 'CUDA'):
            try:
                pr.compute_device_type = tip; pr.get_devices()
                ok = False
                for d in pr.devices:
                    d.use = d.type == tip; ok = ok or d.use
                if ok: break
            except Exception as e: print('missing', tip, e)
        c = sc.cycles
        c.device = 'GPU'; c.samples = samples; c.use_adaptive_sampling = True; c.adaptive_threshold = .02
        c.use_denoising = denoise
        try: c.denoiser = 'OPTIX'
        except Exception: c.denoiser = 'OPENIMAGEDENOISE'
        try: c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
        except Exception: pass
        c.max_bounces = bounces; c.diffuse_bounces = min(3, bounces); c.glossy_bounces = min(3, bounces)
        c.volume_bounces = 0; c.transmission_bounces = 4; c.transparent_max_bounces = 8
        c.volume_step_rate = vol_step; c.volume_max_steps = 256
        c.caustics_reflective = False; c.caustics_refractive = False
        sc.render.use_persistent_data = True             # do not rebuild the scene every frame
        sc.render.use_motion_blur = False
    else:
        sc.render.engine = 'BLENDER_EEVEE'
        e = sc.eevee
        e.taa_render_samples = int(os.environ.get('OG_TAA', min(samples, 32)))
        for k, v in dict(use_raytracing=os.environ.get('OG_RT', '0') == '1', volumetric_tile_size=os.environ.get('OG_TILE', '4'), volumetric_samples=int(os.environ.get('OG_VSAMP', 64)), volumetric_sample_distribution=.8,
                         use_volumetric_shadows=True, volumetric_shadow_samples=16, use_shadows=True, volumetric_start=.05, volumetric_end=60.0,
                         use_bokeh_jittered=os.environ.get('OG_BOKEH', '1') == '1', bokeh_overblur=8.0, bokeh_max_size=80.0, shadow_ray_count=2, shadow_step_count=6,
                         use_fast_gi=os.environ.get('OG_GI', '0') == '1', fast_gi_method='GLOBAL_ILLUMINATION', fast_gi_ray_count=2, fast_gi_step_count=8, fast_gi_distance=6.0).items():
            try: setattr(e, k, v)
            except Exception as ex: print('eevee: missing', k, ex)
        try:
            ro = e.ray_tracing_options; ro.resolution_scale = '2'; ro.use_denoise = True; ro.screen_trace_quality = .5
            e.ray_tracing_method = 'SCREEN'
        except Exception as ex: print('eevee rt:', ex)
        sc.render.use_motion_blur = False
    return sc

def mat_prostoy(imya, col, rough=.8, metal=0., emit=None, emit_sila=0.):
    m = bpy.data.materials.new(imya); m.use_nodes = True
    b = m.node_tree.nodes['Principled BSDF']
    b.inputs['Base Color'].default_value = (*col, 1); b.inputs['Roughness'].default_value = rough; b.inputs['Metallic'].default_value = metal
    if emit is not None:
        b.inputs['Emission Color'].default_value = (*emit, 1); b.inputs['Emission Strength'].default_value = emit_sila
    return m

# --------- fire: volume material driven by the Mantaflow grids (flame, density, heat)
def mat_ognya(imya='ogon', sila=14., dym=6., cvet_dyma=(.02, .018, .016), temp=1.0, shum=False, niz=None):
    """Flame emits from the flame grid (ramp: dark red -> orange -> yellow-white), smoke follows density."""
    m = bpy.data.materials.new(imya); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; N.clear()
    out = N.new('ShaderNodeOutputMaterial')
    af = N.new('ShaderNodeAttribute'); af.attribute_name = 'flame_noise' if shum else 'flame'          # in the noise (detail) cache files the grids are called *_noise
    ad = N.new('ShaderNodeAttribute'); ad.attribute_name = 'density_noise' if shum else 'density'
    ramp = N.new('ShaderNodeValToRGB'); r = ramp.color_ramp
    r.elements[0].position = 0.0; r.elements[0].color = (0, 0, 0, 1)
    r.elements[1].position = 1.0; r.elements[1].color = (1.0, .82, .45, 1)
    for pos, col in ((.08, (.35, .02, .0)), (.28, (1.0, .16, .01)), (.55, (1.0, .42, .05)), (.8, (1.0, .66, .2))):
        e = r.elements.new(pos); e.color = (*col, 1)
    # power: flame^1.4 * sila
    pw = N.new('ShaderNodeMath'); pw.operation = 'POWER'; pw.inputs[1].default_value = 1.4
    ml = N.new('ShaderNodeMath'); ml.operation = 'MULTIPLY'; ml.inputs[1].default_value = sila; ml.name = 'sila'
    em = N.new('ShaderNodeEmission')
    md = N.new('ShaderNodeMath'); md.operation = 'MULTIPLY'; md.inputs[1].default_value = dym; md.name = 'dym'
    sca = N.new('ShaderNodeVolumeScatter'); sca.inputs['Color'].default_value = (*[min(1, c * 12) for c in cvet_dyma], 1)
    sca.inputs['Anisotropy'].default_value = .3
    ab = N.new('ShaderNodeVolumeAbsorption'); ab.inputs['Color'].default_value = (*cvet_dyma, 1)
    a1 = N.new('ShaderNodeAddShader'); a2 = N.new('ShaderNodeAddShader')
    k = nt.links.new
    k(af.outputs['Fac'], ramp.inputs['Fac']); k(ramp.outputs['Color'], em.inputs['Color'])
    k(af.outputs['Fac'], pw.inputs[0]); k(pw.outputs[0], ml.inputs[0])
    if niz:                                   # niz=(z0, z1, k0): near the base (height z0..z1 m in volume axes) emission goes from k0 to 1 so the logs read dark
        tc = N.new('ShaderNodeTexCoord'); sx = N.new('ShaderNodeSeparateXYZ'); mr = N.new('ShaderNodeMapRange'); mr.interpolation_type = 'SMOOTHSTEP'
        for i_, v_ in zip((1, 2, 3, 4), (niz[0], niz[1], niz[2], 1.0)): mr.inputs[i_].default_value = v_
        m2 = N.new('ShaderNodeMath'); m2.operation = 'MULTIPLY'
        k(tc.outputs['Object'], sx.inputs[0]); k(sx.outputs['Z'], mr.inputs[0]); k(ml.outputs[0], m2.inputs[0]); k(mr.outputs[0], m2.inputs[1])
        k(m2.outputs[0], em.inputs['Strength'])
    else: k(ml.outputs[0], em.inputs['Strength'])
    k(ad.outputs['Fac'], md.inputs[0]); k(md.outputs[0], sca.inputs['Density']); k(md.outputs[0], ab.inputs['Density'])
    k(sca.outputs[0], a1.inputs[0]); k(ab.outputs[0], a1.inputs[1]); k(a1.outputs[0], a2.inputs[0]); k(em.outputs[0], a2.inputs[1])
    k(a2.outputs[0], out.inputs['Volume'])
    return m

def aktivnyy(o):
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True); bpy.context.view_layer.objects.active = o

def domen(imya, centr, razmer, res=96, kesh=None, f0=1, f1=100, noise=2, vort=.25, burn=.75, flame_smoke=.6, flame_vort=.5,
          alpha=1.0, beta=1.5, dissolve=30, time_scale=1.0, adaptive=False, max_temp=1.75, ignition=1.25, cfl=4.0, max_shagov=4):
    """Gas simulation domain (fire + smoke). Returns the object; bake with pech()."""
    bpy.ops.mesh.primitive_cube_add(size=1, location=centr); d = bpy.context.object; d.name = imya; d.scale = razmer
    bpy.ops.object.transform_apply(scale=True)
    bpy.ops.object.modifier_add(type='FLUID'); md = d.modifiers[-1]; md.fluid_type = 'DOMAIN'; s = md.domain_settings
    s.domain_type = 'GAS'; s.resolution_max = res
    s.use_noise = noise > 0
    if noise > 0: s.noise_scale = noise; s.noise_strength = 1.0; s.noise_pos_scale = 2.0; s.noise_time_anim = .15
    s.vorticity = vort; s.alpha = alpha; s.beta = beta
    s.burning_rate = burn; s.flame_smoke = flame_smoke; s.flame_vorticity = flame_vort
    s.flame_max_temp = max_temp; s.flame_ignition = ignition
    s.use_dissolve_smoke = dissolve > 0
    if dissolve > 0: s.dissolve_speed = dissolve; s.use_dissolve_smoke_log = True
    s.time_scale = time_scale; s.cfl_condition = cfl
    s.use_adaptive_domain = adaptive
    s.cache_type = 'ALL'; s.cache_frame_start, s.cache_frame_end = f0, f1
    s.cache_data_format = 'OPENVDB'
    try: s.openvdb_cache_compress_type = 'BLOSC'
    except Exception: pass
    for k_ in ('use_collision_border_front', 'use_collision_border_back', 'use_collision_border_left', 'use_collision_border_right',
               'use_collision_border_top'):
        try: setattr(s, k_, False)
        except Exception: pass
    s.timesteps_max = max_shagov
    # IMPORTANT: set the cache directory last and do not touch the domain settings after it (Blender wipes the cache on any edit).
    # Never open a finished cache through the domain in the scenes, only as a volume: obyom_iz_kesha().
    if kesh:
        if os.path.exists(os.path.join(kesh, 'gotovo.txt')): raise RuntimeError('cache already baked: ' + kesh)
        os.makedirs(kesh, exist_ok=True); s.cache_directory = kesh
    return d

def istochnik(o, tip='FIRE', toplivo=1.0, temp=1.5, plotn=1.0, dist=.6, vol=0.0, skorost=None, tex=None):
    aktivnyy(o); bpy.ops.object.modifier_add(type='FLUID'); md = o.modifiers[-1]; md.fluid_type = 'FLOW'; f = md.flow_settings
    f.flow_type = tip; f.flow_behavior = 'INFLOW'; f.fuel_amount = toplivo; f.temperature = temp; f.density = plotn
    f.surface_distance = dist; f.volume_density = vol
    if skorost is not None:
        f.use_initial_velocity = True; f.velocity_coord = skorost
    if tex is not None:
        f.use_texture = True; f.noise_texture = tex
    return f

def pech(d):
    """Bake the simulation (runs synchronously in background mode)."""
    aktivnyy(d); t = time.time()
    r = bpy.ops.fluid.bake_all()
    print('baked', d.name, r, f'{time.time() - t:.0f} s'); sys.stdout.flush()
    kd = d.modifiers[0].domain_settings.cache_directory
    open(os.path.join(kd, 'gotovo.txt'), 'w').write(json.dumps(dict(min=[float(x) for x in (d.matrix_world @ Vector(d.bound_box[0]))],
                                                                   t=time.time() - t, kadrov=d.modifiers[0].domain_settings.cache_frame_end)))

def kesh_gotov(kesh, f1):
    p = os.path.join(kesh, 'data')
    return os.path.isdir(p) and len([x for x in os.listdir(p) if x.endswith('.vdb')]) >= f1 - 2

def svet_kostra(imya, mesto, sila=120., cvet=(1.0, .45, .12), radius=.12, seed=1, nf=300, glubina=.35, shadow=True, mnozh=None):
    """Point light with lively flicker (a sum of slow and fast oscillations), keyed on every frame.
    mnozh(n): an extra per-frame strength multiplier (fire growth, flare)."""
    ld = bpy.data.lights.new(imya, 'POINT'); ld.energy = sila; ld.color = cvet; ld.shadow_soft_size = radius
    ld.use_shadow = shadow
    o = bpy.data.objects.new(imya, ld); bpy.context.scene.collection.objects.link(o); o.location = mesto
    for k_, v_ in dict(use_shadow_jitter=os.environ.get('OG_SJ', '1') == '1', shadow_jitter_overblur=10.0, shadow_filter_radius=1.0, shadow_maximum_resolution=float(os.environ.get('OG_SRES', .005))).items():
        try: setattr(ld, k_, v_)
        except Exception: pass
    rng = np.random.default_rng(seed)
    n = nf + 2; t = np.arange(n) / FPS
    f = 1 + glubina * (.45 * np.sin(t * 9.1 + rng.uniform(0, 6)) + .3 * np.sin(t * 17.3 + rng.uniform(0, 6)) + .25 * np.sin(t * 31.7 + rng.uniform(0, 6)))
    f += glubina * .35 * np.convolve(rng.standard_normal(n), np.ones(3) / 3, 'same')
    dx = .03 * np.sin(t * 7.7 + 1.3); dz = .04 * np.sin(t * 11.1 + .4)
    for i in range(n):
        ld.energy = float(sila * max(.25, f[i]) * (mnozh(i) if mnozh else 1.0)); ld.keyframe_insert('energy', frame=i)
        o.location = (mesto[0] + float(dx[i]), mesto[1], mesto[2] + float(dz[i])); o.keyframe_insert('location', frame=i)
    return o

def kamera(imya='kam', lens=35, sensor=36, dof=None, fstop=2.0):
    cd = bpy.data.cameras.new(imya); cd.lens = lens; cd.sensor_width = sensor; cd.clip_start = .01; cd.clip_end = 5000
    o = bpy.data.objects.new(imya, cd); bpy.context.scene.collection.objects.link(o); bpy.context.scene.camera = o
    if dof is not None:
        cd.dof.use_dof = True; cd.dof.focus_distance = dof; cd.dof.aperture_fstop = fstop
    return o

def smotret(o, cel):
    d = Vector(cel) - o.location; o.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()

def render_kadry(sc, papka, kadry, log=None):
    os.makedirs(papka, exist_ok=True)
    for n in kadry:
        f = os.path.join(papka, f'{n:04d}.png')
        if os.path.exists(f) and os.path.getsize(f) > 1000: continue
        sc.frame_set(n); sc.render.filepath = f; t = time.time()
        bpy.ops.render.render(write_still=True)
        print(f'frame {n} {time.time() - t:.1f} s'); sys.stdout.flush()

def argumenty():
    a = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    return a

def spisok_kadrov(s, nf):
    if s == 'vse': return list(range(1, nf + 1))
    out = []
    for p in s.split(','):
        if '-' in p:
            a, b = p.split('-'); out += list(range(int(a), int(b) + 1))
        else: out.append(int(p))
    return [n for n in out if 1 <= n <= nf]

def mat_ognya_bb(imya='ogon-bb', temp=1700., yark=1.0, dym=2.0, cvet_dyma=(.03, .028, .026), rasseyanie=.25, attr_t='temperature'):
    """Flame as a black body (Principled Volume): colour and brightness from the simulated temperature; dark smoke with almost no scattering."""
    m = bpy.data.materials.new(imya); m.use_nodes = True
    nt = m.node_tree; N = nt.nodes; N.clear()
    out = N.new('ShaderNodeOutputMaterial'); pv = N.new('ShaderNodeVolumePrincipled')
    pv.inputs['Color'].default_value = (*cvet_dyma, 1); pv.inputs['Density'].default_value = dym
    pv.inputs['Blackbody Intensity'].default_value = yark; pv.inputs['Temperature'].default_value = temp
    pv.inputs['Temperature Attribute'].default_value = attr_t
    pv.inputs['Anisotropy'].default_value = .2
    try: pv.inputs['Absorption Color'].default_value = (0, 0, 0, 1)
    except Exception: pass
    nt.links.new(pv.outputs[0], out.inputs['Volume'])
    return m


def obyom_iz_kesha(kesh, imya='ogon', mat=None, sdvig=0, rezhim='CLIP', shum=False, mesto=None, nachalo=1):
    """A baked simulation as a volume object (VDB sequence). sdvig: frame offset (scene frame n shows cache frame n + sdvig);
    rezhim: CLIP | EXTEND | REPEAT | PING_PONG. Location comes from gotovo.txt (lower-left corner of the domain) unless given."""
    pap = os.path.join(kesh, 'noise' if shum else 'data'); files = sorted(f for f in os.listdir(pap) if f.endswith('.vdb'))
    vol = bpy.data.volumes.new(imya); vol.filepath = os.path.join(pap, files[0]); vol.is_sequence = True
    vol.frame_duration = len(files) - max(0, sdvig); vol.frame_start = nachalo; vol.frame_offset = sdvig; vol.sequence_mode = rezhim   # file frame = (scene frame - nachalo + 1, within 1..duration according to the mode) + sdvig
    o = bpy.data.objects.new(imya, vol); bpy.context.scene.collection.objects.link(o)
    if mesto is None:
        mesto = json.load(open(os.path.join(kesh, 'gotovo.txt')))['min']
    o.location = mesto
    if mat is not None: vol.materials.append(mat)
    return o

def koster_petlya(kesh, sila=26., dym=.6, nf=300, mnozh=None, mesto=(0, 0, 0), masshtab=1.0, imya='koster', nachalo_kesha=30, niz=None):
    """A campfire from a baked cache as a seamless loop: two volumes offset by half a period, emission crossfades between them,
    so the loop seam is invisible. mnozh(n): per-frame strength multiplier (flare, build-up). mesto: base of the flame.
    Returns (objects, materials)."""
    N = json.load(open(os.path.join(kesh, 'gotovo.txt')))['kadrov'] - nachalo_kesha
    obs, mats = [], []
    for k in range(2):
        m = mat_ognya(f'{imya}-m{k}', sila=sila, dym=dym, niz=niz)
        o = obyom_iz_kesha(kesh, imya=f'{imya}{k}', mat=m, rezhim='REPEAT', mesto=(0, 0, 0))
        vol = o.data; vol.frame_duration = N; vol.frame_offset = nachalo_kesha; vol.frame_start = 1 - (N // 2 if k else 0)
        o.scale = (masshtab,) * 3; o.location = (mesto[0] - .65 * masshtab, mesto[1] - .65 * masshtab, mesto[2])
        s_ = m.node_tree.nodes['sila'].inputs[1]; d_ = m.node_tree.nodes['dym'].inputs[1]
        for n in range(0, nf + 2):
            a = ((n - 1) + (N // 2 if k else 0)) % N; w = math.sin(math.pi * a / N) ** 2
            s_.default_value = sila * w * (mnozh(n) if mnozh else 1.0); s_.keyframe_insert('default_value', frame=n)
            d_.default_value = dym * w; d_.keyframe_insert('default_value', frame=n)
        obs.append(o); mats.append(m)
    return obs, mats
