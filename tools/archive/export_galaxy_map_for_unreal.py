"""Package the standalone galaxy-map Blender scene for Unreal import."""
import json, sys
from pathlib import Path
import bpy

ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();ART=ROOT/'Art'/'GalaxyMap';EXPORTS=ART/'Exports'
SOURCE=ART/'GalaxyMap_Master.blend';UNREAL_BLEND=ART/'GalaxyMap_Unreal.blend';REGISTRY=ART/'GalaxyMap_SystemRegistry.json';GALAXY=ART/'GalaxyMap_Manifest.json';PACKAGE=EXPORTS/'GalaxyMap_UnrealPackage.json'
LAYERS={'Backdrop':'00_ConceptFoundation','Nodes':'10_StarNodes','Routes':'20_JumpRoutes','Anomalies':'40_Anomalies','Labels':'50_Labels'}

def duplicate_layer(collection_name):
 c=bpy.data.collections.get(collection_name)
 if not c:return []
 result=[]
 for source in c.objects:
  if source.type not in {'MESH','CURVE','FONT'}:continue
  o=source.copy();o.data=source.data.copy();bpy.context.scene.collection.objects.link(o);o.matrix_world=source.matrix_world.copy();o.hide_render=False;o.hide_viewport=False;result.append(o)
 return result
def export_layer(label,collection_name):
 bpy.ops.object.select_all(action='DESELECT');objects=duplicate_layer(collection_name)
 if not objects:raise RuntimeError(f'No export objects in {collection_name}')
 for o in objects:o.select_set(True)
 bpy.context.view_layer.objects.active=objects[0]
 for o in list(objects):
  if o.type!='MESH':bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
 bpy.ops.object.select_all(action='DESELECT');converted=[]
 for o in objects:
  current=bpy.data.objects.get(o.name)
  if current:current.select_set(True);converted.append(current)
 bpy.context.view_layer.objects.active=converted[0]
 if len(converted)>1:bpy.ops.object.join()
 mesh=bpy.context.view_layer.objects.active;mesh.name=f'SM_GalaxyMap_{label}';mesh.data.name=mesh.name;bpy.ops.object.transform_apply(location=False,rotation=True,scale=True);mesh.data.calc_loop_triangles();path=EXPORTS/f'SM_GalaxyMap_{label}.fbx'
 bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'MESH'},apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,bake_anim=False,path_mode='COPY',embed_textures=True)
 info={'layer':label,'fbx':str(path.relative_to(ROOT)).replace('\\','/'),'source_collection':collection_name,'source_objects':len(objects),'vertices':len(mesh.data.vertices),'triangles':len(mesh.data.loop_triangles),'materials':[m.name for m in mesh.data.materials if m]}
 bpy.data.objects.remove(mesh,do_unlink=True);return info
def main():
 EXPORTS.mkdir(parents=True,exist_ok=True);bpy.context.preferences.filepaths.save_version=0;s=bpy.context.scene;s.unit_settings.system='METRIC';s.unit_settings.length_unit='METERS';s['unreal_scale']='1 Blender meter = 100 Unreal centimeters';s['unreal_package']='GalaxyMap_UnrealPackage.json';bpy.ops.wm.save_as_mainfile(filepath=str(UNREAL_BLEND))
 layers=[export_layer(label,name) for label,name in LAYERS.items()];registry=json.loads(REGISTRY.read_text(encoding='utf-8'));galaxy=json.loads(GALAXY.read_text(encoding='utf-8'));placements=[]
 for system in registry['systems']:
  if not system.get('placement') or not system.get('node_id'):continue
  x,y=system['placement']['galaxy_position'];placements.append({'system_id':system['system_id'],'display_name':system['display_name'],'node_id':system['node_id'],'location_cm':[round(x*100,2),round(y*100,2),20.0],'selection_radius_cm':45.0,'system_seed':system['system_seed'],'system_map':system['system_map']})
 package={'schema_version':1,'asset':'Ginnungagap Overall Galaxy Map','source_blend':str(SOURCE.relative_to(ROOT)).replace('\\','/'),'unreal_blend':str(UNREAL_BLEND.relative_to(ROOT)).replace('\\','/'),'unreal_destination':'/Game/Assets/GalaxyMap','level_destination':'/Game/Assets/Maps/Galaxy/L_GalaxyMap','units':'centimeters','layers':layers,'system_placements':placements,'routes':galaxy['routes'],'anomalies':galaxy['anomalies'],'concept_texture':'Content/Assets/SpaceSystems/Source/T_SpaceSky_CosmicRift.png'};PACKAGE.write_text(json.dumps(package,indent=2),encoding='utf-8');print(json.dumps({'layers':len(layers),'systems':len(placements),'routes':len(galaxy['routes']),'package':str(PACKAGE)},indent=2))
main()
