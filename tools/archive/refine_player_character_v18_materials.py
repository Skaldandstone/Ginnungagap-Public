"""Add production-oriented procedural textile materials to the V17 undersuit."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerCharacter_Undersuit_Concept_v17.blend"
OUTPUT = SUIT_DIR / "PlayerCharacter_Undersuit_Concept_v18.blend"
PREVIEWS = SUIT_DIR / "Production_v18_Previews"
REPORT = SUIT_DIR / "PlayerCharacter_Undersuit_v18_MaterialPass.json"


def set_input(node, name: str, value) -> None:
    socket = node.inputs.get(name)
    if socket is not None:
        socket.default_value = value


def textile_material(
    name: str,
    dark: tuple[float, float, float, float],
    light: tuple[float, float, float, float],
    roughness: tuple[float, float],
    weave_scale: float,
    bump_strength: float,
) -> bpy.types.Material:
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    tree = material.node_tree
    tree.nodes.clear()
    nodes, links = tree.nodes, tree.links

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (720, 0)
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (450, 0)
    set_input(bsdf, "Metallic", 0.0)
    set_input(bsdf, "IOR", 1.46)
    set_input(bsdf, "Sheen Weight", 0.12)

    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.location = (-900, 20)
    macro = nodes.new("ShaderNodeTexNoise")
    macro.name = "V18_DyeVariation"
    macro.location = (-680, 190)
    macro.noise_dimensions = "3D"
    macro.inputs["Scale"].default_value = 5.2
    macro.inputs["Detail"].default_value = 3.2
    macro.inputs["Roughness"].default_value = 0.68
    macro.inputs["Distortion"].default_value = 0.18

    dye = nodes.new("ShaderNodeValToRGB")
    dye.name = "V18_DyePalette"
    dye.location = (-420, 220)
    dye.color_ramp.elements[0].position = 0.22
    dye.color_ramp.elements[0].color = dark
    dye.color_ramp.elements[1].position = 0.78
    dye.color_ramp.elements[1].color = light

    rough = nodes.new("ShaderNodeValToRGB")
    rough.name = "V18_RoughnessBreakup"
    rough.location = (-160, -150)
    rough.color_ramp.elements[0].color = (roughness[0],) * 3 + (1,)
    rough.color_ramp.elements[1].color = (roughness[1],) * 3 + (1,)

    wave_x = nodes.new("ShaderNodeTexWave")
    wave_x.name = "V18_WarpThreads"
    wave_x.location = (-670, -170)
    wave_x.wave_type = "BANDS"
    wave_x.bands_direction = "X"
    wave_x.inputs["Scale"].default_value = weave_scale
    wave_x.inputs["Distortion"].default_value = 2.2
    wave_x.inputs["Detail"].default_value = 2.0
    wave_y = nodes.new("ShaderNodeTexWave")
    wave_y.name = "V18_WeftThreads"
    wave_y.location = (-670, -390)
    wave_y.wave_type = "BANDS"
    wave_y.bands_direction = "Y"
    wave_y.inputs["Scale"].default_value = weave_scale * 0.92
    wave_y.inputs["Distortion"].default_value = 1.7
    wave_y.inputs["Detail"].default_value = 2.0
    weave = nodes.new("ShaderNodeMixRGB")
    weave.name = "V18_CrossWeave"
    weave.blend_type = "MULTIPLY"
    weave.inputs[0].default_value = 1.0
    weave.location = (-390, -300)

    micro = nodes.new("ShaderNodeTexNoise")
    micro.name = "V18_MicroFiber"
    micro.location = (-390, -500)
    micro.noise_dimensions = "3D"
    micro.inputs["Scale"].default_value = weave_scale * 1.65
    micro.inputs["Detail"].default_value = 2.0
    micro.inputs["Roughness"].default_value = 0.38
    height = nodes.new("ShaderNodeMixRGB")
    height.name = "V18_FiberHeight"
    height.blend_type = "MULTIPLY"
    height.inputs[0].default_value = 0.78
    height.location = (-120, -390)
    bump = nodes.new("ShaderNodeBump")
    bump.name = "V18_TextileNormal"
    bump.location = (170, -280)
    bump.inputs["Strength"].default_value = bump_strength
    bump.inputs["Distance"].default_value = 0.00045

    links.new(texcoord.outputs["Generated"], macro.inputs["Vector"])
    links.new(texcoord.outputs["Generated"], wave_x.inputs["Vector"])
    links.new(texcoord.outputs["Generated"], wave_y.inputs["Vector"])
    links.new(texcoord.outputs["Generated"], micro.inputs["Vector"])
    links.new(macro.outputs["Fac"], dye.inputs["Fac"])
    links.new(macro.outputs["Fac"], rough.inputs["Fac"])
    links.new(dye.outputs["Color"], bsdf.inputs["Base Color"])
    links.new(rough.outputs["Color"], bsdf.inputs["Roughness"])
    links.new(wave_x.outputs["Color"], weave.inputs[1])
    links.new(wave_y.outputs["Color"], weave.inputs[2])
    links.new(weave.outputs["Color"], height.inputs[1])
    links.new(micro.outputs["Fac"], height.inputs[2])
    links.new(height.outputs["Color"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])
    material["v18_surface_system"] = "macro dye breakup + cross weave + microfiber normal"
    return material


def bonded_material() -> bpy.types.Material:
    material = textile_material(
        "M_V18_BondedNeckSeal",
        (0.002, 0.004, 0.005, 1),
        (0.010, 0.015, 0.017, 1),
        (0.68, 0.80),
        115.0,
        0.028,
    )
    bsdf = next(node for node in material.node_tree.nodes if node.type == "BSDF_PRINCIPLED")
    set_input(bsdf, "Coat Weight", 0.0)
    set_input(bsdf, "Sheen Weight", 0.04)
    material["v18_finish"] = "bonded stretch seal"
    return material


def assign_regions(obj, base, flex) -> dict[str, int]:
    obj.data.materials.clear()
    obj.data.materials.append(base)
    obj.data.materials.append(flex)
    counts = {"base": 0, "flex": 0}
    groups = {group.name: group.index for group in obj.vertex_groups}

    def average_weight(polygon, group_name):
        group_index = groups[group_name]
        values = []
        for vertex_index in polygon.vertices:
            membership = next((item for item in obj.data.vertices[vertex_index].groups if item.group == group_index), None)
            values.append(membership.weight if membership else 0.0)
        return sum(values) / len(values)

    joint_pairs = (
        ("upperarm_l", "lowerarm_l"), ("upperarm_r", "lowerarm_r"),
        ("thigh_l", "calf_l"), ("thigh_r", "calf_r"),
    )
    for polygon in obj.data.polygons:
        joint_flex = any(
            min(average_weight(polygon, first), average_weight(polygon, second)) > 0.13
            for first, second in joint_pairs
        )
        polygon.material_index = 1 if joint_flex else 0
        counts["flex" if polygon.material_index else "base"] += 1
    obj["v18_material_zones"] = "woven base; flex knit at elbows, knees, and side torso"
    return counts


def pose_suiting_up(armature) -> None:
    rotations = {
        "spine_01": (5, 0, 0), "spine_02": (8, -2, 2),
        "neck": (8, 0, 0), "head": (15, -6, 3),
        "upperarm_l": (-4, -8, 8), "lowerarm_l": (2, -3, -12),
        "upperarm_r": (4, 8, -8), "lowerarm_r": (-2, 3, 12),
    }
    for name, degrees in rotations.items():
        bone = armature.pose.bones.get(name)
        if bone:
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = tuple(math.radians(value) for value in degrees)
    bpy.context.view_layer.update()


def clear_pose(armature) -> None:
    bpy.context.view_layer.objects.active = armature
    armature.hide_set(False)
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode="OBJECT")


def render(scene, camera, label, position, target, resolution=(1000, 1000), lens=78) -> None:
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
    scene.render.filepath = str(PREVIEWS / f"PlayerCharacter_Undersuit_v18_{label}.png")
    bpy.ops.render.render(write_still=True)


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects["RIG_PlayerCharacter_Undersuit_v17"]
    rig.name = "RIG_PlayerCharacter_Undersuit_v18"
    suit = bpy.data.objects["SK_PlayerCharacter_Undersuit_v17"]
    suit.name = "SK_PlayerCharacter_Undersuit_v18"
    yoke = bpy.data.objects["SK_PlayerUndersuit_NeckYoke_v17"]
    yoke.name = "SK_PlayerUndersuit_NeckYoke_v18"

    base = textile_material(
        "M_V18_PressureWeave_Base",
        (0.0015, 0.0030, 0.0040, 1),
        (0.0070, 0.0115, 0.0140, 1),
        (0.76, 0.88),
        245.0,
        0.038,
    )
    flex = textile_material(
        "M_V18_PressureWeave_Flex",
        (0.0020, 0.0040, 0.0050, 1),
        (0.0100, 0.0150, 0.0170, 1),
        (0.82, 0.93),
        165.0,
        0.052,
    )
    bonded = bonded_material()
    region_counts = assign_regions(suit, base, flex)
    yoke.data.materials.clear()
    yoke.data.materials.append(bonded)
    suit["asset_status"] = "CHARACTER_UNDERSUIT_V18_MATERIAL_REVIEW"
    suit["contains_oversuit"] = False
    yoke["contains_oversuit"] = False

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    render(scene, camera, "Front", Vector((0, -4.15, 1.13)), Vector((0, 0, 1.10)), (900, 1100), 72)
    render(scene, camera, "TextileDetail", Vector((1.12, -2.35, 1.22)), Vector((0, -0.01, 1.20)), (1100, 1000), 92)
    render(scene, camera, "CollarDetail", Vector((1.05, -2.10, 1.52)), Vector((0, 0, 1.47)), (1100, 1000), 96)
    pose_suiting_up(rig)
    render(scene, camera, "SuitingUpPose", Vector((2.7, -3.3, 1.18)), Vector((0, 0, 1.05)), (1100, 1000), 72)
    clear_pose(rig)
    bpy.context.window.scene = original_scene

    REPORT.write_text(json.dumps({
        "schema": 1,
        "asset": "PlayerCharacter_Undersuit_Concept_v18",
        "status": "material_review",
        "contains_oversuit": False,
        "materials": [base.name, flex.name, bonded.name],
        "regional_polygon_counts": region_counts,
        "surface_features": [
            "low-frequency dye variation",
            "cross-woven thread structure",
            "microfiber normal breakup",
            "regional roughness variation",
            "bonded neck-seal finish",
        ],
    }, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V18_MATERIAL_PASS", f"regions={region_counts}", f"output={OUTPUT}")


if __name__ == "__main__":
    main()
