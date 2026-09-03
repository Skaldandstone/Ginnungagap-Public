"""Create the concept-proportioned Quinn shell while retaining the shared Manny skeleton."""

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
REPORT = PROJECT / "Saved/Reports/PrimaryOversuitV25QuinnProjectionShell.json"
SOURCE_PATH = "/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple"
TARGET_PATH = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt/Working/Iteration_02_ConceptSilhouette/SKM_PrimaryOversuit_QuinnProjectionShell_I02"
MATERIAL_PATH = "/Game/Characters/Player/Undersuit/MetaHuman/MI_MH_CryoBodysuit_Standard"
OFFSET_CM = 1.5

source = unreal.EditorAssetLibrary.load_asset(SOURCE_PATH)
if not isinstance(source, unreal.SkeletalMesh):
    raise RuntimeError(f"Missing Quinn source: {SOURCE_PATH}")
skeleton = source.get_editor_property("skeleton")
mesh = unreal.DynamicMesh()
mesh, copy_outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh(
    source, mesh, unreal.GeometryScriptCopyMeshFromAssetOptions(), unreal.GeometryScriptMeshReadLOD()
)
offset = unreal.GeometryScriptMeshOffsetOptions()
offset.offset_distance = OFFSET_CM
offset.solve_steps = 4
offset.smooth_alpha = 0.15
offset.reproject_during_smoothing = True
mesh.apply_mesh_offset(offset)
if unreal.EditorAssetLibrary.does_asset_exist(TARGET_PATH):
    unreal.EditorAssetLibrary.delete_asset(TARGET_PATH)
options = unreal.GeometryScriptCreateNewSkeletalMeshAssetOptions()
options.enable_recompute_normals = True
options.enable_recompute_tangents = True
options.use_original_vertex_order = True
material = unreal.EditorAssetLibrary.load_asset(MATERIAL_PATH)
if material:
    options.materials = {"Material_0": material, "Material_1": material}
created = unreal.GeometryScript_NewAssetUtils.create_new_skeletal_mesh_asset_from_mesh(mesh, skeleton, TARGET_PATH, options)
asset, create_outcome = created if isinstance(created, tuple) else (created, "unknown")
if not isinstance(asset, unreal.SkeletalMesh):
    raise RuntimeError(f"Could not create Quinn V25 shell: {created}")
unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.AssetRole", "PrimaryOversuitProjectionShell")
unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.Iteration", "V25.I02.Quinn")
unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.IndependentWearable", "true")
unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.SharedSkeleton", skeleton.get_path_name())
unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "concept_proportioned_shell_created",
    "asset": asset.get_path_name(),
    "source": source.get_path_name(),
    "skeleton": skeleton.get_path_name(),
    "normal_offset_cm": OFFSET_CM,
    "copy_outcome": str(copy_outcome),
    "create_outcome": str(create_outcome),
    "vertices": mesh.get_vertex_count(),
    "triangles": mesh.get_triangle_count(),
    "reason": "Quinn proportions match the original concept and authored projection-module centres while retaining the shared Manny skeleton.",
    "runtime_ready": False,
}, indent=2), encoding="utf-8")
unreal.log(f"Created V25 Quinn projection shell: {asset.get_path_name()}")
