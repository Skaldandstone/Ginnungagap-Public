"""Grounded macro-form correction built from V8 after rejecting the bulky V9 study."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerSuit_Production_v8.blend"
OUTPUT = SUIT_DIR / "PlayerSuit_Production_v10.blend"
PREVIEWS = SUIT_DIR / "Production_v10_Previews"
REPORT = SUIT_DIR / "PlayerSuit_Production_v10_GroundedCorrection.json"


def make_material(name, color, metallic, roughness):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def plate(name, location, scale, collection, material, bone, rotation=(0, 0, 0), bevel=.006):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    obj.data.materials.append(material)
    modifier = obj.modifiers.new("V10_SubtleEdge", "BEVEL")
    modifier.width = bevel
    modifier.segments = 3
    armature = bpy.data.objects["RIG_PlayerSuit_Production_v10"]
    world = obj.matrix_world.copy()
    obj.parent = armature
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = world
    obj["rig_attachment"] = bone
    obj["v10_grounded_form"] = True
    return obj


def render(scene, camera, visible):
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.camera = camera
    for obj in visible:
        obj.hide_render = False
    target = Vector((0, 0, .98))
    for label, position in {
        "Front": Vector((0, -4.4, 1.02)), "Back": Vector((0, 4.4, 1.02)),
        "Side": Vector((4.4, 0, 1.02)), "ThreeQuarter": Vector((3.1, -3.1, 1.06)),
    }.items():
        camera.location = position
        camera.data.lens = 60
        camera.rotation_euler = (target - position).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(PREVIEWS / f"PlayerSuit_Production_v10_{label}.png")
        bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    armature = bpy.data.objects["RIG_PlayerSuit_Production_v8"]
    armature.name = "RIG_PlayerSuit_Production_v10"
    base = bpy.data.objects["SK_PlayerSuit_Production_v8_BaseGarment"]
    base.name = "SK_PlayerSuit_Production_v10_BaseGarment"
    collection = bpy.data.collections.new("SUIT_PRODUCTION_v10_GROUNDED_FORM")
    bpy.context.scene.collection.children.link(collection)
    armor = make_material("M_V10_MutedArmor", (.25, .29, .30), .36, .34)
    dark = make_material("M_V10_DarkArmor", (.025, .037, .044), .50, .31)
    accent = make_material("M_V10_RestrainedAccent", (.47, .075, .012), .20, .35)
    created, passes = [], []

    def add_pass(label, objects):
        objects = objects if isinstance(objects, list) else [objects]
        created.extend(objects)
        passes.append({"pass": len(passes) + 1, "label": label,
                       "objects": [obj.name for obj in objects]})

    # Compact only the visibly oversized legacy helmet pieces.
    changed = []
    for name, factor in {
        "SKV6_Helmet_ClearDome": (.84, .84, .90),
        "SKV6_Helmet_LowerPressureRing": (.80, .80, .72),
        "SKV6_Helmet_UpperIvoryRing": (.80, .80, .72),
        "SKV6_Helmet_LockBand": (.82, .82, .78),
        "SKV6_Helmet_InnerNeckGasket": (.86, .86, .84),
    }.items():
        obj = bpy.data.objects.get(name)
        if obj:
            obj.scale = tuple(obj.scale[i] * factor[i] for i in range(3))
            obj["v10_grounded_form"] = "compacted"
            changed.append(obj)
    add_pass("Compact helmet without changing head scale", changed)

    add_pass("Close-fitting split chest planes", [
        plate(f"SKV10_Chest_{side}", (x, -.190, 1.285), (.092, .016, .095), collection,
              armor, "chest", rotation=(0, 0, math.radians(angle)), bevel=.010)
        for side, x, angle in (("L", -.075, -4), ("R", .075, 4))
    ])
    add_pass("Narrow sternum datum", plate("SKV10_SternumDatum", (0, -.213, 1.285),
                                           (.015, .010, .105), collection, dark, "chest", bevel=.003))
    add_pass("Low-profile abdomen lames", [
        plate(f"SKV10_Abdomen_{i}", (0, -.184, 1.135-i*.047),
              (.090-i*.005, .010, .014), collection, dark if i % 2 else armor,
              "spine_02", bevel=.004) for i in range(4)
    ])
    add_pass("Trim shoulder caps", [
        plate(f"SKV10_Shoulder_{side}", (x, -.042, 1.340), (.082, .030, .065), collection,
              armor, f"upperarm_{side.lower()}", rotation=(0, math.radians(side == "L" and -8 or 8), 0), bevel=.014)
        for side, x in (("L", -.225), ("R", .225))
    ])
    add_pass("Fitted forearm rails", [
        plate(f"SKV10_Forearm_{side}", (x, -.080, 1.055), (.045, .022, .105), collection,
              dark, f"lowerarm_{side.lower()}", bevel=.009) for side, x in (("L", -.340), ("R", .340))
    ])
    add_pass("Integrated belt language", [
        plate(f"SKV10_Belt_{i}", ((i-2)*.050, -.164, .895), (.019, .012, .025), collection,
              accent if i in (0, 4) else dark, "pelvis", bevel=.004) for i in range(5)
    ])
    add_pass("Thigh seam rails instead of shells", [
        plate(f"SKV10_ThighRail_{side}", (x, -.094, .710), (.025, .014, .135), collection,
              dark, f"thigh_{side.lower()}", bevel=.006) for side, x in (("L", -.145), ("R", .145))
    ])
    add_pass("Close knee and shin plates", [
        plate(f"SKV10_Knee_{side}", (x, -.127, .525), (.058, .018, .048), collection,
              armor, f"calf_{side.lower()}", bevel=.012) for side, x in (("L", -.128), ("R", .128))
    ] + [
        plate(f"SKV10_Shin_{side}", (x, -.096, .360), (.050, .014, .105), collection,
              armor, f"calf_{side.lower()}", bevel=.010) for side, x in (("L", -.128), ("R", .128))
    ])
    add_pass("Subtle boot toe protection", [
        plate(f"SKV10_Toe_{side}", (x, -.170, .095), (.070, .026, .025), collection,
              dark, f"foot_{side.lower()}", bevel=.012) for side, x in (("L", -.128), ("R", .128))
    ])

    if len(passes) != 10:
        raise RuntimeError(f"Expected ten grounded-form passes, found {len(passes)}")
    base["asset_status"] = "ART_DIRECTION_REVIEW_V10_GROUNDED_FORM"
    base["runtime_replacement"] = False
    base["rejected_direction"] = "V9 bulky floating armor study"
    REPORT.write_text(json.dumps({"schema": 1, "asset": "PlayerSuit_Production_v10",
                                  "status": "grounded_macro_form_review", "passes": passes,
                                  "new_object_count": len(created)}, indent=2), encoding="utf-8")
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    original = bpy.context.window.scene
    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    bpy.context.window.scene = scene
    render(scene, bpy.data.objects["CAM_HighPolyReview"], [base, *created])
    bpy.context.window.scene = original
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V10_GROUNDED_FORM", f"passes={len(passes)}", f"objects={len(created)}", f"output={OUTPUT}")


if __name__ == "__main__":
    main()
