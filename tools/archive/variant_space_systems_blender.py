"""Phase six: reusable stellar variants, anomalies, infrastructure, and traffic."""
import json, math, random, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems'
BLEND=OUT/'SpaceSystems_Master.blend';PREVIEW=OUT/'SpaceSystems_Phase6_Variants.png';REPORT=OUT/'SpaceSystems_Phase6_Report.json'
RNG=random.Random(66109)

def col(n):
 c=bpy.data.collections.get(n) or bpy.data.collections.new(n)
 if c.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(c)
 return c
def move(o,c):
 if o.name not in c.objects:c.objects.link(o)
 for s in list(o.users_collection):
  if s!=c:s.objects.unlink(o)
 return o
def mat(n,c,e=0,a=1,metal=0,rough=.4):
 m=bpy.data.materials.get(n) or bpy.data.materials.new(n);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
 p.inputs['Base Color'].default_value=(*c,a);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if e:p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=e
 if a<1:p.inputs['Alpha'].default_value=a;m.surface_render_method='DITHERED'
 return m
def sph(n,p,r,m,seg=20):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=max(8,seg//2),location=p,radius=r);o=bpy.context.object;o.name=n;o.data.materials.append(m);return o
def cube(n,p,sc,m):
 bpy.ops.mesh.primitive_cube_add(location=p);o=bpy.context.object;o.name=n;o.scale=sc;o.data.materials.append(m);return o
def cyl(n,p,r,d,m,rot=(0,0,0),v=20):
 bpy.ops.mesh.primitive_cylinder_add(vertices=v,radius=r,depth=d,location=p,rotation=rot);o=bpy.context.object;o.name=n;o.data.materials.append(m);return o
def tor(n,p,maj,mi,m,rot=(0,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_radius=maj,minor_radius=mi,major_segments=64,minor_segments=8,location=p,rotation=rot);o=bpy.context.object;o.name=n;o.data.materials.append(m);return o
def line(n,pts,m,w=.035):
 d=bpy.data.curves.new(n,'CURVE');d.dimensions='3D';d.bevel_depth=w;d.bevel_resolution=2;s=d.splines.new('NURBS');s.points.add(len(pts)-1)
 for a,b in zip(s.points,pts):a.co=(*b,1)
 s.order_u=min(3,len(pts));s.use_endpoint_u=True;o=bpy.data.objects.new(n,d);bpy.context.collection.objects.link(o);o.data.materials.append(m);return o
def spin(o,end=600,turn=1):
 o.rotation_mode='XYZ';o.keyframe_insert(data_path='rotation_euler',frame=1);o.rotation_euler.z+=math.tau*turn;o.keyframe_insert(data_path='rotation_euler',frame=end)
def craft(name,p,scale,hull,glow,c):
 root=bpy.data.objects.new(name,None);root.location=p;c.objects.link(root)
 parts=[cube(name+'_Hull',p,(1.2*scale,.32*scale,.28*scale),hull),cube(name+'_WingL',Vector(p)+Vector((0,.65*scale,0)),(.55*scale,.36*scale,.06*scale),hull),cube(name+'_WingR',Vector(p)-Vector((0,.65*scale,0)),(.55*scale,.36*scale,.06*scale),hull),sph(name+'_Engine',Vector(p)+Vector((-1.25*scale,0,0)),.16*scale,glow,12)]
 for x in parts:x.parent=root;move(x,c)
 return root

def main():
 s=bpy.context.scene;hull=bpy.data.materials.get('M_StationHull');blue=mat('M_VariantBlue',(0.02,.3,1),20);violet=mat('M_VariantViolet',(.38,.01,1),18);red=mat('M_VariantRed',(1,.015,.002),18);white=mat('M_VariantWhite',(.7,.85,1),25);black=mat('M_VariantBlack',(0,0,.001),0,1,0,.01);amber=mat('M_TrafficAmber',(1,.18,.01),14);cyan=mat('M_TrafficCyan',(0,.6,1),14)
 variants=col('LIB_StellarVariants')
 # 1. Animated binary blue-white pair.
 pivot=bpy.data.objects.new('Variant_BinaryPivot',None);pivot.location=(85,0,0);variants.objects.link(pivot)
 for i,off in enumerate((Vector((0,4,0)),Vector((0,-4,0)))):
  star=sph(f'Variant_BinaryStar_{i+1}',pivot.location+off,2.4 if i==0 else 1.7,blue if i==0 else white,48);star.parent=pivot;move(star,variants)
 spin(pivot,360,1);pivot.hide_render=True;pivot['variant']='binary_blue_white'
 # 2. Violet dwarf.
 dwarf=sph('Variant_VioletDwarf',(85,18,0),2.1,violet,48);dwarf.hide_render=True;dwarf['variant']='violet_dwarf';move(dwarf,variants)
 # 3. Red supergiant.
 giant=sph('Variant_RedSupergiant',(85,-22,0),7.8,red,64);giant.hide_render=True;giant['variant']='red_supergiant';move(giant,variants)
 # 4. Pulsar core.
 pulsar=sph('Variant_PulsarCore',(85,38,0),1.1,white,40);pulsar.hide_render=True;move(pulsar,variants)
 # 5. Pulsar beams.
 for z in (-1,1):
  beam=cyl('Variant_PulsarBeam_'+str(z),(85,38,z*10),.28,20,blue);beam.hide_render=True;beam.parent=pulsar;move(beam,variants)
 spin(pulsar,90,4)
 # 6. Magnetar field arcs.
 for i in range(8):
  pts=[]
  for j in range(14):
   a=-math.pi/2+j/13*math.pi;pts.append(Vector((85,55,0))+Vector((math.cos(a)*(3+i*.4),math.sin(a)*(2+i*.3),math.sin(a*2+i)*1.2)))
  o=line('Variant_MagnetarArc_'+str(i+1),pts,violet,.045);o.hide_render=True;move(o,variants)
 # 7. Full black-hole accretion disk.
 anomalies=col('LIB_AnomalyVariants');center=Vector((73,-45,8));core=sph('Variant_BlackHoleCore',center,2.2,black,48);core.hide_render=True;move(core,anomalies)
 for i in range(11):
  ring=tor('Variant_AccretionRing_'+str(i+1),center,3.2+i*.55,.08,red if i<4 else amber,(.28,.1,.2));ring.hide_render=True;move(ring,anomalies);spin(ring,180+i*15,1 if i%2 else -1)
 # 8. Photon ring.
 photon=tor('Variant_BlackHolePhotonRing',center,2.55,.12,white,(.28,.1,.2));photon.hide_render=True;move(photon,anomalies)
 # 9. Wormhole throat.
 worm=Vector((72,-65,4))
 for i in range(9):
  r=tor('Variant_WormholeLayer_'+str(i+1),worm+Vector((0,i*.25,0)),4-i*.32,.08,blue,(math.pi/2,0,0));r.hide_render=True;move(r,anomalies);spin(r,120+i*12,1)
 # 10. Expanding stellar shockwave.
 wave=tor('Variant_StellarShockwave',(0,0,0),12,.12,red);wave.scale=(.4,.4,.4);wave.keyframe_insert(data_path='scale',frame=1);wave.scale=(4,4,4);wave.keyframe_insert(data_path='scale',frame=600);move(wave,col('SYS_EnvironmentalEvents'))
 # 11. Eclipse shadow proxy.
 eclipse=sph('EclipseShadowVolume',(-11.5,17.5,-1),3.0,black,24);eclipse.hide_render=True;eclipse.display_type='WIRE';eclipse['event']='planetary_eclipse';move(eclipse,col('SYS_EventVolumes'))
 # 12. Asteroid mining rig.
 infra=col('SYS_IndustrialInfrastructure');rig=Vector((-26,6,4));root=bpy.data.objects.new('ResourceNode_1_MiningRig',None);root.location=rig;infra.objects.link(root)
 for x in [tor('MiningRig_Clamp',rig,1.1,.1,hull,(math.pi/2,0,0)),cyl('MiningRig_Drill',rig+Vector((0,0,-1)),.16,2.2,amber),cube('MiningRig_Module',rig+Vector((1.5,0,0)),(.7,.35,.35),hull)]:x.parent=root;move(x,infra)
 spin(root,480,.5)
 # 13. Derelict distress beacon.
 der=bpy.data.objects.get('Derelict_ExpeditionVessel')
 if der:
  beacon=sph('Derelict_DistressBeacon',der.location+Vector((0,0,1.2)),.18,red,12);beacon.parent=der;move(beacon,infra);beacon.scale=(.4,)*3;beacon.keyframe_insert(data_path='scale',frame=1);beacon.scale=(1.8,)*3;beacon.keyframe_insert(data_path='scale',frame=60);beacon.scale=(.4,)*3;beacon.keyframe_insert(data_path='scale',frame=120)
 # 14. Station traffic drones.
 traffic=col('SYS_SpaceTraffic')
 for i in range(12):
  a=i/12*math.tau;p=Vector((17,16,3))+Vector((math.cos(a)*4,math.sin(a)*4,math.sin(a*2)*.6));d=craft('TrafficDrone_'+str(i+1),p,.22,hull,cyan,traffic);d['traffic_role']='station_drone'
 # 15. Cargo convoy.
 for i in range(5):
  p=Vector((-8-i*3,-13+i*.8,2));d=craft('CargoConvoy_'+str(i+1),p,.55,hull,amber,traffic);d['traffic_role']='cargo';d.keyframe_insert(data_path='location',frame=1);d.location+=Vector((32,12,2));d.keyframe_insert(data_path='location',frame=600)
 # 16. Patrol craft wing.
 for i in range(3):
  p=Vector((5,-18+i*2,5+i*.5));d=craft('PatrolCraft_'+str(i+1),p,.45,hull,blue,traffic);d['traffic_role']='patrol';d.keyframe_insert(data_path='location',frame=1);d.location+=Vector((18,25,-3));d.keyframe_insert(data_path='location',frame=450)
 # 17. Science-probe telemetry beam.
 probe=bpy.data.objects.get('LongRange_ScienceProbe')
 anomaly=bpy.data.objects.get('GravityAnomaly_Core')
 if probe and anomaly:move(line('ScienceProbe_TelemetryBeam',[probe.location,anomaly.location],cyan,.025),traffic)
 # 18. Cinematic shot markers.
 for n,f in [('BINARY_VARIANT',90),('MINING_RIG',210),('TRAFFIC_CROSSING',360),('DISTRESS_SIGNAL',510)]:
  if not s.timeline_markers.get(n):s.timeline_markers.new(n,frame=f)
 # 19. Variant preview cameras.
 cameras=col('SYS_Cameras')
 for name,loc,target in [('Camera_BinaryVariant',(105,-18,12),(85,0,0)),('Camera_BlackHoleVariant',(96,-70,24),center)]:
  if not bpy.data.objects.get(name):
   bpy.ops.object.camera_add(location=loc);c=bpy.context.object;c.name=name;c.data.lens=60;c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler();move(c,cameras)
 # 20. Catalog, render, save.
 ctrl=bpy.data.objects.get('SpaceSystem_MasterController');ctrl['variant_count']=7;ctrl['traffic_enabled']=True
 s['phase6_steps']=20;s['asset_version']='6.0';s.camera=bpy.data.objects.get('Camera_CinematicOverview') or s.camera;s.render.resolution_x=1280;s.render.resolution_y=720;s.render.filepath=str(PREVIEW);bpy.ops.render.render(write_still=True);bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
 report={'phase':6,'steps':20,'version':'6.0','objects':len(bpy.data.objects),'actions':len(bpy.data.actions),'variant_count':7,'traffic_objects':len(traffic.objects),'features':['binary pair','violet dwarf','red giant','pulsar','pulsar beams','magnetar arcs','accretion disk','photon ring','wormhole','shockwave','eclipse volume','mining rig','distress beacon','traffic drones','cargo convoy','patrol wing','telemetry beam','shot markers','variant cameras','catalog']};REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
main()
