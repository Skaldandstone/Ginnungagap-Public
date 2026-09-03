"""Refine the V16 neck/clavicle transition with a deforming undersuit yoke."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerCharacter_Undersuit_Concept_v16.blend"
OUTPUT = SUIT_DIR / "PlayerCharacter_Undersuit_Concept_v17.blend"
PREVIEWS = SUIT_DIR / "Production_v17_Previews"
REPORT = SUIT_DIR / "PlayerCharacter_Undersuit_v17_NecklinePass.json"


def narrow_low_neck(head: bpy.types.Object) -> int:
    """Remove the inherited bust-like shoulder shelf without touching the face."""
    keys = head.data.shape_keys.key_blocks if head.data.shape_keys else ()
    affected = 0
    for key_index, key in enumerate(keys):
        for point in key.data:
            world = head.matrix_world @ point.co
            if world.z >= 1.545:
                continue
            blend = min(1.0, max(0.0, (1.545 - world.z) / 0.055))
            world.x *= 1.0 - 0.46 * blend
            world.y = world.y * (1.0 - 0.24 * blend) + 0.008 * blend
            point.co = head.matrix_world.inverted() @ world
            if key_index == 0:
                affected += 1
    head["v17_low_neck_sculpt"] = "narrowed clavicle shelf; face region unchanged"
    return affected


def build_yoke(
    armature: bpy.types.Object,
    undersuit: bpy.types.Object,
    material: bpy.types.Material,
) -> bpy.types.Object:
    segments = 96
    # Radius, depth, height: a close crew neck flowing into the upper undersuit.
    rings = (
        (0.087, 0.073, 1.558),
        (0.108, 0.085, 1.550),
        (0.140, 0.105, 1.538),
        (0.180, 0.134, 1.522),
        (0.225, 0.160, 1.500),
    )
    vertices = []
    faces = []
    for rx, ry, z in rings:
        for index in range(segments):
            angle = 2 * math.pi * index / segments
            # The back sits slightly higher and closes more tightly than the front.
            rear = max(0.0, math.sin(angle))
            vertices.append((rx * math.cos(angle), ry * math.sin(angle) + 0.004, z + 0.012 * rear))
    for ring in range(len(rings) - 1):
        start = ring * segments
        next_start = (ring + 1) * segments
        for index in range(segments):
            following = (index + 1) % segments
            faces.append((start + index, start + following, next_start + following, next_start + index))

    mesh = bpy.data.meshes.new("SK_PlayerUndersuit_NeckYoke_v17_Mesh")
    mesh.from_pydata(vertices, [], faces)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    mesh.materials.append(material)
    yoke = bpy.data.objects.new("SK_PlayerUndersuit_NeckYoke_v17", mesh)
    bpy.context.collection.objects.link(yoke)

    neck_group = yoke.vertex_groups.new(name="neck")
    chest_group = yoke.vertex_groups.new(name="spine_02")
    conform_group = yoke.vertex_groups.new(name="V17_ConformToUndersuit")
    for ring in range(len(rings)):
        neck_weight = 1.0 - ring / (len(rings) - 1)
        indices = list(range(ring * segments, (ring + 1) * segments))
        neck_group.add(indices, neck_weight, "REPLACE")
        chest_group.add(indices, 1.0 - neck_weight, "REPLACE")
        if ring:
            conform_group.add(indices, (ring / (len(rings) - 1)) ** 1.35, "REPLACE")

    modifier = yoke.modifiers.new("V17_Armature", "ARMATURE")
    modifier.object = armature
    conform = yoke.modifiers.new("V17_ConformToUndersuit", "SHRINKWRAP")
    conform.wrap_method = "NEAREST_SURFACEPOINT"
    conform.target = undersuit
    conform.offset = 0.0025
    conform.vertex_group = conform_group.name
    solidify = yoke.modifiers.new("V17_SoftFabricThickness", "SOLIDIFY")
    solidify.thickness = 0.0035
    solidify.offset = 0.0
    bevel = yoke.modifiers.new("V17_SoftEdge", "BEVEL")
    bevel.width = 0.0025
    bevel.segments = 2
    yoke.parent = armature
    yoke["semantic_layer"] = "character_undersuit"
    yoke["contains_oversuit"] = False
    yoke["v17_design_role"] = "soft pressure-garment clavicle yoke and close collar"
    return yoke


def pose_suiting_up(armature: bpy.types.Object) -> None:
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


def clear_pose(armature: bpy.types.Object) -> None:
    bpy.context.view_layer.objects.active = armature
    armature.hide_set(False)
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode="OBJECT")


def render(scene, camera, label, position, target, resolution=(900, 1100), lens=72) -> None:
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
    scene.render.filepath = str(PREVIEWS / f"PlayerCharacter_Undersuit_v17_{label}.png")
    bpy.ops.render.render(write_still=True)


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    armature = bpy.data.objects["RIG_PlayerCharacter_Undersuit_v16"]
    armature.name = "RIG_PlayerCharacter_Undersuit_v17"
    undersuit = bpy.data.objects["SK_PlayerCharacter_Undersuit_v16"]
    undersuit.name = "SK_PlayerCharacter_Undersuit_v17"
    head = bpy.data.objects["SK_PlayerHead_Production_v6"]
    affected = narrow_low_neck(head)
    yoke = build_yoke(armature, undersuit, undersuit.data.materials[0])
    undersuit["asset_status"] = "CHARACTER_UNDERSUIT_V17_CONCEPT_REVIEW"
    undersuit["contains_oversuit"] = False

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    render(scene, camera, "Front", Vector((0, -4.1, 1.18)), Vector((0, 0, 1.15)))
    render(scene, camera, "Profile", Vector((4.1, 0, 1.18)), Vector((0, 0, 1.15)))
    render(scene, camera, "Neckline", Vector((1.2, -2.25, 1.52)), Vector((0, 0, 1.48)), (1000, 1000), 86)
    pose_suiting_up(armature)
    render(scene, camera, "SuitingUpPose", Vector((2.7, -3.3, 1.18)), Vector((0, 0, 1.05)), (1100, 1000), 72)
    clear_pose(armature)
    bpy.context.window.scene = original_scene

    REPORT.write_text(json.dumps({
        "schema": 1,
        "asset": "PlayerCharacter_Undersuit_Concept_v17",
        "status": "concept_review",
        "contains_oversuit": False,
        "low_neck_basis_vertices_affected": affected,
        "added_component": yoke.name,
        "design_intent": "remove exposed clavicle shelf and close the pressure-garment neckline",
    }, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V17_NECKLINE_PASS", f"affected={affected}", f"yoke={yoke.name}", f"output={OUTPUT}")


if __name__ == "__main__":
    main()
