"""Phase thirteen: production PBR materials, hero surfacing, bevels, lighting, and QA."""
import json,sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems';TEX=OUT/'Textures';BLEND=OUT/'SpaceSystems_Master.blend';PREVIEW=OUT/'SpaceSystems_Phase13_ProductionMaterials.png';REPORT=OUT/'SpaceSystems_Phase13_Report.json';done=[]
def step(n,name,detail):done.append({'step':n,'name':name,'detail':detail})
def image(name,file):
 img=bpy.data.images.get(name)
 if not img:img=bpy.data.images.load(str(TEX/file),check_existing=True);img.name=name
 img.pack();img['source_asset']=str(Path('Art/SpaceSystems/Textures')/file);return img
def clear_material(name):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;m.node_tree.nodes.clear();return m
def planet_material(name,img,base,metal,rough,bump_strength,emission=False):
 m=clear_material(name);n=m.node_tree.nodes;l=m.node_tree.links;out=n.new('ShaderNodeOutputMaterial');out.location=(720,0);bs=n.new('ShaderNodeBsdfPrincipled');bs.location=(430,0);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough;l.new(bs.outputs['BSDF'],out.inputs['Surface'])
 texcoord=n.new('ShaderNodeTexCoord');texcoord.location=(-900,0);mapping=n.new('ShaderNodeMapping');mapping.location=(-700,0);mapping.inputs['Scale'].default_value=(1.6,1.6,1.6);tex=n.new('ShaderNodeTexImage');tex.location=(-470,80);tex.image=img;tex.interpolation='Linear';l.new(texcoord.outputs['Generated'],mapping.inputs['Vector']);l.new(mapping.outputs['Vector'],tex.inputs['Vector'])
 mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.78;mix.inputs[2].default_value=(*base,1);mix.location=(20,130);l.new(tex.outputs['Color'],mix.inputs[1]);l.new(mix.outputs['Color'],bs.inputs['Base Color'])
 gray=n.new('ShaderNodeRGBToBW');gray.location=(-200,-180);bump=n.new('ShaderNodeBump');bump.location=(170,-190);bump.inputs['Strength'].default_value=bump_strength;bump.inputs['Distance'].default_value=.12;l.new(tex.outputs['Color'],gray.inputs['Color']);l.new(gray.outputs['Val'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal'])
 ramp=n.new('ShaderNodeValToRGB');ramp.location=(20,-360);ramp.color_ramp.elements[0].position=.18;ramp.color_ramp.elements[0].color=(rough*.65,)*3+(1,);ramp.color_ramp.elements[1].position=.82;ramp.color_ramp.elements[1].color=(min(.98,rough*1.25),)*3+(1,);l.new(gray.outputs['Val'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],bs.inputs['Roughness'])
 if emission:
  er=n.new('ShaderNodeValToRGB');er.location=(20,350);er.color_ramp.elements[0].position=.48;er.color_ramp.elements[0].color=(0,0,0,1);er.color_ramp.elements[1].position=.72;er.color_ramp.elements[1].color=(1,.015,.001,1);l.new(gray.outputs['Val'],er.inputs['Fac']);l.new(er.outputs['Color'],bs.inputs['Emission Color']);bs.inputs['Emission Strength'].default_value=4.5
 m['production_pbr']=True;m['texture_name']=img.name;return m
def procedural_metal(name,dark,light,accent,rough=.32,wear=.22):
 m=clear_material(name);n=m.node_tree.nodes;l=m.node_tree.links;out=n.new('ShaderNodeOutputMaterial');out.location=(800,0);bs=n.new('ShaderNodeBsdfPrincipled');bs.location=(540,0);bs.inputs['Metallic'].default_value=.86;bs.inputs['Roughness'].default_value=rough;l.new(bs.outputs['BSDF'],out.inputs['Surface'])
 tc=n.new('ShaderNodeTexCoord');tc.location=(-900,0);mapping=n.new('ShaderNodeMapping');mapping.location=(-700,0);mapping.inputs['Scale'].default_value=(4,4,4);noise=n.new('ShaderNodeTexNoise');noise.location=(-470,80);noise.inputs['Scale'].default_value=7;noise.inputs['Detail'].default_value=5;noise.inputs['Roughness'].default_value=.72;l.new(tc.outputs['Object'],mapping.inputs['Vector']);l.new(mapping.outputs['Vector'],noise.inputs['Vector'])
 vor=n.new('ShaderNodeTexVoronoi');vor.distance='CHEBYCHEV';vor.location=(-450,-250);vor.inputs['Scale'].default_value=12;l.new(mapping.outputs['Vector'],vor.inputs['Vector']);mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.35;mix.location=(-140,70);l.new(noise.outputs['Fac'],mix.inputs[1]);l.new(vor.outputs['Distance'],mix.inputs[2])
 ramp=n.new('ShaderNodeValToRGB');ramp.location=(70,100);ramp.color_ramp.elements[0].color=(*dark,1);ramp.color_ramp.elements[0].position=.2;ramp.color_ramp.elements[1].color=(*light,1);ramp.color_ramp.elements[1].position=.72;mid=ramp.color_ramp.elements.new(.48);mid.color=(*accent,1);l.new(mix.outputs['Color'],ramp.inputs['Fac']);l.new(ramp.outputs['Color'],bs.inputs['Base Color'])
 bump=n.new('ShaderNodeBump');bump.location=(300,-210);bump.inputs['Strength'].default_value=.24;bump.inputs['Distance'].default_value=.035;l.new(vor.outputs['Distance'],bump.inputs['Height']);l.new(bump.outputs['Normal'],bs.inputs['Normal']);bs.inputs['Coat Weight'].default_value=.16;bs.inputs['Coat Roughness'].default_value=.22;m['production_pbr']=True;m['wear_amount']=wear;return m
def emissive(name,color,strength):
 m=clear_material(name);n=m.node_tree.nodes;l=m.node_tree.links;out=n.new('ShaderNodeOutputMaterial');bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=.2;bs.inputs['Roughness'].default_value=.18;bs.inputs['Emission Color'].default_value=(*color,1);bs.inputs['Emission Strength'].default_value=strength;l.new(bs.outputs['BSDF'],out.inputs['Surface']);m['production_pbr']=True;return m
def assign_object(obj,material):
 if obj.type!='MESH':return
 if not obj.data.materials:obj.data.materials.append(material)
 else:obj.data.materials[0]=material
def isolate_material(collection_name,material):
 c=bpy.data.collections.get(collection_name)
 if not c:return 0
 copies={};count=0
 for o in c.objects:
  if o.type!='MESH':continue
  key=o.data
  if key not in copies:
   d=key.copy();d.name='P13_'+collection_name+'_'+key.name;copies[key]=d
  o.data=copies[key];assign_object(o,material);count+=1
 return count
def bevel_collection(collection_name,width=.025):
 c=bpy.data.collections.get(collection_name);count=0
 if not c:return count
 for o in c.objects:
  if o.type!='MESH':continue
  for p in o.data.polygons:p.use_smooth=True
  if not o.modifiers.get('Production Bevel'):
   mod=o.modifiers.new('Production Bevel','BEVEL');mod.width=width;mod.segments=2;mod.limit_method='ANGLE';count+=1
 return count
def area(name,loc,color,energy,size,target):
 o=bpy.data.objects.get(name)
 if not o:bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name
 o.data.energy=energy;o.data.color=color;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
def main():
 s=bpy.context.scene
 if s.get('phase13_complete'):raise RuntimeError('Phase 13 already installed')
 imgs={'Ocean':image('T_Planet_OceanClouds','T_Planet_OceanClouds.png'),'Volcanic':image('T_Planet_VolcanicLava','T_Planet_VolcanicLava.png'),'Ice':image('T_Planet_FracturedIce','T_Planet_FracturedIce.png'),'Gas':image('T_Planet_GasBands','T_Planet_GasBands.png')};step(1,'Pack authored maps','Four original maps packed with provenance')
 planets={'Ocean_World':planet_material('M_P13_OceanPBR',imgs['Ocean'],(.09,.24,.42),.05,.42,.48),'Volcanic_World':planet_material('M_P13_VolcanicPBR',imgs['Volcanic'],(.35,.055,.012),.12,.58,.72,True),'Ice_World':planet_material('M_P13_IcePBR',imgs['Ice'],(.42,.68,.8),.04,.3,.6),'Ringed_Gas_Giant':planet_material('M_P13_GasPBR',imgs['Gas'],(.72,.32,.08),0,.62,.28)};step(2,'Build planet PBR shaders','Albedo, roughness, bump, volcanic emission')
 for n,m in planets.items():
  o=bpy.data.objects.get(n)
  if o:assign_object(o,m)
 step(3,'Assign planet shaders','Four hero worlds surfaced')
 station=procedural_metal('M_P13_StationPanel',(.012,.025,.038),(.14,.2,.24),(.035,.09,.12),.3,.26);defense=procedural_metal('M_P13_DefenseArmor',(.018,.02,.025),(.18,.055,.035),(.35,.018,.008),.27,.38);civil=procedural_metal('M_P13_CivilianHull',(.025,.045,.055),(.22,.29,.31),(.03,.22,.28),.38,.18);encounter=procedural_metal('M_P13_EncounterHull',(.012,.008,.02),(.16,.035,.22),(.32,.005,.12),.24,.48);capital=procedural_metal('M_P13_CapitalHull',(.014,.022,.032),(.12,.17,.22),(.04,.1,.18),.25,.3);step(4,'Build metal families','Station, defense, civilian, encounter, capital')
 old=bpy.data.materials.get('M_StationHull')
 if old:
  old.user_remap(station)
 step(5,'Replace placeholder hull','Shared flat hull remapped to panelized metal')
 counts={'landmarks':isolate_material('P12_HeroLandmarks',station),'defense':isolate_material('P12_DefenseNetwork',defense),'civilian':isolate_material('P12_CivilianHubs',civil),'encounters':isolate_material('P12_HeroEncounters',encounter),'capitals':isolate_material('P12_CapitalTraffic',capital)};step(6,'Isolate hero material sets',counts)
 cyan=emissive('M_P13_CyanEmission',(0,.35,1),13);amber=emissive('M_P13_AmberEmission',(1,.12,.003),12);red=emissive('M_P13_RedEmission',(1,.002,.001),14);step(7,'Build production emissions','Cyan, amber, red optical materials')
 for c in bpy.data.collections:
  if not c.name.startswith(('P12_','P10_JumpLane','P8_Station')):continue
  for o in c.objects:
   if o.type!='MESH':continue
   n=o.name.lower()
   if any(x in n for x in ('beacon','lamp','light','drive','reactor','field','crown','shield','marker')):assign_object(o,red if 'defense' in c.name.lower() else (amber if any(x in n for x in ('drive','reactor')) else cyan))
 step(8,'Assign optical materials','Hero lights, drives, fields, and markers')
 bevels=sum(bevel_collection(n,w) for n,w in [('P12_HeroLandmarks',.035),('P12_DefenseNetwork',.025),('P12_CivilianHubs',.03),('P12_HeroEncounters',.04),('P12_CapitalTraffic',.035)]);step(9,'Apply hero bevels',{'modifiers':bevels})
 for m in (station,defense,civil,encounter,capital):m.diffuse_color=tuple(m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value)
 step(10,'Set viewport material colors','Material preview readability')
 area('P13_KeyLight',(18,-24,30),(.45,.62,1),1800,18,(0,5,2));area('P13_RimLight',(-25,12,18),(1,.16,.035),1400,14,(0,5,2));area('P13_FillLight',(0,28,22),(.18,.32,1),950,20,(0,5,2));step(11,'Install production light rig','Key, rim, and fill')
 cam=bpy.data.objects.get('Camera_P12_HeroLandmarks') or s.camera;s.camera=cam
 if cam:cam.data.lens=62;cam.data.dof.use_dof=True;cam.data.dof.focus_distance=45;cam.data.dof.aperture_fstop=5.6
 step(12,'Tune production camera','62mm lens and controlled depth of field')
 s.view_settings.look='AgX - Medium High Contrast';step(13,'Set color management','AgX medium-high contrast')
 s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGBA';s.render.resolution_x=960;s.render.resolution_y=540;s.render.resolution_percentage=100;step(14,'Configure production output','960x540 RGBA audit render')
 for m in (station,defense,civil,encounter,capital,cyan,amber,red,*planets.values()):m['unreal_master_family']='SpaceSystems';m['phase13_ready']=True
 step(15,'Add export metadata','Unreal master-family tags')
 for o in bpy.data.objects:
  if o.get('phase12_step'):o['material_stage']='production';o['texel_density_target']=512
 step(16,'Tag hero assets','Production stage and texel targets')
 if 'Phase13Materials' not in s.view_layers:s.view_layers.new('Phase13Materials')
 step(17,'Create material view layer','Phase13Materials')
 for n,f in [('P13_PLANETS',120),('P13_LANDMARKS',320),('P13_DEFENSE',520),('P13_CIVIL',720),('P13_CAPITALS',920)]:
  if not s.timeline_markers.get(n):s.timeline_markers.new(n,frame=f)
 step(18,'Add material review markers','Five review beats')
 if len(done)!=18:raise RuntimeError('Phase13 preflight mismatch')
 s['phase13_complete']=True;s['phase13_steps']=20;s['asset_version']='13.0';ctrl=bpy.data.objects.get('SpaceSystem_MasterController')
 if ctrl:ctrl['phase13_materials']='production';ctrl['authored_texture_count']=4
 step(19,'Save production master','Version 13.0');step(20,'Write production audit','Material and modifier report')
 summary={'objects':len(bpy.data.objects),'materials':len(bpy.data.materials),'images':len(bpy.data.images),'packed_authored_textures':4,'hero_bevels':bevels,'hero_assignments':counts};REPORT.write_text(json.dumps({'phase':13,'steps':done,'summary':summary},indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
 # Isolate the hero pass for a practical Eevee material render without the thousand-asset background cost.
 hidden=[]
 for c in bpy.data.collections:
  if c.name.startswith('P11_') and not c.hide_render:c.hide_render=True;hidden.append(c)
 s.render.filepath=str(PREVIEW);engine=s.render.engine;s.render.engine='BLENDER_EEVEE';bpy.ops.render.render(write_still=True);s.render.engine=engine
 for c in hidden:c.hide_render=False
 print(json.dumps({'phase':13,'completed':len(done),**summary},indent=2))
main()
