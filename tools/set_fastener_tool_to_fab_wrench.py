"""Points the demo's hand tool definition at the Fab engineering wrench, oriented for the hand.

The pressure-bottle fastener tool was a pistol-shaped placeholder mesh modelled facing the camera.
The demo's workshop bench grants DA_Weapon_PressureBottleFastenerTool, whose WeaponMesh and
WeaponMeshTransform the weapon actor applies in RefreshFromDefinition. SM_Wrench from
ModSci_EngiProps measures 23 cm along X, flat in Z; rolled upright, pitched a little down,
scaled 1.6x it reads as a heavy wrench held out in front, pointing where the player looks.

    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/set_fastener_tool_to_fab_wrench.py -NullRHI
"""
import unreal

DEFINITION = "/Game/Assets/Gameplay/EarlyProjectileWeapons/Data/Weapons/DA_Weapon_PressureBottleFastenerTool"
WRENCH = "/Game/ModSci_EngiProps/Meshes/SM_Wrench"

definition = unreal.load_asset(DEFINITION)
wrench = unreal.load_asset(WRENCH)
assert definition and wrench, "definition or wrench missing"
definition.set_editor_property("weapon_mesh", wrench)
xf = unreal.Transform()
xf.translation = unreal.Vector(4.0, 0.0, 0.0)
xf.rotation = unreal.Rotator(pitch=-12.0, yaw=0.0, roll=90.0).quaternion()
xf.scale3d = unreal.Vector(1.6, 1.6, 1.6)
definition.set_editor_property("weapon_mesh_transform", xf)
definition.set_editor_property("muzzle_offset", unreal.Vector(22.0, 0.0, 0.0))
saved = unreal.EditorAssetLibrary.save_loaded_asset(definition)
print(f"WRENCH saved={saved} mesh={definition.get_editor_property('weapon_mesh').get_path_name()}")
