"""Raises the demo map's navmesh layer budget so four stacked decks fit in it.

Ginnungagap.Smoke.DemoReachability failed on "the player start is on navigable floor" while the
build log repeated `192 tile limit reached` from FRecastNavMeshGenerator::AddGeneratedTileLayer.

192 is not an arbitrary number. The NavMeshBoundsVolume is 15000 x 3600 across and TileSizeUU is
1000, which is 16 x 4 = 64 tile columns, and Recast's budget is tile columns x AverageLayersPerTile.
This map had that at 3, and 64 x 3 is exactly 192. A tile column here has to hold four decks, each
with a floor, the underside of the deck above it, and whatever the dressing pass stood on top --
well past three. So generation ran out of budget partway through and stopped emitting layers, and one of the
holes it left happened to be under the PlayerStart.

The player start was never unreachable. The navmesh simply stopped being built before it got there,
which is the same failure the darkness hunt kept producing: a symptom read as the thing it looked
like rather than the thing it was.

16 rather than something larger: the budget is preallocated, so it costs memory whether or not the
layers exist. Four decks needing floor + ceiling is eight, and eight of headroom for mezzanines and
prop stacks is generous without being a blank cheque. It is also a 5.3x rise from 3, against a
generator that was overflowing rather than merely tight.
"""

import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
WANTED_LAYERS = 16

unreal.EditorLoadingAndSavingUtils.load_map(MAP)
actors = unreal.EditorActorSubsystem().get_all_level_actors()

changed = 0
for actor in actors:
    if not isinstance(actor, unreal.RecastNavMesh):
        continue

    try:
        before = actor.get_editor_property("average_layers_per_tile")
    except Exception as error:
        unreal.log_error("NAVFIX cannot read average_layers_per_tile: {}".format(error))
        unreal.log_error("NAVFIX the property is protected; this needs the ini route instead")
        break

    unreal.log("NAVFIX {} average_layers_per_tile before = {}".format(actor.get_name(), before))

    try:
        actor.set_editor_property("average_layers_per_tile", WANTED_LAYERS)
    except Exception as error:
        unreal.log_error("NAVFIX cannot write average_layers_per_tile: {}".format(error))
        break

    # Read back rather than trust the write. Setting a property that was silently ignored and
    # reporting success is exactly the mistake the emissive pass made earlier in this project.
    after = actor.get_editor_property("average_layers_per_tile")
    unreal.log("NAVFIX {} average_layers_per_tile after  = {}".format(actor.get_name(), after))

    if after != WANTED_LAYERS:
        unreal.log_error("NAVFIX write did not stick: wanted {} got {}".format(WANTED_LAYERS, after))
        break

    changed += 1

if changed:
    unreal.EditorLoadingAndSavingUtils.save_map(unreal.EditorLevelLibrary.get_editor_world(), MAP)
    unreal.log("NAVFIX saved map with {} navmesh actor(s) updated".format(changed))
else:
    unreal.log_error("NAVFIX nothing changed")
