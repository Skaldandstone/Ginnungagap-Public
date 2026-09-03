"""Validate the V28 cryo-bodysuit surface finish."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
ASSET = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v28.blend"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v28_Validation.json"
FORBIDDEN = ("helmet", "visor", "oversuit", "armor", "armour", "backpack", "rear_pack")


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(ASSET))
    rig = bpy.data.objects.get("RIG_PlayerCharacter_CryoBodysuit_v28")
    body = bpy.data.objects.get("SK_PlayerCharacter_CryoBodysuit_v28")
    seal = bpy.data.objects.get("SK_PlayerCharacter_CryoNeckSeal_v28")
    head = bpy.data.objects.get("SK_PlayerHead_Production_v6")
    seams = [
        bpy.data.objects.get("SK_CryoSeam_CenterFront_v28"),
        bpy.data.objects.get("SK_CryoSeam_LeftLeg_v28"),
        bpy.data.objects.get("SK_CryoSeam_RightLeg_v28"),
    ]
    renderables = [
        obj for obj in bpy.context.scene.objects
        if obj.type in {"MESH", "CURVE"} and not obj.hide_render
    ]
    leaked = [
        obj.name for obj in renderables
        if any(token in obj.name.lower() for token in FORBIDDEN)
    ]
    smoothing = body.modifiers.get("V28_FabricSurfaceRelax") if body else None
    material = body.data.materials[0] if body and body.data.materials else None
    bump = material.node_tree.nodes.get("V18_TextileNormal") if material else None
    bump_strength = float(bump.inputs["Strength"].default_value) if bump else -1.0
    checks = {
        "required_assets_present": bool(rig and body and seal and head and all(seams)),
        "surface_relaxation_present": bool(
            smoothing and smoothing.type == "LAPLACIANSMOOTH" and smoothing.iterations == 2
        ),
        "surface_relaxation_is_subtle": bool(smoothing and 0.0 < smoothing.lambda_factor <= 0.025),
        "textile_bump_refined": 0.0 <= bump_strength <= 0.0081,
        "surface_finish_declared": bool(body and body.get("v28_surface_finish")),
        "production_head_base_topology_preserved": bool(head and len(head.data.vertices) == 19158),
        "no_rejected_neck_proxy": bpy.data.objects.get("SK_PlayerCharacter_CleanNeck_v27") is None,
        "no_rejected_collar": bpy.data.objects.get("SK_PlayerCharacter_CryoCompressionCollar_v27") is None,
        "no_rejected_rear_patch": bpy.data.objects.get("SK_PlayerCharacter_RearNeckRetopo_v28") is None,
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
        "surface_lambda": float(smoothing.lambda_factor) if smoothing else 0.0,
        "surface_iterations": smoothing.iterations if smoothing else 0,
        "textile_bump_strength": bump_strength,
        "forbidden_geometry": leaked,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("V28_VALIDATION", json.dumps(result, separators=(",", ":")))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
