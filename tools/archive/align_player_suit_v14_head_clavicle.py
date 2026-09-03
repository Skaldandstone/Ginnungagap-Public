"""Correct V13 head and clavicle profile alignment without changing the helmet."""

from __future__ import annotations

import json
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerSuit_Production_v13.blend"
OUTPUT = SUIT_DIR / "PlayerSuit_Production_v14.blend"
PREVIEWS = SUIT_DIR / "Production_v14_Previews"
REPORT = SUIT_DIR / "PlayerSuit_Production_v14_Alignment.json"
HEAD_ADDITIONAL_REARWARD_M = .030
CLAVICLE_MAX_REARWARD_M = .028


def move_head_root():
    head = bpy.data.objects["SK_PlayerHead_Production_v6"]
    before = head.matrix_world.translation.copy()
    world = head.matrix_world.copy()
    world.translation.y += HEAD_ADDITIONAL_REARWARD_M
    head.matrix_world = world
    bpy.context.view_layer.update()
    return before, head.matrix_world.translation.copy()


def reshape_upper_chest(obj, maximum):
    inverse = obj.matrix_world.inverted()
    moved = []
    total = 0.0
    for vertex in obj.data.vertices:
        world = obj.matrix_world @ vertex.co
        if world.y >= .035 or abs(world.x) >= .30 or not (1.30 < world.z < 1.52):
            continue
        z_weight = min(1.0, max(0.0, (world.z - 1.30) / .10))
        x_weight = min(1.0, max(0.0, (.30 - abs(world.x)) / .08))
        front_weight = min(1.0, max(.15, (.035 - world.y) / .12))
        offset = maximum * z_weight * x_weight * front_weight
        world.y += offset
        vertex.co = inverse @ world
        moved.append(vertex.index)
        total += offset
    if not moved:
        raise RuntimeError(f"No upper-chest vertices selected on {obj.name}")
    obj["v14_clavicle_vertex_count"] = len(moved)
    obj["v14_average_rearward_m"] = total / len(moved)
    return len(moved), total / len(moved)


def move_object_world_y(obj, amount):
    world = obj.matrix_world.copy()
    world.translation.y += amount
    obj.matrix_world = world
    obj["v14_alignment_offset_y_m"] = amount


def point_camera(camera, position, target):
    camera.location = position
    camera.data.lens = 65
    camera.rotation_euler = (target - position).to_track_quat("-Z", "Y").to_euler()


def render(scene, camera, visible):
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.camera = camera
    for obj in visible:
        obj.hide_render = False
    target = Vector((0, 0, .99))
    for label, position in {
        "Front": Vector((0, -4.4, 1.02)),
        "Profile": Vector((4.4, 0, 1.02)),
        "ThreeQuarter": Vector((3.1, -3.1, 1.06)),
    }.items():
        point_camera(camera, position, target)
        scene.render.filepath = str(PREVIEWS / f"PlayerSuit_Production_v14_{label}.png")
        bpy.ops.render.render(write_still=True)
    scene.render.resolution_x = 1000
    scene.render.resolution_y = 800
    point_camera(camera, Vector((2.2, 0, 1.55)), Vector((0, 0, 1.50)))
    camera.data.lens = 82
    scene.render.filepath = str(PREVIEWS / "PlayerSuit_Production_v14_ProfileAlignmentCloseup.png")
    bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    armature = bpy.data.objects["RIG_PlayerSuit_Production_v13"]
    armature.name = "RIG_PlayerSuit_Production_v14"
    undersuit = bpy.data.objects["SK_PlayerSuit_Production_v13_Undersuit"]
    undersuit.name = "SK_PlayerSuit_Production_v14_Undersuit"
    before, after = move_head_root()

    reshaped = {}
    count, average = reshape_upper_chest(undersuit, CLAVICLE_MAX_REARWARD_M)
    reshaped[undersuit.name] = {"vertices": count, "average_offset_m": average}
    for name, amount in {
        "SKV11_ChestUpper": CLAVICLE_MAX_REARWARD_M,
        "SKV11_ChestLower": .014,
        "SKV11_Shoulder_L": .020,
        "SKV11_Shoulder_R": .020,
    }.items():
        obj = bpy.data.objects.get(name)
        if obj:
            count, average = reshape_upper_chest(obj, amount)
            reshaped[name] = {"vertices": count, "average_offset_m": average}

    # Keep accepted chest hardware seated on the corrected shell surface.
    moved_hardware = []
    for name in ("SKV12_ChestCenterSeal", "SKV12_ChestTelemetry",
                 "SKV12_StatusLamp_0", "SKV12_StatusLamp_1", "SKV12_StatusLamp_2"):
        obj = bpy.data.objects.get(name)
        if obj:
            move_object_world_y(obj, .020)
            moved_hardware.append(name)

    undersuit["asset_status"] = "ART_DIRECTION_REVIEW_V14_HEAD_CLAVICLE_ALIGNED"
    undersuit["runtime_replacement"] = False
    undersuit["head_total_rearward_from_v12_m"] = .070
    REPORT.write_text(json.dumps({
        "schema": 1, "asset": "PlayerSuit_Production_v14", "status": "alignment_review",
        "head_additional_rearward_m": HEAD_ADDITIONAL_REARWARD_M,
        "head_total_rearward_from_v12_m": .070,
        "head_before": list(before), "head_after": list(after),
        "clavicle_max_rearward_m": CLAVICLE_MAX_REARWARD_M,
        "reshaped_meshes": reshaped, "moved_hardware": moved_hardware,
    }, indent=2), encoding="utf-8")
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    original = bpy.context.window.scene
    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    bpy.context.window.scene = scene
    visible = list(dict.fromkeys([
        *bpy.data.collections["CHARACTER_V13_BODY"].objects,
        *bpy.data.collections["CHARACTER_V13_UNDERSUIT"].objects,
        *bpy.data.collections["CHARACTER_V13_OVERSUIT"].objects,
    ]))
    render(scene, bpy.data.objects["CAM_HighPolyReview"], visible)
    bpy.context.window.scene = original
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V14_ALIGNMENT", f"head_additional={HEAD_ADDITIONAL_REARWARD_M}",
          f"undersuit_vertices={reshaped[undersuit.name]['vertices']}", f"output={OUTPUT}")


if __name__ == "__main__":
    main()
