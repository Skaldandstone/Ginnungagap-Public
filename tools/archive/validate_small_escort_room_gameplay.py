"""Validate the incremental gameplay pass on the Small Escort operations district."""

import unreal


MAP = "/Game/Assets/Maps/ShipProduction/L_SmallEscort_OperationsDeck"
PREFIX = "EscortOps_"
EXPECTED_PICKUP_ROOMS = {"MED-07-01", "SUR-07-01", "LIF-06-01", "EVA-06-01"}
EXPECTED_CHECKPOINTS = {
    "OPS-08-01": "EscortOps_Deck08_Entry",
    "CCM-07-01": "EscortOps_Deck07_CrewCommons",
    "DCR-06-01": "EscortOps_Deck06_DamageControl",
}


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(MAP):
        raise RuntimeError("Could not load Small Escort operations district")

    level_actors = actors.get_all_level_actors()
    failures = []
    rooms = {
        str(actor.get_editor_property("room_code")): actor
        for actor in level_actors
        if actor.get_actor_label().startswith(PREFIX + "Room_")
    }
    activities = [
        actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "Activity_")
    ]
    pickups = [
        actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "Pickup_")
    ]
    checkpoints = [
        actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "Checkpoint_")
    ]

    if len(rooms) != 24:
        failures.append(f"room count {len(rooms)} != 24")
    if len(activities) != 24:
        failures.append(f"activity station count {len(activities)} != 24")
    activity_rooms = set()
    for station in activities:
        label = station.get_actor_label()
        room_code = label[len(PREFIX + "Activity_"):].split("_", 1)[0]
        room = rooms.get(room_code)
        activity_rooms.add(room_code)
        if not room:
            failures.append(f"activity {label} has no owning room")
            continue
        if station.get_editor_property("target_actor") != room:
            failures.append(f"activity {label} does not target its room")
        if str(station.get_editor_property("station_id")) != f"{room_code}-ACT-00":
            failures.append(f"activity {label} has an unstable station id")
        if str(station.get_editor_property("owning_room_code")) != room_code:
            failures.append(f"activity {label} has the wrong owning room code")
        mesh = station.get_editor_property("mesh")
        if not mesh or not mesh.get_editor_property("static_mesh"):
            failures.append(f"activity {label} has no visible interaction mesh")
        origin, extent = station.get_actor_bounds(False)
        room_center = room.get_actor_location()
        if abs(origin.y - room_center.y) - extent.y < 180.0:
            failures.append(f"activity {label} intrudes into the 3.6 m central lane")
        if abs(origin.x - room_center.x) + extent.x > 750.0 + 2.0:
            failures.append(f"activity {label} exceeds its room envelope on X")
        if abs(origin.y - room_center.y) + extent.y > 700.0 + 2.0:
            failures.append(f"activity {label} exceeds its room envelope on Y")
    if activity_rooms != set(rooms):
        failures.append("activity stations do not cover every room exactly once")

    if len(pickups) != 4:
        failures.append(f"survival pickup count {len(pickups)} != 4")
    pickup_rooms = set()
    for pickup in pickups:
        label = pickup.get_actor_label()
        room_code = label[len(PREFIX + "Pickup_"):].split("_", 1)[0]
        pickup_rooms.add(room_code)
        visual = pickup.get_editor_property("visual_mesh")
        if not visual or not visual.get_editor_property("static_mesh"):
            failures.append(f"survival pickup {label} has no visible mesh")
    if pickup_rooms != EXPECTED_PICKUP_ROOMS:
        failures.append(f"survival pickup room coverage is incorrect: {sorted(pickup_rooms)}")

    if len(checkpoints) != len(EXPECTED_CHECKPOINTS):
        failures.append(f"deck checkpoint count {len(checkpoints)} != {len(EXPECTED_CHECKPOINTS)}")
    checkpoint_rooms = set()
    for checkpoint in checkpoints:
        label = checkpoint.get_actor_label()
        room_code = label[len(PREFIX + "Checkpoint_"):]
        checkpoint_rooms.add(room_code)
        expected_id = EXPECTED_CHECKPOINTS.get(room_code)
        if not expected_id:
            failures.append(f"unexpected checkpoint {label}")
            continue
        if str(checkpoint.get_editor_property("checkpoint_id")) != expected_id:
            failures.append(f"checkpoint {label} has an unstable id")
        room = rooms.get(room_code)
        if not room:
            failures.append(f"checkpoint {label} has no owning room")
            continue
        delta = checkpoint.get_actor_location() - room.get_actor_location()
        if abs(delta.x) > 1.0 or abs(delta.y) > 1.0:
            failures.append(f"checkpoint {label} is not centered in its safe room lane")
        trigger = checkpoint.get_editor_property("trigger")
        if not trigger or trigger.get_unscaled_box_extent().x < 250.0:
            failures.append(f"checkpoint {label} has an undersized trigger")
    if checkpoint_rooms != set(EXPECTED_CHECKPOINTS):
        failures.append(f"deck checkpoint room coverage is incorrect: {sorted(checkpoint_rooms)}")

    directors = [
        actor for actor in level_actors if actor.get_actor_label() == PREFIX + "GameplayDirector"
    ]
    objectives = [
        actor for actor in level_actors
        if actor.get_actor_label() == PREFIX + "ObjectiveConsole_DCR-06-01"
    ]
    if len(directors) != 1:
        failures.append(f"gameplay director count {len(directors)} != 1")
    else:
        director = directors[0]
        if str(director.get_editor_property("primary_objective_id")) != "EscortOps_RestoreOperations":
            failures.append("gameplay director objective id is incorrect")
        if director.get_editor_property("spawn_gameplay_on_begin_play"):
            failures.append("gameplay director random spawning is enabled")
    if len(objectives) != 1:
        failures.append(f"objective console count {len(objectives)} != 1")
    elif str(objectives[0].get_editor_property("objective_id")) != "EscortOps_RestoreOperations":
        failures.append("objective console does not resolve the registered district objective")
    if (objectives and rooms.get("DCR-06-01")
            and rooms["DCR-06-01"].get_editor_property("system_anchor") != objectives[0]):
        failures.append("Damage Control Central is not bound to the objective console")

    if failures:
        raise RuntimeError("Small Escort room gameplay validation failed:\n" + "\n".join(failures))
    unreal.log(
        f"Small Escort room gameplay validation passed: {len(activities)} activities, "
        f"{len(pickups)} supplies, {len(checkpoints)} deck checkpoints, "
        "one mission-linked objective console"
    )


if __name__ == "__main__":
    main()
