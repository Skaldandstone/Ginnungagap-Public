"""Validate editable MetaHuman source faces and assembly readiness."""

import json
from pathlib import Path

import unreal
from metahuman_toolset.metahuman import MetaHumanToolset


root = "/Game/Characters/MetaHumans/SourceFaces"
subsystem = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
assets = unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False)
results = []
for path in sorted(assets):
    character = unreal.load_asset(path)
    is_character = isinstance(character, unreal.MetaHumanCharacter)
    session = MetaHumanToolset.begin_edit(path) if is_character else None
    buildable = subsystem.can_build_meta_human(character, True) if is_character else False
    results.append({"path": path, "is_metahuman_character": is_character, "assembly_ready": bool(buildable)})
    if session:
        MetaHumanToolset.end_edit(session)

report = {
    "schema": 1,
    "status": "pass" if len(results) == 12 and all(item["is_metahuman_character"] and item["assembly_ready"] for item in results) else "fail",
    "source_count": len(results),
    "assembly_ready_count": sum(item["assembly_ready"] for item in results),
    "sources": results,
}
report_path = Path(unreal.Paths.project_saved_dir()) / "MetaHumanSourceValidation.json"
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"METAHUMAN_SOURCE_VALIDATION {json.dumps(report, separators=(',', ':'))}")
unreal.SystemLibrary.quit_editor()
