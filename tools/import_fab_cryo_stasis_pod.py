"""Imports Fab's "Sci-Fi Cryo Stasis Pod - Sleep Chamber" (Wanted199514) from its FBX + PBR set.

One static mesh, one material slot; the glass door is alpha in the base colour, so the material
is translucent with opacity from that alpha, which is what lets the sleeper show through. Source
files live under Art/Fab/CryoStasisPod (ignored); the imported assets are what gets committed.

    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/import_fab_cryo_stasis_pod.py -NullRHI
"""
import unreal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Art" / "Fab" / "CryoStasisPod" / "SciFi_Cryo_Pod_01"
DEST = "/Game/Fab_CryoStasisPod"
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

tex_tasks = []
for name, src in [("BaseColor", "SciFi_Cryo_Pod_01_BaseColor.png"), ("Normal", "SciFi_Cryo_Pod_01_normal.png"),
                  ("Metallic", "SciFi_Cryo_Pod_01_metallic.png"), ("Roughness", "SciFi_Cryo_Pod_01_roughness.png")]:
    t = unreal.AssetImportTask()
    t.filename = str(SRC / "Textures" / src); t.destination_path = f"{DEST}/Textures"; t.destination_name = f"T_CryoStasisPod_{name}"
    t.automated = True; t.replace_existing = True; t.save = True
    tex_tasks.append(t)
tools.import_asset_tasks(tex_tasks)
textures = {}
for name in ["BaseColor", "Normal", "Metallic", "Roughness"]:
    tex = unreal.load_asset(f"{DEST}/Textures/T_CryoStasisPod_{name}")
    if tex and name != "BaseColor":
        tex.set_editor_property("srgb", False)
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP if name == "Normal" else unreal.TextureCompressionSettings.TC_MASKS)
        unreal.EditorAssetLibrary.save_loaded_asset(tex)
    textures[name] = tex

mat_path = f"{DEST}/Materials"
if unreal.EditorAssetLibrary.does_asset_exist(f"{mat_path}/M_CryoStasisPod"):
    unreal.EditorAssetLibrary.delete_asset(f"{mat_path}/M_CryoStasisPod")
mat = tools.create_asset("M_CryoStasisPod", mat_path, unreal.Material, unreal.MaterialFactoryNew())
mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
mat.set_editor_property("two_sided", True)
y = -300
for name, prop, out in [("BaseColor", unreal.MaterialProperty.MP_BASE_COLOR, "RGB"), ("Normal", unreal.MaterialProperty.MP_NORMAL, "RGB"),
                        ("Metallic", unreal.MaterialProperty.MP_METALLIC, "R"), ("Roughness", unreal.MaterialProperty.MP_ROUGHNESS, "R")]:
    node = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -400, y)
    node.set_editor_property("texture", textures[name])
    if name == "Normal":
        node.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    elif name in ("Metallic", "Roughness"):
        node.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)  # masks-compressed: Linear Color fails the compile
    mel.connect_material_property(node, out, prop)
    if name == "BaseColor":
        mel.connect_material_property(node, "A", unreal.MaterialProperty.MP_OPACITY)
    y += 220
mel.recompile_material(mat)
unreal.EditorAssetLibrary.save_loaded_asset(mat)

t = unreal.AssetImportTask()
t.filename = str(SRC / "SciFi_Cryo_Pod_01.fbx"); t.destination_path = f"{DEST}/Meshes"; t.destination_name = "SM_CryoStasisPod"
t.automated = True; t.replace_existing = True; t.save = True
opts = unreal.FbxImportUI()
opts.import_mesh = True; opts.import_as_skeletal = False; opts.import_materials = False; opts.import_textures = False; opts.import_animations = False
opts.static_mesh_import_data.combine_meshes = True
opts.static_mesh_import_data.auto_generate_collision = True
t.options = opts
tools.import_asset_tasks([t])
mesh = unreal.load_asset(f"{DEST}/Meshes/SM_CryoStasisPod")
assert mesh, "pod import failed"
for i in range(mesh.get_num_sections(0)):
    mesh.set_material(i, mat)
unreal.EditorAssetLibrary.save_loaded_asset(mesh)
b = mesh.get_bounding_box(); mn, mx = b.min, b.max
print(f"CRYOPOD SM_CryoStasisPod: X {mn.x:.1f}..{mx.x:.1f} Y {mn.y:.1f}..{mx.y:.1f} Z {mn.z:.1f}..{mx.z:.1f} sections={mesh.get_num_sections(0)}")
