"""Validate V17 construction, separation, and donning-interface contracts."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
ASSET_DIR = ROOT / "Art" / "Characters" / "PlayerSuits" / "PrimaryOversuits"
EXPORT_DIR = ROOT / "Build" / "Unreal" / "PlayerSuits" / "PrimaryOversuits_v17"
REPORT = ASSET_DIR / "PrimaryOversuits_v17_Validation.json"
QA = ASSET_DIR / "PrimaryOversuits_v17_QA.md"
REQUIRED_SHARED = ("WaistYokeFront", "HipYoke", "UnderarmPressureBellows",
                   "ElbowPressureCuff", "AnkleLockRing", "MagSoleRail",
                   "RearEntrySpine", "RearEntryLatch", "HelmetCrownRail")
REQUIRED_CLASS = {
    "Marine": ("CuirassEdge", "ThighHardpoint", "BeltCell"),
    "Scientist": ("MastCage", "SampleRack", "LidarBrace", "InstrumentKey"),
    "Technician": ("FoldedToolLink", "ToolJoint", "PackHeatSink", "PowerConduit"),
    "Medical": ("RearRescueHandle", "InjectorRack", "ForearmAidPanel", "TriageBeacon"),
}
ROLE_ALIASES = {"Marine": "Security", "Scientist": "Crew",
                "Technician": "Engineering", "Medical": "Medical"}


def validate(class_name):
    blend = ASSET_DIR / f"PlayerOversuit_{class_name}_v17.blend"
    fbx = EXPORT_DIR / f"SKM_PlayerOversuit_{class_name}_v17.fbx"
    errors = []
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    rigs = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    meshes = [obj for obj in bpy.data.objects
              if obj.type == "MESH" and obj.get("asset_layer") == "oversuit"]
    interfaces = [obj for obj in bpy.data.objects if obj.get("asset_layer") == "oversuit_interface"]
    forbidden = [obj.name for obj in bpy.data.objects
                 if any(token in obj.name.lower() for token in ("playerhead", "undersuit", "body_mesh"))]
    if len(rigs) != 1:
        errors.append(f"expected one armature, found {len(rigs)}")
    else:
        rig = rigs[0]
        if rig.get("oversuit_pass") != 17:
            errors.append("V17 armature metadata missing")
        if rig.get("profile_role_alias") != ROLE_ALIASES[class_name]:
            errors.append("role alias mismatch")
        if not rig.get("don_sequence") or not rig.get("doff_sequence"):
            errors.append("don/doff sequence metadata missing")
        if rig.get("donning_interface_count") != 8:
            errors.append("declared donning interface count is not eight")
    if forbidden:
        errors.append("forbidden wearer geometry: " + ", ".join(forbidden))
    if len(meshes) < 70:
        errors.append(f"mesh count below V17 floor: {len(meshes)}")
    if len(interfaces) != 8:
        errors.append(f"expected eight donning interfaces, found {len(interfaces)}")
    names = [obj.name for obj in meshes]
    for token in (*REQUIRED_SHARED, *REQUIRED_CLASS[class_name]):
        if not any(token in name for name in names):
            errors.append(f"missing required construction feature: {token}")
    stages = {obj.get("donning_stage") for obj in meshes}
    for stage in (10, 20, 30, 40, 50, 60, 70):
        if stage not in stages:
            errors.append(f"donning stage absent: {stage}")
    for obj in meshes:
        attached = obj.parent and obj.parent.type == "ARMATURE"
        deformed = any(mod.type == "ARMATURE" for mod in obj.modifiers)
        if not (attached or deformed):
            errors.append(f"unbound mesh: {obj.name}")
        if any(not all(math.isfinite(value) for value in vertex.co) for vertex in obj.data.vertices):
            errors.append(f"non-finite geometry: {obj.name}")
    if not fbx.exists() or fbx.stat().st_size < 1024:
        errors.append("missing or empty FBX")
    previews = [ASSET_DIR / "Previews_v17" / f"PlayerOversuit_{class_name}_v17_{view}.png"
                for view in ("Front", "ThreeQuarter", "Rear", "RearThreeQuarter")]
    if any(not path.exists() or path.stat().st_size < 1024 for path in previews):
        errors.append("one or more V17 previews are missing")
    return {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "mesh_count": len(meshes),
        "interface_count": len(interfaces),
        "donning_stages": sorted(stage for stage in stages if isinstance(stage, int)),
        "forbidden_object_count": len(forbidden),
        "blend_bytes": blend.stat().st_size,
        "fbx_bytes": fbx.stat().st_size if fbx.exists() else 0,
    }


def main():
    results = {class_name: validate(class_name) for class_name in REQUIRED_CLASS}
    passed = all(result["status"] == "passed" for result in results.values())
    payload = {"schema": 1, "asset": "PrimaryOversuits_v17",
               "status": "passed" if passed else "failed", "classes": results}
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = ["# Primary class oversuits v17 QA", "",
             f"Overall status: **{payload['status'].upper()}**", "",
             "| Class | Meshes | Interfaces | Donning stages | Blend | FBX | Status |",
             "| --- | ---: | ---: | --- | ---: | ---: | --- |"]
    for class_name, result in results.items():
        lines.append(f"| {class_name} | {result['mesh_count']} | {result['interface_count']} | "
                     f"{', '.join(map(str, result['donning_stages']))} | "
                     f"{result['blend_bytes']:,} B | {result['fbx_bytes']:,} B | "
                     f"{result['status'].upper()} |")
        lines.extend(f"  - {error}" for error in result["errors"])
    lines += ["", "V17 remains a review package until final skeleton, animated fit, pressure",
              "interface, Unreal import, and replicated equip tests pass."]
    QA.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("PRIMARY_OVERSUITS_V17_VALIDATION", payload["status"], REPORT)
    if not passed:
        raise RuntimeError("V17 validation failed; inspect the JSON report")


if __name__ == "__main__":
    main()
