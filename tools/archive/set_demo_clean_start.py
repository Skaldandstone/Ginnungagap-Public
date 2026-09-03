"""Stop the demo map resuming a saved checkpoint when it loads.

The mission director restores completed objectives from the GinnungagapShipCheckpoint slot on its
first tick. On a development machine that slot is whatever the last session left, which meant
launching the demo showed objectives another run had already finished, with the beacons pointing at
nothing. It is also timing-dependent -- the restore bails when the player pawn is not spawned yet --
so it does not behave the same way twice.

A level that exists to be recorded in one take should begin at the beginning. This turns the
restore off for this map's director only; the class default stays on, so every other map behaves
exactly as before.

The wider question -- whether the game wants checkpoint-on-load at all, and what should invalidate
a checkpoint -- is TRO-264 and is not answered here.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/set_demo_clean_start.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"


def main():
    if not unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        unreal.log_error("Map not found: {}".format(MAP_PATH))
        return

    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    level_subsystem.load_level(MAP_PATH)

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    directors = [a for a in actor_subsystem.get_all_level_actors()
                 if a.get_class().get_name() == "QuickDemoMissionDirector"]

    if not directors:
        unreal.log_error("No mission director in the map; nothing to configure")
        return

    for director in directors:
        director.set_editor_property("restore_checkpoint_on_start", False)
        # Read back. A bool that silently stays true would leave the demo resuming exactly as
        # before, and the log would still say it was set.
        value = director.get_editor_property("restore_checkpoint_on_start")
        if value:
            unreal.log_error("{}: restore_checkpoint_on_start did not take".format(
                director.get_actor_label()))
        else:
            unreal.log("  {} starts clean".format(director.get_actor_label()))

    saved = level_subsystem.save_current_level()
    unreal.log("Configured {} director(s). Saved {}: {}".format(len(directors), MAP_PATH, saved))


if __name__ == "__main__":
    main()
