"""Phase 88: clean Pelagos hero-station rebuild against the approved AAA concept."""
import bpy,json,math,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems';LEVEL=OUT/'SpaceSystems_PelagosOrbitalArrival_Level.blend';PREVIEW=OUT/'Pelagos_OrbitalArrival_AAA_Rebuild_v1.png';REPORT=OUT/'Pelagos_OrbitalArrival_AAA_Rebuild_v1.json'
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
def finish(o,n,m,c,bev=.04,smooth=False):
 o.name=n;o.data.materials.append(m)
 if bev:b=o.modifiers.new('Manufactured edge','BEVEL');b.width=bev;b.segments=3
 if smooth:
  for p in o.data.polygons:p.use_smooth=True
 return move(o,c)
def cube(n,p,sc,m,c,rot=(0,0,0),bev=.04):
 bpy.ops.mesh.primitive_cube_add(location=p,rotation=rot);o=bpy.context.object;o.scale=sc;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True);return finish(o,n,m,c,bev)
def cyl(n,a,b,r,m,c,verts=40):
 a,b=Vector(a),Vector(b);v=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=v.length,location=(a+b)/2);o=bpy.context.object;o.rotation_mode='QUATERNION';o.rotation_quaternion=v.to_track_quat('Z','Y');return finish(o,n,m,c,r*.1,True)
def sphere(n,p,r,m,c,sc=(1,1,1)):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=r,location=p);o=bpy.context.object;o.scale=sc;return finish(o,n,m,c,0,True)
def torus(n,p,major,minor,m,c,rot=(0,0,0),seg=96):
 bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=seg,minor_segments=16,location=p,rotation=rot);return finish(bpy.context.object,n,m,c,0,True)
def light(n,kind,p,color,energy,size,c,target):
 d=bpy.data.lights.new(n,kind);d.color=color;d.energy=energy
 if kind=='AREA':d.shape='DISK';d.size=size
 o=bpy.data.objects.new(n,d);c.objects.link(o);o.location=p;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();return o
def main():
 s=bpy.context.scene
 if s.get('aaa_concept_rebuild')=='88.0':raise RuntimeError('Concept rebuild already installed')
 old=bpy.data.collections.get('AAA_REBUILD_88')
 if old:
  for o in list(old.all_objects):bpy.data.objects.remove(o,do_unlink=True)
  bpy.data.collections.remove(old)
 c=col('AAA_REBUILD_88')
 # Beauty reset: retain only the planet/atmosphere and restrained star layer from the old scene.
 keep=('OceanArrival_Planet','AAA_PelagosAtmosphere','AP25_Star_')
 hidden=0
 for o in bpy.data.objects:
  if o.type in {'MESH','CURVE','FONT'} and not o.name.startswith(keep):o.hide_render=True;hidden+=1
 # Material families derived from the approved concept.
 hull=mat('R88_WeatheredTitanium',(.16,.18,.19),.76,.34);white=mat('R88_ThermalCeramic',(.52,.53,.5),.24,.42);dark=mat('R88_Recess',(.004,.007,.009),.7,.25);foil=mat('R88_ThermalFoil',(.24,.11,.02),.72,.4);glass=mat('R88_ObservationGlass',(.004,.025,.045),.35,.12,(.005,.035,.07),.5);cyan=mat('R88_NavCyan',(.003,.08,.14),.2,.18,(.01,.25,.8),5);amber=mat('R88_ServiceAmber',(.2,.025,.003),.25,.28,(1,.045,.004),7)
 # HABITATION WHEEL — segmented pressure modules with inner service corridor and genuine spokes.
 wheel_x=-6.2;R=7.2
 torus('R88_WheelOuterRib',(wheel_x,0,3),R+.72,.16,hull,c,(0,math.pi/2,0));torus('R88_WheelInnerRib',(wheel_x,0,3),R-.72,.13,dark,c,(0,math.pi/2,0))
 for i in range(32):
  a=i*math.tau/32;y=math.cos(a)*R;z=3+math.sin(a)*R
  # Broad tangent-aligned pressure section, visually separated from neighbors.
  module=cube(f'R88_WheelModule_{i:02d}',(wheel_x,y,z),(1.18,.82,.54),white if i%8 else foil,c,(a,0,0),.13)
  cube(f'R88_WheelPanel_{i:02d}',(wheel_x-1.19,y,z),(.025,.58,.32),hull,c,(a,0,0),.02)
  for w in (-.3,0,.3):
   yy=y+math.cos(a)*w;zz=z+math.sin(a)*w;sphere(f'R88_WheelWindow_{i:02d}_{w}',(wheel_x-1.23,yy,zz),.045,cyan,c,sc=(.35,1,1))
 for i in range(6):
  a=i*math.tau/6;y=math.cos(a)*(R-.8);z=3+math.sin(a)*(R-.8)
  cyl(f'R88_WheelSpokeA_{i}',(wheel_x,0,3),(wheel_x,y,z),.2,hull,c)
  # Paired truss chord communicates load path.
  cyl(f'R88_WheelSpokeB_{i}',(wheel_x+.55,0,3),(wheel_x+.55,y,z),.09,white,c,24)
 # Reinforced non-rotating wheel hub.
 cyl('R88_WheelHub',(-8.1,0,3),(-4.3,0,3),1.45,hull,c);torus('R88_HubBearingA',(-7.55,0,3),1.7,.19,foil,c,(0,math.pi/2,0));torus('R88_HubBearingB',(-4.8,0,3),1.7,.19,white,c,(0,math.pi/2,0))
 # OPERATIONS SPINE — layered modules rather than one primitive tube.
 for i,x in enumerate((-3.2,-.6,2.0,4.6,7.2,9.8)):
  cube(f'R88_SpineModule_{i}',(x,0,3),(1.18,1.55,1.28),hull,c,bev=.26)
  cube(f'R88_SpineArmorTop_{i}',(x,0,4.32),(.88,1.25,.09),white,c,bev=.06)
  cube(f'R88_SpineArmorSide_{i}',(x,-1.58,3),(.88,.08,.75),white if i%2 else foil,c,bev=.06)
  cube(f'R88_SpineRecess_{i}',(x,-1.68,3),(.55,.025,.38),dark,c,bev=.02)
  for j in range(5):sphere(f'R88_SpineWindow_{i}_{j}',(x-.48+j*.24,-1.72,3.72),.04,cyan,c,sc=(1,.3,.55))
  if i<5:cyl(f'R88_SpineTrussTop_{i}',(x+.9,0,4.4),(x+1.7,0,4.4),.09,dark,c,20)
 # Recessed hangars on the camera-facing side with door frames and interior light depth.
 for i,x in enumerate((-1.3,2.4,6.1)):
  cube(f'R88_HangarVoid_{i}',(x,-1.78,2.6),(1.12,.2,.64),dark,c,bev=.05)
  for z in (2.0,3.2):cyl(f'R88_HangarRail_{i}_{z}',(x-1.1,-2.0,z),(x+1.1,-2.0,z),.045,white,c,16)
  for j in range(4):sphere(f'R88_HangarLamp_{i}_{j}',(x-.75+j*.5,-2.02,3.13),.035,amber,c)
  cube(f'R88_HangarDeck_{i}',(x,-2.05,2.02),(1.1,.48,.045),hull,c,bev=.02)
 # COMMAND SUPERSTRUCTURE — stacked, asymmetric control volumes and observation cupola.
 cube('R88_CommandBase',(4.2,.25,5.05),(2.35,1.45,.55),hull,c,bev=.22);cube('R88_CommandMid',(4.6,.15,5.9),(1.55,1.15,.38),white,c,bev=.18);sphere('R88_CommandCupola',(4.8,-.2,6.6),1.0,glass,c,sc=(1.75,1.05,.6))
 for i in range(9):a=math.pi*(.15+.7*i/8);sphere(f'R88_CupolaWindow_{i}',(4.8+math.cos(a)*1.45,-1.18,6.62+math.sin(a)*.36),.055,cyan,c,sc=(1,.3,.65))
 # Antenna masts and sensor pallets.
 for i,(x,h) in enumerate(((2.9,2.4),(4.6,3.2),(6.2,2.0))):
  cyl(f'R88_Mast_{i}',(x,.5,6.2),(x,.5,6.2+h),.075,hull,c,20);cyl(f'R88_MastForkA_{i}',(x,.5,6.2+h),(x-.3,.5,6.65+h),.035,white,c,14);cyl(f'R88_MastForkB_{i}',(x,.5,6.2+h),(x+.3,.5,6.65+h),.035,white,c,14)
 # Forward arrival-control prow.
 cube('R88_ForwardProw',(11.8,0,3),(1.65,1.45,1.08),white,c,bev=.34);cube('R88_ProwGlass',(13.15,-.65,3.32),(.36,.82,.44),glass,c,rot=(0,0,-.18),bev=.12);cyl('R88_ProwNeck',(9.8,0,3),(10.25,0,3),.82,hull,c)
 # Paired radiator wings and articulated roots.
 for side in (-1,1):
  y=side*2.1;cyl(f'R88_RadiatorBoom_{side}',(3.0,side*1.2,2.1),(3.0,y,1.1),.13,hull,c)
  for j in range(4):
   yy=y+side*(.85+j*1.15);cube(f'R88_Radiator_{side}_{j}',(3.0,yy,.75),(1.55,.48,.055),dark,c,rot=(0,.08*side,0),bev=.025)
   for k in range(5):cube(f'R88_RadiatorCell_{side}_{j}_{k}',(1.85+k*.58,yy,.82),(.24,.4,.012),glass,c,bev=.01)
 # Docking clusters — recessed industrial ports with gantries, not floating neon rings.
 for dock,(x,z) in enumerate(((-1.7,1.1),(1.2,1.1),(7.2,1.1),(9.6,1.1)),1):
  cube(f'R88_DockHousing_{dock}',(x,-2.6,z),(.85,.72,.62),hull,c,bev=.16);cyl(f'R88_DockTunnel_{dock}',(x,-2.35,z),(x,-3.5,z),.48,dark,c,32);torus(f'R88_DockSeal_{dock}',(x,-3.55,z),.5,.095,white,c,(math.pi/2,0,0),64)
  for side in (-1,1):cyl(f'R88_DockClamp_{dock}_{side}',(x+side*.5,-3.38,z-.42),(x+side*.62,-3.75,z),.065,foil,c,16)
  sphere(f'R88_DockStatus_{dock}',(x,-3.68,z+.68),.07,amber if dock==3 else cyan,c)
 # Human-scale handrails, access hatches, tanks, and maintenance workbee.
 for i in range(18):
  x=-3.5+i*.78;cyl(f'R88_HandrailPost_{i}',(x,-1.78,4.32),(x,-1.78,4.62),.018,white,c,10)
  if i<17:cyl(f'R88_HandrailTop_{i}',(x,-1.78,4.62),(x+.78,-1.78,4.62),.018,white,c,10)
 for i,x in enumerate((-2.2,0,7.8)):cyl(f'R88_ServiceTank_{i}',(x,1.8,1.6),(x,1.8,3),.22,foil,c,24)
 sphere('R88_Workbee',(-.4,-4.6,3.8),.34,hull,c,sc=(1.8,.7,.55));cyl('R88_WorkbeeArm',(-.1,-4.6,3.8),(.6,-4.2,3.2),.045,white,c,16);sphere('R88_WorkbeeLamp',(-.62,-4.82,3.9),.055,cyan,c)
 # Decal-like identity geometry, kept restrained.
 bpy.ops.object.text_add(location=(3.0,-1.79,3.55),rotation=(math.pi/2,0,0));t=bpy.context.object;t.data.body='PELAGOS ORBITAL';t.data.size=.28;t.data.extrude=.006;t.data.materials.append(white);t.name='R88_Identity';move(t,c)
 # New lighting rig and camera matched to the concept's readable three-quarter composition.
 for o in bpy.data.objects:
  if o.type=='LIGHT':o.hide_render=True
 light('R88_Key','AREA',(-18,-22,24),(1,.62,.38),2400,18,c,(1,0,3));light('R88_PlanetBounce','AREA',(10,18,-2),(.08,.28,1),1800,22,c,(1,0,3));light('R88_Fill','AREA',(-4,-12,7),(.18,.3,.55),950,12,c,(1,0,3))
 cam_data=bpy.data.cameras.new('Camera_R88_AAA_Rebuild');cam_data.lens=56;cam_data.dof.use_dof=True;cam_data.dof.aperture_fstop=8;cam=bpy.data.objects.new('Camera_R88_AAA_Rebuild',cam_data);c.objects.link(cam);cam.location=(-25,-33,15);cam.rotation_euler=(Vector((1.5,2.5,3.3))-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
 s.render.engine='BLENDER_EEVEE';s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';s.render.filepath=str(PREVIEW);s.view_settings.look='AgX - Medium High Contrast';s.view_settings.exposure=.6
 s['aaa_concept_rebuild']='88.0';s['asset_version']='88.0';s['level_status']='aaa_rebuild_candidate';s['concept_reference']='Pelagos_OrbitalArrival_AAA_Concept_v1.png'
 report={'phase':88,'version':'88.0','concept':'Pelagos_OrbitalArrival_AAA_Concept_v1.png','new_objects':len(c.objects),'legacy_render_objects_hidden':hidden,'features':['segmented habitation wheel','reinforced bearing hub','layered operations spine','three recessed hangars','command superstructure','forward control prow','radiator wings','four industrial docking clusters','human-scale maintenance detail'],'gameplay_preserved':True}
 REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8');bpy.ops.wm.save_as_mainfile(filepath=str(LEVEL));bpy.ops.render.render(write_still=True);print(json.dumps(report,indent=2))
main()
