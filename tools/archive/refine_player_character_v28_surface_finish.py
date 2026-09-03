"""Apply a restrained production surface finish to the V27 cryo bodysuit."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v27.blend"
OUTPUT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v28.blend"
PREVIEWS = SUIT_DIR / "Production_v28_Previews"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v28_SurfaceFinishPass.json"


def add_surface_finish(body: bpy.types.Object) -> dict[str, float | int]:
    modifier = body.modifiers.get("V28_FabricSurfaceRelax")
    if modifier is None:
        modifier = body.modifiers.new("V28_FabricSurfaceRelax", "LAPLACIANSMOOTH")
    modifier.iterations = 2
    modifier.lambda_factor = 0.022
    modifier.lambda_border = 0.0
    modifier.use_volume_preserve = True
    modifier.use_normalized = True
    modifier.show_in_editmode = False
    body["v28_surface_finish"] = "low-amplitude volume-preserving relaxation after armature deformation"
    return {"iterations": modifier.iterations, "lambda": modifier.lambda_factor}


def refine_textile(body: bpy.types.Object) -> dict[str, float]:
    material = body.data.materials[0]
    nodes = material.node_tree.nodes
    bump = nodes.get("V18_TextileNormal")
    previous_strength = 0.0
    if bump and bump.inputs.get("Strength"):
        previous_strength = float(bump.inputs["Strength"].default_value)
        bump.inputs["Strength"].default_value = min(previous_strength, 0.008)
        if bump.inputs.get("Distance"):
            bump.inputs["Distance"].default_value = min(
                float(bump.inputs["Distance"].default_value), 0.025
            )
    material["v28_finish"] = "fine bonded compression textile; reduced macro bump"
    return {
        "previous_bump_strength": previous_strength,
        "new_bump_strength": float(bump.inputs["Strength"].default_value) if bump else 0.0,
    }


def reduce_seam_bulk(seams: list[bpy.types.Object]) -> dict[str, float | int]:
    changed = 0
    before = []
    after = []
    for seam in seams:
        if seam.type != "CURVE":
            continue
        before.append(float(seam.data.bevel_depth))
        seam.data.bevel_depth *= 0.82
        seam.data.bevel_resolution = max(2, seam.data.bevel_resolution)
        after.append(float(seam.data.bevel_depth))
        changed += 1
        seam["v28_finish"] = "reduced bonded seam profile"
    return {
        "changed_objects": changed,
        "mean_before": sum(before) / len(before) if before else 0.0,
        "mean_after": sum(after) / len(after) if after else 0.0,
    }


def pose_cryo_wake(armature: bpy.types.Object) -> None:
    rotations = {
        "spine_01": (7, 0, 0), "spine_02": (10, -2, 2),
        "neck": (9, 0, 0), "head": (18, -7, 3),
        "upperarm_l": (-7, -10, 10), "lowerarm_l": (4, -4, -15),
        "upperarm_r": (7, 10, -10), "lowerarm_r": (-4, 4, 15),
    }
    for name, degrees in rotations.items():
        bone = armature.pose.bones.get(name)
        if bone:
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = tuple(math.radians(value) for value in degrees)
    bpy.context.view_layer.update()


def clear_pose(armature: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = armature
    armature.hide_set(False)
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode="OBJECT")


def render(scene, camera, label, position, target, resolution=(1000, 1000), lens=84) -> None:
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.camera = camera
    camera.location = position
    camera.data.lens = lens
    camera.rotation_euler = (target - position).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(PREVIEWS / f"PlayerCharacter_CryoBodysuit_v28_{label}.png")
    bpy.ops.render.render(write_still=True)


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects["RIG_PlayerCharacter_CryoBodysuit_v27"]
    rig.name = "RIG_PlayerCharacter_CryoBodysuit_v28"
    body = bpy.data.objects["SK_PlayerCharacter_CryoBodysuit_v27"]
    body.name = "SK_PlayerCharacter_CryoBodysuit_v28"
    seal = bpy.data.objects["SK_PlayerCharacter_CryoNeckSeal_v27"]
    seal.name = "SK_PlayerCharacter_CryoNeckSeal_v28"
    seams = []
    for old, new in (
        ("SK_CryoSeam_CenterFront_v27", "SK_CryoSeam_CenterFront_v28"),
        ("SK_CryoSeam_LeftLeg_v27", "SK_CryoSeam_LeftLeg_v28"),
        ("SK_CryoSeam_RightLeg_v27", "SK_CryoSeam_RightLeg_v28"),
    ):
        seam = bpy.data.objects[old]
        seam.name = new
        seams.append(seam)

    smoothing = add_surface_finish(body)
    textile = refine_textile(body)
    seam_finish = reduce_seam_bulk(seams)
    body["asset_status"] = "CHARACTER_CRYO_BODYSUIT_V28_SURFACE_FINISH_REVIEW"
    body["contains_oversuit"] = False

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    render(scene, camera, "Front", Vector((0, -4.10, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 82)
    render(scene, camera, "Profile", Vector((4.10, 0, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 82)
    render(scene, camera, "SurfaceDetail", Vector((0.82, -1.90, 1.34)), Vector((0, 0, 1.30)), (1100, 1000), 102)
    pose_cryo_wake(rig)
    render(scene, camera, "CryoWakePose", Vector((2.75, -3.35, 1.16)), Vector((0, 0, 1.04)), (1100, 1000), 82)
    clear_pose(rig)
    bpy.context.window.scene = original_scene

    result = {
        "schema": 1,
        "asset": "PlayerCharacter_CryoBodysuit_Concept_v28",
        "status": "surface_finish_review",
        "contains_oversuit": False,
        "surface_smoothing": smoothing,
        "textile": textile,
        "seams": seam_finish,
        "neck_interface_source": "V27 preserved without rejected proxy or patch",
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V28_SURFACE_FINISH", json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
