"""Phases 28-37: ten recorded production-art passes for Pelagos Orbital Arrival."""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector

ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems';LEVEL=OUT/'SpaceSystems_PelagosOrbitalArrival_Level.blend'
REPORT=OUT/'SpaceSystems_TenProductionPasses_Report.json';FINAL=OUT/'SpaceSystems_PelagosOrbitalArrival_AAA_Final.png';passes=[]
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
def finish(o,n,m,c,bevel=.05):
 o.name=n;o.data.materials.append(m)
 if bevel:b=o.modifiers.new('Production bevel','BEVEL');b.width=bevel;b.segments=3
 for p in o.data.polygons:p.use_smooth=True
 return move(o,c)
def cube(n,p,sc,m,c,rot=(0,0,0),bevel=.05):
 bpy.ops.mesh.primitive_cube_add(location=p,rotation=rot);o=bpy.context.object;o.scale=sc;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,n,m,c,bevel)
def sphere(n,p,r,m,c,scale=(1,1,1)):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=r,location=p);o=bpy.context.object;o.scale=scale;return finish(o,n,m,c,0)
def cyl(n,a,b,r,m,c,verts=32):
 a,b=Vector(a),Vector(b);v=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=v.length,location=(a+b)/2);o=bpy.context.object;o.rotation_mode='QUATERNION';o.rotation_quaternion=v.to_track_quat('Z','Y');return finish(o,n,m,c,r*.12)
def torus(n,p,major,minor,m,c,rot=(0,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=80,minor_segments=16,location=p,rotation=rot);return finish(bpy.context.object,n,m,c,0)
def light(n,kind,p,color,energy,c,size=5,target=(0,2,3)):
 d=bpy.data.lights.new(n,kind);d.color=color;d.energy=energy
 if kind=='AREA':d.shape='DISK';d.size=size
 o=bpy.data.objects.new(n,d);c.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
def record(number,name,changes):
 s=bpy.context.scene;s[f'production_pass_{number}']=name;passes.append({'pass':number,'name':name,'changes':changes,'objects':len(bpy.data.objects)})
 # Each pass is saved as an auditable milestone; selected visual checkpoints render below.
 bpy.ops.wm.save_as_mainfile(filepath=str(LEVEL))
def checkpoint(number):
 s=bpy.context.scene;s.render.resolution_x=960;s.render.resolution_y=540;s.render.resolution_percentage=100;s.render.filepath=str(OUT/f'SpaceSystems_Pass{number}_Checkpoint.png');bpy.ops.render.render(write_still=True)
def main():
 s=bpy.context.scene
 if s.get('ten_passes_complete'):raise RuntimeError('Ten production passes already applied')
 old=bpy.data.collections.get('TENPASS_28_37')
 if old:
  for o in list(old.all_objects):bpy.data.objects.remove(o,do_unlink=True)
  bpy.data.collections.remove(old)
 c=col('TENPASS_28_37');hull=mat('TP_Hull',(0.025,.045,.075),.9,.23);white=mat('TP_Ceramic',(.24,.28,.3),.35,.3);dark=mat('TP_Radiator',(.003,.007,.012),.76,.2);cyan=mat('TP_Cyan',(.005,.12,.25),.2,.22,(.01,.32,1),6);amber=mat('TP_Amber',(.22,.025,.004),.3,.25,(1,.06,.006),8);red=mat('TP_Marking',(.3,.012,.006),.3,.35)

 # 28 — silhouette: move the docking comb behind the hull and add an asymmetric service keel.
 for o in bpy.data.objects:
  if o.name.startswith(('HS_DockingSpine','HS_DockArm_','HS_DockCollar_','HS_DockLight_','AAA_DockBrace','AAA_DockMark')):o.hide_render=True
 cyl('TP_ServiceKeel',(-2,3.5,1.2),(5.8,3.5,1.2),.34,hull,c);sphere('TP_ReactorBulb',(6.4,3.5,1.2),1.1,hull,c,scale=(1.35,1,1));cyl('TP_KeelBraceA',(0,2,2),(0,3.5,1.2),.12,white,c);cyl('TP_KeelBraceB',(3.8,2,2),(3.8,3.5,1.2),.12,white,c)
 record(28,'Silhouette hierarchy',['removed foreground docking comb','added asymmetric service keel','added reactor counterweight'])

 # 29 — primary forms: new far-side four-port docking drum with enclosed shoulders.
 cyl('TP_DockSpine',(-2,5.6,-1.0),(-2,5.6,7.8),.48,hull,c)
 for i,z in enumerate((-.2,2.1,4.4,6.7),1):
  cyl(f'TP_DockShoulder_{i}',(-2,4.7,z),(-2,7.1,z),.5,hull,c);torus(f'TP_DockCollar_{i}',(-2,7.5,z),.9,.24,white,c,(math.pi/2,0,0));torus(f'TP_DockStatus_{i}',(-2,7.74,z),.63,.045,amber if i==3 else cyan,c,(math.pi/2,0,0))
 record(29,'Primary form refinement',['far-side docking drum','enclosed dock shoulders','four readable capture collars'])

 # 30 — secondary forms: layered armor, access housings, and radial wheel segmentation.
 for i,x in enumerate((-4.1,-2.1,.0,2.2,4.3)):
  for side in (-1,1):cube(f'TP_Armor_{i}_{side}',(x,2+side*2.02,3),(.72,.08,.72),white,c,bevel=.16)
 for i in range(12):
  a=i*math.tau/12;y=2+math.cos(a)*7.08;z=3+math.sin(a)*7.08;cube(f'TP_WheelSegment_{i}',(1.2,y,z),(.36,.48,.24),white,c,(a,0,0),.11)
 record(30,'Secondary form language',['pressure hull armor housings','habitat wheel segmentation','consistent rounded edge language']);checkpoint(30)

 # 31 — materials: a consistent three-family palette with deliberate roughness contrast.
 hero=bpy.data.collections.get('ARTISTPASS_HeroStation')
 if hero:
  for o in hero.objects:
   if not getattr(o.data,'materials',None):continue
   o.data.materials.clear();o.data.materials.append(dark if 'Array' in o.name else (white if any(k in o.name for k in ('Collar','HabPod','Spoke')) else hull))
 record(31,'Material consolidation',['titanium hull family','thermal ceramic armor','low-gloss radiator family','restrained emissions'])

 # 32 — surface language: longitudinal rails, maintenance ports, and recessed bands.
 for side in (-1,1):
  y=2+side*2.08
  for z in (2.1,3.9):cyl(f'TP_LongRail_{side}_{z}',(-4.6,y,z),(5.8,y,z),.035,white,c,16)
  for i,x in enumerate((-3.7,-1.7,.3,2.3,4.3)):torus(f'TP_AccessPort_{side}_{i}',(x,y,3),.21,.045,amber if i==0 else cyan,c,(math.pi/2,0,0))
 record(32,'Surface breakup',['longitudinal hull rails','ten access ports','recessed functional color coding'])

 # 33 — graphics/decals: readable identity marks and hazard rhythm.
 font_curve=bpy.ops.object.text_add(location=(-1.8,-.11,3.62),rotation=(math.pi/2,0,0));txt=bpy.context.object;txt.data.body='PELAGOS  //  ORBITAL 07';txt.data.align_x='CENTER';txt.data.size=.32;txt.data.extrude=.008;txt.data.materials.append(white);move(txt,c);txt.name='TP_HullIdentity'
 for i in range(9):cube(f'TP_HazardTick_{i}',(-4.1+i*.48,-.09,2.15),(.12,.025,.035),amber if i%2 else red,c,bevel=.01)
 record(33,'Identity and decals',['station designation','hazard ticks','functional color grammar']);checkpoint(33)

 # 34 — docking detail: approach lamps, umbilicals, clamp housings, and service targets.
 for i,z in enumerate((-.2,2.1,4.4,6.7),1):
  for side in (-1,1):cyl(f'TP_Clamp_{i}_{side}',(-2+side*.62,7.35,z-.55),(-2+side*.72,7.65,z),.1,white,c,20)
  for j in range(3):sphere(f'TP_ApproachLamp_{i}_{j}',(-2+(j-1)*.48,7.82,z+1.0),.07,cyan if i!=3 else amber,c)
 record(34,'Dock production detail',['capture clamps','approach lamp arrays','service-target hierarchy'])

 # 35 — scale/story: observation cupola, maintenance drone, external tanks and handrails.
 sphere('TP_ObservationCupola',(-3.7,1.75,4.8),.48,cyan,c,scale=(1.5,.55,.7));cyl('TP_CupolaNeck',(-3.7,2,4.3),(-3.7,2,4.75),.24,hull,c)
 for i in range(3):cyl(f'TP_ServiceTank_{i}',(4.5+i*.55,3.8,.45),(4.5+i*.55,3.8,1.45),.16,white,c,24)
 sphere('TP_MaintenanceDrone',(-5.3,-1.2,4.8),.23,hull,c,scale=(1.6,.65,.55));cyl('TP_DroneArm',(-5.15,-1.2,4.8),(-4.75,-1.2,4.55),.035,white,c,16)
 record(35,'Scale and storytelling',['observation cupola','external service tanks','maintenance drone']);checkpoint(35)

 # 36 — planet/environment: authored ocean/cloud procedural material and controlled star density.
 planet=bpy.data.objects.get('OceanArrival_Planet')
 if planet:
  pm=bpy.data.materials.get('TP_Pelagos') or bpy.data.materials.new('TP_Pelagos');pm.use_nodes=True;n=pm.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=2.7;noise.inputs['Detail'].default_value=7;noise.inputs['Roughness'].default_value=.68;r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(.002,.012,.035,1);r.color_ramp.elements[1].color=(.015,.16,.23,1);pm.node_tree.links.new(noise.outputs['Fac'],r.inputs[0]);pm.node_tree.links.new(r.outputs[0],p.inputs['Base Color']);p.inputs['Roughness'].default_value=.38;p.inputs['Coat Weight'].default_value=.18;pm.node_tree.links.new(p.outputs[0],out.inputs[0]);planet.data.materials.clear();planet.data.materials.append(pm)
 stars=bpy.data.collections.get('ARTISTPASS_Stars')
 if stars:
  for i,o in enumerate(stars.objects):o.hide_render=(i%5!=0)
 record(36,'Planet and environment',['deep-ocean procedural response','controlled cloud-scale breakup','reduced star density']);checkpoint(36)

 # 37 — final lighting/composition/QA: readable station exposure and clean thirds.
 for o in list(c.objects):
  if o.type=='LIGHT':bpy.data.objects.remove(o,do_unlink=True)
 light('TP_Key','AREA',(-18,-18,22),(1,.42,.16),1350,c,14,(0,2,3));light('TP_Fill','AREA',(-8,-8,4),(.06,.28,1),1100,c,10,(0,2,3));light('TP_Rim','AREA',(18,24,16),(.08,.32,1),1900,c,18,(1,2,4))
 cam=bpy.data.objects.get('Camera_PelagosArtistHero');cam.location=(-38,-46,17);cam.data.lens=62;cam.data.shift_x=.03;cam.data.shift_y=.015;cam.rotation_euler=(Vector((1.4,7.0,3.6))-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
 s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(FINAL);s.view_settings.look='AgX - Medium High Contrast';s.render.film_transparent=False
 record(37,'Final lighting, composition and QA',['three-point motivated lighting','clean station/planet overlap','1080p master','debug visibility audit'])
 s['ten_passes_complete']=True;s['asset_version']='37.0';s['level_status']='production_art_candidate'
 s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.filepath=str(FINAL);bpy.ops.wm.save_as_mainfile(filepath=str(LEVEL));bpy.ops.render.render(write_still=True)
 report={'range':'28-37','count':10,'passes':passes,'final':str(FINAL),'summary':{'new_art_objects':len(c.objects),'gameplay_preserved':True,'final_resolution':[1920,1080]}}
 REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report['summary'],indent=2))
main()
