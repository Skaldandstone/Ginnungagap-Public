"""Render neutral-clay reviews from the Unreal silhouette-pass FBX exports."""

from pathlib import Path
import math
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
EXPORT_ROOT = ROOT / "Art/Ships/Exterior/UnrealSculptReview/Silhouette01/Exported"
OUTPUT = ROOT / "Art/Ships/Exterior/UnrealSculptReview/Silhouette01"
OUTPUT.mkdir(parents=True, exist_ok=True)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def look_at(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


def combined_bounds(objects):
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    low = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
    high = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
    return low, high, high - low


def render_ship(ship):
    clear_scene()
    imported = []
    for fbx in sorted((EXPORT_ROOT / ship).glob("*.fbx")):
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(
            filepath=str(fbx), use_custom_normals=False, automatic_bone_orientation=False
        )
        imported.extend(obj for obj in set(bpy.data.objects) - before if obj.type == "MESH")
    if not imported:
        raise RuntimeError(f"No silhouette review meshes imported for {ship}")

    material = bpy.data.materials.new("M_UnrealSilhouette_Clay")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.105, 0.16, 0.235, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.18
    bsdf.inputs["Roughness"].default_value = 0.42
    for obj in imported:
        obj.data.materials.clear()
        obj.data.materials.append(material)
        for polygon in obj.data.polygons:
            polygon.use_smooth = True

    low, high, size = combined_bounds(imported)
    center = (low + high) * 0.5
    length = size.x
    world = bpy.context.scene.world or bpy.data.worlds.new("SilhouetteReviewWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.0015, 0.003, 0.008, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.22

    camera_data = bpy.data.cameras.new("CAM_SilhouetteReview")
    camera = bpy.data.objects.new("CAM_SilhouetteReview", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = center + Vector((length * 0.34, -length * 2.12, length * 0.46))
    camera.data.lens = 58
    camera.data.clip_start = max(0.1, length * 0.0001)
    camera.data.clip_end = length * 5.0
    look_at(camera, center)
    bpy.context.scene.camera = camera

    for name, offset, energy, color, angle in (
        ("Key", (0.15, -0.45, 0.65), 4.0, (0.78, 0.88, 1.0), 8.0),
        ("Rim", (-0.36, 0.35, 0.22), 2.2, (1.0, 0.34, 0.11), 12.0),
    ):
        data = bpy.data.lights.new(name, "SUN")
        light = bpy.data.objects.new(name, data)
        bpy.context.collection.objects.link(light)
        light.location = center + Vector(tuple(length * value for value in offset))
        data.energy = energy
        data.angle = math.radians(angle)
        data.color = color
        look_at(light, center)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.filepath = str(OUTPUT / f"{ship}_Silhouette01_ThreeQuarter.png")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / f"{ship}_Silhouette01_Review.blend"))
    bpy.ops.render.render(write_still=True)


render_ship("MilitaryCorvette")
render_ship("ExpeditionCarrier")
