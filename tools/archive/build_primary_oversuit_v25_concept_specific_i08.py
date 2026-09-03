"""Build V25 I08 concept-specific helmet, harness, and role equipment modules."""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory()).resolve()
REPORT = PROJECT / "Saved/Reports/PrimaryOversuitV25ConceptSpecificI08.json"
ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt"
FOLDER = ROOT + "/Working/Iteration_08_ConceptSpecificModules"
MATERIAL_ROOT = ROOT + "/Working/Iteration_07_ConceptAlignedRoleLineup/Materials"
PRIMITIVE = unreal.GeometryScriptPrimitiveOptions()
NORMALS = unreal.GeometryScriptCalculateNormalsOptions(angle_weighted=True, area_weighted=True)
REVOLVE = unreal.GeometryScriptRevolveOptions()
IDENTITY = unreal.Transform()


def xf(x=0.0, y=0.0, z=0.0, pitch=0.0, yaw=0.0, roll=0.0,
       sx=1.0, sy=1.0, sz=1.0):
    return unreal.Transform(
        location=unreal.Vector(x, y, z),
        rotation=unreal.Rotator(pitch=pitch, yaw=yaw, roll=roll),
        scale=unreal.Vector(sx, sy, sz),
    )


def ellipsoid(mesh, center, half_size, rotation=(0.0, 0.0, 0.0), steps=64):
    mesh.append_sphere_lat_long(
        PRIMITIVE,
        xf(*center, pitch=rotation[0], yaw=rotation[1], roll=rotation[2],
           sx=half_size[0] / 10.0, sy=half_size[1] / 10.0, sz=half_size[2] / 10.0),
        10.0, steps, max(32, steps // 2),
    )


def capsule(mesh, center, radius, line_length, scale=(1.0, 1.0, 1.0), rotation=(0.0, 0.0, 0.0)):
    mesh.append_capsule(
        PRIMITIVE,
        xf(*center, pitch=rotation[0], yaw=rotation[1], roll=rotation[2],
           sx=scale[0], sy=scale[1], sz=scale[2]),
        radius, line_length, 14, 56, 6,
    )


def torus(mesh, center, major, minor, scale=(1.0, 1.0, 1.0)):
    mesh.append_torus(
        PRIMITIVE,
        xf(*center, sx=scale[0], sy=scale[1], sz=scale[2]),
        REVOLVE, major, minor, 96, 20,
    )


def box(mesh, center, size):
    mesh.append_box(
        PRIMITIVE,
        xf(center[0], center[1], center[2] - size[2] * 0.5),
        size[0], size[1], size[2], 2, 2, 2,
    )


def create_asset(name, mesh, material, role, wearable=True):
    path = f"{FOLDER}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    mesh.auto_repair_normals()
    mesh.recompute_normals(NORMALS)
    asset, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
        mesh, path, unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    )
    if not isinstance(asset, unreal.StaticMesh) or outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError(f"Could not create {path}: {outcome}")
    slot = unreal.StaticMaterial()
    slot.set_editor_property("material_interface", material)
    slot.set_editor_property("material_slot_name", unreal.Name(role))
    asset.set_editor_property("static_materials", [slot])
    for key, value in {
        "Ginnungagap.AssetRole": "PrimaryOversuitConceptSpecificModule" if wearable else "PrimaryOversuitReviewProxy",
        "Ginnungagap.ModuleRole": role,
        "Ginnungagap.Iteration": "V25.I08",
        "Ginnungagap.IndependentWearable": str(wearable).lower(),
        "Ginnungagap.RuntimeReady": "false",
    }.items():
        unreal.EditorAssetLibrary.set_metadata_tag(asset, key, value)
    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
    return asset


unreal.EditorAssetLibrary.make_directory(FOLDER)
neutral = unreal.EditorAssetLibrary.load_asset(MATERIAL_ROOT + "/M_V25_I07_Crew_Hard")
visor = unreal.EditorAssetLibrary.load_asset(MATERIAL_ROOT + "/M_V25_I07_ClearPressureDome")
trim = unreal.EditorAssetLibrary.load_asset(MATERIAL_ROOT + "/M_V25_I07_Crew_Trim")
screen = unreal.EditorAssetLibrary.load_asset(MATERIAL_ROOT + "/M_V25_I07_Crew_Screen")
if not all(isinstance(value, unreal.MaterialInterface) for value in (neutral, visor, trim, screen)):
    raise RuntimeError("I07 material foundation is incomplete")

assets = {}

# Open bubble enclosure.  Unlike the earlier complete grey sphere, this uses a
# translucent material and is framed by separate authored shell components.
mesh = unreal.DynamicMesh()
ellipsoid(mesh, (0.0, -1.0, 174.2), (17.8, 19.4, 21.0), steps=80)
assets["PressureDome"] = create_asset("SM_V25_I08_PressureDome", mesh, visor, "PressureDome")

# One integrated oval pressure seal instead of three stacked torus bands.
mesh = unreal.DynamicMesh()
torus(mesh, (0.0, 0.5, 150.1), 18.4, 2.6, (1.0, 0.80, 1.0))
assets["IntegratedCollar"] = create_asset("SM_V25_I08_IntegratedCollar", mesh, neutral, "Hard")

# A single connected hard shell surrounds the dome.  The front opening is cut
# from a hollow ellipsoid, matching the concept's crown/side/rear helmet shell
# without the disconnected orbiting pieces seen in the first I08 render.
mesh = unreal.DynamicMesh()
ellipsoid(mesh, (0.0, 1.0, 174.0), (18.9, 20.0, 22.0), steps=88)
inner = unreal.DynamicMesh()
ellipsoid(inner, (0.0, 0.2, 174.0), (15.3, 17.4, 18.5), steps=80)
mesh.apply_mesh_boolean(
    IDENTITY, inner, IDENTITY,
    unreal.GeometryScriptBooleanOperation.SUBTRACT,
    unreal.GeometryScriptMeshBooleanOptions(),
)
opening = unreal.DynamicMesh()
box(opening, (0.0, -17.2, 174.0), (27.0, 33.0, 29.0))
mesh.apply_mesh_boolean(
    IDENTITY, opening, IDENTITY,
    unreal.GeometryScriptBooleanOperation.SUBTRACT,
    unreal.GeometryScriptMeshBooleanOptions(),
)
assets["HelmetFrame"] = create_asset("SM_V25_I08_HelmetFrame", mesh, neutral, "Hard")

# Preview-only head volume demonstrates that the dome is open and transparent.
mesh = unreal.DynamicMesh()
ellipsoid(mesh, (0.0, 1.2, 174.0), (8.4, 7.1, 10.6), steps=64)
assets["PreviewHead"] = create_asset("SM_V25_I08_PreviewHead", mesh, trim, "PreviewProxy", wearable=False)

# Narrow shoulder-to-waist webbing, compact rounded rectangular chest mount,
# and inset display.  The pressure garment remains visible around every piece.
mesh = unreal.DynamicMesh()
capsule(mesh, (-10.2, -11.2, 119.0), 1.6, 27.0, (1.0, 0.48, 1.0), (-12.0, 0.0, 0.0))
capsule(mesh, (10.2, -11.2, 119.0), 1.6, 27.0, (1.0, 0.48, 1.0), (12.0, 0.0, 0.0))
assets["HarnessWebbing"] = create_asset("SM_V25_I08_HarnessWebbing", mesh, trim, "Trim")

mesh = unreal.DynamicMesh()
box(mesh, (0.0, -12.7, 122.8), (21.5, 4.0, 16.5))
assets["ChestComputerFrame"] = create_asset("SM_V25_I08_ChestComputerFrame", mesh, neutral, "Hard")

mesh = unreal.DynamicMesh()
box(mesh, (0.0, -15.0, 124.2), (11.5, 1.4, 7.5))
assets["ChestComputerScreen"] = create_asset("SM_V25_I08_ChestComputerScreen", mesh, screen, "Screen")

# Shared shallow forearm and knee reinforcement.
mesh = unreal.DynamicMesh()
for side in (-1.0, 1.0):
    ellipsoid(mesh, (side * 42.0, -2.8, 117.0), (3.3, 1.25, 6.4), (side * -32.0, 0.0, 0.0), 56)
assets["ForearmShells"] = create_asset("SM_V25_I08_ForearmShells", mesh, neutral, "Hard")

mesh = unreal.DynamicMesh()
for side in (-1.0, 1.0):
    ellipsoid(mesh, (side * 10.6, -4.0, 57.0), (4.5, 1.4, 6.0), steps=56)
assets["KneeShells"] = create_asset("SM_V25_I08_KneeShells", mesh, neutral, "Hard")

# Role accents are deliberately small, removable pieces rather than alternate
# armor bodies.  Every mesh can receive a class accent material at assembly.
mesh = unreal.DynamicMesh()
box(mesh, (13.0, -13.2, 130.0), (5.0, 1.4, 3.2))
box(mesh, (0.0, -12.2, 101.0), (5.0, 1.5, 2.2))
assets["CrewModules"] = create_asset("SM_V25_I08_CrewModules", mesh, neutral, "Accent")

mesh = unreal.DynamicMesh()
for x in (-7.0, 0.0, 7.0):
    box(mesh, (x, -12.2, 100.0), (4.7, 1.8, 5.5))
box(mesh, (-13.0, -13.2, 130.0), (6.0, 1.5, 3.5))
assets["EngineeringModules"] = create_asset("SM_V25_I08_EngineeringModules", mesh, neutral, "Accent")

mesh = unreal.DynamicMesh()
box(mesh, (0.0, -13.4, 108.5), (12.0, 2.6, 10.0))
box(mesh, (0.0, -15.0, 108.5), (2.2, 1.1, 7.2))
box(mesh, (0.0, -15.1, 108.5), (7.2, 1.2, 2.2))
assets["MedicalModules"] = create_asset("SM_V25_I08_MedicalModules", mesh, neutral, "Accent")

mesh = unreal.DynamicMesh()
for side in (-1.0, 1.0):
    box(mesh, (side * 12.5, -13.2, 130.0), (6.0, 1.6, 3.5))
    box(mesh, (side * 7.0, -12.2, 100.0), (5.0, 1.8, 5.5))
assets["SecurityModules"] = create_asset("SM_V25_I08_SecurityModules", mesh, neutral, "Accent")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "concept_specific_modules_created",
    "iteration": "V25.I08",
    "concept_references": [
        "docs/concept-art/reference/suits/standard-suit-turnaround.png",
        "docs/concept-art/reference/suits/player-suit-role-lineup.png",
        "docs/concept-art/reference/suits/player-suit-hands-free-equipment-concept-v2.png",
    ],
    "design_changes": [
        "open translucent pressure dome",
        "single integrated collar",
        "connected hollow crown/side/rear helmet shell",
        "compact chest computer and narrow webbing",
        "small removable class modules",
        "no donor tactical bags, chest slab, belt, or thigh cases",
    ],
    "assets": {name: asset.get_path_name() for name, asset in assets.items()},
    "preview_head_is_not_wearable": True,
    "runtime_ready": False,
}, indent=2), encoding="utf-8")
unreal.EditorAssetLibrary.save_directory(FOLDER, only_if_is_dirty=False, recursive=True)
unreal.log("PRIMARY OVERSUIT V25 I08: concept-specific modules created")
