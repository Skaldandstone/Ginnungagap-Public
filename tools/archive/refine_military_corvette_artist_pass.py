"""Add concept-specific artist refinement to the Military Corvette master."""
from pathlib import Path
import json, math, random
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
MASTER=ROOT/"Art/Ships/Exterior/ConceptMatch/FleetCapitalConceptMatch.blend"
OUT=ROOT/"Art/Ships/Exterior/ConceptMatch/MilitaryCorvette"
bpy.ops.wm.open_mainfile(filepath=str(MASTER))
SHIP=bpy.data.collections["SM_Ship_MilitaryCorvette_ConceptMatch"]
rng=random.Random(2400430620)

MAT={
 "hull":bpy.data.materials.get("M_Escort_Armor"), "dark":bpy.data.materials.get("M_Escort_ArmorDark"),
 "frame":bpy.data.materials.get("M_Escort_Structure"), "thermal":bpy.data.materials.get("M_Escort_Thermal"),
 "orange":bpy.data.materials.get("M_Escort_SafetyOrange"), "blue":bpy.data.materials.get("M_Escort_BlueLight"),
 "drive":bpy.data.materials.get("M_Escort_Drive"), "glass":bpy.data.materials.get("M_Escort_Glass"),
}
MAT["hull2"]=MAT["dark"]

def col(name):
    old=bpy.data.collections.get(name)
    if old:
        for o in list(old.objects): bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.collections.remove(old)
    c=bpy.data.collections.new(name); SHIP.children.link(c); return c

def move(o,c):
    for q in list(o.users_collection): q.objects.unlink(o)
    c.objects.link(o); return o

def box(name,loc,size,mat,c,bevel=1.5):
    bpy.ops.mesh.primitive_cube_add(location=loc); o=bpy.context.object; o.name=name; o.scale=tuple(v*.5 for v in size); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(MAT[mat]); move(o,c)
    if bevel: m=o.modifiers.new("EdgeTreatment","BEVEL"); m.width=bevel; m.segments=3
    return o

def cyl(name,loc,r,depth,mat,c,axis="X",verts=20):
    rot=(0,math.pi/2,0) if axis=="X" else ((math.pi/2,0,0) if axis=="Y" else (0,0,0))
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc,rotation=rot); o=bpy.context.object; o.name=name; o.data.materials.append(MAT[mat]); return move(o,c)

def torus(name,loc,major,minor,mat,c,axis="X"):
    rot=(0,math.pi/2,0) if axis=="X" else ((math.pi/2,0,0) if axis=="Y" else (0,0,0))
    bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=24,minor_segments=8,location=loc,rotation=rot); o=bpy.context.object; o.name=name; o.data.materials.append(MAT[mat]); return move(o,c)

def pipe(name,a,b,r,mat,c):
    a,b=Vector(a),Vector(b); d=b-a; bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=d.length,location=(a+b)*.5)
    o=bpy.context.object; o.name=name; o.rotation_mode="QUATERNION"; o.rotation_quaternion=d.to_track_quat('Z','Y'); o.data.materials.append(MAT[mat]); return move(o,c)

def hull_radius(x):
    # Shipping envelope approximation after the concept master normalization.
    t=min(1,abs(x)/1200); taper=max(.12,(1-t**3)**.33)
    return 205*taper,224*taper-12

def side_panel(name,x0,x1,z0,z1,side,mat,c,lift=2.2):
    verts=[]
    for z in (z0,z1):
        for x in (x0,x1):
            hy,hz=hull_radius(x); nz=min(.97,abs((z+12)/max(hz,1))); y=side*(hy*max(.1,(1-nz**3.2)**(1/3.2))+lift); verts.append((x,y,z))
    mesh=bpy.data.meshes.new(name+"_Mesh"); mesh.from_pydata(verts,[],[(0,1,3,2)]); mesh.materials.append(MAT[mat]); mesh.update(); o=bpy.data.objects.new(name,mesh); c.objects.link(o)
    s=o.modifiers.new("ArmorThickness","SOLIDIFY"); s.thickness=2.6; e=o.modifiers.new("RolledEdges","BEVEL"); e.width=.8; e.segments=2; return o

def top_panel(name,x0,x1,y0,y1,mat,c):
    verts=[]
    for y in (y0,y1):
        for x in (x0,x1):
            hy,hz=hull_radius(x); ny=min(.97,abs(y/max(hy,1))); z=-12+hz*max(.1,(1-ny**3.2)**(1/3.2))+2.2; verts.append((x,y,z))
    mesh=bpy.data.meshes.new(name+"_Mesh"); mesh.from_pydata(verts,[],[(0,1,3,2)]); mesh.materials.append(MAT[mat]); mesh.update(); o=bpy.data.objects.new(name,mesh); c.objects.link(o)
    s=o.modifiers.new("ArmorThickness","SOLIDIFY"); s.thickness=2.2; e=o.modifiers.new("RolledEdges","BEVEL"); e.width=.7; e.segments=2; return o

# 111–120: macro armor belts with concept-faithful overlap and shadow gaps.
c=col("P111_120_ConformalArmorBelts")
xs=[-1040,-900,-730,-540,-330,-100,150,390,610,810,980]
for side in (-1,1):
    for band,(z0,z1) in enumerate(((-150,-72),(-64,18),(30,106),(115,174))):
        for i in range(len(xs)-1):
            gap=4.5; side_panel(f"Corvette_Armor_{side}_{band}_{i:02}",xs[i]+gap,xs[i+1]-gap,z0,z1,side,"hull" if (i+band)%6 else "dark",c)
for i in range(len(xs)-1):
    for lane,(y0,y1) in enumerate(((-145,-52),(-45,45),(52,145))): top_panel(f"Corvette_Dorsal_{lane}_{i:02}",xs[i]+5,xs[i+1]-5,y0,y1,"hull" if (i+lane)%5 else "dark",c)

# 121–130: recessed mechanical waist with real depth, buses, exchangers, and access logic.
c=col("P121_130_RecessedMechanicalWaist")
for side in (-1,1):
    y=side*195
    for i,x in enumerate(range(-870,871,145)):
        box(f"WaistVoid_{side}_{i}",(x,y,-48),(112,10,58),"thermal",c,2)
        box(f"WaistFrameTop_{side}_{i}",(x,y+side*5,-16),(120,9,8),"frame",c,1)
        box(f"WaistFrameBottom_{side}_{i}",(x,y+side*5,-80),(120,9,8),"frame",c,1)
        for j,z in enumerate((-64,-48,-32)):
            cyl(f"WaistCanister_{side}_{i}_{j}",(x-32+j*32,y+side*9,z),7,10,"orange" if (i+j)%7==0 else "frame",c,axis="Y",verts=14)
        if i%3==0: box(f"AccessHatch_{side}_{i}",(x,y+side*11,5),(68,5,42),"dark",c,2)
    for row,z in enumerate((-86,-10)):
        pipe(f"LongitudinalBus_{side}_{row}",(-930,y+side*13,z),(930,y+side*13,z),3.2,"orange" if row else "frame",c)

# 131–138: primary hangar becomes an engineered pressure opening.
c=col("P131_138_HangarArchitecture")
for side in (-1,1):
    y=side*180
    for i,x in enumerate(range(100,621,65)):
        box(f"HangarRib_{side}_{i}",(x,y+side*13,-45),(8,18,164),"frame",c,2)
        box(f"HangarCeilingRail_{side}_{i}",(x,y+side*18,31),(46,8,6),"hull",c,1)
        box(f"HangarDeckPlate_{side}_{i}",(x,y+side*18,-119),(54,12,4),"dark",c,.7)
    for z in (-127,43): box(f"HangarMassiveSill_{side}_{z}",(360,y+side*16,z),(590,28,18),"hull2",c,4)
    for x in (65,655): box(f"HangarMassiveJamb_{side}_{x}",(x,y+side*16,-42),(22,28,184),"hull2",c,4)
    for i in range(18): box(f"HangarGuideLight_{side}_{i}",(95+i*30,y+side*32,-111),(9,3,3),"blue" if i%4 else "orange",c,.25)

# 139–145: buried citadel terraces, armored windows, and sensor redundancy.
c=col("P139_145_CitadelRefinement")
for level,(z,sx,sy) in enumerate(((190,430,275),(220,330,220),(247,240,165),(270,145,105))):
    box(f"CitadelArmorTerrace_{level}",(-180,0,z),(sx,sy,30),"hull" if level<2 else "dark",c,6)
    for side in (-1,1):
        for i in range(8): box(f"CitadelWindow_{level}_{side}_{i}",(-180-sx*.32+i*sx*.09,side*(sy*.5+1.5),z+2),(sx*.045,2.2,5),"blue",c,.35)
for i,(x,h) in enumerate(((-230,78),(-180,112),(-120,66))):
    pipe(f"CitadelMast_{i}",(x,0,274),(x,0,min(306,274+h)),2.2,"frame",c)
    torus(f"CitadelRadar_{i}",(x,0,min(307,275+h)),14-i*2,1.4,"hull",c,axis="Z")

# 146–152: 4x4 drive face gains wells, petals, feed trunks, and armored dividers.
c=col("P146_152_DriveFaceRefinement")
for row,z in enumerate((-108,-36,36,108)):
    for column,y in enumerate((-108,-36,36,108)):
        n=row*4+column; torus(f"DriveWell_{n:02}",(-1176,y,z),25,4,"thermal",c); torus(f"DrivePetalRing_{n:02}",(-1183,y,z),21,2.4,"orange" if n in (0,3,12,15) else "hull",c)
        cyl(f"DriveCore_{n:02}",(-1187,y,z),15,3,"drive",c)
        for k in range(4):
            a=math.tau*k/4; pipe(f"DrivePetal_{n:02}_{k}",(-1172,y+math.cos(a)*21,z+math.sin(a)*21),(-1190,y+math.cos(a)*17,z+math.sin(a)*17),1.6,"frame",c)
for y in (-72,0,72): box(f"DriveColumnDivider_{y}",(-1172,y,0),(18,7,270),"frame",c,1)
for z in (-72,0,72): box(f"DriveRowDivider_{z}",(-1172,0,z),(18,270,7),"frame",c,1)

# 153–160: defense terraces and controlled surface storytelling.
c=col("P153_160_DefenseAndStory")
for i,x in enumerate(range(-800,801,160)):
    y=(-1 if i%2 else 1)*92; box(f"DefensePlinth_{i}",(x,y,222),(80,70,14),"dark",c,3); cyl(f"DefenseRace_{i}",(x,y,234),14,8,"frame",c,axis="Z",verts=16)
    box(f"DefenseHousing_{i}",(x,y,244),(38,30,18),"hull",c,3)
    for off in (-5,5): pipe(f"DefenseBarrel_{i}_{off}",(x+12,y+off,247),(x+60,y+off,252),2,"thermal",c)
for side in (-1,1):
    for i in range(24):
        x=-980+i*82; hy,hz=hull_radius(x); z=-135+(i%7)*42; y=side*(min(203,hy)+5)
        if i%5==0: box(f"RepairPlate_{side}_{i}",(x,y,z),(45,4,26),"dark",c,1)
        box(f"WorkLight_{side}_{i}",(x,y+side*3,z+15),(5,2,3),"orange" if i%8==0 else "blue",c,.2)

# Re-export the corvette only.
SHIP["production_passes"]=160; SHIP["latest_pass_range"]="111-160"; SHIP["artist_gate"]="macro and mid-frequency concept match"
bpy.ops.object.select_all(action="DESELECT")
for o in SHIP.all_objects:
    if o.type=="MESH": o.select_set(True)
bpy.context.view_layer.objects.active=next(o for o in SHIP.all_objects if o.type=="MESH")
bpy.ops.export_scene.gltf(filepath=str(OUT/"Exports/SM_Ship_MilitaryCorvette_ConceptMatch.glb"),export_format="GLB",use_selection=True,export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER))
report={"asset":"SM_Ship_MilitaryCorvette_ConceptMatch","passes":"111-160","focus":["conformal armor belts","recessed mechanical waist","hangar pressure architecture","buried citadel","4x4 drive face","defense terraces","surface storytelling"],"dimensions_contract_m":[2400,430,620],"concept":"docs/concept-art/reference/ships/medium-military-corvette-exterior.png"}
(OUT/"MilitaryCorvette_ArtistPass_111_160.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("CORVETTE_ARTIST_PASS_160_COMPLETE")
