"""Validate V22's compact neckline integration and preserved cryo details."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
ASSET = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v22.blend"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v22_Validation.json"
FORBIDDEN = ("helmet", "visor", "oversuit", "armor", "armour", "backpack", "rear_pack")


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(ASSET))
    body = bpy.data.objects.get("SK_PlayerCharacter_CryoBodysuit_v22")
    gasket = bpy.data.objects.get("SK_PlayerCharacter_CryoGasket_v22")
    bridge = bpy.data.objects.get("SK_PlayerCharacter_CryoNeckBridge_v22")
    seams = [
        bpy.data.objects.get("SK_CryoSeam_CenterFront_v22"),
        bpy.data.objects.get("SK_CryoSeam_LeftLeg_v22"),
        bpy.data.objects.get("SK_CryoSeam_RightLeg_v22"),
    ]
    renderables = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE"} and not obj.hide_render]
    leaked = [obj.name for obj in renderables if any(token in obj.name.lower() for token in FORBIDDEN)]
    bridge_thickness = next((m.thickness for m in bridge.modifiers if m.type == "SOLIDIFY"), None) if bridge else None
    details = [obj for obj in [gasket, bridge, *seams] if obj]
    checks = {
        "required_assets_present": bool(body and gasket and bridge and all(seams)),
        "localized_shoulder_cleanup_recorded": bool(body and body.get("v22_shoulder_cleanup")),
        "compact_bridge_is_soft_layer_scale": bool(bridge_thickness and bridge_thickness <= 0.0011),
        "all_details_are_cryo_layer": all(
            obj.get("semantic_layer") == "character_cryo_bodysuit" for obj in details
        ),
        "all_details_deform_with_rig": all(
            any(modifier.type == "ARMATURE" for modifier in obj.modifiers) for obj in details
        ),
        "compression_mask_preserved": bool(body and body.data.color_attributes.get("V21_CompressionMask")),
        "character_declares_no_oversuit": bool(body and body.get("contains_oversuit") is False),
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
        "bridge_thickness_m": bridge_thickness,
        "detail_objects": [obj.name for obj in details],
        "forbidden_geometry": leaked,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("V22_VALIDATION", json.dumps(result, separators=(",", ":")))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
