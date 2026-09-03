"""Build the clean V25 I03 concept-sculpt modules around the Quinn shell.

This pass intentionally excludes every I02 projection block.  The new meshes are
authored at character scale in Unreal coordinates (X width, Y depth, Z up) and
follow the original front/profile/rear concept's soft pressure-suit hierarchy.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
REPORT = PROJECT / "Saved/Reports/PrimaryOversuitV25ConceptSculptI03.json"
ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt"
FOLDER = ROOT + "/Working/Iteration_03_ConceptSculpt"
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


def translucent_visor_material():
    name = "M_V25_I03_FresnelVisorReview"
    path = f"{MATERIAL_FOLDER}/{name}"
    existing = unreal.EditorAssetLibrary.load_asset(path)
    if isinstance(existing, unreal.Material):
        return existing
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIAL_FOLDER, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not isinstance(asset, unreal.Material):
        raise RuntimeError(f"Could not create {path}")
    asset.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    asset.set_editor_property("two_sided", True)
    base = unreal.MaterialEditingLibrary.create_material_expression(
        asset, unreal.MaterialExpressionConstant3Vector, -360, -40
    )
    base.set_editor_property("constant", unreal.LinearColor(0.06, 0.16, 0.20, 1.0))
    opacity = unreal.MaterialEditingLibrary.create_material_expression(
        asset, unreal.MaterialExpressionFresnel, -360, 90
    )
    opacity.set_editor_property("exponent", 3.2)
    opacity.set_editor_property("base_reflect_fraction", 0.12)
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        asset, unreal.MaterialExpressionConstant, -360, 180
    )
    rough.set_editor_property("r", 0.08)
    specular = unreal.MaterialEditingLibrary.create_material_expression(
        asset, unreal.MaterialExpressionConstant, -360, 260
    )
    specular.set_editor_property("r", 0.85)
    unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(specular, "", unreal.MaterialProperty.MP_SPECULAR)
    unreal.MaterialEditingLibrary.recompile_material(asset)
    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


def ellipsoid(mesh, center, half_size, steps=48):
    mesh.append_sphere_lat_long(
        PRIMITIVE,
        xf(*center, sx=half_size[0] / 10.0, sy=half_size[1] / 10.0, sz=half_size[2] / 10.0),
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
        40,
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
        "Ginnungagap.AssetRole": "PrimaryOversuitConceptSculptModule",
        "Ginnungagap.ModuleRole": role,
        "Ginnungagap.Iteration": "V25.I03",
        "Ginnungagap.IndependentWearable": "true",
        "Ginnungagap.ReferenceMethod": "FrontProfileRearConceptSilhouette",
        "Ginnungagap.RuntimeReady": "false",
    }
    for key, value in metadata.items():
        unreal.EditorAssetLibrary.set_metadata_tag(asset, key, value)
    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


unreal.EditorAssetLibrary.make_directory(FOLDER)
unreal.EditorAssetLibrary.make_directory(MATERIAL_FOLDER)

soft_material = material("M_V25_I03_SoftSuitReview", (0.045, 0.052, 0.060), 0.88)
hard_material = material("M_V25_I03_HardShellReview", (0.60, 0.57, 0.50), 0.58, 0.08)
trim_material = material("M_V25_I03_TrimReview", (0.075, 0.082, 0.088), 0.48, 0.30)
screen_material = material("M_V25_I03_ScreenReview", (0.025, 0.095, 0.125), 0.28, 0.20)
visor_material = unreal.EditorAssetLibrary.load_asset(
    "/Game/Characters/Player/Suit/Materials/MI_Suit_Visor"
)
if not isinstance(visor_material, unreal.MaterialInterface):
    raise RuntimeError("Missing existing suit visor material")

assets = {}

# The clear pressure enclosure is almost spherical in front view, slightly
# deeper in profile, and stops at the upper collar rather than swallowing it.
mesh = unreal.DynamicMesh()
ellipsoid(mesh, (0.0, -0.8, 158.0), (17.4, 18.8, 20.7), 72)
assets["HelmetBubble"] = create_asset("SM_V25_I03_HelmetBubble", mesh, visor_material, "HelmetBubble")

# Hard helmet fittings: two restrained concentric brow/seal bands and compact
# ear mechanisms.  These are deliberately curved rather than boxed armor.
mesh = unreal.DynamicMesh()
torus(mesh, (0.0, -0.4, 141.2), 16.9, 1.35, (1.0, 0.94, 1.0))
for side in (-1.0, 1.0):
    capsule(mesh, (side * 16.2, -0.1, 150.5), 3.7, 7.8, (0.56, 0.72, 1.0))
assets["HelmetHardware"] = create_asset("SM_V25_I03_HelmetHardware", mesh, hard_material, "HelmetHardware")

# Broad, low pressure collar, matching the layered ring visible in all three
# concept views.  The rear is left intact to meet the backpack/helmet seals.
mesh = unreal.DynamicMesh()
torus(mesh, (0.0, 1.0, 135.4), 18.0, 2.15, (1.0, 0.82, 1.0))
torus(mesh, (0.0, 1.0, 131.5), 18.5, 1.75, (1.0, 0.78, 1.0))
assets["PressureCollar"] = create_asset("SM_V25_I03_PressureCollar", mesh, hard_material, "PressureCollar")

# A shallow capsule gives the chest unit the concept's softened rectangular
# outline without returning to the I02 box language.
mesh = unreal.DynamicMesh()
capsule(mesh, (0.0, -12.0, 100.5), 10.0, 10.5, (1.28, 0.30, 1.0))
ellipsoid(mesh, (-10.5, -10.6, 123.2), (5.0, 2.4, 8.0), 40)
ellipsoid(mesh, (10.5, -10.6, 123.2), (5.0, 2.4, 8.0), 40)
assets["ChestHarness"] = create_asset("SM_V25_I03_ChestHarness", mesh, hard_material, "ChestHarness")

mesh = unreal.DynamicMesh()
capsule(mesh, (0.0, -15.3, 108.0), 5.8, 5.0, (1.42, 0.34, 1.0))
assets["ChestComputer"] = create_asset("SM_V25_I03_ChestComputer", mesh, screen_material, "ChestComputer")

# Narrow webbing follows the chest instead of widening the torso silhouette.
mesh = unreal.DynamicMesh()
capsule(mesh, (-10.2, -9.2, 96.5), 1.9, 28.0, (1.0, 0.55, 1.0), (-13.0, 0.0, 0.0))
capsule(mesh, (10.2, -9.2, 96.5), 1.9, 28.0, (1.0, 0.55, 1.0), (13.0, 0.0, 0.0))
assets["HarnessStraps"] = create_asset("SM_V25_I03_HarnessStraps", mesh, trim_material, "HarnessStraps")

# The life-support pack stays compact and high on the back, with a softened
# rectangular shell plus a shallow rear service panel rather than a giant cube.
mesh = unreal.DynamicMesh()
capsule(mesh, (0.0, 13.2, 95.0), 10.0, 22.0, (1.36, 0.58, 1.0))
ellipsoid(mesh, (0.0, 13.6, 136.0), (10.8, 5.3, 4.2), 40)
assets["LifeSupportPack"] = create_asset("SM_V25_I03_LifeSupportPack", mesh, hard_material, "LifeSupportPack")

mesh = unreal.DynamicMesh()
capsule(mesh, (0.0, 19.0, 102.5), 6.6, 13.0, (1.35, 0.22, 1.0))
ellipsoid(mesh, (0.0, 19.6, 133.2), (7.8, 1.1, 2.2), 36)
assets["LifeSupportDetail"] = create_asset("SM_V25_I03_LifeSupportDetail", mesh, trim_material, "LifeSupportDetail")

for name, asset in assets.items():
    bounds = asset.get_bounds()
    size = bounds.box_extent * 2.0
    unreal.log(f"I03 {name}: {size.x:.2f} x {size.y:.2f} x {size.z:.2f} cm")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "clean_concept_sculpt_modules_created",
    "iteration": "V25.I03",
    "method": "Unreal Geometry Script smooth primitives authored against front/profile/rear concept",
    "base_shell": ROOT + "/Working/Iteration_02_ConceptSilhouette/SKM_PrimaryOversuit_QuinnProjectionShell_I02",
    "old_i02_projection_blocks_included": False,
    "materials": {
        "soft_suit": soft_material.get_path_name(),
        "hard_shell": hard_material.get_path_name(),
        "trim": trim_material.get_path_name(),
        "screen": screen_material.get_path_name(),
        "visor": visor_material.get_path_name(),
    },
    "assets": {name: asset.get_path_name() for name, asset in assets.items()},
    "runtime_ready": False,
}, indent=2), encoding="utf-8")
unreal.EditorAssetLibrary.save_directory(FOLDER)
unreal.log("PRIMARY OVERSUIT V25 I03: clean concept-sculpt modules complete")
