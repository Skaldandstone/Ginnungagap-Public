"""Build an editable cinematic space-system scene in Blender.

Run with Blender:
  blender --background --python tools/build_space_systems_blender.py -- <project-root>
"""

import math
import random
import json
import secrets
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
OUT = ROOT / "Art" / "SpaceSystems"
BLEND = OUT / "SpaceSystems_Master.blend"
PREVIEW = OUT / "SpaceSystems_Preview.png"
GLTF = OUT / "SpaceSystems_UnrealPreview.glb"
MANIFEST = OUT / "SpaceSystems_GenerationManifest.json"


def generator_seed():
    """Use a fresh seed by default, while allowing exact rebuilds with --seed N."""
    args = sys.argv[sys.argv.index("--") + 2:]
    if "--seed" in args:
        index = args.index("--seed")
        if index + 1 >= len(args):
            raise ValueError("--seed requires an integer value")
        return int(args[index + 1], 0)
    return secrets.randbits(63)


SEED = generator_seed()
RNG = random.Random(SEED)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.materials, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def mat_principled(name, base, metallic=0.0, roughness=0.5, emission=None, strength=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*base, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def mat_planet(name, dark, light, scale=4.0, distortion=0.25, emission=None):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    n = mat.node_tree.nodes
    l = mat.node_tree.links
    bsdf = n.get("Principled BSDF")
    tex = n.new("ShaderNodeTexNoise")
    tex.noise_dimensions = "4D"
    tex.inputs["Scale"].default_value = scale
    tex.inputs["Detail"].default_value = 7.0
    tex.inputs["Roughness"].default_value = 0.72
    tex.inputs["Distortion"].default_value = distortion
    ramp = n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (*dark, 1)
    ramp.color_ramp.elements[1].color = (*light, 1)
    l.new(tex.outputs["Fac"], ramp.inputs["Fac"])
    l.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
    bump = n.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.3
    bump.inputs["Distance"].default_value = 0.18
    l.new(tex.outputs["Fac"], bump.inputs["Height"])
    l.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = 0.58
    if emission:
        l.new(ramp.outputs["Color"], bsdf.inputs["Emission Color"])
        bsdf.inputs["Emission Strength"].default_value = emission
    return mat


def mat_volume(name, color, density, emission=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.remove(nodes.get("Principled BSDF"))
    volume = nodes.new("ShaderNodeVolumePrincipled")
    volume.inputs["Color"].default_value = (*color, 1)
    volume.inputs["Density"].default_value = density
    volume.inputs["Emission Color"].default_value = (*color, 1)
    volume.inputs["Emission Strength"].default_value = emission
    links.new(volume.outputs["Volume"], nodes.get("Material Output").inputs["Volume"])
    return mat


def smooth(obj):
    if hasattr(obj.data, "polygons"):
        for poly in obj.data.polygons:
            poly.use_smooth = True


def uv_sphere(name, location, radius, material, segments=64, rings=32):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, location=location, radius=radius)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    smooth(obj)
    return obj


def ico(name, location, radius, material, subdivisions=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = (RNG.uniform(0.72, 1.3), RNG.uniform(0.72, 1.25), RNG.uniform(0.7, 1.2))
    obj.rotation_euler = [RNG.random() * math.tau for _ in range(3)]
    obj.data.materials.append(material)
    return obj


def torus(name, location, major, minor, material, tilt=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=128,
                                    minor_segments=12, location=location, rotation=tilt)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    return obj


def orbit_curve(name, radius, material, tilt=(0, 0, 0), width=0.006):
    curve = bpy.data.curves.new(name, "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = width
    curve.bevel_resolution = 2
    spline = curve.splines.new("NURBS")
    spline.points.add(63)
    for i, point in enumerate(spline.points):
        a = math.tau * i / 63
        point.co = (math.cos(a) * radius, math.sin(a) * radius, 0, 1)
    spline.use_cyclic_u = True
    spline.order_u = 3
    spline.use_endpoint_u = False
    obj = bpy.data.objects.new(name, curve)
    bpy.context.collection.objects.link(obj)
    obj.rotation_euler = tilt
    obj.data.materials.append(material)
    return obj


def add_starfield(material):
    for i in range(900):
        direction = Vector((RNG.uniform(-1, 1), RNG.uniform(-1, 1), RNG.uniform(-0.65, 1))).normalized()
        distance = RNG.uniform(95, 150)
        radius = RNG.choice((0.025, 0.035, 0.05, 0.08))
        uv_sphere(f"Starfield_{i:04d}", direction * distance, radius, material, 8, 4)


def add_belt(material, radius=30, count=620, broken=False):
    collection = bpy.data.collections.new("Asteroid_Belt")
    bpy.context.scene.collection.children.link(collection)
    old = bpy.context.view_layer.active_layer_collection
    bpy.context.view_layer.active_layer_collection = bpy.context.view_layer.layer_collection.children[collection.name]
    for i in range(count):
        a = math.tau * i / count + RNG.uniform(-0.018, 0.018)
        if broken and 2.0 < a < 2.65:
            continue
        r = radius + RNG.gauss(0, 1.2)
        pos = (math.cos(a) * r, math.sin(a) * r, RNG.gauss(0, 0.55))
        ico(f"BeltRock_{i:04d}", pos, RNG.uniform(0.06, 0.32), material, 1)
    bpy.context.view_layer.active_layer_collection = old


def add_comet(name, location, direction, ice_mat, tail_mat):
    nucleus = ico(name, location, 0.55, ice_mat, 3)
    direction = Vector(direction).normalized()
    bpy.ops.mesh.primitive_cone_add(vertices=48, radius1=2.2, radius2=0.18, depth=16,
                                    location=Vector(location) + direction * 8)
    tail = bpy.context.object
    tail.name = name + "_LuminousTail"
    tail.data.materials.append(tail_mat)
    tail.rotation_mode = "QUATERNION"
    tail.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(direction)
    return nucleus, tail


def add_nebula(volume_mat):
    collection = bpy.data.collections.new("Ion_Nebula")
    bpy.context.scene.collection.children.link(collection)
    for i in range(11):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3, radius=1, location=(RNG.uniform(-12, 8), RNG.uniform(18, 34), RNG.uniform(-8, 9)))
        obj = bpy.context.object
        obj.name = f"NebulaCloud_{i:02d}"
        obj.scale = (RNG.uniform(6, 14), RNG.uniform(3, 8), RNG.uniform(4, 10))
        obj.data.materials.append(volume_mat)


def add_camera():
    bpy.ops.object.camera_add(location=(58, -67, 38))
    cam = bpy.context.object
    cam.name = "Camera_CinematicOverview"
    cam.data.lens = 48
    cam.data.sensor_width = 36
    target = Vector((2, 5, 1))
    cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.camera = cam
    return cam


def camera_at(name, location, target, lens):
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.object
    cam.name = name
    cam.data.lens = lens
    cam.data.sensor_width = 36
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()
    return cam


def animate_spin(obj, frames=600, turns=1.0):
    obj.rotation_mode = "XYZ"
    obj.keyframe_insert(data_path="rotation_euler", frame=1)
    obj.rotation_euler.z += math.tau * turns
    obj.keyframe_insert(data_path="rotation_euler", frame=frames)


def animate_orbit(obj, center, frames, turns=1.0):
    pivot = bpy.data.objects.new(obj.name + "_OrbitPivot", None)
    pivot.empty_display_type = "CIRCLE"
    pivot.empty_display_size = max(0.5, (obj.location - Vector(center)).length * 0.08)
    pivot.location = center
    bpy.context.collection.objects.link(pivot)
    world = obj.matrix_world.copy()
    obj.parent = pivot
    obj.matrix_world = world
    pivot.rotation_euler.z = 0
    pivot.keyframe_insert(data_path="rotation_euler", frame=1)
    pivot.rotation_euler.z = math.tau * turns
    pivot.keyframe_insert(data_path="rotation_euler", frame=frames)
    return pivot


def setup_world_and_compositor(scene):
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    bg.inputs["Color"].default_value = (0.00005, 0.0001, 0.00035, 1)
    bg.inputs["Strength"].default_value = 0.025
    scene.use_nodes = True
    tree = getattr(scene, "node_tree", None)
    modern_compositor = tree is None
    if tree is None:
        tree = bpy.data.node_groups.new("SpaceSystem_Compositor", "CompositorNodeTree")
        scene.compositing_node_group = tree
    nodes = tree.nodes
    links = tree.links
    nodes.clear()
    layers = nodes.new("CompositorNodeRLayers")
    glare = nodes.new("CompositorNodeGlare")
    if "Threshold" in glare.inputs:
        glare.inputs["Threshold"].default_value = 0.7
    if "Size" in glare.inputs:
        glare.inputs["Size"].default_value = 0.65
    if "Strength" in glare.inputs:
        glare.inputs["Strength"].default_value = 0.85
    links.new(layers.outputs["Image"], glare.inputs["Image"])
    if modern_compositor:
        tree.interface.new_socket(name="Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        composite = nodes.new("NodeGroupOutput")
        links.new(glare.outputs["Image"], composite.inputs["Image"])
    else:
        composite = nodes.new("CompositorNodeComposite")
        links.new(glare.outputs["Image"], composite.inputs["Image"])


def organize_scene():
    rules = {
        "SYS_Stars": ("Primary_", "Starfield_"),
        "SYS_Planets": ("Volcanic_World", "Ocean_World", "Ringed_Gas_Giant", "Ice_World"),
        "SYS_Orbits": ("_Orbit",),
        "SYS_Comets": ("Comet_",),
        "SYS_FracturedWorld": ("FracturedWorld_",),
        "SYS_Cameras": ("Camera_",),
    }
    for collection_name, prefixes in rules.items():
        collection = bpy.data.collections.get(collection_name) or bpy.data.collections.new(collection_name)
        if not collection.name in bpy.context.scene.collection.children:
            bpy.context.scene.collection.children.link(collection)
        for obj in list(bpy.context.scene.objects):
            if any(token in obj.name for token in prefixes):
                if obj.name not in collection.objects:
                    collection.objects.link(obj)
                for source in list(obj.users_collection):
                    if source != collection and source == bpy.context.scene.collection:
                        source.objects.unlink(obj)


def export_unreal_preview():
    bpy.ops.object.select_all(action="DESELECT")
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH" and not obj.name.startswith("Starfield_") and "Nebula" not in obj.name:
            obj.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(GLTF), export_format="GLB", use_selection=True,
                              export_materials="EXPORT", export_animations=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    clear_scene()
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.world.color = (0.0002, 0.0004, 0.001)
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.frame_start = 1
    scene.frame_end = 600
    scene.render.fps = 30
    setup_world_and_compositor(scene)

    gold = mat_principled("M_Star_Gold", (0.9, 0.11, 0.008), 0, 0.2, (1.0, 0.16, 0.01), 18)
    star_white = mat_principled("M_Star_Core", (1, 0.72, 0.28), 0, 0.15, (1, 0.42, 0.08), 10)
    ocean = mat_planet("M_Planet_Ocean", (0.002, 0.015, 0.055), (0.02, 0.35, 0.72), 3.8)
    volcanic = mat_planet("M_Planet_Volcanic", (0.006, 0.002, 0.001), (1.0, 0.055, 0.004), 7.5, 0.5, 1.5)
    ice = mat_planet("M_Planet_Ice", (0.04, 0.12, 0.18), (0.55, 0.9, 1.0), 5.2)
    gas = mat_planet("M_Gas_Giant", (0.055, 0.01, 0.08), (0.85, 0.3, 0.08), 2.1, 0.08)
    rock = mat_principled("M_Asteroid", (0.055, 0.045, 0.038), 0.12, 0.82)
    ring = mat_principled("M_Ring_Ice", (0.18, 0.24, 0.27), 0.03, 0.5)
    orbit = mat_principled("M_OrbitGuide", (0.01, 0.08, 0.12), 0, 0.35, (0.01, 0.2, 0.35), 2.0)
    stars = mat_principled("M_Starfield", (0.2, 0.3, 0.5), 0, 0.2, (0.5, 0.75, 1), 15)
    nebula = mat_volume("M_Ion_Nebula", (0.10, 0.008, 0.30), 0.008, 0.12)
    tail = mat_volume("M_Comet_Tail", (0.08, 0.34, 0.72), 0.018, 0.45)

    add_starfield(stars)
    star = uv_sphere("Primary_Golden_Giant", (0, 0, 0), 6.2, gold, 96, 48)
    uv_sphere("Primary_Star_Core", (0, 0, 0), 5.85, star_white, 96, 48)
    bpy.ops.object.light_add(type="POINT", location=(0, 0, 0))
    bpy.context.object.name = "Primary_Stellar_Light"
    bpy.context.object.data.energy = 8500
    bpy.context.object.data.color = (1.0, 0.35, 0.08)

    archetypes = [
        ("Volcanic_World", volcanic, (1.25, 2.15), False),
        ("Ocean_World", ocean, (1.75, 2.85), False),
        ("Ringed_Gas_Giant", gas, (3.8, 5.6), True),
        ("Ice_World", ice, (1.35, 2.5), False),
    ]
    planet_count = RNG.randint(3, 7)
    chosen = [RNG.choice(archetypes) for _ in range(planet_count)]
    # Ensure every generated system has at least one visually dominant world.
    if not any(item[3] for item in chosen):
        chosen[RNG.randrange(planet_count)] = archetypes[2]
    planets = []
    next_orbit = RNG.uniform(12.0, 15.0)
    for index, (base_name, material, size_range, ringed) in enumerate(chosen, 1):
        size = RNG.uniform(*size_range)
        name = f"{base_name}_{index:02d}"
        planets.append((name, next_orbit, RNG.uniform(0, math.tau), size, material, ringed))
        next_orbit += RNG.uniform(max(5.5, size * 2.0), max(8.5, size * 2.8))

    generated = {"seed": SEED, "planets": [], "features": []}
    for index, (name, radius, angle, size, material, ringed) in enumerate(planets):
        tilt = (math.radians(RNG.uniform(-9, 9)), math.radians(RNG.uniform(-6, 6)), 0)
        orbit_curve(name + "_Orbit", radius, orbit, tilt)
        pos = Vector((math.cos(angle) * radius, math.sin(angle) * radius, math.sin(tilt[0]) * radius * 0.35))
        planet = uv_sphere(name, pos, size, material)
        planet.rotation_euler = (RNG.random(), RNG.random(), RNG.random())
        if ringed:
            torus(name + "_Ring_A", pos, size * 1.75, size * 0.10, ring, (0.28, 0.12, 0.5))
            torus(name + "_Ring_B", pos, size * 2.05, size * 0.055, ring, (0.28, 0.12, 0.5))
        moon_count = RNG.randint(0, 4)
        for moon_i in range(moon_count):
            ma = angle + 1.1 + moon_i * 1.9
            mr = size * (1.65 + moon_i * 0.72)
            mpos = pos + Vector((math.cos(ma) * mr, math.sin(ma) * mr, math.sin(ma * 1.7) * mr * 0.22))
            uv_sphere(f"{name}_Moon_{moon_i + 1}", mpos, size * RNG.uniform(0.12, 0.24), ice if moon_i % 2 else rock, 32, 16)
        generated["planets"].append({
            "name": name, "archetype": name.rsplit("_", 1)[0], "orbit_radius": round(radius, 3),
            "size": round(size, 3), "moons": moon_count, "ringed": ringed,
        })

    if RNG.random() < 0.8:
        belt_radius = RNG.uniform(18.0, max(20.0, next_orbit - 4.0))
        belt_count = RNG.randint(360, 780)
        add_belt(rock, belt_radius, belt_count, broken=RNG.random() < 0.55)
        generated["features"].append({"type": "asteroid_belt", "radius": round(belt_radius, 3), "objects": belt_count})
    if RNG.random() < 0.7:
        add_nebula(nebula)
        generated["features"].append({"type": "ion_nebula", "clouds": 11})
    comet_count = RNG.randint(0, 3)
    for comet_index in range(comet_count):
        name = f"Comet_{comet_index + 1:02d}"
        location = (RNG.uniform(-48, 48), RNG.uniform(-38, 38), RNG.uniform(-18, 22))
        direction = (RNG.uniform(-1, 1), RNG.uniform(-1, 1), RNG.uniform(-0.35, 0.35))
        add_comet(name, location, direction, ice, tail)
    if comet_count:
        generated["features"].append({"type": "comets", "count": comet_count})

    # Fractured-world debris vignette.
    if RNG.random() < 0.55:
        fractured_center = Vector((RNG.uniform(-28, -16), RNG.uniform(12, 25), RNG.uniform(-4, 9)))
        fragment_count = RNG.randint(20, 48)
        for i in range(fragment_count):
            offset = Vector((RNG.uniform(-1, 1), RNG.uniform(-1, 1), RNG.uniform(-1, 1))).normalized() * RNG.uniform(2.2, 6.0)
            ico(f"FracturedWorld_Fragment_{i:02d}", fractured_center + offset, RNG.uniform(0.18, 0.75), volcanic, 2)
        generated["features"].append({"type": "fractured_world", "fragments": fragment_count})

    add_camera()
    camera_at("Camera_PlanetaryApproach", (25, -39, 8), (5, 5, 0), 62)
    camera_at("Camera_AnomalySurvey", (-45, 46, 23), (-12, 22, 5), 54)
    camera_at("Camera_CometTracking", (53, -40, 23), (42, -25, 17), 80)

    animate_spin(star, 600, 0.35)
    for obj in list(scene.objects):
        if obj.type == "MESH" and any(key in obj.name for key in ("_World", "Gas_Giant")) and "Moon" not in obj.name:
            animate_spin(obj, 600, RNG.uniform(0.6, 1.8))
        if "Moon_" in obj.name and obj.type == "MESH":
            parent_name = obj.name.split("_Moon_")[0]
            parent = bpy.data.objects.get(parent_name)
            if parent:
                animate_orbit(obj, parent.location, 240 + RNG.randrange(0, 220), RNG.choice((1.0, -1.0)))
        if obj.name.startswith("Comet_"):
            obj.keyframe_insert(data_path="location", frame=1)
            obj.location += Vector((RNG.uniform(-9, 9), RNG.uniform(-6, 6), RNG.uniform(-3, 3)))
            obj.keyframe_insert(data_path="location", frame=600)

    organize_scene()
    scene.render.filepath = str(PREVIEW)
    scene["ginnungagap_asset"] = "Procedural Space Systems Master"
    scene["generation_seed"] = str(SEED)
    scene["features"] = json.dumps(generated, separators=(",", ":"))
    MANIFEST.write_text(json.dumps(generated, indent=2), encoding="utf-8")
    bpy.ops.render.render(write_still=True)
    export_unreal_preview()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    print(f"Saved {BLEND}")
    print(f"Rendered {PREVIEW}")
    print(f"Generation seed: {SEED}")


main()
