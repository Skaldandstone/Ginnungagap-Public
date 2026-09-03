"""Compare V32 and exported Manny reference spaces before garment rebinding."""

import json
from pathlib import Path

import bpy


root = Path(bpy.path.abspath("//")).parents[2]
fbx = root / "Build" / "Unreal" / "PlayerSuits" / "CryoBodysuitV32" / "SKM_Manny_Simple_Reference.fbx"
existing = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(fbx), use_anim=False, automatic_bone_orientation=False)
imported = [obj for obj in bpy.data.objects if obj not in existing]
manny_rig = next(obj for obj in imported if obj.type == "ARMATURE")
manny_mesh = next(obj for obj in imported if obj.type == "MESH")
v32_rig = bpy.data.objects["RIG_PlayerCharacter_CryoBodysuit_v32"]
v32_suit = bpy.data.objects["SK_PlayerCharacter_CryoBodysuit_v32"]


def bounds(obj):
    points = [obj.matrix_world @ obj.data.vertices[index].co for index in range(len(obj.data.vertices))]
    low = [min(point[axis] for point in points) for axis in range(3)]
    high = [max(point[axis] for point in points) for axis in range(3)]
    return {"min": low, "max": high, "size": [high[index] - low[index] for index in range(3)]}


def bone_points(rig, names):
    return {
        name: list(rig.matrix_world @ rig.data.bones[name].head_local)
        for name in names if rig.data.bones.get(name)
    }


common = sorted(set(bone.name for bone in v32_rig.data.bones) & set(bone.name for bone in manny_rig.data.bones))
report = {
    "manny_rig": manny_rig.name,
    "manny_rig_transform": {"scale": list(manny_rig.scale), "rotation": list(manny_rig.rotation_euler)},
    "manny_mesh": manny_mesh.name,
    "manny_bounds": bounds(manny_mesh),
    "v32_bounds": bounds(v32_suit),
    "common_bones": common,
    "manny_points": bone_points(manny_rig, ("root", "pelvis", "spine_01", "spine_02", "spine_03", "head", "hand_l", "foot_l")),
    "v32_points": bone_points(v32_rig, ("root", "pelvis", "spine_01", "spine_02", "chest", "head", "hand_l", "foot_l")),
}
print("MANNY_V32_ALIGNMENT", json.dumps(report, separators=(",", ":")))
