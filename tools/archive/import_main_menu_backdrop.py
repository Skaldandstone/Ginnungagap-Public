import os
import unreal


SOURCE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Art", "UI", "Menu", "MainMenu_Backdrop_v1.png"))
DESTINATION = "/Game/UI/Textures"
ASSET_PATH = f"{DESTINATION}/T_MainMenu_Backdrop"


def main() -> None:
    if unreal.EditorAssetLibrary.does_asset_exist(ASSET_PATH):
        unreal.log(f"Menu backdrop already imported: {ASSET_PATH}")
        return
    task = unreal.AssetImportTask()
    task.filename = SOURCE
    task.destination_path = DESTINATION
    task.destination_name = "T_MainMenu_Backdrop"
    task.automated = True
    task.replace_existing = False
    task.save = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    if not unreal.EditorAssetLibrary.does_asset_exist(ASSET_PATH):
        raise RuntimeError(f"Failed to import {SOURCE}")
    texture = unreal.EditorAssetLibrary.load_asset(ASSET_PATH)
    texture.set_editor_property("srgb", True)
    texture.set_editor_property("never_stream", True)
    unreal.EditorAssetLibrary.save_loaded_asset(texture)
    unreal.log(f"Imported menu backdrop: {ASSET_PATH}")


main()
