"""Audit installed Fab animation packs for Bloom enemy compatibility and intent."""

import json
from pathlib import Path

import unreal


ROOTS = (
    "/Game/DeadBodies_Poses_nikoff",
    "/Game/Characters/Mannequins/Animations",
)
MESHES = (
    "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt/Working/Iteration_02_ConceptSilhouette/SKM_PrimaryOversuit_QuinnProjectionShell_I02",
    "/Game/DeadBodies_Poses_nikoff/Demo/Mannequins/Meshes/SKM_Manny_Simple",
)


def safe_property(asset, name):
    try:
        value = asset.get_editor_property(name)
        return value.get_path_name() if value else None
    except Exception:
        return None


def safe_length(asset):
    try:
        return float(asset.get_play_length())
    except Exception:
        try:
            return float(asset.get_editor_property("sequence_length"))
        except Exception:
            return None


records = []
for root in ROOTS:
    if not unreal.EditorAssetLibrary.does_directory_exist(root):
        continue
    for path in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if not asset:
            continue
        class_name = asset.get_class().get_name()
        if class_name not in ("AnimSequence", "AnimMontage", "PoseAsset", "BlendSpace", "BlendSpace1D"):
            continue
        records.append(
            {
                "path": path.split(".", 1)[0],
                "class": class_name,
                "skeleton": safe_property(asset, "skeleton"),
                "preview_mesh": safe_property(asset, "preview_skeletal_mesh"),
                "length_seconds": safe_length(asset),
            }
        )

records.sort(key=lambda item: item["path"].lower())
mesh_records = []
for path in MESHES:
    mesh = unreal.EditorAssetLibrary.load_asset(path)
    mesh_records.append(
        {
            "path": path,
            "class": mesh.get_class().get_name() if mesh else None,
            "skeleton": safe_property(mesh, "skeleton") if mesh else None,
        }
    )
output = Path(unreal.SystemLibrary.get_project_saved_directory()) / "Reports/BloomFabAnimationAudit.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(
    json.dumps({"roots": ROOTS, "meshes": mesh_records, "assets": records}, indent=2),
    encoding="utf-8",
)
unreal.log(f"BLOOM FAB ANIMATION AUDIT: {len(records)} assets written to {output}")
