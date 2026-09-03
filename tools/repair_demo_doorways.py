"""Opens every doorway in the placed demo ship, without regenerating it.

The doorway audit found 0 of 96 passable, sealed by two things this repairs in place:

1. The production bulkhead Blueprint's four solid slabs -- FrameMesh, LeftPanel, RightPanel and
   the origin-parked VisualMesh -- on all 96 doors and 16 airlocks. Neutralised exactly as the
   generator now does for fresh spawns (see neutralise_bulkhead_slabs there).

2. Concept props the generator spawns with collision=False today but that carry full collision
   on this map, which predates that flag: the corridor ribs standing in every doorway, floor
   insets and stripes, wall panels and kickplates.

The dressing-pass wall panels across the gaps are not touched here; re-running the two passes
recreates them without collision and, since tonight, split around the gaps.

use_default_collision is switched off before any collision change. With it on -- and it is on for
every StaticMeshActor the generator and the dressers spawn -- the component re-derives its collision
from the mesh asset on every load, so a NO_COLLISION set in the editor silently reverts on reload.
That is why the generator's collision=False never held across a save, why this script's first two
runs reported success and changed nothing, and why the dressers' "visual only" panels were solid.
The door slabs are Blueprint components with the flag off, which is why only they persisted.
"""
import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
SLABS = ("FrameMesh", "LeftPanel", "RightPanel", "VisualMesh")
CONCEPT_LABELS = ("ConceptCorridorRib", "ConceptCorridorFloorInset", "ConceptCorridorFloorStripe",
                  "ConceptRoomFloorInset", "ConceptRoomFloorStripe", "ConceptWallPanel", "ConceptKickplate")


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(MAP):
        unreal.log_error("REPAIR could not load {}".format(MAP))
        return
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()

    doors = slabs = 0
    for actor in actors:
        if "Bulkhead" not in actor.get_class().get_name() and actor.get_class().get_name() != "BulkheadDoor":
            continue
        doors += 1
        actor.modify(True)
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            if component.get_name() in SLABS:
                component.modify(True)
                component.set_editor_property("use_default_collision", False)
                component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                component.set_visibility(False)
                slabs += 1
    unreal.log("REPAIR bulkhead actors {} slabs neutralised {}".format(doors, slabs))

    props = 0
    for actor in actors:
        label = actor.get_actor_label()
        by_label = any(label.startswith(prefix) or ("_" + prefix) in label for prefix in CONCEPT_LABELS)
        by_tag = "ConceptDressing" in [str(t) for t in actor.tags]
        if not by_label and not by_tag:
            continue
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            if component.get_collision_enabled() != unreal.CollisionEnabled.NO_COLLISION:
                actor.modify(True)
                component.modify(True)
                component.set_editor_property("use_default_collision", False)
                component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                props += 1
    unreal.log("REPAIR concept props set to no collision {}".format(props))

    # Collision changed, so the level's saved navmesh is now stale. A headless session cannot
    # rebuild it; the demo director rebuilds from live geometry at level start instead.
    levels.save_current_level()
    unreal.log("REPAIR saved")


main()
