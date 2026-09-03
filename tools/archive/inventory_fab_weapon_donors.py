"""Inventory recently added Fab packs for reusable weapon/tool donor meshes."""

from __future__ import annotations

import json
from pathlib import Path
import re

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
REPORT = PROJECT / "Saved/Reports/FabWeaponDonorInventory.json"
API_REPORT = PROJECT / "Saved/Reports/FabCompositeGeometryApi.txt"
ROOTS = (
    "/Game/Ice_Station",
    "/Game/Sci-Fi_Flying_Cargo_Ship",
    "/Game/Alien_Portal",
    "/Game/Alien_Biomass",
)

CANDIDATE_PATTERN = re.compile(
    r"(reactor|propeller|generator|antenna|pipe|scientific|handle|turret|citern|"
    r"computer|air_evac|aeration|alien_tech)",
    re.IGNORECASE,
)


def main() -> None:
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    records = []
    for root in ROOTS:
        for asset_data in registry.get_assets_by_path(unreal.Name(root), recursive=True):
            if not CANDIDATE_PATTERN.search(str(asset_data.asset_name)):
                continue
            asset = asset_data.get_asset()
            if not isinstance(asset, unreal.StaticMesh):
                continue
            bounds = asset.get_bounds()
            size = bounds.box_extent * 2.0
            records.append({
                "pack": root.split("/")[2],
                "asset": asset.get_path_name(),
                "name": str(asset_data.asset_name),
                "size_cm": [size.x, size.y, size.z],
                "longest_cm": max(size.x, size.y, size.z),
                "material_slots": len(asset.get_editor_property("static_materials")),
            })

    records.sort(key=lambda record: (record["pack"], record["asset"]))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "roots": ROOTS,
        "candidate_static_mesh_count": len(records),
        "candidate_pattern": CANDIDATE_PATTERN.pattern,
        "assets": records,
    }, indent=2), encoding="utf-8")
    API_REPORT.write_text("\n\n".join((
        unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2.__doc__ or "",
        unreal.GeometryScript_MeshEdits.append_mesh_transformed.__doc__ or "",
        unreal.GeometryScript_MeshTransforms.transform_mesh.__doc__ or "",
    )), encoding="utf-8")
    unreal.log(f"Inventoried {len(records)} Fab donor meshes across {len(ROOTS)} packs")


if __name__ == "__main__":
    main()
