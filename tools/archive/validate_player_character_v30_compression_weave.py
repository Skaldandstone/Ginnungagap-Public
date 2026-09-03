"""Validate the V30 compression-weave material refinement."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
ASSET = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v30.blend"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v30_Validation.json"
FORBIDDEN = ("helmet", "visor", "oversuit", "armor", "armour", "backpack", "rear_pack")


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(ASSET))
    rig = bpy.data.objects.get("RIG_PlayerCharacter_CryoBodysuit_v30")
    body = bpy.data.objects.get("SK_PlayerCharacter_CryoBodysuit_v30")
    seal = bpy.data.objects.get("SK_PlayerCharacter_CryoNeckSeal_v30")
    seams = [
        bpy.data.objects.get("SK_CryoSeam_CenterFront_v30"),
        bpy.data.objects.get("SK_CryoSeam_LeftLeg_v30"),
        bpy.data.objects.get("SK_CryoSeam_RightLeg_v30"),
    ]
    renderables = [
        obj for obj in bpy.context.scene.objects
        if obj.type in {"MESH", "CURVE"} and not obj.hide_render
    ]
    leaked = [
        obj.name for obj in renderables
        if any(token in obj.name.lower() for token in FORBIDDEN)
    ]
    attribute = body.data.color_attributes.get("V30_CompressionWeaveMask") if body else None
    values = [float(item.color[0]) for item in attribute.data] if attribute else []
    material = body.data.materials[0] if body and body.data.materials else None
    nodes = material.node_tree.nodes if material else None
    mask_node = nodes.get("V30_CompressionWeaveMask") if nodes else None
    noise = nodes.get("V30_CompressionMicroWeave") if nodes else None
    modulation = nodes.get("V30_CompressionModulate") if nodes else None
    dye_noise = nodes.get("V18_DyeVariation") if nodes else None
    dye_palette = nodes.get("V18_DyePalette") if nodes else None
    checks = {
        "required_assets_present": bool(rig and body and seal and all(seams)),
        "compression_weave_mask_present": bool(attribute and values),
        "mask_strength_is_capped": bool(values and max(values) <= 0.4801),
        "mask_has_no_hard_full_strength_vertices": bool(values and not any(value > 0.5 for value in values)),
        "mask_mean_is_subtle": bool(values and sum(values) / len(values) < 0.065),
        "mask_node_uses_v30_attribute": bool(
            mask_node and mask_node.layer_name == "V30_CompressionWeaveMask"
        ),
        "procedural_weave_nodes_present": bool(noise and modulation),
        "base_dye_noise_refined": bool(
            dye_noise and abs(float(dye_noise.inputs["Scale"].default_value) - 28.0) < 0.01
        ),
        "pale_dye_palette_preserved": bool(
            dye_palette
            and dye_palette.color_ramp.elements[0].color[0] >= 0.12
            and dye_palette.color_ramp.elements[-1].color[0] <= 0.18
        ),
        "v29_glove_refinement_preserved": bool(body and body.get("v29_integrated_gloves")),
        "v28_surface_finish_preserved": bool(body and body.modifiers.get("V28_FabricSurfaceRelax")),
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
        "mask_mean": sum(values) / len(values) if values else 0.0,
        "mask_max": max(values) if values else 0.0,
        "mask_vertices_above_half": sum(value > 0.5 for value in values),
        "forbidden_geometry": leaked,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("V30_VALIDATION", json.dumps(result, separators=(",", ":")))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
