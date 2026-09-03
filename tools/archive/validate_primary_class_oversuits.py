"""Validate the standalone V16 primary class oversuit package in Blender."""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
ASSET_DIR = ROOT / "Art" / "Characters" / "PlayerSuits" / "PrimaryOversuits"
EXPORT_DIR = ROOT / "Build" / "Unreal" / "PlayerSuits" / "PrimaryOversuits"
REPORT = ASSET_DIR / "PrimaryOversuits_v16_Validation.json"
QA = ASSET_DIR / "PrimaryOversuits_v16_QA.md"
CLASSES = {
    "Marine": ("Security", ("BallisticCuirass", "ExpandedPauldron", "HelmetCamera")),
    "Scientist": ("Crew", ("InstrumentChest", "SensorMast", "SampleCanister", "SurveyLidar")),
    "Technician": ("Engineering", ("ToolArmDock", "PowerCell", "CableReel", "DiagnosticTerminal")),
    "Medical": ("Medical", ("TelemetryPanel", "SterileEquipmentPack", "Injector", "BiometricScanner")),
}


def validate(class_name, role_alias, required_tokens):
    blend = ASSET_DIR / f"PlayerOversuit_{class_name}_v16.blend"
    fbx = EXPORT_DIR / f"SKM_PlayerOversuit_{class_name}_v16.fbx"
    errors = []
    if not blend.exists():
        return {"status": "failed", "errors": [f"missing blend: {blend}"]}
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    armatures = [obj for obj in bpy.data.objects if obj.type == "ARMATURE"]
    meshes = [obj for obj in bpy.data.objects if obj.type == "MESH" and obj.get("asset_layer") == "oversuit"]
    forbidden = [obj.name for obj in bpy.data.objects
                 if any(token in obj.name.lower() for token in ("playerhead", "undersuit", "body_mesh"))]
    if len(armatures) != 1:
        errors.append(f"expected one armature, found {len(armatures)}")
    else:
        rig = armatures[0]
        if rig.get("oversuit_class") != class_name:
            errors.append("armature class metadata mismatch")
        if rig.get("profile_role_alias") != role_alias:
            errors.append("profile role alias mismatch")
        if not rig.get("wearer_independent"):
            errors.append("wearer-independent contract missing")
    if forbidden:
        errors.append("forbidden player/undersuit objects: " + ", ".join(forbidden))
    if len(meshes) < 38:
        errors.append(f"oversuit mesh count too low: {len(meshes)}")
    names = [obj.name for obj in meshes]
    for token in required_tokens:
        if not any(token in name for name in names):
            errors.append(f"missing required class module: {token}")
    unbound = []
    invalid_vertices = []
    for obj in meshes:
        attached = obj.parent and obj.parent.type == "ARMATURE"
        deformed = any(mod.type == "ARMATURE" for mod in obj.modifiers)
        if not (attached or deformed):
            unbound.append(obj.name)
        if any(not all(math.isfinite(v) for v in vertex.co) for vertex in obj.data.vertices):
            invalid_vertices.append(obj.name)
    if unbound:
        errors.append("unbound oversuit meshes: " + ", ".join(unbound))
    if invalid_vertices:
        errors.append("non-finite mesh vertices: " + ", ".join(invalid_vertices))
    if not fbx.exists() or fbx.stat().st_size < 1024:
        errors.append(f"missing or empty FBX: {fbx}")
    previews = [ASSET_DIR / "Previews" / f"PlayerOversuit_{class_name}_v16_{view}.png"
                for view in ("Front", "ThreeQuarter", "Rear")]
    missing_previews = [str(path) for path in previews if not path.exists() or path.stat().st_size < 1024]
    if missing_previews:
        errors.append("missing previews: " + ", ".join(missing_previews))
    return {
        "status": "passed" if not errors else "failed",
        "errors": errors,
        "mesh_count": len(meshes),
        "class_module_count": sum(bool(obj.get("class_module") != "shared_pressure_envelope") for obj in meshes),
        "forbidden_object_count": len(forbidden),
        "fbx_bytes": fbx.stat().st_size if fbx.exists() else 0,
        "blend_bytes": blend.stat().st_size,
    }


def main():
    results = {name: validate(name, alias, tokens)
               for name, (alias, tokens) in CLASSES.items()}
    passed = all(result["status"] == "passed" for result in results.values())
    payload = {
        "schema": 1,
        "asset": "PrimaryOversuits_v16",
        "status": "passed" if passed else "failed",
        "separation_contract": "no player body or undersuit objects in any class asset",
        "classes": results,
    }
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    lines = [
        "# Primary class oversuits v16 QA",
        "",
        f"Overall status: **{payload['status'].upper()}**",
        "",
        "Each class file is a standalone modular skeletal garment. Player body and undersuit",
        "geometry are forbidden from the package; the shared armature is retained only as the",
        "deformation/attachment reference.",
        "",
        "| Class | Existing role alias | Meshes | Class modules | FBX | Status |",
        "| --- | --- | ---: | ---: | ---: | --- |",
    ]
    for name, (alias, _) in CLASSES.items():
        result = results[name]
        lines.append(f"| {name} | {alias} | {result.get('mesh_count', 0)} | "
                     f"{result.get('class_module_count', 0)} | {result.get('fbx_bytes', 0):,} B | "
                     f"{result['status'].upper()} |")
        if result["errors"]:
            lines.extend(f"  - {error}" for error in result["errors"])
    lines.extend([
        "",
        "Promotion remains gated on animated fit, collision/cloth review, Unreal import, and",
        "multiplayer loadout replication against the finalized player/undersuit rig.",
    ])
    QA.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("PRIMARY_OVERSUITS_V16_VALIDATION", payload["status"], REPORT)
    if not passed:
        raise RuntimeError("Primary oversuit validation failed; inspect the JSON report")


if __name__ == "__main__":
    main()
