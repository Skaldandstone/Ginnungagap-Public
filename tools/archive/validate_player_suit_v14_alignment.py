"""Validate V14 head/dome centering and upper-chest rest-shape correction."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
BLEND = SUIT_DIR / "PlayerSuit_Production_v14.blend"
BUILD = SUIT_DIR / "PlayerSuit_Production_v14_Alignment.json"
REPORT = SUIT_DIR / "PlayerSuit_Production_v14_validation.json"
RENDER = SUIT_DIR / "Production_v14_Previews" / "PlayerSuit_Production_v14_ProfilePose.png"


def center(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    evaluated.to_mesh_clear()
    return sum(points, Vector()) / len(points)


def main():
    build = json.loads(BUILD.read_text(encoding="utf-8"))
    if abs(build["head_total_rearward_from_v12_m"] - .070) > 1e-6:
        raise RuntimeError("V14 total head correction must be 7 cm from V12")
    if len(build.get("reshaped_meshes", {})) != 5:
        raise RuntimeError("V14 must reshape the undersuit and four matching oversuit shells")
    if any(spec["vertices"] < 100 for spec in build["reshaped_meshes"].values()):
        raise RuntimeError("V14 clavicle correction contains an undersampled mesh")

    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    armature = bpy.data.objects["RIG_PlayerSuit_Production_v14"]
    face = bpy.data.objects["SK_PlayerHead_Production_v6"]
    eye = bpy.data.objects["V6_HEAD_Eye_L"]
    dome = bpy.data.objects["SKV6_Helmet_ClearDome"]
    depsgraph = bpy.context.evaluated_depsgraph_get()
    face_center = center(face, depsgraph)
    eye_center = center(eye, depsgraph)
    dome_center = center(dome, depsgraph)
    profile_delta = abs(face_center.y - dome_center.y)
    if profile_delta > .035:
        raise RuntimeError(f"V14 head remains too far from dome center: {profile_delta:.4f} m")
    if (eye_center - face_center).length > .24:
        raise RuntimeError("V14 eye attachment is detached at rest")

    for name, rotation in {
        "spine_02": (math.radians(4), math.radians(-3), math.radians(2)),
        "head": (math.radians(-4), math.radians(11), math.radians(-3)),
        "upperarm_l": (math.radians(-15), math.radians(-20), math.radians(15)),
        "lowerarm_l": (math.radians(8), math.radians(-5), math.radians(-38)),
    }.items():
        bone = armature.pose.bones.get(name)
        if bone:
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = rotation
    bpy.context.view_layer.update()
    posed_graph = bpy.context.evaluated_depsgraph_get()
    if (center(eye, posed_graph) - center(face, posed_graph)).length > .24:
        raise RuntimeError("V14 eye attachment failed in profile pose")

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    bpy.context.window.scene = scene
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(RENDER)
    camera.location = Vector((4.4, 0, 1.02))
    camera.data.lens = 65
    camera.rotation_euler = (Vector((0, 0, .99)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.render.render(write_still=True)

    REPORT.write_text(json.dumps({
        "schema": 1, "asset": "PlayerSuit_Production_v14", "status": "passed",
        "head_total_rearward_from_v12_m": .070,
        "head_dome_profile_delta_m": profile_delta,
        "face_center": list(face_center), "dome_center": list(dome_center),
        "reshaped_mesh_count": len(build["reshaped_meshes"]),
        "profile_pose_render": str(RENDER.relative_to(ROOT)).replace("\\", "/"),
    }, indent=2), encoding="utf-8")
    bpy.context.view_layer.objects.active = armature
    armature.hide_set(False); armature.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), check_existing=False)
    print("V14_ALIGNMENT_VALIDATION", f"profile_delta={profile_delta:.6f}", "status=passed")


if __name__ == "__main__":
    main()
