"""Validate the V7 modular player suit and render an articulated QA pose."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
BLEND = ROOT / "Art" / "Characters" / "PlayerSuits" / "PlayerSuit_Production_v7.blend"
PREVIEW = ROOT / "Art" / "Characters" / "PlayerSuits" / "Production_v7_Previews" / "PlayerSuit_Production_v7_Deformation.png"
REPORT = ROOT / "Art" / "Characters" / "PlayerSuits" / "PlayerSuit_Production_v7_validation.json"

REQUIRED_PARTS = {
    "SKV7_Armor_Sternum": "chest",
    "SKV7_Armor_Shoulder_L": "upperarm_l",
    "SKV7_Armor_Shoulder_R": "upperarm_r",
    "SKV7_Armor_Forearm_L": "lowerarm_l",
    "SKV7_Armor_Forearm_R": "lowerarm_r",
    "SKV7_Armor_Knee_L": "calf_l",
    "SKV7_Armor_Knee_R": "calf_r",
    "SKV7_Armor_Boot_L": "foot_l",
    "SKV7_Armor_Boot_R": "foot_r",
    "SKV7_LifeSupport_MainPack": "chest",
}


def evaluated_bounds(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    coordinates = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    evaluated.to_mesh_clear()
    if not coordinates or not all(math.isfinite(value) for co in coordinates for value in co):
        raise RuntimeError(f"Invalid evaluated geometry: {obj.name}")
    return {
        "min": [min(co[axis] for co in coordinates) for axis in range(3)],
        "max": [max(co[axis] for co in coordinates) for axis in range(3)],
    }


def validate_material(obj):
    if not obj.data.materials or obj.data.materials[0] is None:
        raise RuntimeError(f"V7 component has no material: {obj.name}")
    material = obj.data.materials[0]
    if not material.use_nodes or material.node_tree.nodes.get("Principled BSDF") is None:
        raise RuntimeError(f"V7 component has no production shader: {obj.name}")
    return material.name


def main():
    if not BLEND.exists():
        raise RuntimeError(f"Build V7 before validation: {BLEND}")
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    armature = bpy.data.objects["RIG_PlayerSuit_Production_v7"]
    collection = bpy.data.collections["SUIT_PRODUCTION_v7_AUTHORED_SHELLS"]
    meshes = sorted((obj for obj in collection.objects if obj.type == "MESH"), key=lambda obj: obj.name)
    if len(meshes) < 25:
        raise RuntimeError(f"Expected at least 25 authored V7 mesh modules, found {len(meshes)}")
    lod_counts = {}
    for level in (1, 2):
        lod_collection = bpy.data.collections.get(f"SUIT_PRODUCTION_v7_LOD{level}_CANDIDATES")
        if lod_collection is None:
            raise RuntimeError(f"Missing V7 LOD{level} candidate collection")
        candidates = [obj for obj in lod_collection.objects if obj.type == "MESH"]
        if len(candidates) < 20:
            raise RuntimeError(f"Expected at least 20 V7 LOD{level} module candidates, found {len(candidates)}")
        if any(obj.get("lod_level") != level for obj in candidates):
            raise RuntimeError(f"V7 LOD{level} candidate metadata is incomplete")
        lod_counts[str(level)] = len(candidates)

    for name, expected_bone in REQUIRED_PARTS.items():
        obj = bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"Missing required V7 module: {name}")
        if obj.parent != armature or obj.parent_bone != expected_bone:
            raise RuntimeError(f"{name} must attach to {expected_bone}")

    pose = {
        "spine_02": (math.radians(5), math.radians(-3), math.radians(4)),
        "head": (math.radians(-5), math.radians(12), math.radians(-4)),
        "upperarm_l": (math.radians(-18), math.radians(-24), math.radians(18)),
        "lowerarm_l": (math.radians(12), math.radians(-8), math.radians(-48)),
        "upperarm_r": (math.radians(10), math.radians(18), math.radians(-14)),
        "lowerarm_r": (math.radians(-8), math.radians(6), math.radians(35)),
        "thigh_l": (math.radians(14), 0, math.radians(3)),
        "calf_l": (math.radians(-22), 0, 0),
        "thigh_r": (math.radians(-8), 0, math.radians(-3)),
    }
    for name, rotation in pose.items():
        bone = armature.pose.bones.get(name)
        if bone:
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = rotation
    bpy.context.view_layer.update()

    depsgraph = bpy.context.evaluated_depsgraph_get()
    bounds = {}
    materials = {}
    for obj in meshes:
        bounds[obj.name] = evaluated_bounds(obj, depsgraph)
        materials[obj.name] = validate_material(obj)
        height = bounds[obj.name]["max"][2] - bounds[obj.name]["min"][2]
        if height > 0.75:
            raise RuntimeError(f"Module deformation exploded: {obj.name}, height={height:.3f}")

    PREVIEW.parent.mkdir(parents=True, exist_ok=True)
    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    bpy.context.window.scene = scene
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(PREVIEW)
    target = Vector((0, 0, .98))
    camera.location = Vector((3.6, -3.6, 1.10))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.render.render(write_still=True)

    report = {
        "schema": 1,
        "asset": "PlayerSuit_Production_v7",
        "status": "passed_articulated_module_validation",
        "module_count": len(meshes),
        "lod_candidate_counts": lod_counts,
        "required_parts": sorted(REQUIRED_PARTS),
        "material_families": sorted(set(materials.values())),
        "pose_bones": sorted(pose),
        "bounds": bounds,
        "preview": str(PREVIEW.relative_to(ROOT)).replace("\\", "/"),
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")

    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), check_existing=False)
    print("V7_DEFORMATION_VALIDATION", f"modules={len(meshes)}", f"report={REPORT}")


if __name__ == "__main__":
    main()
