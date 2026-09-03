"""Import/reimport the concept-matched CRYO-01 FBXs into Unreal Engine.

Run with UnrealEditor-Cmd.exe Ginnungagap.uproject -ExecutePythonScript=<this file>.
"""
from pathlib import Path
import unreal

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Build" / "Unreal" / "ShipRooms" / "Cryo"
DEST = "/Game/Assets/ShipRooms/Cryo"
IMPORTS = (
    ("SM_Room_CryoShell", SOURCE / "SM_Room_CryoShell.fbx"),
    ("SM_Room_CryoMachinery", SOURCE / "SM_Room_CryoMachinery.fbx"),
    ("SM_CryoPod_Base", SOURCE / "SM_CryoPod_Base.fbx"),
    ("SM_CryoPod_RuntimeLid", SOURCE / "SM_CryoPod_RuntimeLid.fbx"),
)


def import_static_mesh(name, filename):
    if not filename.exists():
        raise RuntimeError(f"Missing CRYO-01 export: {filename}")
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("import_materials", True)
    options.set_editor_property("import_textures", False)
    options.static_mesh_import_data.set_editor_property("combine_meshes", True)
    options.static_mesh_import_data.set_editor_property("generate_lightmap_u_vs", True)
    options.static_mesh_import_data.set_editor_property("auto_generate_collision", True)
    options.static_mesh_import_data.set_editor_property("convert_scene", True)
    options.static_mesh_import_data.set_editor_property("convert_scene_unit", True)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(filename))
    task.set_editor_property("destination_path", DEST)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("replace_existing_settings", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    asset_path = f"{DEST}/{name}"
    mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not mesh:
        raise RuntimeError(f"CRYO-01 import did not create {asset_path}")
    mesh.set_editor_property("light_map_resolution", 256 if name.endswith("Shell") else 128)
    mesh.set_editor_property("light_map_coordinate_index", 1)
    body_setup = mesh.get_editor_property("body_setup")
    if body_setup:
        # Combined convex auto-collision bridges the pod gaps and blocks the aisle.
        # Exact query collision follows the visible shell, mounts, and machinery.
        body_setup.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    unreal.log(f"CRYO-01 ready: {asset_path}")
    return asset_path


def main():
    unreal.EditorAssetLibrary.make_directory(DEST)
    imported = [import_static_mesh(name, path) for name, path in IMPORTS]
    missing = [path for path in imported if not unreal.EditorAssetLibrary.does_asset_exist(path)]
    if missing:
        raise RuntimeError("Missing imported CRYO-01 assets: " + ", ".join(missing))
    unreal.log("CRYO-01 import complete: " + ", ".join(imported))


main()
