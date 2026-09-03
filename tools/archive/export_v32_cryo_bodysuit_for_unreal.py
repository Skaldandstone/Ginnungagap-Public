"""Export the authored V32 cryo bodysuit as a clean Unreal skeletal FBX."""

from pathlib import Path

import bpy


ROOT = Path(bpy.path.abspath("//")).parents[2]
OUTPUT_DIR = ROOT / "Build" / "Unreal" / "PlayerSuits" / "CryoBodysuitV32"
OUTPUT = OUTPUT_DIR / "SK_CryoBodysuit_V32.fbx"
RIG_NAME = "RIG_PlayerCharacter_CryoBodysuit_v32"
GARMENT_NAMES = (
    "SK_PlayerCharacter_CryoBodysuit_v32",
    "SK_PlayerCharacter_CryoNeckSeal_v32",
    "SK_CryoSeam_CenterFront_v32",
    "SK_CryoSeam_LeftLeg_v32",
    "SK_CryoSeam_RightLeg_v32",
)


def activate(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.hide_set(False)
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


rig = bpy.data.objects[RIG_NAME]
garments = [bpy.data.objects[name] for name in GARMENT_NAMES]

# Export the undeformed reference pose, not the review animation pose.
activate(rig)
bpy.ops.object.mode_set(mode="POSE")
bpy.ops.pose.select_all(action="SELECT")
bpy.ops.pose.transforms_clear()
bpy.ops.object.mode_set(mode="OBJECT")
rig.data.pose_position = "REST"

# Match the runtime player/MetaHuman torso naming used by the Copy Pose bridge.
chest = rig.data.bones.get("chest")
if chest:
    chest.name = "spine_03"
for garment in garments:
    group = garment.vertex_groups.get("chest")
    if group:
        group.name = "spine_03"

# Bake surface-only modifiers while preserving armature deformation.
for garment in garments:
    activate(garment)
    for modifier in list(garment.modifiers):
        if modifier.type != "ARMATURE":
            bpy.ops.object.modifier_apply(modifier=modifier.name)

# Consolidate the shell, seal, and seam geometry into one skinned asset.
bpy.ops.object.select_all(action="DESELECT")
for garment in garments:
    garment.hide_set(False)
    garment.select_set(True)
bpy.context.view_layer.objects.active = garments[0]
bpy.ops.object.join()
suit = bpy.context.object
suit.name = "SK_CryoBodysuit_V32"
suit.data.name = "SK_CryoBodysuit_V32_Mesh"
suit.parent = rig

armature = next((modifier for modifier in suit.modifiers if modifier.type == "ARMATURE"), None)
if not armature:
    armature = suit.modifiers.new("Armature", "ARMATURE")
armature.object = rig

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
suit.select_set(True)
bpy.context.view_layer.objects.active = rig
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
)
print(f"V32_UNREAL_EXPORT {OUTPUT}")
