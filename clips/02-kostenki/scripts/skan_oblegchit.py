# Decimate the bones cut from the scan -> modeli/<name>_d.obj, plus a showcase render for checking.
#   blender -b --factory-startup --python skan_oblegchit.py -- <root> <showcase.png>
import bpy, sys, math, os
from mathutils import Vector
A = sys.argv[sys.argv.index('--') + 1:]; ROOT, OUT = A[0], A[1]
CEL = {'skan_cherep': 260000, 'skan_chelyust': 120000, 'skan_bivenR': 70000, 'skan_bivenL': 70000, 'skan_bedro': 90000,
       'skan_golen': 40000, 'skan_predpl': 40000}
sc = bpy.context.scene
for o in list(bpy.data.objects): bpy.data.objects.remove(o, do_unlink=True)
x = -4.0; obs = []
for imya, cel in CEL.items():
    src = f'{ROOT}/modeli/{imya}.obj'
    if not os.path.exists(src): continue
    bpy.ops.wm.obj_import(filepath=src, forward_axis='Y', up_axis='Z')
    o = bpy.context.selected_objects[0]; bpy.context.view_layer.objects.active = o
    n = len(o.data.polygons)
    if n > cel:
        d = o.modifiers.new('d', 'DECIMATE'); d.ratio = cel / n; bpy.ops.object.modifier_apply(modifier='d')
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.normals_make_consistent(inside=False); bpy.ops.object.mode_set(mode='OBJECT')
    for p in o.data.polygons: p.use_smooth = True
    bpy.ops.object.select_all(action='DESELECT'); o.select_set(True)
    bpy.ops.wm.obj_export(filepath=f'{ROOT}/modeli/{imya}_d.obj', export_selected_objects=True, export_materials=False, export_uv=False, forward_axis='Y', up_axis='Z')
    print(imya, n, '→', len(o.data.polygons))
    o.location = (x, 0, 0); x += max(o.dimensions.x, .5) + .35; obs.append(o)
# showcase
m = bpy.data.materials.new('kost'); m.use_nodes = True; p = m.node_tree.nodes['Principled BSDF']; p.inputs['Base Color'].default_value = (.62, .52, .38, 1); p.inputs['Roughness'].default_value = .6
for o in obs: o.data.materials.append(m)
sc.render.engine = 'BLENDER_EEVEE'; sc.render.resolution_x, sc.render.resolution_y = 1920, 820; sc.eevee.taa_render_samples = 32
sc.view_settings.view_transform = 'AgX'
w = bpy.data.worlds.new('w'); sc.world = w; w.use_nodes = True; w.node_tree.nodes['Background'].inputs[0].default_value = (.06, .065, .07, 1)
for nm, en, rot in (('key', 5, (50, 0, 30)), ('fill', 1.5, (70, 0, -110))):
    d = bpy.data.lights.new(nm, 'SUN'); d.energy = en; o = bpy.data.objects.new(nm, d); sc.collection.objects.link(o); o.rotation_euler = tuple(math.radians(a) for a in rot)
cx = (obs[0].location.x + obs[-1].location.x) / 2
cam_d = bpy.data.cameras.new('c'); cam_d.type = 'ORTHO'; cam_d.ortho_scale = (obs[-1].location.x - obs[0].location.x) + 2.2
cam = bpy.data.objects.new('c', cam_d); sc.collection.objects.link(cam); sc.camera = cam
cam.location = (cx, -8, 2.2); cam.rotation_euler = (math.radians(80), 0, 0)
sc.render.filepath = OUT; bpy.ops.render.render(write_still=True); print('ok')
