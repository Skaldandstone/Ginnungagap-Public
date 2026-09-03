"""Generate and import the modular player pressure-suit kit.

Run with UnrealEditor-Cmd.exe Ginnungagap.uproject -ExecutePythonScript=<this file>
The script is idempotent and keeps generated source OBJ files under Saved/GeneratedSuit.
"""

import math
import os
import unreal


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_DIR = os.path.join(ROOT, "Saved", "GeneratedSuit")
MESH_PATH = "/Game/Characters/Player/Suit/Meshes"
MAT_PATH = "/Game/Characters/Player/Suit/Materials"
BP_PATH = "/Game/Characters/Player/Blueprints"
SKIN_TEXTURE_PATH = "/Game/Characters/Player/Skins/Textures"
CHARACTER_MAT_PATH = "/Game/Materials/Characters"
SKIN_SOURCE_DIR = os.path.join(ROOT, "Content", "Characters", "Player", "Skins", "Source")
os.makedirs(SOURCE_DIR, exist_ok=True)


class Mesh:
    def __init__(self):
        self.vertices = []
        self.faces = []

    def vertex(self, p):
        self.vertices.append(p)
        return len(self.vertices)

    def quad(self, a, b, c, d):
        self.faces.extend([(a, b, c), (a, c, d)])

    def box(self, center, size):
        cx, cy, cz = center
        x, y, z = [v * 0.5 for v in size]
        ids = [self.vertex((cx + sx*x, cy + sy*y, cz + sz*z))
               for sx, sy, sz in ((-1,-1,-1), (1,-1,-1), (1,1,-1), (-1,1,-1),
                                  (-1,-1,1), (1,-1,1), (1,1,1), (-1,1,1))]
        for q in ((0,3,2,1), (4,5,6,7), (0,1,5,4), (1,2,6,5), (2,3,7,6), (3,0,4,7)):
            self.quad(*(ids[i] for i in q))

    def cylinder(self, center, radius, height, segments=24, axis="x"):
        rings = []
        for side in (-0.5, 0.5):
            ring = []
            for i in range(segments):
                a = 2 * math.pi * i / segments
                q = (side*height, radius*math.cos(a), radius*math.sin(a))
                if axis == "z": q = (q[1], q[2], q[0])
                ring.append(self.vertex(tuple(center[j] + q[j] for j in range(3))))
            rings.append(ring)
        for i in range(segments):
            n = (i + 1) % segments
            self.quad(rings[0][i], rings[0][n], rings[1][n], rings[1][i])
        c0 = self.vertex(tuple(center[j] + ((-height/2,0,0) if axis == "x" else (0,0,-height/2))[j] for j in range(3)))
        c1 = self.vertex(tuple(center[j] + ((height/2,0,0) if axis == "x" else (0,0,height/2))[j] for j in range(3)))
        for i in range(segments):
            n = (i + 1) % segments
            self.faces.extend([(c0, rings[0][n], rings[0][i]), (c1, rings[1][i], rings[1][n])])

    def ellipsoid(self, center, radii, rings=12, segments=24, z_min=-1.0, z_max=1.0):
        rows = []
        for r in range(rings + 1):
            t = r / rings
            z_norm = z_min + (z_max - z_min) * t
            phi = math.asin(max(-1.0, min(1.0, z_norm)))
            row = []
            for i in range(segments):
                a = 2 * math.pi * i / segments
                p = (center[0] + radii[0] * math.cos(phi) * math.cos(a),
                     center[1] + radii[1] * math.cos(phi) * math.sin(a),
                     center[2] + radii[2] * math.sin(phi))
                row.append(self.vertex(p))
            rows.append(row)
        for r in range(rings):
            for i in range(segments):
                n = (i + 1) % segments
                self.quad(rows[r][i], rows[r][n], rows[r+1][n], rows[r+1][i])

    def ellipsoid_sector(self, center, radii, angle_min, angle_max,
                         rings=12, segments=16, z_min=-1.0, z_max=1.0):
        """Open ellipsoid sector; local +X is character forward."""
        rows = []
        for r in range(rings + 1):
            z_norm = z_min + (z_max - z_min) * r / rings
            phi = math.asin(max(-1.0, min(1.0, z_norm)))
            row = []
            for i in range(segments + 1):
                a = angle_min + (angle_max - angle_min) * i / segments
                row.append(self.vertex((
                    center[0] + radii[0] * math.cos(phi) * math.cos(a),
                    center[1] + radii[1] * math.cos(phi) * math.sin(a),
                    center[2] + radii[2] * math.sin(phi))))
            rows.append(row)
        for r in range(rings):
            for i in range(segments):
                self.quad(rows[r][i], rows[r][i+1], rows[r+1][i+1], rows[r+1][i])

    def tube(self, points, radius, segments=10):
        """Low-poly hose following a sequence of points."""
        rows = []
        for index, point in enumerate(points):
            before = points[max(0, index - 1)]
            after = points[min(len(points) - 1, index + 1)]
            tangent = [after[i] - before[i] for i in range(3)]
            length = math.sqrt(sum(v*v for v in tangent)) or 1.0
            tangent = [v / length for v in tangent]
            reference = (0, 0, 1) if abs(tangent[2]) < .9 else (0, 1, 0)
            side = (tangent[1]*reference[2] - tangent[2]*reference[1],
                    tangent[2]*reference[0] - tangent[0]*reference[2],
                    tangent[0]*reference[1] - tangent[1]*reference[0])
            side_len = math.sqrt(sum(v*v for v in side)) or 1.0
            side = tuple(v / side_len for v in side)
            up = (side[1]*tangent[2] - side[2]*tangent[1],
                  side[2]*tangent[0] - side[0]*tangent[2],
                  side[0]*tangent[1] - side[1]*tangent[0])
            row = []
            for i in range(segments):
                a = 2 * math.pi * i / segments
                row.append(self.vertex(tuple(point[j] + radius * (
                    math.cos(a)*side[j] + math.sin(a)*up[j]) for j in range(3))))
            rows.append(row)
        for r in range(len(rows) - 1):
            for i in range(segments):
                n = (i + 1) % segments
                self.quad(rows[r][i], rows[r][n], rows[r+1][n], rows[r+1][i])

    def torus(self, center, major, minor, major_segments=28, minor_segments=10):
        rows = []
        for i in range(major_segments):
            a = 2 * math.pi * i / major_segments
            row = []
            for j in range(minor_segments):
                b = 2 * math.pi * j / minor_segments
                row.append(self.vertex((center[0] + minor*math.sin(b),
                                        center[1] + (major + minor*math.cos(b))*math.cos(a),
                                        center[2] + (major + minor*math.cos(b))*math.sin(a))))
            rows.append(row)
        for i in range(major_segments):
            ni = (i + 1) % major_segments
            for j in range(minor_segments):
                nj = (j + 1) % minor_segments
                self.quad(rows[i][j], rows[ni][j], rows[ni][nj], rows[i][nj])

    def write(self, name):
        path = os.path.join(SOURCE_DIR, name + ".obj")
        min_z = min(v[2] for v in self.vertices)
        max_z = max(v[2] for v in self.vertices)
        z_span = max(max_z - min_z, 0.001)
        with open(path, "w", encoding="ascii") as f:
            f.write("o " + name + "\n")
            for v in self.vertices:
                f.write("v %.5f %.5f %.5f\n" % v)
            uv_index = 1
            for face in self.faces:
                uvs = []
                for vertex_index in face:
                    x, y, z = self.vertices[vertex_index - 1]
                    uvs.append([(math.atan2(y, x) / (2 * math.pi)) + 0.5,
                                (z - min_z) / z_span])
                if max(uv[0] for uv in uvs) - min(uv[0] for uv in uvs) > 0.5:
                    for uv in uvs:
                        if uv[0] < 0.5:
                            uv[0] += 1.0
                for u, v in uvs:
                    f.write("vt %.6f %.6f\n" % (u, v))
                f.write("f %d/%d %d/%d %d/%d\n" % (
                    face[0], uv_index, face[1], uv_index + 1, face[2], uv_index + 2))
                uv_index += 3
        return path


def build_mesh_sources():
    sources = {}

    # Rear hard-shell hemisphere with crown rails and side hinge blocks. The clear
    # pressure dome is a separate translucent mesh so the face remains readable.
    m = Mesh(); m.ellipsoid_sector((0,0,0), (15.5,14.5,16.5), math.pi/2, 3*math.pi/2, 16, 24, -.82, 1.0); m.torus((0,0,-10), 13.8, 1.4, 30, 10); m.box((-3,-13,0), (6,3.5,12)); m.box((-3,13,0), (6,3.5,12)); m.box((11.5,0,-9.0), (3,21,3.0)); m.box((10.5,-12,0), (4,3.0,15)); m.box((10.5,12,0), (4,3.0,15))
    sources["SM_Suit_HelmetShell"] = m.write("SM_Suit_HelmetShell")

    m = Mesh(); m.ellipsoid((1.0,0,0), (15.8,14.2,17.2), 22, 32, -0.92, 1.0)
    sources["SM_Suit_Visor"] = m.write("SM_Suit_Visor")

    m = Mesh(); m.torus((0,0,-1.0), 13.8, 1.8, 32, 12); m.torus((0,0,-3.4), 14.5, 1.0, 32, 10); m.box((2,0,-3.0), (5,10,3)); m.box((-2,-10.5,-4), (4,3.5,4.5)); m.box((-2,10.5,-4), (4,3.5,4.5))
    sources["SM_Suit_PressureCollar"] = m.write("SM_Suit_PressureCollar")

    m = Mesh(); m.box((0,0,2), (5,24,21)); m.box((3.5,0,6), (3,17,9)); m.box((2.5,-11,3), (3,3.5,15)); m.box((2.5,11,3), (3,3.5,15)); m.tube([(-1,-10,9), (1,-13,5), (0,-12,-4)], 1.0); m.tube([(-1,10,9), (1,13,5), (0,12,-4)], 1.0)
    sources["SM_Suit_ChestPlate"] = m.write("SM_Suit_ChestPlate")

    m = Mesh(); m.box((0,0,1), (12,27,35)); m.box((-7,0,2), (3,22,29)); m.box((-9,0,3), (2,15,15)); m.box((7,0,11), (3,20,8)); m.box((7,0,-11), (3,17,7)); m.box((8,-9,-2), (3,6,12)); m.box((8,9,-2), (3,6,12)); m.cylinder((1,-8.5,11), 3.4, 18, 22, axis="z"); m.cylinder((1,8.5,11), 3.4, 18, 22, axis="z"); m.cylinder((7,-7,-11), 2.2, 5, 18); m.cylinder((7,7,-11), 2.2, 5, 18); m.tube([(6,-8,16), (2,-13,19), (-5,-14,12)], 1.35); m.tube([(6,8,16), (2,13,19), (-5,14,12)], 1.35); m.tube([(6,-9,-5), (2,-13,-9), (-5,-12,-13)], .9); m.tube([(6,9,-5), (2,13,-9), (-5,12,-13)], .9)
    sources["SM_Suit_LifeSupportPack"] = m.write("SM_Suit_LifeSupportPack")

    m = Mesh(); m.ellipsoid((0,0,0), (7,10,8), 10, 24, -.35, 1.0); m.box((-2,0,-3), (4,13,6)); m.box((2,0,3), (3,10,3))
    sources["SM_Suit_ShoulderPad"] = m.write("SM_Suit_ShoulderPad")

    m = Mesh(); m.box((0,0,0), (7,11,8)); m.box((4.3,0,1), (2.8,8,5.5)); m.box((6.0,0,1), (1.4,6.5,3.6)); m.cylinder((-4,0,0), 5.8, 3.2, 22); m.box((5.6,-3.8,-3), (1.8,1.8,1.8)); m.box((5.6,3.8,-3), (1.8,1.8,1.8))
    sources["SM_Suit_ForearmComputer"] = m.write("SM_Suit_ForearmComputer")

    m = Mesh(); m.ellipsoid((1,0,4), (6.2,8.8,7.8), 10, 22, -.35, 1.0); m.box((-1,0,-5), (5,12.5,17)); m.box((1,0,-14), (4,11,5)); m.box((3,-5.6,-5), (2,1.8,13)); m.box((3,5.6,-5), (2,1.8,13))
    sources["SM_Suit_KneePad"] = m.write("SM_Suit_KneePad")

    m = Mesh(); m.box((3,0,0), (24,13,9)); m.box((-7,0,6), (9,14,14)); m.box((8,0,-5), (16,15,4)); m.box((-4,0,-4), (8,15,4)); m.box((9,0,3), (6,14,5)); m.box((-5,0,12), (5,14,3)); m.box((14,0,-2), (5,13,5))
    sources["SM_Suit_BootShell"] = m.write("SM_Suit_BootShell")

    m = Mesh(); m.ellipsoid((1,0,0), (7.5,5.4,4.4), 9, 20, -.75, 1.0); m.cylinder((-6,0,0), 5.3, 5.5, 20); m.box((6,0,-1), (8,9,3)); m.box((9,-3.3,-1), (5,1.4,2.5)); m.box((9,-1.1,-1), (5,1.4,2.5)); m.box((9,1.1,-1), (5,1.4,2.5)); m.box((9,3.3,-1), (5,1.4,2.5)); m.box((1,0,4), (7,8,2))
    sources["SM_Suit_Glove"] = m.write("SM_Suit_Glove")

    m = Mesh(); m.box((0,0,0), (6,12,15)); m.box((3,0,3), (2,9,5)); m.cylinder((-3,0,4), 5.8, 2.5, 18)
    sources["SM_Suit_ThighPouch"] = m.write("SM_Suit_ThighPouch")

    m = Mesh(); m.box((0,0,0), (7,18,13)); m.box((4,0,1), (2.5,12,8)); m.box((5,-6,-4), (2,3,3)); m.box((5,6,-4), (2,3,3))
    sources["SM_Suit_Module_Crew"] = m.write("SM_Suit_Module_Crew")

    m = Mesh(); m.box((0,0,0), (8,24,15)); m.cylinder((5,-7,1), 4.0, 4.0, 18); m.cylinder((5,7,1), 4.0, 4.0, 18); m.box((5,0,-5), (3,8,3))
    sources["SM_Suit_Module_Engineering"] = m.write("SM_Suit_Module_Engineering")

    m = Mesh(); m.box((0,0,0), (7,20,21)); m.box((4,0,0), (3,6,17)); m.box((4,0,0), (3,16,6))
    sources["SM_Suit_Module_Medical"] = m.write("SM_Suit_Module_Medical")

    m = Mesh(); m.box((0,0,0), (11,24,22)); m.box((7,0,3), (4,17,10)); m.box((7,-8,-6), (4,6,6)); m.box((7,8,-6), (4,6,6)); m.box((6,0,-9), (3,10,4))
    sources["SM_Suit_Module_Security"] = m.write("SM_Suit_Module_Security")
    return sources


def import_mesh(name, filename, force=False):
    destination = MESH_PATH + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(destination):
        if not force:
            return
    task = unreal.AssetImportTask()
    task.filename = filename
    task.destination_path = MESH_PATH
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = True
    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = False
    options.import_materials = False
    options.import_textures = False
    options.static_mesh_import_data.combine_meshes = True
    options.static_mesh_import_data.generate_lightmap_u_vs = True
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    asset = unreal.EditorAssetLibrary.load_asset(destination)
    if not asset:
        raise RuntimeError("Failed to import " + destination)
    asset.set_editor_property("allow_cpu_access", False)
    unreal.EditorAssetLibrary.save_loaded_asset(asset)


def import_skin_textures():
    textures = {}
    for role in ("Crew", "Engineering", "Medical", "Security"):
        textures[role] = {}
        for channel in ("Albedo", "Normal", "Roughness", "Metallic", "AO"):
            suffix = "" if channel == "Albedo" else "_" + channel
            name = "T_PlayerSkin_" + role + suffix
            source = os.path.join(SKIN_SOURCE_DIR, name + ".png")
            destination = SKIN_TEXTURE_PATH + "/" + name
            task = unreal.AssetImportTask()
            task.filename = source
            task.destination_path = SKIN_TEXTURE_PATH
            task.destination_name = name
            task.automated = True
            task.replace_existing = True
            task.save = True
            unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
            texture = unreal.EditorAssetLibrary.load_asset(destination)
            if not texture:
                raise RuntimeError("Failed to import " + destination)
            texture.set_editor_property("srgb", channel == "Albedo")
            if channel == "Normal":
                texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
            elif channel != "Albedo":
                texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
            unreal.EditorAssetLibrary.save_loaded_asset(texture)
            textures[role][channel] = texture
    return textures


def create_textured_master(name, destination_path):
    path = destination_path + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, destination_path, unreal.Material, unreal.MaterialFactoryNew())
    unreal.MaterialEditingLibrary.set_material_usage(
        material, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH)
    albedo = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSampleParameter2D, -360, -80)
    albedo.set_editor_property("parameter_name", "SkinTexture")
    albedo.set_editor_property("texture", unreal.EditorAssetLibrary.load_asset(
        SKIN_TEXTURE_PATH + "/T_PlayerSkin_Crew"))
    role_tint = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, -360, -180)
    role_tint.set_editor_property("parameter_name", "SuitColor")
    role_tint.set_editor_property("default_value", unreal.LinearColor(1, 1, 1, 1))
    role_strength = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, -360, -240)
    role_strength.set_editor_property("parameter_name", "RoleColorStrength")
    role_strength.set_editor_property("default_value", 0.22)
    tinted_albedo = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionLinearInterpolate, -120, -100)
    unreal.MaterialEditingLibrary.connect_material_expressions(albedo, "RGB", tinted_albedo, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(role_tint, "", tinted_albedo, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(role_strength, "", tinted_albedo, "Alpha")
    normal = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSampleParameter2D, -360, 80)
    normal.set_editor_property("parameter_name", "NormalTexture")
    normal.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    normal.set_editor_property("texture", unreal.EditorAssetLibrary.load_asset(
        SKIN_TEXTURE_PATH + "/T_PlayerSkin_Crew_Normal"))
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSampleParameter2D, -360, 220)
    rough.set_editor_property("parameter_name", "RoughnessTexture")
    rough.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    rough.set_editor_property("texture", unreal.EditorAssetLibrary.load_asset(
        SKIN_TEXTURE_PATH + "/T_PlayerSkin_Crew_Roughness"))
    metal = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSampleParameter2D, -360, 360)
    metal.set_editor_property("parameter_name", "MetallicTexture")
    metal.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    metal.set_editor_property("texture", unreal.EditorAssetLibrary.load_asset(
        SKIN_TEXTURE_PATH + "/T_PlayerSkin_Crew_Metallic"))
    ao = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSampleParameter2D, -360, 500)
    ao.set_editor_property("parameter_name", "AOTexture")
    ao.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    ao.set_editor_property("texture", unreal.EditorAssetLibrary.load_asset(
        SKIN_TEXTURE_PATH + "/T_PlayerSkin_Crew_AO"))
    damage = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, -100, -20)
    damage.set_editor_property("parameter_name", "DamageAmount")
    grime = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, -100, 40)
    grime.set_editor_property("parameter_name", "GrimeAmount")
    bloom = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, -100, 100)
    bloom.set_editor_property("parameter_name", "BloomAmount")
    role_emission = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, -100, 160)
    role_emission.set_editor_property("parameter_name", "RoleEmissionStrength")
    role_emission.set_editor_property("default_value", 0.0)
    damage_color = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, 80, -80)
    damage_color.set_editor_property("constant", unreal.LinearColor(0.12, 0.055, 0.025, 1))
    grime_color = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, 80, 20)
    grime_color.set_editor_property("constant", unreal.LinearColor(0.035, 0.025, 0.018, 1))
    bloom_color = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, 80, 120)
    bloom_color.set_editor_property("constant", unreal.LinearColor(0.32, 0.015, 0.5, 1))
    damage_lerp = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionLinearInterpolate, 300, -60)
    grime_lerp = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionLinearInterpolate, 500, -30)
    bloom_lerp = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionLinearInterpolate, 700, 0)
    unreal.MaterialEditingLibrary.connect_material_expressions(tinted_albedo, "", damage_lerp, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(damage_color, "", damage_lerp, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(damage, "", damage_lerp, "Alpha")
    unreal.MaterialEditingLibrary.connect_material_expressions(damage_lerp, "", grime_lerp, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(grime_color, "", grime_lerp, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(grime, "", grime_lerp, "Alpha")
    unreal.MaterialEditingLibrary.connect_material_expressions(grime_lerp, "", bloom_lerp, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(bloom_color, "", bloom_lerp, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(bloom, "", bloom_lerp, "Alpha")
    emissive = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionMultiply, 500, 150)
    role_emissive = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionMultiply, 500, 220)
    combined_emissive = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionAdd, 700, 180)
    unreal.MaterialEditingLibrary.connect_material_expressions(bloom_color, "", emissive, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(bloom, "", emissive, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(role_tint, "", role_emissive, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(role_emission, "", role_emissive, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(emissive, "", combined_emissive, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(role_emissive, "", combined_emissive, "B")
    unreal.MaterialEditingLibrary.connect_material_property(bloom_lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(combined_emissive, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(normal, "RGB", unreal.MaterialProperty.MP_NORMAL)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "R", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "R", unreal.MaterialProperty.MP_METALLIC)
    unreal.MaterialEditingLibrary.connect_material_property(ao, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def create_master_material():
    path = MAT_PATH + "/M_PlayerSuit_Master"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    factory = unreal.MaterialFactoryNew()
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset("M_PlayerSuit_Master", MAT_PATH, unreal.Material, factory)
    color = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionVectorParameter, -320, -40)
    color.set_editor_property("parameter_name", "SuitColor")
    color.set_editor_property("default_value", unreal.LinearColor(0.18, 0.20, 0.22, 1.0))
    rough = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionScalarParameter, -320, 120)
    rough.set_editor_property("parameter_name", "Roughness")
    rough.set_editor_property("default_value", 0.68)
    metal = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionScalarParameter, -320, 220)
    metal.set_editor_property("parameter_name", "Metallic")
    metal.set_editor_property("default_value", 0.12)
    unreal.MaterialEditingLibrary.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def create_instance(name, parent, color, roughness=0.68, metallic=0.12, texture=None, destination_path=MAT_PATH):
    path = destination_path + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mi = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, destination_path, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    unreal.MaterialEditingLibrary.set_material_instance_parent(mi, parent)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(mi, "SuitColor", unreal.LinearColor(*color))
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "Roughness", roughness)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "Metallic", metallic)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(mi, "RoleColorStrength", 0.22)
    if texture:
        if isinstance(texture, dict):
            for channel, parameter in (("Albedo", "SkinTexture"), ("Normal", "NormalTexture"),
                                       ("Roughness", "RoughnessTexture"), ("Metallic", "MetallicTexture"),
                                       ("AO", "AOTexture")):
                unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(
                    mi, parameter, texture[channel])
        else:
            unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(mi, "SkinTexture", texture)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    return mi


def create_visor_material():
    path = MAT_PATH + "/M_PlayerSuit_Visor"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_PlayerSuit_Visor", MAT_PATH, unreal.Material, unreal.MaterialFactoryNew())
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
    color = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionVectorParameter, -300, -60)
    color.set_editor_property("parameter_name", "SuitColor")
    color.set_editor_property("default_value", unreal.LinearColor(0.02, 0.05, 0.065, 1.0))
    opacity = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant, -300, 100)
    opacity.set_editor_property("r", 0.38)
    rough = unreal.MaterialEditingLibrary.create_material_expression(material, unreal.MaterialExpressionConstant, -300, 180)
    rough.set_editor_property("r", 0.16)
    fresnel = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionFresnel, -80, 20)
    edge_color = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -80, 100)
    edge_color.set_editor_property("constant", unreal.LinearColor(0.10, 0.28, 0.42, 1.0))
    edge_reflection = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionMultiply, 100, 60)
    visor_color = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionAdd, 280, 20)
    unreal.MaterialEditingLibrary.connect_material_expressions(fresnel, "", edge_reflection, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(edge_color, "", edge_reflection, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(color, "", visor_color, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(edge_reflection, "", visor_color, "B")
    unreal.MaterialEditingLibrary.connect_material_property(visor_color, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(edge_reflection, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def create_blueprint(name, role):
    path = BP_PATH + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.CoopSurvivalCharacter)
    bp = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, BP_PATH, unreal.Blueprint, factory)
    if not bp:
        raise RuntimeError("Failed to create " + path)
    cdo = unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property("pressure_suit_role", role)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)


def main():
    unreal.log("Building modular player suit assets...")
    sources = build_mesh_sources()
    if "-VisorOnly" in unreal.SystemLibrary.get_command_line():
        import_mesh("SM_Suit_Visor", sources["SM_Suit_Visor"], force=True)
        unreal.EditorAssetLibrary.save_asset(MESH_PATH + "/SM_Suit_Visor", only_if_is_dirty=False)
        unreal.log("Player suit visor asset complete.")
        return
    for name, source in sources.items():
        import_mesh(name, source, force=True)

    textures = import_skin_textures()
    master = create_textured_master("M_PlayerSuit_Master", MAT_PATH)
    create_instance("MI_Suit_Crew", master, (0.05, 0.28, 0.80, 1), texture=textures["Crew"])
    create_instance("MI_Suit_Engineering", master, (0.95, 0.30, 0.025, 1), texture=textures["Engineering"])
    create_instance("MI_Suit_Medical", master, (0.04, 0.72, 0.52, 1), texture=textures["Medical"])
    create_instance("MI_Suit_Security", master, (0.78, 0.035, 0.025, 1), 0.58, 0.12, textures["Security"])

    character_master = create_textured_master("M_PlayerSkin_Master", CHARACTER_MAT_PATH)
    create_instance("MI_Default", character_master, (1,1,1,1), texture=textures["Crew"], destination_path=CHARACTER_MAT_PATH)
    create_instance("MI_ArcticCamo", character_master, (1,1,1,1), texture=textures["Medical"], destination_path=CHARACTER_MAT_PATH)
    create_instance("MI_DeepSea", character_master, (1,1,1,1), 0.62, 0.08, textures["Security"], CHARACTER_MAT_PATH)
    create_instance("MI_Hazmat", character_master, (1,1,1,1), texture=textures["Engineering"], destination_path=CHARACTER_MAT_PATH)
    create_instance("MI_Veteran", character_master, (1,1,1,1), 0.82, 0.05, textures["Crew"], CHARACTER_MAT_PATH)
    create_instance("MI_Specter", character_master, (1,1,1,1), 0.38, 0.18, textures["Security"], CHARACTER_MAT_PATH)
    visor = create_visor_material()
    create_instance("MI_Suit_Visor", visor, (0.004, 0.012, 0.020, 1.0), 0.16, 0.08)

    roles = unreal.PressureSuitRole
    create_blueprint("BP_Player_Suit_Crew", roles.CREW)
    create_blueprint("BP_Player_Suit_Engineering", roles.ENGINEERING)
    create_blueprint("BP_Player_Suit_Medical", roles.MEDICAL)
    create_blueprint("BP_Player_Suit_Security", roles.SECURITY)
    unreal.EditorAssetLibrary.save_directory("/Game/Characters/Player")
    unreal.log("Player suit assets complete.")


main()
