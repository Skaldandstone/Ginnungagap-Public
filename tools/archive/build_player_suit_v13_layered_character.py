"""Build V13 as explicit character, undersuit, and oversuit layers."""

from __future__ import annotations

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerSuit_Production_v12.blend"
OUTPUT = SUIT_DIR / "PlayerSuit_Production_v13.blend"
PREVIEWS = SUIT_DIR / "Production_v13_Previews"
REPORT = SUIT_DIR / "PlayerSuit_Production_v13_Layers.json"
HEAD_REARWARD_OFFSET = .040


def undersuit_material():
    material = bpy.data.materials.get("M_V13_UndersuitFabric") or bpy.data.materials.new("M_V13_UndersuitFabric")
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (.018, .026, .031, 1)
    bsdf.inputs["Metallic"].default_value = .01
    bsdf.inputs["Roughness"].default_value = .72
    weave = nodes.get("V13_UndersuitWeave") or nodes.new("ShaderNodeTexNoise")
    weave.name = "V13_UndersuitWeave"
    weave.inputs["Scale"].default_value = 210
    weave.inputs["Detail"].default_value = 2.4
    bump = nodes.get("V13_UndersuitBump") or nodes.new("ShaderNodeBump")
    bump.name = "V13_UndersuitBump"
    bump.inputs["Strength"].default_value = .11
    bump.inputs["Distance"].default_value = .001
    if not bump.inputs["Height"].is_linked:
        links.new(weave.outputs["Fac"], bump.inputs["Height"])
    if not bsdf.inputs["Normal"].is_linked:
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    material["character_layer"] = "undersuit"
    return material


def link_unique(collection, objects):
    for obj in objects:
        if collection.objects.get(obj.name) is None:
            collection.objects.link(obj)


def point_camera(camera, position, target):
    camera.location = position
    camera.data.lens = 62
    camera.rotation_euler = (target - position).to_track_quat("-Z", "Y").to_euler()


def render_layers(scene, camera, character, undersuit, oversuit):
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.camera = camera
    target = Vector((0, 0, .98))
    all_visible = [*character, *undersuit, *oversuit]
    for obj in all_visible:
        obj.hide_render = False
    for label, position in {
        "Front": Vector((0, -4.4, 1.02)),
        "Profile": Vector((4.4, 0, 1.02)),
        "ThreeQuarter": Vector((3.1, -3.1, 1.06)),
        "Back": Vector((0, 4.4, 1.02)),
    }.items():
        point_camera(camera, position, target)
        scene.render.filepath = str(PREVIEWS / f"PlayerSuit_Production_v13_{label}.png")
        bpy.ops.render.render(write_still=True)

    # Layer audit: wearer/head + undersuit, with the entire oversuit hidden.
    for obj in oversuit:
        obj.hide_render = True
    point_camera(camera, Vector((3.1, -3.1, 1.06)), target)
    scene.render.filepath = str(PREVIEWS / "PlayerSuit_Production_v13_UndersuitOnly.png")
    bpy.ops.render.render(write_still=True)
    for obj in oversuit:
        obj.hide_render = False

    # Oversuit audit without the garment surface; retain head for scale.
    for obj in undersuit:
        obj.hide_render = True
    scene.render.filepath = str(PREVIEWS / "PlayerSuit_Production_v13_OversuitOnly.png")
    bpy.ops.render.render(write_still=True)
    for obj in undersuit:
        obj.hide_render = False


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    armature = bpy.data.objects["RIG_PlayerSuit_Production_v12"]
    armature.name = "RIG_PlayerSuit_Production_v13"
    base = bpy.data.objects["SK_PlayerSuit_Production_v12_BaseGarment"]
    base.name = "SK_PlayerSuit_Production_v13_Undersuit"
    base.data.materials.clear()
    base.data.materials.append(undersuit_material())
    base["character_layer"] = "undersuit"
    base["export_group"] = "SKM_PlayerCharacter_Undersuit"

    head_root = bpy.data.objects.get("SK_PlayerHead_Production_v6")
    if head_root is None:
        raise RuntimeError("V13 requires the V6 production head root")
    before = head_root.matrix_world.translation.copy()
    world = head_root.matrix_world.copy()
    world.translation.y += HEAD_REARWARD_OFFSET
    head_root.matrix_world = world
    bpy.context.view_layer.update()
    after = head_root.matrix_world.translation.copy()

    character_objects = [armature]
    for obj in bpy.data.objects:
        if obj.get("production_head_component"):
            obj["character_layer"] = "character"
            obj["export_group"] = "SKM_PlayerCharacter_Body"
            character_objects.append(obj)

    oversuit_objects = []
    conformal = bpy.data.collections.get("SUIT_PRODUCTION_v11_CONFORMAL_ARMOR")
    if conformal:
        oversuit_objects.extend(obj for obj in conformal.objects if obj.get("v11_conformal_shell"))
    finish = bpy.data.collections.get("SUIT_PRODUCTION_v12_PANEL_FINISH")
    if finish:
        oversuit_objects.extend(obj for obj in finish.objects
                                if not obj.get("v12_review_status") and not obj.hide_render)
    oversuit_objects.extend(obj for obj in bpy.data.objects if obj.name.startswith("SKV6_Helmet_"))
    oversuit_objects = list(dict.fromkeys(oversuit_objects))
    for obj in oversuit_objects:
        obj["character_layer"] = "oversuit"
        obj["export_group"] = "SKM_PlayerOversuit_Modular"

    character_collection = bpy.data.collections.new("CHARACTER_V13_BODY")
    undersuit_collection = bpy.data.collections.new("CHARACTER_V13_UNDERSUIT")
    oversuit_collection = bpy.data.collections.new("CHARACTER_V13_OVERSUIT")
    bpy.context.scene.collection.children.link(character_collection)
    bpy.context.scene.collection.children.link(undersuit_collection)
    bpy.context.scene.collection.children.link(oversuit_collection)
    link_unique(character_collection, character_objects)
    link_unique(undersuit_collection, [base])
    link_unique(oversuit_collection, oversuit_objects)

    base["asset_status"] = "ART_DIRECTION_REVIEW_V13_LAYERED_CHARACTER"
    base["runtime_replacement"] = False
    base["head_rearward_offset_m"] = HEAD_REARWARD_OFFSET
    REPORT.write_text(json.dumps({
        "schema": 1, "asset": "PlayerSuit_Production_v13", "status": "layered_character_review",
        "head_translation_before": list(before), "head_translation_after": list(after),
        "head_rearward_offset_m": HEAD_REARWARD_OFFSET,
        "layers": {
            "character": [obj.name for obj in character_objects],
            "undersuit": [base.name],
            "oversuit": [obj.name for obj in oversuit_objects],
        },
    }, indent=2), encoding="utf-8")
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    original = bpy.context.window.scene
    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    bpy.context.window.scene = scene
    render_layers(scene, bpy.data.objects["CAM_HighPolyReview"], character_objects, [base], oversuit_objects)
    bpy.context.window.scene = original
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V13_LAYERED_CHARACTER", f"head_offset={HEAD_REARWARD_OFFSET}",
          f"character={len(character_objects)}", f"undersuit=1", f"oversuit={len(oversuit_objects)}")


if __name__ == "__main__":
    main()
