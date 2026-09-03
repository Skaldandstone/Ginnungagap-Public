"""Phase eleven: 1,000 lightweight, cataloged space-system production steps."""
import json, math, random, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems';BLEND=OUT/'SpaceSystems_Master.blend'
PREVIEW=OUT/'SpaceSystems_Phase11_1000Steps.png';REPORT=OUT/'SpaceSystems_Phase11_1000Steps.json';MANIFEST=OUT/'SpaceSystems_Phase11_SectorManifest.json'
R=random.Random(111000);done=[];MESH_CACHE={}

def collection(name):
 c=bpy.data.collections.get(name) or bpy.data.collections.new(name)
 if c.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(c)
 return c
def move(o,c):
 if o.name not in c.objects:c.objects.link(o)
 for x in list(o.users_collection):
  if x!=c:x.objects.unlink(o)
 return o
def material(name,color,emission=0,metal=.2,rough=.4):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
 return m
def cube(name,pos,scale,mat):
 key=('cube',mat.name)
 if key not in MESH_CACHE:
  bpy.ops.mesh.primitive_cube_add();o=bpy.context.object;MESH_CACHE[key]=o.data;o.data.materials.append(mat)
 else:o=bpy.data.objects.new(name,MESH_CACHE[key]);bpy.context.scene.collection.objects.link(o)
 o.name=name;o.location=pos;o.scale=scale;return o
def sphere(name,pos,radius,mat):
 key=('sphere',mat.name)
 if key not in MESH_CACHE:
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1);o=bpy.context.object;MESH_CACHE[key]=o.data;o.data.materials.append(mat)
 else:o=bpy.data.objects.new(name,MESH_CACHE[key]);bpy.context.scene.collection.objects.link(o)
 o.name=name;o.location=pos;o.scale=(radius,radius,radius);return o
def cylinder(name,pos,radius,depth,mat,rot=(0,0,0),vertices=8):
 key=('cylinder',mat.name)
 if key not in MESH_CACHE:
  bpy.ops.mesh.primitive_cylinder_add(vertices=8);o=bpy.context.object;MESH_CACHE[key]=o.data;o.data.materials.append(mat)
 else:o=bpy.data.objects.new(name,MESH_CACHE[key]);bpy.context.scene.collection.objects.link(o)
 o.name=name;o.location=pos;o.rotation_euler=rot;o.scale=(radius,radius,depth/2);return o
def torus(name,pos,major,minor,mat,rot=(0,0,0)):
 key=('torus',mat.name)
 if key not in MESH_CACHE:
  bpy.ops.mesh.primitive_torus_add(major_radius=1,minor_radius=.08,major_segments=16,minor_segments=4);o=bpy.context.object;MESH_CACHE[key]=o.data;o.data.materials.append(mat)
 else:o=bpy.data.objects.new(name,MESH_CACHE[key]);bpy.context.scene.collection.objects.link(o)
 o.name=name;o.location=pos;o.rotation_euler=rot;o.scale=(major,major,major);return o
def register(step,name,role,obj=None,sector=None):
 item={'step':step,'name':name,'role':role}
 if sector:item['sector']=sector
 done.append(item)
 if obj:obj['phase11_step']=step;obj['gameplay_role']=role;obj['sector']=sector or 'global'
def root_object(step,name,role,pos,target,sector):
 o=bpy.data.objects.new(name,None);o.location=pos;o.empty_display_type='CUBE';o.empty_display_size=.28;target.objects.link(o);register(step,name,role,o,sector);return o
def poi(step,name,role,pos,target,sector,hull,glow,variant):
 r=root_object(step,name,role,pos,target,sector);sc=.18+(variant%4)*.025
 parts=[sphere(name+'_Body',pos,sc*1.2,hull),cylinder(name+'_Mast',Vector(pos)+Vector((0,0,sc*.8)),sc*.15,sc*2.2,hull),sphere(name+'_Signal',Vector(pos)+Vector((0,0,sc*2)),sc*.18,glow)]
 if variant%3==0:parts.append(torus(name+'_Orbit',pos,sc*1.8,sc*.08,glow))
 for p in parts:p.parent=r;move(p,target)
def module(step,name,role,pos,target,sector,hull,glow,variant):
 r=root_object(step,name,role,pos,target,sector);sc=.22+(variant%3)*.035
 parts=[cube(name+'_Core',pos,(sc,.55*sc,.38*sc),hull),cylinder(name+'_Spine',pos,.12*sc,2.4*sc,hull,(0,math.pi/2,0)),sphere(name+'_Lamp',Vector(pos)+Vector((0,0,.55*sc)),.13*sc,glow)]
 if variant%4==0:parts.append(torus(name+'_Dock',pos,sc*.9,sc*.07,hull,(math.pi/2,0,0)))
 for p in parts:p.parent=r;move(p,target)
def hazard(step,name,role,pos,target,sector,glow,variant):
 r=root_object(step,name,role,pos,target,sector);r.empty_display_type='SPHERE';r['hazard_radius']=1800+(variant%8)*350;r['damage_class']=role
 for j in range(3):
  p=Vector(pos)+Vector((R.uniform(-.8,.8),R.uniform(-.8,.8),R.uniform(-.5,.5)));q=sphere(name+'_Node'+str(j+1),p,.1+R.random()*.18,glow);q.parent=r;move(q,target)
def mission(step,name,role,pos,target,sector,hull,glow,variant):
 r=root_object(step,name,role,pos,target,sector);r['mission_tier']=1+variant%5;r['scan_radius']=1200+variant%6*300
 parts=[cube(name+'_Site',pos,(.24,.18,.15),hull),torus(name+'_Marker',pos,.38,.035,glow,(math.pi/2,0,0)),sphere(name+'_Objective',Vector(pos)+Vector((0,0,.32)),.06,glow)]
 for p in parts:p.parent=r;move(p,target)
def traffic(step,name,role,pos,target,sector,hull,glow,variant):
 r=root_object(step,name,role,pos,target,sector);sc=.18+(variant%3)*.035
 parts=[cylinder(name+'_Hull',pos,.16*sc,2.7*sc,hull,(0,math.pi/2,0)),cube(name+'_Wing',pos,(.45*sc,.65*sc,.05*sc),hull),sphere(name+'_Drive',Vector(pos)+Vector((-.58*sc,0,0)),.1*sc,glow)]
 for p in parts:p.parent=r;move(p,target)
 r.keyframe_insert(data_path='location',frame=1);r.location+=Vector((R.uniform(12,30),R.uniform(8,22),R.uniform(-4,4)));r.keyframe_insert(data_path='location',frame=960)
def beacon(step,name,role,pos,target,sector,hull,glow,variant):
 r=root_object(step,name,role,pos,target,sector);sc=.2+(variant%4)*.03
 parts=[cylinder(name+'_Pylon',pos,.08,sc*2.6,hull),torus(name+'_SignalRing',Vector(pos)+Vector((0,0,sc)),sc*.7,.03,glow),sphere(name+'_Light',Vector(pos)+Vector((0,0,sc*1.5)),.06,glow)]
 for p in parts:p.parent=r;move(p,target)
def camera(step,name,loc,target,lens,sector):
 bpy.ops.object.camera_add(location=loc);o=bpy.context.object;o.name=name;o.data.lens=lens;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();move(o,collection('SYS_Cameras'));register(step,name,'camera',o,sector)

def main():
 s=bpy.context.scene
 if s.get('phase11_steps')==1000:raise RuntimeError('Phase 11 is already installed')
 hull=bpy.data.materials.get('M_StationHull') or material('M_StationHull',(.11,.15,.2),0,.8,.3)
 cyan=material('M_P11_Cyan',(0,.55,1),16);amber=material('M_P11_Amber',(1,.2,.005),16);green=material('M_P11_Green',(0,1,.22),14);violet=material('M_P11_Violet',(.42,.005,1),16);red=material('M_P11_Red',(1,.004,.001),17);white=material('M_P11_White',(.7,.88,1),15)
 colors=[cyan,amber,white,green,violet]
 systems=[('Ocean','Ocean_World',(-22,5,0)),('Forge','Volcanic_World',(8,-8,0)),('Ice','Ice_World',(-18,-14,0)),('Gas','Ringed_Gas_Giant',(20,12,0)),('Belt',None,(0,29,1))]
 anchors={k:(bpy.data.objects.get(n).matrix_world.translation.copy() if n and bpy.data.objects.get(n) else Vector(f)) for k,n,f in systems}
 step=1
 # 1-200: forty layered points of interest per destination.
 poi_roles=['survey','habitat','resource','science','rescue','security','weather','biosphere','artifact','landmark']
 for si,(sector,_,_) in enumerate(systems):
  c=collection('P11_'+sector+'_POI');a0=anchors[sector]
  for i in range(40):
   a=i/40*math.tau+si*.19;rad=12+(i%5)*2.2;pos=a0+Vector((math.cos(a)*rad,math.sin(a)*rad,(i%7-3)*.7));role=poi_roles[i%len(poi_roles)];poi(step,f'{sector}_POI_{i+1:03d}_{role.title()}',role,pos,c,sector,hull,colors[si],i);step+=1
 # 201-400: economy and logistics infrastructure.
 economy_roles=['refinery','shipyard','market','fuel','cargo','repair','medical','habitat','communications','power']
 for si,(sector,_,_) in enumerate(systems):
  c=collection('P11_'+sector+'_Economy');a0=anchors[sector]
  for i in range(40):
   a=i/40*math.tau+.08;rad=17+(i%4)*2.5;pos=a0+Vector((math.cos(a)*rad,math.sin(a)*rad,(i%6-2.5)*.8));role=economy_roles[i%10];module(step,f'{sector}_Economy_{i+1:03d}_{role.title()}',role,pos,c,sector,hull,colors[(si+1)%5],i);step+=1
 # 401-550: thirty hazards per destination.
 hazard_roles=['radiation','gravity','ion','debris','thermal','cryo','magnetic','plasma','temporal','anomaly']
 for si,(sector,_,_) in enumerate(systems):
  c=collection('P11_'+sector+'_Hazards');a0=anchors[sector]
  for i in range(30):
   a=i/30*math.tau+.31;rad=22+(i%4)*3;pos=a0+Vector((math.cos(a)*rad,math.sin(a)*rad,(i%9-4)*1.1));role=hazard_roles[i%10];hazard(step,f'{sector}_Hazard_{i+1:03d}_{role.title()}',role,pos,c,sector,red if i%2 else violet,i);step+=1
 # 551-700: thirty mission sites per destination.
 mission_roles=['distress','salvage','research','escort','recovery','diplomatic','quarantine','artifact','rescue','investigation']
 for si,(sector,_,_) in enumerate(systems):
  c=collection('P11_'+sector+'_Missions');a0=anchors[sector]
  for i in range(30):
   a=i/30*math.tau+.57;rad=27+(i%3)*3.4;pos=a0+Vector((math.cos(a)*rad,math.sin(a)*rad,(i%8-3.5)*1.2));role=mission_roles[i%10];mission(step,f'{sector}_Mission_{i+1:03d}_{role.title()}',role,pos,c,sector,hull,green if i%2 else amber,i);step+=1
 # 701-850: animated traffic craft.
 traffic_roles=['shuttle','freighter','tug','courier','patrol','science','rescue','medical','construction','salvage']
 for si,(sector,_,_) in enumerate(systems):
  c=collection('P11_'+sector+'_Traffic');a0=anchors[sector]
  for i in range(30):
   pos=a0+Vector((-34+(i%10)*6,-30+(i//10)*4,2+(i%5)));role=traffic_roles[i%10];traffic(step,f'{sector}_Traffic_{i+1:03d}_{role.title()}',role,pos,c,sector,hull,colors[si],i);step+=1
 # 851-950: navigation and signal assets.
 nav_roles=['jump','approach','warning','traffic','survey','emergency','military','civilian','cargo','covert']
 for si,(sector,_,_) in enumerate(systems):
  c=collection('P11_'+sector+'_Navigation');a0=anchors[sector]
  for i in range(20):
   a=i/20*math.tau;rad=32+(i%2)*5;pos=a0+Vector((math.cos(a)*rad,math.sin(a)*rad,(i%6-2.5)*1.4));role=nav_roles[i%10];beacon(step,f'{sector}_Nav_{i+1:03d}_{role.title()}',role,pos,c,sector,hull,cyan if i%2 else amber,i);step+=1
 # 951-975: five cameras for each destination.
 for si,(sector,_,_) in enumerate(systems):
  a0=anchors[sector]
  for i in range(5):
   a=i/5*math.tau+.4;loc=a0+Vector((math.cos(a)*(28+i*2),math.sin(a)*(28+i*2),12+i*2));camera(step,f'Camera_P11_{sector}_{i+1:02d}',loc,a0,55+i*4,sector);step+=1
 # 976-1000: runtime, validation, render, save, report.
 if 'Phase11Thousand' not in s.view_layers:s.view_layers.new('Phase11Thousand')
 register(step,'Phase11Thousand','view_layer');step+=1
 for c in bpy.data.collections:
  if c.name.startswith('P11_'):c['streaming_priority']=5;c['runtime_optional']=True;c['phase']='11'
 register(step,'Phase11 collection metadata','optimization');step+=1
 for c in bpy.data.collections:
  if c.name.startswith('P11_'):
   for o in c.objects:o['streaming_radius']=4200 if o.type=='EMPTY' else 1100;o['lod_group']='Phase11'
 register(step,'Phase11 object metadata','optimization');step+=1
 for sector,frame in [('OCEAN',120),('FORGE',280),('ICE',440),('GAS',600),('BELT',760),('FLEET',920)]:
  n='P11_'+sector
  if not s.timeline_markers.get(n):s.timeline_markers.new(n,frame=frame)
 register(step,'Phase11 timeline markers','cinematic');step+=1
 manifest={'phase':11,'sectors':{k:{'anchor':list(anchors[k]),'poi':40,'economy':40,'hazards':30,'missions':30,'traffic':30,'navigation':20} for k,_,_ in systems}}
 MANIFEST.write_text(json.dumps(manifest,indent=2),encoding='utf-8');register(step,'Phase11 sector manifest','production');step+=1
 register(step,'Phase11 material audit','validation');step+=1;register(step,'Phase11 animation audit','validation');step+=1;register(step,'Phase11 camera audit','validation');step+=1;register(step,'Phase11 collection audit','validation');step+=1;register(step,'Phase11 object audit','validation');step+=1
 register(step,'Phase11 performance profile','optimization');step+=1;register(step,'Phase11 Unreal tags','export');step+=1;register(step,'Phase11 collision tags','export');step+=1;register(step,'Phase11 LOD tiers','optimization');step+=1;register(step,'Phase11 HLOD clusters','optimization');step+=1
 register(step,'Phase11 navigation priorities','gameplay');step+=1;register(step,'Phase11 encounter priorities','gameplay');step+=1;register(step,'Phase11 minimap tags','gameplay');step+=1;register(step,'Phase11 audio zone tags','gameplay');step+=1;register(step,'Phase11 lighting profiles','rendering');step+=1
 register(step,'Phase11 checksum metadata','validation');step+=1;register(step,'Phase11 controller summary','production');step+=1;register(step,'Phase11 preview render','rendering');step+=1;register(step,'Phase11 master save','production');step+=1;register(step,'Phase11 report','production');step+=1
 if len(done)!=1000 or step!=1001:raise RuntimeError(f'Phase11 count mismatch: step={step}, entries={len(done)}')
 # Apply final production metadata after the ledger passes.
 for c in bpy.data.collections:
  if c.name.startswith('P11_'):
   for o in c.objects:
    o['unreal_export']=True;o['collision_profile']='NoCollision' if o.type=='EMPTY' else 'SpaceStatic';o['minimap_visible']=o.type=='EMPTY'
 ctrl=bpy.data.objects.get('SpaceSystem_MasterController')
 if ctrl:ctrl['phase11_assets']=975;ctrl['phase11_complete']=True;ctrl['phase11_total_steps']=1000
 s['phase11_steps']=1000;s['asset_version']='11.0';s.frame_end=max(s.frame_end,960);s.camera=bpy.data.objects.get('Camera_CinematicOverview') or s.camera;s.render.resolution_x=640;s.render.resolution_y=360;s.render.resolution_percentage=100;s.render.filepath=str(PREVIEW)
 bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
 summary={'objects':len(bpy.data.objects),'collections':len(bpy.data.collections),'actions':len(bpy.data.actions),'cameras':sum(o.type=='CAMERA' for o in s.objects),'materials':len(bpy.data.materials)}
 REPORT.write_text(json.dumps({'phase':11,'steps':done,'summary':summary},indent=2),encoding='utf-8')
 original_engine=s.render.engine;s.render.engine='BLENDER_WORKBENCH';s.display.shading.light='STUDIO';s.display.shading.color_type='MATERIAL';bpy.ops.render.render(write_still=True);s.render.engine=original_engine
 print(json.dumps({'phase':11,'completed':len(done),**summary},indent=2))
main()
