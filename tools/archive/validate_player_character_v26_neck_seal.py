"""Validate the V26 conforming neck seal and skin-interface cleanup."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bmesh
import bpy


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
ASSET = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v26.blend"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v26_Validation.json"
FORBIDDEN = ("helmet", "visor", "oversuit", "armor", "armour", "backpack", "rear_pack")


def boundary_vertex_count(body: bpy.types.Object) -> int:
    bm = bmesh.new()
    bm.from_mesh(body.data)
    count = sum(1 for vertex in bm.verts if any(edge.is_boundary for edge in vertex.link_edges))
    bm.free()
    return count


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(ASSET))
    rig = bpy.data.objects.get("RIG_PlayerCharacter_CryoBodysuit_v26")
    body = bpy.data.objects.get("SK_PlayerCharacter_CryoBodysuit_v26")
    seal = bpy.data.objects.get("SK_PlayerCharacter_CryoNeckSeal_v26")
    head = bpy.data.objects.get("SK_PlayerHead_Production_v6")
    seams = [
        bpy.data.objects.get("SK_CryoSeam_CenterFront_v26"),
        bpy.data.objects.get("SK_CryoSeam_LeftLeg_v26"),
        bpy.data.objects.get("SK_CryoSeam_RightLeg_v26"),
    ]
    renderables = [
        obj for obj in bpy.context.scene.objects
        if obj.type in {"MESH", "CURVE"} and not obj.hide_render
    ]
    leaked = [
        obj.name for obj in renderables
        if any(token in obj.name.lower() for token in FORBIDDEN)
    ]
    boundary_count = boundary_vertex_count(body) if body else 0
    checks = {
        "required_assets_present": bool(rig and body and seal and head and all(seams)),
        "single_neck_boundary_preserved": boundary_count == 158,
        "conforming_shape_declared": bool(body and body.get("v26_neckline_shape")),
        "head_interface_cleanup_declared": bool(head and head.get("v26_interface_cleanup")),
        "head_mask_preserved": bool(
            head
            and head.vertex_groups.get("V24_HeadNeckKeep")
            and head.modifiers.get("V24_NeckOnlyBoundary")
        ),
        "seal_is_quad_only": bool(
            seal and all(len(polygon.vertices) == 4 for polygon in seal.data.polygons)
        ),
        "seal_density_expected": bool(
            seal and len(seal.data.vertices) == 1280 and len(seal.data.polygons) == 1280
        ),
        "seal_is_rigged": bool(
            seal and any(modifier.type == "ARMATURE" for modifier in seal.modifiers)
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
        "neck_boundary_vertices": boundary_count,
        "seal_vertices": len(seal.data.vertices) if seal else 0,
        "seal_quads": len(seal.data.polygons) if seal else 0,
        "forbidden_geometry": leaked,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("V26_VALIDATION", json.dumps(result, separators=(",", ":")))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
