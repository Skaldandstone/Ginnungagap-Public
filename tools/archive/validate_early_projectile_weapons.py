import json
from pathlib import Path

import unreal


ROOT = "/Game/Assets/Gameplay/EarlyProjectileWeapons"
MESH_ROOT = ROOT + "/Meshes"
DATA_ROOT = ROOT + "/Data/Weapons"
BLUEPRINT_ROOT = ROOT + "/Blueprints"
CATALOG_PATH = ROOT + "/Data/DA_EarlyProjectileWeaponCatalog"
REVIEW_MAP_PATH = "/Game/Assets/Maps/ModelLibrary/L_EarlyProjectileWeapons_Unreal"
REPORT_PATH = Path(unreal.Paths.project_dir()) / "Saved/Reports/EarlyProjectileWeaponValidation.json"

WEAPONS = (
    "BearingDispenser",
    "PressureBottleFastenerTool",
    "SmartSoftProjectileCarbine",
)


def asset(path):
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        raise AssertionError("Missing asset: " + path)
    loaded = unreal.EditorAssetLibrary.load_asset(path)
    if loaded is None:
        raise AssertionError("Could not load asset: " + path)
    return loaded


def check(condition, message, failures):
    if not condition:
        failures.append(message)


def profile_value(profile, property_name):
    return profile.get_editor_property(property_name)


def main():
    failures = []
    records = []

    for weapon_id in WEAPONS:
        mesh_path = f"{MESH_ROOT}/SM_{weapon_id}"
        definition_path = f"{DATA_ROOT}/DA_Weapon_{weapon_id}"
        blueprint_path = f"{BLUEPRINT_ROOT}/BP_Weapon_{weapon_id}"

        mesh = asset(mesh_path)
        definition = asset(definition_path)
        blueprint = asset(blueprint_path)

        safe_profile = definition.get_editor_property("safe_profile")
        unsafe_profile = definition.get_editor_property("unsafe_modified_profile")
        upgrade_stages = definition.get_editor_property("upgrade_stages")
        muzzle_offset = definition.get_editor_property("muzzle_offset")

        check(len(upgrade_stages) == 2, f"{weapon_id}: expected exactly two upgrade stages", failures)
        profiles = [safe_profile] + [stage.get_editor_property("firing_profile") for stage in upgrade_stages]
        for level, profile in enumerate(profiles):
            check(
                profile_value(profile, "delivery_mode") == unreal.WeaponDeliveryMode.PROJECTILE,
                f"{weapon_id}: level {level} is not a physical projectile profile",
                failures,
            )
            check(
                not profile_value(profile, "can_damage_hull"),
                f"{weapon_id}: level {level} should be hull-safe",
                failures,
            )
            check(
                profile_value(profile, "projectile_speed_cm_per_second") > 0.0,
                f"{weapon_id}: level {level} has no projectile speed",
                failures,
            )

        check(
            all(
                profile_value(profiles[index], "biological_damage")
                >= profile_value(profiles[index - 1], "biological_damage")
                for index in range(1, len(profiles))
            ),
            f"{weapon_id}: permanent upgrade damage regresses",
            failures,
        )
        check(
            all(
                profile_value(profiles[index], "max_range_cm")
                >= profile_value(profiles[index - 1], "max_range_cm")
                for index in range(1, len(profiles))
            ),
            f"{weapon_id}: permanent upgrade range regresses",
            failures,
        )
        check(
            profile_value(unsafe_profile, "delivery_mode") == unreal.WeaponDeliveryMode.PROJECTILE,
            f"{weapon_id}: unsafe conversion is not a physical projectile profile",
            failures,
        )
        check(
            profile_value(unsafe_profile, "can_damage_hull"),
            f"{weapon_id}: unsafe conversion does not carry hull risk",
            failures,
        )
        check(muzzle_offset.x > 0.0, f"{weapon_id}: muzzle is not forward of the origin", failures)

        bounds = mesh.get_bounds().box_extent * 2.0
        check(bounds.x > 10.0 and bounds.y > 5.0 and bounds.z > 5.0, f"{weapon_id}: invalid mesh bounds", failures)

        cdo = unreal.get_default_object(blueprint.generated_class())
        cdo_definition = cdo.get_editor_property("definition")
        visual_mesh = cdo.get_editor_property("visual_mesh").get_editor_property("static_mesh")
        check(
            cdo_definition is not None and cdo_definition.get_path_name() == definition.get_path_name(),
            f"{weapon_id}: Blueprint does not reference its definition",
            failures,
        )
        check(
            visual_mesh is not None and visual_mesh.get_path_name() == mesh.get_path_name(),
            f"{weapon_id}: Blueprint does not reference its generated mesh",
            failures,
        )

        records.append(
            {
                "weapon_id": weapon_id,
                "upgrade_stages": len(upgrade_stages),
                "delivery_mode": "PhysicalProjectile",
                "safe_hull_damage": bool(profile_value(safe_profile, "can_damage_hull")),
                "unsafe_hull_damage": bool(profile_value(unsafe_profile, "can_damage_hull")),
                "mesh_size_cm": [bounds.x, bounds.y, bounds.z],
            }
        )

    catalog = asset(CATALOG_PATH)
    entries = catalog.get_editor_property("entries")
    content_ids = {str(entry.get_editor_property("content_id")) for entry in entries}
    check(len(entries) == 3, "Seed catalog does not contain exactly three entries", failures)
    check(content_ids == set(WEAPONS), "Seed catalog content IDs do not match the three weapons", failures)
    check(
        unreal.EditorAssetLibrary.does_asset_exist(REVIEW_MAP_PATH),
        "Early projectile weapon review map is missing",
        failures,
    )

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
        raise AssertionError("Early projectile weapon validation failed: " + "; ".join(failures))
    unreal.log("Early projectile weapon validation passed: 3 weapons, 6 upgrades, 3 unsafe conversions")


if __name__ == "__main__":
    main()
