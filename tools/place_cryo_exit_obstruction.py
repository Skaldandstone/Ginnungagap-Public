"""Places a Cut/Squeeze obstruction at the cryo bay's own threshold door.

For the wake-up sequence: cut the door with a found tool, the result is a gap you squeeze through.
Not one of the three shared authoring presets -- CollapsedDebris permits all three verbs,
WeldedBulkhead is cut-or-blow with no squeeze, JammedHatch is squeeze-only with nothing to cut. This
beat wants exactly two of the three (Cut, Squeeze; no Breach -- a demo that opens with the ship
already hit does not also want the player's first action to be loud), which is specific enough to
this one story moment that it is configured directly here rather than added as a fourth generic
preset to a shared function meant for reusable obstruction types.

Anchored on the cryo threshold door's own transform (found by tag) rather than a guessed room
coordinate, so this does not repeat tonight's pattern of placing something from arithmetic that
turned out wrong.
"""

import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
CRYO_CODE = "QD-03-01"
TAG = "QuickDemoCryoExitObstruction"


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(MAP):
        unreal.log_error("OBS could not load {}".format(MAP))
        return

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    removed = 0
    for actor in actor_subsystem.get_all_level_actors():
        if actor.actor_has_tag(TAG):
            actor_subsystem.destroy_actor(actor)
            removed += 1
    if removed:
        unreal.log("OBS removed {} previous placement(s)".format(removed))

    door = None
    for actor in actor_subsystem.get_all_level_actors():
        tags = [str(t) for t in actor.tags]
        if "RoomThresholdDoor" in tags and CRYO_CODE in tags:
            door = actor
            break

    if not door:
        unreal.log_error("OBS no RoomThresholdDoor tagged {} -- cryo's door tag may have changed"
                         .format(CRYO_CODE))
        return

    door_location = door.get_actor_location()
    # Centred in the doorway, in the wall plane, with the box turned so its 380 cm width spans the
    # generator's 250 cm gap along the wall and its 120 cm depth runs through it. Not the door
    # actor's forward vector: the generator leaves every door at yaw 0, which points +X along the
    # wall, and the first placement -- 120 cm along that axis -- plugged a quarter of the gap and
    # left a pawn 185 cm to walk past. Through the doorway is +/-Y, toward the corridor.
    room = None
    for actor in actor_subsystem.get_all_level_actors():
        if actor.get_class().get_name() == "ModularShipRoom" and CRYO_CODE in [str(t) for t in actor.tags]:
            room = actor
            break
    if not room:
        unreal.log_error("OBS no ModularShipRoom tagged {}".format(CRYO_CODE))
        return
    # Box centre at floor top + half-height: the door actor sits 10 below the floor, whose top is
    # 10 above that, and the Blocker's half-height is 160.
    location = unreal.Vector(door_location.x, door_location.y, door_location.z + 180.0)
    rotation = unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0)

    barrier_class = unreal.load_class(None, "/Script/Ginnungagap.ObstructionBarrier")
    if not barrier_class:
        unreal.log_error("OBS could not load AObstructionBarrier")
        return

    barrier = actor_subsystem.spawn_actor_from_class(barrier_class, location, rotation)
    if not barrier:
        unreal.log_error("OBS spawn failed")
        return

    barrier.tags = [unreal.Name(TAG), unreal.Name("CRYO-EXIT")]
    barrier.set_editor_property("display_name", "Buckled bulkhead")
    barrier.set_editor_property("bypassable", False)

    # Cut and Squeeze only. No Breach -- the ship has already been hit; the player's first action
    # should not also be an explosion.
    cut = unreal.ObstructionVerbOption()
    cut.set_editor_property("allowed", True)
    cut.set_editor_property("duration_seconds", 8.0)
    cut.set_editor_property("minimum_equipment_condition", 0.2)
    cut.set_editor_property("noise_loudness", 0.3)

    squeeze = unreal.ObstructionVerbOption()
    squeeze.set_editor_property("allowed", True)
    squeeze.set_editor_property("duration_seconds", 6.0)
    squeeze.set_editor_property("noise_loudness", 0.15)
    squeeze.set_editor_property("near_entrapment_chance", 0.25)

    options = {
        unreal.ObstructionVerb.CUT: cut,
        unreal.ObstructionVerb.SQUEEZE: squeeze,
    }
    barrier.set_editor_property("options", options)

    # Read back rather than trust the write.
    check = barrier.get_editor_property("options")
    unreal.log("OBS placed at {:.0f},{:.0f},{:.0f}  verbs={}  bypassable={}".format(
        location.x, location.y, location.z,
        [str(k) for k in check.keys()],
        barrier.get_editor_property("bypassable")))

    levels.save_current_level()
    unreal.log("OBS saved")


main()
