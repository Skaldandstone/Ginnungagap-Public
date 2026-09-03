"""Log the installed MetaHuman parametric-body constraint names and ranges."""

import json
import unreal


PACKAGE_PATH = "/Game/Characters/MetaHumans/Generated"
ASSET_NAME = "MHC_ConstraintProbe"
ASSET_PATH = f"{PACKAGE_PATH}/{ASSET_NAME}"


def main():
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    if unreal.EditorAssetLibrary.does_asset_exist(ASSET_PATH):
        unreal.EditorAssetLibrary.delete_asset(ASSET_PATH)

    character = asset_tools.create_asset(
        asset_name=ASSET_NAME,
        package_path=PACKAGE_PATH,
        asset_class=unreal.MetaHumanCharacter,
        factory=unreal.new_object(type=unreal.MetaHumanCharacterFactoryNew),
    )
    if character is None:
        raise RuntimeError("Unable to create temporary MetaHuman Character")

    subsystem = unreal.get_editor_subsystem(unreal.MetaHumanCharacterEditorSubsystem)
    if not subsystem.try_add_object_to_edit(character):
        raise RuntimeError("Unable to open temporary MetaHuman Character for editing")

    try:
        rows = []
        for constraint in subsystem.get_body_constraints(
            character=character,
            scale_measurement_ranges_with_height=False,
        ):
            rows.append(
                {
                    "name": str(constraint.name),
                    "active": bool(constraint.is_active),
                    "target": float(constraint.target_measurement),
                    "min": float(constraint.min_measurement),
                    "max": float(constraint.max_measurement),
                }
            )
        unreal.log_warning("GGP_METAHUMAN_CONSTRAINTS=" + json.dumps(rows, separators=(",", ":")))
    finally:
        if subsystem.is_object_added_for_editing(character):
            subsystem.remove_object_to_edit(character)
        unreal.EditorAssetLibrary.delete_asset(ASSET_PATH)


if __name__ == "__main__":
    try:
        main()
    finally:
        unreal.SystemLibrary.quit_editor()

