"""Turn the accepted concept-generated suit into a production review mesh.

The generated mesh is retained as a high-poly source.  A duplicate is made
manifold with voxel remesh, quad-retopologized, UV unwrapped, and receives
selected-to-active baked base-color and tangent-normal textures.
"""

from __future__ import annotations

import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE_BLEND = SUIT_DIR / "PlayerSuit_Production_v4.blend"
OUTPUT_BLEND = SUIT_DIR / "PlayerSuit_Production_v5.blend"
TEXTURE_DIR = SUIT_DIR / "Textures" / "Production_v5"
PREVIEW_DIR = SUIT_DIR / "Production_v5_Previews"


def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.hide_set(False)
    obj.hide_viewport = False
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def ensure_collection(name, parent=None):
    coll = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    owner = parent or bpy.context.scene.collection
    if coll.name not in [child.name for child in owner.children]:
        owner.children.link(coll)
    return coll


def link_only(obj, coll):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    coll.objects.link(obj)


def build_retopology(source):
    production = ensure_collection("SUIT_PRODUCTION_v5")
    existing = bpy.data.objects.get("SK_PlayerSuit_Production_v5")
    if existing:
        bpy.data.objects.remove(existing, do_unlink=True)

    target = source.copy()
    target.data = source.data.copy()
    target.name = "SK_PlayerSuit_Production_v5"
    link_only(target, production)
    target.hide_render = False
    target.hide_set(False)

    # Bake source orientation and dimensions into the production mesh.
    select_only(target)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Close the generated mesh's open boundaries while preserving the suit's
    # large forms and garment silhouette.
    target.data.remesh_voxel_size = 0.006
    bpy.ops.object.voxel_remesh()
    smooth = target.modifiers.new("Surface_Relax", "LAPLACIANSMOOTH")
    smooth.iterations = 2
    smooth.lambda_factor = 0.16
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.modifier_apply(modifier=smooth.name)

    select_only(target)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Produce an all-quad production cage at a density that retains the
    # concept-generated folds and primary hard-surface forms.
    select_only(target)
    bpy.ops.object.quadriflow_remesh(
        use_mesh_symmetry=True,
        use_preserve_sharp=True,
        use_preserve_boundary=False,
        preserve_attributes=False,
        smooth_normals=True,
        mode="FACES",
        target_faces=28000,
        seed=11,
    )
    for poly in target.data.polygons:
        poly.use_smooth = True

    # UV0 is created on the quad cage, independently from the generated mesh.
    select_only(target)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(
        angle_limit=math.radians(68),
        margin_method="SCALED",
        island_margin=0.006,
        area_weight=0.25,
        correct_aspect=True,
        scale_to_bounds=True,
    )
    bpy.ops.object.mode_set(mode="OBJECT")
    target.data.uv_layers.active.name = "UV0"

    target["production_role"] = "concept-derived all-quad render/deformation cage"
    target["retopology"] = "voxel manifold repair + QuadriFlow 28k target"
    target["uv_layout"] = "UV0 packed production review layout"
    target["source_highpoly"] = source.name
    target["unreal_export_allowed"] = False
    target["next_gate"] = "texture bake validation, deformation test, art approval"
    return target


def new_bake_material(target):
    mat = bpy.data.materials.get("M_PlayerSuit_Production_v5_Baked")
    if mat is None:
        mat = bpy.data.materials.new("M_PlayerSuit_Production_v5_Baked")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.48
    mat.node_tree.links.new(bsdf.outputs[0], output.inputs[0])
    target.data.materials.clear()
    target.data.materials.append(mat)
    return mat, bsdf


def make_image(name, colorspace):
    image = bpy.data.images.get(name)
    if image:
        bpy.data.images.remove(image)
    image = bpy.data.images.new(name, width=2048, height=2048, alpha=True)
    image.colorspace_settings.name = colorspace
    image.generated_color = (0.03, 0.03, 0.03, 1)
    return image


def active_image_node(material, name, image):
    node = material.node_tree.nodes.new("ShaderNodeTexImage")
    node.name = name
    node.image = image
    for candidate in material.node_tree.nodes:
        candidate.select = False
    node.select = True
    material.node_tree.nodes.active = node
    return node


def bake_maps(source, target):
    TEXTURE_DIR.mkdir(parents=True, exist_ok=True)
    material, bsdf = new_bake_material(target)
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.render.bake.use_selected_to_active = True
    scene.render.bake.cage_extrusion = 0.018
    scene.render.bake.max_ray_distance = 0.045
    scene.render.bake.margin = 12

    # Base color.
    base = make_image("T_PlayerSuit_v5_BaseColor", "sRGB")
    base_node = active_image_node(material, "BaseColor_BakeTarget", base)
    source.hide_set(False)
    source.hide_viewport = False
    source.hide_render = False
    bpy.ops.object.select_all(action="DESELECT")
    source.select_set(True)
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    try:
        bpy.ops.object.bake(type="DIFFUSE", pass_filter={"COLOR"})
        base.filepath_raw = str(TEXTURE_DIR / "T_PlayerSuit_v5_BaseColor.png")
        base.file_format = "PNG"
        base.save()
        material.node_tree.links.new(base_node.outputs["Color"], bsdf.inputs["Base Color"])
        target["basecolor_bake"] = "complete"
    except Exception as exc:
        target["basecolor_bake"] = f"failed: {exc}"
        print(f"BASECOLOR_BAKE_WARNING={exc}")

    # Tangent normal.
    normal = make_image("T_PlayerSuit_v5_Normal", "Non-Color")
    normal_node = active_image_node(material, "Normal_BakeTarget", normal)
    bpy.ops.object.select_all(action="DESELECT")
    source.select_set(True)
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    try:
        bpy.ops.object.bake(type="NORMAL", normal_space="TANGENT")
        normal.filepath_raw = str(TEXTURE_DIR / "T_PlayerSuit_v5_Normal.png")
        normal.file_format = "PNG"
        normal.save()
        normal_map = material.node_tree.nodes.new("ShaderNodeNormalMap")
        normal_map.inputs["Strength"].default_value = 0.72
        material.node_tree.links.new(normal_node.outputs["Color"], normal_map.inputs["Color"])
        material.node_tree.links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])
        target["normal_bake"] = "complete"
    except Exception as exc:
        target["normal_bake"] = f"failed: {exc}"
        print(f"NORMAL_BAKE_WARNING={exc}")

    source.hide_render = True
    source.hide_set(True)
    return material


def validate(target):
    bm = bmesh.new()
    bm.from_mesh(target.data)
    stats = {
        "vertices": len(bm.verts),
        "faces": len(bm.faces),
        "triangles": sum(len(face.verts) == 3 for face in bm.faces),
        "quads": sum(len(face.verts) == 4 for face in bm.faces),
        "ngons": sum(len(face.verts) > 4 for face in bm.faces),
        "boundary_edges": sum(edge.is_boundary for edge in bm.edges),
        "nonmanifold_edges": sum(not edge.is_manifold for edge in bm.edges),
        "uv_layers": [uv.name for uv in target.data.uv_layers],
    }
    bm.free()
    if stats["faces"] < 18000:
        raise RuntimeError(f"Retopology too light: {stats}")
    if stats["triangles"] or stats["ngons"]:
        raise RuntimeError(f"Production cage is not all-quads: {stats}")
    if stats["boundary_edges"] or stats["nonmanifold_edges"]:
        raise RuntimeError(f"Production cage is not manifold: {stats}")
    if "UV0" not in stats["uv_layers"]:
        raise RuntimeError(f"UV0 missing: {stats}")
    print(f"V5_VALIDATION_OK={stats}")
    return stats


def render_previews(target):
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.data.scenes.get("SCENE_HighPolyReview")
    if scene is None:
        print("PREVIEW_WARNING=SCENE_HighPolyReview missing")
        return
    original = bpy.context.window.scene
    camera = bpy.data.objects.get("CAM_HighPolyReview")
    if camera is None:
        print("PREVIEW_WARNING=CAM_HighPolyReview missing")
        return

    # Ensure production collection is available in the review scene.
    coll = target.users_collection[0]
    if coll.name not in [child.name for child in scene.collection.children]:
        scene.collection.children.link(coll)
    target.hide_render = False
    target.hide_set(False)
    target.rotation_mode = "XYZ"
    target.rotation_euler = (0, 0, 0)
    target.location = (0, 0, 0)
    target.scale = (1, 1, 1)
    reference_collection = bpy.data.collections.get("REF_HighPoly_Generated")
    if reference_collection:
        for ref in reference_collection.objects:
            ref.hide_render = True

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    scene.camera = camera
    target_point = Vector((0, 0, 0.94))
    for label, position in {
        "Front": Vector((0, -5, 1)),
        "Back": Vector((0, 5, 1)),
        "Side": Vector((5, 0, 1)),
        "ThreeQuarter": Vector((3.6, -3.6, 1.05)),
    }.items():
        camera.location = position
        camera.rotation_euler = (target_point - position).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(PREVIEW_DIR / f"PlayerSuit_Production_v5_{label}.png")
        bpy.context.window.scene = scene
        bpy.ops.render.render(write_still=True)
    bpy.context.window.scene = original


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE_BLEND))
    source = bpy.data.objects.get("REF_PlayerSuit_MultiView_Rodin")
    if source is None:
        raise RuntimeError("Accepted multi-view generated source is missing")
    source.hide_set(False)
    source.hide_render = False
    target = build_retopology(source)
    validate(target)
    bake_maps(source, target)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND), check_existing=False)
    render_previews(target)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_BLEND), check_existing=False)
    print(f"V5_BLEND={OUTPUT_BLEND}")
    print(f"V5_TEXTURES={TEXTURE_DIR}")
    print(f"V5_PREVIEWS={PREVIEW_DIR}")


if __name__ == "__main__":
    main()
