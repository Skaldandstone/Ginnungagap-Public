"""Validate the V25 welded neckline garment shell."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bmesh
import bpy


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
ASSET = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v25.blend"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v25_Validation.json"
FORBIDDEN = ("helmet", "visor", "oversuit", "armor", "armour", "backpack", "rear_pack")


def boundary_components(body: bpy.types.Object) -> list[set[int]]:
    bm = bmesh.new()
    bm.from_mesh(body.data)
    adjacency: dict[int, set[int]] = {}
    for edge in bm.edges:
        if edge.is_boundary:
            a, b = edge.verts[0].index, edge.verts[1].index
            adjacency.setdefault(a, set()).add(b)
            adjacency.setdefault(b, set()).add(a)
    unseen = set(adjacency)
    components = []
    while unseen:
        seed = unseen.pop()
        component = {seed}
        stack = [seed]
        while stack:
            current = stack.pop()
            for neighbor in adjacency[current]:
                if neighbor not in component:
                    component.add(neighbor)
                    unseen.discard(neighbor)
                    stack.append(neighbor)
        components.append(component)
    bm.free()
    return components


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(ASSET))
    rig = bpy.data.objects.get("RIG_PlayerCharacter_CryoBodysuit_v25")
    body = bpy.data.objects.get("SK_PlayerCharacter_CryoBodysuit_v25")
    gasket = bpy.data.objects.get("SK_PlayerCharacter_CryoGasket_v25")
    head = bpy.data.objects.get("SK_PlayerHead_Production_v6")
    seams = [
        bpy.data.objects.get("SK_CryoSeam_CenterFront_v25"),
        bpy.data.objects.get("SK_CryoSeam_LeftLeg_v25"),
        bpy.data.objects.get("SK_CryoSeam_RightLeg_v25"),
    ]
    renderables = [
        obj for obj in bpy.context.scene.objects
        if obj.type in {"MESH", "CURVE"} and not obj.hide_render
    ]
    leaked = [
        obj.name for obj in renderables
        if any(token in obj.name.lower() for token in FORBIDDEN)
    ]
    components = boundary_components(body) if body else []
    checks = {
        "required_assets_present": bool(rig and body and gasket and head and all(seams)),
        "temporary_patch_integrated": bpy.data.objects.get("SK_PlayerCharacter_CryoNeckTransition_v25") is None,
        "old_v24_patch_removed": bpy.data.objects.get("SK_PlayerCharacter_CryoNeckRetopo_v24") is None,
        "welded_neckline_declared": bool(body and body.get("v25_neckline_topology")),
        "upper_back_cleanup_declared": bool(body and body.get("v25_upper_back_cleanup")),
        "compression_mask_preserved": bool(
            body and body.data.color_attributes.get("V21_CompressionMask")
        ),
        "armature_deformation_preserved": bool(
            body and any(modifier.type == "ARMATURE" for modifier in body.modifiers)
        ),
        "neck_boundary_cycle_present": any(len(component) == 158 for component in components),
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
        "body_vertices": len(body.data.vertices) if body else 0,
        "body_polygons": len(body.data.polygons) if body else 0,
        "boundary_component_sizes": sorted((len(component) for component in components), reverse=True),
        "forbidden_geometry": leaked,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("V25_VALIDATION", json.dumps(result, separators=(",", ":")))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
