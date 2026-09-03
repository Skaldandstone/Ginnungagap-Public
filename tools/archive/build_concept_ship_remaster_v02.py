"""Build concept-faithful hard-surface fleet ships without scan reconstruction.

This is a clean procedural authoring pass.  It uses the dimensions and signature
features printed on the three exterior concept boards, creates coherent mounted
geometry, exports an Unreal-ready GLB, and renders validation views.
"""

from __future__ import annotations

import json
import math
import os
import random
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


PROJECT = Path(__file__).resolve().parents[1]
VERSION = int(os.environ.get("GINNUNGAGAP_SHIP_REMASTER_VERSION", "2"))
TAG = f"V{VERSION:02d}"
OUT_ROOT = PROJECT / f"Art/Ships/Exterior/ConceptRemaster{TAG}"
SHIP_KEY = os.environ.get("GINNUNGAGAP_SHIP_REMASTER", "SmallUtilityEscort")
RNG = random.Random(80221)
BUILT: list[bpy.types.Object] = []

SPECS = {
    "SmallUtilityEscort": {
        "dimensions": (900.0, 125.0, 250.0),
        "concept": "docs/concept-art/reference/ships/small-utility-escort-exterior.png",
        "features": ["recessed service hangar", "six-engine drive district", "docking spine"],
    },
    "MilitaryCorvette": {
        "dimensions": (2400.0, 430.0, 620.0),
        "concept": "docs/concept-art/reference/ships/medium-military-corvette-exterior.png",
        "features": ["dual recessed hangars", "armored citadel", "defense terraces", "4x4 drive face"],
    },
    "ExpeditionCarrier": {
        "dimensions": (6500.0, 1400.0, 1800.0),
        "concept": "docs/concept-art/reference/ships/large-expedition-carrier-exterior.png",
        "features": ["carrier concourse", "habitat drum bay", "command city", "twelve-engine drive face"],
    },
}


def material(name, color, metallic=0.7, roughness=0.28, emission=None, strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    node = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    node.inputs["Base Color"].default_value = color
    node.inputs["Metallic"].default_value = metallic
    node.inputs["Roughness"].default_value = roughness
    if emission:
        socket = node.inputs.get("Emission Color") or node.inputs.get("Emission")
        socket.default_value = emission
        node.inputs["Emission Strength"].default_value = strength
    return mat


def make_materials():
    return {
        "armor": material("M_Remaster_Armor", (0.29, 0.31, 0.33, 1), 0.82, 0.27),
        "armor_light": material("M_Remaster_ArmorLight", (0.52, 0.54, 0.55, 1), 0.78, 0.3),
        "armor_dark": material("M_Remaster_ArmorDark", (0.075, 0.085, 0.095, 1), 0.88, 0.22),
        "structure": material("M_Remaster_Structure", (0.018, 0.024, 0.03, 1), 0.9, 0.2),
        "radiator": material("M_Remaster_Radiator", (0.055, 0.065, 0.075, 1), 0.74, 0.38),
        "orange": material("M_Remaster_SafetyOrange", (0.86, 0.16, 0.018, 1), 0.58, 0.25),
        "glass": material("M_Remaster_Glass", (0.01, 0.055, 0.085, 1), 0.48, 0.12),
        "blue": material("M_Remaster_BlueLight", (0.01, 0.12, 0.3, 1), 0.25, 0.16, (0.01, 0.55, 1, 1), 12),
        "drive": material("M_Remaster_Drive", (0.015, 0.04, 0.08, 1), 0.65, 0.16, (0.015, 0.32, 1, 1), 10),
    }


def assign(obj, mat):
    obj.data.materials.append(mat)
    BUILT.append(obj)
    return obj


def box(name, loc, scale, mat, bevel=1.0, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        mod = obj.modifiers.new("EdgeSoftening", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    return assign(obj, mat)


def cyl(name, loc, radius, depth, mat, axis="X", vertices=24, bevel=0.0):
    rot = (0, math.pi / 2, 0) if axis == "X" else ((math.pi / 2, 0, 0) if axis == "Y" else (0, 0, 0))
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.name = name
    if bevel:
        mod = obj.modifiers.new("RimSoftening", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    return assign(obj, mat)


def chamfered_section(name, x0, x1, half_y, half_z, mat, taper0=1.0, taper1=1.0):
    ring = [
        (0.0, 1.0), (0.70, 1.0), (1.0, 0.62), (1.0, -0.62),
        (0.70, -1.0), (-0.70, -1.0), (-1.0, -0.62), (-1.0, 0.62),
    ]
    verts = []
    for x, taper in ((x0, taper0), (x1, taper1)):
        verts.extend((x, y * half_y * taper, z * half_z * taper) for y, z in ring)
    faces = [tuple(range(7, -1, -1)), tuple(range(8, 16))]
    for i in range(8):
        j = (i + 1) % 8
        faces.append((i, j, 8 + j, 8 + i))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bevel = obj.modifiers.new("HullEdgeSoftening", "BEVEL")
    bevel.width = min(half_y, half_z) * 0.025
    bevel.segments = 2
    return assign(obj, mat)


def wing_plate(name, points, z, thickness, mat):
    """Create a beveled swept wing from four XY plan-view points."""
    bottom = z - thickness * 0.5
    top = z + thickness * 0.5
    verts = [(x, y, bottom) for x, y in points] + [(x, y, top) for x, y in points]
    faces = [(3, 2, 1, 0), (4, 5, 6, 7)]
    for i in range(4):
        j = (i + 1) % 4
        faces.append((i, j, 4 + j, 4 + i))
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(obj)
    bevel = obj.modifiers.new("WingEdgeSoftening", "BEVEL")
    bevel.width = thickness * 0.08
    bevel.segments = 2
    return assign(obj, mat)


def frame(name, center, opening, depth, mat, axis="Y", bar=8.0):
    x, y, z = center
    width, height = opening
    if axis == "Y":
        box(name + "_Top", (x, y, z + height / 2), (width + bar * 2, depth, bar), mat, bar * 0.18)
        box(name + "_Bottom", (x, y, z - height / 2), (width + bar * 2, depth, bar), mat, bar * 0.18)
        box(name + "_Fore", (x + width / 2, y, z), (bar, depth, height), mat, bar * 0.18)
        box(name + "_Aft", (x - width / 2, y, z), (bar, depth, height), mat, bar * 0.18)


def surface_lights(prefix, x0, x1, count, y, z, size, mats):
    for i in range(count):
        x = x0 + (x1 - x0) * (i + 0.5) / count
        box(f"{prefix}_Light_{i:02d}", (x, y, z), size, mats["blue"], size[2] * 0.25)


def armor_run(prefix, x0, x1, count, y, z, plate_size, mats, top=False):
    step = (x1 - x0) / count
    for i in range(count):
        x = x0 + step * (i + 0.5)
        tone = mats["armor_light"] if i % 3 else mats["armor"]
        dims = (step * 0.86, plate_size[0], plate_size[1]) if not top else (step * 0.86, plate_size[0], plate_size[1])
        box(f"{prefix}_Armor_{i:02d}", (x, y, z), dims, tone, min(dims) * 0.05)
        if i % 5 == 2:
            if top:
                box(f"{prefix}_Orange_{i:02d}", (x, y, z + dims[2] * 0.55), (step * 0.34, dims[1] * 0.18, dims[2] * 0.16), mats["orange"], 0.4)
            else:
                box(f"{prefix}_Orange_{i:02d}", (x, y * 1.006, z), (step * 0.34, dims[1] * 1.08, dims[2] * 0.18), mats["orange"], 0.4)


def turret(name, loc, scale, mats):
    x, y, z = loc
    cyl(name + "_Base", (x, y, z), scale * 0.42, scale * 0.25, mats["structure"], axis="Z", vertices=20, bevel=scale * 0.03)
    box(name + "_Housing", (x, y, z + scale * 0.22), (scale * 0.9, scale * 0.7, scale * 0.35), mats["armor"], scale * 0.08)
    cyl(name + "_Barrel", (x + scale * 0.68, y, z + scale * 0.26), scale * 0.08, scale * 0.9, mats["structure"], axis="X", vertices=12)


def engine_face(prefix, x, ys, zs, radius, mats):
    for row, z in enumerate(zs):
        for col, y in enumerate(ys):
            name = f"{prefix}_R{row}_C{col}"
            cyl(name + "_Housing", (x + radius * 0.55, y, z), radius * 1.18, radius * 1.4, mats["structure"], axis="X", vertices=28, bevel=radius * 0.05)
            cyl(name + "_Collar", (x - radius * 0.05, y, z), radius, radius * 0.34, mats["armor"], axis="X", vertices=28, bevel=radius * 0.04)
            cyl(name + "_Glow", (x - radius * 0.24, y, z), radius * 0.72, radius * 0.12, mats["drive"], axis="X", vertices=28)


def greeble_side(prefix, x0, x1, count, y, z0, z1, depth, mats):
    for i in range(count):
        x = x0 + (x1 - x0) * (i + 0.5) / count
        z = z0 + (z1 - z0) * (0.2 + 0.6 * RNG.random())
        w = (x1 - x0) / count * RNG.uniform(0.35, 0.72)
        h = max(3.0, (z1 - z0) * RNG.uniform(0.04, 0.1))
        mat = mats["structure"] if i % 4 else mats["orange"]
        box(f"{prefix}_{i:03d}", (x, y, z), (w, depth, h), mat, min(h, depth) * 0.12)


def build_small(m):
    chamfered_section("Escort_Core_Aft", -450, -270, 56, 112, m["armor"], 0.72, 1.0)
    chamfered_section("Escort_Core_Main", -270, 310, 61, 120, m["armor"], 1.0, 1.0)
    chamfered_section("Escort_Core_Bow", 310, 450, 58, 108, m["armor"], 1.0, 0.68)
    armor_run("Escort_Port", -260, 360, 12, -60.5, 18, (5, 42), m)
    armor_run("Escort_Starboard", -260, 360, 12, 60.5, 18, (5, 42), m)
    armor_run("Escort_Dorsal", -300, 360, 11, 0, 119, (88, 5), m, top=True)
    for side in (-1, 1):
        y = side * 62
        box(f"Escort_HangarRecess_{side}", (55, y, -5), (310, 5, 112), m["structure"], 2)
        frame(f"Escort_HangarFrame_{side}", (55, y * 1.012, -5), (310, 112), 9, m["armor_dark"], bar=12)
        surface_lights(f"Escort_Hangar_{side}", -78, 188, 11, y * 1.025, 45, (13, 3, 3), m)
    box("Escort_CommandLower", (18, 0, 126), (150, 62, 18), m["armor_dark"], 4)
    box("Escort_CommandDeck", (5, 0, 142), (105, 49, 18), m["armor_light"], 4)
    box("Escort_CommandCrown", (-8, 0, 158), (64, 35, 15), m["armor_dark"], 3)
    cyl("Escort_SensorMast", (-8, 0, 180), 3.2, 36, m["structure"], axis="Z", vertices=12)
    cyl("Escort_SensorDish", (-8, 0, 194), 14, 2.5, m["blue"], axis="Z", vertices=24)
    engine_face("Escort_Drive", -478, [-29, 29], [-70, 0, 70], 17, m)
    greeble_side("Escort_PortService", -350, 390, 30, -62.8, -92, 94, 5, m)
    greeble_side("Escort_StarboardService", -350, 390, 30, 62.8, -92, 94, 5, m)


def build_corvette(m):
    chamfered_section("Corvette_DriveBlock", -1200, -930, 205, 285, m["armor_dark"], 0.82, 1.0)
    chamfered_section("Corvette_AftHull", -930, -280, 212, 300, m["armor"], 1.0, 1.0)
    chamfered_section("Corvette_MidHull", -280, 650, 215, 305, m["armor"], 1.0, 0.94)
    chamfered_section("Corvette_BowHull", 650, 1200, 202, 276, m["armor"], 0.94, 0.55)
    armor_run("Corvette_Port", -1060, 1080, 22, -214, 52, (12, 82), m)
    armor_run("Corvette_Starboard", -1060, 1080, 22, 214, 52, (12, 82), m)
    armor_run("Corvette_Dorsal", -1030, 1060, 20, 0, 304, (350, 12), m, top=True)
    for side in (-1, 1):
        y = side * 218
        for idx, hx in enumerate((-360, 235)):
            box(f"Corvette_HangarRecess_{side}_{idx}", (hx, y, -24), (430, 12, 190), m["structure"], 5)
            frame(f"Corvette_HangarFrame_{side}_{idx}", (hx, y * 1.005, -24), (430, 190), 18, m["armor_dark"], bar=22)
            surface_lights(f"Corvette_HangarLight_{side}_{idx}", hx - 175, hx + 175, 9, y * 1.01, 60, (22, 5, 5), m)
    box("Corvette_CitadelFoundation", (140, 0, 318), (620, 300, 34), m["armor_dark"], 8)
    box("Corvette_CitadelLower", (115, 0, 352), (450, 246, 46), m["armor"], 9)
    box("Corvette_CitadelUpper", (75, 0, 390), (300, 180, 40), m["armor_light"], 8)
    box("Corvette_CitadelCrown", (25, 0, 423), (170, 112, 32), m["armor_dark"], 6)
    for y in (-52, 0, 52):
        cyl(f"Corvette_CitadelMast_{y}", (15, y, 462), 3.4, 58, m["structure"], axis="Z", vertices=12)
    for x in (-760, -500, 590, 830):
        for y in (-118, 118):
            turret(f"Corvette_Defense_{x}_{y}", (x, y, 322), 34, m)
    if VERSION >= 3:
        for side in (-1, 1):
            points = [(120, side * 172), (-650, side * 172), (-940, side * 382), (-385, side * 382)]
            wing_plate(f"Corvette_PropulsionWing_{side}", points, -48, 62, m["armor_dark"])
            inset = [(15, side * 183), (-595, side * 183), (-855, side * 350), (-405, side * 350)]
            wing_plate(f"Corvette_PropulsionWingArmor_{side}", inset, -12, 20, m["armor_light"])
            box(f"Corvette_WingRoot_{side}", (-275, side * 190, -46), (560, 70, 120), m["structure"], 9)
            engine_face(f"Corvette_WingDrive_{side}", -970, [side * 365], [-82, 82], 33, m)
        engine_face("Corvette_CentralDrive", -1265, [-76, 76], [-145, 0, 145], 32, m)
    else:
        engine_face("Corvette_Drive", -1265, [-142, -48, 48, 142], [-200, -66, 66, 200], 36, m)
    for side in (-1, 1):
        greeble_side(f"Corvette_Service_{side}", -1090, 1110, 52, side * 218.5, -235, 235, 13, m)
        surface_lights(f"Corvette_Waist_{side}", -980, 980, 28, side * 222, -150, (28, 5, 6), m)
    for x in (-1040, -830, 760, 970):
        box(f"Corvette_BeltFrame_{x}", (x, 0, -120), (34, 428, 470), m["armor_dark"], 5)


def build_carrier(m):
    chamfered_section("Carrier_DriveCitadel", -3250, -2820, 675, 850, m["armor_dark"], 0.82, 1.0)
    chamfered_section("Carrier_AftHull", -2820, -1250, 695, 880, m["armor"], 1.0, 1.0)
    chamfered_section("Carrier_MainHull", -1250, 1950, 700, 900, m["armor"], 1.0, 0.96)
    chamfered_section("Carrier_ForwardHull", 1950, 3250, 670, 820, m["armor"], 0.96, 0.58)
    armor_run("Carrier_Port", -3000, 2920, 30, -698, 150, (24, 230), m)
    armor_run("Carrier_Starboard", -3000, 2920, 30, 698, 150, (24, 230), m)
    for lane, y in enumerate((-430, -145, 145, 430)):
        armor_run(f"Carrier_DorsalLane_{lane}", -2850, 2850, 25, y, 895, (245, 24), m, top=True)
    for side in (-1, 1):
        y = side * 708
        box(f"Carrier_ConcourseRecess_{side}", (1350, y, -40), (1550, 30, 430), m["structure"], 10)
        frame(f"Carrier_ConcourseFrame_{side}", (1350, y * 1.002, -40), (1550, 430), 38, m["armor_dark"], bar=55)
        surface_lights(f"Carrier_ConcourseLight_{side}", 680, 2020, 18, y * 1.006, 150, (40, 12, 12), m)
    # Protected habitat drums run longitudinally inside a recessed structural bay.
    for side in (-1, 1):
        y = side * 610
        box(f"Carrier_HabitatBay_{side}", (-1140, side * 706, -210), (2050, 34, 520), m["structure"], 10)
        frame(f"Carrier_HabitatBayFrame_{side}", (-1140, side * 712, -210), (2050, 520), 42, m["armor_dark"], bar=58)
        for idx, x in enumerate((-1880, -1510, -1140, -770, -400)):
            cyl(f"Carrier_HabitatDrum_{side}_{idx}", (x, y, -210), 205, 315, m["armor"], axis="X", vertices=32, bevel=12)
            for band in (-142, 0, 142):
                cyl(f"Carrier_HabitatBand_{side}_{idx}_{band}", (x + band, y, -210), 214, 24, m["armor_dark"], axis="X", vertices=32)
            surface_lights(f"Carrier_HabitatLight_{side}_{idx}", x - 115, x + 115, 4, side * 818, -210, (24, 7, 10), m)
    box("Carrier_CommandFoundation", (260, 0, 912), (1650, 760, 55), m["armor_dark"], 12)
    for tier, (sx, sy, sz, z) in enumerate(((1250, 620, 85, 970), (880, 470, 85, 1050), (560, 320, 80, 1128), (310, 190, 70, 1200))):
        box(f"Carrier_CommandCityTier_{tier}", (130 - tier * 55, 0, z), (sx, sy, sz), m["armor_light"] if tier % 2 else m["armor"], 14)
    for y in (-110, -38, 38, 110):
        cyl(f"Carrier_CommandMast_{y}", (-40, y, 1300), 7, 170 + abs(y) * 0.25, m["structure"], axis="Z", vertices=14)
    for x in (-2500, -2050, -750, 1650, 2220, 2650):
        for y in (-360, 360):
            turret(f"Carrier_Defense_{x}_{y}", (x, y, 915), 72, m)
    if VERSION >= 3:
        for side in (-1, 1):
            points = [(520, side * 610), (-1840, side * 610), (-2920, side * 1210), (-520, side * 1210)]
            wing_plate(f"Carrier_PropulsionWing_{side}", points, -330, 190, m["armor_dark"])
            inset = [(300, side * 635), (-1720, side * 635), (-2750, side * 1140), (-590, side * 1140)]
            wing_plate(f"Carrier_PropulsionWingArmor_{side}", inset, -220, 55, m["armor_light"])
            box(f"Carrier_WingRootTruss_{side}", (-900, side * 655, -325), (1900, 180, 330), m["structure"], 24)
            for x in (-2050, -2520):
                box(f"Carrier_WingRadiator_{side}_{x}", (x, side * 970, -205), (350, 300, 34), m["radiator"], 9)
            engine_face(f"Carrier_WingDrive_{side}", -2940, [side * 1140], [-265, 0, 265], 98, m)
        engine_face("Carrier_CentralDrive", -3400, [-225, 225], [-335, 0, 335], 108, m)
    else:
        engine_face("Carrier_Drive", -3400, [-480, -160, 160, 480], [-430, 0, 430], 115, m)
    for side in (-1, 1):
        greeble_side(f"Carrier_Service_{side}", -3000, 3000, 78, side * 704, -650, 650, 32, m)
        surface_lights(f"Carrier_Waist_{side}", -2800, 2800, 42, side * 712, -520, (70, 12, 14), m)
    for x in (-2860, -2450, -2020, 2280, 2660, 2970):
        box(f"Carrier_TransverseFrame_{x}", (x, 0, -180), (65, 1390, 1320), m["armor_dark"], 10)


def apply_modifiers():
    bpy.context.view_layer.update()
    for obj in list(BUILT):
        if not obj.modifiers:
            continue
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        for mod in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except RuntimeError:
                pass
        obj.select_set(False)


def bounds():
    points = [obj.matrix_world @ Vector(corner) for obj in BUILT for corner in obj.bound_box]
    return Vector(tuple(min(p[i] for p in points) for i in range(3))), Vector(tuple(max(p[i] for p in points) for i in range(3)))


def enforce_dimensions(target):
    low, high = bounds()
    center = (low + high) * 0.5
    size = high - low
    factors = Vector((target[0] / size.x, target[1] / size.y, target[2] / size.z))
    transform = Matrix.Diagonal((*factors, 1.0)) @ Matrix.Translation(-center)
    for obj in BUILT:
        obj.matrix_world = transform @ obj.matrix_world
    bpy.context.view_layer.update()


def setup_scene():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.55
    world = bpy.data.worlds.new("RemasterV02World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.0015, 0.003, 0.006, 1)
    bg.inputs["Strength"].default_value = 0.22
    for name, direction, energy, color in (
        ("Key", (0.4, -1, 0.8), 3.5, (1.0, 0.86, 0.7)),
        ("Fill", (-0.4, -1, 0.1), 1.8, (0.3, 0.55, 1.0)),
        ("Rim", (-0.8, 0.7, 1.0), 2.4, (0.2, 0.5, 1.0)),
    ):
        data = bpy.data.lights.new(name, "SUN")
        data.energy = energy
        data.color = color
        data.angle = math.radians(7)
        obj = bpy.data.objects.new(name, data)
        scene.collection.objects.link(obj)
        obj.location = Vector(direction) * 1000
        obj.rotation_euler = (-obj.location).to_track_quat("-Z", "Y").to_euler()


def camera(name, location, target, scale):
    data = bpy.data.cameras.new(name)
    data.type = "ORTHO"
    data.ortho_scale = scale
    data.clip_start = 0.1
    data.clip_end = 100000
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (target - location).to_track_quat("-Z", "Y").to_euler()
    return obj


def render_views(output):
    low, high = bounds()
    center, size = (low + high) * 0.5, high - low
    length, beam, height = size
    views = {
        "Beauty": (center + Vector((-length * 0.72, -length * 0.9, height * 1.05)), length / 1.08),
        "Side": (center + Vector((0, -length * 1.4, 0)), length / 1.2),
        "Top": (center + Vector((0, 0, length * 1.4)), length / 1.2),
        "Rear": (center + Vector((-length * 1.4, 0, 0)), max(beam, height) * 1.42),
    }
    rendered = {}
    for view, (loc, scale) in views.items():
        cam = camera("CAM_" + view, loc, center, scale)
        bpy.context.scene.camera = cam
        path = output / f"{SHIP_KEY}_Remaster{TAG}_{view}.png"
        bpy.context.scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rendered[view] = path
    return rendered


def export(output):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in BUILT:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = BUILT[0]
    path = output / f"{SHIP_KEY}_Remaster{TAG}.glb"
    bpy.ops.export_scene.gltf(filepath=str(path), export_format="GLB", use_selection=True, export_apply=True, export_yup=True)
    return path


def main():
    if SHIP_KEY not in SPECS:
        raise RuntimeError(f"Unknown ship key: {SHIP_KEY}")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = make_materials()
    {"SmallUtilityEscort": build_small, "MilitaryCorvette": build_corvette, "ExpeditionCarrier": build_carrier}[SHIP_KEY](mats)
    apply_modifiers()
    enforce_dimensions(SPECS[SHIP_KEY]["dimensions"])
    setup_scene()
    output = OUT_ROOT / SHIP_KEY
    output.mkdir(parents=True, exist_ok=True)
    glb = export(output)
    blend = output / f"{SHIP_KEY}_Remaster{TAG}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    rendered = render_views(output)
    low, high = bounds()
    signature_features = list(SPECS[SHIP_KEY]["features"])
    if VERSION >= 3 and SHIP_KEY == "MilitaryCorvette":
        signature_features = ["dual recessed hangars", "armored citadel", "mounted defense terraces", "six central drives plus twin-engine wing pods"]
    elif VERSION >= 3 and SHIP_KEY == "ExpeditionCarrier":
        signature_features = ["carrier concourse", "protected habitat drum bay", "command city", "six central drives plus three-engine wing pods"]
    manifest = {
        "version": VERSION,
        "ship": SHIP_KEY,
        "method": "Clean procedural hard-surface authoring from concept-board dimensions and features; no RealityScan"
        + ("; distributed wing propulsion redesign" if VERSION >= 3 else ""),
        "concept_authority": SPECS[SHIP_KEY]["concept"],
        "signature_features": signature_features,
        "object_count": len(BUILT),
        "dimensions_m": [round(v, 3) for v in high - low],
        "blend": str(blend.relative_to(PROJECT)).replace("\\", "/"),
        "glb": str(glb.relative_to(PROJECT)).replace("\\", "/"),
        "renders": {k: str(v.relative_to(PROJECT)).replace("\\", "/") for k, v in rendered.items()},
        "promotion_status": "Visual review required before Unreal import",
    }
    (output / "RemasterManifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"REMASTER_{TAG}_COMPLETE", json.dumps(manifest))


if __name__ == "__main__":
    main()
