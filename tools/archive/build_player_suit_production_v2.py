"""Build a clean, concept-driven player suit hero model in Blender.

This intentionally does not reuse the accumulated procedural blockout geometry.
The goal of this pass is a readable human silhouette and the concept's large
forms.  Rigging, class variants, and Unreal export remain downstream gates.
"""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
BLEND_PATH = OUT_DIR / "PlayerSuit_Production_v2.blend"
PREVIEW_DIR = OUT_DIR / "Production_v2_Previews"


def reset_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def collection(name: str) -> bpy.types.Collection:
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def move_to_collection(obj: bpy.types.Object, coll: bpy.types.Collection):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    coll.objects.link(obj)


def set_input(node, name, value):
    socket = node.inputs.get(name)
    if socket is not None:
        socket.default_value = value


def material_principled(name, color, roughness=0.5, metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    set_input(bsdf, "Base Color", color)
    set_input(bsdf, "Roughness", roughness)
    set_input(bsdf, "Metallic", metallic)
    return mat


def material_fabric():
    mat = bpy.data.materials.new("M_Undersuit_Charcoal_Fabric")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    set_input(bsdf, "Roughness", 0.78)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 115.0
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.7
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.016, 0.021, 0.026, 1)
    ramp.color_ramp.elements[1].color = (0.038, 0.044, 0.050, 1)
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.16
    bump.inputs["Distance"].default_value = 0.025
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def material_armor():
    mat = bpy.data.materials.new("M_Armor_Aged_Ivory")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes.get("Principled BSDF")
    set_input(bsdf, "Roughness", 0.34)
    set_input(bsdf, "Metallic", 0.06)
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 7.0
    noise.inputs["Detail"].default_value = 4.0
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.27, 0.25, 0.21, 1)
    ramp.color_ramp.elements[0].position = 0.15
    ramp.color_ramp.elements[1].color = (0.72, 0.68, 0.57, 1)
    ramp.color_ramp.elements[1].position = 0.78
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08
    bump.inputs["Distance"].default_value = 0.035
    nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def material_visor():
    mat = bpy.data.materials.new("M_Visor_Clear")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    output = nt.nodes.new("ShaderNodeOutputMaterial")
    transparent = nt.nodes.new("ShaderNodeBsdfTransparent")
    transparent.inputs["Color"].default_value = (0.70, 0.82, 0.88, 1)
    glossy = nt.nodes.new("ShaderNodeBsdfGlossy")
    glossy.inputs["Color"].default_value = (0.10, 0.16, 0.19, 1)
    glossy.inputs["Roughness"].default_value = 0.16
    mix = nt.nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value = 0.025
    nt.links.new(transparent.outputs[0], mix.inputs[1])
    nt.links.new(glossy.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], output.inputs[0])
    mat.surface_render_method = "DITHERED"
    return mat


def assign(obj, mat):
    if obj.data and hasattr(obj.data, "materials"):
        obj.data.materials.append(mat)


def smooth(obj):
    if obj.type == "MESH":
        for poly in obj.data.polygons:
            poly.use_smooth = True


def add_bevel(obj, width=0.01, segments=3):
    mod = obj.modifiers.new("Edge_Soften", "BEVEL")
    mod.width = width
    mod.segments = segments


def uv_sphere(name, loc, scale, mat, coll, segments=40, rings=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    smooth(obj)
    assign(obj, mat)
    move_to_collection(obj, coll)
    return obj


def rounded_box(name, loc, scale, mat, coll, bevel=0.018, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    add_bevel(obj, bevel, 4)
    assign(obj, mat)
    move_to_collection(obj, coll)
    return obj


def panel_prism(name, outline, center_y, half_depth, mat, coll, bevel=0.014):
    """Extrude a front-view outline into a softly beveled hard-shell panel."""
    count = len(outline)
    front_y = center_y - half_depth
    back_y = center_y + half_depth
    verts = [(x, front_y, z) for x, z in outline] + [(x, back_y, z) for x, z in outline]
    faces = [tuple(range(count)), tuple(reversed(range(count, count * 2)))]
    for i in range(count):
        n = (i + 1) % count
        faces.append((i, n, count + n, count + i))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    add_bevel(obj, bevel, 4)
    assign(obj, mat)
    return obj


def loft(name, rings, mat, coll, sides=32, cap=True):
    """Closed elliptical cross-section surface.

    Rings contain (z, half_width, half_depth, x_center, y_center).
    Front of the character is negative Y.
    """
    verts = []
    for z, rx, ry, cx, cy in rings:
        for i in range(sides):
            a = 2.0 * math.pi * i / sides
            verts.append((cx + rx * math.cos(a), cy + ry * math.sin(a), z))
    faces = []
    for r in range(len(rings) - 1):
        for i in range(sides):
            n = (i + 1) % sides
            a = r * sides + i
            b = r * sides + n
            c = (r + 1) * sides + n
            d = (r + 1) * sides + i
            faces.append((a, b, c, d))
    if cap:
        faces.append(tuple(reversed(range(sides))))
        start = (len(rings) - 1) * sides
        faces.append(tuple(start + i for i in range(sides)))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    smooth(obj)
    assign(obj, mat)
    return obj


def capsule_between(name, start, end, radius_a, radius_b, mat, coll, sides=24):
    """Tapered, rounded limb segment aligned between arbitrary endpoints."""
    a = Vector(start)
    b = Vector(end)
    axis = b - a
    length = axis.length
    direction = axis.normalized()
    helper = Vector((0, 0, 1)) if abs(direction.z) < 0.92 else Vector((0, 1, 0))
    u = direction.cross(helper).normalized()
    v = direction.cross(u).normalized()
    ring_defs = [
        (0.0, radius_a * 0.72),
        (0.04 * length, radius_a),
        (0.92 * length, radius_b),
        (length, radius_b * 0.72),
    ]
    verts = []
    for along, radius in ring_defs:
        center = a + direction * along
        for i in range(sides):
            ang = 2 * math.pi * i / sides
            p = center + radius * (u * math.cos(ang) + v * math.sin(ang))
            verts.append(tuple(p))
    faces = []
    for r in range(len(ring_defs) - 1):
        for i in range(sides):
            n = (i + 1) % sides
            faces.append((r * sides + i, r * sides + n, (r + 1) * sides + n, (r + 1) * sides + i))
    faces.append(tuple(reversed(range(sides))))
    start_i = (len(ring_defs) - 1) * sides
    faces.append(tuple(start_i + i for i in range(sides)))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    coll.objects.link(obj)
    smooth(obj)
    assign(obj, mat)
    return obj


def curve_tube(name, points, radius, mat, coll, cyclic=False):
    curve = bpy.data.curves.new(name + "_Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 2
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for bp, co in zip(spline.bezier_points, points):
        bp.co = co
        bp.handle_left_type = "AUTO"
        bp.handle_right_type = "AUTO"
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve)
    coll.objects.link(obj)
    assign(obj, mat)
    return obj


def torus(name, loc, major_radius, minor_radius, mat, coll, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major_radius,
        minor_radius=minor_radius,
        major_segments=48,
        minor_segments=10,
        location=loc,
        rotation=rotation,
    )
    obj = bpy.context.object
    obj.name = name
    smooth(obj)
    assign(obj, mat)
    move_to_collection(obj, coll)
    return obj


def build_suit():
    reset_scene()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    suit = collection("SUIT_HERO_NEUTRAL")
    garment = collection("01_Garment")
    armor_coll = collection("02_Armor")
    helmet = collection("03_Helmet")
    equipment = collection("04_Equipment")
    detail = collection("05_Detail")
    presentation = collection("90_Presentation")
    for child in (garment, armor_coll, helmet, equipment, detail):
        bpy.context.scene.collection.children.unlink(child)
        suit.children.link(child)

    fabric = material_fabric()
    armor = material_armor()
    dark_rubber = material_principled("M_Rubber_Black", (0.012, 0.015, 0.018, 1), 0.62, 0.02)
    metal = material_principled("M_Metal_Gunmetal", (0.07, 0.075, 0.078, 1), 0.26, 0.78)
    accent = material_principled("M_Accent_Ochre", (0.52, 0.21, 0.035, 1), 0.36, 0.25)
    screen = material_principled("M_Display_Amber", (0.025, 0.060, 0.065, 1), 0.30, 0.12)
    screen_bsdf = screen.node_tree.nodes.get("Principled BSDF")
    set_input(screen_bsdf, "Emission Color", (0.33, 0.10, 0.012, 1))
    set_input(screen_bsdf, "Emission Strength", 0.85)
    skin = material_principled("M_Skin", (0.48, 0.23, 0.14, 1), 0.52, 0.0)
    hair = material_principled("M_Hair", (0.045, 0.018, 0.009, 1), 0.66, 0.0)
    eye = material_principled("M_Eye_Dark", (0.018, 0.010, 0.007, 1), 0.25, 0.0)
    eye_white = material_principled("M_Eye_White", (0.52, 0.48, 0.42, 1), 0.30, 0.0)
    visor = material_visor()

    # Continuous garment masses: human proportions first, armor second.
    loft("GSU_Torso", [
        (0.88, 0.225, 0.145, 0, 0.006),
        (0.98, 0.285, 0.165, 0, 0.003),
        (1.13, 0.295, 0.158, 0, 0.000),
        (1.29, 0.315, 0.158, 0, 0.000),
        (1.40, 0.335, 0.164, 0, 0.008),
        (1.47, 0.245, 0.135, 0, 0.018),
    ], fabric, garment)
    loft("GSU_Pelvis", [
        (0.69, 0.225, 0.145, 0, 0.018),
        (0.78, 0.275, 0.175, 0, 0.018),
        (0.90, 0.255, 0.160, 0, 0.010),
        (0.97, 0.235, 0.150, 0, 0.006),
    ], fabric, garment)

    # Legs have long, soft garment shapes instead of stacked hard cylinders.
    for side, sx in (("L", 1), ("R", -1)):
        hip_x = 0.145 * sx
        capsule_between(f"GSU_{side}_Thigh", (hip_x, 0.012, 0.82), (0.145 * sx, 0.005, 0.43), 0.108, 0.087, fabric, garment)
        uv_sphere(f"GSU_{side}_Knee_Flex", (0.145 * sx, -0.006, 0.405), (0.092, 0.090, 0.108), fabric, garment, 32, 20)
        capsule_between(f"GSU_{side}_Calf", (0.145 * sx, 0.005, 0.39), (0.15 * sx, 0.018, 0.115), 0.088, 0.069, fabric, garment)

        # Arms hang naturally with a slight outward shoulder line.
        shoulder = (0.305 * sx, 0.008, 1.36)
        elbow = (0.345 * sx, -0.002, 1.02)
        wrist = (0.350 * sx, -0.018, 0.735)
        capsule_between(f"GSU_{side}_UpperArm", shoulder, elbow, 0.086, 0.069, fabric, garment)
        uv_sphere(f"GSU_{side}_Elbow_Flex", elbow, (0.072, 0.070, 0.086), fabric, garment, 32, 18)
        capsule_between(f"GSU_{side}_Forearm", elbow, wrist, 0.073, 0.057, fabric, garment)
        capsule_between(f"Glove_{side}_Palm", wrist, (0.354 * sx, -0.027, 0.605), 0.058, 0.052, dark_rubber, garment)
        # Readable glove silhouette; fingers remain grouped at gameplay distance.
        capsule_between(f"Glove_{side}_Fingers", (0.354 * sx, -0.032, 0.62), (0.354 * sx, -0.045, 0.535), 0.049, 0.037, dark_rubber, garment, 20)
        capsule_between(f"Glove_{side}_Thumb", (0.316 * sx, -0.052, 0.62), (0.312 * sx, -0.074, 0.57), 0.021, 0.016, dark_rubber, garment, 16)

    # Neck seal and concept-identifying helmet.
    loft("GSU_Neck", [(1.42, 0.112, 0.10, 0, 0.015), (1.54, 0.105, 0.095, 0, 0.018)], fabric, garment, 28)
    torus("Helmet_LowerPressureRing", (0, 0.008, 1.485), 0.205, 0.036, dark_rubber, helmet)
    torus("Helmet_UpperIvoryRing", (0, 0.006, 1.525), 0.207, 0.025, armor, helmet)
    torus("Helmet_LockBand", (0, 0.005, 1.555), 0.207, 0.014, metal, helmet)

    # Face is intentionally simple but proportioned and readable through the visor.
    uv_sphere("Head_HairMass", (0, 0.018, 1.674), (0.128, 0.108, 0.155), hair, helmet, 40, 24)
    uv_sphere("Head_Face", (0, -0.052, 1.658), (0.104, 0.079, 0.137), skin, helmet, 40, 24)
    uv_sphere("Face_Nose", (0, -0.134, 1.650), (0.010, 0.012, 0.020), skin, helmet, 24, 14)
    for x in (-0.036, 0.036):
        uv_sphere("Face_EyeWhite", (x, -0.130, 1.695), (0.016, 0.005, 0.008), eye_white, helmet, 20, 12)
        uv_sphere("Face_Eye", (x, -0.136, 1.695), (0.006, 0.003, 0.005), eye, helmet, 16, 10)
        curve_tube("Face_Brow", [(x - 0.020, -0.151, 1.720), (x, -0.154, 1.725), (x + 0.020, -0.151, 1.720)], 0.0023, hair, helmet)
    curve_tube("Face_Mouth", [(-0.032, -0.152, 1.610), (0, -0.157, 1.605), (0.032, -0.152, 1.610)], 0.0021, eye, helmet)
    # Hair side shapes keep the face framed rather than helmet-bald.
    for x in (-0.097, 0.097):
        uv_sphere("Hair_Side", (x, -0.060, 1.674), (0.016, 0.020, 0.090), hair, helmet, 24, 14)

    uv_sphere("Helmet_ClearDome", (0, -0.006, 1.675), (0.205, 0.198, 0.218), visor, helmet, 64, 36)
    rounded_box("Helmet_LeftTemple", (0.196, 0.025, 1.670), (0.020, 0.070, 0.085), armor, helmet, 0.013)
    rounded_box("Helmet_RightTemple", (-0.196, 0.025, 1.670), (0.020, 0.070, 0.085), armor, helmet, 0.013)
    curve_tube("Helmet_CrownRail", [(-0.07, 0.175, 1.80), (0, 0.195, 1.835), (0.07, 0.175, 1.80)], 0.014, armor, helmet)

    panel_prism("Armor_LeftClavicle", [(-0.225, 1.475), (-0.028, 1.475), (-0.065, 1.410), (-0.205, 1.405)], -0.115, 0.022, armor, armor_coll, 0.012)
    panel_prism("Armor_RightClavicle", [(0.028, 1.475), (0.225, 1.475), (0.205, 1.405), (0.065, 1.410)], -0.115, 0.022, armor, armor_coll, 0.012)

    # Large hard-shell forms closely follow the concept and stay visually sparse.
    panel_prism("Armor_ChestCarrier", [
        (-0.180, 1.435), (0.180, 1.435), (0.205, 1.375),
        (0.170, 1.145), (0.105, 1.105), (-0.105, 1.105),
        (-0.170, 1.145), (-0.205, 1.375),
    ], -0.174, 0.038, armor, armor_coll, 0.024)
    rounded_box("Armor_ChestInset", (0, -0.219, 1.310), (0.110, 0.014, 0.082), metal, armor_coll, 0.013)
    rounded_box("Armor_ChestDisplay", (0, -0.238, 1.315), (0.072, 0.009, 0.043), screen, armor_coll, 0.008)
    for x in (-0.168, 0.168):
        rounded_box("Armor_ChestLatch", (x, -0.218, 1.31), (0.019, 0.011, 0.032), accent, armor_coll, 0.006)

    # Shoulder fabric remains exposed, matching the reference.
    for side, sx in (("L", 1), ("R", -1)):
        rounded_box(f"Armor_{side}_Forearm", (0.354 * sx, -0.078, 0.875), (0.058, 0.026, 0.132), armor, armor_coll, 0.021, rotation=(0, 0, -0.04 * sx))
        rounded_box(f"Armor_{side}_ForearmDisplay", (0.354 * sx, -0.110, 0.885), (0.033, 0.008, 0.074), screen, armor_coll, 0.008)
        rounded_box(f"Armor_{side}_Knee", (0.145 * sx, -0.090, 0.405), (0.073, 0.028, 0.092), armor, armor_coll, 0.025)
        rounded_box(f"Boot_{side}_Cuff", (0.150 * sx, 0.004, 0.135), (0.082, 0.082, 0.096), armor, armor_coll, 0.031)
        rounded_box(f"Boot_{side}_Shell", (0.150 * sx, -0.040, 0.066), (0.097, 0.145, 0.064), armor, armor_coll, 0.034)
        rounded_box(f"Boot_{side}_Sole", (0.150 * sx, -0.045, 0.015), (0.104, 0.154, 0.024), dark_rubber, armor_coll, 0.017)
        rounded_box(f"Boot_{side}_ToeGuard", (0.150 * sx, -0.152, 0.075), (0.089, 0.045, 0.040), metal, armor_coll, 0.021)

    # Functional belt and restrained harness geometry.
    waist_belt = torus("Harness_WaistBelt", (0, 0.01, 0.895), 0.268, 0.025, dark_rubber, equipment)
    waist_belt.scale = (1.0, 0.67, 0.48)
    bpy.context.view_layer.objects.active = waist_belt
    waist_belt.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    waist_belt.select_set(False)
    rounded_box("Harness_Buckle", (0, -0.176, 0.895), (0.055, 0.020, 0.040), metal, equipment, 0.008)
    for sx in (-1, 1):
        rounded_box("Harness_HipPouch", (0.260 * sx, -0.010, 0.845), (0.045, 0.085, 0.065), dark_rubber, equipment, 0.015)
        curve_tube("Harness_ShoulderStrap", [(0.19 * sx, -0.178, 1.43), (0.16 * sx, -0.205, 1.18), (0.21 * sx, -0.170, 0.91)], 0.014, dark_rubber, equipment)
        curve_tube("Harness_ThighStrap", [(0.25 * sx, -0.13, 0.84), (0.19 * sx, -0.16, 0.70), (0.14 * sx, -0.14, 0.62)], 0.011, dark_rubber, equipment)

    # Compact life-support pack; its depth and width mirror the side/back concepts.
    rounded_box("LSS_Backpack_Main", (0, 0.214, 1.245), (0.220, 0.095, 0.275), armor, equipment, 0.032)
    rounded_box("LSS_Backpack_Inset", (0, 0.315, 1.270), (0.155, 0.018, 0.145), metal, equipment, 0.014)
    rounded_box("LSS_Backpack_LowerRail", (0, 0.325, 1.055), (0.165, 0.025, 0.025), dark_rubber, equipment, 0.010)
    for sx in (-1, 1):
        curve_tube(f"LSS_Hose_{sx}", [(0.15 * sx, 0.23, 1.42), (0.23 * sx, 0.12, 1.48), (0.20 * sx, -0.005, 1.53)], 0.020, dark_rubber, equipment)
        torus(f"LSS_HoseClamp_{sx}", (0.202 * sx, 0.006, 1.525), 0.026, 0.006, metal, equipment, rotation=(math.pi / 2, 0, 0))

    # Folded universal tool-arm interface, flush to the pack when not in use.
    rounded_box("ToolArm_Rail", (-0.245, 0.235, 1.255), (0.025, 0.050, 0.190), metal, equipment, 0.010)
    uv_sphere("ToolArm_ShoulderJoint", (-0.275, 0.208, 1.390), (0.038, 0.038, 0.038), accent, equipment, 24, 14)
    capsule_between("ToolArm_Upper_Stowed", (-0.278, 0.205, 1.375), (-0.302, 0.195, 1.245), 0.022, 0.019, armor, equipment, 16)
    uv_sphere("ToolArm_ElbowJoint", (-0.303, 0.194, 1.235), (0.030, 0.030, 0.030), accent, equipment, 20, 12)
    capsule_between("ToolArm_Lower_Stowed", (-0.303, 0.194, 1.222), (-0.280, 0.190, 1.105), 0.019, 0.016, armor, equipment, 16)
    rounded_box("ToolArm_EndEffectorSocket", (-0.278, 0.184, 1.080), (0.030, 0.025, 0.022), metal, equipment, 0.007)

    # Garment seams and flex zones create tailoring without turning into greebles.
    curve_tube("Seam_CenterFront", [(0, -0.169, 1.08), (0, -0.176, 0.97), (0, -0.166, 0.75)], 0.0032, metal, detail)
    for sx in (-1, 1):
        curve_tube("Seam_TorsoSide", [(0.26 * sx, -0.125, 1.34), (0.27 * sx, -0.145, 1.16), (0.22 * sx, -0.132, 0.98)], 0.0030, metal, detail)
        for z in (0.25, 0.31):
            curve_tube("Calf_FlexSeam", [(0.075 * sx, -0.080, z), (0.155 * sx, -0.104, z - 0.01), (0.235 * sx, -0.078, z)], 0.0030, metal, detail)
        for z in (1.10, 1.17):
            curve_tube("Elbow_FlexSeam", [(0.35 * sx, -0.062, z), (0.41 * sx, -0.085, z - 0.015), (0.47 * sx, -0.055, z)], 0.0028, metal, detail)

    # Naming and production metadata make the visual gate explicit.
    suit["asset_status"] = "VISUAL_HERO_GATE"
    suit["concept_reference"] = "Player_Concept_Likeness_v2.png"
    suit["unreal_export_allowed"] = False
    suit["next_gate"] = "silhouette approval, then topology/rig integration"

    # Neutral studio presentation.
    floor_mat = material_principled("M_StudioFloor", (0.115, 0.115, 0.110, 1), 0.72, 0.0)
    rounded_box("StudioFloor", (0, 0, -0.035), (2.8, 2.8, 0.035), floor_mat, presentation, 0.02)

    return presentation


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_render(presentation):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.world.color = (0.055, 0.055, 0.052)

    bpy.ops.object.camera_add(location=(0, -6, 1.02))
    camera = bpy.context.object
    camera.name = "CAM_ConceptReview"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.02
    camera.data.lens = 58
    scene.camera = camera
    move_to_collection(camera, presentation)

    def area(name, loc, energy, size, color):
        bpy.ops.object.light_add(type="AREA", location=loc)
        light = bpy.context.object
        light.name = name
        light.data.energy = energy
        light.data.shape = "DISK"
        light.data.size = size
        light.data.color = color
        look_at(light, (0, 0, 1.02))
        move_to_collection(light, presentation)

    area("Key_Softbox", (-3.0, -4.0, 4.2), 850, 3.0, (1.0, 0.88, 0.76))
    area("Fill_Softbox", (3.2, -2.0, 2.6), 620, 2.6, (0.72, 0.84, 1.0))
    area("Rim_Softbox", (0.0, 3.0, 3.7), 1000, 2.2, (0.85, 0.92, 1.0))
    return camera


def render_turnaround(camera):
    scene = bpy.context.scene
    target = (0, 0, 0.94)
    views = {
        "Front": ((0, -6.0, 1.05), 2.02),
        "Side": ((6.0, 0, 1.05), 2.02),
        "Back": ((0, 6.0, 1.05), 2.02),
        "ThreeQuarter": ((4.3, -4.3, 1.10), 2.04),
    }
    for label, (location, scale) in views.items():
        camera.location = location
        camera.data.ortho_scale = scale
        look_at(camera, target)
        scene.render.filepath = str(PREVIEW_DIR / f"PlayerSuit_Production_v2_{label}.png")
        bpy.ops.render.render(write_still=True)


def validate():
    scene_objects = list(bpy.context.scene.objects)
    names = {obj.name for obj in scene_objects}
    required = {
        "GSU_Torso",
        "GSU_Pelvis",
        "Helmet_ClearDome",
        "Armor_ChestCarrier",
        "LSS_Backpack_Main",
        "ToolArm_Rail",
    }
    missing = sorted(required - names)
    if missing:
        raise RuntimeError(f"Missing required hero forms: {missing}")
    mesh_count = sum(obj.type == "MESH" for obj in scene_objects)
    if mesh_count < 45:
        raise RuntimeError(f"Unexpectedly incomplete suit: {mesh_count} meshes")
    print(f"VALIDATION_OK meshes={mesh_count} objects={len(scene_objects)}")


def main():
    presentation = build_suit()
    camera = setup_render(presentation)
    validate()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)
    render_turnaround(camera)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)
    print(f"BLEND_SAVED={BLEND_PATH}")
    print(f"PREVIEWS_SAVED={PREVIEW_DIR}")


if __name__ == "__main__":
    main()
