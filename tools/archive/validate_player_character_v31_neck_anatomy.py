"""Validate the V31 neck-anatomy and neckline-fit pass."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bmesh
import bpy


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
ASSET = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v31.blend"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v31_Validation.json"
FORBIDDEN = ("helmet", "visor", "oversuit", "armor", "armour", "backpack", "rear_pack")
UNWANTED_NECK_PARTS = ("proxy", "collar", "rear_patch", "neck_patch")


def boundary_vertex_count(obj: bpy.types.Object) -> int:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    count = sum(any(edge.is_boundary for edge in vertex.link_edges) for vertex in bm.verts)
    bm.free()
    return count


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(ASSET))
    rig = bpy.data.objects.get("RIG_PlayerCharacter_CryoBodysuit_v31")
    body = bpy.data.objects.get("SK_PlayerCharacter_CryoBodysuit_v31")
    seal = bpy.data.objects.get("SK_PlayerCharacter_CryoNeckSeal_v31")
    head = bpy.data.objects.get("SK_PlayerHead_Production_v6")
    seams = [
        bpy.data.objects.get("SK_CryoSeam_CenterFront_v31"),
        bpy.data.objects.get("SK_CryoSeam_LeftLeg_v31"),
        bpy.data.objects.get("SK_CryoSeam_RightLeg_v31"),
    ]
    renderables = [
        obj for obj in bpy.context.scene.objects
        if obj.type in {"MESH", "CURVE"} and not obj.hide_render
    ]
    leaked = [
        obj.name for obj in renderables
        if any(token in obj.name.lower() for token in FORBIDDEN)
    ]
    unwanted_neck_parts = [
        obj.name for obj in renderables
        if any(token in obj.name.lower() for token in UNWANTED_NECK_PARTS)
    ]
    mask = body.data.color_attributes.get("V30_CompressionWeaveMask") if body else None
    mask_values = [float(item.color[0]) for item in mask.data] if mask else []
    shape_key_count = len(head.data.shape_keys.key_blocks) if head and head.data.shape_keys else 0
    boundary_count = boundary_vertex_count(body) if body else 0
    checks = {
        "required_assets_present": bool(rig and body and seal and head and all(seams)),
        "production_head_vertex_count_preserved": bool(head and len(head.data.vertices) == 19158),
        "all_head_shape_keys_preserved": shape_key_count == 27,
        "neck_anatomy_metadata_present": bool(head and head.get("v31_neck_anatomy")),
        "body_neckline_fit_metadata_present": bool(body and body.get("v31_neckline_fit")),
        "seal_neckline_fit_metadata_present": bool(seal and seal.get("v31_neckline_fit")),
        "ordered_neckline_boundary_preserved": boundary_count == 158,
        "v30_compression_mask_preserved": bool(mask_values and max(mask_values) <= 0.4801),
        "v29_glove_refinement_preserved": bool(body and body.get("v29_integrated_gloves")),
        "v28_surface_finish_preserved": bool(body and body.modifiers.get("V28_FabricSurfaceRelax")),
        "character_declares_no_oversuit": bool(body and body.get("contains_oversuit") is False),
        "no_outer_suit_geometry": not leaked,
        "no_added_proxy_or_collar_geometry": not unwanted_neck_parts,
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
        "head_vertex_count": len(head.data.vertices) if head else 0,
        "head_shape_key_count": shape_key_count,
        "neckline_boundary_vertices": boundary_count,
        "compression_mask_max": max(mask_values) if mask_values else 0.0,
        "forbidden_geometry": leaked,
        "unwanted_neck_geometry": unwanted_neck_parts,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("V31_VALIDATION", json.dumps(result, separators=(",", ":")))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
