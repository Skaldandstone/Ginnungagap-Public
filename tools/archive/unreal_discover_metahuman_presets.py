"""List installed MetaHuman Character preset assets for library generation."""

import json
from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
report_path = root / "Saved" / "MetaHumanPresetDiscovery.json"
registry = unreal.AssetRegistryHelpers.get_asset_registry()
class_path = unreal.TopLevelAssetPath("/Script/MetaHumanCharacter", "MetaHumanCharacter")
assets = registry.get_assets_by_class(class_path, True)
records = []
for asset in assets:
    package_name = str(asset.package_name)
    records.append(
        {
            "asset_name": str(asset.asset_name),
            "package_name": package_name,
            "package_path": str(asset.package_path),
            "is_engine_or_plugin_content": package_name.startswith("/MetaHumanCharacter/") or package_name.startswith("/Engine/"),
        }
    )

report_path.write_text(json.dumps({"count": len(records), "assets": records}, indent=2), encoding="utf-8")
unreal.log(f"METAHUMAN_PRESET_DISCOVERY count={len(records)} report={report_path}")
unreal.SystemLibrary.quit_editor()
