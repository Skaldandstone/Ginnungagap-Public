"""Render the Unreal Fab concept blockout geometry at approved ship proportions."""
from pathlib import Path
import math

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "Art/Ships/Exterior/UnrealSculptReview/FabConcept"
OUTPUT.mkdir(parents=True, exist_ok=True)
SHIPS = {
    "MilitaryCorvette": {
        "source": ROOT / "Art/Ships/Exterior/FabDonors/Spaceship4/SM_FabDonor_Spaceship4_Clean.glb",
        "meters": (2400.0, 430.0, 620.0),
    },
    "ExpeditionCarrier": {
        "source": ROOT / "Art/Ships/Exterior/FabDonors/BC304/SM_FabDonor_BC304_Clean.glb",
        "meters": (6500.0, 1400.0, 1800.0),
    },
}


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def look_at(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


def bounds(objects):
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    return low, high, high - low


def render_ship(name, config):
    clear_scene()
    bpy.ops.import_scene.gltf(filepath=str(config["source"]))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"No donor geometry in {config['source']}")
    low, high, size = bounds(meshes)
    if size.y > size.x and size.y > size.z:
        for obj in meshes:
            obj.rotation_euler.z += math.radians(90.0)
        bpy.context.view_layer.update()
        low, high, size = bounds(meshes)
    target = config["meters"]
    scale = (target[0] / size.x, target[1] / size.y, target[2] / size.z)
    center = (low + high) * 0.5
    for obj in meshes:
        obj.location -= center
        obj.scale.x *= scale[0]
        obj.scale.y *= scale[1]
        obj.scale.z *= scale[2]
    bpy.context.view_layer.update()
    low, high, size = bounds(meshes)
    center = (low + high) * 0.5
    length = size.x

    clay = bpy.data.materials.new(f"M_{name}_FabClay")
    clay.use_nodes = True
    bsdf = clay.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.16, 0.20, 0.25, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.24
    bsdf.inputs["Roughness"].default_value = 0.38
    for obj in meshes:
        obj.data.materials.clear()
        obj.data.materials.append(clay)
        for polygon in obj.data.polygons:
            polygon.use_smooth = True

    world = bpy.context.scene.world or bpy.data.worlds.new("FabConceptWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.0015, 0.003, 0.008, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.23

    camera_data = bpy.data.cameras.new("CAM_FabConcept")
    camera = bpy.data.objects.new("CAM_FabConcept", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = center + Vector((length * 0.35, -length * 2.15, length * 0.45))
    camera.data.lens = 58
    camera.data.clip_start = max(0.1, length * 0.0001)
    camera.data.clip_end = length * 6.0
    look_at(camera, center)
    bpy.context.scene.camera = camera

    for light_name, energy, color, direction in (
        ("Key", 4.3, (0.78, 0.88, 1.0), Vector((0.2, -0.4, 0.8))),
        ("Rim", 2.0, (1.0, 0.34, 0.11), Vector((-0.5, 0.3, 0.25))),
    ):
        data = bpy.data.lights.new(light_name, "SUN")
        light = bpy.data.objects.new(light_name, data)
        bpy.context.collection.objects.link(light)
        light.location = center + direction * length
        data.energy = energy
        data.angle = math.radians(9.0)
        data.color = color
        look_at(light, center)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.filepath = str(OUTPUT / f"{name}_FabConceptBlockout.png")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / f"{name}_FabConceptBlockout.blend"))
    bpy.ops.render.render(write_still=True)


for ship_name, ship_config in SHIPS.items():
    render_ship(ship_name, ship_config)
