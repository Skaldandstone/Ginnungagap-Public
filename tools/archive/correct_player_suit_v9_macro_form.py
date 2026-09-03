"""Correct V8 macro form after visual review and render a V9 comparison set."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerSuit_Production_v8.blend"
OUTPUT = SUIT_DIR / "PlayerSuit_Production_v9.blend"
PREVIEWS = SUIT_DIR / "Production_v9_Previews"
REPORT = SUIT_DIR / "PlayerSuit_Production_v9_MacroCorrection.json"


def material(name, color, metallic, roughness):
    value = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    value.use_nodes = True
    bsdf = value.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return value


def attach(obj, collection, mat, bone, bevel=.008):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    if bevel:
        modifier = obj.modifiers.new("V9_ControlledEdge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 4
    armature = bpy.data.objects["RIG_PlayerSuit_Production_v9"]
    world = obj.matrix_world.copy()
    obj.parent = armature
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = world
    obj["rig_attachment"] = bone
    obj["v9_macro_correction"] = True
    return obj


def box(name, location, scale, collection, mat, bone, rotation=(0, 0, 0), bevel=.008):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return attach(obj, collection, mat, bone, bevel)


def shell(name, location, scale, collection, mat, bone, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return attach(obj, collection, mat, bone, .004)


def ring(name, location, radius, depth, collection, mat, bone):
    bpy.ops.mesh.primitive_torus_add(major_radius=radius, minor_radius=depth,
                                    major_segments=64, minor_segments=12, location=location)
    obj = bpy.context.object
    obj.name = name
    return attach(obj, collection, mat, bone, .002)


def render_reviews(scene, camera, objects):
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.camera = camera
    for obj in objects:
        obj.hide_render = False
    target = Vector((0, 0, 1.0))
    for label, position in {
        "Front": Vector((0, -4.25, 1.02)),
        "Back": Vector((0, 4.25, 1.02)),
        "Side": Vector((4.25, 0, 1.02)),
        "ThreeQuarter": Vector((3.0, -3.0, 1.08)),
    }.items():
        camera.location = position
        camera.data.lens = 62
        camera.rotation_euler = (target - position).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(PREVIEWS / f"PlayerSuit_Production_v9_{label}.png")
        bpy.ops.render.render(write_still=True)


def main():
    if not SOURCE.exists():
        raise RuntimeError(f"V8 source is missing: {SOURCE}")
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    armature = bpy.data.objects["RIG_PlayerSuit_Production_v8"]
    armature.name = "RIG_PlayerSuit_Production_v9"
    base = bpy.data.objects["SK_PlayerSuit_Production_v8_BaseGarment"]
    base.name = "SK_PlayerSuit_Production_v9_BaseGarment"
    collection = bpy.data.collections.new("SUIT_PRODUCTION_v9_MACRO_CORRECTION")
    bpy.context.scene.collection.children.link(collection)

    ivory = material("M_V9_ArmorIvory", (.62, .66, .64), .18, .24)
    dark = material("M_V9_ArmorDark", (.025, .034, .040), .55, .30)
    orange = material("M_V9_ArmorOrange", (.82, .12, .015), .22, .28)
    rubber = material("M_V9_Seal", (.006, .009, .011), .0, .80)
    created = []
    passes = []

    def record(label, operation):
        result = operation()
        result = result if isinstance(result, list) else ([result] if result else [])
        created.extend(result)
        passes.append({"pass": len(passes) + 1, "label": label, "objects": [obj.name for obj in result]})

    def compact_legacy_helmet():
        changed = []
        for name, scale in {
            "SKV6_Helmet_ClearDome": (.82, .82, .88),
            "SKV6_Helmet_LowerPressureRing": (.78, .78, .70),
            "SKV6_Helmet_UpperIvoryRing": (.78, .78, .70),
            "SKV6_Helmet_LockBand": (.80, .80, .76),
            "SKV6_Helmet_InnerNeckGasket": (.84, .84, .82),
        }.items():
            obj = bpy.data.objects.get(name)
            if obj:
                obj.scale = tuple(obj.scale[index] * scale[index] for index in range(3))
                obj["v9_macro_correction"] = "compact helmet/collar"
                changed.append(obj)
        return changed
    record("Compact helmet and collar envelope", compact_legacy_helmet)

    record("Raised split pectoral shells", lambda: [
        shell(f"SKV9_Pectoral_{side}", (x, -.225, 1.285), (.125, .040, .112), collection,
              ivory, "chest", rotation=(0, 0, math.radians(angle)))
        for side, x, angle in (("L", -.092, -5), ("R", .092, 5))
    ])
    record("Deep central sternum channel", lambda: box("SKV9_SternumChannel", (0, -.271, 1.285),
                                                        (.026, .018, .120), collection, dark, "chest", bevel=.005))
    record("Readable abdominal armor stack", lambda: [
        box(f"SKV9_AbdominalPlate_{index}", (0, -.220, 1.120-index*.052),
            (.105-index*.006, .026, .019), collection, ivory if index % 2 == 0 else dark,
            "spine_02", bevel=.007) for index in range(4)
    ])
    record("Broadened shoulder silhouette", lambda: [
        shell(f"SKV9_ShoulderCap_{side}", (x, -.035, 1.340), (.120, .085, .105), collection,
              ivory, f"upperarm_{side.lower()}") for side, x in (("L", -.235), ("R", .235))
    ])
    record("Separated upper-arm armor", lambda: [
        shell(f"SKV9_UpperArmShell_{side}", (x, -.048, 1.235), (.075, .060, .105), collection,
              dark, f"upperarm_{side.lower()}") for side, x in (("L", -.285), ("R", .285))
    ])
    record("Pronounced forearm bracers", lambda: [
        box(f"SKV9_ForearmBracer_{side}", (x, -.095, 1.055), (.065, .050, .130), collection,
            ivory, f"lowerarm_{side.lower()}", bevel=.014) for side, x in (("L", -.345), ("R", .345))
    ])
    record("Mechanical waist transition", lambda: [
        box(f"SKV9_WaistBlock_{index}", ((index-2)*.060, -.183, .900), (.025, .022, .040),
            collection, dark if index % 2 else orange, "pelvis", bevel=.005) for index in range(5)
    ])
    record("Separated thigh armor planes", lambda: [
        shell(f"SKV9_ThighShell_{side}", (x, -.100, .720), (.090, .050, .170), collection,
              dark, f"thigh_{side.lower()}") for side, x in (("L", -.140), ("R", .140))
    ])
    record("Framed knee and shin hierarchy", lambda: [
        shell(f"SKV9_Knee_{side}", (x, -.145, .525), (.080, .040, .075), collection,
              ivory, f"calf_{side.lower()}") for side, x in (("L", -.128), ("R", .128))
    ] + [
        box(f"SKV9_ShinPlate_{side}", (x, -.112, .355), (.067, .032, .125), collection,
            ivory, f"calf_{side.lower()}", bevel=.012) for side, x in (("L", -.128), ("R", .128))
    ])
    record("Compact armored boot volumes", lambda: [
        box(f"SKV9_BootShell_{side}", (x, -.090, .105), (.088, .132, .058), collection,
            dark, f"foot_{side.lower()}", bevel=.018) for side, x in (("L", -.128), ("R", .128))
    ])
    record("New fitted helmet interface", lambda: [
        ring("SKV9_HelmetPressureSeal", (0, .002, 1.520), .122, .010, collection, rubber, "chest"),
        box("SKV9_HelmetLatchFront", (0, -.142, 1.510), (.045, .016, .016), collection, orange, "chest", bevel=.004),
    ])

    if len(passes) != 12:
        raise RuntimeError(f"Expected 12 macro-correction passes, found {len(passes)}")
    base["asset_status"] = "ART_DIRECTION_REVIEW_V9_MACRO_CORRECTED"
    base["runtime_replacement"] = False
    base["v9_macro_pass_count"] = len(passes)
    REPORT.write_text(json.dumps({"schema": 1, "asset": "PlayerSuit_Production_v9",
                                  "status": "macro_form_review", "passes": passes,
                                  "new_object_count": len(created)}, indent=2), encoding="utf-8")
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    original = bpy.context.window.scene
    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    bpy.context.window.scene = scene
    render_reviews(scene, bpy.data.objects["CAM_HighPolyReview"], [base, *created])
    bpy.context.window.scene = original
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V9_MACRO_CORRECTION", f"passes={len(passes)}", f"objects={len(created)}", f"output={OUTPUT}")


if __name__ == "__main__":
    main()
