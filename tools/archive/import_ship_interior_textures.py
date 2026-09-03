"""Import the generated ship textures and build their Unreal material assets."""

import os
import unreal


CONTENT_DIR = unreal.SystemLibrary.get_project_content_directory()
TEXTURE_SOURCE_DIR = os.path.join(CONTENT_DIR, "Assets", "Textures")
TEXTURE_PACKAGE = "/Game/Assets/Textures"
MATERIAL_PACKAGE = "/Game/Assets/Materials"

ASSETS = (
    ("T_ShipBulkhead_WornSteel.png", "T_ShipBulkhead_WornSteel", "M_ShipBulkhead_WornSteel", 0.62, 0.48, 3.0, False),
    ("T_ShipDeck_NonSlip.png", "T_ShipDeck_NonSlip", "M_ShipDeck_NonSlip", 0.78, 0.18, 3.5, False),
    ("T_ShipUtility_Hazard.png", "T_ShipUtility_Hazard", "M_ShipUtility_Hazard", 0.68, 0.42, 2.5, False),
    ("T_SpaceSuit_Damaged.png", "T_SpaceSuit_Damaged", "M_SpaceSuit_Damaged", 0.72, 0.22, 1.8, False),
    ("T_Bloom_AmethystCorruption.png", "T_Bloom_AmethystCorruption", "M_Bloom_AmethystCorruption", 0.38, 0.12, 2.2, True),
)


def import_texture(filename, asset_name):
    destination = f"{TEXTURE_PACKAGE}/{asset_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(destination):
        return unreal.load_asset(destination)

    task = unreal.AssetImportTask()
    task.set_editor_property("filename", os.path.join(TEXTURE_SOURCE_DIR, filename))
    task.set_editor_property("destination_path", TEXTURE_PACKAGE)
    task.set_editor_property("destination_name", asset_name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", False)
    task.set_editor_property("save", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.load_asset(destination)
    if not texture:
        raise RuntimeError(f"Texture import failed: {filename}")
    unreal.EditorAssetLibrary.save_loaded_asset(texture)
    return texture


def build_material(texture, material_name, roughness, metallic, tiling, emissive):
    destination = f"{MATERIAL_PACKAGE}/{material_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(destination):
        unreal.EditorAssetLibrary.delete_asset(destination)

    factory = unreal.MaterialFactoryNew()
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        material_name, MATERIAL_PACKAGE, unreal.Material, factory
    )
    if not material:
        raise RuntimeError(f"Material creation failed: {material_name}")
    if material_name in ("M_SpaceSuit_Damaged", "M_Bloom_AmethystCorruption"):
        material.set_editor_property("used_with_skeletal_mesh", True)

    uv = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureCoordinate, -650, 0
    )
    uv.set_editor_property("u_tiling", tiling)
    uv.set_editor_property("v_tiling", tiling)

    sample = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -380, 0
    )
    sample.set_editor_property("texture", texture)
    unreal.MaterialEditingLibrary.connect_material_expressions(uv, "", sample, "UVs")
    unreal.MaterialEditingLibrary.connect_material_property(
        sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR
    )
    if emissive:
        unreal.MaterialEditingLibrary.connect_material_property(
            sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )

    rough = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -300, 220
    )
    rough.set_editor_property("r", roughness)
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS
    )

    metal = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -300, 320
    )
    metal.set_editor_property("r", metallic)
    unreal.MaterialEditingLibrary.connect_material_property(
        metal, "", unreal.MaterialProperty.MP_METALLIC
    )

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


for source_name, texture_name, material_name, roughness, metallic, tiling, emissive in ASSETS:
    imported_texture = import_texture(source_name, texture_name)
    build_material(imported_texture, material_name, roughness, metallic, tiling, emissive)

unreal.log("Imported military corvette textures and built three ship interior materials.")
