"""Build the complete salvage gameplay batch natively inside Unreal Engine.

Geometry Scripting creates the Static Mesh assets. The same pass creates shared
materials, weapon/item definitions, Blueprint actors, the weighted seed catalog,
district-director defaults, and an in-engine review level. No DCC import is used.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = "/Game/Assets/Gameplay/SalvageBatch03"
MESH_PATH = ROOT + "/Meshes"
MATERIAL_PATH = ROOT + "/Materials"
WEAPON_DATA_PATH = ROOT + "/Data/Weapons"
ITEM_DATA_PATH = ROOT + "/Data/Items"
BP_GEAR_PATH = ROOT + "/Blueprints/Gear"
BP_OBJECT_PATH = ROOT + "/Blueprints/Objects"
CATALOG_PATH = ROOT + "/Data/DA_SalvageBatch03_SeedCatalog"
MAP_PATH = "/Game/Assets/Maps/ModelLibrary/L_SalvageGameplayBatch03_Unreal"
SAFE_MAP_PATH = "/Game/Assets/Maps/ModelLibrary/L_GameplayModelLibrary"
PROJECT_DIR = Path(unreal.SystemLibrary.get_project_directory())
REPORT_PATH = PROJECT_DIR / "Saved/Reports/SalvageGameplayBatch03Unreal.json"
FAB_MAPPING_PATH = PROJECT_DIR / "Art/Weapons/Fab/CosmoartLowPolyWeapons/WeaponConceptMapping.json"

PRIMITIVE = unreal.GeometryScriptPrimitiveOptions()
NORMALS = unreal.GeometryScriptCalculateNormalsOptions()
REVOLVE = unreal.GeometryScriptRevolveOptions()


GEAR = [
    dict(id="CompactRockCorer", label="Compact Rock Corer", form="corer", size=(88, 38, 38), envelope="STANDARD",
         fold=None, rooms=["EVA", "GeologyLab", "Cargo"], weight=.72, player=True, aerial=True, robotic=True,
         tags=["Tool.Mining", "Tool.Sample", "Hazard.Puncture"], range=95, damage=24, mass=9.4),
    dict(id="ThermalMiningLance", label="Thermal Mining Lance", form="lance", size=(134, 42, 44), envelope="LONG",
         fold=(84, 34, 36), rooms=["EVA", "MachineShop", "Cargo"], weight=.42, player=True, aerial=False, robotic=True,
         tags=["Tool.Mining", "Tool.Thermal", "Hazard.Hull"], range=145, damage=32, mass=17.8),
    dict(id="RegolithAuger", label="Regolith Auger", form="auger", size=(108, 46, 44), envelope="LONG",
         fold=(76, 38, 38), rooms=["EVA", "Cargo", "Fabrication"], weight=.55, player=True, aerial=False, robotic=True,
         tags=["Tool.Mining", "Tool.Excavation", "Hazard.Entangle"], range=105, damage=27, mass=16.2),
    dict(id="ExplosiveBoltRemover", label="Explosive Bolt Remover", form="bolt", size=(82, 34, 34), envelope="COMPACT",
         fold=None, rooms=["Airlock", "MachineShop", "Armory"], weight=.64, player=True, aerial=True, robotic=True,
         tags=["Tool.Salvage", "Tool.Ordnance", "Hazard.Explosive"], range=80, damage=20, mass=7.6),
    dict(id="MagneticScrapFlinger", label="Magnetic Scrap Flinger", form="flinger", size=(94, 58, 52), envelope="BULKY",
         fold=(70, 44, 42), rooms=["Cargo", "Recycler", "EVA"], weight=.38, player=True, aerial=True, robotic=True,
         tags=["Tool.Salvage", "Tool.Magnetic", "Weapon.Kinetic"], range=900, damage=38, mass=19.1),
    dict(id="DiamondCableSaw", label="Diamond Cable Saw", form="saw", size=(102, 54, 48), envelope="BULKY",
         fold=(68, 40, 38), rooms=["MachineShop", "EVA", "DamageControl"], weight=.48, player=True, aerial=False, robotic=True,
         tags=["Tool.Salvage", "Tool.Cutting", "Hazard.Laceration"], range=90, damage=34, mass=14.7),
    dict(id="PlasmaGouger", label="Plasma Gouger", form="gouger", size=(96, 40, 40), envelope="STANDARD",
         fold=None, rooms=["MachineShop", "DamageControl", "EVA"], weight=.44, player=True, aerial=True, robotic=True,
         tags=["Tool.Salvage", "Tool.Plasma", "Hazard.Hull"], range=120, damage=36, mass=11.9),
    dict(id="KineticSampleHammer", label="Kinetic Sample Hammer", form="hammer", size=(78, 34, 34), envelope="COMPACT",
         fold=None, rooms=["GeologyLab", "EVA", "Science"], weight=.76, player=True, aerial=True, robotic=True,
         tags=["Tool.Sample", "Tool.Impact", "Weapon.Kinetic"], range=85, damage=26, mass=8.1),
    dict(id="ExteriorTetherGun", label="Exterior Tether Gun", form="tether", size=(104, 40, 40), envelope="STANDARD",
         fold=(76, 34, 34), rooms=["Airlock", "EVA", "Cargo"], weight=.82, player=True, aerial=True, robotic=True,
         tags=["Tool.EVA", "Tool.Tether", "Traversal.Anchor"], range=1800, damage=8, mass=10.6),
    dict(id="DebrisCaptureClaw", label="Debris Capture Claw", form="claw", size=(112, 62, 54), envelope="BULKY",
         fold=(72, 42, 40), rooms=["Cargo", "EVA", "Recycler"], weight=.52, player=False, aerial=True, robotic=True,
         tags=["Tool.Salvage", "Tool.Capture", "Drone.Preferred"], range=130, damage=18, mass=22.4),
]

FIRST_USE_REFERENCES = {
    "CompactRockCorer": "Art/Weapons/RealityScan/CompactRockCorer_Pilot/CleanReference/CompactRockCorer_FirstUse_Orbit_A.png",
    "ThermalMiningLance": "Art/Weapons/SalvageBatch03/CleanFirstUseReferences/ThermalMiningLance_FirstUse_Orbit.png",
    "RegolithAuger": "Art/Weapons/SalvageBatch03/CleanFirstUseReferences/RegolithAuger_FirstUse_Orbit.png",
    "ExplosiveBoltRemover": "Art/Weapons/SalvageBatch03/CleanFirstUseReferences/ExplosiveBoltRemover_FirstUse_Orbit.png",
    "MagneticScrapFlinger": "Art/Weapons/SalvageBatch03/CleanFirstUseReferences/MagneticScrapFlinger_FirstUse_Orbit.png",
    "DiamondCableSaw": "Art/Weapons/SalvageBatch03/CleanFirstUseReferences/DiamondCableSaw_FirstUse_Orbit.png",
}

OBJECTS = [
    dict(id="SalvageToolRack", label="Salvage Tool Rack", form="rack", size=(135, 42, 145), rooms=["MachineShop", "Cargo", "Airlock"], weight=.82, quantity=(1, 1), tags=["Prop.Storage", "Anchor.Tools"], pickup=False, mass=42),
    dict(id="PortableToolCharger", label="Portable Tool Charger", form="charger", size=(62, 42, 34), rooms=["MachineShop", "DamageControl", "Cargo"], weight=.64, quantity=(1, 2), tags=["Pickup.Power", "Tool.Support"], pickup=True, mass=8.5),
    dict(id="RockCoreCanister", label="Rock Core Canister", form="canister", size=(46, 24, 24), rooms=["GeologyLab", "Science", "Cargo"], weight=.78, quantity=(1, 3), tags=["Pickup.Sample", "Mission.Optional"], pickup=True, mass=2.8),
    dict(id="TetherSpoolCase", label="Tether Spool Case", form="spool", size=(54, 38, 30), rooms=["Airlock", "EVA", "Cargo"], weight=.86, quantity=(1, 2), tags=["Pickup.Ammo", "Tool.Tether"], pickup=True, mass=5.2),
    dict(id="ThermalCellCrate", label="Thermal Cell Crate", form="cellcrate", size=(68, 46, 34), rooms=["MachineShop", "Armory", "Cargo"], weight=.58, quantity=(1, 2), tags=["Pickup.Ammo", "Hazard.Thermal"], pickup=True, mass=11.4),
    dict(id="ExplosiveBoltCaddy", label="Explosive Bolt Caddy", form="boltcaddy", size=(56, 34, 34), rooms=["Armory", "Airlock", "MachineShop"], weight=.28, quantity=(1, 1), tags=["Pickup.Ordnance", "Hazard.Explosive"], pickup=True, mass=7.9),
    dict(id="MagneticScrapBin", label="Magnetic Scrap Bin", form="scrapbin", size=(110, 78, 72), rooms=["Recycler", "Cargo", "MachineShop"], weight=.72, quantity=(1, 2), tags=["Prop.Resource", "Pickup.Scrap"], pickup=False, mass=58),
    dict(id="SalvageSurveyBeacon", label="Salvage Survey Beacon", form="beacon", size=(42, 42, 82), rooms=["Airlock", "EVA", "Derelict"], weight=.45, quantity=(1, 2), tags=["Prop.Navigation", "Mission.Optional"], pickup=False, mass=12),
]


def text(value):
    return unreal.TextLibrary.conv_string_to_text(value)


def xf(x=0, y=0, z=0, pitch=0, yaw=0, roll=0, sx=1, sy=1, sz=1):
    return unreal.Transform(
        location=unreal.Vector(x, y, z),
        rotation=unreal.Rotator(pitch=pitch, yaw=yaw, roll=roll),
        scale=unreal.Vector(sx, sy, sz),
    )


def box(mesh, loc, dims, rotation=(0, 0, 0)):
    mesh.append_box(PRIMITIVE, xf(*loc, pitch=rotation[0], yaw=rotation[1], roll=rotation[2]), *dims, 2, 2, 2)


def cylinder(mesh, loc, radius, length, axis="x"):
    rotation = {"x": (90, 0, 0), "y": (0, 0, 90), "z": (0, 0, 0)}[axis]
    mesh.append_cylinder(PRIMITIVE, xf(*loc, pitch=rotation[0], yaw=rotation[1], roll=rotation[2]), radius, length, 24, 2, True)


def torus(mesh, loc, major, minor, axis="x", scale=(1, 1, 1)):
    rotation = {"x": (90, 0, 0), "y": (0, 0, 90), "z": (0, 0, 0)}[axis]
    mesh.append_torus(PRIMITIVE, xf(*loc, pitch=rotation[0], yaw=rotation[1], roll=rotation[2], sx=scale[0], sy=scale[1], sz=scale[2]), REVOLVE, major, minor, 32, 10)


def sphere(mesh, loc, radius, scale=(1, 1, 1)):
    mesh.append_sphere_lat_long(PRIMITIVE, xf(*loc, sx=scale[0], sy=scale[1], sz=scale[2]), radius, 32, 16)


def common_tool(mesh, d):
    length, width, height = d["size"]
    box(mesh, (-length*.08, 0, height*.56), (length*.48, width*.58, height*.48))
    box(mesh, (-length*.08, 0, height*.86), (length*.40, width*.20, height*.11))
    if d["player"]:
        box(mesh, (-length*.18, 0, height*.20), (length*.14, width*.34, height*.40), (0, -7, 0))
    box(mesh, (-length*.02, -width*.31, height*.63), (length*.18, 1.4, height*.09))


def copy_static_mesh(asset_path):
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError(f"Fab donor Static Mesh unavailable: {asset_path}")
    mesh = unreal.DynamicMesh()
    mesh, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        asset,
        mesh,
        unreal.GeometryScriptCopyMeshFromAssetOptions(),
        unreal.GeometryScriptMeshReadLOD(),
        False,
    )
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError(f"Could not copy Fab donor mesh {asset_path}: {outcome}")
    return mesh, asset


def rotated_scaled_origin(origin, scale, rotation):
    x, y, z = origin.x * scale.x, origin.y * scale.y, origin.z * scale.z
    if rotation == "yaw-90":
        return unreal.Vector(y, -x, z)
    if rotation == "pitch90":
        return unreal.Vector(z, y, -x)
    return unreal.Vector(x, y, z)


def rotation_for(rotation):
    if rotation == "yaw-90":
        return unreal.Rotator(pitch=0, yaw=-90, roll=0)
    if rotation == "pitch90":
        return unreal.Rotator(pitch=90, yaw=0, roll=0)
    return unreal.Rotator()


def append_static_module(target, asset_path, source_target_size, center, rotation="none"):
    donor, asset = copy_static_mesh(asset_path)
    bounds = asset.get_bounds()
    size = bounds.box_extent * 2.0
    scale = unreal.Vector(
        source_target_size[0] / max(size.x, .001),
        source_target_size[1] / max(size.y, .001),
        source_target_size[2] / max(size.z, .001),
    )
    transformed_origin = rotated_scaled_origin(bounds.origin, scale, rotation)
    transform = unreal.Transform(
        location=unreal.Vector(
            center[0] - transformed_origin.x,
            center[1] - transformed_origin.y,
            center[2] - transformed_origin.z,
        ),
        rotation=rotation_for(rotation),
        scale=scale,
    )
    unreal.GeometryScript_MeshTransforms.transform_mesh(donor, transform)
    unreal.GeometryScript_MeshEdits.append_mesh(target, donor, unreal.Transform())


def append_fab_chassis(target, d, entry):
    chassis, asset = copy_static_mesh(entry["unrealAsset"])
    bounds = asset.get_bounds()
    size = bounds.box_extent * 2.0
    dimensions = (size.x, size.y, size.z)
    longest_axis = max(range(3), key=lambda index: dimensions[index])
    source_longest = dimensions[longest_axis]
    uniform = d["size"][0] * .72 / max(source_longest, .001)
    scale = unreal.Vector(uniform, uniform, uniform)
    rotation = ("none", "yaw-90", "pitch90")[longest_axis]
    transformed_origin = rotated_scaled_origin(bounds.origin, scale, rotation)
    center = unreal.Vector(-d["size"][0] * .12, 0, d["size"][2] * .50)
    transform = unreal.Transform(
        location=center - transformed_origin,
        rotation=rotation_for(rotation),
        scale=scale,
    )
    unreal.GeometryScript_MeshTransforms.transform_mesh(chassis, transform)
    unreal.GeometryScript_MeshEdits.append_mesh(target, chassis, unreal.Transform())


def append_concept_head(mesh, d):
    length, width, height = d["size"]
    if d["form"] == "lance":
        cylinder(mesh, (length*.48, 0, height*.58), height*.055, length*.34)
        for x in (.34, .46): torus(mesh, (length*x, 0, height*.58), height*.12, 1.8)
    elif d["form"] == "auger":
        cylinder(mesh, (length*.43, 0, height*.56), height*.075, length*.42)
        for index, x in enumerate((.31, .40, .49, .58)):
            torus(mesh, (length*x, 0, height*.56), height*(.18-index*.018), 2.7)
    elif d["form"] == "bolt":
        for side in (-1, 1):
            box(mesh, (length*.56, side*width*.13, height*.56), (length*.22, width*.09, height*.09))
    elif d["form"] == "flinger":
        cylinder(mesh, (length*.38, 0, height*.58), height*.12, length*.24)
        torus(mesh, (length*.35, 0, height*.58), height*.23, 3.2)
    elif d["form"] == "saw":
        cylinder(mesh, (length*.33, 0, height*.56), height*.10, width*.34, "y")
        torus(mesh, (length*.33, 0, height*.56), height*.27, 3.2, "y")
        box(mesh, (length*.24, 0, height*.76), (length*.38, width*.52, height*.08))


def composite_fab_weapon_mesh(d, entry):
    mesh = unreal.DynamicMesh()
    append_fab_chassis(mesh, d, entry)
    for module in entry.get("donorModules", []):
        append_static_module(
            mesh,
            module["unrealAsset"],
            module["sourceTargetSizeCm"],
            module["locationCm"],
            module.get("rotation", "none"),
        )
    append_concept_head(mesh, d)
    return finalize(mesh)


def gear_mesh(d):
    mesh = unreal.DynamicMesh()
    length, width, height = d["size"]
    common_tool(mesh, d)
    form = d["form"]
    if form == "corer":
        cylinder(mesh, (length*.27, 0, height*.56), height*.10, length*.42)
        for i, x in enumerate((.32, .42, .51)):
            torus(mesh, (length*x, 0, height*.56), height*(.105-i*.015), 1.5)
    elif form == "lance":
        cylinder(mesh, (length*.30, 0, height*.58), height*.10, length*.52)
        for x in (.14, .26, .38): torus(mesh, (length*x, 0, height*.58), height*.14, 1.6)
        cylinder(mesh, (length*.61, 0, height*.58), height*.045, length*.16)
    elif form == "auger":
        cylinder(mesh, (length*.25, 0, height*.56), height*.08, length*.45)
        for i, x in enumerate((.18, .28, .38, .48)):
            torus(mesh, (length*x, 0, height*.56), height*(.17-i*.018), 2.6)
    elif form == "bolt":
        cylinder(mesh, (length*.30, 0, height*.56), height*.105, length*.40)
        for side in (-1, 1): box(mesh, (length*.52, side*width*.14, height*.56), (length*.13, width*.12, height*.11))
    elif form == "flinger":
        torus(mesh, (length*.30, 0, height*.58), height*.24, 4.5)
        cylinder(mesh, (length*.32, 0, height*.58), height*.13, length*.28)
        for side in (-1, 1): cylinder(mesh, (-length*.20, side*width*.30, height*.62), height*.07, length*.18)
    elif form == "saw":
        cylinder(mesh, (length*.32, 0, height*.56), height*.24, width*.28, "y")
        torus(mesh, (length*.32, 0, height*.56), height*.25, 3.5, "y")
        box(mesh, (length*.24, 0, height*.72), (length*.34, width*.55, height*.10))
    elif form == "gouger":
        cylinder(mesh, (length*.31, 0, height*.57), height*.12, length*.38)
        for x in (.16, .30, .43): torus(mesh, (length*x, 0, height*.57), height*.14, 1.4)
    elif form == "hammer":
        cylinder(mesh, (length*.27, 0, height*.56), height*.09, length*.38)
        cylinder(mesh, (length*.49, 0, height*.56), height*.20, width*.52, "y")
        cylinder(mesh, (length*.49, -width*.29, height*.56), height*.14, width*.08, "y")
    elif form == "tether":
        cylinder(mesh, (length*.31, 0, height*.57), height*.105, length*.44)
        torus(mesh, (-length*.10, width*.24, height*.61), height*.16, 2.7, "y")
        for side in (-1, 1): box(mesh, (length*.54, side*width*.10, height*.57), (length*.12, width*.08, height*.08))
    elif form == "claw":
        cylinder(mesh, (length*.22, 0, height*.57), height*.15, length*.30)
        for side in (-1, -.35, .35, 1):
            box(mesh, (length*.48, side*width*.22, height*.56), (length*.38, width*.10, height*.10), (0, -side*12, 0))
            box(mesh, (length*.67, side*width*.15, height*.56), (length*.10, width*.10, height*.13))
    return finalize(mesh)


def object_mesh(d):
    mesh = unreal.DynamicMesh()
    length, width, height = d["size"]
    form = d["form"]
    if form == "rack":
        for side in (-1, 1):
            box(mesh, (0, side*width*.43, height*.5), (length, 8, 8))
            box(mesh, (-length*.44, side*width*.43, height*.5), (8, 8, height))
        for x in (-.40, -.12, .16, .44): box(mesh, (length*x, 0, height*.48), (6, width, 12))
    elif form == "charger":
        box(mesh, (0, 0, height*.5), d["size"])
        for x in (-.22, 0, .22): box(mesh, (length*x, -width*.46, height*.56), (length*.16, 2.5, height*.42))
        box(mesh, (0, 0, height*1.02), (length*.34, width*.18, 7))
    elif form == "canister":
        cylinder(mesh, (0, 0, height*.5), width*.36, length*.72)
        for x in (-length*.42, length*.42): cylinder(mesh, (x, 0, height*.5), width*.44, length*.12)
        cylinder(mesh, (0, 0, height*.5), width*.16, length*.65)
    elif form == "spool":
        box(mesh, (0, 0, height*.5), d["size"])
        torus(mesh, (0, -width*.51, height*.52), height*.28, 2.8, "y")
        box(mesh, (length*.32, -width*.52, height*.52), (length*.12, 3.5, height*.20))
    elif form == "cellcrate":
        box(mesh, (0, 0, height*.5), d["size"])
        for x in (-.24, 0, .24): cylinder(mesh, (length*x, -width*.30, height*.52), height*.19, width*.55, "y")
    elif form == "boltcaddy":
        box(mesh, (0, 0, height*.42), (length, width, height*.72))
        for x in (-.28, 0, .28): cylinder(mesh, (length*x, 0, height*.85), width*.11, height*.32, "z")
        box(mesh, (0, 0, height*1.04), (length*.42, width*.16, 6))
    elif form == "scrapbin":
        box(mesh, (0, 0, height*.40), (length, width, height*.78))
        box(mesh, (0, 0, height*.82), (length*.86, width*.82, height*.18))
        for x, y in ((-.28, -.18), (.05, .20), (.30, -.10)): box(mesh, (length*x, width*y, height*.91), (26, 16, 12), (0, x*35, y*25))
    elif form == "beacon":
        cylinder(mesh, (0, 0, height*.42), width*.32, height*.64, "z")
        for angle, x, y in ((0, 1, 0), (120, -.5, .866), (240, -.5, -.866)):
            box(mesh, (x*width*.34, y*width*.34, height*.10), (34, 6, 7), (0, angle, 0))
        cylinder(mesh, (0, 0, height*.82), width*.18, height*.22, "z")
        torus(mesh, (0, 0, height*.84), width*.24, 2.5, "z")
    return finalize(mesh)


def finalize(mesh):
    mesh.discard_mesh_attributes()
    mesh.auto_generate_x_atlas_mesh_u_vs(0, unreal.GeometryScriptXAtlasOptions())
    mesh.recompute_normals(NORMALS)
    return mesh


def material(name, color, roughness, metallic=0, emissive=0):
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIAL_PATH, unreal.Material, unreal.MaterialFactoryNew())
    base = unreal.MaterialEditingLibrary.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -340, -20)
    base.set_editor_property("constant", unreal.LinearColor(*color, 1))
    rough = unreal.MaterialEditingLibrary.create_material_expression(asset, unreal.MaterialExpressionConstant, -340, 130)
    rough.set_editor_property("r", roughness)
    metal = unreal.MaterialEditingLibrary.create_material_expression(asset, unreal.MaterialExpressionConstant, -340, 220)
    metal.set_editor_property("r", metallic)
    unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emissive:
        multiply = unreal.MaterialEditingLibrary.create_material_expression(asset, unreal.MaterialExpressionMultiply, -80, 0)
        strength = unreal.MaterialEditingLibrary.create_material_expression(asset, unreal.MaterialExpressionConstant, -220, 60)
        strength.set_editor_property("r", emissive)
        unreal.MaterialEditingLibrary.connect_material_expressions(base, "", multiply, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(strength, "", multiply, "B")
        unreal.MaterialEditingLibrary.connect_material_property(multiply, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(asset)
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def build_materials():
    return {
        "gear": material("M_Salvage_EquipmentOrange", (.34, .085, .018), .42, .52),
        "first_use": material("M_Salvage_FirstUseCeramic", (.38, .34, .26), .34, .14),
        "pickup": material("M_Salvage_PickupYellow", (.46, .25, .022), .50, .28),
        "prop": material("M_Salvage_IndustrialGunmetal", (.035, .052, .061), .56, .78),
        "hazard": material("M_Salvage_OrdnanceRed", (.42, .012, .009), .44, .38),
        "floor": material("M_Salvage_ReviewFloor", (.012, .018, .026), .74, .45),
    }


def static_mesh(name, dynamic_mesh, assigned_material, metadata):
    path = f"{MESH_PATH}/SM_{name}"
    options = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    asset, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dynamic_mesh, path, options)
    if not asset or outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError(f"Geometry Scripting failed for {path}: {outcome}")
    slot = unreal.StaticMaterial()
    slot.set_editor_property("material_interface", assigned_material)
    slot.set_editor_property("material_slot_name", unreal.Name("Surface"))
    asset.set_editor_property("static_materials", [slot])
    asset.set_editor_property("light_map_resolution", 64)
    asset.set_editor_property("light_map_coordinate_index", 0)
    body = asset.get_editor_property("body_setup")
    if body:
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.Source", "Unreal Geometry Scripting")
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.Generator", "tools/build_salvage_gameplay_batch_03_unreal.py")
    for key, value in metadata.items(): unreal.EditorAssetLibrary.set_metadata_tag(asset, key, str(value))
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def data_asset(name, folder, cls):
    factory = unreal.DataAssetFactory()
    factory.set_editor_property("data_asset_class", cls)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, cls, factory)
    if not asset: raise RuntimeError(f"Could not create Data Asset {folder}/{name}")
    return asset


def blueprint(name, folder, parent):
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.Blueprint, factory)
    if not asset: raise RuntimeError(f"Could not create Blueprint {folder}/{name}")
    return asset


def profile(d, unsafe=False):
    value = unreal.WeaponFiringProfile()
    multiplier = 1.65 if unsafe else 1.0
    value.set_editor_property("max_range_cm", d["range"] * (1.35 if unsafe else 1))
    value.set_editor_property("trace_radius_cm", 5 if d["form"] in ("claw", "saw", "auger") else 3)
    value.set_editor_property("biological_damage", d["damage"] * multiplier)
    value.set_editor_property("impact_impulse", (13000 + d["mass"]*900) * multiplier)
    value.set_editor_property("recoil_impulse", (1300 + d["mass"]*180) * multiplier)
    value.set_editor_property("cooldown_seconds", .8 if unsafe else .55)
    hull_risk = any(tag in d["tags"] for tag in ("Hazard.Hull", "Hazard.Explosive", "Weapon.Kinetic"))
    value.set_editor_property("can_damage_hull", bool(unsafe and hull_risk))
    value.set_editor_property("hull_impact_severity", .55 if unsafe and hull_risk else 0)
    value.set_editor_property("breach_severity", .32 if unsafe and hull_risk else 0)
    return value


def envelope(d):
    value = unreal.WeaponCollisionEnvelope()
    value.set_editor_property("envelope_class", getattr(unreal.WeaponEnvelopeClass, d["envelope"]))
    value.set_editor_property("half_extents_cm", unreal.Vector(*(component*.5 for component in d["size"])))
    value.set_editor_property("center_offset_cm", unreal.Vector(0, 0, d["size"][2]*.5))
    value.set_editor_property("can_fold_for_traversal", d["fold"] is not None)
    if d["fold"]: value.set_editor_property("folded_half_extents_cm", unreal.Vector(*(component*.5 for component in d["fold"])))
    return value


def load_fab_mappings():
    if not FAB_MAPPING_PATH.is_file():
        return {}
    payload = json.loads(FAB_MAPPING_PATH.read_text(encoding="utf-8"))
    return {entry["id"]: entry for entry in payload.get("mappings", [])}


def resolve_weapon_visual(d, fallback_mesh, fab_mappings):
    entry = fab_mappings.get(d["id"])
    if not entry:
        return fallback_mesh, unreal.Transform(), None
    if entry.get("donorModules"):
        return fallback_mesh, unreal.Transform(), entry
    mesh = unreal.EditorAssetLibrary.load_asset(entry["unrealAsset"])
    if not isinstance(mesh, unreal.StaticMesh):
        unreal.log_warning(f"Fab visual unavailable for {d['id']}; using procedural fallback: {entry['unrealAsset']}")
        return fallback_mesh, unreal.Transform(), None
    bounds = mesh.get_bounds()
    size = bounds.box_extent * 2.0
    dimensions = (size.x, size.y, size.z)
    longest_axis = max(range(3), key=lambda index: dimensions[index])
    source_longest = dimensions[longest_axis]
    scale = d["size"][0] / source_longest if source_longest > 0.001 else 1.0
    origin = bounds.origin
    if longest_axis == 1:
        rotation = unreal.Rotator(pitch=0.0, yaw=-90.0, roll=0.0)
        rotated_origin = unreal.Vector(origin.y, -origin.x, origin.z)
    elif longest_axis == 2:
        rotation = unreal.Rotator(pitch=90.0, yaw=0.0, roll=0.0)
        rotated_origin = unreal.Vector(origin.z, origin.y, -origin.x)
    else:
        rotation = unreal.Rotator()
        rotated_origin = origin
    transform = unreal.Transform(
        location=unreal.Vector(
            -rotated_origin.x * scale,
            -rotated_origin.y * scale,
            d["size"][2] * 0.5 - rotated_origin.z * scale,
        ),
        rotation=rotation,
        scale=unreal.Vector(scale, scale, scale),
    )
    return mesh, transform, entry


def build_gear(meshes, fab_mappings):
    blueprints = {}
    definitions = {}
    visuals = {}
    for d in GEAR:
        visual_mesh, visual_transform, fab_entry = resolve_weapon_visual(d, meshes[d["id"]], fab_mappings)
        definition = data_asset("DA_Weapon_" + d["id"], WEAPON_DATA_PATH, unreal.ShipboardWeaponDefinition)
        definition.set_editor_property("weapon_id", unreal.Name(d["id"]))
        definition.set_editor_property("display_name", text(d["label"]))
        definition.set_editor_property("description", text("Industrial salvage tool with an authorized work profile and a dangerous bypass profile."))
        definition.set_editor_property("weapon_mesh", visual_mesh)
        definition.set_editor_property("safe_profile", profile(d, False))
        definition.set_editor_property("unsafe_modified_profile", profile(d, True))
        definition.set_editor_property("collision_envelope", envelope(d))
        definition.set_editor_property("player_compatible", d["player"])
        definition.set_editor_property("aerial_drone_compatible", d["aerial"])
        definition.set_editor_property("robotic_drone_compatible", d["robotic"])
        definition.set_editor_property("unsafe_modification_requires_soldier", "Hazard.Explosive" in d["tags"])
        if fab_entry:
            visual_source = "Fab modular composite" if fab_entry.get("donorModules") else "Fab chassis"
            unreal.EditorAssetLibrary.set_metadata_tag(definition, "Ginnungagap.VisualSource", visual_source)
            unreal.EditorAssetLibrary.set_metadata_tag(definition, "Ginnungagap.FabAsset", fab_entry["unrealAsset"])
            donor_assets = [module["unrealAsset"] for module in fab_entry.get("donorModules", [])]
            if donor_assets:
                unreal.EditorAssetLibrary.set_metadata_tag(definition, "Ginnungagap.FabDonorAssets", ",".join(donor_assets))
            unreal.EditorAssetLibrary.set_metadata_tag(definition, "Ginnungagap.MappingConfidence", fab_entry["confidence"])
        unreal.EditorAssetLibrary.save_loaded_asset(definition)
        bp = blueprint("BP_Weapon_" + d["id"], BP_GEAR_PATH, unreal.ShipboardWeapon)
        cdo = unreal.get_default_object(bp.generated_class())
        cdo.set_editor_property("definition", definition)
        visual_component = cdo.get_editor_property("visual_mesh")
        visual_component.set_static_mesh(visual_mesh)
        visual_component.set_relative_transform(visual_transform, False, False)
        cdo.get_editor_property("muzzle").set_relative_location(
            unreal.Vector(d["size"][0] * 0.48, 0, d["size"][2] * 0.5), False, False)
        unreal.EditorAssetLibrary.save_loaded_asset(bp)
        blueprints[d["id"]] = bp
        definitions[d["id"]] = definition
        visuals[d["id"]] = {
            "mesh": visual_mesh,
            "transform": visual_transform,
            "fab": fab_entry,
        }
    return blueprints, definitions, visuals


def build_objects(meshes):
    blueprints = {}
    definitions = {}
    for d in OBJECTS:
        if d["pickup"]:
            definition = data_asset("DA_Item_" + d["id"], ITEM_DATA_PATH, unreal.ItemDefinition)
            definition.set_editor_property("item_id", unreal.Name(d["id"]))
            definition.set_editor_property("display_name", text(d["label"]))
            definition.set_editor_property("description", text("Shipboard salvage supply from the Batch 03 world-item catalog."))
            definition.set_editor_property("max_stack_size", max(1, d["quantity"][1]))
            definition.set_editor_property("unit_mass_kg", d["mass"])
            definition.set_editor_property("item_tags", [unreal.Name(tag) for tag in d["tags"]])
            definition.set_editor_property("world_mesh", meshes[d["id"]])
            unreal.EditorAssetLibrary.save_loaded_asset(definition)
            bp = blueprint("BP_Pickup_" + d["id"], BP_OBJECT_PATH, unreal.InventoryItemPickup)
            cdo = unreal.get_default_object(bp.generated_class())
            cdo.set_editor_property("item_definition", definition)
            cdo.set_editor_property("quantity", d["quantity"][0])
            cdo.get_editor_property("visual_mesh").set_static_mesh(meshes[d["id"]])
            definitions[d["id"]] = definition
        else:
            bp = blueprint("BP_Prop_" + d["id"], BP_OBJECT_PATH, unreal.StaticMeshActor)
            cdo = unreal.get_default_object(bp.generated_class())
            cdo.get_editor_property("static_mesh_component").set_static_mesh(meshes[d["id"]])
            cdo.set_editor_property("replicates", True)
        unreal.EditorAssetLibrary.save_loaded_asset(bp)
        blueprints[d["id"]] = bp
    return blueprints, definitions


def build_catalog(gear_bps, object_bps):
    catalog = data_asset("DA_SalvageBatch03_SeedCatalog", ROOT + "/Data", unreal.WorldItemSeedCatalog)
    catalog.set_editor_property("catalog_id", unreal.Name("SalvageBatch03"))
    entries = []
    for d in GEAR + OBJECTS:
        entry = unreal.WorldItemSeedEntry()
        entry.set_editor_property("content_id", unreal.Name(d["id"]))
        entry.set_editor_property("actor_class", (gear_bps if d in GEAR else object_bps)[d["id"]].generated_class())
        entry.set_editor_property("weight", d["weight"])
        quantities = d.get("quantity", (1, 1))
        entry.set_editor_property("min_quantity", quantities[0])
        entry.set_editor_property("max_quantity", quantities[1])
        entry.set_editor_property("room_profiles", [unreal.Name(room) for room in d["rooms"]])
        entry.set_editor_property("content_tags", [unreal.Name(tag) for tag in d["tags"]])
        entries.append(entry)
    catalog.set_editor_property("entries", entries)
    unreal.EditorAssetLibrary.save_loaded_asset(catalog)
    return catalog


def wire_districts(catalog):
    settings = {
        "BP_DistrictDirector_Small": (4, ["Airlock", "DamageControl", "Cargo"]),
        "BP_DistrictDirector_Medium": (7, ["MachineShop", "Cargo", "Armory", "Recycler"]),
        "BP_DistrictDirector_Large": (10, ["Cargo", "EVA", "GeologyLab", "Science", "MachineShop"]),
    }
    for name, (count, rooms) in settings.items():
        path = f"/Game/Assets/Ships/Production/Blueprints/Gameplay/{name}"
        bp = unreal.EditorAssetLibrary.load_asset(path)
        if not bp:
            unreal.log_warning(f"District Blueprint unavailable; catalog not assigned: {path}")
            continue
        cdo = unreal.get_default_object(bp.generated_class())
        cdo.set_editor_property("world_item_catalog", catalog)
        cdo.set_editor_property("world_item_seed_count", count)
        cdo.set_editor_property("world_item_room_profiles", [unreal.Name(room) for room in rooms])
        unreal.EditorAssetLibrary.save_loaded_asset(bp)


def build_review_map(all_bps, materials, catalog):
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        if not level.load_level(MAP_PATH):
            raise RuntimeError("Could not load existing review level " + MAP_PATH)
        existing_actors = actors.get_all_level_actors()
        if existing_actors:
            actors.destroy_actors(existing_actors)
    elif not level.new_level(MAP_PATH):
        raise RuntimeError("Could not create review level " + MAP_PATH)
    for index, d in enumerate(GEAR + OBJECTS):
        row, column = divmod(index, 6)
        location = unreal.Vector((column-2.5)*250, (1-row)*310, 12)
        actor = actors.spawn_actor_from_class(all_bps[d["id"]].generated_class(), location, unreal.Rotator(0, 0, 0))
        actor.set_actor_label(f"Batch03_{index+1:02d}_{d['id']}")
        label = actors.spawn_actor_from_class(unreal.TextRenderActor, location + unreal.Vector(0, -85, 145), unreal.Rotator(0, 180, 0))
        label.set_actor_label("Label_" + d["id"])
        label.text_render.set_text(d["label"].upper())
        label.text_render.set_editor_property("world_size", 15)
        label.text_render.set_editor_property("text_render_color", unreal.Color(120, 205, 255, 255))
    floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator())
    floor.set_actor_label("Batch03_UnrealReviewFloor")
    floor.static_mesh_component.set_static_mesh(unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane.Plane"))
    floor.static_mesh_component.set_material(0, materials["floor"])
    floor.set_actor_scale3d(unreal.Vector(20, 16, 1))
    key = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 1200), unreal.Rotator(-42, -28, 0))
    key.light_component.set_editor_property("intensity", 4.0)
    key.light_component.set_editor_property("light_color", unreal.Color(215, 230, 255, 255))
    sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 800), unreal.Rotator())
    sky.light_component.set_editor_property("intensity", .7)
    for y, color in ((-1100, unreal.Color(255, 92, 35, 255)), (1100, unreal.Color(55, 115, 255, 255))):
        light = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(0, y, 650), unreal.Rotator())
        light.light_component.set_editor_property("intensity", 4200)
        light.light_component.set_editor_property("light_color", color)
        light.light_component.set_editor_property("source_width", 500)
        light.light_component.set_editor_property("source_height", 500)
    camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(2550, 250, 1650), unreal.Rotator(-25, 180, 0))
    camera.set_actor_label("Batch03_UnrealReviewCamera")
    camera.camera_component.set_editor_property("field_of_view", 52)
    for index, room in enumerate(("Airlock", "Cargo", "MachineShop", "EVA", "Science")):
        seed = actors.spawn_actor_from_class(unreal.WorldItemSeedPoint, unreal.Vector(-1000+index*500, 1050, 20), unreal.Rotator())
        seed.set_actor_label("SeedPreview_" + room)
        seed.set_editor_property("catalog", catalog)
        seed.set_editor_property("room_profile", unreal.Name(room))
        seed.set_editor_property("seed", 4103+index)
        seed.set_editor_property("seed_on_begin_play", False)
    if not level.save_current_level():
        raise RuntimeError("Could not save review level " + MAP_PATH)


def clean_generated_content():
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
        if unreal.EditorAssetLibrary.does_asset_exist(SAFE_MAP_PATH):
            level.load_level(SAFE_MAP_PATH)
        unreal.EditorAssetLibrary.delete_asset(MAP_PATH)
    if unreal.EditorAssetLibrary.does_directory_exist(ROOT):
        unreal.EditorAssetLibrary.delete_directory(ROOT)
        leftovers = unreal.EditorAssetLibrary.list_assets(ROOT, recursive=True, include_folder=False)
        if leftovers: raise RuntimeError(f"Could not clean generated Unreal batch: {leftovers}")
    for path in (ROOT, MESH_PATH, MATERIAL_PATH, WEAPON_DATA_PATH, ITEM_DATA_PATH, BP_GEAR_PATH, BP_OBJECT_PATH):
        unreal.EditorAssetLibrary.make_directory(path)


def main():
    unreal.log("Building Salvage Gameplay Batch 03 entirely in Unreal...")
    clean_generated_content()
    materials = build_materials()
    fab_mappings = load_fab_mappings()
    meshes = {}
    for d in GEAR:
        is_first_use = d["id"] in FIRST_USE_REFERENCES
        metadata = {
            "ContentId": d["id"], "Rooms": ",".join(d["rooms"]), "Weight": d["weight"],
            "Kind": "ShipboardWeapon", "VisualState": "FactoryFirstUse" if is_first_use else "StandardIssue",
        }
        if is_first_use:
            metadata["ReferenceArt"] = FIRST_USE_REFERENCES[d["id"]]
        fab_entry = fab_mappings.get(d["id"])
        if fab_entry and fab_entry.get("donorModules"):
            metadata["FabChassis"] = fab_entry["unrealAsset"]
            metadata["FabDonorAssets"] = ",".join(module["unrealAsset"] for module in fab_entry["donorModules"])
            metadata["VisualAssembly"] = "Fab modular composite plus concept-specific Geometry Script head"
            dynamic_mesh = composite_fab_weapon_mesh(d, fab_entry)
        else:
            dynamic_mesh = gear_mesh(d)
        meshes[d["id"]] = static_mesh(
            d["id"], dynamic_mesh, materials["first_use" if is_first_use else "gear"], metadata)
    for d in OBJECTS:
        mat = materials["hazard"] if d["id"] == "ExplosiveBoltCaddy" else materials["pickup" if d["pickup"] else "prop"]
        meshes[d["id"]] = static_mesh(d["id"], object_mesh(d), mat, {
            "ContentId": d["id"], "Rooms": ",".join(d["rooms"]), "Weight": d["weight"], "Kind": "WorldObject"})
    gear_bps, weapon_defs, weapon_visuals = build_gear(meshes, fab_mappings)
    object_bps, item_defs = build_objects(meshes)
    catalog = build_catalog(gear_bps, object_bps)
    wire_districts(catalog)
    build_review_map({**gear_bps, **object_bps}, materials, catalog)
    if not unreal.EditorAssetLibrary.save_directory(ROOT, only_if_is_dirty=False, recursive=True):
        raise RuntimeError("Could not save generated Unreal batch " + ROOT)
    expected_assets = (
        [f"{MESH_PATH}/SM_{d['id']}" for d in GEAR + OBJECTS]
        + [f"{WEAPON_DATA_PATH}/DA_Weapon_{d['id']}" for d in GEAR]
        + [f"{ITEM_DATA_PATH}/DA_Item_{d['id']}" for d in OBJECTS if d["pickup"]]
        + [f"{BP_GEAR_PATH}/BP_Weapon_{d['id']}" for d in GEAR]
        + [f"{BP_OBJECT_PATH}/BP_{'Pickup' if d['pickup'] else 'Prop'}_{d['id']}" for d in OBJECTS]
        + [CATALOG_PATH, MAP_PATH]
    )
    missing_assets = [path for path in expected_assets if not unreal.EditorAssetLibrary.does_asset_exist(path)]
    if missing_assets:
        raise RuntimeError("Generated assets failed validation: " + ", ".join(missing_assets))
    if len(catalog.get_editor_property("entries")) != len(GEAR) + len(OBJECTS):
        raise RuntimeError("Seed catalog entry count does not match generated actor count")
    records = []
    for d in GEAR + OBJECTS:
        bounds = meshes[d["id"]].get_bounds().box_extent * 2
        record = {"id": d["id"], "mesh": meshes[d["id"]].get_path_name(), "size_cm": [bounds.x, bounds.y, bounds.z],
                  "blueprint": (gear_bps if d in GEAR else object_bps)[d["id"]].get_path_name(), "rooms": d["rooms"]}
        if d in GEAR:
            visual = weapon_visuals[d["id"]]
            record["gameplay_visual_mesh"] = visual["mesh"].get_path_name()
            if visual["fab"] and visual["fab"].get("donorModules"):
                record["visual_source"] = "Fab modular composite"
                record["fab_donor_assets"] = [module["unrealAsset"] for module in visual["fab"]["donorModules"]]
            else:
                record["visual_source"] = "Fab chassis" if visual["fab"] else "Procedural fallback"
            if visual["fab"]:
                record["fab_mapping_confidence"] = visual["fab"]["confidence"]
                record["fab_adaptation"] = visual["fab"]["adaptation"]
        if d["id"] in FIRST_USE_REFERENCES:
            record.update({"visual_state": "FactoryFirstUse", "reference_art": FIRST_USE_REFERENCES[d["id"]],
                           "material": materials["first_use"].get_path_name()})
        records.append(record)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps({"source": "Unreal Geometry Scripting", "mesh_count": len(meshes),
        "weapon_definition_count": len(weapon_defs), "item_definition_count": len(item_defs),
        "blueprint_count": len(gear_bps)+len(object_bps), "material_count": len(materials),
        "first_use_material": materials["first_use"].get_path_name(),
        "first_use_assets": sorted(FIRST_USE_REFERENCES),
        "fab_visual_count": sum(1 for visual in weapon_visuals.values() if visual["fab"]),
        "fab_mapping_file": str(FAB_MAPPING_PATH),
        "catalog": catalog.get_path_name(), "review_map": MAP_PATH,
        "district_seed_counts": {"small": 4, "medium": 7, "large": 10},
        "validated_asset_count": len(expected_assets), "assets": records}, indent=2), encoding="utf-8")
    unreal.log(f"Salvage Batch 03 Unreal build complete: {len(meshes)} meshes, {len(records)} actors, catalog and review map")


if __name__ == "__main__":
    main()
