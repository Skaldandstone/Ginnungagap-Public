"""Phase four: 750 instanced, station-focused production steps for BRG-CIC-01."""

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
PREVIEW = ART / "ShipRooms_BridgeCIC_Phase4_750Steps_Preview.png"
REPORT = ART / "ShipRooms_BridgeCIC_Phase4_750Steps.json"
EXPORT = ROOT / "Build" / "Unreal" / "ShipRooms" / "BridgeCIC"
RNG = random.Random(40750)
DONE = []


def replace_collection(name):
    old = bpy.data.collections.get(name)
    if old:
        for obj in list(old.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
    result = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(result)
    return result


def material(name, color, metallic=.25, roughness=.45, emission=0):
    result = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    result.use_nodes = True
    bsdf = result.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*color, 1)
        bsdf.inputs["Emission Strength"].default_value = emission
    return result


def prototype_cube(name, dimensions, mat):
    bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    mesh = obj.data
    mesh.name = name + "_Mesh"
    bpy.data.objects.remove(obj, do_unlink=True)
    return mesh


def prototype_cylinder(name, radius, depth, mat, vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    mesh = obj.data
    mesh.name = name + "_Mesh"
    bpy.data.objects.remove(obj, do_unlink=True)
    return mesh


def instance(step, name, role, pos, rot, scale, mesh, target, metadata=None):
    obj = bpy.data.objects.new(name, mesh)
    obj.location = pos
    obj.rotation_euler = rot
    obj.scale = scale
    obj["bridge_phase4_step"] = step
    obj["gameplay_role"] = role
    obj["linked_instance"] = True
    if metadata:
        for key, value in metadata.items():
            obj[key] = value
    target.objects.link(obj)
    DONE.append({"step": step, "name": name, "role": role})
    return obj


def marker(step, name, role, pos, target, metadata=None):
    obj = bpy.data.objects.new(name, None)
    obj.location = pos
    obj.empty_display_type = "ARROWS"
    obj.empty_display_size = .16
    obj["bridge_phase4_step"] = step
    obj["gameplay_role"] = role
    if metadata:
        for key, value in metadata.items():
            obj[key] = value
    target.objects.link(obj)
    DONE.append({"step": step, "name": name, "role": role})
    return obj


STATIONS = (
    ("SensorAcquisition", Vector((-5.35, 1.55, 1.36)), math.radians(90)),
    ("ContactAnalysis", Vector((-5.35, -1.60, 1.36)), math.radians(90)),
    ("PowerRouting", Vector((5.35, -1.60, 1.36)), math.radians(-90)),
    ("DamageControl", Vector((5.35, 1.55, 1.36)), math.radians(-90)),
    ("Helm", Vector((-1.65, 4.30, 1.36)), 0),
    ("Navigation", Vector((1.65, 4.30, 1.36)), 0),
    ("Command", Vector((0, -4.30, 1.48)), math.pi),
    ("TacticalTable", Vector((0, 0, 1.08)), 0),
)


def station_point(index, radius=.65, z=.0):
    station_name, center, facing = STATIONS[index % len(STATIONS)]
    ring = index // len(STATIONS)
    angle = facing + (ring % 9 - 4) * .13
    distance = radius + (ring % 4) * .13
    point = center + Vector((math.cos(angle) * distance, math.sin(angle) * distance, z + (ring % 3) * .09))
    return station_name, point, facing


def wall_point(index, count):
    phase = index / count * 4
    z = .55 + (index % 6) * .63
    if phase < 1:
        return Vector((-8.15 + phase * 16.3, -6.95, z)), 0
    if phase < 2:
        return Vector((8.15, -6.95 + (phase - 1) * 13.7, z)), math.radians(90)
    if phase < 3:
        return Vector((8.15 - (phase - 2) * 16.3, 6.80, z)), math.pi
    return Vector((-8.15, 6.80 - (phase - 3) * 13.7, z)), math.radians(-90)


def main():
    if not BLEND.exists():
        raise RuntimeError(f"Missing bridge scene: {BLEND}")

    mats = {
        "hull": bpy.data.materials.get("M_CIC_GraphiteHull") or material("M_CIC_GraphiteHull", (.025, .035, .045), .82, .27),
        "structure": bpy.data.materials.get("M_CIC_Structure") or material("M_CIC_Structure", (.085, .105, .12), .78, .31),
        "rubber": bpy.data.materials.get("M_CIC_Rubber") or material("M_CIC_Rubber", (.012, .016, .019), .05, .72),
        "cyan": bpy.data.materials.get("M_CIC_Cyan") or material("M_CIC_Cyan", (.01, .18, .25), .25, .28, 4),
        "amber": bpy.data.materials.get("M_CIC_Amber") or material("M_CIC_Amber", (.65, .24, .02), .35, .34, 4),
        "red": bpy.data.materials.get("M_CIC_Red") or material("M_CIC_Red", (.28, .008, .006), .3, .35, 4),
        "violet": bpy.data.materials.get("M_CIC_Violet") or material("M_CIC_Violet", (.12, .02, .22), .2, .32, 4),
    }

    meshes = {
        "panel": prototype_cube("P4_PROTO_Panel", (.46, .08, .28), mats["hull"]),
        "screen": prototype_cube("P4_PROTO_Screen", (.30, .035, .18), mats["cyan"]),
        "status_amber": prototype_cube("P4_PROTO_StatusAmber", (.10, .025, .04), mats["amber"]),
        "status_red": prototype_cube("P4_PROTO_StatusRed", (.10, .025, .04), mats["red"]),
        "status_violet": prototype_cube("P4_PROTO_StatusViolet", (.10, .025, .04), mats["violet"]),
        "key": prototype_cube("P4_PROTO_Key", (.045, .045, .030), mats["amber"]),
        "breaker": prototype_cube("P4_PROTO_Breaker", (.07, .08, .15), mats["red"]),
        "dial": prototype_cylinder("P4_PROTO_Dial", .055, .045, mats["rubber"]),
        "pipe": prototype_cylinder("P4_PROTO_Pipe", .025, .60, mats["structure"], 10),
        "brace": prototype_cube("P4_PROTO_Brace", (.10, .16, .70), mats["structure"]),
        "crate": prototype_cube("P4_PROTO_Crate", (.36, .26, .20), mats["structure"]),
        "slate": prototype_cube("P4_PROTO_Slate", (.22, .16, .018), mats["cyan"]),
        "damage": prototype_cube("P4_PROTO_Damage", (.26, .012, .15), mats["violet"]),
        "light": prototype_cube("P4_PROTO_Light", (.28, .035, .055), mats["amber"]),
    }

    groups = {
        "integration": replace_collection("P4_StationIntegration_150"),
        "structure": replace_collection("P4_WallCeilingStructure_125"),
        "interaction": replace_collection("P4_InteractionStates_100"),
        "display": replace_collection("P4_DisplayPlates_100"),
        "ergonomics": replace_collection("P4_Ergonomics_75"),
        "conduits": replace_collection("P4_Conduits_75"),
        "emergency": replace_collection("P4_EmergencyBloom_50"),
        "optimization": replace_collection("P4_OptimizationValidation_50"),
        "presentation": replace_collection("P4_CameraLighting_25"),
    }

    step = 1
    # 150 deliberate station-integration modules.
    integration_types = ("Bezel", "WristRest", "StatusBank", "GuardRail", "CablePort", "TaskTray")
    for index in range(150):
        station_name, pos, facing = station_point(index, .35, -.12)
        kind = integration_types[index % len(integration_types)]
        mesh = meshes[("panel", "panel", "status_amber", "brace", "panel", "crate")[index % 6]]
        scale = (.70, .70, .70) if kind != "GuardRail" else (.45, .45, .85)
        instance(step, f"P4_INT_{index+1:03d}_{station_name}_{kind}", "station_integration", pos,
                 (0, 0, facing), scale, mesh, groups["integration"], {"station": station_name}); step += 1

    # 125 wall and ceiling structural details.
    structure_types = ("ArmorPlate", "Brace", "CableBracket", "PressureSeal", "VentBaffle")
    for index in range(125):
        pos, facing = wall_point(index, 125)
        kind = structure_types[index % len(structure_types)]
        mesh = meshes["brace" if index % 5 in (1, 2) else "panel"]
        instance(step, f"P4_STR_{index+1:03d}_{kind}", "wall_ceiling_structure", pos,
                 (0, 0, facing), (.75, .65, .75), mesh, groups["structure"]); step += 1

    # 100 stateful interaction objects around operational stations.
    state_names = ("Idle", "Focused", "Scanning", "Uncertain", "Confirmed", "Blocked", "Damaged", "Corrupted")
    control_names = ("Trackball", "TuneDial", "CompareKey", "Breaker", "CommitLever")
    for index in range(100):
        station_name, pos, facing = station_point(index + 31, .18, .02)
        state = state_names[index % len(state_names)]
        control_name = control_names[index % len(control_names)]
        mesh = meshes[("dial", "dial", "key", "breaker", "breaker")[index % 5]]
        instance(step, f"P4_STATE_{index+1:03d}_{station_name}_{control_name}_{state}", "interaction_state",
                 pos, (math.radians(90) if mesh == meshes["dial"] else 0, 0, facing), (.75, .75, .75), mesh,
                 groups["interaction"], {"station": station_name, "interaction_state": state}); step += 1

    # 100 device-bound display plates with semantic data roles.
    data_roles = ("Range", "Bearing", "Hazard", "Resource", "Confidence", "Trace", "Power", "Damage", "Route", "Crew")
    for index in range(100):
        station_name, pos, facing = station_point(index + 67, .58, .12)
        role = data_roles[index % len(data_roles)]
        mesh = meshes[("screen", "screen", "status_red", "status_amber", "status_amber",
                       "status_violet", "status_amber", "status_red", "screen", "screen")[index % 10]]
        instance(step, f"P4_DSP_{index+1:03d}_{station_name}_{role}", "display_plate", pos,
                 (math.radians(12), 0, facing), (.72, .72, .72), mesh, groups["display"],
                 {"station": station_name, "data_role": role, "device_bound": True}); step += 1

    # 75 ergonomics, reach, restraint and clearance markers.
    ergonomic_roles = ("ReachNear", "ReachFar", "EyeLine", "KneeClearance", "Harness", "Egress")
    for index in range(75):
        station_name, pos, facing = station_point(index + 13, .85, -.55)
        role = ergonomic_roles[index % len(ergonomic_roles)]
        marker(step, f"P4_ERGO_{index+1:03d}_{station_name}_{role}", "ergonomics", pos,
               groups["ergonomics"], {"station": station_name, "audit_type": role}); step += 1

    # 75 linked conduit runs and labeled endpoints.
    conduit_roles = ("Power", "Data", "Coolant", "Pneumatic", "Emergency")
    for index in range(75):
        pos, facing = wall_point(index + 9, 75)
        role = conduit_roles[index % len(conduit_roles)]
        instance(step, f"P4_CONDUIT_{index+1:03d}_{role}", "conduit", pos,
                 (0, math.radians(90), facing), (.75, .75, .75), meshes["pipe"], groups["conduits"],
                 {"service": role}); step += 1

    # 50 emergency and Bloom-response variants.
    emergency_roles = ("EmergencyLight", "BloomResidue", "Scorch", "QuarantineMarker", "PowerOutage")
    for index in range(50):
        pos, facing = wall_point(index + 21, 50)
        role = emergency_roles[index % len(emergency_roles)]
        mesh = meshes["light" if role == "EmergencyLight" else "damage"]
        instance(step, f"P4_EMG_{index+1:03d}_{role}", "emergency_bloom_variant", pos,
                 (0, 0, facing), (.70, .70, .70), mesh, groups["emergency"],
                 {"variant": role, "default_visible": False}); step += 1

    # 50 production/optimization markers.
    optimization_roles = (
        "LinkedMeshAudit", "InstanceCount", "DrawCallGroup", "LODGroup", "NanitePolicy",
        "CollisionProxy", "LightmapPolicy", "MaterialSlotAudit", "NamingAudit", "ScaleAudit",
        "AisleClearance", "StationReach", "SeatClearance", "Sightline", "ViewportSafety",
        "BulkheadSocket", "AudioAnchor", "VFXAnchor", "InteractionAnchor", "DamageToggle",
        "BloomToggle", "PowerToggle", "EmergencyToggle", "StreamingTag", "UnrealFolder",
    )
    for index in range(50):
        role = optimization_roles[index % len(optimization_roles)]
        station_name, pos, _ = station_point(index + 5, 1.05, -.65)
        marker(step, f"P4_OPT_{index+1:03d}_{station_name}_{role}", "optimization_validation", pos,
               groups["optimization"], {"audit_type": role, "station": station_name}); step += 1

    # 25 camera, light and presentation steps.
    presentation_roles = ("StationCamera", "InteractionCamera", "TaskLight", "EmergencyLight", "PreviewMarker")
    for index in range(25):
        station_name, pos, facing = station_point(index, 1.25, 1.45)
        role = presentation_roles[index % len(presentation_roles)]
        if "Light" in role:
            instance(step, f"P4_PRE_{index+1:03d}_{station_name}_{role}", "camera_lighting", pos,
                     (0, 0, facing), (.85, .85, .85), meshes["light"], groups["presentation"],
                     {"presentation_role": role});
        else:
            marker(step, f"P4_PRE_{index+1:03d}_{station_name}_{role}", "camera_lighting", pos,
                   groups["presentation"], {"presentation_role": role})
        step += 1

    if len(DONE) != 750 or step != 751:
        raise RuntimeError(f"Expected 750 steps; got {len(DONE)}, next={step}")

    for key, group in groups.items():
        group["bridge_phase"] = 4
        group["category"] = key
        group["uses_linked_meshes"] = key not in ("ergonomics", "optimization")
        group["unreal_folder"] = "/Game/Assets/ShipRooms/BridgeCIC/Phase4"

    # Keep phase-three geometry in the scene but omit its loose greybox dressing from this verification render.
    for group in bpy.data.collections:
        if group.name.startswith("P3_"):
            group.hide_render = True

    scene = bpy.context.scene
    scene["bridge_cic_phase4_steps"] = 750
    scene["bridge_cic_phase4_complete"] = True
    scene["bridge_cic_asset_version"] = "4.0-instanced-integration"
    scene["phase4_unique_prototype_meshes"] = len(meshes)
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)

    # FBX does not preserve Blender linked-mesh instancing and can warn when many objects share
    # mesh data with object-level material layouts. Keep the authored scene instanced, but export
    # temporary single-user mesh copies so every FBX node has an unambiguous material table.
    EXPORT.mkdir(parents=True, exist_ok=True)
    export_temp = replace_collection("P4_EXPORT_TEMP_SINGLE_USER")
    export_copies = []
    for group in groups.values():
        for source in group.objects:
            if source.type != "MESH":
                continue
            copy = source.copy()
            copy.data = source.data.copy()
            copy.name = source.name + "_FBX"
            export_temp.objects.link(copy)
            export_copies.append(copy)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in export_copies:
        obj.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(EXPORT / "SM_Room_BridgeCIC_Phase4_750Steps.fbx"),
                             use_selection=True, apply_unit_scale=True, axis_forward="-Y", axis_up="Z",
                             add_leaf_bones=False, bake_anim=False)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in export_copies:
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(export_temp)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))

    counts = {
        "station_integration": 150, "wall_ceiling_structure": 125, "interaction_states": 100,
        "display_plates": 100, "ergonomics": 75, "conduits": 75,
        "emergency_bloom": 50, "optimization_validation": 50, "camera_lighting": 25,
    }
    summary = {
        "phase": 4, "steps": len(DONE), "category_counts": counts,
        "objects": len(bpy.data.objects), "collections": len(bpy.data.collections),
        "materials": len(bpy.data.materials), "linked_prototype_meshes": len(meshes),
        "blend": str(BLEND.relative_to(ROOT)), "preview": str(PREVIEW.relative_to(ROOT)),
    }
    REPORT.write_text(json.dumps({"phase": 4, "steps": DONE, "summary": summary}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


main()
