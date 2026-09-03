"""Phase eighteen: rename and operationalize Pelagos Orbital Arrival."""
import json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems';LEVEL=OUT/'SpaceSystems_PelagosOrbitalArrival_Level.blend';PREVIEW=OUT/'SpaceSystems_PelagosOrbitalArrival_Beauty.png';REPORT=OUT/'SpaceSystems_PelagosOrbitalArrival_Report.json';MANIFEST=OUT/'SpaceSystems_PelagosOrbitalArrival_Manifest.json';done=[]
def col(n):
 c=bpy.data.collections.get(n) or bpy.data.collections.new(n)
 if c.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(c)
 return c
def move(o,c):
 if o.name not in c.objects:c.objects.link(o)
 for x in list(o.users_collection):
  if x!=c:x.objects.unlink(o)
 return o
def reg(n,role,o=None,**data):
 item={'index':len(done)+1,'name':n,'role':role,**data};done.append(item)
 if o:
  o['phase18_index']=item['index'];o['functional_role']=role
  for k,v in data.items():o[k]=v
def empty(n,p,c,role,display='CUBE',size=1,**data):
 o=bpy.data.objects.get(n) or bpy.data.objects.new(n,None)
 if not o.users_collection:c.objects.link(o)
 o.location=p;o.empty_display_type=display;o.empty_display_size=size;reg(n,role,o,**data);return o
def cube(n,p,sc,m,c,role,bevel=.05,**data):
 bpy.ops.mesh.primitive_cube_add(location=p);o=bpy.context.object;o.name=n;o.scale=sc;o.data.materials.append(m);move(o,c)
 if bevel:q=o.modifiers.new('Production Bevel','BEVEL');q.width=bevel;q.segments=3
 reg(n,role,o,**data);return o
def sphere(n,p,r,m,c,role,seg=32,**data):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=seg//2,radius=r,location=p);o=bpy.context.object;o.name=n;o.data.materials.append(m);move(o,c)
 for f in o.data.polygons:f.use_smooth=True
 reg(n,role,o,**data);return o
def torus(n,p,major,minor,m,c,role,rot=(0,0,0),**data):
 bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=64,minor_segments=12,location=p,rotation=rot);o=bpy.context.object;o.name=n;o.data.materials.append(m);move(o,c);reg(n,role,o,**data);return o
def curve(n,pts,m,c,role,width=.035,**data):
 d=bpy.data.curves.new(n+'_Curve','CURVE');d.dimensions='3D';d.bevel_depth=width;d.bevel_resolution=3;d.materials.append(m);sp=d.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for p,co in zip(sp.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 o=bpy.data.objects.new(n,d);c.objects.link(o);reg(n,role,o,**data);return o
def camera(n,loc,target,c,lens=52):
 d=bpy.data.cameras.new(n);d.lens=lens;d.clip_end=5000;d.dof.use_dof=True;d.dof.focus_distance=(Vector(target)-Vector(loc)).length;d.dof.aperture_fstop=7.1;o=bpy.data.objects.new(n,d);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();c.objects.link(o);reg(n,'camera',o);return o
def main():
 s=bpy.context.scene
 if s.get('phase18_complete'):raise RuntimeError('Phase 18 already installed')
 hull=bpy.data.materials.get('LVL_Hull_Navy');white=bpy.data.materials.get('LVL_Hull_Ceramic');orange=bpy.data.materials.get('LVL_SafetyOrange');cyan=bpy.data.materials.get('LVL_Emission_Cyan');amber=bpy.data.materials.get('LVL_Emission_Amber');green=bpy.data.materials.get('LVL_Emission_Green');ocean=bpy.data.materials.get('LVL_OceanPlanet')
 functional=col('LEVEL_FunctionalMap');arrival=col('LEVEL_ArrivalSystem');docking=col('LEVEL_DockingSystem');navigation=col('LEVEL_NavigationSystem');hazards=col('LEVEL_SafetyVolumes');planet=col('LEVEL_PelagosCues');cams=col('LEVEL_FunctionalCameras')
 # Rename visible and metadata-level identity.
 reg('Pelagos Orbital Arrival','level_identity',None,previous_name='Ocean Arrival');s['level_name']='Pelagos Orbital Arrival';s['destination_world']='Pelagos';s['environment']='high_orbit'
 # Jump exit gate and energy geometry.
 torus('PelagosJumpGate_Outer',(-31,-15,3),4.2,.34,hull,arrival,'jump_gate_hull',(0,math.pi/2,0),gate_id='PELAGOS_GATE_A')
 torus('PelagosJumpGate_Inner',(-31,-15,3),3.35,.12,cyan,arrival,'jump_gate_energy',(0,math.pi/2,0),gate_id='PELAGOS_GATE_A')
 for i in range(4):a=i/4*math.tau;y=-15+math.cos(a)*4.2;z=3+math.sin(a)*4.2;cube(f'JumpGatePylon_{i+1}',(-31,y,z),(.55,.34,.48),white,arrival,'jump_gate_pylon',.08)
 # Four arrival transforms support player, fleet, civilian, and emergency arrivals.
 arrivals=[('Player',(-36,-15,3),2800),('Fleet',(-36,-10,7),4200),('Civilian',(-37,-20,0),2400),('Emergency',(-34,-15,-4),1800)]
 for role,p,clearance in arrivals:o=empty('ArrivalSpawn_'+role,p,arrival,'arrival_spawn','ARROWS',1.2,spawn_class=role.lower(),clearance_radius=clearance,forward_axis='+X');o.rotation_euler[1]=math.pi/2
 empty('ArrivalTrigger_JumpComplete',(-28,-15,3),arrival,'arrival_trigger','SPHERE',3,trigger_event='OnJumpComplete',one_shot=True)
 empty('ArrivalTrigger_ControlHandoff',(-20,-10,3),arrival,'arrival_trigger','SPHERE',3,trigger_event='EnablePlayerControl',one_shot=True)
 empty('ArrivalTrigger_StationGreeting',(-12,-4,3),arrival,'arrival_trigger','SPHERE',3,trigger_event='PlayStationGreeting',one_shot=True)
 empty('ArrivalTrigger_DockingClearance',(-7,0,3),arrival,'arrival_trigger','SPHERE',3,trigger_event='RequestDockingClearance',one_shot=False)
 # Explicit inbound/outbound traffic geometry and route metadata.
 curve('Lane_PlayerInbound',[(-36,-15,3),(-26,-12,3),(-15,-6,3),(-6,0,3)],cyan,navigation,'arrival_lane',.055,lane_id='PLAYER_IN',speed_limit=220)
 curve('Lane_CivilianInbound',[(-37,-20,0),(-27,-15,1),(-16,-8,2),(-7,-1,2)],green,navigation,'traffic_lane',.035,lane_id='CIV_IN',speed_limit=160)
 curve('Lane_CargoInbound',[(-38,-8,7),(-25,-5,6),(-14,-1,5),(-6,1,5)],amber,navigation,'traffic_lane',.04,lane_id='CARGO_IN',speed_limit=120)
 curve('Lane_Outbound',[(-5,4,7),(-14,10,9),(-27,16,12),(-40,22,15)],cyan,navigation,'departure_lane',.035,lane_id='OUTBOUND',speed_limit=280)
 # Navigation buoys communicate direction and safe corridor.
 for i in range(10):t=i/9;p=Vector((-29,-14,3)).lerp(Vector((-7,-1,3)),t);sphere(f'InboundBuoy_{i+1:02d}',p,.13,green if i<7 else amber,navigation,'navigation_buoy',16,sequence=i+1,lane_id='PLAYER_IN')
 # Four functional docks and approach transforms.
 dock_z=[-1.2,1.1,4.1,6.8]
 for i,z in enumerate(dock_z,1):
  empty(f'DockTransform_{i}',(-13.6,2,z+.25),docking,'dock_transform','ARROWS',.8,dock_id=f'PELAGOS_DOCK_{i}',ship_size='medium' if i<4 else 'large',occupied=False)
  empty(f'DockApproach_{i}',(-19,2,z+.25),docking,'dock_approach','CIRCLE',1.2,dock_id=f'PELAGOS_DOCK_{i}',approach_distance=5400)
  cube(f'DockStatusPanel_{i}',(-12.7,.45,z+.65),(.28,.06,.18),green if i!=3 else amber,docking,'dock_status',.025,dock_id=f'PELAGOS_DOCK_{i}',status='available' if i!=3 else 'reserved')
 # Traffic and docking authority controllers.
 empty('BP_PelagosTrafficController',(0,2,12),functional,'traffic_controller','PLAIN_AXES',1.5,max_active_ships=18,arrival_interval=22,departure_interval=28)
 empty('BP_PelagosDockingAuthority',(0,2,10),functional,'docking_controller','PLAIN_AXES',1.5,dock_count=4,clearance_timeout=45)
 empty('BP_PelagosMissionDirector',(0,2,14),functional,'mission_controller','PLAIN_AXES',1.5,mission_table='DT_PelagosOrbitalMissions')
 # Exclusion/safety volumes keep arrivals clear of station and planet.
 empty('SafetyVolume_StationExclusion',(0,2,3),hazards,'exclusion_volume','SPHERE',9,damage=False,block_spawns=True)
 empty('SafetyVolume_JumpGate',(-31,-15,3),hazards,'jump_exclusion','SPHERE',6,damage=True,damage_type='jump_shear')
 empty('SafetyVolume_PlanetGravity',(16,38,4),hazards,'gravity_volume','SPHERE',16,gravity_strength=1.8,warning_distance=22000)
 empty('SafetyVolume_TrafficCorridor',(-17,-7,3),hazards,'traffic_clearance','CUBE',8,clearance_radius=1800)
 # Strengthen Pelagos visual identity: cloud arcs, orbital markers, and surface lights.
 for i in range(5):a=i/5*math.tau+.3;torus(f'PelagosCloudArc_{i+1}',(16,38,4),13.52+i*.025,.055,white,planet,'cloud_band',(math.sin(a)*.25,a*.3,a))
 for i in range(12):a=i/12*math.tau;p=(16+math.cos(a)*12.7,38+math.sin(a)*12.7,4+math.sin(a*3)*2.4);sphere(f'PelagosCityLight_{i+1:02d}',p,.12,amber,planet,'surface_city_light',12,city_cluster=i+1)
 torus('PelagosOrbitalEquator',(16,38,4),14.4,.035,cyan,planet,'orbital_reference',(0,0,.18))
 # Animate the player ship from jump exit to its station handoff point.
 ship=bpy.data.objects.get('PlayerShip_Hull');wing=bpy.data.objects.get('PlayerShip_Wing');cockpit=bpy.data.objects.get('PlayerShip_Cockpit')
 ship_parts=[o for o in (ship,wing,cockpit,bpy.data.objects.get('PlayerShip_Drive_-9.55'),bpy.data.objects.get('PlayerShip_Drive_-8.45')) if o]
 ship_root=empty('PlayerShip_ArrivalRoot',(0,0,0),arrival,'player_ship_root','ARROWS',.8,route='PLAYER_IN')
 for o in ship_parts:o.parent=ship_root
 ship_root.location=(-19,-6,1);ship_root.keyframe_insert(data_path='location',frame=1);ship_root.location=(-3,1,1);ship_root.keyframe_insert(data_path='location',frame=90);ship_root.location=(9,9,1);ship_root.keyframe_insert(data_path='location',frame=180);reg('Player ship arrival animation','arrival_animation',None,frames=[1,90,180])
 # Functional cameras for jump, handoff, docking, and orbital reveal.
 cameras=[('Camera_PelagosJumpExit',(-43,-25,13),(-25,-10,3),48),('Camera_PelagosControlHandoff',(-25,-17,8),(-10,-3,3),58),('Camera_PelagosDocking',(-22,-7,7),(-10,2,3),65),('Camera_PelagosOrbitalReveal',(-28,-25,16),(8,24,4),42)]
 for n,loc,target,lens in cameras:camera(n,loc,target,cams,lens)
 # Timeline and map state routing.
 for n,f in [('PELAGOS_JUMP_EXIT',1),('PELAGOS_HANDOFF',90),('PELAGOS_CLEARANCE',150),('PELAGOS_DOCKING',220),('PELAGOS_ORBITAL_REVEAL',300)]:
  if not s.timeline_markers.get(n):s.timeline_markers.new(n,frame=f)
 reg('Pelagos arrival timeline','timeline',None,markers=5)
 s['player_arrival_spawn']='ArrivalSpawn_Player';s['arrival_lane']='Lane_PlayerInbound';s['docking_authority']='BP_PelagosDockingAuthority';s['traffic_controller']='BP_PelagosTrafficController';s['mission_director']='BP_PelagosMissionDirector';s['level_exit_lane']='Lane_Outbound';reg('Pelagos gameplay routing','map_configuration')
 # Package, validate, save, and render.
 for img in bpy.data.images:
  if not img.packed_file:img.pack()
 validation={'arrival_spawns':sum(o.name.startswith('ArrivalSpawn_') for o in bpy.data.objects),'docks':sum(o.name.startswith('DockTransform_') for o in bpy.data.objects),'approaches':sum(o.name.startswith('DockApproach_') for o in bpy.data.objects),'lanes':sum(o.name.startswith('Lane_') for o in bpy.data.objects),'controllers':sum(o.name.startswith('BP_Pelagos') for o in bpy.data.objects),'safety_volumes':sum(o.name.startswith('SafetyVolume_') for o in bpy.data.objects)};reg('Pelagos functional validation','validation',None,**validation)
 s['phase18_complete']=True;s['asset_version']='18.0';s['level_status']='functional_art_vertical_slice';s.frame_end=360;s.camera=bpy.data.objects.get('Camera_PelagosOrbitalReveal');s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.filepath=str(PREVIEW);s.view_settings.look='AgX - Medium High Contrast'
 manifest={'level':'Pelagos Orbital Arrival','version':'18.0','environment':'high_orbit','arrival':{'player_spawn':'ArrivalSpawn_Player','lane':'Lane_PlayerInbound','trigger_sequence':['ArrivalTrigger_JumpComplete','ArrivalTrigger_ControlHandoff','ArrivalTrigger_StationGreeting','ArrivalTrigger_DockingClearance']},'docking':{'authority':'BP_PelagosDockingAuthority','dock_count':4},'traffic':{'controller':'BP_PelagosTrafficController','routes':['Lane_CivilianInbound','Lane_CargoInbound','Lane_Outbound']},'validation':validation};MANIFEST.write_text(json.dumps(manifest,indent=2),encoding='utf-8');REPORT.write_text(json.dumps({'phase':18,'completed_steps':len(done),'features':done,'manifest':manifest},indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(LEVEL));bpy.ops.render.render(write_still=True);print(json.dumps({'phase':18,'completed_steps':len(done),**validation},indent=2))
main()
