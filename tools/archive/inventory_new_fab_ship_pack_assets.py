"""Inventory ship-relevant meshes and materials from the newly installed Fab packs."""
from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
REPORT = PROJECT / "Saved/Reports/NewFabShipPackInventory.json"

ASSET_PATHS = (
    "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Hangar/SM_hangar",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Cargo_modules/SM_cargo_body_01",
    "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Reactor/SM_reactor",
    "/Game/SciFi_Cliff/Meshes/Circular_module/SM_circular_module_03",
    "/Game/SciFi_Cliff/Meshes/Antenna/SM_antenna_02",
    "/Game/Ice_Station/Meshes/Building/SM_base_building_big",
    "/Game/Ice_Station/Meshes/Antennas/SM_building_details_01",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_POWER_GENERATOR_01",
    "/Game/MaterialsScifi/Materials/Instances/MI_Scifi_Panels_06",
    "/Game/MaterialsScifi/Materials/Instances/MI_Scifi_Panels_09",
    "/Game/MaterialsScifi/Materials/Instances/MI_Scifi_Panels_13",
    "/Game/MaterialsScifi/Materials/Instances/MI_Scifi_Panels_14",
)


def vector(value):
    return [round(value.x, 3), round(value.y, 3), round(value.z, 3)]


rows = []
for object_path in ASSET_PATHS:
        asset = unreal.EditorAssetLibrary.load_asset(object_path)
        if isinstance(asset, unreal.StaticMesh):
            bounds = asset.get_bounds()
            materials = []
            for slot in asset.get_editor_property("static_materials"):
                material = slot.get_editor_property("material_interface")
                materials.append(material.get_path_name() if material else None)
            try:
                triangles = int(asset.get_num_triangles(0))
            except Exception:
                triangles = None
            rows.append({
                "type": "StaticMesh",
                "path": asset.get_path_name(),
                "size_cm": vector(bounds.box_extent * 2.0),
                "origin_cm": vector(bounds.origin),
                "triangles_lod0": triangles,
                "materials": materials,
            })
        elif isinstance(asset, unreal.MaterialInterface):
            rows.append({"type": "Material", "path": asset.get_path_name()})

rows.sort(key=lambda item: (item["type"], item["path"].lower()))
payload = {
    "version": 1,
    "candidate_paths": list(ASSET_PATHS),
    "asset_count": len(rows),
    "assets": rows,
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
unreal.log(f"NEW FAB SHIP INVENTORY: {len(rows)} candidates -> {REPORT}")
