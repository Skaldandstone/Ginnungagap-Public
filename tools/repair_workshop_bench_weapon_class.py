"""Repairs the placed workshop bench's GrantedWeaponClass, which the map saved as the bare base.

The constructor sets GrantedWeaponClass to BP_Weapon_PressureBottleFastenerTool_C, but a placed
instance's saved properties replace constructor defaults outright, and this map's bench was saved
with the bare AShipboardWeapon base -- so the constructor fix never reached it, and the bench would
grant an inert base weapon. A ship regen would spawn a fresh bench and get this right on its own;
this repairs the one saved instance without a regen.

Items are left alone: the four saved there are distinct and legitimate, not duplicates.
"""
import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
TOOL_CLASS = "/Game/Assets/Gameplay/EarlyProjectileWeapons/Blueprints/BP_Weapon_PressureBottleFastenerTool.BP_Weapon_PressureBottleFastenerTool_C"
TOOL_DEF = "/Game/Assets/Gameplay/EarlyProjectileWeapons/Data/Weapons/DA_Weapon_PressureBottleFastenerTool"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    unreal.log_error("REPAIR could not load {}".format(MAP))
else:
    tool_class = unreal.load_class(None, TOOL_CLASS)
    tool_def = unreal.load_asset(TOOL_DEF)
    if not tool_class or not tool_def:
        unreal.log_error("REPAIR missing class={} def={}".format(bool(tool_class), bool(tool_def)))
    else:
        actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
        benches = [a for a in actors if a.get_class().get_name() == "QuickDemoWorkshopBench"]
        for bench in benches:
            before = bench.get_editor_property("granted_weapon_class")
            bench.set_editor_property("granted_weapon_class", tool_class)
            bench.set_editor_property("granted_weapon_definition", tool_def)
            after_c = bench.get_editor_property("granted_weapon_class")
            after_d = bench.get_editor_property("granted_weapon_definition")
            unreal.log("REPAIR {} class {} -> {}  def={}".format(
                bench.get_name(),
                before.get_name() if before else "NONE",
                after_c.get_name() if after_c else "NONE",
                after_d.get_name() if after_d else "NONE"))
        levels.save_current_level()
        unreal.log("REPAIR saved ({} bench)".format(len(benches)))
