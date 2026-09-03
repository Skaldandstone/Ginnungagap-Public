"""Put a ship environment controller on each deck so the demo is not silent.

`AShipEnvironmentController` drives the ambient bed, the alarm, the Bloom presence sound, the
atmosphere fog colour, the vignette and film grain, and the damage decals. All of it worked and
none of it ran, because the actor was never spawned and appears in no map. Every one of those
properties was dead for the same reason a helm was invisible and two benches had no mesh: the
class was fine and no instance existed.

The sounds are the project's own, not the Fab horror pack. `S_Ship_AmbientHum_Loop`,
`S_Ship_DamageAlarm_Loop` and `S_Bloom_Atmosphere_Loop` were authored for exactly these three
slots and are named for them. The Fab pack is worth reaching for when the sound language is
designed properly (TRO-45); it is not worth reaching for to fill a slot that already has a
purpose-made asset sitting next to it.

One controller per deck, on the corridor centreline. Its attenuation sphere is 65 m against a 72 m
half-corridor, so a single controller very nearly covers its deck and two would overlap and stack
two copies of the same loop against each other.

Both runtime follow flags are on, so the controller tracks the live Bloom stage and the deck's
damage score rather than sitting on an authored preview value. That is what makes the ambience
change when the ship does, which is the entire point of it existing.

Idempotent: tagged and replaced on re-run.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/place_demo_environment_audio.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
TAG = "GeneratedEnvironmentAudio"

AUDIO = "/Game/Assets/Ships/Production/Audio/"
SOUNDS = {
    "ship_hum_sound": AUDIO + "S_Ship_AmbientHum_Loop.S_Ship_AmbientHum_Loop",
    "alarm_sound": AUDIO + "S_Ship_DamageAlarm_Loop.S_Ship_DamageAlarm_Loop",
    "bloom_sound": AUDIO + "S_Bloom_Atmosphere_Loop.S_Bloom_Atmosphere_Loop",
}

# Corridor section centres, measured from the map.
DECK_CENTRE_Z = {1: 215.0, 2: 735.0, 3: 1255.0, 4: 1775.0}


def main():
    if not unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        unreal.log_error("Map not found: {}".format(MAP_PATH))
        return

    loaded = {}
    for prop, path in SOUNDS.items():
        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            # Refused rather than skipped. A controller with no ambient bed is silent, which is
            # exactly the state this script exists to fix, and it would report success.
            unreal.log_error("Sound missing: {}".format(path))
            return
        loaded[prop] = unreal.EditorAssetLibrary.load_asset(path)

    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    level_subsystem.load_level(MAP_PATH)

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = actor_subsystem.get_all_level_actors()

    removed = 0
    for actor in actors:
        if TAG in [str(t) for t in actor.tags]:
            actor_subsystem.destroy_actor(actor)
            removed += 1
    if removed:
        unreal.log("Removed {} controller(s) from a previous run".format(removed))
        actors = actor_subsystem.get_all_level_actors()

    # Match each deck to its corridor section, so the controller can follow that section's damage
    # rather than guessing from its own bounds.
    sections = {}
    for actor in actors:
        if actor.get_class().get_name() != "ShipSection":
            continue
        label = actor.get_actor_label()
        for deck in DECK_CENTRE_Z:
            if label.endswith("_D{:02d}".format(deck)):
                sections[deck] = actor

    placed = 0
    for deck, centre_z in sorted(DECK_CENTRE_Z.items()):
        controller = actor_subsystem.spawn_actor_from_class(
            unreal.ShipEnvironmentController, unreal.Vector(0.0, 0.0, centre_z))
        if not controller:
            unreal.log_error("Failed to spawn a controller for deck {:02d}".format(deck))
            continue

        controller.set_actor_label("EnvironmentAudio_D{:02d}".format(deck))
        controller.tags = [TAG]

        for prop, asset in loaded.items():
            controller.set_editor_property(prop, asset)

        # Follow the run rather than an authored preview stage, so the ambience answers the ship.
        controller.set_editor_property("follow_live_bloom_state", True)
        controller.set_editor_property("follow_ship_damage_state", True)

        section = sections.get(deck)
        if section:
            controller.set_editor_property("monitored_section", section)
        else:
            # Not fatal -- the controller falls back to locating the section containing it -- but
            # worth saying, because a deck whose section is not found silently stops reacting to
            # damage and nothing else reports that.
            unreal.log_warning(
                "No corridor section found for deck {:02d}; controller will locate its own".format(deck))

        # Read back rather than trust the setter. An object-reference property that reports success
        # and stays None is a failure mode this project has already hit once today through a
        # different API, and a silent one: the controller spawns, the log says placed, and the
        # demo is still silent.
        assigned = []
        for prop in SOUNDS:
            value = controller.get_editor_property(prop)
            assigned.append("{}={}".format(prop.split("_")[0], "ok" if value else "NONE"))
            if not value:
                unreal.log_error("Deck {:02d}: {} did not take".format(deck, prop))

        unreal.log("  Deck {:02d}: z={:.0f}  {}{}".format(
            deck, centre_z, "  ".join(assigned),
            "" if section else "  (no section match)"))
        placed += 1

    saved = level_subsystem.save_current_level()
    unreal.log("Placed {} environment controller(s). Saved {}: {}".format(
        placed, MAP_PATH, saved))


if __name__ == "__main__":
    main()
