"""Put opposition in the demo map, which has never had any.

A survival-horror slice with nothing hunting the player is a walking tour. The map has 96 rooms,
900 dressed actors, a full mission chain and no threat of any kind in it.

The opposition itself is not missing. The project already authors seven threat archetypes across
three factions, five encounter presets, a spawn director and a patrol/perception controller, all
tested. What is missing is an instance -- the same shape of gap as the sensor array, the helm, both
benches, the environment controller and the player's own oversuit, every one of which was a working
system that nothing in any map reached. Tests kept passing throughout, because a test asserts what
a thing does and not whether anyone can meet it.

## What is placed

One director running an alien hunting pack: two bipedal hunters and three quadruped stalkers. That
count and mix is chosen for a camera rather than for balance. Two silhouettes read as two kinds of
thing on sight, which is what a grant video can convey; a stat difference is not. Five is enough
that the ship feels occupied and few enough that they do not queue up in a corridor.

The encounter is authored as Custom rather than by preset, deliberately. BeginPlay rebuilds
EncounterDefinition from the preset whenever Preset is not Custom, which would restore two flags
this slice must not have:

  * bPrimaryAntagonist would register a required eliminate objective, putting "kill five aliens" in
    a mission chain whose last step is meant to be bringing the CIC online.
  * bBlocksJumpWhileActive would gate the jump console behind clearing them, which breaks the demo's
    ordering and the Ginnungagap.Smoke.DemoMissionChain test with it.

The pack is a presence in this slice, not a quest. Turning either flag back on is a one-line change
when there is a combat loop to hang it off.

## Where they start

Anchored, rather than left to the director's fallbacks. With no AShipSection in this map the
fallback is a random ring around the director itself, which on a 144 m ship would put them anywhere
including inside a bulkhead.

Anchors are placed in rooms along the middle and far end of the route, never in the cryo bay. A
player who opens their eyes to a stalker standing over the pod has not survived anything; the pack
should be somewhere ahead, found rather than issued.

Idempotent: tagged and matched on re-run.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/place_demo_threat_encounter.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
TAG = "GeneratedDemoThreat"

# Deck section centres and the floor drop, matching the hero-shot rig. Anchors sit a little above
# the deck so a spawn that lands on one is not embedded in the floor plate.
DECK = {1: 215.0, 2: 735.0, 3: 1255.0, 4: 1775.0}
FLOOR_DROP = 195.0
SPAWN_HEIGHT = 95.0

# Where the pack starts, as (deck, x, y). Room centres taken from the same coordinates the dressing
# and hero-shot passes use, so these are rooms rather than points in a wall.
#
# Nothing on deck 3 west: that is the cryo bay and the first two rooms of the route, and the opening
# of this slice is a person waking up alone. The first stalker should be something the player walks
# into, not something waiting for them to open their eyes.
ANCHORS = [
    (3,  5400.0, -680.0, "BloomBreach"),      # the room that has already failed
    (3,  6600.0,  680.0, "CICApproach"),      # between the player and the last objective
    (2, -5400.0,  680.0, "PowerControl"),     # mid-route, one deck down
    (1, -1200.0,  680.0, "LowerDeckSpine"),   # the long way round
]

# Two silhouettes, not one repeated. A quadruped and a biped are distinguishable across a corridor
# at low light, which is the only distinction a video can carry.
SPAWN_GROUPS = [
    ("ALIEN_BIPED_HUNTER", 2),
    ("ALIEN_QUADRUPED_STALKER", 3),
]

ENCOUNTER_ID = "DemoAlienPack"


def at(deck, x, y, height=SPAWN_HEIGHT):
    return unreal.Vector(x, y, DECK[deck] - FLOOR_DROP + height)


def clear_previous(actors_api):
    """Removes this script's own actors, and any other threat director in the map.

    The second half is not tidiness. The first run of this script added a director to a map that
    already had one, and the result was ten threats where five were intended -- caught only because
    Ginnungagap.Smoke.ThreatEncounter counts them. Two directors in one map is never what anyone
    wants: they spawn independently, each registers its own objective, and the encounter the level
    is balanced around is silently doubled.

    So the demo map holds exactly one, and this script owns it.
    """
    removed = 0
    foreign = 0
    for actor in actors_api.get_all_level_actors():
        if TAG in [str(t) for t in actor.tags]:
            actors_api.destroy_actor(actor)
            removed += 1
        elif actor.get_class().get_name() == "ShipThreatDirector":
            unreal.log_warning(
                "Removing a threat director this script did not place: {}".format(
                    actor.get_actor_label()))
            actors_api.destroy_actor(actor)
            foreign += 1

    if foreign:
        unreal.log("Removed {} pre-existing director(s); the map holds one".format(foreign))
    return removed


def build_definition():
    definition = unreal.ThreatEncounterDefinition()
    definition.set_editor_property("encounter_id", ENCOUNTER_ID)
    definition.set_editor_property(
        "display_name", unreal.Text("Something is moving on the lower decks"))

    groups = []
    for archetype_name, count in SPAWN_GROUPS:
        group = unreal.ThreatSpawnGroup()
        group.set_editor_property("archetype", getattr(unreal.ThreatArchetype, archetype_name))
        group.set_editor_property("count", count)
        groups.append(group)
    definition.set_editor_property("spawn_groups", groups)

    # Note the property names: Unreal drops the leading b from a bool UPROPERTY when exposing it to
    # Python, so bPrimaryAntagonist is "primary_antagonist" here. Getting that wrong throws rather
    # than silently doing nothing, which is the good outcome and worth not "fixing".
    #
    # The two that must stay off for this slice. See the module docstring.
    definition.set_editor_property("primary_antagonist", False)
    definition.set_editor_property("blocks_jump_while_active", False)

    # Left on, and the reason is not spawning.
    #
    # This was switched off on the first pass, reasoning that with no ship sections in the map the
    # section path would fall through to a random ring around the director. That was wrong twice
    # over. There are sections; and StartEncounter uses the gathered section list for two different
    # things -- choosing spawn points, and handing each spawned threat somewhere to patrol.
    # SpawnAnchors already wins the first, so turning this off changed nothing about where they
    # appear and quietly left all five with no patrol route at all.
    #
    # A threat with no patrol route stands still, and a motionless enemy in a dark corridor is
    # indistinguishable from an empty one. Ginnungagap.Smoke.ThreatEncounter asserts exactly this
    # and is what caught it.
    definition.set_editor_property("prefer_ship_sections", True)

    definition.set_editor_property("requires_bloom", False)
    definition.set_editor_property("currency_reward", 0)
    return definition


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(MAP_PATH):
        unreal.log_error("Could not load " + MAP_PATH)
        return

    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    removed = clear_previous(actors_api)
    if removed:
        unreal.log("Removed {} actor(s) from a previous run".format(removed))

    anchors = []
    for deck, x, y, name in ANCHORS:
        location = at(deck, x, y)
        anchor = actors_api.spawn_actor_from_class(unreal.TargetPoint, location)
        if not anchor:
            unreal.log_error("Could not place anchor {}".format(name))
            continue
        anchor.set_actor_label("DemoThreatAnchor_" + name)
        anchor.tags = [TAG]
        anchors.append(anchor)
        unreal.log("  anchor {:<16} deck {} at ({:.0f}, {:.0f}, {:.0f})".format(
            name, deck, location.x, location.y, location.z))

    if not anchors:
        unreal.log_error("No anchors placed; refusing to leave a director spawning at random")
        return

    # The director stands with the first anchor. Its own location is only used as a fallback spawn
    # origin, but a director sitting at the world origin is a thing someone will later wonder about.
    director = actors_api.spawn_actor_from_class(
        unreal.ShipThreatDirector, anchors[0].get_actor_location())
    if not director:
        unreal.log_error("Could not spawn the threat director")
        return

    director.set_actor_label("QuickDemo4D_ThreatDirector")
    director.tags = [TAG]
    director.set_editor_property("preset", unreal.ThreatEncounterPreset.CUSTOM)
    director.set_editor_property("encounter_definition", build_definition())
    director.set_editor_property("spawn_anchors", anchors)
    director.set_editor_property("auto_start", True)

    # Read back rather than trusting the setters. Struct properties set from Python have silently
    # failed in this project before -- ObjectTools.set_properties reports success on a StaticMesh
    # and leaves it None -- and an encounter with no spawn groups starts, reports nothing, and
    # spawns nobody.
    written = director.get_editor_property("encounter_definition")
    group_count = len(written.get_editor_property("spawn_groups"))
    total = sum(count for _, count in SPAWN_GROUPS)

    if group_count != len(SPAWN_GROUPS):
        unreal.log_error("Wrote {} spawn group(s), read back {}".format(
            len(SPAWN_GROUPS), group_count))
    else:
        unreal.log("Director set: {} group(s), {} threat(s), {} anchor(s), auto-start on".format(
            group_count, total, len(anchors)))

    saved = levels.save_current_level()
    unreal.log("Saved {}: {}".format(MAP_PATH, saved))


if __name__ == "__main__":
    main()
