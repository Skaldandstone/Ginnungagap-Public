"""Generate expanded handheld tools, industrial weapons, consumables, and mission items."""

import importlib.util
from pathlib import Path
import unreal

project=Path(unreal.SystemLibrary.get_project_directory())
spec=importlib.util.spec_from_file_location("gameplay_models",project/"tools"/"build_gameplay_model_library.py")
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); Mesh=module.Mesh
ROOT="/Game/Assets/Models/GameplayItems"; OUT=project/"Intermediate"/"GameplayItems"


def models():
    result={}
    def make(kind,name,fn): mesh=Mesh(name); fn(mesh); result[name]=(kind,mesh)
    make("equipment","SM_Weapon_FlareLauncher",lambda m:(m.cylinder((18,0,0),6,42,14,"x"),m.box((-2,0,-13),(11,10,26)),m.cylinder((42,0,0),8,7,16,"x")))
    make("equipment","SM_Weapon_TetherLauncher",lambda m:(m.box((16,0,0),(48,15,18)),m.cylinder((34,0,0),10,18,16,"x"),m.box((-2,0,-15),(12,12,30)),m.cylinder((10,0,13),8,8,14,"y")))
    make("equipment","SM_Weapon_RivetRifle",lambda m:(m.box((22,0,0),(72,14,18)),m.box((-2,0,-18),(12,12,34)),m.box((45,0,0),(14,10,10)),m.box((-18,0,0),(18,13,14))))
    make("equipment","SM_Tool_CuttingTorch",lambda m:(m.cylinder((12,0,0),5,38,14,"x"),m.cylinder((34,0,0),3,10,10,"x"),m.box((-7,0,-11),(10,9,22))))
    make("equipment","SM_Tool_PryBar",lambda m:(m.cylinder((0,0,0),3,75,10,"x"),m.box((39,0,5),(12,5,14)),m.box((-39,0,-5),(12,5,14))))
    make("equipment","SM_Tool_TorqueWrench",lambda m:(m.cylinder((0,0,0),3,48,10,"x"),m.cylinder((27,0,0),9,8,14,"x"),m.box((-29,0,0),(12,6,14))))
    make("pickup","SM_Consumable_FieldMedkit",lambda m:(m.box((0,0,12),(46,32,24)),m.box((0,0,26),(50,36,5)),m.box((0,-19,12),(18,5,7))))
    make("pickup","SM_Component_FilterCartridge",lambda m:(m.cylinder((0,0,18),9,36,18,"z"),*[m.box((0,y,18),(22,3,30)) for y in (-7,0,7)]))
    make("pickup","SM_Component_CoolantCell",lambda m:(m.cylinder((0,0,22),8,44,16,"z"),m.cylinder((0,0,47),10,6,14,"z"),m.cylinder((0,0,-3),10,6,14,"z")))
    make("pickup","SM_Mission_NavigationDataCore",lambda m:(m.box((0,0,18),(28,18,36)),m.box((0,0,39),(22,14,6)),m.box((0,-11,18),(18,5,22))))
    make("pickup","SM_Mission_SensorModule",lambda m:(m.box((0,0,18),(42,30,36)),m.cylinder((0,0,43),10,14,16,"z"),m.box((0,-19,17),(30,8,18))))
    make("pickup","SM_Component_HullPatch",lambda m:(m.box((0,0,2),(65,45,4)),*[m.cylinder((x,y,5),2,6,8,"z") for x,y in ((-27,-17),(-27,17),(27,-17),(27,17))]))
    make("pickup","SM_Component_PowerFuse",lambda m:(m.cylinder((0,0,0),4,28,12,"x"),m.cylinder((-16,0,0),6,5,12,"x"),m.cylinder((16,0,0),6,5,12,"x")))
    make("pickup","SM_Mission_BioSampleCase",lambda m:(m.box((0,0,18),(62,40,36)),m.box((0,0,39),(66,44,6)),m.cylinder((-17,-23,18),6,28,12,"z"),m.cylinder((17,-23,18),6,28,12,"z")))
    return result


def main():
    OUT.mkdir(parents=True,exist_ok=True); built=models()
    mats={"equipment":unreal.EditorAssetLibrary.load_asset("/Game/Assets/Materials/Production/Instances/MI_Surface_Equipment"),"pickup":unreal.EditorAssetLibrary.load_asset("/Game/Assets/Materials/Production/Instances/MI_Surface_Pickup")}
    for name,(kind,mesh) in built.items():
        path=OUT/(name+".obj"); mesh.write(path); destination=ROOT+"/"+name
        if not unreal.EditorAssetLibrary.does_asset_exist(destination):
            task=unreal.AssetImportTask(); task.filename=str(path); task.destination_path=ROOT; task.destination_name=name; task.automated=True; task.save=True
            opts=unreal.FbxImportUI(); opts.import_mesh=True; opts.import_as_skeletal=False; opts.import_materials=False; opts.import_textures=False
            opts.static_mesh_import_data.combine_meshes=True; opts.static_mesh_import_data.generate_lightmap_u_vs=True; opts.static_mesh_import_data.auto_generate_collision=True; task.options=opts
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        asset=unreal.EditorAssetLibrary.load_asset(destination)
        if not isinstance(asset,unreal.StaticMesh): raise RuntimeError("Import failed: "+destination)
        if mats[kind]: asset.set_material(0,mats[kind]); unreal.EditorAssetLibrary.save_loaded_asset(asset)
    unreal.log(f"Handheld and mission-item library ready: {len(built)} meshes.")


main()
