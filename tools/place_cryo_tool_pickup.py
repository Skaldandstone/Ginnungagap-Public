"""Places a pickupable tool inside the cryo bay, near the exit, before the Cut/Squeeze obstruction.

"The tool could just be laying inside the cryo room, or something" -- James, once the search for
the exact right semantic item (a consumable repair item vs. an equipment slot vs. a weapon-mount
grant) turned out to be real new-system scope rather than a five-minute fix.

Reuses AInventoryItemPickup exactly as designed: a generic, tested, replicated pickup that transfers
an item into the player's inventory on interact. DA_Item_FieldRepairKit is what already exists in
the project under that description ("patch stock, seam tape and a spare seal set") -- not a perfect
narrative match for a cutting tool, and that is fine; the beat is "something to find and pick up
near cryo," not a specific implement.

Placed near the cryo threshold door (anchored on its own tag, same anchor the obstruction itself
uses), on the room side, so a player reaches it before the obstruction rather than after.
"""

import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
CRYO_CODE = "QD-03-01"
ITEM = "/Game/Assets/Gameplay/FieldSupplies/Data/Items/DA_Item_FieldRepairKit"
TAG = "QuickDemoCryoToolPickup"


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(MAP):
        unreal.log_error("TOOL could not load {}".format(MAP))
        return

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    removed = 0
    for actor in actor_subsystem.get_all_level_actors():
        if actor.actor_has_tag(TAG):
            actor_subsystem.destroy_actor(actor)
            removed += 1
    if removed:
        unreal.log("TOOL removed {} previous placement(s)".format(removed))

    door = None
    for actor in actor_subsystem.get_all_level_actors():
        tags = [str(t) for t in actor.tags]
        if "RoomThresholdDoor" in tags and CRYO_CODE in tags:
            door = actor
            break
    if not door:
        unreal.log_error("TOOL no RoomThresholdDoor tagged {}".format(CRYO_CODE))
        return

    door_location = door.get_actor_location()
    # Into the room from the doorway, on the near side of the threshold. Not the door actor's
    # forward vector: every generated door sits at yaw 0, +X along the wall, and the first placement
    # put this 220 cm along the wall -- inside the InnerWall segment. Through the doorway is +/-Y;
    # the room is on the side away from the corridor, found from the room actor itself.
    room = None
    for actor in actor_subsystem.get_all_level_actors():
        if actor.get_class().get_name() == "ModularShipRoom" and CRYO_CODE in [str(t) for t in actor.tags]:
            room = actor
            break
    if not room:
        unreal.log_error("TOOL no ModularShipRoom tagged {}".format(CRYO_CODE))
        return
    toward_room = -1.0 if door_location.y > room.get_actor_location().y else 1.0
    # Offset along the wall as well: straight in from the door is the player start's own
    # footprint, and a pickup's 95 cm interaction sphere there sits under the magnetic-boot trace,
    # which then reads "not metal" and refuses to engage on the first frame of the demo.
    location = unreal.Vector(door_location.x - 150.0, door_location.y + toward_room * 220.0, door_location.z + 20.0)

    pickup_class = unreal.load_class(None, "/Script/Ginnungagap.InventoryItemPickup")
    if not pickup_class:
        unreal.log_error("TOOL could not load AInventoryItemPickup")
        return

    item = unreal.load_asset(ITEM)
    if not item:
        unreal.log_error("TOOL could not load {}".format(ITEM))
        return

    pickup = actor_subsystem.spawn_actor_from_class(pickup_class, location, unreal.Rotator())
    if not pickup:
        unreal.log_error("TOOL spawn failed")
        return

    pickup.tags = [unreal.Name(TAG), unreal.Name("CRYO-TOOL")]
    pickup.call_method("ConfigurePickup", args=(item, 1))

    # Read back rather than trust the write.
    check_item = pickup.get_editor_property("item_definition")
    check_qty = pickup.get_editor_property("quantity")
    unreal.log("TOOL placed at {:.0f},{:.0f},{:.0f}  item={}  qty={}".format(
        location.x, location.y, location.z,
        check_item.get_name() if check_item else "NONE", check_qty))

    levels.save_current_level()
    unreal.log("TOOL saved")


main()
