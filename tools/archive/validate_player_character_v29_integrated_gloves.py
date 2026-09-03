"""Validate the V29 deformation-safe integrated glove refinement."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
ASSET = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v29.blend"
PASS_REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v29_GlovePass.json"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v29_Validation.json"
FORBIDDEN = ("helmet", "visor", "oversuit", "armor", "armour", "backpack", "rear_pack")


def group_members(body: bpy.types.Object, name: str) -> int:
    group = body.vertex_groups.get(name)
    if group is None:
        return 0
    return sum(
        1 for vertex in body.data.vertices
        if any(item.group == group.index and item.weight > 0.0 for item in vertex.groups)
    )


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(ASSET))
    pass_data = json.loads(PASS_REPORT.read_text(encoding="utf-8"))
    rig = bpy.data.objects.get("RIG_PlayerCharacter_CryoBodysuit_v29")
    body = bpy.data.objects.get("SK_PlayerCharacter_CryoBodysuit_v29")
    seal = bpy.data.objects.get("SK_PlayerCharacter_CryoNeckSeal_v29")
    seams = [
        bpy.data.objects.get("SK_CryoSeam_CenterFront_v29"),
        bpy.data.objects.get("SK_CryoSeam_LeftLeg_v29"),
        bpy.data.objects.get("SK_CryoSeam_RightLeg_v29"),
    ]
    renderables = [
        obj for obj in bpy.context.scene.objects
        if obj.type in {"MESH", "CURVE"} and not obj.hide_render
    ]
    leaked = [
        obj.name for obj in renderables
        if any(token in obj.name.lower() for token in FORBIDDEN)
    ]
    changed_left = int(pass_data["gloves"]["l"]["changed_vertices"])
    changed_right = int(pass_data["gloves"]["r"]["changed_vertices"])
    checks = {
        "required_assets_present": bool(rig and body and seal and all(seams)),
        "glove_refinement_declared": bool(body and body.get("v29_integrated_gloves")),
        "left_glove_vertices_changed": changed_left > 1000,
        "right_glove_vertices_changed": changed_right > 1000,
        "bilateral_edit_is_balanced": abs(changed_left - changed_right) <= 32,
        "empty_hand_groups_documented": bool(
            body and group_members(body, "hand_l") == 0 and group_members(body, "hand_r") == 0
        ),
        "actual_lowerarm_weights_preserved": bool(
            body
            and group_members(body, "lowerarm_l") > 2000
            and group_members(body, "lowerarm_r") > 2000
        ),
        "rejected_finger_channels_absent": not any(
            obj.name.startswith("SK_CryoGloveFingerChannels_") for obj in bpy.data.objects
        ),
        "surface_finish_preserved": bool(
            body and body.modifiers.get("V28_FabricSurfaceRelax")
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
        "changed_glove_vertices": {"left": changed_left, "right": changed_right},
        "hand_group_members": {
            "left": group_members(body, "hand_l") if body else 0,
            "right": group_members(body, "hand_r") if body else 0,
        },
        "forbidden_geometry": leaked,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("V29_VALIDATION", json.dumps(result, separators=(",", ":")))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
