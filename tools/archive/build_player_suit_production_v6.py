"""Build the v6 player suit review asset from the validated v5 checkpoint.

This pass replaces the low-resolution generated face presentation with a
topology-correct, UV-textured human head; refines the helmet collar; and adds
Unreal-ready LOD review meshes without modifying v5.
"""

from __future__ import annotations

from pathlib import Path

import bpy
from mathutils import Matrix, Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE_BLEND = SUIT_DIR / "PlayerSuit_Production_v5.blend"
HEAD_BLEND = SUIT_DIR / "PlayerHead_MakeHuman_Source.blend"
OUTPUT_BLEND = SUIT_DIR / "PlayerSuit_Production_v6.blend"
PREVIEW_DIR = SUIT_DIR / "Production_v6_Previews"

SOURCE_EYE_CENTER = Vector((0.0, -0.10871, 1.45128))
TARGET_EYE_CENTER = Vector((0.0, -0.12600, 1.69500))
HEAD_SCALE = 1.12

HEAD_OBJECTS = (
    "SRC_PlayerHead_MakeHuman",
    "HEAD_Hair_Short02_CC0",
    "HEAD_Eye_L",
    "HEAD_Eye_R",
    "HEAD_Iris_L",
    "HEAD_Iris_R",
    "HEAD_Pupil_L",
    "HEAD_Pupil_R",
    "HEAD_Brow_L",
    "HEAD_Brow_R",
)


def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.hide_set(False)
    obj.hide_viewport = False
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def move_to_collection(obj, collection):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def evaluated_vertex_coordinate(obj, index):
    keys = obj.data.shape_keys.key_blocks if obj.data.shape_keys else None
    if not keys:
        return obj.data.vertices[index].co.copy()
    basis = keys[0].data[index].co
    co = basis.copy()
    for key in keys[1:]:
        if abs(key.value) > 1.0e-6:
            co += (key.data[index].co - basis) * key.value
    return co


def import_head(collection):
    with bpy.data.libraries.load(str(HEAD_BLEND), link=False) as (source, destination):
        requested_names = tuple(name for name in HEAD_OBJECTS if name in source.objects)
        destination.objects = list(requested_names)
    imported = {
        requested_name: obj
        for requested_name, obj in zip(requested_names, destination.objects)
        if obj is not None
    }
    missing = sorted(set(HEAD_OBJECTS) - set(imported))
    if missing:
        raise RuntimeError(f"Head source objects missing: {missing}")

    common = (
        Matrix.Translation(TARGET_EYE_CENTER)
        @ Matrix.Scale(HEAD_SCALE, 4)
        @ Matrix.Translation(-SOURCE_EYE_CENTER)
    )
    for obj in imported.values():
        source_world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = common @ source_world
        move_to_collection(obj, collection)
        obj.hide_render = False
        obj.hide_set(False)
        obj.hide_viewport = False
        obj["production_head_component"] = True

    for source_name, obj in imported.items():
        obj.name = "V6_" + source_name

    face = imported["SRC_PlayerHead_MakeHuman"]
    face.name = "SK_PlayerHead_Production_v6"
    face.data.name = "SK_PlayerHead_Production_v6_Mesh"
    visible = face.vertex_groups.get("V6_Head_Visible") or face.vertex_groups.new(name="V6_Head_Visible")
    keep = [
        vertex.index
        for vertex in face.data.vertices
        if evaluated_vertex_coordinate(face, vertex.index).z >= 1.275
    ]
    visible.add(keep, 1.0, "REPLACE")
    trim = face.modifiers.new("V6_Trim_Below_Collar", "MASK")
    trim.vertex_group = visible.name
    trim.threshold = 0.5

    face["topology_source"] = "MakeHuman/MPFB2 CC0 basemesh"
    face["skin_source"] = "MakeHuman system assets CC0 young_caucasian_female"
    face["facial_shape_key_count"] = len(face.data.shape_keys.key_blocks) if face.data.shape_keys else 0
    face["head_scale"] = HEAD_SCALE
    return imported


def parent_to_bone(objects, armature, bone_name="head"):
    root = objects["SRC_PlayerHead_MakeHuman"]
    relative_matrices = {
        source_name: root.matrix_world.inverted() @ obj.matrix_world
        for source_name, obj in objects.items()
        if source_name != "SRC_PlayerHead_MakeHuman"
    }
    world = root.matrix_world.copy()
    root.parent = armature
    root.parent_type = "BONE"
    root.parent_bone = bone_name
    root.matrix_world = world
    bpy.context.view_layer.update()
    for source_name, obj in objects.items():
        if source_name == "SRC_PlayerHead_MakeHuman":
            continue
        if obj.data and hasattr(obj.data, "transform"):
            if source_name.startswith("HEAD_Eye_"):
                side = 1.0 if source_name.endswith("_L") else -1.0
                local = Vector((0.02831 * side, -0.10871, 1.45128))
                obj.data.transform(Matrix.Translation(local))
            elif source_name.startswith("HEAD_Iris_"):
                side = 1.0 if source_name.endswith("_L") else -1.0
                local = Vector((0.02831 * side, -0.12196, 1.45128))
                obj.data.transform(Matrix.Translation(local))
            elif source_name.startswith("HEAD_Pupil_"):
                side = 1.0 if source_name.endswith("_L") else -1.0
                local = Vector((0.02831 * side, -0.12336, 1.45128))
                obj.data.transform(Matrix.Translation(local))
            else:
                obj.data.transform(relative_matrices[source_name])
        obj.parent = root
        obj.parent_type = "OBJECT"
        obj.parent_bone = ""
        obj.matrix_parent_inverse = Matrix.Identity(4)
        obj.matrix_basis = Matrix.Identity(4)
    bpy.context.view_layer.update()


def trim_legacy_head(target):
    group = target.vertex_groups.get("V6_Suit_Below_Collar") or target.vertex_groups.new(
        name="V6_Suit_Below_Collar"
    )
    keep = [
        vertex.index
        for vertex in target.data.vertices
        if (target.matrix_world @ vertex.co).z <= 1.505
    ]
    group.add(keep, 1.0, "REPLACE")
    mask = target.modifiers.get("V6_Remove_Legacy_Generated_Head") or target.modifiers.new(
        "V6_Remove_Legacy_Generated_Head", "MASK"
    )
    mask.vertex_group = group.name
    mask.threshold = 0.5
    target.modifiers.move(len(target.modifiers) - 1, 0)
    target["legacy_head_removed"] = True


def create_neck_gasket(collection):
    material = bpy.data.materials.get("M_V6_NeckGasket") or bpy.data.materials.new("M_V6_NeckGasket")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.012, 0.016, 0.020, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.66
    bsdf.inputs["Metallic"].default_value = 0.08
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=0.118, depth=0.105, location=(0.0, 0.006, 1.515))
    gasket = bpy.context.object
    gasket.name = "SKV6_Helmet_InnerNeckGasket"
    gasket.scale.y = 1.04
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    gasket.data.materials.append(material)
    bevel = gasket.modifiers.new("Pressure_Gasket_Rounding", "BEVEL")
    bevel.width = 0.012
    bevel.segments = 4
    for poly in gasket.data.polygons:
        poly.use_smooth = True
    gasket["rig_attachment"] = "chest"
    gasket["production_accessory"] = True
    move_to_collection(gasket, collection)
    return gasket


def refine_helmet():
    scales = {
        "SKV5_Helmet_LowerPressureRing": (0.86, 0.86, 0.58),
        "SKV5_Helmet_UpperIvoryRing": (0.89, 0.89, 0.62),
        "SKV5_Helmet_LockBand": (0.91, 0.91, 0.72),
    }
    refined = {}
    for old_name, factors in scales.items():
        obj = bpy.data.objects.get(old_name)
        if obj is None:
            print(f"HELMET_WARNING missing={old_name}")
            continue
        obj.name = old_name.replace("SKV5_", "SKV6_")
        obj.scale = tuple(obj.scale[i] * factors[i] for i in range(3))
        obj["v6_proportion_refined"] = True
        refined[obj.name] = obj
    dome = bpy.data.objects.get("SKV5_Helmet_ClearDome")
    if dome:
        dome.name = "SKV6_Helmet_ClearDome"
        dome["v6_proportion_refined"] = True
        refined[dome.name] = dome

    # The earlier procedural head and unprefixed helmet pieces are reference
    # objects only; force them out of production renders.
    for obj in bpy.data.objects:
        if obj.name.startswith("HEAD_") or obj.name == "Head_HairMass":
            obj.hide_render = True
        if obj.name.startswith("Helmet_"):
            obj.hide_render = True
    return refined


def upgrade_visor_material(dome):
    if dome is None or not dome.data.materials:
        return
    material = dome.data.materials[0].copy()
    material.name = "M_Visor_Clear_v6"
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = (0.008, 0.020, 0.030, 1.0)
        bsdf.inputs["Roughness"].default_value = 0.09
        if "Transmission Weight" in bsdf.inputs:
            bsdf.inputs["Transmission Weight"].default_value = 0.72
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = 0.38
        if "Coat Roughness" in bsdf.inputs:
            bsdf.inputs["Coat Roughness"].default_value = 0.08
        bsdf.inputs["IOR"].default_value = 1.45
        bsdf.inputs["Alpha"].default_value = 0.23
    material.diffuse_color = (0.012, 0.03, 0.045, 0.23)
    if hasattr(material, "surface_render_method"):
        material.surface_render_method = "DITHERED"
    dome.data.materials[0] = material
    dome.visible_shadow = False


def upgrade_suit_material(target):
    if not target.data.materials:
        return
    material = target.data.materials[0].copy()
    material.name = "M_PlayerSuit_Production_v6_Detail"
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    if bsdf is None:
        target.data.materials[0] = material
        return

    weave = nodes.new("ShaderNodeTexNoise")
    weave.name = "V6_Fabric_Microstructure"
    weave.inputs["Scale"].default_value = 185.0
    weave.inputs["Detail"].default_value = 2.2
    weave.inputs["Roughness"].default_value = 0.72
    bump = nodes.new("ShaderNodeBump")
    bump.name = "V6_Fabric_MicroBump"
    bump.inputs["Strength"].default_value = 0.16
    bump.inputs["Distance"].default_value = 0.0014
    existing_normal = bsdf.inputs["Normal"].links[0].from_socket if bsdf.inputs["Normal"].is_linked else None
    if existing_normal:
        links.new(existing_normal, bump.inputs["Normal"])
    links.new(weave.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    rough_noise = nodes.new("ShaderNodeTexNoise")
    rough_noise.name = "V6_Roughness_Breakup"
    rough_noise.inputs["Scale"].default_value = 38.0
    rough_noise.inputs["Detail"].default_value = 3.0
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.name = "V6_Roughness_Range"
    ramp.color_ramp.elements[0].color = (0.34, 0.34, 0.34, 1.0)
    ramp.color_ramp.elements[1].color = (0.68, 0.68, 0.68, 1.0)
    links.new(rough_noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Roughness"])
    target.data.materials[0] = material


def create_lod(source, collection, level, ratio):
    name = f"SK_PlayerSuit_Production_v6_LOD{level}"
    existing = bpy.data.objects.get(name)
    if existing:
        bpy.data.objects.remove(existing, do_unlink=True)
    lod = source.copy()
    lod.data = source.data.copy()
    lod.name = name
    lod.data.name = name + "_Mesh"
    collection.objects.link(lod)
    lod.hide_render = True
    lod.hide_set(True)
    lod.hide_viewport = True
    decimate = lod.modifiers.new(f"LOD{level}_Decimate", "DECIMATE")
    decimate.ratio = ratio
    decimate.use_collapse_triangulate = True
    lod.modifiers.move(len(lod.modifiers) - 1, 0)
    select_only(lod)
    bpy.ops.object.modifier_apply(modifier=decimate.name)
    lod.hide_set(True)
    lod.hide_viewport = True
    lod["lod_level"] = level
    lod["source_lod"] = "SK_PlayerSuit_Production_v6_LOD0"
    lod["target_ratio"] = ratio
    lod["uv0_present"] = bool(lod.data.uv_layers.get("UV0"))
    lod["vertex_group_count"] = len(lod.vertex_groups)
    return lod


def triangle_count(obj):
    return sum(max(0, len(poly.vertices) - 2) for poly in obj.data.polygons)


def render_reviews(target, head_objects, helmet):
    scene = bpy.data.scenes.get("SCENE_HighPolyReview")
    camera = bpy.data.objects.get("CAM_HighPolyReview")
    if scene is None or camera is None:
        raise RuntimeError("v5 review scene/camera missing")
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    target.hide_render = False
    for obj in head_objects.values():
        obj.hide_render = False
    for obj in helmet.values():
        obj.hide_render = False

    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    camera.data.lens = 55
    target_point = Vector((0, 0, 0.94))
    views = {
        "Front": Vector((0, -5, 1)),
        "Back": Vector((0, 5, 1)),
        "Side": Vector((5, 0, 1)),
        "ThreeQuarter": Vector((3.6, -3.6, 1.05)),
    }
    for label, position in views.items():
        camera.location = position
        camera.rotation_euler = (target_point - position).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(PREVIEW_DIR / f"PlayerSuit_Production_v6_{label}.png")
        bpy.ops.render.render(write_still=True)

    scene.render.resolution_x = 1024
    scene.render.resolution_y = 1024
    camera.data.type = "PERSP"
    camera.data.lens = 85
    head_target = Vector((0.0, -0.015, 1.68))
    camera.location = Vector((0.0, -0.58, 1.68))
    camera.rotation_euler = (head_target - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(PREVIEW_DIR / "PlayerSuit_Production_v6_HeadCloseup.png")
    bpy.ops.render.render(write_still=True)
    bpy.context.window.scene = original_scene


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE_BLEND))
    v5 = bpy.data.objects.get("SK_PlayerSuit_Production_v5")
    armature = bpy.data.objects.get("RIG_PlayerSuit_Production_v5")
    collection = bpy.data.collections.get("SUIT_PRODUCTION_v5")
    if not v5 or not armature or not collection:
        raise RuntimeError("Validated v5 suit, rig, or collection missing")
    collection.name = "SUIT_PRODUCTION_v6"
    v5.name = "SK_PlayerSuit_Production_v6_LOD0"
    v5.data.name = "SK_PlayerSuit_Production_v6_LOD0_Mesh"
    armature.name = "RIG_PlayerSuit_Production_v6"
    armature.data.name = "RIG_PlayerSuit_Production_v6_Data"

    helmet = refine_helmet()
    upgrade_visor_material(helmet.get("SKV6_Helmet_ClearDome"))
    upgrade_suit_material(v5)
    trim_legacy_head(v5)
    gasket = create_neck_gasket(collection)
    helmet[gasket.name] = gasket
    head_objects = import_head(collection)
    parent_to_bone(head_objects, armature, "head")

    lod1 = create_lod(v5, collection, 1, 0.50)
    lod2 = create_lod(v5, collection, 2, 0.25)

    v5["asset_status"] = "ART_DIRECTION_REVIEW_V6"
    v5["concept_fidelity_pass"] = "anatomical head, CC0 skin/hair, slim collar"
    v5["lod1_triangles"] = triangle_count(lod1)
    v5["lod2_triangles"] = triangle_count(lod2)
    v5["closeup_gate"] = "pending art-director approval"
    armature["rig_standard"] = "Ginnungagap humanoid v6"

    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND), check_existing=False)
    render_reviews(v5, head_objects, helmet)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND), check_existing=False)

    face = head_objects["SRC_PlayerHead_MakeHuman"]
    print(
        "V6_VALIDATION",
        f"lod0_tris={triangle_count(v5)}",
        f"lod1_tris={triangle_count(lod1)}",
        f"lod2_tris={triangle_count(lod2)}",
        f"uv0={bool(v5.data.uv_layers.get('UV0'))}",
        f"weights={len(v5.vertex_groups)}",
        f"face_verts={len(face.data.vertices)}",
        f"face_polys={len(face.data.polygons)}",
        f"face_shape_keys={len(face.data.shape_keys.key_blocks) if face.data.shape_keys else 0}",
    )
    print("SAVED_V6", OUTPUT_BLEND)


if __name__ == "__main__":
    main()
