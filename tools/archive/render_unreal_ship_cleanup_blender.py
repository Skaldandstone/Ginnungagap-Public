"""Render neutral-clay reviews from Unreal exports or their source GLBs."""
from pathlib import Path
import math
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
EXPORT_ROOT = ROOT / "Art/Ships/Exterior/UnrealSculptReview/Exported"
SOURCE_ROOT = ROOT / "Art/Ships/Exterior/UnrealSculptBase"
OUTPUT = ROOT / "Art/Ships/Exterior/UnrealSculptReview"
OUTPUT.mkdir(parents=True, exist_ok=True)

SOURCE_GLB = {
    "MilitaryCorvette": SOURCE_ROOT / "SM_Ship_MilitaryCorvette_Shipping.glb",
    "ExpeditionCarrier": SOURCE_ROOT / "SM_Ship_ExpeditionCarrier_Shipping.glb",
}


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


def clay_material():
    material = bpy.data.materials.new("M_UnrealSculpt_Clay")
    material.diffuse_color = (0.105, 0.135, 0.17, 1.0)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.12, 0.18, 0.26, 1.0)
    bsdf.inputs["Metallic"].default_value = 0.2
    bsdf.inputs["Roughness"].default_value = 0.4
    return material


def render_ship(ship):
    clear_scene()
    imported = []
    exported_fbx = sorted((EXPORT_ROOT / ship).glob("*.fbx"))
    for fbx in exported_fbx:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.fbx(filepath=str(fbx), use_custom_normals=True, automatic_bone_orientation=False)
        imported.extend(obj for obj in set(bpy.data.objects) - before if obj.type == "MESH")
    if not imported:
        glb = SOURCE_GLB[ship]
        if not glb.exists():
            raise RuntimeError(f"Missing Unreal sculpt source GLB: {glb}")
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(glb))
        imported.extend(obj for obj in set(bpy.data.objects) - before if obj.type == "MESH")
    if not imported:
        raise RuntimeError(f"No review meshes imported for {ship}")
    material = clay_material()
    for obj in imported:
        obj.data.materials.clear()
        obj.data.materials.append(material)
        for polygon in obj.data.polygons:
            polygon.use_smooth = True

    low, high, size = combined_bounds(imported)
    center = (low + high) * 0.5
    length = size.x

    world = bpy.context.scene.world or bpy.data.worlds.new("SculptReviewWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.0015, 0.003, 0.008, 1.0)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.22

    camera_data = bpy.data.cameras.new("CAM_UnrealSculptReview")
    camera = bpy.data.objects.new("CAM_UnrealSculptReview", camera_data)
    bpy.context.collection.objects.link(camera)
    camera.location = center + Vector((length * 0.35, -length * 2.15, length * 0.45))
    camera.data.lens = 58
    camera.data.clip_start = max(0.1, length * 0.0001)
    camera.data.clip_end = length * 5.0
    look_at(camera, center)
    bpy.context.scene.camera = camera

    key_data = bpy.data.lights.new("Key", "SUN")
    key = bpy.data.objects.new("Key", key_data)
    bpy.context.collection.objects.link(key)
    key.location = center + Vector((length * 0.15, -length * 0.45, length * 0.65))
    key_data.energy = 4.0
    key_data.angle = math.radians(8.0)
    key_data.color = (0.78, 0.88, 1.0)
    look_at(key, center)

    rim_data = bpy.data.lights.new("Rim", "SUN")
    rim = bpy.data.objects.new("Rim", rim_data)
    bpy.context.collection.objects.link(rim)
    rim.location = center + Vector((-length * 0.36, length * 0.35, length * 0.22))
    rim_data.energy = 2.2
    rim_data.angle = math.radians(12.0)
    rim_data.color = (1.0, 0.34, 0.11)
    look_at(rim, center)

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.render.filepath = str(OUTPUT / f"{ship}_Cleanup01_ThreeQuarter.png")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT / f"{ship}_Cleanup01_Review.blend"))
    bpy.ops.render.render(write_still=True)


render_ship("MilitaryCorvette")
render_ship("ExpeditionCarrier")
