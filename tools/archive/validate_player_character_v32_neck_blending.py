"""Validate the V32 neck-interface blending pass."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bmesh
import bpy


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
ASSET = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v32.blend"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v32_Validation.json"
FORBIDDEN = ("helmet", "visor", "oversuit", "armor", "armour", "backpack", "rear_pack", "proxy")


def boundary_count(obj: bpy.types.Object) -> int:
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    count = sum(any(edge.is_boundary for edge in vertex.link_edges) for vertex in bm.verts)
    bm.free()
    return count


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(ASSET))
    rig = bpy.data.objects.get("RIG_PlayerCharacter_CryoBodysuit_v32")
    body = bpy.data.objects.get("SK_PlayerCharacter_CryoBodysuit_v32")
    seal = bpy.data.objects.get("SK_PlayerCharacter_CryoNeckSeal_v32")
    head = bpy.data.objects.get("SK_PlayerHead_Production_v6")
    seams = [bpy.data.objects.get(name) for name in (
        "SK_CryoSeam_CenterFront_v32", "SK_CryoSeam_LeftLeg_v32", "SK_CryoSeam_RightLeg_v32"
    )]
    renderables = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE"} and not obj.hide_render]
    leaked = [obj.name for obj in renderables if any(token in obj.name.lower() for token in FORBIDDEN)]
    mask = body.data.color_attributes.get("V30_CompressionWeaveMask") if body else None
    values = [float(item.color[0]) for item in mask.data] if mask else []
    checks = {
        "required_assets_present": bool(rig and body and seal and head and all(seams)),
        "head_topology_preserved": bool(head and len(head.data.vertices) == 19158),
        "head_shape_keys_preserved": bool(head and head.data.shape_keys and len(head.data.shape_keys.key_blocks) == 27),
        "v31_anatomy_preserved": bool(head and head.get("v31_neck_anatomy")),
        "v32_body_blend_present": bool(body and body.get("v32_neck_blend")),
        "v32_seal_blend_present": bool(seal and seal.get("v32_neck_blend")),
        "neckline_boundary_preserved": bool(body and boundary_count(body) == 158),
        "seal_uses_body_fabric": bool(body and seal and body.data.materials and seal.data.materials and body.data.materials[0] == seal.data.materials[0]),
        "compression_mask_preserved": bool(values and max(values) <= 0.4801),
        "earlier_surface_work_preserved": bool(body and body.get("v29_integrated_gloves") and body.modifiers.get("V28_FabricSurfaceRelax")),
        "declares_no_oversuit": bool(body and body.get("contains_oversuit") is False),
        "no_forbidden_geometry": not leaked,
        "finite_geometry": all(math.isfinite(value) for obj in renderables for corner in obj.bound_box for value in corner),
    }
    result = {
        "schema": 1,
        "asset": ASSET.relative_to(ROOT).as_posix(),
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "forbidden_geometry": leaked,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("V32_VALIDATION", json.dumps(result, separators=(",", ":")))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
