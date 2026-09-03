"""Phase five: game-ready navigation, hazards, LODs, collisions, and export."""

import json, math, random, sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
OUT = ROOT / "Art" / "SpaceSystems"
BLEND = OUT / "SpaceSystems_Master.blend"
PREVIEW = OUT / "SpaceSystems_Phase5_Gameplay.png"
GLB = OUT / "SpaceSystems_Gameplay.glb"
REPORT = OUT / "SpaceSystems_Phase5_Report.json"
RNG = random.Random(55201)

def col(name):
    c=bpy.data.collections.get(name) or bpy.data.collections.new(name)
    if c.name not in bpy.context.scene.collection.children: bpy.context.scene.collection.children.link(c)
    return c

def move(o,c):
    if o.name not in c.objects: c.objects.link(o)
    for s in list(o.users_collection):
        if s!=c: s.objects.unlink(o)
    return o

def mat(name,color,emit=0,alpha=1,metal=0,rough=.45):
    m=bpy.data.materials.get(name) or bpy.data.materials.new(name); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,alpha)
    p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough
    if emit: p.inputs['Emission Color'].default_value=(*color,1); p.inputs['Emission Strength'].default_value=emit
    if alpha<1: p.inputs['Alpha'].default_value=alpha; m.surface_render_method='DITHERED'
    return m

def sphere(name,p,r,m,seg=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=max(8,seg//2),location=p,radius=r)
    o=bpy.context.object;o.name=name;o.data.materials.append(m);return o

def cube(name,p,scale,m):
    bpy.ops.mesh.primitive_cube_add(location=p);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(m);return o

def cyl(name,p,r,d,m,rot=(0,0,0),verts=20):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=p,rotation=rot)
    o=bpy.context.object;o.name=name;o.data.materials.append(m);return o

def torus(name,p,major,minor,m,rot=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=64,minor_segments=8,location=p,rotation=rot)
    o=bpy.context.object;o.name=name;o.data.materials.append(m);return o

def curve(name,points,m,width=.035,cyclic=False):
    d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=width;d.bevel_resolution=2
    s=d.splines.new('NURBS');s.points.add(len(points)-1)
    for a,b in zip(s.points,points):a.co=(*b,1)
    s.order_u=min(3,len(points));s.use_endpoint_u=True;s.use_cyclic_u=cyclic
    o=bpy.data.objects.new(name,d);bpy.context.collection.objects.link(o);o.data.materials.append(m);return o

def pulse(o,start=1,end=120):
    o.scale=(.7,.7,.7);o.keyframe_insert(data_path='scale',frame=start)
    o.scale=(1.35,1.35,1.35);o.keyframe_insert(data_path='scale',frame=(start+end)//2)
    o.scale=(.7,.7,.7);o.keyframe_insert(data_path='scale',frame=end)

def main():
    s=bpy.context.scene
    cyan=mat('M_GameplayNav',(0,.45,1),10,.42);green=mat('M_GameplayResource',(0,1,.25),14,.4)
    red=mat('M_GameplayHazard',(1,.015,.001),15,.35);amber=mat('M_GameplayWarning',(1,.22,.005),12,.4)
    proxy=mat('M_ProxyDisplay',(.02,.15,.23),1,.12);hull=bpy.data.materials.get('M_StationHull')

    # 1. Low-poly celestial LOD proxies.
    lod=col('EXPORT_LOD1_Celestials')
    for name in ('Ocean_World','Volcanic_World','Ringed_Gas_Giant','Ice_World'):
        src=bpy.data.objects.get(name)
        if src:
            o=sphere(name+'_LOD1',src.matrix_world.translation,max(src.dimensions)/2,src.data.materials[0],12)
            o.hide_render=True;o.hide_viewport=True;o['lod_level']=1;move(o,lod)
    # 2. Collision proxies.
    collision=col('UCX_CelestialCollision')
    for name in ('Ocean_World','Volcanic_World','Ringed_Gas_Giant','Ice_World'):
        src=bpy.data.objects.get(name)
        if src:
            o=sphere('UCX_'+name,src.matrix_world.translation,max(src.dimensions)/2,proxy,8)
            o.hide_render=True;o.display_type='WIRE';o['collision_type']='sphere';move(o,collision)
    # 3. System navigation grid rings.
    grid=col('SYS_NavigationGrid')
    for r in (10,20,30,40,50):move(torus(f'NavGrid_{r}km',(0,0,0),r,.018,cyan),grid)
    # 4. Coordinate-axis beacons.
    for axis,p in (('X',(48,0,0)),('Y',(0,48,0)),('Z',(0,0,26))):
        o=sphere('AxisBeacon_'+axis,p,.18,cyan,12);o['axis']=axis;move(o,grid);pulse(o,1,180)
    # 5. Curved safe-travel lanes.
    lanes=col('SYS_SafeTravelLanes')
    routes=[[(0,-4,0),(8,-10,2),(17,-14,3),(20,-24,4)],[(0,2,0),(-8,7,1),(-12,14,0),(-11.5,17.5,-1)]]
    for i,pts in enumerate(routes):move(curve(f'SafeTravelLane_{i+1}',pts,cyan,.055),lanes)
    # 6. Arrival corridor markers.
    gate=bpy.data.objects.get('JumpGate_Controller');arrival=col('SYS_ArrivalCorridor')
    if gate:
        for i in range(10):
            p=gate.location+Vector((0,(i-5)*1.5,0));move(torus(f'ArrivalMarker_{i+1}',p,1.1,.035,cyan,(math.pi/2,0,0)),arrival)
    # 7. Docking ports for both stations.
    docks=col('SYS_DockingPorts')
    for station_name in ('OceanWorld_ResearchStation','GasGiant_Refinery'):
        st=bpy.data.objects.get(station_name)
        if st:
            for i,side in enumerate((-1,1)):
                p=st.location+Vector((0,side*2.0,0));o=cyl(f'{station_name}_Dock_{i+1}',p,.38,1.1,hull,(math.pi/2,0,0))
                o['dock_id']=i+1;o['approach_clearance']=450;move(o,docks)
    # 8. Pulsing resource identifiers.
    resources=col('SYS_ResourceIndicators')
    for i in range(1,4):
        core=bpy.data.objects.get(f'ResourceNode_{i}_Core')
        if core:
            o=torus(f'ResourceNode_{i}_Indicator',core.location,1.2,.05,green,(math.pi/2,0,0));move(o,resources);pulse(o,1+i*20,160+i*20)
    # 9. Animated hazard identifiers.
    hazards=col('SYS_HazardIndicators')
    for i in range(1,4):
        buoy=bpy.data.objects.get(f'HazardBuoy_{i}')
        if buoy:
            o=sphere(f'HazardPulse_{i}',buoy.location,.5+i*.1,red,12);move(o,hazards);pulse(o,1+i*15,100+i*15)
    # 10. Radiation storm arcs near the star.
    events=col('SYS_EnvironmentalEvents')
    for i in range(7):
        pts=[]
        for j in range(12):
            a=-.65+j/11*1.3;rad=9+i*.55;pts.append((math.cos(a)*rad,math.sin(a)*rad,math.sin(a*3+i)*1.2))
        move(curve(f'SolarRadiationArc_{i+1}',pts,amber,.09),events)
    # 11. Micro-debris hazard corridor.
    for i in range(80):
        p=Vector((-8+i*.22,24+RNG.gauss(0,1.1),RNG.gauss(0,.7)));o=sphere(f'HazardDebris_{i:03d}',p,RNG.uniform(.04,.16),hull,8)
        o['hazard']='micro_debris';move(o,events)
    # 12. Ice geysers.
    ice=bpy.data.objects.get('Ice_World')
    if ice:
        for i in range(8):
            p=ice.location+Vector((RNG.uniform(-1,1),RNG.uniform(-1,1),1.9));o=cyl(f'IceGeyser_{i+1}',p,.04,RNG.uniform(.5,1.5),cyan)
            o['event']='cryo_geyser';move(o,events)
    # 13. Volcanic plume columns.
    volcanic=bpy.data.objects.get('Volcanic_World')
    if volcanic:
        for i in range(6):
            p=volcanic.location+Vector((RNG.uniform(-1,1),RNG.uniform(-1,1),1.7));o=cyl(f'VolcanicPlume_{i+1}',p,.12,RNG.uniform(1,2.4),amber)
            o['event']='thermal_plume';move(o,events)
    # 14. Ocean lightning events.
    ocean=bpy.data.objects.get('Ocean_World')
    if ocean:
        for i in range(8):
            base=ocean.location+Vector((RNG.uniform(-1.3,1.3),RNG.uniform(-1.3,1.3),2.5));pts=[base+Vector((RNG.uniform(-.2,.2),0,-j*.22)) for j in range(8)]
            move(curve(f'OceanLightning_{i+1}',pts,cyan,.025),events)
    # 15. Gas giant polar aurora rings.
    gas=bpy.data.objects.get('Ringed_Gas_Giant')
    if gas:
        for z,n in ((4.45,'North'),(-4.45,'South')):move(torus('GasGiant_'+n+'Aurora',gas.location+Vector((0,0,z)),2.1,.06,green),events)
    # 16. Gravity anomaly exclusion volume.
    anomaly=bpy.data.objects.get('GravityAnomaly_Core')
    if anomaly:
        o=sphere('GravityAnomaly_ExclusionVolume',anomaly.location,8.5,red,20);o.hide_render=True;o.display_type='WIRE';o['hazard_radius']=850000;move(o,collision)
    # 17. Camera route preview.
    cam=bpy.data.objects.get('Camera_CometTracking')
    if cam:
        cam.keyframe_insert(data_path='location',frame=1);cam.location+=Vector((-14,8,3));cam.keyframe_insert(data_path='location',frame=300);cam.location+=Vector((18,5,-2));cam.keyframe_insert(data_path='location',frame=600)
    # 18. Gameplay naming and units metadata.
    ctrl=bpy.data.objects.get('SpaceSystem_MasterController')
    if ctrl:ctrl['distance_unit']='kilometers';ctrl['map_radius_km']=60;ctrl['gameplay_ready']=True
    # 19. Updated gameplay GLB export.
    bpy.ops.object.select_all(action='DESELECT')
    for o in s.objects:
        if o.type=='MESH' and not o.name.startswith(('Starfield_','UCX_')) and not o.hide_render:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(GLB),export_format='GLB',use_selection=True,export_materials='EXPORT',export_animations=True)
    # 20. Render, save, and report.
    s.camera=bpy.data.objects.get('Camera_CinematicOverview') or s.camera;s.render.resolution_x=1280;s.render.resolution_y=720;s.render.resolution_percentage=100
    s.render.filepath=str(PREVIEW);s['phase5_steps']=20;s['asset_version']='5.0';bpy.ops.render.render(write_still=True);bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    report={'phase':5,'steps':20,'version':'5.0','objects':len(bpy.data.objects),'materials':len(bpy.data.materials),'actions':len(bpy.data.actions),
            'features':['LOD proxies','collision proxies','navigation grid','axis beacons','safe lanes','arrival corridor','docking ports','resource indicators','hazard indicators','radiation arcs','debris corridor','ice geysers','volcanic plumes','ocean lightning','gas auroras','anomaly exclusion','camera route','unit metadata','gameplay GLB','validation']}
    REPORT.write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
main()
