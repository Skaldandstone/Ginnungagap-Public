"""Build the V25 I04 full-body functional-detail pass around the Quinn shell.

I04 keeps the smooth concept-sculpt helmet and life-support pieces from I03,
replaces the oversized chest bib, and carries the same restrained hard-suit
language through the waist, forearms, knees, and boots.  All geometry is still
pose-fit review geometry; it is not the final segmented or skinned wearable.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
REPORT = PROJECT / "Saved/Reports/PrimaryOversuitV25FunctionalDetailI04.json"
ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt"
FOLDER = ROOT + "/Working/Iteration_04_FunctionalDetail"
I03 = ROOT + "/Working/Iteration_03_ConceptSculpt"
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


def require_material(path):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(asset, unreal.MaterialInterface):
        raise RuntimeError(f"Missing material: {path}")
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
        "Ginnungagap.AssetRole": "PrimaryOversuitFunctionalDetailModule",
        "Ginnungagap.ModuleRole": role,
        "Ginnungagap.Iteration": "V25.I04",
        "Ginnungagap.IndependentWearable": "true",
        "Ginnungagap.ReferenceMethod": "FrontProfileRearConceptPoseFit",
        "Ginnungagap.RuntimeReady": "false",
    }
    for key, value in metadata.items():
        unreal.EditorAssetLibrary.set_metadata_tag(asset, key, value)
    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


unreal.EditorAssetLibrary.make_directory(FOLDER)

hard_material = require_material(I03 + "/Materials/M_V25_I03_HardShellReview")
trim_material = require_material(I03 + "/Materials/M_V25_I03_TrimReview")
screen_material = require_material(I03 + "/Materials/M_V25_I03_ScreenReview")

assets = {}

# A much smaller central mounting plate replaces the I03 torso-wide bib.  The
# upper pads merely bridge the webbing to the computer instead of widening the
# chest silhouette.
mesh = unreal.DynamicMesh()
capsule(mesh, (0.0, -11.7, 107.2), 6.4, 5.8, (1.12, 0.25, 1.0))
assets["ChestMount"] = create_asset("SM_V25_I04_ChestMount", mesh, hard_material, "ChestMount")

# The pressure-control computer is compact and distinct from its backing plate,
# closer to the small instrument package in the original art.
mesh = unreal.DynamicMesh()
capsule(mesh, (0.0, -13.7, 110.5), 4.0, 3.0, (1.22, 0.30, 1.0))
assets["ChestComputer"] = create_asset(
    "SM_V25_I04_ChestComputer", mesh, screen_material, "ChestComputer"
)

# Soft-edged waist hardware gives the chest system a visual endpoint and makes
# the upper and lower suit read as one wearable assembly.
mesh = unreal.DynamicMesh()
torus(mesh, (0.0, 0.3, 95.3), 14.5, 1.05, (1.0, 0.70, 1.0))
assets["WaistHarness"] = create_asset(
    "SM_V25_I04_WaistHarness", mesh, trim_material, "WaistHarness"
)

mesh = unreal.DynamicMesh()
ellipsoid(mesh, (0.0, -10.8, 95.3), (2.8, 1.0, 2.0), steps=40)
assets["WaistBuckle"] = create_asset(
    "SM_V25_I04_WaistBuckle", mesh, trim_material, "WaistBuckle"
)

# Shallow forearm shells follow Quinn's angled reference pose.  Their low depth
# keeps the soft pressure garment visible around all sides.
mesh = unreal.DynamicMesh()
ellipsoid(mesh, (-41.8, -2.6, 101.8), (3.5, 1.45, 7.6), (34.0, 0.0, 0.0), 48)
ellipsoid(mesh, (41.8, -2.6, 101.8), (3.5, 1.45, 7.6), (-34.0, 0.0, 0.0), 48)
assets["ForearmGuards"] = create_asset(
    "SM_V25_I04_ForearmGuards", mesh, trim_material, "ForearmGuards"
)

# One subdued outer-arm status display, not a second bulky weapon-like module.
mesh = unreal.DynamicMesh()
ellipsoid(mesh, (43.1, -4.0, 102.2), (2.0, 0.68, 3.7), (-34.0, 0.0, 0.0), 40)
assets["ForearmDisplay"] = create_asset(
    "SM_V25_I04_ForearmDisplay", mesh, screen_material, "ForearmDisplay"
)

# Knee shells and ankle/toe reinforcement repeat the same rounded, restrained
# visual language instead of introducing angular power-armour plates.
mesh = unreal.DynamicMesh()
ellipsoid(mesh, (-10.6, -4.3, 52.0), (4.6, 1.55, 6.4), steps=48)
ellipsoid(mesh, (10.6, -4.3, 52.0), (4.6, 1.55, 6.4), steps=48)
assets["KneeGuards"] = create_asset(
    "SM_V25_I04_KneeGuards", mesh, trim_material, "KneeGuards"
)

mesh = unreal.DynamicMesh()
ellipsoid(mesh, (-9.3, -6.0, 4.6), (5.8, 6.2, 2.7), steps=48)
ellipsoid(mesh, (9.3, -6.0, 4.6), (5.8, 6.2, 2.7), steps=48)
assets["BootArmor"] = create_asset(
    "SM_V25_I04_BootArmor", mesh, trim_material, "BootArmor"
)

# I03 established the correct white shell language but its pack ran almost the
# full torso height.  This shorter, higher replacement preserves the concept's
# compact portable life-support silhouette.
mesh = unreal.DynamicMesh()
capsule(mesh, (0.0, 13.0, 105.5), 8.0, 16.0, (1.28, 0.54, 1.0))
ellipsoid(mesh, (0.0, 13.1, 132.8), (8.4, 4.0, 3.2), steps=40)
assets["LifeSupportPack"] = create_asset(
    "SM_V25_I04_LifeSupportPack", mesh, hard_material, "LifeSupportPack"
)

mesh = unreal.DynamicMesh()
capsule(mesh, (0.0, 17.7, 109.5), 5.1, 9.0, (1.28, 0.20, 1.0))
ellipsoid(mesh, (0.0, 17.8, 130.8), (5.8, 0.8, 1.7), steps=36)
assets["LifeSupportDetail"] = create_asset(
    "SM_V25_I04_LifeSupportDetail", mesh, trim_material, "LifeSupportDetail"
)

for name, asset in assets.items():
    bounds = asset.get_bounds()
    size = bounds.box_extent * 2.0
    unreal.log(f"I04 {name}: {size.x:.2f} x {size.y:.2f} x {size.z:.2f} cm")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "functional_detail_pose_fit_created",
    "iteration": "V25.I04",
    "method": "Unreal Geometry Script smooth pose-fit modules authored against concept and Quinn shell",
    "base_shell": ROOT + "/Working/Iteration_02_ConceptSilhouette/SKM_PrimaryOversuit_QuinnProjectionShell_I02",
    "reused_i03_modules": [
        "HelmetBubble", "HelmetHardware", "PressureCollar", "HarnessStraps",
    ],
    "excluded_modules": [
        "I02ProjectionBlocks", "I03ChestHarness", "I03ChestComputer",
        "I03LifeSupportPack", "I03LifeSupportDetail",
    ],
    "materials": {
        "hard_shell": hard_material.get_path_name(),
        "trim": trim_material.get_path_name(),
        "screen": screen_material.get_path_name(),
    },
    "assets": {name: asset.get_path_name() for name, asset in assets.items()},
    "pose_fit_only": True,
    "runtime_ready": False,
}, indent=2), encoding="utf-8")
unreal.EditorAssetLibrary.save_directory(FOLDER)
unreal.log("PRIMARY OVERSUIT V25 I04: functional-detail pose-fit complete")
