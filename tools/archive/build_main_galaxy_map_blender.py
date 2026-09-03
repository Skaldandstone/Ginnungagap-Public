"""Build the standalone procedural Ginnungagap galaxy map from approved concept art only."""
import json, math, random, secrets, sys, uuid
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();ARGS=sys.argv[sys.argv.index('--')+2:]
OUT=ROOT/'Art'/'GalaxyMap';BLEND=OUT/'GalaxyMap_Master.blend';PREVIEW=OUT/'GalaxyMap_Preview.png';MANIFEST=OUT/'GalaxyMap_Manifest.json';REGISTRY=OUT/'GalaxyMap_SystemRegistry.json'
CONCEPT=ROOT/'Content'/'Assets'/'SpaceSystems'/'Source'/'T_SpaceSky_CosmicRift.png'
seed=int(ARGS[ARGS.index('--seed')+1],0) if '--seed' in ARGS else secrets.randbits(63);R=random.Random(seed)
def option(name,default):return int(ARGS[ARGS.index(name)+1]) if name in ARGS else default

def clear():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 for c in list(bpy.data.collections):
  if c.name!='Collection':bpy.data.collections.remove(c)
def col(name):
 c=bpy.data.collections.get(name) or bpy.data.collections.new(name)
 if c.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(c)
 return c
def move(o,c):
 if o.name not in c.objects:c.objects.link(o)
 for x in list(o.users_collection):
  if x!=c:x.objects.unlink(o)
def mat(name,color,emit=0,alpha=1):
 m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=.32;b.inputs['Alpha'].default_value=alpha
 if emit:b.inputs['Emission Color'].default_value=(*color,1);b.inputs['Emission Strength'].default_value=emit
 if alpha<1:m.surface_render_method='DITHERED'
 return m
def sphere(name,p,radius,m,c,segments=12):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=max(6,segments//2),radius=radius,location=p);o=bpy.context.object;o.name=name;o.data.materials.append(m);move(o,c);return o
def curve(name,points,m,c,width=.018):
 data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=width;data.bevel_resolution=2;spline=data.splines.new('BEZIER');spline.bezier_points.add(len(points)-1)
 for bp,p in zip(spline.bezier_points,points):bp.co=p;bp.handle_left_type='AUTO';bp.handle_right_type='AUTO'
 o=bpy.data.objects.new(name,data);c.objects.link(o);o.data.materials.append(m);return o
def backdrop():
 image=bpy.data.images.load(str(CONCEPT),check_existing=True);image.pack();m=bpy.data.materials.new('M_GalaxyConcept_Backdrop');m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');em=n.new('ShaderNodeEmission');tex=n.new('ShaderNodeTexImage');tex.image=image;em.inputs['Strength'].default_value=.62;l.new(tex.outputs['Color'],em.inputs['Color']);l.new(em.outputs['Emission'],out.inputs['Surface'])
 bpy.ops.mesh.primitive_plane_add(size=2,location=(0,4,0),rotation=(math.pi/2,0,0));o=bpy.context.object;o.name='Galaxy_ConceptTopology';o.scale=(20,10,1);o.data.materials.append(m);move(o,col('00_ConceptFoundation'))
def system_name(index):
 starts=['Ael','Bor','Cygn','Dra','Eir','Fen','Ginn','Hel','Iri','Jot','Kyr','Lys','Myr','Nid','Or','Pel','Rim','Skad','Tyr','Vann']
 ends=['ara','eon','heim','ion','ora','os','rift','skar','us','veil','yr'];return starts[(index*7+3)%len(starts)]+ends[(index*11+5)%len(ends)]
def system_definition(index):
 system_id=str(uuid.uuid5(uuid.NAMESPACE_URL,f'ginnungagap:system-catalog:{index}'));system_seed=uuid.UUID(system_id).int%2147483646+1;sr=random.Random(system_seed)
 star_type=sr.choice(['GoldenGiant','BlueWhiteStar','BinaryStars','VioletDwarf','RedDwarf','NeutronStar']);phenomenon=sr.choice([star_type,'IonNebula','GravityAnomaly','FracturedWorld']);planet_types=['barren','ocean','volcanic','ice','gas_giant','toxic','tidally_locked'];resource_types=['NavigationFuel','StructuralAlloy','CryoCoolant','LifeSupportFilters','SensorComponents','PowerCells'];hazard_types=['SolarRadiationStorm','CosmicRadiationBelt','MicroDebrisField','ThermalExtreme','MicrogravityShear']
 return {'system_id':system_id,'display_name':system_name(index),'system_seed':system_seed,'star_type':star_type,'dominant_phenomenon':phenomenon,'danger_tier':sr.randint(1,5),'celestial_bodies':[{'slot':n+1,'type':sr.choice(planet_types),'moons':sr.randint(0,4)} for n in range(sr.randint(3,9))],'hazards':sr.sample(hazard_types,sr.randint(1,3)),'resources':sr.sample(resource_types,sr.randint(2,5))}

def main():
 OUT.mkdir(parents=True,exist_ok=True);previous={}
 if REGISTRY.exists():
  old=json.loads(REGISTRY.read_text(encoding='utf-8'))
  if int(old.get('galaxy_seed',-1))==seed:previous={x['system_id']:x for x in old.get('systems',[])}
 bpy.context.preferences.filepaths.save_version=0;clear();s=bpy.context.scene;backdrop()
 node_mats=[mat('M_Map_Cyan',(.01,.42,1),4.5),mat('M_Map_Violet',(.42,.03,1),4.2),mat('M_Map_Amber',(1,.22,.015),4.5),mat('M_Map_White',(.65,.82,1),5)]
 route_mats=[mat('M_Route_Cyan',(.01,.25,.7),2.2),mat('M_Route_Violet',(.32,.015,.72),2),mat('M_Route_Amber',(.75,.12,.005),2.1)]
 anomaly_mat=mat('M_Map_Anomaly',(1,.03,.2),5);nodes_c=col('10_StarNodes');routes_c=col('20_JumpRoutes');regions_c=col('30_Regions');anomaly_c=col('40_Anomalies');labels_c=col('50_Labels')
 # Anchors echo the concept's blue-left, violet-center, and amber-right rift masses.
 anchors=[(-13,-1.5,0),(-7,2.5,0),(-1,-2.7,0),(6,1.5,0),(12,-.5,0),(15,3.2,0)]
 rolled_region_count=R.randint(7,11);region_count=option('--region-count',rolled_region_count);min_nodes=option('--min-nodes',8);max_nodes=option('--max-nodes',16)
 if not 1<=region_count<=32 or not 2<=min_nodes<=max_nodes<=64:raise ValueError('Expansion limits: regions 1-32; nodes 2-64 with min <= max')
 regions=[];all_nodes=[];systems=[]
 for i in range(region_count):
  base=Vector(anchors[i%len(anchors)])+Vector((R.uniform(-2,2),0,R.uniform(-1.5,1.5)));palette=0 if base.x<-5 else (1 if base.x<5 else 2);count=R.randint(min_nodes,max_nodes);region_nodes=[]
  for j in range(count):
   p=base+Vector((R.gauss(0,1.65),R.uniform(-.18,.18)-.25,R.gauss(0,.95)));size=R.uniform(.028,.075)*(2.2 if j==0 else 1);o=sphere(f'G_{i+1:02d}_Node_{j+1:02d}',p,size,node_mats[3] if j==0 else node_mats[palette],nodes_c,10);node_class='capital' if j==0 else R.choice(['charted','frontier','resource','hazard']);system_index=len(systems);definition=system_definition(system_index);system_id=definition['system_id'];display_name=definition['display_name'];system_seed=definition['system_seed']
   binding=previous.get(system_id,{}).get('system_map',{'status':'generated_definition','generation_mode':'procedural','map_asset':None,'source_manifest':None});extensions=previous.get(system_id,{}).get('extensions',{})
   o['region_id']=i+1;o['node_class']=node_class;o['system_id']=system_id;o['display_name']=display_name;o['system_seed']=system_seed;o['system_map_status']=binding.get('status','generated_definition');region_nodes.append(o);all_nodes.append(o);systems.append({**definition,'node_id':o.name,'placement':{'playthrough_seed':seed,'region_id':i+1,'galaxy_position':[round(p.x,4),round(p.z,4)],'route_node':o.name},'node_class':node_class,'discovery_state':'known' if node_class=='capital' else 'unscanned','tags':previous.get(system_id,{}).get('tags',[]),'system_map':binding,'extensions':extensions})
  regions.append({'id':i+1,'center':[round(base.x,3),round(base.z,3)],'palette':['cyan','violet','amber'][palette],'nodes':[o.name for o in region_nodes]})
  bpy.ops.object.text_add(location=(base.x,-.45,base.z-1.25),rotation=(math.pi/2,0,0));label=bpy.context.object;label.name=f'Region_{i+1:02d}_Label';label.data.body=f'SECTOR {i+1:02d}';label.data.align_x='CENTER';label.data.size=.24;label.data.extrude=.002;label.data.materials.append(node_mats[palette]);move(label,labels_c)
 # Authored campaign systems keep their identities/content but receive a fresh placement per playthrough.
 authored=[x for x in previous.values() if x.get('catalog_status')=='authored']
 for authored_index,source in enumerate(authored):
  region_index=(seed+authored_index*7)%len(regions);region=regions[region_index];center=Vector((region['center'][0],-.25,region['center'][1]));p=center+Vector((R.uniform(-1.4,1.4),0,R.uniform(-.8,.8)));o=sphere(f'Authored_{source["display_name"]}_Node',p,.16,node_mats[3],nodes_c,14);system_id=source['system_id'];binding=source.get('system_map',{'status':'unbuilt','generation_mode':'authored','map_asset':None,'source_manifest':None});o['region_id']=region_index+1;o['node_class']=source.get('node_class','authored_hub');o['system_id']=system_id;o['display_name']=source['display_name'];o['system_seed']=source['system_seed'];o['system_map_status']=binding.get('status','unbuilt');definition={k:v for k,v in source.items() if k not in {'node_id','placement','discovery_state','system_map','extensions','tags'}};entry={**definition,'node_id':o.name,'placement':{'playthrough_seed':seed,'region_id':region_index+1,'galaxy_position':[round(p.x,4),round(p.z,4)],'route_node':o.name},'node_class':source.get('node_class','authored_hub'),'discovery_state':source.get('discovery_state','known'),'tags':source.get('tags',[]),'system_map':binding,'extensions':source.get('extensions',{})};systems.append(entry);all_nodes.append(o);region['nodes'].append(o.name)
 # Local routes plus a sparse connected backbone.
 route_records=[]
 for i,region in enumerate(regions):
  objs=[bpy.data.objects[n] for n in region['nodes']];hub=objs[0]
  for j,target in enumerate(objs[1:R.randint(4,min(8,len(objs)))],1):
   mid=(hub.location+target.location)*.5+Vector((R.uniform(-.4,.4),-.08,R.uniform(-.35,.35)));o=curve(f'Route_{i+1:02d}_{j:02d}',[hub.location,mid,target.location],route_mats[i%3],routes_c,.014);route_records.append([hub.name,target.name])
  for target in [x for x in objs if x.name.startswith('Authored_')]:
   if [hub.name,target.name] not in route_records:mid=(hub.location+target.location)*.5+Vector((0,-.1,R.uniform(-.45,.45)));curve(f'AuthoredRoute_{target.name}',[hub.location,mid,target.location],route_mats[i%3],routes_c,.03);route_records.append([hub.name,target.name])
 for i in range(len(regions)-1):
  a=bpy.data.objects[regions[i]['nodes'][0]];b=bpy.data.objects[regions[i+1]['nodes'][0]];mid=(a.location+b.location)*.5+Vector((0,-.12,R.uniform(-1.2,1.2)));curve(f'Backbone_{i+1:02d}',[a.location,mid,b.location],route_mats[i%3],routes_c,.026);route_records.append([a.name,b.name])
 anomalies=[]
 for i in range(R.randint(3,6)):
  p=Vector((R.uniform(-16,16),-.3,R.uniform(-6.5,6.5)));bpy.ops.mesh.primitive_torus_add(major_radius=R.uniform(.18,.42),minor_radius=.025,major_segments=32,minor_segments=6,location=p,rotation=(math.pi/2,0,0));o=bpy.context.object;o.name=f'RiftAnomaly_{i+1:02d}';o.data.materials.append(anomaly_mat);o['threat']='uncharted_rift';move(o,anomaly_c);anomalies.append(o.name)
 bpy.ops.object.camera_add(location=(0,-28,0));cam=bpy.context.object;cam.name='Camera_GalaxyMap';cam.data.type='ORTHO';cam.data.ortho_scale=40;cam.rotation_euler=(math.pi/2,0,0);s.camera=cam;move(cam,col('90_Camera'))
 s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1920;s.render.resolution_y=960;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(PREVIEW);s.render.film_transparent=False;s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-.2;s.world.color=(0,0,0)
 s['asset']='Ginnungagap Overall Galaxy Map';s['generation_seed']=str(seed);s['scope']='galaxy-scale only; no ships, planets, or system-level assets';s['concept_source']='Content/Assets/SpaceSystems/Source/T_SpaceSky_CosmicRift.png'
 # Authored catalog systems may intentionally have no placement in this playthrough. Preserve them
 # in the identity registry until galaxy-generation rules explicitly place them.
 placed_ids={entry['system_id'] for entry in systems}
 systems.extend(entry for entry in previous.values() if entry.get('catalog_status')=='authored' and entry['system_id'] not in placed_ids)
 node_to_id={entry['node_id']:entry['system_id'] for entry in systems if entry.get('node_id')};route_links=[{'route_id':f'ROUTE-{i+1:04d}','from_system_id':node_to_id[a],'to_system_id':node_to_id[b],'travel_cost':round(1+Vector(bpy.data.objects[a].location-bpy.data.objects[b].location).length*.18,2),'status':'charted'} for i,(a,b) in enumerate(route_records)]
 data={'schema_version':3,'seed':seed,'scope':'overall_galaxy_map','identity_model':'persistent_systems_procedural_placement','concept_source':s['concept_source'],'generation_options':{'region_count':region_count,'min_nodes':min_nodes,'max_nodes':max_nodes},'regions':regions,'route_count':len(route_records),'routes':route_links,'anomalies':anomalies,'node_count':len(all_nodes),'system_registry':REGISTRY.name,'extensions':{}};registry={'schema_version':3,'galaxy_seed':seed,'identity_model':'system_id_and_contents_are_stable; placement_and_routes_are_per_playthrough','binding_preservation':'merge_by_system_id','systems':systems,'extensions':{}};MANIFEST.write_text(json.dumps(data,indent=2),encoding='utf-8');REGISTRY.write_text(json.dumps(registry,indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(BLEND));bpy.ops.render.render(write_still=True);bpy.ops.wm.save_as_mainfile(filepath=str(BLEND));print(json.dumps({'seed':seed,'regions':len(regions),'nodes':len(all_nodes),'routes':len(route_records),'anomalies':len(anomalies),'populated_systems':len(systems),'preserved_bindings':sum(1 for x in systems if x['system_map']['map_asset'])},indent=2))
main()
