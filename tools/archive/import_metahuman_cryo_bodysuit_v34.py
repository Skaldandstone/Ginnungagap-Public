"""Import the rebuilt continuous V34 cryo bodysuit against PlayerFace01's body skeleton."""

import json
import os

import unreal


PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
SOURCE_FBX = os.path.join(
    PROJECT_DIR, "Build", "Unreal", "PlayerSuits", "CryoBodysuitV34", "SK_CryoBodysuit_V34_Face01.fbx"
)
BODY_ASSET = "/Game/Characters/MetaHumans/Assembled/PlayerFace01/Body/SKM_MHC_Face01_Ada_BodyMesh"
DESTINATION = "/Game/Characters/Player/Undersuit/CryoBodysuitV34"
DESTINATION_NAME = "SK_CryoBodysuit_V34_Face01"
MATERIAL_PATH = "/Game/Characters/Player/Undersuit/MetaHuman/MI_MH_CryoBodysuit_Standard"
REPORT_PATH = os.path.join(PROJECT_DIR, "Saved", "CryoBodysuitV34Import.json")


def main():
    body_mesh = unreal.EditorAssetLibrary.load_asset(BODY_ASSET)
    material = unreal.EditorAssetLibrary.load_asset(MATERIAL_PATH)
    if not os.path.isfile(SOURCE_FBX) or not isinstance(body_mesh, unreal.SkeletalMesh):
        raise RuntimeError("V34 source FBX or MetaHuman body asset is missing")
    skeleton = body_mesh.get_editor_property("skeleton")
    if not isinstance(skeleton, unreal.Skeleton):
        raise RuntimeError("MetaHuman body skeleton is missing")

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", SOURCE_FBX)
    task.set_editor_property("destination_path", DESTINATION)
    task.set_editor_property("destination_name", DESTINATION_NAME)
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    task.set_editor_property("replace_existing", True)

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", True)
    options.set_editor_property("import_animations", False)
    options.set_editor_property("import_materials", False)
    options.set_editor_property("import_textures", False)
    options.set_editor_property("create_physics_asset", False)
    options.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_SKELETAL_MESH)
    options.set_editor_property("skeleton", skeleton)
    options.skeletal_mesh_import_data.set_editor_property(
        "normal_import_method", unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    )
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    asset_path = f"{DESTINATION}/{DESTINATION_NAME}"
    mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not isinstance(mesh, unreal.SkeletalMesh):
        raise RuntimeError(f"V34 skeletal import failed: {list(task.imported_object_paths)}")

    slots = mesh.get_editor_property("materials")
    if material:
        for slot in slots:
            slot.set_editor_property("material_interface", material)
        mesh.set_editor_property("materials", slots)
    unreal.EditorAssetLibrary.set_metadata_tag(mesh, "Ginnungagap.CryoSuitVersion", "34")
    unreal.EditorAssetLibrary.set_metadata_tag(mesh, "Ginnungagap.BodyPreset", "PlayerFace01")
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)

    with open(REPORT_PATH, "w", encoding="utf-8") as report_file:
        json.dump({
            "status": "pass",
            "asset": mesh.get_path_name(),
            "skeleton": mesh.get_editor_property("skeleton").get_path_name(),
            "material_slots": len(mesh.get_editor_property("materials")),
            "source": SOURCE_FBX,
        }, report_file, indent=2)
    unreal.log("CRYO_BODYSUIT_V34_IMPORT " + mesh.get_path_name())


main()
