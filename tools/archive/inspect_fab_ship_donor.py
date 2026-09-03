"""Render and report the licensed Botanical Cruiser Fab donor asset."""
from pathlib import Path
import json
import math

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Art/Ships/Exterior/FabDonors/BotanicalCruiser/bsg_botanical_cruiser.glb"
OUTPUT = ROOT / "Art/Ships/Exterior/FabDonors/BotanicalCruiser"
REPORT = ROOT / "Saved/Reports/FabBotanicalCruiser_Inspection.json"


def look_at(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(SOURCE))
meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
if not meshes:
    raise RuntimeError(f"No meshes imported from {SOURCE}")

points = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
size = high - low
center = (low + high) * 0.5
long_axis = max(range(3), key=lambda index: size[index])
length = size[long_axis]

material = bpy.data.materials.new("M_DonorInspection_Clay")
material.use_nodes = True
bsdf = material.node_tree.nodes.get("Principled BSDF")
bsdf.inputs["Base Color"].default_value = (0.13, 0.19, 0.27, 1.0)
bsdf.inputs["Metallic"].default_value = 0.18
bsdf.inputs["Roughness"].default_value = 0.38
for obj in meshes:
    obj.data.materials.clear()
    obj.data.materials.append(material)
    obj.data.calc_loop_triangles()
    for polygon in obj.data.polygons:
        polygon.use_smooth = True

world = bpy.context.scene.world or bpy.data.worlds.new("DonorInspectionWorld")
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.0015, 0.003, 0.008, 1.0)
world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.24

camera_data = bpy.data.cameras.new("CAM_DonorInspection")
camera = bpy.data.objects.new("CAM_DonorInspection", camera_data)
bpy.context.collection.objects.link(camera)
if long_axis == 0:
    offset = Vector((length * 0.35, -length * 2.15, length * 0.45))
elif long_axis == 1:
    offset = Vector((length * 2.15, length * 0.35, length * 0.45))
else:
    offset = Vector((length * 2.15, -length * 0.35, length * 0.45))
camera.location = center + offset
camera.data.lens = 58
camera.data.clip_start = max(0.01, length * 0.0001)
camera.data.clip_end = length * 6.0
look_at(camera, center)
bpy.context.scene.camera = camera

for name, energy, color, direction, angle in (
    ("Key", 4.2, (0.78, 0.88, 1.0), Vector((0.2, -0.4, 0.8)), 8.0),
    ("Rim", 2.1, (1.0, 0.34, 0.11), Vector((-0.5, 0.3, 0.25)), 12.0),
):
    data = bpy.data.lights.new(name, "SUN")
    light = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(light)
    light.location = center + direction * length
    data.energy = energy
    data.color = color
    data.angle = math.radians(angle)
    look_at(light, center)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGBA"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.render.filepath = str(OUTPUT / "BotanicalCruiser_Donor_ThreeQuarter.png")
bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / "BotanicalCruiser_Donor_Inspection.blend"))
bpy.ops.render.render(write_still=True)

REPORT.parent.mkdir(parents=True, exist_ok=True)
payload = {
    "source": str(SOURCE),
    "objects": len(meshes),
    "vertices": sum(len(obj.data.vertices) for obj in meshes),
    "triangles": sum(len(obj.data.loop_triangles) for obj in meshes),
    "materials_before_clay_override": len(bpy.data.materials) - 1,
    "bounds": {"min": list(low), "max": list(high), "size": list(size)},
    "long_axis": "XYZ"[long_axis],
    "render": scene.render.filepath,
}
REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
