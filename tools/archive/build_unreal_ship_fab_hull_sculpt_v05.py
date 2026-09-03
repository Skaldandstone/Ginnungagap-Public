"""Run the Fab hull sculpt refinement in migration-safe Iteration_05 packages.

The canonical repository currently has unresolved LFS merge entries on the
Iteration_04 packages.  This wrapper preserves those packages and executes the
same authored build into fresh asset/map/report paths.
"""
from pathlib import Path

import unreal


project = Path(unreal.SystemLibrary.get_project_directory())
source_path = project / "tools/build_unreal_ship_fab_hull_sculpt.py"
source = source_path.read_text(encoding="utf-8")
source = source.replace("Iteration_04_FabHullSculpt", "Iteration_05_FabHullSculpt")
source = source.replace(
    "Saved/Reports/UnrealShipFabHullSculpt.json",
    "Saved/Reports/UnrealShipFabHullSculptV05.json",
)
source = source.replace(
    "/Game/MaterialsScifi/Materials/Instances/MI_Scifi_Panels_09",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Materials/Material_instances/MI_cargo_body_01",
)
source = source.replace(
    "/Game/MaterialsScifi/Materials/Instances/MI_Scifi_Panels_06",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Materials/Material_instances/MI_cargo_body_01",
)
source = source.replace(
    "/Game/MaterialsScifi/Materials/Instances/MI_Scifi_Panels_13",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Materials/Material_instances/MI_trim_01",
)
source = source.replace(
    "/Game/MaterialsScifi/Materials/Instances/MI_Scifi_Panels_14",
    "/Game/Ice_Station/Materials/Light/MI_light1",
)
source = source.replace(
    "ellipsoid((-10000, 0, -28600), (72000, 15500, 2400)",
    "ellipsoid((-10000, 0, -26000), (72000, 15500, 5000)",
)
source = source.replace(
    "ellipsoid((-20000, 0, -87000), (190000, 52000, 3000)",
    "ellipsoid((-20000, 0, -82000), (190000, 52000, 8000)",
)
source = source.replace(
    "((-117000, 0, -4000), (6000, 39000, 42000))",
    "((-110000, 0, -4000), (20000, 39000, 42000))",
)
source = source.replace(
    "((117500, 0, -4500), (5000, 30000, 29000))",
    "((110000, 0, -4500), (20000, 30000, 29000))",
)
source = source.replace(
    "((-319000, 0, -10000), (12000, 118000, 130000))",
    "((-315000, 0, -10000), (20000, 118000, 130000))",
)
source = source.replace(
    "((319000, 0, -12000), (12000, 90000, 90000))",
    "((315000, 0, -12000), (20000, 90000, 90000))",
)
for old_height in ("50000", "58000", "62000", "64000"):
    source = source.replace(f"6000, {old_height}))", "6000, 32000))")
source = source.replace(
    "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_FabHullSculpt\"",
    "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_FabHullSculpt05\"",
)
source = source.replace(
    "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_FabHullSculpt\"",
    "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_FabHullSculpt05\"",
)
source = source.replace(
    '''    if not unreal.EditorAssetLibrary.does_asset_exist(config["map"]):
        duplicate = unreal.EditorAssetLibrary.duplicate_asset(config["source_map"], config["map"])
        if duplicate is None:
            raise RuntimeError(f"Could not duplicate {config['source_map']} to {config['map']}")
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)''',
    '''    if not unreal.EditorAssetLibrary.does_asset_exist(config["map"]):
        if unreal.EditorAssetLibrary.does_asset_exist(config["source_map"]):
            duplicate = unreal.EditorAssetLibrary.duplicate_asset(config["source_map"], config["map"])
            if duplicate is None:
                raise RuntimeError(f"Could not duplicate {config['source_map']} to {config['map']}")
        else:
            levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
            if not levels.new_level(config["map"]):
                raise RuntimeError(f"Could not create clean review map {config['map']}")
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)''',
)
exec(compile(source, str(source_path), "exec"), {"__name__": "__main__"})
