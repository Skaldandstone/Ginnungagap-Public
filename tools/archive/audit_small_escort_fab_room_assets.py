"""Audit imported Fab assets proposed for the Small Escort operations district.

This script is intentionally read-only with respect to Unreal content. It loads a curated set of
vendor assets, records their classes and static-mesh bounds, and writes a JSON report under
Saved/Reports so dressing scripts can use explicit, reviewed scale choices.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
REPORT = PROJECT / "Saved/Reports/SmallEscortFabRoomAssetAudit.json"

ASSETS = (
    # Ice Station: modular architecture and inhabited-room props.
    "/Game/Ice_Station/Meshes/Walls/SM_interior_wall",
    "/Game/Ice_Station/Meshes/Walls/SM_interior_wall_02",
    "/Game/Ice_Station/Meshes/Walls/SM_interior_wall_03",
    "/Game/Ice_Station/Meshes/Walls/SM_interior_wall_04",
    "/Game/Ice_Station/Meshes/Walls/SM_interior_wall_angle",
    "/Game/Ice_Station/Meshes/Walls/SM_module_01_interior",
    "/Game/Ice_Station/Meshes/Floor/SM_floor",
    "/Game/Ice_Station/Meshes/Floor/SM_floor_02",
    "/Game/Ice_Station/Meshes/Floor/SM_large_floor_module",
    "/Game/Ice_Station/Meshes/Door/SM_Door",
    "/Game/Ice_Station/Meshes/Door/SM_door_frame",
    "/Game/Ice_Station/Meshes/Door/SM_small_door",
    "/Game/Ice_Station/Meshes/Computer/SM_computer_01",
    "/Game/Ice_Station/Meshes/Computer/SM_computer_02",
    "/Game/Ice_Station/Meshes/Computer/SM_computer_circular",
    "/Game/Ice_Station/Meshes/Computer/SM_top_computer",
    "/Game/Ice_Station/Meshes/interior/SM_generator",
    "/Game/Ice_Station/Meshes/interior/SM_module_round_01",
    "/Game/Ice_Station/Meshes/Bed/SM_bed_01",
    "/Game/Ice_Station/Meshes/Bed/SM_bed_02",
    "/Game/Ice_Station/Meshes/Chair/SM_chair",
    "/Game/Ice_Station/Meshes/Table/SM_Table",
    "/Game/Ice_Station/Meshes/Crates/SM_crate_01",
    "/Game/Ice_Station/Meshes/Crates/SM_crate_04",
    "/Game/Ice_Station/Meshes/Crates/SM_large_crate_01",
    "/Game/Ice_Station/Meshes/Pipe/SM_pipe_group_01",
    "/Game/Ice_Station/Meshes/Pipe/SM_pipe_group_02",
    "/Game/Ice_Station/Meshes/stairs/SM_ramp_module",
    "/Game/Ice_Station/Meshes/stairs/SM_stairs_01",
    "/Game/Ice_Station/Blueprint/BP_sliding_doors",
    "/Game/Ice_Station/Blueprint/BP_light_white",
    "/Game/Ice_Station/Blueprint/BP_light_red",
    # Flying Cargo Ship: industrial, cargo, corridor, and reactor dressing.
    "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Walls/SM_corridor",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Walls/SM_wall_02",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Walls/SM_wall_03",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Floor/SM_floor_corridor",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Ceiling_detail/SM_ceiling_detal_01",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Ceiling_detail/SM_ceiling_square",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Reactor/SM_reactor",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Reactor/SM_small_reactor",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Pipes/SM_large_pipe_01",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Pipes/SM_pipe_03",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Container/SM_container_blue",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Container/SM_container_orange",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Container/SM_container_red",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Blueprint/BP_reactor",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Blueprint/BP_reactor_02",
    # Material pack used for controlled room-color variants.
    "/Game/MaterialsScifi/Materials/Instances/MI_Scifi_Panels_11",
)


def vector_dict(value):
    return {"x": round(value.x, 3), "y": round(value.y, 3), "z": round(value.z, 3)}


def audit_asset(path):
    asset = unreal.load_asset(path)
    if not asset:
        return {"path": path, "status": "missing"}

    item = {
        "path": path,
        "status": "loaded",
        "class": asset.get_class().get_name(),
    }
    if isinstance(asset, unreal.StaticMesh):
        bounds = asset.get_bounding_box()
        minimum = bounds.min
        maximum = bounds.max
        item.update({
            "bounds_min_cm": vector_dict(minimum),
            "bounds_max_cm": vector_dict(maximum),
            "size_cm": vector_dict(maximum - minimum),
            "material_slots": len(asset.get_editor_property("static_materials")),
        })
    elif isinstance(asset, unreal.Blueprint):
        generated = asset.generated_class()
        item["generated_class"] = generated.get_name() if generated else None
    return item


def main():
    results = [audit_asset(path) for path in ASSETS]
    missing = [item["path"] for item in results if item["status"] != "loaded"]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "asset_count": len(results),
        "loaded_count": len(results) - len(missing),
        "missing": missing,
        "assets": results,
    }, indent=2), encoding="utf-8")
    if missing:
        raise RuntimeError("Fab room asset audit found missing assets: " + ", ".join(missing))
    unreal.log(f"Small Escort Fab room asset audit passed: {len(results)} assets")


if __name__ == "__main__":
    main()
