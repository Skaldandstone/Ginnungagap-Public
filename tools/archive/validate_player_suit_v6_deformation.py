"""Pose-test v6, validate face attachments/LODs, render evidence, restore rest."""

import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
BLEND = ROOT / "Art" / "Characters" / "PlayerSuits" / "PlayerSuit_Production_v6.blend"
OUT = ROOT / "Art" / "Characters" / "PlayerSuits" / "Production_v6_Previews"


def bounds_for(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    coords = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    finite = all(math.isfinite(value) for co in coords for value in co)
    bounds = (
        tuple(min(co[i] for co in coords) for i in range(3)),
        tuple(max(co[i] for co in coords) for i in range(3)),
    )
    evaluated.to_mesh_clear()
    return finite, bounds


def center(bounds):
    return Vector(tuple((bounds[0][i] + bounds[1][i]) * 0.5 for i in range(3)))


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    arm = bpy.data.objects["RIG_PlayerSuit_Production_v6"]
    suit = bpy.data.objects["SK_PlayerSuit_Production_v6_LOD0"]
    face = bpy.data.objects["SK_PlayerHead_Production_v6"]
    eye_l = bpy.data.objects["V6_HEAD_Eye_L"]
    eye_r = bpy.data.objects["V6_HEAD_Eye_R"]
    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    bpy.context.window.scene = scene
    scene.camera = camera

    pose_values = {
        "spine_02": (math.radians(2), math.radians(-3), math.radians(2)),
        "head": (math.radians(-4), math.radians(8), math.radians(-3)),
        "upperarm_l": (math.radians(-8), math.radians(-18), math.radians(16)),
        "lowerarm_l": (math.radians(5), math.radians(-8), math.radians(-22)),
        "upperarm_r": (math.radians(6), math.radians(10), math.radians(-10)),
        "lowerarm_r": (math.radians(-4), math.radians(6), math.radians(14)),
        "thigh_l": (math.radians(7), math.radians(-2), math.radians(2)),
        "calf_l": (math.radians(-11), 0, 0),
        "thigh_r": (math.radians(-4), math.radians(2), math.radians(-2)),
    }
    for name, rotation in pose_values.items():
        bone = arm.pose.bones.get(name)
        if bone:
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = rotation
    bpy.context.view_layer.update()

    depsgraph = bpy.context.evaluated_depsgraph_get()
    suit_finite, suit_bounds = bounds_for(suit, depsgraph)
    face_finite, face_bounds = bounds_for(face, depsgraph)
    left_finite, left_bounds = bounds_for(eye_l, depsgraph)
    right_finite, right_bounds = bounds_for(eye_r, depsgraph)
    if not all((suit_finite, face_finite, left_finite, right_finite)):
        raise RuntimeError("Non-finite coordinates found in v6 deformation test")
    if suit_bounds[1][2] - suit_bounds[0][2] > 2.3:
        raise RuntimeError(f"Suit deformation bounds exploded: {suit_bounds}")
    face_center = center(face_bounds)
    for label, eye_bounds in (("left", left_bounds), ("right", right_bounds)):
        eye_center = center(eye_bounds)
        if eye_center.z < 1.2 or (eye_center - face_center).length > 0.32:
            raise RuntimeError(f"{label} eye detached from face: eye={eye_center}, face={face_center}")

    for level in (1, 2):
        lod = bpy.data.objects[f"SK_PlayerSuit_Production_v6_LOD{level}"]
        if not lod.data.uv_layers.get("UV0"):
            raise RuntimeError(f"LOD{level} lost UV0")
        if len(lod.vertex_groups) < 20:
            raise RuntimeError(f"LOD{level} lost deformation groups")

    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    camera.data.type = "PERSP"
    camera.data.lens = 55
    target = Vector((0, 0, 0.98))
    camera.location = Vector((3.6, -3.6, 1.10))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(OUT / "PlayerSuit_Production_v6_DeformationTest.png")
    bpy.ops.render.render(write_still=True)

    bpy.context.view_layer.objects.active = arm
    arm.hide_set(False)
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.update()
    suit["deformation_test"] = "passed v6 asymmetric pose with head attachment validation"
    suit["facial_attachment_test"] = "passed"
    bpy.context.window.scene = bpy.data.scenes["Scene"]
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), check_existing=False)
    print(
        "V6_DEFORMATION_VALIDATION",
        f"suit_bounds={suit_bounds}",
        f"face_bounds={face_bounds}",
        f"left_eye={left_bounds}",
        f"right_eye={right_bounds}",
        "lod_uv_weights=passed",
    )


if __name__ == "__main__":
    main()

