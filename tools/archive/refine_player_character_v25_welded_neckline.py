"""Rebuild and weld the cryo-bodysuit neckline using the true boundary order."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v24.blend"
OUTPUT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v25.blend"
PREVIEWS = SUIT_DIR / "Production_v25_Previews"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v25_WeldedNecklinePass.json"


def ordered_neck_boundary(body: bpy.types.Object) -> tuple[list[Vector], list[int]]:
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bm.verts.ensure_lookup_table()
    adjacency: dict[int, set[int]] = {}
    for edge in bm.edges:
        if not edge.is_boundary:
            continue
        a, b = edge.verts[0].index, edge.verts[1].index
        adjacency.setdefault(a, set()).add(b)
        adjacency.setdefault(b, set()).add(a)

    unseen = set(adjacency)
    components: list[set[int]] = []
    while unseen:
        seed = unseen.pop()
        component = {seed}
        stack = [seed]
        while stack:
            current = stack.pop()
            for neighbor in adjacency[current]:
                if neighbor not in component:
                    component.add(neighbor)
                    unseen.discard(neighbor)
                    stack.append(neighbor)
        components.append(component)

    candidates = [
        component for component in components
        if max(bm.verts[index].co.z for index in component) > 1.44
        and abs(sum(bm.verts[index].co.x for index in component) / len(component)) < 0.08
    ]
    if not candidates:
        bm.free()
        raise RuntimeError("No coherent neck boundary loop found")
    component = max(candidates, key=len)
    if any(len(adjacency[index] & component) != 2 for index in component):
        bm.free()
        raise RuntimeError("Selected neck boundary is not a simple cycle")

    start = min(component, key=lambda index: (bm.verts[index].co.y, abs(bm.verts[index].co.x)))
    ordered = [start]
    previous = None
    current = start
    while True:
        neighbors = sorted(adjacency[current] & component)
        following = neighbors[0] if neighbors[0] != previous else neighbors[1]
        if following == start:
            break
        if following in ordered:
            bm.free()
            raise RuntimeError("Boundary walk self-intersected")
        ordered.append(following)
        previous, current = current, following
    if len(ordered) != len(component):
        bm.free()
        raise RuntimeError("Boundary walk did not consume the selected loop")

    points = [bm.verts[index].co.copy() for index in ordered]
    signed_area = sum(
        points[index].x * points[(index + 1) % len(points)].y
        - points[(index + 1) % len(points)].x * points[index].y
        for index in range(len(points))
    )
    if signed_area < 0:
        points.reverse()
        ordered.reverse()
    bm.free()
    return points, ordered


def transfer_weights(obj: bpy.types.Object, source: bpy.types.Object, rig: bpy.types.Object) -> None:
    for group in source.vertex_groups:
        obj.vertex_groups.new(name=group.name)
    transfer = obj.modifiers.new("V25_TransferWeights", "DATA_TRANSFER")
    transfer.object = source
    transfer.use_vert_data = True
    transfer.data_types_verts = {"VGROUP_WEIGHTS"}
    transfer.vert_mapping = "POLYINTERP_NEAREST"
    transfer.layers_vgroup_select_src = "ALL"
    transfer.layers_vgroup_select_dst = "NAME"
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=transfer.name)
    obj.parent = rig


def build_ordered_patch(body: bpy.types.Object, rig: bpy.types.Object) -> tuple[bpy.types.Object, dict]:
    outer, boundary_indices = ordered_neck_boundary(body)
    count = len(outer)
    rings = 6
    vertices: list[Vector] = []
    for ring in range(rings):
        blend = ring / (rings - 1)
        smooth = blend * blend * (3.0 - 2.0 * blend)
        for point in outer:
            angle = math.atan2((point.y - 0.004) / 0.084, point.x / 0.102)
            rear = max(0.0, math.sin(angle))
            inner = Vector((
                0.101 * math.cos(angle),
                0.004 + 0.081 * math.sin(angle),
                1.476 + 0.007 * rear,
            ))
            vertices.append(point.lerp(inner, smooth))
    faces = [
        (
            ring * count + index,
            ring * count + (index + 1) % count,
            (ring + 1) * count + (index + 1) % count,
            (ring + 1) * count + index,
        )
        for ring in range(rings - 1)
        for index in range(count)
    ]
    mesh = bpy.data.meshes.new("SK_PlayerCharacter_CryoNeckTransition_v25_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(body.data.materials[0])
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    patch = bpy.data.objects.new("SK_PlayerCharacter_CryoNeckTransition_v25", mesh)
    bpy.context.collection.objects.link(patch)
    transfer_weights(patch, body, rig)
    patch["semantic_layer"] = "character_cryo_bodysuit"
    patch["contains_oversuit"] = False
    return patch, {
        "boundary_vertices": count,
        "rings": rings,
        "patch_vertices": len(vertices),
        "patch_quads": len(faces),
        "boundary_indices": len(boundary_indices),
    }


def weld_patch(body: bpy.types.Object, patch: bpy.types.Object) -> int:
    before = len(body.data.vertices) + len(patch.data.vertices)
    bpy.ops.object.select_all(action="DESELECT")
    body.select_set(True)
    patch.select_set(True)
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.join()
    bm = bmesh.new()
    bm.from_mesh(body.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=0.00001)
    after = len(bm.verts)
    bm.to_mesh(body.data)
    bm.free()
    body.data.update()
    return before - after


def clean_upper_back_profile(body: bpy.types.Object) -> int:
    changed = 0
    inverse = body.matrix_world.inverted()
    for vertex in body.data.vertices:
        world = body.matrix_world @ vertex.co
        if not (1.22 < world.z < 1.37 and abs(world.x) < 0.23 and world.y > 0.145):
            continue
        z_fade = math.sin(math.pi * (world.z - 1.22) / 0.15) ** 2
        x_fade = 1.0 if abs(world.x) <= 0.16 else max(0.0, (0.23 - abs(world.x)) / 0.07)
        influence = z_fade * x_fade
        world.y += (0.145 - world.y) * influence
        vertex.co = inverse @ world
        changed += 1
    body["v25_upper_back_cleanup"] = "localized posterior spike relaxed into torso profile"
    return changed


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
    scene.render.filepath = str(PREVIEWS / f"PlayerCharacter_CryoBodysuit_v25_{label}.png")
    bpy.ops.render.render(write_still=True)


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects["RIG_PlayerCharacter_CryoBodysuit_v24"]
    rig.name = "RIG_PlayerCharacter_CryoBodysuit_v25"
    body = bpy.data.objects["SK_PlayerCharacter_CryoBodysuit_v24"]
    body.name = "SK_PlayerCharacter_CryoBodysuit_v25"
    old_patch = bpy.data.objects["SK_PlayerCharacter_CryoNeckRetopo_v24"]
    bpy.data.objects.remove(old_patch, do_unlink=True)
    gasket = bpy.data.objects["SK_PlayerCharacter_CryoGasket_v24"]
    gasket.name = "SK_PlayerCharacter_CryoGasket_v25"
    for old, new in (
        ("SK_CryoSeam_CenterFront_v24", "SK_CryoSeam_CenterFront_v25"),
        ("SK_CryoSeam_LeftLeg_v24", "SK_CryoSeam_LeftLeg_v25"),
        ("SK_CryoSeam_RightLeg_v24", "SK_CryoSeam_RightLeg_v25"),
    ):
        bpy.data.objects[old].name = new

    back_vertices = clean_upper_back_profile(body)
    patch, topology = build_ordered_patch(body, rig)
    welded = weld_patch(body, patch)
    body["asset_status"] = "CHARACTER_CRYO_BODYSUIT_V25_WELDED_NECKLINE_REVIEW"
    body["contains_oversuit"] = False
    body["v25_neckline_topology"] = "true ordered boundary, six quad rings, welded garment shell"

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    render(scene, camera, "Front", Vector((0, -4.10, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 82)
    render(scene, camera, "Profile", Vector((4.10, 0, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 82)
    render(scene, camera, "NecklineDetail", Vector((0.82, -1.90, 1.49)), Vector((0, 0, 1.46)), (1100, 1000), 102)
    pose_cryo_wake(rig)
    render(scene, camera, "CryoWakePose", Vector((2.75, -3.35, 1.16)), Vector((0, 0, 1.04)), (1100, 1000), 82)
    clear_pose(rig)
    bpy.context.window.scene = original_scene

    result = {
        "schema": 1,
        "asset": "PlayerCharacter_CryoBodysuit_Concept_v25",
        "status": "welded_neckline_review",
        "contains_oversuit": False,
        "topology": topology,
        "welded_vertices": welded,
        "upper_back_vertices_refined": back_vertices,
        "integrated_patch_object_remaining": bpy.data.objects.get("SK_PlayerCharacter_CryoNeckTransition_v25") is not None,
        "gasket": gasket.name,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V25_WELDED_NECKLINE", json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
