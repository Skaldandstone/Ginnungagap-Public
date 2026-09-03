"""Move the separated V15 character toward the local suiting-up concept art."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerCharacter_Undersuit_v15.blend"
OUTPUT = SUIT_DIR / "PlayerCharacter_Undersuit_Concept_v16.blend"
PREVIEWS = SUIT_DIR / "Production_v16_Previews"
REPORT = SUIT_DIR / "PlayerCharacter_Undersuit_v16_ConceptPass.json"
CONCEPT = "docs/concept-art/reference/suits/player-suiting-up-armory-concept.png"


def masculine_head(face):
    keys = face.data.shape_keys.key_blocks
    # The source demographic keys do not drive the separate hair/eyes. Preserve
    # the validated V15 values until a unified facial rig is authored.
    face["v16_identity_target"] = "validated V15 face retained; concept identity deferred"
    return {key.name: key.value for key in keys if key.value > 0}


def reshape_undersuit(obj):
    inverse = obj.matrix_world.inverted()
    affected = {"shoulders_chest": 0, "waist": 0, "hips": 0}
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        if 1.18 < world.z < 1.50:
            blend = min(1.0, (world.z - 1.18) / .14)
            world.x *= 1.0 + .075 * blend
            world.y *= 1.025
            affected["shoulders_chest"] += 1
        elif .94 < world.z <= 1.18:
            world.x *= .965
            affected["waist"] += 1
        elif .68 < world.z <= .94:
            world.x *= .94
            world.y *= .95
            affected["hips"] += 1
        vertex.co = inverse @ world
    obj["v16_proportion_pass"] = "broader shoulder/chest, narrower waist/hips"
    return affected


def refine_fabric(material):
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (.009, .014, .017, 1)
    bsdf.inputs["Metallic"].default_value = .0
    bsdf.inputs["Roughness"].default_value = .78
    weave = nodes.get("V16_TechnicalWeave") or nodes.new("ShaderNodeTexWave")
    weave.name = "V16_TechnicalWeave"
    weave.wave_type = "BANDS"
    weave.bands_direction = "X"
    weave.inputs["Scale"].default_value = 260
    weave.inputs["Distortion"].default_value = 3.0
    bump = nodes.get("V16_TechnicalBump") or nodes.new("ShaderNodeBump")
    bump.name = "V16_TechnicalBump"
    bump.inputs["Strength"].default_value = .075
    bump.inputs["Distance"].default_value = .0007
    for link in list(bump.inputs["Height"].links):
        links.remove(link)
    links.new(weave.outputs["Color"], bump.inputs["Height"])
    for link in list(bsdf.inputs["Normal"].links):
        links.remove(link)
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    material["v16_concept_finish"] = "dark ribbed technical pressure garment"


def darken_hair():
    hair = bpy.data.objects.get("V6_HEAD_Hair_Short02_CC0")
    if not hair or not hair.data.materials:
        return None
    source = hair.data.materials[0]
    material = source.copy()
    material.name = "M_V16_Hair_ConceptBrown"
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        for link in list(bsdf.inputs["Base Color"].links):
            material.node_tree.links.remove(link)
        bsdf.inputs["Base Color"].default_value = (.035, .020, .012, 1)
        bsdf.inputs["Roughness"].default_value = .48
    hair.data.materials[0] = material
    return material.name


def pose_suiting_up(armature):
    pose = {
        "spine_01": (math.radians(5), 0, 0),
        "spine_02": (math.radians(9), math.radians(-2), math.radians(2)),
        "neck": (math.radians(11), 0, 0),
        "head": (math.radians(18), math.radians(-7), math.radians(3)),
        "upperarm_l": (math.radians(-4), math.radians(-8), math.radians(8)),
        "lowerarm_l": (math.radians(2), math.radians(-3), math.radians(-12)),
        "hand_l": (math.radians(-8), math.radians(4), math.radians(-8)),
        "upperarm_r": (math.radians(4), math.radians(8), math.radians(-8)),
        "lowerarm_r": (math.radians(-2), math.radians(3), math.radians(12)),
        "hand_r": (math.radians(7), math.radians(-4), math.radians(7)),
        "thigh_l": (math.radians(10), math.radians(-3), math.radians(2)),
        "calf_l": (math.radians(-16), 0, 0),
    }
    for name, rotation in pose.items():
        bone = armature.pose.bones.get(name)
        if bone:
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = rotation
    bpy.context.view_layer.update()
    return sorted(pose)


def render(scene, camera, label, position, target, resolution=(900, 1100), lens=68):
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x, scene.render.resolution_y = resolution
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.camera = camera
    camera.location = position
    camera.data.lens = lens
    camera.rotation_euler = (target - position).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(PREVIEWS / f"PlayerCharacter_Undersuit_v16_{label}.png")
    bpy.ops.render.render(write_still=True)


def clear_pose(armature):
    bpy.context.view_layer.objects.active = armature
    armature.hide_set(False); armature.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode="OBJECT")


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    armature = bpy.data.objects["RIG_PlayerCharacter_Undersuit_v15"]
    armature.name = "RIG_PlayerCharacter_Undersuit_v16"
    undersuit = bpy.data.objects["SK_PlayerCharacter_Undersuit_v15"]
    undersuit.name = "SK_PlayerCharacter_Undersuit_v16"
    face = bpy.data.objects["SK_PlayerHead_Production_v6"]
    head_weights = masculine_head(face)
    proportions = reshape_undersuit(undersuit)
    refine_fabric(undersuit.data.materials[0])
    hair_material = darken_hair()
    undersuit["asset_status"] = "CHARACTER_UNDERSUIT_V16_CONCEPT_REVIEW"
    undersuit["concept_reference"] = CONCEPT
    undersuit["contains_oversuit"] = False

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    original = bpy.context.window.scene
    bpy.context.window.scene = scene
    render(scene, camera, "Front", Vector((0, -4.4, 1.02)), Vector((0, 0, .98)))
    render(scene, camera, "Profile", Vector((4.4, 0, 1.02)), Vector((0, 0, .98)))
    pose_bones = pose_suiting_up(armature)
    render(scene, camera, "SuitingUpPose", Vector((2.7, -3.3, 1.18)), Vector((0, 0, 1.05)),
           resolution=(1100, 1000), lens=72)
    render(scene, camera, "SuitingUpPortrait", Vector((1.6, -2.2, 1.48)), Vector((0, 0, 1.40)),
           resolution=(1000, 1000), lens=82)
    clear_pose(armature)
    bpy.context.window.scene = original
    REPORT.write_text(json.dumps({
        "schema": 1, "asset": "PlayerCharacter_Undersuit_v16", "status": "concept_review",
        "concept_reference": CONCEPT, "contains_oversuit": False,
        "head_shape_weights": head_weights, "proportion_vertex_counts": proportions,
        "hair_material": hair_material, "suiting_pose_bones": pose_bones,
    }, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V16_SUITING_CONCEPT", f"head_keys={head_weights}", f"proportions={proportions}",
          f"output={OUTPUT}")


if __name__ == "__main__":
    main()
