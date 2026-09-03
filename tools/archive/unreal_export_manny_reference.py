"""Export the exact gameplay Manny mesh/skeleton for V32 garment rebinding."""

import json
from pathlib import Path

import unreal


ASSET_PATH = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple"
asset = unreal.EditorAssetLibrary.load_asset(ASSET_PATH)
if not isinstance(asset, unreal.SkeletalMesh):
    raise RuntimeError(f"Missing Manny reference mesh: {ASSET_PATH}")

output = (
    Path(unreal.Paths.project_dir()) / "Build" / "Unreal" / "PlayerSuits" /
    "CryoBodysuitV32" / "SKM_Manny_Simple_Reference.fbx"
)
output.parent.mkdir(parents=True, exist_ok=True)
task = unreal.AssetExportTask()
task.object = asset
task.filename = str(output)
task.automated = True
task.prompt = False
task.replace_identical = True
task.write_empty_files = False
options = unreal.FbxExportOption()
options.export_morph_targets = False
options.export_preview_mesh = True
task.options = options
if not unreal.Exporter.run_asset_export_task(task):
    raise RuntimeError("Manny skeletal reference export failed")

report = {"status": "pass", "asset": ASSET_PATH, "file": str(output)}
(Path(unreal.Paths.project_saved_dir()) / "MannyReferenceExport.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8"
)
unreal.log(f"MANNY_REFERENCE_EXPORT {json.dumps(report, separators=(',', ':'))}")
unreal.SystemLibrary.quit_editor()
