"""Fresh-load QA for Unreal capital-ship sculpt cleanup assets and maps."""
from pathlib import Path
import json
import unreal

PROJECT = Path(unreal.SystemLibrary.get_project_directory())
OUT = PROJECT / "Saved/Reports/UnrealShipSculptCleanup01_Validation.json"
SHIPS = {
    "MilitaryCorvette": {
        "folder": "/Game/Assets/Ships/Exterior/UnrealSculpt/MilitaryCorvette/Working/Iteration_02_Cleanup",
        "map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_Sculpt",
        "expected": (240000.0, 43000.0, 62000.0),
        "modules": 6,
    },
    "ExpeditionCarrier": {
        "folder": "/Game/Assets/Ships/Exterior/UnrealSculpt/ExpeditionCarrier/Working/Iteration_02_Cleanup",
        "map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_Sculpt",
        "expected": (650000.0, 140000.0, 180000.0),
        "modules": 7,
    },
}
READ = unreal.GeometryScriptCopyMeshFromAssetOptions(
    apply_build_settings=True, request_tangents=True, ignore_remove_degenerates=True
)
LOD = unreal.GeometryScriptMeshReadLOD(lod_index=0)
DEGENERATES = unreal.GeometryScriptDegenerateTriangleOptions(
    mode=unreal.GeometryScriptRepairMeshMode.DELETE_ONLY,
    min_triangle_area=0.01,
    min_edge_length=0.01,
    compact_on_completion=True,
)


def read_dynamic(asset):
    dynamic = unreal.DynamicMesh()
    result = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(asset, dynamic, READ, LOD)
    if isinstance(result, tuple):
        dynamic = result[0]
        if result[1] != unreal.GeometryScriptOutcomePins.SUCCESS:
            raise RuntimeError(f"Dynamic mesh read failed for {asset.get_path_name()}")
    return dynamic


def actor_bounds(actors):
    low = [float("inf")] * 3
    high = [float("-inf")] * 3
    for actor in actors:
        origin, extent = actor.get_actor_bounds(False)
        for index, value in enumerate((origin.x, origin.y, origin.z)):
            radius = (extent.x, extent.y, extent.z)[index]
            low[index] = min(low[index], value - radius)
            high[index] = max(high[index], value + radius)
    return low, high, [high[index] - low[index] for index in range(3)]


results = []
for ship, config in SHIPS.items():
    assets = []
    module_checks = []
    for path in unreal.EditorAssetLibrary.list_assets(config["folder"], recursive=False, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if not isinstance(asset, unreal.StaticMesh):
            continue
        assets.append(asset)
        dynamic = read_dynamic(asset)
        original_triangles = dynamic.get_triangle_count()
        test = unreal.DynamicMesh()
        dynamic.copy_mesh_to_mesh(test)
        test.repair_mesh_degenerate_geometry(DEGENERATES)
        repaired_triangles = test.get_triangle_count()
        tangent_result = dynamic.get_mesh_has_tangents()
        has_tangents = tangent_result[1] if isinstance(tangent_result, tuple) else False
        hull = any(token in asset.get_name() for token in ("HullBow", "HullMidship", "HullStern"))
        module_checks.append({
            "name": asset.get_name(),
            "triangles": original_triangles,
            "degenerate_triangles_removed_by_test": original_triangles - repaired_triangles,
            "uv_sets": dynamic.get_num_uv_sets(),
            "has_tangents": has_tangents,
            "open_border_edges": dynamic.get_num_open_border_edges(),
            "closed_hull": (not hull) or dynamic.get_num_open_border_edges() == 0,
        })
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level.load_level(config["map"]):
        raise RuntimeError(f"Could not load validation map {config['map']}")
    actors = []
    unit_scale = True
    correct_folder = True
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if not isinstance(actor, unreal.StaticMeshActor) or not actor.get_actor_label().startswith("SCULPT_WORKING_"):
            continue
        actors.append(actor)
        scale = actor.get_actor_scale3d()
        unit_scale = unit_scale and all(abs(value - 1.0) < 0.0001 for value in (scale.x, scale.y, scale.z))
        mesh = actor.static_mesh_component.get_editor_property("static_mesh")
        correct_folder = correct_folder and mesh is not None and config["folder"] in mesh.get_path_name()
    low, high, size = actor_bounds(actors)
    scale_verified = all(abs(size[index] - config["expected"][index]) <= 10.0 for index in range(3))
    modules_verified = (
        len(assets) == config["modules"]
        and len(actors) == config["modules"]
        and all(item["degenerate_triangles_removed_by_test"] == 0 for item in module_checks)
        and all(item["uv_sets"] >= 1 and item["has_tangents"] and item["closed_hull"] for item in module_checks)
    )
    results.append({
        "ship": ship,
        "folder": config["folder"],
        "map": config["map"],
        "asset_count": len(assets),
        "actor_count": len(actors),
        "unit_actor_scale": unit_scale,
        "actors_reference_cleanup": correct_folder,
        "bounds_cm": {"min": low, "max": high, "size": size},
        "expected_cm": config["expected"],
        "scale_verified": scale_verified,
        "modules_verified": modules_verified,
        "modules": module_checks,
    })

passed = all(
    item["scale_verified"]
    and item["modules_verified"]
    and item["unit_actor_scale"]
    and item["actors_reference_cleanup"]
    for item in results
)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"version": 1, "passed": passed, "ships": results}, indent=2), encoding="utf-8")
if not passed:
    raise RuntimeError("Unreal ship sculpt cleanup validation failed")
unreal.log("Unreal ship sculpt cleanup validation passed")
