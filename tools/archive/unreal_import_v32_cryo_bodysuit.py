"""Import the authored V32 cryo bodysuit as an independent Unreal skeletal garment."""

import json
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = ROOT / "Build" / "Unreal" / "PlayerSuits" / "CryoBodysuitV32" / "SK_CryoBodysuit_V32_Manny.fbx"
DESTINATION = "/Game/Characters/Player/Undersuit/CryoBodysuitV32"
MANNY_PATH = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple"
MATERIAL_PATH = (
    "/Game/Characters/Player/Undersuit/MetaHuman/"
    "MI_MH_CryoBodysuit_Standard.MI_MH_CryoBodysuit_Standard"
)

if not SOURCE.exists():
    raise RuntimeError(f"Missing V32 bodysuit export: {SOURCE}")

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
target_mesh = unreal.EditorAssetLibrary.load_asset(MANNY_PATH)
if not isinstance(target_mesh, unreal.SkeletalMesh):
    raise RuntimeError(f"Missing gameplay Manny mesh: {MANNY_PATH}")
options.skeleton = target_mesh.get_editor_property("skeleton")
options.skeletal_mesh_import_data.normal_import_method = (
    unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
)
task.options = options

unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
skeletal_mesh = next(
    (unreal.EditorAssetLibrary.load_asset(path) for path in task.imported_object_paths
     if isinstance(unreal.EditorAssetLibrary.load_asset(path), unreal.SkeletalMesh)),
    None,
)
if not skeletal_mesh:
    raise RuntimeError(f"V32 import produced no skeletal mesh: {task.imported_object_paths}")

material = unreal.EditorAssetLibrary.load_asset(MATERIAL_PATH)
if not material:
    raise RuntimeError(f"Missing cryo material: {MATERIAL_PATH}")
materials = list(skeletal_mesh.get_editor_property("materials"))
for index, slot in enumerate(materials):
    slot.material_interface = material
    materials[index] = slot
skeletal_mesh.set_editor_property("materials", materials)

for key, value in {
    "SemanticLayer": "CryoBodysuit",
    "ContainsOversuit": "false",
    "SourceRevision": "V32",
    "RuntimePoseDriver": "MetaHumanCopyPoseAnimInstance",
}.items():
    unreal.EditorAssetLibrary.set_metadata_tag(skeletal_mesh, key, value)
unreal.EditorAssetLibrary.save_loaded_asset(skeletal_mesh, only_if_is_dirty=False)

skeleton = skeletal_mesh.get_editor_property("skeleton")
report = {
    "status": "pass",
    "skeletal_mesh": skeletal_mesh.get_path_name(),
    "skeleton": skeleton.get_path_name() if skeleton else None,
    "material_slots": len(materials),
    "source": str(SOURCE),
}
report_path = Path(unreal.Paths.project_saved_dir()) / "MetaHumanCryoBodysuitV32Import.json"
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"METAHUMAN_CRYO_V32_IMPORT {json.dumps(report, separators=(',', ':'))}")
unreal.SystemLibrary.quit_editor()
