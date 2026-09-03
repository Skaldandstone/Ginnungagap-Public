"""Imports the baked title plate and glow as UI textures.

Pairs with tools/build_title_bloom_plate.py, which bakes the PNGs with Pillow outside Unreal.

Run:  UnrealEditor-Cmd.exe <project> -ExecutePythonScript=<forward-slash path to this file> -NullRHI
"""
from pathlib import Path

import unreal

SOURCE_DIR = Path(unreal.SystemLibrary.get_project_directory()) / "Intermediate" / "UI" / "Title"
DESTINATION = "/Game/UI/Textures"
TEXTURES = {
    "T_Title_Ginnungagap_Plate": "Title_Ginnungagap_Plate.png",
    "T_Title_Ginnungagap_Glow": "Title_Ginnungagap_Glow.png",
}


def main():
    tasks = []
    for name, filename in TEXTURES.items():
        source = SOURCE_DIR / filename
        if not source.exists():
            unreal.log_error("TITLE missing {}; run tools/build_title_bloom_plate.py first".format(source))
            return
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", str(source))
        task.set_editor_property("destination_path", DESTINATION)
        task.set_editor_property("destination_name", name)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", True)
        tasks.append(task)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)
    for name in TEXTURES:
        texture = unreal.load_asset("{}/{}".format(DESTINATION, name))
        if not texture:
            unreal.log_error("TITLE {} did not import".format(name))
            continue
        # UI: no mips, no sRGB surprises on the alpha, never streamed out from under the menu.
        texture.set_editor_property("lod_group", unreal.TextureGroup.TEXTUREGROUP_UI)
        texture.set_editor_property("mip_gen_settings", unreal.TextureMipGenSettings.TMGS_NO_MIPMAPS)
        texture.set_editor_property("never_stream", True)
        unreal.EditorAssetLibrary.save_loaded_asset(texture)
        unreal.log("TITLE imported {} ({}x{})".format(texture.get_path_name(),
            texture.blueprint_get_size_x(), texture.blueprint_get_size_y()))


if __name__ == "__main__":
    main()
