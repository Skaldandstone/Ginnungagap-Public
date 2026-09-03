"""Import the validated V7 suit into an isolated Unreal review destination.

This deliberately does not replace PackagedCombined or the live player pawn.
Run with UnrealEditor-Cmd after the V7 Blender export completes.
"""

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
PACKAGE = PROJECT / "Build" / "Unreal" / "PlayerSuitsV7Review"
MANIFEST = PACKAGE / "PlayerSuitV7_ReviewManifest.json"


def main():
    if not MANIFEST.exists():
        raise RuntimeError(f"V7 review manifest is missing: {MANIFEST}")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    if manifest.get("status") != "review_only_not_runtime_promoted":
        raise RuntimeError("Refusing a V7 package without the review-only safety status")
    source = PROJECT / manifest["fbx"]
    if not source.exists() or source.stat().st_size < 1024:
        raise RuntimeError(f"V7 review FBX is missing or empty: {source}")

    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = manifest["destination"]
    task.automated = True
    task.save = True
    task.replace_existing = True
    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = True
    options.import_animations = False
    options.import_materials = True
    options.import_textures = False
    options.create_physics_asset = False
    options.skeletal_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_COMPUTE_NORMALS
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    if not task.imported_object_paths:
        raise RuntimeError("Unreal did not import any V7 review assets")

    module_count = len(manifest["modules"])
    for asset_path in task.imported_object_paths:
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if not asset:
            continue
        unreal.EditorAssetLibrary.set_metadata_tag(asset, "PlayerSuitVersion", "7")
        unreal.EditorAssetLibrary.set_metadata_tag(asset, "PlayerSuitStatus", "ReviewOnly")
        unreal.EditorAssetLibrary.set_metadata_tag(asset, "PlayerSuitModuleCount", str(module_count))
        unreal.EditorAssetLibrary.set_metadata_tag(asset, "PlayerSuitPromotionGate", manifest["promotion_gate"])
        unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
    unreal.EditorAssetLibrary.save_directory(manifest["destination"], only_if_is_dirty=False, recursive=True)
    unreal.log(f"V7 player-suit review import complete: {task.imported_object_paths}")


main()
