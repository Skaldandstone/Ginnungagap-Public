"""Build Ginnos as a clean 3D production-quality system-map vertical slice."""
import json, math, random, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'GalaxyMap'/'DemoSystems'/'Ginnos_c6449799';BLEND=OUT/'Ginnos_SystemMap_v2.blend';PREVIEW=OUT/'Ginnos_ProductionPreview.png';GLB=OUT/'Ginnos_Production.glb';REPORT=OUT/'Ginnos_ProductionManifest.json';SEED=529913223;R=random.Random(SEED)
def clean():bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def simple_mat(name,color,rough=.5,metal=0,emit=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF');b.inputs['Base Color'].default_value=(*color,1);b.inputs['Roughness'].default_value=rough;b.inputs['Metallic'].default_value=metal
 if emit:b.inputs['Emission Color'].default_value=(*color,1);b.inputs['Emission Strength'].default_value=emit
 return m
def surface_mat(name,dark,mid,light,scale,rough,emit=0):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;b=n.get('Principled BSDF');tc=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.noise_dimensions='4D';noise.inputs['Scale'].default_value=scale;noise.inputs['Detail'].default_value=9;noise.inputs['Roughness'].default_value=.76;noise.inputs['Distortion'].default_value=.18;ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*dark,1);ramp.color_ramp.elements[1].color=(*light,1);middle=ramp.color_ramp.elements.new(.48);middle.color=(*mid,1);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.24;bump.inputs['Distance'].default_value=.08;l.new(tc.outputs['Generated'],noise.inputs['Vector']);l.new(noise.outputs['Fac'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],b.inputs['Base Color']);l.new(noise.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],b.inputs['Normal']);b.inputs['Roughness'].default_value=rough
 if emit:l.new(ramp.outputs['Color'],b.inputs['Emission Color']);b.inputs['Emission Strength'].default_value=emit
 return m
def volume_mat(name,color,scale,density,emission):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');v=n.new('ShaderNodeVolumePrincipled');v.inputs['Color'].default_value=(*color,1);v.inputs['Density'].default_value=0;v.inputs['Emission Color'].default_value=(*color,1);v.inputs['Emission Strength'].default_value=emission
 tc=n.new('ShaderNodeTexCoord');large=n.new('ShaderNodeTexNoise');large.noise_dimensions='4D';large.inputs['Scale'].default_value=scale;large.inputs['Detail'].default_value=9;large.inputs['Roughness'].default_value=.86;large.inputs['Distortion'].default_value=.35
 fine=n.new('ShaderNodeTexNoise');fine.noise_dimensions='4D';fine.inputs['Scale'].default_value=scale*5.2;fine.inputs['Detail'].default_value=6;fine.inputs['Roughness'].default_value=.72
 multiply=n.new('ShaderNodeMath');multiply.operation='MULTIPLY';ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='EASE';ramp.color_ramp.elements[0].position=.27;ramp.color_ramp.elements[0].color=(0,0,0,1);ramp.color_ramp.elements[1].position=.66;ramp.color_ramp.elements[1].color=(density,)*3+(1,)
 l.new(tc.outputs['Generated'],large.inputs['Vector']);l.new(tc.outputs['Generated'],fine.inputs['Vector']);l.new(large.outputs['Fac'],multiply.inputs[0]);l.new(fine.outputs['Fac'],multiply.inputs[1]);l.new(multiply.outputs[0],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],v.inputs['Density']);l.new(v.outputs['Volume'],out.inputs['Volume']);return m
def atmosphere_mat(name,color,strength=2.2):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');transparent=n.new('ShaderNodeBsdfTransparent');emission=n.new('ShaderNodeEmission');emission.inputs['Color'].default_value=(*color,1);emission.inputs['Strength'].default_value=strength;layer=n.new('ShaderNodeLayerWeight');ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='EASE';ramp.color_ramp.elements[0].position=.68;ramp.color_ramp.elements[0].color=(0,0,0,1);ramp.color_ramp.elements[1].position=.93;ramp.color_ramp.elements[1].color=(1,1,1,1);mix=n.new('ShaderNodeMixShader');l.new(layer.outputs['Facing'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],mix.inputs[0]);l.new(transparent.outputs[0],mix.inputs[1]);l.new(emission.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface']);return m
def cloud_mat(name):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');transparent=n.new('ShaderNodeBsdfTransparent');cloud=n.new('ShaderNodeBsdfPrincipled');cloud.inputs['Base Color'].default_value=(.48,.62,.75,1);cloud.inputs['Roughness'].default_value=.78;cloud.inputs['Emission Color'].default_value=(.02,.055,.11,1);cloud.inputs['Emission Strength'].default_value=.12;tc=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.noise_dimensions='4D';noise.inputs['Scale'].default_value=3.6;noise.inputs['Detail'].default_value=9;noise.inputs['Roughness'].default_value=.82;noise.inputs['Distortion'].default_value=.28;fine=n.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=15;fine.inputs['Detail'].default_value=5;mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.38;ramp.color_ramp.elements[0].color=(0,0,0,1);ramp.color_ramp.elements[1].position=.57;ramp.color_ramp.elements[1].color=(1,1,1,1);mix=n.new('ShaderNodeMixShader');l.new(tc.outputs['Generated'],noise.inputs['Vector']);l.new(tc.outputs['Generated'],fine.inputs['Vector']);l.new(noise.outputs['Fac'],mult.inputs[0]);l.new(fine.outputs['Fac'],mult.inputs[1]);l.new(mult.outputs[0],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],mix.inputs[0]);l.new(transparent.outputs[0],mix.inputs[1]);l.new(cloud.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs['Surface']);return m
def gas_giant_mat(name):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;b=n.get('Principled BSDF');tc=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3.2;noise.inputs['Detail'].default_value=8;noise.inputs['Roughness'].default_value=.78;noise.inputs['Distortion'].default_value=.32;scale=n.new('ShaderNodeVectorMath');scale.operation='SCALE';scale.inputs['Scale'].default_value=.16;add=n.new('ShaderNodeVectorMath');add.operation='ADD';wave=n.new('ShaderNodeTexWave');wave.wave_type='BANDS';wave.bands_direction='Z';wave.inputs['Scale'].default_value=10.5;wave.inputs['Distortion'].default_value=5.2;wave.inputs['Detail'].default_value=6;wave.inputs['Detail Scale'].default_value=1.8;ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1]);palette=[(0,.012,.004,.025,1),(.24,.16,.025,.18,1),(.48,.42,.08,.12,1),(.7,.11,.025,.25,1),(.88,.52,.16,.08,1),(1,.04,.008,.07,1)]
 for pos,r,g,bv,a in palette:e=ramp.color_ramp.elements.new(pos) if pos else ramp.color_ramp.elements[0];e.position=pos;e.color=(r,g,bv,a)
 bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.055;l.new(tc.outputs['Generated'],noise.inputs['Vector']);l.new(noise.outputs['Color'],scale.inputs[0]);l.new(tc.outputs['Generated'],add.inputs[0]);l.new(scale.outputs['Vector'],add.inputs[1]);l.new(add.outputs['Vector'],wave.inputs['Vector']);l.new(wave.outputs['Color'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],b.inputs['Base Color']);l.new(ramp.outputs['Color'],b.inputs['Emission Color']);b.inputs['Emission Strength'].default_value=.07;l.new(wave.outputs['Fac'],bump.inputs['Height']);l.new(bump.outputs['Normal'],b.inputs['Normal']);b.inputs['Roughness'].default_value=.48;return m
def ice_world_mat(name):
 m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;b=n.get('Principled BSDF');tc=n.new('ShaderNodeTexCoord');vor=n.new('ShaderNodeTexVoronoi');vor.voronoi_dimensions='3D';vor.feature='DISTANCE_TO_EDGE';vor.inputs['Scale'].default_value=7.5;ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.015;ramp.color_ramp.elements[0].color=(.003,.012,.035,1);ramp.color_ramp.elements[1].position=.095;ramp.color_ramp.elements[1].color=(.38,.72,.9,1);mid=ramp.color_ramp.elements.new(.045);mid.color=(.025,.18,.38,1);bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.42;bump.inputs['Distance'].default_value=.035;l.new(tc.outputs['Generated'],vor.inputs['Vector']);l.new(vor.outputs['Distance'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],b.inputs['Base Color']);l.new(vor.outputs['Distance'],bump.inputs['Height']);l.new(bump.outputs['Normal'],b.inputs['Normal']);b.inputs['Roughness'].default_value=.36;b.inputs['Coat Weight'].default_value=.22;return m
def barren_world_mat(name):
 m=surface_mat(name,(.004,.005,.007),(.035,.028,.024),(.18,.1,.055),11,.88);n=m.node_tree.nodes;l=m.node_tree.links;b=n.get('Principled BSDF');tc=n.get('Texture Coordinate');vor=n.new('ShaderNodeTexVoronoi');vor.distance='EUCLIDEAN';vor.inputs['Scale'].default_value=14;bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.52;bump.inputs['Distance'].default_value=.06;l.new(tc.outputs['Generated'],vor.inputs['Vector']);l.new(vor.outputs['Distance'],bump.inputs['Height']);l.new(bump.outputs['Normal'],b.inputs['Normal']);return m
def sphere(name,p,r,m,seg=64):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=seg//2,radius=r,location=p);o=bpy.context.object;o.name=name;o.data.materials.append(m)
 for f in o.data.polygons:f.use_smooth=True
 return o
def hero_asteroid(name,p,radius,material):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3,radius=radius,location=p);o=bpy.context.object;o.name=name;o.data.materials.append(material);o.scale=(R.uniform(.75,1.45),R.uniform(.65,1.25),R.uniform(.7,1.35));o.rotation_euler=[R.random()*math.tau for _ in range(3)]
 tex=bpy.data.textures.new(name+'_Displacement',type='CLOUDS');tex.noise_scale=radius*.32;tex.noise_depth=2;mod=o.modifiers.new('FracturedSilhouette','DISPLACE');mod.texture=tex;mod.strength=radius*.24;mod.texture_coords='GLOBAL'
 bpy.context.view_layer.objects.active=o;bpy.ops.object.shade_smooth();return o
def cube_volume(name,p,scale,m):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4,radius=1,location=p);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(m);o['cinematic_only']=True;return o
def point_at(o,target):o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()
def filament(name,points,material,width=.018,cyclic=False):
 curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=2;curve.bevel_depth=width;curve.bevel_resolution=2
 spline=curve.splines.new('NURBS');spline.points.add(len(points)-1)
 for p,co in zip(spline.points,points):p.co=(*co,1)
 spline.use_cyclic_u=cyclic
 if len(points)>3:spline.order_u=min(4,len(points));spline.use_endpoint_u=not cyclic
 obj=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(obj);obj.data.materials.append(material);obj['cinematic_only']=True;return obj
def main():
 OUT.mkdir(parents=True,exist_ok=True);clean();s=bpy.context.scene;s.world=bpy.data.worlds.new('Ginnos Deep Space');s.world.use_nodes=True;bg=s.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.00003,.00008,.00035,1);bg.inputs['Strength'].default_value=.012
 star_mats=[simple_mat('M_Starfield_Cool',(.18,.38,1),.24,emit=.42),simple_mat('M_Starfield_White',(.72,.82,1),.2,emit=.55),simple_mat('M_Starfield_Warm',(1,.48,.18),.26,emit=.36)]
 for i in range(700):
  x=R.uniform(-26,26);z=R.uniform(-14,14);y=R.uniform(9,18);sphere(f'Star_{i:04d}',(x,y,z),R.choice([.006,.009,.013,.018,.026]),R.choices(star_mats,weights=(5,7,1))[0],8)
 hero_star_mats=[simple_mat('M_HeroStar_Blue',(.28,.58,1),.14,emit=3.4),simple_mat('M_HeroStar_White',(.9,.94,1),.12,emit=3),simple_mat('M_HeroStar_Gold',(1,.34,.08),.16,emit=2.6)]
 for i in range(22):
  sphere(f'HeroStar_{i:02d}',(R.uniform(-25,25),R.uniform(10,17),R.uniform(-13,13)),R.uniform(.018,.045),R.choices(hero_star_mats,weights=(6,5,1))[0],12)
 # Layered, low-density volumes leave true black space between radiation filaments.
 cube_volume('Nebula_Cobalt',(-5,10,0),(19,2.8,8),volume_mat('M_Nebula_Cobalt',(.005,.06,.42),1.1,.004,.04))
 cube_volume('Nebula_Cyan',(7,11,-2),(12,2.2,5),volume_mat('M_Nebula_Cyan',(.005,.22,.55),1.8,.0025,.05))
 # Offset lobes create broken silhouettes and pockets of true black space.
 cloud_specs=[((-13,8,5),(8,1.8,3.6),(.01,.08,.5),1.5,.007,.07),((-3,9,-5),(11,2.1,2.8),(.005,.18,.65),2.4,.006,.08),((9,10,2),(7,1.6,3.1),(.08,.025,.5),2.0,.004,.055),((16,9,-5),(6,1.4,2.4),(.005,.22,.5),3.1,.006,.075)]
 for i,(p,scale,color,noise_scale,density,emit) in enumerate(cloud_specs):cube_volume(f'NebulaLobe_{i+1:02d}',p,scale,volume_mat(f'M_NebulaLobe_{i+1:02d}',color,noise_scale,density,emit))
 star_mat=surface_mat('M_GinnosStar',(.005,.018,.18),(.025,.18,.72),(.5,.78,1),7.2,.2,.62);star=sphere('Ginnos_Primary',(8,3,5),2.35,star_mat,96);star['system_id']='c6449799-ec65-58df-b772-9aead6c05d5e';star['stellar_class']='BlueWhiteStar'
 corona=sphere('Ginnos_Corona',star.location,2.72,volume_mat('M_GinnosCorona',(.025,.22,1),3.4,.004,.1),64);corona['cinematic_only']=True
 # Localized magnetic arches rise from and reconnect to the photosphere.
 plasma=simple_mat('M_PlasmaArc',(.08,.42,1),.16,emit=2.2)
 for i in range(13):
  center=R.random()*math.tau;span=R.uniform(.28,.82);height=R.uniform(.22,1.15);tilt=R.uniform(-.38,.38);pts=[]
  for j in range(24):
   t=j/23;a=center+(t-.5)*span;rad=2.34+math.sin(t*math.pi)*height;warp=R.uniform(-.018,.018);pts.append((star.location.x+math.cos(a)*(rad+warp),star.location.y+math.sin(t*math.pi)*tilt+R.uniform(-.012,.012),star.location.z+math.sin(a)*(rad+warp)))
  filament(f'PlasmaProminence_{i+1:02d}',pts,plasma,R.uniform(.006,.019))
 ocean=surface_mat('M_Ocean',(.001,.012,.045),(.004,.085,.3),(.02,.42,.78),4,.24);ice=ice_world_mat('M_Ice_Fractured');barren=barren_world_mat('M_Barren_Cratered');gas=gas_giant_mat('M_GasGiant_Banded');atmos=atmosphere_mat('M_AtmosphericLimb',(.015,.22,1),.72);clouds=cloud_mat('M_OceanClouds')
 specs=[('OceanWorld',(-10,1,3.2),1.45,ocean),('IceWorld',(1,3,-5.5),.9,ice),('BarrenWorld',(-5,4,-1.5),.55,barren),('GasGiant',(13,7,-4),1.35,gas)]
 bodies=[]
 for idx,(name,p,radius,m) in enumerate(specs):
  sphere(name+'_Atmosphere',p,radius*1.028,atmos,64)
  if name=='OceanWorld':sphere(name+'_CloudLayer',p,radius*1.014,clouds,72)
  body=sphere(name,p,radius,m,72 if radius>2 else 48);body['body_slot']=idx+1;bodies.append(body)
 # Gas-giant storm, rings, and shepherd moons establish a unique silhouette.
 ring_mat=simple_mat('M_GasRing',(.18,.055,.12),.72,metal=.05,emit=.08);gas_pos=Vector((13,7,-4))
 for i,(major,minor) in enumerate(((1.72,.035),(1.9,.022),(2.13,.045),(2.38,.018))):
  bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=128,minor_segments=8,location=gas_pos,rotation=(.36,.12,.28));ring=bpy.context.object;ring.name=f'GasGiant_Ring_{i+1:02d}';ring.data.materials.append(ring_mat)
 storm_mat=surface_mat('M_GasStorm',(.09,.008,.005),(.5,.08,.018),(.95,.36,.08),5.5,.58,emit=.08);storm=sphere('GasGiant_GreatStorm',(12.62,5.72,-3.72),.42,storm_mat,48);storm.scale=(1.35,.12,.58);storm.rotation_euler=(.08,.2,-.22)
 moon_mat=surface_mat('M_ShepherdMoon',(.012,.014,.018),(.08,.075,.07),(.24,.2,.17),9,.82)
 sphere('GasGiant_ShepherdMoon_A',(15.35,7.1,-3.45),.16,moon_mat,32);sphere('GasGiant_ShepherdMoon_B',(10.82,6.7,-4.62),.11,moon_mat,32)
 # A broad diagonal debris river provides scale and navigational hazard.
 rock=surface_mat('M_Debris',(.006,.008,.012),(.028,.038,.055),(.11,.14,.18),7.5,.86)
 for i in range(260):
  t=R.random();p=Vector((-24+t*48,R.uniform(-.5,5),-10+t*14+math.sin(t*math.tau*2)*1.8+R.gauss(0,.65)));o=sphere(f'Debris_{i:03d}',p,R.uniform(.025,.16)*(2 if i<20 else 1),rock,10);o.scale=(R.uniform(.55,1.8),R.uniform(.55,1.4),R.uniform(.55,1.6));o.rotation_euler=[R.random()*math.tau for _ in range(3)]
 # Large anchors interrupt the particle-like rhythm and establish foreground scale.
 for i,t in enumerate((.18,.31,.43,.56,.67,.78,.88)):
  p=(-24+t*48,R.uniform(-.2,3.2),-10+t*14+math.sin(t*math.tau*2)*1.8+R.uniform(-.45,.45));hero_asteroid(f'HeroAsteroid_{i+1:02d}',p,R.uniform(.32,.68),rock)
 dust=simple_mat('M_IonizedDust',(.025,.16,.48),.55,emit=.35)
 for i in range(150):
  t=R.random();p=(-24+t*48,R.uniform(1.5,7),-10+t*14+R.gauss(0,1.15));sphere(f'Dust_{i:03d}',p,R.uniform(.004,.014),dust,6)
 for name,p,role in [('ArrivalAnchor',(-16,-1,-7),'player_arrival'),('JumpExitAnchor',(-19,-1,-9),'jump_exit'),('ResourceAnchor',(4,0,-4),'resource'),('HazardAnchor',(0,0,0),'radiation_hazard')]:o=bpy.data.objects.new(name,None);o.location=p;o.empty_display_type='SPHERE';o.empty_display_size=.45;o['gameplay_role']=role;bpy.context.collection.objects.link(o)
 bpy.ops.object.light_add(type='AREA',location=(7,-5,8));key=bpy.context.object;key.name='Stellar_Key';key.data.energy=2300;key.data.color=(.22,.52,1);key.data.size=10;point_at(key,(0,0,0));bpy.ops.object.light_add(type='AREA',location=(-14,-8,7));fill=bpy.context.object;fill.name='Planet_Fill';fill.data.energy=650;fill.data.color=(.03,.12,.35);fill.data.size=12;point_at(fill,(-8,0,3))
 bpy.ops.object.light_add(type='POINT',location=star.location);stellar_light=bpy.context.object;stellar_light.name='Ginnos_StellarRadiance';stellar_light.data.energy=850;stellar_light.data.color=(.18,.42,1);stellar_light.data.shadow_soft_size=2.1
 bpy.ops.object.light_add(type='AREA',location=(10,-6,-2));rim=bpy.context.object;rim.name='Debris_Rim';rim.data.energy=1050;rim.data.color=(.04,.22,1);rim.data.size=8;point_at(rim,(6,2,-1))
 bpy.ops.object.camera_add(location=(0,-38,2.5));cam=bpy.context.object;cam.name='Camera_Ginnos_Hero';cam.data.lens=58;cam.data.sensor_width=36;point_at(cam,(2.6,2,1.4));s.camera=cam
 s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1920;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(PREVIEW);s.render.film_transparent=False;s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-.72;s['system_id']='c6449799-ec65-58df-b772-9aead6c05d5e';s['system_seed']=SEED;s['concept_reference_only']='docs/concept-art/reference/space/blue-white-radiation-system.png';s['uses_concept_backplate']=False;bpy.context.preferences.filepaths.save_version=0
 # Soft bloom without destroying stellar-surface detail.
 s.use_nodes=True;tree=getattr(s,'node_tree',None);modern=tree is None
 if modern:
  tree=bpy.data.node_groups.new('GinnosCompositor','CompositorNodeTree');s.compositing_node_group=tree
 n=tree.nodes;l=tree.links;n.clear();rl=n.new('CompositorNodeRLayers');glare=n.new('CompositorNodeGlare')
 if 'Threshold' in glare.inputs:glare.inputs['Threshold'].default_value=1.1
 if 'Size' in glare.inputs:glare.inputs['Size'].default_value=.7
 l.new(rl.outputs['Image'],glare.inputs['Image'])
 if modern:
  tree.interface.new_socket(name='Image',in_out='OUTPUT',socket_type='NodeSocketColor');comp=n.new('NodeGroupOutput');l.new(glare.outputs['Image'],comp.inputs['Image'])
 else:
  comp=n.new('CompositorNodeComposite');l.new(glare.outputs['Image'],comp.inputs['Image'])
 bpy.ops.wm.save_as_mainfile(filepath=str(BLEND));bpy.ops.render.render(write_still=True);bpy.ops.object.select_all(action='DESELECT')
 for o in s.objects:
  if o.type=='MESH' and not o.get('cinematic_only') and not o.name.startswith('Star_'):o.select_set(True)
 bpy.ops.export_scene.gltf(filepath=str(GLB),export_format='GLB',use_selection=True,export_materials='EXPORT',export_animations=False);report={'schema_version':2,'system_id':s['system_id'],'system_seed':SEED,'quality_status':'art_direction_prototype','uses_concept_backplate':False,'bodies':[o.name for o in bodies],'debris':260,'hero_asteroids':7,'ionized_dust':150,'starfield':700,'hero_stars':22,'landmarks':[],'gameplay_anchors':['ArrivalAnchor','JumpExitAnchor','ResourceAnchor','HazardAnchor'],'blend':str(BLEND.relative_to(ROOT)).replace('\\','/'),'glb':str(GLB.relative_to(ROOT)).replace('\\','/'),'preview':str(PREVIEW.relative_to(ROOT)).replace('\\','/')};REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
main()
