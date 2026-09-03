"""Inventory and render the exterior Fab donor ships for Unreal kitbashing."""
from pathlib import Path
import json
import math

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
DONORS = {
    "BC304": ROOT / "Art/Ships/Exterior/FabDonors/BC304/stargate_bc_304.glb",
    "Spaceship4": ROOT / "Art/Ships/Exterior/FabDonors/Spaceship4/spaceship_4.glb",
}
REPORT = ROOT / "Saved/Reports/FabShipDonorInventory.json"


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def look_at(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


def bounds(objects):
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    low = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    high = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    return low, high, high - low


def inspect(name, source):
    clear_scene()
    bpy.ops.import_scene.gltf(filepath=str(source))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if name == "Spaceship4":
        def hierarchy_names(obj):
            names = []
            while obj is not None:
                names.append(obj.name.lower())
                obj = obj.parent
            return names
        rejected = [obj for obj in meshes if any("emit" in node_name for node_name in hierarchy_names(obj))]
        for obj in rejected:
            bpy.data.objects.remove(obj, do_unlink=True)
        meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"No meshes imported from {source}")
    low, high, size = bounds(meshes)
    center = (low + high) * 0.5
    long_axis = max(range(3), key=lambda index: size[index])
    length = size[long_axis]

    components = []
    for obj in meshes:
        obj.data.calc_loop_triangles()
        dimensions = list(obj.dimensions)
        components.append({
            "name": obj.name,
            "parent": obj.parent.name if obj.parent else None,
            "location": list(obj.location),
            "dimensions": dimensions,
            "vertices": len(obj.data.vertices),
            "triangles": len(obj.data.loop_triangles),
            "volume_proxy": dimensions[0] * dimensions[1] * dimensions[2],
        })
    components.sort(key=lambda item: item["volume_proxy"], reverse=True)

    clay = bpy.data.materials.new(f"M_{name}_DonorClay")
    clay.use_nodes = True
    bsdf = clay.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.13, 0.19, 0.27, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.18
    bsdf.inputs["Roughness"].default_value = 0.38
    for obj in meshes:
        obj.data.materials.clear()
        obj.data.materials.append(clay)
        for polygon in obj.data.polygons:
            polygon.use_smooth = True

    world = bpy.context.scene.world or bpy.data.worlds.new("DonorWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.0015, 0.003, 0.008, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.24

    camera_data = bpy.data.cameras.new("CAM_Donor")
    camera = bpy.data.objects.new("CAM_Donor", camera_data)
    bpy.context.collection.objects.link(camera)
    if long_axis == 0:
        offset = Vector((length * 0.35, -length * 2.15, length * 0.45))
    else:
        offset = Vector((length * 2.15, length * 0.35, length * 0.45))
    camera.location = center + offset
    camera.data.lens = 58
    camera.data.clip_start = max(0.01, length * 0.0001)
    camera.data.clip_end = length * 6.0
    look_at(camera, center)
    bpy.context.scene.camera = camera

    for light_name, energy, color, direction in (
        ("Key", 4.2, (0.78, 0.88, 1.0), Vector((0.2, -0.4, 0.8))),
        ("Rim", 2.1, (1.0, 0.34, 0.11), Vector((-0.5, 0.3, 0.25))),
    ):
        data = bpy.data.lights.new(light_name, "SUN")
        light = bpy.data.objects.new(light_name, data)
        bpy.context.collection.objects.link(light)
        light.location = center + direction * length
        data.energy = energy
        data.angle = math.radians(9.0)
        data.color = color
        look_at(light, center)

    output = source.parent / f"{name}_Donor_ThreeQuarter.png"
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.filepath = str(output)
    bpy.ops.render.render(write_still=True)

    return {
        "source": str(source),
        "objects": len(meshes),
        "vertices": sum(item["vertices"] for item in components),
        "triangles": sum(item["triangles"] for item in components),
        "bounds": {"min": list(low), "max": list(high), "size": list(size)},
        "long_axis": "XYZ"[long_axis],
        "components": components,
        "render": str(output),
    }


payload = {name: inspect(name, source) for name, source in DONORS.items()}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({name: {key: value for key, value in data.items() if key != "components"} for name, data in payload.items()}, indent=2))
