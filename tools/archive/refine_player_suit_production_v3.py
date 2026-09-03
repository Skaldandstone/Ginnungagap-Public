"""Production refinement pass for the concept-driven player suit.

Creates a continuous anatomy-aware undersuit shell, a quad facial sculpt,
localized garment folds, and UV maps for every renderable mesh.  The v2 file
is opened read-only and the result is saved as PlayerSuit_Production_v3.blend.
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerSuit_Production_v2.blend"
OUTPUT = SUIT_DIR / "PlayerSuit_Production_v3.blend"
PREVIEWS = SUIT_DIR / "Production_v3_Previews"


def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.hide_set(False)
    obj.hide_viewport = False
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def get_or_create_collection(name, parent=None):
    coll = bpy.data.collections.get(name)
    if coll is None:
        coll = bpy.data.collections.new(name)
    if not coll.users:
        (parent or bpy.context.scene.collection).children.link(coll)
    return coll


def move_to_collection(obj, coll):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    coll.objects.link(obj)


def smooth(obj):
    if obj.type == "MESH":
        for poly in obj.data.polygons:
            poly.use_smooth = True


def ellipsoid(name, loc, scale, coll):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1.0, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move_to_collection(obj, coll)
    return obj


def limb_mass(name, start, end, radius, depth, coll):
    start = Vector(start)
    end = Vector(end)
    center = (start + end) * 0.5
    length = (end - start).length
    obj = ellipsoid(name, center, (radius, depth, length * 0.55), coll)
    obj.rotation_euler = (end - start).to_track_quat("Z", "Y").to_euler()
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    obj.select_set(False)
    return obj


def make_continuous_undersuit(coll, fabric):
    pieces = []
    # Torso and pelvic masses overlap deliberately before voxel union.
    pieces += [
        ellipsoid("SculptMass_Chest", (0, 0.006, 1.265), (0.282, 0.148, 0.282), coll),
        ellipsoid("SculptMass_Ribcage", (0, 0.000, 1.110), (0.248, 0.140, 0.240), coll),
        ellipsoid("SculptMass_Waist", (0, 0.010, 0.955), (0.192, 0.120, 0.180), coll),
        ellipsoid("SculptMass_Pelvis", (0, 0.018, 0.800), (0.215, 0.136, 0.182), coll),
    ]
    for side, sx in (("L", 1), ("R", -1)):
        pieces += [
            ellipsoid(f"SculptMass_{side}_Glute", (0.095 * sx, 0.042, 0.780), (0.097, 0.105, 0.125), coll),
            limb_mass(f"SculptMass_{side}_Thigh", (0.115 * sx, 0.018, 0.785), (0.145 * sx, 0.000, 0.460), 0.082, 0.081, coll),
            ellipsoid(f"SculptMass_{side}_Knee", (0.145 * sx, -0.005, 0.410), (0.069, 0.068, 0.086), coll),
            limb_mass(f"SculptMass_{side}_Calf", (0.145 * sx, 0.000, 0.390), (0.150 * sx, 0.012, 0.135), 0.064, 0.068, coll),
            ellipsoid(f"SculptMass_{side}_Shoulder", (0.275 * sx, 0.010, 1.365), (0.062, 0.066, 0.082), coll),
            limb_mass(f"SculptMass_{side}_UpperArm", (0.275 * sx, 0.008, 1.355), (0.330 * sx, -0.002, 1.035), 0.056, 0.060, coll),
            ellipsoid(f"SculptMass_{side}_Elbow", (0.330 * sx, -0.003, 1.020), (0.051, 0.052, 0.065), coll),
            limb_mass(f"SculptMass_{side}_Forearm", (0.330 * sx, -0.005, 1.000), (0.350 * sx, -0.018, 0.745), 0.048, 0.054, coll),
        ]

    bpy.ops.object.select_all(action="DESELECT")
    for obj in pieces:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = pieces[0]
    bpy.ops.object.join()
    body = pieces[0]
    body.name = "SUIT_Undersuit_SculptSource"
    body.data.remesh_voxel_size = 0.013
    select_only(body)
    bpy.ops.object.voxel_remesh()

    select_only(body)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")

    # Smooth the voxel union before producing the game-oriented quad cage.
    smooth_mod = body.modifiers.new("Sculpt_SurfaceRelax", "LAPLACIANSMOOTH")
    smooth_mod.iterations = 4
    smooth_mod.lambda_factor = 0.34
    bpy.context.view_layer.objects.active = body
    bpy.ops.object.modifier_apply(modifier=smooth_mod.name)
    smooth(body)

    # Blender's QuadriFlow makes a single animation-friendly all-quad shell.
    select_only(body)
    try:
        bpy.ops.object.quadriflow_remesh(
            use_mesh_symmetry=True,
            use_preserve_sharp=False,
            use_preserve_boundary=False,
            preserve_attributes=False,
            smooth_normals=True,
            mode="FACES",
            target_faces=18000,
            seed=7,
        )
        body["retopology_method"] = "QuadriFlow 18k symmetrical cage"
    except Exception as exc:
        # Preserve a valid remeshed shell if QuadriFlow is unavailable.
        body["retopology_method"] = f"voxel fallback: {exc}"

    body.name = "SUIT_Undersuit_Retopo"
    if body.data.materials:
        body.data.materials.clear()
    body.data.materials.append(fabric)
    add_tailored_folds(body)
    smart_uv(body, margin=0.012)
    body["uv_set"] = "UV0 garment production layout"
    body["fold_pass"] = "waist, elbow, knee, calf compression"
    body["production_role"] = "continuous deforming garment shell"

    subdiv = body.modifiers.new("Render_Subdivision", "SUBSURF")
    subdiv.subdivision_type = "CATMULL_CLARK"
    subdiv.levels = 1
    subdiv.render_levels = 2
    return body


def gaussian(value, center, width):
    return math.exp(-((value - center) / width) ** 2)


def add_tailored_folds(obj):
    """Displace the quad cage subtly around compression zones."""
    mesh = obj.data
    mesh.update()
    for vertex in mesh.vertices:
        co = vertex.co
        x, y, z = co.x, co.y, co.z
        displacement = 0.0

        # Horizontal compression folds at the waist and under the chest carrier.
        torso_mask = gaussian(abs(x), 0.0, 0.30) * gaussian(y, -0.035, 0.23)
        displacement += 0.0040 * math.sin((z - 0.92) * 88.0) * gaussian(z, 0.92, 0.070) * torso_mask
        displacement += 0.0028 * math.sin((z - 1.08) * 96.0) * gaussian(z, 1.07, 0.055) * torso_mask

        # Knee bellows: restrained folds, not stacked rings.
        leg_mask = gaussian(abs(x), 0.145, 0.085)
        displacement += 0.0048 * math.sin((z - 0.405) * 112.0) * gaussian(z, 0.405, 0.075) * leg_mask
        displacement += 0.0028 * math.sin((z - 0.245) * 102.0) * gaussian(z, 0.245, 0.060) * leg_mask

        # Elbow compression zones follow both hanging arms.
        arm_mask = gaussian(abs(x), 0.34, 0.080)
        displacement += 0.0042 * math.sin((z - 1.02) * 112.0) * gaussian(z, 1.02, 0.068) * arm_mask

        # Bias folds toward the visible front/side surfaces.
        front_weight = 0.55 + 0.45 * max(0.0, -vertex.normal.y)
        vertex.co += vertex.normal * displacement * front_weight
    mesh.update()


def sculpt_face(face_coll, skin, eye_white, iris, hair):
    # Remove the placeholder facial components but retain the pressure helmet.
    remove_prefixes = ("Head_Face", "Face_Nose", "Face_Eye", "Face_Brow", "Face_Mouth", "Hair_Side")
    for obj in list(bpy.data.objects):
        if obj.name.startswith(remove_prefixes):
            bpy.data.objects.remove(obj, do_unlink=True)

    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=48, location=(0, -0.050, 1.660))
    face = bpy.context.object
    face.name = "HEAD_Face_Sculpt_Retopo"
    face.scale = (0.098, 0.076, 0.133)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move_to_collection(face, face_coll)

    # Integrated facial plane, jaw, cheeks, sockets, nose and lips.
    for vertex in face.data.vertices:
        x, y, z = vertex.co.x, vertex.co.y, vertex.co.z
        world_z = z + face.location.z
        if z < 0.025:
            taper = 0.76 + 0.24 * max(0.0, min(1.0, (z + 0.138) / 0.163))
            vertex.co.x *= taper
        if z < -0.095:
            vertex.co.y += 0.008 * gaussian(z, -0.125, 0.032)

        # Only deform the forward-facing half (negative local Y).
        if y < 0.010:
            front = gaussian(y, -0.068, 0.055)
            nose = gaussian(x, 0.0, 0.020) * gaussian(world_z, 1.655, 0.038)
            bridge = gaussian(x, 0.0, 0.017) * gaussian(world_z, 1.685, 0.055)
            sockets = (
                gaussian(x, -0.036, 0.022) + gaussian(x, 0.036, 0.022)
            ) * gaussian(world_z, 1.695, 0.022)
            cheeks = (
                gaussian(x, -0.052, 0.032) + gaussian(x, 0.052, 0.032)
            ) * gaussian(world_z, 1.657, 0.040)
            lips = gaussian(x, 0.0, 0.038) * gaussian(world_z, 1.610, 0.013)
            chin = gaussian(x, 0.0, 0.050) * gaussian(world_z, 1.574, 0.025)
            vertex.co.y -= front * (0.032 * nose + 0.008 * bridge + 0.005 * cheeks + 0.004 * lips + 0.003 * chin)
            vertex.co.y += front * 0.0055 * sockets
    face.data.update()
    smooth(face)
    face.data.materials.append(skin)
    face["topology"] = "UV quad facial cage with integrated forms"
    face["uv_set"] = "UV0 facial layout"

    # Preserve the sphere's clean UVs and add a non-destructive render subdivision.
    if not face.data.uv_layers:
        smart_uv(face, margin=0.018)
    subdiv = face.modifiers.new("Face_Render_Subdivision", "SUBSURF")
    subdiv.levels = 2
    subdiv.render_levels = 2

    # Eyes sit in the sculpted sockets; scale is deliberately human, not doll-like.
    for side, sx in (("L", 1), ("R", -1)):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, location=(0.035 * sx, -0.126, 1.695))
        white = bpy.context.object
        white.name = f"HEAD_EyeWhite_{side}"
        white.scale = (0.0155, 0.0060, 0.0080)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        smooth(white)
        white.data.materials.append(eye_white)
        move_to_collection(white, face_coll)

        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, location=(0.035 * sx, -0.132, 1.695))
        pupil = bpy.context.object
        pupil.name = f"HEAD_Iris_{side}"
        pupil.scale = (0.0055, 0.0026, 0.0055)
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        smooth(pupil)
        pupil.data.materials.append(iris)
        move_to_collection(pupil, face_coll)

    # Eyebrows, eyelids and mouth are curves hugging the facial surface.
    curve_material = hair
    add_curve(face_coll, "HEAD_Brow_L", [(0.017, -0.129, 1.721), (0.035, -0.134, 1.726), (0.053, -0.129, 1.722)], 0.0017, curve_material)
    add_curve(face_coll, "HEAD_Brow_R", [(-0.053, -0.129, 1.722), (-0.035, -0.134, 1.726), (-0.017, -0.129, 1.721)], 0.0017, curve_material)
    add_curve(face_coll, "HEAD_UpperLid_L", [(0.020, -0.134, 1.697), (0.035, -0.138, 1.701), (0.050, -0.134, 1.697)], 0.0012, hair)
    add_curve(face_coll, "HEAD_UpperLid_R", [(-0.050, -0.134, 1.697), (-0.035, -0.138, 1.701), (-0.020, -0.134, 1.697)], 0.0012, hair)
    add_curve(face_coll, "HEAD_Lips", [(-0.030, -0.139, 1.610), (0, -0.143, 1.606), (0.030, -0.139, 1.610)], 0.0015, iris)

    # Low-profile side locks and a thin curve establish the hairline.
    add_curve(face_coll, "HEAD_Hairline", [(-0.072, -0.126, 1.760), (-0.040, -0.134, 1.780), (0, -0.137, 1.786), (0.040, -0.134, 1.780), (0.072, -0.126, 1.760)], 0.0032, hair)
    for side, sx in (("L", 1), ("R", -1)):
        side_lock = ellipsoid(f"HEAD_HairLock_{side}", (0.091 * sx, -0.067, 1.675), (0.013, 0.017, 0.078), face_coll)
        side_lock.data.materials.append(hair)
        smooth(side_lock)
    return face


def add_curve(coll, name, points, radius, material):
    curve = bpy.data.curves.new(name + "_Curve", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 2
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, co in zip(spline.bezier_points, points):
        point.co = co
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    coll.objects.link(obj)
    obj.data.materials.append(material)
    return obj


def smart_uv(obj, margin=0.015):
    if obj.type != "MESH" or not obj.data.polygons:
        return
    select_only(obj)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(
        angle_limit=math.radians(66),
        margin_method="SCALED",
        island_margin=margin,
        area_weight=0.2,
        correct_aspect=True,
        scale_to_bounds=True,
    )
    bpy.ops.object.mode_set(mode="OBJECT")
    if obj.data.uv_layers:
        obj.data.uv_layers.active.name = "UV0"


def uv_all_render_meshes():
    failures = []
    for obj in list(bpy.context.scene.objects):
        if obj.type != "MESH" or not obj.data.polygons or obj.name == "StudioFloor":
            continue
        if not obj.data.uv_layers:
            try:
                smart_uv(obj)
            except Exception as exc:
                failures.append((obj.name, str(exc)))
        obj["uv_validation"] = "UV0 present" if obj.data.uv_layers else "missing"
    return failures


def hide_legacy_garment():
    for obj in list(bpy.data.objects):
        if obj.name.startswith("GSU_"):
            obj.hide_render = True
            obj.hide_set(True)
            obj["legacy_v2_geometry"] = True


def configure_skin_material():
    skin = bpy.data.materials.get("M_Skin")
    if skin and skin.use_nodes:
        bsdf = skin.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            if bsdf.inputs.get("Base Color"):
                bsdf.inputs["Base Color"].default_value = (0.37, 0.16, 0.095, 1)
            if bsdf.inputs.get("Roughness"):
                bsdf.inputs["Roughness"].default_value = 0.48
            if bsdf.inputs.get("Subsurface Weight"):
                bsdf.inputs["Subsurface Weight"].default_value = 0.07
    return skin


def render_turnaround():
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    camera = bpy.data.objects.get("CAM_ConceptReview")
    if camera is None:
        return
    scene.camera = camera
    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    target = Vector((0, 0, 0.94))
    views = {
        "Front": (Vector((0, -6.0, 1.05)), 2.02),
        "Side": (Vector((6.0, 0, 1.05)), 2.02),
        "Back": (Vector((0, 6.0, 1.05)), 2.02),
        "ThreeQuarter": (Vector((4.3, -4.3, 1.10)), 2.04),
    }
    for label, (position, scale) in views.items():
        camera.location = position
        camera.data.ortho_scale = scale
        camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(PREVIEWS / f"PlayerSuit_Production_v3_{label}.png")
        bpy.ops.render.render(write_still=True)


def validate(body, face, uv_failures):
    body_faces = len(body.data.polygons)
    body_ngons = sum(len(poly.vertices) > 4 for poly in body.data.polygons)
    body_quads = sum(len(poly.vertices) == 4 for poly in body.data.polygons)
    face_ngons = sum(len(poly.vertices) > 4 for poly in face.data.polygons)
    mesh_objects = [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and obj.name != "StudioFloor" and not obj.hide_render]
    missing_uv = [obj.name for obj in mesh_objects if not obj.data.uv_layers]
    if body_faces < 5000:
        raise RuntimeError(f"Retopology result too light: {body_faces} faces")
    if body_ngons:
        raise RuntimeError(f"Undersuit retopo contains {body_ngons} ngons")
    if face_ngons:
        raise RuntimeError(f"Face cage contains {face_ngons} ngons")
    if missing_uv:
        raise RuntimeError(f"Renderable meshes missing UV0: {missing_uv}")
    if uv_failures:
        print(f"UV_WARNINGS={uv_failures}")
    print(
        f"PRODUCTION_VALIDATION_OK body_faces={body_faces} body_quads={body_quads} "
        f"face_faces={len(face.data.polygons)} uv_meshes={len(mesh_objects)}"
    )


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    hide_legacy_garment()
    hero = bpy.data.collections.get("SUIT_HERO_NEUTRAL")
    garment = get_or_create_collection("01_Garment_Production", hero)
    face_coll = bpy.data.collections.get("03_Helmet") or get_or_create_collection("03_Helmet", hero)
    fabric = bpy.data.materials.get("M_Undersuit_Charcoal_Fabric")
    skin = configure_skin_material()
    eye_white = bpy.data.materials.get("M_Eye_White")
    iris = bpy.data.materials.get("M_Eye_Dark")
    hair = bpy.data.materials.get("M_Hair")
    if not all((fabric, skin, eye_white, iris, hair)):
        raise RuntimeError("Required v2 materials are missing")

    body = make_continuous_undersuit(garment, fabric)
    face = sculpt_face(face_coll, skin, eye_white, iris, hair)
    uv_failures = uv_all_render_meshes()

    hero["asset_status"] = "PRODUCTION_GEOMETRY_REVIEW"
    hero["anatomy_pass"] = "continuous anthropometric garment shell"
    hero["face_pass"] = "integrated quad sculpt with sockets/nose/cheeks/lips"
    hero["retopology_pass"] = body.get("retopology_method", "unknown")
    hero["uv_pass"] = "UV0 validated on all renderable meshes"
    hero["unreal_export_allowed"] = False
    hero["next_gate"] = "deformation test and art-director visual approval"

    validate(body, face, uv_failures)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    render_turnaround()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print(f"PRODUCTION_V3_SAVED={OUTPUT}")
    print(f"PRODUCTION_V3_PREVIEWS={PREVIEWS}")


if __name__ == "__main__":
    main()
