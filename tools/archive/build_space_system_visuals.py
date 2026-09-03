"""Import the original cosmic panorama and build reusable procedural-system materials."""
from pathlib import Path
import unreal

ROOT = "/Game/Assets/SpaceSystems"
MAT_ROOT = ROOT + "/Materials"
SOURCE = Path(unreal.SystemLibrary.get_project_directory()) / "Content/Assets/SpaceSystems/Source/T_SpaceSky_CosmicRift.png"


def make_material(name, color, emissive=0.0, roughness=0.65, two_sided=False):
    path = f"{MAT_ROOT}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MAT_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("two_sided", two_sided)
    base = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -420, -80)
    base.set_editor_property("parameter_name", "BodyColor")
    base.set_editor_property("default_value", unreal.LinearColor(*color, 1.0))
    rough = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -420, 100)
    rough.set_editor_property("r", roughness)
    unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    if emissive > 0.0:
        strength = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -220, -180)
        strength.set_editor_property("r", emissive)
        multiply = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply, 0, -100)
        unreal.MaterialEditingLibrary.connect_material_expressions(base, "", multiply, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(strength, "", multiply, "B")
        unreal.MaterialEditingLibrary.connect_material_property(multiply, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def import_sky_texture():
    destination = ROOT + "/Textures"
    asset_path = destination + "/T_SpaceSky_CosmicRift"
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return unreal.EditorAssetLibrary.load_asset(asset_path)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(SOURCE))
    task.set_editor_property("destination_path", destination)
    task.set_editor_property("destination_name", "T_SpaceSky_CosmicRift")
    task.set_editor_property("automated", True)
    task.set_editor_property("save", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return unreal.EditorAssetLibrary.load_asset(asset_path)


def make_sky_material(texture):
    path = MAT_ROOT + "/M_SpaceSky_CosmicRift"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_SpaceSky_CosmicRift", MAT_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("two_sided", True)
    sample = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -360, -40)
    sample.set_editor_property("texture", texture)
    strength = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -160, 80)
    strength.set_editor_property("r", 0.35)
    multiply = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply, 20, -20)
    unreal.MaterialEditingLibrary.connect_material_expressions(sample, "RGB", multiply, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(strength, "", multiply, "B")
    unreal.MaterialEditingLibrary.connect_material_property(multiply, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)


def make_additive_atmosphere():
    path = MAT_ROOT + "/M_Atmosphere_Additive"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_Atmosphere_Additive", MAT_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("two_sided", True)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    color = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -500, -120)
    color.set_editor_property("parameter_name", "AtmosphereColor")
    color.set_editor_property("default_value", unreal.LinearColor(0.04, 0.38, 1.0, 1.0))
    fresnel = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionFresnel, -500, 40)
    strength = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -500, 180)
    strength.set_editor_property("parameter_name", "GlowStrength")
    strength.set_editor_property("default_value", 5.0)
    glow = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply, -220, -80)
    final = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionMultiply, 0, -80)
    unreal.MaterialEditingLibrary.connect_material_expressions(color, "", glow, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(fresnel, "", glow, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(glow, "", final, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(strength, "", final, "B")
    unreal.MaterialEditingLibrary.connect_material_property(final, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(fresnel, "", unreal.MaterialProperty.MP_OPACITY)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


texture = import_sky_texture()
make_sky_material(texture)
make_material("M_Star_Gold", (1.0, 0.32, 0.035), 24.0, 0.1)
make_material("M_Star_Blue", (0.08, 0.42, 1.0), 30.0, 0.1)
make_material("M_Star_Violet", (0.42, 0.08, 1.0), 26.0, 0.1)
make_material("M_Planet_Ocean", (0.015, 0.12, 0.26), 0.1, 0.48)
make_material("M_Planet_Volcanic", (0.26, 0.025, 0.008), 1.4, 0.78)
make_material("M_Planet_Ice", (0.18, 0.42, 0.56), 0.25, 0.3)
make_material("M_Planet_GasGiant", (0.42, 0.16, 0.055), 0.18, 0.52)
make_material("M_Phenomenon_Anomaly", (0.2, 0.015, 0.65), 18.0, 0.15, True)
make_additive_atmosphere()
unreal.EditorAssetLibrary.save_directory(ROOT)
unreal.log("Space-system visual library complete.")
