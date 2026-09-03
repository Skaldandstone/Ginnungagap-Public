"""Pose-test the v5 production suit, render evidence, then restore rest pose."""

import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
BLEND = ROOT / "Art" / "Characters" / "PlayerSuits" / "PlayerSuit_Production_v5.blend"
OUT = ROOT / "Art" / "Characters" / "PlayerSuits" / "Production_v5_Previews"


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    arm = bpy.data.objects["RIG_PlayerSuit_Production_v5"]
    mesh = bpy.data.objects["SK_PlayerSuit_Production_v5"]
    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    bpy.context.window.scene = scene
    scene.camera = camera

    # Moderate asymmetric gameplay pose exercises shoulders, elbows, hips,
    # knees, weighted backpack body, head-parented visor, and tool arm.
    pose_values = {
        "spine_02": (math.radians(2), math.radians(-3), math.radians(2)),
        "head": (math.radians(-3), math.radians(5), math.radians(-2)),
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

    # Verify evaluated mesh contains finite coordinates and remains plausible.
    depsgraph = bpy.context.evaluated_depsgraph_get()
    evaluated = mesh.evaluated_get(depsgraph)
    eval_mesh = evaluated.to_mesh()
    coords = [evaluated.matrix_world @ vertex.co for vertex in eval_mesh.vertices]
    finite = all(math.isfinite(value) for co in coords for value in co)
    bounds = (
        tuple(min(co[i] for co in coords) for i in range(3)),
        tuple(max(co[i] for co in coords) for i in range(3)),
    )
    evaluated.to_mesh_clear()
    if not finite:
        raise RuntimeError("Deformation produced non-finite vertex coordinates")
    if bounds[1][2] - bounds[0][2] > 2.3:
        raise RuntimeError(f"Deformation bounds exploded: {bounds}")

    target = Vector((0, 0, 0.94))
    camera.location = Vector((3.6, -3.6, 1.05))
    camera.rotation_euler = (target - camera.location).to_track_quat("-Z", "Y").to_euler()
    scene.render.filepath = str(OUT / "PlayerSuit_Production_v5_DeformationTest.png")
    bpy.ops.render.render(write_still=True)
    print(f"DEFORMATION_VALIDATION finite={finite} bounds={bounds}")

    # Restore the authored rest pose before saving the production source.
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.window.scene = bpy.data.scenes["Scene"]
    mesh["deformation_test"] = "passed moderate asymmetric pose"
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), check_existing=False)


if __name__ == "__main__":
    main()
