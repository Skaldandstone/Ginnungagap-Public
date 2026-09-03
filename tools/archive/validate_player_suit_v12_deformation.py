"""Validate the accepted V12 panel finish in an asymmetric articulated pose."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
BLEND = SUIT_DIR / "PlayerSuit_Production_v12.blend"
LEDGER = SUIT_DIR / "PlayerSuit_Production_v12_Passes.json"
REPORT = SUIT_DIR / "PlayerSuit_Production_v12_validation.json"
RENDER = SUIT_DIR / "Production_v12_Previews" / "PlayerSuit_Production_v12_Deformation.png"


def evaluated_bounds(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    coords = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    evaluated.to_mesh_clear()
    if not coords or not all(math.isfinite(value) for co in coords for value in co):
        raise RuntimeError(f"Invalid evaluated geometry: {obj.name}")
    return ([min(co[i] for co in coords) for i in range(3)],
            [max(co[i] for co in coords) for i in range(3)])


def main():
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    if ledger.get("pass_count") != 18 or len(ledger.get("passes", [])) != 18:
        raise RuntimeError("V12 must contain exactly 18 recorded refinement passes")
    if [item["pass"] for item in ledger["passes"]] != list(range(1, 19)):
        raise RuntimeError("V12 pass ledger is not contiguous")
    rejected = set(ledger.get("rejected_after_visual_review", []))
    if len(rejected) < 10:
        raise RuntimeError("V12 visual rejection record is unexpectedly incomplete")

    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    armature = bpy.data.objects["RIG_PlayerSuit_Production_v12"]
    conformal = bpy.data.collections["SUIT_PRODUCTION_v11_CONFORMAL_ARMOR"]
    patches = [obj for obj in conformal.objects if obj.get("v11_conformal_shell")]
    if len(patches) != 14:
        raise RuntimeError(f"Expected 14 conformal armor patches, found {len(patches)}")
    for patch in patches:
        modifiers = {modifier.type for modifier in patch.modifiers}
        if not {"MASK", "SOLIDIFY", "ARMATURE"}.issubset(modifiers):
            raise RuntimeError(f"Conformal modifier stack is incomplete: {patch.name} {modifiers}")

    accepted_details = [obj for obj in bpy.data.collections["SUIT_PRODUCTION_v12_PANEL_FINISH"].objects
                        if obj.name not in rejected]
    for name in rejected:
        obj = bpy.data.objects.get(name)
        if obj is None or not obj.hide_render:
            raise RuntimeError(f"Rejected V12 attachment is not quarantined: {name}")

    pose = {
        "spine_02": (math.radians(4), math.radians(-4), math.radians(3)),
        "head": (math.radians(-5), math.radians(12), math.radians(-3)),
        "upperarm_l": (math.radians(-18), math.radians(-22), math.radians(18)),
        "lowerarm_l": (math.radians(10), math.radians(-7), math.radians(-45)),
        "upperarm_r": (math.radians(9), math.radians(16), math.radians(-12)),
        "lowerarm_r": (math.radians(-7), math.radians(5), math.radians(30)),
        "thigh_l": (math.radians(12), 0, math.radians(2)),
        "calf_l": (math.radians(-20), 0, 0),
    }
    for name, rotation in pose.items():
        bone = armature.pose.bones.get(name)
        if bone:
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = rotation
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    bounds = {}
    for patch in patches:
        minimum, maximum = evaluated_bounds(patch, depsgraph)
        if (Vector(maximum) - Vector(minimum)).length > 1.0:
            raise RuntimeError(f"V12 conformal patch exploded in pose: {patch.name}")
        bounds[patch.name] = {"min": minimum, "max": maximum}

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    bpy.context.window.scene = scene
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER)
    camera.location = Vector((3.1, -3.1, 1.06))
    camera.rotation_euler = (Vector((0, 0, .98)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.render.render(write_still=True)

    REPORT.write_text(json.dumps({
        "schema": 1, "asset": "PlayerSuit_Production_v12", "status": "passed",
        "pass_count": 18, "conformal_patch_count": len(patches),
        "accepted_detail_count": len(accepted_details), "rejected_detail_count": len(rejected),
        "pose_bones": sorted(pose), "bounds": bounds,
        "render": str(RENDER.relative_to(ROOT)).replace("\\", "/"),
    }, indent=2), encoding="utf-8")

    bpy.context.view_layer.objects.active = armature
    armature.hide_set(False); armature.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), check_existing=False)
    print("V12_DEFORMATION_VALIDATION", f"patches={len(patches)}",
          f"accepted_details={len(accepted_details)}", f"report={REPORT}")


if __name__ == "__main__":
    main()
