"""Validate serialized Fab chassis assignments for Salvage Gameplay Batch 03."""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
MAPPING_PATH = PROJECT / "Art/Weapons/Fab/CosmoartLowPolyWeapons/WeaponConceptMapping.json"
REPORT_PATH = PROJECT / "Saved/Reports/FabWeaponMappingValidation.json"
BP_ROOT = "/Game/Assets/Gameplay/SalvageBatch03/Blueprints/Gear"
DATA_ROOT = "/Game/Assets/Gameplay/SalvageBatch03/Data/Weapons"
MESH_ROOT = "/Game/Assets/Gameplay/SalvageBatch03/Meshes"
CATALOG_PATH = "/Game/Assets/Gameplay/SalvageBatch03/Data/DA_SalvageBatch03_SeedCatalog"
MAP_PATH = "/Game/Assets/Maps/ModelLibrary/L_SalvageGameplayBatch03_Unreal"


def object_path(package_path: str) -> str:
    return f"{package_path}.{package_path.rsplit('/', 1)[-1]}"


def main() -> None:
    mappings = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))["mappings"]
    failures: list[str] = []
    records = []
    composite_count = 0

    for entry in mappings:
        concept_id = entry["id"]
        donor_modules = entry.get("donorModules", [])
        if donor_modules:
            composite_count += 1
            expected_mesh_path = f"{MESH_ROOT}/SM_{concept_id}"
        else:
            expected_mesh_path = entry["unrealAsset"]
        expected_mesh = unreal.EditorAssetLibrary.load_asset(expected_mesh_path)
        if not isinstance(expected_mesh, unreal.StaticMesh):
            failures.append(f"{concept_id}: expected visual mesh is missing: {expected_mesh_path}")
        for module in donor_modules:
            if not isinstance(unreal.EditorAssetLibrary.load_asset(module["unrealAsset"]), unreal.StaticMesh):
                failures.append(f"{concept_id}: donor mesh is missing: {module['unrealAsset']}")
        blueprint_path = f"{BP_ROOT}/BP_Weapon_{concept_id}"
        definition_path = f"{DATA_ROOT}/DA_Weapon_{concept_id}"
        blueprint = unreal.EditorAssetLibrary.load_asset(blueprint_path)
        definition = unreal.EditorAssetLibrary.load_asset(definition_path)
        if not isinstance(blueprint, unreal.Blueprint):
            failures.append(f"Missing Blueprint: {blueprint_path}")
            continue
        if not isinstance(definition, unreal.ShipboardWeaponDefinition):
            failures.append(f"Missing definition: {definition_path}")
            continue

        cdo = unreal.get_default_object(blueprint.generated_class())
        visual = cdo.get_editor_property("visual_mesh")
        muzzle = cdo.get_editor_property("muzzle")
        assigned_mesh = visual.get_editor_property("static_mesh")
        definition_mesh = definition.get_editor_property("weapon_mesh")
        relative_location = visual.get_editor_property("relative_location")
        relative_rotation = visual.get_editor_property("relative_rotation")
        relative_scale = visual.get_editor_property("relative_scale3d")
        muzzle_location = muzzle.get_editor_property("relative_location")

        if assigned_mesh != expected_mesh:
            failures.append(f"{concept_id}: Blueprint mesh does not match {expected_mesh_path}")
        if definition_mesh != expected_mesh:
            failures.append(f"{concept_id}: definition mesh does not match {expected_mesh_path}")
        if muzzle_location.x <= 0.0:
            failures.append(f"{concept_id}: muzzle is not forward of the actor origin")

        records.append({
            "id": concept_id,
            "blueprint": object_path(blueprint_path),
            "definition": object_path(definition_path),
            "mesh": assigned_mesh.get_path_name() if assigned_mesh else "",
            "relative_location": [relative_location.x, relative_location.y, relative_location.z],
            "relative_rotation": [relative_rotation.pitch, relative_rotation.yaw, relative_rotation.roll],
            "relative_scale": [relative_scale.x, relative_scale.y, relative_scale.z],
            "muzzle_location": [muzzle_location.x, muzzle_location.y, muzzle_location.z],
            "confidence": entry["confidence"],
            "visual_source": "Fab modular composite" if donor_modules else "Fab chassis",
            "fab_chassis": entry["unrealAsset"],
            "fab_donor_assets": [module["unrealAsset"] for module in donor_modules],
        })

    catalog = unreal.EditorAssetLibrary.load_asset(CATALOG_PATH)
    catalog_entries = len(catalog.get_editor_property("entries")) if catalog else 0
    if catalog_entries != 18:
        failures.append(f"Seed catalog contains {catalog_entries} entries; expected 18")
    if not unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        failures.append(f"Missing review map: {MAP_PATH}")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps({
        "validated_weapon_count": len(records),
        "validated_composite_count": composite_count,
        "catalog_entry_count": catalog_entries,
        "review_map": MAP_PATH,
        "failures": failures,
        "weapons": records,
    }, indent=2), encoding="utf-8")
    if failures:
        raise RuntimeError("Fab weapon mapping validation failed: " + "; ".join(failures))
    unreal.log(f"Validated {len(records)} serialized Fab weapon mappings and {catalog_entries} catalog entries")


if __name__ == "__main__":
    main()
