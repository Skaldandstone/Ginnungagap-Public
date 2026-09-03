"""Generate the first broad gameplay-model library for Ginnungagap.

Run with:
  UnrealEditor-Cmd.exe Ginnungagap.uproject -run=pythonscript \
    -script=tools/build_gameplay_model_library.py -unattended -nop4

The script creates deterministic OBJ interchange files in Intermediate and imports
real Unreal static meshes.  These are production-scale silhouette models intended
for immediate gameplay hookup and later detail/texture passes.
"""

from __future__ import annotations

import math
from pathlib import Path

import unreal


ROOT = "/Game/Assets/Models"
SOURCE_DIR = Path(unreal.SystemLibrary.get_project_directory()) / "Intermediate" / "GameplayModels"


class Mesh:
    def __init__(self, name):
        self.name, self.vertices, self.faces = name, [], []

    def vertex(self, point):
        self.vertices.append(point)
        return len(self.vertices)

    def box(self, center, size):
        cx, cy, cz = center
        sx, sy, sz = (v * .5 for v in size)
        ids = [self.vertex((cx+x*sx, cy+y*sy, cz+z*sz)) for x, y, z in (
            (-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),
            (-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1))]
        for f in ((0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)):
            self.faces.append(tuple(ids[i] for i in f))

    def cylinder(self, center, radius, height, sides=16, axis="z"):
        rings = []
        for end in (-.5, .5):
            ring = []
            for i in range(sides):
                a = math.tau*i/sides
                u, v, w = radius*math.cos(a), radius*math.sin(a), height*end
                p = {"x": (w,u,v), "y": (u,w,v), "z": (u,v,w)}[axis]
                ring.append(self.vertex(tuple(center[j]+p[j] for j in range(3))))
            rings.append(ring)
        self.faces += [tuple(reversed(rings[0])), tuple(rings[1])]
        for i in range(sides):
            n = (i+1) % sides
            self.faces.append((rings[0][i], rings[0][n], rings[1][n], rings[1][i]))

    def sphere(self, center, radii, rings=8, sides=16):
        rows = []
        for r in range(1, rings):
            phi = math.pi*r/rings
            rows.append([self.vertex((center[0]+radii[0]*math.sin(phi)*math.cos(math.tau*s/sides),
                                      center[1]+radii[1]*math.sin(phi)*math.sin(math.tau*s/sides),
                                      center[2]+radii[2]*math.cos(phi))) for s in range(sides)])
        bottom = self.vertex((center[0], center[1], center[2]-radii[2]))
        top = self.vertex((center[0], center[1], center[2]+radii[2]))
        for s in range(sides):
            n = (s+1) % sides
            self.faces += [(bottom, rows[-1][n], rows[-1][s]), (top, rows[0][s], rows[0][n])]
        for r in range(len(rows)-1):
            for s in range(sides):
                n = (s+1) % sides
                self.faces.append((rows[r][s], rows[r+1][s], rows[r+1][n], rows[r][n]))

    def write(self, path):
        with open(path, "w", encoding="ascii") as out:
            out.write("o " + self.name + "\n")
            for x, y, z in self.vertices:
                out.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
            for x, y, z in self.vertices:
                out.write(f"vt {(x % 200)/200:.6f} {(z % 200)/200:.6f}\n")
            for face in self.faces:
                out.write("f " + " ".join(f"{i}/{i}" for i in face) + "\n")


def build_library():
    assets = {}
    def make(category, name, fn):
        mesh = Mesh(name); fn(mesh); assets[name] = (category, mesh)

    # Handheld equipment and pickups (centimeters, X-forward).
    make("Equipment", "SM_Tool_RepairWelder", lambda m: (m.box((18,0,0),(36,10,14)), m.box((-3,0,-10),(12,9,22)), m.cylinder((40,0,0),5,10,12,"x")))
    make("Equipment", "SM_Tool_PlasmaCutter", lambda m: (m.box((16,0,0),(42,11,16)), m.box((-1,0,-12),(10,10,24)), m.cylinder((42,0,0),3,12,10,"x")))
    make("Equipment", "SM_Tool_BioScanner", lambda m: (m.box((0,0,0),(28,18,7)), m.box((7,0,6),(12,14,5)), m.cylinder((-13,0,-6),4,12,10,"z")))
    make("Equipment", "SM_Tool_FireExtinguisher", lambda m: (m.cylinder((0,0,24),9,48,16), m.box((0,0,52),(16,7,8)), m.cylinder((10,0,48),3,18,10,"x")))
    make("Equipment", "SM_Weapon_IndustrialNailer", lambda m: (m.box((12,0,0),(42,13,16)), m.box((-3,0,-14),(10,11,28)), m.box((29,0,0),(12,9,9))))
    make("Equipment", "SM_Weapon_ShockBaton", lambda m: (m.cylinder((0,0,30),4,60,12), m.cylinder((0,0,-5),6,14,12), m.box((0,0,61),(12,5,5))))
    make("Pickups", "SM_Pickup_OxygenCanister", lambda m: (m.cylinder((0,0,28),10,56,16), m.cylinder((0,0,60),5,8,12)))
    make("Pickups", "SM_Pickup_MedicalInjector", lambda m: (m.cylinder((0,0,0),4,32,12,"x"), m.box((-19,0,0),(7,14,14)), m.cylinder((18,0,0),2,8,8,"x")))
    make("Pickups", "SM_Pickup_PowerCell", lambda m: (m.box((0,0,0),(16,10,30)), m.box((0,0,18),(10,7,6)), m.box((0,0,-18),(12,8,6))))
    make("Pickups", "SM_Pickup_RepairPartsCase", lambda m: (m.box((0,0,18),(54,34,36)), m.box((0,0,38),(58,38,6)), m.box((0,-20,20),(24,5,8))))
    make("Pickups", "SM_Pickup_SampleCanister", lambda m: (m.cylinder((0,0,18),7,36,16), m.cylinder((0,0,39),9,6,12), m.cylinder((0,0,-3),9,6,12)))

    # Mission machinery and traversal props.
    make("Drones", "SM_Drone_Retrieval", lambda m: (m.box((0,0,12),(70,46,18)), m.cylinder((0,-31,12),12,8,16,"y"), m.cylinder((0,31,12),12,8,16,"y"), m.box((30,0,-3),(18,28,20)), m.box((-28,0,3),(20,32,10))))
    make("Drones", "SM_Drone_Repair", lambda m: (m.sphere((0,0,18),(28,22,14)), m.box((22,0,2),(28,10,8)), m.cylinder((-20,-20,18),7,8,12,"y"), m.cylinder((-20,20,18),7,8,12,"y")))
    make("ShipSystems", "SM_System_CryoPod", lambda m: (m.box((0,0,35),(220,92,70)), m.sphere((15,0,74),(82,40,28)), m.box((-96,0,82),(28,80,110))))
    make("ShipSystems", "SM_System_LifeSupport", lambda m: (m.box((0,0,105),(150,90,210)), m.cylinder((-42,-52,112),20,145,16), m.cylinder((42,-52,112),20,145,16), m.box((0,-54,34),(120,12,42))))
    make("ShipSystems", "SM_System_SensorConsole", lambda m: (m.box((0,0,65),(150,70,130)), m.box((0,-46,125),(135,16,72)), m.box((0,-52,62),(110,25,25))))
    make("ShipSystems", "SM_System_JumpConsole", lambda m: (m.box((0,0,55),(190,85,110)), m.box((0,-55,112),(175,20,100)), m.cylinder((0,-70,45),25,18,20,"y")))
    make("ShipSystems", "SM_System_EscapePod", lambda m: (m.sphere((0,0,95),(75,70,115)), m.box((0,0,18),(115,105,36)), m.box((0,-67,100),(72,12,115))))
    make("Environment", "SM_Prop_EVA_TetherReel", lambda m: (m.cylinder((0,0,38),32,24,20,"y"), m.cylinder((0,0,38),12,34,16,"y"), m.box((0,0,8),(75,42,16))))
    make("Environment", "SM_Prop_DeconShower", lambda m: (m.box((-55,0,110),(14,70,220)), m.box((55,0,110),(14,70,220)), m.box((0,0,212),(110,70,16)), m.cylinder((0,0,196),5,16,10,"z")))

    # Static visual proxies: deliberately segmented for later skeletal replacement.
    make("Bloom", "SM_Bloom_Crawler_Proxy", lambda m: (m.sphere((0,0,28),(38,28,22)), m.sphere((38,0,24),(20,18,17)), *[m.cylinder((-8, y, 10),4,70,10,"x") for y in (-28,-10,10,28)]))
    make("Bloom", "SM_Bloom_Puppeteer_Proxy", lambda m: (m.sphere((0,0,125),(28,24,45)), m.sphere((0,0,182),(18,17,22)), m.cylinder((0,-32,118),7,90,12,"y"), m.cylinder((0,32,118),7,90,12,"y"), m.cylinder((0,-13,55),10,110,12,"z"), m.cylinder((0,13,55),10,110,12,"z")))
    make("Bloom", "SM_Bloom_InfestedDrone_Proxy", lambda m: (m.box((0,0,38),(72,52,24)), m.sphere((20,-18,45),(24,18,20)), m.sphere((-24,12,34),(20,25,18)), m.cylinder((0,-36,36),11,9,12,"y"), m.cylinder((0,36,36),11,9,12,"y")))
    make("Bloom", "SM_Bloom_HiveNode", lambda m: (m.sphere((0,0,44),(46,38,44)), m.sphere((28,-18,24),(30,24,25)), m.sphere((-24,20,20),(26,31,22)), *[m.cylinder((0,0,15),5,90,9,"x") for _ in range(1)]))
    return assets


def import_asset(category, name, source):
    destination = f"{ROOT}/{category}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(destination):
        return False
    task = unreal.AssetImportTask()
    task.filename = str(source); task.destination_path = f"{ROOT}/{category}"
    task.destination_name = name; task.automated = True; task.replace_existing = False; task.save = True
    options = unreal.FbxImportUI(); options.import_mesh = True; options.import_as_skeletal = False
    options.import_materials = False; options.import_textures = False
    options.static_mesh_import_data.combine_meshes = True
    options.static_mesh_import_data.generate_lightmap_u_vs = True
    options.static_mesh_import_data.auto_generate_collision = True
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    if not unreal.EditorAssetLibrary.does_asset_exist(destination):
        raise RuntimeError("Import failed: " + destination)
    return True


def main():
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    assets = build_library(); imported = 0
    for name, (category, mesh) in assets.items():
        source = SOURCE_DIR / f"{name}.obj"; mesh.write(source)
        imported += int(import_asset(category, name, source))
    unreal.EditorAssetLibrary.save_directory(ROOT, only_if_is_dirty=False, recursive=True)
    unreal.log(f"Gameplay model library ready: {len(assets)} models ({imported} newly imported).")


if __name__ == "__main__":
    main()
