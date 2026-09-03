"""Audit candidate Fab modules for clean shipboard-robot role equipment."""

import json
from pathlib import Path

import unreal


SOURCES = [
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/LAMP/SM_SCANNER_01",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_MECHA_ARM_01",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_MECHA_ARM_02",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_MECHA_ARM_03",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_ELECTRIC_BOX_01_CLOSE",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_POWER_GENERATOR_01",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/OTHERS/SM_PANEL_01",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/HANDLE/SM_HANDLE_LONG_01",
]


report = []
for path in SOURCES:
    asset = unreal.EditorAssetLibrary.load_asset(path)
    entry = {"path": path, "class": asset.get_class().get_name() if asset else None}
    if isinstance(asset, unreal.StaticMesh):
        box = asset.get_bounding_box()
        entry["bounds"] = {
            "min": [box.min.x, box.min.y, box.min.z],
            "max": [box.max.x, box.max.y, box.max.z],
            "size": [box.max.x - box.min.x, box.max.y - box.min.y, box.max.z - box.min.z],
        }
    else:
        entry["bounds"] = None
    report.append(entry)

output = Path(unreal.SystemLibrary.get_project_saved_directory()) / "Reports/UncorruptedRobotFabPartAudit.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"Uncorrupted robot Fab part audit written to {output}")
