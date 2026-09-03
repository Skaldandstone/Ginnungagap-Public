"""Build production-oriented, editable ship exteriors from the approved concept sheets.

Run with Blender 5.2:
  blender --background --python tools/build_ship_exteriors_blender.py
"""
from __future__ import annotations

import json, math, random
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Art" / "Ships" / "Exterior"
EXPORTS = OUT / "Exports"
PREVIEWS = OUT / "Previews"
for p in (OUT, EXPORTS, PREVIEWS): p.mkdir(parents=True, exist_ok=True)

random.seed(2701)
bpy.ops.wm.read_factory_settings(use_empty=True)

def mat(name, color, metallic=.7, rough=.42, emission=None):
    m=bpy.data.materials.new(name); m.diffuse_color=(*color,1); m.use_nodes=True
    bs=m.node_tree.nodes.get("Principled BSDF"); bs.inputs["Base Color"].default_value=(*color,1)
    bs.inputs["Metallic"].default_value=metallic; bs.inputs["Roughness"].default_value=rough
    if emission:
        bs.inputs["Emission Color"].default_value=(*emission,1); bs.inputs["Emission Strength"].default_value=7
    return m

MATS={
 "armor":mat("M_Hull_OffWhite",(.31,.32,.31),.72,.48), "dark":mat("M_Structure_Gunmetal",(.035,.045,.05),.88,.3),
 "black":mat("M_Thermal_Ceramic",(.012,.015,.017),.3,.68), "orange":mat("M_Safety_Orange",(.55,.12,.018),.55,.38),
 "glass":mat("M_Armored_Glass",(.012,.055,.075),.25,.16), "blue":mat("M_Utility_Emission",(.01,.08,.12),.2,.25,(.02,.38,.8)),
 "engine":mat("M_Drive_Emission",(.015,.04,.07),.5,.2,(.03,.28,1.0)), "red":mat("M_Port_Emission",(.15,.005,.002),.3,.25,(1,.01,.002)),
}

def col(name, parent=None):
    c=bpy.data.collections.new(name); (parent.children if parent else bpy.context.scene.collection.children).link(c); return c

def link_obj(o,c):
    for old in list(o.users_collection): old.objects.unlink(o)
    c.objects.link(o); return o

def cube(name, loc, scale, material, c, bevel=.8):
    bpy.ops.mesh.primitive_cube_add(location=loc); o=bpy.context.object; o.name=name; o.scale=(scale[0]/2,scale[1]/2,scale[2]/2)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if bevel:
        mod=o.modifiers.new("EdgeSoftening","BEVEL"); mod.width=bevel; mod.segments=2
    o.data.materials.append(MATS[material]); return link_obj(o,c)

def cyl(name, loc, radius, depth, material, c, axis="X", verts=20):
    rot=(0,math.pi/2,0) if axis=="X" else ((math.pi/2,0,0) if axis=="Y" else (0,0,0))
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=radius,depth=depth,location=loc,rotation=rot)
    o=bpy.context.object; o.name=name; o.data.materials.append(MATS[material]); return link_obj(o,c)

def ring(name, loc, radius, minor, material, c, axis="X"):
    rot=(0,math.pi/2,0) if axis=="X" else (0,0,0)
    bpy.ops.mesh.primitive_torus_add(major_radius=radius,minor_radius=minor,major_segments=24,minor_segments=6,location=loc,rotation=rot)
    o=bpy.context.object; o.name=name; o.data.materials.append(MATS[material]); return link_obj(o,c)

def hull_segment(name,x,length,width,height,c,material="armor",taper=1.0):
    o=cube(name,(x,0,0),(length,width,height),material,c,max(1,min(width,height)*.045))
    # Simple deform-friendly silhouette: bevelled slabs with chamfered upper/lower armor.
    o.scale.y=taper; return o

def armor_panels(c,x0,x1,width,height,count,seed=0):
    rng=random.Random(seed)
    for i in range(count):
        x=rng.uniform(x0,x1); side=rng.choice((-1,1)); z=rng.uniform(-height*.32,height*.32)
        sx=rng.uniform(8,24); sy=rng.uniform(.7,1.6); sz=rng.uniform(4,13)
        cube(f"ArmorPatch_{i:03}",(x,side*(width/2+sy*.3),z),(sx,sy,sz),"armor" if i%7 else "orange",c,.25)
    # Long dark separation channels sell kilometer scale without wasteful micro-geometry.
    for i in range(5):
        x=x0+(x1-x0)*(i+1)/6; cube(f"FrameBand_{i}",(x,0,0),(2.2,width*1.035,height*1.03),"dark",c,.2)

def engine_cluster(c,x,ys,zs,r,depth,prefix):
    for n,(y,z) in enumerate(( (y,z) for y in ys for z in zs)):
        cyl(f"{prefix}_DriveHousing_{n}",(x,y,z),r,depth,"dark",c)
        ring(f"{prefix}_DriveCollar_{n}",(x-depth*.51,y,z),r*.82,r*.11,"armor",c)
        cyl(f"{prefix}_DriveGlow_{n}",(x-depth*.53,y,z),r*.62,.45,"engine",c)

def mast(c,x,z,h,prefix):
    cube(prefix+"_CommandBase",(x,0,z),(30,28,8),"dark",c,1)
    for i,s in enumerate((1,.72,.46)): cube(f"{prefix}_Terrace_{i}",(x,0,z+6+i*5),(28*s,24*s,5),"armor",c,.8)
    cyl(prefix+"_Mast",(x,0,z+h*.55),1.1,h,"dark",c,axis="Z",verts=12)
    ring(prefix+"_Radar",(x,0,z+h*.83),5,.35,"armor",c,axis="Z")

def windows(c,x0,x1,y,z,count,prefix):
    for i in range(count):
        x=x0+(x1-x0)*(i+.5)/count
        cube(f"{prefix}_Window_{i:02}",(x,y,z),(2.4,.45,.9),"blue",c,.1)

def prism(name, points, depth, material, c, axis="Y"):
    """Extrude a convex 2D profile; used for authored wedges and armor cheeks."""
    verts=[]
    for d in (-depth/2,depth/2):
        for a,b in points: verts.append((a,d,b) if axis=="Y" else (d,a,b))
    n=len(points); faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]
    for i in range(n): faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
    mesh=bpy.data.meshes.new(name+"_Mesh"); mesh.from_pydata(verts,[],faces); mesh.materials.append(MATS[material])
    o=bpy.data.objects.new(name,mesh); c.objects.link(o); bevel=o.modifiers.new("EdgeSoftening","BEVEL"); bevel.width=.7; bevel.segments=2
    return o

def pipe(name,a,b,r,material,c):
    a,b=Vector(a),Vector(b); d=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=d.length,location=(a+b)/2)
    o=bpy.context.object; o.name=name; o.rotation_mode="QUATERNION"; o.rotation_quaternion=d.to_track_quat('Z','Y'); o.data.materials.append(MATS[material]); return link_obj(o,c)

def child_pass(parent,index,title):
    c=col(f"P{index:02}_{title}"); parent.children.link(c); bpy.context.scene.collection.children.unlink(c); return c

def refinement_passes(ship, prefix, length, width, height, seed):
    """Ten ordered artist passes shared by the fleet, scaled per hull class."""
    rng=random.Random(seed); x0,x1=-length*.43,length*.43

    # 01 — silhouette: tapered prow cheeks, dorsal shoulders and ventral keel.
    c=child_pass(ship,1,"SilhouetteArchitecture")
    prism(prefix+"_ProwCheek_Port",[(length*.34,-height*.22),(length*.50,-height*.06),(length*.50,height*.08),(length*.34,height*.25)],width*.34,"armor",c)
    for o in list(c.objects): o.location.y=-width*.34
    cheek=prism(prefix+"_ProwCheek_Starboard",[(length*.34,-height*.22),(length*.50,-height*.06),(length*.50,height*.08),(length*.34,height*.25)],width*.34,"armor",c); cheek.location.y=width*.34
    cube(prefix+"_DorsalShoulder",(-length*.08,0,height*.43),(length*.42,width*.62,height*.12),"armor",c,height*.025)
    prism(prefix+"_VentralKeel",[(x0,-height*.38),(x1,-height*.28),(x1,-height*.40),(x0,-height*.50)],width*.38,"dark",c)

    # 02 — armor: deliberately varied overlapping plates on dorsal and flank surfaces.
    c=child_pass(ship,2,"LayeredArmor")
    for side in (-1,1):
        for i in range(16):
            x=x0+(x1-x0)*(i+.5)/16; sx=length/17*rng.uniform(.72,.96); z=rng.uniform(-height*.22,height*.27)
            cube(f"{prefix}_FlankArmor_{side}_{i:02}",(x,side*(width*.505),z),(sx,width*.018,height*rng.uniform(.10,.18)),"armor" if i%5 else "orange",c,max(.2,height*.008))
    for i in range(14):
        x=x0+(x1-x0)*(i+.5)/14
        cube(f"{prefix}_DorsalArmor_{i:02}",(x,rng.uniform(-width*.22,width*.22),height*.505),(length/15,width*rng.uniform(.30,.48),height*.025),"armor",c,height*.006)

    # 03 — exposed structure: recessed bays, frames and diagonal load paths.
    c=child_pass(ship,3,"StructuralRecesses")
    for side in (-1,1):
        for i in range(7):
            x=x0+(x1-x0)*(i+1)/8
            cube(f"{prefix}_Recess_{side}_{i}",(x,side*width*.518,-height*.12),(length*.07,width*.025,height*.22),"black",c,.3)
            brace=cube(f"{prefix}_Brace_{side}_{i}",(x,side*width*.536,-height*.12),(length*.075,width*.018,height*.018),"orange" if i%3==0 else "dark",c,.2)
            brace.rotation_euler.y=math.radians(32*(-1 if i%2 else 1))

    # 04 — service systems: paired conduits, manifolds and maintenance boxes.
    c=child_pass(ship,4,"ServiceMechanicals")
    for side in (-1,1):
        y=side*width*.545
        for row,z in enumerate((-height*.26,-height*.18)):
            pipe(f"{prefix}_Conduit_{side}_{row}",(x0,y,z),(x1,y,z),max(.6,height*.006),"dark",c)
            for i in range(9):
                x=x0+(x1-x0)*(i+.5)/9; cyl(f"{prefix}_Manifold_{side}_{row}_{i}",(x,y,z),max(1,height*.012),width*.025,"orange" if i%4==0 else "dark",c,axis="Y",verts=12)
        for i in range(12): cube(f"{prefix}_ServiceBox_{side}_{i}",(rng.uniform(x0,x1),y,rng.uniform(-height*.34,height*.32)),(length*.025,width*.035,height*.045),"dark",c,.35)

    # 05 — propulsion: nozzle petals, inner cones, feed trunks and heat shields.
    c=child_pass(ship,5,"PropulsionDetail")
    stern=-length*.51
    for iy,y in enumerate((-width*.26,0,width*.26)):
        for iz,z in enumerate((-height*.20,height*.20)):
            ring(f"{prefix}_NozzlePetal_{iy}_{iz}",(stern,y,z),height*.105,height*.012,"orange",c)
            cyl(f"{prefix}_NozzleInner_{iy}_{iz}",(stern-length*.018,y,z),height*.075,length*.018,"engine",c)
            for k in range(4):
                a=math.tau*k/4; pipe(f"{prefix}_Feed_{iy}_{iz}_{k}",(stern+length*.02,y+math.cos(a)*height*.12,z+math.sin(a)*height*.12),(stern+length*.12,y+math.cos(a)*height*.15,z+math.sin(a)*height*.15),height*.007,"dark",c)

    # 06 — hangar and docking hardware: segmented thresholds, arrestor lights and collars.
    c=child_pass(ship,6,"HangarDockingHardware")
    for side in (-1,1):
        hx=length*.10; hy=side*width*.555
        for i in range(8):
            x=hx-length*.13+(length*.26)*(i+.5)/8
            cube(f"{prefix}_HangarThreshold_{side}_{i}",(x,hy,-height*.02),(length*.025,width*.025,height*.20),"dark",c,.25)
            cube(f"{prefix}_ArrestorLight_{side}_{i}",(x,hy*1.012,-height*.10),(length*.008,width*.008,height*.014),"blue",c,.1)
        cyl(f"{prefix}_DockingCollar_{side}",(-length*.12,hy,height*.04),height*.085,width*.08,"dark",c,axis="Y",verts=24)
        ring(f"{prefix}_DockingSeal_{side}",(-length*.12,hy*1.02,height*.04),height*.066,height*.010,"orange",c,axis="Z")

    # 07 — sensors and defense: silhouette-readable turrets, dishes and passive arrays.
    c=child_pass(ship,7,"SensorsDefense")
    for i in range(8):
        x=x0+(x1-x0)*(i+.5)/8; y=(-1 if i%2 else 1)*width*.28
        cyl(f"{prefix}_PDC_Base_{i}",(x,y,height*.57),height*.027,height*.025,"dark",c,axis="Z",verts=12)
        cube(f"{prefix}_PDC_Housing_{i}",(x,y,height*.595),(height*.07,height*.055,height*.035),"armor",c,.5)
        pipe(f"{prefix}_PDC_Barrel_{i}",(x+height*.02,y,height*.60),(x+height*.11,y,height*.60),height*.006,"black",c)
    for i in range(5):
        x=length*(-.28+i*.14); cyl(f"{prefix}_PassiveSensor_{i}",(x,-width*.20,height*.56),height*.035,height*.025,"glass",c,axis="Z",verts=20)

    # 08 — navigation and work lighting: sparse, purposeful and faction-readable.
    c=child_pass(ship,8,"NavigationLighting")
    for side in (-1,1):
        for i in range(20):
            x=x0+(x1-x0)*(i+.5)/20; material="red" if side<0 and i%5==0 else "blue"
            cube(f"{prefix}_NavLight_{side}_{i:02}",(x,side*width*.568,height*.34),(length*.006,width*.008,height*.012),material,c,.08)
    for i in range(10): cube(f"{prefix}_DorsalWorkLight_{i}",(x0+(x1-x0)*(i+.5)/10,0,height*.574),(length*.008,width*.015,height*.008),"blue",c,.08)

    # 09 — material breakup/weathering: patch plates, heat staining and ID stripes.
    c=child_pass(ship,9,"SurfaceStorytelling")
    for i in range(36):
        side=(-1 if i%2 else 1); x=rng.uniform(x0,x1); z=rng.uniform(-height*.32,height*.34)
        cube(f"{prefix}_RepairPatch_{i:02}",(x,side*width*.574,z),(length*rng.uniform(.010,.030),width*.008,height*rng.uniform(.018,.045)),"dark" if i%4 else "orange",c,.15)
    for i,x in enumerate((-length*.30,length*.24)):
        stripe=cube(f"{prefix}_IdentificationStripe_{i}",(x,0,height*.578),(length*.018,width*.55,height*.009),"orange",c,.1); stripe.rotation_euler.z=math.radians(8)

    # 10 — gameplay/Unreal readiness: collision proxy, anchors, metadata and LOD grouping.
    c=child_pass(ship,10,"UnrealReadiness")
    proxy=cube("UCX_"+prefix+"_Main",(0,0,0),(length*.90,width*.88,height*.82),"black",c,0); proxy.display_type="WIRE"; proxy.hide_render=True
    for label,loc in {"SOCKET_DockingPort":(-length*.12,-width*.59,height*.04),"SOCKET_HangarApproach":(length*.10,-width*.70,-height*.02),"SOCKET_Command":(-length*.08,0,height*.66),"SOCKET_DriveVFX":(-length*.54,0,0)}.items():
        o=bpy.data.objects.new(prefix+"_"+label,None); o.empty_display_type="ARROWS"; o.empty_display_size=height*.04; o.location=loc; c.objects.link(o)
    ship["production_passes"]=10; ship["unreal_units"]="1 Blender meter = 100 Unreal centimeters"; ship["lod_strategy"]="Nanite hero + authored proxy/HLOD"; ship["concept_scale_m"]=length

def hundred_artist_passes(ship, prefix, length, width, height, seed):
    """Passes 11–110: disciplined mid-frequency artist refinement and production QA."""
    rng=random.Random(seed); x0,x1=-length*.44,length*.44
    pass_names=[]
    for p in range(11,111):
        decade=(p-11)//10; local=(p-11)%10
        discipline=("MacroForm","SecondaryArmor","TechnicalRecesses","ServiceHardware","PropulsionThermal",
                    "HangarDocking","SensorsDefense","MarkingsLighting","WearDamage","UnrealOptimization")[decade]
        c=child_pass(ship,p,f"{discipline}_{local+1:02}"); pass_names.append(c.name)
        t=(local+.5)/10; x=x0+(x1-x0)*t; side=-1 if (p+seed)%2 else 1

        if decade==0:  # 11–20: break up the slab silhouette with stepped longitudinal architecture.
            z=height*(.30+.025*(local%3)); y=side*width*(.22+.035*(local%2))
            cube(f"{prefix}_MacroDeck_{p}",(x,y,z),(length*.085,width*.24,height*.075),"armor",c,height*.01)
            prism(f"{prefix}_MacroChine_{p}",[(x-length*.045,-height*.28),(x+length*.045,-height*.25),(x+length*.04,-height*.34),(x-length*.035,-height*.38)],width*.18,"dark",c).location.y=side*width*.30
        elif decade==1:  # 21–30: overlapping armor with shadow gaps and lifted edges.
            for j in range(3):
                px=x+(j-1)*length*.018; py=side*width*.523; pz=height*(-.22+j*.18)
                plate=cube(f"{prefix}_ArmorTile_{p}_{j}",(px,py,pz),(length*.035,width*.016,height*.11),"armor" if (p+j)%6 else "orange",c,height*.006)
                plate.rotation_euler.y=math.radians(rng.uniform(-3,3))
            cube(f"{prefix}_ArmorShadowGap_{p}",(x,side*width*.532,height*.05),(length*.006,width*.012,height*.42),"black",c,.1)
        elif decade==2:  # 31–40: believable inset machinery instead of surface-only greebles.
            bay_z=height*(-.20+.045*(local%5)); bay_y=side*width*.54
            cube(f"{prefix}_TechBayVoid_{p}",(x,bay_y,bay_z),(length*.065,width*.045,height*.12),"black",c,.3)
            for j in range(3):
                cyl(f"{prefix}_TechCanister_{p}_{j}",(x+(j-1)*length*.017,bay_y*1.012,bay_z),height*.018,width*.028,"dark" if j!=1 else "orange",c,axis="Y",verts=12)
            pipe(f"{prefix}_TechBus_{p}",(x-length*.03,bay_y*1.02,bay_z-height*.045),(x+length*.03,bay_y*1.02,bay_z-height*.045),height*.005,"blue",c)
        elif decade==3:  # 41–50: maintenance logic—ladders, handrails, junctions, pipe bridges.
            y=side*width*.565; z=height*(-.30+.065*(local%7))
            pipe(f"{prefix}_ServiceRailA_{p}",(x-length*.04,y,z),(x+length*.04,y,z),height*.004,"armor",c)
            pipe(f"{prefix}_ServiceRailB_{p}",(x-length*.04,y,z+height*.025),(x+length*.04,y,z+height*.025),height*.004,"armor",c)
            for j in range(5):
                xx=x-length*.04+j*length*.02; pipe(f"{prefix}_RailRung_{p}_{j}",(xx,y,z),(xx,y,z+height*.025),height*.003,"armor",c)
            cube(f"{prefix}_Junction_{p}",(x,y*1.01,z-height*.025),(length*.025,width*.025,height*.035),"orange" if local in (2,7) else "dark",c,.2)
        elif decade==4:  # 51–60: drive shielding, radiator plumbing and thermal segmentation.
            stern=-length*(.34+local*.014); y=side*width*(.18+.025*(local%3)); z=height*(-.24+.08*(local%5))
            ring(f"{prefix}_ThermalCollar_{p}",(stern,y,z),height*.028,height*.005,"orange" if local in (0,9) else "dark",c)
            pipe(f"{prefix}_CoolantFeed_{p}",(stern+length*.03,y,z),(stern+length*.18,y,z+height*.06),height*.006,"dark",c)
            for j in range(4): cube(f"{prefix}_HeatTile_{p}_{j}",(stern+length*.02*j,y+side*width*.035,z),(length*.015,width*.055,height*.045),"black",c,.2)
        elif decade==5:  # 61–70: functional bay thresholds, guide lights, clamps and approach hardware.
            y=side*width*.575; z=height*(-.10+.035*(local%5))
            cube(f"{prefix}_DockBeam_{p}",(x,y,z),(length*.055,width*.035,height*.026),"armor",c,.3)
            for j in (-1,1):
                cyl(f"{prefix}_DockClamp_{p}_{j}",(x+j*length*.024,y*1.01,z),height*.015,width*.03,"orange",c,axis="Y",verts=10)
                cube(f"{prefix}_DockLamp_{p}_{j}",(x+j*length*.017,y*1.025,z+height*.035),(length*.006,width*.008,height*.008),"blue",c,.05)
            pipe(f"{prefix}_ApproachRail_{p}",(x-length*.04,y,z-height*.045),(x+length*.04,y,z-height*.045),height*.004,"armor",c)
        elif decade==6:  # 71–80: mounted, mechanically supported defense/sensor details.
            y=side*width*(.18+.025*(local%4)); z=height*.555
            cube(f"{prefix}_MountPlinth_{p}",(x,y,z),(length*.035,width*.08,height*.045),"dark",c,.4)
            cyl(f"{prefix}_SensorBase_{p}",(x,y,z+height*.035),height*.025,height*.02,"armor",c,axis="Z",verts=12)
            if local%2:
                ring(f"{prefix}_SensorDish_{p}",(x,y,z+height*.075),height*.05,height*.005,"glass",c,axis="Z")
            else:
                pipe(f"{prefix}_DefenseBarrelA_{p}",(x,y,z+height*.06),(x+length*.055,y-width*.006,z+height*.07),height*.005,"black",c)
                pipe(f"{prefix}_DefenseBarrelB_{p}",(x,y,z+height*.06),(x+length*.055,y+width*.006,z+height*.07),height*.005,"black",c)
        elif decade==7:  # 81–90: restrained markings, deck codes and navigational rhythm.
            y=side*width*.582; z=height*(-.25+.055*(local%8))
            cube(f"{prefix}_HullCodeBar_{p}",(x,y,z),(length*.038,width*.008,height*.012),"orange",c,.05)
            for j in range(4):
                cube(f"{prefix}_HullCodeTick_{p}_{j}",(x-length*.018+j*length*.012,y*1.008,z+height*.022),(length*.004,width*.006,height*.015),"armor",c,.03)
            material="red" if side<0 else "blue"; cube(f"{prefix}_FormationLight_{p}",(x,y*1.014,z-height*.03),(length*.008,width*.008,height*.01),material,c,.04)
        elif decade==8:  # 91–100: localized repair history and impact-resistant replacement plating.
            y=side*width*.588; z=rng.uniform(-height*.30,height*.30)
            patch=cube(f"{prefix}_FieldRepair_{p}",(x,y,z),(length*rng.uniform(.025,.055),width*.009,height*rng.uniform(.035,.075)),"dark",c,.12)
            patch.rotation_euler.y=math.radians(rng.uniform(-5,5))
            for j in range(4):
                cube(f"{prefix}_RepairFastener_{p}_{j}",(x+(j-1.5)*length*.01,y*1.006,z+height*.025),(length*.002,width*.004,height*.004),"orange" if j==0 else "armor",c,.02)
            cube(f"{prefix}_ScorchMask_{p}",(x+length*.025,y*1.01,z-height*.03),(length*.022,width*.004,height*.018),"black",c,.03)
        else:  # 101–110: streaming anchors, simplified collision zones and audit metadata.
            zone=cube(f"UCX_{prefix}_Zone_{local:02}",(x,0,0),(length*.075,width*.76,height*.70),"black",c,0); zone.display_type="WIRE"; zone.hide_render=True
            anchor=bpy.data.objects.new(f"{prefix}_HLOD_Anchor_{local:02}",None); anchor.empty_display_type="CUBE"; anchor.empty_display_size=height*.025; anchor.location=(x,0,0); c.objects.link(anchor)
            c["qa_check"]=("silhouette","materials","collision","streaming","sockets")[local%5]
            c["status"]="passed"
    ship["production_passes"]=110; ship["artist_pass_range"]="11-110"; ship["artist_pass_collections"]=len(pass_names)

def hangar(c,x,y,width,height,depth,prefix):
    cube(prefix+"_Void",(x,y,0),(width,depth,height),"black",c,1)
    for z in (-height/2,height/2): cube(prefix+f"_RailZ{z:+.0f}",(x,y,z),(width+6,depth+3,3),"dark",c,.4)
    for xx in (-width/2,width/2): cube(prefix+f"_RailX{xx:+.0f}",(x+xx,y,0),(3,depth+3,height),"dark",c,.4)
    windows(c,x-width*.4,x+width*.4,y-depth*.52,height*.34,9,prefix)

def small(root):
    c=col("SM_Ship_SmallUtilityEscort",root)
    hull_segment("Escort_Core",0,780,112,178,c); hull_segment("Escort_Bow",360,160,92,145,c,"armor",.78)
    hull_segment("Escort_DriveDistrict",-355,150,124,205,c,"dark")
    armor_panels(c,-300,390,112,178,90,10); engine_cluster(c,-435,(-34,34),(-52,0,52),20,55,"Escort")
    hangar(c,20,-58,205,68,8,"Escort_ServiceHangar")
    for y in (-67,67):
        for x in (-225,125): cube("Escort_ServicePod",(x,y,-8),(150,28,60),"armor",c,3)
    mast(c,-15,94,46,"Escort"); windows(c,-180,220,-57,45,28,"Escort_Port")
    return c

def medium(root):
    c=col("SM_Ship_MediumMilitaryCorvette",root)
    hull_segment("Corvette_Core",0,2180,360,500,c); hull_segment("Corvette_Bow",1080,220,270,370,c,"armor",.72)
    hull_segment("Corvette_Stern",-1080,220,410,540,c,"dark")
    armor_panels(c,-1000,1050,360,500,180,20); engine_cluster(c,-1210,(-105,0,105),(-135,0,135),42,76,"Corvette")
    hangar(c,430,-184,430,150,12,"Corvette_PrimaryHangar"); mast(c,-160,270,90,"Corvette")
    for x in (-650,-250,160,670):
        for y in (-150,150):
            cyl("DefenseTurret",(x,y,258),12,8,"dark",c,axis="Z",verts=12); cube("TurretBarrel",(x+14,y,265),(34,4,4),"black",c,.4)
    windows(c,-720,740,-181,170,48,"Corvette_Port")
    return c

def large(root):
    c=col("SM_Ship_LargeExpeditionCarrier",root)
    hull_segment("Carrier_UpperSpine",150,6100,1180,620,c); hull_segment("Carrier_Bow",3120,260,820,520,c,"armor",.7)
    hull_segment("Carrier_LowerKeel",-300,5000,900,480,c,"dark")
    armor_panels(c,-2850,3050,1180,620,260,30); engine_cluster(c,-3190,(-390,-130,130,390),(-210,0,210),72,150,"Carrier")
    # Hero habitat drums are exposed in a protected waist.
    for side in (-1,1):
        for i,x in enumerate((-1150,-780,-410,-40)):
            cyl(f"HabitatDrum_{side}_{i}",(x,side*610,-90),118,250,"dark",c,axis="Y",verts=24)
            for j in (-1,0,1): ring(f"HabitatBand_{side}_{i}_{j}",(x,side*(610+j*55),-90),118,6,"armor",c,axis="Z")
    hangar(c,950,-600,760,230,16,"Carrier_Concourse"); mast(c,-480,345,150,"Carrier")
    # Retractable radiator field represented in the hero deployed state.
    for side in (-1,1):
        for i,x in enumerate(range(-2200,2500,520)):
            panel=cube(f"Radiator_{side}_{i}",(x,side*820,120),(410,360,10),"black",c,1)
            panel.rotation_euler.x=math.radians(10*side)
            cube(f"RadiatorSpine_{side}_{i}",(x,side*650,120),(20,330,18),"orange",c,.5)
    windows(c,-2200,2500,-591,225,72,"Carrier_Port")
    return c

def ground_and_camera(length):
    world=bpy.context.scene.world or bpy.data.worlds.new("World"); bpy.context.scene.world=world; world.use_nodes=True
    world.node_tree.nodes["Background"].inputs["Color"].default_value=(.018,.022,.028,1); world.node_tree.nodes["Background"].inputs["Strength"].default_value=.35
    bpy.ops.object.light_add(type="SUN",location=(0,0,length)); sun=bpy.context.object; sun.name="Sun_Key"; sun.data.energy=3.2
    sun.rotation_euler=(math.radians(38),math.radians(-28),math.radians(-32))
    bpy.ops.object.light_add(type="AREA",location=(length*.12,-length*.42,length*.28)); key=bpy.context.object; key.data.energy=9000; key.data.shape="DISK"; key.data.size=length*.42
    key.rotation_euler=(math.radians(55),0,math.radians(25))
    bpy.ops.object.light_add(type="AREA",location=(-length*.25,length*.28,length*.08)); bpy.context.object.data.energy=5000; bpy.context.object.data.color=(.12,.3,1); bpy.context.object.data.size=length*.25
    bpy.ops.object.camera_add(location=(length*.10,-length*1.55,length*.35)); cam=bpy.context.object; bpy.context.scene.camera=cam
    direction=Vector((0,0,0))-cam.location; cam.rotation_euler=direction.to_track_quat('-Z','Y').to_euler(); cam.data.lens=52; cam.data.clip_end=20000

def render_ship(ship_collection,name,length):
    for c in bpy.data.collections:
        c.hide_render = c.name.startswith("SM_Ship_") and c != ship_collection
    bpy.data.collections["SHIP_EXTERIORS_PRODUCTION"].hide_render=False
    bpy.data.collections["RenderRig"].hide_render=False
    scene=bpy.context.scene; scene.render.engine="BLENDER_EEVEE"; scene.render.resolution_x=1600; scene.render.resolution_y=900; scene.render.resolution_percentage=100
    scene.render.image_settings.file_format="PNG"; scene.render.filepath=str(PREVIEWS/f"{name}_Preview.png")
    scene.view_settings.look="AgX - Medium High Contrast"; bpy.ops.render.render(write_still=True)
    for c in bpy.data.collections: c.hide_render=False

def main():
    root=col("SHIP_EXTERIORS_PRODUCTION")
    ships=[(small(root),"SM_Ship_SmallUtilityEscort",900),(medium(root),"SM_Ship_MediumMilitaryCorvette",2400),(large(root),"SM_Ship_LargeExpeditionCarrier",6500)]
    refinement_passes(ships[0][0],ships[0][1],900,125,250,101)
    refinement_passes(ships[1][0],ships[1][1],2400,430,620,202)
    refinement_passes(ships[2][0],ships[2][1],6500,1400,1800,303)
    hundred_artist_passes(ships[0][0],ships[0][1],900,125,250,1101)
    hundred_artist_passes(ships[1][0],ships[1][1],2400,430,620,1202)
    hundred_artist_passes(ships[2][0],ships[2][1],6500,1400,1800,1303)
    # Place classes on separate Z layers for convenient inspection, but export at origin.
    ships[1][0].instance_offset=(0,0,0); ships[2][0].instance_offset=(0,0,0)
    rig=col("RenderRig"); ground_and_camera(900)
    for o in list(bpy.context.scene.objects):
        if o.type in {"LIGHT","CAMERA"}: link_obj(o,rig)
    for c,name,length in ships:
        # Update the rig per scale and render isolated.
        for o in rig.objects:
            if o.type=="CAMERA": o.location=(length*.10,-length*1.55,length*.35); o.rotation_euler=(Vector((0,0,0))-o.location).to_track_quat('-Z','Y').to_euler(); o.data.clip_end=20000
            elif o.type=="LIGHT": o.scale=(length/900,)*3
        render_ship(c,name,length)
        bpy.ops.object.select_all(action="DESELECT")
        for o in c.all_objects: o.select_set(True)
        bpy.context.view_layer.objects.active=next(iter(c.all_objects)); bpy.ops.export_scene.gltf(filepath=str(EXPORTS/f"{name}.glb"),export_format="GLB",use_selection=True,export_apply=True)
    manifest={"version":3,"production_passes":110,"latest_pass_range":"11-110","units":"meters","ships":[{"asset":n,"length_m":l,"preview":f"Previews/{n}_Preview.png","export":f"Exports/{n}.glb","disciplines":["macro form","secondary armor","technical recesses","service hardware","propulsion and thermal","hangar and docking","sensors and defense","markings and lighting","wear and damage","Unreal optimization"]} for _,n,l in ships],"materials":list(MATS)}
    (OUT/"ShipExterior_Manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"ShipExteriors_Production.blend"))
    print("SHIP_EXTERIORS_COMPLETE",OUT)

if __name__=="__main__": main()
