"""Import the 100-object rigid-bound suit prototype as an Unreal Skeletal Mesh."""

from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = ROOT / "Build" / "Unreal" / "PlayerSuits" / "FBX" / "SKM_PlayerSuit_Prototype.fbx"
DESTINATION = "/Game/Characters/Player/Suit/PackagedCombined/SkeletalPrototype"


def main():
    if not SOURCE.exists():
        raise RuntimeError(f"Skeletal suit prototype FBX is missing: {SOURCE}")
    task = unreal.AssetImportTask()
    task.filename = str(SOURCE)
    task.destination_path = DESTINATION
    task.automated = True
    task.save = True
    task.replace_existing = True
    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = True
    options.import_animations = False
    options.import_materials = False
    options.import_textures = False
    options.skeletal_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_COMPUTE_NORMALS
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    if not task.imported_object_paths:
        raise RuntimeError("Unreal did not import a skeletal suit prototype asset")
    for path in task.imported_object_paths:
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if asset:
            unreal.EditorAssetLibrary.set_metadata_tag(asset, "PlayerSuitRigidBindCount", "100")
            unreal.EditorAssetLibrary.set_metadata_tag(asset, "PlayerSuitPrototype", "true")
            unreal.EditorAssetLibrary.set_metadata_tag(asset, "PlayerSuitDeformationSteps", "100")
            unreal.EditorAssetLibrary.set_metadata_tag(asset, "PlayerSuitSmoothWeightedSections", "10")
            unreal.EditorAssetLibrary.set_metadata_tag(asset, "PlayerSuitAnatomySteps", "500")
            unreal.EditorAssetLibrary.set_metadata_tag(asset, "PlayerSuitAnatomyBoundMeshes", "100")
            unreal.EditorAssetLibrary.set_metadata_tag(asset, "PlayerSuitRealPlayerFinishSteps", "500")
            unreal.EditorAssetLibrary.set_metadata_tag(asset, "PlayerSuitRealPlayerBoundMeshes", "120")
            unreal.EditorAssetLibrary.set_metadata_tag(asset, "PlayerSuitProductionRefinementSteps", "1000")
            unreal.EditorAssetLibrary.set_metadata_tag(asset, "PlayerSuitProductionRefinementMeshes", "60")
            unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
    unreal.log(f"Player suit skeletal prototype import complete: {task.imported_object_paths}")


main()
