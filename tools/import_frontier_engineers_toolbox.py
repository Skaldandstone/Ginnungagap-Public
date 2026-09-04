"""Imports Fab's "Frontier - Engineer's Toolbox" (Martin Ljungblad) from its FBX + PBR textures.

The listing ships no Unreal build, only FBX/OBJ with a Standard PBR texture set, so this brings
the tools in as separate static meshes under /Game/Frontier_EngineersToolbox with one material
per texture set (FrontierTools_1 for the tools, FrontierTools_Toolbox1 for the toolbox), wired
BaseColor / Normal / Metallic / Roughness / Emissive. Source files live under
Art/Fab/Frontier_EngineersToolbox (ignored by git; the imported assets are what gets committed).

    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/import_frontier_engineers_toolbox.py -NullRHI
"""
import unreal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Art" / "Fab" / "Frontier_EngineersToolbox"
FBX = SRC / "frontier_engineerstoolbox_fbx.fbx"
TEX = SRC / "textures" / "Textures" / "Standard PBR Static"
DEST = "/Game/Frontier_EngineersToolbox"
SETS = ["FrontierTools_1", "FrontierTools_Toolbox1"]
CHANNELS = ["BaseColor", "Normal", "Metallic", "Roughness", "Emissive"]

tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary


def import_textures():
    tasks = []
    for s in SETS:
        for c in CHANNELS:
            t = unreal.AssetImportTask()
            t.filename = str(TEX / f"{s}_{c}.png")
            t.destination_path = f"{DEST}/Textures"
            t.destination_name = f"T_{s}_{c}"
            t.automated = True; t.replace_existing = True; t.save = True
            tasks.append(t)
    tools.import_asset_tasks(tasks)
    out = {}
    for s in SETS:
        for c in CHANNELS:
            tex = unreal.load_asset(f"{DEST}/Textures/T_{s}_{c}")
            if tex:
                if c == "Normal":
                    tex.set_editor_property("srgb", False)
                    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
                elif c in ("Metallic", "Roughness"):
                    tex.set_editor_property("srgb", False)
                    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
                unreal.EditorAssetLibrary.save_loaded_asset(tex)
            out[(s, c)] = tex
    return out


def make_material(name, textures):
    path = f"{DEST}/Materials"
    if unreal.EditorAssetLibrary.does_asset_exist(f"{path}/{name}"):
        unreal.EditorAssetLibrary.delete_asset(f"{path}/{name}")
    mat = tools.create_asset(name, path, unreal.Material, unreal.MaterialFactoryNew())
    y = -300
    for c, prop in [("BaseColor", unreal.MaterialProperty.MP_BASE_COLOR), ("Normal", unreal.MaterialProperty.MP_NORMAL),
                    ("Metallic", unreal.MaterialProperty.MP_METALLIC), ("Roughness", unreal.MaterialProperty.MP_ROUGHNESS),
                    ("Emissive", unreal.MaterialProperty.MP_EMISSIVE_COLOR)]:
        tex = textures.get(c)
        if not tex:
            continue
        node = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -400, y)
        node.set_editor_property("texture", tex)
        if c == "Normal":
            node.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        elif c in ("Metallic", "Roughness"):
            # Masks-compressed textures sample as Masks; Linear Color fails the compile.
            node.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
        mel.connect_material_property(node, "RGB" if c != "Metallic" and c != "Roughness" else "R", prop)
        y += 220
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def import_meshes():
    t = unreal.AssetImportTask()
    t.filename = str(FBX)
    t.destination_path = f"{DEST}/Meshes"
    t.automated = True; t.replace_existing = True; t.save = True
    opts = unreal.FbxImportUI()
    opts.import_mesh = True; opts.import_as_skeletal = False; opts.import_materials = False; opts.import_textures = False
    opts.import_animations = False
    opts.static_mesh_import_data.combine_meshes = False
    opts.static_mesh_import_data.generate_lightmap_u_vs = False
    opts.static_mesh_import_data.auto_generate_collision = True
    opts.static_mesh_import_data.import_uniform_scale = 1.0
    t.options = opts
    tools.import_asset_tasks([t])
    return list(t.imported_object_paths)


textures = import_textures()
mats = {s: make_material(f"M_{s}", {c: textures[(s, c)] for c in CHANNELS}) for s in SETS}
paths = import_meshes()
print(f"TOOLBOX imported {len(paths)} mesh(es)")
for p in paths:
    mesh = unreal.load_asset(p)
    if not isinstance(mesh, unreal.StaticMesh):
        continue
    b = mesh.get_bounding_box(); mn, mx = b.min, b.max
    n = mesh.get_name().lower()
    mat = mats["FrontierTools_Toolbox1"] if "toolbox" in n else mats["FrontierTools_1"]
    for i in range(mesh.get_num_sections(0)):
        mesh.set_material(i, mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    print(f"TOOLBOX {mesh.get_name()}: X {mn.x:.1f}..{mx.x:.1f} Y {mn.y:.1f}..{mx.y:.1f} Z {mn.z:.1f}..{mx.z:.1f} sections={mesh.get_num_sections(0)}")
