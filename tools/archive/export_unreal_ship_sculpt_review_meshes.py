"""Export the repaired Unreal sculpt meshes for deterministic external review renders."""
from pathlib import Path
import json
import unreal

PROJECT = Path(unreal.SystemLibrary.get_project_directory())
OUTPUT = PROJECT / "Art/Ships/Exterior/UnrealSculptReview/Exported"
REPORT = PROJECT / "Saved/Reports/UnrealShipSculptReviewExports.json"
FOLDERS = {
    "MilitaryCorvette": "/Game/Assets/Ships/Exterior/UnrealSculpt/MilitaryCorvette/Working/Iteration_02_Cleanup",
    "ExpeditionCarrier": "/Game/Assets/Ships/Exterior/UnrealSculpt/ExpeditionCarrier/Working/Iteration_02_Cleanup",
}

exports = []
for ship, folder in FOLDERS.items():
    ship_dir = OUTPUT / ship
    ship_dir.mkdir(parents=True, exist_ok=True)
    for asset_path in unreal.EditorAssetLibrary.list_assets(folder, recursive=False, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if not isinstance(asset, unreal.StaticMesh):
            continue
        filename = ship_dir / f"{asset.get_name()}.fbx"
        task = unreal.AssetExportTask()
        task.object = asset
        task.filename = str(filename)
        task.automated = True
        task.prompt = False
        task.replace_identical = True
        task.write_empty_files = False
        task.options = unreal.FbxExportOption()
        if not unreal.Exporter.run_asset_export_task(task):
            raise RuntimeError(f"Could not export {asset_path}")
        exports.append({"ship": ship, "asset": asset_path, "file": str(filename)})

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"version": 1, "exports": exports}, indent=2), encoding="utf-8")
if len(exports) != 13:
    raise RuntimeError(f"Expected 13 cleanup exports, produced {len(exports)}")
unreal.log("Unreal ship sculpt review exports complete")
