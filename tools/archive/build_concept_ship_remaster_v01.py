"""Build clean concept-authority ship remasters directly from authored Blender geometry.

Run once per ship with ``GINNUNGAGAP_SHIP_REMASTER`` set to one of the keys in
``SHIP_SPECS``. The script deliberately bypasses RealityScan: it isolates the
authored hard-surface collections, enforces the dimensions printed on the
concept board, applies a restrained industrial material treatment, exports a
GLB, and renders beauty/orthographic validation views.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

import bpy
from mathutils import Matrix, Vector


PROJECT = Path(__file__).resolve().parents[1]
OUT_ROOT = PROJECT / "Art" / "Ships" / "Exterior" / "ConceptRemasterV01"
SHIP_KEY = os.environ.get("GINNUNGAGAP_SHIP_REMASTER", "SmallUtilityEscort")

SHIP_SPECS = {
    "SmallUtilityEscort": {
        "source": PROJECT
        / "Art/Ships/Exterior/ConceptMatch/SmallUtilityEscort/SmallUtilityEscort_ConceptMatch.blend1",
        "collections": {
            "01_PrimaryHull",
            "02_RecessedServiceHangar",
            "03_SixEngineDriveDistrict",
            "04_ConformalArmorAndStructure",
            "05_CommandDockingSensors",
            "06_ScaleCuesAndSurfaceStory",
            "07_ProductionSurfacePass",
        },
        "dimensions_m": (900.0, 125.0, 250.0),
        "concept": "docs/concept-art/reference/ships/small-utility-escort-exterior.png",
    },
    "MilitaryCorvette": {
        "source": PROJECT / "Art/Ships/Exterior/ConceptMatch/FleetCapitalConceptMatch.blend1",
        "collections": {
            "01_ArmoredHull",
            "02_ArmorAndWaist",
            "03_4x4DriveDistrict",
            "04_DualHangars",
            "05_ArmoredCitadel",
            "06_DefenseTerraces",
            "07_BowArmor",
        },
        "dimensions_m": (2400.0, 430.0, 620.0),
        "concept": "docs/concept-art/reference/ships/medium-military-corvette-exterior.png",
    },
    "ExpeditionCarrier": {
        "source": PROJECT / "Art/Ships/Exterior/ConceptMatch/FleetCapitalConceptMatch.blend1",
        "collections": {
            "01_CivicArmoredSpine",
            "02_ArmorAndServiceWaist",
            "03_TwelveDriveDistrict",
            "04_ConcourseHangars",
            "05_CommandCity",
            "06_DefenseAndSensors",
            "07_ProtectedHabitats",
        },
        "dimensions_m": (6500.0, 1400.0, 1800.0),
        "concept": "docs/concept-art/reference/ships/large-expedition-carrier-exterior.png",
    },
}


def iter_world_corners(obj: bpy.types.Object):
    for corner in obj.bound_box:
        yield obj.matrix_world @ Vector(corner)


def bounds(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    points = [point for obj in objects for point in iter_world_corners(obj)]
    if not points:
        raise RuntimeError(f"No renderable geometry selected for {SHIP_KEY}")
    return (
        Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points))),
        Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points))),
    )


def select_ship_geometry(collection_names: set[str]) -> list[bpy.types.Object]:
    keep = []
    for obj in list(bpy.data.objects):
        member_names = {collection.name for collection in obj.users_collection}
        if (
            obj.type in {"MESH", "CURVE"}
            and member_names.intersection(collection_names)
            and obj.name != "Decal_HullID"
        ):
            keep.append(obj)
        elif obj.type in {"MESH", "CURVE", "CAMERA", "LIGHT", "EMPTY"}:
            bpy.data.objects.remove(obj, do_unlink=True)
    return keep


def enforce_dimensions(
    objects: list[bpy.types.Object], target: tuple[float, float, float]
) -> None:
    minimum, maximum = bounds(objects)
    center = (minimum + maximum) * 0.5
    size = maximum - minimum
    factors = Vector((target[0] / size.x, target[1] / size.y, target[2] / size.z))
    transform = Matrix.Diagonal((factors.x, factors.y, factors.z, 1.0)) @ Matrix.Translation(
        -center
    )
    for obj in objects:
        obj.matrix_world = transform @ obj.matrix_world
    bpy.context.view_layer.update()


def principled(material: bpy.types.Material):
    if not material.use_nodes:
        material.use_nodes = True
    return next(
        (node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED"), None
    )


def set_input(node, names: tuple[str, ...], value) -> None:
    for name in names:
        socket = node.inputs.get(name)
        if socket is not None:
            socket.default_value = value
            return


def set_material(
    name: str,
    color: tuple[float, float, float, float],
    metallic: float,
    roughness: float,
    emission: tuple[float, float, float, float] | None = None,
    emission_strength: float = 0.0,
) -> None:
    material = bpy.data.materials.get(name)
    if material is None:
        return
    node = principled(material)
    if node is None:
        return
    set_input(node, ("Base Color",), color)
    set_input(node, ("Metallic",), metallic)
    set_input(node, ("Roughness",), roughness)
    if emission is not None:
        set_input(node, ("Emission Color", "Emission"), emission)
        set_input(node, ("Emission Strength",), emission_strength)


def remaster_materials() -> None:
    set_material("M_Escort_Armor", (0.32, 0.35, 0.38, 1.0), 0.78, 0.26)
    set_material("M_Escort_ArmorDark", (0.07, 0.085, 0.10, 1.0), 0.82, 0.22)
    set_material("M_Escort_Structure", (0.025, 0.032, 0.04, 1.0), 0.88, 0.2)
    set_material("M_Escort_SafetyOrange", (0.95, 0.19, 0.025, 1.0), 0.48, 0.24)
    set_material("M_Escort_Thermal", (0.035, 0.045, 0.055, 1.0), 0.7, 0.35)
    set_material("M_Escort_Glass", (0.015, 0.055, 0.085, 1.0), 0.45, 0.12)
    set_material(
        "M_Escort_BlueLight",
        (0.01, 0.15, 0.3, 1.0),
        0.25,
        0.18,
        (0.02, 0.48, 1.0, 1.0),
        14.0,
    )
    set_material(
        "M_Escort_Drive",
        (0.025, 0.06, 0.09, 1.0),
        0.72,
        0.2,
        (0.01, 0.22, 0.8, 1.0),
        8.0,
    )
    set_material("M_Decal_White", (0.7, 0.73, 0.75, 1.0), 0.35, 0.35)
    set_material("M_Decal_Red", (0.65, 0.025, 0.015, 1.0), 0.35, 0.3)
    set_material("M_Heat_Discoloration", (0.14, 0.045, 0.025, 1.0), 0.68, 0.38)


def create_sun(name: str, direction: tuple[float, float, float], energy: float, color):
    data = bpy.data.lights.new(name=name, type="SUN")
    data.energy = energy
    data.color = color
    data.angle = math.radians(8.0)
    obj = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = Vector(direction) * 1000.0
    obj.rotation_euler = (-obj.location).to_track_quat("-Z", "Y").to_euler()


def setup_lighting() -> None:
    world = bpy.context.scene.world or bpy.data.worlds.new("RemasterWorld")
    bpy.context.scene.world = world
    world.use_nodes = True
    background = world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.0025, 0.004, 0.007, 1.0)
    background.inputs["Strength"].default_value = 0.28
    create_sun("Key_Sun", (0.65, -1.0, 0.8), 3.2, (1.0, 0.88, 0.74))
    create_sun("Fill_Sun", (-0.45, -1.0, 0.15), 1.75, (0.36, 0.58, 1.0))
    create_sun("Rim_Sun", (-0.8, 0.75, 1.0), 2.1, (0.22, 0.52, 1.0))


def look_at(camera: bpy.types.Object, target: Vector) -> None:
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()


def make_camera(name: str, location: Vector, target: Vector, ortho_scale: float):
    data = bpy.data.cameras.new(name)
    data.type = "ORTHO"
    data.ortho_scale = ortho_scale
    data.lens = 58.0
    data.clip_start = 0.1
    data.clip_end = 100000.0
    camera = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(camera)
    camera.location = location
    look_at(camera, target)
    return camera


def render_views(output: Path, size: Vector, center: Vector) -> dict[str, str]:
    scene = bpy.context.scene
    length, beam, height = size
    views = {
        "Beauty": (
            center + Vector((-length * 0.58, -length * 0.88, height * 1.22)),
            max(length / 1.15, height * 1.8),
        ),
        "Side": (
            center + Vector((0.0, -length * 1.4, 0.0)),
            max(length / 1.3, height * 1.5),
        ),
        "Top": (
            center + Vector((0.0, 0.0, length * 1.4)),
            max(length / 1.3, beam * 1.5),
        ),
        "Rear": (
            center + Vector((-length * 1.4, 0.0, 0.0)),
            max(height * 1.4, beam / 1.45),
        ),
    }
    rendered = {}
    for view_name, (location, scale) in views.items():
        camera = make_camera(f"CAM_{view_name}", location, center, scale)
        scene.camera = camera
        path = output / f"{SHIP_KEY}_RemasterV01_{view_name}.png"
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        rendered[view_name] = str(path)
    return rendered


def export_glb(output: Path, objects: list[bpy.types.Object]) -> Path:
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.hide_render = False
        obj.hide_set(False)
        obj.select_set(True)
    bpy.context.view_layer.objects.active = objects[0]
    path = output / f"{SHIP_KEY}_RemasterV01.glb"
    bpy.ops.export_scene.gltf(
        filepath=str(path),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
    )
    return path


def main() -> None:
    if SHIP_KEY not in SHIP_SPECS:
        raise RuntimeError(f"Unknown ship remaster key: {SHIP_KEY}")
    spec = SHIP_SPECS[SHIP_KEY]
    source = Path(spec["source"])
    if not source.exists():
        raise RuntimeError(f"Authored source missing: {source}")
    bpy.ops.wm.open_mainfile(filepath=str(source))
    objects = select_ship_geometry(set(spec["collections"]))
    enforce_dimensions(objects, tuple(spec["dimensions_m"]))
    remaster_materials()
    setup_lighting()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.7

    output = OUT_ROOT / SHIP_KEY
    output.mkdir(parents=True, exist_ok=True)
    minimum, maximum = bounds(objects)
    size = maximum - minimum
    center = (minimum + maximum) * 0.5
    glb = export_glb(output, objects)
    blend = output / f"{SHIP_KEY}_RemasterV01.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    rendered = render_views(output, size, center)
    manifest = {
        "version": 1,
        "ship": SHIP_KEY,
        "method": "Direct hard-surface remaster from authored concept-match geometry",
        "concept_authority": spec["concept"],
        "source": str(source.relative_to(PROJECT)).replace("\\", "/"),
        "source_collections": sorted(spec["collections"]),
        "object_count": len(objects),
        "dimensions_m": [round(value, 3) for value in size],
        "blend": str(blend.relative_to(PROJECT)).replace("\\", "/"),
        "glb": str(glb.relative_to(PROJECT)).replace("\\", "/"),
        "renders": {
            key: str(Path(value).relative_to(PROJECT)).replace("\\", "/")
            for key, value in rendered.items()
        },
        "promotion_status": "Visual review required before Unreal import",
    }
    (output / "RemasterManifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("REMASTER_COMPLETE", json.dumps(manifest))


if __name__ == "__main__":
    main()
