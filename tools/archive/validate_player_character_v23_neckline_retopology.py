"""Validate the V23 local quad neckline retopology."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
ASSET = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v23.blend"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v23_Validation.json"
FORBIDDEN = ("helmet", "visor", "oversuit", "armor", "armour", "backpack", "rear_pack")


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(ASSET))
    body = bpy.data.objects.get("SK_PlayerCharacter_CryoBodysuit_v23")
    patch = bpy.data.objects.get("SK_PlayerCharacter_CryoNeckRetopo_v23")
    gasket = bpy.data.objects.get("SK_PlayerCharacter_CryoGasket_v23")
    old_bridge = bpy.data.objects.get("SK_PlayerCharacter_CryoNeckBridge_v22")
    seams = [
        bpy.data.objects.get("SK_CryoSeam_CenterFront_v23"),
        bpy.data.objects.get("SK_CryoSeam_LeftLeg_v23"),
        bpy.data.objects.get("SK_CryoSeam_RightLeg_v23"),
    ]
    renderables = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE"} and not obj.hide_render]
    leaked = [obj.name for obj in renderables if any(token in obj.name.lower() for token in FORBIDDEN)]
    patch_modifier_types = {modifier.type for modifier in patch.modifiers} if patch else set()
    checks = {
        "required_assets_present": bool(body and patch and gasket and all(seams)),
        "temporary_bridge_removed": old_bridge is None,
        "retopology_is_quad_only": bool(patch and all(len(poly.vertices) == 4 for poly in patch.data.polygons)),
        "expected_local_patch_density": bool(
            patch and len(patch.data.vertices) == 632 and len(patch.data.polygons) == 474
        ),
        "rig_weights_transferred": bool(patch and len(patch.vertex_groups) >= 20),
        "armature_deformation_present": "ARMATURE" in patch_modifier_types,
        "patch_is_cryo_layer": bool(patch and patch.get("semantic_layer") == "character_cryo_bodysuit"),
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
        "patch_vertices": len(patch.data.vertices) if patch else 0,
        "patch_quads": len(patch.data.polygons) if patch else 0,
        "patch_vertex_groups": len(patch.vertex_groups) if patch else 0,
        "forbidden_geometry": leaked,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("V23_VALIDATION", json.dumps(result, separators=(",", ":")))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
