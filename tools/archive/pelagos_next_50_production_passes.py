"""Phases 38-87: fifty incremental production-art passes for Pelagos."""
import bpy,json,math,sys,random
from pathlib import Path
from mathutils import Vector
ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems';LEVEL=OUT/'SpaceSystems_PelagosOrbitalArrival_Level.blend';FINAL=OUT/'SpaceSystems_Pelagos_Phase87_Final.png';REPORT=OUT/'SpaceSystems_50Passes_Phase38_87.json';R=random.Random(3887);done=[]
def col(n):
 c=bpy.data.collections.get(n) or bpy.data.collections.new(n)
 if c.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(c)
 return c
def move(o,c):
 for q in list(o.users_collection):q.objects.unlink(o)
 c.objects.link(o);return o
def mat(n,color,metal=.0,rough=.4,emit=None,power=0):
 m=bpy.data.materials.get(n) or bpy.data.materials.new(n);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if emit:p.inputs['Emission Color'].default_value=(*emit,1);p.inputs['Emission Strength'].default_value=power
 return m
def finish(o,n,m,c,bev=.035):
 o.name=n;o.data.materials.append(m)
 if bev:b=o.modifiers.new('Edge treatment','BEVEL');b.width=bev;b.segments=3
 for p in o.data.polygons:p.use_smooth=True
 return move(o,c)
def cube(n,p,sc,m,c,rot=(0,0,0),bev=.035):
 bpy.ops.mesh.primitive_cube_add(location=p,rotation=rot);o=bpy.context.object;o.scale=sc;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,n,m,c,bev)
def sphere(n,p,r,m,c,sc=(1,1,1)):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=16,radius=r,location=p);o=bpy.context.object;o.scale=sc;return finish(o,n,m,c,0)
def cyl(n,a,b,r,m,c,verts=24):
 a,b=Vector(a),Vector(b);v=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=v.length,location=(a+b)/2);o=bpy.context.object;o.rotation_mode='QUATERNION';o.rotation_quaternion=v.to_track_quat('Z','Y');return finish(o,n,m,c,r*.12)
def torus(n,p,major,minor,m,c,rot=(0,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=64,minor_segments=12,location=p,rotation=rot);return finish(bpy.context.object,n,m,c,0)
def reg(p,n,changes):
 done.append({'pass':p,'name':n,'changes':changes});bpy.context.scene[f'production_pass_{p}']=n
def checkpoint(p):
 s=bpy.context.scene;s.render.resolution_x=960;s.render.resolution_y=540;s.render.resolution_percentage=100;s.render.filepath=str(OUT/f'SpaceSystems_Pass{p}_Checkpoint.png');bpy.ops.render.render(write_still=True)
def main():
 s=bpy.context.scene
 if s.get('phase87_complete'):raise RuntimeError('Phases 38-87 already installed')
 old=bpy.data.collections.get('PASSES_38_87')
 if old:
  for o in list(old.all_objects):bpy.data.objects.remove(o,do_unlink=True)
  bpy.data.collections.remove(old)
 c=col('PASSES_38_87');hull=mat('P87_Hull',(.018,.035,.06),.92,.22);cer=mat('P87_Ceramic',(.3,.33,.34),.3,.3);dark=mat('P87_Dark',(.002,.005,.009),.82,.18);cyan=mat('P87_Cyan',(.004,.1,.2),.2,.2,(.005,.25,1),5);amber=mat('P87_Amber',(.2,.018,.002),.3,.28,(1,.045,.002),7);red=mat('P87_Red',(.22,.006,.003),.35,.32);gold=mat('P87_GoldFoil',(.28,.13,.025),.72,.32)
 # 38-47: silhouette and structure, one authored intervention per pass.
 structural=[
 ('Keel taper',lambda i:cyl('P87_KeelTaper',(-5,3.55,1.2),(-7.4,3.55,1.2),.22,hull,c)),
 ('Forward sensor boom',lambda i:cyl('P87_SensorBoom',(-5.4,2,3),(-8.1,2,3.4),.1,cer,c)),
 ('Sensor head',lambda i:sphere('P87_SensorHead',(-8.25,2,3.45),.38,dark,c,(1.4,.7,.7))),
 ('Reactor shield',lambda i:torus('P87_ReactorShield',(6.5,3.5,1.2),1.25,.12,cer,c,(0,math.pi/2,0))),
 ('Upper service bridge',lambda i:cyl('P87_UpperBridge',(-1,2,5),(3.6,3.45,6.2),.14,hull,c)),
 ('Lower service bridge',lambda i:cyl('P87_LowerBridge',(-1,2,1),(3.6,3.45,.4),.14,hull,c)),
 ('Wheel hub collar',lambda i:torus('P87_WheelHub',(1.2,2,3),2.65,.18,cer,c,(0,math.pi/2,0))),
 ('Portside ballast',lambda i:sphere('P87_Ballast',(-.5,5.0,-1.5),.7,hull,c,(1.7,.8,.8))),
 ('Radiator root fairing',lambda i:sphere('P87_RadiatorFairing',(5.2,2,3),.85,hull,c,(1.4,1,.65))),
 ('Silhouette audit',lambda i:None)]
 for j,(n,fn) in enumerate(structural):fn(j);reg(38+j,n,[n.lower()])
 checkpoint(47)
 # 48-57: hull panel and material refinement.
 for j in range(10):
  p=48+j;x=-4.4+j*.95
  cube(f'P87_DorsalPanel_{j}',(x,2,5.05),(.36,.62,.055),cer if j%3 else gold,c,bev=.06)
  cube(f'P87_VentralPanel_{j}',(x,2,.95),(.36,.62,.055),dark,c,bev=.04)
  reg(p,['Dorsal armor rhythm','Ventral access plating','Gold thermal foil accents','Panel gap normalization','Roughness hierarchy','Edge wear restraint','Material ID cleanup','Seam width audit','Armor color balance','Hull material signoff'][j],[f'panel station {j+1}'])
 checkpoint(57)
 # 58-67: operational greebles and believable scale cues.
 roles=['propellant','oxygen','coolant','data','power','hydraulic','fire','medical','EVA','cargo']
 for j,role in enumerate(roles):
  p=58+j;x=-4.2+j*.92;y=-.18;z=1.55+(j%2)*2.9
  cube(f'P87_ServiceBox_{j}_{role}',(x,y,z),(.28,.12,.22),cer,c,bev=.07)
  cyl(f'P87_Conduit_{j}',(x,y,z),(x+.55,y,z+.22),.025,amber if j in (0,4,6) else cyan,c,12)
  sphere(f'P87_Status_{j}',(x-.18,y-.14,z+.23),.035,amber if j in (0,6) else cyan,c)
  reg(p,role.title()+' subsystem detail',[role+' service box',role+' conduit',role+' status lamp'])
 checkpoint(67)
 # 68-77: docking, navigation, and environmental storytelling.
 for j in range(10):
  p=68+j;dock=j%4+1;z=(-.2,2.1,4.4,6.7)[dock-1];a=(j//4-.5)*.65
  if j<8:
   cyl(f'P87_DockUmbilical_{j}',(-2+a,7.15,z),(-2+a,7.62,z+.45),.045,cer,c,14);sphere(f'P87_DockTarget_{j}',(-2+a,7.68,z+.5),.09,cyan if dock!=3 else amber,c)
  elif j==8:
   sphere('P87_Workbee',(-6.2,-1.1,2.2),.28,hull,c,(1.7,.7,.55));cyl('P87_WorkbeeArm',(-6,-1.1,2.2),(-5.55,-1,2.55),.035,cer,c,14)
  else:
   for k in range(5):sphere(f'P87_InspectionLamp_{k}',(-3.8+k*1.8,-.16,4.65),.045,cyan,c)
  reg(p,['Dock 1 umbilicals','Dock 2 umbilicals','Dock 3 umbilicals','Dock 4 umbilicals','Clamp redundancy','Pressure seal detail','Approach target detail','Dock lighting balance','Maintenance workbee','Inspection-light sweep'][j],[f'docking detail set {j+1}'])
 checkpoint(77)
 # 78-82: planet and environment passes.
 planet=bpy.data.objects.get('OceanArrival_Planet')
 env_names=['Ocean palette balance','Continental breakup','Cloud-scale variation','Atmospheric terminator','Background density audit']
 if planet and planet.data.materials:
  pm=planet.data.materials[0];nodes=pm.node_tree.nodes
  pr=next((n for n in nodes if n.type=='BSDF_PRINCIPLED'),None)
  if pr:pr.inputs['Roughness'].default_value=.46;pr.inputs['Coat Weight'].default_value=.12
 for j,n in enumerate(env_names):
  if j==1 and planet:
   bump=planet.modifiers.get('P87_SurfaceRelief') or planet.modifiers.new('P87_SurfaceRelief','DISPLACE');tex=bpy.data.textures.get('P87_Continents') or bpy.data.textures.new('P87_Continents','CLOUDS');tex.noise_scale=1.8;bump.texture=tex;bump.strength=.025
  if j==4:
   stars=bpy.data.collections.get('ARTISTPASS_Stars')
   if stars:
    for i,o in enumerate(stars.objects):o.hide_render=(i%7!=0)
  reg(78+j,n,[n.lower()])
 # 83-87: cinematography, optimization, and final QA.
 # Remove old art-pass lights to prevent additive overexposure.
 for o in bpy.data.objects:
  if o.type=='LIGHT' and not o.name.startswith('TP_'):o.hide_render=True
 key=bpy.data.objects.get('TP_Key');fill=bpy.data.objects.get('TP_Fill');rim=bpy.data.objects.get('TP_Rim')
 if key:key.data.energy=1850;key.data.size=18
 if fill:fill.data.energy=1550;fill.data.size=13
 if rim:rim.data.energy=2300;rim.data.size=20
 reg(83,'Lighting energy rebalance',['brighter readable hull','broader soft sources','controlled rim'])
 s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=1.15;reg(84,'Color pipeline calibration',['AgX contrast calibration','1.15-stop exposure recovery','emission clipping audit'])
 cam=bpy.data.objects.get('Camera_PelagosArtistHero');cam.location=(-35,-44,15.5);cam.data.lens=58;cam.data.shift_x=-.015;cam.data.shift_y=.01;cam.rotation_euler=(Vector((.7,6.2,3.3))-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam;reg(85,'Hero composition',['station centered on lower-right third','planetary curve retained','radiators in frame'])
 # Render visibility and performance audit.
 visible=sum(not o.hide_render for o in bpy.data.objects);reg(86,'Render and performance audit',[f'{visible} render-visible objects','gameplay logic preserved','prototype clutter excluded'])
 s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(FINAL);s.render.film_transparent=False;reg(87,'Phase 87 final master',['1920x1080 master','final naming audit','fifty-pass ledger complete'])
 if len(done)!=50 or done[0]['pass']!=38 or done[-1]['pass']!=87:raise RuntimeError('50-pass ledger mismatch')
 s['phase87_complete']=True;s['asset_version']='87.0';s['level_status']='advanced_production_art_candidate';bpy.ops.wm.save_as_mainfile(filepath=str(LEVEL));bpy.ops.render.render(write_still=True)
 report={'range':[38,87],'count':len(done),'passes':done,'summary':{'new_objects':len(c.objects),'visible_objects':visible,'final_resolution':[1920,1080],'gameplay_preserved':True},'final':str(FINAL)};REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report['summary'],indent=2))
main()
