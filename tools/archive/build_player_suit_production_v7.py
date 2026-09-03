"""Build the v7 authored-shell player suit from the validated v6 checkpoint.

V7 is intentionally non-destructive.  It keeps the proven V6 body, head, rig,
and LODs, then adds individually selectable hard-surface shells and garment
construction details.  The result is an art-direction asset, not an automatic
replacement for the runtime skeletal mesh.
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerSuit_Production_v6.blend"
OUTPUT = SUIT_DIR / "PlayerSuit_Production_v7.blend"
PREVIEWS = SUIT_DIR / "Production_v7_Previews"


def material(name, color, metallic=0.0, roughness=0.45):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def move_to(obj, collection):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)


def finish(obj, collection, mat, bevel=0.006):
    move_to(obj, collection)
    obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new("V7_Edge_Radius", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj["v7_authored_shell"] = True
    obj["export_class"] = "separate_rigid_part"
    return obj


def rounded_box(name, location, scale, collection, mat, bevel=0.008, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, collection, mat, bevel)


def capsule(name, location, scale, collection, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, collection, mat, 0.003)


def cylinder(name, location, radius, depth, collection, mat, rotation=(0, 0, 0), vertices=48):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                       location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    return finish(obj, collection, mat, min(radius * 0.12, 0.005))


def bone_parent(obj, armature, bone):
    world = obj.matrix_world.copy()
    obj.parent = armature
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = world
    obj["rig_attachment"] = bone


def mirror_part(obj, name):
    duplicate = obj.copy()
    duplicate.data = obj.data.copy()
    duplicate.name = name
    obj.users_collection[0].objects.link(duplicate)
    duplicate.location.x *= -1
    return duplicate


def create_shells(collection, armature):
    ivory = material("M_V7_CeramicArmor", (0.46, 0.49, 0.48), 0.12, 0.28)
    charcoal = material("M_V7_RubberizedFabric", (0.025, 0.032, 0.037), 0.02, 0.72)
    gunmetal = material("M_V7_Gunmetal", (0.055, 0.065, 0.071), 0.72, 0.24)
    orange = material("M_V7_SafetyOrange", (0.68, 0.16, 0.025), 0.25, 0.32)
    parts = []

    # Layered torso architecture: a floating sternum plate, two rib shells,
    # lower-abdomen lames, and visible dark expansion gaps.
    parts.append(rounded_box("SKV7_Armor_Sternum", (0, -0.176, 1.255), (.108, .026, .145), collection, ivory, .014))
    for side in (-1, 1):
        rib = capsule(f"SKV7_Armor_Rib_{'L' if side < 0 else 'R'}", (side * .132, -.154, 1.225),
                      (.104, .035, .175), collection, ivory)
        rib.rotation_euler.z = side * math.radians(7)
        parts.append(rib)
    for index, z in enumerate((1.092, 1.035, .979)):
        width = .115 - index * .008
        parts.append(rounded_box(f"SKV7_Armor_AbdominalLame_{index+1}", (0, -.164, z),
                                 (width, .021, .022), collection, gunmetal, .008))
    parts.append(rounded_box("SKV7_Armor_ChestStatusRail", (0, -.207, 1.345),
                             (.078, .012, .018), collection, orange, .004))

    # Limb shells remain discrete and bone-addressable for later rigid weighting.
    limb_specs = (
        ("Shoulder", "upperarm", (.202, -.015, 1.335), (.105, .075, .095), ivory),
        ("Forearm", "lowerarm", (.315, -.035, 1.125), (.075, .065, .145), gunmetal),
        ("Thigh", "thigh", (.128, -.018, .735), (.092, .055, .165), charcoal),
        ("Knee", "calf", (.126, -.125, .535), (.078, .038, .080), ivory),
        ("Shin", "calf", (.125, -.080, .365), (.072, .040, .130), ivory),
        ("Boot", "foot", (.125, -.085, .105), (.090, .145, .060), gunmetal),
    )
    for label, bone, loc, scale, mat in limb_specs:
        left = capsule(f"SKV7_Armor_{label}_L", loc, scale, collection, mat)
        right = mirror_part(left, f"SKV7_Armor_{label}_R")
        bone_parent(left, armature, f"{bone}_l")
        bone_parent(right, armature, f"{bone}_r")
        parts.extend((left, right))

    # Serviceable backpack with independent tanks, manifold, and protective cage.
    pack = rounded_box("SKV7_LifeSupport_MainPack", (0, .155, 1.205), (.165, .075, .225), collection, gunmetal, .018)
    bone_parent(pack, armature, "chest")
    parts.append(pack)
    for side in (-1, 1):
        tank = cylinder(f"SKV7_LifeSupport_Tank_{'L' if side < 0 else 'R'}",
                        (side * .105, .245, 1.205), .044, .315, collection, ivory)
        bone_parent(tank, armature, "chest")
        parts.append(tank)
    manifold = rounded_box("SKV7_LifeSupport_Manifold", (0, .247, 1.345), (.075, .024, .035), collection, orange, .006)
    bone_parent(manifold, armature, "chest")
    parts.append(manifold)

    # Repeated fasteners communicate assembly scale without texture dependence.
    for x in (-.082, .082):
        for z in (1.16, 1.34):
            bolt = cylinder(f"SKV7_Fastener_{x:+.3f}_{z:.3f}", (x, -.207, z), .008, .008,
                            collection, gunmetal, rotation=(math.pi / 2, 0, 0), vertices=24)
            bone_parent(bolt, armature, "chest")
            parts.append(bolt)
    for obj in parts:
        if obj.parent is None:
            bone_parent(obj, armature, "chest")
        obj["construction_standard"] = "replaceable sealed suit module"
    return parts


def create_seams(collection, armature):
    seam_mat = material("M_V7_SeamTape", (0.10, 0.115, 0.12), 0.0, 0.82)
    seams = []
    paths = {
        "Torso_Center": [(0, -.193, .92), (0, -.197, 1.10), (0, -.202, 1.40)],
        "Waist_L": [(-.17, -.06, .91), (-.19, -.04, .83), (-.16, -.07, .76)],
        "Waist_R": [(.17, -.06, .91), (.19, -.04, .83), (.16, -.07, .76)],
    }
    for label, points in paths.items():
        curve = bpy.data.curves.new(f"SKV7_Seam_{label}_Curve", "CURVE")
        curve.dimensions = "3D"
        curve.bevel_depth = .0032
        curve.bevel_resolution = 2
        spline = curve.splines.new("BEZIER")
        spline.bezier_points.add(len(points) - 1)
        for point, coordinate in zip(spline.bezier_points, points):
            point.co = coordinate
            point.handle_left_type = point.handle_right_type = "AUTO"
        obj = bpy.data.objects.new(f"SKV7_Seam_{label}", curve)
        collection.objects.link(obj)
        obj.data.materials.append(seam_mat)
        bone_parent(obj, armature, "spine_02")
        obj["v7_garment_detail"] = True
        seams.append(obj)
    return seams


def create_module_lods(shells):
    """Create non-rendering per-module reduction candidates for review.

    These remain unapplied so artists can protect silhouettes before accepting
    the reductions. They are intentionally excluded from the review FBX.
    """
    results = {}
    for level, ratio in ((1, .55), (2, .28)):
        collection = bpy.data.collections.new(f"SUIT_PRODUCTION_v7_LOD{level}_CANDIDATES")
        bpy.context.scene.collection.children.link(collection)
        candidates = []
        for source in shells:
            if source.type != "MESH" or source.name.startswith("SKV7_Fastener_"):
                continue
            candidate = source.copy()
            candidate.data = source.data.copy()
            candidate.name = f"{source.name}_LOD{level}"
            collection.objects.link(candidate)
            modifier = candidate.modifiers.new(f"LOD{level}_SilhouetteReview", "DECIMATE")
            modifier.ratio = ratio
            modifier.use_collapse_triangulate = True
            candidate.hide_render = True
            candidate.hide_set(True)
            candidate.hide_viewport = True
            candidate["lod_level"] = level
            candidate["target_triangle_ratio"] = ratio
            candidate["lod_status"] = "candidate_requires_silhouette_approval"
            candidates.append(candidate)
        results[level] = candidates
    return results


def render_reviews(scene, camera, visible):
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.camera = camera
    for obj in visible:
        obj.hide_render = False
    target = Vector((0, 0, .96))
    for label, position in {
        "Front": Vector((0, -5, 1.0)),
        "Back": Vector((0, 5, 1.0)),
        "Side": Vector((5, 0, 1.0)),
        "ThreeQuarter": Vector((3.5, -3.5, 1.08)),
    }.items():
        camera.location = position
        camera.rotation_euler = (target - position).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(PREVIEWS / f"PlayerSuit_Production_v7_{label}.png")
        bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    armature = bpy.data.objects["RIG_PlayerSuit_Production_v6"]
    suit = bpy.data.objects["SK_PlayerSuit_Production_v6_LOD0"]
    suit.name = "SK_PlayerSuit_Production_v7_BaseGarment"
    armature.name = "RIG_PlayerSuit_Production_v7"
    collection = bpy.data.collections.new("SUIT_PRODUCTION_v7_AUTHORED_SHELLS")
    bpy.context.scene.collection.children.link(collection)
    shells = create_shells(collection, armature)
    seams = create_seams(collection, armature)
    lods = create_module_lods(shells)
    suit["asset_status"] = "ART_DIRECTION_REVIEW_V7"
    suit["v7_scope"] = "separate hard-surface shells, garment seams, fasteners, material breakup"
    suit["runtime_replacement"] = False
    suit["v7_lod1_candidate_count"] = len(lods[1])
    suit["v7_lod2_candidate_count"] = len(lods[2])
    armature["rig_standard"] = "Ginnungagap humanoid v7 review"
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    original = bpy.context.window.scene
    bpy.context.window.scene = scene
    render_reviews(scene, camera, [suit, *shells, *seams])
    bpy.context.window.scene = original
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V7_VALIDATION", f"shells={len(shells)}", f"seams={len(seams)}",
          f"lod_candidates={len(lods[1]) + len(lods[2])}", f"output={OUTPUT}")


if __name__ == "__main__":
    main()
