"""Import the locally licensed Cosmoart Fab weapon pack into an isolated Unreal root.

The raw Fab archive remains in Saved/FabSources and is never copied into shipping content.
This importer creates only integrated Unreal assets plus provenance and geometry reports.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
SOURCE_ROOT = PROJECT / "Saved/FabSources/CosmoartLowPolyWeapons/Source/low_poly_guns_fbx"
MAPPING_PATH = PROJECT / "Art/Weapons/Fab/CosmoartLowPolyWeapons/WeaponConceptMapping.json"
DEST_ROOT = "/Game/ThirdParty/Fab/CosmoartLowPolyWeapons"
MESH_ROOT = DEST_ROOT + "/Meshes"
TEXTURE_ROOT = DEST_ROOT + "/Textures"
REPORT_PATH = PROJECT / "Saved/Reports/FabCosmoartWeaponImport.json"
LISTING = "https://www.fab.com/listings/1f5dd738-5316-4845-9cbe-6bdc4a6e1f5f"


def asset_token(stem: str) -> str:
    return "_".join(part.capitalize() for part in stem.split("_"))


def import_texture() -> str:
    source = SOURCE_ROOT / "uv_palette.png"
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = TEXTURE_ROOT
    task.destination_name = "T_Cosmoart_WeaponPalette"
    task.automated = True
    task.replace_existing = True
    task.save = False
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    paths = list(task.imported_object_paths)
    return paths[0] if paths else ""


def import_mesh(source: Path) -> unreal.StaticMesh:
    name = "SM_Cosmoart_" + asset_token(source.stem)
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = MESH_ROOT
    task.destination_name = name
    task.automated = True
    task.replace_existing = True
    task.save = False

    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = False
    options.import_materials = True
    options.import_textures = True
    options.static_mesh_import_data.combine_meshes = True
    options.static_mesh_import_data.generate_lightmap_u_vs = True
    options.static_mesh_import_data.auto_generate_collision = False
    task.options = options

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    asset = unreal.EditorAssetLibrary.load_asset(f"{MESH_ROOT}/{name}")
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError(f"Fab FBX did not produce {MESH_ROOT}/{name}: {list(task.imported_object_paths)}")
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.Source", "Fab integrated asset")
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.FabListing", LISTING)
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.FabSeller", "Cosmoart")
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.FabLicense", "Fab Standard License")
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.SourceFile", str(source.relative_to(SOURCE_ROOT)))
    return asset


def main() -> None:
    if not SOURCE_ROOT.is_dir():
        raise RuntimeError(f"Local Fab source is unavailable: {SOURCE_ROOT}")
    mapping = json.loads(MAPPING_PATH.read_text(encoding="utf-8"))
    concept_ids_by_source: dict[str, list[str]] = {}
    for entry in mapping["mappings"]:
        concept_ids_by_source.setdefault(entry["source"].replace("\\", "/"), []).append(entry["id"])

    for path in (DEST_ROOT, MESH_ROOT, TEXTURE_ROOT):
        unreal.EditorAssetLibrary.make_directory(path)
    palette = import_texture()

    records = []
    sources = sorted(
        path for path in SOURCE_ROOT.rglob("*.fbx")
        if path.name not in {"all_guns.fbx", "desert_map.fbx"}
    )
    for source in sources:
        mesh = import_mesh(source)
        relative = source.relative_to(SOURCE_ROOT).as_posix()
        mapped_ids = concept_ids_by_source.get(relative, [])
        if mapped_ids:
            unreal.EditorAssetLibrary.set_metadata_tag(mesh, "Ginnungagap.ConceptMappings", ",".join(mapped_ids))
        bounds = mesh.get_bounds()
        size = bounds.box_extent * 2.0
        records.append({
            "source": relative,
            "asset": mesh.get_path_name(),
            "size_cm": [size.x, size.y, size.z],
            "mapped_concept_ids": mapped_ids,
            "material_slots": len(mesh.get_editor_property("static_materials")),
        })

    if len(records) != 29:
        raise RuntimeError(f"Expected 29 Fab weapon meshes, imported {len(records)}")
    if not unreal.EditorAssetLibrary.save_directory(DEST_ROOT, only_if_is_dirty=False, recursive=True):
        raise RuntimeError(f"Could not save imported Fab assets under {DEST_ROOT}")

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps({
        "listing": LISTING,
        "seller": "Cosmoart",
        "license": "Fab Standard License",
        "source_root": str(SOURCE_ROOT),
        "destination": DEST_ROOT,
        "palette": palette,
        "mesh_count": len(records),
        "mapped_mesh_count": sum(1 for record in records if record["mapped_concept_ids"]),
        "assets": records,
    }, indent=2), encoding="utf-8")
    unreal.log(f"Imported Cosmoart Fab weapon pack: {len(records)} meshes under {DEST_ROOT}")


if __name__ == "__main__":
    main()
