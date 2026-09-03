"""Validate the V16 concept-aligned character/undersuit deliverable."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
ASSET = SUIT_DIR / "PlayerCharacter_Undersuit_Concept_v16.blend"
REPORT = SUIT_DIR / "PlayerCharacter_Undersuit_v16_Validation.json"

FORBIDDEN = (
    "helmet", "visor", "armor", "armour", "oversuit", "hard_shell",
    "backpack", "rear_pack", "pauldron", "chest_plate",
)


def world_center(obj: bpy.types.Object) -> Vector:
    return sum((obj.matrix_world @ Vector(corner) for corner in obj.bound_box), Vector()) / 8


def finite_bounds(obj: bpy.types.Object) -> bool:
    return all(math.isfinite(value) for corner in obj.bound_box for value in corner)


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(ASSET))

    required = {
        "rig": bpy.data.objects.get("RIG_PlayerCharacter_Undersuit_v16"),
        "undersuit": bpy.data.objects.get("SK_PlayerCharacter_Undersuit_v16"),
        "head": bpy.data.objects.get("SK_PlayerHead_Production_v6"),
        "hair": bpy.data.objects.get("V6_HEAD_Hair_Short02_CC0"),
    }
    missing = [label for label, obj in required.items() if obj is None]

    renderables = [
        obj for obj in bpy.context.scene.objects
        if obj.type in {"MESH", "CURVE"} and not obj.hide_render
    ]
    leaked = [
        obj.name for obj in renderables
        if any(token in obj.name.lower() for token in FORBIDDEN)
    ]

    undersuit = required["undersuit"]
    head = required["head"]
    hair = required["hair"]
    checks = {
        "required_objects_present": not missing,
        "no_outer_suit_named_geometry": not leaked,
        "undersuit_declares_no_oversuit": bool(undersuit and undersuit.get("contains_oversuit") is False),
        "undersuit_has_material": bool(undersuit and undersuit.data.materials),
        "all_renderable_bounds_finite": all(finite_bounds(obj) for obj in renderables),
    }

    attachment = {}
    if head and hair:
        head_center = world_center(head)
        hair_center = world_center(hair)
        separation = (hair_center - head_center).length
        attachment = {
            "head_center": list(head_center),
            "hair_center": list(hair_center),
            "center_separation_m": separation,
        }
        checks["hair_remains_attached"] = separation < 0.25
    else:
        checks["hair_remains_attached"] = False

    report = {
        "schema": 1,
        "asset": ASSET.relative_to(ROOT).as_posix(),
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "missing": missing,
        "forbidden_geometry": leaked,
        "renderable_count": len(renderables),
        "attachment": attachment,
    }
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("V16_VALIDATION", json.dumps(report, separators=(",", ":")))
    if report["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
