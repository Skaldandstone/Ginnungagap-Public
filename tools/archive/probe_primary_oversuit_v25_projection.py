"""Probe the Manny-compatible bodysuit and Geometry Script skeletal APIs."""

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
REPORT = PROJECT / "Saved/Reports/PrimaryOversuitV25ProjectionProbe.json"
SOURCE = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"


source = unreal.EditorAssetLibrary.load_asset(SOURCE)
if not isinstance(source, unreal.SkeletalMesh):
    raise RuntimeError(f"Missing skeletal source: {SOURCE}")

dynamic_mesh = unreal.DynamicMesh()
copy_options = unreal.GeometryScriptCopyMeshFromAssetOptions()
read_lod = unreal.GeometryScriptMeshReadLOD()
copy_result = unreal.GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh(
    source, dynamic_mesh, copy_options, read_lod
)


def vector_values(value):
    return [value.x, value.y, value.z]

report = {
    "source": source.get_path_name(),
    "source_class": source.get_class().get_name(),
    "skeleton": source.get_editor_property("skeleton").get_path_name(),
    "bounds": {
        "origin": vector_values(source.get_bounds().origin),
        "extent": vector_values(source.get_bounds().box_extent),
    },
    "materials": [
        material.material_interface.get_path_name() if material.material_interface else None
        for material in source.get_editor_property("materials")
    ],
    "copy_result_type": type(copy_result).__name__,
    "copy_result": str(copy_result),
    "vertex_count": dynamic_mesh.get_vertex_count(),
    "triangle_count": dynamic_mesh.get_triangle_count(),
    "asset_utils_methods": [
        name for name in dir(unreal.GeometryScript_AssetUtils)
        if "skeletal" in name.lower() or "material" in name.lower()
    ],
    "dynamic_mesh_methods": [
        name for name in dir(dynamic_mesh)
        if any(token in name.lower() for token in ("offset", "smooth", "triangle", "vertex", "bounds"))
    ],
    "selection_types": [name for name in dir(unreal.GeometryScriptMeshSelectionType) if name.isupper()],
    "new_asset_options": [name for name in dir(unreal.GeometryScriptCreateNewSkeletalMeshAssetOptions()) if not name.startswith("_")],
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"V25 projection probe written to {REPORT}")
