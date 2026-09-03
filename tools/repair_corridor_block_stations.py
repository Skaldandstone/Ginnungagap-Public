"""Gives every corridor block in the placed map an override panel on both faces.

The generator placed one station per corridor block, always on the west face. A block is met from
whichever direction the route runs, and the demo's deck-2 route reached its block from the east:
the only panel was behind the door it was meant to open, and the walkthrough -- like a player --
could not get to it. The generator now places two; this brings the existing map up to that.

For each station whose target is a corridor block, a duplicate is placed mirrored across the
block's plane, facing the other way, if no station already sits on that side. Idempotent.

Run:  UnrealEditor-Cmd.exe <project> -ExecutePythonScript=<forward-slash path to this file> -NullRHI
"""
import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"


def tags(actor):
    return [str(t) for t in actor.tags]


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(MAP_PATH):
        unreal.log_error("STATIONS could not load " + MAP_PATH)
        return
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = actors_api.get_all_level_actors()

    stations = [a for a in actors if a.get_class().get_name() == "MechanicalOverrideStation"]
    by_door = {}
    for station in stations:
        target = station.get_editor_property("target_actor")
        if target and "CorridorBlockDoor" in tags(target):
            by_door.setdefault(target.get_name(), (target, []))[1].append(station)

    added = 0
    for door_name, (door, door_stations) in by_door.items():
        door_x = door.get_actor_location().x
        sides = {"west" if s.get_actor_location().x < door_x else "east" for s in door_stations}
        if len(sides) == 2:
            continue
        source = door_stations[0]
        loc = source.get_actor_location()
        mirrored = unreal.Vector(2.0 * door_x - loc.x, loc.y, loc.z)
        rot = source.get_actor_rotation()
        twin = actors_api.duplicate_actor(source, None, unreal.Vector(0.0, 0.0, 0.0))
        if not twin:
            unreal.log_error("STATIONS could not duplicate {}".format(source.get_actor_label()))
            continue
        twin.set_actor_location(mirrored, False, False)
        twin.set_actor_rotation(unreal.Rotator(roll=rot.roll, pitch=rot.pitch, yaw=rot.yaw + 180.0), False)
        twin.set_editor_property("target_actor", door)
        face = "East" if mirrored.x > door_x else "West"
        twin.set_actor_label(source.get_actor_label() + "_" + face)
        twin.tags = [t for t in tags(source) if t != "CorridorBlockStation"] + ["CorridorBlockStation"]
        source.tags = [t for t in tags(source) if t != "CorridorBlockStation"] + ["CorridorBlockStation"]
        added += 1
        unreal.log("STATIONS {} gets a {} panel at ({:.0f}, {:.0f}, {:.0f})".format(door.get_actor_label(), face.lower(), mirrored.x, mirrored.y, mirrored.z))

    unreal.log("STATIONS {} corridor blocks, {} panels added".format(len(by_door), added))
    saved = levels.save_current_level()
    unreal.log("STATIONS saved {}: {}".format(MAP_PATH, saved))


if __name__ == "__main__":
    main()
