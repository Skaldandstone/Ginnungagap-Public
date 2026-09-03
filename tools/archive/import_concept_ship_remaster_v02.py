"""Import the concept-authored V02 fleet into an isolated Unreal review namespace."""

from __future__ import annotations

import json
import os
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
VERSION = int(os.environ.get("GINNUNGAGAP_SHIP_REMASTER_VERSION", "2"))
TAG = f"V{VERSION:02d}"
REPORT = PROJECT / f"Saved/Reports/ConceptShipRemaster{TAG}Import.json"
ROOT = f"/Game/Assets/Ships/Exterior/ConceptRemaster{TAG}"
MAP_ROOT = f"/Game/Assets/Maps/ShipExterior/ConceptRemaster{TAG}"

SHIPS = (
    ("SmallUtilityEscort", (90000.0, 12500.0, 25000.0), "docs/concept-art/reference/ships/small-utility-escort-exterior.png"),
    ("MilitaryCorvette", (240000.0, 43000.0, 62000.0), "docs/concept-art/reference/ships/medium-military-corvette-exterior.png"),
    ("ExpeditionCarrier", (650000.0, 140000.0, 180000.0), "docs/concept-art/reference/ships/large-expedition-carrier-exterior.png"),
)


def import_ship(key: str, authority: str):
    source = PROJECT / f"Art/Ships/Exterior/ConceptRemaster{TAG}" / key / f"{key}_Remaster{TAG}.glb"
    if not source.exists():
        raise RuntimeError(f"Missing V02 GLB: {source}")
    destination = f"{ROOT}/{key}"
    unreal.EditorAssetLibrary.make_directory(destination)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(source))
    task.set_editor_property("destination_path", destination)
    task.set_editor_property("destination_name", f"SM_{key}_ConceptRemaster{TAG}")
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", False)
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("import_materials", True)
    options.set_editor_property("import_textures", True)
    options.static_mesh_import_data.set_editor_property("combine_meshes", True)
    options.static_mesh_import_data.set_editor_property("generate_lightmap_u_vs", True)
    options.static_mesh_import_data.set_editor_property("auto_generate_collision", False)
    options.static_mesh_import_data.set_editor_property("convert_scene", True)
    options.static_mesh_import_data.set_editor_property("convert_scene_unit", True)
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    meshes = []
    for path in unreal.EditorAssetLibrary.list_assets(destination, recursive=True, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if isinstance(asset, unreal.StaticMesh):
            meshes.append(asset)
    if len(meshes) != 1:
        raise RuntimeError(f"V02 import for {key} must produce one combined StaticMesh; found {len(meshes)}")
    mesh = meshes[0]
    desired_name = f"SM_{key}_ConceptRemaster{TAG}"
    if mesh.get_name() != desired_name:
        target = f"{destination}/{desired_name}"
        if unreal.EditorAssetLibrary.does_asset_exist(target):
            unreal.EditorAssetLibrary.delete_asset(target)
        if not unreal.EditorAssetLibrary.rename_asset(mesh.get_path_name().split(".")[0], target):
            raise RuntimeError(f"Could not normalize imported mesh name for {key}")
        mesh = unreal.EditorAssetLibrary.load_asset(target)

    nanite = mesh.get_editor_property("nanite_settings")
    nanite.set_editor_property("enabled", True)
    mesh.set_editor_property("nanite_settings", nanite)
    body = mesh.get_editor_property("body_setup")
    if body:
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    source_note = f"Concept Remaster {TAG} clean hard-surface authoring; no RealityScan"
    if VERSION >= 3:
        source_note += "; distributed wing propulsion"
    unreal.EditorAssetLibrary.set_metadata_tag(mesh, "Ginnungagap.Source", source_note)
    unreal.EditorAssetLibrary.set_metadata_tag(mesh, "Ginnungagap.DesignAuthority", authority)
    unreal.EditorAssetLibrary.set_metadata_tag(mesh, "Ginnungagap.PromotionStatus", "Isolated review candidate; does not replace production mesh without approval")
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    unreal.EditorAssetLibrary.save_directory(destination, only_if_is_dirty=False, recursive=True)
    return mesh, destination, list(task.get_editor_property("imported_object_paths"))


def review_map(key: str, mesh, target):
    map_path = f"{MAP_ROOT}/L_{key}_ConceptRemaster{TAG}"
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(map_path):
        if not level.load_level(map_path):
            raise RuntimeError(f"Could not load {map_path}")
        existing = actors.get_all_level_actors()
        if existing:
            actors.destroy_actors(existing)
    elif not level.new_level(map_path):
        raise RuntimeError(f"Could not create {map_path}")

    raw_extent = mesh.get_bounds().box_extent * 2.0
    raw = (raw_extent.x, raw_extent.y, raw_extent.z)
    scale = unreal.Vector(*(target[i] / raw[i] if raw[i] > 0 else 1.0 for i in range(3)))
    ship = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(), unreal.Rotator())
    ship.set_actor_label(f"{TAG}_{key}_ExactConceptDimensions")
    ship.static_mesh_component.set_static_mesh(mesh)
    ship.set_actor_scale3d(scale)

    length, beam, height = target
    key_light = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, height * 2), unreal.Rotator(-38, -32, 0))
    key_light.set_actor_label(f"{TAG}_KeyLight")
    key_light.light_component.set_editor_property("intensity", 5.0)
    sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, height), unreal.Rotator())
    sky.set_actor_label(f"{TAG}_SkyLight")
    sky.light_component.set_editor_property("intensity", 1.0)
    cam_loc = unreal.Vector(-length * 0.55, -length * 0.72, height * 1.35)
    cam_rot = unreal.MathLibrary.find_look_at_rotation(cam_loc, unreal.Vector())
    camera = actors.spawn_actor_from_class(unreal.CameraActor, cam_loc, cam_rot)
    camera.set_actor_label(f"{TAG}_{key}_ReviewCamera")
    camera.camera_component.set_editor_property("field_of_view", 48.0)
    label = actors.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(-length * 0.42, -beam * 0.72, height * 0.72), unreal.Rotator(0, 180, 0))
    label.set_actor_label(f"{TAG}_{key}_ConceptAuthorityLabel")
    label.text_render.set_text(f"CONCEPT REMASTER {TAG} — {key} — {length / 100000.0:.1f} km")
    label.text_render.set_editor_property("world_size", max(length * 0.01, 700.0))
    label.text_render.set_editor_property("text_render_color", unreal.Color(95, 205, 255, 255))
    if not level.save_current_level():
        raise RuntimeError(f"Could not save {map_path}")
    return {
        "map": map_path,
        "mesh_bounds_cm": [raw_extent.x, raw_extent.y, raw_extent.z],
        "actor_scale": [scale.x, scale.y, scale.z],
        "placed_dimensions_cm": list(target),
    }


def main():
    results = []
    for key, target, authority in SHIPS:
        mesh, destination, imported = import_ship(key, authority)
        review = review_map(key, mesh, target)
        results.append({"ship": key, "mesh": mesh.get_path_name(), "destination": destination, "imported_paths": imported, "review": review})
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({"status": "pass", "version": VERSION, "ships": results}, indent=2), encoding="utf-8")
    unreal.log(f"CONCEPT REMASTER {TAG} IMPORT COMPLETE: {REPORT}")


if __name__ == "__main__":
    main()
