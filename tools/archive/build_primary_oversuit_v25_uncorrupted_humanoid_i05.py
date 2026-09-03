"""Build V25 I05 from the new uncorrupted-humanoid concept language.

This pass deliberately replaces the smooth I03/I04 applique shapes with the
grounded industrial pressure-suit cues established by the August concept sheet:
warm worn fabric, dark load-bearing webbing, compact rectangular instruments,
segmented off-white pressure hardware, orange indexing marks, substantial boots,
and a short serviceable life-support pack.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
REPORT = PROJECT / "Saved/Reports/PrimaryOversuitV25UncorruptedHumanoidI05.json"
ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt"
FOLDER = ROOT + "/Working/Iteration_05_UncorruptedHumanoid"
MATERIAL_FOLDER = FOLDER + "/Materials"
PRIMITIVE = unreal.GeometryScriptPrimitiveOptions()
NORMALS = unreal.GeometryScriptCalculateNormalsOptions(angle_weighted=True, area_weighted=True)
REVOLVE = unreal.GeometryScriptRevolveOptions()


def xf(x=0.0, y=0.0, z=0.0, pitch=0.0, yaw=0.0, roll=0.0,
       sx=1.0, sy=1.0, sz=1.0):
    return unreal.Transform(
        location=unreal.Vector(x, y, z),
        rotation=unreal.Rotator(pitch=pitch, yaw=yaw, roll=roll),
        scale=unreal.Vector(sx, sy, sz),
    )


def material(name, color, roughness, metallic=0.0):
    path = f"{MATERIAL_FOLDER}/{name}"
    existing = unreal.EditorAssetLibrary.load_asset(path)
    if isinstance(existing, unreal.Material):
        return existing
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIAL_FOLDER, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not isinstance(asset, unreal.Material):
        raise RuntimeError(f"Could not create {path}")
    base = unreal.MaterialEditingLibrary.create_material_expression(
        asset, unreal.MaterialExpressionConstant3Vector, -360, -40
    )
    base.set_editor_property("constant", unreal.LinearColor(*color, 1.0))
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        asset, unreal.MaterialExpressionConstant, -360, 100
    )
    rough.set_editor_property("r", roughness)
    metal = unreal.MaterialEditingLibrary.create_material_expression(
        asset, unreal.MaterialExpressionConstant, -360, 200
    )
    metal.set_editor_property("r", metallic)
    unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    unreal.MaterialEditingLibrary.recompile_material(asset)
    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


def ellipsoid(mesh, center, half_size, rotation=(0.0, 0.0, 0.0), steps=48):
    mesh.append_sphere_lat_long(
        PRIMITIVE,
        xf(*center, pitch=rotation[0], yaw=rotation[1], roll=rotation[2],
           sx=half_size[0] / 10.0, sy=half_size[1] / 10.0, sz=half_size[2] / 10.0),
        10.0,
        steps,
        max(24, steps // 2),
    )


def capsule(mesh, base, radius, line_length, scale=(1.0, 1.0, 1.0), rotation=(0.0, 0.0, 0.0)):
    mesh.append_capsule(
        PRIMITIVE,
        xf(*base, pitch=rotation[0], yaw=rotation[1], roll=rotation[2],
           sx=scale[0], sy=scale[1], sz=scale[2]),
        radius,
        line_length,
        10,
        32,
        4,
    )


def torus(mesh, center, major, minor, scale=(1.0, 1.0, 1.0), rotation=(0.0, 0.0, 0.0)):
    mesh.append_torus(
        PRIMITIVE,
        xf(*center, pitch=rotation[0], yaw=rotation[1], roll=rotation[2],
           sx=scale[0], sy=scale[1], sz=scale[2]),
        REVOLVE,
        major,
        minor,
        64,
        16,
    )


def box(mesh, center, dimensions, rotation=(0.0, 0.0, 0.0)):
    mesh.append_box(
        PRIMITIVE,
        xf(*center, pitch=rotation[0], yaw=rotation[1], roll=rotation[2]),
        dimensions[0], dimensions[1], dimensions[2],
        2, 2, 2,
    )


def create_asset(name, mesh, assigned_material, role):
    path = f"{FOLDER}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        if not unreal.EditorAssetLibrary.delete_asset(path):
            raise RuntimeError(f"Could not replace {path}")
    mesh.auto_repair_normals()
    mesh.recompute_normals(NORMALS)
    asset, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
        mesh, path, unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    )
    if not isinstance(asset, unreal.StaticMesh) or outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError(f"Could not create {path}: {outcome}")
    slot = unreal.StaticMaterial()
    slot.set_editor_property("material_interface", assigned_material)
    slot.set_editor_property("material_slot_name", unreal.Name(role))
    asset.set_editor_property("static_materials", [slot])
    body = asset.get_editor_property("body_setup")
    if body:
        body.set_editor_property(
            "collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
        )
    metadata = {
        "Ginnungagap.AssetRole": "PrimaryOversuitUncorruptedHumanoidModule",
        "Ginnungagap.ModuleRole": role,
        "Ginnungagap.Iteration": "V25.I05",
        "Ginnungagap.IndependentWearable": "true",
        "Ginnungagap.ReferenceMethod": "UncorruptedHumanoidBaselineConcept",
        "Ginnungagap.RuntimeReady": "false",
    }
    for key, value in metadata.items():
        unreal.EditorAssetLibrary.set_metadata_tag(asset, key, value)
    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


unreal.EditorAssetLibrary.make_directory(FOLDER)
unreal.EditorAssetLibrary.make_directory(MATERIAL_FOLDER)

fabric = material("M_V25_I05B_WarmPressureFabric", (0.205, 0.195, 0.175), 0.94)
hard = material("M_V25_I05B_WornOffWhiteHardware", (0.275, 0.255, 0.215), 0.76, 0.12)
webbing = material("M_V25_I05B_LoadBearingWebbing", (0.030, 0.034, 0.037), 0.80, 0.05)
metal = material("M_V25_I05B_DarkMechanism", (0.055, 0.060, 0.064), 0.48, 0.58)
screen = material("M_V25_I05B_InstrumentGlass", (0.018, 0.080, 0.105), 0.24, 0.22)
orange = material("M_V25_I05B_OrangeIndexing", (0.34, 0.085, 0.012), 0.62, 0.08)
visor = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Player/Suit/Materials/MI_Suit_Visor")
if not isinstance(visor, unreal.MaterialInterface):
    raise RuntimeError("Missing existing pressure-suit visor material")

assets = {}

# Keep the review visor slightly smaller and more face-shaped than I03's globe.
# The opaque review material is temporary; the production visor remains clear.
mesh = unreal.DynamicMesh()
ellipsoid(mesh, (0.0, -1.4, 158.0), (16.4, 17.2, 19.5), steps=72)
assets["VisorEnvelope"] = create_asset(
    "SM_V25_I05_VisorEnvelope", mesh, visor, "VisorEnvelope"
)

# Two pressure seals, mechanical ear housings, and a narrow crown service rail.
mesh = unreal.DynamicMesh()
torus(mesh, (0.0, 0.6, 137.0), 17.5, 1.8, (1.0, 0.82, 1.0))
torus(mesh, (0.0, 0.6, 132.9), 18.1, 1.45, (1.0, 0.78, 1.0))
ellipsoid(mesh, (-17.0, 0.0, 152.0), (2.8, 4.3, 5.8), steps=40)
ellipsoid(mesh, (17.0, 0.0, 152.0), (2.8, 4.3, 5.8), steps=40)
ellipsoid(mesh, (0.0, 1.0, 177.0), (3.0, 5.2, 1.5), steps=36)
assets["HelmetPressureHardware"] = create_asset(
    "SM_V25_I05_HelmetPressureHardware", mesh, hard, "HelmetPressureHardware"
)

# Black structural webbing establishes the reference sheet's X-harness and
# continues to the hips instead of ending at a floating chest plate.
mesh = unreal.DynamicMesh()
capsule(mesh, (-10.5, -9.8, 110.0), 1.45, 29.0, (1.0, 0.52, 1.0), (-7.0, 0.0, 0.0))
capsule(mesh, (10.5, -9.8, 110.0), 1.45, 29.0, (1.0, 0.52, 1.0), (7.0, 0.0, 0.0))
capsule(mesh, (-12.0, -8.8, 83.5), 1.3, 17.0, (1.0, 0.50, 1.0), (25.0, 0.0, 0.0))
capsule(mesh, (12.0, -8.8, 83.5), 1.3, 17.0, (1.0, 0.50, 1.0), (-25.0, 0.0, 0.0))
torus(mesh, (0.0, 0.0, 93.0), 17.0, 1.35, (1.0, 0.76, 1.0))
assets["LoadBearingHarness"] = create_asset(
    "SM_V25_I05_LoadBearingHarness", mesh, webbing, "LoadBearingHarness"
)

# Compact rectangular pressure controller: dark backing, off-white bezel, inset
# display, and four service cartridges below it.
mesh = unreal.DynamicMesh()
capsule(mesh, (0.0, -11.2, 105.5), 7.0, 7.5, (1.34, 0.24, 1.0))
assets["ChestRigBacking"] = create_asset(
    "SM_V25_I05_ChestRigBacking", mesh, webbing, "ChestRigBacking"
)

mesh = unreal.DynamicMesh()
capsule(mesh, (0.0, -13.0, 110.0), 4.8, 3.5, (1.26, 0.30, 1.0))
for x in (-6.0, -2.0, 2.0, 6.0):
    ellipsoid(mesh, (x, -12.7, 101.4), (1.45, 1.45, 3.5), steps=32)
assets["ChestEquipment"] = create_asset(
    "SM_V25_I05_ChestEquipment", mesh, hard, "ChestEquipment"
)

mesh = unreal.DynamicMesh()
capsule(mesh, (0.0, -14.7, 112.1), 3.4, 1.0, (1.25, 0.22, 1.0))
assets["ChestDisplay"] = create_asset(
    "SM_V25_I05_ChestDisplay", mesh, screen, "ChestDisplay"
)

# A practical utility belt and asymmetrical tool pouches break the clean toy-like
# symmetry of I04 while staying clear of the leg silhouette.
mesh = unreal.DynamicMesh()
ellipsoid(mesh, (-12.0, -11.2, 91.0), (3.4, 2.0, 4.4), steps=40)
ellipsoid(mesh, (11.6, -11.3, 90.4), (3.9, 2.0, 5.0), steps=40)
ellipsoid(mesh, (-17.0, -1.5, 84.5), (2.5, 3.7, 6.0), (0.0, 0.0, -5.0), 40)
assets["UtilityPouches"] = create_asset(
    "SM_V25_I05_UtilityPouches", mesh, webbing, "UtilityPouches"
)

# Rectangular, bone-aligned forearm housings replace the detached ellipses.
mesh = unreal.DynamicMesh()
ellipsoid(mesh, (-41.0, -2.7, 102.0), (4.0, 2.0, 7.4), (34.0, 0.0, 0.0), 48)
ellipsoid(mesh, (41.0, -2.7, 102.0), (4.0, 2.0, 7.4), (-34.0, 0.0, 0.0), 48)
assets["ForearmHousings"] = create_asset(
    "SM_V25_I05_ForearmHousings", mesh, hard, "ForearmHousings"
)

mesh = unreal.DynamicMesh()
ellipsoid(mesh, (42.2, -4.6, 102.4), (2.4, 0.65, 3.8), (-34.0, 0.0, 0.0), 36)
assets["ForearmDisplay"] = create_asset(
    "SM_V25_I05_ForearmDisplay", mesh, screen, "ForearmDisplay"
)

# Protective knees and shins are connected, layered hard parts rather than dots.
mesh = unreal.DynamicMesh()
for x in (-10.6, 10.6):
    ellipsoid(mesh, (x, -4.8, 52.0), (5.0, 1.9, 5.8), steps=44)
    ellipsoid(mesh, (x, -3.8, 40.5), (4.3, 1.45, 6.0), steps=44)
assets["KneeShinArmor"] = create_asset(
    "SM_V25_I05_KneeShinArmor", mesh, hard, "KneeShinArmor"
)

# Layered toe caps plus ankle closure rings make the footwear read as sealed
# magnetic pressure boots, consistent with the game's traversal system.
mesh = unreal.DynamicMesh()
for x in (-9.2, 9.2):
    ellipsoid(mesh, (x, -6.0, 4.8), (6.2, 6.4, 3.0), steps=48)
    torus(mesh, (x, -0.5, 15.0), 5.7, 1.0, (1.0, 0.76, 1.0))
assets["PressureBootHardware"] = create_asset(
    "SM_V25_I05_PressureBootHardware", mesh, hard, "PressureBootHardware"
)

# Short, serviceable rectangular PLSS with side bottles and a rear access panel.
mesh = unreal.DynamicMesh()
capsule(mesh, (0.0, 13.0, 104.0), 8.2, 16.0, (1.30, 0.55, 1.0))
capsule(mesh, (-12.2, 13.0, 105.0), 3.0, 17.0, (0.82, 1.0, 1.0))
capsule(mesh, (12.2, 13.0, 105.0), 3.0, 17.0, (0.82, 1.0, 1.0))
assets["LifeSupportPack"] = create_asset(
    "SM_V25_I05_LifeSupportPack", mesh, hard, "LifeSupportPack"
)

mesh = unreal.DynamicMesh()
capsule(mesh, (0.0, 18.0, 108.0), 5.2, 7.0, (1.28, 0.20, 1.0))
ellipsoid(mesh, (0.0, 18.4, 130.0), (5.5, 0.8, 1.7), steps=36)
assets["LifeSupportServicePanel"] = create_asset(
    "SM_V25_I05_LifeSupportServicePanel", mesh, metal, "LifeSupportServicePanel"
)

# Sparse orange registration marks provide family resemblance to both the new
# humanoid suits and the matching uncorrupted robotics.
mesh = unreal.DynamicMesh()
box(mesh, (0.0, -15.5, 120.2), (5.0, 0.45, 0.9))
box(mesh, (42.5, -5.5, 105.5), (2.2, 0.4, 0.8), (-34.0, 0.0, 0.0))
for x in (-10.6, 10.6):
    box(mesh, (x, -7.0, 52.8), (4.0, 0.45, 0.9))
box(mesh, (0.0, 20.1, 130.0), (5.0, 0.4, 0.8))
assets["OrangeIndexing"] = create_asset(
    "SM_V25_I05_OrangeIndexing", mesh, orange, "OrangeIndexing"
)

for name, asset in assets.items():
    bounds = asset.get_bounds()
    size = bounds.box_extent * 2.0
    unreal.log(f"I05 {name}: {size.x:.2f} x {size.y:.2f} x {size.z:.2f} cm")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "uncorrupted_humanoid_concept_pass_created",
    "iteration": "V25.I05",
    "reference": "docs/concept-art/reference/bloom/uncorrupted-humanoid-baselines.png",
    "base_shell": ROOT + "/Working/Iteration_02_ConceptSilhouette/SKM_PrimaryOversuit_QuinnProjectionShell_I02",
    "design_changes": [
        "warm light pressure fabric instead of near-black body stocking",
        "two-stage segmented helmet seal and mechanical ear hardware",
        "continuous dark load-bearing chest and hip webbing",
        "compact rectangular chest and forearm instruments",
        "connected knee-shin protection and layered pressure boots",
        "short rectangular serviceable life-support pack",
        "sparse orange equipment indexing shared with uncorrupted robots",
    ],
    "excluded_iterations": ["I02ProjectionBlocks", "I03Modules", "I04Modules"],
    "materials": {
        "fabric": fabric.get_path_name(),
        "hard": hard.get_path_name(),
        "webbing": webbing.get_path_name(),
        "metal": metal.get_path_name(),
        "screen": screen.get_path_name(),
        "orange": orange.get_path_name(),
        "temporary_visor": visor.get_path_name(),
    },
    "assets": {name: asset.get_path_name() for name, asset in assets.items()},
    "pose_fit_only": True,
    "runtime_ready": False,
}, indent=2), encoding="utf-8")
unreal.EditorAssetLibrary.save_directory(FOLDER)
unreal.log("PRIMARY OVERSUIT V25 I05: uncorrupted-humanoid concept pass complete")
