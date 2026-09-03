"""Validate the V18 undersuit material pass and character-only boundary."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
ASSET = SUIT_DIR / "PlayerCharacter_Undersuit_Concept_v18.blend"
REPORT = SUIT_DIR / "PlayerCharacter_Undersuit_v18_Validation.json"
MATERIALS = (
    "M_V18_PressureWeave_Base",
    "M_V18_PressureWeave_Flex",
    "M_V18_BondedNeckSeal",
)
FORBIDDEN = ("helmet", "visor", "oversuit", "armor", "armour", "backpack", "rear_pack")


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(ASSET))
    suit = bpy.data.objects.get("SK_PlayerCharacter_Undersuit_v18")
    yoke = bpy.data.objects.get("SK_PlayerUndersuit_NeckYoke_v18")
    materials = {name: bpy.data.materials.get(name) for name in MATERIALS}
    renderables = [obj for obj in bpy.context.scene.objects if obj.type in {"MESH", "CURVE"} and not obj.hide_render]
    leaked = [obj.name for obj in renderables if any(token in obj.name.lower() for token in FORBIDDEN)]
    required_nodes = {"V18_DyeVariation", "V18_CrossWeave", "V18_MicroFiber", "V18_TextileNormal"}
    node_checks = {
        name: bool(material and material.use_nodes and required_nodes.issubset(material.node_tree.nodes.keys()))
        for name, material in materials.items()
    }
    assigned = set(material.name for obj in (suit, yoke) if obj for material in obj.data.materials if material)
    flex_polygons = sum(1 for polygon in suit.data.polygons if polygon.material_index == 1) if suit else 0
    checks = {
        "character_assets_present": bool(suit and yoke),
        "all_shader_graphs_complete": all(node_checks.values()),
        "all_materials_assigned": set(MATERIALS).issubset(assigned),
        "flex_regions_exist": flex_polygons > 0,
        "character_declares_no_oversuit": bool(suit and suit.get("contains_oversuit") is False),
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
        "material_node_checks": node_checks,
        "assigned_materials": sorted(assigned),
        "flex_polygon_count": flex_polygons,
        "forbidden_geometry": leaked,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print("V18_VALIDATION", json.dumps(result, separators=(",", ":")))
    if result["status"] != "pass":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
