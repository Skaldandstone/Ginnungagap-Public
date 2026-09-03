"""Create Unreal-native Modeling Mode sculpt workspaces for the capital ships."""
from pathlib import Path
import json
import unreal

PROJECT=Path(unreal.SystemLibrary.get_project_directory())
SOURCE=PROJECT/"Art/Ships/Exterior/UnrealSculptBase"
ROOT="/Game/Assets/Ships/Exterior/UnrealSculpt"
MAP_ROOT="/Game/Assets/Maps/ShipExterior/Sculpt"
REPORT=PROJECT/"Saved/Reports/UnrealShipSculptWorkspace.json"

SHIPS={
 "MilitaryCorvette":{"glb":SOURCE/"SM_Ship_MilitaryCorvette_Shipping.glb","dest":ROOT+"/MilitaryCorvette/Source","working":ROOT+"/MilitaryCorvette/Working/Iteration_01","map":MAP_ROOT+"/L_MilitaryCorvette_Sculpt","dims_cm":(240000,43000,62000),"concept":PROJECT/"docs/concept-art/reference/ships/medium-military-corvette-exterior.png"},
 "ExpeditionCarrier":{"glb":SOURCE/"SM_Ship_ExpeditionCarrier_Shipping.glb","dest":ROOT+"/ExpeditionCarrier/Source","working":ROOT+"/ExpeditionCarrier/Working/Iteration_01","map":MAP_ROOT+"/L_ExpeditionCarrier_Sculpt","dims_cm":(650000,140000,180000),"concept":PROJECT/"docs/concept-art/reference/ships/large-expedition-carrier-exterior.png"},
}

def import_file(path,dest,replace=True):
    task=unreal.AssetImportTask();task.filename=str(path);task.destination_path=dest;task.automated=True;task.replace_existing=replace;task.replace_existing_settings=False;task.save=False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);return list(task.imported_object_paths)

def static_meshes(dest):
    result=[]
    for path in unreal.EditorAssetLibrary.list_assets(dest,recursive=True,include_folder=False):
        asset=unreal.EditorAssetLibrary.load_asset(path)
        if isinstance(asset,unreal.StaticMesh):result.append(asset)
    return result

def configure(mesh):
    # Keep sculpt sources non-Nanite. Enable Nanite only on a shape-approved copy.
    mesh.set_editor_property("light_map_coordinate_index",1)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)

def make_working_copies(meshes,working):
    if unreal.EditorAssetLibrary.does_directory_exist(working):
        unreal.EditorAssetLibrary.delete_directory(working)
    unreal.EditorAssetLibrary.make_directory(working)
    result=[]
    for mesh in meshes:
        source=mesh.get_path_name().split(".")[0]
        destination=working+"/"+mesh.get_name()
        copy=unreal.EditorAssetLibrary.duplicate_asset(source,destination)
        if not isinstance(copy,unreal.StaticMesh):
            raise RuntimeError("Could not create sculpt working copy "+destination)
        configure(copy);result.append(copy)
    return result

def spawn_mesh(mesh,label=None,loc=(0,0,0),scale=(1,1,1),material=None):
    a=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(*loc),unreal.Rotator());a.set_actor_label(label or mesh.get_name());a.set_actor_scale3d(unreal.Vector(*scale));a.static_mesh_component.set_static_mesh(mesh)
    if material:a.static_mesh_component.set_material(0,material)
    return a

def bounds(actors):
    lo=[float("inf")]*3;hi=[float("-inf")]*3
    for a in actors:
        o,e=a.get_actor_bounds(False)
        for i,v in enumerate((o.x,o.y,o.z)):lo[i]=min(lo[i],v-(e.x,e.y,e.z)[i]);hi[i]=max(hi[i],v+(e.x,e.y,e.z)[i])
    return lo,hi,[hi[i]-lo[i] for i in range(3)]

def make_reference_material(name,texture):
    folder=ROOT+"/References";path=folder+"/"+name
    if unreal.EditorAssetLibrary.does_asset_exist(path):return unreal.EditorAssetLibrary.load_asset(path)
    mat=unreal.AssetToolsHelpers.get_asset_tools().create_asset(name,folder,unreal.Material,unreal.MaterialFactoryNew());mat.set_editor_property("shading_model",unreal.MaterialShadingModel.MSM_UNLIT)
    sample=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionTextureSample,-300,0);sample.texture=texture
    unreal.MaterialEditingLibrary.connect_material_property(sample,"RGB",unreal.MaterialProperty.MP_EMISSIVE_COLOR);unreal.MaterialEditingLibrary.recompile_material(mat);unreal.EditorAssetLibrary.save_loaded_asset(mat);return mat

def create_map(ship_name,cfg,meshes,reference_material):
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(cfg["map"]):unreal.EditorAssetLibrary.delete_asset(cfg["map"])
    if not level.new_level(cfg["map"]):raise RuntimeError("Could not create "+cfg["map"])
    actors=[spawn_mesh(m,"SCULPT_WORKING_"+m.get_name()) for m in meshes]
    raw_lo,raw_hi,raw_size=bounds(actors);expected=cfg["dims_cm"]
    correction=[expected[i]/raw_size[i] for i in range(3)]
    for actor in actors:actor.set_actor_scale3d(unreal.Vector(*correction))
    lo,hi,size=bounds(actors);verified=all(abs(size[i]-expected[i])<=max(10,expected[i]*.001) for i in range(3))
    cube=unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
    # EVA and shuttle references remain visually subordinate but make brush scale legible.
    spawn_mesh(cube,"SCALE_EVA_1p8m",(0,-expected[1]*.62,-expected[2]*.45),(.55,.35,1.8))
    spawn_mesh(cube,"SCALE_Shuttle_35m",(expected[0]*.12,-expected[1]*.63,-expected[2]*.40),(35,9,6))
    # Reference sheet is placed as a freestanding unlit board away from the sculpt volume.
    plane=unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane.Plane")
    ref=spawn_mesh(plane,"REFERENCE_ConceptSheet",(0,expected[1]*1.45,0),(expected[0]/100,expected[0]/150,1),reference_material)
    ref.set_actor_rotation(unreal.Rotator(90,0,0),False)
    sun=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,expected[2]),unreal.Rotator(-28,-35,0));sun.set_actor_label("SCULPT_KeyLight");sun.light_component.set_editor_property("intensity",4.0)
    sky=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,expected[2]),unreal.Rotator());sky.set_actor_label("SCULPT_FillLight");sky.light_component.set_editor_property("intensity",.35)
    for label,loc,rot,fov in (("CAM_Sculpt_ThreeQuarter",(expected[0]*.25,-expected[0]*1.35,expected[2]*.65),(0,100,-12),52),("CAM_Sculpt_Side",(0,-expected[0]*1.6,0),(0,90,0),42),("CAM_Sculpt_Drive",(-expected[0]*.55,-expected[1]*1.2,0),(0,45,0),58)):
        cam=unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(unreal.CameraActor,unreal.Vector(*loc),unreal.Rotator(rot[2],rot[1],rot[0]));cam.set_actor_label(label);cam.camera_component.set_editor_property("field_of_view",fov)
    level.save_current_level();return {"map":cfg["map"],"working_directory":cfg["working"],"modules":len(meshes),"raw_import_size_cm":raw_size,"assembly_scale_correction":correction,"bounds_cm":{"min":lo,"max":hi,"size":size},"expected_cm":expected,"scale_verified":verified}

results=[]
for ship_name,cfg in SHIPS.items():
    if not cfg["glb"].exists():raise RuntimeError("Missing sculpt base "+str(cfg["glb"]))
    # Remove generated references in dependency order so reruns stay clean.
    if unreal.EditorAssetLibrary.does_asset_exist(cfg["map"]):unreal.EditorAssetLibrary.delete_asset(cfg["map"])
    if unreal.EditorAssetLibrary.does_directory_exist(cfg["working"]):unreal.EditorAssetLibrary.delete_directory(cfg["working"])
    if unreal.EditorAssetLibrary.does_directory_exist(cfg["dest"]):unreal.EditorAssetLibrary.delete_directory(cfg["dest"])
    import_file(cfg["glb"],cfg["dest"]);meshes=static_meshes(cfg["dest"])
    for m in meshes:configure(m)
    working_meshes=make_working_copies(meshes,cfg["working"])
    tex_dest=ROOT+"/References/"+ship_name;import_file(cfg["concept"],tex_dest)
    textures=[unreal.EditorAssetLibrary.load_asset(p) for p in unreal.EditorAssetLibrary.list_assets(tex_dest,recursive=True,include_folder=False)];textures=[t for t in textures if isinstance(t,unreal.Texture2D)]
    if not textures:raise RuntimeError("Concept texture import failed for "+ship_name)
    results.append(create_map(ship_name,cfg,working_meshes,make_reference_material("M_REF_"+ship_name,textures[0])))

unreal.EditorAssetLibrary.save_directory(ROOT);unreal.EditorAssetLibrary.save_directory(MAP_ROOT)
REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(json.dumps({"version":2,"toolchain":["ModelingToolsEditorMode","GeometryScripting","ScriptableToolsEditorMode","StaticMeshEditorModeling","MeshModelingToolsetExp","MeshPainting"],"workflow":["edit Working/Iteration_01 only; Source is immutable","Voxel Remesh for silhouette only","Sculpt/Smooth/Move brushes at district scale","PolyGroup and Edit Materials for armor breakup","UV and Bake after silhouette approval","Nanite and collision validation on Approved copy"],"ships":results},indent=2),encoding="utf-8")
if not all(r["scale_verified"] for r in results):raise RuntimeError("Unreal sculpt workspace scale validation failed")
unreal.log("Unreal ship sculpt workspaces complete")
