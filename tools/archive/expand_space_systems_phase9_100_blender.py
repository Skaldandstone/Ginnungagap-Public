"""Phase nine: 100 additional orbital, encounter, fleet, and production steps."""
import json, math, random, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(sys.argv[sys.argv.index('--') + 1]).resolve()
OUT = ROOT / 'Art' / 'SpaceSystems'
BLEND = OUT / 'SpaceSystems_Master.blend'
PREVIEW = OUT / 'SpaceSystems_Phase9_100Steps.png'
REPORT = OUT / 'SpaceSystems_Phase9_100Steps.json'
R = random.Random(9100)
done = []

def collection(name):
    c = bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(c)
    return c

def move(obj, target):
    if obj.name not in target.objects:
        target.objects.link(obj)
    for c in list(obj.users_collection):
        if c != target:
            c.objects.unlink(obj)
    return obj

def material(name, color, emission=0, metallic=.2, roughness=.35):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    p = m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Metallic'].default_value = metallic
    p.inputs['Roughness'].default_value = roughness
    if emission:
        p.inputs['Emission Color'].default_value = (*color, 1)
        p.inputs['Emission Strength'].default_value = emission
    return m

def cube(name, pos, scale, mat):
    bpy.ops.mesh.primitive_cube_add(location=pos)
    o = bpy.context.object; o.name = name; o.scale = scale; o.data.materials.append(mat)
    return o

def sphere(name, pos, radius, mat, segments=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=max(6, segments // 2), location=pos, radius=radius)
    o = bpy.context.object; o.name = name; o.data.materials.append(mat)
    return o

def cylinder(name, pos, radius, depth, mat, rotation=(0,0,0), vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth, location=pos, rotation=rotation)
    o = bpy.context.object; o.name = name; o.data.materials.append(mat)
    return o

def torus(name, pos, major, minor, mat, rotation=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=32, minor_segments=6, location=pos, rotation=rotation)
    o = bpy.context.object; o.name = name; o.data.materials.append(mat)
    return o

def register(step, name, role, obj=None):
    done.append({'step': step, 'name': name, 'role': role})
    if obj:
        obj['phase9_step'] = step; obj['gameplay_role'] = role

def installation(step, prefix, pos, role, target, hull, light, scale=.34, style=0):
    root = bpy.data.objects.new(prefix, None); root.location = pos; root.empty_display_type = 'CUBE'; root.empty_display_size = scale
    target.objects.link(root); register(step, prefix, role, root)
    parts = []
    if style % 3 == 0:
        parts += [cube(prefix+'_Core', pos, (scale,.65*scale,.45*scale), hull), torus(prefix+'_Dock', pos, 1.25*scale,.09*scale,hull,(math.pi/2,0,0))]
    elif style % 3 == 1:
        parts += [cylinder(prefix+'_Spine',pos,.22*scale,2.7*scale,hull,(0,math.pi/2,0)), sphere(prefix+'_Hub',pos,.48*scale,hull,10)]
    else:
        parts += [cube(prefix+'_Truss',pos,(1.25*scale,.13*scale,.13*scale),hull), cylinder(prefix+'_Tower',pos,.16*scale,1.8*scale,hull)]
    parts += [sphere(prefix+'_Beacon',Vector(pos)+Vector((0,0,.75*scale)),.13*scale,light,10)]
    for p in parts: p.parent=root; move(p,target)
    return root

def vessel(step, name, pos, role, target, hull, light, scale=.4):
    root=bpy.data.objects.new(name,None); root.location=pos; root.empty_display_type='ARROWS'; target.objects.link(root); register(step,name,role,root)
    parts=[cylinder(name+'_Fuselage',pos,.25*scale,2.6*scale,hull,(0,math.pi/2,0)),
           cube(name+'_Port',Vector(pos)+Vector((0,.48*scale,0)),(.65*scale,.22*scale,.06*scale),hull),
           cube(name+'_Starboard',Vector(pos)+Vector((0,-.48*scale,0)),(.65*scale,.22*scale,.06*scale),hull),
           sphere(name+'_Drive',Vector(pos)+Vector((-1.35*scale,0,0)),.16*scale,light,10)]
    for p in parts:p.parent=root;move(p,target)
    root.keyframe_insert(data_path='location',frame=1)
    root.location += Vector((R.uniform(18,30),R.uniform(10,22),R.uniform(-4,4)))
    root.keyframe_insert(data_path='location',frame=720)

def add_camera(step,name,loc,target,lens):
    bpy.ops.object.camera_add(location=loc);o=bpy.context.object;o.name=name;o.data.lens=lens
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();move(o,collection('SYS_Cameras'));register(step,name,'camera',o)

def main():
    s=bpy.context.scene
    hull=bpy.data.materials.get('M_StationHull') or material('M_StationHull',(.12,.16,.2),0,.75,.3)
    cyan=material('M_P9_NavCyan',(0,.55,1),18); gold=material('M_P9_TradeGold',(1,.25,.01),16)
    mint=material('M_P9_BioMint',(0,1,.28),14); violet=material('M_P9_AnomalyViolet',(.45,.01,1),18)
    red=material('M_P9_DangerRed',(1,.005,.002),18); white=material('M_P9_IceWhite',(.65,.85,1),16)
    anchors={}
    for key,name,fallback in [('Ocean','Ocean_World',(-22,5,0)),('Volcanic','Volcanic_World',(8,-8,0)),('Ice','Ice_World',(-18,-14,0)),('Gas','Ringed_Gas_Giant',(20,12,0))]:
        o=bpy.data.objects.get(name); anchors[key]=o.matrix_world.translation.copy() if o else Vector(fallback)
    anchors['Belt']=Vector((0,29,1)); anchors['Deep']=Vector((-32,30,9))

    networks=[
      ('Ocean',anchors['Ocean'],cyan,[('OrbitalFerry','transit'),('WeatherShield','protection'),('KelpFreighter','cargo'),('TideObservatory','science'),('RescueConstellation','rescue'),('HabitatSpindle','habitat'),('DefenseBuoy','security'),('WaterExchange','commerce'),('CloudFoundry','industry'),('JumpApproach','navigation'),('MoonletRelay','communications'),('PilgrimDock','passenger'),('CurrentMapper','science'),('OrbitalGarden','food')]),
      ('Volcanic',anchors['Volcanic'],gold,[('ForgeStation','industry'),('MagmaFreighter','cargo'),('SolarShade','protection'),('AshRefinery','resource'),('HeatSinkArray','power'),('MiningHabitat','habitat'),('FlareWatch','hazard_monitor'),('CinderDock','transport'),('FoundryRing','construction'),('EmergencyLifeboat','rescue'),('OreExchange','commerce'),('SeismicRelay','science'),('DefensePlatform','security'),('JumpBeacon','navigation')]),
      ('Ice',anchors['Ice'],white,[('CryoFreighter','cargo'),('AuroraMirror','science'),('ThermalGrid','power'),('VaultEscort','security'),('CometDock','transport'),('WaterExchange','commerce'),('ResearchSpindle','science'),('RescueBeacon','rescue'),('IceBreakerPort','logistics'),('PolarHabitat','habitat'),('FaultLidar','hazard_monitor'),('SampleCourier','mission'),('JumpLantern','navigation'),('SeedBank','food')]),
      ('Gas',anchors['Gas'],gold,[('CloudHarvester','resource'),('StormSkimmer','science'),('FloatingBorough','habitat'),('RingMine','resource'),('PressureDock','transport'),('FuelExchange','commerce'),('CycloneWatch','hazard_monitor'),('MagneticSail','power'),('RescueBalloon','rescue'),('JumpGateTender','navigation'),('HeliumBarge','cargo'),('CloudGarden','food'),('DefenseKite','security'),('RelayCrown','communications')]),
      ('Belt',anchors['Belt'],mint,[('ClaimBeacon','navigation'),('RockHopperPort','transport'),('OreMarket','commerce'),('DrillSwarmControl','resource'),('HabitatCluster','habitat'),('TugDepot','logistics'),('SmelterSpine','industry'),('RescueCage','rescue'),('PirateWatch','security'),('IceBroker','commerce'),('SurveyLantern','science'),('MassDriverRelay','transport'),('SalvageExchange','salvage'),('ProspectorMemorial','landmark')])]
    step=1
    for zone,anchor,light,items in networks:
        c=collection('P9_'+zone+'OrbitalNetwork')
        for idx,(name,role) in enumerate(items):
            angle=idx/len(items)*math.tau; radius=4.8+(idx%3)*.8
            pos=anchor+Vector((math.cos(angle)*radius,math.sin(angle)*radius,(idx%5-2)*.38))
            installation(step,zone+'_'+name,pos,role,c,hull,light,.3+(idx%3)*.025,idx);step+=1

    encounters=[('PlasmaReef','energy'),('GravitonMaze','gravity'),('DerelictConvoy','salvage'),('CrystalBloom','exobiology'),('DarkMatterPool','anomaly'),('ShatteredMoon','debris'),('SolarProminence','thermal'),('TemporalShoal','time'),('RogueComet','cryo'),('SilentGraveyard','distress')]
    c=collection('P9_EncounterZones')
    for idx,(name,role) in enumerate(encounters):
        pos=anchors['Deep']+Vector(((idx%5)*7,(idx//5)*9,math.sin(idx)*3));root=bpy.data.objects.new('Encounter_'+name,None);root.location=pos;root.empty_display_type='SPHERE';c.objects.link(root);register(step,'Encounter_'+name,role,root)
        for j in range(8):
            a=j/8*math.tau; p=pos+Vector((math.cos(a)*(1.5+idx*.08),math.sin(a)*(1.5+idx*.08),R.uniform(-.7,.7)))
            q=sphere(name+'_Node_'+str(j+1),p,.12+R.random()*.2,violet if idx%2 else red,8);q.parent=root;move(q,c)
        root['encounter_radius']=3200+idx*250;root['runtime_optional']=True;step+=1

    fleet=[('DiplomaticClipper','diplomatic'),('HospitalFrigate','medical'),('HeavyOreCarrier','cargo'),('ScienceCruiser','science'),('JumpRescueShip','rescue'),('FleetTanker','fuel'),('SystemPatrol','security'),('PacketRunner','communications'),('OrbitalConstructor','construction'),('DeepSalvager','salvage')]
    c=collection('P9_SystemFleet')
    for idx,(name,role) in enumerate(fleet):
        vessel(step,name,Vector((-28+idx*5,-30+(idx%2)*3,2+(idx%3))),role,c,hull,cyan if idx%2 else gold,.42+(idx%3)*.06);step+=1

    camera_specs=[('Camera_P9_OceanNetwork',anchors['Ocean']+Vector((12,-13,8)),anchors['Ocean'],68),('Camera_P9_ForgeOrbit',anchors['Volcanic']+Vector((11,-12,7)),anchors['Volcanic'],72),('Camera_P9_IceNetwork',anchors['Ice']+Vector((12,-10,7)),anchors['Ice'],72),('Camera_P9_GasNetwork',anchors['Gas']+Vector((17,-16,10)),anchors['Gas'],65),('Camera_P9_EncounterField',(-2,52,22),anchors['Deep']+Vector((14,5,0)),58)]
    for name,loc,target,lens in camera_specs:add_camera(step,name,loc,target,lens);step+=1

    if 'Phase9Gameplay' not in s.view_layers:s.view_layers.new('Phase9Gameplay')
    register(step,'Phase9Gameplay','view_layer');step+=1
    for c in bpy.data.collections:
        if c.name.startswith('P9_'):c['streaming_priority']=3;c['runtime_optional']=True;c['phase']='9'
    register(step,'Phase9 collection streaming','optimization');step+=1
    for c in bpy.data.collections:
        if c.name.startswith('P9_'):
            for o in c.objects:o['streaming_radius']=3500 if o.type=='EMPTY' else 1200;o['lod_group']='Phase9'
    register(step,'Phase9 LOD metadata','optimization');step+=1
    for name,frame in [('P9_OCEAN',120),('P9_FORGE',240),('P9_ICE',360),('P9_GAS',480),('P9_ENCOUNTERS',600)]:
        if not s.timeline_markers.get(name):s.timeline_markers.new(name,frame=frame)
    register(step,'Phase9 cinematic markers','cinematic');step+=1
    if len(done)!=99 or step!=100:raise RuntimeError(f'Expected step 100 with 99 entries, got step={step}, entries={len(done)}')
    register(100,'Phase9 validated save and report','production')
    ctrl=bpy.data.objects.get('SpaceSystem_MasterController')
    if ctrl:ctrl['phase9_assets']=95;ctrl['phase9_complete']=True
    s['phase9_steps']=100;s['asset_version']='9.0';s.frame_end=max(s.frame_end,720)
    s.camera=bpy.data.objects.get('Camera_CinematicOverview') or s.camera
    s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100;s.render.filepath=str(PREVIEW)
    bpy.ops.render.render(write_still=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    summary={'objects':len(bpy.data.objects),'collections':len(bpy.data.collections),'actions':len(bpy.data.actions),'cameras':len([o for o in s.objects if o.type=='CAMERA'])}
    REPORT.write_text(json.dumps({'phase':9,'steps':done,'summary':summary},indent=2),encoding='utf-8')
    print(json.dumps({'phase':9,'completed':len(done),**summary},indent=2))

main()
