"""Prints how the hand-held tools sit on the weapon actor: mesh bounds and the transforms applied.

The mount puts a weapon actor at (50, 22, -26) from the first-person camera with zero rotation,
so the actor's +X is the direction the player looks. A tool whose long axis or muzzle runs the
other way points back at the camera -- which is what the first demo recordings showed. This
reports, for the captive bolt driver's mesh and the fastener tool's definition, where the mesh
extends along each axis so the correction can be made where the mesh is assigned.

    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/inspect_held_tool_orientation.py -NullRHI
"""
import unreal

MESHES = {
    "captive bolt driver (ACaptiveBoltDriver ctor)": "/Game/Assets/Models/GameplayItems/SM_Weapon_RivetRifle",
}
DEFINITION = "/Game/Assets/Gameplay/EarlyProjectileWeapons/Data/Weapons/DA_Weapon_PressureBottleFastenerTool"
BLUEPRINT = "/Game/Assets/Gameplay/EarlyProjectileWeapons/Blueprints/BP_Weapon_PressureBottleFastenerTool"


def describe_mesh(label, mesh):
    if not mesh:
        print(f"  {label}: <missing>")
        return
    box = mesh.get_bounding_box()
    mn, mx = box.min, box.max
    print(f"  {label}: {mesh.get_path_name()}")
    print(f"    X {mn.x:7.1f} .. {mx.x:7.1f}   Y {mn.y:7.1f} .. {mx.y:7.1f}   Z {mn.z:7.1f} .. {mx.z:7.1f}")
    longest = max(("X", mx.x - mn.x), ("Y", mx.y - mn.y), ("Z", mx.z - mn.z), key=lambda t: t[1])
    print(f"    longest axis {longest[0]} ({longest[1]:.1f} cm); +X extent {mx.x:.1f}, -X extent {-mn.x:.1f}")


for label, path in MESHES.items():
    describe_mesh(label, unreal.load_asset(path))

definition = unreal.load_asset(DEFINITION)
if definition:
    print(f"definition {DEFINITION}")
    mesh = definition.get_editor_property("weapon_mesh")
    describe_mesh("fastener tool WeaponMesh", mesh)
    xf = definition.get_editor_property("weapon_mesh_transform")
    print(f"  WeaponMeshTransform: loc={xf.translation} rot={xf.rotation.rotator()} scale={xf.scale3d}")
    print(f"  MuzzleOffset: {definition.get_editor_property('muzzle_offset')}")
else:
    print("definition missing")

bp = unreal.load_asset(BLUEPRINT)
if bp:
    gen = bp.generated_class()
    cdo = unreal.get_default_object(gen)
    print(f"blueprint {BLUEPRINT} class {gen.get_name()}")
    for comp in unreal.get_default_object(gen).get_components_by_class(unreal.StaticMeshComponent) if hasattr(cdo, "get_components_by_class") else []:
        print(f"  component {comp.get_name()} mesh={comp.static_mesh} rel_rot={comp.relative_rotation} rel_loc={comp.relative_location} scale={comp.relative_scale3d}")
else:
    print("blueprint missing")
