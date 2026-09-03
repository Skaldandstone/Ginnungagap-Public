"""Fail-fast validation for the three generated playable ship districts."""

import unreal


MAP_ROOT = "/Game/Assets/Maps/ShipProduction"
MAPS = (
    "L_Small_Companionway_Showcase",
    "L_Medium_ExpressSpine_Showcase",
    "L_Large_CarrierConcourse_Showcase",
)
EXPECTED_DESTINATIONS = {
    "L_Small_Companionway_Showcase": "L_Medium_ExpressSpine_Showcase",
    "L_Medium_ExpressSpine_Showcase": "L_Large_CarrierConcourse_Showcase",
    "L_Large_CarrierConcourse_Showcase": "L_Small_Companionway_Showcase",
}
EXPECTED_FITTED_ROOMS = {
    "L_Small_Companionway_Showcase": 4,
    "L_Medium_ExpressSpine_Showcase": 6,
    "L_Large_CarrierConcourse_Showcase": 8,
}
FITTED_ACTOR_BUDGETS = {
    "L_Small_Companionway_Showcase": 80,
    "L_Medium_ExpressSpine_Showcase": 140,
    "L_Large_CarrierConcourse_Showcase": 220,
}
REQUIRED_LABELS = (
    "PlayerStart",
    "Gameplay_DistrictDirector",
    "Gameplay_PressureSection",
    "Gameplay_ObjectiveConsole",
    "Gameplay_Checkpoint",
    "Gameplay_DistrictTransitConsole",
    "Gameplay_NavMeshBounds",
    "ShipEnvironmentController",
)


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    failures = []

    for map_name in MAPS:
        if not levels.load_level(f"{MAP_ROOT}/{map_name}"):
            failures.append(f"{map_name}: failed to load")
            continue

        level_actors = actors.get_all_level_actors()
        by_label = {actor.get_actor_label(): actor for actor in level_actors}
        missing = [label for label in REQUIRED_LABELS if label not in by_label]
        if missing:
            failures.append(f"{map_name}: missing {', '.join(missing)}")

        interactive_count = sum(
            actor.get_actor_label().startswith("InteractiveValidation_") for actor in level_actors)
        if interactive_count < 6:
            failures.append(f"{map_name}: only {interactive_count}/6 interactive fixtures")

        environment = by_label.get("ShipEnvironmentController")
        if environment:
            if not environment.get_editor_property("follow_live_bloom_state"):
                failures.append(f"{map_name}: environment does not follow live Bloom")
            if not environment.get_editor_property("follow_ship_damage_state"):
                failures.append(f"{map_name}: environment does not follow section damage")

        aggregate_section = by_label.get("Gameplay_PressureSection")
        if aggregate_section and aggregate_section.get_editor_property("register_with_navigation"):
            failures.append(f"{map_name}: legacy aggregate section still participates in navigation")

        fitted_rooms = [actor for actor in level_actors
                        if actor.get_actor_label().startswith("ModularFit_Room_")]
        expected_rooms = EXPECTED_FITTED_ROOMS[map_name]
        if len(fitted_rooms) != expected_rooms:
            failures.append(f"{map_name}: fitted room count {len(fitted_rooms)} != {expected_rooms}")
        room_codes = [str(room.get_editor_property("room_code")) for room in fitted_rooms]
        if len(room_codes) != len(set(room_codes)):
            failures.append(f"{map_name}: fitted room codes are not unique")
        expected_edges = max(0, expected_rooms - 1)
        fitted_doors = [actor for actor in level_actors
                        if actor.get_actor_label().startswith("ModularFit_Bulkhead_")]
        if len(fitted_doors) != expected_edges:
            failures.append(f"{map_name}: fitted bulkhead count {len(fitted_doors)} != {expected_edges}")
        reciprocal_links = sum(len(room.get_editor_property("connections")) for room in fitted_rooms)
        if reciprocal_links != expected_edges * 2:
            failures.append(
                f"{map_name}: fitted reciprocal link count {reciprocal_links} != {expected_edges * 2}")

        fitted_actors = [actor for actor in level_actors
                         if actor.get_actor_label().startswith("ModularFit_")]
        if len(fitted_actors) > FITTED_ACTOR_BUDGETS[map_name]:
            failures.append(
                f"{map_name}: {len(fitted_actors)} fitted actors exceed budget "
                f"{FITTED_ACTOR_BUDGETS[map_name]}")
        for room in fitted_rooms:
            code = str(room.get_editor_property("room_code"))
            profile = room.get_editor_property("gameplay_profile")
            power_priority = profile.get_editor_property("power_priority")
            power_draw = profile.get_editor_property("nominal_power_draw")
            occupancy = profile.get_editor_property("safe_occupancy")
            hazard_tier = profile.get_editor_property("hazard_tier")
            loot_tier = profile.get_editor_property("loot_tier")
            if not 0 <= power_priority <= 10 or power_draw < 0.0 or occupancy < 0:
                failures.append(f"{map_name}: room {code} has an invalid power/occupancy profile")
            if not 0 <= hazard_tier <= 5 or not 0 <= loot_tier <= 5:
                failures.append(f"{map_name}: room {code} has an invalid hazard/loot profile")
            for binding in ("system_anchor", "loot_anchor", "maintenance_anchor",
                            "identity_light", "code_sign", "name_sign"):
                if not room.get_editor_property(binding):
                    failures.append(f"{map_name}: room {code} has no {binding} binding")
            required_room_labels = (
                f"ModularFit_Dressing_{code}_Primary",
                f"ModularFit_Dressing_{code}_Secondary",
                f"ModularFit_Dressing_{code}_Terminal",
                f"ModularFit_Sign_{code}_Code",
                f"ModularFit_Sign_{code}_Name",
                f"ModularFit_Light_{code}",
                f"ModularFit_Anchor_{code}_System",
                f"ModularFit_Anchor_{code}_Loot",
                f"ModularFit_Anchor_{code}_Maintenance",
                f"ModularFit_Hazard_{code}_Port",
                f"ModularFit_Hazard_{code}_Starboard",
            )
            missing_room_labels = [label for label in required_room_labels if label not in by_label]
            if missing_room_labels:
                failures.append(
                    f"{map_name}: room {code} missing dressing: {', '.join(missing_room_labels)}")

        transit = by_label.get("Gameplay_DistrictTransitConsole")
        if transit:
            destination = str(transit.get_editor_property("destination_map_name"))
            if destination != EXPECTED_DESTINATIONS[map_name]:
                failures.append(
                    f"{map_name}: transit destination {destination} != {EXPECTED_DESTINATIONS[map_name]}")

        director = by_label.get("Gameplay_DistrictDirector")
        if map_name == "L_Small_Companionway_Showcase" and director:
            if not director.get_editor_property("spawn_demo_systems"):
                failures.append(f"{map_name}: canonical demo systems are disabled")
            if director.get_editor_property("demo_jump_countdown_seconds") < 10.0:
                failures.append(f"{map_name}: jump countdown is too short for the companionway")
            if director.get_editor_property("demo_jumps_to_destination") > 3:
                failures.append(f"{map_name}: demo requires too many jumps to reach an outcome")

        unreal.log(
            f"Validated {map_name}: {len(level_actors)} actors, {interactive_count} fixtures, "
            f"{len(fitted_rooms)} fitted rooms, transit linked")

    if failures:
        raise RuntimeError("Playable ship validation failed:\n" + "\n".join(failures))
    unreal.log("Playable ship validation complete: all 3 maps passed.")


if __name__ == "__main__":
    main()
