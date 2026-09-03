"""Blend the V31 neck, soft seal, and bodysuit into one clean interface."""

from __future__ import annotations

import json
import math
import sys
from collections import deque
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from refine_player_character_v31_neck_anatomy import clear_pose, pose_cryo_wake, render


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v31.blend"
OUTPUT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v32.blend"
PREVIEWS = SUIT_DIR / "Production_v32_Previews"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v32_NeckBlendPass.json"


def smoothstep(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return value * value * (3.0 - 2.0 * value)


def boundary_graph(body: bpy.types.Object) -> tuple[list[int], dict[int, set[int]]]:
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.verts.ensure_lookup_table()
    adjacency = {
        vertex.index: {edge.other_vert(vertex).index for edge in vertex.link_edges}
        for vertex in bm.verts
    }
    boundary = [vertex.index for vertex in bm.verts if any(edge.is_boundary for edge in vertex.link_edges)]
    bm.free()
    return boundary, adjacency


def neckline_target(y: float) -> float:
    # A crew neck is lowest at the sternum and rises smoothly behind the neck.
    u = (y + 0.0625) / 0.133
    return 1.503 + 0.055 * smoothstep(u)


def blend_body_interface(body: bpy.types.Object) -> dict[str, float | int]:
    boundary, adjacency = boundary_graph(body)
    if len(boundary) != 158:
        raise RuntimeError(f"Expected 158 neckline boundary vertices, found {len(boundary)}")

    seed = {index: index for index in boundary}
    distance = {index: 0 for index in boundary}
    queue = deque(boundary)
    while queue:
        current = queue.popleft()
        if distance[current] >= 7:
            continue
        for neighbor in adjacency[current]:
            if neighbor not in distance:
                distance[neighbor] = distance[current] + 1
                seed[neighbor] = seed[current]
                queue.append(neighbor)

    original_z = [vertex.co.z for vertex in body.data.vertices]
    deltas = {
        index: neckline_target(body.data.vertices[index].co.y) - body.data.vertices[index].co.z
        for index in boundary
    }
    falloff = (1.0, 0.84, 0.66, 0.48, 0.32, 0.20, 0.11, 0.05)
    for index, rings in distance.items():
        body.data.vertices[index].co.z += deltas[seed[index]] * falloff[rings]

    # Remove the inherited high rear shelf and replace it with a trapezius-like slope.
    capped = 0
    maximum_drop = 0.0
    for vertex in body.data.vertices:
        x, y, z = vertex.co
        if y <= 0.070 or z <= 1.455 or abs(x) >= 0.30:
            continue
        target = 1.558 - 1.10 * (y - 0.070) - 0.20 * max(0.0, abs(x) - 0.075)
        if z > target:
            blend = smoothstep((y - 0.070) / 0.055)
            drop = (z - target) * (0.35 + 0.65 * blend)
            vertex.co.z -= drop
            capped += 1
            maximum_drop = max(maximum_drop, drop)

    # Relax only height, retaining the authored circumference and suit volume.
    region = {
        vertex.index for vertex in body.data.vertices
        if vertex.co.z > 1.455 and vertex.co.y > 0.045 and abs(vertex.co.x) < 0.28
    }
    for _ in range(3):
        current = [vertex.co.z for vertex in body.data.vertices]
        updates = {}
        for index in region:
            neighbors = [n for n in adjacency[index] if n in region]
            if neighbors:
                average = sum(current[n] for n in neighbors) / len(neighbors)
                updates[index] = current[index] * 0.66 + average * 0.34
        for index, value in updates.items():
            body.data.vertices[index].co.z = value

    body.data.update()
    body["v32_neck_blend"] = "front-to-back crew neckline with seven-ring falloff and rear trapezius relaxation"
    return {
        "boundary_vertices": len(boundary),
        "transition_vertices": len(distance),
        "rear_vertices_capped": capped,
        "maximum_rear_drop_m": maximum_drop,
        "front_target_z_m": neckline_target(-0.0625),
        "rear_target_z_m": neckline_target(0.0705),
        "maximum_source_z_change_m": max(
            abs(vertex.co.z - original_z[vertex.index]) for vertex in body.data.vertices
        ),
    }


def blend_seal(seal: bpy.types.Object, body: bpy.types.Object) -> dict[str, float | int]:
    moved = 0
    maximum = 0.0
    for vertex in seal.data.vertices:
        u = max(0.0, min(1.0, (vertex.co.y + 0.0625) / 0.133))
        previous_center = 1.499 + 0.024 * u
        delta = neckline_target(vertex.co.y) - previous_center
        vertex.co.z += delta
        moved += 1
        maximum = max(maximum, abs(delta))
    seal.data.update()
    if body.data.materials:
        if seal.data.materials:
            seal.data.materials[0] = body.data.materials[0]
        else:
            seal.data.materials.append(body.data.materials[0])
    seal["v32_neck_blend"] = "seal follows the front-low rear-high crew neckline"
    return {"moved_vertices": moved, "maximum_vertical_adjustment_m": maximum}


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects["RIG_PlayerCharacter_CryoBodysuit_v31"]
    body = bpy.data.objects["SK_PlayerCharacter_CryoBodysuit_v31"]
    seal = bpy.data.objects["SK_PlayerCharacter_CryoNeckSeal_v31"]
    rig.name = "RIG_PlayerCharacter_CryoBodysuit_v32"
    body.name = "SK_PlayerCharacter_CryoBodysuit_v32"
    seal.name = "SK_PlayerCharacter_CryoNeckSeal_v32"
    for old, new in (
        ("SK_CryoSeam_CenterFront_v31", "SK_CryoSeam_CenterFront_v32"),
        ("SK_CryoSeam_LeftLeg_v31", "SK_CryoSeam_LeftLeg_v32"),
        ("SK_CryoSeam_RightLeg_v31", "SK_CryoSeam_RightLeg_v32"),
    ):
        bpy.data.objects[old].name = new

    body_stats = blend_body_interface(body)
    seal_stats = blend_seal(seal, body)
    body["asset_status"] = "CHARACTER_CRYO_BODYSUIT_V32_NECK_BLEND_REVIEW"
    body["contains_oversuit"] = False

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    globals()["PREVIEWS"] = PREVIEWS
    render.__globals__["PREVIEWS"] = PREVIEWS
    def render_v32(label, position, target, resolution, lens):
        render(scene, camera, label, position, target, resolution, lens)
        old = PREVIEWS / f"PlayerCharacter_CryoBodysuit_v31_{label}.png"
        old.replace(PREVIEWS / f"PlayerCharacter_CryoBodysuit_v32_{label}.png")

    render_v32("NeckBlendDetail", Vector((0.72, -1.78, 1.57)), Vector((0, 0.005, 1.56)), (1100, 1000), 110)
    render_v32("Profile", Vector((4.10, 0, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 82)
    render_v32("RearQuarter", Vector((2.25, 2.55, 1.48)), Vector((0, 0.02, 1.40)), (1000, 1000), 92)
    pose_cryo_wake(rig)
    render_v32("CryoWakePose", Vector((2.75, -3.35, 1.16)), Vector((0, 0, 1.04)), (1100, 1000), 82)
    clear_pose(rig)
    bpy.context.window.scene = original_scene

    result = {
        "schema": 1,
        "asset": "PlayerCharacter_CryoBodysuit_Concept_v32",
        "status": "neck_blend_review",
        "contains_oversuit": False,
        "body_interface": body_stats,
        "seal_interface": seal_stats,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V32_NECK_BLEND", json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
