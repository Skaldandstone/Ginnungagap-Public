"""Phase 27: high-detail material, atmosphere, silhouette, and composition pass."""
import json, math, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems'
LEVEL=OUT/'SpaceSystems_PelagosOrbitalArrival_Level.blend';PREVIEW=OUT/'SpaceSystems_PelagosOrbitalArrival_AAA.png';REPORT=OUT/'SpaceSystems_AAA_Polish_Report.json'
def col(n):
 c=bpy.data.collections.get(n) or bpy.data.collections.new(n)
 if c.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(c)
 return c
def move(o,c):
 for q in list(o.users_collection):q.objects.unlink(o)
 c.objects.link(o);return o
def shader(name,base,metal,rough,accent=None):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');p=n.new('ShaderNodeBsdfPrincipled');p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=7;noise.inputs['Detail'].default_value=5;noise.inputs['Roughness'].default_value=.72
 ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*tuple(v*.45 for v in base),1);ramp.color_ramp.elements[1].color=(*base,1)
 m.node_tree.links.new(noise.outputs['Fac'],ramp.inputs['Fac']);m.node_tree.links.new(ramp.outputs['Color'],p.inputs['Base Color']);m.node_tree.links.new(p.outputs[0],out.inputs[0]);return m
def emissive(name,color,power):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=power;p.inputs['Roughness'].default_value=.25;return m
def finish(o,n,m,c,bevel=.04):
 o.name=n;o.data.materials.append(m)
 if bevel:b=o.modifiers.new('Micro bevel','BEVEL');b.width=bevel;b.segments=3
 for p in o.data.polygons:p.use_smooth=True
 return move(o,c)
def cube(n,p,sc,m,c,rot=(0,0,0),bevel=.04):
 bpy.ops.mesh.primitive_cube_add(location=p,rotation=rot);o=bpy.context.object;o.scale=sc;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,n,m,c,bevel)
def cyl(n,a,b,r,m,c,verts=32):
 a,b=Vector(a),Vector(b);v=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=v.length,location=(a+b)/2);o=bpy.context.object;o.rotation_mode='QUATERNION';o.rotation_quaternion=v.to_track_quat('Z','Y');return finish(o,n,m,c,r*.15)
def atmosphere_material():
 m=bpy.data.materials.get('AAA_Atmosphere') or bpy.data.materials.new('AAA_Atmosphere');m.use_nodes=True;n=m.node_tree.nodes;n.clear();out=n.new('ShaderNodeOutputMaterial');mix=n.new('ShaderNodeMixShader');trans=n.new('ShaderNodeBsdfTransparent');emit=n.new('ShaderNodeEmission');emit.inputs['Color'].default_value=(.004,.035,.22,1);emit.inputs['Strength'].default_value=.65;layer=n.new('ShaderNodeLayerWeight');layer.inputs['Blend'].default_value=.18;ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.06;ramp.color_ramp.elements[1].position=.32
 m.node_tree.links.new(layer.outputs['Facing'],ramp.inputs[0]);m.node_tree.links.new(ramp.outputs[0],mix.inputs[0]);m.node_tree.links.new(trans.outputs[0],mix.inputs[1]);m.node_tree.links.new(emit.outputs[0],mix.inputs[2]);m.node_tree.links.new(mix.outputs[0],out.inputs[0]);m.surface_render_method='DITHERED';return m
def main():
 s=bpy.context.scene
 if s.get('aaa_polish_version')=='27.1':raise RuntimeError('AAA polish already installed')
 old=bpy.data.collections.get('AAA_POLISH_27')
 if old:
  for o in list(old.all_objects):bpy.data.objects.remove(o,do_unlink=True)
  bpy.data.collections.remove(old)
 c=col('AAA_POLISH_27')
 # Remove every remaining prototype/readability artifact from the beauty camera.
 noise_terms=('DockGuide','PlayerShip','Traffic_','P20_','EnvironmentCue','DistantMarker','DebrisArc','CityLight','OrbitalEquator','CloudArc','NavMarker','InboundBuoy','Mission_','ServiceProp','DockStatus','CargoPallet')
 hidden=0
 for o in bpy.data.objects:
  if any(t in o.name for t in noise_terms):o.hide_render=True;hidden+=1
 orphan=bpy.data.objects.get('Cube')
 if orphan:orphan.hide_render=True;hidden+=1
 stars=bpy.data.collections.get('ARTISTPASS_Stars')
 if stars:
  for i,o in enumerate(stars.objects):o.hide_render=(i%3!=0)
 # Authored hull response: subtle large-scale coating breakup, never noisy procedural camouflage.
 hull=shader('AAA_HullCoating',(.035,.055,.085),.88,.26);ceramic=shader('AAA_ThermalCeramic',(.34,.39,.42),.3,.32);dark=shader('AAA_Radiator',(.004,.009,.017),.72,.18);cyan=emissive('AAA_ServiceCyan',(.01,.28,1),7);amber=emissive('AAA_WarningAmber',(1,.09,.008),10)
 hero=bpy.data.collections.get('ARTISTPASS_HeroStation')
 if hero:
  for o in hero.objects:
   if not o.data or not hasattr(o.data,'materials'):continue
   if 'Light' in o.name or 'Beacon' in o.name:continue
   o.data.materials.clear();o.data.materials.append(dark if 'Array' in o.name else (ceramic if any(k in o.name for k in ('Collar','HabPod','Spoke')) else hull))
 # Fine panel seams on the main pressure hull establish human scale.
 for i in range(22):
  x=-4.65+i*.53;cube(f'AAA_HullSeam_{i:02d}',(x,.02,3),( .012,.018,1.5),dark,c,(0,0,0),.006)
 # Window strips, service hatches and warning marks: controlled repetition with clear function.
 for side in (-1,1):
  y=2+side*2.06
  for i in range(14):
   x=-4.3+i*.68;cube(f'AAA_Window_{side}_{i:02d}',(x,y,3.32),(.2,.025,.075),cyan,c,bevel=.018)
  for i in range(5):
   x=-3.8+i*2.15;cube(f'AAA_ServiceHatch_{side}_{i}',(x,y,2.35),(.52,.035,.34),ceramic,c,bevel=.07)
 # Structural truss pairs and cable conduits around docking spine.
 for i,z in enumerate((-1.2,1.5,4.2,6.9)):
  cyl(f'AAA_DockBraceA_{i}',(-1.5,-4.8,z),(-.4,-8.5,z+.72),.09,ceramic,c)
  cyl(f'AAA_DockBraceB_{i}',(-1.5,-4.8,z),(-2.6,-8.5,z-.72),.09,ceramic,c)
  for j in range(6):
   cube(f'AAA_DockMark_{i}_{j}',(-1.5,-8.9+j*.1,z-0.58+j*.2),(.035,.12,.045),amber if i==2 else cyan,c,bevel=.01)
 # Communications whiskers and sensor clusters break perfect primitive symmetry.
 for i in range(7):
  x=-2.8+i*1.35;cyl(f'AAA_SensorMast_{i}',(x,2,5.0),(x,2,5.45+(i%3)*.22),.035,ceramic,c,16)
  bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=10,radius=.1+(i%2)*.025,location=(x,2,5.52+(i%3)*.22));finish(bpy.context.object,f'AAA_SensorHead_{i}',cyan if i in (1,5) else ceramic,c,0)
 # Planet atmosphere shell derived from actual planet mesh, retaining the authored globe.
 planet=bpy.data.objects.get('OceanArrival_Planet')
 if planet:
  at=planet.copy();at.data=planet.data.copy();at.name='AAA_PelagosAtmosphere';at.scale=planet.scale*1.012;at.data.materials.clear();at.data.materials.append(atmosphere_material());c.objects.link(at)
 # Dedicated sunlight gives Pelagos a readable terminator and the station a motivated key.
 data=bpy.data.lights.new('AAA_PelagosSun','SUN');data.energy=3.2;data.color=(1,.48,.2);data.angle=math.radians(4);sun=bpy.data.objects.new('AAA_PelagosSun',data);c.objects.link(sun);sun.rotation_euler=(math.radians(28),math.radians(-32),math.radians(-38))
 cam=bpy.data.objects.get('Camera_PelagosArtistHero');cam.location=(-34,-42,15);cam.data.lens=58;cam.data.shift_x=.10;cam.rotation_euler=(Vector((1.5,8,3.8))-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
 s.render.filepath=str(PREVIEW);s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.view_settings.look='AgX - Medium High Contrast'
 s['aaa_polish_version']='27.1';s['quality_target']='AAA environment hero asset'
 report={'phase':27,'version':'27.1','detail_meshes':len(c.objects),'legacy_objects_hidden':hidden,'visible_stars':sum(not o.hide_render for o in stars.objects) if stars else 0,'features':['coating variation','hull seams','window strips','service hatches','dock bracing','warning marks','sensor clusters','atmosphere limb','motivated sunlight'],'gameplay_preserved':True}
 REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(LEVEL));bpy.ops.render.render(write_still=True);print(json.dumps(report,indent=2))
main()
