"""Phase eight: one hundred cataloged world-building and production steps."""
import json,math,random,sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems';BLEND=OUT/'SpaceSystems_Master.blend';PREVIEW=OUT/'SpaceSystems_Phase8_100Steps.png';REPORT=OUT/'SpaceSystems_Phase8_100Steps.json';R=random.Random(8100);done=[]
def col(n):
 c=bpy.data.collections.get(n) or bpy.data.collections.new(n)
 if c.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(c)
 return c
def move(o,c):
 if o.name not in c.objects:c.objects.link(o)
 for s in list(o.users_collection):
  if s!=c:s.objects.unlink(o)
 return o
def mat(n,c,e=0,metal=0,rough=.4):
 m=bpy.data.materials.get(n) or bpy.data.materials.new(n);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*c,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if e:p.inputs['Emission Color'].default_value=(*c,1);p.inputs['Emission Strength'].default_value=e
 return m
def sph(n,p,r,m,seg=12):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=max(6,seg//2),location=p,radius=r);o=bpy.context.object;o.name=n;o.data.materials.append(m);return o
def cube(n,p,sc,m):
 bpy.ops.mesh.primitive_cube_add(location=p);o=bpy.context.object;o.name=n;o.scale=sc;o.data.materials.append(m);return o
def cyl(n,p,r,d,m,rot=(0,0,0),v=12):
 bpy.ops.mesh.primitive_cylinder_add(vertices=v,radius=r,depth=d,location=p,rotation=rot);o=bpy.context.object;o.name=n;o.data.materials.append(m);return o
def tor(n,p,maj,mi,m,rot=(0,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_radius=maj,minor_radius=mi,major_segments=32,minor_segments=6,location=p,rotation=rot);o=bpy.context.object;o.name=n;o.data.materials.append(m);return o
def root(n,p,c,role,step):
 o=bpy.data.objects.new(n,None);o.location=p;o.empty_display_type='CUBE';o.empty_display_size=.35;c.objects.link(o);o['gameplay_role']=role;o['phase8_step']=step;done.append({'step':step,'name':n,'role':role});return o
def install(step,n,p,role,c,hull,glow,scale=.3):
 r=root(n,p,c,role,step);parts=[cube(n+'_Core',p,(scale,.7*scale,.55*scale),hull),tor(n+'_Ring',p,1.3*scale,.09*scale,hull,(math.pi/2,0,0)),sph(n+'_Beacon',Vector(p)+Vector((0,0,.8*scale)),.14*scale,glow,10)]
 for o in parts:o.parent=r;move(o,c)
 return r
def craft(step,n,p,role,c,hull,glow,scale=.3):
 r=root(n,p,c,role,step);parts=[cube(n+'_Hull',p,(1.2*scale,.35*scale,.25*scale),hull),cube(n+'_WingL',Vector(p)+Vector((0,.55*scale,0)),(.55*scale,.22*scale,.04*scale),hull),cube(n+'_WingR',Vector(p)-Vector((0,.55*scale,0)),(.55*scale,.22*scale,.04*scale),hull),sph(n+'_Engine',Vector(p)+Vector((-1.25*scale,0,0)),.12*scale,glow,10)]
 for o in parts:o.parent=r;move(o,c)
 return r
def camera(step,n,loc,target,lens=70):
 bpy.ops.object.camera_add(location=loc);o=bpy.context.object;o.name=n;o.data.lens=lens;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();move(o,col('SYS_Cameras'));o['phase8_step']=step;done.append({'step':step,'name':n,'role':'camera'});return o
def main():
 s=bpy.context.scene;hull=bpy.data.materials.get('M_StationHull');cyan=mat('M_P8Cyan',(0,.5,1),14);green=mat('M_P8Green',(0,1,.2),12);amber=mat('M_P8Amber',(1,.18,.004),14);red=mat('M_P8Red',(1,.008,.001),15);violet=mat('M_P8Violet',(.35,.005,1),14);white=mat('M_P8White',(.7,.85,1),14)
 worlds={k:bpy.data.objects.get(v) for k,v in {'Ocean':'Ocean_World','Volcanic':'Volcanic_World','Ice':'Ice_World','Gas':'Ringed_Gas_Giant'}.items()};P={k:(o.matrix_world.translation if o else Vector()) for k,o in worlds.items()}
 # Steps 1-10: ocean landmarks.
 ocean_names=[('FloatingArcology','habitat'),('AquacultureRing','food'),('DesalinationPlant','life_support'),('HurricaneMonitor','weather'),('ElevatorClamp','transport'),('PolarLaboratory','science'),('SubseaRelay','communications'),('CloudSeeder','weather_control'),('TidalSubstation','power'),('RescueDock','rescue')];c=col('P8_OceanLandmarks')
 for i,(n,r) in enumerate(ocean_names,1):a=i/10*math.tau;install(i,'Ocean_'+n,P['Ocean']+Vector((math.cos(a)*3.4,math.sin(a)*3.4,(i%3-1)*.35)),r,c,hull,cyan,.28)
 # Steps 11-20: volcanic landmarks.
 names=[('MagmaTap','resource'),('ShieldPylon','protection'),('AshSampler','science'),('SulfurMine','resource'),('LavaBridge','transport'),('GeothermalHub','power'),('EmergencyBunker','shelter'),('HeatRelay','communications'),('DroneDock','logistics'),('SeismicArray','science')];c=col('P8_VolcanicLandmarks')
 for j,(n,r) in enumerate(names,11):a=(j-10)/10*math.tau;install(j,'Volcanic_'+n,P['Volcanic']+Vector((math.cos(a)*3,math.sin(a)*3,(j%2)*.4)),r,c,hull,amber,.27)
 # Steps 21-30: ice landmarks.
 names=[('CryoVault','storage'),('CoreDrill','science'),('GlacierCrawler','resource'),('ThermalHabitat','habitat'),('AuroraStation','science'),('IcePort','transport'),('WaterHarvester','resource'),('FaultMonitor','hazard_monitor'),('BeaconTower','navigation'),('SampleArchive','science')];c=col('P8_IceLandmarks')
 for j,(n,r) in enumerate(names,21):a=(j-20)/10*math.tau;install(j,'Ice_'+n,P['Ice']+Vector((math.cos(a)*3,math.sin(a)*3,(j%3-1)*.3)),r,c,hull,white,.26)
 # Steps 31-40: gas giant assets.
 names=[('HeliumSkimmer','resource'),('StormLab','science'),('PressureRelay','communications'),('CloudCity','habitat'),('FuelCondenser','resource'),('MagnetosphereProbe','science'),('RingPort','transport'),('AtmosphereBeacon','navigation'),('RescuePlatform','rescue'),('WeatherControl','weather_control')];c=col('P8_GasLandmarks')
 for j,(n,r) in enumerate(names,31):a=(j-30)/10*math.tau;install(j,'Gas_'+n,P['Gas']+Vector((math.cos(a)*7,math.sin(a)*7,math.sin(a*2))),r,c,hull,amber,.32)
 # Steps 41-50: belt installations.
 names=[('ProspectorGuild','habitat'),('OreProcessor','resource'),('IceDepot','resource'),('MassDriver','transport'),('TugStation','logistics'),('SurveyArray','science'),('RefuelPoint','fuel'),('SalvageYard','salvage'),('EmergencyShelter','shelter'),('TradePost','commerce')];c=col('P8_BeltLandmarks')
 for j,(n,r) in enumerate(names,41):a=(j-40)/10*math.tau;install(j,'Belt_'+n,Vector((math.cos(a)*29,math.sin(a)*29,R.uniform(-2,2))),r,c,hull,green,.3)
 # Steps 51-60: station services.
 names=[('TrafficControl','traffic'),('RepairDock','repair'),('MedicalDock','medical'),('CargoTerminal','cargo'),('Shipyard','construction'),('SecurityPost','security'),('CrewTransfer','transport'),('SensorMast','sensors'),('FuelFarm','fuel'),('DataCenter','communications')];c=col('P8_StationServices')
 for j,(n,r) in enumerate(names,51):install(j,'Station_'+n,Vector((12+(j-51)*1.2,12+(j%2)*1.1,3+(j%3)*.4)),r,c,hull,cyan,.3)
 # Steps 61-70: hazards.
 hazard_specs=[('RadiationPocket','radiation',(9,5,4)),('GravityShear','gravity',(-30,24,9)),('DebrisCloud','debris',(4,28,1)),('ThermalFront','thermal',(7,-7,2)),('IonStorm','ion',(18,22,7)),('CryoMist','cryo',(-24,-12,-2)),('MagneticKnot','magnetic',(25,8,5)),('SolarFlareZone','solar',(11,0,3)),('CometWake','debris',(35,-18,8)),('AnomalyEcho','anomaly',(-38,34,14))];c=col('P8_HazardVolumes')
 for j,(n,r,p) in enumerate(hazard_specs,61):o=sph('Hazard_'+n,p,1.4+(j-61)*.18,red if j%2 else violet,12);o.hide_render=True;o.display_type='WIRE';o['hazard_type']=r;o['phase8_step']=j;move(o,c);done.append({'step':j,'name':o.name,'role':'hazard'})
 # Steps 71-80: science and mission assets.
 names=[('DeepSpaceTelescope','science'),('GravimetricArray','science'),('ExobiologyLab','science'),('CometSampler','science'),('SignalDecoder','mission'),('AncientProbe','mission'),('BlackBoxRecovery','mission'),('DistressCache','mission'),('NavigationArchive','mission'),('QuantumClock','science')];c=col('P8_ScienceMission')
 for j,(n,r) in enumerate(names,71):install(j,n,Vector((-15+(j-71)*3,34-(j%3)*2,5+(j%2))),r,c,hull,violet,.26)
 # Steps 81-90: traffic craft.
 traffic=[('PassengerShuttle','passenger'),('MedicalCutter','medical'),('OreTug','cargo'),('SurveyCorvette','science'),('RescueTender','rescue'),('FuelBarge','fuel'),('PatrolInterceptor','security'),('Courier','communications'),('ConstructionTender','construction'),('SalvageSkiff','salvage')];c=col('P8_TrafficFleet')
 for j,(n,r) in enumerate(traffic,81):o=craft(j,n,Vector((-20+(j-81)*4,-22+(j%3)*2,3+(j%2))),r,c,hull,cyan if j%2 else amber,.36);o.keyframe_insert(data_path='location',frame=1);o.location+=Vector((24,18,R.uniform(-2,2)));o.keyframe_insert(data_path='location',frame=600)
 # Steps 91-95: cameras.
 camera(91,'Camera_OceanInfrastructure',P['Ocean']+Vector((10,-10,6)),P['Ocean'],78);camera(92,'Camera_VolcanicInfrastructure',P['Volcanic']+Vector((9,-8,5)),P['Volcanic'],78);camera(93,'Camera_IceInfrastructure',P['Ice']+Vector((8,-9,5)),P['Ice'],78);camera(94,'Camera_GasInfrastructure',P['Gas']+Vector((14,-14,8)),P['Gas'],72);camera(95,'Camera_BeltColony',(12,38,10),(0,29,1),70)
 # Step 96: dedicated view layer.
 if 'GameplayPopulation' not in s.view_layers:s.view_layers.new('GameplayPopulation')
 done.append({'step':96,'name':'GameplayPopulation','role':'view_layer'})
 # Step 97: collection streaming priorities.
 for c in bpy.data.collections:
  if c.name.startswith('P8_'):c['streaming_priority']=2;c['runtime_optional']=True
 done.append({'step':97,'name':'P8 streaming metadata','role':'optimization'})
 # Step 98: object bounds metadata.
 for c in bpy.data.collections:
  if c.name.startswith('P8_'):
   for o in c.objects:o['streaming_radius']=2500 if o.type=='EMPTY' else 1000
 done.append({'step':98,'name':'streaming radii','role':'optimization'})
 # Step 99: shot markers and catalog.
 for n,f in [('P8_OCEAN',100),('P8_VOLCANIC',200),('P8_ICE',300),('P8_GAS',400),('P8_BELT',500)]:
  if not s.timeline_markers.get(n):s.timeline_markers.new(n,frame=f)
 done.append({'step':99,'name':'phase8 shot markers','role':'cinematic'})
 # Step 100: validate, render, save.
 if len(done)!=99:raise RuntimeError(f'Expected 99 pre-save steps, got {len(done)}')
 done.append({'step':100,'name':'versioned save and report','role':'production'});ctrl=bpy.data.objects.get('SpaceSystem_MasterController');ctrl['phase8_assets']=95;ctrl['phase8_complete']=True;s['phase8_steps']=100;s['asset_version']='8.0';s.camera=bpy.data.objects.get('Camera_CinematicOverview') or s.camera;s.render.resolution_x=1280;s.render.resolution_y=720;s.render.filepath=str(PREVIEW);bpy.ops.render.render(write_still=True);bpy.ops.wm.save_as_mainfile(filepath=str(BLEND));REPORT.write_text(json.dumps({'phase':8,'steps':done,'summary':{'objects':len(bpy.data.objects),'collections':len(bpy.data.collections),'actions':len(bpy.data.actions),'cameras':len([o for o in s.objects if o.type=='CAMERA'])}},indent=2),encoding='utf-8');print(json.dumps({'phase':8,'completed':len(done),'objects':len(bpy.data.objects),'collections':len(bpy.data.collections)},indent=2))
main()
