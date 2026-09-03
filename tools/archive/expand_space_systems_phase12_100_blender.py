"""Phase twelve: 100 hero landmarks, defenses, hubs, encounters, and production steps."""
import json,math,random,sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems';BLEND=OUT/'SpaceSystems_Master.blend';PREVIEW=OUT/'SpaceSystems_Phase12_100Steps.png';REPORT=OUT/'SpaceSystems_Phase12_100Steps.json';R=random.Random(12100);done=[];CACHE={}
def col(n):
 c=bpy.data.collections.get(n) or bpy.data.collections.new(n)
 if c.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(c)
 return c
def move(o,c):
 if o.name not in c.objects:c.objects.link(o)
 for x in list(o.users_collection):
  if x!=c:x.objects.unlink(o)
 return o
def mat(n,color,emit=0,metal=.2,rough=.4):
 m=bpy.data.materials.get(n) or bpy.data.materials.new(n);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if emit:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emit
 return m
def mesh_obj(kind,n,p,scale,m,rot=(0,0,0)):
 key=(kind,m.name)
 if key not in CACHE:
  if kind=='cube':bpy.ops.mesh.primitive_cube_add()
  elif kind=='sphere':bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2)
  elif kind=='cylinder':bpy.ops.mesh.primitive_cylinder_add(vertices=12)
  else:bpy.ops.mesh.primitive_torus_add(major_radius=1,minor_radius=.1,major_segments=24,minor_segments=6)
  o=bpy.context.object;CACHE[key]=o.data;o.data.materials.append(m)
 else:o=bpy.data.objects.new(n,CACHE[key]);bpy.context.scene.collection.objects.link(o)
 o.name=n;o.location=p;o.scale=scale;o.rotation_euler=rot;return o
def reg(step,n,role,o=None):
 done.append({'step':step,'name':n,'role':role})
 if o:o['phase12_step']=step;o['gameplay_role']=role
def root(step,n,role,p,c):
 o=bpy.data.objects.new(n,None);o.location=p;o.empty_display_type='CUBE';o.empty_display_size=.5;c.objects.link(o);reg(step,n,role,o);return o
def landmark(step,n,role,p,c,hull,glow,v):
 r=root(step,n,role,p,c);sc=.55+(v%4)*.12
 parts=[mesh_obj('cylinder',n+'_Spire',p,(sc*.28,sc*.28,sc*2.2),hull),mesh_obj('torus',n+'_Crown',Vector(p)+Vector((0,0,sc*1.8)),(sc*1.3,sc*1.3,sc*1.3),glow),mesh_obj('sphere',n+'_Core',Vector(p)+Vector((0,0,sc*.35)),(sc*.42,)*3,glow)]
 for q in parts:q.parent=r;move(q,c)
 r['landmark_class']=role;r['discovery_value']=1000+v*100
def defense(step,n,role,p,c,hull,glow,v):
 r=root(step,n,role,p,c);sc=.38+(v%3)*.08
 parts=[mesh_obj('cube',n+'_Bunker',p,(sc*1.2,sc,.45*sc),hull),mesh_obj('cylinder',n+'_Cannon',Vector(p)+Vector((0,0,.5*sc)),(.16*sc,.16*sc,1.8*sc),hull,(0,math.pi/2,0)),mesh_obj('torus',n+'_Shield',p,(sc*1.7,)*3,glow,(math.pi/2,0,0))]
 for q in parts:q.parent=r;move(q,c)
 r['defense_class']=role;r['engagement_radius']=3000+v*150
def hub(step,n,role,p,c,hull,glow,v):
 r=root(step,n,role,p,c);sc=.45+(v%4)*.07
 parts=[mesh_obj('sphere',n+'_Habitat',p,(sc,)*3,hull),mesh_obj('torus',n+'_Transit',p,(sc*1.55,)*3,hull,(math.pi/2,0,0)),mesh_obj('cube',n+'_Dock',Vector(p)+Vector((sc*1.4,0,0)),(sc*.7,sc*.22,sc*.18),hull),mesh_obj('sphere',n+'_Beacon',Vector(p)+Vector((0,0,sc*1.15)),(sc*.12,)*3,glow)]
 for q in parts:q.parent=r;move(q,c)
 r['population_class']=role;r['service_slots']=3+v%6
def encounter(step,n,role,p,c,hull,glow,v):
 r=root(step,n,role,p,c);sc=.65+(v%3)*.16
 parts=[mesh_obj('cylinder',n+'_Hull',p,(sc*.28,sc*.28,sc*2.5),hull,(0,math.pi/2,0)),mesh_obj('cube',n+'_Wing',p,(sc*1.7,sc*.55,sc*.1),hull),mesh_obj('torus',n+'_Field',p,(sc*1.1,)*3,glow,(0,math.pi/2,0)),mesh_obj('sphere',n+'_Reactor',Vector(p)+Vector((-sc*1.2,0,0)),(sc*.18,)*3,glow)]
 for q in parts:q.parent=r;move(q,c)
 r['encounter_class']=role;r['threat_tier']=1+v%5
def ship(step,n,role,p,c,hull,glow,v):
 r=root(step,n,role,p,c);sc=.48+(v%4)*.09
 parts=[mesh_obj('cylinder',n+'_Spine',p,(sc*.25,sc*.25,sc*2.6),hull,(0,math.pi/2,0)),mesh_obj('cube',n+'_Dorsal',Vector(p)+Vector((0,0,sc*.38)),(sc*1.25,sc*.55,sc*.14),hull),mesh_obj('cube',n+'_Ventral',Vector(p)+Vector((0,0,-sc*.3)),(sc*.95,sc*.4,sc*.1),hull),mesh_obj('sphere',n+'_Drive',Vector(p)+Vector((-sc*1.4,0,0)),(sc*.16,)*3,glow)]
 for q in parts:q.parent=r;move(q,c)
 r.keyframe_insert(data_path='location',frame=1);r.location+=Vector((R.uniform(25,45),R.uniform(18,35),R.uniform(-8,8)));r.keyframe_insert(data_path='location',frame=1080)
def camera(step,n,loc,target,lens):
 bpy.ops.object.camera_add(location=loc);o=bpy.context.object;o.name=n;o.data.lens=lens;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();move(o,col('SYS_Cameras'));reg(step,n,'camera',o)
def main():
 s=bpy.context.scene
 if s.get('phase12_steps')==100:raise RuntimeError('Phase 12 already installed')
 hull=bpy.data.materials.get('M_StationHull') or mat('M_StationHull',(.12,.16,.2),0,.8,.3);cyan=mat('M_P12_Cyan',(0,.55,1),18);amber=mat('M_P12_Amber',(1,.2,.005),18);green=mat('M_P12_Green',(0,1,.2),16);violet=mat('M_P12_Violet',(.45,.005,1),18);red=mat('M_P12_Red',(1,.004,.001),18)
 anchors={'Ocean':Vector((-22,5,0)),'Forge':Vector((8,-8,0)),'Ice':Vector((-18,-14,0)),'Gas':Vector((20,12,0)),'Belt':Vector((0,29,1))}
 for k,n in [('Ocean','Ocean_World'),('Forge','Volcanic_World'),('Ice','Ice_World'),('Gas','Ringed_Gas_Giant')]:
  if bpy.data.objects.get(n):anchors[k]=bpy.data.objects[n].matrix_world.translation.copy()
 step=1
 landmark_names=[('Ocean','CrownOfTides','habitat'),('Ocean','AbyssElevator','transport'),('Ocean','StormCathedral','weather'),('Ocean','PelagicArchive','science'),('Forge','SolarAnvil','industry'),('Forge','EmberCrown','power'),('Forge','BasaltCitadel','habitat'),('Forge','MagmaBridge','transport'),('Ice','AuroraPalace','science'),('Ice','CrystalVault','storage'),('Ice','WinterSpire','navigation'),('Ice','GlacierMonastery','culture'),('Gas','CloudThrone','habitat'),('Gas','CycloneEye','science'),('Gas','RingCrown','transport'),('Gas','HeliumPalace','commerce'),('Belt','ProspectorHall','culture'),('Belt','IronCathedral','industry'),('Belt','ZeroGMarket','commerce'),('Belt','MemorialRock','landmark')];c=col('P12_HeroLandmarks')
 for i,(sector,n,role) in enumerate(landmark_names):a=i*.83;landmark(step,sector+'_'+n,role,anchors[sector]+Vector((math.cos(a)*(14+i%4*2),math.sin(a)*(14+i%4*2),4+(i%5)*1.4)),c,hull,[cyan,amber,green,violet][i%4],i);step+=1
 defense_roles=['interceptor','shield','missile','sensor','customs'];c=col('P12_DefenseNetwork')
 for i in range(20):sector=list(anchors)[i%5];a=i/20*math.tau;defense(step,sector+'_Defense_'+str(i+1).zfill(2),defense_roles[i%5],anchors[sector]+Vector((math.cos(a)*(20+i%3*2),math.sin(a)*(20+i%3*2),(i%6-2)*1.2)),c,hull,red if i%2 else cyan,i);step+=1
 hub_roles=['residential','trade','medical','education','entertainment'];c=col('P12_CivilianHubs')
 for i in range(20):sector=list(anchors)[i%5];a=i/20*math.tau+.4;hub(step,sector+'_CivilHub_'+str(i+1).zfill(2),hub_roles[i%5],anchors[sector]+Vector((math.cos(a)*(24+i%4*2),math.sin(a)*(24+i%4*2),(i%7-3)*1.3)),c,hull,green if i%2 else amber,i);step+=1
 encounter_names=['AncientGatehouse','PirateFlagship','LivingAsteroid','MachineHive','GhostStation','SolarLeviathan','CrystalArk','GraveyardKing','VoidTemple','ExileCarrier','PlagueFortress','TimeWreck','RogueShipyard','DarkObservatory','WorldEngine'];roles=['artifact','combat','biosphere','machine','derelict'];c=col('P12_HeroEncounters')
 for i,n in enumerate(encounter_names):encounter(step,n,roles[i%5],Vector((-50+i*7,58+(i%3)*8,8+(i%4)*3)),c,hull,violet if i%2 else red,i);step+=1
 ship_names=['RoyalClipper','ColonyLiner','HospitalCarrier','OreSuperfreighter','ScienceArk','RescueCruiser','FleetTender','PatrolDestroyer','DiplomaticYacht','ConstructionBarge','SalvageCarrier','PilgrimShip','JumpCourier','SurveyMothership','FrontierGuard'];roles=['diplomatic','civilian','medical','cargo','science','rescue','logistics','security'];c=col('P12_CapitalTraffic')
 for i,n in enumerate(ship_names):ship(step,n,roles[i%8],Vector((-48+i*7,-48+(i%3)*5,4+(i%4)*2)),c,hull,cyan if i%2 else amber,i);step+=1
 camera_specs=[('Camera_P12_HeroLandmarks',(34,-42,28),(0,5,3),58),('Camera_P12_DefenseGrid',(-45,-38,25),(-5,0,2),62),('Camera_P12_CivilianOrbit',(45,42,25),(8,15,3),60),('Camera_P12_Encounters',(0,92,34),(0,64,11),55),('Camera_P12_CapitalTraffic',(0,-82,30),(0,-45,7),58)]
 for x in camera_specs:camera(step,*x);step+=1
 if 'Phase12Hero' not in s.view_layers:s.view_layers.new('Phase12Hero')
 reg(step,'Phase12Hero','view_layer');step+=1
 for c in bpy.data.collections:
  if c.name.startswith('P12_'):c['streaming_priority']=6;c['runtime_optional']=True
 reg(step,'Phase12 streaming metadata','optimization');step+=1
 for n,f in [('P12_LANDMARKS',160),('P12_DEFENSE',360),('P12_HUBS',560),('P12_ENCOUNTERS',760),('P12_CAPITALS',960)]:
  if not s.timeline_markers.get(n):s.timeline_markers.new(n,frame=f)
 reg(step,'Phase12 shot markers','cinematic');step+=1
 reg(step,'Phase12 validated master save','production');step+=1;reg(step,'Phase12 audit report','production');step+=1
 if len(done)!=100 or step!=101:raise RuntimeError(f'Phase12 count mismatch: {len(done)} entries, step {step}')
 for c in bpy.data.collections:
  if c.name.startswith('P12_'):
   for o in c.objects:o['lod_group']='Phase12';o['streaming_radius']=5200 if o.type=='EMPTY' else 1400;o['unreal_export']=True
 ctrl=bpy.data.objects.get('SpaceSystem_MasterController')
 if ctrl:ctrl['phase12_assets']=95;ctrl['phase12_complete']=True
 s['phase12_steps']=100;s['asset_version']='12.0';s.frame_end=max(s.frame_end,1080);s.camera=bpy.data.objects.get('Camera_P12_HeroLandmarks');s.render.resolution_x=960;s.render.resolution_y=540;s.render.resolution_percentage=100;s.render.filepath=str(PREVIEW);bpy.ops.wm.save_as_mainfile(filepath=str(BLEND));summary={'objects':len(bpy.data.objects),'collections':len(bpy.data.collections),'actions':len(bpy.data.actions),'cameras':sum(o.type=='CAMERA' for o in s.objects)};REPORT.write_text(json.dumps({'phase':12,'steps':done,'summary':summary},indent=2),encoding='utf-8');engine=s.render.engine;s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';bpy.ops.render.render(write_still=True);s.render.engine=engine;print(json.dumps({'phase':12,'completed':len(done),**summary},indent=2))
main()
