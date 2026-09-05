"""The weld seam's material: an emissive bead whose heat is a parameter, so a door being welded or
cut glows white-orange at the torch and cools to a dull bead behind it. Built once by this script
(headless: UnrealEditor-Cmd -ExecutePythonScript), then referenced by AWeldableBulkheadDoor."""
import unreal

DEST = "/Game/Assets/Ships/Production/Materials/Fx"
NAME = "M_WeldSeam"
PATH = f"{DEST}/{NAME}"

if unreal.EditorAssetLibrary.does_asset_exist(PATH):
    print(f"WELDSEAM exists {PATH}")
else:
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mel = unreal.MaterialEditingLibrary
    mat = tools.create_asset(NAME, DEST, unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_DEFAULT_LIT)
    # Heat: 0 is a cold bead (dark, slightly rough metal), 1 is the arc.
    heat = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -700, 0)
    heat.set_editor_property("parameter_name", "Heat")
    heat.set_editor_property("default_value", 0.0)
    cold = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -700, 200)
    cold.set_editor_property("constant", unreal.LinearColor(0.35, 0.16, 0.08, 1.0))
    hot = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -700, 400)
    hot.set_editor_property("constant", unreal.LinearColor(60.0, 22.0, 6.0, 1.0))
    lerp = mel.create_material_expression(mat, unreal.MaterialExpressionLinearInterpolate, -400, 250)
    mel.connect_material_expressions(cold, "", lerp, "A")
    mel.connect_material_expressions(hot, "", lerp, "B")
    mel.connect_material_expressions(heat, "", lerp, "Alpha")
    mel.connect_material_property(lerp, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    base = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, 500)
    base.set_editor_property("constant", unreal.LinearColor(0.12, 0.09, 0.07, 1.0))
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 650)
    rough.set_editor_property("r", 0.75)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    metal = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 750)
    metal.set_editor_property("r", 0.9)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    print(f"WELDSEAM built {PATH}")
