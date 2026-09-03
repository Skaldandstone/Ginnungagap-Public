"""Artist-directed macro/secondary-form pass for the decluttered capital ships."""
from pathlib import Path
import json, math
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"Art/Ships/Exterior/ConceptMatch/Decluttered/FleetCapitalConceptMatch_Decluttered_Textured.blend"
OUT=ROOT/"Art/Ships/Exterior/ConceptMatch/ArtistV2"; OUT.mkdir(parents=True,exist_ok=True); (OUT/"Previews").mkdir(exist_ok=True); (OUT/"Exports").mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
MAT={"hull":bpy.data.materials["M_Escort_Armor"],"dark":bpy.data.materials["M_Escort_ArmorDark"],"frame":bpy.data.materials["M_Escort_Structure"],"thermal":bpy.data.materials["M_Escort_Thermal"],"orange":bpy.data.materials["M_Escort_SafetyOrange"],"blue":bpy.data.materials["M_Escort_BlueLight"],"drive":bpy.data.materials["M_Escort_Drive"]}

def remove_collection(name):
    c=bpy.data.collections.get(name)
    if not c:return 0
    count=len(list(c.all_objects))
    for o in list(c.all_objects): bpy.data.objects.remove(o,do_unlink=True)
    bpy.data.collections.remove(c); return count
removed=sum(remove_collection(n) for n in ("P111_120_ConformalArmorBelts","P153_160_DefenseAndStory","C111_120_ConformalArmorFields","C158_165_DriveDefense"))

def col(ship,name): c=bpy.data.collections.new(name); ship.children.link(c); return c
def move(o,c):
    for q in list(o.users_collection): q.objects.unlink(o)
    c.objects.link(o); return o
def box(name,loc,size,mat,c,bevel=2):
    bpy.ops.mesh.primitive_cube_add(location=loc); o=bpy.context.object; o.name=name; o.scale=tuple(v*.5 for v in size); bpy.ops.object.transform_apply(location=False,rotation=False,scale=True); o.data.materials.append(MAT[mat]); move(o,c)
    if bevel:m=o.modifiers.new("HandFinishedEdge","BEVEL");m.width=bevel;m.segments=3
    return o
def cyl(name,loc,r,d,mat,c,axis="Z",verts=20):
    rot=(0,math.pi/2,0) if axis=="X" else ((math.pi/2,0,0) if axis=="Y" else (0,0,0)); bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=d,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.data.materials.append(MAT[mat]);return move(o,c)
def torus(name,loc,major,minor,mat,c,axis="X"):
    rot=(0,math.pi/2,0) if axis=="X" else ((math.pi/2,0,0) if axis=="Y" else (0,0,0)); bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=28,minor_segments=8,location=loc,rotation=rot);o=bpy.context.object;o.name=name;o.data.materials.append(MAT[mat]);return move(o,c)
def pipe(name,a,b,r,mat,c):
    a,b=Vector(a),Vector(b);d=b-a;bpy.ops.mesh.primitive_cylinder_add(vertices=12,radius=r,depth=d.length,location=(a+b)*.5);o=bpy.context.object;o.name=name;o.rotation_mode="QUATERNION";o.rotation_quaternion=d.to_track_quat('Z','Y');o.data.materials.append(MAT[mat]);return move(o,c)

def plate(name,points,mat,c,thickness,bevel):
    """Extruded authored polygon; points are ordered surface coordinates."""
    n=len(points); verts=list(points)+[(x,y+(thickness if y>=0 else -thickness),z) for x,y,z in points]
    faces=[tuple(range(n-1,-1,-1)),tuple(range(n,n*2))]
    for i in range(n):j=(i+1)%n;faces.append((i,j,j+n,i+n))
    me=bpy.data.meshes.new(name+"_Mesh");me.from_pydata(verts,[],faces);me.materials.append(MAT[mat]);me.update();o=bpy.data.objects.new(name,me);c.objects.link(o);e=o.modifiers.new("ArmorEdge","BEVEL");e.width=bevel;e.segments=3;return o

def corvette_surface(x,z,side):
    t=min(1,abs(x)/1200); hy=207*max(.12,(1-t**3)**.33); hz=226*max(.12,(1-t**3)**.33); nz=min(.97,abs((z+12)/max(hz,1))); return side*(hy*max(.12,(1-nz**3.4)**(1/3.4))+1.5)
def carrier_surface(x,z,side):
    t=min(1,abs(x)/3250);hy=683*max(.10,(1-t**3)**.32);hz=656*max(.10,(1-t**3)**.32);nz=min(.97,abs((z+70)/max(hz,1)));return side*(hy*max(.12,(1-nz**3.3)**(1/3.3))+3)

def shaped_side_armor(ship,prefix,xs,bands,surface,thickness,bevel):
    c=col(ship,prefix+"_BespokeArmorComposition")
    for side in (-1,1):
        for band,(z0,z1) in enumerate(bands):
            for i in range(len(xs)-1):
                x0,x1=xs[i]+5,xs[i+1]-5; cham=min((x1-x0)*.16,(z1-z0)*.25)
                # Alternating chamfer placement creates a designed interlocking rhythm.
                if (i+band)%2==0: outline=[(x0+cham,z0),(x1,z0),(x1,z1-cham),(x1-cham,z1),(x0,z1),(x0,z0+cham)]
                else: outline=[(x0,z0),(x1-cham,z0),(x1,z0+cham),(x1,z1),(x0+cham,z1),(x0,z1-cham)]
                points=[(x,surface(x,z,side),z) for x,z in outline]
                plate(f"{prefix}_Armor_{side}_{band}_{i:02}",points,"dark" if (i+2*band)%9==0 else "hull",c,thickness,bevel)
    return c

def corvette_artist():
    ship=bpy.data.collections["SM_Ship_MilitaryCorvette_ConceptMatch"]
    shaped_side_armor(ship,"Corvette",[-1050,-890,-700,-485,-250,0,255,500,730,920,1070],[(-160,-68),(-55,38),(52,142)],corvette_surface,2.4,.9)
    c=col(ship,"Corvette_ArtistSilhouette")
    # Broad shoulder caps visually integrate citadel and pressure hull.
    for side in (-1,1):
        cap=box(f"Corvette_ShoulderCap_{side}",(-165,side*112,184),(620,145,34),"hull",c,7);cap.rotation_euler.x=math.radians(side*5)
        pipe(f"Corvette_ContinuousChine_{side}",(-930,side*192,-125),(910,side*188,-118),3.2,"frame",c)
    # Hangar reads as one dominant framed void, not many equal ribs.
    for side in (-1,1):
        y=side*194; box(f"Corvette_HangarVoidHero_{side}",(350,y,-48),(575,24,150),"thermal",c,8)
        for x,z,sx,sz in ((60,-48,26,190),(640,-48,26,190),(350,35,610,25),(350,-132,610,25)):box(f"Corvette_HangarFrameHero_{side}_{x}_{z}",(x,y+side*13,z),(sx,30,sz),"dark",c,5)
        for i in range(11):box(f"Corvette_HangarLightHero_{side}_{i}",(100+i*50,y+side*30,-114),(10,3,3),"blue" if i not in (0,10) else "orange",c,.3)
    # Curated defense: eight readable mounts, each with clear support and firing arc.
    for i,x in enumerate((-760,-520,-280,-40,210,450,690,880)):
        y=(-1 if i%2 else 1)*88;z=236;cyl(f"Corvette_DefenseRaceHero_{i}",(x,y,z),12,8,"frame",c);box(f"Corvette_DefenseHero_{i}",(x,y,z+11),(34,28,15),"dark",c,3);pipe(f"Corvette_DefenseBarrelHero_{i}",(x+10,y,z+13),(x+55,y,z+18),2,"thermal",c)
    # Drive face gets a strong perimeter and four grouped quadrants.
    box("Corvette_DrivePerimeterTop",(-1160,0,142),(48,272,18),"dark",c,5);box("Corvette_DrivePerimeterBottom",(-1160,0,-142),(48,272,18),"dark",c,5)
    for side in (-1,1):box(f"Corvette_DrivePerimeterSide_{side}",(-1160,side*142,0),(48,18,300),"dark",c,5)
    ship["artist_version"]="v2";ship["art_direction"]="fewer bespoke plates, dominant hangar, curated defense"

def carrier_artist():
    ship=bpy.data.collections["SM_Ship_ExpeditionCarrier_ConceptMatch"]
    shaped_side_armor(ship,"Carrier",[-2920,-2580,-2200,-1770,-1310,-820,-310,220,760,1300,1810,2260,2650,2960],[(-450,-245),(-220,5),(35,265)],carrier_surface,6,2.2)
    c=col(ship,"Carrier_ArtistSilhouette")
    # Long civic shoulders and command-city plinth unify the kilometer-scale mass.
    for side in (-1,1):
        cap=box(f"Carrier_CivicShoulder_{side}",(-300,side*355,548),(2500,330,55),"hull",c,14);cap.rotation_euler.x=math.radians(side*4)
        pipe(f"Carrier_ContinuousChine_{side}",(-2700,side*650,-360),(2700,side*642,-340),8,"frame",c)
    for level,(z,sx,sy,sz) in enumerate(((545,1180,680,75),(620,880,510,68),(690,610,360,60),(752,380,230,50),(805,190,125,38))):box(f"Carrier_CommandTerraceHero_{level}",(-420,0,z),(sx,sy,sz),"hull" if level<3 else "dark",c,12)
    # Two vast hangar mouths, framed as civic infrastructure.
    for side in (-1,1):
        y=side*625;box(f"Carrier_HangarVoidHero_{side}",(980,y,-125),(1450,40,330),"thermal",c,15)
        for x,z,sx,sz in ((240,-125,45,400),(1720,-125,45,400),(980,58,1530,42),(980,-308,1530,42)):box(f"Carrier_HangarFrameHero_{side}_{x}_{z}",(x,y+side*25,z),(sx,58,sz),"dark",c,10)
        for i in range(19):box(f"Carrier_HangarLightHero_{side}_{i}",(330+i*72,y+side*58,-285),(16,5,5),"blue" if i%6 else "orange",c,.5)
    # Deliberately sparse capital defense rhythm.
    for i,x in enumerate((-2200,-1650,-1100,-550,0,550,1100,1650,2200)):
        y=(-1 if i%2 else 1)*280;z=650;cyl(f"Carrier_DefenseRaceHero_{i}",(x,y,z),25,14,"frame",c);box(f"Carrier_DefenseHero_{i}",(x,y,z+20),(72,58,30),"dark",c,6);pipe(f"Carrier_DefenseBarrelHero_{i}",(x+25,y,z+24),(x+125,y,z+38),4,"thermal",c)
    ship["artist_version"]="v2";ship["art_direction"]="large civic armor fields, command-city hierarchy, vast paired hangars"

def normalize(name,target):
    c=bpy.data.collections[name]
    for _ in range(2):
        dg=bpy.context.evaluated_depsgraph_get();objs=[o for o in c.all_objects if o.type=="MESH"];ps=[o.evaluated_get(dg).matrix_world@Vector(v) for o in objs for v in o.evaluated_get(dg).bound_box];lo=[min(p[i] for p in ps) for i in range(3)];hi=[max(p[i] for p in ps) for i in range(3)];center=[(lo[i]+hi[i])*.5 for i in range(3)];f=[target[i]/(hi[i]-lo[i]) for i in range(3)]
        for o in objs:o.location=tuple((o.location[i]-center[i])*f[i] for i in range(3));o.scale=tuple(o.scale[i]*f[i] for i in range(3))
    c["dimensions_m"]=target;c["scale_verified"]=True

def render(name,length,path):
    target=bpy.data.collections[name]
    for c in bpy.data.collections:c.hide_render=c.name.startswith("SM_Ship_") and c!=target
    w=bpy.context.scene.world;w.use_nodes=True;w.node_tree.nodes["Background"].inputs["Color"].default_value=(.006,.009,.014,1);w.node_tree.nodes["Background"].inputs["Strength"].default_value=.24
    made=[];bpy.ops.object.light_add(type="SUN",location=(0,0,length));made.append(bpy.context.object);made[-1].data.energy=4;made[-1].rotation_euler=(.65,-.48,-.7)
    for loc,e,color,size in (((length*.45,-length*.72,length*.52),19000,(.88,.93,1),length*.72),((-length*.45,length*.28,-length*.02),11000,(.08,.22,.58),length*.42)):
        bpy.ops.object.light_add(type="AREA",location=loc);q=bpy.context.object;q.data.energy=e;q.data.color=color;q.data.size=size;q.rotation_euler=(Vector((0,0,0))-q.location).to_track_quat('-Z','Y').to_euler();made.append(q)
    bpy.ops.object.camera_add(location=(length*.28,-length*2.15,length*.43));cam=bpy.context.object;cam.data.lens=58;cam.data.clip_end=40000;cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler();bpy.context.scene.camera=cam;made.append(cam)
    s=bpy.context.scene;s.render.engine="BLENDER_EEVEE";s.render.resolution_x=1600;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format="PNG";s.view_settings.look="AgX - Medium High Contrast";s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
    for o in made:bpy.data.objects.remove(o,do_unlink=True)
    for c in bpy.data.collections:c.hide_render=False

corvette_artist();carrier_artist();normalize("SM_Ship_MilitaryCorvette_ConceptMatch",(2400,430,620));normalize("SM_Ship_ExpeditionCarrier_ConceptMatch",(6500,1400,1800))
ships=[("SM_Ship_MilitaryCorvette_ConceptMatch",2400,"MilitaryCorvette"),("SM_Ship_ExpeditionCarrier_ConceptMatch",6500,"ExpeditionCarrier")]
for cn,l,n in ships:
    c=bpy.data.collections[cn];bpy.ops.object.select_all(action="DESELECT");[o.select_set(True) for o in c.all_objects if o.type=="MESH"];bpy.context.view_layer.objects.active=next(o for o in c.all_objects if o.type=="MESH");bpy.ops.export_scene.gltf(filepath=str(OUT/"Exports"/("SM_Ship_"+n+"_ArtistV2.glb")),export_format="GLB",use_selection=True,export_apply=True);render(cn,l,OUT/"Previews"/(n+"_ArtistV2_Beauty.png"))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"FleetCapitalShips_ArtistV2.blend"))
report={"version":2,"removed_previous_objects":removed,"principles":["fewer larger bespoke armor plates","strong district hierarchy","dominant hangar architecture","curated defense silhouettes","three-quarter form review","textured materials"],"ships":[{"name":n,"dimensions_m":d,"mesh_count":sum(1 for o in bpy.data.collections[n].all_objects if o.type=='MESH')} for n,d in ((ships[0][0],[2400,430,620]),(ships[1][0],[6500,1400,1800]))]}
(OUT/"ArtistV2_QA.json").write_text(json.dumps(report,indent=2),encoding="utf-8");print("ARTIST_V2_COMPLETE",report)
