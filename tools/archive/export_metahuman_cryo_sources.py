"""Export the assembled MetaHuman body and clothing meshes for a continuous bodysuit rebuild."""

import json
import os

import unreal


PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
OUTPUT_DIR = os.path.join(PROJECT_DIR, "Build", "Unreal", "PlayerSuits", "MetaHumanCryoSources")
REPORT_PATH = os.path.join(PROJECT_DIR, "Saved", "MetaHumanCryoSourceExport.json")
SOURCES = {
    "Body": "/Game/Characters/MetaHumans/Assembled/PlayerFace01/Body/SKM_MHC_Face01_Ada_BodyMesh",
    "Outfit": "/Game/Characters/MetaHumans/Assembled/PlayerFace01/Clothing/MHC_Face01_Ada_Outfits",
}


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    exports = []
    for label, asset_path in SOURCES.items():
        mesh = unreal.EditorAssetLibrary.load_asset(asset_path)
        if not isinstance(mesh, unreal.SkeletalMesh):
            raise RuntimeError(f"Missing MetaHuman {label} mesh: {asset_path}")

        filename = os.path.join(OUTPUT_DIR, f"MHC_Face01_Ada_{label}_Recovered.fbx")
        task = unreal.AssetExportTask()
        task.set_editor_property("object", mesh)
        task.set_editor_property("filename", filename)
        task.set_editor_property("automated", True)
        task.set_editor_property("prompt", False)
        task.set_editor_property("replace_identical", True)
        task.set_editor_property("write_empty_files", False)
        exported = unreal.Exporter.run_asset_export_task(task)
        exports.append({
            "label": label,
            "asset": mesh.get_path_name(),
            "filename": filename,
            "bytes": os.path.getsize(filename) if os.path.isfile(filename) else 0,
            "exported": bool(exported),
        })

    status = "pass" if all(item["exported"] and item["bytes"] > 0 for item in exports) else "fail"
    with open(REPORT_PATH, "w", encoding="utf-8") as report_file:
        json.dump({"status": status, "exports": exports}, report_file, indent=2)
    if status != "pass":
        raise RuntimeError("One or more MetaHuman source exports failed")
    unreal.log("METAHUMAN_CRYO_SOURCE_EXPORT complete")


main()
