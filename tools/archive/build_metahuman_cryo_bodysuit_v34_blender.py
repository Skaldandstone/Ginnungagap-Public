"""Build a continuous fitted cryo bodysuit from the assembled MetaHuman body/outfit coverage."""

import json
import os

import bpy
from mathutils import Vector


PROJECT_DIR = r"C:\Users\James\Documents\Unreal Projects\Ginnungagap"
SOURCE_DIR = os.path.join(PROJECT_DIR, "Build", "Unreal", "PlayerSuits", "MetaHumanCryoSources")
BODY_FBX = os.path.join(SOURCE_DIR, "MHC_Face01_Ada_Body_Recovered.fbx")
OUTFIT_FBX = os.path.join(SOURCE_DIR, "MHC_Face01_Ada_Outfit_Recovered.fbx")
OUTPUT_DIR = os.path.join(PROJECT_DIR, "Build", "Unreal", "PlayerSuits", "CryoBodysuitV34")
OUTPUT_FBX = os.path.join(OUTPUT_DIR, "SK_CryoBodysuit_V34_Face01.fbx")
REPORT_PATH = os.path.join(PROJECT_DIR, "Saved", "CryoBodysuitV34Build.json")
RENDER_PATH = os.path.join(
    PROJECT_DIR, "Saved", "Renders", "CharacterCreator", "CryoBodysuitV34_Face01_Rest.png"
)


def import_fbx(path):
    before = set(bpy.context.scene.objects)
    bpy.ops.wm.fbx_import(filepath=path, use_anim=False)
    return list(set(bpy.context.scene.objects) - before)


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


def render_object(subject):
    corners = [subject.matrix_world @ Vector(corner) for corner in subject.bound_box]
    minimum = Vector((min(v.x for v in corners), min(v.y for v in corners), min(v.z for v in corners)))
    maximum = Vector((max(v.x for v in corners), max(v.y for v in corners), max(v.z for v in corners)))
    center = (minimum + maximum) * 0.5
    extent = maximum - minimum

    material = bpy.data.materials.new("M_CryoBodysuit_V34_Preview")
    material.diffuse_color = (0.055, 0.18, 0.26, 1.0)
    material.metallic = 0.04
    material.roughness = 0.68
    subject.data.materials.clear()
    subject.data.materials.append(material)
    for polygon in subject.data.polygons:
        polygon.material_index = 0

    world = bpy.context.scene.world or bpy.data.worlds.new("CryoInspectionWorld")
    bpy.context.scene.world = world
    world.color = (0.004, 0.008, 0.015)

    camera_data = bpy.data.cameras.new("CryoInspectionCamera")
    camera = bpy.data.objects.new("CryoInspectionCamera", camera_data)
    bpy.context.collection.objects.link(camera)
    bpy.context.scene.camera = camera
    distance = max(extent.z * 1.75, extent.x * 2.7, 2.5)
    camera.location = center + Vector((0.0, -distance, extent.z * 0.03))
    camera.data.lens = 58
    point_at(camera, center)

    for name, offset, energy, color, size in (
        ("Key", Vector((-extent.x, -distance * 0.3, extent.z * 0.55)), 1800.0, (0.65, 0.82, 1.0), 90.0),
        ("Fill", Vector((extent.x, -distance * 0.1, extent.z * 0.05)), 900.0, (1.0, 0.48, 0.30), 75.0),
        ("Rim", Vector((0.0, distance * 0.25, extent.z * 0.55)), 2200.0, (0.28, 0.48, 1.0), 70.0),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy = energy
        data.color = color
        data.shape = "DISK"
        data.size = size
        light = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(light)
        light.location = center + offset
        point_at(light, center)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = RENDER_PATH
    scene.view_settings.look = "AgX - Medium High Contrast"
    bpy.ops.render.render(write_still=True)
    return minimum, maximum


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(os.path.dirname(RENDER_PATH), exist_ok=True)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 0.01

    body_objects = import_fbx(BODY_FBX)
    outfit_objects = import_fbx(OUTFIT_FBX)
    body_mesh = next(obj for obj in body_objects if obj.type == "MESH")
    outfit_mesh = next(obj for obj in outfit_objects if obj.type == "MESH")
    body_armature = next(obj for obj in body_objects if obj.type == "ARMATURE")
    outfit_armature = next(obj for obj in outfit_objects if obj.type == "ARMATURE")

    # Both exports share bone names. Consolidate onto one armature before creating the union source.
    for modifier in list(outfit_mesh.modifiers):
        if modifier.type == "ARMATURE":
            outfit_mesh.modifiers.remove(modifier)
    outfit_modifier = outfit_mesh.modifiers.new("MetaHuman Body Skeleton", "ARMATURE")
    outfit_modifier.object = body_armature

    bpy.ops.object.select_all(action="DESELECT")
    body_mesh.select_set(True)
    outfit_mesh.select_set(True)
    bpy.context.view_layer.objects.active = body_mesh
    bpy.ops.object.join()
    transfer_source = body_mesh
    transfer_source.name = "V34_WeightTransferSource"

    rebuilt = transfer_source.copy()
    rebuilt.data = transfer_source.data.copy()
    bpy.context.collection.objects.link(rebuilt)
    rebuilt.name = "SK_CryoBodysuit_V34_Face01"
    for modifier in list(rebuilt.modifiers):
        rebuilt.modifiers.remove(modifier)

    bpy.context.view_layer.objects.active = rebuilt
    rebuilt.select_set(True)
    transfer_source.select_set(False)
    bridge = rebuilt.modifiers.new("Compression Shell Bridge", "SOLIDIFY")
    bridge.thickness = 1.0
    bridge.offset = 0.0
    bridge.use_even_offset = True
    bpy.ops.object.modifier_apply(modifier=bridge.name)

    rebuilt.data.remesh_voxel_size = 0.8
    rebuilt.data.remesh_voxel_adaptivity = 0.0
    bpy.ops.object.voxel_remesh()

    local_min_z = min(vertex.co.z for vertex in rebuilt.data.vertices)
    local_max_z = max(vertex.co.z for vertex in rebuilt.data.vertices)
    local_half_width = max(abs(vertex.co.x) for vertex in rebuilt.data.vertices)
    center_y = sum(vertex.co.y for vertex in rebuilt.data.vertices) / len(rebuilt.data.vertices)
    height = max(local_max_z - local_min_z, 0.001)
    for vertex in rebuilt.data.vertices:
        normalized_z = (vertex.co.z - local_min_z) / height
        centrality = max(0.0, 1.0 - abs(vertex.co.x) / max(local_half_width * 0.72, 0.001))
        body_band = max(0.0, min(1.0, (normalized_z - 0.39) / 0.10))
        body_band *= max(0.0, min(1.0, (1.02 - normalized_z) / 0.10))
        fit = centrality * body_band
        vertex.co.x *= 1.0 - 0.055 * fit
        vertex.co.y = center_y + (vertex.co.y - center_y) * (1.0 - 0.10 * fit)

    # Relax the union just enough to remove clothing hems without erasing anatomy.
    smooth = rebuilt.modifiers.new("Compression Surface Relax", "LAPLACIANSMOOTH")
    smooth.iterations = 10
    smooth.lambda_factor = 0.26
    bpy.context.view_layer.objects.active = rebuilt
    bpy.ops.object.modifier_apply(modifier=smooth.name)

    bpy.context.view_layer.objects.active = rebuilt
    rebuilt.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    for polygon in rebuilt.data.polygons:
        polygon.use_smooth = True

    for group in transfer_source.vertex_groups:
        rebuilt.vertex_groups.new(name=group.name)
    transfer = rebuilt.modifiers.new("Transfer MetaHuman Skin Weights", "DATA_TRANSFER")
    transfer.object = transfer_source
    transfer.use_vert_data = True
    transfer.data_types_verts = {"VGROUP_WEIGHTS"}
    transfer.vert_mapping = "POLYINTERP_NEAREST"
    transfer.layers_vgroup_select_src = "ALL"
    transfer.layers_vgroup_select_dst = "NAME"
    bpy.context.view_layer.objects.active = rebuilt
    bpy.ops.object.modifier_apply(modifier=transfer.name)

    armature_modifier = rebuilt.modifiers.new("MetaHuman Body Skeleton", "ARMATURE")
    armature_modifier.object = body_armature

    transfer_source.hide_render = True
    outfit_armature.hide_render = True
    minimum, maximum = render_object(rebuilt)

    bpy.ops.object.select_all(action="DESELECT")
    rebuilt.select_set(True)
    body_armature.select_set(True)
    bpy.context.view_layer.objects.active = rebuilt
    bpy.ops.export_scene.fbx(
        filepath=OUTPUT_FBX,
        use_selection=True,
        object_types={"ARMATURE", "MESH"},
        add_leaf_bones=False,
        bake_anim=False,
        apply_unit_scale=True,
        use_space_transform=True,
        axis_forward="-Z",
        axis_up="Y",
    )

    report = {
        "status": "pass",
        "output": OUTPUT_FBX,
        "bytes": os.path.getsize(OUTPUT_FBX),
        "vertices": len(rebuilt.data.vertices),
        "polygons": len(rebuilt.data.polygons),
        "vertex_groups": len(rebuilt.vertex_groups),
        "armature_bones": len(body_armature.data.bones),
        "body_source_vertices": len(body_mesh.data.vertices),
        "bounds_min": list(minimum),
        "bounds_max": list(maximum),
        "render": RENDER_PATH,
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as report_file:
        json.dump(report, report_file, indent=2)


main()
