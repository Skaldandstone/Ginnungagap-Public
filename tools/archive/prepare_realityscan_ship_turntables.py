"""Render photogrammetrically consistent ship turntables for RealityScan 2.2.

The exterior concept boards are design authority, but painted orthographic views are not
camera-consistent photogrammetry inputs.  The concept-matched GLBs provide a coherent proxy
surface derived from those boards.  This script performs a virtual capture of each proxy so
RealityScan can produce an independently reconstructed review mesh without touching production
assets.

Run with Blender, for example:
    blender --background --python tools/prepare_realityscan_ship_turntables.py
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_ROOT = ROOT / "Art" / "Ships" / "Exterior" / "RealityScan"

SHIPS = (
    {
        "name": "SmallUtilityEscort",
        "source": ROOT
        / "Art/Ships/Exterior/ConceptMatch/SmallUtilityEscort/SmallUtilityEscort_ConceptMatch.blend",
        "collection": "SM_Ship_SmallUtilityEscort_ConceptMatch",
        "concept": ROOT / "docs/concept-art/reference/ships/small-utility-escort-exterior.png",
        "dimensions_m": (1400.0, 260.0, 320.0),
    },
    {
        "name": "MilitaryCorvette",
        "source": ROOT
        / "Art/Ships/Exterior/ConceptMatch/ArtistV2/FleetCapitalShips_ArtistV2.blend",
        "collection": "SM_Ship_MilitaryCorvette_ConceptMatch",
        "concept": ROOT / "docs/concept-art/reference/ships/medium-military-corvette-exterior.png",
        "dimensions_m": (2400.0, 430.0, 620.0),
    },
    {
        "name": "ExpeditionCarrier",
        "source": ROOT
        / "Art/Ships/Exterior/ConceptMatch/ArtistV2/FleetCapitalShips_ArtistV2.blend",
        "collection": "SM_Ship_ExpeditionCarrier_ConceptMatch",
        "concept": ROOT / "docs/concept-art/reference/ships/large-expedition-carrier-exterior.png",
        "dimensions_m": (6500.0, 1400.0, 1800.0),
    },
)

AZIMUTHS_DEG = tuple(range(10, 360, 20))
ELEVATIONS_DEG = (-22, 22)
RENDER_SIZE = 640


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.images):
        for datablock in list(datablocks):
            if datablock.users == 0:
                datablocks.remove(datablock)


def mesh_objects() -> list[bpy.types.Object]:
    return [obj for obj in bpy.context.scene.objects if obj.type == "MESH" and not obj.hide_render]


def world_bounds(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    points = [obj.matrix_world @ Vector(corner) for obj in objects for corner in obj.bound_box]
    minimum = Vector(tuple(min(point[i] for point in points) for i in range(3)))
    maximum = Vector(tuple(max(point[i] for point in points) for i in range(3)))
    return minimum, maximum


def normalize_capture_scale(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    minimum, maximum = world_bounds(objects)
    center = (minimum + maximum) * 0.5
    maximum_dimension = max(maximum - minimum)
    scale = 20.0 / maximum_dimension

    # GLB scenes contain deep parent hierarchies.  Transforming every mesh would
    # compound scale down the tree and collapse small authored details.  Parent
    # only imported roots under one capture transform and preserve world matrices.
    imported_roots = [
        obj for obj in list(bpy.context.scene.objects) if obj.parent is None
    ]
    bpy.ops.object.empty_add(type="PLAIN_AXES", location=(0.0, 0.0, 0.0))
    capture_root = bpy.context.object
    capture_root.name = "RS_CaptureRoot"
    for obj in imported_roots:
        matrix_world = obj.matrix_world.copy()
        obj.parent = capture_root
        obj.matrix_world = matrix_world
    capture_root.scale = (scale, scale, scale)
    capture_root.location = -center * scale
    bpy.context.view_layer.update()
    return world_bounds(objects)


def apply_scan_palette(objects: list[bpy.types.Object]) -> None:
    """Replace dark GLB look-dev with feature-rich temporary capture materials."""
    colors = (
        (0.68, 0.72, 0.75, 1.0),
        (0.46, 0.51, 0.56, 1.0),
        (0.25, 0.31, 0.36, 1.0),
        (0.76, 0.38, 0.08, 1.0),
        (0.18, 0.38, 0.50, 1.0),
        (0.54, 0.48, 0.38, 1.0),
    )
    material = bpy.data.materials.new("M_RS_FeatureCapture")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    principled = nodes.get("Principled BSDF")
    object_info = nodes.new("ShaderNodeObjectInfo")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp_elements = ramp.color_ramp.elements
    ramp_elements[0].position = 0.0
    ramp_elements[0].color = colors[0]
    ramp_elements[1].position = 1.0
    ramp_elements[1].color = colors[-1]
    for index, color in enumerate(colors[1:-1], start=1):
        element = ramp_elements.new(index / (len(colors) - 1))
        element.color = color
    texture_coordinates = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 18.0
    noise.inputs["Detail"].default_value = 4.0
    noise.inputs["Roughness"].default_value = 0.68
    noise_ramp = nodes.new("ShaderNodeValToRGB")
    noise_ramp.color_ramp.elements[0].position = 0.28
    noise_ramp.color_ramp.elements[0].color = (0.22, 0.22, 0.22, 1.0)
    noise_ramp.color_ramp.elements[1].position = 0.72
    noise_ramp.color_ramp.elements[1].color = (1.0, 1.0, 1.0, 1.0)
    multiply = nodes.new("ShaderNodeMixRGB")
    multiply.blend_type = "MULTIPLY"
    multiply.inputs[0].default_value = 1.0

    links.new(object_info.outputs["Random"], ramp.inputs["Fac"])
    links.new(texture_coordinates.outputs["Generated"], noise.inputs["Vector"])
    links.new(noise.outputs["Fac"], noise_ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], multiply.inputs[1])
    links.new(noise_ramp.outputs["Color"], multiply.inputs[2])
    links.new(multiply.outputs["Color"], principled.inputs["Base Color"])
    principled.inputs["Metallic"].default_value = 0.12
    principled.inputs["Roughness"].default_value = 0.72
    if "Emission Color" in principled.inputs:
        links.new(multiply.outputs["Color"], principled.inputs["Emission Color"])
        principled.inputs["Emission Strength"].default_value = 0.08
    if "Coat Weight" in principled.inputs:
        principled.inputs["Coat Weight"].default_value = 0.08

    processed_meshes: set[int] = set()
    for obj in objects:
        mesh_key = obj.data.as_pointer()
        if mesh_key in processed_meshes:
            continue
        processed_meshes.add(mesh_key)
        obj.data.materials.clear()
        obj.data.materials.append(material)


def add_lighting(capture_radius: float) -> None:
    world = bpy.context.scene.world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.035, 0.042, 0.052, 1.0)
    background.inputs["Strength"].default_value = 1.6

    bpy.ops.object.light_add(type="SUN", location=(0.0, 0.0, capture_radius))
    sun = bpy.context.object
    sun.name = "RS_Sun"
    sun.data.energy = 3.0
    sun.rotation_euler = (math.radians(32.0), math.radians(-28.0), math.radians(-35.0))

    bpy.ops.object.light_add(type="AREA", location=(0.0, -capture_radius * 0.55, capture_radius * 0.55))
    key = bpy.context.object
    key.name = "RS_Key"
    key.data.energy = 1350.0
    key.data.shape = "DISK"
    key.data.size = capture_radius * 0.75
    key.rotation_euler = (Vector((0.0, 0.0, 0.0)) - key.location).to_track_quat("-Z", "Y").to_euler()

    bpy.ops.object.light_add(type="AREA", location=(-capture_radius * 0.35, capture_radius * 0.5, capture_radius * 0.15))
    fill = bpy.context.object
    fill.name = "RS_Fill"
    fill.data.energy = 900.0
    fill.data.color = (0.45, 0.62, 1.0)
    fill.data.size = capture_radius * 0.55
    fill.rotation_euler = (Vector((0.0, 0.0, 0.0)) - fill.location).to_track_quat("-Z", "Y").to_euler()

    bpy.ops.object.light_add(type="AREA", location=(capture_radius * 0.45, capture_radius * 0.35, -capture_radius * 0.25))
    rim = bpy.context.object
    rim.name = "RS_Rim"
    rim.data.energy = 1050.0
    rim.data.color = (1.0, 0.58, 0.28)
    rim.data.size = capture_radius * 0.45
    rim.rotation_euler = (Vector((0.0, 0.0, 0.0)) - rim.location).to_track_quat("-Z", "Y").to_euler()


def configure_render() -> None:
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = RENDER_SIZE
    scene.render.resolution_y = RENDER_SIZE
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.filepath = ""
    scene.view_settings.look = "AgX - Medium High Contrast"


def render_ship(ship: dict[str, object]) -> dict[str, object]:
    source = Path(ship["source"])
    concept = Path(ship["concept"])
    if not source.exists():
        raise FileNotFoundError(source)
    if not concept.exists():
        raise FileNotFoundError(concept)

    bpy.ops.wm.open_mainfile(filepath=str(source))
    collection_name = str(ship["collection"])
    collection = bpy.data.collections.get(collection_name)
    if collection is None:
        raise RuntimeError(f"Collection {collection_name} not found in {source}")
    keep_objects = set(collection.all_objects)
    for obj in list(bpy.context.scene.objects):
        if obj not in keep_objects:
            bpy.data.objects.remove(obj, do_unlink=True)
    objects = mesh_objects()
    if not objects:
        raise RuntimeError(f"No renderable meshes imported from {source}")

    minimum, maximum = normalize_capture_scale(objects)
    apply_scan_palette(objects)
    extents = maximum - minimum
    center = (minimum + maximum) * 0.5
    # A 58 mm square frame needs substantially more clearance than a typical
    # 16:9 beauty camera, especially for these long hulls.  This keeps the full
    # silhouette inside every frame while retaining enough surface pixels for SFM.
    radius = max(extents) * 2.6
    add_lighting(radius)
    configure_render()

    bpy.ops.object.camera_add(location=(0.0, -radius, radius * 0.25))
    camera = bpy.context.object
    camera.name = f"CAM_RS_{ship['name']}"
    camera.data.lens = 58.0
    camera.data.sensor_width = 36.0
    camera.data.clip_start = 0.01
    camera.data.clip_end = radius * 10.0
    bpy.context.scene.camera = camera

    input_dir = OUTPUT_ROOT / str(ship["name"]) / "InputFrames"
    input_dir.mkdir(parents=True, exist_ok=True)

    # Do not delete arbitrary user files. Only refresh frames produced by this script.
    for prior in input_dir.glob(f"{ship['name']}_RS_*.png"):
        prior.unlink()

    frames: list[dict[str, object]] = []
    frame_index = 0
    for elevation_deg in ELEVATIONS_DEG:
        elevation = math.radians(elevation_deg)
        horizontal = radius * math.cos(elevation)
        z = radius * math.sin(elevation)
        for azimuth_deg in AZIMUTHS_DEG:
            azimuth = math.radians(azimuth_deg)
            camera.location = center + Vector(
                (
                    horizontal * math.cos(azimuth),
                    horizontal * math.sin(azimuth),
                    z,
                )
            )
            camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
            frame_name = f"{ship['name']}_RS_{frame_index:03d}_A{azimuth_deg:03d}_E{elevation_deg:+03d}.png"
            frame_path = input_dir / frame_name
            bpy.context.scene.render.filepath = str(frame_path)
            bpy.ops.render.render(write_still=True)
            frames.append(
                {
                    "file": frame_name,
                    "azimuth_deg": azimuth_deg,
                    "elevation_deg": elevation_deg,
                }
            )
            frame_index += 1

    manifest = {
        "version": 1,
        "asset": ship["name"],
        "method": "RealityScan virtual capture of concept-matched coherent proxy",
        "design_authority": str(concept.relative_to(ROOT)).replace("\\", "/"),
        "proxy_source": str(source.relative_to(ROOT)).replace("\\", "/"),
        "proxy_collection": collection_name,
        "target_dimensions_m": ship["dimensions_m"],
        "capture_frame_count": len(frames),
        "render_size_px": [RENDER_SIZE, RENDER_SIZE],
        "normalized_proxy_bounds": [round(value, 6) for value in extents],
        "frames": frames,
    }
    manifest_path = input_dir.parent / "CaptureManifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    requested = {
        item.strip()
        for item in os.environ.get("GINNUNGAGAP_RS_SHIPS", "").split(",")
        if item.strip()
    }
    summaries = []
    for ship in SHIPS:
        if requested and ship["name"] not in requested:
            continue
        summaries.append(render_ship(ship))
        print(f"REALITYSCAN_CAPTURE_READY {ship['name']} {summaries[-1]['capture_frame_count']} frames")
    (OUTPUT_ROOT / "CaptureSummary.json").write_text(
        json.dumps(summaries, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
