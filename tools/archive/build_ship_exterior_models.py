"""Generate full-scale exterior ship silhouettes and reusable hull modules."""

import math
from pathlib import Path
import unreal

ROOT = "/Game/Assets/Ships/Exterior/Meshes"
SOURCE = Path(unreal.SystemLibrary.get_project_directory()) / "Intermediate" / "ShipExterior"


class Mesh:
    def __init__(self, name): self.name, self.vertices, self.faces = name, [], []
    def v(self, p): self.vertices.append(p); return len(self.vertices)
    def box(self, c, s):
        cx,cy,cz=c; sx,sy,sz=(n*.5 for n in s)
        ids=[self.v((cx+x*sx,cy+y*sy,cz+z*sz)) for x,y,z in ((-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))]
        for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)): self.faces.append(tuple(ids[i] for i in f))
    def cylinder(self,c,r,h,sides=16,axis="x"):
        rings=[]
        for end in (-.5,.5):
            ring=[]
            for i in range(sides):
                a=math.tau*i/sides; u,v,w=r*math.cos(a),r*math.sin(a),h*end
                p={"x":(w,u,v),"y":(u,w,v),"z":(u,v,w)}[axis]
                ring.append(self.v(tuple(c[j]+p[j] for j in range(3))))
            rings.append(ring)
        self.faces += [tuple(reversed(rings[0])),tuple(rings[1])]
        for i in range(sides): n=(i+1)%sides; self.faces.append((rings[0][i],rings[0][n],rings[1][n],rings[1][i]))
    def wedge(self, c, length, width, height, nose=0.18):
        cx,cy,cz=c; x0=cx-length*.5; x1=cx+length*.5; w=width*.5; h=height*.5; nw=w*nose; nh=h*nose
        ids=[self.v(p) for p in ((x0,-w,cz-h),(x0,w,cz-h),(x0,w,cz+h),(x0,-w,cz+h),(x1,-nw,cz-nh),(x1,nw,cz-nh),(x1,nw,cz+nh),(x1,-nw,cz+nh))]
        for f in ((0,1,2,3),(4,7,6,5),(0,4,5,1),(3,2,6,7),(1,5,6,2),(0,3,7,4)): self.faces.append(tuple(ids[i] for i in f))
    def write(self,path):
        with open(path,"w",encoding="ascii") as out:
            out.write("o "+self.name+"\n")
            for x,y,z in self.vertices: out.write(f"v {x:.3f} {y:.3f} {z:.3f}\n")
            for x,y,z in self.vertices: out.write(f"vt {(x%10000)/10000:.6f} {(y%10000)/10000:.6f}\n")
            for face in self.faces: out.write("f "+" ".join(f"{i}/{i}" for i in face)+"\n")


def library():
    result={}
    def make(name,fn): m=Mesh(name); fn(m); result[name]=m
    # 1.4 km utility escort: automated long-duration ship, 24-32 operational decks, <=1,000 crew.
    make("SM_Ship_SmallUtilityEscort",lambda m:(m.wedge((0,0,0),140000,26000,32000),m.box((-22000,0,15000),(47000,18000,5000)),m.cylinder((-65000,-6500,0),5200,16000,20),m.cylinder((-65000,6500,0),5200,16000,20),m.box((8000,-14500,0),(40000,6000,7000)),m.box((8000,14500,0),(40000,6000,7000))))
    # 2.4 km corvette: armored spearhead, recessed drive cluster, dorsal command ridge.
    make("SM_Ship_MediumMilitaryCorvette",lambda m:(m.wedge((10000,0,0),240000,26000,19000,.08),m.box((-25000,0,12000),(100000,12000,6500)),m.box((-60000,0,-11000),(70000,18000,5500)),*[m.cylinder((-112000,y,z),5200,18000,20) for y,z in ((-9000,-4500),(9000,-4500),(-9000,4500),(9000,4500))]))
    # 6.5 km expedition carrier: long inhabited spine with modular hangar shoulders.
    make("SM_Ship_LargeExpeditionCarrier",lambda m:(m.wedge((40000,0,0),650000,52000,40000,.12),m.box((-30000,-52000,0),(280000,65000,26000)),m.box((-30000,52000,0),(280000,65000,26000)),m.box((0,0,30000),(330000,26000,14000)),m.box((-210000,0,-30000),(170000,60000,12000)),*[m.cylinder((-300000,y,z),10500,28000,24) for y,z in ((-25000,-12000),(0,-12000),(25000,-12000),(-25000,12000),(0,12000),(25000,12000))]))
    make("SM_Exterior_EngineCluster",lambda m:(m.box((0,0,0),(18000,22000,16000)),*[m.cylinder((-7000,y,z),3000,14000,18) for y,z in ((-6500,-4000),(6500,-4000),(-6500,4000),(6500,4000))]))
    make("SM_Exterior_RadiatorWing",lambda m:(m.box((0,0,0),(30000,800,12000)),m.box((0,0,0),(800,2600,14000)),*[m.box((x,0,0),(300,1200,11000)) for x in (-12000,-6000,0,6000,12000)]))
    make("SM_Exterior_SensorMast",lambda m:(m.cylinder((0,0,6000),900,12000,14,"z"),m.cylinder((0,0,12500),4500,1000,24,"z"),m.box((0,0,2500),(4500,4500,1200))))
    make("SM_Exterior_CargoPod",lambda m:(m.box((0,0,0),(24000,9000,9000)),m.box((0,0,5200),(22000,9500,1400)),m.box((0,0,-5200),(22000,9500,1400))))
    make("SM_Exterior_DockingCollar",lambda m:(m.cylinder((0,0,0),6000,4500,24,"x"),m.cylinder((3000,0,0),4200,1800,24,"x"),m.box((-2800,0,0),(1800,15000,15000))))
    return result


def import_mesh(name,path):
    destination=ROOT+"/"+name
    if unreal.EditorAssetLibrary.does_asset_exist(destination): return
    task=unreal.AssetImportTask(); task.filename=str(path); task.destination_path=ROOT; task.destination_name=name
    task.automated=True; task.replace_existing=False; task.save=True
    options=unreal.FbxImportUI(); options.import_mesh=True; options.import_as_skeletal=False; options.import_materials=False; options.import_textures=False
    options.static_mesh_import_data.combine_meshes=True; options.static_mesh_import_data.generate_lightmap_u_vs=True; options.static_mesh_import_data.auto_generate_collision=True
    task.options=options; unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    if not unreal.EditorAssetLibrary.does_asset_exist(destination): raise RuntimeError("Import failed: "+destination)


def main():
    SOURCE.mkdir(parents=True,exist_ok=True); models=library()
    for name,mesh in models.items():
        path=SOURCE/(name+".obj"); mesh.write(path); import_mesh(name,path)
    unreal.EditorAssetLibrary.save_directory(ROOT,only_if_is_dirty=False,recursive=True)
    unreal.log(f"Ship exterior library ready: {len(models)} meshes.")


main()
