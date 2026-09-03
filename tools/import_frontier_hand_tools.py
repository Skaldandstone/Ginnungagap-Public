"""Imports the per-tool FBX files made by tools/split_frontier_toolbox_fbx.py as single static
meshes, gives them the toolbox material, points the demo's hand tool definition at the power
tool, and removes the 274-part import of the whole pack that the first pass left behind.

Run after tools/import_frontier_engineers_toolbox.py (textures and materials) and the Blender
split.

    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/import_frontier_hand_tools.py -NullRHI
"""
import unreal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPLIT = ROOT / "Art" / "Fab" / "Frontier_EngineersToolbox" / "split"
DEST = "/Game/Frontier_EngineersToolbox"
TOOLS = ["Powertool", "PlasmaCutter", "Scanner", "Pipewrench"]
DEFINITION = "/Game/Assets/Gameplay/EarlyProjectileWeapons/Data/Weapons/DA_Weapon_PressureBottleFastenerTool"

tools = unreal.AssetToolsHelpers.get_asset_tools()
material = unreal.load_asset(f"{DEST}/Materials/M_FrontierTools_1")
assert material, "run import_frontier_engineers_toolbox.py first"

tasks = []
for name in TOOLS:
    t = unreal.AssetImportTask()
    t.filename = str(SPLIT / f"SM_Frontier_{name}.fbx")
    t.destination_path = f"{DEST}/Tools"
    t.destination_name = f"SM_Frontier_{name}"
    t.automated = True; t.replace_existing = True; t.save = True
    opts = unreal.FbxImportUI()
    opts.import_mesh = True; opts.import_as_skeletal = False; opts.import_materials = False; opts.import_textures = False
    opts.import_animations = False
    opts.static_mesh_import_data.combine_meshes = True
    opts.static_mesh_import_data.auto_generate_collision = True
    t.options = opts
    tasks.append(t)
tools.import_asset_tasks(tasks)

bounds = {}
for name in TOOLS:
    mesh = unreal.load_asset(f"{DEST}/Tools/SM_Frontier_{name}")
    if not mesh:
        print(f"HANDTOOL {name}: import failed")
        continue
    for i in range(mesh.get_num_sections(0)):
        mesh.set_material(i, material)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    b = mesh.get_bounding_box(); mn, mx = b.min, b.max
    bounds[name] = (mn, mx)
    print(f"HANDTOOL SM_Frontier_{name}: X {mn.x:.1f}..{mx.x:.1f} Y {mn.y:.1f}..{mx.y:.1f} Z {mn.z:.1f}..{mx.z:.1f}")

# The pack's business ends sit at -X in the file's frame (the power tool's chuck and bits were at
# X -32..-19 against a body at -20..10), so the tool is turned to face +X, the mount's forward.
definition = unreal.load_asset(DEFINITION)
power = unreal.load_asset(f"{DEST}/Tools/SM_Frontier_Powertool")
if definition and power:
    definition.set_editor_property("weapon_mesh", power)
    xf = unreal.Transform()
    xf.translation = unreal.Vector(0.0, 0.0, 0.0)
    xf.rotation = unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0).quaternion()
    xf.scale3d = unreal.Vector(1.0, 1.0, 1.0)
    definition.set_editor_property("weapon_mesh_transform", xf)
    definition.set_editor_property("muzzle_offset", unreal.Vector(24.0, 0.0, 4.0))
    print("HANDTOOL definition saved:", unreal.EditorAssetLibrary.save_loaded_asset(definition))

# The whole-pack import: one asset per part, 274 of them. Not needed once the tools exist.
if unreal.EditorAssetLibrary.does_directory_exist(f"{DEST}/Meshes"):
    print("HANDTOOL removed part meshes:", unreal.EditorAssetLibrary.delete_directory(f"{DEST}/Meshes"))
