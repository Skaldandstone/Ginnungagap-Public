"""
Repair the CryoPodSystem attachment cycle serialized into L_QuickDemo_FourDeck.

The PIE smoke test (Ginnungagap.Smoke.PlayInEditor) surfaced an engine ensure on every load of the
canonical demo map:

    Attaching SceneComponent CryoPodSystem_4.NeutralRoot to SceneComponent
    CryoPodSystem_4.PodRakePivot would create a cycle.

The class itself is correct -- ACryoPodSystem's constructor makes NeutralRoot the root and attaches
PodRakePivot beneath it. The fault is in the placed instance: an older component hierarchy was
saved into the map, and the loader tries to reapply it against the current one. So this is map data
to repair, not code to change.

Loading and re-saving is the repair. The engine resolves the stale attachment during load -- that
is what the ensure is reporting -- so persisting the loaded state writes the corrected hierarchy
back. This script does that deliberately rather than relying on someone happening to open and save
the map.

Idempotent: on an already-repaired map the attachments match and nothing is written.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/fix_cryopod_attachment_cycle.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound

Note the forward slashes: a Windows-style path containing \tools\ is read as a tab by the shell.
"""

import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"


def describe(actor):
    """Root component name and the parent each scene component thinks it has."""
    root = actor.get_editor_property("root_component")
    return root.get_name() if root else "<none>"


def main():
    if not unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        unreal.log_error("Map not found: {}".format(MAP_PATH))
        return

    unreal.LevelEditorSubsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    unreal.LevelEditorSubsystem.load_level(MAP_PATH)

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = actor_subsystem.get_all_level_actors()

    pods = [a for a in actors if a.get_class().get_name() == "CryoPodSystem"]
    if not pods:
        unreal.log_warning("No CryoPodSystem actors in {} -- nothing to repair".format(MAP_PATH))
        return

    for pod in pods:
        unreal.log("{}: root component is {}".format(pod.get_name(), describe(pod)))

    # Saving persists whatever the loader resolved, which is the corrected hierarchy. Nothing is
    # mutated here on purpose: reassigning attachments by hand risks writing a worse hierarchy than
    # the one the engine already worked out.
    saved = unreal.LevelEditorSubsystem.save_current_level()
    unreal.log("Saved {}: {}".format(MAP_PATH, saved))
    unreal.log("Repaired {} CryoPodSystem actor(s)".format(len(pods)))


if __name__ == "__main__":
    main()
