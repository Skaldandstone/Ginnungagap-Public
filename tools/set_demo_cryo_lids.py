"""Open exactly one cryo pod -- the one the player climbed out of -- and shut the rest.

Cryo pods now rest closed (ACryoPodSystem's constructor), because a bay where every lid stands open
reads as already evacuated: an open pod means somebody got out of it, and four open pods claim four
people did. That is a story problem before it is an art one.

It was also most of the room's art problem. An open lid presents a large oval of
M_Cryo_CrackedFrostGlass to the camera, and with four of them that glass was the brightest, bluest
thing in the frame by a wide margin -- bright enough that desaturating the room lights barely moved
the image. Shutting three of the four removes three-quarters of it.

The player's pod is found rather than named: it is the one nearest the PlayerStart. Naming an index
would be a guess that quietly rots the moment the bay is rearranged, and the map has already had a
console placed 200cm into a bulkhead from exactly that kind of assumption.

Idempotent: every pod is set explicitly on each run, so re-running converges rather than toggling.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/set_demo_cryo_lids.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(MAP_PATH):
        unreal.log_error("Could not load " + MAP_PATH)
        return

    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()

    pods = [a for a in actors if a.get_class().get_name() == "CryoPodSystem"]
    starts = [a for a in actors if a.get_class().get_name() == "PlayerStart"]

    if not pods:
        unreal.log_error("No CryoPodSystem in the map; nothing to set")
        return
    if not starts:
        unreal.log_error("No PlayerStart; refusing to guess which pod the player woke in")
        return

    start = starts[0].get_actor_location()

    def distance(pod):
        return (pod.get_actor_location() - start).length()

    wake_pod = min(pods, key=distance)

    opened = 0
    for pod in pods:
        is_wake = pod == wake_pod
        # Set on every pod rather than only the ones that change, so a pod left open by a previous
        # run or by hand in the editor is brought back into line.
        # "lid_open", not "b_lid_open": Unreal drops the leading b from a bool UPROPERTY when it
        # exposes it to Python. Documented in place_demo_threat_encounter.py and walked into again
        # here, which is the argument for it being written down in both places.
        pod.set_editor_property("lid_open", is_wake)
        if is_wake:
            opened += 1

        unreal.log("  {:<34} {:>6.0f}cm from the player start  lid {}".format(
            pod.get_actor_label(), distance(pod), "OPEN" if is_wake else "shut"))

    saved = levels.save_current_level()
    unreal.log("{} pod(s), {} open. Saved {}: {}".format(len(pods), opened, MAP_PATH, saved))


if __name__ == "__main__":
    main()
