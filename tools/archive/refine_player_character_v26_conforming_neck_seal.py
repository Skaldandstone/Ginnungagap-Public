"""Refine the V25 neckline into a clean conforming cryo-bodysuit seal."""

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
SOURCE = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v25.blend"
OUTPUT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v26.blend"
PREVIEWS = SUIT_DIR / "Production_v26_Previews"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v26_NeckSealPass.json"


def reshape_head_mask(head: bpy.types.Object) -> dict[str, int]:
    group = head.vertex_groups.get("V24_HeadNeckKeep")
    if group is None:
        group = head.vertex_groups.new(name="V24_HeadNeckKeep")
    indices = list(range(len(head.data.vertices)))
    if indices:
        group.remove(indices)
    kept: list[int] = []
    masked = 0
    for vertex in head.data.vertices:
        world = head.matrix_world @ vertex.co
        ellipse = (world.x / 0.088) ** 2 + ((world.y - 0.004) / 0.068) ** 2
        inherited_shelf = world.z < 1.605 and ellipse > 1.0
        shoulder_island = world.z < 1.640 and abs(world.x) > 0.110
        rear_shelf = world.z < 1.655 and world.y > 0.060
        if inherited_shelf or shoulder_island or rear_shelf:
            masked += 1
        else:
            kept.append(vertex.index)
    group.add(kept, 1.0, "REPLACE")
    modifier = head.modifiers.get("V24_NeckOnlyBoundary")
    if modifier is None:
        modifier = head.modifiers.new("V24_NeckOnlyBoundary", "MASK")
    modifier.vertex_group = group.name
    modifier.invert_vertex_group = False
    modifier.threshold = 0.5
    head["v26_interface_cleanup"] = "shoulder skin islands removed; facial topology preserved"
    return {"kept_vertices": len(kept), "masked_vertices": masked}


def boundary_loop_and_distances(body: bpy.types.Object) -> tuple[list[int], dict[int, int]]:
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.verts.ensure_lookup_table()
    adjacency = {vertex.index: {edge.other_vert(vertex).index for edge in vertex.link_edges} for vertex in bm.verts}
    boundary = [vertex.index for vertex in bm.verts if any(edge.is_boundary for edge in vertex.link_edges)]
    if len(boundary) != 158:
        bm.free()
        raise RuntimeError(f"Expected one 158-vertex neckline boundary, found {len(boundary)} vertices")
    boundary_set = set(boundary)
    loop_adjacency = {
        index: [neighbor for neighbor in adjacency[index] if neighbor in boundary_set]
        for index in boundary
    }
    start = min(boundary, key=lambda index: (bm.verts[index].co.y, abs(bm.verts[index].co.x)))
    ordered = [start]
    previous = None
    current = start
    while True:
        neighbors = loop_adjacency[current]
        following = neighbors[0] if neighbors[0] != previous else neighbors[1]
        if following == start:
            break
        ordered.append(following)
        previous, current = current, following

    distance = {index: 0 for index in boundary}
    queue = deque(boundary)
    while queue:
        current = queue.popleft()
        if distance[current] >= 4:
            continue
        for neighbor in adjacency[current]:
            if neighbor not in distance:
                distance[neighbor] = distance[current] + 1
                queue.append(neighbor)
    bm.free()
    return ordered, distance


def neckline_height(angle: float) -> float:
    # A close crew-neck seal: shallow front dip, gently rising rear.
    return 1.493 + 0.012 * math.sin(angle)


def reshape_neckline(body: bpy.types.Object) -> dict[str, int]:
    boundary, distances = boundary_loop_and_distances(body)
    changed = 0
    for index, distance in distances.items():
        vertex = body.data.vertices[index]
        point = vertex.co.copy()
        angle = math.atan2((point.y - 0.004) / 0.081, point.x / 0.101)
        target = neckline_height(angle)
        influence = (1.0, 0.72, 0.46, 0.24, 0.10)[distance]
        point.z += (target - point.z) * influence
        if distance == 0:
            point.x = 0.088 * math.cos(angle)
            point.y = 0.004 + 0.068 * math.sin(angle)
        vertex.co = point
        changed += 1

    shoulder_changes = 0
    for vertex in body.data.vertices:
        point = vertex.co
        side = abs(point.x)
        if not (0.105 < side < 0.205 and abs(point.y - 0.004) < 0.13 and point.z > 1.495):
            continue
        side_t = (side - 0.105) / 0.100
        cap = 1.490 + 0.018 * min(1.0, side_t)
        y_fade = max(0.0, 1.0 - abs(point.y - 0.004) / 0.13)
        point.z += (cap - point.z) * y_fade * 0.78
        shoulder_changes += 1
    body["v26_neckline_shape"] = "dipped front seal with rising rear and relaxed shoulder corners"
    return {
        "boundary_vertices": len(boundary),
        "transition_vertices": changed,
        "shoulder_vertices": shoulder_changes,
    }


def transfer_weights(obj: bpy.types.Object, source: bpy.types.Object, rig: bpy.types.Object) -> None:
    for group in source.vertex_groups:
        obj.vertex_groups.new(name=group.name)
    transfer = obj.modifiers.new("V26_TransferWeights", "DATA_TRANSFER")
    transfer.object = source
    transfer.use_vert_data = True
    transfer.data_types_verts = {"VGROUP_WEIGHTS"}
    transfer.vert_mapping = "POLYINTERP_NEAREST"
    transfer.layers_vgroup_select_src = "ALL"
    transfer.layers_vgroup_select_dst = "NAME"
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=transfer.name)
    armature = obj.modifiers.new("V26_SealArmature", "ARMATURE")
    armature.object = rig
    obj.parent = rig


def build_conforming_seal(
    body: bpy.types.Object,
    rig: bpy.types.Object,
    material: bpy.types.Material,
) -> bpy.types.Object:
    major_segments = 128
    minor_segments = 10
    vertices = []
    for major in range(major_segments):
        angle = math.tau * major / major_segments
        center = Vector((
            0.0885 * math.cos(angle),
            0.004 + 0.0685 * math.sin(angle),
            neckline_height(angle) + 0.0002,
        ))
        radial = Vector((math.cos(angle), math.sin(angle), 0.0)).normalized()
        for minor in range(minor_segments):
            phase = math.tau * minor / minor_segments
            vertices.append(
                center
                + radial * (0.0030 * math.cos(phase))
                + Vector((0.0, 0.0, 0.0018 * math.sin(phase)))
            )
    faces = []
    for major in range(major_segments):
        following = (major + 1) % major_segments
        for minor in range(minor_segments):
            next_minor = (minor + 1) % minor_segments
            faces.append((
                major * minor_segments + minor,
                following * minor_segments + minor,
                following * minor_segments + next_minor,
                major * minor_segments + next_minor,
            ))
    mesh = bpy.data.meshes.new("SK_PlayerCharacter_CryoNeckSeal_v26_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(material)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    seal = bpy.data.objects.new("SK_PlayerCharacter_CryoNeckSeal_v26", mesh)
    bpy.context.collection.objects.link(seal)
    transfer_weights(seal, body, rig)
    seal["semantic_layer"] = "character_cryo_bodysuit"
    seal["contains_oversuit"] = False
    seal["v26_design_role"] = "soft bonded compression seal"
    return seal


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
    scene.render.filepath = str(PREVIEWS / f"PlayerCharacter_CryoBodysuit_v26_{label}.png")
    bpy.ops.render.render(write_still=True)


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects["RIG_PlayerCharacter_CryoBodysuit_v25"]
    rig.name = "RIG_PlayerCharacter_CryoBodysuit_v26"
    body = bpy.data.objects["SK_PlayerCharacter_CryoBodysuit_v25"]
    body.name = "SK_PlayerCharacter_CryoBodysuit_v26"
    old_gasket = bpy.data.objects["SK_PlayerCharacter_CryoGasket_v25"]
    gasket_material = old_gasket.data.materials[0]
    bpy.data.objects.remove(old_gasket, do_unlink=True)
    for old, new in (
        ("SK_CryoSeam_CenterFront_v25", "SK_CryoSeam_CenterFront_v26"),
        ("SK_CryoSeam_LeftLeg_v25", "SK_CryoSeam_LeftLeg_v26"),
        ("SK_CryoSeam_RightLeg_v25", "SK_CryoSeam_RightLeg_v26"),
    ):
        bpy.data.objects[old].name = new

    head = bpy.data.objects["SK_PlayerHead_Production_v6"]
    mask_stats = reshape_head_mask(head)
    shape_stats = reshape_neckline(body)
    seal = build_conforming_seal(body, rig, gasket_material)
    body["asset_status"] = "CHARACTER_CRYO_BODYSUIT_V26_CONFORMING_SEAL_REVIEW"
    body["contains_oversuit"] = False

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    render(scene, camera, "Front", Vector((0, -4.10, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 82)
    render(scene, camera, "Profile", Vector((4.10, 0, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 82)
    render(scene, camera, "NeckSealDetail", Vector((0.82, -1.90, 1.49)), Vector((0, 0, 1.46)), (1100, 1000), 102)
    pose_cryo_wake(rig)
    render(scene, camera, "CryoWakePose", Vector((2.75, -3.35, 1.16)), Vector((0, 0, 1.04)), (1100, 1000), 82)
    clear_pose(rig)
    bpy.context.window.scene = original_scene

    result = {
        "schema": 1,
        "asset": "PlayerCharacter_CryoBodysuit_Concept_v26",
        "status": "conforming_neck_seal_review",
        "contains_oversuit": False,
        "head_mask": mask_stats,
        "neckline_shape": shape_stats,
        "seal": {
            "object": seal.name,
            "vertices": len(seal.data.vertices),
            "quads": len(seal.data.polygons),
        },
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V26_CONFORMING_NECK_SEAL", json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
