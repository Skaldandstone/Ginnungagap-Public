"""Phase fourteen: 100 steps converting the space-system master into a production map."""
import json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems';MASTER=OUT/'SpaceSystems_Master.blend';MAP=OUT/'SpaceSystems_ProductionMap.blend';PREVIEW=OUT/'SpaceSystems_Phase14_ProductionMap.png';REPORT=OUT/'SpaceSystems_Phase14_ProductionMap.json';MANIFEST=OUT/'SpaceSystems_ProductionMap_Manifest.json';done=[]
def col(n,parent=None):
 c=bpy.data.collections.get(n) or bpy.data.collections.new(n);p=parent or bpy.context.scene.collection
 if c.name not in p.children:p.children.link(c)
 return c
def reg(step,n,role,o=None,sector=None):
 x={'step':step,'name':n,'role':role}
 if sector:x['sector']=sector
 done.append(x)
 if o:o['phase14_step']=step;o['production_role']=role;o['sector']=sector or 'global'
def empty(step,n,role,p,c,sector,display='CUBE',size=1):
 o=bpy.data.objects.get(n) or bpy.data.objects.new(n,None)
 if not o.users_collection:c.objects.link(o)
 o.location=p;o.empty_display_type=display;o.empty_display_size=size;reg(step,n,role,o,sector);return o
def lane(step,n,a,b,c,sector,role):
 curve=bpy.data.curves.get(n+'_Curve') or bpy.data.curves.new(n+'_Curve','CURVE');curve.dimensions='3D';curve.bevel_depth=.025;curve.bevel_resolution=2
 curve.splines.clear();sp=curve.splines.new('BEZIER');sp.bezier_points.add(1);sp.bezier_points[0].co=a;sp.bezier_points[1].co=b
 for p in sp.bezier_points:p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 o=bpy.data.objects.get(n) or bpy.data.objects.new(n,curve)
 if not o.users_collection:c.objects.link(o)
 o['lane_role']=role;o['lane_width']=1200;o['speed_limit']=350;reg(step,n,'navigation_lane',o,sector);return o
def camera(step,n,loc,target,lens,c,sector):
 o=bpy.data.objects.get(n)
 if not o:bpy.ops.object.camera_add(location=loc);o=bpy.context.object;o.name=n
 o.location=loc;o.data.lens=lens;o.data.clip_start=.1;o.data.clip_end=10000;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 for x in list(o.users_collection):x.objects.unlink(o)
 c.objects.link(o);reg(step,n,'gameplay_camera',o,sector);return o
def main():
 s=bpy.context.scene
 if s.get('phase14_steps')==100:raise RuntimeError('Phase 14 already installed')
 anchors={'Ocean':Vector((-22,5,0)),'Forge':Vector((8,-8,0)),'Ice':Vector((-18,-14,0)),'Gas':Vector((20,12,0)),'Belt':Vector((0,29,1))}
 for k,n in [('Ocean','Ocean_World'),('Forge','Volcanic_World'),('Ice','Ice_World'),('Gas','Ringed_Gas_Giant')]:
  if bpy.data.objects.get(n):anchors[k]=bpy.data.objects[n].matrix_world.translation.copy()
 root=col('MAP_Production');systems=col('MAP_Sectors',root);gameplay=col('MAP_Gameplay',root);lighting=col('MAP_Lighting',root);navigation=col('MAP_Navigation',root);cameras=col('MAP_Cameras',root)
 step=1;sector_cols={}
 # 1-5 sector roots.
 for sector,p in anchors.items():sector_cols[sector]=col('MAP_Sector_'+sector,systems);o=empty(step,'SectorRoot_'+sector,'sector_root',p,sector_cols[sector],sector,'PLAIN_AXES',3);o['world_partition_id']=sector.lower();o['always_loaded']=False;step+=1
 # 6-10 sector streaming bounds.
 for sector,p in anchors.items():o=empty(step,'StreamingBounds_'+sector,'streaming_bounds',p,sector_cols[sector],sector,'CUBE',18);o.scale=(1.35,1.35,.8);o['radius']=48000;o['priority']=5;step+=1
 # 11-20 inner and outer streaming cells.
 for sector,p in anchors.items():
  for ring,radius in [('Inner',12),('Outer',30)]:o=empty(step,f'StreamCell_{sector}_{ring}','streaming_cell',p,sector_cols[sector],sector,'SPHERE',radius);o['cell_ring']=ring;o['load_distance']=18000 if ring=='Inner' else 52000;step+=1
 # 21-40 four jump/spawn anchors per sector.
 spawn_roles=['player_arrival','civilian_arrival','cargo_arrival','emergency_arrival']
 for sector,p in anchors.items():
  for i,role in enumerate(spawn_roles):a=i/4*math.tau+.4;o=empty(step,f'Spawn_{sector}_{role.title().replace("_","")}',role,p+Vector((math.cos(a)*14,math.sin(a)*14,2+i)),gameplay,sector,'ARROWS',1.4);o.rotation_euler[2]=a+math.pi;o['safe_radius']=1800;o['spawn_class']='ship';step+=1
 # 41-55 three mission entry points per sector.
 mission_roles=['primary_mission','secondary_mission','dynamic_encounter']
 for sector,p in anchors.items():
  for i,role in enumerate(mission_roles):a=i/3*math.tau+.7;o=empty(step,f'MissionEntry_{sector}_{i+1}',role,p+Vector((math.cos(a)*22,math.sin(a)*22,5+i*2)),gameplay,sector,'CIRCLE',1.2);o['activation_radius']=4200;o['mission_pool']=sector+'_'+role;step+=1
 # 56-65 two reflection/lighting probes per sector.
 for sector,p in anchors.items():
  for i,kind in enumerate(['local_reflection','exposure_reference']):o=empty(step,f'LightingProbe_{sector}_{i+1}',kind,p+Vector(((i*2-1)*7,0,6+i*3)),lighting,sector,'SPHERE',4);o['influence_radius']=18000;o['exposure_bias']=0 if i==0 else -.35;step+=1
 # 66-75 apply ten production LOD/collision policies.
 policies=[('hero_landmarks','P12_HeroLandmarks',0),('defenses','P12_DefenseNetwork',1),('civilian_hubs','P12_CivilianHubs',1),('hero_encounters','P12_HeroEncounters',0),('capital_traffic','P12_CapitalTraffic',0),('phase11_poi','P11_Ocean_POI',2),('phase11_economy','P11_Ocean_Economy',2),('minor_worlds','P10_OceanMinorWorlds',1),('jump_lanes','P10_JumpLaneInfrastructure',0),('background_population','P8_TrafficFleet',2)]
 for policy,cname,lod in policies:
  c=bpy.data.collections.get(cname);count=0
  if c:
   c['production_policy']=policy;c['hlod_layer']=lod
   for o in c.objects:o['production_lod']=lod;o['collision_profile']='SpaceHero' if lod==0 else 'SpaceSimple';count+=1
  reg(step,'Policy_'+policy,'lod_collision_policy',None);done[-1]['objects']=count;step+=1
 # 76-85 two navigable approach splines per sector.
 for sector,p in anchors.items():
  lane(step,f'NavLane_{sector}_Inbound',p+Vector((-36,-22,8)),p+Vector((-8,-5,2)),navigation,sector,'inbound');step+=1
  lane(step,f'NavLane_{sector}_Outbound',p+Vector((8,5,2)),p+Vector((38,24,10)),navigation,sector,'outbound');step+=1
 # 86-90 gameplay cameras.
 for i,(sector,p) in enumerate(anchors.items()):camera(step,f'Camera_Map_{sector}',p+Vector((24,-28,16)),p,58+i*2,cameras,sector);step+=1
 # 91-100 final production-map systems.
 if 'ProductionMap' not in s.view_layers:s.view_layers.new('ProductionMap')
 reg(step,'ProductionMap','view_layer');step+=1
 for n,f in [('MAP_OCEAN',100),('MAP_FORGE',280),('MAP_ICE',460),('MAP_GAS',640),('MAP_BELT',820)]:
  if not s.timeline_markers.get(n):s.timeline_markers.new(n,frame=f)
 reg(step,'Production map markers','cinematic');step+=1
 s.world['production_exposure_profile']='space_system_balanced';s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100
 reg(step,'Production world settings','rendering');step+=1
 audit={'missing_sector_roots':[k for k in anchors if not bpy.data.objects.get('SectorRoot_'+k)],'missing_spawns':[k for k in anchors if not bpy.data.objects.get('Spawn_'+k+'_PlayerArrival')]};reg(step,'Production hierarchy audit','validation');done[-1]['result']=audit;step+=1
 map_cam=camera(step,'Camera_ProductionMapOverview',(38,-48,38),(0,8,2),55,cameras,'global');s.camera=map_cam;step+=1
 reg(step,'Production map preview','rendering');step+=1
 reg(step,'Save editable master','production');step+=1
 reg(step,'Save deployable production map','production');step+=1
 reg(step,'Write production manifest','production');step+=1
 reg(step,'Write phase report','production');step+=1
 if len(done)!=100 or step!=101:raise RuntimeError(f'Phase14 count mismatch: {len(done)}, step {step}')
 for c in (root,systems,gameplay,lighting,navigation,cameras):c['production_map']=True;c['phase']=14
 s['phase14_steps']=100;s['phase14_complete']=True;s['asset_version']='14.0';s['map_status']='production_candidate';ctrl=bpy.data.objects.get('SpaceSystem_MasterController')
 if ctrl:ctrl['production_map']='SpaceSystems_ProductionMap';ctrl['sector_count']=5;ctrl['spawn_count']=20
 summary={'objects':len(bpy.data.objects),'collections':len(bpy.data.collections),'sector_roots':5,'streaming_cells':10,'spawn_anchors':20,'mission_entries':15,'lighting_probes':10,'navigation_lanes':10,'gameplay_cameras':6}
 MANIFEST.write_text(json.dumps({'map':'SpaceSystems_ProductionMap','version':'14.0','status':'production_candidate','sectors':{k:{'anchor':list(v),'streaming_radius':48000,'spawn_count':4,'mission_entries':3} for k,v in anchors.items()},'summary':summary},indent=2),encoding='utf-8');REPORT.write_text(json.dumps({'phase':14,'steps':done,'summary':summary,'audit':audit},indent=2),encoding='utf-8')
 bpy.ops.wm.save_as_mainfile(filepath=str(MASTER));bpy.ops.wm.save_as_mainfile(filepath=str(MAP))
 # Lightweight map overview; the production file retains the full PBR renderer.
 engine=s.render.engine;s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.render.resolution_x=960;s.render.resolution_y=540;s.render.filepath=str(PREVIEW);bpy.ops.render.render(write_still=True);s.render.engine=engine
 print(json.dumps({'phase':14,'completed':len(done),**summary},indent=2))
main()
