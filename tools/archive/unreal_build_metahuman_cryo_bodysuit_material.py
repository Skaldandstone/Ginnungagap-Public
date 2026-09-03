"""Build the fitted MetaHuman cryo-bodysuit surface used below wearable layers."""

import json
from pathlib import Path

import unreal


ROOT = "/Game/Characters/Player/Undersuit/MetaHuman"
MASTER_NAME = "M_MH_CryoBodysuit"
INSTANCE_NAME = "MI_MH_CryoBodysuit_Standard"
asset_tools = unreal.AssetToolsHelpers.get_asset_tools()

unreal.EditorAssetLibrary.make_directory(ROOT)

for asset_path in (f"{ROOT}/{INSTANCE_NAME}", f"{ROOT}/{MASTER_NAME}"):
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        unreal.EditorAssetLibrary.delete_asset(asset_path)

material = asset_tools.create_asset(
    MASTER_NAME, ROOT, unreal.Material, unreal.MaterialFactoryNew()
)
unreal.MaterialEditingLibrary.set_material_usage(
    material, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH
)

base = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionVectorParameter, -720, -180
)
base.set_editor_property("parameter_name", "SuitColor")
base.set_editor_property("default_value", unreal.LinearColor(0.018, 0.045, 0.052, 1.0))

fiber = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionVectorParameter, -720, -70
)
fiber.set_editor_property("parameter_name", "FiberColor")
fiber.set_editor_property("default_value", unreal.LinearColor(0.055, 0.105, 0.112, 1.0))

uv = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionTextureCoordinate, -720, 80
)
noise = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionNoise, -500, 80
)
noise.set_editor_property("scale", 72.0)
noise.set_editor_property("quality", 2)
noise.set_editor_property("levels", 3)
unreal.MaterialEditingLibrary.connect_material_expressions(uv, "", noise, "Position")

fiber_amount = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionScalarParameter, -500, 190
)
fiber_amount.set_editor_property("parameter_name", "FiberAmount")
fiber_amount.set_editor_property("default_value", 0.19)
fiber_mask = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionMultiply, -280, 100
)
unreal.MaterialEditingLibrary.connect_material_expressions(noise, "", fiber_mask, "A")
unreal.MaterialEditingLibrary.connect_material_expressions(fiber_amount, "", fiber_mask, "B")

surface = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionLinearInterpolate, -50, -120
)
unreal.MaterialEditingLibrary.connect_material_expressions(base, "", surface, "A")
unreal.MaterialEditingLibrary.connect_material_expressions(fiber, "", surface, "B")
unreal.MaterialEditingLibrary.connect_material_expressions(fiber_mask, "", surface, "Alpha")

edge_color = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionVectorParameter, -260, -270
)
edge_color.set_editor_property("parameter_name", "EdgeColor")
edge_color.set_editor_property("default_value", unreal.LinearColor(0.025, 0.12, 0.135, 1.0))
fresnel = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionFresnel, -260, -190
)
edge_strength = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionScalarParameter, -50, -260
)
edge_strength.set_editor_property("parameter_name", "EdgeStrength")
edge_strength.set_editor_property("default_value", 0.12)
edge_mask = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionMultiply, 160, -210
)
edge_tint = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionMultiply, 360, -190
)
final_color = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionAdd, 570, -100
)
unreal.MaterialEditingLibrary.connect_material_expressions(fresnel, "", edge_mask, "A")
unreal.MaterialEditingLibrary.connect_material_expressions(edge_strength, "", edge_mask, "B")
unreal.MaterialEditingLibrary.connect_material_expressions(edge_color, "", edge_tint, "A")
unreal.MaterialEditingLibrary.connect_material_expressions(edge_mask, "", edge_tint, "B")
unreal.MaterialEditingLibrary.connect_material_expressions(surface, "", final_color, "A")
unreal.MaterialEditingLibrary.connect_material_expressions(edge_tint, "", final_color, "B")

roughness = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionScalarParameter, 150, 80
)
roughness.set_editor_property("parameter_name", "Roughness")
roughness.set_editor_property("default_value", 0.64)
specular = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionScalarParameter, 150, 170
)
specular.set_editor_property("parameter_name", "Specular")
specular.set_editor_property("default_value", 0.32)
metallic = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionScalarParameter, 150, 260
)
metallic.set_editor_property("parameter_name", "Metallic")
metallic.set_editor_property("default_value", 0.02)

unreal.MaterialEditingLibrary.connect_material_property(
    final_color, "", unreal.MaterialProperty.MP_BASE_COLOR
)
unreal.MaterialEditingLibrary.connect_material_property(
    roughness, "", unreal.MaterialProperty.MP_ROUGHNESS
)
unreal.MaterialEditingLibrary.connect_material_property(
    specular, "", unreal.MaterialProperty.MP_SPECULAR
)
unreal.MaterialEditingLibrary.connect_material_property(
    metallic, "", unreal.MaterialProperty.MP_METALLIC
)
unreal.MaterialEditingLibrary.recompile_material(material)
unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)

instance = asset_tools.create_asset(
    INSTANCE_NAME, ROOT, unreal.MaterialInstanceConstant,
    unreal.MaterialInstanceConstantFactoryNew()
)
unreal.MaterialEditingLibrary.set_material_instance_parent(instance, material)
unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
    instance, "SuitColor", unreal.LinearColor(0.012, 0.032, 0.039, 1.0)
)
unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
    instance, "FiberColor", unreal.LinearColor(0.045, 0.09, 0.10, 1.0)
)
unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
    instance, "EdgeColor", unreal.LinearColor(0.02, 0.10, 0.12, 1.0)
)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, "FiberAmount", 0.14)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, "Roughness", 0.67)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, "Specular", 0.28)
unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(instance, "Metallic", 0.015)
unreal.EditorAssetLibrary.save_loaded_asset(instance, only_if_is_dirty=False)

report = {
    "status": "pass",
    "master": material.get_path_name(),
    "instance": instance.get_path_name(),
    "semantic_layer": "cryo_bodysuit",
    "contains_oversuit": False,
}
report_path = Path(unreal.Paths.project_saved_dir()) / "MetaHumanCryoBodysuitMaterial.json"
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"METAHUMAN_CRYO_BODYSUIT {json.dumps(report, separators=(',', ':'))}")
unreal.SystemLibrary.quit_editor()
