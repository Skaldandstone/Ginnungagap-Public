"""Prints the bounds of every static mesh in the Modular Scifi Mechanic Base kit, so a generator
can place them from numbers.  UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/measure_mechanic_kit.py -NullRHI"""
import unreal
reg = unreal.AssetRegistryHelpers.get_asset_registry()
assets = reg.get_assets_by_path("/Game/Modular_Scifi_Mechanic_Base/Mesh/SM", recursive=True)
for a in sorted(assets, key=lambda x: str(x.package_name)):
    if str(a.asset_class_path.asset_name) != "StaticMesh": continue
    m = a.get_asset()
    b = m.get_bounding_box(); mn, mx = b.min, b.max
    print(f"KIT {str(a.package_name).split('/Mesh/SM/')[-1]}: X {mn.x:.0f}..{mx.x:.0f} Y {mn.y:.0f}..{mx.y:.0f} Z {mn.z:.0f}..{mx.z:.0f}")
