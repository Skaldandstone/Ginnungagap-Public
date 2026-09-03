"""Generate the second-pass modular interior prop library."""

import importlib.util
from pathlib import Path
import unreal

source = Path(unreal.SystemLibrary.get_project_directory()) / "tools" / "build_gameplay_model_library.py"
spec = importlib.util.spec_from_file_location("gameplay_models", source); module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
Mesh = module.Mesh
ROOT="/Game/Assets/Models/Environment"; OUT=Path(unreal.SystemLibrary.get_project_directory())/"Intermediate"/"EnvironmentProps"


def models():
    result={}
    def make(name,fn): m=Mesh(name); fn(m); result[name]=m
    make("SM_Prop_Bunk",lambda m:(m.box((0,0,22),(210,85,12)),m.box((-98,0,70),(14,85,140)),m.box((98,0,70),(14,85,140))))
    make("SM_Prop_MedicalBed",lambda m:(m.box((0,0,70),(205,82,14)),m.box((-70,0,82),(58,76,12)),m.box((-80,0,34),(12,65,70)),m.box((80,0,34),(12,65,70))))
    make("SM_Prop_GalleyUnit",lambda m:(m.box((0,0,100),(180,65,200)),m.box((0,-38,112),(160,14,70)),m.box((0,-42,45),(145,18,40))))
    make("SM_Prop_Workbench",lambda m:(m.box((0,0,92),(220,85,14)),m.box((-92,0,45),(14,65,90)),m.box((92,0,45),(14,65,90)),m.box((0,35,150),(220,12,110))))
    make("SM_Prop_Ladder",lambda m:(m.cylinder((0,-28,120),4,240,10,"z"),m.cylinder((0,28,120),4,240,10,"z"),*[m.cylinder((0,0,z),3,56,10,"y") for z in range(15,230,28)]))
    make("SM_Prop_Handrail",lambda m:(m.cylinder((0,-70,42),3,84,10,"z"),m.cylinder((0,70,42),3,84,10,"z"),m.cylinder((0,0,84),3,140,10,"y")))
    make("SM_Prop_CableTray",lambda m:(m.box((0,-28,0),(300,5,12)),m.box((0,28,0),(300,5,12)),*[m.box((x,0,0),(5,56,8)) for x in (-140,-70,0,70,140)]))
    make("SM_Prop_Vent",lambda m:(m.box((0,0,4),(90,90,8)),*[m.box((0,y,10),(72,4,10)) for y in (-30,-20,-10,0,10,20,30)]))
    make("SM_Prop_CargoNetFrame",lambda m:(m.box((0,0,100),(12,180,200)),*[m.cylinder((0,y,100),2,190,8,"z") for y in (-70,-35,0,35,70)]))
    make("SM_Prop_ToolCabinet",lambda m:(m.box((0,0,95),(110,55,190)),m.box((0,-31,95),(100,8,176)),*[m.box((0,-37,z),(70,5,4)) for z in (45,75,105,135)]))
    make("SM_Prop_DeconTank",lambda m:(m.cylinder((0,0,85),34,170,20),m.cylinder((0,0,176),15,12,14),m.box((0,-38,70),(52,10,62))))
    make("SM_Prop_AirlockBench",lambda m:(m.box((0,0,52),(190,55,12)),m.box((-80,0,25),(12,45,50)),m.box((80,0,25),(12,45,50)),m.box((0,24,104),(190,8,95))))
    return result


def main():
    OUT.mkdir(parents=True,exist_ok=True)
    for name,mesh in models().items():
        path=OUT/(name+".obj"); mesh.write(path)
        if unreal.EditorAssetLibrary.does_asset_exist(ROOT+"/"+name): continue
        task=unreal.AssetImportTask(); task.filename=str(path); task.destination_path=ROOT; task.destination_name=name; task.automated=True; task.save=True
        options=unreal.FbxImportUI(); options.import_mesh=True; options.import_as_skeletal=False; options.import_materials=False; options.import_textures=False; options.static_mesh_import_data.combine_meshes=True; options.static_mesh_import_data.generate_lightmap_u_vs=True; options.static_mesh_import_data.auto_generate_collision=True; task.options=options
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    unreal.EditorAssetLibrary.save_directory(ROOT,only_if_is_dirty=False,recursive=True); unreal.log("Environment prop expansion ready: 12 meshes.")


main()
