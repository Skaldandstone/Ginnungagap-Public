"""Add integrated cryo-garment construction detail to the continuous V20 shell."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v20.blend"
OUTPUT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v21.blend"
PREVIEWS = SUIT_DIR / "Production_v21_Previews"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v21_DetailPass.json"


def group_weight(vertex, group_index: int) -> float:
    membership = next((item for item in vertex.groups if item.group == group_index), None)
    return membership.weight if membership else 0.0


def add_compression_mask(body: bpy.types.Object, material: bpy.types.Material) -> dict[str, float]:
    groups = {group.name: group.index for group in body.vertex_groups}
    attribute = body.data.color_attributes.get("V21_CompressionMask")
    if attribute:
        body.data.color_attributes.remove(attribute)
    attribute = body.data.color_attributes.new(
        name="V21_CompressionMask", type="FLOAT_COLOR", domain="POINT"
    )
    total = 0.0
    maximum = 0.0
    for vertex in body.data.vertices:
        pairs = (
            ("upperarm_l", "lowerarm_l"), ("upperarm_r", "lowerarm_r"),
            ("thigh_l", "calf_l"), ("thigh_r", "calf_r"),
        )
        joint = max(
            4.0 * group_weight(vertex, groups[first]) * group_weight(vertex, groups[second])
            for first, second in pairs
        )
        waist = math.exp(-((vertex.co.z - 1.02) / 0.085) ** 2) * 0.22
        mask = min(1.0, max(joint, waist))
        attribute.data[vertex.index].color = (mask, mask, mask, 1.0)
        total += mask
        maximum = max(maximum, mask)

    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    dye = nodes.get("V18_DyePalette")
    color_mask = nodes.new("ShaderNodeVertexColor")
    color_mask.name = "V21_CompressionMask"
    color_mask.layer_name = attribute.name
    color_mask.location = (10, 250)
    mix = nodes.new("ShaderNodeMixRGB")
    mix.name = "V21_CompressionDyeMix"
    mix.blend_type = "MIX"
    mix.location = (220, 220)
    mix.inputs[2].default_value = (0.040, 0.058, 0.064, 1)
    for link in list(bsdf.inputs["Base Color"].links):
        links.remove(link)
    links.new(color_mask.outputs["Color"], mix.inputs[0])
    links.new(dye.outputs["Color"], mix.inputs[1])
    links.new(mix.outputs["Color"], bsdf.inputs["Base Color"])
    body["v21_compression_zones"] = "continuous vertex mask from paired joint weights and waist falloff"
    return {"mean": total / len(body.data.vertices), "maximum": maximum}


def seam_material(source: bpy.types.Material) -> bpy.types.Material:
    material = source.copy()
    material.name = "M_V21_BondedCryoSeam"
    nodes = material.node_tree.nodes
    palette = nodes.get("V18_DyePalette")
    if palette:
        palette.color_ramp.elements[0].color = (0.018, 0.028, 0.032, 1)
        palette.color_ramp.elements[1].color = (0.055, 0.075, 0.080, 1)
    bump = nodes.get("V18_TextileNormal")
    if bump:
        bump.inputs["Strength"].default_value = 0.012
    bsdf = next(node for node in nodes if node.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Roughness"].default_value = 0.62
    material["v21_finish"] = "heat-bonded flexible seam tape"
    return material


def transfer_weights(obj: bpy.types.Object, source: bpy.types.Object, rig: bpy.types.Object) -> None:
    for group in source.vertex_groups:
        obj.vertex_groups.new(name=group.name)
    transfer = obj.modifiers.new("V21_TransferWeights", "DATA_TRANSFER")
    transfer.object = source
    transfer.use_vert_data = True
    transfer.data_types_verts = {"VGROUP_WEIGHTS"}
    transfer.vert_mapping = "POLYINTERP_NEAREST"
    transfer.layers_vgroup_select_src = "ALL"
    transfer.layers_vgroup_select_dst = "NAME"
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=transfer.name)
    armature = obj.modifiers.new("V21_Armature", "ARMATURE")
    armature.object = rig
    obj.parent = rig


def projected_ribbon(
    body: bpy.types.Object,
    rig: bpy.types.Object,
    material: bpy.types.Material,
    name: str,
    x_at_z,
    z_start: float,
    z_end: float,
    samples: int,
    half_width: float,
) -> bpy.types.Object | None:
    vertices = []
    faces = []
    valid_rows = 0
    for row in range(samples):
        z = z_start + (z_end - z_start) * row / (samples - 1)
        center_x = x_at_z(z)
        row_vertices = []
        for x in (center_x - half_width, center_x + half_width):
            hit, location, normal, _ = body.ray_cast(Vector((x, -1.0, z)), Vector((0, 1, 0)))
            if not hit:
                row_vertices = []
                break
            row_vertices.append(location + normal * 0.0014)
        if not row_vertices:
            continue
        vertices.extend(row_vertices)
        if valid_rows:
            start = (valid_rows - 1) * 2
            faces.append((start, start + 1, start + 3, start + 2))
        valid_rows += 1
    if valid_rows < 2:
        return None
    mesh = bpy.data.meshes.new(f"{name}_Mesh")
    mesh.from_pydata(vertices, [], faces)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    ribbon = bpy.data.objects.new(name, mesh)
    bpy.context.collection.objects.link(ribbon)
    mesh.materials.append(material)
    transfer_weights(ribbon, body, rig)
    solidify = ribbon.modifiers.new("V21_SeamThickness", "SOLIDIFY")
    solidify.thickness = 0.00065
    solidify.offset = 0.0
    bevel = ribbon.modifiers.new("V21_SeamSoftEdge", "BEVEL")
    bevel.width = 0.00045
    bevel.segments = 2
    ribbon["semantic_layer"] = "character_cryo_bodysuit"
    ribbon["contains_oversuit"] = False
    ribbon["v21_design_role"] = "bonded construction seam"
    return ribbon


def gasket_collar(rig: bpy.types.Object, material: bpy.types.Material) -> bpy.types.Object:
    major_segments = 96
    minor_segments = 10
    rx, ry, radius, center_z = 0.094, 0.078, 0.0065, 1.480
    vertices = []
    faces = []
    for major in range(major_segments):
        theta = 2 * math.pi * major / major_segments
        cos_theta, sin_theta = math.cos(theta), math.sin(theta)
        for minor in range(minor_segments):
            phi = 2 * math.pi * minor / minor_segments
            radial = radius * math.cos(phi)
            vertices.append((
                (rx + radial) * cos_theta,
                (ry + radial) * sin_theta + 0.004,
                center_z + radius * math.sin(phi),
            ))
    for major in range(major_segments):
        next_major = (major + 1) % major_segments
        for minor in range(minor_segments):
            next_minor = (minor + 1) % minor_segments
            faces.append((
                major * minor_segments + minor,
                major * minor_segments + next_minor,
                next_major * minor_segments + next_minor,
                next_major * minor_segments + minor,
            ))
    mesh = bpy.data.meshes.new("SK_PlayerCharacter_CryoGasket_v21_Mesh")
    mesh.from_pydata(vertices, [], faces)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    collar = bpy.data.objects.new("SK_PlayerCharacter_CryoGasket_v21", mesh)
    bpy.context.collection.objects.link(collar)
    mesh.materials.append(material)
    neck = collar.vertex_groups.new(name="neck")
    neck.add(list(range(len(vertices))), 1.0, "REPLACE")
    armature = collar.modifiers.new("V21_GasketArmature", "ARMATURE")
    armature.object = rig
    collar.parent = rig
    collar["semantic_layer"] = "character_cryo_bodysuit"
    collar["contains_oversuit"] = False
    collar["v21_design_role"] = "close flexible neck gasket"
    return collar


def pose_cryo_wake(armature) -> None:
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
    scene.render.filepath = str(PREVIEWS / f"PlayerCharacter_CryoBodysuit_v21_{label}.png")
    bpy.ops.render.render(write_still=True)


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects["RIG_PlayerCharacter_CryoBodysuit_v20"]
    rig.name = "RIG_PlayerCharacter_CryoBodysuit_v21"
    body = bpy.data.objects["SK_PlayerCharacter_CryoBodysuit_v20"]
    body.name = "SK_PlayerCharacter_CryoBodysuit_v21"
    old_collar = bpy.data.objects["SK_PlayerCharacter_CryoCollar_v20"]
    bpy.data.objects.remove(old_collar, do_unlink=True)

    source_material = bpy.data.materials["M_V20_CryoCompressionFabric"]
    material = source_material.copy()
    material.name = "M_V21_CryoCompressionFabric"
    body.data.materials.clear()
    body.data.materials.append(material)
    mask_stats = add_compression_mask(body, material)
    bonded = seam_material(source_material)
    gasket = gasket_collar(rig, bonded)
    seams = []
    definitions = (
        ("SK_CryoSeam_CenterFront_v21", lambda z: 0.0, 0.66, 1.42, 72, 0.0032),
        ("SK_CryoSeam_LeftLeg_v21", lambda z: -0.105, 0.08, 0.66, 56, 0.0028),
        ("SK_CryoSeam_RightLeg_v21", lambda z: 0.105, 0.08, 0.66, 56, 0.0028),
    )
    for definition in definitions:
        seam = projected_ribbon(body, rig, bonded, *definition)
        if seam:
            seams.append(seam.name)
    body["asset_status"] = "CHARACTER_CRYO_BODYSUIT_V21_DETAIL_REVIEW"
    body["contains_oversuit"] = False

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    render(scene, camera, "Front", Vector((0, -4.15, 1.12)), Vector((0, 0, 1.09)), (900, 1100), 76)
    render(scene, camera, "UpperBody", Vector((1.05, -2.50, 1.28)), Vector((0, 0, 1.22)), (1100, 1000), 94)
    render(scene, camera, "GasketDetail", Vector((0.85, -1.85, 1.50)), Vector((0, 0, 1.47)), (1100, 1000), 98)
    pose_cryo_wake(rig)
    render(scene, camera, "CryoWakePose", Vector((2.75, -3.35, 1.16)), Vector((0, 0, 1.04)), (1100, 1000), 76)
    clear_pose(rig)
    bpy.context.window.scene = original_scene

    REPORT.write_text(json.dumps({
        "schema": 1,
        "asset": "PlayerCharacter_CryoBodysuit_Concept_v21",
        "status": "detail_review",
        "contains_oversuit": False,
        "compression_mask": mask_stats,
        "seams": seams,
        "gasket": gasket.name,
        "materials": [material.name, bonded.name],
    }, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V21_CRYO_DETAILS", f"seams={seams}", f"mask={mask_stats}", f"output={OUTPUT}")


if __name__ == "__main__":
    main()
