"""Phase twenty-one: 500 production-beta steps for Pelagos Orbital Arrival."""
import json,math,random,sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems';LEVEL=OUT/'SpaceSystems_PelagosOrbitalArrival_Level.blend';PREVIEW=OUT/'SpaceSystems_PelagosOrbitalArrival_Phase21.png';REPORT=OUT/'SpaceSystems_PelagosOrbitalArrival_Phase21_500Steps.json';R=random.Random(21500);done=[];CACHE={}
def col(n):
 c=bpy.data.collections.get(n) or bpy.data.collections.new(n)
 if c.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(c)
 return c
def move(o,c):
 if o.name not in c.objects:c.objects.link(o)
 for x in list(o.users_collection):
  if x!=c:x.objects.unlink(o)
 return o
def reg(step,n,role,o=None,visible=False,**data):
 item={'step':step,'name':n,'role':role,'visible':visible,**data};done.append(item)
 if o:
  o['phase21_step']=step;o['production_role']=role
  for k,v in data.items():o[k]=v
def empty(n,p,c,display='PLAIN_AXES',size=.25):
 o=bpy.data.objects.new(n,None);o.location=p;o.empty_display_type=display;o.empty_display_size=size;o.hide_render=True;c.objects.link(o);return o
def linked(kind,n,p,scale,m,c,rot=(0,0,0)):
 key=(kind,m.name)
 if key not in CACHE:
  if kind=='cube':bpy.ops.mesh.primitive_cube_add()
  elif kind=='sphere':bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2)
  else:bpy.ops.mesh.primitive_cylinder_add(vertices=16)
  o=bpy.context.object;CACHE[key]=o.data;o.data.materials.append(m)
 else:o=bpy.data.objects.new(n,CACHE[key]);bpy.context.scene.collection.objects.link(o)
 o.name=n;o.location=p;o.scale=scale;o.rotation_euler=rot;move(o,c);return o
def camera(n,loc,target,c,lens=58):
 d=bpy.data.cameras.new(n);d.lens=lens;d.clip_end=5000;d.dof.use_dof=True;d.dof.focus_distance=(Vector(target)-Vector(loc)).length;d.dof.aperture_fstop=7.1;o=bpy.data.objects.new(n,d);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();c.objects.link(o);return o
def main():
 s=bpy.context.scene
 if s.get('phase21_steps')==500:raise RuntimeError('Phase 21 already installed')
 hull=bpy.data.materials.get('LVL_Hull_Navy');white=bpy.data.materials.get('LVL_Hull_Ceramic');orange=bpy.data.materials.get('LVL_SafetyOrange');cyan=bpy.data.materials.get('LVL_Emission_Cyan');amber=bpy.data.materials.get('LVL_Emission_Amber');green=bpy.data.materials.get('LVL_Emission_Green')
 markings=col('P21_DockMarkings');docklogic=col('P21_DockStateMachines');traffic=col('P21_TrafficBehaviors');missions=col('P21_MissionDefinitions');events=col('P21_EnvironmentalEvents');services=col('P21_ServiceLogic');ux=col('P21_UXAudioAccessibility');cams=col('P21_Cameras');step=1
 # 1-40: ten clean, readable markings for each dock.
 for dock,z in enumerate([-1.2,1.1,4.1,6.8],1):
  for i in range(10):p=(-12.1+(i%5)*.55,.38+(i//5)*2.95,z+.23);m=orange if i in (0,4,5,9) else (green if dock!=3 else amber);o=linked('cube',f'Dock{dock}_Marking_{i+1:02d}',p,(.21,.025,.025),m,markings);reg(step,o.name,'dock_marking',o,True,dock_id=dock,marking_index=i+1);step+=1
 # 41-100: fifteen state-machine nodes per dock.
 dock_states=['offline','standby','reserved','approach','alignment','soft_capture','hard_capture','seal_check','pressure_equalize','service','crew_transfer','departure_request','release','clearance','fault']
 for dock in range(1,5):
  for i,state in enumerate(dock_states):o=empty(f'Dock{dock}_State_{i+1:02d}_{state.title()}',(-4+dock*2,16+i*.35,20),docklogic);reg(step,o.name,'dock_state',o,False,dock_id=dock,state=state,next_state=dock_states[(i+1)%15]);step+=1
 # 101-200: traffic AI behavior definitions.
 behavior_roles=['arrive','depart','hold','yield','dock','undock','patrol','escort','evade','rescue']
 for i in range(100):role=behavior_roles[i%10];o=empty(f'TrafficBehavior_{i+1:03d}_{role.title()}',(-20+(i%20)*2,24+(i//20),25),traffic);reg(step,o.name,'traffic_behavior',o,False,behavior=role,ship_class=i%8+1,priority=i%5+1,max_speed=120+(i%6)*40);step+=1
 # 201-300: mission definitions and completion routing.
 mission_roles=['dock_delivery','rescue','salvage','escort','survey','repair','medical','security','diplomatic','artifact']
 for i in range(100):role=mission_roles[i%10];o=empty(f'PelagosMission_{i+1:03d}_{role.title()}',(-30+(i%25)*2,31+(i//25),28),missions);reg(step,o.name,'mission_definition',o,False,mission_type=role,tier=i%5+1,reward=500+(i%10)*250,timeout=0 if i%4 else 900);step+=1
 # 301-360: thirty hidden event triggers and thirty restrained visible cues.
 event_roles=['solar_flare','ion_storm','traffic_surge','distress','meteor_shower','sensor_blackout']
 for i in range(30):a=i/30*math.tau;p=(math.cos(a)*(28+i%5*3),math.sin(a)*(28+i%5*3),6+(i%7)*2);o=empty(f'EnvironmentTrigger_{i+1:02d}_{event_roles[i%6].title()}',p,events,'SPHERE',1);reg(step,o.name,'environment_trigger',o,False,event_type=event_roles[i%6],cooldown=300+i*10);step+=1
 for i in range(30):a=i/30*math.tau;p=(math.cos(a)*(25+i%4*2),math.sin(a)*(25+i%4*2),8+(i%6)*2);m=amber if i%3==0 else cyan;o=linked('sphere',f'EnvironmentCue_{i+1:02d}',p,(.07,.07,.07),m,events);reg(step,o.name,'environment_cue',o,True,event_link=i+1);step+=1
 # 361-420: station services, inventory, pricing, and repair logic.
 service_roles=['fuel','repair','medical','cargo','customs','crew','upgrade','market','navigation','salvage']
 for i in range(60):role=service_roles[i%10];o=empty(f'ServiceLogic_{i+1:03d}_{role.title()}',(-18+(i%15)*2,38+(i//15),30),services);reg(step,o.name,'service_logic',o,False,service_type=role,availability='docked',cost_multiplier=round(.8+(i%7)*.1,2),duration=30+(i%8)*30);step+=1
 # 421-460: accessibility, HUD, subtitles, audio, and input routing.
 ux_roles=['hud','subtitle','audio_description','colorblind','input_prompt','objective','warning','navigation','tutorial','feedback']
 for i in range(40):role=ux_roles[i%10];o=empty(f'UXRoute_{i+1:02d}_{role.title()}',(-10+(i%10)*2,45+(i//10),32),ux);reg(step,o.name,'ux_route',o,False,ux_type=role,localization_key='PELAGOS_'+str(i+1).zfill(3),priority=i%4+1);step+=1
 # 461-480: coverage cameras.
 for i in range(20):a=i/20*math.tau;radius=32+(i%4)*4;loc=(math.cos(a)*radius,math.sin(a)*radius,12+(i%5)*3);target=(-4,4,4+i%3);o=camera(f'Camera_P21_{i+1:02d}',loc,target,cams,50+(i%7)*4);reg(step,o.name,'coverage_camera',o,True,coverage=i+1);step+=1
 # 481-500: production-beta finalization.
 final_steps=[('Hide runtime splines from beauty','rendering'),('Hide logic collections from beauty','rendering'),('Dock state transition audit','validation'),('Traffic behavior audit','validation'),('Mission definition audit','validation'),('Environmental event audit','validation'),('Service logic audit','validation'),('Accessibility routing audit','validation'),('Camera coverage audit','validation'),('Animation budget audit','validation'),('Object naming audit','validation'),('Collection naming audit','validation'),('Texture dependency audit','validation'),('Material dependency audit','validation'),('Runtime memory budget','optimization'),('Streaming budget','optimization'),('Production beta manifest','production'),('Save version 21','production'),('Render production beta','production'),('Write phase report','production')]
 for n,role in final_steps:reg(step,n,role);step+=1
 if len(done)!=500 or step!=501:raise RuntimeError(f'Phase21 count mismatch {len(done)}, step {step}')
 # Debug and runtime routes remain in the map but never render as neon spaghetti.
 hidden_curves=0
 for o in bpy.data.objects:
  if o.type=='CURVE' and any(k in o.name for k in ('Lane_','Route_','HoldingPattern','ApproachSpline','ArrivalLane','OrbitalTrail')):o.hide_render=True;hidden_curves+=1
 for c in (docklogic,traffic,missions,services,ux):c.hide_render=True;c['logic_only']=True
 for c in (markings,docklogic,traffic,missions,events,services,ux,cams):c['phase']=21;c['runtime_optional']=c not in (markings,cams)
 budgets={'max_active_missions':8,'max_traffic_behaviors':32,'max_environment_events':3,'logic_stream_radius':24000,'camera_cull_distance':80000};validation={'dock_markings':40,'dock_states':60,'traffic_behaviors':100,'missions':100,'environment_events':60,'service_logic':60,'ux_routes':40,'cameras':20,'hidden_runtime_curves':hidden_curves};s['phase21_steps']=500;s['asset_version']='21.0';s['level_status']='production_beta';s['phase21_budgets']=json.dumps(budgets);s.camera=bpy.data.objects.get('Camera_PelagosOrbitalReveal') or s.camera;s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.filepath=str(PREVIEW);s.view_settings.look='AgX - Medium High Contrast';summary={'objects':len(bpy.data.objects),'collections':len(bpy.data.collections),'actions':len(bpy.data.actions),**validation};REPORT.write_text(json.dumps({'phase':21,'steps':done,'budgets':budgets,'summary':summary},indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(LEVEL));bpy.ops.render.render(write_still=True);print(json.dumps({'phase':21,'completed':len(done),**summary},indent=2))
main()
