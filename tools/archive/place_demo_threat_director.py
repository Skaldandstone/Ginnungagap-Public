"""
Put an antagonist in L_QuickDemo_FourDeck.

The map has 96 rooms, 114 bulkhead doors, a five-objective mission chain -- and nothing hostile.
No AShipThreatDirector is placed, so the AI, patrol, perception and stealth systems never execute.
Stealth is a headline mechanic with nothing to hide from, and two of the eleven active skills exist
to counter perception that never happens.

Nothing needed building. AShipThreatDirector self-configures from a preset, finds AShipSection
actors for spawning and patrol routing, and auto-starts. AModularShipRoom derives from AShipSection,
so all 96 rooms are already valid spawn and patrol targets.

Idempotent: tagged and matched on re-run, so this replaces its own director rather than stacking.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/place_demo_threat_director.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
TAG = "GeneratedThreatDirector"

# AlienHuntingPack rather than a boarding party. The demo is meant to show the stealth model, and a
# pack that patrols and hunts exercises light, noise and visibility -- whereas pirates read as a
# firefight, which the demo is not yet equipped for and which the game is not really about.
PRESET = unreal.ThreatEncounterPreset.ALIEN_HUNTING_PACK


def tagged(actor):
    return TAG in [str(t) for t in actor.tags]


def main():
    if not unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        unreal.log_error("Map not found: {}".format(MAP_PATH))
        return

    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    level_subsystem.load_level(MAP_PATH)

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = actor_subsystem.get_all_level_actors()

    removed = 0
    for actor in actors:
        if tagged(actor):
            actor_subsystem.destroy_actor(actor)
            removed += 1
    if removed:
        unreal.log("Removed {} director(s) from a previous run".format(removed))
        actors = actor_subsystem.get_all_level_actors()

    # Spawn and patrol both draw from ship sections, so a map without them would place threats at
    # the director's own location and give the AI nothing to walk between. Worth failing loudly
    # rather than producing an encounter that silently stands still.
    sections = [a for a in actors if isinstance(a, unreal.ShipSection)]
    if not sections:
        unreal.log_error("No AShipSection actors found; threats would have nowhere to spawn or patrol")
        return

    centre = unreal.Vector(0.0, 0.0, 0.0)
    for section in sections:
        centre = centre + section.get_actor_location()
    centre = centre / float(len(sections))

    director = actor_subsystem.spawn_actor_from_class(unreal.ShipThreatDirector, centre)
    if not director:
        unreal.log_error("Failed to spawn AShipThreatDirector")
        return

    director.set_actor_label("ThreatDirector_DemoEncounter")
    director.tags = [TAG]
    director.set_editor_property("preset", PRESET)

    # Auto-start is the default and is left on so the encounter needs no trigger wiring. Whether it
    # should instead begin at a later objective is a pacing decision for a play pass, not something
    # to settle from a script -- see the note logged below.
    director.set_editor_property("auto_start", True)

    unreal.log("Placed threat director at ({:.0f}, {:.0f}, {:.0f}) using preset {} across {} sections"
               .format(centre.x, centre.y, centre.z, PRESET, len(sections)))
    unreal.log("PACING: auto-start is on, so threats are live from the opening cryo objective. "
               "If that undercuts the opening, gate it on QD_RestorePower or QD_SealBreach.")

    saved = level_subsystem.save_current_level()
    unreal.log("Saved {}: {}".format(MAP_PATH, saved))


if __name__ == "__main__":
    main()
