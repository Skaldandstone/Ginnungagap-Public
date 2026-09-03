"""Reports the demo map's navmesh generation limits and the volume they have to cover.

Written because Ginnungagap.Smoke.DemoReachability began failing on "the player start is on
navigable floor" while the log filled with `192 tile limit reached` from AddGeneratedTileLayer.
That is not a reachability bug: it is the generator running out of room and silently leaving holes,
one of which happens to be under the PlayerStart.

Reports rather than fixes, deliberately. Guessing at TileSizeUU and AverageLayersPerTile without
knowing the bounds is how the last five lighting hypotheses went; the numbers are cheap to read.
"""

import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"

unreal.EditorLoadingAndSavingUtils.load_map(MAP)
actors = unreal.EditorActorSubsystem().get_all_level_actors()

for actor in actors:
    if isinstance(actor, unreal.RecastNavMesh):
        unreal.log("NAV recast actor: {}".format(actor.get_name()))
        for prop in ("tile_size_uu", "cell_size", "cell_height", "agent_radius", "agent_height",
                     "agent_max_slope", "agent_max_step_height",
                     "tile_pool_size", "b_fixed_tile_pool_size", "runtime_generation"):
            try:
                unreal.log("NAV   {} = {}".format(prop, actor.get_editor_property(prop)))
            except Exception as error:
                unreal.log("NAV   {} unreadable: {}".format(prop, error))

    if isinstance(actor, unreal.NavMeshBoundsVolume):
        origin, extent = actor.get_actor_bounds(False)
        unreal.log("NAV bounds volume {}: origin={} extent={} (size {} x {} x {})".format(
            actor.get_name(), origin, extent,
            extent.x * 2.0, extent.y * 2.0, extent.z * 2.0))

unreal.log("NAV inspection complete")
