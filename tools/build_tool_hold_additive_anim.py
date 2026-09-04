"""Makes the additive "arm out, holding a tool" animations the crew plays while a tool is mounted.

The crew body runs ABP_Unarmed, whose DefaultSlot sits over the locomotion state machine. A
non-additive montage through that slot would replace the whole body and freeze the legs; an
additive one is applied on top of whatever the legs are doing. There is no hold animation in
the packs, so this takes the free library's right-hand reach (anim_Touch_R, SK_Mannequin: the
arm fully extended forward, hand at waist height) and makes a local-space additive against
MM_Idle with every bone track except the right arm chain stripped, so only that arm moves.

Because the reach is too low for a tool held in view, it also writes variants with the upper
arm's keys rotated by LIFT_DEGREES about each of its local axes, both ways. The look test
(Ginnungagap.Look.OpeningShots) plays each and logs where the hand lands in camera space, which
is how the variant the character uses was chosen; the others stay for the next adjustment.

    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/build_tool_hold_additive_anim.py -NullRHI
"""
import math
import unreal

SOURCE = "/Game/FreeAnimationLibrary/Animations/Interaction/anim_Touch_R"
IDLE = "/Game/Characters/Mannequins/Anims/Unarmed/MM_Idle"
DEST_DIR = "/Game/Characters/Mannequins/Anims/Tools"
LIFT_DEGREES = 30.0
KEEP = {"clavicle_r", "upperarm_r", "upperarm_twist_01_r", "upperarm_twist_02_r", "lowerarm_r", "lowerarm_twist_01_r",
        "lowerarm_twist_02_r", "hand_r", "index_metacarpal_r", "index_01_r", "index_02_r", "index_03_r", "middle_metacarpal_r",
        "middle_01_r", "middle_02_r", "middle_03_r", "ring_metacarpal_r", "ring_01_r", "ring_02_r", "ring_03_r",
        "pinky_metacarpal_r", "pinky_01_r", "pinky_02_r", "pinky_03_r", "thumb_01_r", "thumb_02_r", "thumb_03_r"}


def qmul(a, b):
    ax, ay, az, aw = a; bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def axis_quat(axis, degrees):
    h = math.radians(degrees) * 0.5
    s = math.sin(h)
    return {"X": (s, 0, 0, math.cos(h)), "Y": (0, s, 0, math.cos(h)), "Z": (0, 0, s, math.cos(h))}[axis]


def build(name, lift):
    path = f"{DEST_DIR}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    dup = unreal.EditorAssetLibrary.duplicate_asset(SOURCE, path)
    assert dup, "duplicate failed"
    controller = dup.get_editor_property("controller")
    model = dup.get_editor_property("data_model_interface")
    tracks = [str(n) for n in unreal.AnimationLibrary.get_animation_track_names(dup)]
    controller.open_bracket("Strip to right arm", True)
    for track in tracks:
        if track not in KEEP:
            controller.remove_bone_track(track, True)
    if lift:
        # One or more (axis, degrees) turns of the upper arm, composed in order.
        delta = (0.0, 0.0, 0.0, 1.0)
        for axis, degrees in (lift if isinstance(lift, list) else [lift]):
            delta = qmul(delta, axis_quat(axis, degrees))
        # 5.8's sequencer-backed data model exposes no key arrays to scripting; the bone's local
        # transform is sampled per frame through the (deprecated, still exposed) pose sampler.
        keys = model.get_number_of_keys()
        pos_keys, rot_keys, scale_keys = [], [], []
        for frame in range(keys):
            xf = unreal.AnimationLibrary.get_bone_pose_for_frame(dup, "upperarm_r", frame, False)
            q = xf.rotation
            x, y, z, w = qmul((q.x, q.y, q.z, q.w), delta)
            pos_keys.append(unreal.Vector(xf.translation.x, xf.translation.y, xf.translation.z))
            rot_keys.append(unreal.Quat(x, y, z, w))
            scale_keys.append(unreal.Vector(xf.scale3d.x, xf.scale3d.y, xf.scale3d.z))
        ok = controller.set_bone_track_keys("upperarm_r", pos_keys, rot_keys, scale_keys, True)
        print(f"TOOLHOLD   upperarm_r {keys} keys rewritten, set={ok}")
    controller.close_bracket(True)
    idle = unreal.load_asset(IDLE)
    # Base pose first, additive type last: each property set kicks off an async recompression, and
    # one that starts additive with no base sequence yet dereferences null (GetAdditiveBasePose).
    dup.set_editor_property("ref_pose_seq", idle)
    dup.set_editor_property("ref_frame_index", 0)
    dup.set_editor_property("ref_pose_type", unreal.AdditiveBasePoseType.ABPT_ANIM_FRAME)
    dup.set_editor_property("additive_anim_type", unreal.AdditiveAnimationType.AAT_LOCAL_SPACE_BASE)
    saved = unreal.EditorAssetLibrary.save_loaded_asset(dup)
    print(f"TOOLHOLD {name} saved={saved} lift={lift}")


import sys
SWEEP = "--sweep" in sys.argv or any("sweep" in a for a in sys.argv)

# What the character uses (CoopSurvivalCharacter::HandleMountedWeaponChanged): from the sweep,
# +Z brings the arm inward and up into view, -X lowers it; 25/-25 put the gloved hand and the
# tool in the lower right of the first-person view (hand at about (35, 17, -19) cm from the eye).
build("A_ToolHold_Combo_B", [("Z", 25.0), ("X", -25.0)])

if SWEEP:
    build("A_ToolHold_Additive", None)
    for axis in ("X", "Y", "Z"):
        for sign, tag in ((1.0, "p"), (-1.0, "n")):
            build(f"A_ToolHold_Lift_{axis}{tag}", (axis, sign * LIFT_DEGREES))
    for name, turns in {"A_ToolHold_Combo_A": [("Z", 20.0), ("X", -20.0)], "A_ToolHold_Combo_C": [("Z", 20.0), ("Y", 15.0)],
                        "A_ToolHold_Combo_D": [("Z", 30.0), ("X", -15.0)]}.items():
        build(name, turns)
