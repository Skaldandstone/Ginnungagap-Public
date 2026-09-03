"""Shorten the exposed neck read and add restrained anatomical structure."""

from __future__ import annotations

import json
import math
from collections import deque
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v30.blend"
OUTPUT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v31.blend"
PREVIEWS = SUIT_DIR / "Production_v31_Previews"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v31_NeckAnatomyPass.json"


def angle_distance(first: float, second: float) -> float:
    return abs((first - second + math.pi) % math.tau - math.pi)


def sculpt_neck_anatomy(head: bpy.types.Object) -> dict[str, float | int]:
    shape_keys = list(head.data.shape_keys.key_blocks) if head.data.shape_keys else []
    inverse = head.matrix_world.inverted()
    moved = 0
    maximum_delta = 0.0
    scm_vertices = 0
    throat_vertices = 0
    for vertex in head.data.vertices:
        world = head.matrix_world @ vertex.co
        if not (1.505 < world.z < 1.655 and abs(world.x) < 0.105 and -0.095 < world.y < 0.100):
            continue
        radial = Vector((world.x, world.y - 0.006, 0.0))
        if radial.length < 0.025:
            continue
        direction = radial.normalized()
        angle = math.atan2(radial.y, radial.x)
        t = (world.z - 1.505) / 0.150
        vertical = math.sin(math.pi * max(0.0, min(1.0, t)))

        # General mid-neck taper breaks the straight cylindrical silhouette.
        displacement = -0.0014 * vertical
        scm = max(
            math.exp(-(angle_distance(angle, math.radians(-42.0)) / 0.22) ** 2),
            math.exp(-(angle_distance(angle, math.radians(-138.0)) / 0.22) ** 2),
        )
        scm_vertical = math.sin(math.pi * max(0.0, min(1.0, (t + 0.08) / 1.08)))
        displacement += 0.0032 * scm * scm_vertical
        if scm > 0.35:
            scm_vertices += 1

        throat = math.exp(-(angle_distance(angle, math.radians(-90.0)) / 0.18) ** 2)
        throat_vertical = math.exp(-((t - 0.58) / 0.26) ** 2)
        displacement += 0.0012 * throat * throat_vertical
        if throat > 0.45:
            throat_vertices += 1

        # A small lower-front hollow suggests the suprasternal notch without a hard groove.
        notch = throat * math.exp(-((t - 0.10) / 0.12) ** 2)
        displacement -= 0.0010 * notch
        target_world = world + direction * displacement
        target_local = inverse @ target_world
        delta = target_local - vertex.co
        if shape_keys:
            for key in shape_keys:
                key.data[vertex.index].co += delta
        else:
            vertex.co = target_local
        moved += 1
        maximum_delta = max(maximum_delta, delta.length)
    head.data.update()
    head["v31_neck_anatomy"] = "mid-neck taper, bilateral SCM contours, throat plane, and sternal notch"
    return {
        "moved_vertices": moved,
        "scm_vertices": scm_vertices,
        "throat_vertices": throat_vertices,
        "shape_keys_updated": len(shape_keys),
        "maximum_delta_m": maximum_delta,
    }


def boundary_distances(body: bpy.types.Object, maximum: int = 4) -> tuple[list[int], dict[int, int]]:
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.verts.ensure_lookup_table()
    adjacency = {vertex.index: {edge.other_vert(vertex).index for edge in vertex.link_edges} for vertex in bm.verts}
    boundary = [vertex.index for vertex in bm.verts if any(edge.is_boundary for edge in vertex.link_edges)]
    distance = {index: 0 for index in boundary}
    queue = deque(boundary)
    while queue:
        current = queue.popleft()
        if distance[current] >= maximum:
            continue
        for neighbor in adjacency[current]:
            if neighbor not in distance:
                distance[neighbor] = distance[current] + 1
                queue.append(neighbor)
    bm.free()
    return boundary, distance


def raise_and_tighten_neckline(body: bpy.types.Object, seal: bpy.types.Object) -> dict[str, float | int]:
    boundary, distances = boundary_distances(body)
    if len(boundary) != 158:
        raise RuntimeError(f"Expected 158 neckline boundary vertices, found {len(boundary)}")
    influence_by_distance = (1.0, 0.72, 0.45, 0.24, 0.10)
    changed = 0
    for index, distance in distances.items():
        vertex = body.data.vertices[index]
        influence = influence_by_distance[distance]
        vertex.co.z += 0.018 * influence
        center = Vector((0.0, 0.004, vertex.co.z))
        radial = Vector((vertex.co.x, vertex.co.y - 0.004, 0.0))
        vertex.co = center + radial * (1.0 - 0.022 * influence)
        changed += 1
    for vertex in seal.data.vertices:
        vertex.co.z += 0.018
        vertex.co.x *= 0.978
        vertex.co.y = 0.004 + (vertex.co.y - 0.004) * 0.978
    body["v31_neckline_fit"] = "18 mm raised opening with 2.2 percent radial tightening"
    seal["v31_neckline_fit"] = "seal raised and tightened with garment boundary"
    return {
        "boundary_vertices": len(boundary),
        "transition_vertices": changed,
        "raise_m": 0.018,
        "radial_scale": 0.978,
        "seal_vertices": len(seal.data.vertices),
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
    scene.render.filepath = str(PREVIEWS / f"PlayerCharacter_CryoBodysuit_v31_{label}.png")
    bpy.ops.render.render(write_still=True)


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects["RIG_PlayerCharacter_CryoBodysuit_v30"]
    rig.name = "RIG_PlayerCharacter_CryoBodysuit_v31"
    body = bpy.data.objects["SK_PlayerCharacter_CryoBodysuit_v30"]
    body.name = "SK_PlayerCharacter_CryoBodysuit_v31"
    seal = bpy.data.objects["SK_PlayerCharacter_CryoNeckSeal_v30"]
    seal.name = "SK_PlayerCharacter_CryoNeckSeal_v31"
    for old, new in (
        ("SK_CryoSeam_CenterFront_v30", "SK_CryoSeam_CenterFront_v31"),
        ("SK_CryoSeam_LeftLeg_v30", "SK_CryoSeam_LeftLeg_v31"),
        ("SK_CryoSeam_RightLeg_v30", "SK_CryoSeam_RightLeg_v31"),
    ):
        bpy.data.objects[old].name = new

    head = bpy.data.objects["SK_PlayerHead_Production_v6"]
    anatomy = sculpt_neck_anatomy(head)
    neckline = raise_and_tighten_neckline(body, seal)
    body["asset_status"] = "CHARACTER_CRYO_BODYSUIT_V31_NECK_ANATOMY_REVIEW"
    body["contains_oversuit"] = False

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    render(scene, camera, "Front", Vector((0, -4.10, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 82)
    render(scene, camera, "Profile", Vector((4.10, 0, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 82)
    render(scene, camera, "NeckAnatomyDetail", Vector((0.72, -1.78, 1.57)), Vector((0, 0.005, 1.56)), (1100, 1000), 110)
    pose_cryo_wake(rig)
    render(scene, camera, "CryoWakePose", Vector((2.75, -3.35, 1.16)), Vector((0, 0, 1.04)), (1100, 1000), 82)
    clear_pose(rig)
    bpy.context.window.scene = original_scene

    result = {
        "schema": 1,
        "asset": "PlayerCharacter_CryoBodysuit_Concept_v31",
        "status": "neck_anatomy_review",
        "contains_oversuit": False,
        "anatomy": anatomy,
        "neckline": neckline,
        "production_head_vertex_count_changed": False,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V31_NECK_ANATOMY", json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
