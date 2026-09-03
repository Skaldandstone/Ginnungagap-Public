"""Rebuild the segmented V19 garment as a continuous cryo compression suit."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerCharacter_Undersuit_Concept_v19.blend"
OUTPUT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v20.blend"
PREVIEWS = SUIT_DIR / "Production_v20_Previews"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v20_Rebuild.json"
CONCEPT = "docs/concept-art/reference/rooms/cryo-awakening-compact-damaged-concept.png"


def active(obj) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def apply_modifier(obj, modifier) -> None:
    active(obj)
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def rebuild_shell(source: bpy.types.Object, rig: bpy.types.Object) -> bpy.types.Object:
    body = source.copy()
    body.data = source.data.copy()
    body.name = "SK_PlayerCharacter_CryoBodysuit_v20"
    bpy.context.collection.objects.link(body)
    for modifier in list(body.modifiers):
        body.modifiers.remove(modifier)

    remesh = body.modifiers.new("V20_ContinuousCryoShell", "REMESH")
    remesh.mode = "VOXEL"
    remesh.voxel_size = 0.007
    remesh.adaptivity = 0.0
    remesh.use_remove_disconnected = True
    remesh.use_smooth_shade = True
    apply_modifier(body, remesh)

    smooth = body.modifiers.new("V20_AnatomicalSurface", "SMOOTH")
    smooth.factor = 0.48
    smooth.iterations = 5
    smooth.use_x = True
    smooth.use_y = True
    smooth.use_z = True
    apply_modifier(body, smooth)

    # Voxel remeshing seals open boundaries. Restore the close neck opening so
    # the character head remains physically independent from the garment.
    mesh = bmesh.new()
    mesh.from_mesh(body.data)
    inverse = body.matrix_world.inverted()
    del inverse  # Coordinates are local; source character objects use identity transforms.
    neck_vertices = []
    for vertex in mesh.verts:
        point = vertex.co
        if 1.080 < point.z < 1.585 and point.y > 0.180:
            point.y = 0.180 + (point.y - 0.180) * 0.05
        if 1.350 < point.z < 1.585 and point.y > 0.140:
            point.y = 0.140 + (point.y - 0.140) * 0.15
        embedded_head = point.z > 1.545 and abs(point.x) < 0.260 and abs(point.y) < 0.225
        neck_opening = (
            point.z > 1.455
            and (point.x / 0.108) ** 2 + ((point.y - 0.004) / 0.090) ** 2 < 1.0
        )
        if embedded_head or neck_opening:
            neck_vertices.append(vertex)
    bmesh.ops.delete(mesh, geom=neck_vertices, context="VERTS")
    mesh.to_mesh(body.data)
    mesh.free()
    body.data.update()

    # Recreate all destination groups before interpolation from the production rigged source.
    body.vertex_groups.clear()
    for group in source.vertex_groups:
        body.vertex_groups.new(name=group.name)
    transfer = body.modifiers.new("V20_TransferProductionWeights", "DATA_TRANSFER")
    transfer.object = source
    transfer.use_vert_data = True
    transfer.data_types_verts = {"VGROUP_WEIGHTS"}
    transfer.vert_mapping = "POLYINTERP_NEAREST"
    transfer.layers_vgroup_select_src = "ALL"
    transfer.layers_vgroup_select_dst = "NAME"
    apply_modifier(body, transfer)

    armature = body.modifiers.new("V20_Armature", "ARMATURE")
    armature.object = rig
    body.parent = rig
    body["semantic_layer"] = "character_cryo_bodysuit"
    body["contains_oversuit"] = False
    body["concept_reference"] = CONCEPT
    body["v20_topology"] = "continuous voxel-fused anatomical shell"
    return body


def cryo_material(source_material: bpy.types.Material) -> bpy.types.Material:
    material = source_material.copy()
    material.name = "M_V20_CryoCompressionFabric"
    material["v20_finish"] = "pale medical compression knit; wet cryo-safe surface"
    nodes = material.node_tree.nodes
    palette = nodes.get("V18_DyePalette")
    if palette:
        palette.color_ramp.elements[0].color = (0.055, 0.075, 0.080, 1)
        palette.color_ramp.elements[1].color = (0.170, 0.205, 0.210, 1)
        palette.color_ramp.elements[0].position = 0.30
        palette.color_ramp.elements[1].position = 0.70
    roughness = nodes.get("V18_RoughnessBreakup")
    if roughness:
        roughness.color_ramp.elements[0].color = (0.66, 0.66, 0.66, 1)
        roughness.color_ramp.elements[1].color = (0.82, 0.82, 0.82, 1)
    bump = nodes.get("V18_TextileNormal")
    if bump:
        bump.inputs["Strength"].default_value = 0.032
        bump.inputs["Distance"].default_value = 0.00032
    return material


def rebuild_close_collar(rig: bpy.types.Object, material) -> bpy.types.Object:
    segments = 96
    rings = (
        (0.094, 0.078, 1.462),
        (0.093, 0.077, 1.474),
        (0.092, 0.076, 1.488),
        (0.091, 0.075, 1.503),
    )
    vertices = []
    faces = []
    for rx, ry, z in rings:
        for index in range(segments):
            angle = 2 * math.pi * index / segments
            vertices.append((rx * math.cos(angle), ry * math.sin(angle) + 0.004, z))
    for ring in range(len(rings) - 1):
        for index in range(segments):
            following = (index + 1) % segments
            first = ring * segments + index
            second = ring * segments + following
            third = (ring + 1) * segments + following
            fourth = (ring + 1) * segments + index
            faces.append((first, second, third, fourth))
    mesh = bpy.data.meshes.new("SK_PlayerCharacter_CryoCollar_v20_Mesh")
    mesh.from_pydata(vertices, [], faces)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    collar = bpy.data.objects.new("SK_PlayerCharacter_CryoCollar_v20", mesh)
    bpy.context.collection.objects.link(collar)

    neck = collar.vertex_groups.new(name="neck")
    chest = collar.vertex_groups.new(name="chest")
    for ring in range(len(rings)):
        indices = list(range(ring * segments, (ring + 1) * segments))
        neck_weight = ring / (len(rings) - 1)
        neck.add(indices, neck_weight, "REPLACE")
        chest.add(indices, 1.0 - neck_weight, "REPLACE")
    armature = collar.modifiers.new("V20_CollarArmature", "ARMATURE")
    armature.object = rig
    solidify = collar.modifiers.new("V20_CollarThickness", "SOLIDIFY")
    solidify.thickness = 0.0012
    solidify.offset = 0.0
    bevel = collar.modifiers.new("V20_CollarSoftEdge", "BEVEL")
    bevel.width = 0.0008
    bevel.segments = 2
    collar.data.materials.clear()
    collar.data.materials.append(material)
    collar.parent = rig
    collar["semantic_layer"] = "character_cryo_bodysuit"
    collar["contains_oversuit"] = False
    collar["v20_design_role"] = "close flexible cryo garment neck seal"
    return collar


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
    active(armature)
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
    scene.render.filepath = str(PREVIEWS / f"PlayerCharacter_CryoBodysuit_v20_{label}.png")
    bpy.ops.render.render(write_still=True)


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects["RIG_PlayerCharacter_Undersuit_v19"]
    rig.name = "RIG_PlayerCharacter_CryoBodysuit_v20"
    source = bpy.data.objects["SK_PlayerCharacter_Undersuit_v19"]
    old_yoke = bpy.data.objects["SK_PlayerUndersuit_NeckYoke_v19"]
    body = rebuild_shell(source, rig)
    material = cryo_material(bpy.data.materials["M_V18_PressureWeave_Base"])
    body.data.materials.clear()
    body.data.materials.append(material)
    collar = rebuild_close_collar(rig, material)

    bpy.data.objects.remove(source, do_unlink=True)
    bpy.data.objects.remove(old_yoke, do_unlink=True)
    body["asset_status"] = "CHARACTER_CRYO_BODYSUIT_V20_CONCEPT_REVIEW"

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    render(scene, camera, "Front", Vector((0, -4.15, 1.12)), Vector((0, 0, 1.09)), (900, 1100), 74)
    render(scene, camera, "Profile", Vector((4.15, 0, 1.12)), Vector((0, 0, 1.09)), (900, 1100), 74)
    render(scene, camera, "UpperBody", Vector((1.15, -2.55, 1.28)), Vector((0, 0, 1.22)), (1100, 1000), 92)
    pose_cryo_wake(rig)
    render(scene, camera, "CryoWakePose", Vector((2.75, -3.35, 1.16)), Vector((0, 0, 1.04)), (1100, 1000), 74)
    clear_pose(rig)
    bpy.context.window.scene = original_scene

    REPORT.write_text(json.dumps({
        "schema": 1,
        "asset": "PlayerCharacter_CryoBodysuit_Concept_v20",
        "status": "concept_review",
        "concept_reference": CONCEPT,
        "contains_oversuit": False,
        "topology": body.get("v20_topology"),
        "body_vertices": len(body.data.vertices),
        "body_polygons": len(body.data.polygons),
        "vertex_groups": len(body.vertex_groups),
        "material": material.name,
        "collar": collar.name,
    }, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V20_CRYO_BODYSUIT", f"verts={len(body.data.vertices)}", f"polys={len(body.data.polygons)}", f"output={OUTPUT}")


if __name__ == "__main__":
    main()
