# Bone showcase render (shape check): blender -b --factory-startup --python pokaz_kostey.py -- <root> <out.png>
import bpy, sys, math, os
from mathutils import Vector
A = sys.argv[sys.argv.index('--') + 1:]; ROOT, OUT = A[0], A[1]
sc = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x, sc.render.resolution_y = 1920, 1080
sc.eevee.taa_render_samples = 32
try: sc.eevee.use_raytracing = True
except Exception: pass
sc.view_settings.view_transform = 'AgX'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (.05, .055, .06, 1); w.node_tree.nodes['Background'].inputs[1].default_value = 1
def mat_kost():
    m = bpy.data.materials.new('kost'); m.use_nodes = True; N = m.node_tree.nodes; L = m.node_tree.links.new; p = N['Principled BSDF']
    tc = N.new('ShaderNodeTexCoord'); nz = N.new('ShaderNodeTexNoise'); nz.inputs['Scale'].default_value = 9; nz.inputs['Detail'].default_value = 6
    L(tc.outputs['Object'], nz.inputs['Vector'])
    cr = N.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].color = (.42, .33, .22, 1); cr.color_ramp.elements[1].color = (.80, .72, .58, 1)
    cr.color_ramp.elements[0].position = .35; cr.color_ramp.elements[1].position = .7; L(nz.outputs['Fac'], cr.inputs[0])
    ao = N.new('ShaderNodeAmbientOcclusion'); ao.inputs['Distance'].default_value = .08
    mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = 'MULTIPLY'; L(ao.outputs['AO'], mx.inputs['Factor'])
    mx.inputs['Factor'].default_value = 1
    L(cr.outputs[0], mx.inputs['A']); mx.inputs['B'].default_value = (.45, .38, .3, 1)
    inv = N.new('ShaderNodeMath'); inv.operation = 'SUBTRACT'; inv.inputs[0].default_value = 1; L(ao.outputs['AO'], inv.inputs[1]); L(inv.outputs[0], mx.inputs['Factor'])
    L(mx.outputs['Result'], p.inputs['Base Color'])
    p.inputs['Roughness'].default_value = .62
    try: p.inputs['Subsurface Weight'].default_value = .08; p.inputs['Subsurface Radius'].default_value = (.01, .007, .004)
    except Exception: pass
    bu = N.new('ShaderNodeBump'); nb = N.new('ShaderNodeTexNoise'); nb.inputs['Scale'].default_value = 140; nb.inputs['Detail'].default_value = 4
    L(tc.outputs['Object'], nb.inputs['Vector']); L(nb.outputs['Fac'], bu.inputs['Height']); bu.inputs['Strength'].default_value = .25; bu.inputs['Distance'].default_value = .002
    L(bu.outputs[0], p.inputs['Normal']); return m
MK = mat_kost()
def zagruzit(imya):
    bpy.ops.wm.obj_import(filepath=f'{ROOT}/modeli/{imya}.obj', forward_axis='Y', up_axis='Z')
    o = bpy.context.selected_objects[0]; o.name = imya
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.shade_smooth()
    o.data.materials.clear(); o.data.materials.append(MK); return o
import os as _os
if _os.environ.get('VIDY'):   # skull and mandible from three sides: front, side, three-quarter
    ryad = [('cherep0', (-2.6, 0, 0), 180), ('cherep0', (-1.3, 0, 0), 90), ('cherep1', (0, 0, 0), 145),
            ('chelyust0', (1.2, 0, 0), 180), ('chelyust0', (2.1, 0, 0), 90), ('chelyust1', (3.0, 0, 0), 145)]
else: ryad = [('cherep0', (-2.2, 0, 0), 25), ('cherep1', (-1.1, 0, 0), -20), ('cherep2', (0, 0, 0), 160),
        ('chelyust0', (1.1, .1, 0), 30), ('chelyust1', (1.9, -.2, 0), -35), ('bedro0', (2.7, 0, 0), 0), ('lopatka0', (3.3, .1, 0), 15)]
for imya, pos, rz in ryad:
    if not os.path.exists(f'{ROOT}/modeli/{imya}.obj'): continue
    o = zagruzit(imya); o.location = pos; o.rotation_euler = (0, 0, math.radians(rz))
    if imya.startswith('bedro'): o.rotation_euler = (math.radians(70), 0, math.radians(20)); o.location = (2.7, 0, .15)
bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, -.3)); pl = bpy.context.object
mp = bpy.data.materials.new('pol'); mp.use_nodes = True; mp.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.12, .11, .1, 1); pl.data.materials.append(mp)
for nm, en, rot, sz in (('key', 600, (55, 0, 35), 4), ('fill', 200, (70, 0, -120), 6), ('rim', 400, (60, 0, 170), 3)):
    d = bpy.data.lights.new(nm, 'AREA'); d.energy = en; d.size = sz; o = bpy.data.objects.new(nm, d); sc.collection.objects.link(o)
    o.rotation_euler = tuple(math.radians(a) for a in rot); o.location = Vector((0, 0, 0)) + o.rotation_euler.to_matrix() @ Vector((0, 0, 7))
cam_d = bpy.data.cameras.new('c'); cam_d.lens = 40; cam = bpy.data.objects.new('c', cam_d); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (.6, -6.2, 2.4); cam.rotation_euler = (math.radians(72), 0, math.radians(4))
sc.render.filepath = OUT; bpy.ops.render.render(write_still=True)
print('ok')
