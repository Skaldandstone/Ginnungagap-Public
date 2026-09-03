"""Recompose the procedural master to the blue-white radiation-system concept quality bar."""
import json, math, random, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems'
MASTER=OUT/'SpaceSystems_Master.blend';HERO=OUT/'SpaceSystems_RadiationSystem_Hero.blend'
PREVIEW=OUT/'SpaceSystems_RadiationSystem_Hero.png';REPORT=OUT/'SpaceSystems_RadiationSystem_Hero.json'
BACKDROP=OUT/'Textures'/'T_RadiationNebula_Backplate_v1.png';SHIP=ROOT/'Art'/'Ships'/'Exterior'/'ShipExteriors_Production.blend'
manifest=json.loads((OUT/'SpaceSystems_GenerationManifest.json').read_text(encoding='utf-8'));seed=int(manifest['seed']);R=random.Random(seed^0xB10E57A2)

def mat(name,color,metal=0,rough=.5,emit=0):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough
 if emit:b.inputs['Emission Color'].default_value=(*color,1);b.inputs['Emission Strength'].default_value=emit
 return m
def sphere(name,p,r,m,seg=48,rings=24):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,radius=r,location=p);o=bpy.context.object;o.name=name;o.data.materials.append(m)
 for f in o.data.polygons:f.use_smooth=True
 return o
def point_camera(cam,target):cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler()

def main():
 s=bpy.context.scene
 # Keep the generated solar-system catalog editable but exclude it from this cinematic view.
 for o in s.objects:o.hide_render=True
 old=bpy.data.collections.get('CONCEPT_HERO')
 if old:
  for o in list(old.objects):bpy.data.objects.remove(o,do_unlink=True)
  bpy.data.collections.remove(old)
 hero=bpy.data.collections.new('CONCEPT_HERO');s.collection.children.link(hero)
 def move(o):
  hero.objects.link(o)
  for c in list(o.users_collection):
   if c!=hero:c.objects.unlink(o)
  o.hide_render=False;return o

 # Camera-facing HDR-style background plate. The source is ship/planet-free and remains replaceable.
 img=bpy.data.images.load(str(BACKDROP),check_existing=True);img.pack()
 bg=bpy.data.materials.new('M_RadiationNebula_Backplate');bg.use_nodes=True;n=bg.node_tree.nodes;l=bg.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');tex=n.new('ShaderNodeTexImage');tex.image=img;tex.interpolation='Linear';em.inputs['Strength'].default_value=.72;l.new(tex.outputs['Color'],em.inputs['Color']);l.new(em.outputs['Emission'],out.inputs['Surface'])
 bpy.ops.mesh.primitive_plane_add(size=2,location=(0,28,8),rotation=(math.pi/2,0,0));plate=move(bpy.context.object);plate.name='Radiation_Nebula_Backplate';plate.scale=(36,20,1);plate.data.materials.append(bg)

 # Detailed authored carrier instanced from the production ship library.
 with bpy.data.libraries.load(str(SHIP),link=False) as (src,dst):dst.collections=['SM_Ship_LargeExpeditionCarrier']
 ship_collection=bpy.data.collections.get('SM_Ship_LargeExpeditionCarrier')
 carrier=bpy.data.objects.new('Hero_LargeExpeditionCarrier',None);carrier.instance_type='COLLECTION';carrier.instance_collection=ship_collection;carrier.location=(-9,-2,1.5);carrier.scale=(.0034,)*3;carrier.rotation_euler=(0,0,math.radians(-2));move(carrier)

 # Blue-white radiation star with noisy emissive surface and layered plasma loops.
 star_mat=bpy.data.materials.new('M_BlueWhite_RadiationStar');star_mat.use_nodes=True;n=star_mat.node_tree.nodes;l=star_mat.node_tree.links;b=n.get('Principled BSDF');noise=n.new('ShaderNodeTexNoise');noise.noise_dimensions='4D';noise.inputs['Scale'].default_value=5.5;noise.inputs['Detail'].default_value=9;noise.inputs['Roughness'].default_value=.78;ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.025,.18,1,1);ramp.color_ramp.elements[1].color=(1,1,1,1);mid=ramp.color_ramp.elements.new(.48);mid.color=(.12,.62,1,1);l.new(noise.outputs['Fac'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],b.inputs['Base Color']);l.new(ramp.outputs['Color'],b.inputs['Emission Color']);b.inputs['Emission Strength'].default_value=5.5;b.inputs['Roughness'].default_value=.22
 star=sphere('BlueWhite_Radiation_Primary',(12,8,11),5.8,star_mat,96,48);move(star)
 plasma=mat('M_BlueWhite_Plasma',(.08,.42,1),rough=.15,emit=4)
 for i in range(7):
  bpy.ops.mesh.primitive_torus_add(major_radius=6.3+R.uniform(-.25,.5),minor_radius=R.uniform(.012,.04),major_segments=96,minor_segments=8,location=star.location,rotation=(R.uniform(-.9,.9),R.uniform(-.55,.55),R.uniform(0,math.tau)));move(bpy.context.object).data.materials.append(plasma)

 # Sparse planets: dark silhouettes with cool radiation rims.
 rock=mat('M_RadiationWorld',(.006,.012,.026),metal=.08,rough=.78);rim=mat('M_RadiationRim',(.02,.25,.75),rough=.22,emit=1.6)
 placements=[((-22,7,9),3.7),((24,12,13),1.45),((17,4,-1),2.0)]
 for i,(p,radius) in enumerate(placements):
  world=sphere(f'RadiationWorld_{i+1:02d}',p,radius,rock);move(world)
  toward=Vector((star.location.x-p[0],0,star.location.z-p[2])).normalized()
  edge=sphere(f'RadiationWorld_Rim_{i+1:02d}',Vector(p)+toward*radius*.16+Vector((0,.22,0)),radius,rim);move(edge)

 # Debris river and foreground scale, randomized but deterministic for this system seed.
 debris_mat=mat('M_RadiationDebris',(.018,.026,.04),metal=.18,rough=.72)
 for i in range(180):
  t=R.random();x=-32+t*64;y=R.uniform(-1,10);z=-8+t*13+math.sin(t*math.tau*2)*2+R.gauss(0,1.6);size=R.uniform(.035,.22)*(1.8 if i<18 else 1)
  bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=size,location=(x,y,z));o=move(bpy.context.object);o.name=f'RadiationDebris_{i:03d}';o.scale=(R.uniform(.6,1.8),R.uniform(.6,1.5),R.uniform(.6,1.6));o.rotation_euler=[R.random()*math.tau for _ in range(3)];o.data.materials.append(debris_mat)

 # Ship key/rim light motivated by the star, plus restrained cool fill.
 bpy.ops.object.light_add(type='AREA',location=(6,-8,12));key=move(bpy.context.object);key.name='RadiationStar_Key';key.data.energy=5000;key.data.color=(.32,.62,1);key.data.shape='DISK';key.data.size=12;point_camera(key,carrier.location)
 bpy.ops.object.light_add(type='AREA',location=(-18,-12,8));fill=move(bpy.context.object);fill.name='Carrier_BlueFill';fill.data.energy=1800;fill.data.color=(.04,.16,.42);fill.data.size=16;point_camera(fill,carrier.location)
 bpy.ops.object.light_add(type='AREA',location=(-8,5,-5));rimlight=move(bpy.context.object);rimlight.name='Carrier_Rim';rimlight.data.energy=1500;rimlight.data.color=(.2,.55,1);rimlight.data.size=9;point_camera(rimlight,carrier.location)

 bpy.ops.object.camera_add(location=(0,-62,7));cam=move(bpy.context.object);cam.name='Camera_RadiationSystem_ConceptHero';cam.data.lens=52;cam.data.sensor_width=36;point_camera(cam,(0,2,5));s.camera=cam
 s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1920;s.render.resolution_y=817;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.film_transparent=False;s.render.filepath=str(PREVIEW);s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-.35
 s.world.color=(0,0,0);s['concept_reference']='docs/concept-art/reference/space/blue-white-radiation-system.png';s['hero_style']='blue-white radiation cinematic';s['procedural_seed']=str(seed)
 report={'seed':seed,'reference':s['concept_reference'],'carrier_collection':ship_collection.name,'debris_count':180,'plasma_loops':7,'planets':len(placements),'backplate':BACKDROP.name,'resolution':[1920,817]}
 REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(HERO));bpy.ops.render.render(write_still=True);bpy.ops.wm.save_as_mainfile(filepath=str(HERO));print(json.dumps(report,indent=2))
main()
