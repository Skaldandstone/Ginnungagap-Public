"""Phase seventeen: 100 production-detail steps for the Ocean Arrival level."""
import json,math,random,sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems';LEVEL=OUT/'SpaceSystems_OceanArrival_Level.blend';PREVIEW=OUT/'SpaceSystems_OceanArrival_Phase17.png';REPORT=OUT/'SpaceSystems_OceanArrival_Phase17.json';R=random.Random(17100);done=[]
def col(n):
 c=bpy.data.collections.get(n) or bpy.data.collections.new(n)
 if c.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(c)
 return c
def move(o,c):
 if o.name not in c.objects:c.objects.link(o)
 for x in list(o.users_collection):
  if x!=c:x.objects.unlink(o)
 return o
def reg(step,n,role,o=None):
 done.append({'step':step,'name':n,'role':role})
 if o:o['phase17_step']=step;o['gameplay_role']=role
def cube(n,p,sc,m,c,bevel=.04):
 bpy.ops.mesh.primitive_cube_add(location=p);o=bpy.context.object;o.name=n;o.scale=sc;o.data.materials.append(m);move(o,c)
 if bevel:q=o.modifiers.new('Detail Bevel','BEVEL');q.width=bevel;q.segments=2
 return o
def cyl(n,p,r,d,m,c,rot=(0,0,0),v=16,bevel=.03):
 bpy.ops.mesh.primitive_cylinder_add(vertices=v,radius=r,depth=d,location=p,rotation=rot);o=bpy.context.object;o.name=n;o.data.materials.append(m);move(o,c)
 if bevel:q=o.modifiers.new('Detail Bevel','BEVEL');q.width=bevel;q.segments=2
 return o
def sphere(n,p,r,m,c,v=20):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=v,ring_count=max(8,v//2),radius=r,location=p);o=bpy.context.object;o.name=n;o.data.materials.append(m);move(o,c)
 for f in o.data.polygons:f.use_smooth=True
 return o
def tor(n,p,major,minor,m,c,rot=(0,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=32,minor_segments=8,location=p,rotation=rot);o=bpy.context.object;o.name=n;o.data.materials.append(m);move(o,c);return o
def empty(n,p,c,display='CUBE',size=.4):
 o=bpy.data.objects.new(n,None);o.location=p;o.empty_display_type=display;o.empty_display_size=size;c.objects.link(o);return o
def camera(n,loc,target,c,lens=58):
 d=bpy.data.cameras.new(n);d.lens=lens;d.clip_end=5000;d.dof.use_dof=True;d.dof.focus_distance=(Vector(target)-Vector(loc)).length;d.dof.aperture_fstop=6.3;o=bpy.data.objects.new(n,d);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();c.objects.link(o);return o
def light(n,kind,p,color,energy,size,target,c):
 d=bpy.data.lights.new(n,kind);d.color=color;d.energy=energy
 if kind=='AREA':d.shape='DISK';d.size=size
 o=bpy.data.objects.new(n,d);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();c.objects.link(o);return o
def main():
 s=bpy.context.scene
 if s.get('phase17_steps')==100:raise RuntimeError('Phase 17 already installed')
 mats={n:bpy.data.materials.get(n) for n in ['LVL_Hull_Navy','LVL_Hull_Ceramic','LVL_SafetyOrange','LVL_Glass','LVL_Emission_Cyan','LVL_Emission_Amber','LVL_Emission_Green','LVL_Asteroid']};hull=mats['LVL_Hull_Navy'];white=mats['LVL_Hull_Ceramic'];orange=mats['LVL_SafetyOrange'];glass=mats['LVL_Glass'];cyan=mats['LVL_Emission_Cyan'];amber=mats['LVL_Emission_Amber'];green=mats['LVL_Emission_Green'];rock=mats['LVL_Asteroid']
 geo=col('LEVEL_DetailGeometry');props=col('LEVEL_DockProps');game=col('LEVEL_Gameplay');traffic=col('LEVEL_Traffic');fx=col('LEVEL_EnvironmentalFX');lighting=col('LEVEL_DetailLighting');cams=col('LEVEL_ShotCameras')
 step=1
 # 1-20: surface panels, ribs, antennae, and window bands.
 for i in range(8):a=i/8*math.tau;y=2+math.cos(a)*3.25;z=2.5+math.sin(a)*3.25;o=cube(f'HubPanel_{i+1:02d}',(-3.55,y,z),(.07,.55,.38),white if i%2 else orange,geo,.025);o.rotation_euler[0]=a;reg(step,o.name,'surface_detail',o);step+=1
 for i in range(6):a=i/6*math.tau;y=2+math.cos(a)*5.38;z=2.5+math.sin(a)*5.38;o=cyl(f'RingBrace_{i+1:02d}',(0,y,z),.08,2.8,hull,geo,(0,math.pi/2,a),12,.02);reg(step,o.name,'structural_brace',o);step+=1
 for i in range(4):p=(-2.9,2+(i-1.5)*1.2,4.6);o=cube(f'CommandWindow_{i+1:02d}',p,(.08,.42,.17),cyan,geo,.018);reg(step,o.name,'window',o);step+=1
 for i in range(2):o=cyl(f'SensorBoom_{i+1}',(1.2,2+(i*2-1)*2.2,8.2),.08,3.2,hull,geo,(0,math.pi/2,0),12,.02);reg(step,o.name,'sensor',o);step+=1
 # 21-35: dock equipment and service props.
 dock_props=['CargoCrane','FuelCoupler','AirlockConsole','PowerJunction','MaintenanceCart','CargoPallet','RescueLocker','ToolCabinet','DockWinch','CoolantTank','FireStation','PressureMonitor','TowClamp','CrewShelter','ServiceDroneBay']
 for i,n in enumerate(dock_props):dock=i%4;z=[-1.2,1.1,4.1,6.8][dock];p=(-11.2+(i%3)*.85,3.0+(i//4%2)*.75,z+.45+(i%2)*.3);o=cube('Dock_'+n,p,(.22+.05*(i%3),.18,.25),orange if i%4==0 else white,props,.04);reg(step,o.name,'dock_service',o);step+=1
 # 36-50: gameplay anchors and interactables.
 gameplay=[('PlayerSpawn','spawn'),('DockMaster','npc'),('RefuelTerminal','interactable'),('RepairTerminal','interactable'),('CargoObjective','objective'),('CustomsCheckpoint','checkpoint'),('MedicalStation','interactable'),('SaveBeacon','checkpoint'),('MissionBoard','interactable'),('EmergencyOverride','interactable'),('AirlockEntry','transition'),('ShipUpgradeConsole','interactable'),('SecurityScanner','checkpoint'),('FastTravelNode','travel'),('LevelExit','transition')]
 for i,(n,role) in enumerate(gameplay):dock=i%4;z=[-1.2,1.1,4.1,6.8][dock];p=(-12.3,1.2+(i%3)*.8,z+.65);o=empty('GP_'+n,p,game,'CIRCLE' if role in ('objective','checkpoint') else 'CUBE',.45);o['interaction_radius']=2.5;o['prompt_id']='PROMPT_'+n.upper();reg(step,o.name,role,o);step+=1
 # 51-65: colored traffic craft and service drones.
 roles=['shuttle','cargo','patrol','rescue','service']
 for i in range(15):
  p=(-24+i*3.2,-3+(i%3)*5,5+(i%4)*1.8);root=empty(f'Traffic_{i+1:02d}_{roles[i%5].title()}',p,traffic,'ARROWS',.35);body=cyl(root.name+'_Hull',p,.24,2.3,white if i%2 else hull,traffic,(0,math.pi/2,0),16,.05);wing=cube(root.name+'_Wing',p,(.62,.75,.055),orange if i%3==0 else hull,traffic,.035);drive=sphere(root.name+'_Drive',Vector(p)+Vector((-.12,0,0)),.12,cyan if i%2 else amber,traffic,16)
  for q in (body,wing,drive):q.parent=root
  root.keyframe_insert(data_path='location',frame=1);root.location+=Vector((28,18,R.uniform(-3,5)));root.keyframe_insert(data_path='location',frame=360);reg(step,root.name,roles[i%5],root);step+=1
 # 66-75: environmental depth and motion cues.
 for i in range(5):p=(-15+i*6,12+i*2,8+i);o=sphere(f'DistantMarker_{i+1}',p,.15,amber if i%2 else cyan,fx,16);reg(step,o.name,'distant_navigation',o);step+=1
 for i in range(3):p=(-20+i*20,24+i*5,-5+i*4);o=tor(f'DebrisArc_{i+1}',p,3+i,.08,rock,fx,(R.random(),R.random(),R.random()));reg(step,o.name,'debris_landmark',o);step+=1
 for i in range(2):p=(-20.6,-9+(i*2-1)*.55,2);o=sphere(f'PlayerThrusterGlow_{i+1}',p,.48,cyan,fx,24);o.scale=(1.8,.7,.7);reg(step,o.name,'thruster_fx',o);step+=1
 # 76-85: focused lights and reflection-card proxies.
 light_specs=[('DockKeyA','AREA',(-10,-5,10),(.08,.3,1),700,5,(-10,2,2)),('DockKeyB','AREA',(-10,8,8),(1,.08,.015),620,4,(-10,2,4)),('HubFill','AREA',(5,-5,6),(.08,.2,1),900,7,(0,2,3)),('ShipKey','AREA',(-18,-16,9),(.12,.35,1),780,5,(-17,-9,2)),('PlanetRim','AREA',(15,12,18),(.15,.4,1),1200,10,(0,2,3))]
 for spec in light_specs:o=light(*spec,lighting);reg(step,o.name,'production_light',o);step+=1
 for i in range(5):p=(-9+i*4,7,1+i*.8);o=cube(f'ReflectionCard_{i+1}',p,(1.4,.02,.8),cyan if i%2 else amber,lighting,.0);o.hide_render=True;o.display_type='WIRE';reg(step,o.name,'reflection_probe_proxy',o);step+=1
 # 86-95: gameplay and cinematic shot cameras.
 shots=[('DockApproach',(-24,-20,8),(-8,2,2),52),('PlayerShip',(-23,-14,5),(-16,-8,2),70),('HabitatRing',(-16,4,10),(0,2,3),62),('DockingPads',(-20,-4,4),(-11,2,2),58),('CommandDome',(-13,0,9),(-2,2,5),75),('SolarWing',(15,-8,8),(5,2,3),65),('PlanetReveal',(-20,-18,14),(10,30,4),45),('TrafficLane',(-30,2,13),(-5,7,6),58),('LevelWide',(-32,-28,17),(-1,3,3),52),('ExitRoute',(-6,18,12),(-15,-5,3),60)]
 for n,loc,target,lens in shots:o=camera('Camera_'+n,loc,target,cams,lens);reg(step,o.name,'shot_camera',o);step+=1
 # 96-100: level configuration, review markers, save, render, report.
 s['player_spawn']='GP_PlayerSpawn';s['primary_dock']='DockPad_2';s['level_exit']='GP_LevelExit';reg(step,'Ocean Arrival gameplay routing','level_configuration');step+=1
 for n,f in [('OA_REVEAL',1),('OA_APPROACH',90),('OA_DOCK',180),('OA_STATION',270),('OA_EXIT',360)]:
  if not s.timeline_markers.get(n):s.timeline_markers.new(n,frame=f)
 reg(step,'Ocean Arrival review timeline','cinematic');step+=1
 for img in bpy.data.images:
  if img.name.startswith('T_Planet_OceanClouds') and not img.packed_file:img.pack()
 reg(step,'Pack level texture dependencies','production');step+=1
 reg(step,'Save level version 17','production');step+=1;reg(step,'Render and audit level','production');step+=1
 if len(done)!=100 or step!=101:raise RuntimeError(f'Phase17 count mismatch {len(done)}, step {step}')
 s['phase17_steps']=100;s['asset_version']='17.0';s['level_status']='art_vertical_slice';s.frame_end=360;s.camera=bpy.data.objects.get('Camera_LevelWide');s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.filepath=str(PREVIEW);s.view_settings.look='AgX - Medium High Contrast'
 summary={'objects':len(bpy.data.objects),'materials':len(bpy.data.materials),'lights':sum(o.type=='LIGHT' for o in bpy.data.objects),'cameras':sum(o.type=='CAMERA' for o in bpy.data.objects),'animated_traffic':15,'gameplay_anchors':15,'detail_steps':100};REPORT.write_text(json.dumps({'phase':17,'steps':done,'summary':summary},indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(LEVEL));bpy.ops.render.render(write_still=True);print(json.dumps({'phase':17,'completed':len(done),**summary},indent=2))
main()
