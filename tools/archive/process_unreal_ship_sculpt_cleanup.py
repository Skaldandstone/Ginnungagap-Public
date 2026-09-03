"""Run the first non-destructive Unreal-native cleanup on capital-ship sculpt meshes."""
from pathlib import Path
import json
import unreal

PROJECT = Path(unreal.SystemLibrary.get_project_directory())
SETUP_REPORT = PROJECT / "Saved/Reports/UnrealShipSculptWorkspace.json"
OUT_REPORT = PROJECT / "Saved/Reports/UnrealShipSculptCleanup01.json"

SHIPS = {
    "MilitaryCorvette": {
        "source": "/Game/Assets/Ships/Exterior/UnrealSculpt/MilitaryCorvette/Working/Iteration_01",
        "output": "/Game/Assets/Ships/Exterior/UnrealSculpt/MilitaryCorvette/Working/Iteration_02_Cleanup",
        "map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_Sculpt",
        "expected_cm": (240000.0, 43000.0, 62000.0),
        "voxel_cm": 300.0,
    },
    "ExpeditionCarrier": {
        "source": "/Game/Assets/Ships/Exterior/UnrealSculpt/ExpeditionCarrier/Working/Iteration_01",
        "output": "/Game/Assets/Ships/Exterior/UnrealSculpt/ExpeditionCarrier/Working/Iteration_02_Cleanup",
        "map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_Sculpt",
        "expected_cm": (650000.0, 140000.0, 180000.0),
        "voxel_cm": 750.0,
    },
}

HULL_TOKENS = ("HullBow", "HullMidship", "HullStern")
READ_OPTIONS = unreal.GeometryScriptCopyMeshFromAssetOptions(
    apply_build_settings=True,
    request_tangents=True,
    ignore_remove_degenerates=True,
    use_build_scale=True,
)
READ_LOD = unreal.GeometryScriptMeshReadLOD(lod_index=0)
WRITE_LOD = unreal.GeometryScriptMeshWriteLOD(lod_index=0)
WRITE_OPTIONS = unreal.GeometryScriptCopyMeshToAssetOptions(
    enable_recompute_normals=True,
    enable_recompute_tangents=True,
    enable_remove_degenerates=True,
    clean_assigned_materials=True,
    emit_transaction=False,
    use_build_scale=False,
    apply_nanite_settings=True,
    new_nanite_settings=unreal.MeshNaniteSettings(enabled=False),
)
NORMALS = unreal.GeometryScriptCalculateNormalsOptions(angle_weighted=True, area_weighted=True)
SPLIT_NORMALS = unreal.GeometryScriptSplitNormalsOptions(
    split_by_opening_angle=True,
    opening_angle_deg=52.0,
    split_by_face_group=False,
)
TANGENTS = unreal.GeometryScriptTangentsOptions(
    type=unreal.GeometryScriptTangentTypes.STANDARD_MIKK_T,
    uv_layer=0,
)
DEGENERATES = unreal.GeometryScriptDegenerateTriangleOptions(
    mode=unreal.GeometryScriptRepairMeshMode.REPAIR_OR_DELETE,
    min_triangle_area=0.01,
    min_edge_length=0.01,
    compact_on_completion=True,
)


def static_meshes(folder):
    result = []
    for path in unreal.EditorAssetLibrary.list_assets(folder, recursive=False, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if isinstance(asset, unreal.StaticMesh):
            result.append(asset)
    return sorted(result, key=lambda item: item.get_name())


def duplicate_or_reset(source, output_folder):
    destination = f"{output_folder}/{source.get_name()}"
    existing = unreal.EditorAssetLibrary.load_asset(destination) if unreal.EditorAssetLibrary.does_asset_exist(destination) else None
    if isinstance(existing, unreal.StaticMesh):
        return existing, True
    copy = unreal.EditorAssetLibrary.duplicate_asset(source.get_path_name().split(".")[0], destination)
    if not isinstance(copy, unreal.StaticMesh):
        raise RuntimeError(f"Could not create cleanup mesh {destination}")
    return copy, False


def read_dynamic(asset):
    dynamic = unreal.DynamicMesh()
    result = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(
        asset, dynamic, READ_OPTIONS, READ_LOD
    )
    if isinstance(result, tuple):
        dynamic = result[0]
        outcome = result[1]
        if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
            raise RuntimeError(f"Could not read {asset.get_path_name()}: {outcome}")
    return dynamic


def write_dynamic(dynamic, asset):
    result = unreal.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(
        dynamic, asset, WRITE_OPTIONS, WRITE_LOD
    )
    if isinstance(result, tuple) and result[1] != unreal.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError(f"Could not write {asset.get_path_name()}: {result[1]}")
    asset.set_editor_property("light_map_coordinate_index", 1)
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "ShipSculpt.Iteration", "Iteration_02_Cleanup")
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "ShipSculpt.Tool", "Unreal Geometry Script")
    unreal.EditorAssetLibrary.save_loaded_asset(asset)


def mesh_stats(dynamic):
    box = dynamic.get_mesh_bounding_box()
    size = box.max - box.min
    return {
        "vertices": dynamic.get_vertex_count(),
        "triangles": dynamic.get_triangle_count(),
        "open_border_edges": dynamic.get_num_open_border_edges(),
        "size_cm": [size.x, size.y, size.z],
    }


def clean_dynamic(dynamic, scale, voxel_cm, voxelize):
    dynamic.scale_mesh(unreal.Vector(*scale), unreal.Vector(0.0, 0.0, 0.0))
    dynamic.repair_mesh_degenerate_geometry(DEGENERATES)
    effective_voxel_cm = None
    grid_resolution = None
    if voxelize:
        box = dynamic.get_mesh_bounding_box()
        size = box.max - box.min
        longest = max(size.x, size.y, size.z)
        grid_resolution = max(64, min(220, int(round(longest / voxel_cm))))
        effective_voxel_cm = longest / grid_resolution
        grid = unreal.GeometryScript3DGridParameters(
            size_method=unreal.GeometryScriptGridSizingMethod.GRID_RESOLUTION,
            grid_resolution=grid_resolution,
        )
        solidify = unreal.GeometryScriptSolidifyOptions(
            grid_parameters=grid,
            winding_threshold=0.5,
            solid_at_boundaries=True,
            extend_bounds=effective_voxel_cm * 2.0,
            surface_search_steps=4,
            thicken_shells=True,
            shell_thickness=effective_voxel_cm * 1.5,
        )
        dynamic.apply_mesh_solidify(solidify)
        dynamic.repair_mesh_degenerate_geometry(DEGENERATES)
        dynamic.set_num_uv_sets(1)
        dynamic.set_mesh_u_vs_from_box_projection(
            0,
            unreal.Transform(scale=unreal.Vector(10000.0, 10000.0, 10000.0)),
            unreal.GeometryScriptMeshSelection(),
            4,
        )
    dynamic.auto_repair_normals()
    dynamic.compute_split_normals(SPLIT_NORMALS, NORMALS)
    dynamic.compute_tangents(TANGENTS)
    return dynamic, effective_voxel_cm, grid_resolution


def combined_bounds(assets):
    low = [float("inf")] * 3
    high = [float("-inf")] * 3
    for asset in assets:
        bounds = asset.get_bounds()
        origin = bounds.origin
        extent = bounds.box_extent
        values = (origin.x, origin.y, origin.z)
        extents = (extent.x, extent.y, extent.z)
        for index in range(3):
            low[index] = min(low[index], values[index] - extents[index])
            high[index] = max(high[index], values[index] + extents[index])
    return low, high, [high[index] - low[index] for index in range(3)]


def normalize_assets(assets, expected):
    _, _, current = combined_bounds(assets)
    correction = [expected[index] / current[index] for index in range(3)]
    for asset in assets:
        dynamic = read_dynamic(asset)
        dynamic.scale_mesh(unreal.Vector(*correction), unreal.Vector(0.0, 0.0, 0.0))
        dynamic.recompute_normals(NORMALS)
        dynamic.compute_tangents(TANGENTS)
        write_dynamic(dynamic, asset)
    return current, correction


def update_map(config, assets):
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level.load_level(config["map"]):
        raise RuntimeError(f"Could not load {config['map']}")
    by_name = {asset.get_name(): asset for asset in assets}
    changed = 0
    sculpt_actors = []
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        label = actor.get_actor_label()
        if not label.startswith("SCULPT_WORKING_") or not isinstance(actor, unreal.StaticMeshActor):
            continue
        name = label.replace("SCULPT_WORKING_", "", 1)
        if name not in by_name:
            continue
        actor.static_mesh_component.set_static_mesh(by_name[name])
        actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
        sculpt_actors.append(actor)
        changed += 1
    if changed != len(assets):
        raise RuntimeError(f"Updated {changed}/{len(assets)} sculpt actors in {config['map']}")
    low = [float("inf")] * 3
    high = [float("-inf")] * 3
    for actor in sculpt_actors:
        origin, extent = actor.get_actor_bounds(False)
        for index, value in enumerate((origin.x, origin.y, origin.z)):
            radius = (extent.x, extent.y, extent.z)[index]
            low[index] = min(low[index], value - radius)
            high[index] = max(high[index], value + radius)
    size = [high[index] - low[index] for index in range(3)]
    level.save_current_level()
    return low, high, size


if not SETUP_REPORT.exists():
    raise RuntimeError("Missing Unreal sculpt setup report")
setup = json.loads(SETUP_REPORT.read_text(encoding="utf-8"))
setup_by_name = {entry["map"].split("L_")[1].split("_Sculpt")[0]: entry for entry in setup["ships"]}

results = []
for ship_name, config in SHIPS.items():
    source_assets = static_meshes(config["source"])
    if not source_assets:
        raise RuntimeError(f"No source working meshes in {config['source']}")
    unreal.EditorAssetLibrary.make_directory(config["output"])
    assembly_scale = setup_by_name[ship_name]["assembly_scale_correction"]
    output_assets = []
    modules = []
    for source in source_assets:
        output, existed = duplicate_or_reset(source, config["output"])
        source_dynamic = read_dynamic(source)
        before = mesh_stats(source_dynamic)
        is_hull = any(token in source.get_name() for token in HULL_TOKENS)
        already_clean = existed and unreal.EditorAssetLibrary.get_metadata_tag(output, "ShipSculpt.Iteration") == "Iteration_02_Cleanup"
        if already_clean:
            after = mesh_stats(read_dynamic(output))
            effective_voxel_cm = None
            grid_resolution = None
        else:
            dynamic, effective_voxel_cm, grid_resolution = clean_dynamic(
                source_dynamic, assembly_scale, config["voxel_cm"], is_hull
            )
            after = mesh_stats(dynamic)
            write_dynamic(dynamic, output)
        output_assets.append(output)
        modules.append({
            "name": source.get_name(),
            "voxel_wrapped": is_hull,
            "voxel_cm": config["voxel_cm"] if is_hull else None,
            "effective_voxel_cm": effective_voxel_cm,
            "grid_resolution": grid_resolution,
            "resumed_existing_cleanup": already_clean,
            "before": before,
            "after_cleanup": after,
        })
        unreal.log(f"SHIP SCULPT CLEANUP {ship_name} {source.get_name()}: {before['triangles']} -> {after['triangles']} triangles")
    pre_normalize_size, final_correction = normalize_assets(output_assets, config["expected_cm"])
    low, high, size = update_map(config, output_assets)
    verified = all(abs(size[index] - config["expected_cm"][index]) <= 10.0 for index in range(3))
    results.append({
        "ship": ship_name,
        "map": config["map"],
        "output": config["output"],
        "assembly_scale_baked": assembly_scale,
        "pre_normalize_size_cm": pre_normalize_size,
        "post_cleanup_scale_correction": final_correction,
        "final_bounds_cm": {"min": low, "max": high, "size": size},
        "expected_cm": config["expected_cm"],
        "scale_verified": verified,
        "modules": modules,
    })

unreal.EditorAssetLibrary.save_directory("/Game/Assets/Ships/Exterior/UnrealSculpt")
OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
OUT_REPORT.write_text(json.dumps({"version": 1, "ships": results}, indent=2), encoding="utf-8")
if not all(item["scale_verified"] for item in results):
    raise RuntimeError("Post-cleanup ship scale validation failed")
unreal.log("Unreal ship sculpt cleanup 01 complete")
