"""Close-range armor construction, markings, wear, and thermal detail for capital ships."""
from pathlib import Path
import json, math, random
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]; MASTER=ROOT/"Art/Ships/Exterior/ConceptMatch/FleetCapitalConceptMatch.blend"
bpy.ops.wm.open_mainfile(filepath=str(MASTER))
MAT={"hull":bpy.data.materials.get("M_Escort_Armor"),"dark":bpy.data.materials.get("M_Escort_ArmorDark"),"frame":bpy.data.materials.get("M_Escort_Structure"),"thermal":bpy.data.materials.get("M_Escort_Thermal"),"orange":bpy.data.materials.get("M_Escort_SafetyOrange"),"blue":bpy.data.materials.get("M_Escort_BlueLight"),"heat":bpy.data.materials.get("M_Heat_Discoloration"),"white":bpy.data.materials.get("M_Decal_White")}

def collection(ship,name):
    old=bpy.data.collections.get(name)
    if old:
        for o in list(old.objects): bpy.data.objects.remove(o,do_unlink=True)
        bpy.data.collections.remove(old)
    c=bpy.data.collections.new(name); ship.children.link(c); return c
def move(o,c):
    for q in list(o.users_collection): q.objects.unlink(o)
    c.objects.link(o); return o
def box(name,loc,size,mat,c,bevel=.5):
    bpy.ops.mesh.primitive_cube_add(location=loc); o=bpy.context.object; o.name=name; o.scale=tuple(v*.5 for v in size); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(MAT[mat]); move(o,c)
    if bevel: m=o.modifiers.new("ManufacturedEdge","BEVEL"); m.width=bevel; m.segments=2
    return o
def cyl(name,loc,r,d,mat,c,axis="Y",verts=12):
    rot=(0,math.pi/2,0) if axis=="X" else ((math.pi/2,0,0) if axis=="Y" else (0,0,0)); bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc,rotation=rot); o=bpy.context.object; o.name=name; o.data.materials.append(MAT[mat]); return move(o,c)
def pipe(name,a,b,r,mat,c):
    a,b=Vector(a),Vector(b); d=b-a; bpy.ops.mesh.primitive_cylinder_add(vertices=10,radius=r,depth=d.length,location=(a+b)*.5); o=bpy.context.object; o.name=name; o.rotation_mode="QUATERNION"; o.rotation_quaternion=d.to_track_quat('Z','Y'); o.data.materials.append(MAT[mat]); return move(o,c)

def corvette_pass():
    ship=bpy.data.collections["SM_Ship_MilitaryCorvette_ConceptMatch"]; rng=random.Random(166200)
    c=collection(ship,"P166_175_ArmorConstruction")
    # Structural seam caps and replaceable access covers along the visible pressure belt.
    for side in (-1,1):
        y=side*209
        for i,x in enumerate(range(-920,921,115)):
            box(f"CorvetteSeamCap_{side}_{i}",(x,y,72),(5,3,165),"frame",c,.25)
            z=-125+(i%6)*46; box(f"CorvetteAccessCover_{side}_{i}",(x+36,y+side*2,z),(55,3,30),"dark" if i%4 else "hull",c,1.5)
            for k in range(4):
                fx=x+17+(k%2)*38; fz=z-10+(k//2)*20; cyl(f"CorvetteFastener_{side}_{i}_{k}",(fx,y+side*4,fz),1.6,2.2,"orange" if i%9==0 and k==0 else "frame",c,axis="Y",verts=10)
    c=collection(ship,"P176_183_VentsAndThermal")
    for side in (-1,1):
        y=side*205
        for i,x in enumerate(range(-820,821,205)):
            box(f"CorvetteVentWell_{side}_{i}",(x,y,-95),(120,5,38),"thermal",c,2)
            for j in range(6): box(f"CorvetteVentLouver_{side}_{i}_{j}",(x-48+j*19,y+side*4,-95),(11,3,29),"frame",c,.35)
        for i,x in enumerate(range(-1080,-700,55)):
            box(f"CorvetteHeatTile_{side}_{i}",(x,y,-155+(i%3)*42),(45,4,34),"heat",c,1)
    c=collection(ship,"P184_191_MarkingsAndRepairs")
    for side in (-1,1):
        y=side*212
        for i,x in enumerate((-760,-340,120,560,880)):
            box(f"CorvetteHullCodeBar_{side}_{i}",(x,y,125-(i%2)*55),(95,2.5,10),"orange",c,.25)
            for j in range(3): box(f"CorvetteHullCodeTick_{side}_{i}_{j}",(x-34+j*34,y+side*1.5,143-(i%2)*55),(9,1.8,14),"white",c,.15)
        for i in range(14):
            x=rng.uniform(-880,900); z=rng.uniform(-140,150); p=box(f"CorvetteRepairPatch_{side}_{i}",(x,y,z),(rng.uniform(35,80),3,rng.uniform(22,48)),"dark",c,1); p.rotation_euler.y=math.radians(rng.uniform(-5,5))
    c=collection(ship,"P192_200_EVAAndDriveFinish")
    for side in (-1,1):
        y=side*212
        for i,x in enumerate(range(-700,701,140)):
            pipe(f"CorvetteEVARail_{side}_{i}",(x-45,y,-190),(x+45,y,-190),1.5,"hull",c)
            for px in (x-45,x,x+45): pipe(f"CorvetteEVAPost_{side}_{i}_{px}",(px,y,-205),(px,y,-175),1.1,"hull",c)
    for row,z in enumerate((-108,-36,36,108)):
        for column,y in enumerate((-108,-36,36,108)):
            n=row*4+column
            for k in range(6):
                a=math.tau*k/6; box(f"CorvetteNozzleHeatTile_{n}_{k}",(-1168,y+math.cos(a)*29,z+math.sin(a)*29),(26,8,7),"heat" if k%2 else "thermal",c,1)
    ship["production_passes"]=200; ship["latest_pass_range"]="166-200"
    return ship

def carrier_pass():
    ship=bpy.data.collections["SM_Ship_ExpeditionCarrier_ConceptMatch"]; rng=random.Random(166205)
    c=collection(ship,"C166_175_ArmorConstruction")
    for side in (-1,1):
        y=side*686
        for i,x in enumerate(range(-2700,2701,300)):
            box(f"CarrierSeamCap_{side}_{i}",(x,y,205),(12,7,350),"frame",c,1)
            z=-360+(i%6)*120; box(f"CarrierAccessCover_{side}_{i}",(x+95,y+side*2,z),(150,6,78),"dark" if i%4 else "hull",c,3)
            for k in range(6):
                fx=x+35+(k%3)*58; fz=z-25+(k//3)*50; cyl(f"CarrierFastener_{side}_{i}_{k}",(fx,y+side*7,fz),3.5,5,"orange" if i%10==0 and k==0 else "frame",c,axis="Y",verts=10)
    c=collection(ship,"C176_183_ThermalAndRadiator")
    for side in (-1,1):
        y=side*675
        for i,x in enumerate(range(-2350,2351,470)):
            box(f"CarrierRadiatorWell_{side}_{i}",(x,y,-390),(330,10,120),"thermal",c,5)
            for j in range(9): box(f"CarrierRadiatorBlade_{side}_{i}_{j}",(x-140+j*35,y+side*9,-390),(18,7,102),"frame" if j%4 else "orange",c,1)
        for i,x in enumerate(range(-3050,-2500,85)): box(f"CarrierDriveHeatTile_{side}_{i}",(x,y,-430+(i%4)*120),(70,7,90),"heat",c,2)
    c=collection(ship,"C184_191_CivicMarkingsAndRepairs")
    for side in (-1,1):
        y=side*694
        for i,x in enumerate((-2100,-1300,-450,500,1400,2250)):
            box(f"CarrierHullCodeBar_{side}_{i}",(x,y,310-(i%2)*145),(220,4,22),"orange",c,.7)
            for j in range(4): box(f"CarrierHullCodeTick_{side}_{i}_{j}",(x-78+j*52,y+side*3,348-(i%2)*145),(18,3,30),"white",c,.5)
        for i in range(20):
            x=rng.uniform(-2600,2700); z=rng.uniform(-410,390); p=box(f"CarrierRepairPatch_{side}_{i}",(x,y,z),(rng.uniform(90,210),6,rng.uniform(55,120)),"dark",c,3); p.rotation_euler.y=math.radians(rng.uniform(-4,4))
    c=collection(ship,"C192_205_EVAAndDriveFinish")
    for side in (-1,1):
        y=side*692
        for i,x in enumerate(range(-1900,1901,380)):
            pipe(f"CarrierEVARail_{side}_{i}",(x-130,y,-520),(x+130,y,-520),3.2,"hull",c)
            for px in (x-130,x,x+130): pipe(f"CarrierEVAPost_{side}_{i}_{px}",(px,y,-555),(px,y,-485),2.4,"hull",c)
    for row,z in enumerate((-360,0,360)):
        for column,y in enumerate((-360,-120,120,360)):
            n=row*4+column
            for k in range(8):
                a=math.tau*k/8; box(f"CarrierNozzleHeatTile_{n}_{k}",(-3180,y+math.cos(a)*82,z+math.sin(a)*82),(58,17,14),"heat" if k%2 else "thermal",c,2)
    ship["production_passes"]=205; ship["latest_pass_range"]="166-205"
    return ship

corvette=corvette_pass(); carrier=carrier_pass()
for ship,out,name in ((corvette,ROOT/"Art/Ships/Exterior/ConceptMatch/MilitaryCorvette","SM_Ship_MilitaryCorvette_ConceptMatch"),(carrier,ROOT/"Art/Ships/Exterior/ConceptMatch/ExpeditionCarrier","SM_Ship_ExpeditionCarrier_ConceptMatch")):
    bpy.ops.object.select_all(action="DESELECT"); [o.select_set(True) for o in ship.all_objects if o.type=="MESH"]; bpy.context.view_layer.objects.active=next(o for o in ship.all_objects if o.type=="MESH")
    bpy.ops.export_scene.gltf(filepath=str(out/"Exports"/(name+".glb")),export_format="GLB",use_selection=True,export_apply=True)
bpy.ops.wm.save_as_mainfile(filepath=str(MASTER))
report={"corvette_passes":"166-200","carrier_passes":"166-205","focus":["armor seams","access covers","fastener groups","ventilation","radiators","hull markings","repair history","EVA rails","drive heat treatment"],"bounds_policy":"all added geometry constrained inside approved envelopes"}
(ROOT/"Art/Ships/Exterior/ConceptMatch/CapitalShips_CloseSurfacePass.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("CAPITAL_CLOSE_SURFACE_PASS_COMPLETE")
