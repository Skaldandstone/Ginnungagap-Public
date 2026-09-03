"""Puts the dormant Bloom hulk in the breach room.

The trailer beat sheet: power comes back, and somewhere else in the ship something wakes and
roars. ABloomDormantHulk is the something; this is the somewhere. The breach room is the Bloom's
own site in the demo -- the mass that came through the hull is dressed on its floor -- so the hulk
stands in the rupture in the outer wall, between the two hull fragments the generator leaves
there, facing into the room and the corridor beyond. The breach patch station is on the corridor
side of the room, some seven metres from it: in sight, out of reach.

Idempotent: tagged and replaced on re-run.

Run:  UnrealEditor-Cmd.exe <project> -ExecutePythonScript=<forward-slash path to this file> -NullRHI
"""
import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
TAG = "GeneratedDemoHulk"

ROOM_Y = 1000.0          # room depth (Config/Ships/QuickDemoFourDeck.json room_size_cm[1])
ROOM_HEIGHT = 430.0
CAPSULE_HALF_HEIGHT = 188.0
# How far in from the outer wall plane the capsule centre stands: the hulk is in the rupture, not
# floating outside it. Its capsule radius is 88.
STAND_IN_FROM_OUTER_WALL = 95.0
ALONG_WALL_OFFSET = 30.0  # between the fragments, which sit at -340 and +350 from the room centre


def tags(actor):
    return [str(t) for t in actor.tags]


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(MAP_PATH):
        unreal.log_error("HULK could not load " + MAP_PATH)
        return
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    removed = 0
    breach = None
    for actor in actors_api.get_all_level_actors():
        if TAG in tags(actor):
            actors_api.destroy_actor(actor)
            removed += 1
        elif actor.get_class().get_name() == "ModularShipRoom" and "breach" in tags(actor):
            breach = actor
    if removed:
        unreal.log("HULK removed {} actor(s) from a previous run".format(removed))
    if not breach:
        unreal.log_error("HULK no ModularShipRoom tagged 'breach' in the map")
        return

    centre = breach.get_actor_location()
    side = -1.0 if centre.y < 0.0 else 1.0
    outer_y = centre.y + side * ROOM_Y * 0.5
    floor_top = centre.z - ROOM_HEIGHT * 0.5 + 20.0
    location = unreal.Vector(
        centre.x + ALONG_WALL_OFFSET,
        outer_y - side * STAND_IN_FROM_OUTER_WALL,
        floor_top + CAPSULE_HALF_HEIGHT)
    # Facing the corridor: +Y for a room on the -Y side, -Y otherwise. By keyword: the positional
    # constructor is (roll, pitch, yaw), and the first run of this script stood the hulk on its
    # face with pitch 90 before anyone noticed the log said "yaw 0".
    rotation = unreal.Rotator(roll=0.0, pitch=0.0, yaw=90.0 if side < 0.0 else -90.0)

    hulk_class = getattr(unreal, "BloomDormantHulk", None)
    if hulk_class is None:
        unreal.log_error("HULK unreal.BloomDormantHulk is not reflected; rebuild the editor target first")
        return
    hulk = actors_api.spawn_actor_from_class(hulk_class, location, rotation)
    if not hulk:
        unreal.log_error("HULK spawn failed")
        return
    hulk.set_actor_label("QuickDemo4D_BloomHulk")
    hulk.tags = [TAG, "QuickDemoHulk", "QuickDemoGameplay"]
    room_code = next((t for t in tags(breach) if t.startswith("QD-")), "?")
    unreal.log("HULK placed in {} ({}) at ({:.0f}, {:.0f}, {:.0f}) yaw {:.0f}, wakes on {}".format(
        breach.get_actor_label(), room_code, location.x, location.y, location.z, rotation.yaw,
        hulk.get_editor_property("wake_objective_id")))

    saved = levels.save_current_level()
    unreal.log("HULK saved {}: {}".format(MAP_PATH, saved))


if __name__ == "__main__":
    main()
