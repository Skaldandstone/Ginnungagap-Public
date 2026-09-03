"""Add native room gameplay to the already-built Small Escort operations district.

This incremental path is intentionally independent of the district shell generator. It lets the
authored map receive interactions while other shared native layout changes are awaiting a clean
editor build, and it remains idempotent by replacing only EscortOps gameplay actors.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
MAP = "/Game/Assets/Maps/ShipProduction/L_SmallEscort_OperationsDeck"
PREFIX = "EscortOps_"
REPORT = PROJECT / "Saved/Reports/SmallEscortOperationsDistrict.json"
ROOM_HEIGHT = 430.0

ROOM_ACTIVITY_CLASSES = {
    "OPS-08-01": "MechanicalOverrideStation",
    "BRG-08-01": "SensorCalibrationStation",
    "CIC-08-01": "TurretServiceStation",
    "NAV-08-01": "SensorCalibrationStation",
    "COM-08-01": "BreakerReroutingStation",
    "SNS-08-01": "BloomPurgingStation",
    "ARM-08-01": "TurretServiceStation",
    "CMP-08-01": "MechanicalOverrideStation",
    "CRW-07-01": "SuitPatchingStation",
    "CCM-07-01": "BreakerReroutingStation",
    "GAL-07-01": "FireSuppressionStation",
    "REC-07-01": "ComponentReplacementStation",
    "MED-07-01": "MedicalStabilizationStation",
    "SUR-07-01": "MedicalStabilizationStation",
    "QRT-07-01": "DecontaminationStation",
    "CRY-07-01": "SampleContainmentStation",
    "DCR-06-01": "HullPatchingStation",
    "FAB-06-01": "FabricationStation",
    "LIF-06-01": "OxygenScrubberServiceStation",
    "WTR-06-01": "PipeSealingStation",
    "CGO-06-01": "DroneRepairStation",
    "EVA-06-01": "AirlockRepressurizationStation",
    "ENG-06-01": "CoolantBalancingStation",
    "AUX-06-01": "ReactorStartupStation",
}

ROOM_SURVIVAL_PICKUPS = {
    "MED-07-01": ("HEALTH", 35.0),
    "SUR-07-01": ("HEALTH", 25.0),
    "LIF-06-01": ("OXYGEN", 30.0),
    "EVA-06-01": ("OXYGEN", 30.0),
}

ROOM_CHECKPOINTS = {
    "OPS-08-01": "EscortOps_Deck08_Entry",
    "CCM-07-01": "EscortOps_Deck07_CrewCommons",
    "DCR-06-01": "EscortOps_Deck06_DamageControl",
}


def enum_value(enum_type, name):
    value = getattr(enum_type, name, None)
    if value is None:
        raise RuntimeError(f"Missing reflected enum {enum_type.__name__}.{name}")
    return value


def load_required(path):
    value = unreal.load_asset(path)
    if not value:
        raise RuntimeError("Missing required gameplay asset: " + path)
    return value


def socket_names(room):
    return {str(value).split(".")[-1].upper() for value in room.get_editor_property("enabled_sockets")}


def choose_gameplay_side(room):
    names = socket_names(room)
    if "PORT" in names and "STARBOARD" not in names:
        return 1.0, 0.0
    if "STARBOARD" in names and "PORT" not in names:
        return -1.0, 0.0
    if "PORT" in names and "STARBOARD" in names:
        return -1.0, 500.0
    return -1.0, 0.0


def spawn_activity(actors, room, room_code, class_name, terminal_mesh):
    station_class = getattr(unreal, class_name, None)
    if not station_class:
        raise RuntimeError(f"Missing native activity class unreal.{class_name}")
    center = room.get_actor_location()
    floor_z = center.z - ROOM_HEIGHT * 0.5
    side, station_dx = choose_gameplay_side(room)
    station = actors.spawn_actor_from_class(
        station_class,
        unreal.Vector(center.x + station_dx, center.y + side * 600.0, floor_z + 92.0),
        unreal.Rotator(pitch=0.0, yaw=0.0 if side < 0.0 else 180.0, roll=0.0),
    )
    if not station:
        raise RuntimeError(f"Could not spawn {class_name} in {room_code}")
    station.set_actor_label(f"{PREFIX}Activity_{room_code}_{class_name}")
    station.set_editor_property("target_actor", room)
    station.set_editor_property("cooldown_seconds", 6.0)
    station.set_editor_property(
        "tags", [unreal.Name("GameplayActivity"), unreal.Name("RoomInteraction"), unreal.Name(room_code)]
    )
    station.get_editor_property("mesh").set_static_mesh(terminal_mesh)
    station.set_actor_scale3d(unreal.Vector(0.82, 0.82, 0.82))
    station.configure_procedural_station(
        unreal.Name(f"{room_code}-ACT-00"),
        unreal.Name(room_code),
        6100 + int(round(center.z)),
        0,
        enum_value(unreal.ActivityStationMount, "WALL_PANEL"),
        enum_value(unreal.ActivityStationCondition, "SERVICEABLE"),
        enum_value(unreal.ActivityStationRarity, "SPECIALIZED"),
        0.9,
        -1,
    )
    room.set_editor_property("maintenance_anchor", station)
    return station, side


def spawn_pickup(actors, room, room_code, pickup_spec, side, pickup_meshes):
    pickup_type_name, amount = pickup_spec
    center = room.get_actor_location()
    floor_z = center.z - ROOM_HEIGHT * 0.5
    pickup = actors.spawn_actor_from_class(
        unreal.SurvivalPickup,
        unreal.Vector(center.x + 480.0, center.y - side * 500.0, floor_z + 48.0),
        unreal.Rotator(),
    )
    if not pickup:
        raise RuntimeError(f"Could not spawn survival pickup in {room_code}")
    pickup.set_actor_label(f"{PREFIX}Pickup_{room_code}_{pickup_type_name.title()}")
    pickup.set_editor_property("pickup_type", enum_value(unreal.PickupType, pickup_type_name))
    pickup.set_editor_property("amount", amount)
    pickup.set_editor_property(
        "tags", [unreal.Name("SurvivalSupply"), unreal.Name(pickup_type_name.title()), unreal.Name(room_code)]
    )
    pickup.get_editor_property("visual_mesh").set_static_mesh(pickup_meshes[pickup_type_name])
    pickup.set_actor_scale3d(unreal.Vector(0.32, 0.32, 0.32))
    room.set_editor_property("loot_anchor", pickup)
    return pickup


def spawn_checkpoint(actors, room, room_code, checkpoint_id):
    center = room.get_actor_location()
    floor_z = center.z - ROOM_HEIGHT * 0.5
    checkpoint = actors.spawn_actor_from_class(
        unreal.ShipCheckpointVolume,
        unreal.Vector(center.x, center.y, floor_z + 90.0),
        unreal.Rotator(),
    )
    if not checkpoint:
        raise RuntimeError(f"Could not spawn checkpoint in {room_code}")
    checkpoint.set_actor_label(f"{PREFIX}Checkpoint_{room_code}")
    checkpoint.set_editor_property("checkpoint_id", unreal.Name(checkpoint_id))
    checkpoint.set_editor_property("respawn_offset", unreal.Vector(260.0, 0.0, 0.0))
    checkpoint.set_editor_property(
        "tags", [unreal.Name("DeckCheckpoint"), unreal.Name("RespawnSafe"), unreal.Name(room_code)]
    )
    checkpoint.get_editor_property("trigger").set_box_extent(unreal.Vector(260.0, 260.0, 120.0))
    return checkpoint


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(MAP):
        raise RuntimeError("Could not load Small Escort operations district")

    old_prefixes = (
        PREFIX + "Activity_", PREFIX + "Pickup_", PREFIX + "GameplayDirector",
        PREFIX + "ObjectiveConsole_", PREFIX + "Checkpoint_",
    )
    previous = [
        actor for actor in actors.get_all_level_actors()
        if actor.get_actor_label().startswith(old_prefixes)
    ]
    if previous:
        actors.destroy_actors(previous)

    rooms = {
        str(actor.get_editor_property("room_code")): actor
        for actor in actors.get_all_level_actors()
        if actor.get_actor_label().startswith(PREFIX + "Room_")
    }
    if set(rooms) != set(ROOM_ACTIVITY_CLASSES):
        raise RuntimeError(f"Expected the 24-room operations map; found room codes {sorted(rooms)}")

    terminal_mesh = load_required("/Game/Assets/Ships/Production/Meshes/SM_Prop_WallTerminal")
    pickup_meshes = {
        "HEALTH": load_required("/Game/Ice_Station/Meshes/Crates/SM_crate_01"),
        "OXYGEN": load_required("/Game/Ice_Station/Meshes/Crates/SM_crate_04"),
    }
    objective_asset = load_required(
        "/Game/Assets/Ships/Production/Blueprints/Gameplay/BP_Ship_ObjectiveConsole"
    )

    for room_code, class_name in ROOM_ACTIVITY_CLASSES.items():
        station, side = spawn_activity(actors, rooms[room_code], room_code, class_name, terminal_mesh)
        if room_code in ROOM_SURVIVAL_PICKUPS:
            spawn_pickup(
                actors, rooms[room_code], room_code, ROOM_SURVIVAL_PICKUPS[room_code], side, pickup_meshes
            )

    for room_code, checkpoint_id in ROOM_CHECKPOINTS.items():
        spawn_checkpoint(actors, rooms[room_code], room_code, checkpoint_id)

    director = actors.spawn_actor_from_class(
        unreal.ShipDistrictGameplayDirector, unreal.Vector(0.0, 0.0, 735.0), unreal.Rotator()
    )
    director.set_actor_label(PREFIX + "GameplayDirector")
    director.set_editor_property("district_scale", enum_value(unreal.ShipDistrictScale, "SMALL"))
    director.set_editor_property("district_extent", unreal.Vector(3750.0, 1650.0, 735.0))
    director.set_editor_property("primary_objective_id", "EscortOps_RestoreOperations")
    director.set_editor_property("primary_objective_title", "Restore the escort operations district")
    director.set_editor_property("objective_reward", 350)
    director.set_editor_property("encounter_count", 0)
    director.set_editor_property("oxygen_pickup_count", 0)
    director.set_editor_property("health_pickup_count", 0)
    director.set_editor_property("spawn_gameplay_on_begin_play", False)
    director.set_editor_property("spawn_demo_systems", False)
    director.set_editor_property(
        "tags", [unreal.Name("GameplayDirector"), unreal.Name("SmallEscortOperations")]
    )

    dcr = rooms["DCR-06-01"]
    center = dcr.get_actor_location()
    objective = actors.spawn_actor_from_class(
        objective_asset.generated_class(),
        unreal.Vector(center.x, center.y + 600.0, center.z - ROOM_HEIGHT * 0.5 + 25.0),
        unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0),
    )
    objective.set_actor_label(PREFIX + "ObjectiveConsole_DCR-06-01")
    objective.set_editor_property("objective_id", "EscortOps_RestoreOperations")
    objective.set_editor_property("system_name", "Operations District Restoration Console")
    objective.set_editor_property(
        "tags", [unreal.Name("PrimaryObjective"), unreal.Name("RoomInteraction"), unreal.Name("DCR-06-01")]
    )
    dcr.set_editor_property("system_anchor", objective)

    if not levels.save_current_level():
        raise RuntimeError("Could not save Small Escort operations gameplay pass")
    unreal.EditorAssetLibrary.save_directory("/Game/Assets/Maps/ShipProduction")

    if REPORT.exists():
        data = json.loads(REPORT.read_text(encoding="utf-8"))
    else:
        data = {"map": MAP}
    generated = [
        actor for actor in actors.get_all_level_actors() if actor.get_actor_label().startswith(PREFIX)
    ]
    data.update({
        "interactive_activity_stations": len(ROOM_ACTIVITY_CLASSES),
        "survival_supply_pickups": len(ROOM_SURVIVAL_PICKUPS),
        "district_gameplay_directors": 1,
        "primary_objective_consoles": 1,
        "deck_respawn_checkpoints": len(ROOM_CHECKPOINTS),
        "generated_actors": len(generated),
    })
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(data, indent=2), encoding="utf-8")
    unreal.log(
        f"Small Escort gameplay pass complete: {len(ROOM_ACTIVITY_CLASSES)} activities, "
        f"{len(ROOM_SURVIVAL_PICKUPS)} supplies, {len(ROOM_CHECKPOINTS)} checkpoints, "
        "objective console linked"
    )


if __name__ == "__main__":
    main()
