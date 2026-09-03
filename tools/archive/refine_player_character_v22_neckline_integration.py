"""Integrate the V21 cryo gasket into a clean anatomical neckline."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v21.blend"
OUTPUT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_Concept_v22.blend"
PREVIEWS = SUIT_DIR / "Production_v22_Previews"
REPORT = SUIT_DIR / "PlayerCharacter_CryoBodysuit_v22_NecklinePass.json"


def clean_upper_contour(body: bpy.types.Object) -> dict[str, int]:
    mesh = bmesh.new()
    mesh.from_mesh(body.data)
    mesh.verts.ensure_lookup_table()
    boundary = {
        vertex
        for edge in mesh.edges
        if edge.is_boundary
        for vertex in edge.verts
        if vertex.co.z > 1.385 and abs(vertex.co.x) < 0.34
    }
    shoulder_vertices = [
        vertex for vertex in mesh.verts
        if 1.330 < vertex.co.z < 1.545
        and vertex not in boundary
        and (abs(vertex.co.x) > 0.095 or vertex.co.y > 0.095)
    ]
    bmesh.ops.smooth_vert(
        mesh,
        verts=shoulder_vertices,
        factor=0.34,
        use_axis_x=True,
        use_axis_y=True,
        use_axis_z=True,
    )

    rear_adjusted = 0
    for vertex in mesh.verts:
        point = vertex.co
        if 1.10 < point.z < 1.56 and point.y > 0.185:
            point.y = 0.185 + (point.y - 0.185) * 0.08
            rear_adjusted += 1

    mesh.to_mesh(body.data)
    mesh.free()
    body.data.update()
    body["v22_neckline_boundary"] = "stable V21 boundary retained beneath integrated compression panel"
    body["v22_shoulder_cleanup"] = "localized bmesh smoothing and rear outlier compression"
    return {
        "boundary_vertices": len(boundary),
        "shoulder_vertices": len(shoulder_vertices),
        "rear_vertices": rear_adjusted,
    }


def build_neck_bridge(rig: bpy.types.Object, material: bpy.types.Material) -> bpy.types.Object:
    segments = 96
    rings = (
        (0.112, 0.092, 1.456),
        (0.106, 0.087, 1.463),
        (0.101, 0.083, 1.470),
        (0.098, 0.081, 1.476),
    )
    vertices = []
    faces = []
    for rx, ry, z in rings:
        for index in range(segments):
            angle = 2 * math.pi * index / segments
            rear = max(0.0, math.sin(angle))
            vertices.append((
                rx * math.cos(angle),
                ry * math.sin(angle) + 0.004,
                z + 0.006 * rear,
            ))
    for ring in range(len(rings) - 1):
        for index in range(segments):
            following = (index + 1) % segments
            faces.append((
                ring * segments + index,
                ring * segments + following,
                (ring + 1) * segments + following,
                (ring + 1) * segments + index,
            ))
    mesh = bpy.data.meshes.new("SK_PlayerCharacter_CryoNeckBridge_v22_Mesh")
    mesh.from_pydata(vertices, [], faces)
    for polygon in mesh.polygons:
        polygon.use_smooth = True
    bridge = bpy.data.objects.new("SK_PlayerCharacter_CryoNeckBridge_v22", mesh)
    bpy.context.collection.objects.link(bridge)
    mesh.materials.append(material)

    neck = bridge.vertex_groups.new(name="neck")
    chest = bridge.vertex_groups.new(name="chest")
    for ring in range(len(rings)):
        indices = list(range(ring * segments, (ring + 1) * segments))
        neck_weight = ring / (len(rings) - 1)
        neck.add(indices, neck_weight, "REPLACE")
        chest.add(indices, 1.0 - neck_weight, "REPLACE")
    armature = bridge.modifiers.new("V22_BridgeArmature", "ARMATURE")
    armature.object = rig
    solidify = bridge.modifiers.new("V22_BridgeThickness", "SOLIDIFY")
    solidify.thickness = 0.0010
    solidify.offset = 0.0
    bevel = bridge.modifiers.new("V22_BridgeSoftEdge", "BEVEL")
    bevel.width = 0.00055
    bevel.segments = 2
    bridge.parent = rig
    bridge["semantic_layer"] = "character_cryo_bodysuit"
    bridge["contains_oversuit"] = False
    bridge["v22_design_role"] = "integrated stretch-fabric neckline bridge"
    return bridge


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


def render(scene, camera, label, position, target, resolution=(1000, 1000), lens=80) -> None:
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
    scene.render.filepath = str(PREVIEWS / f"PlayerCharacter_CryoBodysuit_v22_{label}.png")
    bpy.ops.render.render(write_still=True)


def main() -> None:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects["RIG_PlayerCharacter_CryoBodysuit_v21"]
    rig.name = "RIG_PlayerCharacter_CryoBodysuit_v22"
    body = bpy.data.objects["SK_PlayerCharacter_CryoBodysuit_v21"]
    body.name = "SK_PlayerCharacter_CryoBodysuit_v22"
    gasket = bpy.data.objects["SK_PlayerCharacter_CryoGasket_v21"]
    gasket.name = "SK_PlayerCharacter_CryoGasket_v22"
    for old, new in (
        ("SK_CryoSeam_CenterFront_v21", "SK_CryoSeam_CenterFront_v22"),
        ("SK_CryoSeam_LeftLeg_v21", "SK_CryoSeam_LeftLeg_v22"),
        ("SK_CryoSeam_RightLeg_v21", "SK_CryoSeam_RightLeg_v22"),
    ):
        bpy.data.objects[old].name = new

    contour_stats = clean_upper_contour(body)
    bridge = build_neck_bridge(rig, body.data.materials[0])
    body["asset_status"] = "CHARACTER_CRYO_BODYSUIT_V22_NECKLINE_REVIEW"
    body["contains_oversuit"] = False

    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    camera = bpy.data.objects["CAM_HighPolyReview"]
    original_scene = bpy.context.window.scene
    bpy.context.window.scene = scene
    render(scene, camera, "Front", Vector((0, -4.10, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 78)
    render(scene, camera, "Profile", Vector((4.10, 0, 1.14)), Vector((0, 0, 1.10)), (900, 1100), 78)
    render(scene, camera, "NecklineDetail", Vector((0.90, -2.00, 1.49)), Vector((0, 0, 1.46)), (1100, 1000), 98)
    pose_cryo_wake(rig)
    render(scene, camera, "CryoWakePose", Vector((2.75, -3.35, 1.16)), Vector((0, 0, 1.04)), (1100, 1000), 78)
    clear_pose(rig)
    bpy.context.window.scene = original_scene

    REPORT.write_text(json.dumps({
        "schema": 1,
        "asset": "PlayerCharacter_CryoBodysuit_Concept_v22",
        "status": "neckline_review",
        "contains_oversuit": False,
        "contour_stats": contour_stats,
        "neck_bridge": bridge.name,
        "gasket": gasket.name,
        "preserved_details": [
            "center-front bonded seam", "left leg seam", "right leg seam",
            "continuous compression mask",
        ],
    }, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V22_NECKLINE", f"stats={contour_stats}", f"bridge={bridge.name}", f"output={OUTPUT}")


if __name__ == "__main__":
    main()
