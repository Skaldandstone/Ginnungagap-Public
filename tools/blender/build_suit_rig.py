import bpy
import math
import os
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
OUT_DIR = os.path.join(ROOT, 'Content', 'Source', 'Characters', 'PlayerSuit')
BLEND_PATH = os.path.join(OUT_DIR, 'SK_PlayerSuit_Rig.blend')
FBX_PATH = os.path.join(OUT_DIR, 'SK_PlayerSuit_Rig.fbx')

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.actions, bpy.data.armatures, bpy.data.meshes, bpy.data.materials):
    if hasattr(datablocks, 'remove'):
        pass

def material(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1.0)
    return m

body_mat = material('M_ProxyBody', (0.12, 0.15, 0.16))
suit_mat = material('M_ProxySuit', (0.20, 0.24, 0.25))
seal_mat = material('M_ProxySeal', (0.68, 0.65, 0.56))
visor_mat = material('M_ProxyVisor', (0.008, 0.015, 0.020))
station_mat = material('M_ProxyStation', (0.07, 0.09, 0.10))

arm_data = bpy.data.armatures.new('SK_PlayerSuit_Skeleton')
rig = bpy.data.objects.new('SK_PlayerSuit_Rig', arm_data)
bpy.context.collection.objects.link(rig)
bpy.context.view_layer.objects.active = rig
rig.select_set(True)
bpy.ops.object.mode_set(mode='EDIT')

def bone(name, head, tail, parent=None):
    b = arm_data.edit_bones.new(name)
    b.head, b.tail = head, tail
    if parent:
        b.parent = arm_data.edit_bones[parent]
    return b

# Unreal-friendly humanoid hierarchy, Z up and Y forward in Blender.
bone('root', (0, 0, 0), (0, 0, .18))
bone('pelvis', (0, 0, .90), (0, 0, 1.08), 'root')
bone('spine_01', (0, 0, 1.02), (0, 0, 1.25), 'pelvis')
bone('spine_02', (0, 0, 1.25), (0, 0, 1.48), 'spine_01')
bone('neck_01', (0, 0, 1.48), (0, 0, 1.62), 'spine_02')
bone('head', (0, 0, 1.62), (0, 0, 1.86), 'neck_01')
for side, s in [('l', -1), ('r', 1)]:
    bone(f'clavicle_{side}', (0, 0, 1.45), (.18*s, 0, 1.47), 'spine_02')
    bone(f'upperarm_{side}', (.18*s, 0, 1.47), (.48*s, 0, 1.39), f'clavicle_{side}')
    bone(f'lowerarm_{side}', (.48*s, 0, 1.39), (.73*s, 0, 1.22), f'upperarm_{side}')
    bone(f'hand_{side}', (.73*s, 0, 1.22), (.88*s, .01, 1.18), f'lowerarm_{side}')
    bone(f'thigh_{side}', (.11*s, 0, .98), (.13*s, 0, .55), 'pelvis')
    bone(f'calf_{side}', (.13*s, 0, .55), (.13*s, 0, .12), f'thigh_{side}')
    bone(f'foot_{side}', (.13*s, 0, .12), (.13*s, -.24, .06), f'calf_{side}')
    bone(f'hand_ik_{side}', (.88*s, .02, 1.18), (.88*s, .02, 1.30), 'root')

# Independent suit assembly controls: rigid pieces can be detached, donned, doffed, and stowed.
bone('suit_root', (0, .62, .85), (0, .62, 1.05), 'root')
for name, loc in {
    'suit_torso': (0, .62, 1.30), 'suit_arm_l': (-.38, .62, 1.33),
    'suit_arm_r': (.38, .62, 1.33), 'suit_leg_l': (-.13, .62, .57),
    'suit_leg_r': (.13, .62, .57), 'helmet_ctrl': (0, .62, 1.72),
    'neck_seal_ctrl': (0, .62, 1.54)
}.items():
    bone(name, loc, Vector(loc) + Vector((0, 0, .16)), 'suit_root')
bone('recess_root', (0, 1.15, .1), (0, 1.15, .3), 'root')
bone('restraint_l', (-.55, 1.05, 1.25), (-.20, 1.05, 1.25), 'recess_root')
bone('restraint_r', (.55, 1.05, 1.25), (.20, 1.05, 1.25), 'recess_root')
bpy.ops.object.mode_set(mode='OBJECT')

def proxy(name, bone_name, shape, scale, mat):
    if shape == 'sphere':
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12)
    else:
        bpy.ops.mesh.primitive_cube_add()
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    obj.data.materials.append(mat)
    obj.parent = rig
    obj.parent_type = 'BONE'
    obj.parent_bone = bone_name
    obj.matrix_parent_inverse = rig.matrix_world.inverted()
    obj.location = (0, 0, 0)
    return obj

# Readable mannequin and modular suit proxies; these are intentionally replaceable.
proxy('BODY_Torso', 'spine_02', 'cube', (.22, .13, .27), body_mat)
proxy('BODY_Head', 'head', 'sphere', (.13, .12, .16), body_mat)
for side in ('l', 'r'):
    proxy(f'BODY_UpperArm_{side}', f'upperarm_{side}', 'cube', (.07, .07, .19), body_mat)
    proxy(f'BODY_LowerArm_{side}', f'lowerarm_{side}', 'cube', (.06, .06, .17), body_mat)
    proxy(f'BODY_Hand_{side}', f'hand_{side}', 'cube', (.075, .045, .035), body_mat)
    proxy(f'BODY_Thigh_{side}', f'thigh_{side}', 'cube', (.09, .09, .23), body_mat)
    proxy(f'BODY_Calf_{side}', f'calf_{side}', 'cube', (.075, .075, .22), body_mat)
proxy('SUIT_Torso', 'suit_torso', 'cube', (.26, .17, .31), suit_mat)
proxy('SUIT_Arm_L', 'suit_arm_l', 'cube', (.085, .085, .34), suit_mat)
proxy('SUIT_Arm_R', 'suit_arm_r', 'cube', (.085, .085, .34), suit_mat)
proxy('SUIT_Leg_L', 'suit_leg_l', 'cube', (.11, .11, .46), suit_mat)
proxy('SUIT_Leg_R', 'suit_leg_r', 'cube', (.11, .11, .46), suit_mat)
proxy('SUIT_Helmet', 'helmet_ctrl', 'sphere', (.31, .30, .32), visor_mat)
proxy('SUIT_NeckSeal', 'neck_seal_ctrl', 'cube', (.31, .31, .035), seal_mat)
proxy('RECESS_Back', 'recess_root', 'cube', (.68, .12, 1.05), station_mat)
proxy('RECESS_Restraint_L', 'restraint_l', 'cube', (.23, .035, .035), seal_mat)
proxy('RECESS_Restraint_R', 'restraint_r', 'cube', (.23, .035, .035), seal_mat)

def key(pb, frame, location=None, rotation=None, scale=None):
    pb.rotation_mode = 'XYZ'
    if location is not None: pb.location = location
    if rotation is not None: pb.rotation_euler = rotation
    if scale is not None: pb.scale = scale
    pb.keyframe_insert('location', frame=frame)
    pb.keyframe_insert('rotation_euler', frame=frame)
    pb.keyframe_insert('scale', frame=frame)

def new_action(name, end):
    action = bpy.data.actions.new(name)
    action.use_fake_user = True
    rig.animation_data_create()
    rig.animation_data.action = action
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_euler = (0, 0, 0); pb.scale = (1, 1, 1)
    action['unreal_clip_name'] = name
    action['frame_start'] = 0
    action['frame_end'] = end
    return action

# 01: the complete suit is released and pulled clear as one assembly.
new_action('A_Suit_01_Extract', 150)
key(rig.pose.bones['restraint_l'], 0); key(rig.pose.bones['restraint_r'], 0)
key(rig.pose.bones['restraint_l'], 42, rotation=(0, 0, math.radians(-72)))
key(rig.pose.bones['restraint_r'], 42, rotation=(0, 0, math.radians(72)))
key(rig.pose.bones['suit_root'], 0)
key(rig.pose.bones['suit_root'], 150, location=(0, -.78, .02))

# 02: feet/legs, torso, arms/gloves, then neck seal and helmet.
new_action('A_Suit_02_Don', 390)
for name in ('suit_leg_l','suit_leg_r','suit_torso','suit_arm_l','suit_arm_r','neck_seal_ctrl','helmet_ctrl'):
    key(rig.pose.bones[name], 0, location=(0, -.78, 0))
for name, frame in [('suit_leg_l',70),('suit_leg_r',90),('suit_torso',165),('suit_arm_l',215),('suit_arm_r',250),('neck_seal_ctrl',300),('helmet_ctrl',365)]:
    key(rig.pose.bones[name], frame, location=(0, 0, 0))
key(rig.pose.bones['head'], 285, rotation=(math.radians(-8),0,0)); key(rig.pose.bones['head'], 390)

# 03: helmet and neck seal first, then arms, torso, and legs clear the body.
new_action('A_Suit_03_Doff', 360)
for name in ('helmet_ctrl','neck_seal_ctrl','suit_arm_r','suit_arm_l','suit_torso','suit_leg_r','suit_leg_l'):
    key(rig.pose.bones[name], 0)
for name, frame in [('helmet_ctrl',65),('neck_seal_ctrl',90),('suit_arm_r',155),('suit_arm_l',180),('suit_torso',235),('suit_leg_r',305),('suit_leg_l',340)]:
    key(rig.pose.bones[name], frame, location=(0, -.78, 0))

# 04: removed assembly enters the recess; restraint arms close only after seating.
new_action('A_Suit_04_Stow', 180)
key(rig.pose.bones['suit_root'], 0, location=(0, -.78, .02)); key(rig.pose.bones['suit_root'], 135)
key(rig.pose.bones['restraint_l'], 0, rotation=(0,0,math.radians(-72)))
key(rig.pose.bones['restraint_r'], 0, rotation=(0,0,math.radians(72)))
key(rig.pose.bones['restraint_l'], 180); key(rig.pose.bones['restraint_r'], 180)

rig['rig_contract_version'] = 1
rig['clips'] = 'A_Suit_01_Extract,A_Suit_02_Don,A_Suit_03_Doff,A_Suit_04_Stow'
rig['helmet_socket'] = 'helmet_ctrl'
rig['left_hand_ik'] = 'hand_ik_l'
rig['right_hand_ik'] = 'hand_ik_r'

os.makedirs(OUT_DIR, exist_ok=True)
bpy.context.scene.render.fps = 30
bpy.context.scene.frame_start = 0
bpy.context.scene.frame_end = 390
bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
bpy.ops.object.select_all(action='DESELECT')
rig.select_set(True)
for obj in bpy.context.scene.objects:
    if obj.parent == rig: obj.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.export_scene.fbx(
    filepath=FBX_PATH, use_selection=True, object_types={'ARMATURE','MESH'},
    add_leaf_bones=False, bake_anim=True, bake_anim_use_all_actions=True,
    bake_anim_simplify_factor=0.0, axis_forward='-Y', axis_up='Z', apply_unit_scale=True)
print(f'WROTE {BLEND_PATH}')
print(f'WROTE {FBX_PATH}')
