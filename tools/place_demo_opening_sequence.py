"""Places the opening sequence director and tags the player's cryo pod.

AQuickDemoOpeningSequence runs the demo's first eight seconds -- third person on the sleeper,
the strike, the blackout, the wake, first person -- from the pod tagged QuickDemoPlayerPod. The
first pod (QuickDemo4D_CryoPod_01) is the one nearest the player start, so it gets the tag.

Idempotent: tagged and replaced on re-run.

Run:  UnrealEditor-Cmd.exe <project> -ExecutePythonScript=<forward-slash path to this file> -NullRHI
"""
import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
TAG = "GeneratedDemoOpening"
POD_TAG = "QuickDemoPlayerPod"


def tags(actor):
    return [str(t) for t in actor.tags]


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(MAP_PATH):
        unreal.log_error("OPENING could not load " + MAP_PATH)
        return
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    start = None
    pods = []
    for actor in actors_api.get_all_level_actors():
        cls = actor.get_class().get_name()
        if TAG in tags(actor):
            actors_api.destroy_actor(actor)
        elif cls == "PlayerStart":
            start = actor
        elif cls == "CryoPodSystem":
            pods.append(actor)
    if not start or not pods:
        unreal.log_error("OPENING need a PlayerStart and cryo pods; found start={} pods={}".format(bool(start), len(pods)))
        return

    nearest = min(pods, key=lambda p: (p.get_actor_location() - start.get_actor_location()).length())
    for pod in pods:
        current = [t for t in tags(pod) if t != POD_TAG]
        pod.tags = current + ([POD_TAG] if pod is nearest else [])
    unreal.log("OPENING player pod is {} at {}".format(nearest.get_actor_label(), nearest.get_actor_location()))

    opening_class = getattr(unreal, "QuickDemoOpeningSequence", None)
    if opening_class is None:
        unreal.log_error("OPENING unreal.QuickDemoOpeningSequence is not reflected; rebuild the editor target first")
        return
    opening = actors_api.spawn_actor_from_class(opening_class, start.get_actor_location())
    opening.set_actor_label("QuickDemo4D_OpeningSequence")
    opening.tags = [TAG, "QuickDemoGameplay"]

    saved = levels.save_current_level()
    unreal.log("OPENING saved {}: {}".format(MAP_PATH, saved))


if __name__ == "__main__":
    main()
