"""Headless structural audit for L_QuickDemo_FourDeck."""

import json
from collections import Counter
from pathlib import Path

import unreal


MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
PREFIX = "QuickDemo4D_"
REPORT = Path(unreal.SystemLibrary.get_project_saved_directory()) / "Reports" / "QuickDemoFourDeckValidation.json"
CONFIG = Path(unreal.SystemLibrary.get_project_directory()) / "Config" / "Ships" / "QuickDemoFourDeck.json"


def count(labels, stem):
    return sum(label.startswith(PREFIX + stem) for label in labels)


def room_type_slug(name):
    return "".join(character.lower() if character.isalnum() else "_" for character in name).strip("_")


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(MAP_PATH):
        raise RuntimeError(f"Could not load {MAP_PATH}")

    actors = [actor for actor in actors_api.get_all_level_actors() if actor.get_actor_label().startswith(PREFIX)]
    labels = [actor.get_actor_label() for actor in actors]
    config = json.loads(CONFIG.read_text(encoding="utf-8"))
    checks = {
        "rooms": (count(labels, "Room_QD-"), 96),
        "room_lights": (count(labels, "RoomLight_QD-"), 96),
        "primary_corridors": (count(labels, "PrimaryCorridor_D"), 4),
        "corridor_lights": (count(labels, "CorridorLight_D"), 24),
        "room_threshold_doors": (count(labels, "Door_QD-"), 96),
        "room_block_activities": (count(labels, "BlockActivity_QD-"), 25),
        "corridor_blocks": (count(labels, "CorridorBlock_D"), 8),
        "corridor_block_activities": (count(labels, "CorridorBlockActivity_D"), 8),
        "airlocks": (count(labels, "Airlock_QD-"), 8),
        "airlock_activities": (count(labels, "AirlockActivity_QD-"), 8),
        "escape_pods": (count(labels, "EscapePod_QD-"), 6),
        "cryo_pods": (count(labels, "CryoPod_"), 4),
        "seeded_equipment": (count(labels, "Equipment_QD-"), 14),
        "mission_directors": (count(labels, "MissionDirector"), 1),
        "objective_beacons": (count(labels, "ObjectiveBeacon_"), 5),
        "suit_stations": (count(labels, "SuitStation_"), 4),
        "workshop_objective_triggers": (count(labels, "WorkshopObjectiveTrigger"), 1),
        "cic_mission_consoles": (count(labels, "CICMissionConsole"), 1),
        "hatch_ramps": (count(labels, "HatchRamp_"), 6),
        "zero_g_pull_holds": (count(labels, "PullHold_"), 72),
        "power_restore_stations": (count(labels, "PowerRestoreStation"), 1),
        "vacuum_hazards": (count(labels, "VacuumHazard_"), 1),
        "breach_patch_activities": (count(labels, "BreachPatchActivity"), 1),
        "player_starts": (count(labels, "PlayerStart_Cryo"), 1),
        "concept_room_floor_insets": (count(labels, "ConceptRoomFloorInset_"), 96),
        "concept_room_floor_stripes": (count(labels, "ConceptRoomFloorStripe_"), 192),
        "concept_wall_panels": (count(labels, "ConceptWallPanel_"), 288),
        "concept_kickplates": (count(labels, "ConceptKickplate_"), 96),
        "concept_utility_rails": (count(labels, "ConceptUtilityRail_"), 96),
        "concept_wear_patches": (count(labels, "ConceptWearPatch_"), 96),
        "concept_corner_ribs": (count(labels, "ConceptCornerRib_"), 192),
        "concept_ceiling_beams": (count(labels, "ConceptCeilingBeam_"), 96),
        "concept_ceiling_pipes": (count(labels, "ConceptCeilingPipe_"), 192),
        "concept_utility_props": (count(labels, "ConceptUtilityProp_"), 96),
        "concept_light_fixtures": (count(labels, "ConceptLightFixture_"), 96),
        "concept_corridor_floor_insets": (count(labels, "ConceptCorridorFloorInset_"), 4),
        "concept_corridor_floor_stripes": (count(labels, "ConceptCorridorFloorStripe_"), 8),
        "concept_corridor_ribs": (count(labels, "ConceptCorridorRib_"), 144),
        "concept_corridor_pipes": (count(labels, "ConceptCorridorPipe_"), 8),
        "concept_special_props": (count(labels, "ConceptSpecialProp_"), 14),
    }

    deck_rooms = Counter()
    for label in labels:
        if label.startswith(PREFIX + "Room_QD-"):
            deck_rooms[label.split("-")[1]] += 1
    deck_check = dict(sorted(deck_rooms.items()))

    utility_light_intensities = {}
    for actor in actors:
        label = actor.get_actor_label()
        component = actor.get_component_by_class(unreal.PointLightComponent)
        if component:
            utility_light_intensities[label] = component.get_editor_property("intensity") if component else None
    lit_at_start = sorted(label for label, intensity in utility_light_intensities.items() if intensity and intensity > 0.0)

    cryo_pod_yaws = {
        actor.get_actor_label(): round(actor.get_actor_rotation().yaw, 2)
        for actor in actors if actor.get_actor_label().startswith(PREFIX + "CryoPod_")
    }

    gameplay_classes = {
        actor.get_actor_label(): actor.get_class().get_name()
        for actor in actors
        if actor.get_actor_label() in {
            PREFIX + "MissionDirector",
            PREFIX + "PowerRestoreStation",
            PREFIX + "BreachPatchActivity",
            PREFIX + "CICMissionConsole",
        } or actor.get_actor_label().startswith(PREFIX + "SuitStation_")
    }

    failures = [f"{name}: expected {expected}, found {actual}" for name, (actual, expected) in checks.items() if actual != expected]
    if deck_check != {"01": 24, "02": 24, "03": 24, "04": 24}:
        failures.append(f"rooms per deck: {deck_check}")
    if lit_at_start != [PREFIX + "RoomLight_QD-03-01"]:
        failures.append(f"startup utility lights: {lit_at_start}")
    if len(cryo_pod_yaws) != 4 or any(abs(abs(yaw) - 180.0) > 0.1 for yaw in cryo_pod_yaws.values()):
        failures.append(f"cryo pods must face the outer wall at yaw 180: {cryo_pod_yaws}")
    expected_gameplay_classes = {
        PREFIX + "MissionDirector": "QuickDemoMissionDirector",
        PREFIX + "PowerRestoreStation": "QuickDemoPowerStation",
        PREFIX + "BreachPatchActivity": "QuickDemoBreachStation",
        PREFIX + "CICMissionConsole": "QuickDemoCICConsole",
        **{PREFIX + f"SuitStation_{index:02d}": "QuickDemoSuitStation" for index in range(1, 5)},
    }
    if gameplay_classes != expected_gameplay_classes:
        failures.append(f"quick-demo gameplay classes: {gameplay_classes}")

    required_room_types = set(config["mission_room_types"].values())
    required_room_types.update(
        entry["name"] for pool in config["deck_room_type_pools"].values() for entry in pool)
    room_type_counts = Counter()
    for actor in actors:
        if not actor.get_actor_label().startswith(PREFIX + "Room_QD-"):
            continue
        for tag in actor.get_editor_property("tags"):
            tag_text = str(tag)
            if tag_text.startswith("RoomType_"):
                room_type_counts[tag_text.removeprefix("RoomType_")] += 1
    missing_room_types = sorted(
        name for name in required_room_types if room_type_counts[room_type_slug(name)] == 0)
    if missing_room_types:
        failures.append("missing required Wayfarer sector room types: " + ", ".join(missing_room_types))

    result = {
        "map": MAP_PATH,
        "status": "passed" if not failures else "failed",
        "generated_actor_count": len(actors),
        "checks": {name: {"actual": actual, "expected": expected} for name, (actual, expected) in checks.items()},
        "rooms_per_deck": deck_check,
        "startup_lit_utility_lights": lit_at_start,
        "cryo_pod_yaws": cryo_pod_yaws,
        "gameplay_classes": gameplay_classes,
        "required_room_types": sorted(required_room_types),
        "room_type_counts": dict(sorted(room_type_counts.items())),
        "missing_room_types": missing_room_types,
        "pull_hold_labels": sorted(label for label in labels if label.startswith(PREFIX + "PullHold_")),
        "failures": failures,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    if failures:
        raise RuntimeError("Quick-demo validation failed: " + "; ".join(failures))
    unreal.log(f"Quick-demo map validation passed: {len(actors)} generated actors, 96 rooms")


if __name__ == "__main__":
    main()
