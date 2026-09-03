"""Create interactive ship fixture Blueprints and place a validation set in showcase maps."""

import unreal


BP_PATH = "/Game/Assets/Ships/Production/Blueprints"
MESH_PATH = "/Game/Assets/Ships/Production/Meshes"
MAT_PATH = "/Game/Assets/Ships/Production/Materials"
MAP_PATH = "/Game/Assets/Maps/ShipProduction"


def asset(path):
    result = unreal.load_asset(path)
    if not result:
        raise RuntimeError("Missing required asset: " + path)
    return result


def create_blueprint(name, parent_class, defaults):
    path = f"{BP_PATH}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        blueprint = asset(path)
    else:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", parent_class)
        blueprint = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, BP_PATH, unreal.Blueprint, factory)
        if not blueprint:
            raise RuntimeError("Failed to create Blueprint: " + path)
    cdo = unreal.get_default_object(blueprint.generated_class())
    for property_name, value in defaults.items():
        cdo.set_editor_property(property_name, value)
    unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
    return blueprint


def build_blueprints():
    hull = asset(MAT_PATH + "/M_Ship_Hull_OffWhite")
    dark = asset(MAT_PATH + "/M_Ship_Structure_Gunmetal")
    glow = asset(MAT_PATH + "/M_Ship_Light_Cold")
    utility = asset(MAT_PATH + "/M_Ship_Accent_Utility")
    military = asset(MAT_PATH + "/M_Ship_Accent_Military")
    corrupted = unreal.load_asset("/Game/Assets/Materials/M_Bloom_AmethystCorruption") or utility

    fixture_defaults = {
        "normal_material": dark,
        "active_material": glow,
        "corrupted_material": corrupted,
    }
    types = unreal.ShipFixtureType
    fixtures = {
        "BP_Ship_Terminal": ("SM_Prop_WallTerminal", types.TERMINAL, True),
        "BP_Ship_EmergencyLight": ("SM_Prop_LightFixture", types.EMERGENCY_LIGHT, True),
        "BP_Ship_VentControl": ("SM_Prop_PowerJunction", types.VENT_CONTROL, True),
        "BP_Ship_PurgeStation": ("SM_Prop_Scrubber", types.PURGE_STATION, False),
        "BP_Ship_Machinery": ("SM_Prop_PowerJunction", types.MACHINERY, True),
    }
    blueprints = {}
    for name, (mesh_name, fixture_type, toggles) in fixtures.items():
        defaults = dict(fixture_defaults)
        defaults.update({
            "fixture_mesh_asset": asset(f"{MESH_PATH}/{mesh_name}"),
            "fixture_type": fixture_type,
            "toggle_on_interact": toggles,
            "system_name": name.removeprefix("BP_Ship_").replace("_", " "),
        })
        blueprints[name] = create_blueprint(name, unreal.ShipInteractiveFixture, defaults)

    blueprints["BP_Ship_ProductionBulkhead"] = create_blueprint(
        "BP_Ship_ProductionBulkhead",
        unreal.ProductionBulkheadDoor,
        {
            "frame_mesh_asset": asset(MESH_PATH + "/SM_Kit_BulkheadDoor"),
            "panel_mesh_asset": asset(MESH_PATH + "/SM_Kit_Wall_4m"),
            "door_material": hull,
            "system_name": "Production Pressure Bulkhead",
            "cycle_duration": 1.25,
        },
    )
    unreal.EditorAssetLibrary.save_directory(BP_PATH)
    return blueprints


def place_validation_set(map_name, blueprints, width, length, height):
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level.load_level(f"{MAP_PATH}/{map_name}"):
        raise RuntimeError("Failed to load showcase level: " + map_name)
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    # Idempotent: preserve hand edits but do not duplicate this generated validation set.
    if any(actor.get_actor_label().startswith("InteractiveValidation_")
           for actor in actor_subsystem.get_all_level_actors()):
        unreal.log_warning("Interactive validation set already present: " + map_name)
        return

    specs = (
        ("BP_Ship_Terminal", (-length * 0.22, -width * 0.5 + 90, 20), (0, 0, 0)),
        ("BP_Ship_VentControl", (0, -width * 0.5 + 90, 20), (0, 0, 0)),
        ("BP_Ship_PurgeStation", (length * 0.22, -width * 0.5 + 110, 20), (0, 0, 0)),
        ("BP_Ship_Machinery", (-length * 0.18, width * 0.5 - 110, 20), (0, 180, 0)),
        ("BP_Ship_EmergencyLight", (0, 0, height - 55), (0, 0, 0)),
        ("BP_Ship_ProductionBulkhead", (length * 0.12, 0, 0), (0, 90, 0)),
    )
    for index, (bp_name, location, rotation) in enumerate(specs):
        bp = blueprints[bp_name]
        actor = actor_subsystem.spawn_actor_from_class(
            bp.generated_class(), unreal.Vector(*location), unreal.Rotator(rotation[1], rotation[2], rotation[0]))
        if not actor:
            raise RuntimeError(f"Failed to place {bp_name} in {map_name}")
        actor.set_actor_label(f"InteractiveValidation_{index:02d}_{bp_name}")
    level.save_current_level()


def main():
    unreal.log("Building interactive ship Blueprint assets...")
    blueprints = build_blueprints()
    place_validation_set("L_Small_Companionway_Showcase", blueprints, 1200, 5200, 430)
    place_validation_set("L_Medium_ExpressSpine_Showcase", blueprints, 3200, 7200, 760)
    place_validation_set("L_Large_CarrierConcourse_Showcase", blueprints, 4800, 9200, 1200)
    unreal.EditorAssetLibrary.save_directory(BP_PATH)
    unreal.log("Interactive ship pass complete: 6 Blueprints placed across 3 showcase maps.")


main()
