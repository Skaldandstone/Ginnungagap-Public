"""Unreal Editor Python importer for Build/Unreal/PlayerSuits.

Run after export_player_suits_for_unreal.py using UnrealEditor-Cmd -run=pythonscript.
"""

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
PACKAGE = ROOT / "Build" / "Unreal" / "PlayerSuits"
MANIFEST = PACKAGE / "PlayerSuit_UnrealManifest.json"
DESTINATION = "/Game/Characters/Player/Suit/PackagedCombined"


def import_static_mesh(source, destination):
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = destination
    task.automated = True
    task.save = True
    task.replace_existing = True
    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = False
    options.import_materials = False
    options.import_textures = False
    # Production package: one mesh per class/loadout. Fine-grained Blender objects remain
    # available in the source .blend, while Unreal avoids hundreds of per-fastener assets.
    options.static_mesh_import_data.combine_meshes = True
    options.static_mesh_import_data.generate_lightmap_u_vs = True
    options.static_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_COMPUTE_NORMALS
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return list(task.imported_object_paths)


def import_texture(source, destination):
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = destination
    task.automated = True
    task.save = True
    task.replace_existing = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return list(task.imported_object_paths)


def main():
    if not MANIFEST.exists():
        raise RuntimeError(f"Player suit package manifest does not exist: {MANIFEST}")
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    imported = []

    for role, spec in manifest["variants"].items():
        imported += import_static_mesh(PACKAGE / spec["fbx"], f"{DESTINATION}/Variants/{role}")
    for name, spec in manifest["equipment"].items():
        imported += import_static_mesh(PACKAGE / spec["fbx"], f"{DESTINATION}/Equipment/{name}")
    for role, channels in manifest["textures"].items():
        for source in channels.values():
            imported += import_texture(PACKAGE / source, f"{DESTINATION}/Textures/{role}")

    unreal.EditorAssetLibrary.save_directory(DESTINATION, only_if_is_dirty=False, recursive=True)
    unreal.log(f"Player suit package import complete: {len(imported)} assets")


main()
