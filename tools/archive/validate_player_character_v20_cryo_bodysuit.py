"""Validate the V20 continuous cryo bodysuit rebuild."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
ASSET = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v20.blend"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v20_Validation.json"
FORBIDDEN = ("helmet", "visor", "oversuit", "armor", "armour", "backpack", "rear_pack")


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(ASSET))
    rig = bpy.data.objects.get("RIG_PlayerCharacter_CryoBodysuit_v20")
    body = bpy.data.objects.get("SK_PlayerCharacter_CryoBodysuit_v20")
    collar = bpy.data.objects.get("SK_PlayerCharacter_CryoCollar_v20")
    material = bpy.data.materials.get("M_V20_CryoCompressionFabric")
    renderables = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE"} and not obj.hide_render]
    leaked = [obj.name for obj in renderables if any(token in obj.name.lower() for token in FORBIDDEN)]
    modifier_types = {modifier.type for modifier in body.modifiers} if body else set()
    material_nodes = material.node_tree.nodes if material and material.use_nodes else ()
    checks = {
        "required_objects_present": bool(rig and body and collar),
        "continuous_shell_recorded": bool(body and body.get("v20_topology") == "continuous voxel-fused anatomical shell"),
        "production_density_retained": bool(body and len(body.data.vertices) > 50000),
        "rig_weights_transferred": bool(body and len(body.vertex_groups) >= 20),
        "armature_deformation_present": "ARMATURE" in modifier_types,
        "single_cryo_body_material": bool(body and len(body.data.materials) == 1 and body.data.materials[0] == material),
        "procedural_textile_retained": bool(material and "V18_TextileNormal" in material_nodes),
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
        "body_vertices": len(body.data.vertices) if body else 0,
        "body_polygons": len(body.data.polygons) if body else 0,
        "vertex_groups": len(body.vertex_groups) if body else 0,
        "forbidden_geometry": leaked,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("V20_VALIDATION", json.dumps(result, separators=(",", ":")))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
