"""Import the concept-faithful V4 pod base/lid and build an isolated Unreal review map."""
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = ROOT / "Build" / "Unreal" / "ShipRooms" / "Cryo" / "ConceptV4"
DEST = "/Game/Assets/ShipRooms/Cryo/ConceptV4"
MAP = "/Game/Assets/Maps/ShipProduction/L_CryoPod_ConceptV4"


def import_mesh(filename, destination_name):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(SOURCE / filename))
    task.set_editor_property("destination_path", DEST)
    task.set_editor_property("destination_name", destination_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    # Save once after both synchronous imports. Saving each task and then the
    # directory caused redundant package replacement/backup races on Windows.
    task.set_editor_property("save", False)
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("import_materials", True)
    options.set_editor_property("import_textures", True)
    options.static_mesh_import_data.set_editor_property("combine_meshes", True)
    options.static_mesh_import_data.set_editor_property("generate_lightmap_u_vs", True)
    options.static_mesh_import_data.set_editor_property("auto_generate_collision", True)
    options.static_mesh_import_data.set_editor_property("convert_scene", True)
    options.static_mesh_import_data.set_editor_property("convert_scene_unit", True)
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    asset = unreal.EditorAssetLibrary.load_asset(f"{DEST}/{destination_name}")
    if not asset:
        raise RuntimeError(f"Failed to import {filename}")
    return asset


def main():
    # Import the corrected canted-berth revision under new package names. This
    # avoids replacing the prior review packages while another editor has them
    # loaded and gives the production actor an explicit, stable revision.
    import_mesh("SM_CryoPod_ConceptV4_Base.fbx", "SM_CryoPod_ConceptV4_Canted_Base")
    import_mesh("SM_CryoPod_ConceptV4_Lid.fbx", "SM_CryoPod_ConceptV4_Canted_Lid")
    unreal.EditorAssetLibrary.save_directory(DEST)
    unreal.log(f"CRYO-V4 IMPORT COMPLETE: {DEST}")


if __name__ == "__main__":
    main()
