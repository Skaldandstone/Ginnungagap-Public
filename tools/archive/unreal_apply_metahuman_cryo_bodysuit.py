"""Apply the fitted cryo layer to assembled MetaHumans and suppress placeholder clothing."""

import json
from pathlib import Path

import unreal


ASSEMBLED_ROOT = "/Game/Characters/MetaHumans/Assembled"
SUIT_PATH = (
    "/Game/Characters/Player/Undersuit/MetaHuman/"
    "MI_MH_CryoBodysuit_Standard.MI_MH_CryoBodysuit_Standard"
)
HIDE_PATH = "/Game/Characters/MetaHumans/Common/Materials/M_Hide.M_Hide"

suit = unreal.EditorAssetLibrary.load_asset(SUIT_PATH)
hide = unreal.EditorAssetLibrary.load_asset(HIDE_PATH)
if not suit or not hide:
    raise RuntimeError(f"Missing cryo material ({bool(suit)}) or MetaHuman hide material ({bool(hide)})")

body_meshes = []
placeholder_meshes = []
for path in unreal.EditorAssetLibrary.list_assets(ASSEMBLED_ROOT, recursive=True, include_folder=False):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(asset, unreal.SkeletalMesh):
        continue
    name = asset.get_name()
    if name.endswith("_BodyMesh"):
        materials = list(asset.get_editor_property("materials"))
        for index, slot in enumerate(materials):
            slot.material_interface = suit
            materials[index] = slot
        asset.set_editor_property("materials", materials)
        unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
        body_meshes.append(asset.get_path_name())
    elif name.endswith("_Outfits"):
        materials = list(asset.get_editor_property("materials"))
        for index, slot in enumerate(materials):
            slot.material_interface = hide
            materials[index] = slot
        asset.set_editor_property("materials", materials)
        unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
        placeholder_meshes.append(asset.get_path_name())

report = {
    "status": "pass" if body_meshes and placeholder_meshes else "fail",
    "body_meshes": body_meshes,
    "suppressed_placeholder_meshes": placeholder_meshes,
    "cryo_material": suit.get_path_name(),
    "hide_material": hide.get_path_name(),
}
report_path = Path(unreal.Paths.project_saved_dir()) / "MetaHumanCryoBodysuitApplication.json"
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"METAHUMAN_CRYO_APPLICATION {json.dumps(report, separators=(',', ':'))}")
if report["status"] != "pass":
    raise RuntimeError("No assembled body or placeholder garment mesh was updated")
unreal.SystemLibrary.quit_editor()
