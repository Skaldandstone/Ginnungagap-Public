"""Inspect and render the Unreal-recovered cryo bodysuit FBX in its rest pose."""

import json
import math
import os

import bpy
from mathutils import Vector


PROJECT_DIR = r"C:\Users\James\Documents\Unreal Projects\Ginnungagap"
FBX_PATH = os.path.join(
    PROJECT_DIR,
    "Build",
    "Unreal",
    "PlayerSuits",
    "CryoBodysuitV32",
    "SK_CryoBodysuit_V32_Manny_Recovered.fbx",
)
REPORT_PATH = os.path.join(PROJECT_DIR, "Saved", "CryoBodysuitV32BlenderInspection.json")
RENDER_PATH = os.path.join(
    PROJECT_DIR, "Saved", "Renders", "CharacterCreator", "CryoBodysuitV32_Recovered_Rest.png"
)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.fbx_import(filepath=FBX_PATH, use_anim=False)

meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
armatures = [obj for obj in bpy.context.scene.objects if obj.type == "ARMATURE"]
if not meshes:
    raise RuntimeError("Recovered FBX contains no mesh")

corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
minimum = Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
maximum = Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
center = (minimum + maximum) * 0.5
extent = maximum - minimum

report = {
    "status": "pass",
    "source": FBX_PATH,
    "mesh_objects": [
        {
            "name": obj.name,
            "vertices": len(obj.data.vertices),
            "polygons": len(obj.data.polygons),
            "vertex_groups": len(obj.vertex_groups),
            "armature_modifiers": [mod.object.name if mod.object else None for mod in obj.modifiers if mod.type == "ARMATURE"],
        }
        for obj in meshes
    ],
    "armatures": [
        {"name": obj.name, "bones": len(obj.data.bones), "pose_position": obj.data.pose_position}
        for obj in armatures
    ],
    "bounds_min": list(minimum),
    "bounds_max": list(maximum),
    "extent": list(extent),
}
with open(REPORT_PATH, "w", encoding="utf-8") as report_file:
    json.dump(report, report_file, indent=2)

world = bpy.context.scene.world or bpy.data.worlds.new("InspectionWorld")
bpy.context.scene.world = world
world.color = (0.008, 0.012, 0.02)

camera_data = bpy.data.cameras.new("InspectionCamera")
camera = bpy.data.objects.new("InspectionCamera", camera_data)
bpy.context.collection.objects.link(camera)
bpy.context.scene.camera = camera
distance = max(extent.z * 1.75, extent.x * 2.5, 2.5)
camera.location = center + Vector((0.0, -distance, extent.z * 0.05))
camera.data.lens = 58
point_at(camera, center)

for name, offset, energy, color, size in (
    ("Key", Vector((-extent.x, -distance * 0.35, extent.z * 0.65)), 900.0, (0.72, 0.84, 1.0), 3.0),
    ("Fill", Vector((extent.x, -distance * 0.15, extent.z * 0.15)), 550.0, (1.0, 0.55, 0.34), 2.5),
    ("Rim", Vector((0.0, distance * 0.25, extent.z * 0.65)), 1100.0, (0.38, 0.58, 1.0), 2.0),
):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.color = color
    data.shape = "DISK"
    data.size = size
    light = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(light)
    light.location = center + offset
    point_at(light, center)

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 900
scene.render.resolution_y = 1200
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = RENDER_PATH
scene.render.film_transparent = False
scene.view_settings.look = "AgX - Medium High Contrast"
os.makedirs(os.path.dirname(RENDER_PATH), exist_ok=True)
bpy.ops.render.render(write_still=True)
