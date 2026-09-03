"""Assemble the first production-ready optimized MetaHuman player identity."""

import json
import traceback
from pathlib import Path

import unreal


SOURCE_PATH = "/Game/Characters/MetaHumans/SourceFaces/MHC_Face01_Ada.MHC_Face01_Ada"
BUILD_ROOT = "/Game/Characters/MetaHumans/Assembled"
COMMON_ROOT = "/Game/Characters/MetaHumans/Common"
OUTPUT_NAME = "PlayerFace01"

subsystem = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
character = unreal.load_asset(SOURCE_PATH)
report = {
    "schema": 1,
    "status": "fail",
    "source": SOURCE_PATH,
    "pipeline": "optimized",
    "quality": "high",
    "build_root": BUILD_ROOT,
    "common_root": COMMON_ROOT,
    "output_name": OUTPUT_NAME,
    "assets": [],
    "common_assets": [],
}

try:
    if not isinstance(character, unreal.MetaHumanCharacter):
        raise RuntimeError(f"Source is not a MetaHumanCharacter: {SOURCE_PATH}")
    if not subsystem.try_add_object_to_edit(character):
        raise RuntimeError(f"Unable to enter edit mode: {SOURCE_PATH}")
    if not subsystem.can_build_meta_human(character, True):
        raise RuntimeError(f"Source is not assembly-ready: {SOURCE_PATH}")

    params = unreal.MetaHumanCharacterEditorBuildParameters()
    params.pipeline_type = unreal.MetaHumanDefaultPipelineType.OPTIMIZED
    params.pipeline_quality = unreal.MetaHumanQualityLevel.HIGH
    params.absolute_build_path = BUILD_ROOT
    params.name_override = OUTPUT_NAME
    params.common_folder_path = COMMON_ROOT
    params.enable_wardrobe_item_validation = False

    unreal.log(f"METAHUMAN_ASSEMBLY_BEGIN {SOURCE_PATH}")
    subsystem.build_meta_human(character=character, params=params)
    unreal.EditorAssetLibrary.save_directory(BUILD_ROOT, only_if_is_dirty=False, recursive=True)
    unreal.EditorAssetLibrary.save_directory(COMMON_ROOT, only_if_is_dirty=False, recursive=True)
    report["assets"] = sorted(
        unreal.EditorAssetLibrary.list_assets(BUILD_ROOT, recursive=True, include_folder=False)
    )
    report["common_assets"] = sorted(
        unreal.EditorAssetLibrary.list_assets(COMMON_ROOT, recursive=True, include_folder=False)
    )
    report["status"] = "pass" if report["assets"] and report["common_assets"] else "fail"
except Exception as exc:
    report["error"] = str(exc)
    unreal.log_error(traceback.format_exc())
finally:
    if character and subsystem.is_object_added_for_editing(character):
        subsystem.remove_object_to_edit(character)

report_path = Path(unreal.Paths.project_saved_dir()) / "MetaHumanAssemblyFace01.json"
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"METAHUMAN_ASSEMBLY_END {json.dumps(report, separators=(',', ':'))}")
unreal.SystemLibrary.quit_editor()
