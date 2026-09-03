"""Reduce the V18 undersuit envelope while preserving rig alignment."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerCharacter_Undersuit_Concept_v18.blend"
OUTPUT = SUIT_DIR / "PlayerCharacter_Undersuit_Concept_v19.blend"
PREVIEWS = SUIT_DIR / "Production_v19_Previews"
REPORT = SUIT_DIR / "PlayerCharacter_Undersuit_v19_SilhouettePass.json"

RADIAL_SCALE = {
    "root": 0.95,
    "pelvis": 0.92,
    "spine_01": 0.91,
    "spine_02": 0.90,
    "chest": 0.91,
    "neck": 0.94,
    "clavicle_l": 0.92,
    "clavicle_r": 0.92,
    "upperarm_l": 0.90,
    "upperarm_r": 0.90,
    "lowerarm_l": 0.91,
    "lowerarm_r": 0.91,
    "hand_l": 0.95,
    "hand_r": 0.95,
    "thigh_l": 0.92,
    "thigh_r": 0.92,
    "calf_l": 0.93,
    "calf_r": 0.93,
    "foot_l": 0.96,
    "foot_r": 0.96,
}


def nearest_on_segment(point: Vector, start: Vector, end: Vector) -> Vector:
    axis = end - start
    length_squared = axis.length_squared
    if length_squared == 0:
        return start
    factor = max(0.0, min(1.0, (point - start).dot(axis) / length_squared))
    return start + axis * factor


def slim_around_rig(suit: bpy.types.Object, rig: bpy.types.Object) -> dict[str, int]:
    group_names = {group.index: group.name for group in suit.vertex_groups}
    bones = {}
    for name in RADIAL_SCALE:
        bone = rig.data.bones.get(name)
        if bone:
            bones[name] = (
                rig.matrix_world @ bone.head_local,
                rig.matrix_world @ bone.tail_local,
            )

    inverse = suit.matrix_world.inverted()
    counts = {name: 0 for name in RADIAL_SCALE}
    unchanged = 0
    for vertex in suit.data.vertices:
        candidates = [
            (membership.weight, group_names.get(membership.group))
            for membership in vertex.groups
            if group_names.get(membership.group) in bones
        ]
        if not candidates:
            unchanged += 1
            continue
        _, bone_name = max(candidates)
        world = suit.matrix_world @ vertex.co
        start, end = bones[bone_name]
        anchor = nearest_on_segment(world, start, end)
        radial = world - anchor
        # Preserve a little more depth at the chest than width; this avoids a
        # paper-flat profile while removing the padded silhouette.
        scale = RADIAL_SCALE[bone_name]
        if bone_name in {"spine_01", "spine_02", "chest", "pelvis"}:
            radial.x *= scale
            radial.y *= min(0.96, scale + 0.025)
        else:
            radial *= scale
        vertex.co = inverse @ (anchor + radial)
        counts[bone_name] += 1

    suit["v19_silhouette_pass"] = "bone-centered radial reduction; skeleton placement preserved"
    counts["unchanged"] = unchanged
    return counts


def slim_yoke(yoke: bpy.types.Object) -> dict[str, float]:
    for vertex in yoke.data.vertices:
        vertex.co.x *= 0.84
        vertex.co.y *= 0.86
        vertex.co.z = 1.510 + (vertex.co.z - 1.510) * 0.72
    solidify = next((modifier for modifier in yoke.modifiers if modifier.type == "SOLIDIFY"), None)
    bevel = next((modifier for modifier in yoke.modifiers if modifier.type == "BEVEL"), None)
    shrinkwrap = next((modifier for modifier in yoke.modifiers if modifier.type == "SHRINKWRAP"), None)
    if solidify:
        solidify.thickness = 0.0018
    if bevel:
        bevel.width = 0.0012
    if shrinkwrap:
        shrinkwrap.offset = 0.0012
    yoke["v19_silhouette_pass"] = "narrower, lower-profile bonded undersuit neckline"
    return {
        "width_scale": 0.84,
        "depth_scale": 0.86,
        "height_scale": 0.72,
        "solidify_m": solidify.thickness if solidify else 0.0,
    }


def pose_suiting_up(armature) -> None:
    rotations = {
        "spine_01": (5, 0, 0), "spine_02": (8, -2, 2),
        "neck": (8, 0, 0), "head": (15, -6, 3),
        "upperarm_l": (-4, -8, 8), "lowerarm_l": (2, -3, -12),
        "upperarm_r": (4, 8, -8), "lowerarm_r": (-2, 3, 12),
    }
    for name, degrees in rotations.items():
        bone = armature.pose.bones.get(name)
        if bone:
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = tuple(math.radians(value) for value in degrees)
    bpy.context.view_layer.update()


def clear_pose(armature) -> None:
    bpy.context.view_layer.objects.active = armature
    armature.hide_set(False)
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode="OBJECT")


def render(scene, camera, label, position, target, resolution=(1000, 1000), lens=78) -> None:
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
    scene.render.filepath = str(PREVIEWS / f"PlayerCharacter_Undersuit_v19_{label}.png")
    bpy.ops.render.render(write_still=True)


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects["RIG_PlayerCharacter_Undersuit_v18"]
    rig.name = "RIG_PlayerCharacter_Undersuit_v19"
    suit = bpy.data.objects["SK_PlayerCharacter_Undersuit_v18"]
    suit.name = "SK_PlayerCharacter_Undersuit_v19"
    yoke = bpy.data.objects["SK_PlayerUndersuit_NeckYoke_v18"]
    yoke.name = "SK_PlayerUndersuit_NeckYoke_v19"

    reduction_counts = slim_around_rig(suit, rig)
    yoke_settings = slim_yoke(yoke)
    suit["asset_status"] = "CHARACTER_UNDERSUIT_V19_SILHOUETTE_REVIEW"
    suit["contains_oversuit"] = False
    yoke["contains_oversuit"] = False

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    render(scene, camera, "Front", Vector((0, -4.15, 1.13)), Vector((0, 0, 1.10)), (900, 1100), 74)
    render(scene, camera, "Profile", Vector((4.15, 0, 1.13)), Vector((0, 0, 1.10)), (900, 1100), 74)
    render(scene, camera, "UpperBody", Vector((1.10, -2.45, 1.28)), Vector((0, 0, 1.24)), (1100, 1000), 92)
    pose_suiting_up(rig)
    render(scene, camera, "SuitingUpPose", Vector((2.7, -3.3, 1.18)), Vector((0, 0, 1.05)), (1100, 1000), 74)
    clear_pose(rig)
    bpy.context.window.scene = original_scene

    REPORT.write_text(json.dumps({
        "schema": 1,
        "asset": "PlayerCharacter_Undersuit_Concept_v19",
        "status": "silhouette_review",
        "contains_oversuit": False,
        "radial_scales": RADIAL_SCALE,
        "vertex_counts": reduction_counts,
        "yoke_settings": yoke_settings,
        "materials_preserved_from": "V18",
    }, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V19_SLIM_UNDERSUIT", f"counts={reduction_counts}", f"output={OUTPUT}")


if __name__ == "__main__":
    main()
