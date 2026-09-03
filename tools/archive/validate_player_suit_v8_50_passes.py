"""Acceptance validation for the V8 fifty-pass player-suit art batch."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
BLEND = SUIT_DIR / "PlayerSuit_Production_v8.blend"
LEDGER = SUIT_DIR / "PlayerSuit_Production_v8_50Passes.json"
REPORT = SUIT_DIR / "PlayerSuit_Production_v8_validation.json"
RENDER = SUIT_DIR / "Production_v8_Previews" / "PlayerSuit_Production_v8_Deformation.png"

REQUIRED = {
    "SKV8_ClavicleBridge": "chest",
    "SKV8_ElbowGuard_L": "lowerarm_l",
    "SKV8_ElbowGuard_R": "lowerarm_r",
    "SKV8_WristSeal_L": "hand_l",
    "SKV8_WristSeal_R": "hand_r",
    "SKV8_HipBearing_L": "thigh_l",
    "SKV8_HipBearing_R": "thigh_r",
    "SKV8_KneeFrame_L": "calf_l",
    "SKV8_KneeFrame_R": "calf_r",
    "SKV8_MagneticSole_L": "foot_l",
    "SKV8_MagneticSole_R": "foot_r",
    "SKV8_VisorBrow": "head",
    "SKV8_PackRegulator": "chest",
}


def bounds(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    coordinates = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    evaluated.to_mesh_clear()
    if not coordinates or not all(math.isfinite(value) for coordinate in coordinates for value in coordinate):
        raise RuntimeError(f"Non-finite or empty evaluated V8 object: {obj.name}")
    minimum = [min(co[axis] for co in coordinates) for axis in range(3)]
    maximum = [max(co[axis] for co in coordinates) for axis in range(3)]
    return minimum, maximum


def main():
    if not BLEND.exists() or not LEDGER.exists():
        raise RuntimeError("Build the V8 fifty-pass asset before validation")
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    passes = ledger.get("passes", [])
    if ledger.get("pass_count") != 50 or len(passes) != 50:
        raise RuntimeError(f"V8 ledger must contain exactly 50 passes, found {len(passes)}")
    if [entry.get("pass") for entry in passes] != list(range(1, 51)):
        raise RuntimeError("V8 pass ledger is not contiguous from 1 through 50")
    if any(not entry.get("label") for entry in passes):
        raise RuntimeError("V8 pass ledger contains an unnamed pass")

    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    armature = bpy.data.objects["RIG_PlayerSuit_Production_v8"]
    base = bpy.data.objects["SK_PlayerSuit_Production_v8_BaseGarment"]
    collection = bpy.data.collections["SUIT_PRODUCTION_v8_50_PASSES"]
    details = [obj for obj in collection.objects if obj.type in {"MESH", "CURVE"}]
    if len(details) < 80:
        raise RuntimeError(f"Fifty-pass V8 batch is unexpectedly sparse: {len(details)} detail objects")
    if base.get("production_pass_count") != 50:
        raise RuntimeError("V8 base garment does not carry the 50-pass completion marker")
    if base.get("runtime_replacement") is not False:
        raise RuntimeError("V8 must remain review-only until promotion")

    for name, bone in REQUIRED.items():
        obj = bpy.data.objects.get(name)
        if obj is None:
            raise RuntimeError(f"Missing critical V8 production detail: {name}")
        if obj.parent != armature or obj.parent_bone != bone:
            raise RuntimeError(f"{name} is not attached to required bone {bone}")
        if not obj.data.materials:
            raise RuntimeError(f"{name} has no assigned material")

    for level in (1, 2):
        if bpy.data.collections.get(f"SUIT_PRODUCTION_v8_LOD{level}_CANDIDATES") is None:
            raise RuntimeError(f"Missing inherited V8 LOD{level} candidate collection")
    collision = bpy.data.collections.get("SUIT_PRODUCTION_v8_COLLISION_REVIEW")
    proxies = [obj for obj in collision.objects if obj.get("collision_proxy")] if collision else []
    if len(proxies) != 3:
        raise RuntimeError(f"Expected three collision review proxies, found {len(proxies)}")

    pose = {
        "spine_02": (math.radians(5), math.radians(-4), math.radians(4)),
        "head": (math.radians(-6), math.radians(14), math.radians(-5)),
        "upperarm_l": (math.radians(-20), math.radians(-28), math.radians(20)),
        "lowerarm_l": (math.radians(12), math.radians(-8), math.radians(-55)),
        "hand_l": (math.radians(8), math.radians(-5), 0),
        "upperarm_r": (math.radians(12), math.radians(20), math.radians(-16)),
        "lowerarm_r": (math.radians(-9), math.radians(7), math.radians(38)),
        "thigh_l": (math.radians(16), 0, math.radians(3)),
        "calf_l": (math.radians(-25), 0, 0),
        "foot_l": (math.radians(8), 0, 0),
    }
    for name, rotation in pose.items():
        bone = armature.pose.bones.get(name)
        if bone:
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = rotation
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    measurements = {}
    for name in REQUIRED:
        minimum, maximum = bounds(bpy.data.objects[name], depsgraph)
        diagonal = Vector(maximum) - Vector(minimum)
        if diagonal.length > .80:
            raise RuntimeError(f"V8 detail deformation exploded: {name}, diagonal={diagonal.length:.3f}")
        measurements[name] = {"min": minimum, "max": maximum}

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    bpy.context.window.scene = scene
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER)
    camera.location = Vector((3.6, -3.6, 1.10))
    camera.rotation_euler = (Vector((0, 0, .98)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.render.render(write_still=True)

    REPORT.write_text(json.dumps({
        "schema": 1, "asset": "PlayerSuit_Production_v8", "status": "passed",
        "pass_count": 50, "detail_object_count": len(details),
        "collision_proxy_count": len(proxies), "pose_bones": sorted(pose),
        "critical_bounds": measurements,
        "render": str(RENDER.relative_to(ROOT)).replace("\\", "/"),
    }, indent=2), encoding="utf-8")

    bpy.context.view_layer.objects.active = armature
    armature.hide_set(False); armature.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), check_existing=False)
    print("V8_50_PASS_VALIDATION", f"details={len(details)}", f"report={REPORT}")


if __name__ == "__main__":
    main()
