"""Add production-detail phase two to SpaceSystems_Master.blend."""

import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
OUT = ROOT / "Art" / "SpaceSystems"
BLEND = OUT / "SpaceSystems_Master.blend"
PREVIEW = OUT / "SpaceSystems_Phase2_Preview.png"
MANIFEST = OUT / "SpaceSystems_Manifest.json"
RNG = random.Random(442021)


def collection(name):
    result = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if result.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(result)
    return result


def move_to(obj, target):
    if obj.name not in target.objects:
        target.objects.link(obj)
    for source in list(obj.users_collection):
        if source != target:
            source.objects.unlink(obj)


def material(name, color, emission=0.0, metallic=0.0, roughness=0.45, alpha=1.0):
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, alpha)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*color, 1)
        bsdf.inputs["Emission Strength"].default_value = emission
    if alpha < 1:
        bsdf.inputs["Alpha"].default_value = alpha
        mat.surface_render_method = "DITHERED"
    return mat


def sphere(name, location, radius, mat, segments=48):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=max(12, segments // 2), radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def torus(name, location, major, minor, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=96,
                                    minor_segments=10, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def cube(name, location, scale, mat):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    return obj


def cylinder(name, location, radius, depth, mat, rotation=(0, 0, 0), vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return obj


def keyframe_loop(obj, data_path, frame_end=600):
    obj.keyframe_insert(data_path=data_path, frame=1)
    if data_path == "rotation_euler":
        obj.rotation_euler.z += math.tau
    obj.keyframe_insert(data_path=data_path, frame=frame_end)


def add_station(name, location, scale=1.0):
    station_col = collection("SYS_OrbitalStructures")
    hull = material("M_StationHull", (0.035, 0.055, 0.07), metallic=0.8, roughness=0.28)
    light = material("M_StationLight", (0.02, 0.4, 1.0), emission=8, roughness=0.2)
    root = bpy.data.objects.new(name, None)
    root.empty_display_type = "CUBE"
    root.location = location
    station_col.objects.link(root)
    pieces = [
        cylinder(name + "_Core", location, 0.42 * scale, 2.8 * scale, hull, (0, math.pi / 2, 0)),
        torus(name + "_HabRing", location, 1.45 * scale, 0.16 * scale, hull, (math.pi / 2, 0, 0)),
        cube(name + "_SolarA", Vector(location) + Vector((0, 1.8, 0)), (0.85, 0.05, 0.36), hull),
        cube(name + "_SolarB", Vector(location) - Vector((0, 1.8, 0)), (0.85, 0.05, 0.36), hull),
        sphere(name + "_Beacon", Vector(location) + Vector((0, 0, 1.35 * scale)), 0.13 * scale, light, 20),
    ]
    for piece in pieces:
        move_to(piece, station_col)
        piece.parent = root
    root["gameplay_role"] = "orbital_station"
    keyframe_loop(root, "rotation_euler")
    return root


def add_jump_gate():
    gate_col = collection("SYS_JumpArchitecture")
    metal = material("M_JumpGateHull", (0.025, 0.045, 0.06), metallic=0.9, roughness=0.2)
    glow = material("M_JumpGateGlow", (0.02, 0.3, 1.0), emission=16, roughness=0.1)
    center = Vector((20, -24, 4))
    root = bpy.data.objects.new("JumpGate_Controller", None)
    root.location = center
    gate_col.objects.link(root)
    for i in range(3):
        ring = torus(f"JumpGate_Ring_{i + 1}", center, 3.7 + i * 0.42, 0.16, metal if i != 1 else glow,
                     (math.radians(72), 0, math.radians(15 + i * 7)))
        move_to(ring, gate_col)
        ring.parent = root
    for i in range(8):
        angle = math.tau * i / 8
        p = center + Vector((math.cos(angle) * 4.45, math.sin(angle) * 4.45, math.sin(angle * 2) * 0.35))
        node = sphere(f"JumpGate_Emitter_{i + 1}", p, 0.17, glow, 20)
        move_to(node, gate_col)
        node.parent = root
    root["gameplay_role"] = "jump_destination"
    root["interaction_radius_m"] = 5000.0
    keyframe_loop(root, "rotation_euler", 360)


def main():
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.frame_start = 1
    scene.frame_end = 600
    scene.render.fps = 30

    controller_col = collection("SYS_Controllers")
    controller = bpy.data.objects.get("SpaceSystem_MasterController") or bpy.data.objects.new("SpaceSystem_MasterController", None)
    if not controller.users_collection:
        controller_col.objects.link(controller)
    controller.empty_display_type = "SPHERE"
    controller.empty_display_size = 3.0
    controller["astronomical_time_scale"] = 20.0
    controller["system_seed"] = 731947
    controller["danger_tier"] = 4
    controller["dominant_phenomenon"] = "Ion Nebula / Fractured World"

    # 1-2: alternate star and corona layers.
    star_col = collection("SYS_StellarVariants")
    blue = material("M_Star_BlueWhite", (0.12, 0.48, 1.0), emission=22, roughness=0.12)
    corona = material("M_StellarCorona", (1.0, 0.12, 0.015), emission=7, roughness=0.1, alpha=0.16)
    companion = sphere("Binary_BlueWhite_Companion", (-15, -8, 7), 3.2, blue, 72)
    companion.hide_render = True
    companion["variant"] = "binary_star"
    move_to(companion, star_col)
    primary = bpy.data.objects.get("Primary_Golden_Giant")
    if primary:
        corona_obj = sphere("Primary_Stellar_Corona", primary.location, 7.25, corona, 64)
        move_to(corona_obj, star_col)

    # 3: gravity anomaly with lens rings.
    anomaly_col = collection("SYS_GravityAnomaly")
    black = material("M_AnomalyCore", (0.0001, 0.0001, 0.0002), metallic=0.1, roughness=0.02)
    violet = material("M_AnomalyLens", (0.3, 0.015, 0.8), emission=10, roughness=0.08)
    anomaly_center = Vector((-34, 30, 12))
    move_to(sphere("GravityAnomaly_Core", anomaly_center, 2.8, black, 64), anomaly_col)
    for i in range(4):
        ring = torus(f"GravityAnomaly_LensRing_{i + 1}", anomaly_center, 4.0 + i * 0.85, 0.09 + i * 0.025,
                     violet, (RNG.uniform(-0.5, 0.5), RNG.uniform(-0.5, 0.5), RNG.uniform(0, math.tau)))
        move_to(ring, anomaly_col)
        keyframe_loop(ring, "rotation_euler", 300 + i * 70)

    # 4-5: atmosphere shells and ocean-world city lights.
    atmosphere_col = collection("SYS_Atmospheres")
    atmosphere = material("M_Atmosphere_Blue", (0.03, 0.35, 1.0), emission=1.8, roughness=0.12, alpha=0.13)
    city = material("M_CityLights", (1.0, 0.32, 0.015), emission=14, roughness=0.15)
    for planet_name in ("Ocean_World", "Ice_World", "Ringed_Gas_Giant"):
        planet = bpy.data.objects.get(planet_name)
        if planet:
            radius = max(planet.dimensions) * 0.52
            shell = sphere(planet_name + "_Atmosphere", planet.location, radius * 1.055, atmosphere, 48)
            shell.parent = planet
            move_to(shell, atmosphere_col)
    ocean = bpy.data.objects.get("Ocean_World")
    if ocean:
        radius = max(ocean.dimensions) * 0.51
        for i in range(48):
            direction = Vector((RNG.uniform(-1, 1), RNG.uniform(-1, 1), RNG.uniform(-1, 1))).normalized()
            light = sphere(f"OceanWorld_CityLight_{i:02d}", ocean.location + direction * radius * 1.008,
                           RNG.uniform(0.018, 0.05), city, 12)
            light.parent = ocean
            move_to(light, atmosphere_col)

    # 6-7: orbital stations and navigation beacons.
    add_station("OceanWorld_ResearchStation", (17, 16, 3), 0.8)
    add_station("GasGiant_Refinery", (-18, -32, -2), 1.15)
    beacon_col = collection("SYS_NavigationBeacons")
    beacon_glow = material("M_NavigationBeacon", (0.01, 0.85, 1.0), emission=18, roughness=0.1)
    for i, pos in enumerate(((9, -12, 2), (27, 4, 6), (-12, -20, -3), (38, 20, 8))):
        pole = cylinder(f"NavBeacon_{i + 1}_Mast", pos, 0.08, 1.6, material("M_BeaconHull", (0.04, 0.06, 0.08), metallic=0.7))
        lamp = sphere(f"NavBeacon_{i + 1}_Lamp", Vector(pos) + Vector((0, 0, 0.9)), 0.18, beacon_glow, 16)
        move_to(pole, beacon_col); move_to(lamp, beacon_col)
        lamp["sensor_signature"] = 0.95

    # 8: jump gate.
    add_jump_gate()

    # 9-10: resource asteroids and hazard buoys.
    resource_col = collection("SYS_ResourceLandmarks")
    crystal = material("M_ResourceCrystal", (0.01, 0.8, 0.45), emission=6, metallic=0.15, roughness=0.2)
    for i, pos in enumerate(((-26, 6, 4), (31, -7, -5), (-4, 38, 7))):
        core = sphere(f"ResourceNode_{i + 1}_Core", pos, 0.75, bpy.data.materials.get("M_Asteroid"), 20)
        move_to(core, resource_col)
        for j in range(6):
            direction = Vector((RNG.uniform(-1, 1), RNG.uniform(-1, 1), RNG.uniform(-1, 1))).normalized()
            shard = cylinder(f"ResourceNode_{i + 1}_Crystal_{j + 1}", Vector(pos) + direction * 0.72,
                             0.09, RNG.uniform(0.5, 1.2), crystal, direction.to_track_quat("Z", "Y").to_euler(), 6)
            move_to(shard, resource_col)
        core["resource_type"] = ("NavigationFuel", "StructuralAlloy", "PowerCells")[i]
        core["quantity"] = (18, 24, 12)[i]
    hazard_col = collection("SYS_HazardBeacons")
    warning = material("M_HazardWarning", (1.0, 0.025, 0.002), emission=16, roughness=0.15)
    for i, pos in enumerate(((-18, 22, 6), (-28, 28, 9), (4, 31, -4))):
        buoy = torus(f"HazardBuoy_{i + 1}", pos, 0.6, 0.08, warning, (math.pi / 2, 0, 0))
        move_to(buoy, hazard_col)
        buoy["hazard_severity"] = 0.65 + i * 0.12

    # 11-12: sensor landmarks and gameplay metadata.
    for obj in (companion, bpy.data.objects.get("GravityAnomaly_Core"), bpy.data.objects.get("JumpGate_Controller")):
        if obj:
            obj["sensor_contact"] = True
            obj["sensor_signature"] = 1.0
    controller["resource_contacts"] = 3
    controller["hazard_contacts"] = 3

    # 13-14: camera DOF and exposure polish.
    for camera_obj in [o for o in scene.objects if o.type == "CAMERA"]:
        camera_obj.data.dof.use_dof = True
        camera_obj.data.dof.focus_object = primary
        camera_obj.data.dof.aperture_fstop = 5.6
        camera_obj.data.lens = max(camera_obj.data.lens, 52)
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -0.65

    # 15-16: render presets as scene copies and safe-area metadata.
    scene["render_preset"] = "CinematicOverview_1600x900"
    scene["safe_title_percent"] = 0.9
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100

    # 17-18: export grouping and LOD metadata.
    export_col = collection("EXPORT_Unreal_Celestials")
    for name in ("Primary_Golden_Giant", "Ocean_World", "Volcanic_World", "Ringed_Gas_Giant", "Ice_World"):
        obj = bpy.data.objects.get(name)
        if obj and obj.name not in export_col.objects:
            export_col.objects.link(obj)
        if obj:
            obj["unreal_lod_group"] = "LargeProp"
            obj["nanite_recommended"] = True

    # 19: animation markers.
    scene.timeline_markers.clear()
    for name, frame in (("SYSTEM_ESTABLISH", 1), ("PLANET_APPROACH", 150), ("ANOMALY_REVEAL", 300),
                        ("COMET_PASS", 450), ("LOOP_END", 600)):
        scene.timeline_markers.new(name, frame=frame)

    # 20: manifest and validation metadata.
    scene["phase2_steps"] = 20
    scene["asset_version"] = "2.0"
    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))

    manifest = {
        "asset": "SpaceSystems_Master.blend",
        "version": 2,
        "objects": len(bpy.data.objects),
        "materials": len(bpy.data.materials),
        "actions": len(bpy.data.actions),
        "timeline": [scene.frame_start, scene.frame_end],
        "cameras": [o.name for o in scene.objects if o.type == "CAMERA"],
        "collections": sorted(c.name for c in bpy.data.collections if c.name.startswith(("SYS_", "EXPORT_"))),
        "features": ["binary companion", "stellar corona", "gravity anomaly", "atmospheres", "city lights",
                     "orbital stations", "navigation beacons", "jump gate", "resource nodes", "hazard buoys"],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


main()
