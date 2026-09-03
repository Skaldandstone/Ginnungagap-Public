"""Generate the second Bloom enemy, infection-overlay, and growth model set."""

import importlib.util
from pathlib import Path
import unreal

project=Path(unreal.SystemLibrary.get_project_directory())
spec=importlib.util.spec_from_file_location("gameplay_models",project/"tools"/"build_gameplay_model_library.py")
module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module); Mesh=module.Mesh
ROOT="/Game/Assets/Models/Bloom/Expansion"; OUT=project/"Intermediate"/"BloomExpansion"


def models():
    result={}
    def make(name,fn): mesh=Mesh(name); fn(mesh); result[name]=mesh
    # Infection shells attach over a Manny-compatible corpse without replacing its animation rig.
    make("SM_Bloom_Crew_TorsoOverlay",lambda m:(m.sphere((0,0,0),(24,18,34),9,18),m.sphere((12,-12,15),(14,11,17),7,14),m.cylinder((-5,15,-5),3,42,9,"z")))
    make("SM_Bloom_Crew_HeadOverlay",lambda m:(m.sphere((0,0,0),(17,16,20),8,16),m.sphere((9,-8,4),(10,9,12),7,14),m.cylinder((4,9,20),2,20,8,"z")))
    make("SM_Bloom_Crew_ArmOverlay",lambda m:(m.cylinder((0,0,-22),6,44,11,"z"),m.sphere((5,0,-5),(10,8,13),7,14),m.cylinder((11,0,-51),4,30,9,"x")))
    # Rigid drone pieces use independent origins for nacelle and tendril bones.
    make("SM_Bloom_InfestedDrone_Core_Rig",lambda m:(m.box((0,0,0),(70,48,26)),m.sphere((18,-12,10),(26,19,18),9,18),m.sphere((-22,10,-4),(20,24,16),8,16)))
    make("SM_Bloom_InfestedDrone_Nacelle_Rig",lambda m:(m.cylinder((0,0,0),12,18,16,"y"),m.box((0,0,0),(32,14,18)),m.sphere((10,0,8),(12,10,9),7,14)))
    make("SM_Bloom_InfestedDrone_Tendril_Rig",lambda m:(m.cylinder((0,0,-18),3,36,9,"z"),m.cylinder((10,0,-42),2,22,8,"x"),m.sphere((22,0,-42),(5,4,5),6,12)))
    make("SM_Bloom_SporeSac",lambda m:(m.sphere((0,0,32),(24,22,32),10,20),m.sphere((14,-10,18),(17,15,20),8,16),m.cylinder((0,0,5),9,14,14,"z")))
    make("SM_Bloom_CalcifiedBarricade",lambda m:(m.box((0,0,55),(150,26,110)),*[m.sphere((x,-18,z),(28,18,32),8,14) for x,z in ((-55,28),(-18,75),(25,38),(58,78))]))
    make("SM_Bloom_FloorGrowth",lambda m:(m.sphere((0,0,10),(58,45,12),8,18),*[m.cylinder((x,y,22),4,h,9,"z") for x,y,h in ((-30,-18,32),(10,-8,45),(32,20,28),(-8,25,38))]))
    make("SM_Bloom_CeilingStalker_Proxy",lambda m:(m.sphere((0,0,-24),(30,26,24),9,18),m.sphere((12,0,-56),(16,15,19),8,16),*[m.cylinder((x,y,-5),4,70,9,"z") for x,y in ((-20,-18),(-20,18),(20,-18),(20,18))]))
    return result


def main():
    OUT.mkdir(parents=True,exist_ok=True); built=models()
    bloom_mat=unreal.EditorAssetLibrary.load_asset("/Game/Assets/Materials/Production/Instances/MI_Surface_Bloom")
    for name,mesh in built.items():
        path=OUT/(name+".obj"); mesh.write(path); destination=ROOT+"/"+name
        if not unreal.EditorAssetLibrary.does_asset_exist(destination):
            task=unreal.AssetImportTask(); task.filename=str(path); task.destination_path=ROOT; task.destination_name=name; task.automated=True; task.save=True
            opts=unreal.FbxImportUI(); opts.import_mesh=True; opts.import_as_skeletal=False; opts.import_materials=False; opts.import_textures=False
            opts.static_mesh_import_data.combine_meshes=True; opts.static_mesh_import_data.generate_lightmap_u_vs=True; opts.static_mesh_import_data.auto_generate_collision="_Proxy" in name or "Barricade" in name or "SporeSac" in name; task.options=opts
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        asset=unreal.EditorAssetLibrary.load_asset(destination)
        if not isinstance(asset,unreal.StaticMesh): raise RuntimeError("Import failed: "+destination)
        if bloom_mat: asset.set_material(0,bloom_mat); unreal.EditorAssetLibrary.save_loaded_asset(asset)
    unreal.log(f"Bloom expansion ready: {len(built)} meshes.")


main()
