"""Build the first three registry-backed demo solar-system maps."""
import json, math, random, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();ARGS=sys.argv[sys.argv.index('--')+2:];GALAXY=ROOT/'Art'/'GalaxyMap';OUT=GALAXY/'DemoSystems';REGISTRY=GALAXY/'GalaxyMap_SystemRegistry.json'
TARGETS=[
 ('c6449799-ec65-58df-b772-9aead6c05d5e','BlueWhiteStar'),('447921b0-1426-5c6f-abdf-509add2baab5','FracturedWorld'),('ae965473-01da-5a4a-bb7e-44586e62020a','GravityAnomaly'),
 ('fdd34910-86ef-5501-af89-dbba3ec4919a','BlueWhiteStar'),('a568a44f-f2b4-5f74-9f7d-57f0d8372b34','BlueWhiteStar'),('f65e4815-efc7-5972-9b5d-139a8d2a13db','CosmicRift'),
 ('ef6cca24-ebc8-56f8-ac08-55d7af8c171c','CosmicRift'),('4271022d-b609-55c5-bd8e-039ce41282f2','GravityAnomaly'),('bb0085e7-e9c4-561f-8e95-6d244572f2aa','FracturedWorld'),
 ('eb1e6600-f683-5609-8667-7e8bf52c919b','GravityAnomaly'),('335350a3-1066-5d6d-b588-78687388d139','BlueWhiteStar'),('0e5f6cba-f0c3-5412-bb80-68654512a358','CosmicRift')]
CONCEPTS={'BlueWhiteStar':ROOT/'docs'/'concept-art'/'space-systems'/'blue-white-radiation-system.png','FracturedWorld':ROOT/'docs'/'concept-art'/'space-systems'/'fractured-ring-world.png','GravityAnomaly':ROOT/'docs'/'concept-art'/'space-systems'/'gravity-anomaly-bridge.png','CosmicRift':ROOT/'Content'/'Assets'/'SpaceSystems'/'Source'/'T_SpaceSky_CosmicRift.png'}
registry=json.loads(REGISTRY.read_text(encoding='utf-8'));by_id={x['system_id']:x for x in registry['systems']}

def mat(name,color,emit=0,rough=.5,metal=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
 if emit:b.inputs['Emission Color'].default_value=(*color,1);b.inputs['Emission Strength'].default_value=emit
 return m
def sphere(name,p,r,m,seg=48):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=seg//2,radius=r,location=p);o=bpy.context.object;o.name=name;o.data.materials.append(m)
 for f in o.data.polygons:f.use_smooth=True
 return o
def curve(name,r,m):
 d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=.012;d.bevel_resolution=2;s=d.splines.new('NURBS');s.points.add(63)
 for i,p in enumerate(s.points):a=math.tau*i/63;p.co=(math.cos(a)*r,0,math.sin(a)*r,1)
 s.use_cyclic_u=True;s.order_u=3;o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.data.materials.append(m);o['editor_only']=True;o.hide_render=True;return o
def procedural_background(concept_reference,R):
 s=bpy.context.scene;s.world=bpy.data.worlds.new('ProceduralDeepSpace');s.world.use_nodes=True;bg=s.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.00015,.0004,.0015,1);bg.inputs['Strength'].default_value=.018;s['concept_reference']=str(concept_reference.relative_to(ROOT)).replace('\\','/')
 star=mat('M_ProceduralStarfield',(.35,.62,1),7,.18)
 for i in range(320):
  p=(R.uniform(-20,20),R.uniform(4.5,6),R.uniform(-10,12));sphere(f'SkyStar_{i:03d}',p,R.choice([.008,.012,.018,.028]),star,8).data.materials[0]=star
 volume=bpy.data.materials.new('M_ProceduralNebulaVolume');volume.use_nodes=True;n=volume.node_tree.nodes;l=volume.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');pv=n.new('ShaderNodeVolumePrincipled');pv.inputs['Color'].default_value=(.01,.08,.42,1);pv.inputs['Density'].default_value=0;pv.inputs['Emission Color'].default_value=(.005,.08,.55,1);pv.inputs['Emission Strength'].default_value=.18;tc=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.noise_dimensions='4D';noise.inputs['Scale'].default_value=.42;noise.inputs['Detail'].default_value=8;noise.inputs['Roughness'].default_value=.76;ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.47;ramp.color_ramp.elements[0].color=(0,0,0,1);ramp.color_ramp.elements[1].position=.7;ramp.color_ramp.elements[1].color=(.035,.035,.035,1);l.new(tc.outputs['Generated'],noise.inputs['Vector']);l.new(noise.outputs['Fac'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],pv.inputs['Density']);l.new(pv.outputs['Volume'],out.inputs['Volume']);bpy.ops.mesh.primitive_cube_add(location=(0,4.5,1));cloud=bpy.context.object;cloud.name='ProceduralNebulaVolume';cloud.scale=(20,1.5,10);cloud.data.materials.append(volume);cloud['background_geometry']=True
def planet_mat(name,dark,light,rough=.55,emit=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;b=n.get('Principled BSDF');noise=n.new('ShaderNodeTexNoise');noise.noise_dimensions='4D';noise.inputs['Scale'].default_value=RANDOM_SCALE.get(name,5);noise.inputs['Detail'].default_value=7;noise.inputs['Roughness'].default_value=.72;ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*dark,1);ramp.color_ramp.elements[1].color=(*light,1);l.new(noise.outputs['Fac'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],b.inputs['Base Color']);b.inputs['Roughness'].default_value=rough
 if emit:l.new(ramp.outputs['Color'],b.inputs['Emission Color']);b.inputs['Emission Strength'].default_value=emit
 return m
RANDOM_SCALE={'M_DarkWorld':8,'M_IceWorld':5,'M_OceanWorld':3.5,'M_VolcanicWorld':7,'M_GasGiant':2.2}
def empty(name,p,role):
 o=bpy.data.objects.new(name,None);o.location=p;o.empty_display_type='SPHERE';o.empty_display_size=.35;o['gameplay_role']=role;bpy.context.collection.objects.link(o);return o
def build(system,visual_style):
 kind=system['dominant_phenomenon'];bpy.ops.wm.read_factory_settings(use_empty=True);s=bpy.context.scene;R=random.Random(system['system_seed']);folder=OUT/f"{system['display_name']}_{system['system_id'][:8]}";folder.mkdir(parents=True,exist_ok=True);procedural_background(CONCEPTS[visual_style],R)
 dark=planet_mat('M_DarkWorld',(.002,.006,.014),(.035,.06,.09),.76);ice=planet_mat('M_IceWorld',(.025,.12,.2),(.42,.8,1),.34);ocean=planet_mat('M_OceanWorld',(.001,.015,.06),(.01,.28,.72),.24);volcanic=planet_mat('M_VolcanicWorld',(.004,.001,.001),(.8,.018,.002),.58,1.1);gas=planet_mat('M_GasGiant',(.03,.008,.08),(.65,.18,.06),.5);star_blue=planet_mat('M_BlueWhiteStar',(.01,.16,.8),(.8,.95,1),.16,5);star_red=planet_mat('M_RedStar',(.18,.002,.001),(1,.07,.004),.2,4);route=mat('M_OrbitGuide',(.01,.3,.65),1.5,.3);debris=mat('M_Debris',(.025,.03,.04),rough=.82);anomaly=mat('M_Anomaly',(.25,.015,.65),4,.18);rim=mat('M_AtmosphereRim',(.01,.28,1),2.2,.22)
 star_material=star_blue if system['star_type'] in ('BlueWhiteStar','NeutronStar') else star_red;star=sphere('PrimaryStar',(7,1,5),2.45,star_material,72);star['star_type']=system['star_type']
 if system['star_type']=='BinaryStars':sphere('SecondaryStar',(10,1,7),2.1,star_blue,64)
 body_mats={'barren':dark,'ocean':ocean,'volcanic':volcanic,'ice':ice,'gas_giant':gas,'toxic':volcanic,'tidally_locked':dark};body_records=[]
 for i,body in enumerate(system['celestial_bodies']):
  radius=5.2+i*2.2;angle=R.uniform(0,math.tau);p=Vector((math.cos(angle)*radius,0,math.sin(angle)*radius));size=R.uniform(.35,.75)*(1.8 if body['type']=='gas_giant' else 1);curve(f'Orbit_{i+1:02d}',radius,route);toward=Vector((star.location.x-p.x,0,star.location.z-p.z)).normalized();sphere(f'Body_{i+1:02d}_Rim',p+toward*size*.1+Vector((0,.08,0)),size,rim,36);o=sphere(f'Body_{i+1:02d}_{body["type"]}',p,size,body_mats[body['type']],36);o['body_slot']=body['slot'];o['body_type']=body['type'];o['moon_count']=body['moons'];body_records.append({'object':o.name,'location':[round(x,3) for x in p],'radius':round(size,3),**body})
  for moon in range(body['moons']):
   ma=math.tau*moon/max(1,body['moons'])+R.random();mp=p+Vector((math.cos(ma),0,math.sin(ma)))*size*(1.65+moon*.4);sphere(f'{o.name}_Moon_{moon+1:02d}',mp,size*R.uniform(.08,.16),ice if moon%2 else dark,18)
 if kind=='FracturedWorld':
  for i in range(90):a=R.random()*math.tau;r=R.uniform(3.5,6.8);p=Vector((math.cos(a)*r,-.2,math.sin(a)*r));b=sphere(f'Fracture_{i:03d}',p,R.uniform(.035,.18),debris,10);b.scale=(R.uniform(.5,1.8),R.uniform(.5,1.4),R.uniform(.5,1.6))
 elif kind=='GravityAnomaly':
  for i in range(7):bpy.ops.mesh.primitive_torus_add(major_radius=2+i*.32,minor_radius=.035,major_segments=64,minor_segments=8,location=(-5,-.2,1),rotation=(math.pi/2,R.uniform(-.3,.3),R.uniform(-.3,.3)));bpy.context.object.name=f'GravityLens_{i+1:02d}';bpy.context.object.data.materials.append(anomaly)
 else:
  for i in range(3):bpy.ops.mesh.primitive_torus_add(major_radius=2.8+R.uniform(-.1,.35),minor_radius=.018,major_segments=72,minor_segments=8,location=star.location,rotation=(R.uniform(-.7,.7),R.uniform(-.35,.35),R.random()*math.tau));bpy.context.object.name=f'RadiationLoop_{i+1:02d}';bpy.context.object.data.materials.append(star_blue)
 empty('ArrivalAnchor',(-12,-1,-5),'player_arrival');empty('JumpExitAnchor',(-14,-1,-7),'jump_exit')
 for i in range(4):empty(f'EncounterAnchor_{i+1:02d}',(R.uniform(-12,12),-.5,R.uniform(-7,7)),'encounter')
 bpy.ops.object.camera_add(location=(0,-28,3));cam=bpy.context.object;cam.name='Camera_SystemOverview';cam.data.lens=52;cam.rotation_euler=(Vector((0,0,2))-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
 bpy.ops.object.light_add(type='AREA',location=(8,-8,7));key=bpy.context.object;key.name='StellarKey';key.data.energy=1600;key.data.color=(.25,.55,1) if system['star_type']!='RedDwarf' else (1,.12,.02);key.data.size=8;key.rotation_euler=(Vector((0,0,0))-key.location).to_track_quat('-Z','Y').to_euler()
 s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1600;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(folder/'Preview.png');s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-.45;s['system_id']=system['system_id'];s['system_seed']=system['system_seed'];s['display_name']=system['display_name'];s['danger_tier']=system['danger_tier'];s['dominant_phenomenon']=system['dominant_phenomenon'];blend=folder/f"{system['display_name']}_SystemMap.blend";glb=folder/f"{system['display_name']}_UnrealPreview.glb";manifest=folder/'SystemMap_Manifest.json';bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(blend));bpy.ops.render.render(write_still=True)
 bpy.ops.object.select_all(action='DESELECT')
 for o in s.objects:
  if o.type in {'MESH','CURVE'} and not o.get('editor_only') and not o.get('background_geometry'):o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_materials='EXPORT',export_animations=False)
 data={'schema_version':1,'system_id':system['system_id'],'display_name':system['display_name'],'system_seed':system['system_seed'],'dominant_phenomenon':kind,'star_type':system['star_type'],'danger_tier':system['danger_tier'],'hazards':system['hazards'],'resources':system['resources'],'bodies':body_records,'gameplay_anchors':['ArrivalAnchor','JumpExitAnchor','EncounterAnchor_01','EncounterAnchor_02','EncounterAnchor_03','EncounterAnchor_04'],'blend':str(blend.relative_to(ROOT)).replace('\\','/'),'glb':str(glb.relative_to(ROOT)).replace('\\','/'),'preview':str((folder/'Preview.png').relative_to(ROOT)).replace('\\','/'),'concept_source':str(CONCEPTS[visual_style].relative_to(ROOT)).replace('\\','/'),'visual_style':visual_style};manifest.write_text(json.dumps(data,indent=2),encoding='utf-8');return data
def main():
 OUT.mkdir(parents=True,exist_ok=True);only=ARGS[ARGS.index('--only')+1] if '--only' in ARGS else None;selected=[x for x in TARGETS if not only or by_id[x[0]]['display_name'].lower()==only.lower()];built=[]
 for system_id,visual_style in selected:built.append(build(by_id[system_id],visual_style))
 pelagos=next((x for x in registry['systems'] if x['display_name']=='Pelagos' and x.get('catalog_status')=='authored'),None)
 if pelagos and not only:
  built.append({'schema_version':1,'system_id':pelagos['system_id'],'display_name':'Pelagos','system_seed':pelagos['system_seed'],'dominant_phenomenon':pelagos['dominant_phenomenon'],'star_type':pelagos['star_type'],'danger_tier':pelagos['danger_tier'],'hazards':pelagos['hazards'],'resources':pelagos['resources'],'bodies':pelagos['celestial_bodies'],'blend':'Art/SpaceSystems/SpaceSystems_PelagosOrbitalArrival_Level.blend','glb':'Art/SpaceSystems/SpaceSystems_Gameplay.glb','preview':'Art/SpaceSystems/SpaceSystems_PelagosOrbitalArrival_Beauty.png','concept_source':'Art/SpaceSystems/Pelagos_OrbitalArrival_AAA_Concept_v1.png','visual_style':'authored_pelagos','local_operations_volumes':pelagos.get('local_operations_volumes',[])})
 for item in registry['systems']:
  match=next((x for x in built if x['system_id']==item['system_id']),None)
  if match:
   if match['display_name']=='Pelagos':item['system_map']={'status':'demo_ready','generation_mode':'authored_astronomical','map_asset':'/Game/Assets/Maps/SpaceSystems/L_PelagosOrbitalArrival','source_manifest':'Art/SpaceSystems/SpaceSystems_PelagosOrbitalArrival_Manifest.json'}
   else:item['system_map']={'status':'demo_ready','generation_mode':'procedural_blender','map_asset':None,'source_manifest':str((ROOT/match['blend']).parent.joinpath('SystemMap_Manifest.json').relative_to(ROOT)).replace('\\','/')}
 REGISTRY.write_text(json.dumps(registry,indent=2),encoding='utf-8');index_path=OUT/'DemoSystems_Index.json';existing=json.loads(index_path.read_text(encoding='utf-8')).get('systems',[]) if index_path.exists() else [];merged={x['system_id']:x for x in existing};merged.update({x['system_id']:x for x in built});index_path.write_text(json.dumps({'schema_version':1,'systems':list(merged.values())},indent=2),encoding='utf-8');print(json.dumps({'built':len(built),'systems':[x['display_name'] for x in built]},indent=2))
main()
