"""Generate modular wearable equipment and separated Bloom rig-prep meshes."""

import importlib.util
from pathlib import Path
import unreal

project = Path(unreal.SystemLibrary.get_project_directory())
spec = importlib.util.spec_from_file_location("gameplay_models", project/"tools"/"build_gameplay_model_library.py")
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module); Mesh = module.Mesh
OUT = project/"Intermediate"/"CharacterBloomModels"
PLAYER = "/Game/Characters/Player/Equipment/Meshes"
BLOOM = "/Game/Assets/Models/Bloom/RigPrep"


def assets():
    result={}
    def make(folder,name,fn): mesh=Mesh(name); fn(mesh); result[name]=(folder,mesh)
    # Manny-scale wearable modules, centered around their intended attachment pivots.
    make(PLAYER,"SM_Equip_HelmetLamp",lambda m:(m.box((0,0,0),(12,8,6)),m.cylinder((7,0,0),3,5,12,"x")))
    make(PLAYER,"SM_Equip_RadiationShield",lambda m:(m.box((0,0,0),(7,32,38)),m.box((4,0,0),(3,24,28)),m.cylinder((5,0,10),3,5,10,"x")))
    make(PLAYER,"SM_Equip_ThermalPlating",lambda m:(m.box((0,0,0),(6,28,34)),*[m.box((4,0,z),(3,24,4)) for z in (-12,-4,4,12)]))
    make(PLAYER,"SM_Equip_PressureSeal",lambda m:(m.cylinder((0,0,0),15,4,28,"x"),m.box((3,0,0),(4,10,8))))
    make(PLAYER,"SM_Equip_OxygenFilter",lambda m:(m.cylinder((0,0,0),6,18,18,"z"),m.cylinder((0,0,11),3,5,12,"z"),m.box((0,7,0),(8,4,12))))
    make(PLAYER,"SM_Equip_ArmorPauldron",lambda m:(m.sphere((0,0,0),(8,14,11),8,18),m.box((-4,0,-4),(4,18,10))))
    make(PLAYER,"SM_Equip_ToolHolster",lambda m:(m.box((0,0,0),(9,14,28)),m.box((3,0,10),(5,10,5)),m.cylinder((0,0,-15),4,5,10,"z")))
    make(PLAYER,"SM_Equip_TetherHarness",lambda m:(m.box((0,-15,0),(5,8,30)),m.box((0,15,0),(5,8,30)),m.box((0,0,-12),(5,30,7)),m.cylinder((2,0,-18),5,5,16,"x")))

    # Separated modules retain independent origins for skeletal binding and damage swaps.
    make(BLOOM,"SM_Bloom_Crawler_Torso_Rig",lambda m:m.sphere((0,0,0),(38,28,22),10,20))
    make(BLOOM,"SM_Bloom_Crawler_Head_Rig",lambda m:(m.sphere((0,0,0),(20,18,17),9,18),m.box((15,0,-5),(18,12,8))))
    make(BLOOM,"SM_Bloom_Crawler_Leg_Rig",lambda m:(m.cylinder((0,0,-20),4,40,10,"z"),m.cylinder((18,0,-39),3,38,10,"x"),m.box((38,0,-39),(10,7,4))))
    make(BLOOM,"SM_Bloom_Puppeteer_Torso_Rig",lambda m:(m.sphere((0,0,0),(28,24,45),10,20),m.sphere((8,0,26),(15,18,25),8,16)))
    make(BLOOM,"SM_Bloom_Puppeteer_Head_Rig",lambda m:(m.sphere((0,0,0),(18,17,22),9,18),m.sphere((8,-9,3),(8,7,10),7,14)))
    make(BLOOM,"SM_Bloom_Puppeteer_Arm_Rig",lambda m:(m.cylinder((0,0,-24),7,48,12,"z"),m.cylinder((14,0,-55),5,34,10,"x"),m.box((34,0,-55),(14,11,7))))
    make(BLOOM,"SM_Bloom_Puppeteer_Leg_Rig",lambda m:(m.cylinder((0,0,-30),10,60,14,"z"),m.cylinder((15,0,-72),7,40,12,"x"),m.box((40,0,-72),(22,14,8))))
    make(BLOOM,"SM_Bloom_Tendril_Rig",lambda m:(m.cylinder((0,0,18),3,36,9,"z"),m.cylinder((7,0,42),2.5,18,9,"x"),m.sphere((17,0,42),(5,4,5),6,12)))
    return result


def import_mesh(folder,name,path):
    if unreal.EditorAssetLibrary.does_asset_exist(folder+"/"+name): return
    task=unreal.AssetImportTask(); task.filename=str(path); task.destination_path=folder; task.destination_name=name; task.automated=True; task.save=True
    opts=unreal.FbxImportUI(); opts.import_mesh=True; opts.import_as_skeletal=False; opts.import_materials=False; opts.import_textures=False
    opts.static_mesh_import_data.combine_meshes=True; opts.static_mesh_import_data.generate_lightmap_u_vs=True; opts.static_mesh_import_data.auto_generate_collision=False; task.options=opts
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    if not unreal.EditorAssetLibrary.does_asset_exist(folder+"/"+name): raise RuntimeError("Import failed: "+name)


def main():
    OUT.mkdir(parents=True,exist_ok=True); built=assets()
    for name,(folder,mesh) in built.items():
        path=OUT/(name+".obj"); mesh.write(path); import_mesh(folder,name,path)
    unreal.EditorAssetLibrary.save_directory(PLAYER,False,True); unreal.EditorAssetLibrary.save_directory(BLOOM,False,True)
    unreal.log(f"Character/Bloom library ready: {len(built)} meshes.")


main()
