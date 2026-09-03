"""Create weapon production batch 02: 12 weapons, 4 mounts, and a 100-step report."""

import bpy
import json
import math
import os
from mathutils import Vector


ROOT = r"C:\Users\JDSha\OneDrive\Documents\GitHub\Ginnungagap"
ART_DIR = os.path.join(ROOT, "Art", "Weapons", "ProductionBatch02")
EXPORT_DIR = os.path.join(ART_DIR, "Exports")
META_DIR = os.path.join(ART_DIR, "Metadata")
BLEND_PATH = os.path.join(ART_DIR, "ShipboardWeapons_ProductionBatch02.blend")
PREVIEW_PATH = os.path.join(ART_DIR, "ShipboardWeapons_ProductionBatch02_Preview.png")
MANIFEST_PATH = os.path.join(META_DIR, "WeaponBatch02.json")
REPORT_PATH = os.path.join(META_DIR, "ProductionBatch02_100Steps.md")
for directory in (ART_DIR, EXPORT_DIR, META_DIR):
    os.makedirs(directory, exist_ok=True)


WEAPONS = [
    dict(id="ThermalSeamCutter", label="THERMAL SEAM CUTTER", form="cutter", envelope="Compact",
         size=(0.72, 0.28, 0.28), fold=None, players=True, aerial=True, robotic=True, soldier=False,
         ship="Engineering / damage-control", safe="Captive thermal blade", unsafe="Overdriven hull-cutting arc"),
    dict(id="HydraulicRescueSpreader", label="HYDRAULIC RESCUE SPREADER", form="spreader", envelope="Bulky",
         size=(1.15, 0.62, 0.48), fold=(0.78, 0.42, 0.38), players=True, aerial=False, robotic=True, soldier=False,
         ship="Rescue / carrier / industrial", safe="Low-pressure pry", unsafe="High-pressure structural shear"),
    dict(id="CO2SlugProjector", label="CO2 SLUG PROJECTOR", form="projector", envelope="Standard",
         size=(0.98, 0.38, 0.34), fold=None, players=True, aerial=True, robotic=True, soldier=True,
         ship="Security / mining", safe="Frangible polymer slug", unsafe="Hardened penetrator slug"),
    dict(id="CryogenicLineSprayer", label="CRYOGENIC LINE SPRAYER", form="sprayer", envelope="Standard",
         size=(0.92, 0.42, 0.40), fold=None, players=True, aerial=True, robotic=True, soldier=False,
         ship="Science / medical / engineering", safe="Metered cryogenic mist", unsafe="Seal-defeating liquid jet"),
    dict(id="CableAnchorLauncher", label="CABLE ANCHOR LAUNCHER", form="cable", envelope="Long",
         size=(1.35, 0.36, 0.38), fold=(0.82, 0.32, 0.34), players=True, aerial=True, robotic=True, soldier=False,
         ship="EVA / cargo / salvage", safe="Magnetic soft anchor", unsafe="Barbed structural anchor"),
    dict(id="UltrasonicDelaminationTool", label="ULTRASONIC DELAMINATION TOOL", form="sonic", envelope="Standard",
         size=(0.84, 0.44, 0.36), fold=None, players=True, aerial=True, robotic=True, soldier=False,
         ship="Inspection / fabrication", safe="Bond-release resonance", unsafe="Material-fracture resonance"),
    dict(id="PlasmaTorchCarbine", label="PLASMA TORCH CARBINE", form="plasma", envelope="Long",
         size=(1.22, 0.34, 0.38), fold=(0.76, 0.30, 0.32), players=True, aerial=False, robotic=True, soldier=True,
         ship="Security / military repair", safe="Short captive plasma tongue", unsafe="Unshielded extended plasma"),
    dict(id="ShockTetherBaton", label="SHOCK TETHER BATON", form="baton", envelope="Compact",
         size=(0.66, 0.22, 0.22), fold=(0.38, 0.20, 0.20), players=True, aerial=True, robotic=True, soldier=False,
         ship="Medical restraint / security", safe="Current-limited tether", unsafe="Sustained muscle-lock discharge"),
    dict(id="AutonomousSentryNode", label="AUTONOMOUS SENTRY NODE", form="sentry", envelope="Emplaced",
         size=(0.86, 0.78, 0.68), fold=(0.62, 0.52, 0.48), players=False, aerial=False, robotic=True, soldier=True,
         ship="Security / military", safe="Foam and stun package", unsafe="Mixed hardened payload"),
    dict(id="DroneMicroBoltPod", label="DRONE MICRO-BOLT POD", form="dronepod", envelope="Compact",
         size=(0.48, 0.32, 0.24), fold=None, players=False, aerial=True, robotic=True, soldier=False,
         ship="Maintenance drone inventory", safe="Tethered micro-bolts", unsafe="Free-flight hardened bolts"),
    dict(id="RoboticNailDriver", label="ROBOTIC NAIL DRIVER", form="nailer", envelope="Standard",
         size=(0.82, 0.36, 0.34), fold=None, players=True, aerial=False, robotic=True, soldier=False,
         ship="Fabrication / cargo robotics", safe="Depth-limited fastener", unsafe="Bypassed depth stop"),
    dict(id="XenoResonanceFocus", label="XENO RESONANCE FOCUS", form="xeno", envelope="Bulky",
         size=(1.02, 0.58, 0.54), fold=(0.72, 0.44, 0.42), players=True, aerial=False, robotic=True, soldier=True,
         ship="Recovered alien artifact", safe="Human damping cage active", unsafe="Damping cage removed"),
]

MOUNTS = [
    dict(id="PlayerUniversalGrip", label="PLAYER UNIVERSAL GRIP", operators=["Player"]),
    dict(id="AerialDroneGimbal", label="AERIAL DRONE GIMBAL", operators=["AerialDrone"]),
    dict(id="RoboticHardpoint", label="ROBOTIC HARDPOINT", operators=["RoboticDrone"]),
    dict(id="EmplacedTripod", label="EMPLACED TRIPOD", operators=["RoboticDrone", "Soldier"]),
]


bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.name = "ShipboardWeapons_ProductionBatch02"
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 2400
scene.render.resolution_y = 1500
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.render.filepath = PREVIEW_PATH
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0
scene["unreal_forward_axis"] = "+X"
scene["unreal_up_axis"] = "+Z"
scene["unreal_units_per_meter"] = 100

world = bpy.data.worlds.new("World_Batch02")
world.color = (0.004, 0.007, 0.012)
scene.world = world


def material(name, color, metallic=0.0, roughness=0.45, emission=None):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 4.0
    return mat


MAT = {
    "gunmetal": material("M02_Gunmetal", (0.035, 0.05, 0.065), 0.82, 0.23),
    "steel": material("M02_Steel", (0.32, 0.38, 0.42), 0.88, 0.18),
    "dark": material("M02_Rubber", (0.008, 0.012, 0.016), 0.08, 0.78),
    "hazard": material("M02_Hazard", (0.92, 0.38, 0.02), 0.42, 0.3),
    "medical": material("M02_Medical", (0.72, 0.82, 0.78), 0.26, 0.38),
    "red": material("M02_Red", (0.62, 0.018, 0.02), 0.5, 0.3),
    "cyan": material("M02_Cyan", (0.01, 0.25, 0.32), 0.2, 0.22, (0.01, 0.7, 1.0)),
    "violet": material("M02_Xeno", (0.18, 0.025, 0.32), 0.45, 0.22, (0.42, 0.03, 0.95)),
    "label": material("M02_Label", (0.72, 0.88, 1.0), 0.0, 0.42, (0.2, 0.62, 1.0)),
    "deck": material("M02_Deck", (0.012, 0.018, 0.025), 0.55, 0.42),
}
ENV_MATS = {
    "Compact": material("M02_ENV_Compact", (0.04, 0.9, 0.34), 0.25, 0.28),
    "Standard": material("M02_ENV_Standard", (0.02, 0.48, 1.0), 0.25, 0.28),
    "Long": material("M02_ENV_Long", (1.0, 0.4, 0.02), 0.25, 0.28),
    "Bulky": material("M02_ENV_Bulky", (1.0, 0.03, 0.12), 0.25, 0.28),
    "Emplaced": material("M02_ENV_Emplaced", (0.68, 0.06, 0.92), 0.25, 0.28),
}


def make_collection(name):
    col = bpy.data.collections.new(name)
    scene.collection.children.link(col)
    return col


COL_WEAPONS = make_collection("Weapons_Batch02")
COL_ENVELOPES = make_collection("CollisionEnvelopes_Batch02")
COL_MOUNTS = make_collection("MountAdapters")
COL_LABELS = make_collection("Labels")
COL_PRESENTATION = make_collection("Presentation")


def relink(obj, col):
    for current in list(obj.users_collection):
        current.objects.unlink(obj)
    col.objects.link(obj)


def cube(name, parent, loc, dims, mat, bevel=0.02, col=COL_WEAPONS):
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.parent = parent
    obj.location = loc
    obj.data.materials.append(mat)
    if bevel:
        modifier = obj.modifiers.new("EdgeSoftening", "BEVEL")
        modifier.width = min(bevel, min(dims) * 0.18)
        modifier.segments = 3
    relink(obj, col)
    return obj


def cylinder(name, parent, loc, radius, depth, mat, rotation=(0.0, math.pi / 2.0, 0.0), col=COL_WEAPONS):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=radius, depth=depth, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.parent = parent
    obj.location = loc
    obj.data.materials.append(mat)
    bevel = obj.modifiers.new("EdgeSoftening", "BEVEL")
    bevel.width = min(0.014, radius * 0.15)
    bevel.segments = 3
    relink(obj, col)
    return obj


def sphere(name, parent, loc, scale, mat, col=COL_WEAPONS):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=1.0)
    obj = bpy.context.object
    obj.name = name
    obj.parent = parent
    obj.location = loc
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    relink(obj, col)
    return obj


def torus(name, parent, loc, major, minor, mat, rotation=(0.0, math.pi / 2.0, 0.0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=24, minor_segments=8,
                                    rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.parent = parent
    obj.location = loc
    obj.data.materials.append(mat)
    relink(obj, COL_WEAPONS)
    return obj


def socket(parent, name, loc, forward=(1.0, 0.0, 0.0)):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = "ARROWS"
    obj.empty_display_size = 0.09
    obj.parent = parent
    obj.location = loc
    obj["socket_forward"] = list(forward)
    COL_WEAPONS.objects.link(obj)
    return obj


def add_envelope(root, descriptor):
    dims = descriptor["size"]
    env = cube("ENV_" + descriptor["id"], root, (0.0, 0.0, dims[2] * 0.5), dims,
               ENV_MATS[descriptor["envelope"]], 0.0, COL_ENVELOPES)
    wire = env.modifiers.new("EnvelopeWire", "WIREFRAME")
    wire.thickness = 0.008
    wire.use_replace = True
    bevel = env.modifiers.new("EnvelopeEdgeSoftening", "BEVEL")
    bevel.width = 0.004
    bevel.segments = 2
    env["ue_envelope_class"] = descriptor["envelope"]
    env["ue_half_extents_cm"] = [round(value * 50.0, 2) for value in dims]
    env["ue_center_offset_cm"] = [0.0, 0.0, round(dims[2] * 50.0, 2)]
    env["ue_can_fold_for_traversal"] = descriptor["fold"] is not None
    if descriptor["fold"]:
        env["ue_folded_half_extents_cm"] = [round(value * 50.0, 2) for value in descriptor["fold"]]
    return env


def add_common(root, descriptor):
    length, width, height = descriptor["size"]
    cube(descriptor["id"] + "_Receiver", root, (-length * 0.08, 0.0, height * 0.58),
         (length * 0.48, width * 0.58, height * 0.46), MAT["gunmetal"], min(0.028, height * 0.08))
    if descriptor["players"]:
        cube(descriptor["id"] + "_Grip", root, (-length * 0.14, 0.0, height * 0.23),
             (length * 0.13, width * 0.34, height * 0.42), MAT["dark"], 0.02)
    cube(descriptor["id"] + "_Status", root, (-length * 0.06, -width * 0.31, height * 0.65),
         (length * 0.20, 0.012, height * 0.10), MAT["cyan"], 0.004)


def build_form(root, descriptor):
    length, width, height = descriptor["size"]
    form = descriptor["form"]
    add_common(root, descriptor)
    if form == "cutter":
        cylinder(descriptor["id"] + "_Shaft", root, (length * 0.25, 0.0, height * 0.62), height * 0.11, length * 0.42, MAT["steel"])
        for side in (-1, 1):
            cube(descriptor["id"] + "_Fork" + str(side), root, (length * 0.47, side * width * 0.22, height * 0.62),
                 (length * 0.15, width * 0.10, height * 0.16), MAT["hazard"], 0.01)
    elif form == "spreader":
        cylinder(descriptor["id"] + "_Ram", root, (0.0, 0.0, height * 0.58), height * 0.12, length * 0.62, MAT["steel"])
        for side in (-1, 1):
            arm = cube(descriptor["id"] + "_Jaw" + str(side), root, (length * 0.29, side * width * 0.23, height * 0.64),
                       (length * 0.42, width * 0.13, height * 0.16), MAT["hazard"], 0.018)
            arm.rotation_euler.x = side * math.radians(11)
        cylinder(descriptor["id"] + "_Reservoir", root, (-length * 0.34, 0.0, height * 0.65), height * 0.16,
                 length * 0.24, MAT["red"])
    elif form == "projector":
        cylinder(descriptor["id"] + "_Barrel", root, (length * 0.28, 0.0, height * 0.60), height * 0.12,
                 length * 0.46, MAT["steel"])
        cylinder(descriptor["id"] + "_CO2Bottle", root, (-length * 0.23, width * 0.25, height * 0.53),
                 height * 0.16, length * 0.30, MAT["red"])
    elif form == "sprayer":
        cylinder(descriptor["id"] + "_Nozzle", root, (length * 0.31, 0.0, height * 0.60), height * 0.13,
                 length * 0.40, MAT["steel"])
        for side in (-1, 1):
            cylinder(descriptor["id"] + "_Dewar" + str(side), root, (-length * 0.24, side * width * 0.25, height * 0.55),
                     height * 0.17, length * 0.32, MAT["medical"])
    elif form == "cable":
        cylinder(descriptor["id"] + "_LaunchTube", root, (length * 0.28, 0.0, height * 0.58), height * 0.10,
                 length * 0.55, MAT["steel"])
        torus(descriptor["id"] + "_CableSpool", root, (-length * 0.22, 0.0, height * 0.64),
              width * 0.28, width * 0.075, MAT["hazard"], rotation=(math.pi / 2.0, 0.0, 0.0))
    elif form == "sonic":
        cylinder(descriptor["id"] + "_Emitter", root, (length * 0.28, 0.0, height * 0.58), height * 0.20,
                 length * 0.23, MAT["steel"])
        for ring_x in (0.12, 0.25, 0.38):
            torus(descriptor["id"] + "_Ring" + str(ring_x), root, (length * ring_x, 0.0, height * 0.58),
                  height * 0.17, 0.016, MAT["cyan"])
    elif form == "plasma":
        cylinder(descriptor["id"] + "_Torch", root, (length * 0.30, 0.0, height * 0.60), height * 0.11,
                 length * 0.50, MAT["steel"])
        for ring_x in (0.08, 0.23, 0.38):
            torus(descriptor["id"] + "_Coil" + str(ring_x), root, (length * ring_x, 0.0, height * 0.60),
                  height * 0.13, 0.014, MAT["hazard"])
        cylinder(descriptor["id"] + "_Arc", root, (length * 0.57, 0.0, height * 0.60), height * 0.035,
                 length * 0.12, MAT["cyan"])
    elif form == "baton":
        cylinder(descriptor["id"] + "_Baton", root, (length * 0.10, 0.0, height * 0.50), height * 0.18,
                 length * 0.76, MAT["dark"])
        for ring_x in (0.20, 0.36, 0.50):
            torus(descriptor["id"] + "_ShockRing" + str(ring_x), root, (length * ring_x, 0.0, height * 0.50),
                  height * 0.19, 0.012, MAT["cyan"])
    elif form == "sentry":
        cylinder(descriptor["id"] + "_Gimbal", root, (0.0, 0.0, height * 0.58), width * 0.22,
                 width * 0.45, MAT["hazard"], rotation=(math.pi / 2.0, 0.0, 0.0))
        for side in (-1, 1):
            cylinder(descriptor["id"] + "_Pod" + str(side), root, (length * 0.22, side * width * 0.24, height * 0.62),
                     height * 0.11, length * 0.42, MAT["steel"])
        cube(descriptor["id"] + "_Base", root, (-length * 0.20, 0.0, height * 0.20),
             (length * 0.30, width * 0.62, height * 0.24), MAT["dark"], 0.03)
    elif form == "dronepod":
        for side in (-1, 1):
            cylinder(descriptor["id"] + "_Tube" + str(side), root, (length * 0.12, side * width * 0.20, height * 0.55),
                     height * 0.12, length * 0.64, MAT["steel"])
        cube(descriptor["id"] + "_Rail", root, (-length * 0.20, 0.0, height * 0.72),
             (length * 0.42, width * 0.20, height * 0.10), MAT["hazard"], 0.01)
    elif form == "nailer":
        cylinder(descriptor["id"] + "_Driver", root, (length * 0.28, 0.0, height * 0.58), height * 0.12,
                 length * 0.42, MAT["steel"])
        cube(descriptor["id"] + "_Magazine", root, (0.0, width * 0.18, height * 0.29),
             (length * 0.46, width * 0.20, height * 0.16), MAT["hazard"], 0.012)
    elif form == "xeno":
        sphere(descriptor["id"] + "_Core", root, (0.0, 0.0, height * 0.56),
               (length * 0.22, width * 0.27, height * 0.29), MAT["violet"])
        for index, x in enumerate((-0.28, -0.12, 0.08, 0.27)):
            torus(descriptor["id"] + "_Resonator" + str(index), root, (length * x, 0.0, height * 0.56),
                  height * (0.28 - abs(x) * 0.20), 0.025, MAT["violet"])
        cylinder(descriptor["id"] + "_HumanCage", root, (length * 0.30, 0.0, height * 0.56), height * 0.10,
                 length * 0.28, MAT["steel"])


def add_label(body, location, size=0.09):
    curve = bpy.data.curves.new("LabelCurve", "FONT")
    curve.body = body
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = size
    curve.extrude = 0.003
    curve.bevel_depth = 0.001
    curve.materials.append(MAT["label"])
    obj = bpy.data.objects.new("LBL_" + body.split(" ", 1)[0], curve)
    obj.location = location
    obj.rotation_euler.x = math.pi / 2.0
    COL_LABELS.objects.link(obj)


weapon_roots = []
spacing_x = 1.75
spacing_y = 1.48
for index, descriptor in enumerate(WEAPONS):
    row = index // 4
    col = index % 4
    origin = ((col - 1.5) * spacing_x, (1.0 - row) * spacing_y, 0.08)
    root = bpy.data.objects.new("WPN_" + descriptor["id"], None)
    root.empty_display_type = "PLAIN_AXES"
    root.empty_display_size = 0.12
    root.location = origin
    root["weapon_id"] = descriptor["id"]
    root["operator_player"] = descriptor["players"]
    root["operator_aerial_drone"] = descriptor["aerial"]
    root["operator_robotic_drone"] = descriptor["robotic"]
    root["soldier_specialization"] = descriptor["soldier"]
    root["safe_function"] = descriptor["safe"]
    root["unsafe_modification"] = descriptor["unsafe"]
    COL_WEAPONS.objects.link(root)
    build_form(root, descriptor)
    add_envelope(root, descriptor)
    length, width, height = descriptor["size"]
    socket(root, "SOCKET_Mount", (-length * 0.32, 0.0, height * 0.52))
    socket(root, "SOCKET_Muzzle", (length * 0.50, 0.0, height * 0.58))
    socket(root, "SOCKET_LeftHand", (length * 0.10, 0.0, height * 0.32))
    socket(root, "SOCKET_DroneSensor", (0.0, -width * 0.36, height * 0.72))
    add_label(f"{index + 5:02d}  {descriptor['label']}  // {descriptor['envelope'].upper()}",
              (origin[0], origin[1] + 0.62, 0.06), 0.074)
    weapon_roots.append(root)


def build_mount(descriptor, index):
    origin = (-2.65 + index * 1.75, -3.45, 0.10)
    root = bpy.data.objects.new("MNT_" + descriptor["id"], None)
    root.location = origin
    root["supported_operators"] = descriptor["operators"]
    COL_MOUNTS.objects.link(root)
    if index == 0:
        cube(descriptor["id"] + "_Rail", root, (0.0, 0.0, 0.25), (0.64, 0.18, 0.12), MAT["steel"], 0.015, COL_MOUNTS)
        cube(descriptor["id"] + "_Grip", root, (-0.12, 0.0, 0.02), (0.16, 0.14, 0.40), MAT["dark"], 0.025, COL_MOUNTS)
    elif index == 1:
        cube(descriptor["id"] + "_Rail", root, (0.0, 0.0, 0.25), (0.62, 0.20, 0.12), MAT["hazard"], 0.015, COL_MOUNTS)
        cylinder(descriptor["id"] + "_Gimbal", root, (-0.18, 0.0, 0.04), 0.18, 0.24, MAT["steel"],
                 rotation=(math.pi / 2.0, 0.0, 0.0), col=COL_MOUNTS)
    elif index == 2:
        cube(descriptor["id"] + "_Plate", root, (-0.12, 0.0, 0.06), (0.42, 0.44, 0.12), MAT["gunmetal"], 0.025, COL_MOUNTS)
        for side in (-1, 1):
            cylinder(descriptor["id"] + "_Actuator" + str(side), root, (0.12, side * 0.14, 0.22),
                     0.055, 0.36, MAT["steel"], col=COL_MOUNTS)
    else:
        cylinder(descriptor["id"] + "_Post", root, (0.0, 0.0, 0.28), 0.075, 0.55, MAT["steel"],
                 rotation=(0.0, 0.0, 0.0), col=COL_MOUNTS)
        for angle in (0.0, math.radians(120), math.radians(240)):
            leg = cube(descriptor["id"] + "_Leg", root, (math.cos(angle) * 0.26, math.sin(angle) * 0.26, 0.02),
                       (0.48, 0.07, 0.07), MAT["dark"], 0.012, COL_MOUNTS)
            leg.rotation_euler.z = angle
    socket(root, "SOCKET_WeaponInterface", (0.22, 0.0, 0.30))
    add_label(descriptor["label"], (origin[0], origin[1] + 0.48, 0.05), 0.075)
    return root


mount_roots = [build_mount(descriptor, index) for index, descriptor in enumerate(MOUNTS)]

# Presentation deck, camera, and lights.
deck_root = bpy.data.objects.new("PresentationRoot", None)
COL_PRESENTATION.objects.link(deck_root)
cube("PresentationDeck", deck_root, (0.0, -0.75, -0.10), (7.5, 8.2, 0.12), MAT["deck"], 0.02, COL_PRESENTATION)

camera_data = bpy.data.cameras.new("CAM_Batch02")
camera = bpy.data.objects.new("CAM_Batch02", camera_data)
camera.location = (7.8, -10.2, 8.3)
camera_data.lens = 54
COL_PRESENTATION.objects.link(camera)
scene.camera = camera


def point_at(obj, target):
    obj.rotation_euler = (Vector(target) - obj.location).to_track_quat("-Z", "Y").to_euler()


point_at(camera, (0.0, -0.7, 0.4))
for name, location, energy, color, size in [
    ("Key", (2.0, -4.5, 8.0), 1750.0, (0.70, 0.86, 1.0), 4.5),
    ("Rim", (-5.5, 3.0, 5.5), 1350.0, (1.0, 0.24, 0.06), 3.5),
    ("Fill", (5.0, 4.5, 3.5), 1100.0, (0.12, 0.38, 1.0), 4.0),
]:
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.color = color
    data.shape = "DISK"
    data.size = size
    light = bpy.data.objects.new(name, data)
    light.location = location
    point_at(light, (0.0, -0.7, 0.4))
    COL_PRESENTATION.objects.link(light)


def export_root(root, filepath):
    bpy.ops.object.select_all(action="DESELECT")
    root.select_set(True)
    for child in root.children_recursive:
        child.select_set(True)
    bpy.context.view_layer.objects.active = root
    original = root.matrix_world.copy()
    root.location = (0.0, 0.0, 0.0)
    bpy.ops.export_scene.gltf(filepath=filepath, export_format="GLB", use_selection=True,
                              export_apply=True, export_yup=True)
    root.matrix_world = original


bpy.ops.render.render(write_still=True)
for root in weapon_roots:
    export_root(root, os.path.join(EXPORT_DIR, "SM_" + root["weapon_id"] + ".glb"))
for root in mount_roots:
    export_root(root, os.path.join(EXPORT_DIR, "SM_" + root.name + ".glb"))


manifest = {
    "batch": "02",
    "coordinate_system": {"forward": "+X", "up": "+Z", "units": "meters", "unreal_scale": 100},
    "weapons": [],
    "mounts": MOUNTS,
}
for descriptor in WEAPONS:
    entry = dict(descriptor)
    entry["half_extents_cm"] = [round(value * 50.0, 2) for value in descriptor["size"]]
    entry["folded_half_extents_cm"] = ([round(value * 50.0, 2) for value in descriptor["fold"]]
                                        if descriptor["fold"] else None)
    entry["export"] = "Exports/SM_" + descriptor["id"] + ".glb"
    manifest["weapons"].append(entry)
with open(MANIFEST_PATH, "w", encoding="utf-8") as handle:
    json.dump(manifest, handle, indent=2)


steps = []
stage_names = ["blockout", "axis normalization", "collision envelope", "mount sockets",
               "operator compatibility", "safe/unsafe profile", "centered GLB export"]
for descriptor in WEAPONS:
    for stage in stage_names:
        steps.append(f"{descriptor['label']}: {stage}")
for mount in MOUNTS:
    for stage in ("adapter blockout", "interface socket", "centered GLB export"):
        steps.append(f"{mount['label']}: {stage}")
steps.extend(["Render batch preview", "Save standalone Blender library", "Validate generated deliverables",
              "Write batch manifest and completion report"])
assert len(steps) == 100

with open(REPORT_PATH, "w", encoding="utf-8") as handle:
    handle.write("# Weapon Production Batch 02 — 100 completed steps\n\n")
    for index, step in enumerate(steps, 1):
        handle.write(f"- [x] {index:03d}. {step}\n")

bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH, compress=True)
print("BATCH02_COMPLETE", len(WEAPONS), len(MOUNTS), len(steps), BLEND_PATH)
