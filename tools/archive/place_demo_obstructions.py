"""Put obstructions in the demo corridors.

AObstructionBarrier exists, is tested, and stands in no map -- the same shape of gap this project
keeps finding. This places them.

## Which presets, and why not all three

Only CollapsedDebris and JammedHatch. Both can always be squeezed past, which needs no equipment at
all, so neither can strand a player who arrives without the right gear.

WeldedBulkhead is deliberately left out until there is a prompt UI. Its two verbs are cut and blow,
and while blowing has no equipment requirement today, an obstruction whose options are invisible is
one a player stands in front of pressing a key. The barrier auto-selects a usable verb on
interaction, which is enough to be passable and not enough to be a choice -- and a choice the player
cannot see is not the feature.

## Where

In the dark stretches between corridor light pools. The fixtures sit every other 12 m bay, so the
midpoints between them are the darkest parts of the ship, and an obstruction is far more effective
as a thing you come upon than as a thing you see coming from thirty metres away.

Never on deck 3 west. That is the cryo bay and the opening of the route, and
Ginnungagap.Smoke.DemoReachability asserts a walkable path from the player start to the suit
station -- an obstruction across it would be a genuine failure rather than a level-design choice.

## The visual

The barrier's own collision box does the blocking, and the mesh is dressing on top. The mesh is
measured at runtime and scaled to the corridor's cross-section rather than assumed, because
assuming a kit mesh's size has now put a wall panel free-standing in a room, a 610cm lamp through
two walls, and a console inside a bulkhead.

Idempotent: tagged and matched on re-run.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/place_demo_obstructions.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
TAG = "GeneratedDemoObstruction"

# Matches dress_demo_corridors.py. Kept as constants here rather than imported because the dresser
# is a script rather than a module, and a wrong number would be visible in the render.
BAY = 1200.0
CORRIDOR_HALF_LENGTH = 7200.0
CORRIDOR_HALF_WIDTH = 180.0

DECK = {1: 215.0, 2: 735.0, 3: 1255.0, 4: 1775.0}
FLOOR_DROP = 195.0

# The barrier's own blocker, sized to the corridor. Slightly under the full width so it does not
# intersect the wall panels, which stand inside the shell.
BLOCKER_HALF_DEPTH = 60.0
BLOCKER_HALF_WIDTH = 165.0
BLOCKER_HALF_HEIGHT = 150.0

# Debris to drape over it. Measured before use; see the module docstring.
DEBRIS_MESH = "SM_CABLE_MASS_04"
KIT_ROOT = "/Game/Modular_Scifi_Mechanic_Base"

# (deck, bay index, preset). Odd bay indices are the unlit stretches between fixtures.
#
# Deck 3 carries only one, well east of the cryo bay and the first objectives. Decks 1 and 2 carry
# the rest, where the route doubles back and a blockage costs a detour rather than the run.
PLACEMENTS = [
    (3,  9, "CollapsedDebris"),
    (2,  3, "JammedHatch"),
    (2,  7, "CollapsedDebris"),
    (1,  5, "CollapsedDebris"),
    (1, 11, "JammedHatch"),
]


def bay_x(index):
    return -CORRIDOR_HALF_LENGTH + BAY * (index + 0.5)


def find_debris_mesh():
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    for asset in registry.get_assets_by_path(KIT_ROOT, recursive=True):
        if str(asset.asset_name) == DEBRIS_MESH:
            return unreal.EditorAssetLibrary.load_asset(str(asset.package_name))
    return None


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(MAP_PATH):
        unreal.log_error("Could not load " + MAP_PATH)
        return

    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

    removed = 0
    for actor in actors_api.get_all_level_actors():
        if TAG in [str(t) for t in actor.tags]:
            actors_api.destroy_actor(actor)
            removed += 1
    if removed:
        unreal.log("Removed {} obstruction(s) from a previous run".format(removed))

    debris = find_debris_mesh()
    if debris is None:
        unreal.log_warning(
            "{} not found; barriers will be placed with no visual".format(DEBRIS_MESH))
        debris_scale = None
    else:
        bounds = debris.get_bounds().box_extent
        size = (bounds.x * 2.0, bounds.y * 2.0, bounds.z * 2.0)
        unreal.log("{} measures {:.0f} x {:.0f} x {:.0f}".format(DEBRIS_MESH, *size))

        # Scaled to fill the corridor cross-section, from the measurement rather than from a guess.
        # Guarded against a zero dimension, which would produce an infinite scale and a mesh that
        # vanishes or fills the deck.
        def fit(target, actual):
            return target / actual if actual > 1.0 else 1.0

        debris_scale = unreal.Vector(
            fit(BLOCKER_HALF_DEPTH * 2.0, size[0]),
            fit(BLOCKER_HALF_WIDTH * 2.0, size[1]),
            fit(BLOCKER_HALF_HEIGHT * 2.0, size[2]))
        unreal.log("  scaled by ({:.2f}, {:.2f}, {:.2f}) to fill the corridor".format(
            debris_scale.x, debris_scale.y, debris_scale.z))

    placed = 0
    for deck, index, preset in PLACEMENTS:
        floor_z = DECK[deck] - FLOOR_DROP
        location = unreal.Vector(bay_x(index), 0.0, floor_z + BLOCKER_HALF_HEIGHT)

        barrier = actors_api.spawn_actor_from_class(unreal.ObstructionBarrier, location)
        if not barrier:
            unreal.log_error("Could not spawn an obstruction on deck {} bay {}".format(deck, index))
            continue

        barrier.set_actor_label("QuickDemo4D_Obstruction_D{:02d}_{:02d}".format(deck, index))
        barrier.tags = [TAG]
        barrier.call_method("ApplyAuthoringPreset", args=(preset,))

        blocker = barrier.get_editor_property("blocker")
        blocker.set_box_extent(
            unreal.Vector(BLOCKER_HALF_DEPTH, BLOCKER_HALF_WIDTH, BLOCKER_HALF_HEIGHT))

        if debris is not None:
            visual = barrier.get_editor_property("visual_mesh")
            visual.set_static_mesh(debris)
            visual.set_relative_scale3d(debris_scale)

        # Read back what the preset actually produced. ApplyAuthoringPreset silently leaves a
        # barrier with no options at all when it does not recognise a name, which is the correct
        # behaviour and completely invisible from a log line saying the actor was spawned.
        options = barrier.get_editor_property("options")
        if not options:
            unreal.log_error(
                "{} produced no options; the barrier is impassable".format(preset))
            continue

        unreal.log("  deck {} bay {:2d}  {:<16} {} verb(s) at x={:.0f}".format(
            deck, index, preset, len(options), location.x))
        placed += 1

    saved = levels.save_current_level()
    unreal.log("Placed {} obstruction(s). Saved {}: {}".format(placed, MAP_PATH, saved))


if __name__ == "__main__":
    main()
