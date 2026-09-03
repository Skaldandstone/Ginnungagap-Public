"""Report what is actually in the CIC and where, so its hero shot can be framed against numbers.

The hero rig frames rooms by a rule -- stand in the doorway, look in -- which works because it needs
no knowledge of a room's contents. The CIC is the room where that breaks: it holds four interactive
stations, two chairs and a holographic plot inside about ten metres, so whichever way the camera
faces something is a metre from the lens. Two attempts have now produced a frame with an unlit slab
across the middle of it, and the second attempt moved the camera into a *different* station than the
first.

Guessing a third time would be the same mistake this project has made repeatedly: a console placed
200cm into a bulkhead, a wall panel used as a free-standing desk, a 610cm lamp turned across a 360cm
corridor. Every one of those was found by looking at a render, and every one would have been avoided
by measuring first.

So this measures. For the CIC room it reports the room's own bounds, then every actor inside it with
its position relative to the room centre, its footprint, and its height -- which is all a camera
placement needs, and none of which is knowable from the outside.

Writes nothing.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/survey_cic_room.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"

# The room is found from the station that defines it rather than by name or by coordinates. The
# anchor is the actor the mission chain routes the player to, so whichever room contains it is the
# CIC by definition, and this keeps working if the room is moved.
ANCHOR_CLASS = "QuickDemoCICConsole"

# Dressing that is never in anyone's way and would bury the interesting rows. Walls, floors and
# ceilings are the room, not things in it.
IGNORED_SUBSTRINGS = ("SM_WALL", "SM_FLOOR", "SM_CEILING", "Greybox", "Light", "Refl_")


def find_room_for(actors, anchor):
    """The room whose bounds contain the anchor, and its bounds."""
    at = anchor.get_actor_location()
    best = None
    best_volume = None
    for actor in actors:
        if actor.get_class().get_name() != "ModularShipRoom":
            continue
        origin, extent = actor.get_actor_bounds(False)
        if (abs(at.x - origin.x) <= extent.x
                and abs(at.y - origin.y) <= extent.y
                and abs(at.z - origin.z) <= extent.z):
            volume = extent.x * extent.y * extent.z
            # Smallest containing room wins. Rooms can nest inside a deck-sized volume, and the
            # deck is not the room a camera stands in.
            if best_volume is None or volume < best_volume:
                best, best_volume = (origin, extent), volume
    return best


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(MAP_PATH):
        unreal.log_error("Could not load " + MAP_PATH)
        return

    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()

    anchor = None
    for actor in actors:
        if actor.get_class().get_name() == ANCHOR_CLASS:
            anchor = actor
            break
    if anchor is None:
        unreal.log_error("No {} in the map; cannot identify the CIC".format(ANCHOR_CLASS))
        return

    room = find_room_for(actors, anchor)
    if room is None:
        unreal.log_error("The CIC anchor is not inside any room")
        return

    origin, extent = room
    unreal.log("CIC room centre ({:.0f}, {:.0f}, {:.0f})  half-extent ({:.0f}, {:.0f}, {:.0f})".format(
        origin.x, origin.y, origin.z, extent.x, extent.y, extent.z))
    unreal.log("  interior spans X {:.0f}..{:.0f}   Y {:.0f}..{:.0f}".format(
        origin.x - extent.x, origin.x + extent.x,
        origin.y - extent.y, origin.y + extent.y))
    unreal.log("  contents, offsets relative to the room centre:")

    rows = []
    for actor in actors:
        label = actor.get_actor_label()
        if any(skip in label for skip in IGNORED_SUBSTRINGS):
            continue

        at = actor.get_actor_location()
        if (abs(at.x - origin.x) > extent.x
                or abs(at.y - origin.y) > extent.y
                or abs(at.z - origin.z) > extent.z):
            continue

        _, size = actor.get_actor_bounds(False)
        rows.append((at.x - origin.x, at.y - origin.y, at.z - origin.z,
                     size.x * 2.0, size.y * 2.0, size.z * 2.0, label))

    # Sorted by distance from the doorway side, which is the order a camera meets them.
    rows.sort(key=lambda row: row[1])
    for dx, dy, dz, sx, sy, sz, label in rows:
        unreal.log("    {:<36} at ({:+6.0f}, {:+6.0f}, {:+6.0f})  size {:4.0f} x {:4.0f} x {:4.0f}".format(
            label, dx, dy, dz, sx, sy, sz))

    unreal.log("  {} item(s) in the room".format(len(rows)))


if __name__ == "__main__":
    main()
