"""Add a clean deforming neck surface and seat the V26 seal into the bodysuit."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v26.blend"
OUTPUT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v27.blend"
PREVIEWS = SUIT_DIR / "Production_v27_Previews"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v27_CleanNeckPass.json"


def transfer_weights(obj: bpy.types.Object, source: bpy.types.Object, rig: bpy.types.Object) -> None:
    for group in source.vertex_groups:
        obj.vertex_groups.new(name=group.name)
    transfer = obj.modifiers.new("V27_TransferWeights", "DATA_TRANSFER")
    transfer.object = source
    transfer.use_vert_data = True
    transfer.data_types_verts = {"VGROUP_WEIGHTS"}
    transfer.vert_mapping = "POLYINTERP_NEAREST"
    transfer.layers_vgroup_select_src = "ALL"
    transfer.layers_vgroup_select_dst = "NAME"
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=transfer.name)
    armature = obj.modifiers.new("V27_CollarArmature", "ARMATURE")
    armature.object = rig
    obj.parent = rig


def collar_top(angle: float) -> float:
    return 1.517 + 0.004 * math.sin(angle)


def build_compression_collar(
    body: bpy.types.Object,
    rig: bpy.types.Object,
) -> tuple[bpy.types.Object, dict[str, int]]:
    radial_segments = 128
    height_segments = 4
    vertices = []
    for row in range(height_segments + 1):
        t = row / height_segments
        for column in range(radial_segments):
            angle = math.tau * column / radial_segments
            smooth = t * t * (3.0 - 2.0 * t)
            bottom_z = 1.493 + 0.012 * math.sin(angle)
            top_z = collar_top(angle)
            rx = 0.0875 + (0.0820 - 0.0875) * smooth
            ry = 0.0675 + (0.0640 - 0.0675) * smooth
            center_y = 0.004 + 0.002 * smooth
            vertices.append((
                rx * math.cos(angle),
                center_y + ry * math.sin(angle),
                bottom_z + (top_z - bottom_z) * smooth,
            ))
    faces = []
    for row in range(height_segments):
        for column in range(radial_segments):
            following = (column + 1) % radial_segments
            faces.append((
                row * radial_segments + column,
                row * radial_segments + following,
                (row + 1) * radial_segments + following,
                (row + 1) * radial_segments + column,
            ))
    mesh = bpy.data.meshes.new("SK_PlayerCharacter_CryoCompressionCollar_v27_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.materials.append(body.data.materials[0])
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    collar = bpy.data.objects.new("SK_PlayerCharacter_CryoCompressionCollar_v27", mesh)
    bpy.context.collection.objects.link(collar)
    transfer_weights(collar, body, rig)
    collar["semantic_layer"] = "character_cryo_bodysuit"
    collar["v27_design_role"] = "thin flexible compression collar covering inherited skin boundary"
    collar["contains_oversuit"] = False
    return collar, {
        "vertices": len(vertices),
        "quads": len(faces),
        "radial_segments": radial_segments,
        "height_segments": height_segments,
    }


def restore_natural_upper_neck(head: bpy.types.Object) -> dict[str, int]:
    group = head.vertex_groups["V24_HeadNeckKeep"]
    indices = list(range(len(head.data.vertices)))
    group.remove(indices)
    kept = []
    masked = 0
    for vertex in head.data.vertices:
        world = head.matrix_world @ vertex.co
        ellipse = (world.x / 0.088) ** 2 + ((world.y - 0.004) / 0.068) ** 2
        inherited_shelf = world.z < 1.565 and ellipse > 1.0
        shoulder_island = world.z < 1.605 and abs(world.x) > 0.075
        if inherited_shelf or shoulder_island:
            masked += 1
        else:
            kept.append(vertex.index)
    group.add(kept, 1.0, "REPLACE")
    head["v27_upper_neck_restore"] = "natural upper neck restored above tapered lower-neck proxy"
    return {"kept_vertices": len(kept), "masked_vertices": masked}


def seat_seal(seal: bpy.types.Object) -> int:
    changed = 0
    for vertex in seal.data.vertices:
        point = vertex.co
        angle = math.atan2((point.y - 0.004) / 0.0685, point.x / 0.0885)
        center = Vector((
            0.0878 * math.cos(angle),
            0.004 + 0.0678 * math.sin(angle),
            1.4927 + 0.012 * math.sin(angle),
        ))
        offset = point - Vector((
            0.0885 * math.cos(angle),
            0.004 + 0.0685 * math.sin(angle),
            1.4932 + 0.012 * math.sin(angle),
        ))
        offset.z *= 0.72
        vertex.co = center + offset
        changed += 1
    seal["v27_seating"] = "compression seal inset into welded garment boundary"
    return changed


def smooth_masked_head_boundary(head: bpy.types.Object) -> str:
    modifier = head.modifiers.get("V27_MaskedBoundarySubdivision")
    if modifier is None:
        modifier = head.modifiers.new("V27_MaskedBoundarySubdivision", "SUBSURF")
    modifier.subdivision_type = "CATMULL_CLARK"
    modifier.levels = 1
    modifier.render_levels = 1
    modifier.show_only_control_edges = True
    head["v27_boundary_finish"] = "post-mask subdivision softens inherited rear-neck stair stepping"
    return modifier.name


def remove_rear_neck_remnant(head: bpy.types.Object) -> int:
    group = head.vertex_groups["V24_HeadNeckKeep"]
    remove = []
    for vertex in head.data.vertices:
        world = head.matrix_world @ vertex.co
        if world.y > 0.090 and world.z < 1.680:
            remove.append(vertex.index)
    if remove:
        group.remove(remove)
    head["v27_rear_neck_cleanup"] = "lower rear remnant removed from existing non-destructive mask"
    return len(remove)


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
    scene.render.filepath = str(PREVIEWS / f"PlayerCharacter_CryoBodysuit_v27_{label}.png")
    bpy.ops.render.render(write_still=True)


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects["RIG_PlayerCharacter_CryoBodysuit_v26"]
    rig.name = "RIG_PlayerCharacter_CryoBodysuit_v27"
    body = bpy.data.objects["SK_PlayerCharacter_CryoBodysuit_v26"]
    body.name = "SK_PlayerCharacter_CryoBodysuit_v27"
    seal = bpy.data.objects["SK_PlayerCharacter_CryoNeckSeal_v26"]
    seal.name = "SK_PlayerCharacter_CryoNeckSeal_v27"
    for old, new in (
        ("SK_CryoSeam_CenterFront_v26", "SK_CryoSeam_CenterFront_v27"),
        ("SK_CryoSeam_LeftLeg_v26", "SK_CryoSeam_LeftLeg_v27"),
        ("SK_CryoSeam_RightLeg_v26", "SK_CryoSeam_RightLeg_v27"),
    ):
        bpy.data.objects[old].name = new

    head = bpy.data.objects["SK_PlayerHead_Production_v6"]
    rear_vertices = 0
    boundary_modifier = smooth_masked_head_boundary(head)
    seal_vertices = seat_seal(seal)
    body["asset_status"] = "CHARACTER_CRYO_BODYSUIT_V27_CLEAN_NECK_REVIEW"
    body["contains_oversuit"] = False

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    render(scene, camera, "Front", Vector((0, -4.10, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 82)
    render(scene, camera, "Profile", Vector((4.10, 0, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 82)
    render(scene, camera, "NeckInterfaceDetail", Vector((0.82, -1.90, 1.51)), Vector((0, 0, 1.49)), (1100, 1000), 102)
    pose_cryo_wake(rig)
    render(scene, camera, "CryoWakePose", Vector((2.75, -3.35, 1.16)), Vector((0, 0, 1.04)), (1100, 1000), 82)
    clear_pose(rig)
    bpy.context.window.scene = original_scene

    result = {
        "schema": 1,
        "asset": "PlayerCharacter_CryoBodysuit_Concept_v27",
        "status": "clean_neck_interface_review",
        "contains_oversuit": False,
        "head_boundary_modifier": boundary_modifier,
        "rear_head_vertices_masked": rear_vertices,
        "seal_vertices_seated": seal_vertices,
        "production_head_topology_modified": False,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V27_CLEAN_NECK_INTERFACE", json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
