"""Validate V21 integrated seams, gloves, boots, and legacy cleanup."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
ASSET_DIR = ROOT / "Art" / "Characters" / "PlayerSuits" / "PrimaryOversuits"
EXPORT_DIR = ROOT / "Build" / "Unreal" / "PlayerSuits" / "PrimaryOversuits_v21"
REPORT = ASSET_DIR / "PrimaryOversuits_v21_Validation.json"
QA = ASSET_DIR / "PrimaryOversuits_v21_QA.md"
CLASSES = ("Marine", "Scientist", "Technician", "Medical")
REQUIRED = ("ConformalCenterClosure", "ConformalChestSeam_L", "ConformalChestSeam_R",
            "ConformalAbdomenSeam", "IntegratedElbowBellow_L", "IntegratedElbowBellow_R",
            "IntegratedKneeBellow_L", "IntegratedKneeBellow_R", "GlovePalm_L", "GlovePalm_R",
            "GloveFinger_L_4", "GloveFinger_R_4", "GloveThumb_L", "GloveThumb_R",
            "BootToeCap_L", "BootToeCap_R", "BootMagSole_L", "BootMagSole_R")


def validate(class_name):
    blend = ASSET_DIR / f"PlayerOversuit_{class_name}_v21.blend"
    fbx = EXPORT_DIR / f"SKM_PlayerOversuit_{class_name}_v21.fbx"
    errors = []
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    rigs = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    meshes = [obj for obj in bpy.data.objects
              if obj.type == "MESH" and obj.get("asset_layer") == "oversuit"]
    interfaces = [obj for obj in bpy.data.objects if obj.get("asset_layer") == "oversuit_interface"]
    names = [obj.name for obj in meshes]
    legacy = [obj.name for obj in bpy.data.objects if obj.name.startswith("SKV11_")]
    wearer = [obj.name for obj in bpy.data.objects
              if any(token in obj.name.lower() for token in ("playerhead", "undersuit", "body_mesh"))]
    if len(rigs) != 1 or rigs[0].get("oversuit_pass") != 21:
        errors.append("V21 armature metadata missing")
    if legacy:
        errors.append("V11 mesh remains: " + ", ".join(legacy))
    if wearer:
        errors.append("forbidden wearer geometry: " + ", ".join(wearer))
    for token in REQUIRED:
        if not any(token in name for name in names):
            errors.append(f"missing V21 integrated feature: {token}")
    seams = [obj for obj in meshes if obj.get("v21_curve_converted_to_mesh")]
    gloves = [obj for obj in meshes if obj.get("v21_integrated_component") in
              {"flexible_pressure_glove", "external_hard_shell"} and "Glove" in obj.name]
    boots = [obj for obj in meshes if "Boot" in obj.name and obj.get("oversuit_pass") == 21]
    curves = [obj.name for obj in bpy.data.objects if obj.type == "CURVE" and obj.name.startswith("OVR21_")]
    if len(seams) < 15:
        errors.append(f"too few converted conformal seams: {len(seams)}")
    if curves:
        errors.append("unconverted V21 curves remain: " + ", ".join(curves))
    if len(gloves) != 14:
        errors.append(f"articulated glove part count mismatch: {len(gloves)}")
    if len(boots) != 18:
        errors.append(f"dedicated boot part count mismatch: {len(boots)}")
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
        errors.append("missing or empty V21 FBX")
    previews = [ASSET_DIR / "Previews_v21" / f"PlayerOversuit_{class_name}_v21_{view}.png"
                for view in ("Front", "ThreeQuarter", "Rear", "RearThreeQuarter")]
    if any(not path.exists() or path.stat().st_size < 1024 for path in previews):
        errors.append("one or more V21 previews missing")
    return {"status": "passed" if not errors else "failed", "errors": errors,
            "mesh_count": len(meshes), "converted_seam_count": len(seams),
            "glove_part_count": len(gloves), "boot_part_count": len(boots),
            "interface_count": len(interfaces), "legacy_v11_count": len(legacy),
            "forbidden_wearer_count": len(wearer),
            "blend_bytes": blend.stat().st_size, "fbx_bytes": fbx.stat().st_size if fbx.exists() else 0}


def main():
    results = {name: validate(name) for name in CLASSES}
    passed = all(result["status"] == "passed" for result in results.values())
    payload = {"schema": 1, "asset": "PrimaryOversuits_v21",
               "status": "passed" if passed else "failed", "classes": results}
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = ["# Primary class oversuits v21 QA", "",
             f"Overall status: **{payload['status'].upper()}**", "",
             "| Class | Converted seams | Glove parts | Boot parts | V11 meshes | Status |",
             "| --- | ---: | ---: | ---: | ---: | --- |"]
    for name, result in results.items():
        lines.append(f"| {name} | {result['converted_seam_count']} | "
                     f"{result['glove_part_count']} | {result['boot_part_count']} | "
                     f"{result['legacy_v11_count']} | {result['status'].upper()} |")
        lines.extend(f"  - {error}" for error in result["errors"])
    lines += ["", "V21 leaves no V11 mesh, no unconverted authored seam curve, and no wearer",
              "geometry in any class asset."]
    QA.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("PRIMARY_OVERSUITS_V21_VALIDATION", payload["status"], REPORT)
    if not passed:
        raise RuntimeError("V21 validation failed; inspect the JSON report")


if __name__ == "__main__":
    main()
