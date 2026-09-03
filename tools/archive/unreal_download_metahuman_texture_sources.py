"""Download and store production texture sources for the MetaHuman library."""

import json
from pathlib import Path

import unreal
from metahuman_toolset.metahuman import MetaHumanToolset


SOURCE_ROOT = "/Game/Characters/MetaHumans/SourceFaces"
subsystem = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
assets = sorted(unreal.EditorAssetLibrary.list_assets(SOURCE_ROOT, recursive=True, include_folder=False))
results = []

for path in assets:
    character = unreal.load_asset(path)
    if not isinstance(character, unreal.MetaHumanCharacter):
        results.append({"path": path, "status": "not_metahuman"})
        continue
    session = MetaHumanToolset.begin_edit(path)
    if subsystem.can_build_meta_human(character, False):
        status = "already_ready"
    else:
        params = unreal.MetaHumanCharacterTextureRequestParams()
        params.report_progress = False
        params.blocking = True
        unreal.log(f"METAHUMAN_TEXTURE_BEGIN {path}")
        subsystem.request_texture_sources(character, params)
        status = "ready" if subsystem.can_build_meta_human(character, True) else "texture_failed"
        unreal.log(f"METAHUMAN_TEXTURE_END {path} status={status}")
    unreal.EditorAssetLibrary.save_loaded_asset(character, only_if_is_dirty=False)
    MetaHumanToolset.end_edit(session)
    results.append({"path": path, "status": status})

failed = [item for item in results if item["status"] not in {"ready", "already_ready"}]
report = {
    "schema": 1,
    "status": "pass" if len(results) == 12 and not failed else "fail",
    "source_count": len(results),
    "assembly_ready_count": sum(item["status"] in {"ready", "already_ready"} for item in results),
    "results": results,
}
report_path = Path(unreal.Paths.project_saved_dir()) / "MetaHumanTextureSources.json"
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"METAHUMAN_TEXTURE_LIBRARY {json.dumps(report, separators=(',', ':'))}")
unreal.SystemLibrary.quit_editor()
