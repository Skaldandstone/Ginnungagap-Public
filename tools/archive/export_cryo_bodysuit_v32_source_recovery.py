"""Recover an editable FBX source from the preserved Unreal skeletal-mesh asset."""

import json
import os

import unreal


ASSET_PATH = "/Game/Characters/Player/Undersuit/CryoBodysuitV32/SK_CryoBodysuit_V32_Manny"
PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
OUTPUT_DIR = os.path.join(PROJECT_DIR, "Build", "Unreal", "PlayerSuits", "CryoBodysuitV32")
OUTPUT_FBX = os.path.join(OUTPUT_DIR, "SK_CryoBodysuit_V32_Manny_Recovered.fbx")
REPORT_PATH = os.path.join(PROJECT_DIR, "Saved", "CryoBodysuitV32SourceRecovery.json")


def write_report(payload):
    os.makedirs(os.path.dirname(REPORT_PATH), exist_ok=True)
    with open(REPORT_PATH, "w", encoding="utf-8") as report_file:
        json.dump(payload, report_file, indent=2)


def main():
    mesh = unreal.EditorAssetLibrary.load_asset(ASSET_PATH)
    if not isinstance(mesh, unreal.SkeletalMesh):
        write_report({"status": "fail", "reason": "skeletal mesh asset missing", "asset": ASSET_PATH})
        raise RuntimeError("Missing V32 cryo bodysuit skeletal mesh")

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    task = unreal.AssetExportTask()
    task.set_editor_property("object", mesh)
    task.set_editor_property("filename", OUTPUT_FBX)
    task.set_editor_property("automated", True)
    task.set_editor_property("prompt", False)
    task.set_editor_property("replace_identical", True)
    task.set_editor_property("write_empty_files", False)

    exported = unreal.Exporter.run_asset_export_task(task)
    output_exists = os.path.isfile(OUTPUT_FBX) and os.path.getsize(OUTPUT_FBX) > 0
    skeleton = mesh.get_editor_property("skeleton")
    materials = mesh.get_editor_property("materials")
    payload = {
        "status": "pass" if exported and output_exists else "fail",
        "asset": mesh.get_path_name(),
        "skeleton": skeleton.get_path_name() if skeleton else None,
        "material_slots": len(materials),
        "output": OUTPUT_FBX,
        "bytes": os.path.getsize(OUTPUT_FBX) if output_exists else 0,
    }
    write_report(payload)
    if payload["status"] != "pass":
        raise RuntimeError("V32 cryo bodysuit FBX recovery export failed")
    unreal.log("V32 cryo bodysuit recovery FBX exported: " + OUTPUT_FBX)


main()
