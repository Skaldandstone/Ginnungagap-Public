"""Clean the V23 neck/skin boundary and subtly refine the upper silhouette."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v23.blend"
OUTPUT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v24.blend"
PREVIEWS = SUIT_DIR / "Production_v24_Previews"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v24_InterfacePass.json"


def mask_clavicle_shelf(head: bpy.types.Object) -> dict[str, int]:
    keep = head.vertex_groups.get("V24_HeadNeckKeep") or head.vertex_groups.new(name="V24_HeadNeckKeep")
    all_indices = list(range(len(head.data.vertices)))
    if all_indices:
        keep.remove(all_indices)
    kept = []
    masked = 0
    for vertex in head.data.vertices:
        world = head.matrix_world @ vertex.co
        low_neck = world.z < 1.548
        outside_neck = (world.x / 0.096) ** 2 + ((world.y - 0.006) / 0.082) ** 2 > 1.0
        if low_neck and outside_neck:
            masked += 1
        else:
            kept.append(vertex.index)
    if kept:
        keep.add(kept, 1.0, "REPLACE")
    modifier = head.modifiers.get("V24_NeckOnlyBoundary") or head.modifiers.new("V24_NeckOnlyBoundary", "MASK")
    modifier.vertex_group = keep.name
    modifier.invert_vertex_group = False
    modifier.threshold = 0.5
    head["v24_interface_cleanup"] = "inherited clavicle shelf masked; true neck boundary retained"
    return {"kept_vertices": len(kept), "masked_vertices": masked}


def nearest_on_segment(point: Vector, start: Vector, end: Vector) -> Vector:
    axis = end - start
    if axis.length_squared == 0:
        return start
    factor = max(0.0, min(1.0, (point - start).dot(axis) / axis.length_squared))
    return start + factor * axis


def refine_upper_silhouette(body: bpy.types.Object, rig: bpy.types.Object) -> dict[str, int]:
    scales = {
        "chest": 0.978,
        "clavicle_l": 0.965,
        "clavicle_r": 0.965,
        "upperarm_l": 0.962,
        "upperarm_r": 0.962,
    }
    group_names = {group.index: group.name for group in body.vertex_groups}
    bones = {}
    for name in scales:
        bone = rig.data.bones.get(name)
        if bone:
            bones[name] = (rig.matrix_world @ bone.head_local, rig.matrix_world @ bone.tail_local)
    inverse = body.matrix_world.inverted()
    counts = {name: 0 for name in scales}
    for vertex in body.data.vertices:
        world = body.matrix_world @ vertex.co
        if world.z < 1.205:
            continue
        candidates = [
            (membership.weight, group_names.get(membership.group))
            for membership in vertex.groups
            if group_names.get(membership.group) in bones
        ]
        if not candidates:
            continue
        weight, name = max(candidates)
        if weight < 0.30:
            continue
        start, end = bones[name]
        anchor = nearest_on_segment(world, start, end)
        radial = world - anchor
        scale = 1.0 - (1.0 - scales[name]) * weight
        radial *= scale
        vertex.co = inverse @ (anchor + radial)
        counts[name] += 1
    body["v24_upper_silhouette"] = "subtle bone-centered chest, clavicle, and upper-arm refinement"
    return counts


def pose_cryo_wake(armature) -> None:
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


def clear_pose(armature) -> None:
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
    scene.render.filepath = str(PREVIEWS / f"PlayerCharacter_CryoBodysuit_v24_{label}.png")
    bpy.ops.render.render(write_still=True)


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects["RIG_PlayerCharacter_CryoBodysuit_v23"]
    rig.name = "RIG_PlayerCharacter_CryoBodysuit_v24"
    body = bpy.data.objects["SK_PlayerCharacter_CryoBodysuit_v23"]
    body.name = "SK_PlayerCharacter_CryoBodysuit_v24"
    patch = bpy.data.objects["SK_PlayerCharacter_CryoNeckRetopo_v23"]
    patch.name = "SK_PlayerCharacter_CryoNeckRetopo_v24"
    gasket = bpy.data.objects["SK_PlayerCharacter_CryoGasket_v23"]
    gasket.name = "SK_PlayerCharacter_CryoGasket_v24"
    for old, new in (
        ("SK_CryoSeam_CenterFront_v23", "SK_CryoSeam_CenterFront_v24"),
        ("SK_CryoSeam_LeftLeg_v23", "SK_CryoSeam_LeftLeg_v24"),
        ("SK_CryoSeam_RightLeg_v23", "SK_CryoSeam_RightLeg_v24"),
    ):
        bpy.data.objects[old].name = new

    head = bpy.data.objects["SK_PlayerHead_Production_v6"]
    mask_stats = mask_clavicle_shelf(head)
    silhouette_stats = refine_upper_silhouette(body, rig)
    body["asset_status"] = "CHARACTER_CRYO_BODYSUIT_V24_INTERFACE_REVIEW"
    body["contains_oversuit"] = False

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    render(scene, camera, "Front", Vector((0, -4.10, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 82)
    render(scene, camera, "Profile", Vector((4.10, 0, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 82)
    render(scene, camera, "InterfaceDetail", Vector((0.82, -1.90, 1.49)), Vector((0, 0, 1.46)), (1100, 1000), 102)
    pose_cryo_wake(rig)
    render(scene, camera, "CryoWakePose", Vector((2.75, -3.35, 1.16)), Vector((0, 0, 1.04)), (1100, 1000), 82)
    clear_pose(rig)
    bpy.context.window.scene = original_scene

    REPORT.write_text(json.dumps({
        "schema": 1,
        "asset": "PlayerCharacter_CryoBodysuit_Concept_v24",
        "status": "interface_review",
        "contains_oversuit": False,
        "head_mask": mask_stats,
        "upper_silhouette": silhouette_stats,
        "preserved_neck_retopology": patch.name,
        "gasket": gasket.name,
    }, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V24_NECK_SKIN_INTERFACE", f"mask={mask_stats}", f"silhouette={silhouette_stats}", f"output={OUTPUT}")


if __name__ == "__main__":
    main()
