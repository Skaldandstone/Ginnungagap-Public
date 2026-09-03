"""Phase 26: replace the Pelagos blockout station with a coherent hero asset."""
import json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve(); OUT=ROOT/'Art'/'SpaceSystems'
LEVEL=OUT/'SpaceSystems_PelagosOrbitalArrival_Level.blend'
PREVIEW=OUT/'SpaceSystems_PelagosOrbitalArrival_ArtistPass.png'
REPORT=OUT/'SpaceSystems_HeroStation_Report.json'

def col(name):
 c=bpy.data.collections.get(name) or bpy.data.collections.new(name)
 if c.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(c)
 return c
def mat(name,color,metal=.0,rough=.4,emit=None,power=0):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True
 p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if emit:p.inputs['Emission Color'].default_value=(*emit,1);p.inputs['Emission Strength'].default_value=power
 return m
def finish(o,name,m,c,bevel=.08):
 o.name=name;o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=True
 if bevel:b=o.modifiers.new('Machined edge','BEVEL');b.width=bevel;b.segments=3
 for x in list(o.users_collection):x.objects.unlink(o)
 c.objects.link(o);return o
def cyl(name,a,b,r,m,c,verts=48):
 a,b=Vector(a),Vector(b);v=b-a
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=v.length,location=(a+b)/2)
 o=bpy.context.object;o.rotation_mode='QUATERNION';o.rotation_quaternion=v.to_track_quat('Z','Y');return finish(o,name,m,c,r*.12)
def cube(name,p,scale,m,c,bevel=.12,rot=(0,0,0)):
 bpy.ops.mesh.primitive_cube_add(location=p,rotation=rot);o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,name,m,c,bevel)
def sphere(name,p,r,m,c):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=32,radius=r,location=p);return finish(bpy.context.object,name,m,c,0)
def torus(name,p,major,minor,m,c,rot=(0,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=96,minor_segments=20,location=p,rotation=rot);return finish(bpy.context.object,name,m,c,0)
def main():
 s=bpy.context.scene
 if s.get('hero_station_version')=='26.1':raise RuntimeError('Hero station 26.1 already installed')
 old=bpy.data.collections.get('ARTISTPASS_HeroStation')
 if old:
  for o in list(old.all_objects):bpy.data.objects.remove(o,do_unlink=True)
  bpy.data.collections.remove(old)
 c=col('ARTISTPASS_HeroStation')
 # Hide prototype asset piles. Planet, atmosphere, jump gate and gameplay logic remain intact.
 hidden_cols=['LEVEL_DetailGeometry','LEVEL_DockingGameplay','LEVEL_DockingSystem','LEVEL_DockProps','LEVEL_Props','P20_DockModules','P20_ServiceProps','P20_TrafficFleet','P20_MissionEncounters','P20_NavigationHUD','P21_DockMarkings','P21_EnvironmentalEvents']
 for n in hidden_cols:
  q=bpy.data.collections.get(n)
  if q:q.hide_render=True
 geo=bpy.data.collections.get('LEVEL_Geometry')
 if geo:
  for o in geo.objects:
   if not ('Planet' in o.name or 'Atmosphere' in o.name):o.hide_render=True
 for o in bpy.data.objects:
  if o.name.startswith(('DockGuide_','PlayerShip_','P20_Traffic_','Traffic_')):o.hide_render=True
 hull=mat('HS26_Titanium',(0.055,.075,.1),.82,.25);ceramic=mat('HS26_Ceramic',(.28,.34,.38),.25,.3);dark=mat('HS26_Radiator',(.006,.012,.022),.55,.2)
 amber=mat('HS26_Amber',(.2,.035,.006),.3,.25,(1,.12,.015),12);cyan=mat('HS26_Cyan',(.005,.08,.12),.25,.2,(.01,.35,1),9);glass=mat('HS26_Glass',(.008,.025,.04),.25,.08,(.005,.05,.08),.5)
 # Long pressure vessel with nested armor collars and a tapered command prow.
 cyl('HS_CorePressureHull',(-5,2,3),(7,2,3),2.05,hull,c)
 sphere('HS_CommandProw',(-5.2,2,3),2.03,glass,c);sphere('HS_ReactorCap',(7.1,2,3),2.0,dark,c)
 for x,r in [(-3.8,2.32),(-1.0,2.25),(2.0,2.25),(5.0,2.28)]:
  torus('HS_ArmorCollar_'+str(x),(x,2,3),r,.19,ceramic,c,(0,math.pi/2,0))
 # Large habitat wheel with genuine structural hierarchy rather than repeated blocks.
 torus('HS_HabitatWheel',(1.2,2,3),7.1,.72,hull,c,(0,math.pi/2,0))
 torus('HS_HabitatWindowBand',(1.2,2,3),7.12,.16,cyan,c,(0,math.pi/2,0))
 for i in range(8):
  a=i*math.tau/8;y=2+math.cos(a)*6.6;z=3+math.sin(a)*6.6
  cyl(f'HS_Spoke_{i+1:02d}',(1.2,2,3),(1.2,y,z),.16,ceramic,c,32)
  # Habitation pods follow the circumference with rounded, restrained silhouettes.
  pod=sphere(f'HS_HabPod_{i+1:02d}',(1.2,y,z),1,ceramic,c);pod.scale=(1.35,.72,.5);pod.rotation_euler=(a,0,0)
 # Docking truss and four enclosed capture collars on the camera-facing side.
 cyl('HS_DockingSpine',(-1.5,-4.8,-2.2),(-1.5,-4.8,8.2),.42,hull,c)
 for i,z in enumerate((-1.2,1.5,4.2,6.9),1):
  cyl(f'HS_DockArm_{i}',(-1.5,-4.8,z),( -1.5,-9.0,z),.34,hull,c)
  torus(f'HS_DockCollar_{i}',(-1.5,-9.25,z),1.05,.22,ceramic,c,(math.pi/2,0,0))
  torus(f'HS_DockLight_{i}',(-1.5,-9.48,z),.76,.055,amber if i==3 else cyan,c,(math.pi/2,0,0))
 # Paired solar/radiator wings with a believable segmented surface rhythm.
 for side in (-1,1):
  y=2+side*3.0;cyl(f'HS_ArrayBoom_{side}',(5.2,2,3),(5.2,y,3),.16,hull,c)
  for j in range(5):
   yy=y+side*(1.05+j*1.35)
   cube(f'HS_Array_{side}_{j}',(5.2,yy,3),(2.5,.55,.055),dark,c,.04)
   cube(f'HS_ArrayLine_{side}_{j}',(5.2,yy,3.07),(2.42,.035,.012),cyan,c,.01)
 # Antenna crown and navigation beacon.
 cyl('HS_AntennaMast',(3.8,2,5.0),(3.8,2,9.8),.13,ceramic,c)
 torus('HS_AntennaDish',(3.8,2,9.6),1.0,.12,hull,c,(math.pi/2,0,0));sphere('HS_NavBeacon',(3.8,2,10.65),.18,amber,c)
 for o in c.objects:o['production_role']='hero_station';o['phase']=26
 s['hero_station_version']='26.1';s['hero_station_status']='production_art_replacement'
 # Recompose close enough to read craftsmanship while retaining the planetary scale.
 cam=bpy.data.objects.get('Camera_PelagosArtistHero')
 if cam:
  cam.location=(-40,-48,20);cam.data.lens=55;cam.rotation_euler=(Vector((2,11,3.8))-cam.location).to_track_quat('-Z','Y').to_euler()
 s.camera=cam;s.render.filepath=str(PREVIEW);s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100
 report={'phase':26,'version':'26.1','prototype_collections_hidden':len(hidden_cols)+1,'hero_meshes':len(c.objects),'design':'rotating habitat wheel with pressure hull, enclosed docks, radiator arrays and antenna crown','gameplay_preserved':True}
 REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(LEVEL));bpy.ops.render.render(write_still=True);print(json.dumps(report,indent=2))
main()
