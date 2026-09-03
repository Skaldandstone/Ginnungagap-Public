"""Sets the demo navmesh's agent radius to cover the player capsule.

The RecastNavMesh eroded for a 35 cm agent while the player character's capsule is 42 cm, so the
mesh admitted gaps the body cannot pass: the walkthrough pawn wedged against the end of a hatch
rail at the top of the deck ramp, on a path the mesh called valid. 44 was not enough either --
erosion is quantised to the 19 cm cell, so a nominal 44 can leave the mesh edge ~25 cm from a
rail, and the path still hugged the corner. 60 covers the capsule plus a cell of quantisation;
the generator's 250 cm doorways (130 after erosion), 280 cm ramp (160) and 360 cm corridors (240)
keep ample width.
"""
import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
RADIUS = 60.0

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    unreal.log_error("NAVRADIUS could not load {}".format(MAP))
else:
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    for actor in actors:
        if actor.get_class().get_name() != "RecastNavMesh":
            continue
        before = actor.get_editor_property("agent_radius")
        actor.modify(True)
        actor.set_editor_property("agent_radius", RADIUS)
        unreal.log("NAVRADIUS {} agent_radius {} -> {}".format(actor.get_name(), before, actor.get_editor_property("agent_radius")))
    unreal.log("NAVRADIUS saved={}".format(levels.save_current_level()))
