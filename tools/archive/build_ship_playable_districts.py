"""Turn ship showcase maps into playable district vertical slices."""

import unreal


ROOT = "/Game/Assets/Ships/Production"
BP_PATH = ROOT + "/Blueprints/Gameplay"
BUDGET_PATH = ROOT + "/Data/Performance"
MESH_PATH = ROOT + "/Meshes"
MAT_PATH = ROOT + "/Materials"
MAP_PATH = "/Game/Assets/Maps/ShipProduction"


def load(path):
    value = unreal.load_asset(path)
    if not value:
        raise RuntimeError("Missing asset: " + path)
    return value


def create_blueprint(name, parent_class, defaults):
    path = f"{BP_PATH}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        blueprint = load(path)
    else:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", parent_class)
        blueprint = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, BP_PATH, unreal.Blueprint, factory)
    cdo = unreal.get_default_object(blueprint.generated_class())
    for prop, value in defaults.items():
        cdo.set_editor_property(prop, value)
    unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
    return blueprint


def create_budget(name, values):
    path = f"{BUDGET_PATH}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        data = load(path)
    else:
        factory = unreal.DataAssetFactory()
        factory.set_editor_property("data_asset_class", unreal.ShipDistrictBudgetData)
        data = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, BUDGET_PATH, unreal.ShipDistrictBudgetData, factory)
    for prop, value in values.items():
        data.set_editor_property(prop, value)
    unreal.EditorAssetLibrary.save_loaded_asset(data)
    return data


def build_assets():
    budgets = {
        "small": create_budget("DA_Budget_SmallDistrict", {
            "max_visible_triangles": 3_000_000,
            "max_draw_calls": 1400,
            "max_shadowed_movable_lights": 6,
            "max_active_audio_sources": 24,
            "max_active_enemies": 8,
            "streaming_cell_size_meters": 48.0,
        }),
        "medium": create_budget("DA_Budget_MediumDistrict", {
            "max_visible_triangles": 5_500_000,
            "max_draw_calls": 2200,
            "max_shadowed_movable_lights": 10,
            "max_active_audio_sources": 40,
            "max_active_enemies": 16,
            "streaming_cell_size_meters": 64.0,
        }),
        "large": create_budget("DA_Budget_LargeDistrict", {
            "max_visible_triangles": 8_000_000,
            "max_draw_calls": 3000,
            "max_shadowed_movable_lights": 14,
            "max_active_audio_sources": 56,
            "max_active_enemies": 24,
            "streaming_cell_size_meters": 96.0,
        }),
    }

    scales = unreal.ShipDistrictScale
    directors = {
        "small": create_blueprint("BP_DistrictDirector_Small", unreal.ShipDistrictGameplayDirector, {
            "district_scale": scales.SMALL,
            "district_extent": unreal.Vector(2600, 600, 215),
            "primary_objective_id": "Small_RestoreCompanionway",
            "encounter_count": 2,
            "oxygen_pickup_count": 2,
            "health_pickup_count": 1,
            "layout_seed": 4103,
            "spawn_demo_systems": True,
            "demo_jump_countdown_seconds": 20.0,
            "demo_jumps_to_destination": 2,
            "performance_budget": budgets["small"],
        }),
        "medium": create_blueprint("BP_DistrictDirector_Medium", unreal.ShipDistrictGameplayDirector, {
            "district_scale": scales.MEDIUM,
            "district_extent": unreal.Vector(3600, 1600, 380),
            "primary_objective_id": "Medium_PurgeExpressSpine",
            "encounter_count": 4,
            "oxygen_pickup_count": 3,
            "health_pickup_count": 2,
            "layout_seed": 6209,
            "performance_budget": budgets["medium"],
        }),
        "large": create_blueprint("BP_DistrictDirector_Large", unreal.ShipDistrictGameplayDirector, {
            "district_scale": scales.LARGE,
            "district_extent": unreal.Vector(4600, 2400, 600),
            "primary_objective_id": "Large_SecureCarrierConcourse",
            "encounter_count": 6,
            "oxygen_pickup_count": 4,
            "health_pickup_count": 3,
            "layout_seed": 8513,
            "performance_budget": budgets["large"],
        }),
    }

    fixture_defaults = {
        "fixture_mesh_asset": load(MESH_PATH + "/SM_Prop_WallTerminal"),
        "normal_material": load(MAT_PATH + "/M_Ship_Structure_Gunmetal"),
        "active_material": load(MAT_PATH + "/M_Ship_Light_Cold"),
        "corrupted_material": load(MAT_PATH + "/M_Bloom_AdvancedCalcified"),
    }
    terminal = create_blueprint("BP_Ship_ObjectiveConsole", unreal.ShipObjectiveConsole, fixture_defaults)
    transit = create_blueprint("BP_Ship_DistrictTransitConsole", unreal.ShipDistrictTravelConsole, fixture_defaults)
    checkpoint = create_blueprint("BP_Ship_Checkpoint", unreal.ShipCheckpointVolume, {})
    unreal.EditorAssetLibrary.save_directory(BP_PATH)
    unreal.EditorAssetLibrary.save_directory(BUDGET_PATH)
    return directors, terminal, checkpoint, transit


def configure_objective_console(actor, objective_id):
    actor.set_editor_property("objective_id", objective_id)
    actor.set_editor_property("system_name", "District Objective Console")


def place_map_gameplay(map_name, director_bp, terminal_bp, checkpoint_bp,
                       objective_id, extent, section_type):
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    level.load_level(f"{MAP_PATH}/{map_name}")
    if any(actor.get_actor_label() == "Gameplay_DistrictDirector" for actor in actors.get_all_level_actors()):
        unreal.log_warning("Playable district already configured: " + map_name)
        return

    director = actors.spawn_actor_from_class(director_bp.generated_class(), unreal.Vector(0, 0, 0), unreal.Rotator())
    director.set_actor_label("Gameplay_DistrictDirector")

    section = actors.spawn_actor_from_class(unreal.ShipSection, unreal.Vector(0, 0, extent[2]), unreal.Rotator())
    section.set_actor_label("Gameplay_PressureSection")
    section.set_editor_property("section_id", 1)
    section.set_editor_property("section_type", section_type)
    section.get_editor_property("section_bounds").set_box_extent(unreal.Vector(*extent))

    console = actors.spawn_actor_from_class(
        terminal_bp.generated_class(), unreal.Vector(extent[0] * 0.7, -extent[1] + 125, 25), unreal.Rotator())
    console.set_actor_label("Gameplay_ObjectiveConsole")
    configure_objective_console(console, objective_id)

    checkpoint = actors.spawn_actor_from_class(
        checkpoint_bp.generated_class(), unreal.Vector(-extent[0] * 0.25, 0, 220), unreal.Rotator())
    checkpoint.set_actor_label("Gameplay_Checkpoint")
    checkpoint.set_editor_property("checkpoint_id", objective_id + "_Checkpoint")

    nav = actors.spawn_actor_from_class(unreal.NavMeshBoundsVolume, unreal.Vector(0, 0, extent[2]), unreal.Rotator())
    nav.set_actor_label("Gameplay_NavMeshBounds")
    nav.set_actor_scale3d(unreal.Vector(max(1, extent[0] / 200), max(1, extent[1] / 200), max(1, extent[2] / 200)))

    level.save_current_level()


def place_transit_console(map_name, transit_bp, destination_map, destination_name, location):
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    level.load_level(f"{MAP_PATH}/{map_name}")
    existing = next((actor for actor in actors.get_all_level_actors()
                     if actor.get_actor_label() == "Gameplay_DistrictTransitConsole"), None)
    if existing:
        transit = existing
    else:
        transit = actors.spawn_actor_from_class(
            transit_bp.generated_class(), unreal.Vector(*location), unreal.Rotator(0, 180, 0))
        transit.set_actor_label("Gameplay_DistrictTransitConsole")
    transit.set_editor_property("destination_map_name", destination_map)
    transit.set_editor_property("destination_display_name", destination_name)
    transit.set_editor_property("system_name", "Ship District Transit Console")
    level.save_current_level()


def main():
    unreal.log("Building playable ship district pass...")
    directors, terminal, checkpoint, transit = build_assets()
    section_types = unreal.ShipSectionType
    place_map_gameplay("L_Small_Companionway_Showcase", directors["small"], terminal, checkpoint,
                       "Small_RestoreCompanionway", (2600, 600, 215), section_types.CORRIDOR)
    place_map_gameplay("L_Medium_ExpressSpine_Showcase", directors["medium"], terminal, checkpoint,
                       "Medium_PurgeExpressSpine", (3600, 1600, 380), section_types.CORRIDOR)
    place_map_gameplay("L_Large_CarrierConcourse_Showcase", directors["large"], terminal, checkpoint,
                       "Large_SecureCarrierConcourse", (4600, 2400, 600), section_types.CARGO_BAY)
    place_transit_console("L_Small_Companionway_Showcase", transit,
                          "L_Medium_ExpressSpine_Showcase", "Medium Military Corvette", (-1800, 450, 25))
    place_transit_console("L_Medium_ExpressSpine_Showcase", transit,
                          "L_Large_CarrierConcourse_Showcase", "Large Expedition Carrier", (-2500, 1100, 25))
    place_transit_console("L_Large_CarrierConcourse_Showcase", transit,
                          "L_Small_Companionway_Showcase", "Small Utility Escort", (-3200, 1800, 25))
    unreal.log("Playable district pass complete: objectives, pressure, nav, encounters, loot, checkpoints, budgets, transit.")


if __name__ == "__main__":
    main()
