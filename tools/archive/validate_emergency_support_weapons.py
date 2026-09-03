"""Validate the generated emergency-support weapon batch."""

import json
from pathlib import Path

import unreal


ROOT = "/Game/Assets/Gameplay/EmergencySupportWeapons"
MESH_ROOT = ROOT + "/Meshes"
DATA_ROOT = ROOT + "/Data/Weapons"
BLUEPRINT_ROOT = ROOT + "/Blueprints"
CATALOG_PATH = ROOT + "/Data/DA_EmergencySupportWeaponCatalog"
REVIEW_MAP_PATH = "/Game/Assets/Maps/ModelLibrary/L_EmergencySupportWeapons_Unreal"
REPORT_PATH = Path(unreal.Paths.project_dir()) / "Saved/Reports/EmergencySupportWeaponValidation.json"

WEAPONS = {
    "AcousticComplianceEmitter": ("TRACE", "ACOUSTIC_DISORIENT"),
    "DoorBreachRam": ("TRACE", "STAGGER"),
    "RescueShield": ("RESCUE_SHIELD", "NONE"),
    "FlashDazzleArray": ("TRACE", "FLASH_DAZZLE"),
    "MagneticScrapFlinger": ("PROJECTILE", "STAGGER"),
}


def load_asset(path):
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        raise AssertionError("Missing asset: " + path)
    result = unreal.EditorAssetLibrary.load_asset(path)
    if result is None:
        raise AssertionError("Could not load asset: " + path)
    return result


def check(condition, message, failures):
    if not condition:
        failures.append(message)


def value(profile, property_name):
    return profile.get_editor_property(property_name)


def main():
    failures = []
    records = []
    for weapon_id, (mode_name, effect_name) in WEAPONS.items():
        mesh = load_asset(f"{MESH_ROOT}/SM_{weapon_id}")
        definition = load_asset(f"{DATA_ROOT}/DA_Weapon_{weapon_id}")
        blueprint = load_asset(f"{BLUEPRINT_ROOT}/BP_Weapon_{weapon_id}")
        safe = definition.get_editor_property("safe_profile")
        unsafe = definition.get_editor_property("unsafe_modified_profile")
        stages = definition.get_editor_property("upgrade_stages")
        profiles = [safe] + [stage.get_editor_property("firing_profile") for stage in stages]
        expected_mode = getattr(unreal.WeaponDeliveryMode, mode_name)
        expected_effect = getattr(unreal.WeaponControlEffect, effect_name)

        check(len(stages) == 2, f"{weapon_id}: expected two permanent upgrades", failures)
        for level, profile in enumerate(profiles):
            check(value(profile, "delivery_mode") == expected_mode,
                  f"{weapon_id}: level {level} delivery mode is incorrect", failures)
            check(value(profile, "control_effect") == expected_effect,
                  f"{weapon_id}: level {level} control effect is incorrect", failures)
            check(value(profile, "cooldown_seconds") > 0,
                  f"{weapon_id}: level {level} cooldown is invalid", failures)
            if mode_name == "PROJECTILE":
                check(value(profile, "projectile_speed_cm_per_second") > 0,
                      f"{weapon_id}: level {level} projectile speed is invalid", failures)
            if mode_name == "RESCUE_SHIELD":
                extents = value(profile, "shield_half_extents_cm")
                check(value(profile, "shield_duration_seconds") > 0,
                      f"{weapon_id}: level {level} shield duration is invalid", failures)
                check(extents.y >= 40 and extents.z >= 60,
                      f"{weapon_id}: level {level} shield coverage is too small", failures)
            elif effect_name != "NONE":
                check(value(profile, "control_duration_seconds") > 0,
                      f"{weapon_id}: level {level} control duration is invalid", failures)

        check(all(value(profiles[index], "max_range_cm") >= value(profiles[index-1], "max_range_cm")
                  for index in range(1, len(profiles))),
              f"{weapon_id}: permanent upgrade range regresses", failures)
        check(all(value(profiles[index], "cooldown_seconds") <= value(profiles[index-1], "cooldown_seconds")
                  for index in range(1, len(profiles))),
              f"{weapon_id}: permanent upgrade cadence regresses", failures)
        check(value(unsafe, "delivery_mode") == expected_mode,
              f"{weapon_id}: unsafe conversion delivery mode is incorrect", failures)

        bounds = mesh.get_bounds().box_extent * 2.0
        check(bounds.x > 20 and bounds.y > 10 and bounds.z > 10,
              f"{weapon_id}: invalid generated mesh bounds", failures)
        cdo = unreal.get_default_object(blueprint.generated_class())
        cdo_definition = cdo.get_editor_property("definition")
        visual_mesh = cdo.get_editor_property("visual_mesh").get_editor_property("static_mesh")
        check(cdo_definition and cdo_definition.get_path_name() == definition.get_path_name(),
              f"{weapon_id}: Blueprint definition reference mismatch", failures)
        check(visual_mesh and visual_mesh.get_path_name() == mesh.get_path_name(),
              f"{weapon_id}: Blueprint mesh reference mismatch", failures)
        records.append({
            "weapon_id": weapon_id,
            "delivery_mode": mode_name,
            "control_effect": effect_name,
            "upgrade_stages": len(stages),
            "mesh_size_cm": [bounds.x, bounds.y, bounds.z],
        })

    catalog = load_asset(CATALOG_PATH)
    entries = catalog.get_editor_property("entries")
    content_ids = {str(entry.get_editor_property("content_id")) for entry in entries}
    check(len(entries) == len(WEAPONS), "Seed catalog entry count is incorrect", failures)
    check(content_ids == set(WEAPONS), "Seed catalog content IDs are incorrect", failures)
    check(unreal.EditorAssetLibrary.does_asset_exist(REVIEW_MAP_PATH), "Review map is missing", failures)

    report = {
        "passed": not failures,
        "weapon_count": len(records),
        "upgrade_stage_count": sum(record["upgrade_stages"] for record in records),
        "catalog_entry_count": len(entries),
        "review_map": REVIEW_MAP_PATH,
        "weapons": records,
        "failures": failures,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    if failures:
        raise AssertionError("Emergency-support weapon validation failed: " + "; ".join(failures))
    unreal.log("Emergency-support validation passed: 5 weapons, 10 upgrades")


if __name__ == "__main__":
    main()
