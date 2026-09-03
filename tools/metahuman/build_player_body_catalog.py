"""
Create Ginnungagap's starter MetaHuman body lattice and runtime catalog.

The nine MetaHuman Character assets are editor-authored visual sources. Exact gameplay
measurements remain in FCharacterBodyProfile. Set GGP_ASSEMBLE_METAHUMANS=1 to also
request cloud rigging/textures and build UE Optimized actors; optionally set
GGP_METAHUMAN_VARIANT to one variant id while validating the pipeline.
"""

import os
import unreal


CHARACTER_PACKAGE = "/Game/Characters/MetaHumans/Generated"
ASSEMBLY_PACKAGE = "/Game/Characters/MetaHumans/Assembled"
COMMON_PACKAGE = "/Game/Characters/MetaHumans/Common"
CATALOG_PACKAGE = "/Game/Characters/MetaHumans"
CATALOG_NAME = "DA_PlayerMetaHumanCatalog"
CATALOG_PATH = f"{CATALOG_PACKAGE}/{CATALOG_NAME}"
ASSEMBLE = os.environ.get("GGP_ASSEMBLE_METAHUMANS", "0") == "1"
ONLY_VARIANT = os.environ.get("GGP_METAHUMAN_VARIANT", "").strip().lower()
REAUTHOR = os.environ.get("GGP_REAUTHOR_METAHUMANS", "0") == "1"


STATURES = (
    {"id": "compact", "label": "Compact", "height": 155.0},
    {"id": "medium", "label": "Medium", "height": 175.0},
    {"id": "tall", "label": "Tall", "height": 198.0},
)

FRAMES = (
    {
        "id": "narrow",
        "label": "Narrow",
        "shoulder": 37.0,
        "depth": 22.0,
        "mass": 58.0,
        "chest": 86.0,
        "waist": 70.0,
        "hip": 88.0,
        "fat": -0.60,
    },
    {
        "id": "standard",
        "label": "Standard",
        "shoulder": 44.0,
        "depth": 26.0,
        "mass": 78.0,
        "chest": 102.0,
        "waist": 86.0,
        "hip": 102.0,
        "fat": 0.0,
    },
    {
        "id": "broad",
        "label": "Broad",
        "shoulder": 53.0,
        "depth": 32.0,
        "mass": 108.0,
        "chest": 126.0,
        "waist": 108.0,
        "hip": 122.0,
        "fat": 0.50,
    },
)


def variant_specs():
    for stature in STATURES:
        for frame in FRAMES:
            variant_id = f"{stature['id']}_{frame['id']}"
            yield {
                **frame,
                "id": variant_id,
                "label": f"{stature['label']} / {frame['label']}",
                "asset_name": "MHC_Player_" + "_".join(part.title() for part in variant_id.split("_")),
                "height": stature["height"],
            }


def create_or_load_character(asset_tools, spec):
    asset_path = f"{CHARACTER_PACKAGE}/{spec['asset_name']}"
    character = unreal.load_asset(asset_path)
    created = character is None
    if character is None:
        character = asset_tools.create_asset(
            asset_name=spec["asset_name"],
            package_path=CHARACTER_PACKAGE,
            asset_class=unreal.MetaHumanCharacter,
            factory=unreal.new_object(type=unreal.MetaHumanCharacterFactoryNew),
        )
    if character is None:
        raise RuntimeError(f"Unable to create MetaHuman Character {asset_path}")
    return asset_path, character, created


def apply_body_constraints(subsystem, character, spec):
    if not subsystem.try_add_object_to_edit(character):
        raise RuntimeError(f"Unable to edit {character.get_path_name()}; close its asset editor or remove its rig first")
    try:
        constraints = subsystem.get_body_constraints(
            character=character,
            scale_measurement_ranges_with_height=False,
        )
        by_name = {str(item.name): item for item in constraints}
        targets = {
            "Height": spec["height"],
            "Across Shoulder": spec["shoulder"],
            "Chest": spec["chest"],
            "Waist": spec["waist"],
            "Hip": spec["hip"],
            "Fat": spec["fat"],
        }
        missing = sorted(set(targets) - set(by_name))
        if missing:
            raise RuntimeError(f"Installed MetaHuman body model is missing constraints: {missing}")

        for name, target in targets.items():
            constraint = by_name[name]
            if target < constraint.min_measurement or target > constraint.max_measurement:
                raise RuntimeError(
                    f"{spec['id']} requests {name}={target}, outside "
                    f"{constraint.min_measurement}..{constraint.max_measurement}"
                )
            constraint.is_active = True
            constraint.target_measurement = target

        subsystem.set_body_constraints(character=character, body_constraints=list(by_name.values()))
        subsystem.commit_body_state(character=character)
        unreal.EditorAssetLibrary.save_loaded_asset(character, only_if_is_dirty=False)
    finally:
        if subsystem.is_object_added_for_editing(character):
            subsystem.remove_object_to_edit(character)


def assemble_character(subsystem, character, spec):
    if not ASSEMBLE or (ONLY_VARIANT and ONLY_VARIANT != spec["id"]):
        return

    generated_class_path = (
        f"{ASSEMBLY_PACKAGE}/{spec['asset_name']}/BP_{spec['asset_name']}."
        f"BP_{spec['asset_name']}_C"
    )
    if unreal.load_class(None, generated_class_path) is not None:
        unreal.log_warning(f"GGP_METAHUMAN_ASSEMBLY_EXISTS={spec['id']}")
        return

    if not subsystem.try_add_object_to_edit(character):
        raise RuntimeError(f"Unable to open {character.get_path_name()} for assembly")
    try:
        if not subsystem.can_build_meta_human(character=character):
            autorig_params = unreal.MetaHumanCharacterAutoRiggingRequestParams()
            autorig_params.blocking = True
            autorig_params.report_progress = False
            autorig_params.rig_type = unreal.MetaHumanRigType.JOINTS_ONLY
            subsystem.request_auto_rigging(character=character, params=autorig_params)

        if not character.has_high_resolution_textures:
            texture_params = unreal.MetaHumanCharacterTextureRequestParams()
            texture_params.blocking = True
            texture_params.report_progress = False
            subsystem.request_texture_sources(character=character, params=texture_params)
        if not subsystem.can_build_meta_human(character=character):
            raise RuntimeError(f"MetaHuman services did not make {spec['id']} buildable")

        # Preserve completed cloud work before the expensive local assembly/material-bake stage.
        unreal.EditorAssetLibrary.save_loaded_asset(character, only_if_is_dirty=False)

        build_params = unreal.MetaHumanCharacterEditorBuildParameters()
        build_params.pipeline_type = unreal.MetaHumanDefaultPipelineType.OPTIMIZED
        build_params.pipeline_quality = unreal.MetaHumanQualityLevel.MEDIUM
        build_params.absolute_build_path = ASSEMBLY_PACKAGE
        build_params.common_folder_path = COMMON_PACKAGE
        build_params.enable_wardrobe_item_validation = True
        subsystem.build_meta_human(character=character, params=build_params)
        if not unreal.EditorLoadingAndSavingUtils.save_dirty_packages(
            save_map_packages=False,
            save_content_packages=True,
        ):
            raise RuntimeError(f"Failed to save assembled packages for {spec['id']}")
    finally:
        if subsystem.is_object_added_for_editing(character):
            subsystem.remove_object_to_edit(character)


def create_or_load_catalog(asset_tools):
    catalog = unreal.load_asset(CATALOG_PATH)
    if catalog is not None:
        return catalog

    factory = unreal.new_object(type=unreal.DataAssetFactory)
    factory.set_editor_property("data_asset_class", unreal.MetaHumanAppearanceCatalog)
    catalog = asset_tools.create_asset(
        asset_name=CATALOG_NAME,
        package_path=CATALOG_PACKAGE,
        asset_class=unreal.MetaHumanAppearanceCatalog,
        factory=factory,
    )
    if catalog is None:
        raise RuntimeError(f"Unable to create {CATALOG_PATH}")
    return catalog


def make_catalog_entry(spec):
    profile = unreal.CharacterBodyProfile()
    profile.height_cm = spec["height"]
    profile.shoulder_width_cm = spec["shoulder"]
    profile.body_depth_cm = spec["depth"]
    profile.mass_kg = spec["mass"]
    profile.arm_span_ratio = 1.0

    entry = unreal.MetaHumanBodyVariant()
    entry.variant_id = spec["id"]
    entry.display_name = spec["label"]
    entry.description = (
        f"MetaHuman Body Params fit: {spec['height']:.0f} cm height, "
        f"{spec['shoulder']:.0f} cm across shoulder. Exact gameplay depth and mass "
        "remain simulation values."
    )
    entry.authored_measurements = profile
    entry.meta_human_character_id = spec["asset_name"]
    entry.body_params_preset_id = spec["id"]

    generated_class_path = (
        f"{ASSEMBLY_PACKAGE}/{spec['asset_name']}/BP_{spec['asset_name']}."
        f"BP_{spec['asset_name']}_C"
    )
    actor_class = unreal.load_class(None, generated_class_path)
    if actor_class is not None:
        entry.assembled_actor_class = actor_class
    return entry


def main():
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    subsystem = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
    specs = list(variant_specs())

    for index, spec in enumerate(specs, start=1):
        unreal.log_warning(f"GGP_METAHUMAN_BODY {index}/{len(specs)}: {spec['id']}")
        _, character, created = create_or_load_character(asset_tools, spec)
        if created or REAUTHOR:
            apply_body_constraints(subsystem, character, spec)
        assemble_character(subsystem, character, spec)

    catalog = create_or_load_catalog(asset_tools)
    catalog.set_editor_property("body_variants", [make_catalog_entry(spec) for spec in specs])
    unreal.EditorAssetLibrary.save_loaded_asset(catalog, only_if_is_dirty=False)
    unreal.log_warning(f"GGP_METAHUMAN_CATALOG_COMPLETE={CATALOG_PATH};variants={len(specs)};assembled={ASSEMBLE}")


if __name__ == "__main__":
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()
