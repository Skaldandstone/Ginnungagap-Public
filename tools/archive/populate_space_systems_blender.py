"""Phase seven: forty-step world population and production pass."""
import json,math,random,sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems';BLEND=OUT/'SpaceSystems_Master.blend';PREVIEW=OUT/'SpaceSystems_Phase7_Populated.png';REPORT=OUT/'SpaceSystems_Phase7_Report.json';CATALOG=OUT/'SpaceSystems_ModularCatalog.json';R=random.Random(77440)
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
 m=bpy.data.materials.get(n) or bpy.data.materials.new(n);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,a);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if e:p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=e
 if a<1:p.inputs['Alpha'].default_value=a;m.surface_render_method='DITHERED'
 return m
def sph(n,p,r,m,seg=16):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=max(8,seg//2),location=p,radius=r);o=bpy.context.object;o.name=n;o.data.materials.append(m);return o
def cube(n,p,sc,m):
 bpy.ops.mesh.primitive_cube_add(location=p);o=bpy.context.object;o.name=n;o.scale=sc;o.data.materials.append(m);return o
def cyl(n,p,r,d,m,rot=(0,0,0),v=16):
 bpy.ops.mesh.primitive_cylinder_add(vertices=v,radius=r,depth=d,location=p,rotation=rot);o=bpy.context.object;o.name=n;o.data.materials.append(m);return o
def tor(n,p,maj,mi,m,rot=(0,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_radius=maj,minor_radius=mi,major_segments=48,minor_segments=8,location=p,rotation=rot);o=bpy.context.object;o.name=n;o.data.materials.append(m);return o
def root(n,p,c,role):
 o=bpy.data.objects.new(n,None);o.location=p;o.empty_display_type='CUBE';o.empty_display_size=.5;c.objects.link(o);o['gameplay_role']=role;return o
def attach(parts,r,c):
 for p in parts:p.parent=r;move(p,c)
def spin(o,end=600,t=1):
 o.rotation_mode='XYZ';o.keyframe_insert(data_path='rotation_euler',frame=1);o.rotation_euler.z+=math.tau*t;o.keyframe_insert(data_path='rotation_euler',frame=end)
def camera(n,loc,target,lens=65):
 bpy.ops.object.camera_add(location=loc);o=bpy.context.object;o.name=n;o.data.lens=lens;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();move(o,col('SYS_Cameras'));return o
def simple_install(n,p,scale,c,hull,glow,role):
 r=root(n,p,c,role);attach([cube(n+'_Core',p,(.65*scale,.45*scale,.35*scale),hull),tor(n+'_Ring',p,1.0*scale,.08*scale,hull,(math.pi/2,0,0)),sph(n+'_Light',Vector(p)+Vector((0,0,.65*scale)),.1*scale,glow,10)],r,c);return r
def main():
 s=bpy.context.scene;hull=bpy.data.materials.get('M_StationHull');cyan=mat('M_PopCyan',(0,.55,1),14);green=mat('M_PopGreen',(0,1,.24),13);amber=mat('M_PopAmber',(1,.2,.005),14);red=mat('M_PopRed',(1,.01,.001),15);white=mat('M_PopWhite',(.65,.85,1),12);dark=mat('M_PopDark',(.015,.025,.035),0,1,.8,.3)
 ocean=bpy.data.objects.get('Ocean_World');vol=bpy.data.objects.get('Volcanic_World');ice=bpy.data.objects.get('Ice_World');gas=bpy.data.objects.get('Ringed_Gas_Giant')
 oceanp=ocean.matrix_world.translation if ocean else Vector((0,0,0));volp=vol.matrix_world.translation if vol else Vector((0,0,0));icep=ice.matrix_world.translation if ice else Vector((0,0,0));gasp=gas.matrix_world.translation if gas else Vector((0,0,0))
 # 1 Ocean orbital elevator.
 pc=col('MOD_OceanInfrastructure');e=root('OceanWorld_OrbitalElevator',oceanp+Vector((0,0,2.4)),pc,'orbital_elevator');attach([cyl('OceanElevator_Tether',oceanp+Vector((0,0,5)),.035,8,white),cube('OceanElevator_Counterweight',oceanp+Vector((0,0,9)),(.35,.35,.65),hull)],e,pc)
 # 2 Ocean spaceport.
 simple_install('OceanWorld_Spaceport',oceanp+Vector((2.9,0,.3)),.65,pc,hull,cyan,'spaceport')
 # 3 Weather satellites.
 for i in range(6):
  a=i/6*math.tau;p=oceanp+Vector((math.cos(a)*5,math.sin(a)*5,math.sin(a*2)));simple_install('OceanWeatherSat_'+str(i+1),p,.18,pc,hull,cyan,'weather_satellite')
 # 4 Tidal generator array.
 for i in range(8):move(tor('OceanTidalGenerator_'+str(i+1),oceanp+Vector((math.cos(i/8*math.tau)*3.2,math.sin(i/8*math.tau)*3.2,0)),.26,.04,green,(math.pi/2,0,0)),pc)
 # 5 Volcanic observatory.
 vc=col('MOD_VolcanicInfrastructure');simple_install('VolcanicWorld_Observatory',volp+Vector((0,2.4,.2)),.55,vc,hull,amber,'observatory')
 # 6 Thermal shield satellites.
 for i in range(5):
  a=i/5*math.tau;p=volp+Vector((math.cos(a)*4,math.sin(a)*4,.5));o=cube('ThermalShieldSat_'+str(i+1),p,(.5,.08,.5),dark);o['protection']='thermal';move(o,vc)
 # 7 Geothermal collectors.
 for i in range(7):simple_install('GeothermalCollector_'+str(i+1),volp+Vector((R.uniform(-2,2),R.uniform(-2,2),1.6)),.2,vc,hull,amber,'energy_collector')
 # 8 Plume sampling drones.
 for i in range(6):move(sph('PlumeSampler_'+str(i+1),volp+Vector((R.uniform(-3,3),R.uniform(-3,3),R.uniform(2,4))),.14,cyan,10),vc)
 # 9 Ice research base.
 ic=col('MOD_IceInfrastructure');simple_install('IceWorld_ResearchBase',icep+Vector((0,0,2.2)),.65,ic,hull,cyan,'research_base')
 # 10 Cryo harvesters.
 for i in range(7):simple_install('CryoHarvester_'+str(i+1),icep+Vector((R.uniform(-2,2),R.uniform(-2,2),1.7)),.18,ic,hull,white,'cryo_harvester')
 # 11 Geyser probes.
 for i in range(6):
  p=icep+Vector((R.uniform(-2.3,2.3),R.uniform(-2.3,2.3),2.8));o=cyl('GeyserProbe_'+str(i+1),p,.06,.8,green);o['sample_target']='cryo_geyser';move(o,ic)
 # 12 Gas atmospheric scoops.
 gc=col('MOD_GasInfrastructure')
 for i in range(8):
  a=i/8*math.tau;p=gasp+Vector((math.cos(a)*6,math.sin(a)*6,math.sin(a*2)));simple_install('GasScoop_'+str(i+1),p,.25,gc,hull,amber,'atmospheric_scoop')
 # 13 Refinery skimmers.
 for i in range(4):
  p=gasp+Vector((-7+i*2,6+i*.4,1));r=simple_install('RefinerySkimmer_'+str(i+1),p,.35,gc,hull,cyan,'refinery_skimmer');r.keyframe_insert(data_path='location',frame=1);r.location+=Vector((14,-4,0));r.keyframe_insert(data_path='location',frame=600)
 # 14 Ring shepherd satellites.
 for i in range(10):
  a=i/10*math.tau;p=gasp+Vector((math.cos(a)*9,math.sin(a)*9,0));o=sph('RingShepherd_'+str(i+1),p,.13,green,10);o['ring_management']=True;move(o,gc)
 # 15 Storm probes.
 for i in range(5):move(cyl('StormProbe_'+str(i+1),gasp+Vector((R.uniform(-5,5),R.uniform(-5,5),R.uniform(-3,3))),.07,.7,red),gc)
 # 16 Asteroid colony.
 bc=col('MOD_BeltInfrastructure');simple_install('AsteroidBelt_Colony',(0,29,1),1.0,bc,hull,cyan,'belt_colony')
 # 17 Belt mining craft.
 for i in range(8):simple_install('BeltMiner_'+str(i+1),(R.uniform(-10,10),R.uniform(24,34),R.uniform(-2,3)),.22,bc,hull,green,'mining_craft')
 # 18 Defense turrets.
 defense=col('MOD_DefenseNetwork')
 for i,p in enumerate(((10,20,3),(-18,16,2),(24,-8,4),(-20,-20,1),(6,-28,3),(30,12,5))):
  r=root('DefenseTurret_'+str(i+1),p,defense,'defense_turret');attach([cyl('DefenseTurret_'+str(i+1)+'_Base',p,.28,.6,hull),cyl('DefenseTurret_'+str(i+1)+'_Barrel',Vector(p)+Vector((0,0,.5)),.07,1.1,red,(0,math.pi/2,0))],r,defense)
 # 19 Communications relays.
 comms=col('MOD_Communications')
 for i,p in enumerate(((35,0,8),(-35,0,6),(0,38,9),(0,-38,7))):simple_install('CommRelay_'+str(i+1),p,.42,comms,hull,cyan,'communications_relay')
 # 20 Rescue beacon chain.
 rescue=col('MOD_RescueNetwork')
 for i in range(9):
  p=(-28+i*3,10+i*.7,2);o=sph('RescueBeacon_'+str(i+1),p,.12,green,10);o['emergency_channel']='SAR';move(o,rescue)
 # 21 Route signs.
 nav=col('MOD_NavigationControls')
 for i,p in enumerate(((8,-8,2),(16,-16,3),(-7,8,1),(-12,14,0))):
  o=cube('RouteSign_'+str(i+1),p,(.7,.05,.3),cyan);o['route_index']=i;move(o,nav)
 # 22 Speed gates.
 for i in range(6):move(tor('SpeedGate_'+str(i+1),(i*4-10,-12,2),1.0,.05,amber,(math.pi/2,0,0)),nav)
 # 23 Hazard fence.
 for i in range(14):move(cyl('HazardFence_'+str(i+1),(-17+i*.8,22,5),.035,2,red),nav)
 # 24 Exclusion rings.
 for i,r in enumerate((7,9,11)):move(tor('AnomalyExclusionRing_'+str(i+1),(-34,30,12),r,.035,red,(.3,.1,.2)),nav)
 # 25 POI anchor empties.
 anchors=col('GAMEPLAY_Anchors')
 for n,p,t in [('POI_Ocean',oceanp,'celestial'),('POI_Volcanic',volp,'celestial'),('POI_Ice',icep,'celestial'),('POI_Gas',gasp,'celestial'),('POI_Gate',(20,-24,4),'jump_gate')]:root(n,p,anchors,t)
 # 26 Mission anchors.
 for i,p in enumerate(((-26,6,4),(-11,26,-2),(-34,30,12))):root('MissionAnchor_'+str(i+1),p,anchors,'mission_objective')
 # 27 Spawn anchors.
 for i,p in enumerate(((0,0,0),(5,-5,1),(-5,5,-1),(20,-28,4))):root('SpawnAnchor_'+str(i+1),p,anchors,'spawn_point')
 # 28 Audio zones.
 for i,p in enumerate(((0,0,0),(-34,30,12),(20,-24,4))):
  o=sph('AudioZone_'+str(i+1),p,6+i*2,dark,12);o.hide_render=True;o.display_type='WIRE';o['audio_profile']=('stellar','anomaly','jump_gate')[i];move(o,anchors)
 # 29 FX anchors.
 for i,p in enumerate(((0,0,7),(-34,30,12),(20,-24,4),gasp+Vector((0,0,5)))):root('FXAnchor_'+str(i+1),p,anchors,'vfx_origin')
 # 30 Light anchors.
 for i,p in enumerate(((0,0,0),(-34,30,12),(20,-24,4))):root('LightAnchor_'+str(i+1),p,anchors,'lighting_origin')
 # 31 Animated system-orbit camera.
 cam=camera('Camera_SystemOrbit',(65,-50,32),(0,0,0),52);cam.keyframe_insert(data_path='location',frame=1);cam.location=(-65,50,28);cam.keyframe_insert(data_path='location',frame=600)
 # 32 Station close-up camera.
 camera('Camera_StationCloseup',(22,11,7),(17,16,3),78)
 # 33 Planet texture camera.
 camera('Camera_OceanCloseup',oceanp+Vector((8,-8,3)),oceanp,82)
 # 34 Mining-rig camera.
 camera('Camera_MiningRig',(-18,0,9),(-26,6,4),72)
 # 35 Jump-gate camera.
 camera('Camera_JumpGate',(28,-34,10),(20,-24,4),68)
 # 36 Camera shot markers.
 for n,f in [('SYSTEM_ORBIT',30),('STATION_CLOSEUP',140),('OCEAN_CLOSEUP',250),('MINING_OPERATION',370),('JUMP_GATE_APPROACH',520)]:
  if not s.timeline_markers.get(n):s.timeline_markers.new(n,frame=f)
 # 37 Collection performance metadata.
 for c in bpy.data.collections:
  if c.name.startswith(('MOD_','GAMEPLAY_')):c['streaming_group']=c.name;c['runtime_optional']=True
 # 38 Object instancing metadata.
 for c in (pc,vc,ic,gc,bc,defense,comms,rescue):
  for o in c.objects:
   if o.type=='MESH':o['instance_candidate']=True;o['nanite_recommended']=len(o.data.vertices)>200 if hasattr(o.data,'vertices') else False
 # 39 Modular catalog.
 catalog={'collections':{c.name:{'objects':len(c.objects),'optional':bool(c.get('runtime_optional',False))} for c in bpy.data.collections if c.name.startswith(('MOD_','GAMEPLAY_'))},'cameras':[o.name for o in s.objects if o.type=='CAMERA'],'anchors':[o.name for o in anchors.objects]};CATALOG.write_text(json.dumps(catalog,indent=2),encoding='utf-8')
 # 40 Render, version, save, report.
 ctrl=bpy.data.objects.get('SpaceSystem_MasterController');ctrl['population_modules']=8;ctrl['gameplay_anchor_count']=len(anchors.objects);s['phase7_steps']=40;s['asset_version']='7.0';s.camera=bpy.data.objects.get('Camera_CinematicOverview') or s.camera;s.render.resolution_x=1280;s.render.resolution_y=720;s.render.filepath=str(PREVIEW);bpy.ops.render.render(write_still=True);bpy.ops.wm.save_as_mainfile(filepath=str(BLEND));report={'phase':7,'steps':40,'version':'7.0','objects':len(bpy.data.objects),'collections':len(bpy.data.collections),'actions':len(bpy.data.actions),'modules':8,'anchors':len(anchors.objects),'new_cameras':5};REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
main()
