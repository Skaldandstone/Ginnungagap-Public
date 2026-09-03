"""Validate V21 cryo garment seam, compression, and gasket details."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
ASSET = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v21.blend"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v21_Validation.json"
SEAMS = (
    "SK_CryoSeam_CenterFront_v21",
    "SK_CryoSeam_LeftLeg_v21",
    "SK_CryoSeam_RightLeg_v21",
)
FORBIDDEN = ("helmet", "visor", "oversuit", "armor", "armour", "backpack", "rear_pack")


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(ASSET))
    body = bpy.data.objects.get("SK_PlayerCharacter_CryoBodysuit_v21")
    gasket = bpy.data.objects.get("SK_PlayerCharacter_CryoGasket_v21")
    seams = [bpy.data.objects.get(name) for name in SEAMS]
    material = bpy.data.materials.get("M_V21_CryoCompressionFabric")
    bonded = bpy.data.materials.get("M_V21_BondedCryoSeam")
    compression = body.data.color_attributes.get("V21_CompressionMask") if body else None
    renderables = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE"} and not obj.hide_render]
    leaked = [obj.name for obj in renderables if any(token in obj.name.lower() for token in FORBIDDEN)]
    detail_objects = [obj for obj in [gasket, *seams] if obj]
    checks = {
        "body_and_gasket_present": bool(body and gasket),
        "all_bonded_seams_present": all(seams),
        "continuous_compression_mask_present": bool(compression and compression.domain == "POINT"),
        "detail_materials_present": bool(material and bonded),
        "all_details_are_undersuit_layer": all(
            obj.get("semantic_layer") == "character_cryo_bodysuit" for obj in detail_objects
        ),
        "all_details_deform_with_rig": all(
            any(modifier.type == "ARMATURE" for modifier in obj.modifiers) for obj in detail_objects
        ),
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
        "seams": [obj.name for obj in seams if obj],
        "compression_attribute": compression.name if compression else None,
        "detail_objects": [obj.name for obj in detail_objects],
        "forbidden_geometry": leaked,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("V21_VALIDATION", json.dumps(result, separators=(",", ":")))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
