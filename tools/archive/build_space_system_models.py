"""Create celestial/exploration meshes and the exact materials referenced by star-system code."""

import importlib.util
from pathlib import Path
import unreal

project=Path(unreal.SystemLibrary.get_project_directory())
spec=importlib.util.spec_from_file_location("gameplay_models",project/"tools"/"build_gameplay_model_library.py")
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); Mesh=module.Mesh
MESH_ROOT="/Game/Assets/SpaceSystems/Meshes"; MAT_ROOT="/Game/Assets/SpaceSystems/Materials"; OUT=project/"Intermediate"/"SpaceSystems"


def material(name,color,roughness,metallic=0.0,emissive=0.0):
    path=MAT_ROOT+"/"+name
    if unreal.EditorAssetLibrary.does_asset_exist(path): return unreal.EditorAssetLibrary.load_asset(path)
    mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,MAT_ROOT,unreal.Material,unreal.MaterialFactoryNew())
    base=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionConstant3Vector,-260,-40); base.set_editor_property("constant",unreal.LinearColor(*color,1))
    rough=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionConstant,-260,100); rough.set_editor_property("r",roughness)
    metal=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionConstant,-260,180); metal.set_editor_property("r",metallic)
    unreal.MaterialEditingLibrary.connect_material_property(base,"",unreal.MaterialProperty.MP_BASE_COLOR); unreal.MaterialEditingLibrary.connect_material_property(rough,"",unreal.MaterialProperty.MP_ROUGHNESS); unreal.MaterialEditingLibrary.connect_material_property(metal,"",unreal.MaterialProperty.MP_METALLIC)
    if emissive:
        strength=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionConstant,-120,-150); strength.set_editor_property("r",emissive)
        mul=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionMultiply,40,-80); unreal.MaterialEditingLibrary.connect_material_expressions(base,"",mul,"A"); unreal.MaterialEditingLibrary.connect_material_expressions(strength,"",mul,"B"); unreal.MaterialEditingLibrary.connect_material_property(mul,"",unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(mat); unreal.EditorAssetLibrary.save_loaded_asset(mat); return mat


def models():
    result={}
    def make(name,fn): mesh=Mesh(name); fn(mesh); result[name]=mesh
    make("SM_Celestial_Star",lambda m:m.sphere((0,0,0),(500,500,500),16,32))
    make("SM_Celestial_Planet",lambda m:m.sphere((0,0,0),(300,300,300),16,32))
    make("SM_Celestial_Moon",lambda m:m.sphere((0,0,0),(120,116,125),12,24))
    make("SM_Asteroid_Large_A",lambda m:(m.sphere((0,0,0),(170,125,110),10,20),m.sphere((75,-35,10),(90,70,65),8,16)))
    make("SM_Asteroid_Large_B",lambda m:(m.sphere((0,0,0),(145,160,95),10,20),m.sphere((-55,65,-10),(75,85,60),8,16)))
    make("SM_Asteroid_Debris",lambda m:(m.sphere((0,0,0),(28,20,18),7,12),m.sphere((18,-8,4),(15,12,11),6,10)))
    make("SM_Asteroid_ResourceNode",lambda m:(m.sphere((0,0,0),(115,90,78),10,20),*[m.box((x,y,z),(18,12,8)) for x,y,z in ((95,0,10),(-70,50,30),(20,-75,-20))]))
    make("SM_Orbital_NavigationBeacon",lambda m:(m.cylinder((0,0,90),8,180,14,"z"),m.cylinder((0,0,185),38,8,22,"z"),m.box((0,0,20),(95,95,16))))
    make("SM_Orbital_CollectorSatellite",lambda m:(m.box((0,0,0),(110,70,50)),m.box((0,-105,0),(80,120,8)),m.box((0,105,0),(80,120,8)),m.cylinder((65,0,0),24,30,18,"x")))
    make("SM_Orbital_DroneRelay",lambda m:(m.sphere((0,0,0),(35,30,25),9,18),m.cylinder((0,0,55),5,110,12,"z"),m.cylinder((0,0,115),30,6,20,"z")))
    return result


def main():
    mats={
        "star":material("M_Star_Gold",(.95,.35,.035),.18,0,18),
        "blue":material("M_Star_Blue",(.08,.35,1.0),.16,0,20),
        "violet":material("M_Star_Violet",(.48,.07,.85),.2,0,16),
        "ocean":material("M_Planet_Ocean",(.025,.12,.24),.48,.05),
        "volcanic":material("M_Planet_Volcanic",(.18,.025,.008),.66,.08,.8),
        "ice":material("M_Planet_Ice",(.3,.52,.62),.34,.02),
        "sky":material("M_SpaceSky_CosmicRift",(.004,.006,.018),.9,0,.15),
    }
    OUT.mkdir(parents=True,exist_ok=True); built=models()
    asteroid=unreal.EditorAssetLibrary.load_asset("/Game/Assets/Materials/Production/Instances/MI_Surface_Environment")
    for name,mesh in built.items():
        path=OUT/(name+".obj"); mesh.write(path); destination=MESH_ROOT+"/"+name
        if not unreal.EditorAssetLibrary.does_asset_exist(destination):
            task=unreal.AssetImportTask(); task.filename=str(path); task.destination_path=MESH_ROOT; task.destination_name=name; task.automated=True; task.save=True
            opts=unreal.FbxImportUI(); opts.import_mesh=True; opts.import_as_skeletal=False; opts.import_materials=False; opts.import_textures=False; opts.static_mesh_import_data.combine_meshes=True; opts.static_mesh_import_data.generate_lightmap_u_vs=True; opts.static_mesh_import_data.auto_generate_collision=not name.startswith("SM_Celestial"); task.options=opts
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        asset=unreal.EditorAssetLibrary.load_asset(destination)
        if not isinstance(asset,unreal.StaticMesh): raise RuntimeError("Import failed: "+destination)
        assigned=mats["star"] if name=="SM_Celestial_Star" else mats["ocean"] if name.startswith("SM_Celestial") else asteroid
        if assigned: asset.set_material(0,assigned); unreal.EditorAssetLibrary.save_loaded_asset(asset)
    unreal.log(f"Space-system library ready: {len(built)} meshes and {len(mats)} materials.")


main()
