"""Generate reusable exterior detail modules for differentiating ship classes."""

import importlib.util
from pathlib import Path
import unreal

project=Path(unreal.SystemLibrary.get_project_directory())
spec=importlib.util.spec_from_file_location("gameplay_models",project/"tools"/"build_gameplay_model_library.py")
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); Mesh=module.Mesh
ROOT="/Game/Assets/Ships/Exterior/Details"; OUT=project/"Intermediate"/"ShipExteriorDetails"


def models():
    result={}
    def make(name,fn): mesh=Mesh(name); fn(mesh); result[name]=mesh
    make("SM_Exterior_RCSCluster",lambda m:(m.box((0,0,0),(900,700,500)),m.cylinder((0,-430,0),110,360,14,"y"),m.cylinder((0,430,0),110,360,14,"y"),m.cylinder((0,0,340),110,300,14,"z")))
    make("SM_Exterior_HighGainAntenna",lambda m:(m.cylinder((0,0,700),55,1400,14,"z"),m.cylinder((0,0,1500),620,90,28,"z"),m.box((0,0,120),(700,700,220))))
    make("SM_Exterior_ArmorPanel",lambda m:(m.box((0,0,40),(3200,1800,80)),m.box((0,0,95),(2800,1400,55)),*[m.box((x,0,135),(90,1300,35)) for x in (-1200,-600,0,600,1200)]))
    make("SM_Exterior_ObservationBlister",lambda m:(m.sphere((0,0,450),(900,700,450),10,24),m.box((0,0,50),(1900,1500,100))))
    make("SM_Exterior_Lifeboat",lambda m:(m.sphere((0,0,480),(1800,650,480),10,24),m.box((-1500,0,480),(1200,1100,650)),m.box((0,0,80),(3200,1400,160))))
    make("SM_Exterior_EVARail",lambda m:(m.cylinder((0,-900,260),35,520,10,"z"),m.cylinder((0,900,260),35,520,10,"z"),m.cylinder((0,0,520),35,1800,10,"y"),*[m.cylinder((0,y,120),24,240,9,"z") for y in (-600,-300,0,300,600)]))
    make("SM_Exterior_ServiceHatch",lambda m:(m.box((0,0,45),(1600,1200,90)),m.box((0,0,105),(1350,950,55)),m.cylinder((0,-420,145),90,120,16,"z")))
    make("SM_Exterior_HeatExchanger",lambda m:(m.box((0,0,500),(2300,1000,1000)),*[m.box((0,y,500),(2000,55,850)) for y in (-400,-250,-100,50,200,350)],m.cylinder((-900,0,500),180,700,16,"x"),m.cylinder((900,0,500),180,700,16,"x")))
    make("SM_Exterior_DefenseMount",lambda m:(m.cylinder((0,0,260),600,520,22,"z"),m.box((0,0,620),(900,700,300)),m.cylinder((850,-180,700),90,1600,16,"x"),m.cylinder((850,180,700),90,1600,16,"x")))
    make("SM_Exterior_PassiveSensorArray",lambda m:(m.box((0,0,200),(2000,900,400)),*[m.cylinder((x,y,650),80,h,12,"z") for x,y,h in ((-700,-250,700),(-250,250,1100),(250,-250,900),(700,250,600))]))
    make("SM_Exterior_CargoClamp",lambda m:(m.box((0,0,180),(1400,500,360)),m.box((-580,0,540),(220,500,720)),m.box((580,0,540),(220,500,720)),m.box((0,0,850),(1100,500,180))))
    make("SM_Exterior_ThermalShield",lambda m:(m.box((0,0,70),(4000,2400,140)),*[m.box((x,0,155),(120,2100,50)) for x in (-1600,-800,0,800,1600)],*[m.box((0,y,155),(3700,100,50)) for y in (-800,0,800)]))
    return result


def main():
    OUT.mkdir(parents=True,exist_ok=True); built=models(); surface=unreal.EditorAssetLibrary.load_asset("/Game/Assets/Materials/Production/Instances/MI_Surface_ExteriorHull")
    for name,mesh in built.items():
        path=OUT/(name+".obj"); mesh.write(path); destination=ROOT+"/"+name
        if not unreal.EditorAssetLibrary.does_asset_exist(destination):
            task=unreal.AssetImportTask(); task.filename=str(path); task.destination_path=ROOT; task.destination_name=name; task.automated=True; task.save=True
            opts=unreal.FbxImportUI(); opts.import_mesh=True; opts.import_as_skeletal=False; opts.import_materials=False; opts.import_textures=False; opts.static_mesh_import_data.combine_meshes=True; opts.static_mesh_import_data.generate_lightmap_u_vs=True; opts.static_mesh_import_data.auto_generate_collision=True; task.options=opts
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        asset=unreal.EditorAssetLibrary.load_asset(destination)
        if not isinstance(asset,unreal.StaticMesh): raise RuntimeError("Import failed: "+destination)
        if surface: asset.set_material(0,surface); unreal.EditorAssetLibrary.save_loaded_asset(asset)
    unreal.log(f"Exterior detail library ready: {len(built)} meshes.")


main()
