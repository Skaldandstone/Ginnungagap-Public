"""Turn the hard V21 compression bands into subtle woven density changes."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v29.blend"
OUTPUT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v30.blend"
PREVIEWS = SUIT_DIR / "Production_v30_Previews"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v30_CompressionWeavePass.json"


def build_adjacency(mesh: bpy.types.Mesh) -> list[list[int]]:
    adjacency = [[] for _ in mesh.vertices]
    for edge in mesh.edges:
        first, second = edge.vertices
        adjacency[first].append(second)
        adjacency[second].append(first)
    return adjacency


def soften_compression_mask(body: bpy.types.Object) -> dict[str, float | int]:
    source = body.data.color_attributes["V21_CompressionMask"]
    values = [float(item.color[0]) for item in source.data]
    original_mean = sum(values) / len(values)
    original_max = max(values)
    original_strong = sum(value > 0.5 for value in values)
    adjacency = build_adjacency(body.data)
    for _ in range(4):
        next_values = []
        for index, value in enumerate(values):
            neighbors = adjacency[index]
            average = sum(values[neighbor] for neighbor in neighbors) / len(neighbors) if neighbors else value
            next_values.append(0.64 * value + 0.36 * average)
        values = next_values
    gated_values = []
    for vertex, value in zip(body.data.vertices, values):
        point = body.matrix_world @ vertex.co
        elbow_zone = abs(point.x) > 0.205 and 0.98 < point.z < 1.23
        knee_zone = abs(point.x) > 0.055 and 0.43 < point.z < 0.72
        joint = value * 0.55 if elbow_zone or knee_zone else 0.0
        waist = math.exp(-((point.z - 1.02) / 0.082) ** 2) * 0.16
        gated_values.append(min(0.48, max(joint, waist)))
    values = gated_values
    attribute = body.data.color_attributes.get("V30_CompressionWeaveMask")
    if attribute:
        body.data.color_attributes.remove(attribute)
    attribute = body.data.color_attributes.new(
        name="V30_CompressionWeaveMask", type="FLOAT_COLOR", domain="POINT"
    )
    for index, value in enumerate(values):
        attribute.data[index].color = (value, value, value, 1.0)
    body["v30_compression_finish"] = "four-ring vertex blur, capped intensity, procedural weave modulation"
    return {
        "original_mean": original_mean,
        "original_max": original_max,
        "original_vertices_above_half": original_strong,
        "new_mean": sum(values) / len(values),
        "new_max": max(values),
        "new_vertices_above_half": sum(value > 0.5 for value in values),
    }


def build_weave_shader(body: bpy.types.Object) -> dict[str, list[float] | float]:
    material = body.data.materials[0]
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    color_mask = nodes["V21_CompressionMask"]
    color_mask.layer_name = "V30_CompressionWeaveMask"
    color_mask.name = "V30_CompressionWeaveMask"
    mix = nodes["V21_CompressionDyeMix"]
    previous_dye = list(mix.inputs[2].default_value)
    mix.inputs[2].default_value = (0.082, 0.103, 0.108, 1.0)
    dye_noise = nodes["V18_DyeVariation"]
    previous_dye_scale = float(dye_noise.inputs["Scale"].default_value)
    dye_noise.inputs["Scale"].default_value = 28.0
    dye_noise.inputs["Detail"].default_value = 2.0
    dye_noise.inputs["Roughness"].default_value = 0.45
    dye_noise.inputs["Distortion"].default_value = 0.05
    dye_palette = nodes["V18_DyePalette"].color_ramp
    dye_palette.elements[0].color = (0.125, 0.152, 0.158, 1.0)
    dye_palette.elements[-1].color = (0.178, 0.205, 0.210, 1.0)

    noise = nodes.get("V30_CompressionMicroWeave") or nodes.new("ShaderNodeTexNoise")
    noise.name = "V30_CompressionMicroWeave"
    noise.label = "Compression micro-weave"
    noise.noise_dimensions = "3D"
    noise.inputs["Scale"].default_value = 185.0
    noise.inputs["Detail"].default_value = 2.0
    noise.inputs["Roughness"].default_value = 0.34
    noise.location = (-230, 420)
    scale = nodes.get("V30_WeaveAmplitude") or nodes.new("ShaderNodeMath")
    scale.name = "V30_WeaveAmplitude"
    scale.operation = "MULTIPLY"
    scale.inputs[1].default_value = 0.28
    scale.location = (-20, 420)
    bias = nodes.get("V30_WeaveBias") or nodes.new("ShaderNodeMath")
    bias.name = "V30_WeaveBias"
    bias.operation = "ADD"
    bias.inputs[1].default_value = 0.72
    bias.location = (150, 420)
    modulate = nodes.get("V30_CompressionModulate") or nodes.new("ShaderNodeMath")
    modulate.name = "V30_CompressionModulate"
    modulate.operation = "MULTIPLY"
    modulate.location = (330, 350)
    for socket in (scale.inputs[0], bias.inputs[0], modulate.inputs[0], modulate.inputs[1], mix.inputs[0]):
        for link in list(socket.links):
            links.remove(link)
    links.new(noise.outputs["Fac"], scale.inputs[0])
    links.new(scale.outputs[0], bias.inputs[0])
    links.new(color_mask.outputs["Color"], modulate.inputs[0])
    links.new(bias.outputs[0], modulate.inputs[1])
    links.new(modulate.outputs[0], mix.inputs[0])
    material["v30_compression_finish"] = "soft rig-driven density zones with fine procedural weave"
    return {
        "previous_compression_dye": previous_dye,
        "new_compression_dye": list(mix.inputs[2].default_value),
        "weave_scale": float(noise.inputs["Scale"].default_value),
        "weave_amplitude": float(scale.inputs[1].default_value),
        "previous_dye_noise_scale": previous_dye_scale,
        "new_dye_noise_scale": float(dye_noise.inputs["Scale"].default_value),
    }


def pose_cryo_wake(armature: bpy.types.Object) -> None:
    rotations = {
        "spine_01": (7, 0, 0), "spine_02": (10, -2, 2),
        "neck": (9, 0, 0), "head": (18, -7, 3),
        "upperarm_l": (-7, -10, 10), "lowerarm_l": (4, -4, -15),
        "upperarm_r": (7, 10, -10), "lowerarm_r": (-4, 4, 15),
    }
    for name, degrees in rotations.items():
        bone = armature.pose.bones.get(name)
        if bone:
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = tuple(math.radians(value) for value in degrees)
    bpy.context.view_layer.update()


def clear_pose(armature: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = armature
    armature.hide_set(False)
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode="OBJECT")


def render(scene, camera, label, position, target, resolution=(1000, 1000), lens=84) -> None:
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
    scene.render.filepath = str(PREVIEWS / f"PlayerCharacter_CryoBodysuit_v30_{label}.png")
    bpy.ops.render.render(write_still=True)


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects["RIG_PlayerCharacter_CryoBodysuit_v29"]
    rig.name = "RIG_PlayerCharacter_CryoBodysuit_v30"
    body = bpy.data.objects["SK_PlayerCharacter_CryoBodysuit_v29"]
    body.name = "SK_PlayerCharacter_CryoBodysuit_v30"
    seal = bpy.data.objects["SK_PlayerCharacter_CryoNeckSeal_v29"]
    seal.name = "SK_PlayerCharacter_CryoNeckSeal_v30"
    for old, new in (
        ("SK_CryoSeam_CenterFront_v29", "SK_CryoSeam_CenterFront_v30"),
        ("SK_CryoSeam_LeftLeg_v29", "SK_CryoSeam_LeftLeg_v30"),
        ("SK_CryoSeam_RightLeg_v29", "SK_CryoSeam_RightLeg_v30"),
    ):
        bpy.data.objects[old].name = new

    mask_stats = soften_compression_mask(body)
    shader_stats = build_weave_shader(body)
    body["asset_status"] = "CHARACTER_CRYO_BODYSUIT_V30_COMPRESSION_WEAVE_REVIEW"
    body["contains_oversuit"] = False

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    render(scene, camera, "Front", Vector((0, -4.10, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 82)
    render(scene, camera, "Profile", Vector((4.10, 0, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 82)
    render(scene, camera, "CompressionDetail", Vector((0.95, -2.10, 1.05)), Vector((0.18, -0.01, 1.00)), (1100, 1000), 105)
    pose_cryo_wake(rig)
    render(scene, camera, "CryoWakePose", Vector((2.75, -3.35, 1.16)), Vector((0, 0, 1.04)), (1100, 1000), 82)
    clear_pose(rig)
    bpy.context.window.scene = original_scene

    result = {
        "schema": 1,
        "asset": "PlayerCharacter_CryoBodysuit_Concept_v30",
        "status": "compression_weave_review",
        "contains_oversuit": False,
        "mask": mask_stats,
        "shader": shader_stats,
    }
    REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V30_COMPRESSION_WEAVE", json.dumps(result, separators=(",", ":")))


if __name__ == "__main__":
    main()
