"""Attach production-reference identity metadata to existing Unreal assets.

This script does not import, replace, rename, or modify mesh build settings. Pass one or more
`.production.json` paths through Unreal's Python command runner.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal


ROOT = Path(__file__).resolve().parents[2]


def resolve_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def manifest_args() -> list[Path]:
    results = []
    for value in sys.argv[1:]:
        if value.lower().endswith(".production.json"):
            results.append(resolve_path(value).resolve())
    if not results:
        raise RuntimeError("Pass at least one .production.json path")
    return results


def apply_packet(path: Path) -> tuple[int, int]:
    packet = json.loads(path.read_text(encoding="utf-8"))
    unreal_config = packet["build"]["unreal"]
    existing_assets = unreal_config.get("existing_assets", [])
    tags = {
        "ProductionReference.AssetId": packet["asset_id"],
        "ProductionReference.SchemaVersion": packet["schema_version"],
        "ProductionReference.Status": packet["status"],
        "ProductionReference.Ready": str(packet["production_ready"]).lower(),
        "ProductionReference.SourceSheet": packet["source_sheet"]["path"],
        "ProductionReference.SourceSHA256": packet["source_sheet"]["sha256"],
        "ProductionReference.Manifest": path.relative_to(ROOT).as_posix(),
    }
    blocker_count = sum(
        1 for conflict in packet["authority"]["conflicts"] if conflict.get("severity") == "blocker"
    )
    tags["ProductionReference.BlockingConflicts"] = str(blocker_count)

    updated = 0
    missing = 0
    for asset_path in existing_assets:
        if not unreal.EditorAssetLibrary.does_asset_exist(asset_path):
            unreal.log_warning(f"Production reference asset is missing: {asset_path}")
            missing += 1
            continue
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        for key, value in tags.items():
            unreal.EditorAssetLibrary.set_metadata_tag(asset, key, value)
        unreal.EditorAssetLibrary.save_loaded_asset(asset)
        unreal.log(f"Applied {packet['asset_id']} metadata to {asset_path}")
        updated += 1
    return updated, missing


def main() -> None:
    updated = 0
    missing = 0
    for path in manifest_args():
        packet_updated, packet_missing = apply_packet(path)
        updated += packet_updated
        missing += packet_missing
    unreal.log(f"Production reference metadata complete: {updated} updated, {missing} missing")


if __name__ == "__main__":
    main()
