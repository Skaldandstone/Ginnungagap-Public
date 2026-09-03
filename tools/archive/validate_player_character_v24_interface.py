"""Validate the V24 neck/skin interface and upper-silhouette refinement."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
ASSET = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v24.blend"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v24_Validation.json"
FORBIDDEN = ("helmet", "visor", "oversuit", "armor", "armour", "backpack", "rear_pack")


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(ASSET))
    rig = bpy.data.objects.get("RIG_PlayerCharacter_CryoBodysuit_v24")
    body = bpy.data.objects.get("SK_PlayerCharacter_CryoBodysuit_v24")
    patch = bpy.data.objects.get("SK_PlayerCharacter_CryoNeckRetopo_v24")
    gasket = bpy.data.objects.get("SK_PlayerCharacter_CryoGasket_v24")
    head = bpy.data.objects.get("SK_PlayerHead_Production_v6")
    seams = [
        bpy.data.objects.get("SK_CryoSeam_CenterFront_v24"),
        bpy.data.objects.get("SK_CryoSeam_LeftLeg_v24"),
        bpy.data.objects.get("SK_CryoSeam_RightLeg_v24"),
    ]
    renderables = [
        obj for obj in bpy.context.scene.objects
        if obj.type in {"MESH", "CURVE"} and not obj.hide_render
    ]
    leaked = [
        obj.name for obj in renderables
        if any(token in obj.name.lower() for token in FORBIDDEN)
    ]
    head_mask = head.modifiers.get("V24_NeckOnlyBoundary") if head else None
    patch_modifier_types = {modifier.type for modifier in patch.modifiers} if patch else set()
    checks = {
        "required_assets_present": bool(rig and body and patch and gasket and head and all(seams)),
        "head_boundary_mask_present": bool(head_mask and head_mask.type == "MASK"),
        "head_boundary_group_present": bool(head and head.vertex_groups.get("V24_HeadNeckKeep")),
        "head_interface_cleanup_declared": bool(head and head.get("v24_interface_cleanup")),
        "upper_silhouette_refinement_declared": bool(body and body.get("v24_upper_silhouette")),
        "retopology_remains_quad_only": bool(
            patch and all(len(poly.vertices) == 4 for poly in patch.data.polygons)
        ),
        "retopology_density_preserved": bool(
            patch and len(patch.data.vertices) == 632 and len(patch.data.polygons) == 474
        ),
        "retopology_rigged": bool(
            patch and len(patch.vertex_groups) >= 20 and "ARMATURE" in patch_modifier_types
        ),
        "compression_mask_preserved": bool(
            body and body.data.color_attributes.get("V21_CompressionMask")
        ),
        "character_declares_no_oversuit": bool(body and body.get("contains_oversuit") is False),
        "no_outer_suit_geometry": not leaked,
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
        "patch_vertices": len(patch.data.vertices) if patch else 0,
        "patch_quads": len(patch.data.polygons) if patch else 0,
        "head_vertices": len(head.data.vertices) if head else 0,
        "forbidden_geometry": leaked,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("V24_VALIDATION", json.dumps(result, separators=(",", ":")))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
