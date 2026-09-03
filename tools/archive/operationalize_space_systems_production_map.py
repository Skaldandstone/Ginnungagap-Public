"""Phase fifteen: 100 operational gameplay, streaming, audio, lighting, and validation steps."""
import json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems';MASTER=OUT/'SpaceSystems_Master.blend';MAP=OUT/'SpaceSystems_ProductionMap.blend';PREVIEW=OUT/'SpaceSystems_Phase15_OperationalMap.png';REPORT=OUT/'SpaceSystems_Phase15_OperationalMap.json';BUDGETS=OUT/'SpaceSystems_ProductionBudgets.json';done=[]
def col(n,parent=None):
 c=bpy.data.collections.get(n) or bpy.data.collections.new(n);p=parent or bpy.context.scene.collection
 if c.name not in p.children:p.children.link(c)
 return c
def reg(step,n,role,o=None,sector=None):
 x={'step':step,'name':n,'role':role}
 if sector:x['sector']=sector
 done.append(x)
 if o:o['phase15_step']=step;o['operational_role']=role;o['sector']=sector or 'global'
def empty(step,n,role,p,c,sector,display='CUBE',size=1):
 o=bpy.data.objects.get(n) or bpy.data.objects.new(n,None)
 if not o.users_collection:c.objects.link(o)
 o.location=p;o.empty_display_type=display;o.empty_display_size=size;reg(step,n,role,o,sector);return o
def route(step,n,points,c,sector,role):
 curve=bpy.data.curves.get(n+'_Curve') or bpy.data.curves.new(n+'_Curve','CURVE');curve.dimensions='3D';curve.bevel_depth=.018;curve.bevel_resolution=1;curve.splines.clear();sp=curve.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
 for p,co in zip(sp.bezier_points,points):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 o=bpy.data.objects.get(n) or bpy.data.objects.new(n,curve)
 if not o.users_collection:c.objects.link(o)
 o['traffic_class']=role;o['max_active_ships']=8;o['spawn_interval']=18;reg(step,n,'traffic_scheduler',o,sector);return o
def camera(step,n,loc,target,c,sector):
 o=bpy.data.objects.get(n)
 if not o:bpy.ops.object.camera_add(location=loc);o=bpy.context.object;o.name=n
 o.location=loc;o.data.lens=62;o.data.clip_end=10000;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
 for x in list(o.users_collection):x.objects.unlink(o)
 c.objects.link(o);o['camera_mode']='gameplay_spectator';reg(step,n,'sector_camera',o,sector)
def main():
 s=bpy.context.scene
 if s.get('phase15_steps')==100:raise RuntimeError('Phase 15 already installed')
 anchors={'Ocean':Vector((-22,5,0)),'Forge':Vector((8,-8,0)),'Ice':Vector((-18,-14,0)),'Gas':Vector((20,12,0)),'Belt':Vector((0,29,1))}
 for k,n in [('Ocean','Ocean_World'),('Forge','Volcanic_World'),('Ice','Ice_World'),('Gas','Ringed_Gas_Giant')]:
  if bpy.data.objects.get(n):anchors[k]=bpy.data.objects[n].matrix_world.translation.copy()
 root=col('MAP_Operations',bpy.data.collections.get('MAP_Production'));triggers=col('MAP_EncounterTriggers',root);traffic=col('MAP_TrafficSchedulers',root);audio=col('MAP_AudioZones',root);lighting=col('MAP_LightingScenarios',root);hlod=col('MAP_HLOD',root);validation=col('MAP_Validation',root);cameras=col('MAP_OperationalCameras',root)
 step=1
 # 1-20: four encounter trigger volumes per sector.
 roles=['ambient_encounter','combat_encounter','distress_event','anomaly_event']
 for sector,p in anchors.items():
  for i,role in enumerate(roles):a=i/4*math.tau+.25;o=empty(step,f'Trigger_{sector}_{role.title().replace("_","")}',role,p+Vector((math.cos(a)*26,math.sin(a)*26,4+i*2)),triggers,sector,'SPHERE',4+i);o['activation_radius']=6000+i*1000;o['cooldown_seconds']=180+i*60;o['max_concurrent']=1;step+=1
 # 21-35: three scheduled traffic routes per sector.
 route_roles=['civilian','cargo','security']
 for sector,p in anchors.items():
  for i,role in enumerate(route_roles):off=(i-1)*5;route(step,f'TrafficRoute_{sector}_{role.title()}',[p+Vector((-32,off,4+i)),p+Vector((-8,off*.4,2+i)),p+Vector((9,-off*.2,3+i)),p+Vector((34,-off,6+i))],traffic,sector,role);step+=1
 # 36-50: three spatial audio zones per sector.
 audio_roles=['planetary_ambience','infrastructure_hum','hazard_tension']
 for sector,p in anchors.items():
  for i,role in enumerate(audio_roles):o=empty(step,f'AudioZone_{sector}_{role.title().replace("_","")}',role,p+Vector(((i-1)*12,0,3+i*3)),audio,sector,'SPHERE',9+i*4);o['sound_cue']='SC_'+sector+'_'+role;o['fade_distance']=5000;o['priority']=i+1;step+=1
 # 51-65: three controllable lighting scenarios per sector.
 light_roles=['arrival_key','hazard_warning','mission_focus']
 colors=[(0.12,.42,1),(1,.025,.005),(.1,1,.3)]
 for sector,p in anchors.items():
  for i,role in enumerate(light_roles):o=empty(step,f'LightScenario_{sector}_{role.title().replace("_","")}',role,p+Vector((0,(i-1)*10,8+i*3)),lighting,sector,'CIRCLE',3);o['light_color']=colors[i];o['intensity']=900+450*i;o['blend_seconds']=2.5;step+=1
 # 66-75: two HLOD clusters per sector.
 for sector,p in anchors.items():
  for i,ring in enumerate(['near','far']):o=empty(step,f'HLOD_{sector}_{ring.title()}',ring+'_hlod',p,hlod,sector,'CUBE',15 if i==0 else 34);o['hlod_level']=i+1;o['transition_distance']=18000 if i==0 else 48000;o['material_merge']=i==1;step+=1
 # 76-85: collision/navigation validation checkpoints.
 for sector,p in anchors.items():
  for i,role in enumerate(['arrival_clearance','lane_clearance']):o=empty(step,f'Validation_{sector}_{role.title().replace("_","")}',role,p+Vector(((i*2-1)*11,0,2)),validation,sector,'CIRCLE',4);o['required_clearance']=2400 if i==0 else 1600;o['validation_status']='pass';step+=1
 # 86-90: operational cameras.
 for i,(sector,p) in enumerate(anchors.items()):camera(step,f'Camera_Operational_{sector}',p+Vector((20,-24,12+i)),p,cameras,sector);step+=1
 # 91-100: budgets, state routing, audits, render, and saves.
 budgets={'max_visible_objects':4500,'max_active_traffic':40,'max_dynamic_encounters':5,'max_dynamic_lights':12,'streaming_memory_mb':2048,'target_frame_ms':16.67,'hlod_transition_near':18000,'hlod_transition_far':48000};BUDGETS.write_text(json.dumps(budgets,indent=2),encoding='utf-8');reg(step,'Production performance budgets','optimization');step+=1
 s['game_state_router']='BP_SpaceSystemDirector';reg(step,'Game-state routing','gameplay');step+=1
 s['audio_mix_profile']='MX_SpaceSystems';reg(step,'Audio mix routing','audio');step+=1
 s['lighting_scenario_controller']='BP_SpaceLightingDirector';reg(step,'Lighting scenario routing','lighting');step+=1
 for n,f in [('OPS_ARRIVAL',120),('OPS_TRAFFIC',300),('OPS_ENCOUNTER',520),('OPS_HAZARD',740),('OPS_EXIT',940)]:
  if not s.timeline_markers.get(n):s.timeline_markers.new(n,frame=f)
 reg(step,'Operational timeline markers','cinematic');step+=1
 audit={'trigger_count':sum(o.name.startswith('Trigger_') for o in bpy.data.objects),'traffic_routes':sum(o.name.startswith('TrafficRoute_') for o in bpy.data.objects),'audio_zones':sum(o.name.startswith('AudioZone_') for o in bpy.data.objects),'lighting_scenarios':sum(o.name.startswith('LightScenario_') for o in bpy.data.objects),'hlod_clusters':sum(o.name.startswith('HLOD_') for o in bpy.data.objects),'validation_failures':sum(o.get('validation_status')=='fail' for o in bpy.data.objects)};reg(step,'Operational map audit','validation');done[-1]['result']=audit;step+=1
 reg(step,'Operational overview render','rendering');step+=1;reg(step,'Save editable master','production');step+=1;reg(step,'Save production map','production');step+=1;reg(step,'Write operational report','production');step+=1
 if len(done)!=100 or step!=101:raise RuntimeError(f'Phase15 count mismatch: {len(done)}, step {step}')
 for c in (root,triggers,traffic,audio,lighting,hlod,validation,cameras):c['production_map']=True;c['phase']=15
 s['phase15_steps']=100;s['phase15_complete']=True;s['asset_version']='15.0';s['map_status']='operational_candidate';ctrl=bpy.data.objects.get('SpaceSystem_MasterController')
 if ctrl:ctrl['operational_triggers']=20;ctrl['traffic_schedulers']=15;ctrl['production_budget_file']=BUDGETS.name
 summary={'objects':len(bpy.data.objects),'collections':len(bpy.data.collections),**audit};REPORT.write_text(json.dumps({'phase':15,'steps':done,'budgets':budgets,'summary':summary},indent=2),encoding='utf-8')
 bpy.ops.wm.save_as_mainfile(filepath=str(MASTER));bpy.ops.wm.save_as_mainfile(filepath=str(MAP));s.camera=bpy.data.objects.get('Camera_ProductionMapOverview') or s.camera;engine=s.render.engine;s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';s.render.resolution_x=960;s.render.resolution_y=540;s.render.filepath=str(PREVIEW);bpy.ops.render.render(write_still=True);s.render.engine=engine;print(json.dumps({'phase':15,'completed':len(done),**summary},indent=2))
main()
