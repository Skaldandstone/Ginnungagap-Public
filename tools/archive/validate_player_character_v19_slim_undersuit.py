"""Validate V19's slimmer undersuit envelope and retained material system."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
ASSET = SUIT_DIR / "PlayerCharacter_Undersuit_Concept_v19.blend"
REPORT = SUIT_DIR / "PlayerCharacter_Undersuit_v19_Validation.json"
FORBIDDEN = ("helmet", "visor", "oversuit", "armor", "armour", "backpack", "rear_pack")
MATERIALS = {
    "M_V18_PressureWeave_Base",
    "M_V18_PressureWeave_Flex",
    "M_V18_BondedNeckSeal",
}


def dimensions(obj):
    return [round(value, 6) for value in obj.dimensions]


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(ASSET))
    rig = bpy.data.objects.get("RIG_PlayerCharacter_Undersuit_v19")
    suit = bpy.data.objects.get("SK_PlayerCharacter_Undersuit_v19")
    yoke = bpy.data.objects.get("SK_PlayerUndersuit_NeckYoke_v19")
    renderables = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE"} and not obj.hide_render]
    leaked = [obj.name for obj in renderables if any(token in obj.name.lower() for token in FORBIDDEN)]
    assigned = {
        material.name
        for obj in (suit, yoke)
        if obj
        for material in obj.data.materials
        if material
    }
    yoke_solidify = next((modifier for modifier in yoke.modifiers if modifier.type == "SOLIDIFY"), None) if yoke else None
    checks = {
        "required_objects_present": bool(rig and suit and yoke),
        "bone_centered_reduction_recorded": bool(suit and suit.get("v19_silhouette_pass")),
        "low_profile_yoke_recorded": bool(yoke and yoke.get("v19_silhouette_pass")),
        "yoke_thickness_is_undersuit_scale": bool(yoke_solidify and yoke_solidify.thickness <= 0.002),
        "v18_material_system_preserved": MATERIALS.issubset(assigned),
        "character_declares_no_oversuit": bool(suit and suit.get("contains_oversuit") is False),
        "no_outer_suit_geometry": not leaked,
        "finite_renderable_geometry": all(
            math.isfinite(value) for obj in renderables for corner in obj.bound_box for value in corner
        ),
    }
    result = {
        "schema": 1,
        "asset": ASSET.relative_to(ROOT).as_posix(),
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "suit_dimensions_m": dimensions(suit) if suit else None,
        "yoke_dimensions_m": dimensions(yoke) if yoke else None,
        "assigned_materials": sorted(assigned),
        "forbidden_geometry": leaked,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("V19_VALIDATION", json.dumps(result, separators=(",", ":")))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
