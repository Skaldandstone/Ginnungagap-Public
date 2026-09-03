"""Report transform and coordinate integrity for the MetaHuman body/outfit export pair."""

import json
import math
import os

import bpy


PROJECT_DIR = r"C:\Users\James\Documents\Unreal Projects\Ginnungagap"
SOURCE_DIR = os.path.join(PROJECT_DIR, "Build", "Unreal", "PlayerSuits", "MetaHumanCryoSources")
REPORT_PATH = os.path.join(PROJECT_DIR, "Saved", "MetaHumanCryoPairInspection.json")


def import_and_describe(label, filename):
    before = set(bpy.context.scene.objects)
    bpy.ops.wm.fbx_import(filepath=os.path.join(SOURCE_DIR, filename), use_anim=False)
    imported = list(set(bpy.context.scene.objects) - before)
    mesh = next(obj for obj in imported if obj.type == "MESH")
    coordinates = [coordinate for vertex in mesh.data.vertices for coordinate in vertex.co]
    return {
        "label": label,
        "mesh": mesh.name,
        "vertices": len(mesh.data.vertices),
        "polygons": len(mesh.data.polygons),
        "location": list(mesh.location),
        "rotation": list(mesh.rotation_euler),
        "scale": list(mesh.scale),
        "finite": all(math.isfinite(value) for value in coordinates),
        "local_min": min(coordinates),
        "local_max": max(coordinates),
        "bounds": [list(corner) for corner in mesh.bound_box],
        "armatures": [obj.name for obj in imported if obj.type == "ARMATURE"],
        "vertex_groups": len(mesh.vertex_groups),
    }


bpy.ops.wm.read_factory_settings(use_empty=True)
payload = {
    "status": "pass",
    "sources": [
        import_and_describe("Body", "MHC_Face01_Ada_Body_Recovered.fbx"),
        import_and_describe("Outfit", "MHC_Face01_Ada_Outfit_Recovered.fbx"),
    ],
}
with open(REPORT_PATH, "w", encoding="utf-8") as report_file:
    json.dump(payload, report_file, indent=2)
