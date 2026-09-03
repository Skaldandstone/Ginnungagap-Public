"""Finalize the concept-derived v5 suit with equipment and a deformation rig."""

from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
BLEND_PATH = SUIT_DIR / "PlayerSuit_Production_v5.blend"
PREVIEW_DIR = SUIT_DIR / "Production_v5_Previews"


def select_only(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.hide_set(False)
    obj.hide_viewport = False
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def link_only(obj, coll):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    coll.objects.link(obj)


def duplicate_accessories(production):
    source_names = [
        "Helmet_ClearDome",
        "Helmet_LowerPressureRing",
        "Helmet_UpperIvoryRing",
        "Helmet_LockBand",
        "ToolArm_Rail",
        "ToolArm_ShoulderJoint",
        "ToolArm_Upper_Stowed",
        "ToolArm_ElbowJoint",
        "ToolArm_Lower_Stowed",
        "ToolArm_EndEffectorSocket",
    ]
    created = {}
    for source_name in source_names:
        source = bpy.data.objects.get(source_name)
        if source is None:
            print(f"ACCESSORY_WARNING={source_name} missing")
            continue
        final_name = "SKV5_" + source_name
        existing = bpy.data.objects.get(final_name)
        if existing:
            bpy.data.objects.remove(existing, do_unlink=True)
        obj = source.copy()
        if source.data:
            obj.data = source.data.copy()
        obj.name = final_name
        link_only(obj, production)
        obj.hide_set(False)
        obj.hide_viewport = False
        obj.hide_render = False
        obj["production_accessory"] = True
        created[source_name] = obj
    return created


def make_armature(production):
    old = bpy.data.objects.get("RIG_PlayerSuit_Production_v5")
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    arm_data = bpy.data.armatures.new("RIG_PlayerSuit_Production_v5_Data")
    arm = bpy.data.objects.new("RIG_PlayerSuit_Production_v5", arm_data)
    production.objects.link(arm)
    arm.show_in_front = True
    arm_data.display_type = "OCTAHEDRAL"

    select_only(arm)
    bpy.ops.object.mode_set(mode="EDIT")

    def add(name, head, tail, parent=None, connected=False):
        bone = arm_data.edit_bones.new(name)
        bone.head = head
        bone.tail = tail
        bone.parent = parent
        bone.use_connect = connected and parent is not None
        return bone

    root = add("root", (0, 0, 0.02), (0, 0, 0.14))
    pelvis = add("pelvis", (0, 0, 0.78), (0, 0, 0.93), root)
    spine_01 = add("spine_01", (0, 0, 0.93), (0, 0, 1.08), pelvis, True)
    spine_02 = add("spine_02", (0, 0, 1.08), (0, 0, 1.23), spine_01, True)
    chest = add("chest", (0, 0, 1.23), (0, 0, 1.39), spine_02, True)
    neck = add("neck", (0, 0, 1.39), (0, 0, 1.53), chest, True)
    head = add("head", (0, 0, 1.53), (0, 0, 1.78), neck, True)

    for side, sx in (("l", 1), ("r", -1)):
        clav = add(f"clavicle_{side}", (0.02 * sx, 0, 1.36), (0.245 * sx, 0, 1.37), chest)
        upper = add(f"upperarm_{side}", (0.245 * sx, 0, 1.37), (0.325 * sx, -0.005, 1.12), clav, True)
        lower = add(f"lowerarm_{side}", (0.325 * sx, -0.005, 1.12), (0.36 * sx, -0.02, 0.91), upper, True)
        add(f"hand_{side}", (0.36 * sx, -0.02, 0.91), (0.38 * sx, -0.035, 0.80), lower, True)
        thigh = add(f"thigh_{side}", (0.105 * sx, 0, 0.86), (0.135 * sx, 0, 0.53), pelvis)
        calf = add(f"calf_{side}", (0.135 * sx, 0, 0.53), (0.145 * sx, 0.015, 0.18), thigh, True)
        add(f"foot_{side}", (0.145 * sx, 0.015, 0.18), (0.145 * sx, -0.18, 0.08), calf, True)

    bpy.ops.object.mode_set(mode="OBJECT")
    arm["rig_standard"] = "Ginnungagap humanoid v5"
    arm["bone_count"] = len(arm_data.bones)
    return arm


def bind_mesh(target, arm):
    # Remove stale armature parenting/modifiers before the final heat bind.
    target.parent = None
    for modifier in list(target.modifiers):
        if modifier.type == "ARMATURE":
            target.modifiers.remove(modifier)
    target.vertex_groups.clear()
    bpy.ops.object.select_all(action="DESELECT")
    target.select_set(True)
    arm.select_set(True)
    bpy.context.view_layer.objects.active = arm
    try:
        bpy.ops.object.parent_set(type="ARMATURE_AUTO")
        target["skin_bind"] = "automatic heat weights"
    except Exception as exc:
        target["skin_bind"] = f"failed: {exc}"
        print(f"SKIN_BIND_WARNING={exc}")


def parent_accessories(accessories, arm):
    head_parts = {
        "Helmet_ClearDome",
        "Helmet_LowerPressureRing",
        "Helmet_UpperIvoryRing",
        "Helmet_LockBand",
    }
    for source_name, obj in accessories.items():
        world_matrix = obj.matrix_world.copy()
        obj.parent = arm
        obj.parent_type = "BONE"
        obj.parent_bone = "head" if source_name in head_parts else "chest"
        obj.matrix_world = world_matrix


def validate_weights(target, arm):
    deform_names = {bone.name for bone in arm.data.bones if bone.use_deform}
    deform_indices = {group.index for group in target.vertex_groups if group.name in deform_names}
    weighted = 0
    for vertex in target.data.vertices:
        total = sum(item.weight for item in vertex.groups if item.group in deform_indices)
        if total > 0.001:
            weighted += 1
    coverage = weighted / max(1, len(target.data.vertices))
    target["weight_coverage"] = coverage
    target["rig_bones"] = len(arm.data.bones)
    if coverage < 0.985:
        print(f"WEIGHT_COVERAGE_WARNING={coverage:.4f}")
    print(
        f"RIG_VALIDATION bones={len(arm.data.bones)} "
        f"vertex_groups={len(target.vertex_groups)} coverage={coverage:.4f}"
    )
    return coverage


def render_previews(target, accessories):
    scene = bpy.data.scenes.get("SCENE_HighPolyReview")
    camera = bpy.data.objects.get("CAM_HighPolyReview")
    if scene is None or camera is None:
        print("PREVIEW_WARNING=review scene missing")
        return
    production = target.users_collection[0]
    if production.name not in [child.name for child in scene.collection.children]:
        scene.collection.children.link(production)
    target.hide_render = False
    for obj in accessories.values():
        obj.hide_render = False
    original = bpy.context.window.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    target_point = Vector((0, 0, 0.94))
    for label, position in {
        "Front": Vector((0, -5, 1)),
        "Back": Vector((0, 5, 1)),
        "Side": Vector((5, 0, 1)),
        "ThreeQuarter": Vector((3.6, -3.6, 1.05)),
    }.items():
        camera.location = position
        camera.rotation_euler = (target_point - position).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(PREVIEW_DIR / f"PlayerSuit_Production_v5_{label}.png")
        bpy.context.window.scene = scene
        bpy.ops.render.render(write_still=True)
    bpy.context.window.scene = original


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))
    target = bpy.data.objects.get("SK_PlayerSuit_Production_v5")
    if target is None:
        raise RuntimeError("v5 production mesh missing")
    production = bpy.data.collections.get("SUIT_PRODUCTION_v5")
    if production is None:
        raise RuntimeError("v5 production collection missing")
    accessories = duplicate_accessories(production)
    arm = make_armature(production)
    bind_mesh(target, arm)
    parent_accessories(accessories, arm)
    coverage = validate_weights(target, arm)
    target["asset_status"] = "PRODUCTION_DEFORMATION_REVIEW"
    target["concept_fidelity_source"] = "Player_Concept_Likeness_v2 separated multiview"
    target["unreal_export_allowed"] = coverage >= 0.985
    target["next_gate"] = "art-director close-up approval and animation stress test"
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)
    render_previews(target, accessories)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH), check_existing=False)
    print(f"FINALIZED_V5={BLEND_PATH}")


if __name__ == "__main__":
    main()
