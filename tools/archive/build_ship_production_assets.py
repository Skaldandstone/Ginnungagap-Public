"""Build the first Unreal-ready modular ship kit, props, materials, and showcase maps.

Run from Unreal Editor or UnrealEditor-Cmd with PythonScriptPlugin enabled. Geometry sources
are generated deterministically under Intermediate/ShipProduction and imported as real static
mesh assets under /Game/Assets/Ships/Production.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

import unreal


ROOT = "/Game/Assets/Ships/Production"
MESH_PATH = ROOT + "/Meshes"
MATERIAL_PATH = ROOT + "/Materials"
MAP_PATH = "/Game/Assets/Maps/ShipProduction"
SOURCE_DIR = Path(unreal.SystemLibrary.get_project_directory()) / "Intermediate" / "ShipProduction"


class ObjMesh:
    def __init__(self, name):
        self.name = name
        self.vertices = []
        self.faces = []

    def vertex(self, xyz):
        self.vertices.append(xyz)
        return len(self.vertices)

    def box(self, center, size):
        cx, cy, cz = center
        sx, sy, sz = (v * 0.5 for v in size)
        ids = [self.vertex((cx + x * sx, cy + y * sy, cz + z * sz)) for x, y, z in (
            (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1))]
        for face in ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
                     (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            self.faces.append(tuple(ids[i] for i in face))

    def cylinder(self, center, radius, height, sides=16, axis="z"):
        cx, cy, cz = center
        rings = []
        for sign in (-0.5, 0.5):
            ring = []
            for i in range(sides):
                a = math.tau * i / sides
                u, v, w = radius * math.cos(a), radius * math.sin(a), height * sign
                point = {"x": (cx + w, cy + u, cz + v),
                         "y": (cx + u, cy + w, cz + v),
                         "z": (cx + u, cy + v, cz + w)}[axis]
                ring.append(self.vertex(point))
            rings.append(ring)
        self.faces.append(tuple(reversed(rings[0])))
        self.faces.append(tuple(rings[1]))
        for i in range(sides):
            j = (i + 1) % sides
            self.faces.append((rings[0][i], rings[0][j], rings[1][j], rings[1][i]))

    def sphere(self, center, radius, rings=8, sides=16, scale=(1.0, 1.0, 1.0)):
        cx, cy, cz = center
        rows = []
        for ring in range(1, rings):
            phi = math.pi * ring / rings
            row = []
            for side in range(sides):
                theta = math.tau * side / sides
                row.append(self.vertex((
                    cx + radius * math.sin(phi) * math.cos(theta) * scale[0],
                    cy + radius * math.sin(phi) * math.sin(theta) * scale[1],
                    cz + radius * math.cos(phi) * scale[2],
                )))
            rows.append(row)
        bottom = self.vertex((cx, cy, cz - radius * scale[2]))
        top = self.vertex((cx, cy, cz + radius * scale[2]))
        for side in range(sides):
            nxt = (side + 1) % sides
            self.faces.append((bottom, rows[-1][nxt], rows[-1][side]))
            self.faces.append((top, rows[0][side], rows[0][nxt]))
        for ring in range(len(rows) - 1):
            for side in range(sides):
                nxt = (side + 1) % sides
                self.faces.append((rows[ring][side], rows[ring + 1][side],
                                   rows[ring + 1][nxt], rows[ring][nxt]))

    def write(self, path):
        with open(path, "w", encoding="utf-8") as stream:
            stream.write("o " + self.name + "\n")
            for x, y, z in self.vertices:
                stream.write(f"v {x:.4f} {y:.4f} {z:.4f}\n")
            # Interchange's OBJ translator expects a valid UV index for every face vertex.
            # A deterministic box-projection seed is sufficient for prototype trim materials;
            # final Nanite meshes will receive authored UV channels.
            for x, y, z in self.vertices:
                stream.write(f"vt {(x % 400.0) / 400.0:.6f} {(z % 400.0) / 400.0:.6f}\n")
            for face in self.faces:
                stream.write("f " + " ".join(f"{i}/{i}" for i in face) + "\n")


def mesh_sources():
    meshes = {}

    def make(name, build):
        mesh = ObjMesh(name)
        build(mesh)
        meshes[name] = mesh

    make("SM_Kit_Floor_4m", lambda m: m.box((0, 0, 10), (400, 400, 20)))
    make("SM_Kit_Ceiling_4m", lambda m: m.box((0, 0, 15), (400, 400, 30)))
    make("SM_Kit_Wall_4m", lambda m: (m.box((0, 0, 200), (400, 24, 400)),
                                      m.box((-165, -18, 200), (28, 36, 390)),
                                      m.box((165, -18, 200), (28, 36, 390))))
    make("SM_Kit_BulkheadDoor", lambda m: (m.box((-160, 0, 210), (80, 48, 420)),
                                            m.box((160, 0, 210), (80, 48, 420)),
                                            m.box((0, 0, 380), (240, 48, 80)),
                                            m.box((0, 0, 25), (240, 48, 50))))
    make("SM_Kit_StructuralRib", lambda m: (m.box((-190, 0, 200), (36, 60, 400)),
                                             m.box((190, 0, 200), (36, 60, 400)),
                                             m.box((0, 0, 380), (400, 60, 36))))
    make("SM_Prop_WallTerminal", lambda m: (m.box((0, 0, 115), (110, 42, 230)),
                                             m.box((0, -28, 145), (82, 12, 92)),
                                             m.box((0, -42, 62), (96, 36, 46))))
    make("SM_Prop_CargoCrate", lambda m: (m.box((0, 0, 55), (120, 100, 110)),
                                           m.box((0, 0, 112), (126, 106, 12))))
    make("SM_Prop_OxygenBottle", lambda m: (m.cylinder((0, 0, 70), 24, 140, 20),
                                             m.cylinder((0, 0, 148), 10, 16, 12)))
    make("SM_Prop_CrashSeat", lambda m: (m.box((0, 0, 45), (62, 70, 18)),
                                          m.box((0, 28, 115), (62, 18, 145)),
                                          m.box((-24, 0, 22), (10, 55, 45)),
                                          m.box((24, 0, 22), (10, 55, 45))))
    make("SM_Prop_Locker", lambda m: (m.box((0, 0, 110), (90, 48, 220)),
                                       m.box((0, -27, 110), (78, 8, 202))))
    make("SM_Prop_Scrubber", lambda m: (m.box((0, 0, 95), (125, 90, 190)),
                                         m.cylinder((-36, -48, 105), 18, 110, 16),
                                         m.cylinder((36, -48, 105), 18, 110, 16)))
    make("SM_Prop_PowerJunction", lambda m: (m.box((0, 0, 95), (105, 52, 190)),
                                              m.cylinder((-28, -34, 70), 12, 28, 12, "y"),
                                              m.cylinder((28, -34, 70), 12, 28, 12, "y")))
    make("SM_Prop_PipeStraight", lambda m: m.cylinder((0, 0, 0), 12, 400, 16, "x"))
    make("SM_Prop_LightFixture", lambda m: (m.box((0, 0, 8), (160, 38, 16)),
                                             m.box((0, 0, -2), (132, 24, 8))))
    return meshes


def import_mesh(name, source_file):
    path = f"{MESH_PATH}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.load_asset(path)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(source_file))
    task.set_editor_property("destination_path", MESH_PATH)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", False)
    task.set_editor_property("save", True)
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    options.static_mesh_import_data.set_editor_property("combine_meshes", True)
    options.static_mesh_import_data.set_editor_property("generate_lightmap_u_vs", True)
    options.static_mesh_import_data.set_editor_property("auto_generate_collision", True)
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    asset = unreal.load_asset(path)
    if not asset:
        raise RuntimeError("Static mesh import failed: " + path)
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def create_material(name, color, roughness, metallic=0.0, emissive=0.0):
    path = f"{MATERIAL_PATH}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.load_asset(path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIAL_PATH, unreal.Material, unreal.MaterialFactoryNew())
    base = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -300, 0)
    base.set_editor_property("constant", unreal.LinearColor(*color, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -300, 180)
    rough.set_editor_property("r", roughness)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    metal = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -300, 260)
    metal.set_editor_property("r", metallic)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emissive:
        multiply = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionMultiply, -80, 80)
        strength = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant, -300, 90)
        strength.set_editor_property("r", emissive)
        unreal.MaterialEditingLibrary.connect_material_expressions(base, "", multiply, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(strength, "", multiply, "B")
        unreal.MaterialEditingLibrary.connect_material_property(
            multiply, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def spawn_mesh(mesh, location, rotation=(0, 0, 0), scale=(1, 1, 1), material=None, label=""):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location))
    actor.set_actor_rotation(unreal.Rotator(rotation[1], rotation[2], rotation[0]), False)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    actor.set_actor_label(label or mesh.get_name())
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    if material:
        component.set_material(0, material)
    return actor


def build_room(map_name, room_width, room_length, ceiling_height, style, meshes, materials):
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    map_asset = f"{MAP_PATH}/{map_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(map_asset):
        unreal.log_warning("Showcase map already exists; preserving it: " + map_asset)
        return
    if not level_subsystem.new_level(map_asset):
        raise RuntimeError("Could not create level: " + map_asset)

    tile = 400.0
    nx = max(2, int(room_length / tile))
    ny = max(2, int(room_width / tile))
    hull = materials["hull"]
    deck = materials["deck"]
    accent = materials[style]
    dark = materials["dark"]
    glow = materials["glow"]

    for ix in range(nx):
        x = (ix - (nx - 1) * 0.5) * tile
        for iy in range(ny):
            y = (iy - (ny - 1) * 0.5) * tile
            spawn_mesh(meshes["SM_Kit_Floor_4m"], (x, y, 0), material=deck, label="Floor")
            spawn_mesh(meshes["SM_Kit_Ceiling_4m"], (x, y, ceiling_height), material=dark, label="Ceiling")
        for side in (-1, 1):
            y = side * ny * tile * 0.5
            spawn_mesh(meshes["SM_Kit_Wall_4m"], (x, y, 0), material=hull, label="PressureWall")
        if ix % 3 == 0:
            spawn_mesh(meshes["SM_Kit_StructuralRib"], (x, 0, 0),
                       scale=(1, max(1.0, ny), ceiling_height / 400.0), material=accent, label="StructuralRib")
    for end in (-1, 1):
        x = end * nx * tile * 0.5
        spawn_mesh(meshes["SM_Kit_BulkheadDoor"], (x, 0, 0),
                   rotation=(0, 0, 90), scale=(1, 1, ceiling_height / 400.0), material=accent,
                   label="PressureBulkhead")

    prop_x = [(-nx * tile * 0.25), 0, (nx * tile * 0.25)]
    prop_names = ("SM_Prop_WallTerminal", "SM_Prop_Locker", "SM_Prop_PowerJunction")
    for x, prop_name in zip(prop_x, prop_names):
        spawn_mesh(meshes[prop_name], (x, -ny * tile * 0.5 + 55, 15), material=accent, label=prop_name)
    for x in range(-int(nx / 2), int(nx / 2), 2):
        spawn_mesh(meshes["SM_Prop_LightFixture"], (x * tile, 0, ceiling_height - 30),
                   material=glow, label="CeilingLight")
    for i in range(max(2, ny)):
        spawn_mesh(meshes["SM_Prop_CargoCrate"],
                   ((nx * tile * 0.25) + i * 135, ny * tile * 0.28, 20),
                   material=accent, label="CargoCrate")
    spawn_mesh(meshes["SM_Prop_Scrubber"], (-nx * tile * 0.3, ny * tile * 0.33, 10),
               material=accent, label="LifeSupportScrubber")
    spawn_mesh(meshes["SM_Prop_OxygenBottle"], (-nx * tile * 0.3 + 150, ny * tile * 0.33, 10),
               material=accent, label="EmergencyOxygen")

    for x in (-nx * tile * 0.3, 0, nx * tile * 0.3):
        light = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.RectLight, unreal.Vector(x, 0, ceiling_height - 80))
        light.set_actor_rotation(unreal.Rotator(-90, 0, 0), False)
        comp = light.get_component_by_class(unreal.RectLightComponent)
        comp.set_editor_property("intensity", 4200.0 if style != "large" else 6500.0)
        comp.set_editor_property("attenuation_radius", 1600.0)
        comp.set_editor_property("source_width", min(room_width * 0.45, 900.0))
        comp.set_editor_property("source_height", 80.0)
        comp.set_editor_property("light_color", unreal.Color(190, 215, 235))
    sky = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, ceiling_height * 0.5))
    sky.get_component_by_class(unreal.SkyLightComponent).set_editor_property("intensity", 0.18)
    player_start = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.PlayerStart, unreal.Vector(-nx * tile * 0.42, 0, 110))
    player_start.set_actor_rotation(unreal.Rotator(0, 0, 0), False)
    level_subsystem.save_current_level()


def main():
    unreal.log("Building Ginnungagap ship production assets...")
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    meshes = {}
    for name, source in mesh_sources().items():
        file_path = SOURCE_DIR / (name + ".obj")
        source.write(file_path)
        meshes[name] = import_mesh(name, file_path)

    materials = {
        "hull": create_material("M_Ship_Hull_OffWhite", (0.32, 0.34, 0.33), 0.68, 0.18),
        "deck": create_material("M_Ship_Deck_NonSlip", (0.055, 0.06, 0.065), 0.82, 0.3),
        "dark": create_material("M_Ship_Structure_Gunmetal", (0.035, 0.045, 0.05), 0.58, 0.72),
        "small": create_material("M_Ship_Accent_Utility", (0.34, 0.13, 0.035), 0.62, 0.34),
        "medium": create_material("M_Ship_Accent_Military", (0.16, 0.19, 0.2), 0.52, 0.64),
        "large": create_material("M_Ship_Accent_Civic", (0.075, 0.14, 0.18), 0.55, 0.42),
        "glow": create_material("M_Ship_Light_Cold", (0.18, 0.48, 0.7), 0.22, 0.0, 12.0),
    }

    build_room("L_Small_Companionway_Showcase", 1200, 5200, 430, "small", meshes, materials)
    build_room("L_Medium_ExpressSpine_Showcase", 3200, 7200, 760, "medium", meshes, materials)
    build_room("L_Large_CarrierConcourse_Showcase", 4800, 9200, 1200, "large", meshes, materials)
    unreal.EditorAssetLibrary.save_directory(ROOT)
    unreal.EditorAssetLibrary.save_directory(MAP_PATH)
    unreal.log("Ship production assets complete: 14 meshes, 7 materials, 3 showcase maps.")


if __name__ == "__main__":
    main()
