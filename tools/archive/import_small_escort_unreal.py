"""Import and validate the concept-matched Small Utility Escort in Unreal.

Run with UnrealEditor-Cmd.  The script intentionally preserves the GLB scene's
authored mesh/material split, enables Nanite on every imported static mesh, and
writes a machine-readable report used by the subsequent showcase build.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
SOURCE = PROJECT / "Art/Ships/Exterior/ConceptMatch/SmallUtilityEscort/Exports/SM_Ship_SmallUtilityEscort_ConceptMatch.glb"
DEST = "/Game/Assets/Ships/Exterior/ConceptMatch/SmallUtilityEscort"
REPORT = PROJECT / "Saved/Reports/SmallEscortUnrealImport.json"
EXPECTED_CM = (140000.0, 26000.0, 32000.0)


def imported_static_meshes():
    result = []
    for path in unreal.EditorAssetLibrary.list_assets(DEST, recursive=True, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if isinstance(asset, unreal.StaticMesh):
            result.append(asset)
    return result


def import_source():
    if not SOURCE.exists():
        raise RuntimeError(f"Missing escort GLB: {SOURCE}")
    unreal.EditorAssetLibrary.make_directory(DEST)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(SOURCE))
    task.set_editor_property("destination_path", DEST)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("replace_existing_settings", False)
    # Interchange's bulk save can collide in Saved/ when another unattended editor
    # is running. Import first, then save each configured asset deterministically.
    task.set_editor_property("save", False)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    meshes = imported_static_meshes()
    if not meshes:
        raise RuntimeError(f"GLB import produced no StaticMesh assets under {DEST}")
    return meshes, list(task.get_editor_property("imported_object_paths"))


def configure_mesh(mesh):
    try:
        nanite = mesh.get_editor_property("nanite_settings")
        nanite.set_editor_property("enabled", True)
        mesh.set_editor_property("nanite_settings", nanite)
    except Exception as exc:
        unreal.log_warning(f"Nanite configuration skipped for {mesh.get_name()}: {exc}")
    try:
        mesh.set_editor_property("light_map_coordinate_index", 1)
    except Exception:
        pass
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)


def aggregate_local_bounds(meshes):
    mins = [float("inf")] * 3
    maxs = [float("-inf")] * 3
    entries = []
    for mesh in meshes:
        bounds = mesh.get_bounds()
        origin, extent = bounds.origin, bounds.box_extent
        lo = (origin.x - extent.x, origin.y - extent.y, origin.z - extent.z)
        hi = (origin.x + extent.x, origin.y + extent.y, origin.z + extent.z)
        for i in range(3):
            mins[i] = min(mins[i], lo[i])
            maxs[i] = max(maxs[i], hi[i])
        entries.append({"asset": mesh.get_path_name(), "origin_cm": [origin.x, origin.y, origin.z],
                        "extent_cm": [extent.x, extent.y, extent.z], "materials": len(mesh.static_materials)})
    size = [maxs[i] - mins[i] for i in range(3)]
    # Interchange may bake scene-node transforms into actors rather than mesh bounds.
    # This raw measurement is diagnostic; the showcase performs an aggregate actor check.
    return mins, maxs, size, entries


def main():
    unreal.log("Importing concept-matched Small Utility Escort...")
    meshes, imported_paths = import_source()
    for mesh in meshes:
        configure_mesh(mesh)
    mins, maxs, size, entries = aggregate_local_bounds(meshes)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "source": str(SOURCE), "destination": DEST, "static_mesh_count": len(meshes),
        "imported_object_count": len(imported_paths), "expected_overall_cm": EXPECTED_CM,
        "raw_combined_mesh_bounds_cm": {"min": mins, "max": maxs, "size": size},
        "nanite_requested": True, "uv1_lightmap_index_requested": True, "assets": entries,
    }
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.EditorAssetLibrary.save_directory(DEST)
    unreal.log(f"Small Escort import complete: {len(meshes)} meshes; report {REPORT}")


if __name__ == "__main__":
    main()
