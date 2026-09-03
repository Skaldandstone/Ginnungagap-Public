"""Transfer the V32 garment rest pose onto the exact exported Manny skeleton."""

import json
from pathlib import Path

import bpy
from mathutils import Matrix


ROOT = Path(bpy.path.abspath("//")).parents[2]
SOURCE_RIG = bpy.data.objects["RIG_PlayerCharacter_CryoBodysuit_v32"]
SOURCE_NAMES = (
    "SK_PlayerCharacter_CryoBodysuit_v32",
    "SK_PlayerCharacter_CryoNeckSeal_v32",
    "SK_CryoSeam_CenterFront_v32",
    "SK_CryoSeam_LeftLeg_v32",
    "SK_CryoSeam_RightLeg_v32",
)
MANNY_FBX = ROOT / "Build" / "Unreal" / "PlayerSuits" / "CryoBodysuitV32" / "SKM_Manny_Simple_Reference.fbx"
OUTPUT = ROOT / "Build" / "Unreal" / "PlayerSuits" / "CryoBodysuitV32" / "SK_CryoBodysuit_V32_Manny.fbx"
REPORT = ROOT / "Saved" / "V32MannyRebind.json"
REMAP = {"chest": "spine_03", "neck": "neck_01"}


def activate(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


activate(SOURCE_RIG)
bpy.ops.object.mode_set(mode="POSE")
bpy.ops.pose.select_all(action="SELECT")
bpy.ops.pose.transforms_clear()
bpy.ops.object.mode_set(mode="OBJECT")
SOURCE_RIG.data.pose_position = "REST"

existing = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(MANNY_FBX), use_anim=False, automatic_bone_orientation=False)
imported = [obj for obj in bpy.data.objects if obj not in existing]
manny_rig = next(obj for obj in imported if obj.type == "ARMATURE")
manny_meshes = [obj for obj in imported if obj.type == "MESH"]
manny_rig.data.pose_position = "REST"


def old_matrix(name):
    bone = SOURCE_RIG.data.bones.get(name)
    return SOURCE_RIG.matrix_world @ bone.matrix_local if bone else Matrix.Identity(4)


def new_matrix(old_name):
    new_name = REMAP.get(old_name, old_name)
    bone = manny_rig.data.bones.get(new_name)
    # Unreal's root exports as the armature FBX node rather than a Blender bone.
    return manny_rig.matrix_world @ bone.matrix_local if bone else manny_rig.matrix_world


garments = [bpy.data.objects[name] for name in SOURCE_NAMES]
displacements = []
for garment in garments:
    activate(garment)
    for modifier in list(garment.modifiers):
        if modifier.type != "ARMATURE":
            bpy.ops.object.modifier_apply(modifier=modifier.name)

    group_by_index = {group.index: group.name for group in garment.vertex_groups}
    inverse_world = garment.matrix_world.inverted()
    for vertex in garment.data.vertices:
        source_world = garment.matrix_world @ vertex.co
        result = source_world * 0.0
        total = 0.0
        for membership in vertex.groups:
            old_name = group_by_index.get(membership.group)
            if not old_name:
                continue
            new_name = REMAP.get(old_name, old_name)
            if old_name != "root" and not manny_rig.data.bones.get(new_name):
                continue
            transform = new_matrix(old_name) @ old_matrix(old_name).inverted()
            result += (transform @ source_world) * membership.weight
            total += membership.weight
        if total > 1.0e-6:
            result /= total
            displacements.append((result - source_world).length)
            vertex.co = inverse_world @ result
    garment.data.update()

    for old_name, new_name in REMAP.items():
        group = garment.vertex_groups.get(old_name)
        if group:
            group.name = new_name
    for modifier in list(garment.modifiers):
        if modifier.type == "ARMATURE":
            garment.modifiers.remove(modifier)
    armature = garment.modifiers.new("MannyArmature", "ARMATURE")
    armature.object = manny_rig
    world = garment.matrix_world.copy()
    garment.parent = manny_rig
    garment.matrix_world = world

# Join the shell, neck seal, and seam geometry after all receive the same rest transfer.
bpy.ops.object.select_all(action="DESELECT")
for garment in garments:
    garment.select_set(True)
bpy.context.view_layer.objects.active = garments[0]
bpy.ops.object.join()
suit = bpy.context.object
suit.name = "SK_CryoBodysuit_V32_Manny"
suit.data.name = "SK_CryoBodysuit_V32_Manny_Mesh"

# Export only the rebound garment and exact Manny skeleton; the reference body is excluded.
for mesh in manny_meshes:
    mesh.select_set(False)
bpy.ops.object.select_all(action="DESELECT")
manny_rig.select_set(True)
suit.select_set(True)
bpy.context.view_layer.objects.active = manny_rig
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.fbx(
    filepath=str(OUTPUT),
    use_selection=True,
    object_types={"ARMATURE", "MESH"},
    axis_forward="-Y",
    axis_up="Z",
    apply_unit_scale=True,
    apply_scale_options="FBX_SCALE_UNITS",
    add_leaf_bones=False,
    bake_anim=False,
    use_mesh_modifiers=True,
    mesh_smooth_type="FACE",
    path_mode="AUTO",
    armature_nodetype="NULL",
)

report = {
    "status": "pass",
    "output": str(OUTPUT),
    "vertices": len(suit.data.vertices),
    "average_rest_transfer_m": sum(displacements) / len(displacements),
    "maximum_rest_transfer_m": max(displacements),
    "manny_bones": len(manny_rig.data.bones),
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
print("V32_MANNY_REBIND", json.dumps(report, separators=(",", ":")))
