"""Phase-three close-range detail and cinematic motion for the Blender space-system master."""

import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.stdout.reconfigure(line_buffering=True)


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
OUT = ROOT / "Art" / "SpaceSystems"
BLEND = OUT / "SpaceSystems_Master.blend"
PREVIEW = OUT / "SpaceSystems_Phase3_Preview.png"
REPORT = OUT / "SpaceSystems_Phase3_Report.json"
RNG = random.Random(90817)


def col(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c


def move(obj, c):
    if obj.name not in c.objects:
        c.objects.link(obj)
    for source in list(obj.users_collection):
        if source != c:
            source.objects.unlink(obj)
    return obj


def mat(name, color, emission=0, metallic=0, roughness=.45, alpha=1):
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get("Principled BSDF")
    p.inputs["Base Color"].default_value = (*color, alpha)
    p.inputs["Metallic"].default_value = metallic
    p.inputs["Roughness"].default_value = roughness
    if emission:
        p.inputs["Emission Color"].default_value = (*color, 1)
        p.inputs["Emission Strength"].default_value = emission
    if alpha < 1:
        p.inputs["Alpha"].default_value = alpha
        m.surface_render_method = "DITHERED"
    return m


def sphere(name, p, r, material, seg=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=max(8, seg // 2), location=p, radius=r)
    o = bpy.context.object; o.name = name; o.data.materials.append(material)
    for poly in o.data.polygons: poly.use_smooth = True
    return o


def cube(name, p, scale, material):
    bpy.ops.mesh.primitive_cube_add(location=p)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(material)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return o


def cyl(name, p, radius, depth, material, rotation=(0, 0, 0), vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=p, rotation=rotation)
    o = bpy.context.object; o.name = name; o.data.materials.append(material)
    return o


def torus(name, p, major, minor, material, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=72,
                                    minor_segments=8, location=p, rotation=rotation)
    o = bpy.context.object; o.name = name; o.data.materials.append(material)
    return o


def poly_curve(name, points, material, bevel=.035, cyclic=False):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"; curve.bevel_depth = bevel; curve.bevel_resolution = 3
    spline = curve.splines.new("NURBS"); spline.points.add(len(points) - 1)
    for point, value in zip(spline.points, points): point.co = (*value, 1)
    spline.order_u = min(3, len(points)); spline.use_endpoint_u = True; spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, curve); bpy.context.collection.objects.link(obj); obj.data.materials.append(material)
    return obj


def loop_rotation(obj, frame_end=600, turns=1):
    obj.rotation_mode = "XYZ"; obj.keyframe_insert(data_path="rotation_euler", frame=1)
    obj.rotation_euler.z += math.tau * turns; obj.keyframe_insert(data_path="rotation_euler", frame=frame_end)


def main():
    print("PHASE3 start", flush=True)
    scene = bpy.context.scene
    primary = bpy.data.objects.get("Primary_Golden_Giant")
    ocean = bpy.data.objects.get("Ocean_World")
    volcanic = bpy.data.objects.get("Volcanic_World")
    gas = bpy.data.objects.get("Ringed_Gas_Giant")
    ice = bpy.data.objects.get("Ice_World")

    dark = mat("M_Sunspot", (.015, .002, .001), emission=.2, roughness=.8)
    flare = mat("M_SolarProminence", (1, .035, .002), emission=25, roughness=.08)
    cloud = mat("M_CloudLayer", (.65, .78, .9), emission=.12, roughness=.65, alpha=.23)
    polar = mat("M_PolarIce", (.55, .85, 1), emission=.3, roughness=.35)
    aurora = mat("M_Aurora", (.01, 1, .38), emission=18, roughness=.08, alpha=.32)
    storm = mat("M_GasStorm", (.75, .07, .015), emission=.25, roughness=.5)
    lava = mat("M_LavaFissure", (1, .018, .001), emission=22, roughness=.16)
    crack = mat("M_IceCrack", (.02, .5, 1), emission=5, roughness=.2)
    dust = mat("M_RingDust", (.18, .22, .24), emission=.05, roughness=.7)
    hull = bpy.data.materials.get("M_StationHull") or mat("M_StationHull", (.025, .045, .06), metallic=.8, roughness=.3)
    window = mat("M_WindowLights", (.015, .35, 1), emission=15, roughness=.12)

    # 1. Sunspot clusters.
    stellar_detail = col("SYS_StellarSurfaceDetail")
    if primary:
        for i in range(34):
            d = Vector((RNG.uniform(-1, 1), RNG.uniform(-1, 1), RNG.uniform(-1, 1))).normalized()
            spot = sphere(f"Sunspot_{i:02d}", primary.location + d * 6.18, RNG.uniform(.08, .3), dark, 12)
            spot.scale.z = RNG.uniform(.12, .35); spot.parent = primary; move(spot, stellar_detail)
    print("PHASE3 stellar detail", flush=True)

    # 2. Solar prominence arcs.
    for i in range(5):
        angle = math.tau * i / 5 + .25
        tangent = Vector((-math.sin(angle), math.cos(angle), 0))
        base = Vector((math.cos(angle), math.sin(angle), 0)) * 6.1
        points = []
        for j in range(9):
            t = j / 8
            points.append(base + tangent * ((t - .5) * 5.2) + Vector((0, 0, math.sin(t * math.pi) * 3.2)))
        move(poly_curve(f"SolarProminence_{i + 1}", points, flare, .07), stellar_detail)

    # 3. Blue companion corona, kept with the disabled stellar variant.
    companion = bpy.data.objects.get("Binary_BlueWhite_Companion")
    if companion:
        blue_corona = sphere("BinaryCompanion_Corona", companion.location, 3.75,
                             mat("M_BlueCorona", (.02, .2, 1), emission=9, alpha=.15), 48)
        blue_corona.hide_render = companion.hide_render; blue_corona.parent = companion; move(blue_corona, stellar_detail)

    # 4. Richer nebula density breakup.
    nebula_mat = bpy.data.materials.get("M_Ion_Nebula")
    if nebula_mat and nebula_mat.use_nodes:
        nodes = nebula_mat.node_tree.nodes; links = nebula_mat.node_tree.links
        volume = next((n for n in nodes if n.bl_idname == "ShaderNodeVolumePrincipled"), None)
        if volume and not nodes.get("NebulaDensityNoise"):
            noise = nodes.new("ShaderNodeTexNoise"); noise.name = "NebulaDensityNoise"
            noise.noise_dimensions = "4D"; noise.inputs["Scale"].default_value = 1.8
            noise.inputs["Detail"].default_value = 5; noise.inputs["Roughness"].default_value = .8
            ramp = nodes.new("ShaderNodeValToRGB"); ramp.name = "NebulaDensityRamp"
            ramp.color_ramp.elements[0].position = .38; ramp.color_ramp.elements[1].position = .67
            links.new(noise.outputs["Fac"], ramp.inputs["Fac"]); links.new(ramp.outputs["Color"], volume.inputs["Density"])
    print("PHASE3 nebula", flush=True)

    atmosphere_detail = col("SYS_PlanetSurfaceDetail")
    # 5. Ocean cloud shell.
    if ocean:
        radius = max(ocean.dimensions) * .53
        clouds = sphere("OceanWorld_CloudDeck", ocean.location, radius, cloud, 48)
        clouds.scale.z = .985; clouds.parent = ocean; move(clouds, atmosphere_detail); loop_rotation(clouds, 420, .7)

    # 6. Polar caps.
    if ocean:
        radius = max(ocean.dimensions) * .515
        for sign, label in ((1, "North"), (-1, "South")):
            cap = sphere(f"OceanWorld_{label}PolarCap", ocean.location + Vector((0, 0, sign * radius * .88)), radius * .34, polar, 28)
            cap.scale.z = .18; cap.parent = ocean; move(cap, atmosphere_detail)

    # 7. Aurora bands.
    if ocean:
        for sign, label in ((1, "North"), (-1, "South")):
            band = torus(f"OceanWorld_{label}Aurora", ocean.location + Vector((0, 0, sign * 1.9)), 1.15, .045, aurora)
            band.parent = ocean; move(band, atmosphere_detail); loop_rotation(band, 240, sign)

    # 8. Gas giant storm eye.
    if gas:
        storm_obj = sphere("GasGiant_GreatStorm", gas.location + Vector((4.55, .65, -.5)), .7, storm, 28)
        storm_obj.scale = (.18, 1.0, .55); storm_obj.parent = gas; move(storm_obj, atmosphere_detail)

    # 9. Gas giant band rings.
    if gas:
        for i in range(7):
            z = gas.location.z + (i - 3) * .48
            band = torus(f"GasGiant_Band_{i + 1}", (gas.location.x, gas.location.y, z), 4.65 - abs(i - 3) * .08,
                         .035 + (i % 2) * .018, storm if i in (2, 4) else dust)
            band.parent = gas; move(band, atmosphere_detail)

    # 10. Volcanic lava vents.
    if volcanic:
        radius = max(volcanic.dimensions) * .515
        for i in range(24):
            d = Vector((RNG.uniform(-1, 1), RNG.uniform(-1, 1), RNG.uniform(-1, 1))).normalized()
            vent = sphere(f"VolcanicWorld_LavaVent_{i:02d}", volcanic.location + d * radius, RNG.uniform(.035, .11), lava, 10)
            vent.parent = volcanic; move(vent, atmosphere_detail)

    # 11. Ice-world glowing fault lines.
    if ice:
        for i in range(9):
            points = []
            for j in range(7):
                a = j / 6 * math.pi * 1.4 + i * .55
                points.append(ice.location + Vector((math.cos(a) * 1.98, math.sin(a) * 1.98, math.sin(a * 2.1 + i) * .32)))
            curve = poly_curve(f"IceWorld_Fault_{i + 1}", points, crack, .025)
            curve.parent = ice; move(curve, atmosphere_detail)

    # 12. Dense gas-giant ring particles.
    ring_particles = col("SYS_RingParticles")
    if gas:
        for i in range(220):
            a = RNG.random() * math.tau; r = RNG.uniform(7.1, 10.2)
            p = gas.location + Vector((math.cos(a) * r, math.sin(a) * r, RNG.gauss(0, .13)))
            rock = sphere(f"GasRingParticle_{i:03d}", p, RNG.uniform(.025, .11), dust, 8)
            rock.parent = gas; move(rock, ring_particles)
    print("PHASE3 planets and rings", flush=True)

    # 13. Asteroid-belt navigation lane lights.
    lane = col("SYS_BeltNavigationLane")
    for i in range(18):
        a = i / 18 * math.tau; r = 29
        lamp = sphere(f"BeltLaneLight_{i + 1}", (math.cos(a) * r, math.sin(a) * r, 1.4), .09, aurora, 12)
        lamp["navigation_lane"] = True; move(lamp, lane)
    print("PHASE3 navigation lane", flush=True)

    # 14. Satellite constellation.
    satellites = col("SYS_SatelliteConstellation")
    if ocean:
        for i in range(8):
            a = i / 8 * math.tau; p = ocean.location + Vector((math.cos(a) * 4.2, math.sin(a) * 4.2, math.sin(a * 2) * .6))
            body = cube(f"SurveySatellite_{i + 1}", p, (.16, .1, .1), hull); move(body, satellites)
            panel_a = cube(f"SurveySatellite_{i + 1}_PanelA", p + Vector((0, .28, 0)), (.22, .18, .015), window)
            panel_b = cube(f"SurveySatellite_{i + 1}_PanelB", p - Vector((0, .28, 0)), (.22, .18, .015), window)
            panel_a.parent = body; panel_b.parent = body; body.parent = ocean; move(panel_a, satellites); move(panel_b, satellites)

    # 15. Derelict vessel landmark.
    derelict_col = col("SYS_DerelictVessel")
    derelict_root = bpy.data.objects.new("Derelict_ExpeditionVessel", None); derelict_root.location = (-11, 26, -2); derelict_col.objects.link(derelict_root)
    for piece in (
        cube("Derelict_Hull", derelict_root.location, (2.8, .65, .55), hull),
        cube("Derelict_BrokenBow", derelict_root.location + Vector((3.0, .2, .25)), (.9, .5, .38), hull),
        cyl("Derelict_Engine", derelict_root.location - Vector((2.9, 0, 0)), .42, .8, dark, (0, math.pi / 2, 0)),
    ):
        piece.parent = derelict_root; move(piece, derelict_col)
    derelict_root.rotation_euler = (.4, -.25, .8); derelict_root["sensor_contact"] = True; derelict_root["salvageable"] = True
    loop_rotation(derelict_root, 600, .18)
    print("PHASE3 derelict", flush=True)

    # 16. Long-range science probe.
    probe_col = col("SYS_ScienceProbe")
    probe = sphere("LongRange_ScienceProbe", (7, 35, 12), .24, hull, 18); move(probe, probe_col)
    dish = torus("ScienceProbe_Dish", (7, 35, 12.45), .42, .045, window, (math.pi / 2, 0, 0)); dish.parent = probe; move(dish, probe_col)
    probe["telemetry"] = "gravity_anomaly_survey"; probe["sensor_signature"] = .35

    # 17. Station window strips.
    station_lights = col("SYS_StationLighting")
    for station_name in ("OceanWorld_ResearchStation", "GasGiant_Refinery"):
        station = bpy.data.objects.get(station_name)
        if station:
            for i in range(12):
                a = i / 12 * math.tau
                light = sphere(f"{station_name}_Window_{i + 1}", station.location + Vector((math.cos(a) * 1.1, math.sin(a) * 1.1, .15)), .055, window, 10)
                light.parent = station; move(light, station_lights)

    # 18. Jump-gate energy membrane.
    gate = bpy.data.objects.get("JumpGate_Controller")
    if gate:
        membrane = sphere("JumpGate_EnergyMembrane", gate.location, 3.55, mat("M_JumpMembrane", (.015, .15, 1), emission=10, alpha=.12), 48)
        membrane.scale.z = .08; membrane.parent = gate; move(membrane, col("SYS_JumpArchitecture")); loop_rotation(membrane, 180, 2)
    print("PHASE3 structures", flush=True)

    # 19. Animated cinematic camera dolly.
    camera = bpy.data.objects.get("Camera_PlanetaryApproach")
    if camera:
        camera.keyframe_insert(data_path="location", frame=1)
        camera.location += Vector((-8, 14, 5)); camera.keyframe_insert(data_path="location", frame=300)
        camera.location += Vector((12, 10, -2)); camera.keyframe_insert(data_path="location", frame=600)
        camera["shot_name"] = "Planetary Approach Dolly"

    # 20. Phase report, render and scene metadata.
    scene["phase3_steps"] = 20; scene["asset_version"] = "3.0"
    scene["close_range_detail"] = True; scene["cinematic_camera_motion"] = True
    scene.camera = bpy.data.objects.get("Camera_CinematicOverview") or scene.camera
    scene.render.resolution_x = 1280; scene.render.resolution_y = 720; scene.render.resolution_percentage = 100
    scene.render.filepath = str(PREVIEW)
    print("PHASE3 rendering", flush=True)
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    report = {
        "phase": 3, "steps": 20, "objects": len(bpy.data.objects), "materials": len(bpy.data.materials),
        "actions": len(bpy.data.actions), "collections": len(bpy.data.collections),
        "features": ["sunspots", "prominences", "companion corona", "nebula density noise", "cloud deck",
                     "polar caps", "auroras", "gas storm", "gas bands", "lava vents", "ice faults",
                     "ring particles", "belt lane", "satellites", "derelict vessel", "science probe",
                     "station windows", "jump membrane", "camera dolly", "phase metadata"]
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


main()
