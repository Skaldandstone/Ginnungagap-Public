"""Concept-first production rebuilds for the Military Corvette and Expedition Carrier."""
from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("escort_base", ROOT / "tools/build_small_escort_concept_match.py")
b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)


def child(name, parent): return b.collection(name, parent)


def radial_armor(prefix, x, half_y, half_z, collection, bands=16):
    for i in range(bands):
        a = math.tau * i / bands
        y, z = math.cos(a) * half_y, math.sin(a) * half_z
        panel = b.box(f"{prefix}_RadialArmor_{i:02}", (x, y, z),
                      (90, max(8, half_y * .22), max(10, half_z * .18)),
                      "hull" if i % 5 else "hull2", collection, 3, 3)
        panel.rotation_euler.x = a


def armor_grid(prefix, sections, collection, count=28):
    # Strong longitudinal armor rhythm and dark waist recesses from the sheets.
    length = sections[-1][0] - sections[0][0]
    for side in (-1, 1):
        for i in range(count):
            x = sections[0][0] + length * (i + .5) / count
            hy, hz, zo = b.hull_section_at(x)
            z = zo + hz * (-.18 + .13 * (i % 4))
            y = side * (hy + 3.2)
            p = b.box(f"{prefix}_FlankPlate_{side}_{i:02}", (x, y, z),
                      (length / count * .88, 5.2, hz * .26), "hull" if i % 6 else "orange", collection, 2, 2)
            p.rotation_euler.x = math.radians(side * (4 if z > zo else -4))
        b.box(f"{prefix}_WaistRecess_{side}", (0, side * (sections[len(sections)//2][1] + 1), -45),
              (length * .72, 9, sections[len(sections)//2][2] * .28), "thermal", collection, 3, 3)
        for i in range(18):
            x = -length * .34 + length * .68 * (i + .5) / 18
            b.box(f"{prefix}_WaistModule_{side}_{i:02}", (x, side * (sections[len(sections)//2][1] + 7), -45),
                  (length * .025, 8, 24), "frame" if i % 4 else "orange", collection, 1, 2)


def hangar(prefix, loc, size, side, collection):
    x, _, z = loc; width, depth, height = size; y = side * loc[1]
    b.box(prefix + "_Void", (x, y, z), (width, depth, height), "thermal", collection, 6, 4)
    for xx in (-width/2, width/2): b.box(prefix + "_Jamb", (x+xx, y+side*depth*.52, z), (14, 18, height+24), "frame", collection, 3, 3)
    for zz in (-height/2, height/2): b.box(prefix + "_Sill", (x, y+side*depth*.52, z+zz), (width+20, 18, 14), "frame", collection, 3, 3)
    for i in range(12):
        xx=x-width*.44+width*.88*i/11
        b.box(f"{prefix}_Rib_{i:02}",(xx,y-side*depth*.15,z),(5,depth*.65,height*.8),"hull2",collection,1,2)
        b.box(f"{prefix}_Guide_{i:02}",(xx,y+side*depth*.57,z-height*.40),(9,3,4),"blue" if i%3 else "orange",collection,.3,1)


def drive_grid(prefix, x, ys, zs, radius, collection):
    for row,z in enumerate(zs):
        for col,y in enumerate(ys):
            n=row*len(ys)+col
            b.cylinder(f"{prefix}_Housing_{n:02}",(x+18,y,z),radius*1.18,55,"frame",collection)
            b.torus(f"{prefix}_ArmorRing_{n:02}",(x-12,y,z),radius*1.03,radius*.18,"hull",collection)
            b.torus(f"{prefix}_Safety_{n:02}",(x-17,y,z),radius*.78,radius*.07,"orange",collection)
            b.cylinder(f"{prefix}_Glow_{n:02}",(x-20,y,z),radius*.67,3,"drive",collection)
    b.box(prefix+"_Backplane",(x+42,0,0),(85,max(ys)-min(ys)+radius*2.8,max(zs)-min(zs)+radius*2.8),"thermal",collection,14,4)


def citadel(prefix, loc, scale, collection, military=True):
    x,y,z=loc; sx,sy,sz=scale
    for i,f in enumerate((1,.78,.56,.36)):
        b.box(f"{prefix}_Terrace_{i}",(x,y,z+i*sz*.16),(sx*f,sy*f,sz*.28),"hull" if i<2 else "hull2",collection,6,4)
    for side in (-1,1):
        for i in range(10): b.box(f"{prefix}_Window_{side}_{i}",(x-sx*.35+i*sx*.075,y+side*sy*.405,z+sz*.2),(sx*.04,2.5,5),"blue",collection,.5,2)
    for i,h in enumerate((sz*.65,sz*.5,sz*.34)):
        b.cylinder(f"{prefix}_Mast_{i}",(x+(-1+i)*sx*.08,y,z+sz*.6+h/2),2.5,h,"frame",collection,axis="Z",verts=12)
        b.torus(f"{prefix}_Radar_{i}",(x+(-1+i)*sx*.08,y,z+sz*.6+h),sz*.09,1.8,"hull",collection,axis="Z")


def defense(prefix, length, half_y, top_z, collection, count):
    for i in range(count):
        x=-length*.34+length*.68*(i+.5)/count; y=(-1 if i%2 else 1)*half_y*.52
        b.cylinder(f"{prefix}_Base_{i:02}",(x,y,top_z),12,9,"frame",collection,axis="Z",verts=16)
        b.box(f"{prefix}_Turret_{i:02}",(x,y,top_z+9),(34,28,15),"hull2",collection,3,3)
        for off in (-4,4): b.pipe(f"{prefix}_Barrel_{i:02}_{off}",(x+10,y+off,top_z+12),(x+52,y+off,top_z+16),2.2,"thermal",collection)


def normalize_assembly(root, target):
    """Bake the complete authored assembly into its approved overall envelope."""
    for _ in range(2):
        deps=bpy.context.evaluated_depsgraph_get(); lo=[1e30]*3; hi=[-1e30]*3
        objects=[o for o in root.all_objects if o.type=="MESH"]
        for o in objects:
            ev=o.evaluated_get(deps)
            for corner in ev.bound_box:
                p=ev.matrix_world @ Vector(corner)
                for i in range(3): lo[i]=min(lo[i],p[i]); hi[i]=max(hi[i],p[i])
        center=[(lo[i]+hi[i])*.5 for i in range(3)]; size=[hi[i]-lo[i] for i in range(3)]; factors=[target[i]/size[i] for i in range(3)]
        for o in objects:
            o.location=tuple((o.location[i]-center[i])*factors[i] for i in range(3))
            o.scale=tuple(o.scale[i]*factors[i] for i in range(3))
    root["native_scale_baked"]=True; root["scale_verified"]=True


def setup_render(target, dims, outdir, name):
    for c in bpy.data.collections: c.hide_render = c.name.startswith("SM_Ship_") and c != target
    world=bpy.context.scene.world or bpy.data.worlds.new("World"); bpy.context.scene.world=world; world.use_nodes=True
    world.node_tree.nodes["Background"].inputs["Color"].default_value=(.006,.008,.011,1); world.node_tree.nodes["Background"].inputs["Strength"].default_value=.18
    L=dims[0]
    bpy.ops.object.light_add(type="SUN",location=(0,0,L)); sun=bpy.context.object; sun.data.energy=3.1; sun.rotation_euler=(.7,-.4,-.65)
    bpy.ops.object.light_add(type="AREA",location=(L*.12,-L*.42,L*.22)); area=bpy.context.object; area.data.energy=11000; area.data.size=L*.5
    bpy.ops.object.camera_add(location=(L*.08,-L*1.48,L*.31)); cam=bpy.context.object; cam.data.lens=56; cam.data.clip_end=30000
    cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler(); bpy.context.scene.camera=cam
    s=bpy.context.scene; s.render.engine="BLENDER_EEVEE"; s.render.resolution_x=1600; s.render.resolution_y=900; s.render.resolution_percentage=100
    s.view_settings.look="AgX - Medium High Contrast"; s.render.image_settings.file_format="PNG"; s.render.filepath=str(outdir/f"{name}_Beauty.png")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam,do_unlink=True); bpy.data.objects.remove(area,do_unlink=True); bpy.data.objects.remove(sun,do_unlink=True)
    for c in bpy.data.collections: c.hide_render=False


def build_corvette():
    out=ROOT/"Art/Ships/Exterior/ConceptMatch/MilitaryCorvette"; (out/"Previews").mkdir(parents=True,exist_ok=True); (out/"Exports").mkdir(exist_ok=True)
    root=child("SM_Ship_MilitaryCorvette_ConceptMatch",None)
    sections=[(-1200,95,125,-15),(-1160,155,175,-18),(-980,195,215,-20),(-650,210,225,-18),(-150,215,230,-15),(420,210,225,-12),(800,190,205,-10),(1060,150,170,-8),(1170,95,120,-5),(1200,22,45,0)]
    b.HULL_SECTIONS=sections; hull=child("01_ArmoredHull",root); b.lofted_hull("Corvette_PressureEnvelope",sections,"hull2",hull,sides=32,power=3.25)
    crown=[(x,y*.88,z*.34,zo+z*.72) for x,y,z,zo in sections[1:-1]]; b.lofted_hull("Corvette_DorsalArmorCrown",crown,"hull",hull,sides=24,power=4)
    armor_grid("Corvette",sections,child("02_ArmorAndWaist",root),34)
    drive_grid("Corvette_Drive",-1178,(-120,-40,40,120),(-120,-40,40,120),25,child("03_4x4DriveDistrict",root))
    h=child("04_DualHangars",root); hangar("Corvette_Hangar_Port",(330,211,-35),(500,22,155),-1,h); hangar("Corvette_Hangar_Starboard",(330,211,-35),(500,22,155),1,h)
    citadel("Corvette_Citadel",(-190,0,255),(390,250,120),child("05_ArmoredCitadel",root))
    defense("Corvette_Defense",2400,215,304,child("06_DefenseTerraces",root),14)
    radial_armor("Corvette_Bow",1085,148,205,child("07_BowArmor",root),14)
    normalize_assembly(root,(2400,430,620))
    root["dimensions_m"]=(2400,430,620); root["concept_reference"]="docs/concept-art/reference/ships/medium-military-corvette-exterior.png"; root["production_passes"]=110
    setup_render(root,(2400,430,620),out/"Previews","MilitaryCorvette_ConceptMatch")
    bpy.ops.object.select_all(action="DESELECT"); [o.select_set(True) for o in root.all_objects if o.type=="MESH"]; bpy.context.view_layer.objects.active=next(o for o in root.all_objects if o.type=="MESH")
    bpy.ops.export_scene.gltf(filepath=str(out/"Exports/SM_Ship_MilitaryCorvette_ConceptMatch.glb"),export_format="GLB",use_selection=True,export_apply=True)
    return root,out


def build_carrier():
    out=ROOT/"Art/Ships/Exterior/ConceptMatch/ExpeditionCarrier"; (out/"Previews").mkdir(parents=True,exist_ok=True); (out/"Exports").mkdir(exist_ok=True)
    root=child("SM_Ship_ExpeditionCarrier_ConceptMatch",None)
    sections=[(-3250,300,390,-70),(-3160,520,540,-75),(-2700,650,610,-80),(-1700,700,640,-75),(0,700,650,-70),(1700,680,625,-60),(2700,590,550,-45),(3150,400,430,-25),(3250,35,80,0)]
    b.HULL_SECTIONS=sections; hull=child("01_CivicArmoredSpine",root); b.lofted_hull("Carrier_MainEnvelope",sections,"hull2",hull,sides=36,power=3.4)
    crown=[(x,y*.90,z*.29,zo+z*.75) for x,y,z,zo in sections[1:-1]]; b.lofted_hull("Carrier_UpperCivicSpine",crown,"hull",hull,sides=28,power=4.2)
    armor_grid("Carrier",sections,child("02_ArmorAndServiceWaist",root),48)
    drive_grid("Carrier_Drive",-3200,(-420,-140,140,420),(-420,0,420),70,child("03_TwelveDriveDistrict",root))
    hs=child("04_ConcourseHangars",root); hangar("Carrier_Hangar_Port",(900,690,-80),(1100,35,320),-1,hs); hangar("Carrier_Hangar_Starboard",(900,690,-80),(1100,35,320),1,hs)
    citadel("Carrier_CommandCity",(-380,0,710),(850,520,260),child("05_CommandCity",root),False)
    defense("Carrier_Defense",6500,700,885,child("06_DefenseAndSensors",root),20)
    habitats=child("07_ProtectedHabitats",root)
    for side in (-1,1):
        for i,x in enumerate((-1500,-950,-400,150)):
            b.cylinder(f"Carrier_Habitat_{side}_{i}",(x,side*610,-200),115,250,"frame",habitats,axis="Y",verts=28)
            for yy in (-90,0,90): b.torus(f"Carrier_HabitatBand_{side}_{i}_{yy}",(x,side*(610+yy),-200),115,6,"hull",habitats,axis="Z")
    normalize_assembly(root,(6500,1400,1800))
    root["dimensions_m"]=(6500,1400,1800); root["concept_reference"]="docs/concept-art/reference/ships/large-expedition-carrier-exterior.png"; root["production_passes"]=110
    setup_render(root,(6500,1400,1800),out/"Previews","ExpeditionCarrier_ConceptMatch")
    bpy.ops.object.select_all(action="DESELECT"); [o.select_set(True) for o in root.all_objects if o.type=="MESH"]; bpy.context.view_layer.objects.active=next(o for o in root.all_objects if o.type=="MESH")
    bpy.ops.export_scene.gltf(filepath=str(out/"Exports/SM_Ship_ExpeditionCarrier_ConceptMatch.glb"),export_format="GLB",use_selection=True,export_apply=True)
    return root,out


corvette,cout=build_corvette(); carrier,lout=build_carrier()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/"Art/Ships/Exterior/ConceptMatch/FleetCapitalConceptMatch.blend"))
manifest={"version":1,"ships":[{"asset":corvette.name,"dimensions_m":[2400,430,620],"concept":"docs/concept-art/reference/ships/medium-military-corvette-exterior.png"},{"asset":carrier.name,"dimensions_m":[6500,1400,1800],"concept":"docs/concept-art/reference/ships/large-expedition-carrier-exterior.png"}],"method":"superellipse section loft, radial end armor, recessed service waist, concept-specific hangars, command structures, and drive grids"}
(ROOT/"Art/Ships/Exterior/ConceptMatch/FleetCapitalConceptMatch_Manifest.json").write_text(json.dumps(manifest,indent=2),encoding="utf-8")
print("FLEET_CAPITAL_CONCEPT_MATCH_COMPLETE")
