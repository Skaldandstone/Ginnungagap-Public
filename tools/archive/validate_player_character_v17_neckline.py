"""Validate the V17 character-only neckline pass."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
ASSET = SUIT_DIR / "PlayerCharacter_Undersuit_Concept_v17.blend"
REPORT = SUIT_DIR / "PlayerCharacter_Undersuit_v17_Validation.json"
FORBIDDEN = ("helmet", "visor", "oversuit", "armor", "armour", "backpack", "rear_pack")


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(ASSET))
    rig = bpy.data.objects.get("RIG_PlayerCharacter_Undersuit_v17")
    suit = bpy.data.objects.get("SK_PlayerCharacter_Undersuit_v17")
    head = bpy.data.objects.get("SK_PlayerHead_Production_v6")
    yoke = bpy.data.objects.get("SK_PlayerUndersuit_NeckYoke_v17")
    required = {"rig": rig, "undersuit": suit, "head": head, "neck_yoke": yoke}
    missing = [name for name, obj in required.items() if obj is None]
    renderables = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE"} and not obj.hide_render]
    leaked = [obj.name for obj in renderables if any(term in obj.name.lower() for term in FORBIDDEN)]
    modifier_types = {modifier.type for modifier in yoke.modifiers} if yoke else set()
    checks = {
        "required_objects_present": not missing,
        "no_outer_suit_geometry": not leaked,
        "character_asset_declares_no_oversuit": bool(suit and suit.get("contains_oversuit") is False),
        "yoke_is_undersuit_layer": bool(yoke and yoke.get("semantic_layer") == "character_undersuit"),
        "yoke_has_armature_deformation": "ARMATURE" in modifier_types,
        "yoke_conforms_to_undersuit": "SHRINKWRAP" in modifier_types,
        "finite_renderable_geometry": all(
            math.isfinite(value)
            for obj in renderables
            for corner in obj.bound_box
            for value in corner
        ),
    }
    result = {
        "schema": 1,
        "asset": ASSET.relative_to(ROOT).as_posix(),
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "missing": missing,
        "forbidden_geometry": leaked,
        "renderable_count": len(renderables),
        "yoke_modifiers": sorted(modifier_types),
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("V17_VALIDATION", json.dumps(result, separators=(",", ":")))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
