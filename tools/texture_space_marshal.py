"""Gives the Space Marshal oversuit its textures.

SK_SpaceMarshal_Manny was re-imported against SK_Mannequin (tools/rebind_space_marshal_to_manny.py)
with the FBX's legacy Phong material instances, which carry no textures at all, so the crew wore
a white plaster suit. The Fab bundle's texture set (Art/Fab/SpaceMarshal/textures, from
textures.zip on the listing) is imported here and one material per slot is built from it:
BaseColor, Normal, ORM (AO / roughness / metallic in R / G / B) and Emissive where the set has
one; the eyelash is masked by its opacity map.

    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/texture_space_marshal.py -NullRHI
"""
from pathlib import Path
import unreal

MESH = "/Game/Characters/PlayerSuits/PrimaryOversuits/SpaceMarshalManny/SK_SpaceMarshal_Manny"
DEST = "/Game/Characters/PlayerSuits/PrimaryOversuits/SpaceMarshalManny"
TEX = Path(r"C:\Users\James\Documents\Unreal Projects\Ginnungagap\Art\Fab\SpaceMarshal\textures")
# material slot -> texture set prefix
SLOTS = {"Head": "Head_Male", "Eyelash": "Eyelash", "Tongue": "Tongue", "Upper_Teeth": "Upper_Teeth",
         "Lower_Teeth": "Lower_Teeth", "HeadCap": "HeadCap", "SM_Suit": "SM_Suit", "SM_Boots": "SM_Boots",
         "SM_Pouch": "SM_Pouch", "SM_Gloves": "SM_Gloves", "SM_Bags": "SM_Bags", "SM_Helm": "SM_Helm",
         "MS_Visor": "MS_Visor"}
CHANNELS = ["BaseColor", "Normal", "ORM", "Emissive", "Opacity"]

tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary


def import_textures():
    tasks, wanted = [], []
    for prefix in sorted(set(SLOTS.values())):
        for c in CHANNELS:
            f = TEX / f"{prefix}_{c}.png"
            if not f.exists():
                continue
            t = unreal.AssetImportTask()
            t.filename = str(f); t.destination_path = f"{DEST}/Textures"; t.destination_name = f"T_{prefix}_{c}"
            t.automated = True; t.replace_existing = True; t.save = True
            tasks.append(t); wanted.append((prefix, c))
    tools.import_asset_tasks(tasks)
    out = {}
    for prefix, c in wanted:
        tex = unreal.load_asset(f"{DEST}/Textures/T_{prefix}_{c}")
        if not tex:
            print(f"MARSHAL missing after import: {prefix}_{c}"); continue
        if c == "Normal":
            tex.set_editor_property("srgb", False); tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        elif c in ("ORM", "Opacity"):
            tex.set_editor_property("srgb", False); tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
        # The hero suit's textures stay resident: streamed, only the 1x1 mip was ever brought in
        # for this re-imported skeletal mesh and every part rendered as its average colour.
        tex.set_editor_property("never_stream", True)
        unreal.EditorAssetLibrary.save_loaded_asset(tex)
        out[(prefix, c)] = tex
    return out


def make_material(slot, prefix, textures):
    name = f"M_SpaceMarshal_{slot}"
    path = f"{DEST}/Materials"
    if unreal.EditorAssetLibrary.does_asset_exist(f"{path}/{name}"):
        unreal.EditorAssetLibrary.delete_asset(f"{path}/{name}")
    mat = tools.create_asset(name, path, unreal.Material, unreal.MaterialFactoryNew())
    # Worn on a skeletal mesh with facial morphs: without these usages the renderer draws the
    # engine's default grey material in its place, which is the "white plaster suit".
    mat.set_editor_property("used_with_skeletal_mesh", True)
    mat.set_editor_property("used_with_morph_targets", True)
    y = -400
    def sample(c, sampler=None):
        tex = textures.get((prefix, c))
        if not tex:
            return None
        nonlocal y
        node = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -500, y)
        node.set_editor_property("texture", tex)
        if sampler:
            node.set_editor_property("sampler_type", sampler)
        y += 240
        return node
    if n := sample("BaseColor"):
        mel.connect_material_property(n, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    if n := sample("Normal", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL):
        mel.connect_material_property(n, "RGB", unreal.MaterialProperty.MP_NORMAL)
    # Masks-compressed textures must be sampled as Masks: with Linear Color the material fails to
    # compile ("Sampler type is Linear Color, should be Masks") and the default grey is drawn.
    if n := sample("ORM", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS):
        mel.connect_material_property(n, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
        mel.connect_material_property(n, "G", unreal.MaterialProperty.MP_ROUGHNESS)
        mel.connect_material_property(n, "B", unreal.MaterialProperty.MP_METALLIC)
    if n := sample("Emissive"):
        mel.connect_material_property(n, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    if n := sample("Opacity", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS):
        mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
        mat.set_editor_property("two_sided", True)
        mel.connect_material_property(n, "R", unreal.MaterialProperty.MP_OPACITY_MASK)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


textures = import_textures()
print(f"MARSHAL imported {len(textures)} textures")
sk = unreal.load_asset(MESH)
mats = list(sk.get_editor_property("materials"))
assigned = 0
for i, m in enumerate(mats):
    slot = str(m.material_slot_name)
    prefix = SLOTS.get(slot)
    if not prefix:
        print(f"MARSHAL no texture set for slot {slot}"); continue
    mat = make_material(slot, prefix, textures)
    m.material_interface = mat
    mats[i] = m
    assigned += 1
sk.set_editor_property("materials", mats)
unreal.EditorAssetLibrary.save_loaded_asset(sk)
print(f"MARSHAL assigned {assigned}/{len(mats)} slots on {MESH}")
