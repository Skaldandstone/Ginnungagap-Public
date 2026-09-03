"""Prints the placed workshop bench's actual GrantedItems, to settle 4-vs-2.

The constructor adds exactly two (Sealant, Coolant) and a NewObject unit test confirms two. The
instance placed in L_QuickDemo_FourDeck reports four in live PIE. Neither the ship builder nor the
loadout touches this array. Ground truth from the placed actor rather than more theorising.
"""
import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    unreal.log_error("DIAG could not load {}".format(MAP))
else:
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    benches = [a for a in actors if a.get_class().get_name() == "QuickDemoWorkshopBench"]
    unreal.log("DIAG benches placed: {}".format(len(benches)))
    for bench in benches:
        items = bench.get_editor_property("granted_items")
        names = [i.get_name() if i else "NULL" for i in items]
        wc = bench.get_editor_property("granted_weapon_class")
        unreal.log("DIAG {} items={} {}".format(bench.get_name(), len(names), names))
        unreal.log("DIAG {} weapon_class={}".format(bench.get_name(), wc.get_name() if wc else "NONE"))
