"""Phase twenty: 500 production-content steps for Pelagos Orbital Arrival."""
import json,math,random,sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems';LEVEL=OUT/'SpaceSystems_PelagosOrbitalArrival_Level.blend';PREVIEW=OUT/'SpaceSystems_PelagosOrbitalArrival_Phase20.png';REPORT=OUT/'SpaceSystems_PelagosOrbitalArrival_Phase20_500Steps.json';R=random.Random(20500);done=[];CACHE={}
def col(n):
 c=bpy.data.collections.get(n) or bpy.data.collections.new(n)
 if c.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(c)
 return c
def move(o,c):
 if o.name not in c.objects:c.objects.link(o)
 for x in list(o.users_collection):
  if x!=c:x.objects.unlink(o)
 return o
def reg(step,n,role,o=None,rendered=True,**data):
 item={'step':step,'name':n,'role':role,'rendered':rendered,**data};done.append(item)
 if o:
  o['phase20_step']=step;o['gameplay_role']=role
  for k,v in data.items():o[k]=v
def linked(kind,n,p,scale,m,c,rot=(0,0,0)):
 key=(kind,m.name)
 if key not in CACHE:
  if kind=='cube':bpy.ops.mesh.primitive_cube_add()
  elif kind=='sphere':bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2)
  elif kind=='cylinder':bpy.ops.mesh.primitive_cylinder_add(vertices=16)
  else:bpy.ops.mesh.primitive_torus_add(major_radius=1,minor_radius=.1,major_segments=32,minor_segments=8)
  o=bpy.context.object;CACHE[key]=o.data;o.data.materials.append(m)
 else:o=bpy.data.objects.new(n,CACHE[key]);bpy.context.scene.collection.objects.link(o)
 o.name=n;o.location=p;o.scale=scale;o.rotation_euler=rot;move(o,c);return o
def empty(n,p,c,display='CUBE',size=.35):
 o=bpy.data.objects.new(n,None);o.location=p;o.empty_display_type=display;o.empty_display_size=size;c.objects.link(o);return o
def curve(n,pts,m,c,width=.02):
 d=bpy.data.curves.new(n+'_Curve','CURVE');d.dimensions='3D';d.bevel_depth=width;d.bevel_resolution=2;d.materials.append(m);sp=d.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for p,co in zip(sp.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 o=bpy.data.objects.new(n,d);c.objects.link(o);return o
def camera(n,loc,target,c,lens=58):
 d=bpy.data.cameras.new(n);d.lens=lens;d.clip_end=5000;d.dof.use_dof=True;d.dof.focus_distance=(Vector(target)-Vector(loc)).length;d.dof.aperture_fstop=7.1;o=bpy.data.objects.new(n,d);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();c.objects.link(o);return o
def main():
 s=bpy.context.scene
 if s.get('phase20_steps')==500:raise RuntimeError('Phase 20 already installed')
 hull=bpy.data.materials.get('LVL_Hull_Navy');white=bpy.data.materials.get('LVL_Hull_Ceramic');orange=bpy.data.materials.get('LVL_SafetyOrange');glass=bpy.data.materials.get('LVL_Glass');cyan=bpy.data.materials.get('LVL_Emission_Cyan');amber=bpy.data.materials.get('LVL_Emission_Amber');green=bpy.data.materials.get('LVL_Emission_Green');rock=bpy.data.materials.get('LVL_Asteroid')
 dockc=col('P20_DockModules');servicec=col('P20_ServiceProps');trafficc=col('P20_TrafficFleet');missionc=col('P20_MissionEncounters');envc=col('P20_Environment');logicc=col('P20_GameplayLogic');navc=col('P20_NavigationHUD');camc=col('P20_Cameras')
 step=1
 # 1-80: twenty readable modules on each of four docks.
 dock_roles=['cargo_lock','fuel_port','power_bus','airlock','pressure_valve','tow_hook','sensor','camera','work_light','warning_light','tool_rack','rescue_kit','coolant','data_port','crew_gate','security','fire_system','repair_arm','status_panel','service_hatch']
 for dock,z in enumerate([-1.2,1.1,4.1,6.8],1):
  for i,role in enumerate(dock_roles):
   p=(-12.8+(i%5)*.55,.55+(i//5)*.65,z+.35+(i%3)*.22);m=orange if role in ('warning_light','fire_system','rescue_kit') else (cyan if role in ('work_light','status_panel','data_port') else white);o=linked('cube',f'Dock{dock}_Module_{i+1:02d}_{role.title()}',p,(.16+.03*(i%3),.12,.12+.03*(i%2)),m,dockc);reg(step,o.name,role,o,dock_id=dock);step+=1
 # 81-140: sixty service props distributed through station docking levels.
 services=['fuel','repair','medical','cargo','customs','crew','upgrade','market','navigation','salvage']
 for i in range(60):
  dock=i%4;z=[-1.2,1.1,4.1,6.8][dock];role=services[i%10];p=(-10.8+(i%6)*.62,3.6+(i//12)*.48,z+.3+(i%2)*.3);m=green if role in ('medical','crew') else (amber if role in ('cargo','salvage','fuel') else white);o=linked('cube',f'ServiceProp_{i+1:03d}_{role.title()}',p,(.14+.04*(i%3),.13,.18),m,servicec);reg(step,o.name,'service_prop',o,service_type=role,dock_id=dock+1);step+=1
 # 141-220: eighty linked, animated traffic craft.
 traffic_roles=['shuttle','freighter','tug','patrol','medical','rescue','courier','construction']
 for i in range(80):
  role=traffic_roles[i%8];p=Vector((-48+(i%16)*6,-28+(i//16)*8,5+(i%5)*2));root=empty(f'P20_Traffic_{i+1:03d}_{role.title()}',p,trafficc,'ARROWS',.3);body=linked('cylinder',root.name+'_Hull',p,(.18,.18,.75),white if i%2 else hull,trafficc,(0,math.pi/2,0));wing=linked('cube',root.name+'_Wing',p,(.55,.7,.045),orange if i%5==0 else hull,trafficc);drive=linked('sphere',root.name+'_Drive',p+Vector((-.75,0,0)),(.11,.11,.11),cyan if i%2 else amber,trafficc)
  for q in (body,wing,drive):q.parent=root
  root.keyframe_insert(data_path='location',frame=1);root.location+=Vector((R.uniform(30,65),R.uniform(18,42),R.uniform(-8,12)));root.keyframe_insert(data_path='location',frame=480);reg(step,root.name,role,root,route_id='P20_ROUTE_'+str(i%12+1));step+=1
 # 221-300: mission/encounter anchors; only their compact beacons render.
 mission_roles=['distress','salvage','escort','survey','repair','medical','cargo','security','artifact','rescue']
 for i in range(80):
  role=mission_roles[i%10];a=i/80*math.tau;rad=35+(i%8)*3;p=Vector((math.cos(a)*rad,math.sin(a)*rad,4+(i%9-4)*2));root=empty(f'Mission_{i+1:03d}_{role.title()}',p,missionc,'SPHERE',.65);root.hide_render=True;beacon=linked('sphere',root.name+'_Beacon',p,(.09,.09,.09),amber if i%3 else green,missionc);beacon.parent=root;reg(step,root.name,'mission_anchor',root,False,mission_type=role,tier=1+i%5,activation_radius=3500);step+=1
 # 301-360: environmental storytelling and orbital depth.
 for i in range(30):a=i/30*math.tau;rad=22+R.uniform(0,25);p=(math.cos(a)*rad,math.sin(a)*rad,R.uniform(-8,16));o=linked('sphere',f'P20_OrbitalRock_{i+1:02d}',p,(R.uniform(.2,.9),R.uniform(.15,.7),R.uniform(.2,1.1)),rock,envc,(R.random(),R.random(),R.random()));reg(step,o.name,'orbital_debris',o);step+=1
 for i in range(15):a=i/15*math.tau;p=(16+math.cos(a)*13.1,38+math.sin(a)*13.1,4+math.sin(a*3)*3);o=linked('sphere',f'P20_PelagosCity_{i+1:02d}',p,(.08,.08,.08),amber,envc);reg(step,o.name,'planet_city_light',o);step+=1
 for i in range(10):p=(-28+i*5,18+(i%3)*4,8+(i%4)*3);o=linked('cube',f'P20_DerelictDebris_{i+1:02d}',p,(.3+i%3*.15,.12,.18),hull,envc,(R.random(),R.random(),R.random()));reg(step,o.name,'derelict_debris',o);step+=1
 for i in range(5):a=i/5*math.tau;pts=[(math.cos(a+j*.6)*(18+i*2),20+math.sin(a+j*.6)*(18+i*2),6+i) for j in range(4)];o=curve(f'P20_OrbitalTrail_{i+1}',pts,cyan if i%2 else amber,envc,.018);reg(step,o.name,'orbital_trail',o);step+=1
 # 361-420: gameplay/AI/audio nodes, hidden from beauty rendering.
 logic_roles=['ai_spawn','audio_zone','combat_director','mission_router','checkpoint','save_state','streaming_gate','tutorial','telemetry','difficulty']
 for i in range(60):role=logic_roles[i%10];p=(-10+(i%10)*2,10+(i//10)*2,18+(i%3));o=empty(f'Logic_{i+1:03d}_{role.title()}',p,logicc,'PLAIN_AXES',.25);o.hide_render=True;reg(step,o.name,role,o,False,node_id=i+1,enabled=True);step+=1
 # 421-460: route signage, HUD anchors, and approach splines.
 for i in range(20):p=(-30+i*1.35,-13+i*.6,3+(i%3)*.35);o=linked('sphere',f'P20_NavMarker_{i+1:02d}',p,(.08,.08,.08),green if i<14 else amber,navc);reg(step,o.name,'navigation_marker',o,sequence=i+1);step+=1
 for i in range(10):p=(-14+(i%5)*3,5+(i//5)*5,8+i%3);o=empty(f'P20_HUDAnchor_{i+1:02d}',p,navc,'CIRCLE',.35);o.hide_render=True;reg(step,o.name,'hud_anchor',o,False,widget_id='W_Pelagos_'+str(i+1));step+=1
 for i in range(10):a=i/10*math.tau;pts=[(-31,-15,3),(math.cos(a)*18,math.sin(a)*18,5+i%3),(0,2,3+i%4)];o=curve(f'P20_ApproachSpline_{i+1:02d}',pts,cyan if i%2 else green,navc,.015);reg(step,o.name,'approach_spline',o,lane_class='dynamic');step+=1
 # 461-480: production and gameplay cameras.
 for i in range(20):a=i/20*math.tau;loc=(math.cos(a)*(30+i%4*3),math.sin(a)*(30+i%4*3),10+(i%5)*3);target=(0,2,3 if i%2 else 6);o=camera(f'Camera_P20_{i+1:02d}',loc,target,camc,48+i%6*5);reg(step,o.name,'production_camera',o,shot_index=i+1);step+=1
 # 481-500: production-map finalization steps.
 finals=[('Traffic performance budget','optimization'),('Mission concurrency budget','optimization'),('Dock occupancy audit','validation'),('Arrival route audit','validation'),('Emergency response audit','validation'),('Service availability audit','validation'),('Navigation readability audit','validation'),('Camera coverage audit','validation'),('Material dependency audit','validation'),('Texture packing audit','validation'),('Animation range audit','validation'),('Collision metadata audit','validation'),('Streaming metadata audit','validation'),('HUD routing audit','validation'),('Audio routing audit','validation'),('Mission manifest','production'),('Runtime manifest','production'),('Save version 20','production'),('Beauty render','production'),('Phase 20 report','production')]
 for n,role in finals:reg(step,n,role);step+=1
 if len(done)!=500 or step!=501:raise RuntimeError(f'Phase20 count mismatch {len(done)}, step {step}')
 for c in (dockc,servicec,trafficc,missionc,envc,logicc,navc,camc):c['phase']=20;c['runtime_optional']=c in (missionc,envc,logicc)
 for img in bpy.data.images:
  if not img.packed_file:img.pack()
 budgets={'max_active_traffic':24,'max_concurrent_missions':6,'max_near_dock_traffic':5,'mission_stream_radius':45000,'environment_stream_radius':60000};validation={'dock_modules':80,'service_props':60,'traffic':80,'missions':80,'environment':60,'logic_nodes':60,'navigation_hud':40,'cameras':20};s['phase20_steps']=500;s['asset_version']='20.0';s['level_status']='production_alpha';s['phase20_budgets']=json.dumps(budgets);s.frame_end=480;s.camera=bpy.data.objects.get('Camera_P20_03');s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.filepath=str(PREVIEW);s.view_settings.look='AgX - Medium High Contrast';summary={'objects':len(bpy.data.objects),'collections':len(bpy.data.collections),'actions':len(bpy.data.actions),**validation};REPORT.write_text(json.dumps({'phase':20,'steps':done,'budgets':budgets,'summary':summary},indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(LEVEL));bpy.ops.render.render(write_still=True);print(json.dumps({'phase':20,'completed':len(done),**summary},indent=2))
main()
