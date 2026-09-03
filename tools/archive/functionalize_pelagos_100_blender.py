"""Phase nineteen: 100 functional gameplay and production steps for Pelagos Orbital Arrival."""
import json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems';LEVEL=OUT/'SpaceSystems_PelagosOrbitalArrival_Level.blend';PREVIEW=OUT/'SpaceSystems_PelagosOrbitalArrival_Phase19.png';REPORT=OUT/'SpaceSystems_PelagosOrbitalArrival_Phase19.json';done=[]
def col(n):
 c=bpy.data.collections.get(n) or bpy.data.collections.new(n)
 if c.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(c)
 return c
def move(o,c):
 if o.name not in c.objects:c.objects.link(o)
 for x in list(o.users_collection):
  if x!=c:x.objects.unlink(o)
 return o
def reg(step,n,role,o=None,**data):
 item={'step':step,'name':n,'role':role,**data};done.append(item)
 if o:
  o['phase19_step']=step;o['gameplay_role']=role
  for k,v in data.items():o[k]=v
def empty(n,p,c,display='CUBE',size=.4):
 o=bpy.data.objects.new(n,None);o.location=p;o.empty_display_type=display;o.empty_display_size=size;c.objects.link(o);return o
def cube(n,p,sc,m,c,bevel=.035):
 bpy.ops.mesh.primitive_cube_add(location=p);o=bpy.context.object;o.name=n;o.scale=sc;o.data.materials.append(m);move(o,c)
 if bevel:q=o.modifiers.new('Gameplay Bevel','BEVEL');q.width=bevel;q.segments=2
 return o
def cyl(n,p,r,d,m,c,rot=(0,0,0),v=16):
 bpy.ops.mesh.primitive_cylinder_add(vertices=v,radius=r,depth=d,location=p,rotation=rot);o=bpy.context.object;o.name=n;o.data.materials.append(m);move(o,c);q=o.modifiers.new('Gameplay Bevel','BEVEL');q.width=.025;q.segments=2;return o
def sphere(n,p,r,m,c,v=16):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=v,ring_count=max(8,v//2),radius=r,location=p);o=bpy.context.object;o.name=n;o.data.materials.append(m);move(o,c);return o
def curve(n,pts,m,c,width=.025):
 d=bpy.data.curves.new(n+'_Curve','CURVE');d.dimensions='3D';d.bevel_depth=width;d.bevel_resolution=2;d.materials.append(m);sp=d.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for p,co in zip(sp.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 o=bpy.data.objects.new(n,d);c.objects.link(o);return o
def camera(n,loc,target,c,lens=62):
 d=bpy.data.cameras.new(n);d.lens=lens;d.clip_end=5000;d.dof.use_dof=True;d.dof.focus_distance=(Vector(target)-Vector(loc)).length;d.dof.aperture_fstop=6.3;o=bpy.data.objects.new(n,d);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();c.objects.link(o);return o
def main():
 s=bpy.context.scene
 if s.get('phase19_steps')==100:raise RuntimeError('Phase 19 already installed')
 hull=bpy.data.materials.get('LVL_Hull_Navy');white=bpy.data.materials.get('LVL_Hull_Ceramic');orange=bpy.data.materials.get('LVL_SafetyOrange');cyan=bpy.data.materials.get('LVL_Emission_Cyan');amber=bpy.data.materials.get('LVL_Emission_Amber');green=bpy.data.materials.get('LVL_Emission_Green')
 docking=col('LEVEL_DockingGameplay');flow=col('LEVEL_ArrivalFlow');traffic=col('LEVEL_TrafficLogic');safety=col('LEVEL_EmergencySystems');services=col('LEVEL_StationServices');hud=col('LEVEL_HUDAnchors');cams=col('LEVEL_GameplayCameras')
 step=1
 # 1-20: five operational pieces for each of four docks.
 for dock,z in enumerate([-1.2,1.1,4.1,6.8],1):
  p=(-13.0,2,z+.2);o=cyl(f'Dock{dock}_HardClamp',p,.18,1.4,hull,docking,(0,math.pi/2,0));reg(step,o.name,'docking_clamp',o,dock_id=dock);step+=1
  o=cube(f'Dock{dock}_SoftCapture',(-13.7,2,z+.2),(.18,.72,.72),white,docking,.06);reg(step,o.name,'soft_capture',o,dock_id=dock);step+=1
  o=sphere(f'Dock{dock}_AlignmentLight',(-14.1,2,z+.85),.13,green if dock!=3 else amber,docking);reg(step,o.name,'alignment_light',o,dock_id=dock);step+=1
  o=empty(f'Dock{dock}_CaptureTrigger',(-14.5,2,z+.2),docking,'SPHERE',1.1);reg(step,o.name,'capture_trigger',o,dock_id=dock,trigger_radius=2.2);step+=1
  o=empty(f'Dock{dock}_ReleaseTrigger',(-11.8,2,z+.2),docking,'CIRCLE',.7);reg(step,o.name,'release_trigger',o,dock_id=dock,requires_clearance=True);step+=1
 # 21-40: arrival-state checkpoints and sequencer events.
 states=[('JumpFlash',(-32,-15,3)),('SensorAcquire',(-29,-14,3)),('IFFChallenge',(-26,-12,3)),('TrafficContact',(-23,-10,3)),('ControlHandoff',(-20,-8,3)),('SpeedRestriction',(-18,-7,3)),('LaneMerge',(-16,-6,3)),('StationGreeting',(-14,-5,3)),('DockRequest',(-12,-4,3)),('DockAssignment',(-10,-3,3)),('ApproachStart',(-9,-2,3)),('AlignmentCheck',(-8,-1,3)),('FinalApproach',(-7,0,3)),('SoftCapture',(-6,1,3)),('HardDock',(-5,2,3)),('PressureEqualize',(-4,2,3)),('ServiceAvailable',(-3,2,3)),('MissionUpdate',(-2,2,3)),('FreeFlightRestore',(-1,2,3)),('ArrivalComplete',(0,2,3))]
 for i,(n,p) in enumerate(states):o=empty('Flow_'+n,p,flow,'CIRCLE',.45);reg(step,o.name,'arrival_state',o,state_order=i+1,event='On'+n,auto_advance=i not in (2,8,11,14));step+=1
 # 41-55: traffic control nodes and holding patterns.
 for i in range(10):a=i/10*math.tau;p=(-22+math.cos(a)*8,-3+math.sin(a)*8,7+(i%3)*2);o=empty(f'TrafficNode_{i+1:02d}',p,traffic,'ARROWS',.5);reg(step,o.name,'traffic_node',o,node_index=i+1,max_occupancy=1);step+=1
 for i in range(3):a=i/3*math.tau;pts=[(-20+math.cos(a+j*.8)*(10+i*3),8+math.sin(a+j*.8)*(10+i*3),10+i*3) for j in range(5)];o=curve(f'HoldingPattern_{i+1}',pts,amber if i==2 else cyan,traffic,.025);reg(step,o.name,'holding_pattern',o,priority=i+1);step+=1
 o=empty('TrafficConflictResolver',(-12,5,13),traffic,'PLAIN_AXES',1);reg(step,o.name,'traffic_logic',o,resolution_mode='altitude_then_time');step+=1
 o=empty('TrafficSpawnBudget',(-12,5,15),traffic,'PLAIN_AXES',1);reg(step,o.name,'traffic_budget',o,max_ships=18,max_near_dock=4);step+=1
 # 56-70: hazards, emergency response, and rescue systems.
 hazards=[('JumpShear',(-28,-15,3),5),('StationCollision',(0,2,3),8),('PlanetGravity',(16,38,4),16),('TrafficCrossing',(-12,-3,4),5),('SolarGlare',(8,18,12),7)]
 for n,p,r in hazards:o=empty('Hazard_'+n,p,safety,'SPHERE',r);reg(step,o.name,'hazard_volume',o,hazard_type=n,warning_distance=r*1000);step+=1
 response=[('RescueSpawn',(-9,9,8),'rescue_spawn'),('EmergencyDock',(-13,2,6.8),'emergency_dock'),('TowStart',(-18,3,7),'tow_anchor'),('EvacuationPoint',(-4,8,4),'evacuation'),('MedicalHandoff',(-10,2,6.8),'medical'),('DistressRelay',(-2,8,11),'communications'),('FireSuppression',(-11,2,4.8),'fire_response'),('HullBreachTeam',(-9,2,4.8),'repair_response'),('QuarantineHold',(-16,8,9),'quarantine'),('EmergencyExit',(-22,15,12),'emergency_lane')]
 for n,p,role in response:o=empty('Emergency_'+n,p,safety,'CUBE',.7);reg(step,o.name,role,o,response_time=30);step+=1
 # 71-85: station services available after docking.
 service_defs=[('Refuel','fuel',120),('Repair','repair',180),('Medical','medical',60),('Cargo','cargo',150),('Customs','customs',45),('CrewTransfer','passenger',90),('ShipUpgrade','upgrade',240),('MissionBoard','missions',0),('Market','commerce',0),('NavigationData','navigation',30),('SalvageSale','salvage',60),('Insurance','insurance',0),('Resupply','supplies',90),('Quarantine','quarantine',300),('FastTravel','travel',0)]
 for i,(n,role,duration) in enumerate(service_defs):dock=i%4;z=[-1.2,1.1,4.1,6.8][dock];o=empty('Service_'+n,(-11.5,3.4,z+.5),services,'CUBE',.5);reg(step,o.name,'station_service',o,service_type=role,duration_seconds=duration,dock_id=dock+1);step+=1
 # 86-95: HUD anchors and gameplay cameras.
 hud_defs=[('JumpGateLabel',(-31,-15,7)),('StationLabel',(0,2,12)),('DockLabel',(-13,2,8)),('PlanetLabel',(16,38,18)),('ObjectiveMarker',(-8,0,4))]
 for n,p in hud_defs:o=empty('HUD_'+n,p,hud,'CIRCLE',.5);reg(step,o.name,'hud_anchor',o,widget='W_'+n);step+=1
 shots=[('ArrivalPilot',(-24,-16,7),(-10,-3,3),58),('DockingPilot',(-18,-7,5),(-12,2,3),70),('TrafficControl',(-16,10,15),(-12,-2,6),62),('EmergencyOverview',(-22,14,18),(-5,3,5),55),('StationServices',(-18,0,8),(-10,2,3),75)]
 for n,loc,target,lens in shots:o=camera('Camera_'+n,loc,target,cams,lens);reg(step,o.name,'gameplay_camera',o,camera_mode=n);step+=1
 # 96-100: route graph, validation, save, render, report.
 graph={'states':[x[0] for x in states],'start':'JumpFlash','complete':'ArrivalComplete','manual_gates':['IFFChallenge','DockRequest','AlignmentCheck','HardDock']};s['arrival_state_graph']=json.dumps(graph);reg(step,'Pelagos arrival state graph','gameplay_configuration');step+=1
 for n,f in [('P19_JUMP',1),('P19_HANDOFF',72),('P19_REQUEST',126),('P19_CAPTURE',180),('P19_SERVICES',240)]:
  if not s.timeline_markers.get(n):s.timeline_markers.new(n,frame=f)
 reg(step,'Pelagos functional timeline','cinematic');step+=1
 validation={'dock_clamps':sum(o.name.endswith('HardClamp') for o in bpy.data.objects),'arrival_states':sum(o.name.startswith('Flow_') for o in bpy.data.objects),'traffic_nodes':sum(o.name.startswith('TrafficNode_') for o in bpy.data.objects),'emergency_assets':sum(o.name.startswith('Emergency_') for o in bpy.data.objects),'services':sum(o.name.startswith('Service_') for o in bpy.data.objects)};reg(step,'Pelagos gameplay validation','validation',None,**validation);step+=1
 reg(step,'Save Pelagos version 19','production');step+=1;reg(step,'Render and report Pelagos','production');step+=1
 if len(done)!=100 or step!=101:raise RuntimeError(f'Phase19 count mismatch {len(done)}, step {step}')
 s['phase19_steps']=100;s['asset_version']='19.0';s['level_status']='functional_gameplay_map';s.camera=bpy.data.objects.get('Camera_DockingPilot');s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.filepath=str(PREVIEW);s.view_settings.look='AgX - Medium High Contrast';summary={'objects':len(bpy.data.objects),'collections':len(bpy.data.collections),'cameras':sum(o.type=='CAMERA' for o in bpy.data.objects),'actions':len(bpy.data.actions),**validation};REPORT.write_text(json.dumps({'phase':19,'steps':done,'state_graph':graph,'summary':summary},indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(LEVEL));bpy.ops.render.render(write_still=True);print(json.dumps({'phase':19,'completed':len(done),**summary},indent=2))
main()
