"""Export V7 as an isolated Unreal review package with a machine-readable manifest."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import bpy


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve() if "--" in sys.argv else Path(__file__).resolve().parents[1]
BLEND = ROOT / "Art" / "Characters" / "PlayerSuits" / "PlayerSuit_Production_v7.blend"
OUTPUT = ROOT / "Build" / "Unreal" / "PlayerSuitsV7Review"
FBX = OUTPUT / "SKM_PlayerSuit_Production_v7_Review.fbx"
MANIFEST = OUTPUT / "PlayerSuitV7_ReviewManifest.json"


def main():
    if not BLEND.exists():
        raise RuntimeError(f"Build and validate V7 before export: {BLEND}")
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    armature = bpy.data.objects["RIG_PlayerSuit_Production_v7"]
    shells = bpy.data.collections["SUIT_PRODUCTION_v7_AUTHORED_SHELLS"]
    base = bpy.data.objects["SK_PlayerSuit_Production_v7_BaseGarment"]
    head_components = [obj for obj in bpy.data.objects if obj.get("production_head_component")]
    helmet = [obj for obj in bpy.data.objects if obj.name.startswith("SKV6_Helmet_")]
    selected = [armature, base, *head_components, *helmet, *list(shells.objects)]
    selected = list(dict.fromkeys(selected))
    bpy.ops.object.select_all(action="DESELECT")
    for obj in selected:
        obj.hide_set(False)
        obj.hide_viewport = False
        obj.select_set(True)
    bpy.context.view_layer.objects.active = armature
    OUTPUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=str(FBX),
        use_selection=True,
        object_types={"ARMATURE", "MESH", "CURVE"},
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="-Z",
        axis_up="Y",
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        add_leaf_bones=False,
        bake_anim=False,
        path_mode="RELATIVE",
        embed_textures=False,
    )
    if not FBX.exists() or FBX.stat().st_size < 1024:
        raise RuntimeError(f"V7 FBX export failed: {FBX}")
    modules = [obj for obj in shells.objects if obj.type in {"MESH", "CURVE"}]
    manifest = {
        "schema": 1,
        "status": "review_only_not_runtime_promoted",
        "source": str(BLEND.relative_to(ROOT)).replace("\\", "/"),
        "fbx": str(FBX.relative_to(ROOT)).replace("\\", "/"),
        "destination": "/Game/Characters/Player/Suit/V7Review",
        "asset_name": "SKM_PlayerSuit_Production_v7_Review",
        "skeleton": armature.name,
        "bone_count": len(armature.data.bones),
        "lod_candidates": {
            str(level): len(bpy.data.collections[f"SUIT_PRODUCTION_v7_LOD{level}_CANDIDATES"].objects)
            for level in (1, 2)
        },
        "modules": [
            {
                "name": obj.name,
                "type": obj.type,
                "attachment": obj.get("rig_attachment", "rest-space torso"),
                "material": obj.data.materials[0].name if obj.data.materials else None,
            }
            for obj in sorted(modules, key=lambda item: item.name)
        ],
        "import": {
            "skeletal": True,
            "import_materials": True,
            "import_textures": False,
            "normal_method": "compute_normals",
            "create_physics_asset": False,
        },
        "promotion_gate": "V7 articulated validation, Unreal physics review, and art-director approval",
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("V7_UNREAL_EXPORT", f"objects={len(selected)}", f"modules={len(modules)}", f"fbx={FBX}")


if __name__ == "__main__":
    main()
