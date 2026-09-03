"""Import the rejected Compact Rock Corer RealityScan pilot for Unreal review.

The pilot deliberately does not replace the production Batch 03 mesh. It creates
an isolated comparison asset and level so reconstruction quality can be judged
in-engine before any promotion decision is made.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
SOURCE = PROJECT / "Art/Weapons/RealityScan/CompactRockCorer_Pilot/RealityScanOutput/CompactRockCorer_Normal.obj"
DEST = "/Game/Assets/Gameplay/RealityScanPilots/CompactRockCorer"
MAP_PATH = "/Game/Assets/Maps/ModelLibrary/L_RealityScan_CompactRockCorer_Pilot"
SAFE_MAP = "/Game/Assets/Maps/ModelLibrary/L_GameplayModelLibrary"
PRODUCTION_MESH = "/Game/Assets/Gameplay/SalvageBatch03/Meshes/SM_CompactRockCorer"
REPORT = PROJECT / "Saved/Reports/RealityScanCompactRockCorerPilot.json"


def clean_generated_content():
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        if unreal.EditorAssetLibrary.does_asset_exist(SAFE_MAP):
            if not level.load_level(SAFE_MAP):
                raise RuntimeError("Could not load safe map before refreshing RealityScan content")
    if unreal.EditorAssetLibrary.does_directory_exist(DEST):
        unreal.EditorAssetLibrary.delete_directory(DEST)
    unreal.EditorAssetLibrary.make_directory(DEST)


def import_scan():
    if not SOURCE.exists():
        raise RuntimeError(f"RealityScan pilot source is missing: {SOURCE}")
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(SOURCE))
    task.set_editor_property("destination_path", DEST)
    task.set_editor_property("destination_name", "SM_CompactRockCorer_RS_Pilot")
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    meshes = []
    for path in unreal.EditorAssetLibrary.list_assets(DEST, recursive=True, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if isinstance(asset, unreal.StaticMesh):
            meshes.append(asset)
    if len(meshes) != 1:
        raise RuntimeError(f"Expected one RealityScan Static Mesh, found {len(meshes)}: {meshes}")
    mesh = meshes[0]
    nanite = mesh.get_editor_property("nanite_settings")
    nanite.set_editor_property("enabled", True)
    mesh.set_editor_property("nanite_settings", nanite)
    body = mesh.get_editor_property("body_setup")
    if body:
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    unreal.EditorAssetLibrary.set_metadata_tag(mesh, "Ginnungagap.Source", "RealityScan 2.2 concept-art pilot")
    unreal.EditorAssetLibrary.set_metadata_tag(
        mesh,
        "Ginnungagap.PromotionStatus",
        "Rejected for first-use: 5 of 12 views aligned; purple reads as Bloom infection",
    )
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    return mesh, list(task.get_editor_property("imported_object_paths"))


def add_label(actors, label, location):
    actor = actors.spawn_actor_from_class(unreal.TextRenderActor, location, unreal.Rotator(0, 180, 0))
    actor.set_actor_label("Label_" + label.replace(" ", "_"))
    actor.text_render.set_text(label)
    actor.text_render.set_editor_property("world_size", 13)
    actor.text_render.set_editor_property("text_render_color", unreal.Color(120, 205, 255, 255))


def build_review_map(scan_mesh, scan_scale):
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        if not level.load_level(MAP_PATH):
            raise RuntimeError("Could not load existing RealityScan pilot review map")
        existing_actors = actors.get_all_level_actors()
        if existing_actors:
            actors.destroy_actors(existing_actors)
    elif not level.new_level(MAP_PATH):
        raise RuntimeError("Could not create RealityScan pilot review map")

    production = unreal.EditorAssetLibrary.load_asset(PRODUCTION_MESH)
    if not isinstance(production, unreal.StaticMesh):
        raise RuntimeError("Production Compact Rock Corer mesh is unavailable")

    for label, mesh, location, scale in (
        ("PRODUCTION GEOMETRY SCRIPT", production, unreal.Vector(0, 90, 55), 1.0),
        ("REJECTED REALITYSCAN COLOR STUDY", scan_mesh, unreal.Vector(0, -90, 55), scan_scale),
    ):
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, location, unreal.Rotator(0, 0, 0))
        actor.set_actor_label(label.replace(" ", "_"))
        actor.static_mesh_component.set_static_mesh(mesh)
        actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))
        add_label(actors, label, location + unreal.Vector(0, -45, 90))

    floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator())
    floor.static_mesh_component.set_static_mesh(unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane.Plane"))
    floor.set_actor_scale3d(unreal.Vector(5, 5, 1))

    key = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 500), unreal.Rotator(-45, -30, 0))
    key.light_component.set_editor_property("intensity", 4.0)
    sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 400), unreal.Rotator())
    sky.light_component.set_editor_property("intensity", 0.8)
    camera_location = unreal.Vector(300, -420, 230)
    camera_rotation = unreal.MathLibrary.find_look_at_rotation(camera_location, unreal.Vector(0, 0, 55))
    camera = actors.spawn_actor_from_class(unreal.CameraActor, camera_location, camera_rotation)
    camera.set_actor_label("RealityScan_Pilot_ReviewCamera")
    camera.camera_component.set_editor_property("field_of_view", 48)

    if not level.save_current_level():
        raise RuntimeError("Could not save RealityScan pilot review map")


def main():
    clean_generated_content()
    mesh, imported_paths = import_scan()
    bounds = mesh.get_bounds()
    size = bounds.box_extent * 2
    longest_axis = max(size.x, size.y, size.z)
    display_scale = 88.0 / longest_axis if longest_axis > 0 else 1.0
    build_review_map(mesh, display_scale)
    unreal.EditorAssetLibrary.save_directory(DEST, only_if_is_dirty=False, recursive=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "source": str(SOURCE),
        "destination": DEST,
        "mesh": mesh.get_path_name(),
        "review_map": MAP_PATH,
        "imported_paths": imported_paths,
        "raw_bounds_cm": [size.x, size.y, size.z],
        "review_scale": display_scale,
        "realityscan_alignment": {"input_views": 12, "largest_component_views": 5, "secondary_component_views": 3},
        "source_faces": 38878,
        "promotion_status": "rejected",
        "promotion_reason": "Largest component aligned only 5 of 12 generated views, and its purple treatment reads as Bloom infection rather than factory first-use equipment.",
    }, indent=2), encoding="utf-8")
    unreal.log(f"Rejected RealityScan Compact Rock Corer study imported for comparison: {mesh.get_path_name()}")


if __name__ == "__main__":
    main()
