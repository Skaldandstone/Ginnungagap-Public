"""Phase 25: cinematic artist pass for the Pelagos space map.

Run against SpaceSystems_PelagosOrbitalArrival_Level.blend.  The pass is
idempotent, preserves gameplay objects, and creates a dedicated render layer.
"""
import json, math, random, sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
OUT = ROOT / "Art" / "SpaceSystems"
LEVEL = OUT / "SpaceSystems_PelagosOrbitalArrival_Level.blend"
PREVIEW = OUT / "SpaceSystems_PelagosOrbitalArrival_ArtistPass.png"
REPORT = OUT / "SpaceSystems_ArtistPass_Report.json"
RNG = random.Random(250825)


def collection(name):
    value = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if value.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(value)
    return value


def material(name, color, emission=None, strength=0.0, metallic=0.0, roughness=0.45):
    value = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    value.diffuse_color = (*color, 1)
    value.use_nodes = True
    shader = value.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = roughness
    if emission:
        shader.inputs["Emission Color"].default_value = (*emission, 1)
        shader.inputs["Emission Strength"].default_value = strength
    return value


def move(obj, target):
    for source in list(obj.users_collection):
        source.objects.unlink(obj)
    target.objects.link(obj)
    return obj


def look_at(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


def add_uv(name, location, radius, mat, target, segments=48):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=segments // 2,
                                         radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    for face in obj.data.polygons:
        face.use_smooth = True
    return move(obj, target)


def add_light(name, kind, location, color, energy, target, size=5.0):
    data = bpy.data.lights.new(name, kind)
    data.color = color
    data.energy = energy
    if kind == "AREA":
        data.shape = "DISK"
        data.size = size
    obj = bpy.data.objects.new(name, data)
    target.objects.link(obj)
    obj.location = location
    return obj


def main():
    scene = bpy.context.scene
    if scene.get("artist_pass_version") == "25.2":
        raise RuntimeError("Artist pass 25.2 is already installed")

    # Allow an intentional revision of the art layer without accumulating geometry.
    old_art = bpy.data.collections.get("ARTISTPASS_25")
    if old_art:
        for obj in list(old_art.all_objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        for child in list(old_art.children):
            bpy.data.collections.remove(child)
        bpy.data.collections.remove(old_art)

    art = collection("ARTISTPASS_25")
    stars = collection("ARTISTPASS_Stars")
    lights = collection("ARTISTPASS_Lighting")
    hero = collection("ARTISTPASS_HeroSet")
    cameras = collection("ARTISTPASS_Cameras")
    for child in (stars, lights, hero, cameras):
        if child.name in scene.collection.children:
            scene.collection.children.unlink(child)
        if child.name not in art.children:
            art.children.link(child)

    navy = material("AP25_DeepSpace", (0.001, 0.003, 0.012), roughness=1)
    star_cool = material("AP25_StarCool", (0.55, 0.75, 1.0), (0.55, 0.75, 1.0), 18)
    star_warm = material("AP25_StarWarm", (1.0, 0.56, 0.22), (1.0, 0.34, 0.08), 14)
    moon_mat = material("AP25_Moon", (0.045, 0.06, 0.08), metallic=0.05, roughness=0.82)
    cyan = material("AP25_Cyan", (0.01, 0.18, 0.24), (0.02, 0.55, 1.0), 9, metallic=0.25, roughness=0.3)

    # Remove editor/readability geometry from the beauty pass without touching gameplay state.
    hidden = []
    debug_terms = ("CloudArc", "OrbitalEquator", "OrbitalTrail", "Lane_", "Route_",
                   "HoldingPattern", "ApproachSpline", "SafetyVolume", "NavGrid")
    for obj in bpy.data.objects:
        if any(term in obj.name for term in debug_terms):
            obj.hide_render = True
            hidden.append(obj.name)

    # A sparse, depth-layered star field; clustered distribution avoids wallpaper uniformity.
    for index in range(260):
        angle = RNG.random() * math.tau
        elevation = RNG.uniform(-0.62, 0.72)
        distance = RNG.uniform(115, 205)
        center_bias = RNG.choice((0.0, 0.0, 0.0, 0.2))
        location = (math.cos(angle) * math.cos(elevation) * distance,
                    math.sin(angle) * math.cos(elevation) * distance,
                    math.sin(elevation) * distance + center_bias * 25)
        radius = RNG.choice((0.009, 0.012, 0.015, 0.02, 0.032))
        add_uv(f"AP25_Star_{index:03d}", location, radius,
               star_warm if index % 19 == 0 else star_cool, stars, 8)

    # Distant moon provides a second focal scale and breaks the empty upper-right quadrant.
    moon = add_uv("AP25_PelagosMoon", (58, 61, 28), 3.1, moon_mat, hero, 64)
    noise = moon.modifiers.new("Ancient surface", "DISPLACE")
    tex = bpy.data.textures.new("AP25_MoonNoise", type="MUSGRAVE")
    tex.noise_scale = 0.42
    noise.texture = tex
    noise.strength = 0.16

    # Replace the flat blue globe with physically useful material response.
    planet = bpy.data.objects.get("OceanPlanet") or bpy.data.objects.get("Pelagos")
    if not planet:
        candidates = [o for o in bpy.data.objects if o.type == "MESH" and "Ocean" in o.name and len(o.data.polygons) > 100]
        planet = max(candidates, key=lambda o: o.dimensions.length) if candidates else None
    if planet:
        ocean = material("AP25_PelagosOcean", (0.008, 0.055, 0.12), metallic=0.16, roughness=0.24)
        planet.data.materials.clear()
        planet.data.materials.append(ocean)
        ocean_shader = ocean.node_tree.nodes.get("Principled BSDF")
        ocean_shader.inputs["Coat Weight"].default_value = 0.28
        ocean_shader.inputs["Coat Roughness"].default_value = 0.16

    # Shape the station with warm/cool separation and readable pools of light.
    sun = add_light("AP25_KeySun", "AREA", (-30, -24, 34), (1.0, 0.42, 0.17), 1650, lights, 18)
    look_at(sun, (-3, 2, 4))
    rim = add_light("AP25_PlanetRim", "AREA", (25, 48, 24), (0.12, 0.42, 1.0), 2400, lights, 22)
    look_at(rim, (-2, 5, 4))
    fill = add_light("AP25_StationFill", "AREA", (-9, -7, 7), (0.08, 0.55, 1.0), 920, lights, 9)
    look_at(fill, (-5, 2, 3))
    for index, z in enumerate((-1.2, 1.1, 4.1, 6.8)):
        lamp = add_light(f"AP25_DockPool_{index+1}", "AREA", (-12.4, -0.4, z + 1.0),
                         (0.05, 0.55, 1.0) if index != 2 else (1.0, 0.2, 0.03),
                         170, lights, 1.8)
        look_at(lamp, (-12.4, 2.0, z))

    # Hero camera: station on left third, Pelagos on right, approach lane implied by silhouettes.
    cam_data = bpy.data.cameras.new("Camera_PelagosArtistHero")
    cam_data.lens = 50
    cam_data.sensor_width = 36
    cam_data.dof.use_dof = True
    cam_data.dof.aperture_fstop = 6.3
    cam = bpy.data.objects.new("Camera_PelagosArtistHero", cam_data)
    cameras.objects.link(cam)
    cam.location = (-38, -42, 18)
    look_at(cam, (3.5, 18.5, 4.0))
    focus = bpy.data.objects.get("StationCore") or bpy.data.objects.get("LVL_StationCore")
    if focus:
        cam.data.dof.focus_object = focus
    else:
        cam.data.dof.focus_distance = 45
    scene.camera = cam

    # Filmic scene setup tuned for readable blacks and restrained highlights.
    world = scene.world or bpy.data.worlds.new("AP25_World")
    scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.001, 0.003, 0.012, 1)
    background.inputs["Strength"].default_value = 0.018
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.resolution_percentage = 100
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.filepath = str(PREVIEW)

    scene["artist_pass_version"] = "25.2"
    scene["visual_target"] = "cinematic grounded hard-sf"
    scene["beauty_camera"] = cam.name
    art["production_role"] = "artist_beauty_layer"
    report = {
        "phase": 25,
        "version": "25.2",
        "target": "cinematic grounded hard-sf",
        "star_count": 260,
        "lights": 7,
        "hidden_debug_objects": len(hidden),
        "camera": cam.name,
        "resolution": [1920, 1080],
        "preserved_gameplay_objects": True,
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(LEVEL))
    bpy.ops.render.render(write_still=True)
    print(json.dumps(report, indent=2))


main()
