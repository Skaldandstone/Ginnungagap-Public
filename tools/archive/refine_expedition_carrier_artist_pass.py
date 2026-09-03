"""Add concept-specific artist refinement to the Expedition Carrier master."""
from pathlib import Path
import json, math
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]; MASTER=ROOT/"Art/Ships/Exterior/ConceptMatch/FleetCapitalConceptMatch.blend"; OUT=ROOT/"Art/Ships/Exterior/ConceptMatch/ExpeditionCarrier"
bpy.ops.wm.open_mainfile(filepath=str(MASTER)); SHIP=bpy.data.collections["SM_Ship_ExpeditionCarrier_ConceptMatch"]
MAT={"hull":bpy.data.materials.get("M_Escort_Armor"),"dark":bpy.data.materials.get("M_Escort_ArmorDark"),"frame":bpy.data.materials.get("M_Escort_Structure"),"thermal":bpy.data.materials.get("M_Escort_Thermal"),"orange":bpy.data.materials.get("M_Escort_SafetyOrange"),"blue":bpy.data.materials.get("M_Escort_BlueLight"),"drive":bpy.data.materials.get("M_Escort_Drive"),"glass":bpy.data.materials.get("M_Escort_Glass")}

def col(name):
    old=bpy.data.collections.get(name)
    if old:
        for o in list(old.objects): bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.collections.remove(old)
    c=bpy.data.collections.new(name); SHIP.children.link(c); return c
def move(o,c):
    for q in list(o.users_collection): q.objects.unlink(o)
    c.objects.link(o); return o
def box(name,loc,size,mat,c,bev=4):
    bpy.ops.mesh.primitive_cube_add(location=loc); o=bpy.context.object; o.name=name; o.scale=tuple(v*.5 for v in size); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(MAT[mat]); move(o,c)
    if bev: m=o.modifiers.new("EdgeTreatment","BEVEL"); m.width=bev; m.segments=3
    return o
def cyl(name,loc,r,d,mat,c,axis="X",verts=24):
    rot=(0,math.pi/2,0) if axis=="X" else ((math.pi/2,0,0) if axis=="Y" else (0,0,0)); bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc,rotation=rot); o=bpy.context.object; o.name=name; o.data.materials.append(MAT[mat]); return move(o,c)
def torus(name,loc,major,minor,mat,c,axis="X"):
    rot=(0,math.pi/2,0) if axis=="X" else ((math.pi/2,0,0) if axis=="Y" else (0,0,0)); bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=28,minor_segments=8,location=loc,rotation=rot); o=bpy.context.object; o.name=name; o.data.materials.append(MAT[mat]); return move(o,c)
def pipe(name,a,b,r,mat,c):
    a,b=Vector(a),Vector(b); d=b-a; bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=d.length,location=(a+b)*.5); o=bpy.context.object; o.name=name; o.rotation_mode="QUATERNION"; o.rotation_quaternion=d.to_track_quat('Z','Y'); o.data.materials.append(MAT[mat]); return move(o,c)
def radii(x):
    t=min(1,abs(x)/3250); taper=max(.1,(1-t**3)**.32); return 680*taper,650*taper-70
def side_panel(name,x0,x1,z0,z1,side,mat,c):
    vs=[]
    for z in (z0,z1):
        for x in (x0,x1):
            hy,hz=radii(x); nz=min(.97,abs((z+70)/max(hz,1))); y=side*(hy*max(.12,(1-nz**3.3)**(1/3.3))+5); vs.append((x,y,z))
    me=bpy.data.meshes.new(name+"_Mesh"); me.from_pydata(vs,[],[(0,1,3,2)]); me.materials.append(MAT[mat]); me.update(); o=bpy.data.objects.new(name,me); c.objects.link(o); s=o.modifiers.new("PlateThickness","SOLIDIFY"); s.thickness=7; e=o.modifiers.new("RolledEdge","BEVEL"); e.width=2.2; e.segments=2
def top_panel(name,x0,x1,y0,y1,mat,c):
    vs=[]
    for y in (y0,y1):
        for x in (x0,x1):
            hy,hz=radii(x); ny=min(.97,abs(y/max(hy,1))); z=-70+hz*max(.12,(1-ny**3.3)**(1/3.3))+6; vs.append((x,y,z))
    me=bpy.data.meshes.new(name+"_Mesh"); me.from_pydata(vs,[],[(0,1,3,2)]); me.materials.append(MAT[mat]); me.update(); o=bpy.data.objects.new(name,me); c.objects.link(o); s=o.modifiers.new("PlateThickness","SOLIDIFY"); s.thickness=6; e=o.modifiers.new("RolledEdge","BEVEL"); e.width=2; e.segments=2

# 111–120 — civic-scale conformal armor fields.
c=col("C111_120_ConformalArmorFields"); xs=[-2950,-2620,-2260,-1870,-1460,-1020,-560,-80,420,930,1450,1940,2380,2750,3040]
for side in (-1,1):
    for band,(z0,z1) in enumerate(((-420,-245),(-225,-50),(-30,150),(175,345))):
        for i in range(len(xs)-1): side_panel(f"CarrierArmor_{side}_{band}_{i:02}",xs[i]+10,xs[i+1]-10,z0,z1,side,"hull" if (i+band)%7 else "dark",c)
for lane,(y0,y1) in enumerate(((-480,-180),(-160,160),(180,480))):
    for i in range(len(xs)-1): top_panel(f"CarrierDorsal_{lane}_{i:02}",xs[i]+12,xs[i+1]-12,y0,y1,"hull" if (i+lane)%6 else "dark",c)

# 121–130 — deep service waist and kilometer-readable structural rhythm.
c=col("C121_130_ServiceWaist");
for side in (-1,1):
    y=side*645
    for i,x in enumerate(range(-2550,2551,300)):
        box(f"CarrierWaistVoid_{side}_{i}",(x,y,-170),(245,24,155),"thermal",c,5); box(f"CarrierWaistFrame_{side}_{i}",(x,y+side*16,-82),(265,18,18),"frame",c,2)
        for j,z in enumerate((-215,-170,-125)): cyl(f"CarrierWaistTank_{side}_{i}_{j}",(x-70+j*70,y+side*25,z),20,28,"orange" if (i+j)%9==0 else "frame",c,axis="Y",verts=16)
    for z in (-265,-65): pipe(f"CarrierServiceBus_{side}_{z}",(-2700,y+side*35,z),(2700,y+side*35,z),8,"orange" if z==-65 else "frame",c)

# 131–140 — paired concourse hangars with pressure ribs, cranes, and approach lights.
c=col("C131_140_ConcourseHangars")
for side in (-1,1):
    y=side*610
    for i,x in enumerate(range(300,1651,120)):
        box(f"CarrierHangarRib_{side}_{i}",(x,y+side*38,-120),(14,40,330),"frame",c,3); box(f"CarrierCraneRail_{side}_{i}",(x,y+side*52,20),(90,20,10),"hull",c,2)
        box(f"CarrierDeckPlate_{side}_{i}",(x,y+side*54,-278),(102,35,7),"dark",c,1)
    for z in (-295,58): box(f"CarrierHangarSill_{side}_{z}",(970,y+side*40,z),(1500,65,28),"dark",c,7)
    for x in (205,1735): box(f"CarrierHangarJamb_{side}_{x}",(x,y+side*40,-118),(34,65,380),"dark",c,7)
    for i in range(28): box(f"CarrierApproachLight_{side}_{i}",(260+i*52,y+side*78,-268),(14,5,5),"orange" if i%6==0 else "blue",c,.5)

# 141–150 — command city, observation galleries, sensor crown.
c=col("C141_150_CommandCity")
for level,(z,sx,sy,sz) in enumerate(((500,1120,650,90),(580,860,520,82),(650,620,390,72),(715,420,275,62),(770,240,165,48))):
    box(f"CommandCityTerrace_{level}",(-420,0,z),(sx,sy,sz),"hull" if level<3 else "dark",c,12)
    for side in (-1,1):
        for i in range(14): box(f"ObservationGallery_{level}_{side}_{i}",(-420-sx*.4+i*sx*.062,side*(sy*.5+3),z+3),(sx*.035,5,10),"blue",c,1)
for i,(x,h) in enumerate(((-570,110),(-440,145),(-300,95),(-170,80))):
    pipe(f"CarrierSensorMast_{i}",(x,0,790),(x,0,min(884,790+h)),5,"frame",c); torus(f"CarrierRadar_{i}",(x,0,min(888,794+h)),28-i*3,3,"hull",c,axis="Z")

# 151–157 — protected habitat district with windows, transfer trunks, and armor eyebrows.
c=col("C151_157_HabitatDistrict")
for side in (-1,1):
    for i,x in enumerate((-1600,-1100,-600,-100,400)):
        cyl(f"HabitatDrumHero_{side}_{i}",(x,side*585,-210),105,190,"frame",c,axis="Y",verts=32)
        for yoff in (-65,0,65): torus(f"HabitatBandHero_{side}_{i}_{yoff}",(x,side*(585+yoff),-210),105,7,"hull",c,axis="Y")
        for k in range(10):
            a=math.tau*k/10; box(f"HabitatWindow_{side}_{i}_{k}",(x+math.cos(a)*92,side*683,-210+math.sin(a)*92),(13,5,8),"blue",c,1)
        box(f"HabitatEyebrow_{side}_{i}",(x,side*600,-85),(260,120,24),"hull",c,6)
        pipe(f"HabitatTransfer_{side}_{i}",(x,side*470,-210),(x,side*585,-210),12,"orange" if i==2 else "frame",c)

# 158–165 — twelve-drive face, thermal shutters, and defense terraces.
c=col("C158_165_DriveDefense")
for row,z in enumerate((-360,0,360)):
    for column,y in enumerate((-360,-120,120,360)):
        n=row*4+column; torus(f"CarrierDriveWell_{n:02}",(-3190,y,z),72,10,"thermal",c); torus(f"CarrierDriveArmor_{n:02}",(-3210,y,z),61,8,"hull",c); cyl(f"CarrierDriveCore_{n:02}",(-3223,y,z),43,5,"drive",c)
        for k in range(6):
            a=math.tau*k/6; pipe(f"CarrierDrivePetal_{n:02}_{k}",(-3185,y+math.cos(a)*61,z+math.sin(a)*61),(-3230,y+math.cos(a)*48,z+math.sin(a)*48),4,"frame",c)
for i,x in enumerate(range(-2300,2301,330)):
    y=(-1 if i%2 else 1)*300; box(f"CarrierDefensePlinth_{i}",(x,y,635),(150,120,28),"dark",c,6); cyl(f"CarrierDefenseRace_{i}",(x,y,659),28,18,"frame",c,axis="Z",verts=18); box(f"CarrierDefenseHousing_{i}",(x,y,682),(75,58,34),"hull",c,5)
    for off in (-10,10): pipe(f"CarrierDefenseBarrel_{i}_{off}",(x+25,y+off,688),(x+125,y+off,702),4,"thermal",c)

SHIP["production_passes"]=165; SHIP["latest_pass_range"]="111-165"; SHIP["artist_gate"]="macro and mid-frequency concept match"
bpy.ops.object.select_all(action="DESELECT"); [o.select_set(True) for o in SHIP.all_objects if o.type=="MESH"]; bpy.context.view_layer.objects.active=next(o for o in SHIP.all_objects if o.type=="MESH")
bpy.ops.export_scene.gltf(filepath=str(OUT/"Exports/SM_Ship_ExpeditionCarrier_ConceptMatch.glb"),export_format="GLB",use_selection=True,export_apply=True); bpy.ops.wm.save_as_mainfile(filepath=str(MASTER))
(OUT/"ExpeditionCarrier_ArtistPass_111_165.json").write_text(json.dumps({"asset":SHIP.name,"passes":"111-165","focus":["conformal armor fields","deep service waist","concourse hangars","command city","protected habitats","twelve-drive face","defense terraces"],"dimensions_contract_m":[6500,1400,1800]},indent=2),encoding="utf-8")
print("CARRIER_ARTIST_PASS_165_COMPLETE")
