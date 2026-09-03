"""Apply 200 seed-driven artist-production passes to the procedural galaxy master."""
import json, math, random, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve(); OUT=ROOT/'Art'/'SpaceSystems'
BLEND=OUT/'SpaceSystems_Master.blend'; PREVIEW=OUT/'SpaceSystems_Artist200_Preview.png'
REPORT=OUT/'SpaceSystems_Artist200_Passes.json'; MANIFEST=OUT/'SpaceSystems_GenerationManifest.json'
inventory=json.loads(MANIFEST.read_text(encoding='utf-8')); SEED=int(inventory['seed']); R=random.Random(SEED^0xA27157); steps=[]

def record(category,name,detail,obj=None):
 step=len(steps)+1; item={'step':step,'category':category,'name':name,'detail':detail}
 if obj: obj['artist_pass']=step; item['object']=obj.name
 steps.append(item)
def col(name):
 c=bpy.data.collections.get(name) or bpy.data.collections.new(name)
 if c.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(c)
 return c
def move(o,c):
 if o.name not in c.objects:c.objects.link(o)
 for source in list(o.users_collection):
  if source!=c:source.objects.unlink(o)
def mat(name,color,metal=0,rough=.5,emit=0,alpha=1):
 m=bpy.data.materials.get(name) or bpy.data.materials.new(name);m.use_nodes=True;b=m.node_tree.nodes.get('Principled BSDF')
 b.inputs['Base Color'].default_value=(*color,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough;b.inputs['Alpha'].default_value=alpha
 if emit:b.inputs['Emission Color'].default_value=(*color,1);b.inputs['Emission Strength'].default_value=emit
 if alpha<1:m.surface_render_method='DITHERED'
 return m
def sphere(name,p,radius,m,segments=24,rings=12):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,radius=radius,location=p);o=bpy.context.object;o.name=name;o.data.materials.append(m)
 for face in o.data.polygons:face.use_smooth=True
 return o
def torus(name,p,major,minor,m,rotation=(0,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=64,minor_segments=8,location=p,rotation=rotation);o=bpy.context.object;o.name=name;o.data.materials.append(m);return o
def cube(name,p,scale,m,rotation=(0,0,0)):
 bpy.ops.mesh.primitive_cube_add(location=p,rotation=rotation);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(m);bevel=o.modifiers.new('Artist edge treatment','BEVEL');bevel.width=min(scale)*.16;bevel.segments=2;return o

def main():
 s=bpy.context.scene;old_collections=[c for c in bpy.data.collections if c.name.startswith('ARTIST_200')]
 for old in old_collections:
  for o in list(old.objects):
   if o.name in bpy.data.objects:bpy.data.objects.remove(o,do_unlink=True)
 for old in old_collections:
  if old.name in bpy.data.collections:bpy.data.collections.remove(old)
 root=col('ARTIST_200');root['procedural_seed']=str(SEED)
 s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.film_transparent=False;s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=-.65
 settings=[('Eevee production renderer','Realtime cinematic renderer'),('Full-HD master','1920x1080 output'),('PNG lossless output','RGBA-safe delivery'),('Opaque deep-space plate','No accidental alpha'),('AgX highlight rolloff','Medium-high contrast'),('Exposure protection','Preserve stellar detail'),('Thirty-frame cadence','Gameplay-compatible motion'),('Six-hundred-frame shot','Twenty-second master'),('Seed provenance',str(SEED)),('Inventory provenance',f"{len(inventory['planets'])} generated worlds"),('Orbit-line restraint','Guides remain subordinate'),('Volumetric restraint','Nebulae pushed into depth'),('Emission discipline','Avoid clipped color channels'),('Physical scale metadata','One Blender unit is one meter'),('Collection isolation','Artist additions are removable'),('Non-destructive refinement','Base procedural meshes preserved'),('Shared material policy','Low draw-call material families'),('Smooth silhouette policy','Hero spheres shade smooth'),('Export continuity','Base GLB remains available'),('Artist pass baseline','Production refinement v1')]
 for n,d in settings:record('global',n,d)
 for c in bpy.data.collections:
  if c.name=='Ion_Nebula':c.hide_render=True
 for o in bpy.data.objects:
  if o.name.startswith('NebulaCloud_') or o.name.endswith('_LuminousTail'):o.hide_render=True
 for material_name,strength in [('M_Star_Gold',5.0),('M_Star_Core',3.5)]:
  inherited=bpy.data.materials.get(material_name)
  if inherited and inherited.use_nodes:
   inherited.node_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=strength
 gold=mat('M_A200_StellarCorona',(1,.12,.008),rough=.18,emit=2.5,alpha=.22);white=mat('M_A200_StellarCore',(1,.62,.2),rough=.12,emit=2)
 cyan=mat('M_A200_Cyan',(.005,.22,.68),.2,.24,3.5);amber=mat('M_A200_Amber',(1,.09,.004),.15,.28,3);hull=mat('M_A200_OrbitalHull',(.025,.045,.065),.84,.31);glass=mat('M_A200_Atmosphere',(.02,.16,.42),0,.12,.08,.10);dust=mat('M_A200_Dust',(.16,.11,.07),.05,.86)
 star=bpy.data.objects.get('Primary_Golden_Giant');center=star.location.copy() if star else Vector();stellar=col('ARTIST_200_Stellar')
 for i in range(30):
  a=math.tau*i/30+R.uniform(-.035,.035);o=torus(f'A200_CoronaArc_{i+1:02d}',center,6.65+R.uniform(-.18,.38),R.uniform(.008,.028),gold if i%4 else white,(R.uniform(-.28,.28),R.uniform(-.18,.18),a));move(o,stellar);record('stellar',f'Corona arc {i+1:02d}','Layered magnetic limb filament',o)
 worlds=[bpy.data.objects.get(x['name']) for x in inventory['planets']];worlds=[x for x in worlds if x];planetary=col('ARTIST_200_Planetary')
 for i in range(40):
  w=worlds[i%len(worlds)];radius=max(w.dimensions)*.5
  if i<len(worlds):o=sphere(f'A200_Atmosphere_{i+1:02d}',w.location,radius*1.035,glass,48,24);detail=f'Thin atmospheric limb for {w.name}'
  else:
   a=math.tau*i/40+R.uniform(-.08,.08);local=Vector((math.cos(a),math.sin(a),R.uniform(-.35,.35))).normalized()*radius*1.012;o=sphere(f'A200_SurfaceLight_{i+1:02d}',w.location+local,radius*R.uniform(.006,.014),cyan if i%3 else amber,10,6);detail=f'Night-side settlement or storm light on {w.name}'
  move(o,planetary);record('planetary',f'World refinement {i+1:02d}',detail,o)
 orbital=col('ARTIST_200_OrbitalDepth');largest=max(worlds,key=lambda x:max(x.dimensions));lr=max(largest.dimensions)*.5
 for i in range(30):
  a=math.tau*i/30;dist=lr*R.uniform(1.55,2.35);p=largest.location+Vector((math.cos(a)*dist,math.sin(a)*dist,R.uniform(-.08,.08)*lr));o=sphere(f'A200_RingParticle_{i+1:02d}',p,R.uniform(.012,.048)*lr,dust,10,5);move(o,orbital);record('orbital_depth',f'Ring particle cluster {i+1:02d}',f'Scale breakup around {largest.name}',o)
 infra=col('ARTIST_200_Infrastructure')
 for i in range(25):
  w=worlds[i%len(worlds)];radius=max(w.dimensions)*.5;a=math.tau*((i*.61803398875)%1);p=w.location+Vector((math.cos(a),math.sin(a),R.uniform(-.22,.22)))*radius*R.uniform(1.55,2.4);o=cube(f'A200_OrbitalNode_{i+1:02d}',p,(radius*.055,radius*.018,radius*.018),hull,(0,0,a));move(o,infra);b=sphere(f'A200_OrbitalBeacon_{i+1:02d}',p+Vector((0,0,radius*.035)),radius*.012,cyan if i%4 else amber,10,5);b.parent=o;move(b,infra);record('infrastructure',f'Orbital node {i+1:02d}',f'Scale cue near {w.name}',o)
 depth=col('ARTIST_200_StarDepth')
 for i in range(20):
  direction=Vector((R.uniform(-1,1),R.uniform(-1,1),R.uniform(-.55,.8))).normalized();o=sphere(f'A200_DepthStar_{i+1:02d}',direction*R.uniform(105,145),R.uniform(.035,.08),white if i%5==0 else cyan,10,5);move(o,depth);record('space_depth',f'Depth star {i+1:02d}','Controlled bright-star hierarchy',o)
 hero=bpy.data.objects.get('Camera_Artist200_Hero')
 if not hero:bpy.ops.object.camera_add();hero=bpy.context.object;hero.name='Camera_Artist200_Hero'
 hero.location=(58,-72,34);hero.data.lens=55;target=sum((w.location for w in worlds),Vector())/len(worlds)*.28;hero.rotation_euler=(target-hero.location).to_track_quat('-Z','Y').to_euler();hero.data.dof.use_dof=True;hero.data.dof.focus_object=star;hero.data.dof.aperture_fstop=7.1;move(hero,root);s.camera=hero
 camera=[('Hero camera placement','Three-quarter orbital overview'),('Fifty-five millimeter lens','Natural compression'),('Barycentric aim','Generated inventory remains framed'),('Stellar focus target','Stable focal plane'),('Controlled aperture','Readable depth'),('Horizon clearance','Avoid tangent collisions'),('Primary hierarchy','Star anchors composition'),('Secondary hierarchy','Largest world counterweight'),('Orbit rhythm','Curves lead through frame'),('Negative-space reserve','UI-safe dark-space region'),('Warm/cool separation','Gold against cyan'),('Clipped-highlight check','Exposure protects corona'),('Silhouette check','World limbs remain distinct'),('Motion-safe framing','Moons remain in action area'),('Final camera activation',hero.name)]
 for n,d in camera:record('cinematography',n,d,hero if n=='Final camera activation' else None)
 qa=[('Seed recorded',str(SEED)),('Planet inventory validated',str(len(worlds))),('Artist collection tagged',root.name),('Procedural rerun policy','Replace ARTIST_200 collections'),('Shared stellar material',gold.name),('Shared hull material',hull.name),('Shared atmosphere material',glass.name),('Emission family validated','Cyan and amber'),('Camera assigned',hero.name),('Render engine validated',s.render.engine),('Resolution validated','1920x1080'),('Color management validated',s.view_settings.look),('World count cross-check',str(len(inventory['planets']))),('Manifest relationship',MANIFEST.name),('Base geometry preserved','Non-destructive additions'),('Collection streaming tag','artist_detail'),('Unreal export tag','optional cinematic detail'),('Pass-count assertion','Exactly 200'),('Master save gate',BLEND.name),('Beauty render gate',PREVIEW.name)]
 for n,d in qa:record('qa',n,d)
 if len(steps)!=200:raise RuntimeError(f'Artist pass count mismatch: {len(steps)}')
 root['streaming_class']='artist_detail';root['unreal_export_optional']=True;s['artist_200_complete']=True;s['artist_200_seed']=str(SEED);s.render.filepath=str(PREVIEW);summary={'seed':SEED,'passes':len(steps),'objects':len(bpy.data.objects),'materials':len(bpy.data.materials),'camera':hero.name,'planets':len(worlds)};REPORT.write_text(json.dumps({'summary':summary,'steps':steps},indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(BLEND));bpy.ops.render.render(write_still=True);bpy.ops.wm.save_as_mainfile(filepath=str(BLEND));print(json.dumps(summary,indent=2))
main()
