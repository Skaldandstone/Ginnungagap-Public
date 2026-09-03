"""Build a curated, production-quality Ocean Arrival vertical-slice level."""
import json,math,random,sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems';TEX=OUT/'Textures';SOURCE=OUT/'SpaceSystems_ProductionMap.blend';LEVEL=OUT/'SpaceSystems_OceanArrival_Level.blend';PREVIEW=OUT/'SpaceSystems_OceanArrival_Beauty.png';REPORT=OUT/'SpaceSystems_OceanArrival_Report.json';R=random.Random(1601)
def col(n):
 c=bpy.data.collections.get(n) or bpy.data.collections.new(n)
 if c.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(c)
 return c
def move(o,c):
 if o.name not in c.objects:c.objects.link(o)
 for x in list(o.users_collection):
  if x!=c:x.objects.unlink(o)
 return o
def mat(name,base,metal=.0,rough=.45,emit=None,strength=0):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(*base,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
 if emit:bs.inputs['Emission Color'].default_value=(*emit,1);bs.inputs['Emission Strength'].default_value=strength
 m.node_tree.links.new(bs.outputs['BSDF'],out.inputs['Surface']);m.diffuse_color=(*base,1);return m
def panel_mat(name,base,accent):
 m=mat(name,base,.88,.3);n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF');tc=n.new('ShaderNodeTexCoord');tc.location=(-700,0);noise=n.new('ShaderNodeTexNoise');noise.location=(-480,40);noise.inputs['Scale'].default_value=9;noise.inputs['Detail'].default_value=4;vor=n.new('ShaderNodeTexVoronoi');vor.location=(-480,-210);vor.distance='CHEBYCHEV';vor.inputs['Scale'].default_value=18;ramp=n.new('ShaderNodeValToRGB');ramp.location=(-150,30);ramp.color_ramp.elements[0].color=(*base,1);ramp.color_ramp.elements[1].color=(*accent,1);ramp.color_ramp.elements[0].position=.24;ramp.color_ramp.elements[1].position=.74;bump=n.new('ShaderNodeBump');bump.location=(80,-180);bump.inputs['Strength'].default_value=.2;bump.inputs['Distance'].default_value=.025;l.new(tc.outputs['Object'],noise.inputs['Vector']);l.new(tc.outputs['Object'],vor.inputs['Vector']);l.new(noise.outputs['Fac'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],bs.inputs['Base Color']);l.new(vor.outputs['Distance'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal']);return m
def ocean_mat():
 img=bpy.data.images.get('T_Planet_OceanClouds') or bpy.data.images.load(str(TEX/'T_Planet_OceanClouds.png'),check_existing=True);img.pack();m=mat('LVL_OceanPlanet',(.03,.14,.3),.02,.38);n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF');tc=n.new('ShaderNodeTexCoord');tex=n.new('ShaderNodeTexImage');tex.image=img;tex.interpolation='Linear';bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.35;bump.inputs['Distance'].default_value=.08;l.new(tc.outputs['Generated'],tex.inputs['Vector']);l.new(tex.outputs['Color'],bs.inputs['Base Color']);l.new(tex.outputs['Color'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal']);bs.inputs['Coat Weight'].default_value=.22;return m
def cube(n,p,scale,m,c,bevel=.08):
 bpy.ops.mesh.primitive_cube_add(location=p);o=bpy.context.object;o.name=n;o.scale=scale;o.data.materials.append(m);move(o,c)
 if bevel:mod=o.modifiers.new('Production Bevel','BEVEL');mod.width=bevel;mod.segments=3
 return o
def cyl(n,p,r,d,m,c,rot=(0,0,0),v=24,bevel=.06):
 bpy.ops.mesh.primitive_cylinder_add(vertices=v,radius=r,depth=d,location=p,rotation=rot);o=bpy.context.object;o.name=n;o.data.materials.append(m);move(o,c)
 if bevel:mod=o.modifiers.new('Production Bevel','BEVEL');mod.width=bevel;mod.segments=3
 return o
def sphere(n,p,r,m,c,seg=48):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=seg//2,radius=r,location=p);o=bpy.context.object;o.name=n;o.data.materials.append(m);move(o,c)
 for f in o.data.polygons:f.use_smooth=True
 return o
def torus(n,p,major,minor,m,c,rot=(0,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=64,minor_segments=12,location=p,rotation=rot);o=bpy.context.object;o.name=n;o.data.materials.append(m);move(o,c)
 for f in o.data.polygons:f.use_smooth=True
 return o
def curve(n,pts,bevel,m,c):
 d=bpy.data.curves.new(n+'_Curve','CURVE');d.dimensions='3D';d.bevel_depth=bevel;d.bevel_resolution=3;sp=d.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
 for p,co in zip(sp.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
 o=bpy.data.objects.new(n,d);c.objects.link(o);d.materials.append(m);return o
def light(name,kind,loc,color,energy,size,target,c):
 data=bpy.data.lights.new(name,kind);data.energy=energy;data.color=color
 if kind=='AREA':data.shape='DISK';data.size=size
 o=bpy.data.objects.new(name,data);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();c.objects.link(o);return o
def camera(name,loc,target,c):
 data=bpy.data.cameras.new(name);data.lens=48;data.sensor_width=36;data.clip_end=5000;data.dof.use_dof=True;data.dof.focus_distance=(Vector(target)-Vector(loc)).length;data.dof.aperture_fstop=7.1;o=bpy.data.objects.new(name,data);o.location=loc;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();c.objects.link(o);return o
def main():
 s=bpy.context.scene
 # Hide the procedural catalog from this curated beauty-shot level.
 hidden=0
 for c in bpy.data.collections:
  if c.name.startswith(('P8_','P9_','P10_','P11_','P12_','MAP_')):c.hide_render=True;c.hide_viewport=True;hidden+=1
 level=col('LEVEL_OceanArrival');geo=col('LEVEL_Geometry');props=col('LEVEL_Props');fx=col('LEVEL_FX');lights=col('LEVEL_Lighting');cams=col('LEVEL_Cameras')
 for c in (geo,props,fx,lights,cams):
  if c.name in s.collection.children:s.collection.children.unlink(c)
  if c.name not in level.children:level.children.link(c)
 hull=panel_mat('LVL_Hull_Navy',(.012,.026,.045),(.08,.18,.24));white=panel_mat('LVL_Hull_Ceramic',(.16,.2,.22),(.42,.5,.52));paint=mat('LVL_SafetyOrange',(.65,.055,.008),.72,.3);glass=mat('LVL_Glass',(.005,.055,.09),.2,.12);cyan=mat('LVL_Emission_Cyan',(.005,.08,.18),.15,.16,(0,.55,1),14);amber=mat('LVL_Emission_Amber',(.18,.025,.001),.1,.18,(1,.12,.003),12);green=mat('LVL_Emission_Green',(.002,.12,.025),.1,.18,(0,1,.18),10);ocean=ocean_mat();dark=mat('LVL_Asteroid',(.035,.026,.022),.05,.86)
 # Textured planet and atmospheric rim establish the destination.
 sphere('OceanArrival_Planet',(16,38,4),13,ocean,geo,64);atmo=mat('LVL_Atmosphere',(.008,.12,.45),.0,.16,(0,.18,1),1.8);shell=sphere('OceanArrival_Atmosphere',(16,38,4),13.35,atmo,fx,64);shell.display_type='TEXTURED'
 # Hero orbital station: hub, rotating rings, axial docks, and asymmetric silhouette.
 cyl('Station_MainHub',(0,2,2.5),3.2,7.2,hull,geo,(math.pi/2,0,0),48,.12);torus('Station_HabitatRing',(0,2,2.5),5.4,.42,white,geo,(math.pi/2,0,0));torus('Station_ServiceRing',(0,2,2.5),3.9,.18,paint,geo,(math.pi/2,0,0));sphere('Station_CommandDome',(-1.8,2,5.4),1.45,glass,geo,48)
 for i in range(8):a=i/8*math.tau;y=2+math.cos(a)*5.4;z=2.5+math.sin(a)*5.4;cyl(f'RingModule_{i+1:02d}',(0,y,z),.52,2.3,white if i%2 else hull,geo,(0,math.pi/2,0),20,.08);sphere(f'RingWindow_{i+1:02d}',(-1.2,y,z),.18,cyan,props,20)
 # Docking arms create traversable/readable approach geometry.
 for i,z in enumerate([-1.2,1.1,4.1,6.8]):
  cube(f'DockArm_{i+1}',(-7.5,2,z),(4.5,.42,.3),hull,geo,.1);cube(f'DockPad_{i+1}',(-12,2,z),(1.4,1.8,.18),white,geo,.08);cube(f'DockStripe_{i+1}',(-12,2,z+.2),(1.2,1.5,.025),paint,props,.02);torus(f'DockGuide_{i+1}',(-13.5,2,z+.8),1.25,.07,cyan,fx,(0,math.pi/2,0))
 # Solar wings and communications crown.
 for side in (-1,1):
  cube('SolarBoom_'+str(side),(3.8,2,2.5),(2.2,.14,.14),hull,geo,.05);cube('SolarWing_'+str(side),(6.2,2,2.5),(2.1,3.6,.045),glass,props,.025)
  for j in range(5):cube(f'SolarCell_{side}_{j}',(6.2,2+(j-2)*1.35,2.58),(1.95,.58,.018),cyan,props,.01)
 cyl('CommMast',(0,2,8.4),.2,5.2,hull,geo);torus('CommDish',(0,2,10.8),1.15,.12,white,geo,(math.pi/2,0,0));sphere('CommBeacon',(0,2,11.4),.22,amber,fx,24)
 # Foreground player craft gives scale and a clear destination line.
 cyl('PlayerShip_Hull',(-17,-9,2),.72,7.5,hull,geo,(0,math.pi/2,0),32,.12);cube('PlayerShip_Wing',(-17,-9,2), (2.2,2.9,.12),white,geo,.08);cube('PlayerShip_Cockpit',(-14.2,-9,2.45),(1.25,.68,.38),glass,props,.14)
 for y in (-9.55,-8.45):sphere('PlayerShip_Drive_'+str(y),(-20.7,y,2),.3,cyan,fx,24)
 # Approach lane, beacons, landing lights, and a restrained asteroid layer.
 curve('ArrivalLane',[(-24,-12,2),(-16,-8,2.2),(-8,-2,2.8),(-3,1,3)],.035,cyan,fx)
 for i in range(7):t=i/6;p=Vector((-22,-11,1.1)).lerp(Vector((-5,0,2.2)),t);sphere(f'ApproachBeacon_{i+1}',p,.12,green,fx,16)
 for i in range(42):a=R.uniform(0,math.tau);rad=R.uniform(28,52);p=(math.cos(a)*rad,math.sin(a)*rad,R.uniform(-12,18));o=sphere(f'BackgroundRock_{i+1:02d}',p,R.uniform(.18,.85),dark,props,12);o.scale=(1,R.uniform(.6,1.6),R.uniform(.55,1.4))
 # Cinematic three-point lighting and a warm star direction.
 light('Level_Sun','SUN',(-20,-20,35),(1,.32,.08),3.2,0,(0,2,2),lights);light('Level_Key','AREA',(-9,-14,18),(.18,.42,1),1600,12,(0,2,2),lights);light('Level_Rim','AREA',(18,18,16),(1,.12,.025),2100,10,(0,2,3),lights);light('Level_Fill','AREA',(-18,8,5),(.03,.18,1),900,14,(-8,2,2),lights)
 cam=camera('Camera_OceanArrival_Beauty',(-27,-25,14),(-1,3,3),cams);s.camera=cam
 # Dark, colored world instead of diagnostic gray.
 w=bpy.data.worlds.get('OceanArrivalWorld') or bpy.data.worlds.new('OceanArrivalWorld');w.use_nodes=True;bg=w.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.0004,.0012,.006,1);bg.inputs['Strength'].default_value=.08;s.world=w
 s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(PREVIEW);s.view_settings.look='AgX - Medium High Contrast';s['level_name']='Ocean Arrival';s['level_status']='vertical_slice';s['hidden_catalog_collections']=hidden;s['asset_version']='16.0'
 # Keep the beauty pass compositor-neutral so material values remain readable in Blender 5.2.
 report={'phase':16,'level':'Ocean Arrival','status':'vertical_slice','hidden_catalog_collections':hidden,'objects':len(bpy.data.objects),'level_objects':sum(len(c.objects) for c in (geo,props,fx,lights,cams)),'materials':['LVL_Hull_Navy','LVL_Hull_Ceramic','LVL_SafetyOrange','LVL_Glass','LVL_Emission_Cyan','LVL_Emission_Amber','LVL_Emission_Green','LVL_OceanPlanet'],'features':['curated visibility','textured planet','hero orbital station','docking pads','solar wings','player craft','approach lane','navigation beacons','three-point lighting','colored world','Eevee beauty render']}
 REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(LEVEL));bpy.ops.render.render(write_still=True);print(json.dumps(report,indent=2))
main()
