"""Validate V13 character/undersuit/oversuit separation and head placement."""

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
BLEND = SUIT_DIR / "PlayerSuit_Production_v13.blend"
BUILD_REPORT = SUIT_DIR / "PlayerSuit_Production_v13_Layers.json"
REPORT = SUIT_DIR / "PlayerSuit_Production_v13_validation.json"
RENDER = SUIT_DIR / "Production_v13_Previews" / "PlayerSuit_Production_v13_ProfilePose.png"


def center(obj, depsgraph):
    evaluated = obj.evaluated_get(depsgraph)
    mesh = evaluated.to_mesh()
    points = [evaluated.matrix_world @ vertex.co for vertex in mesh.vertices]
    evaluated.to_mesh_clear()
    return sum(points, Vector()) / len(points)


def main():
    build = json.loads(BUILD_REPORT.read_text(encoding="utf-8"))
    if abs(build["head_rearward_offset_m"] - .04) > 1e-6:
        raise RuntimeError("V13 head offset is not the approved 4 cm correction")
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    collections = {
        layer: bpy.data.collections.get(name) for layer, name in {
            "character": "CHARACTER_V13_BODY",
            "undersuit": "CHARACTER_V13_UNDERSUIT",
            "oversuit": "CHARACTER_V13_OVERSUIT",
        }.items()
    }
    if any(collection is None for collection in collections.values()):
        raise RuntimeError("V13 semantic layer collections are incomplete")
    if len(collections["undersuit"].objects) != 1:
        raise RuntimeError("V13 must have exactly one weighted undersuit mesh")
    undersuit = collections["undersuit"].objects[0]
    if undersuit.get("character_layer") != "undersuit":
        raise RuntimeError("V13 undersuit layer metadata is missing")
    if not undersuit.data.materials or undersuit.data.materials[0].name != "M_V13_UndersuitFabric":
        raise RuntimeError("V13 undersuit does not use its standalone fabric material")
    if len(collections["oversuit"].objects) < 25:
        raise RuntimeError("V13 oversuit collection is unexpectedly sparse")
    if any(obj.get("character_layer") != "oversuit" for obj in collections["oversuit"].objects):
        raise RuntimeError("V13 oversuit collection contains an untagged object")

    armature = bpy.data.objects["RIG_PlayerSuit_Production_v13"]
    face = bpy.data.objects["SK_PlayerHead_Production_v6"]
    left_eye = bpy.data.objects["V6_HEAD_Eye_L"]
    dome = bpy.data.objects["SKV6_Helmet_ClearDome"]
    depsgraph = bpy.context.evaluated_depsgraph_get()
    face_center = center(face, depsgraph)
    eye_center = center(left_eye, depsgraph)
    dome_center = center(dome, depsgraph)
    if (eye_center - face_center).length > .24:
        raise RuntimeError("V13 eye attachment separated from the repositioned head")
    if abs(face_center.y - dome_center.y) > .12:
        raise RuntimeError(f"V13 head is not centered in the helmet profile: face={face_center}, dome={dome_center}")

    for name, rotation in {
        "spine_02": (math.radians(3), math.radians(-3), math.radians(2)),
        "head": (math.radians(-4), math.radians(10), math.radians(-3)),
        "upperarm_l": (math.radians(-14), math.radians(-18), math.radians(14)),
        "lowerarm_l": (math.radians(8), math.radians(-5), math.radians(-35)),
    }.items():
        bone = armature.pose.bones.get(name)
        if bone:
            bone.rotation_mode = "XYZ"
            bone.rotation_euler = rotation
    bpy.context.view_layer.update()
    moved_face = center(face, bpy.context.evaluated_depsgraph_get())
    moved_eye = center(left_eye, bpy.context.evaluated_depsgraph_get())
    if (moved_eye - moved_face).length > .24:
        raise RuntimeError("V13 eye attachment failed under head pose")

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
    camera.data.lens = 62
    camera.rotation_euler = (Vector((0, 0, .98)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    bpy.ops.render.render(write_still=True)

    REPORT.write_text(json.dumps({
        "schema": 1, "asset": "PlayerSuit_Production_v13", "status": "passed",
        "head_rearward_offset_m": .04,
        "layer_counts": {name: len(collection.objects) for name, collection in collections.items()},
        "face_center": list(face_center), "dome_center": list(dome_center),
        "face_dome_profile_delta_m": abs(face_center.y - dome_center.y),
        "profile_pose_render": str(RENDER.relative_to(ROOT)).replace("\\", "/"),
    }, indent=2), encoding="utf-8")

    bpy.context.view_layer.objects.active = armature
    armature.hide_set(False); armature.select_set(True)
    bpy.ops.object.mode_set(mode="POSE")
    bpy.ops.pose.select_all(action="SELECT")
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND), check_existing=False)
    print("V13_LAYER_VALIDATION", f"character={len(collections['character'].objects)}",
          f"undersuit={len(collections['undersuit'].objects)}",
          f"oversuit={len(collections['oversuit'].objects)}")


if __name__ == "__main__":
    main()
