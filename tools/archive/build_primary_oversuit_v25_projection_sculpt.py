"""Build the first projection-guided primary oversuit shell as an independent Manny skeletal asset."""

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
REPORT = PROJECT / "Saved/Reports/PrimaryOversuitV25ProjectionSculpt.json"
SOURCE_PATH = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"
TARGET_PATH = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt/Working/Iteration_01/SKM_PrimaryOversuit_ProjectionShell_I01"
MATERIAL_PATH = "/Game/Characters/Player/Undersuit/MetaHuman/MI_MH_CryoBodysuit_Standard"
OFFSET_CM = 1.8


def vec(value):
    return [value.x, value.y, value.z]


source = unreal.EditorAssetLibrary.load_asset(SOURCE_PATH)
if not isinstance(source, unreal.SkeletalMesh):
    raise RuntimeError(f"Missing skeletal source: {SOURCE_PATH}")

skeleton = source.get_editor_property("skeleton")
mesh = unreal.DynamicMesh()
copy_options = unreal.GeometryScriptCopyMeshFromAssetOptions()
read_lod = unreal.GeometryScriptMeshReadLOD()
mesh, copy_outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh(
    source, mesh, copy_options, read_lod
)

offset_options = unreal.GeometryScriptMeshOffsetOptions()
offset_options.offset_distance = OFFSET_CM
offset_options.solve_steps = 4
offset_options.smooth_alpha = 0.15
offset_options.reproject_during_smoothing = True
mesh.apply_mesh_offset(offset_options)

if unreal.EditorAssetLibrary.does_asset_exist(TARGET_PATH):
    unreal.EditorAssetLibrary.delete_asset(TARGET_PATH)

create_options = unreal.GeometryScriptCreateNewSkeletalMeshAssetOptions()
create_options.enable_recompute_normals = True
create_options.enable_recompute_tangents = True
create_options.use_original_vertex_order = True
material = unreal.EditorAssetLibrary.load_asset(MATERIAL_PATH)
if material:
    create_options.materials = {"Material_0": material, "Material_1": material}

created = unreal.GeometryScript_NewAssetUtils.create_new_skeletal_mesh_asset_from_mesh(
    mesh, skeleton, TARGET_PATH, create_options
)
if isinstance(created, tuple):
    asset, create_outcome = created
else:
    asset, create_outcome = created, "unknown"
if not isinstance(asset, unreal.SkeletalMesh):
    raise RuntimeError(f"Failed creating V25 skeletal shell: {created}")

unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.AssetRole", "PrimaryOversuitProjectionShell")
unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.Iteration", "V25.I01")
unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.IndependentWearable", "true")
unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.ReferenceMethod", "calibrated_front_profile_rear_projection")
unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.RuntimeReady", "false")
unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)

bounds = asset.get_bounds()
report = {
    "status": "projection_shell_created",
    "asset": asset.get_path_name(),
    "source": source.get_path_name(),
    "skeleton": skeleton.get_path_name(),
    "copy_outcome": str(copy_outcome),
    "create_outcome": str(create_outcome),
    "normal_offset_cm": OFFSET_CM,
    "vertices": mesh.get_vertex_count(),
    "triangles": mesh.get_triangle_count(),
    "bounds": {"origin": vec(bounds.origin), "extent": vec(bounds.box_extent)},
    "concept_references": [
        "Art/Characters/PlayerSuits/RealityScan/V25_ConceptLock/Input/00_front.png",
        "Art/Characters/PlayerSuits/RealityScan/V25_ConceptLock/Input/01_profile.png",
        "Art/Characters/PlayerSuits/RealityScan/V25_ConceptLock/Input/02_rear.png",
    ],
    "independent_wearable": True,
    "runtime_ready": False,
    "notes": "First sculpting blank: fitted offset shell retaining the Manny skeleton and skin weights. Helmet, collar, life-support pack, and class modules remain separate follow-on pieces.",
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"V25 projection sculpt created: {asset.get_path_name()}")
unreal.log(f"V25 projection sculpt report: {REPORT}")
