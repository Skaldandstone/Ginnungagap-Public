"""Refresh assembled MetaHuman material dependencies after shared assets are persisted.

MetaHuman assembly can save material functions before every Common dependency has
arrived on disk.  Loading the complete library in a fresh editor and updating the
functions/materials produces valid shader maps for the assembled characters.
"""

import json
from pathlib import Path

import unreal


ROOTS = (
    "/Game/Characters/MetaHumans/Common",
    "/Game/Characters/MetaHumans/Assembled",
)

registry = unreal.AssetRegistryHelpers.get_asset_registry()
asset_data = []
for root in ROOTS:
    asset_data.extend(registry.get_assets_by_path(root, recursive=True))

# Load the whole dependency set before touching any function. This is the key
# difference from the assembly-time save, when later Common assets may not exist.
loaded = []
for data in asset_data:
    asset = data.get_asset()
    if asset:
        loaded.append(asset)

functions = [asset for asset in loaded if isinstance(asset, unreal.MaterialFunctionInterface)]
materials = [asset for asset in loaded if isinstance(asset, unreal.Material)]
instances = [asset for asset in loaded if isinstance(asset, unreal.MaterialInstanceConstant)]

update_function = getattr(unreal.MaterialEditingLibrary, "update_material_function", None)
updated_functions = 0
if update_function:
    # Two passes settle function-to-function chains regardless of registry order.
    for _ in range(2):
        for function in functions:
            update_function(function)
            updated_functions += 1

for material in materials:
    unreal.MaterialEditingLibrary.recompile_material(material)

# Re-save only material assets. Meshes, Blueprints, DNA, and textures remain untouched.
for asset in functions + materials + instances:
    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)

report = {
    "status": "pass",
    "loaded": len(loaded),
    "functions": len(functions),
    "function_updates": updated_functions,
    "materials": len(materials),
    "instances": len(instances),
    "update_function_available": bool(update_function),
}
report_path = Path(unreal.Paths.project_saved_dir()) / "MetaHumanMaterialRepair.json"
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"METAHUMAN_MATERIAL_REPAIR {json.dumps(report, separators=(',', ':'))}")
unreal.SystemLibrary.quit_editor()
