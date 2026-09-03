"""Create the editable MetaHuman source-face library used by the character creator."""

import json
from pathlib import Path

import unreal


SOURCE_ROOT = "/MetaHumanCharacter/Optional/Presets"
DESTINATION_ROOT = "/Game/Characters/MetaHumans/SourceFaces"
FACE_PRESETS = (
    ("Face01", "Ada"),
    ("Face02", "Bruce"),
    ("Face03", "Aoi"),
    ("Face04", "Isaiah"),
    ("Face05", "Jelena"),
    ("Face06", "Omari"),
    ("Face07", "Asha"),
    ("Face08", "Celeste"),
    ("Face09", "Jorge"),
    ("Face10", "Lani"),
    ("Face11", "Sook-ja"),
    ("Face12", "Zuri"),
)


def main() -> None:
    if not unreal.MetaHumanGeneratorSubsystemWrapper.is_optional_content_installed():
        raise RuntimeError("MetaHuman Creator Core Data is not installed")

    created = []
    existing = []
    failures = []
    for face_id, preset_name in FACE_PRESETS:
        source = f"{SOURCE_ROOT}/{preset_name}"
        destination = f"{DESTINATION_ROOT}/MHC_{face_id}_{preset_name.replace('-', '')}"
        if unreal.EditorAssetLibrary.does_asset_exist(destination):
            existing.append(destination)
            continue
        asset = unreal.EditorAssetLibrary.duplicate_asset(source, destination)
        if asset:
            unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
            created.append(destination)
        else:
            failures.append({"source": source, "destination": destination})

    report = {
        "schema": 1,
        "source_face_count": len(FACE_PRESETS),
        "created": created,
        "already_existing": existing,
        "failures": failures,
        "visual_combinations": len(FACE_PRESETS) * 4 * 8 * 6,
        "independent_axes": {
            "faces": len(FACE_PRESETS),
            "body_presets": 4,
            "skin_tones": 8,
            "hair_styles": 6,
            "voice_profiles": 4,
            "suit_roles": 4,
        },
    }
    report_path = Path(unreal.Paths.project_saved_dir()) / "MetaHumanSourceLibrary.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"METAHUMAN_SOURCE_LIBRARY {json.dumps(report, separators=(',', ':'))}")
    if failures:
        raise RuntimeError(f"Failed to create {len(failures)} MetaHuman source assets")
    unreal.SystemLibrary.quit_editor()


main()
