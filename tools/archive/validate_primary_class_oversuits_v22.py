"""Validate the concept-matched V22 standalone class oversuits."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
ASSET_DIR = ROOT / "Art" / "Characters" / "PlayerSuits" / "PrimaryOversuits"
EXPORT_DIR = ROOT / "Build" / "Unreal" / "PlayerSuits" / "PrimaryOversuits_v22"
REPORT = ASSET_DIR / "PrimaryOversuits_v22_Validation.json"
CLASSES = ("Marine", "Scientist", "Technician", "Medical")
FORBIDDEN = ("undersuit", "face", "eyelid", "eyewhite", "pupil", "hair", "mouth", "nose", "chin", "cheek", "brow")


def validate(class_name):
    blend = ASSET_DIR / f"PlayerOversuit_{class_name}_v22.blend"
    fbx = EXPORT_DIR / f"SKM_PlayerOversuit_{class_name}_v22.fbx"
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    meshes = [o for o in bpy.data.objects if o.type == "MESH" and o.get("asset_layer") == "oversuit"]
    rigs = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    interfaces = [o for o in bpy.data.objects if o.get("asset_layer") == "oversuit_interface"]
    forbidden = [o.name for o in bpy.data.objects if any(token in o.name.lower() for token in FORBIDDEN)]
    bad_materials = [m.name for m in bpy.data.materials if any(token in m.name.lower() for token in ("skin", "eye", "hair", "mouth")) and m.users]
    bounds = []
    for obj in meshes:
        bounds.extend(obj.matrix_world @ corner for corner in obj.bound_box)
    width = max(p.y for p in bounds) - min(p.y for p in bounds)
    depth = max(p.x for p in bounds) - min(p.x for p in bounds)
    height = max(p.z for p in bounds) - min(p.z for p in bounds)
    errors = []
    if len(meshes) < 300:
        errors.append(f"concept detail mesh count too low: {len(meshes)}")
    if len(rigs) != 1 or len(rigs[0].data.bones) != 22:
        errors.append("expected one 22-bone production oversuit rig")
    if len(interfaces) != 8:
        errors.append(f"expected 8 donning interfaces, found {len(interfaces)}")
    if forbidden:
        errors.append(f"wearer/undersuit objects remain: {forbidden[:8]}")
    if bad_materials:
        errors.append(f"wearer materials remain in use: {bad_materials}")
    if not (145 <= height <= 195 and 45 <= width <= 130 and 25 <= depth <= 110):
        errors.append(f"implausible suit bounds h/w/d={height:.1f}/{width:.1f}/{depth:.1f} cm")
    if not fbx.exists() or fbx.stat().st_size < 1_000_000:
        errors.append("FBX export missing or unexpectedly small")
    return {
        "status": "passed" if not errors else "failed", "errors": errors,
        "mesh_count": len(meshes), "bone_count": len(rigs[0].data.bones) if rigs else 0,
        "interface_count": len(interfaces), "forbidden_wearer_count": len(forbidden),
        "forbidden_material_count": len(bad_materials),
        "bounds_cm": {"height": round(height, 2), "width": round(width, 2), "depth": round(depth, 2)},
        "blend_bytes": blend.stat().st_size, "fbx_bytes": fbx.stat().st_size if fbx.exists() else 0,
    }


results = {name: validate(name) for name in CLASSES}
status = "passed" if all(item["status"] == "passed" for item in results.values()) else "failed"
REPORT.write_text(json.dumps({"schema": 1, "asset": "PrimaryOversuits_v22", "status": status, "classes": results}, indent=2), encoding="utf-8")
if status != "passed":
    raise SystemExit(f"PRIMARY_OVERSUITS_V22_VALIDATION failed {REPORT}")
print(f"PRIMARY_OVERSUITS_V22_VALIDATION passed {REPORT}")
