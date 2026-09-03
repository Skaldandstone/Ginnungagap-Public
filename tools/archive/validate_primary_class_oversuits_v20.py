"""Validate the V20 tailoring and surface-construction pass."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
ASSET_DIR = ROOT / "Art" / "Characters" / "PlayerSuits" / "PrimaryOversuits"
EXPORT_DIR = ROOT / "Build" / "Unreal" / "PlayerSuits" / "PrimaryOversuits_v20"
REPORT = ASSET_DIR / "PrimaryOversuits_v20_Validation.json"
QA = ASSET_DIR / "PrimaryOversuits_v20_QA.md"
CLASSES = ("Marine", "Scientist", "Technician", "Medical")
REQUIRED = ("CenterClosure", "ChestSeam_L", "ChestSeam_R", "AbdomenSeam",
            "ElbowBellow_L", "ElbowBellow_R", "KneeBellow_L", "KneeBellow_R",
            "ThighOuterSeam_L", "ThighOuterSeam_R", "PalmPlate_L", "PalmPlate_R")


def validate(class_name):
    blend = ASSET_DIR / f"PlayerOversuit_{class_name}_v20.blend"
    fbx = EXPORT_DIR / f"SKM_PlayerOversuit_{class_name}_v20.fbx"
    errors = []
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    rigs = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    meshes = [obj for obj in bpy.data.objects
              if obj.type == "MESH" and obj.get("asset_layer") == "oversuit"]
    interfaces = [obj for obj in bpy.data.objects if obj.get("asset_layer") == "oversuit_interface"]
    names = [obj.name for obj in meshes]
    wearer = [obj.name for obj in bpy.data.objects
              if any(token in obj.name.lower() for token in ("playerhead", "undersuit", "body_mesh"))]
    if len(rigs) != 1 or rigs[0].get("oversuit_pass") != 20:
        errors.append("V20 armature metadata missing")
    if wearer:
        errors.append("forbidden wearer geometry: " + ", ".join(wearer))
    for token in REQUIRED:
        if not any(token in name for name in names):
            errors.append(f"missing V20 construction feature: {token}")
    reshaped = [obj for obj in meshes if obj.get("v20_tailored_scale")]
    textile = [obj for obj in meshes if obj.get("v20_tailored_pressure_fabric")]
    surface = [obj for obj in meshes if obj.get("v20_surface_construction")]
    fabric_mats = [mat for mat in bpy.data.materials if mat.get("v20_pressure_textile")]
    if len(reshaped) < 20:
        errors.append(f"too few tailored shells: {len(reshaped)}")
    if len(textile) < 20:
        errors.append(f"too few textile-assigned shells: {len(textile)}")
    if len(surface) < 35:
        errors.append(f"too few construction details: {len(surface)}")
    if len(fabric_mats) != 1:
        errors.append(f"expected one V20 pressure textile material, found {len(fabric_mats)}")
    elif not fabric_mats[0].node_tree.nodes.get("V20_TextileBump"):
        errors.append("pressure textile bump node missing")
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
        errors.append("missing or empty V20 FBX")
    previews = [ASSET_DIR / "Previews_v20" / f"PlayerOversuit_{class_name}_v20_{view}.png"
                for view in ("Front", "ThreeQuarter", "Rear", "RearThreeQuarter")]
    if any(not path.exists() or path.stat().st_size < 1024 for path in previews):
        errors.append("one or more V20 previews missing")
    return {"status": "passed" if not errors else "failed", "errors": errors,
            "mesh_count": len(meshes), "tailored_shell_count": len(reshaped),
            "textile_shell_count": len(textile), "surface_detail_count": len(surface),
            "interface_count": len(interfaces), "forbidden_wearer_count": len(wearer),
            "blend_bytes": blend.stat().st_size, "fbx_bytes": fbx.stat().st_size if fbx.exists() else 0}


def main():
    results = {name: validate(name) for name in CLASSES}
    passed = all(result["status"] == "passed" for result in results.values())
    payload = {"schema": 1, "asset": "PrimaryOversuits_v20",
               "status": "passed" if passed else "failed", "classes": results}
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = ["# Primary class oversuits v20 QA", "",
             f"Overall status: **{payload['status'].upper()}**", "",
             "| Class | Tailored shells | Textile shells | Surface details | Interfaces | Status |",
             "| --- | ---: | ---: | ---: | ---: | --- |"]
    for name, result in results.items():
        lines.append(f"| {name} | {result['tailored_shell_count']} | "
                     f"{result['textile_shell_count']} | {result['surface_detail_count']} | "
                     f"{result['interface_count']} | {result['status'].upper()} |")
        lines.extend(f"  - {error}" for error in result["errors"])
    lines += ["", "V20 tailors V19 volumes and adds pressure-garment construction without",
              "reintroducing wearer geometry or altering the eight donning interfaces."]
    QA.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("PRIMARY_OVERSUITS_V20_VALIDATION", payload["status"], REPORT)
    if not passed:
        raise RuntimeError("V20 validation failed; inspect the JSON report")


if __name__ == "__main__":
    main()
