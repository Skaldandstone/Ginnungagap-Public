"""Build a local quad neckline transition from the V22 garment boundary."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v22.blend"
OUTPUT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v23.blend"
PREVIEWS = SUIT_DIR / "Production_v23_Previews"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v23_RetopologyPass.json"


def upper_boundary_components(body: bpy.types.Object) -> list[list[Vector]]:
    mesh = bmesh.new()
    mesh.from_mesh(body.data)
    edges = [
        edge for edge in mesh.edges
        if edge.is_boundary
        and max(vertex.co.z for vertex in edge.verts) > 1.385
        and min(abs(vertex.co.x) for vertex in edge.verts) < 0.36
    ]
    adjacency = {}
    for edge in edges:
        first, second = edge.verts
        adjacency.setdefault(first, set()).add(second)
        adjacency.setdefault(second, set()).add(first)
    unseen = set(adjacency)
    components = []
    while unseen:
        seed = unseen.pop()
        stack = [seed]
        component = {seed}
        while stack:
            vertex = stack.pop()
            for neighbor in adjacency.get(vertex, ()):
                if neighbor not in component:
                    component.add(neighbor)
                    unseen.discard(neighbor)
                    stack.append(neighbor)
        points = [vertex.co.copy() for vertex in component]
        if len(points) >= 8:
            components.append(points)
    mesh.free()
    return sorted(components, key=len, reverse=True)


def transfer_weights(obj: bpy.types.Object, source: bpy.types.Object, rig: bpy.types.Object) -> None:
    for group in source.vertex_groups:
        obj.vertex_groups.new(name=group.name)
    transfer = obj.modifiers.new("V23_TransferWeights", "DATA_TRANSFER")
    transfer.object = source
    transfer.use_vert_data = True
    transfer.data_types_verts = {"VGROUP_WEIGHTS"}
    transfer.vert_mapping = "POLYINTERP_NEAREST"
    transfer.layers_vgroup_select_src = "ALL"
    transfer.layers_vgroup_select_dst = "NAME"
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=transfer.name)
    armature = obj.modifiers.new("V23_Armature", "ARMATURE")
    armature.object = rig
    obj.parent = rig


def build_retopology_patch(
    body: bpy.types.Object,
    rig: bpy.types.Object,
    material: bpy.types.Material,
) -> tuple[bpy.types.Object, dict]:
    components = upper_boundary_components(body)
    if not components:
        raise RuntimeError("No upper garment boundary found")
    outer = components[0]
    outer.sort(key=lambda point: math.atan2(point.y - 0.004, point.x))
    count = len(outer)

    vertices = []
    rings = 4
    for ring in range(rings):
        blend = ring / (rings - 1)
        for point in outer:
            angle = math.atan2(point.y - 0.004, point.x)
            rear = max(0.0, math.sin(angle))
            inner = Vector((
                0.100 * math.cos(angle),
                0.004 + 0.082 * math.sin(angle),
                1.474 + 0.006 * rear,
            ))
            # Smoothstep keeps the outer row tangent closer to the body.
            factor = blend * blend * (3.0 - 2.0 * blend)
            vertices.append(point.lerp(inner, factor))

    faces = []
    for ring in range(rings - 1):
        for index in range(count):
            following = (index + 1) % count
            faces.append((
                ring * count + index,
                ring * count + following,
                (ring + 1) * count + following,
                (ring + 1) * count + index,
            ))
    mesh = bpy.data.meshes.new("SK_PlayerCharacter_CryoNeckRetopo_v23_Mesh")
    mesh.from_pydata(vertices, [], faces)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    patch = bpy.data.objects.new("SK_PlayerCharacter_CryoNeckRetopo_v23", mesh)
    bpy.context.collection.objects.link(patch)
    mesh.materials.append(material)
    transfer_weights(patch, body, rig)
    solidify = patch.modifiers.new("V23_FabricThickness", "SOLIDIFY")
    solidify.thickness = 0.0008
    solidify.offset = 0.0
    bevel = patch.modifiers.new("V23_SoftBoundary", "BEVEL")
    bevel.width = 0.00045
    bevel.segments = 2
    patch["semantic_layer"] = "character_cryo_bodysuit"
    patch["contains_oversuit"] = False
    patch["v23_design_role"] = "boundary-matched local quad neckline retopology"
    return patch, {
        "component_count": len(components),
        "selected_boundary_vertices": count,
        "patch_vertices": len(vertices),
        "patch_quads": len(faces),
    }


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


def render(scene, camera, label, position, target, resolution=(1000, 1000), lens=82) -> None:
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
    scene.render.filepath = str(PREVIEWS / f"PlayerCharacter_CryoBodysuit_v23_{label}.png")
    bpy.ops.render.render(write_still=True)


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects["RIG_PlayerCharacter_CryoBodysuit_v22"]
    rig.name = "RIG_PlayerCharacter_CryoBodysuit_v23"
    body = bpy.data.objects["SK_PlayerCharacter_CryoBodysuit_v22"]
    body.name = "SK_PlayerCharacter_CryoBodysuit_v23"
    bridge = bpy.data.objects["SK_PlayerCharacter_CryoNeckBridge_v22"]
    bpy.data.objects.remove(bridge, do_unlink=True)
    gasket = bpy.data.objects["SK_PlayerCharacter_CryoGasket_v22"]
    gasket.name = "SK_PlayerCharacter_CryoGasket_v23"
    for old, new in (
        ("SK_CryoSeam_CenterFront_v22", "SK_CryoSeam_CenterFront_v23"),
        ("SK_CryoSeam_LeftLeg_v22", "SK_CryoSeam_LeftLeg_v23"),
        ("SK_CryoSeam_RightLeg_v22", "SK_CryoSeam_RightLeg_v23"),
    ):
        bpy.data.objects[old].name = new

    patch, stats = build_retopology_patch(body, rig, body.data.materials[0])
    body["asset_status"] = "CHARACTER_CRYO_BODYSUIT_V23_RETOPOLOGY_REVIEW"
    body["contains_oversuit"] = False

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    render(scene, camera, "Front", Vector((0, -4.10, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 80)
    render(scene, camera, "Profile", Vector((4.10, 0, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 80)
    render(scene, camera, "NecklineDetail", Vector((0.90, -2.00, 1.49)), Vector((0, 0, 1.46)), (1100, 1000), 100)
    pose_cryo_wake(rig)
    render(scene, camera, "CryoWakePose", Vector((2.75, -3.35, 1.16)), Vector((0, 0, 1.04)), (1100, 1000), 80)
    clear_pose(rig)
    bpy.context.window.scene = original_scene

    REPORT.write_text(json.dumps({
        "schema": 1,
        "asset": "PlayerCharacter_CryoBodysuit_Concept_v23",
        "status": "retopology_review",
        "contains_oversuit": False,
        "retopology": stats,
        "patch": patch.name,
        "replaced_component": "SK_PlayerCharacter_CryoNeckBridge_v22",
        "gasket": gasket.name,
    }, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V23_NECK_RETOPOLOGY", f"stats={stats}", f"patch={patch.name}", f"output={OUTPUT}")


if __name__ == "__main__":
    main()
