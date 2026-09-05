"""Imports Fab's "Sci-fi New Door" (CGGame) from its FBX + PBR textures.

The listing ships no Unreal build: an FBX with three parts (a portal frame and a left and a
right leaf, prepared for a 10x10 grid) and two PBR sets (Portal, Door) as PNG. They come in as
three static meshes under /Game/Fab_SciFiDoor/Meshes with one material per set, so the production
bulkhead can wear them as its frame and leaves. Source files live under Art/Fab/SciFiDoor
(ignored by git; the imported assets are what gets committed).

    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/import_fab_scifi_door.py -NullRHI
"""
import unreal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "Art" / "Fab" / "SciFiDoor"
FBX = SRC / "Sci-fi Game Door Free 01.fbx"
TEX = SRC / "Textures Sci-fi Game Door Free 01"
DEST = "/Game/Fab_SciFiDoor"
SETS = ["Door", "Portal"]
CHANNELS = {"Base_color": "BaseColor", "Normal_OpenGL": "Normal", "Metallic": "Metallic", "Roughness": "Roughness", "Mixed_AO": "AO"}

tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary


def import_textures():
    tasks = []
    for s in SETS:
        for src, c in CHANNELS.items():
            t = unreal.AssetImportTask()
            t.filename = str(TEX / f"{s}_{src}.png")
            t.destination_path = f"{DEST}/Textures"
            t.destination_name = f"T_{s}_{c}"
            t.automated = True; t.replace_existing = True; t.save = True
            tasks.append(t)
    tools.import_asset_tasks(tasks)
    out = {}
    for s in SETS:
        for c in CHANNELS.values():
            tex = unreal.load_asset(f"{DEST}/Textures/T_{s}_{c}")
            if tex:
                if c == "Normal":
                    tex.set_editor_property("srgb", False)
                    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
                    # OpenGL-style normal map: green points the other way from what Unreal expects.
                    tex.set_editor_property("flip_green_channel", True)
                elif c in ("Metallic", "Roughness", "AO"):
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
                    ("AO", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)]:
        tex = textures.get(c)
        if not tex:
            continue
        node = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -400, y)
        node.set_editor_property("texture", tex)
        if c == "Normal":
            node.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        elif c in ("Metallic", "Roughness", "AO"):
            node.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
        mel.connect_material_property(node, "R" if c in ("Metallic", "Roughness", "AO") else "RGB", prop)
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
mats = {s: make_material(f"M_SciFiDoor_{s}", {c: textures[(s, c)] for c in CHANNELS.values()}) for s in SETS}
paths = import_meshes()
print(f"SCIFIDOOR imported {len(paths)} mesh(es)")
for p in paths:
    mesh = unreal.load_asset(p)
    if not isinstance(mesh, unreal.StaticMesh):
        continue
    n = mesh.get_name().lower()
    # The FBX names its frame "Prtal_Door" (sic).
    mat = mats["Portal"] if "portal" in n or "prtal" in n or "frame" in n or "arch" in n else mats["Door"]
    for i in range(mesh.get_num_sections(0)):
        mesh.set_material(i, mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    b = mesh.get_bounding_box(); mn, mx = b.min, b.max
    print(f"SCIFIDOOR {mesh.get_name()}: X {mn.x:.1f}..{mx.x:.1f} Y {mn.y:.1f}..{mx.y:.1f} Z {mn.z:.1f}..{mx.z:.1f} sections={mesh.get_num_sections(0)} material={mat.get_name()}")
