"""Phase ten: 100 celestial, jump-lane, encounter, fleet, and production steps."""
import json, math, random, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(sys.argv[sys.argv.index('--')+1]).resolve();OUT=ROOT/'Art'/'SpaceSystems';BLEND=OUT/'SpaceSystems_Master.blend'
PREVIEW=OUT/'SpaceSystems_Phase10_100Steps.png';REPORT=OUT/'SpaceSystems_Phase10_100Steps.json';R=random.Random(10100);done=[]

def col(n):
 c=bpy.data.collections.get(n) or bpy.data.collections.new(n)
 if c.name not in bpy.context.scene.collection.children:bpy.context.scene.collection.children.link(c)
 return c
def move(o,c):
 if o.name not in c.objects:c.objects.link(o)
 for x in list(o.users_collection):
  if x!=c:x.objects.unlink(o)
 return o
def mat(n,color,emit=0,metal=.15,rough=.45):
 m=bpy.data.materials.get(n) or bpy.data.materials.new(n);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
 if emit:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emit
 return m
def sph(n,p,r,m,seg=16):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2,radius=r,location=p);o=bpy.context.object;o.name=n;o.data.materials.append(m);return o
def cube(n,p,sc,m):
 bpy.ops.mesh.primitive_cube_add(location=p);o=bpy.context.object;o.name=n;o.scale=sc;o.data.materials.append(m);return o
def cyl(n,p,r,d,m,rot=(0,0,0),v=12):
 bpy.ops.mesh.primitive_cylinder_add(vertices=v,radius=r,depth=d,location=p,rotation=rot);o=bpy.context.object;o.name=n;o.data.materials.append(m);return o
def tor(n,p,major,minor,m,rot=(0,0,0)):
 bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=32,minor_segments=6,location=p,rotation=rot);o=bpy.context.object;o.name=n;o.data.materials.append(m);return o
def reg(step,n,role,o=None):
 done.append({'step':step,'name':n,'role':role})
 if o:o['phase10_step']=step;o['gameplay_role']=role
def moon(step,system,name,role,pos,radius,surface,glow,target,ring=False):
 root=bpy.data.objects.new(system+'_'+name,None);root.location=pos;root.empty_display_type='SPHERE';root.empty_display_size=radius;target.objects.link(root);reg(step,root.name,role,root)
 body=sph(root.name+'_Body',pos,radius,surface);body.parent=root;body['celestial_class']=role;move(body,target)
 beacon=sph(root.name+'_NavLight',Vector(pos)+Vector((0,0,radius*1.15)),radius*.055,glow);beacon.parent=root;move(beacon,target)
 if ring:
  q=tor(root.name+'_Ring',pos,radius*1.45,radius*.05,surface);q.parent=root;move(q,target)
 root['map_radius_km']=int(radius*1800);root['scan_required']=role in {'anomaly','derelict','biosphere'}
def gate(step,name,pos,role,target,hull,glow,scale=1):
 root=bpy.data.objects.new(name,None);root.location=pos;root.empty_display_type='CIRCLE';target.objects.link(root);reg(step,name,role,root)
 parts=[tor(name+'_Outer',pos,1.35*scale,.14*scale,hull,(math.pi/2,0,0)),tor(name+'_Energy',pos,1.05*scale,.055*scale,glow,(math.pi/2,0,0)),cyl(name+'_PylonA',Vector(pos)+Vector((0,-1.5*scale,0)),.12*scale,1.1*scale,hull),cyl(name+'_PylonB',Vector(pos)+Vector((0,1.5*scale,0)),.12*scale,1.1*scale,hull)]
 for p in parts:p.parent=root;move(p,target)
 root['lane_type']=role;root['arrival_radius']=2200*scale
def capital(step,name,pos,role,target,hull,glow,scale=1):
 root=bpy.data.objects.new(name,None);root.location=pos;root.empty_display_type='CUBE';target.objects.link(root);reg(step,name,role,root)
 parts=[cyl(name+'_Spine',pos,.38*scale,5.5*scale,hull,(0,math.pi/2,0),16),cube(name+'_Dorsal',Vector(pos)+Vector((0,0,.55*scale)),(1.4*scale,.55*scale,.18*scale),hull),cube(name+'_Ventral',Vector(pos)+Vector((0,0,-.5*scale)),(1.1*scale,.42*scale,.14*scale),hull),tor(name+'_Reactor',Vector(pos)+Vector((-.9*scale,0,0)),.55*scale,.12*scale,glow,(0,math.pi/2,0))]
 for p in parts:p.parent=root;move(p,target)
 root['encounter_class']=role;root['combat_radius']=5000
def patrol(step,name,pos,role,target,hull,glow):
 root=bpy.data.objects.new(name,None);root.location=pos;root.empty_display_type='ARROWS';target.objects.link(root);reg(step,name,role,root)
 for j in range(3):
  off=Vector((0,(j-1)*.8,abs(j-1)*-.25));p=Vector(pos)+off
  ship=cyl(name+'_Ship'+str(j+1),p,.12,1.35,hull,(0,math.pi/2,0),10);ship.parent=root;move(ship,target)
  e=sph(name+'_Drive'+str(j+1),p+Vector((-.72,0,0)),.075,glow);e.parent=root;move(e,target)
 root.keyframe_insert(data_path='location',frame=1);root.location+=Vector((R.uniform(28,38),R.uniform(15,26),R.uniform(-5,5)));root.keyframe_insert(data_path='location',frame=840)
def camera(step,n,loc,target,lens=65):
 bpy.ops.object.camera_add(location=loc);o=bpy.context.object;o.name=n;o.data.lens=lens;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();move(o,col('SYS_Cameras'));reg(step,n,'camera',o)

def main():
 s=bpy.context.scene;hull=bpy.data.materials.get('M_StationHull') or mat('M_StationHull',(.12,.16,.2),0,.8,.3)
 rock=mat('M_P10_Rock',(.09,.07,.06),0,0,.82);ice=mat('M_P10_Ice',(.28,.55,.72),0,.05,.3);ocean=mat('M_P10_Ocean',(.01,.13,.32),0,.1,.25);lava=mat('M_P10_Lava',(.32,.018,.003),2,0,.6);bio=mat('M_P10_Bio',(.04,.24,.06),0,.05,.65);gold=mat('M_P10_Gold',(1,.18,.005),18);cyan=mat('M_P10_Cyan',(0,.55,1),18);violet=mat('M_P10_Violet',(.4,.005,1),18);red=mat('M_P10_Red',(1,.005,.001),18)
 anchors={k:(bpy.data.objects.get(n).matrix_world.translation.copy() if bpy.data.objects.get(n) else Vector(f)) for k,n,f in [('Ocean','Ocean_World',(-22,5,0)),('Volcanic','Volcanic_World',(8,-8,0)),('Ice','Ice_World',(-18,-14,0)),('Gas','Ringed_Gas_Giant',(20,12,0))]};anchors['Belt']=Vector((0,29,1))
 system_specs={
 'Ocean':[('Pelagos','ocean',ocean),('Neritic','biosphere',bio),('Brine','ice',ice),('Thalassa','ocean',ocean),('Stormhold','rock',rock),('Abyssal','anomaly',violet),('Coral','biosphere',bio),('TritonReach','ice',ice),('BlueShepherd','ocean',ocean),('DrownedWatch','derelict',rock)],
 'Volcanic':[('Cinder','volcanic',lava),('Basalt','rock',rock),('Pyre','volcanic',lava),('Scoria','resource',rock),('Ember','volcanic',lava),('Char','derelict',rock),('Sulfur','resource',lava),('Caldera','volcanic',lava),('ForgeMoon','industry',rock),('RedShepherd','hazard',lava)],
 'Ice':[('Rime','ice',ice),('Hoarfrost','ice',ice),('GlassMoon','resource',ice),('PaleVault','derelict',ice),('Aurora','anomaly',cyan),('Boreal','biosphere',bio),('Cryostone','ice',ice),('WhiteEcho','anomaly',violet),('Snowblind','hazard',ice),('WinterArchive','science',ice)],
 'Gas':[('ShepherdAlpha','rock',rock),('ShepherdBeta','ice',ice),('Tempest','hazard',rock),('Zephyr','biosphere',bio),('HeliumMoon','resource',ice),('Ringbreaker','rock',rock),('CloudAnchor','industry',rock),('LightningVault','anomaly',violet),('GoldenEye','science',lava),('FarLantern','navigation',ice)],
 'Belt':[('CeresGate','dwarf',rock),('Ironheart','resource',rock),('GreenRock','biosphere',bio),('DeadRelay','derelict',rock),('IceFort','ice',ice),('ProspectorHome','habitat',rock),('SplitStone','hazard',rock),('PurpleShard','anomaly',violet),('TradeRock','commerce',rock),('JumpStone','navigation',ice)]}
 step=1
 for system,specs in system_specs.items():
  c=col('P10_'+system+'MinorWorlds');anchor=anchors[system]
  for i,(name,role,surface) in enumerate(specs):
   a=i/10*math.tau+.18;rad=8.5+(i%3)*2.1;pos=anchor+Vector((math.cos(a)*rad,math.sin(a)*rad,(i%4-1.5)*1.45));moon(step,system,name,role,pos,.38+(i%4)*.13,surface,cyan if i%2 else gold,c,i in {2,7});step+=1
 lanes=[('OceanArrival','civilian',anchors['Ocean']+Vector((-10,-6,3))),('OceanEmergency','rescue',anchors['Ocean']+Vector((9,7,-2))),('OceanCargo','cargo',anchors['Ocean']+Vector((2,-11,1))),('OceanResearch','science',anchors['Ocean']+Vector((-4,10,4))),('ForgeArrival','industrial',anchors['Volcanic']+Vector((-10,-6,2))),('ForgeMilitary','security',anchors['Volcanic']+Vector((10,6,3))),('ForgeOre','cargo',anchors['Volcanic']+Vector((4,-11,-1))),('ForgeEvac','rescue',anchors['Volcanic']+Vector((-5,10,4))),('IceArrival','civilian',anchors['Ice']+Vector((-10,-5,2))),('IceScience','science',anchors['Ice']+Vector((10,5,3))),('IceFreight','cargo',anchors['Ice']+Vector((3,-11,-2))),('IceRescue','rescue',anchors['Ice']+Vector((-5,10,3))),('GasArrival','civilian',anchors['Gas']+Vector((-12,-7,3))),('GasFuel','fuel',anchors['Gas']+Vector((12,7,-2))),('GasResearch','science',anchors['Gas']+Vector((5,-13,5))),('GasStormExit','emergency',anchors['Gas']+Vector((-6,12,1))),('BeltArrival','civilian',anchors['Belt']+Vector((-11,-6,2))),('BeltOre','cargo',anchors['Belt']+Vector((11,6,-2))),('BeltSecurity','security',anchors['Belt']+Vector((4,-12,4))),('BeltSmuggler','covert',anchors['Belt']+Vector((-6,11,-3)))]
 c=col('P10_JumpLaneInfrastructure')
 for name,role,pos in lanes:gate(step,'JumpLane_'+name,pos,role,c,hull,cyan if step%2 else gold,.8+(step%3)*.12);step+=1
 encounters=[('LeviathanWreck','boss_derelict'),('NomadArk','diplomatic'),('RaiderCitadel','combat'),('AncientDreadnought','artifact'),('ColonyExodus','rescue'),('MachineCathedral','anomaly'),('VoidWhaler','hazard'),('CrownCarrier','military'),('PlagueBarge','quarantine'),('WorldSeed','biosphere')]
 c=col('P10_CapitalEncounters')
 for i,(name,role) in enumerate(encounters):capital(step,name,Vector((-40+i*8,44+(i%2)*7,8+(i%3)*2)),role,c,hull,violet if i%2 else red,.75+(i%3)*.18);step+=1
 wings=[('OceanWardens','security'),('ForgeConvoy','cargo'),('IceSurveyWing','science'),('GasRescueWing','rescue'),('BeltProspectors','resource'),('DiplomaticEscort','diplomatic'),('MedicalResponse','medical'),('SalvagePack','salvage'),('JumpInspectors','navigation'),('FrontierPatrol','security')]
 c=col('P10_PatrolWings')
 for i,(name,role) in enumerate(wings):patrol(step,name,Vector((-35+i*7,-38+(i%2)*4,3+(i%3))),role,c,hull,cyan if i%2 else gold);step+=1
 for name,loc,target,lens in [('Camera_P10_OceanMoons',anchors['Ocean']+Vector((20,-22,14)),anchors['Ocean'],58),('Camera_P10_ForgeMoons',anchors['Volcanic']+Vector((20,-21,13)),anchors['Volcanic'],60),('Camera_P10_IceMoons',anchors['Ice']+Vector((19,-22,14)),anchors['Ice'],60),('Camera_P10_GasMoons',anchors['Gas']+Vector((27,-25,17)),anchors['Gas'],55),('Camera_P10_CapitalEncounters',(0,75,28),(0,48,10),62)]:camera(step,name,loc,target,lens);step+=1
 if 'Phase10Celestial' not in s.view_layers:s.view_layers.new('Phase10Celestial')
 reg(step,'Phase10Celestial','view_layer');step+=1
 for c in bpy.data.collections:
  if c.name.startswith('P10_'):c['world_partition_cell']='celestial';c['streaming_priority']=4;c['runtime_optional']=True
 reg(step,'Phase10 world partition metadata','optimization');step+=1
 for c in bpy.data.collections:
  if c.name.startswith('P10_'):
   for o in c.objects:o['lod_group']='Phase10';o['streaming_radius']=5000 if o.type=='EMPTY' else 1600
 reg(step,'Phase10 streaming bounds','optimization');step+=1
 for name,frame in [('P10_MOONS',140),('P10_LANES',300),('P10_CAPITALS',500),('P10_PATROLS',700)]:
  if not s.timeline_markers.get(name):s.timeline_markers.new(name,frame=frame)
 reg(step,'Phase10 cinematic markers','cinematic');step+=1
 if len(done)!=99 or step!=100:raise RuntimeError(f'Phase10 count mismatch: step={step}, entries={len(done)}')
 reg(100,'Phase10 validated save and report','production');ctrl=bpy.data.objects.get('SpaceSystem_MasterController')
 if ctrl:ctrl['phase10_assets']=95;ctrl['phase10_complete']=True
 s['phase10_steps']=100;s['asset_version']='10.0';s.frame_end=max(s.frame_end,840);s.camera=bpy.data.objects.get('Camera_CinematicOverview') or s.camera;s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.filepath=str(PREVIEW)
 bpy.ops.render.render(write_still=True);bpy.ops.wm.save_as_mainfile(filepath=str(BLEND));summary={'objects':len(bpy.data.objects),'collections':len(bpy.data.collections),'actions':len(bpy.data.actions),'cameras':sum(o.type=='CAMERA' for o in s.objects)};REPORT.write_text(json.dumps({'phase':10,'steps':done,'summary':summary},indent=2),encoding='utf-8');print(json.dumps({'phase':10,'completed':len(done),**summary},indent=2))
main()
