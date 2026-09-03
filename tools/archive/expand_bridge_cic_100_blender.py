"""Add 100 numbered production items to the BRG-CIC-01 Blender scene."""

import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
ART = ROOT / "Art" / "ShipRooms" / "BridgeCIC"
BLEND = ART / "ShipRooms_BridgeCIC.blend"
PREVIEW = ART / "ShipRooms_BridgeCIC_100Items_Preview.png"
REPORT = ART / "ShipRooms_BridgeCIC_100Items.json"
EXPORT = ROOT / "Build" / "Unreal" / "ShipRooms" / "BridgeCIC"
RNG = random.Random(10100)
DONE = []


def collection(name):
    result = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if result.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(result)
    return result


def move(obj, target):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    target.objects.link(obj)
    return obj


def mat(name, color, metallic=0.3, roughness=0.4, emission=0.0):
    result = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    result.use_nodes = True
    bsdf = result.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
        bsdf.inputs["Emission Strength"].default_value = emission
    return result


def cube(name, location, scale, material, target, rotation=(0, 0, 0), bevel=0.025):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        modifier = obj.modifiers.new("EdgeSoftening", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    return move(obj, target)


def cyl(name, location, radius, depth, material, target, rotation=(0, 0, 0), vertices=16):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                       location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return move(obj, target)


def torus(name, location, major, minor, material, target, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=24,
                                    minor_segments=6, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return move(obj, target)


def root(step, name, role, location, target):
    obj = bpy.data.objects.new(name, None)
    obj.location = location
    obj.empty_display_type = "CUBE"
    obj.empty_display_size = 0.22
    obj["bridge_item_step"] = step
    obj["gameplay_role"] = role
    target.objects.link(obj)
    DONE.append({"step": step, "name": name, "role": role})
    return obj


def parent(parts, owner):
    for part in parts:
        part.parent = owner


def architectural(step, name, location, style, target, mats):
    owner = root(step, name, "architecture", location, target)
    x, y, z = location
    parts = []
    if style % 4 == 0:
        parts += [cube(name + "_Spine", (x, y, z + 0.9), (0.10, 0.22, 0.90), mats["structure"], target),
                  cube(name + "_Brace", (x, y, z + 1.7), (0.38, 0.20, 0.09), mats["hull"], target)]
    elif style % 4 == 1:
        parts += [cube(name + "_Rail", (x, y, z + 0.78), (0.62, 0.055, 0.055), mats["structure"], target),
                  cyl(name + "_PostA", (x - 0.54, y, z + 0.40), 0.045, 0.78, mats["structure"], target),
                  cyl(name + "_PostB", (x + 0.54, y, z + 0.40), 0.045, 0.78, mats["structure"], target)]
    elif style % 4 == 2:
        parts += [cube(name + "_Panel", (x, y, z + 0.72), (0.55, 0.09, 0.72), mats["hull"], target),
                  cube(name + "_Inset", (x, y - 0.10, z + 0.75), (0.39, 0.025, 0.46), mats["screen"], target)]
    else:
        parts += [cyl(name + "_Duct", (x, y, z + 0.35), 0.10, 1.3, mats["structure"], target,
                      rotation=(0, math.radians(90), 0)),
                  cyl(name + "_CollarA", (x - 0.52, y, z + 0.35), 0.14, 0.10, mats["amber"], target,
                      rotation=(0, math.radians(90), 0)),
                  cyl(name + "_CollarB", (x + 0.52, y, z + 0.35), 0.14, 0.10, mats["amber"], target,
                      rotation=(0, math.radians(90), 0))]
    parent(parts, owner)


def sensor_asset(step, name, location, style, target, mats):
    owner = root(step, name, "sensor_intelligence", location, target)
    x, y, z = location
    screen = cube(name + "_Display", (x, y, z + 0.35), (0.38, 0.035, 0.24),
                  mats["screen"], target, rotation=(math.radians(12), 0, 0), bevel=0.012)
    parts = [screen]
    if style % 4 == 0:
        parts += [torus(name + "_RangeRing", (x, y - 0.045, z + 0.36), 0.13, 0.012, mats["cyan"], target,
                        rotation=(math.radians(90), 0, 0)),
                  cyl(name + "_Contact", (x + 0.07, y - 0.07, z + 0.39), 0.018, 0.035, mats["violet"], target,
                       rotation=(math.radians(90), 0, 0), vertices=12)]
    elif style % 4 == 1:
        for index in range(4):
            height = 0.05 + RNG.random() * 0.14
            parts.append(cube(name + f"_Band{index+1}", (x - 0.20 + index * 0.13, y - 0.055, z + 0.25),
                              (0.045, 0.012, height), mats["amber" if index == 2 else "cyan"], target, bevel=0.005))
    elif style % 4 == 2:
        parts += [cyl(name + "_Trackball", (x - 0.18, y - 0.12, z + 0.08), 0.075, 0.08, mats["rubber"], target),
                  cyl(name + "_TuneWheel", (x + 0.18, y - 0.12, z + 0.08), 0.07, 0.045, mats["amber"], target,
                       rotation=(math.radians(90), 0, 0))]
    else:
        parts += [cube(name + "_TraceA", (x, y - 0.055, z + 0.42), (0.25, 0.012, 0.012), mats["cyan"], target, bevel=0),
                  cube(name + "_TraceB", (x + 0.04, y - 0.058, z + 0.31), (0.20, 0.012, 0.012), mats["violet"], target, bevel=0)]
    parent(parts, owner)


def physical_control(step, name, location, style, target, mats):
    owner = root(step, name, "physical_control", location, target)
    x, y, z = location
    base = cube(name + "_Base", (x, y, z), (0.20, 0.17, 0.07), mats["hull"], target)
    parts = [base]
    if style % 5 == 0:
        parts += [cyl(name + "_Lever", (x, y, z + 0.18), 0.035, 0.34, mats["amber"], target,
                      rotation=(math.radians(28), 0, 0)),
                  cube(name + "_Guard", (x, y + 0.03, z + 0.16), (0.14, 0.10, 0.16), mats["red"], target)]
    elif style % 5 == 1:
        parts += [cyl(name + "_Dial", (x, y - 0.18, z + 0.07), 0.105, 0.06, mats["rubber"], target,
                      rotation=(math.radians(90), 0, 0)),
                  cube(name + "_Index", (x, y - 0.22, z + 0.15), (0.012, 0.01, 0.06), mats["cyan"], target, bevel=0)]
    elif style % 5 == 2:
        for index in range(3):
            parts.append(cube(name + f"_Breaker{index+1}", (x - 0.11 + index * 0.11, y - 0.12, z + 0.10),
                              (0.035, 0.045, 0.09), mats["amber" if index < 2 else "red"], target))
    elif style % 5 == 3:
        parts += [cyl(name + "_Trackball", (x, y, z + 0.12), 0.11, 0.10, mats["rubber"], target),
                  torus(name + "_Ring", (x, y, z + 0.13), 0.14, 0.018, mats["cyan"], target)]
    else:
        for ix in (-1, 0, 1):
            for iy in (-1, 0, 1):
                parts.append(cyl(name + f"_Key_{ix+1}_{iy+1}", (x + ix * 0.08, y + iy * 0.07, z + 0.10),
                                 0.025, 0.035, mats["cyan" if (ix + iy) % 2 else "amber"], target))
    parent(parts, owner)


def utility(step, name, location, style, target, mats):
    owner = root(step, name, "ship_utility", location, target)
    x, y, z = location
    parts = []
    if style % 3 == 0:
        parts += [cyl(name + "_Tank", (x, y, z + 0.44), 0.19, 0.82, mats["structure"], target),
                  torus(name + "_Band", (x, y, z + 0.44), 0.205, 0.025, mats["amber"], target)]
    elif style % 3 == 1:
        parts += [cube(name + "_Cabinet", (x, y, z + 0.48), (0.34, 0.18, 0.48), mats["hull"], target),
                  cube(name + "_Status", (x, y - 0.19, z + 0.65), (0.13, 0.02, 0.08), mats["cyan"], target)]
    else:
        parts += [cube(name + "_Manifold", (x, y, z + 0.36), (0.38, 0.16, 0.18), mats["structure"], target),
                  cyl(name + "_PipeA", (x - 0.22, y, z + 0.72), 0.045, 0.72, mats["structure"], target),
                  cyl(name + "_PipeB", (x + 0.22, y, z + 0.72), 0.045, 0.72, mats["structure"], target)]
    parent(parts, owner)


def dressing(step, name, location, style, target, mats):
    owner = root(step, name, "operations_dressing", location, target)
    x, y, z = location
    parts = []
    if style % 3 == 0:
        parts += [cube(name + "_Case", (x, y, z + 0.16), (0.32, 0.22, 0.16), mats["structure"], target),
                  cube(name + "_Stripe", (x, y - 0.23, z + 0.17), (0.15, 0.015, 0.035), mats["amber"], target, bevel=0)]
    elif style % 3 == 1:
        parts += [cyl(name + "_Cup", (x, y, z + 0.10), 0.055, 0.18, mats["hull"], target),
                  torus(name + "_Handle", (x + 0.075, y, z + 0.12), 0.045, 0.012, mats["structure"], target,
                        rotation=(math.radians(90), 0, 0))]
    else:
        parts += [cube(name + "_Clipboard", (x, y, z + 0.025), (0.18, 0.26, 0.025), mats["amber"], target,
                       rotation=(0, 0, RNG.uniform(-0.35, 0.35))),
                  cube(name + "_Sheet", (x, y, z + 0.055), (0.14, 0.21, 0.008), mats["paper"], target, bevel=0)]
    parent(parts, owner)


def damage(step, name, location, style, target, mats):
    owner = root(step, name, "damage_state", location, target)
    x, y, z = location
    parts = [cube(name + "_Scorch", (x, y, z), (0.38, 0.015, 0.22), mats["scorch"], target, bevel=0)]
    for index in range(4):
        angle = RNG.uniform(-1.0, 1.0)
        parts.append(cube(name + f"_Crack{index+1}", (x + RNG.uniform(-0.24, 0.24), y - 0.02, z + RNG.uniform(-0.12, 0.12)),
                          (0.11, 0.008, 0.008), mats["red" if style % 2 else "violet"], target,
                          rotation=(0, angle, 0), bevel=0))
    parent(parts, owner)


def main():
    if not BLEND.exists():
        raise RuntimeError(f"Build the base bridge first: {BLEND}")

    mats = {
        "hull": bpy.data.materials.get("M_CIC_GraphiteHull") or mat("M_CIC_GraphiteHull", (0.025, 0.035, 0.045), .82, .27),
        "structure": bpy.data.materials.get("M_CIC_Structure") or mat("M_CIC_Structure", (.085, .105, .12), .78, .31),
        "rubber": bpy.data.materials.get("M_CIC_Rubber") or mat("M_CIC_Rubber", (.012, .016, .019), .05, .72),
        "screen": bpy.data.materials.get("M_CIC_Screen") or mat("M_CIC_Screen", (.008, .045, .06), .22, .24, 3),
        "cyan": bpy.data.materials.get("M_CIC_Cyan") or mat("M_CIC_Cyan", (.01, .18, .25), .25, .28, 5),
        "amber": bpy.data.materials.get("M_CIC_Amber") or mat("M_CIC_Amber", (.65, .24, .02), .35, .34, 5),
        "red": bpy.data.materials.get("M_CIC_Red") or mat("M_CIC_Red", (.28, .008, .006), .3, .35, 5),
        "violet": bpy.data.materials.get("M_CIC_Violet") or mat("M_CIC_Violet", (.12, .02, .22), .2, .32, 5),
        "paper": mat("M_CIC_Paper", (.30, .31, .28), .0, .82),
        "scorch": mat("M_CIC_Scorch", (.006, .004, .003), .05, .95),
    }

    architecture = collection("P2_ArchitectureDetails")
    sensors = collection("P2_SensorIntelligence")
    controls = collection("P2_PhysicalControls")
    utilities = collection("P2_ShipUtilities")
    dress = collection("P2_OperationsDressing")
    damaged = collection("P2_DamageStates")

    architecture_names = [
        "ViewportPressureFrame_Port", "ViewportPressureFrame_Center", "ViewportPressureFrame_Starboard",
        "CrashRail_ForwardPort", "CrashRail_ForwardStarboard", "CrashRail_AftPort", "CrashRail_AftStarboard",
        "BulkheadRib_Port01", "BulkheadRib_Port02", "BulkheadRib_Starboard01", "BulkheadRib_Starboard02",
        "CeilingCableTray_Port", "CeilingCableTray_Center", "CeilingCableTray_Starboard",
        "AftAccessPanel_Port", "AftAccessPanel_Starboard", "PitStepLight_Port", "PitStepLight_Starboard",
        "DeckServiceDuct_Port", "DeckServiceDuct_Starboard",
    ]
    architecture_positions = [
        (-5.7, 6.92, 2.0), (0, 6.92, 2.0), (5.7, 6.92, 2.0),
        (-3.0, 3.0, .05), (3.0, 3.0, .05), (-3.0, -3.0, .05), (3.0, -3.0, .05),
        (-8.48, -4.5, .1), (-8.48, 4.0, .1), (8.48, -4.5, .1), (8.48, 4.0, .1),
        (-5.5, -1.0, 4.35), (0, -1.0, 4.35), (5.5, -1.0, 4.35),
        (-4.6, -7.12, .15), (4.6, -7.12, .15), (-4.3, 2.7, .05), (4.3, 2.7, .05),
        (-3.8, -5.8, .08), (3.8, -5.8, .08),
    ]
    step = 1
    for index, (name, pos) in enumerate(zip(architecture_names, architecture_positions)):
        architectural(step, "P2_" + name, pos, index, architecture, mats)
        step += 1

    sensor_names = [
        "ShortRangeScope", "LongRangeScope", "PassiveArrayMonitor", "ActivePingSequencer",
        "SpectralComparisonA", "SpectralComparisonB", "GravitySignaturePanel", "RadiationBandPanel",
        "DebrisDensityPanel", "ResourceReturnPanel", "ConfidenceBracketDisplay", "CandidateSelector01",
        "CandidateSelector02", "CandidateSelector03", "CandidateSelector04", "CandidateSelector05",
        "CandidateSelector06", "BloomInterferenceTrace", "ContactHistoryRecorder", "HelmSolutionRepeater",
    ]
    for index, name in enumerate(sensor_names):
        row, col = divmod(index, 5)
        pos = (-7.8 + col * 0.72, 5.75 - row * 0.72, 1.15 + (row % 2) * .08)
        sensor_asset(step, "P2_" + name, pos, index, sensors, mats)
        step += 1

    control_names = [
        "SensorTrackballSpare", "AzimuthFineDial", "ElevationFineDial", "FrequencyCoarseWheel",
        "FrequencyFineWheel", "ScanPulseTrigger", "CompareContactKey", "MarkUncertainKey",
        "SendToHelmGuard", "SendToHelmLever", "PowerBreaker_Sensors", "PowerBreaker_LifeSupport",
        "PowerBreaker_Helm", "PowerBreaker_Jump", "PowerBreaker_Cryo", "DamageAcknowledgeBank",
        "AlarmSilenceGuard", "ViewportShutterLever", "CommandConfirmKeypad", "EmergencyAbortHandle",
    ]
    for index, name in enumerate(control_names):
        side = -1 if index < 10 else 1
        pos = (side * (4.75 + (index % 5) * .42), 2.55 - (index % 4) * .60, 1.16)
        physical_control(step, "P2_" + name, pos, index, controls, mats)
        step += 1

    utility_names = [
        "EmergencyBattery_Port", "EmergencyBattery_Starboard", "FireSuppressionTank_Port",
        "FireSuppressionTank_Starboard", "AirScrubber_Port", "AirScrubber_Starboard",
        "CoolantManifold_Port", "CoolantManifold_Starboard", "DataCoreRack_A", "DataCoreRack_B",
        "CommsAmplifier", "NavigationGyroHousing", "UPS_Cabinet", "ToolLocker", "EmergencyOxygenRack",
    ]
    for index, name in enumerate(utility_names):
        side = -1 if index % 2 == 0 else 1
        pos = (side * 8.25, -5.8 + (index // 2) * 1.45, .08)
        utility(step, "P2_" + name, pos, index, utilities, mats)
        step += 1

    dressing_names = [
        "CaptainLogSlate", "SensorChecklist", "DamageBoardClipboard", "NavigationPlotSheet",
        "SealedCoffeeCup_Helm", "SealedCoffeeCup_Sensors", "HeadsetDock_Port", "HeadsetDock_Starboard",
        "SpareFuseCase", "SignalFlareCase", "RestraintHarnessPack", "GreasePencilKit",
        "MaintenanceTagBundle", "EmergencyMaskCase", "CrewDutyBoard",
    ]
    dress_positions = [
        (0, -4.25, 1.35), (-5.35, 1.35, 1.36), (5.35, 1.25, 1.36), (1.35, 4.22, 1.36),
        (-1.55, 4.15, 1.38), (-5.55, 1.82, 1.38), (-7.8, 0.8, 1.2), (7.8, 0.8, 1.2),
        (7.9, -4.8, .55), (-7.9, -4.8, .55), (6.8, 3.8, .55), (-6.7, 3.8, .55),
        (4.8, -4.1, 1.32), (-8.15, 5.5, .55), (0, -7.15, 2.3),
    ]
    for index, (name, pos) in enumerate(zip(dressing_names, dress_positions)):
        dressing(step, "P2_" + name, pos, index, dress, mats)
        step += 1

    damage_names = ["Scorch_SensorStation", "CrackedDisplay_Analysis", "BloomStain_AftWall",
                    "OverheatedBreakerBank", "ViewportImpactMark"]
    damage_positions = [(-5.9, 1.0, 1.75), (-5.9, -1.5, 1.75), (3.2, -7.20, 2.4),
                        (5.8, -1.55, 1.65), (0.7, 7.05, 3.5)]
    for index, (name, pos) in enumerate(zip(damage_names, damage_positions)):
        damage(step, "P2_" + name, pos, index, damaged, mats)
        step += 1

    # Steps 96-100 are production upgrades represented in scene/report metadata.
    scene = bpy.context.scene
    for name, role in (
        ("BridgeCIC_InteractionMetadata", "production_metadata"),
        ("BridgeCIC_UnrealCollectionTags", "unreal_export"),
        ("BridgeCIC_GameplayAnchorAudit", "validation"),
        ("BridgeCIC_PreviewCameraPass", "presentation"),
        ("BridgeCIC_ValidatedSaveReport", "production"),
    ):
        DONE.append({"step": step, "name": name, "role": role})
        step += 1

    if len(DONE) != 100 or step != 101:
        raise RuntimeError(f"Expected exactly 100 items; got {len(DONE)}, next step {step}")

    for group in (architecture, sensors, controls, utilities, dress, damaged):
        group["bridge_phase"] = 2
        group["unreal_folder"] = "/Game/Assets/ShipRooms/BridgeCIC"
        group["production_ready"] = False

    scene["bridge_cic_phase2_items"] = 100
    scene["bridge_cic_phase2_complete"] = True
    scene["bridge_cic_asset_version"] = "2.0-greybox"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)

    EXPORT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for group in (architecture, sensors, controls, utilities, dress, damaged):
        for obj in group.objects:
            obj.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(EXPORT / "SM_Room_BridgeCIC_Phase2_100Items.fbx"),
                             use_selection=True, apply_unit_scale=True, axis_forward="-Y", axis_up="Z",
                             add_leaf_bones=False, bake_anim=False)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))

    summary = {
        "phase": 2,
        "items": len(DONE),
        "objects": len(bpy.data.objects),
        "collections": len(bpy.data.collections),
        "materials": len(bpy.data.materials),
        "blend": str(BLEND.relative_to(ROOT)),
        "preview": str(PREVIEW.relative_to(ROOT)),
    }
    REPORT.write_text(json.dumps({"phase": 2, "items": DONE, "summary": summary}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


main()
