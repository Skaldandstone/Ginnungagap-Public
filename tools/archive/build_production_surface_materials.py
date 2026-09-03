"""Build shared parameterized surface masters and apply category instances."""

import unreal

ROOT="/Game/Assets/Materials/Production"


def master(name, organic=False):
    path=ROOT+"/"+name
    if unreal.EditorAssetLibrary.does_asset_exist(path): return unreal.EditorAssetLibrary.load_asset(path)
    mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,ROOT,unreal.Material,unreal.MaterialFactoryNew())
    base=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionVectorParameter,-650,-120); base.set_editor_property("parameter_name","BaseColor"); base.set_editor_property("default_value",unreal.LinearColor(.18,.2,.2,1))
    wear=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionVectorParameter,-650,20); wear.set_editor_property("parameter_name","WearColor"); wear.set_editor_property("default_value",unreal.LinearColor(.04,.045,.05,1))
    noise=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionNoise,-650,180)
    amount=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionScalarParameter,-440,230); amount.set_editor_property("parameter_name","WearAmount"); amount.set_editor_property("default_value",.18)
    mask=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionMultiply,-250,150)
    lerp=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionLinearInterpolate,-30,-80)
    rough=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionScalarParameter,-220,300); rough.set_editor_property("parameter_name","Roughness"); rough.set_editor_property("default_value",.62)
    metal=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionScalarParameter,-220,390); metal.set_editor_property("parameter_name","Metallic"); metal.set_editor_property("default_value",.25)
    unreal.MaterialEditingLibrary.connect_material_expressions(noise,"",mask,"A"); unreal.MaterialEditingLibrary.connect_material_expressions(amount,"",mask,"B")
    unreal.MaterialEditingLibrary.connect_material_expressions(base,"",lerp,"A"); unreal.MaterialEditingLibrary.connect_material_expressions(wear,"",lerp,"B"); unreal.MaterialEditingLibrary.connect_material_expressions(mask,"",lerp,"Alpha")
    unreal.MaterialEditingLibrary.connect_material_property(lerp,"",unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(rough,"",unreal.MaterialProperty.MP_ROUGHNESS); unreal.MaterialEditingLibrary.connect_material_property(metal,"",unreal.MaterialProperty.MP_METALLIC)
    if organic:
        glow=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionScalarParameter,180,50); glow.set_editor_property("parameter_name","Bioluminescence"); glow.set_editor_property("default_value",1.4)
        emission=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionMultiply,370,-20)
        unreal.MaterialEditingLibrary.connect_material_expressions(lerp,"",emission,"A"); unreal.MaterialEditingLibrary.connect_material_expressions(glow,"",emission,"B")
        unreal.MaterialEditingLibrary.connect_material_property(emission,"",unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(mat); unreal.EditorAssetLibrary.save_loaded_asset(mat); return mat


def instance(name,parent,color,wear,roughness,metallic,wear_amount=.18,glow=None):
    path=ROOT+"/Instances/"+name
    if unreal.EditorAssetLibrary.does_asset_exist(path): inst=unreal.EditorAssetLibrary.load_asset(path)
    else: inst=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,ROOT+"/Instances",unreal.MaterialInstanceConstant,unreal.MaterialInstanceConstantFactoryNew())
    inst.set_editor_property("parent",parent)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(inst,"BaseColor",unreal.LinearColor(*color,1))
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(inst,"WearColor",unreal.LinearColor(*wear,1))
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst,"Roughness",roughness)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst,"Metallic",metallic)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst,"WearAmount",wear_amount)
    if glow is not None: unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst,"Bioluminescence",glow)
    unreal.EditorAssetLibrary.save_loaded_asset(inst); return inst


def apply(root,material):
    count=0
    for path in unreal.EditorAssetLibrary.list_assets(root,recursive=True,include_folder=False):
        asset=unreal.EditorAssetLibrary.load_asset(path)
        if isinstance(asset,unreal.StaticMesh): asset.set_material(0,material); unreal.EditorAssetLibrary.save_loaded_asset(asset); count+=1
    return count


def main():
    hard=master("M_Surface_HardSurface"); organic=master("M_Surface_BloomOrganic",True)
    mats={
        "equipment":instance("MI_Surface_Equipment",hard,(.28,.07,.016),(.025,.03,.032),.48,.42,.22),
        "pickup":instance("MI_Surface_Pickup",hard,(.38,.22,.02),(.055,.035,.012),.58,.28,.2),
        "drone":instance("MI_Surface_Drone",hard,(.028,.09,.145),(.02,.025,.03),.44,.62,.16),
        "system":instance("MI_Surface_ShipSystem",hard,(.28,.3,.29),(.045,.05,.052),.66,.26,.24),
        "environment":instance("MI_Surface_Environment",hard,(.035,.044,.05),(.12,.07,.035),.6,.68,.26),
        "exterior":instance("MI_Surface_ExteriorHull",hard,(.2,.22,.215),(.035,.04,.045),.61,.42,.2),
        "wearable":instance("MI_Surface_Wearable",hard,(.09,.105,.11),(.025,.03,.032),.56,.48,.16),
        "bloom":instance("MI_Surface_Bloom",organic,(.13,.012,.18),(.34,.035,.19),.31,.05,.42,1.8),
    }
    total=0
    total+=apply("/Game/Assets/Models/Equipment",mats["equipment"]); total+=apply("/Game/Assets/Models/Pickups",mats["pickup"])
    total+=apply("/Game/Assets/Models/Drones",mats["drone"]); total+=apply("/Game/Assets/Models/ShipSystems",mats["system"])
    total+=apply("/Game/Assets/Models/Environment",mats["environment"]); total+=apply("/Game/Assets/Ships/Exterior/Meshes",mats["exterior"])
    total+=apply("/Game/Characters/Player/Equipment/Meshes",mats["wearable"]); total+=apply("/Game/Assets/Models/Bloom",mats["bloom"])
    unreal.log(f"Production surfaces applied to {total} meshes with 2 masters and 8 instances.")


main()
