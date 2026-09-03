"""Create the first concept-specific Unreal silhouette pass for both capital ships.

This pass is deliberately non-destructive.  It duplicates the validated cleanup
meshes into ``Iteration_03_Silhouette``, applies broad-form vertex deformation,
normalizes the complete assembly back to its approved dimensions, and repoints
the existing sculpt-map actors at the new working assets.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
REPORT = PROJECT / "Saved/Reports/UnrealShipSculptSilhouette01.json"

SHIPS = {
    "MilitaryCorvette": {
        "source": "/Game/Assets/Ships/Exterior/UnrealSculpt/MilitaryCorvette/Working/Iteration_02_Cleanup",
        "output": "/Game/Assets/Ships/Exterior/UnrealSculpt/MilitaryCorvette/Working/Iteration_03_Silhouette",
        "map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_Sculpt",
        "expected_cm": (240000.0, 43000.0, 62000.0),
        "concept": "docs/concept-art/reference/ships/medium-military-corvette-exterior.png",
        "modules": 6,
    },
    "ExpeditionCarrier": {
        "source": "/Game/Assets/Ships/Exterior/UnrealSculpt/ExpeditionCarrier/Working/Iteration_02_Cleanup",
        "output": "/Game/Assets/Ships/Exterior/UnrealSculpt/ExpeditionCarrier/Working/Iteration_03_Silhouette",
        "map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_Sculpt",
        "expected_cm": (650000.0, 140000.0, 180000.0),
        "concept": "docs/concept-art/reference/ships/large-expedition-carrier-exterior.png",
        "modules": 7,
    },
}

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
    opening_angle_deg=48.0,
    split_by_face_group=False,
)
TANGENTS = unreal.GeometryScriptTangentsOptions(
    type=unreal.GeometryScriptTangentTypes.STANDARD_MIKK_T,
    uv_layer=0,
)


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 0.0
    t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def static_meshes(folder: str) -> list[unreal.StaticMesh]:
    meshes = []
    for path in unreal.EditorAssetLibrary.list_assets(folder, recursive=False, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if isinstance(asset, unreal.StaticMesh):
            meshes.append(asset)
    return sorted(meshes, key=lambda item: item.get_name())


def read_dynamic(asset: unreal.StaticMesh) -> unreal.DynamicMesh:
    dynamic = unreal.DynamicMesh()
    result = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(
        asset, dynamic, READ_OPTIONS, READ_LOD
    )
    if isinstance(result, tuple):
        dynamic = result[0]
        if result[1] != unreal.GeometryScriptOutcomePins.SUCCESS:
            raise RuntimeError(f"Could not read {asset.get_path_name()}: {result[1]}")
    return dynamic


def write_dynamic(dynamic: unreal.DynamicMesh, asset: unreal.StaticMesh, ship: str) -> None:
    dynamic.auto_repair_normals()
    dynamic.compute_split_normals(SPLIT_NORMALS, NORMALS)
    dynamic.compute_tangents(TANGENTS)
    result = unreal.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(
        dynamic, asset, WRITE_OPTIONS, WRITE_LOD
    )
    if isinstance(result, tuple) and result[1] != unreal.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError(f"Could not write {asset.get_path_name()}: {result[1]}")
    asset.set_editor_property("light_map_coordinate_index", 1)
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "ShipSculpt.Iteration", "Iteration_03_Silhouette")
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "ShipSculpt.Pass", "Silhouette_01")
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "ShipSculpt.Ship", ship)
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "ShipSculpt.Tool", "Unreal Geometry Script")
    unreal.EditorAssetLibrary.save_loaded_asset(asset)


def duplicate_output(source: unreal.StaticMesh, output_folder: str) -> tuple[unreal.StaticMesh, bool]:
    destination = f"{output_folder}/{source.get_name()}"
    if unreal.EditorAssetLibrary.does_asset_exist(destination):
        existing = unreal.EditorAssetLibrary.load_asset(destination)
        if not isinstance(existing, unreal.StaticMesh):
            raise RuntimeError(f"Silhouette destination is not a StaticMesh: {destination}")
        # Always rebuild generated silhouette assets from the preserved cleanup
        # source. This keeps reruns deterministic and prevents pass stacking.
        return existing, False
    copy = unreal.EditorAssetLibrary.duplicate_asset(source.get_path_name().split(".")[0], destination)
    if not isinstance(copy, unreal.StaticMesh):
        raise RuntimeError(f"Could not duplicate silhouette asset {destination}")
    return copy, False


def deform_corvette(
    name: str,
    position: unreal.Vector,
    expected: tuple[float, ...],
    module_center: unreal.Vector,
) -> unreal.Vector:
    half_x, half_y, half_z = (value * 0.5 for value in expected)
    nx = max(-1.0, min(1.0, position.x / half_x))
    ny = max(-1.0, min(1.0, position.y / half_y))
    nz = max(-1.0, min(1.0, position.z / half_z))
    middle = 1.0 - smoothstep(0.28, 0.86, abs(nx))
    bow = smoothstep(0.56, 1.0, nx)
    stern = smoothstep(0.68, 1.0, -nx)

    # Establish a compact armored center, a sharper prow, a hard drive shoulder,
    # and subtly faceted cross-sections instead of a generic rounded capsule.
    y_scale = 1.0 + 0.055 * middle - 0.19 * bow + 0.035 * stern
    z_scale = 1.0 + 0.070 * middle - 0.15 * bow + 0.030 * stern
    y_scale *= 1.0 - 0.040 * abs(nz) ** 3
    z_scale *= 1.0 - 0.032 * abs(ny) ** 3

    target = unreal.Vector(position.x, position.y * y_scale, position.z * z_scale)
    if "CommandDefense" in name:
        # Keep the authored defense terraces registered to the hull. A small
        # upward bias preserves their readable stepped hierarchy.
        target.z += half_z * 0.006
    return target


def deform_carrier(
    name: str,
    position: unreal.Vector,
    expected: tuple[float, ...],
    module_center: unreal.Vector,
) -> unreal.Vector:
    half_x, half_y, half_z = (value * 0.5 for value in expected)
    nx = max(-1.0, min(1.0, position.x / half_x))
    ny = max(-1.0, min(1.0, position.y / half_y))
    nz = max(-1.0, min(1.0, position.z / half_z))
    middle = 1.0 - smoothstep(0.38, 0.92, abs(nx))
    bow = smoothstep(0.58, 1.0, nx)
    stern = smoothstep(0.74, 1.0, -nx)

    # Build the carrier around broad deck masses, a tapered navigation prow, and
    # a full drive block.  Cross-axis terms flatten the hull into civic layers.
    y_scale = 1.0 + 0.085 * middle - 0.20 * bow + 0.045 * stern
    z_scale = 1.0 + 0.050 * middle - 0.13 * bow + 0.040 * stern
    y_scale *= 1.0 - 0.025 * abs(nz) ** 4
    z_scale *= 0.955 + 0.045 * abs(nz)

    target = unreal.Vector(position.x, position.y * y_scale, position.z * z_scale)
    if "CommandDefense" in name:
        target.z += half_z * 0.005
    elif "HabitatCivic" in name:
        # Pull the carrier's inhabited drum district out of the hull shadow.
        target.y *= 1.035
        target.z *= 1.020
    return target


def deform_mesh(
    ship: str,
    asset_name: str,
    dynamic: unreal.DynamicMesh,
    expected: tuple[float, ...],
) -> dict:
    _, position_list, has_gaps = unreal.GeometryScript_MeshQueries.get_all_vertex_positions(
        dynamic, False
    )
    if has_gaps:
        raise RuntimeError(f"Silhouette source requires dense vertex IDs: {asset_name}")
    positions = position_list.convert_vector_list_to_array()
    deform = deform_corvette if ship == "MilitaryCorvette" else deform_carrier
    bounds = dynamic.get_mesh_bounding_box()
    module_center = (bounds.min + bounds.max) * 0.5
    displacement_sum = 0.0
    displacement_max = 0.0
    changed = 0
    for vertex_id, position in enumerate(positions):
        target = deform(asset_name, position, expected, module_center)
        displacement = (target - position).length()
        if not math.isfinite(displacement):
            raise RuntimeError(f"Non-finite silhouette displacement in {asset_name}")
        if displacement > 0.001:
            position_list.set_vector_list_item(vertex_id, target)
            displacement_sum += displacement
            displacement_max = max(displacement_max, displacement)
            changed += 1
    unreal.GeometryScript_MeshEdits.set_all_mesh_vertex_positions(dynamic, position_list)
    if not changed:
        raise RuntimeError(f"Silhouette pass did not deform {asset_name}")
    return {
        "changed_vertices": changed,
        "average_displacement_cm": displacement_sum / changed,
        "maximum_displacement_cm": displacement_max,
    }


def combined_bounds(assets: list[unreal.StaticMesh]) -> tuple[list[float], list[float], list[float]]:
    low = [float("inf")] * 3
    high = [float("-inf")] * 3
    for asset in assets:
        bounds = asset.get_bounds()
        values = (bounds.origin.x, bounds.origin.y, bounds.origin.z)
        extents = (bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z)
        for index in range(3):
            low[index] = min(low[index], values[index] - extents[index])
            high[index] = max(high[index], values[index] + extents[index])
    return low, high, [high[index] - low[index] for index in range(3)]


def normalize_assets(
    ship: str, assets: list[unreal.StaticMesh], expected: tuple[float, ...]
) -> tuple[list[float], list[float]]:
    _, _, current = combined_bounds(assets)
    correction = [expected[index] / current[index] for index in range(3)]
    for asset in assets:
        dynamic = read_dynamic(asset)
        dynamic.scale_mesh(unreal.Vector(*correction), unreal.Vector(0.0, 0.0, 0.0))
        write_dynamic(dynamic, asset, ship)
    return current, correction


def normalize_dynamics(
    dynamics: list[unreal.DynamicMesh], expected: tuple[float, ...]
) -> tuple[list[float], list[float]]:
    low = [float("inf")] * 3
    high = [float("-inf")] * 3
    for dynamic in dynamics:
        box = dynamic.get_mesh_bounding_box()
        for index, value in enumerate((box.min.x, box.min.y, box.min.z)):
            low[index] = min(low[index], value)
        for index, value in enumerate((box.max.x, box.max.y, box.max.z)):
            high[index] = max(high[index], value)
    current = [high[index] - low[index] for index in range(3)]
    correction = [expected[index] / current[index] for index in range(3)]
    for dynamic in dynamics:
        dynamic.scale_mesh(unreal.Vector(*correction), unreal.Vector(0.0, 0.0, 0.0))
    return current, correction


def update_map(config: dict, assets: list[unreal.StaticMesh]) -> dict:
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level.load_level(config["map"]):
        raise RuntimeError(f"Could not load {config['map']}")
    assets_by_name = {asset.get_name(): asset for asset in assets}
    actors = []
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if not isinstance(actor, unreal.StaticMeshActor):
            continue
        label = actor.get_actor_label()
        if not label.startswith("SCULPT_WORKING_"):
            continue
        name = label.replace("SCULPT_WORKING_", "", 1)
        if name not in assets_by_name:
            continue
        actor.static_mesh_component.set_static_mesh(assets_by_name[name])
        actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
        actors.append(actor)
    if len(actors) != len(assets):
        raise RuntimeError(f"Updated {len(actors)}/{len(assets)} actors in {config['map']}")
    low = [float("inf")] * 3
    high = [float("-inf")] * 3
    for actor in actors:
        origin, extent = actor.get_actor_bounds(False)
        values = (origin.x, origin.y, origin.z)
        extents = (extent.x, extent.y, extent.z)
        for index in range(3):
            low[index] = min(low[index], values[index] - extents[index])
            high[index] = max(high[index], values[index] + extents[index])
    size = [high[index] - low[index] for index in range(3)]
    level.save_current_level()
    return {"min": low, "max": high, "size": size}


results = []
for ship, config in SHIPS.items():
    sources = static_meshes(config["source"])
    if len(sources) != config["modules"]:
        raise RuntimeError(f"Expected {config['modules']} cleanup modules for {ship}, found {len(sources)}")
    unreal.EditorAssetLibrary.make_directory(config["output"])
    outputs = []
    dynamics = []
    modules = []
    for source in sources:
        output, resumed = duplicate_output(source, config["output"])
        if resumed:
            modules.append({"name": source.get_name(), "resumed_existing_pass": True})
        else:
            dynamic = read_dynamic(source)
            deformation = deform_mesh(ship, source.get_name(), dynamic, config["expected_cm"])
            dynamics.append(dynamic)
            modules.append({
                "name": source.get_name(),
                "resumed_existing_pass": False,
                **deformation,
            })
        outputs.append(output)
    if len(dynamics) != len(outputs):
        raise RuntimeError(f"Silhouette rebuild did not prepare every {ship} module")
    pre_normalize_size, correction = normalize_dynamics(dynamics, config["expected_cm"])
    for output, dynamic in zip(outputs, dynamics):
        write_dynamic(dynamic, output, ship)
    final_bounds = update_map(config, outputs)
    scale_verified = all(
        abs(final_bounds["size"][index] - config["expected_cm"][index]) <= 10.0
        for index in range(3)
    )
    results.append({
        "ship": ship,
        "concept": config["concept"],
        "source": config["source"],
        "output": config["output"],
        "map": config["map"],
        "module_count": len(outputs),
        "pre_normalize_size_cm": pre_normalize_size,
        "normalization": correction,
        "final_bounds_cm": final_bounds,
        "expected_cm": config["expected_cm"],
        "scale_verified": scale_verified,
        "modules": modules,
    })

unreal.EditorAssetLibrary.save_directory("/Game/Assets/Ships/Exterior/UnrealSculpt")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"version": 1, "pass": "Silhouette_01", "ships": results}, indent=2), encoding="utf-8")
if not all(item["scale_verified"] for item in results):
    raise RuntimeError("Capital-ship silhouette scale validation failed")
unreal.log("Unreal capital-ship silhouette pass 01 complete")
