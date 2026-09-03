"""Create non-destructive Unreal Fab-donor concept blockouts for both capital ships."""
from pathlib import Path
import json

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
REPORT = PROJECT / "Saved/Reports/UnrealShipFabConceptBlockout.json"
ROOT = "/Game/Assets/Ships/Exterior"

SHIPS = {
    "MilitaryCorvette": {
        "glb": PROJECT / "Art/Ships/Exterior/FabDonors/Spaceship4/SM_FabDonor_Spaceship4_Clean.glb",
        "import": ROOT + "/FabDonors/Spaceship4",
        "output": ROOT + "/UnrealSculpt/MilitaryCorvette/Working/Iteration_03_FabConceptBlockout",
        "source_map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_Sculpt",
        "map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_FabConcept",
        "expected_cm": (240000.0, 43000.0, 62000.0),
        "donor": "Spaceship 4 by Gerardo Justel (CC BY 4.0)",
    },
    "ExpeditionCarrier": {
        "glb": PROJECT / "Art/Ships/Exterior/FabDonors/BC304/SM_FabDonor_BC304_Clean.glb",
        "import": ROOT + "/FabDonors/BC304",
        "output": ROOT + "/UnrealSculpt/ExpeditionCarrier/Working/Iteration_03_FabConceptBlockout",
        "source_map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_Sculpt",
        "map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_FabConcept",
        "expected_cm": (650000.0, 140000.0, 180000.0),
        "donor": "BC-304 | Starportal by 3D Sci-Fi (CC BY 4.0)",
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
    clean_assigned_materials=False,
    emit_transaction=False,
    use_build_scale=False,
    apply_nanite_settings=True,
    new_nanite_settings=unreal.MeshNaniteSettings(enabled=False),
)
NORMALS = unreal.GeometryScriptCalculateNormalsOptions(angle_weighted=True, area_weighted=True)
TANGENTS = unreal.GeometryScriptTangentsOptions(
    type=unreal.GeometryScriptTangentTypes.STANDARD_MIKK_T,
    uv_layer=0,
)


def import_glb(source, destination):
    unreal.EditorAssetLibrary.make_directory(destination)
    existing = []
    for path in unreal.EditorAssetLibrary.list_assets(destination, recursive=True, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if isinstance(asset, unreal.StaticMesh):
            existing.append(asset)
    if len(existing) == 1:
        return existing[0]
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = destination
    task.automated = True
    task.replace_existing = True
    task.replace_existing_settings = False
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    meshes = []
    for path in unreal.EditorAssetLibrary.list_assets(destination, recursive=True, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if isinstance(asset, unreal.StaticMesh):
            meshes.append(asset)
    if len(meshes) != 1:
        raise RuntimeError(f"Expected one standardized donor mesh in {destination}; found {len(meshes)}")
    return meshes[0]


def read_dynamic(asset):
    dynamic = unreal.DynamicMesh()
    result = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh(
        asset, dynamic, READ_OPTIONS, READ_LOD
    )
    if isinstance(result, tuple):
        dynamic = result[0]
        if result[1] != unreal.GeometryScriptOutcomePins.SUCCESS:
            raise RuntimeError(f"Could not read {asset.get_path_name()}: {result[1]}")
    return dynamic


def prepare_output(source, output_folder, ship_name):
    unreal.EditorAssetLibrary.make_directory(output_folder)
    destination = f"{output_folder}/SM_{ship_name}_FabConceptBlockout"
    if unreal.EditorAssetLibrary.does_asset_exist(destination):
        asset = unreal.EditorAssetLibrary.load_asset(destination)
    else:
        asset = unreal.EditorAssetLibrary.duplicate_asset(
            source.get_path_name().split(".")[0], destination
        )
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError(f"Could not create {destination}")
    return asset


def fit_mesh(source, output, expected, donor):
    dynamic = read_dynamic(source)
    box = dynamic.get_mesh_bounding_box()
    size = box.max - box.min
    imported = [size.x, size.y, size.z]
    rotated_to_x = False
    if size.y > size.x and size.y > size.z:
        dynamic.rotate_mesh(
            unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0),
            unreal.Vector(0.0, 0.0, 0.0),
        )
        rotated_to_x = True
        box = dynamic.get_mesh_bounding_box()
        size = box.max - box.min
    before = [size.x, size.y, size.z]
    scale = [expected[index] / before[index] for index in range(3)]
    center = (box.min + box.max) * 0.5
    dynamic.translate_mesh(unreal.Vector(-center.x, -center.y, -center.z))
    dynamic.scale_mesh(unreal.Vector(*scale), unreal.Vector(0.0, 0.0, 0.0))
    dynamic.auto_repair_normals()
    dynamic.recompute_normals(NORMALS)
    dynamic.compute_tangents(TANGENTS)
    result = unreal.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(
        dynamic, output, WRITE_OPTIONS, WRITE_LOD
    )
    if isinstance(result, tuple) and result[1] != unreal.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError(f"Could not write {output.get_path_name()}: {result[1]}")
    unreal.EditorAssetLibrary.set_metadata_tag(output, "ShipSculpt.Iteration", "Iteration_03_FabConceptBlockout")
    unreal.EditorAssetLibrary.set_metadata_tag(output, "ShipSculpt.Tool", "Unreal Geometry Script")
    unreal.EditorAssetLibrary.set_metadata_tag(output, "ShipSculpt.Donor", donor)
    unreal.EditorAssetLibrary.save_loaded_asset(output)
    final = read_dynamic(output).get_mesh_bounding_box()
    final_size = final.max - final.min
    return imported, before, rotated_to_x, scale, [final_size.x, final_size.y, final_size.z]


def create_review_map(config, mesh, ship_name):
    if not unreal.EditorAssetLibrary.does_asset_exist(config["map"]):
        duplicate = unreal.EditorAssetLibrary.duplicate_asset(config["source_map"], config["map"])
        if duplicate is None:
            raise RuntimeError(f"Could not duplicate {config['source_map']} to {config['map']}")
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level.load_level(config["map"]):
        raise RuntimeError(f"Could not load {config['map']}")
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label().startswith("SCULPT_WORKING_"):
            actor.set_actor_hidden_in_game(True)
            actor.set_is_temporarily_hidden_in_editor(True)
        elif actor.get_actor_label().startswith("FAB_CONCEPT_"):
            actors.destroy_actor(actor)
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator()
    )
    actor.set_actor_label(f"FAB_CONCEPT_{ship_name}")
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_scale3d(unreal.Vector(1.0, 1.0, 1.0))
    origin, extent = actor.get_actor_bounds(False)
    size = [extent.x * 2.0, extent.y * 2.0, extent.z * 2.0]
    level.save_current_level()
    return size


results = []
for ship_name, config in SHIPS.items():
    if not config["glb"].exists():
        raise RuntimeError(f"Missing prepared Fab donor: {config['glb']}")
    source = import_glb(config["glb"], config["import"])
    output = prepare_output(source, config["output"], ship_name)
    imported, before, rotated_to_x, scale, final_asset_size = fit_mesh(
        source, output, config["expected_cm"], config["donor"]
    )
    map_size = create_review_map(config, output, ship_name)
    verified = all(
        abs(map_size[index] - config["expected_cm"][index]) <= 20.0
        for index in range(3)
    )
    results.append({
        "ship": ship_name,
        "donor": config["donor"],
        "source_glb": str(config["glb"]),
        "source_asset": source.get_path_name(),
        "output_asset": output.get_path_name(),
        "review_map": config["map"],
        "raw_import_size_cm": imported,
        "oriented_size_cm": before,
        "rotated_long_axis_to_x": rotated_to_x,
        "baked_scale": scale,
        "asset_size_cm": final_asset_size,
        "map_size_cm": map_size,
        "expected_cm": config["expected_cm"],
        "scale_verified": verified,
    })

unreal.EditorAssetLibrary.save_directory(ROOT + "/FabDonors")
unreal.EditorAssetLibrary.save_directory(ROOT + "/UnrealSculpt")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"version": 1, "ships": results}, indent=2), encoding="utf-8")
if not all(item["scale_verified"] for item in results):
    raise RuntimeError("Fab concept blockout scale validation failed")
unreal.log("Unreal Fab ship concept blockouts complete")
