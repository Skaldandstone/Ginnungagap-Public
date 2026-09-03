"""Generate room-specific machinery for medical, engineering, cargo, command, and drone bays."""

import importlib.util
from pathlib import Path
import unreal

project=Path(unreal.SystemLibrary.get_project_directory())
spec=importlib.util.spec_from_file_location("gameplay_models",project/"tools"/"build_gameplay_model_library.py")
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); Mesh=module.Mesh
ROOT="/Game/Assets/Models/RoomMachinery"; OUT=project/"Intermediate"/"RoomMachinery"


def models():
    result={}
    def make(name,fn): mesh=Mesh(name); fn(mesh); result[name]=mesh
    make("SM_Medical_DiagnosticArch",lambda m:(m.box((-60,0,105),(18,70,210)),m.box((60,0,105),(18,70,210)),m.box((0,0,202),(120,70,18)),m.box((0,-44,105),(95,16,105))))
    make("SM_Medical_SupplyCabinet",lambda m:(m.box((0,0,100),(130,55,200)),m.box((-33,-31,110),(55,8,145)),m.box((33,-31,110),(55,8,145)),m.box((0,-35,28),(105,12,36))))
    make("SM_Medical_SurgicalLamp",lambda m:(m.cylinder((0,0,100),5,200,12,"z"),m.cylinder((35,0,198),4,70,10,"x"),m.cylinder((72,0,198),26,10,20,"x")))
    make("SM_Engineering_ReactorCoil",lambda m:(m.cylinder((0,0,105),42,210,24,"z"),*[m.cylinder((0,0,z),52,12,24,"z") for z in (30,70,110,150,190)],m.box((0,0,8),(125,125,16))))
    make("SM_Engineering_BreakerBank",lambda m:(m.box((0,0,110),(180,48,220)),*[m.box((x,-29,z),(36,12,28)) for x in (-60,-20,20,60) for z in (45,85,125,165)]))
    make("SM_Engineering_CoolantPump",lambda m:(m.cylinder((0,0,65),38,130,20,"z"),m.cylinder((0,0,142),20,24,16,"z"),m.cylinder((-55,0,65),12,55,14,"x"),m.cylinder((55,0,65),12,55,14,"x")))
    make("SM_Engineering_PortableGenerator",lambda m:(m.box((0,0,55),(145,80,110)),m.cylinder((-45,-48,48),18,16,16,"y"),m.cylinder((45,-48,48),18,16,16,"y"),m.box((0,-48,85),(80,16,28))))
    make("SM_Cargo_Pallet",lambda m:(m.box((0,0,12),(180,140,18)),*[m.box((x,0,2),(28,140,10)) for x in (-65,0,65)]))
    make("SM_Cargo_HandLoader",lambda m:(m.box((0,0,22),(85,75,18)),m.box((-36,30,105),(12,12,180)),m.box((0,30,190),(85,12,18)),m.cylinder((0,-42,18),18,75,16,"y")))
    make("SM_Command_HelmChair",lambda m:(m.box((0,0,48),(72,75,18)),m.box((-28,25,122),(16,18,145)),m.box((28,25,122),(16,18,145)),m.box((0,35,118),(62,14,130)),m.box((0,0,14),(45,45,30))))
    make("SM_Command_HolographicTable",lambda m:(m.box((0,0,85),(180,110,18)),m.box((0,0,40),(75,65,80)),m.box((0,0,103),(150,80,10)),m.cylinder((0,0,120),35,16,20,"z")))
    make("SM_Drone_ServiceRack",lambda m:(m.box((0,0,110),(220,70,220)),m.box((0,-44,52),(195,22,75)),m.box((0,-44,145),(195,22,75)),*[m.cylinder((x,-58,z),9,18,14,"y") for x in (-70,0,70) for z in (52,145)]))
    make("SM_Drone_LaunchCradle",lambda m:(m.box((0,0,18),(210,120,24)),m.box((-92,0,58),(18,100,80)),m.box((92,0,58),(18,100,80)),m.cylinder((0,-45,38),12,180,16,"x")))
    make("SM_Utility_WaterRecycler",lambda m:(m.box((0,0,105),(150,85,210)),m.cylinder((-42,-52,112),22,145,18,"z"),m.cylinder((42,-52,112),22,145,18,"z"),m.box((0,-55,38),(112,16,45))))
    return result


def main():
    OUT.mkdir(parents=True,exist_ok=True); built=models()
    surface=unreal.EditorAssetLibrary.load_asset("/Game/Assets/Materials/Production/Instances/MI_Surface_Environment")
    for name,mesh in built.items():
        path=OUT/(name+".obj"); mesh.write(path); destination=ROOT+"/"+name
        if not unreal.EditorAssetLibrary.does_asset_exist(destination):
            task=unreal.AssetImportTask(); task.filename=str(path); task.destination_path=ROOT; task.destination_name=name; task.automated=True; task.save=True
            opts=unreal.FbxImportUI(); opts.import_mesh=True; opts.import_as_skeletal=False; opts.import_materials=False; opts.import_textures=False
            opts.static_mesh_import_data.combine_meshes=True; opts.static_mesh_import_data.generate_lightmap_u_vs=True; opts.static_mesh_import_data.auto_generate_collision=True; task.options=opts
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        asset=unreal.EditorAssetLibrary.load_asset(destination)
        if not isinstance(asset,unreal.StaticMesh): raise RuntimeError("Import failed: "+destination)
        if surface: asset.set_material(0,surface); unreal.EditorAssetLibrary.save_loaded_asset(asset)
    unreal.log(f"Room machinery library ready: {len(built)} meshes.")


main()
