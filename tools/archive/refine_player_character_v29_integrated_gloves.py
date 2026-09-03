"""Refine the blocky V28 hand and wrist silhouettes as integrated cryo gloves."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v28.blend"
OUTPUT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v29.blend"
PREVIEWS = SUIT_DIR / "Production_v29_Previews"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v29_GlovePass.json"


def group_weight(vertex: bpy.types.MeshVertex, group_index: int) -> float:
    membership = next((item for item in vertex.groups if item.group == group_index), None)
    return membership.weight if membership else 0.0


def nearest_on_axis(point: Vector, start: Vector, end: Vector) -> tuple[Vector, float]:
    axis = end - start
    length_squared = axis.length_squared
    if length_squared == 0.0:
        return start.copy(), 0.0
    t = max(0.0, min(1.0, (point - start).dot(axis) / length_squared))
    return start + axis * t, t


def glove_scale(t: float) -> float:
    if t < 0.20:
        return 0.965
    if t < 0.72:
        blend = (t - 0.20) / 0.52
        return 0.965 + (0.885 - 0.965) * blend
    blend = (t - 0.72) / 0.28
    smooth = blend * blend * (3.0 - 2.0 * blend)
    return 0.885 + (0.735 - 0.885) * smooth


def refine_integrated_gloves(
    body: bpy.types.Object,
    rig: bpy.types.Object,
) -> dict[str, dict[str, float | int]]:
    inverse = body.matrix_world.inverted()
    results = {}
    for side in ("l", "r"):
        hand_name = f"hand_{side}"
        lowerarm_name = f"lowerarm_{side}"
        lowerarm_group = body.vertex_groups[lowerarm_name].index
        bone = rig.data.bones[hand_name]
        start = rig.matrix_world @ bone.head_local
        end = rig.matrix_world @ bone.tail_local
        # The inherited remesh is offset from the authored hand bones.
        lateral_offset = -0.05 if side == "l" else 0.05
        start.x += lateral_offset
        end.x += lateral_offset
        start.z += 0.19
        end.z += 0.19
        axis = (end - start).normalized()
        changed = 0
        hand_vertices = 0
        wrist_vertices = 0
        for vertex in body.data.vertices:
            lowerarm_weight = group_weight(vertex, lowerarm_group)
            world = body.matrix_world @ vertex.co
            on_side = world.x > 0.220 if side == "l" else world.x < -0.220
            in_hand_volume = on_side and 0.985 < world.z < 1.115 and -0.180 < world.y < 0.150
            if not in_hand_volume or lowerarm_weight < 0.01:
                continue
            hand_weight = max(0.42, lowerarm_weight)
            anchor, t = nearest_on_axis(world, start, end)
            radial = world - anchor
            scale = 1.0 - (1.0 - glove_scale(t)) * hand_weight
            radial *= scale
            # Reduce palm depth more than width to avoid the inflated mitten read.
            radial.y *= 1.0 - 0.10 * hand_weight * (0.35 + 0.65 * t)
            extension = axis * (0.0055 * hand_weight * t * t)
            target = anchor + radial + extension
            # Preserve a soft transition where lower-arm and hand weights overlap.
            transition = max(0.28, min(1.0, hand_weight + 0.25 * (1.0 - lowerarm_weight)))
            vertex.co = inverse @ world.lerp(target, transition)
            changed += 1
            if t < 0.25:
                wrist_vertices += 1
            else:
                hand_vertices += 1
        results[side] = {
            "changed_vertices": changed,
            "hand_vertices": hand_vertices,
            "wrist_vertices": wrist_vertices,
            "distal_scale": glove_scale(1.0),
        }
    body["v29_integrated_gloves"] = "bone-axis wrist blend, palm-depth reduction, and distal taper"
    return results


def build_finger_channels(
    rig: bpy.types.Object,
    material: bpy.types.Material,
) -> dict[str, dict[str, int]]:
    results = {}
    front = Vector((0.0, -1.0, 0.0))
    for side in ("l", "r"):
        bone_name = f"hand_{side}"
        bone = rig.data.bones[bone_name]
        start = rig.matrix_world @ bone.head_local
        end = rig.matrix_world @ bone.tail_local
        axis = (end - start).normalized()
        width = axis.cross(front).normalized()
        vertices = []
        faces = []
        sides = 6
        radius = 0.00048
        for offset in (-0.015, -0.005, 0.005, 0.015):
            line_start = start.lerp(end, 0.52) + width * offset + front * 0.036
            line_end = start.lerp(end, 0.94) + width * (offset * 0.72) + front * 0.032
            line_axis = (line_end - line_start).normalized()
            normal_a = line_axis.cross(front).normalized()
            normal_b = line_axis.cross(normal_a).normalized()
            base = len(vertices)
            for point in (line_start, line_end):
                for index in range(sides):
                    angle = math.tau * index / sides
                    vertices.append(point + radius * (normal_a * math.cos(angle) + normal_b * math.sin(angle)))
            for index in range(sides):
                following = (index + 1) % sides
                faces.append((base + index, base + following, base + sides + following, base + sides + index))
        mesh = bpy.data.meshes.new(f"SK_CryoGloveFingerChannels_{side}_v29_Mesh")
        mesh.from_pydata(vertices, [], faces)
        mesh.materials.append(material)
        for polygon in mesh.polygons:
            polygon.use_smooth = True
        channels = bpy.data.objects.new(f"SK_CryoGloveFingerChannels_{side}_v29", mesh)
        bpy.context.collection.objects.link(channels)
        group = channels.vertex_groups.new(name=bone_name)
        group.add(list(range(len(vertices))), 1.0, "REPLACE")
        armature = channels.modifiers.new("V29_GloveChannelArmature", "ARMATURE")
        armature.object = rig
        channels.parent = rig
        channels["semantic_layer"] = "character_cryo_bodysuit"
        channels["contains_oversuit"] = False
        channels["v29_design_role"] = "shallow bonded finger-channel welds"
        results[side] = {"vertices": len(vertices), "quads": len(faces), "channels": 4}
    return results


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
    scene.render.filepath = str(PREVIEWS / f"PlayerCharacter_CryoBodysuit_v29_{label}.png")
    bpy.ops.render.render(write_still=True)


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects["RIG_PlayerCharacter_CryoBodysuit_v28"]
    rig.name = "RIG_PlayerCharacter_CryoBodysuit_v29"
    body = bpy.data.objects["SK_PlayerCharacter_CryoBodysuit_v28"]
    body.name = "SK_PlayerCharacter_CryoBodysuit_v29"
    seal = bpy.data.objects["SK_PlayerCharacter_CryoNeckSeal_v28"]
    seal.name = "SK_PlayerCharacter_CryoNeckSeal_v29"
    for old, new in (
        ("SK_CryoSeam_CenterFront_v28", "SK_CryoSeam_CenterFront_v29"),
        ("SK_CryoSeam_LeftLeg_v28", "SK_CryoSeam_LeftLeg_v29"),
        ("SK_CryoSeam_RightLeg_v28", "SK_CryoSeam_RightLeg_v29"),
    ):
        bpy.data.objects[old].name = new

    glove_stats = refine_integrated_gloves(body, rig)
    body["asset_status"] = "CHARACTER_CRYO_BODYSUIT_V29_INTEGRATED_GLOVE_REVIEW"
    body["contains_oversuit"] = False

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    render(scene, camera, "Front", Vector((0, -4.10, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 82)
    render(scene, camera, "Profile", Vector((4.10, 0, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 82)
    render(scene, camera, "GloveDetail", Vector((1.30, -2.05, 0.88)), Vector((0.36, -0.02, 0.89)), (1100, 1000), 108)
    pose_cryo_wake(rig)
    render(scene, camera, "CryoWakePose", Vector((2.75, -3.35, 1.16)), Vector((0, 0, 1.04)), (1100, 1000), 82)
    clear_pose(rig)
    bpy.context.window.scene = original_scene

    result = {
        "schema": 1,
        "asset": "PlayerCharacter_CryoBodysuit_Concept_v29",
        "status": "integrated_glove_review",
        "contains_oversuit": False,
        "gloves": glove_stats,
        "finger_bones_available": False,
        "rig_strategy": "empty hand groups detected; bounded glove volume preserves actual lower-arm weighting",
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V29_INTEGRATED_GLOVES", json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
