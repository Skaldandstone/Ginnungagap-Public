"""Build a Blender-authored shipboard weapon collision-envelope reference kit."""

import bpy
import math
import os
from mathutils import Vector


ROOT = r"C:\Users\JDSha\OneDrive\Documents\GitHub\Ginnungagap"
ART_DIR = os.path.join(ROOT, "Art", "Weapons")
EXPORT_DIR = os.path.join(ART_DIR, "Exports")
BLEND_PATH = os.path.join(ART_DIR, "ShipboardWeapon_CollisionKit.blend")
PREVIEW_PATH = os.path.join(ART_DIR, "ShipboardWeapon_CollisionKit_Preview.png")
os.makedirs(EXPORT_DIR, exist_ok=True)

BACKGROUND_BUILD = bpy.app.background
if BACKGROUND_BUILD:
    bpy.ops.wm.read_factory_settings(use_empty=True)
ORIGINAL_SCENE = bpy.context.scene
# Interactive execution opens the completed kit only after confirming the source file was clean.
OPEN_RESULT_WHEN_COMPLETE = not BACKGROUND_BUILD


def mat(name, color, metallic=0.0, roughness=0.45, emission=None):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*color, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 3.0
    return material


M_GUNMETAL = mat("M_Gunmetal", (0.055, 0.07, 0.08), 0.82, 0.24)
M_DARK = mat("M_GripRubber", (0.015, 0.02, 0.025), 0.1, 0.72)
M_HAZARD = mat("M_SafetyYellow", (0.9, 0.42, 0.025), 0.42, 0.32)
M_STEEL = mat("M_BrushedSteel", (0.3, 0.36, 0.4), 0.88, 0.2)
M_RED = mat("M_ServiceRed", (0.55, 0.025, 0.02), 0.55, 0.32)
M_CYAN = mat("M_StatusCyan", (0.015, 0.22, 0.27), 0.25, 0.24, (0.01, 0.55, 0.75))
M_FOAM = mat("M_FoamCanister", (0.62, 0.66, 0.58), 0.35, 0.5)
M_ENVELOPES = {
    "Compact": mat("M_ENV_Compact", (0.05, 0.78, 0.34), 0.15, 0.35),
    "Standard": mat("M_ENV_Standard", (0.02, 0.48, 0.92), 0.15, 0.35),
    "Long": mat("M_ENV_Long", (0.92, 0.42, 0.02), 0.15, 0.35),
    "Bulky": mat("M_ENV_Bulky", (0.86, 0.04, 0.12), 0.15, 0.35),
}
M_PASSAGE = mat("M_PassageGuide", (0.24, 0.28, 0.32), 0.7, 0.28)
M_TEXT = mat("M_Label", (0.74, 0.9, 0.98), 0.0, 0.4, (0.25, 0.72, 1.0))


scene = bpy.context.scene if BACKGROUND_BUILD else bpy.data.scenes.new("Weapon_Collision_Kit")
scene.name = "Weapon_Collision_Kit"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1800
scene.render.resolution_y = 1100
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = PREVIEW_PATH
world = bpy.data.worlds.new("World_WeaponCollisionKit")
world.color = (0.006, 0.009, 0.014)
scene.world = world

root_collection = bpy.data.collections.new("WeaponCollisionKit")
scene.collection.children.link(root_collection)


def collection(name):
    col = bpy.data.collections.new(name)
    root_collection.children.link(col)
    return col


COL_WEAPONS = collection("Weapons")
COL_ENVELOPES = collection("CollisionEnvelopes")
COL_PASSAGES = collection("PassageGuides")
COL_LABELS = collection("Labels")
COL_LIGHTS = collection("Presentation")


def link_only(obj, col):
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    col.objects.link(obj)


def cube(name, location, dimensions, material, bevel=0.025, col=COL_WEAPONS):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod = obj.modifiers.new("EdgeSoftening", "BEVEL")
        mod.width = bevel
        mod.segments = 3
    obj.data.materials.append(material)
    obj.color = material.diffuse_color
    link_only(obj, col)
    return obj


def cylinder(name, location, radius, depth, material, rotation=(0.0, math.pi / 2.0, 0.0), col=COL_WEAPONS):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    obj.color = material.diffuse_color
    bevel = obj.modifiers.new("EdgeSoftening", "BEVEL")
    bevel.width = min(radius * 0.12, 0.018)
    bevel.segments = 3
    link_only(obj, col)
    return obj


def text(name, body, location, size=0.16, align="CENTER"):
    curve = bpy.data.curves.new(name + "_Curve", "FONT")
    curve.body = body
    curve.align_x = align
    curve.align_y = "CENTER"
    curve.size = size
    curve.extrude = 0.004
    curve.bevel_depth = 0.001
    obj = bpy.data.objects.new(name, curve)
    obj.location = location
    obj.rotation_euler = (math.pi / 2.0, 0.0, 0.0)
    curve.materials.append(M_TEXT)
    obj.color = M_TEXT.diffuse_color
    COL_LABELS.objects.link(obj)
    return obj


def envelope(name, center, full_dimensions, envelope_class, can_fold=False, folded_dimensions=None):
    env = cube("ENV_" + name, center, full_dimensions, M_ENVELOPES[envelope_class], 0.0, COL_ENVELOPES)
    env.display_type = "WIRE"
    env.display.show_shadows = False
    env.show_in_front = True
    env["ue_envelope_class"] = envelope_class
    env["ue_half_extents_cm"] = [round(v * 50.0, 3) for v in full_dimensions]
    env["ue_center_offset_cm"] = [0.0, 0.0, 0.0]
    env["ue_can_fold_for_traversal"] = can_fold
    if folded_dimensions:
        env["ue_folded_half_extents_cm"] = [round(v * 50.0, 3) for v in folded_dimensions]
        folded = cube("ENV_FOLDED_" + name, center, folded_dimensions, M_CYAN, 0.0, COL_ENVELOPES)
        folded.display_type = "WIRE"
        folded.display.show_shadows = False
        folded.show_in_front = True
        folded.hide_render = True
    return env


def weapon_root(name, origin):
    root = bpy.data.objects.new(name, None)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.18
    root.location = (0.0, 0.0, 0.0)
    root["presentation_origin"] = list(origin)
    COL_WEAPONS.objects.link(root)
    return root


def parent_parts(root, parts):
    for obj in parts:
        world_transform = obj.matrix_world.copy()
        obj.parent = root
        obj.matrix_world = world_transform
    root["unreal_forward_axis"] = "+X"
    root["unreal_up_axis"] = "+Z"


rows = [2.55, 0.85, -0.85, -2.55]

# 01: Captive bolt driver - existing first-playable ship tool.
y = rows[0]
root = weapon_root("WPN_CaptiveBoltDriver", (0.0, y, 0.72))
parts = [
    cube("CBD_MainHousing", (0.0, y, 0.72), (0.46, 0.19, 0.19), M_GUNMETAL),
    cylinder("CBD_CaptiveBarrel", (0.30, y, 0.74), 0.065, 0.24, M_STEEL),
    cube("CBD_MuzzleGuard", (0.43, y, 0.74), (0.07, 0.16, 0.17), M_HAZARD, 0.016),
    cube("CBD_RearBattery", (-0.27, y, 0.73), (0.16, 0.17, 0.17), M_DARK, 0.018),
    cube("CBD_Grip", (-0.07, y, 0.52), (0.12, 0.14, 0.25), M_DARK, 0.025),
    cube("CBD_StatusStrip", (0.05, y - 0.101, 0.77), (0.19, 0.012, 0.035), M_CYAN, 0.005),
]
parent_parts(root, parts)
envelope("CaptiveBoltDriver", (0.0, y, 0.70), (0.70, 0.24, 0.24), "Compact")
text("LBL_CBD", "01  CAPTIVE BOLT DRIVER   // COMPACT  70 x 24 x 24 cm", (-0.1, y, 1.14), 0.12)

# 02: Pneumatic tissue injector / rivet launcher.
y = rows[1]
root = weapon_root("WPN_PneumaticInjector", (0.0, y, 0.72))
parts = [
    cube("PI_Receiver", (0.0, y, 0.76), (0.57, 0.24, 0.22), M_GUNMETAL),
    cylinder("PI_Barrel", (0.38, y, 0.78), 0.052, 0.34, M_STEEL),
    cylinder("PI_AirBottle", (-0.17, y + 0.14, 0.67), 0.09, 0.36, M_RED),
    cube("PI_BottleCradle", (-0.16, y, 0.67), (0.30, 0.28, 0.07), M_HAZARD, 0.015),
    cube("PI_Grip", (-0.10, y, 0.51), (0.13, 0.15, 0.27), M_DARK, 0.025),
    cube("PI_PressureReadout", (0.07, y - 0.132, 0.80), (0.17, 0.014, 0.055), M_CYAN, 0.005),
]
parent_parts(root, parts)
envelope("PneumaticInjector", (0.0, y, 0.72), (1.00, 0.36, 0.32), "Standard")
text("LBL_PI", "02  PNEUMATIC INJECTOR   // STANDARD  100 x 36 x 32 cm", (-0.1, y, 1.18), 0.12)

# 03: Folding arc-cutter lance.
y = rows[2]
root = weapon_root("WPN_ArcCutterLance", (0.0, y, 0.72))
parts = [
    cylinder("ACL_MainShaft", (0.15, y, 0.75), 0.052, 1.18, M_STEEL),
    cube("ACL_PowerHousing", (-0.45, y, 0.74), (0.34, 0.25, 0.25), M_GUNMETAL),
    cylinder("ACL_Hinge", (-0.18, y, 0.75), 0.10, 0.18, M_HAZARD, rotation=(math.pi / 2.0, 0.0, 0.0)),
    cube("ACL_ForwardGrip", (0.17, y, 0.60), (0.17, 0.13, 0.19), M_DARK, 0.025),
    cube("ACL_RearGrip", (-0.46, y, 0.52), (0.14, 0.15, 0.25), M_DARK, 0.025),
    cylinder("ACL_Electrode", (0.79, y, 0.75), 0.025, 0.18, M_CYAN),
]
parent_parts(root, parts)
envelope("ArcCutterLance", (0.0, y, 0.72), (1.60, 0.30, 0.30), "Long", True, (0.76, 0.26, 0.28))
text("LBL_ACL", "03  FOLDING ARC-CUTTER LANCE   // LONG  160 x 30 x 30 cm", (-0.1, y, 1.18), 0.12)

# 04: Bulky foam-suppression projector with twin ship-service canisters.
y = rows[3]
root = weapon_root("WPN_FoamSuppressionProjector", (0.0, y, 0.72))
parts = [
    cube("FSP_Receiver", (0.08, y, 0.76), (0.52, 0.29, 0.27), M_GUNMETAL),
    cylinder("FSP_Nozzle", (0.41, y, 0.78), 0.085, 0.30, M_STEEL),
    cylinder("FSP_LeftTank", (-0.20, y - 0.18, 0.72), 0.12, 0.43, M_FOAM),
    cylinder("FSP_RightTank", (-0.20, y + 0.18, 0.72), 0.12, 0.43, M_FOAM),
    cube("FSP_TankBrace", (-0.19, y, 0.72), (0.31, 0.49, 0.10), M_HAZARD, 0.018),
    cube("FSP_ShoulderBrace", (-0.42, y, 0.78), (0.16, 0.36, 0.32), M_DARK, 0.035),
    cube("FSP_Control", (0.10, y - 0.16, 0.91), (0.20, 0.055, 0.07), M_CYAN, 0.008),
]
parent_parts(root, parts)
envelope("FoamSuppressionProjector", (0.0, y, 0.72), (0.95, 0.60, 0.50), "Bulky")
text("LBL_FSP", "04  FOAM SUPPRESSION PROJECTOR   // BULKY  95 x 60 x 50 cm", (-0.1, y, 1.22), 0.12)


def passage_frame(name, x, y, clear_width, clear_height, depth=0.16):
    z = clear_height / 2.0
    bar = 0.09
    parts = [
        cube(name + "_Left", (x, y - clear_width / 2.0 - bar / 2.0, z), (depth, bar, clear_height + 0.18), M_PASSAGE, 0.01, COL_PASSAGES),
        cube(name + "_Right", (x, y + clear_width / 2.0 + bar / 2.0, z), (depth, bar, clear_height + 0.18), M_PASSAGE, 0.01, COL_PASSAGES),
        cube(name + "_Top", (x, y, clear_height + bar / 2.0), (depth, clear_width + bar * 2.0, bar), M_PASSAGE, 0.01, COL_PASSAGES),
        cube(name + "_Deck", (x, y, -bar / 2.0), (depth, clear_width + bar * 2.0, bar), M_PASSAGE, 0.01, COL_PASSAGES),
    ]
    for part in parts:
        part["clear_width_cm"] = round(clear_width * 100.0, 2)
        part["clear_height_cm"] = round(clear_height * 100.0, 2)
        part["travel_axis"] = "+X"
    return parts


# Three reusable authoring guides placed to the right of the weapon study.
passage_frame("PASS_Duct_40x50", 2.25, 2.15, 0.40, 0.50)
passage_frame("PASS_Hatch_90x90", 2.25, 0.25, 0.90, 0.90)
passage_frame("PASS_ServiceGap_55x70", 2.25, -2.00, 0.55, 0.70)
text("LBL_PASS_1", "DUCT 40 x 50 cm", (2.25, 2.15, 0.78), 0.10)
text("LBL_PASS_2", "HATCH 90 x 90 cm", (2.25, 0.25, 1.18), 0.10)
text("LBL_PASS_3", "SERVICE GAP 55 x 70 cm", (2.25, -2.00, 0.98), 0.10)

# Ground/reference plane.
ground = cube("PresentationDeck", (0.85, 0.0, -0.11), (4.8, 7.0, 0.12), M_DARK, 0.02, COL_PASSAGES)

# Camera and lighting.
camera_data = bpy.data.cameras.new("CAM_WeaponCollisionKit")
camera = bpy.data.objects.new("CAM_WeaponCollisionKit", camera_data)
COL_LIGHTS.objects.link(camera)
scene.camera = camera
camera.location = (7.6, -8.8, 7.2)
camera_data.lens = 53


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


point_at(camera, (0.65, 0.0, 0.65))
for name, location, energy, color, size in [
    ("Key", (2.0, -4.0, 7.0), 1500.0, (0.72, 0.86, 1.0), 4.0),
    ("Rim", (-4.0, 3.0, 4.5), 1100.0, (1.0, 0.28, 0.08), 3.0),
    ("Fill", (5.5, 4.0, 2.8), 900.0, (0.1, 0.45, 1.0), 3.0),
]:
    light_data = bpy.data.lights.new(name, "AREA")
    light_data.energy = energy
    light_data.color = color
    light_data.shape = "DISK"
    light_data.size = size
    light = bpy.data.objects.new(name, light_data)
    light.location = location
    point_at(light, (0.6, 0.0, 0.6))
    COL_LIGHTS.objects.link(light)

# Unit and export metadata.
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
scene["unreal_units_per_meter"] = 100
scene["collision_envelope_axis"] = "Local X length, Y width, Z height"
scene["passage_travel_axis"] = "Local +X"

# Render from the temporary scene, then export each weapon with its envelope as GLB.
if bpy.context.window:
    bpy.context.window.scene = scene
bpy.ops.render.render(write_still=True)

for root in [obj for obj in COL_WEAPONS.objects if obj.type == "EMPTY" and obj.name.startswith("WPN_")]:
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    for child in root.children_recursive:
        child.select_set(True)
    short_name = root.name.removeprefix("WPN_")
    env = bpy.data.objects.get("ENV_" + short_name)
    if env:
        env.select_set(True)
    bpy.context.view_layer.objects.active = root
    original_root_transform = root.matrix_world.copy()
    original_env_transform = env.matrix_world.copy() if env else None
    presentation_origin = Vector(root["presentation_origin"])
    root.location -= presentation_origin
    if env:
        env.location -= presentation_origin
    bpy.ops.export_scene.gltf(
        filepath=os.path.join(EXPORT_DIR, "SM_" + short_name + ".glb"),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
    )
    root.matrix_world = original_root_transform
    if env and original_env_transform:
        env.matrix_world = original_env_transform

# Write a standalone file. Background mode owns an empty document; interactive mode writes a
# library first so the source document is never saved or overwritten.
if BACKGROUND_BUILD:
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH, compress=True)
else:
    bpy.data.libraries.write(BLEND_PATH, {scene}, path_remap="RELATIVE_ALL", fake_user=True, compress=True)

if OPEN_RESULT_WHEN_COMPLETE:
    bpy.ops.wm.open_mainfile(filepath=BLEND_PATH)
else:
    bpy.context.window.scene = ORIGINAL_SCENE

print("WEAPON_COLLISION_KIT_COMPLETE", BLEND_PATH, PREVIEW_PATH)
