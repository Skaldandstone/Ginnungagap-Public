"""Validate V19 dedicated smooth pressure/armor shell replacements."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
ASSET_DIR = ROOT / "Art" / "Characters" / "PlayerSuits" / "PrimaryOversuits"
EXPORT_DIR = ROOT / "Build" / "Unreal" / "PlayerSuits" / "PrimaryOversuits_v19"
REPORT = ASSET_DIR / "PrimaryOversuits_v19_Validation.json"
QA = ASSET_DIR / "PrimaryOversuits_v19_QA.md"
CLASSES = ("Marine", "Scientist", "Technician", "Medical")
REQUIRED = ("SmoothUpperTorso", "SmoothAbdomen", "PelvisPressureBridge",
            "ForearmGauntlet_L", "ForearmGauntlet_R", "GloveShell_L", "GloveShell_R",
            "ThighGaiter_L", "ThighGaiter_R", "KneePad_L", "KneePad_R",
            "ShinGaiter_L", "ShinGaiter_R", "ShinArmorPlate_L", "ShinArmorPlate_R")


def validate(class_name):
    blend = ASSET_DIR / f"PlayerOversuit_{class_name}_v19.blend"
    fbx = EXPORT_DIR / f"SKM_PlayerOversuit_{class_name}_v19.fbx"
    errors = []
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    rigs = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    meshes = [obj for obj in bpy.data.objects
              if obj.type == "MESH" and obj.get("asset_layer") == "oversuit"]
    interfaces = [obj for obj in bpy.data.objects if obj.get("asset_layer") == "oversuit_interface"]
    names = [obj.name for obj in meshes]
    wearer = [obj.name for obj in bpy.data.objects
              if any(token in obj.name.lower() for token in ("playerhead", "undersuit", "body_mesh"))]
    old_regions = [name for name in names if name.startswith(("SKV11_Chest", "SKV11_Forearm",
                                                              "SKV11_Knee", "SKV11_Shin",
                                                              "SKV11_Shoulder", "SKV11_Thigh"))]
    boots = [name for name in names if name.startswith("SKV11_Boot_")]
    if len(rigs) != 1 or rigs[0].get("oversuit_pass") != 19:
        errors.append("V19 armature metadata missing")
    if wearer:
        errors.append("forbidden wearer geometry: " + ", ".join(wearer))
    if old_regions:
        errors.append("legacy V11 masked regions remain: " + ", ".join(old_regions))
    if sorted(boots) != ["SKV11_Boot_L", "SKV11_Boot_R"]:
        errors.append("V11 retained-boot policy mismatch")
    for token in REQUIRED:
        if not any(token in name for name in names):
            errors.append(f"missing dedicated V19 shell: {token}")
    dedicated = [obj for obj in meshes if obj.get("v19_dedicated_shell")]
    if len(dedicated) < 25:
        errors.append(f"dedicated shell count too low: {len(dedicated)}")
    if len(interfaces) != 8:
        errors.append(f"donning interface count changed: {len(interfaces)}")
    for obj in meshes:
        attached = obj.parent and obj.parent.type == "ARMATURE"
        deformed = any(mod.type == "ARMATURE" for mod in obj.modifiers)
        if not (attached or deformed):
            errors.append(f"unbound mesh: {obj.name}")
        if any(not all(math.isfinite(value) for value in vertex.co) for vertex in obj.data.vertices):
            errors.append(f"non-finite geometry: {obj.name}")
    if not fbx.exists() or fbx.stat().st_size < 1024:
        errors.append("missing or empty V19 FBX")
    previews = [ASSET_DIR / "Previews_v19" / f"PlayerOversuit_{class_name}_v19_{view}.png"
                for view in ("Front", "ThreeQuarter", "Rear", "RearThreeQuarter")]
    if any(not path.exists() or path.stat().st_size < 1024 for path in previews):
        errors.append("one or more V19 previews missing")
    return {"status": "passed" if not errors else "failed", "errors": errors,
            "mesh_count": len(meshes), "dedicated_shell_count": len(dedicated),
            "retained_boot_count": len(boots), "interface_count": len(interfaces),
            "forbidden_wearer_count": len(wearer),
            "blend_bytes": blend.stat().st_size, "fbx_bytes": fbx.stat().st_size if fbx.exists() else 0}


def main():
    results = {name: validate(name) for name in CLASSES}
    passed = all(result["status"] == "passed" for result in results.values())
    payload = {"schema": 1, "asset": "PrimaryOversuits_v19",
               "status": "passed" if passed else "failed", "classes": results}
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = ["# Primary class oversuits v19 QA", "",
             f"Overall status: **{payload['status'].upper()}**", "",
             "| Class | Meshes | Dedicated shells | Retained boots | Interfaces | Status |",
             "| --- | ---: | ---: | ---: | ---: | --- |"]
    for name, result in results.items():
        lines.append(f"| {name} | {result['mesh_count']} | {result['dedicated_shell_count']} | "
                     f"{result['retained_boot_count']} | {result['interface_count']} | "
                     f"{result['status'].upper()} |")
        lines.extend(f"  - {error}" for error in result["errors"])
    lines += ["", "All V11 masked torso and limb regions are removed. Only the two authored",
              "V11 boot shells remain; V19 supplies dedicated smooth pressure and armor forms."]
    QA.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("PRIMARY_OVERSUITS_V19_VALIDATION", payload["status"], REPORT)
    if not passed:
        raise RuntimeError("V19 validation failed; inspect the JSON report")


if __name__ == "__main__":
    main()
