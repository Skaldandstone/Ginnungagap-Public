"""Generate damaged ship-state, emergency-response, and repair-state models."""

import importlib.util
from pathlib import Path
import unreal

project=Path(unreal.SystemLibrary.get_project_directory())
spec=importlib.util.spec_from_file_location("gameplay_models",project/"tools"/"build_gameplay_model_library.py")
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); Mesh=module.Mesh
ROOT="/Game/Assets/Models/DamageControl"; OUT=project/"Intermediate"/"DamageControl"


def models():
    result={}
    def make(name,fn): mesh=Mesh(name); fn(mesh); result[name]=mesh
    make("SM_Damage_HullBreach_Rim",lambda m:(*[m.box((x,0,z),(45,12,18)) for x,z in ((-65,-55),(0,-72),(65,-50),(-75,15),(78,20),(-45,65),(25,72))],m.box((0,8,0),(35,8,30))))
    make("SM_Damage_HullBreach_Patched",lambda m:(m.box((0,0,2),(155,125,6)),*[m.cylinder((x,y,7),3,10,8,"z") for x,y in ((-65,-50),(-65,50),(65,-50),(65,50),(0,-55),(0,55))]))
    make("SM_Damage_BrokenPipe",lambda m:(m.cylinder((-48,0,0),12,95,16,"x"),m.cylinder((48,8,5),12,90,16,"x"),m.cylinder((0,0,0),18,14,18,"x")))
    make("SM_Damage_ExposedCableBundle",lambda m:(*[m.cylinder((0,y,z),3,180,9,"x") for y,z in ((-10,-8),(-4,8),(4,-4),(10,7))],m.box((-82,0,0),(18,35,28))))
    make("SM_Damage_ElectricalJunction",lambda m:(m.box((0,0,70),(105,48,140)),m.box((15,-29,75),(72,10,90)),*[m.cylinder((x,-38,25),5,40,10,"z") for x in (-28,0,28)]))
    make("SM_Damage_PressureLeakNozzle",lambda m:(m.cylinder((0,0,20),9,40,14,"z"),m.cylinder((0,0,44),15,8,16,"z"),m.box((0,0,5),(46,46,10))))
    make("SM_Emergency_FireSuppressionCart",lambda m:(m.box((0,0,55),(75,55,110)),m.cylinder((-22,-35,22),14,12,14,"y"),m.cylinder((22,-35,22),14,12,14,"y"),m.cylinder((0,0,120),12,20,14,"z")))
    make("SM_Emergency_RadiationBarrier",lambda m:(m.box((0,0,95),(170,24,190)),m.box((0,0,95),(125,32,145)),m.box((0,0,8),(195,65,16))))
    make("SM_Emergency_FoldingBarricade",lambda m:(m.box((0,0,75),(180,12,22)),m.box((0,0,120),(180,12,22)),m.box((-75,0,65),(12,30,130)),m.box((75,0,65),(12,30,130))))
    make("SM_Emergency_RepairFoamTank",lambda m:(m.cylinder((0,0,55),18,110,18,"z"),m.cylinder((0,0,116),8,12,12,"z"),m.box((0,-23,60),(24,8,45))))
    make("SM_Emergency_CasualtyBag",lambda m:(m.sphere((0,0,22),(92,34,22),10,22),m.box((0,0,8),(175,58,10)),m.box((0,-34,20),(35,5,10))))
    make("SM_Emergency_PortableAirScrubber",lambda m:(m.box((0,0,65),(90,70,130)),m.cylinder((-24,-42,70),14,85,14,"z"),m.cylinder((24,-42,70),14,85,14,"z"),m.box((0,-42,20),(68,14,25))))
    return result


def main():
    OUT.mkdir(parents=True,exist_ok=True); built=models(); surface=unreal.EditorAssetLibrary.load_asset("/Game/Assets/Materials/Production/Instances/MI_Surface_Environment")
    for name,mesh in built.items():
        path=OUT/(name+".obj"); mesh.write(path); destination=ROOT+"/"+name
        if not unreal.EditorAssetLibrary.does_asset_exist(destination):
            task=unreal.AssetImportTask(); task.filename=str(path); task.destination_path=ROOT; task.destination_name=name; task.automated=True; task.save=True
            opts=unreal.FbxImportUI(); opts.import_mesh=True; opts.import_as_skeletal=False; opts.import_materials=False; opts.import_textures=False; opts.static_mesh_import_data.combine_meshes=True; opts.static_mesh_import_data.generate_lightmap_u_vs=True; opts.static_mesh_import_data.auto_generate_collision=True; task.options=opts
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        asset=unreal.EditorAssetLibrary.load_asset(destination)
        if not isinstance(asset,unreal.StaticMesh): raise RuntimeError("Import failed: "+destination)
        if surface: asset.set_material(0,surface); unreal.EditorAssetLibrary.save_loaded_asset(asset)
    unreal.log(f"Damage-control library ready: {len(built)} meshes.")


main()
