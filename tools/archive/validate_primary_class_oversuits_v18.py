"""Validate the V18 curved-form primary oversuit pass."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
ASSET_DIR = ROOT / "Art" / "Characters" / "PlayerSuits" / "PrimaryOversuits"
EXPORT_DIR = ROOT / "Build" / "Unreal" / "PlayerSuits" / "PrimaryOversuits_v18"
REPORT = ASSET_DIR / "PrimaryOversuits_v18_Validation.json"
QA = ASSET_DIR / "PrimaryOversuits_v18_QA.md"
CLASS_FEATURE = {"Marine": "CurvedCuirass", "Scientist": "InstrumentPod",
                 "Technician": "ServiceBib", "Medical": "TelemetryShell"}
FORBIDDEN_BLOCKOUT = {"Marine": ("BallisticCuirass",), "Scientist": ("InstrumentChest",),
                      "Technician": ("PowerCell_L", "PowerCell_R"),
                      "Medical": ("TelemetryPanel", "SterileEquipmentPack")}


def validate(class_name):
    blend = ASSET_DIR / f"PlayerOversuit_{class_name}_v18.blend"
    fbx = EXPORT_DIR / f"SKM_PlayerOversuit_{class_name}_v18.fbx"
    errors = []
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    rigs = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    meshes = [obj for obj in bpy.data.objects
              if obj.type == "MESH" and obj.get("asset_layer") == "oversuit"]
    interfaces = [obj for obj in bpy.data.objects if obj.get("asset_layer") == "oversuit_interface"]
    names = [obj.name for obj in meshes]
    forbidden_wearer = [obj.name for obj in bpy.data.objects
                        if any(token in obj.name.lower() for token in
                               ("playerhead", "undersuit", "body_mesh"))]
    if len(rigs) != 1 or rigs[0].get("oversuit_pass") != 18:
        errors.append("V18 armature contract missing")
    if forbidden_wearer:
        errors.append("forbidden wearer geometry: " + ", ".join(forbidden_wearer))
    for token in ("ContinuousWaistRing", "LifeSupportShroud", "HelmetCrownPad",
                  "HarnessStrut", CLASS_FEATURE[class_name]):
        if not any(token in name for name in names):
            errors.append(f"missing V18 curved-form feature: {token}")
    for token in FORBIDDEN_BLOCKOUT[class_name]:
        if any(token in name and name.startswith("OVR16_") for name in names):
            errors.append(f"legacy blockout part retained: {token}")
    curved = [obj for obj in meshes if obj.get("v18_form_refinement")]
    softened = [obj for obj in meshes if obj.get("v18_softened_edges")]
    if len(curved) < 9:
        errors.append(f"too few new curved forms: {len(curved)}")
    if len(softened) < 20:
        errors.append(f"too few softened inherited parts: {len(softened)}")
    if len(interfaces) != 8:
        errors.append(f"donning interfaces changed: {len(interfaces)}")
    for obj in meshes:
        attached = obj.parent and obj.parent.type == "ARMATURE"
        deformed = any(mod.type == "ARMATURE" for mod in obj.modifiers)
        if not (attached or deformed):
            errors.append(f"unbound mesh: {obj.name}")
        if any(not all(math.isfinite(v) for v in vertex.co) for vertex in obj.data.vertices):
            errors.append(f"non-finite geometry: {obj.name}")
    if not fbx.exists() or fbx.stat().st_size < 1024:
        errors.append("missing or empty V18 FBX")
    previews = [ASSET_DIR / "Previews_v18" / f"PlayerOversuit_{class_name}_v18_{view}.png"
                for view in ("Front", "ThreeQuarter", "Rear", "RearThreeQuarter")]
    if any(not path.exists() or path.stat().st_size < 1024 for path in previews):
        errors.append("one or more V18 previews missing")
    return {"status": "passed" if not errors else "failed", "errors": errors,
            "mesh_count": len(meshes), "curved_form_count": len(curved),
            "softened_part_count": len(softened), "interface_count": len(interfaces),
            "forbidden_wearer_count": len(forbidden_wearer),
            "blend_bytes": blend.stat().st_size, "fbx_bytes": fbx.stat().st_size if fbx.exists() else 0}


def main():
    results = {name: validate(name) for name in CLASS_FEATURE}
    passed = all(result["status"] == "passed" for result in results.values())
    payload = {"schema": 1, "asset": "PrimaryOversuits_v18",
               "status": "passed" if passed else "failed", "classes": results}
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = ["# Primary class oversuits v18 QA", "",
             f"Overall status: **{payload['status'].upper()}**", "",
             "| Class | Meshes | Curved forms | Softened parts | Interfaces | Status |",
             "| --- | ---: | ---: | ---: | ---: | --- |"]
    for name, result in results.items():
        lines.append(f"| {name} | {result['mesh_count']} | {result['curved_form_count']} | "
                     f"{result['softened_part_count']} | {result['interface_count']} | "
                     f"{result['status'].upper()} |")
        lines.extend(f"  - {error}" for error in result["errors"])
    lines += ["", "V18 replaces the dominant V17 blockout silhouettes with curved and tapered",
              "forms while retaining the standalone garment and donning contracts."]
    QA.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("PRIMARY_OVERSUITS_V18_VALIDATION", payload["status"], REPORT)
    if not passed:
        raise RuntimeError("V18 validation failed; inspect the JSON report")


if __name__ == "__main__":
    main()
