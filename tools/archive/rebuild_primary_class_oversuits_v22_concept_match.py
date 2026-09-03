"""Rebuild the four primary oversuits from the concept-matched production master.

V22 deliberately abandons the procedural V16-V21 mannequin.  It extracts the
visible class variants from PlayerSuit_Master, removes wearer/undersuit meshes,
recenters the suit, restores a production skeleton, and exports a standalone
skeletal garment whose silhouette follows the approved realistic role lineup.

Run with Blender:
  blender --background --python tools/rebuild_primary_class_oversuits_v22_concept_match.py -- <project-root>
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
MASTER = SUIT_DIR / "PlayerSuit_Master.blend"
SOURCE_FBX = ROOT / "Build" / "Unreal" / "PlayerSuits" / "FBX"
OUT_DIR = SUIT_DIR / "PrimaryOversuits"
PREVIEW_DIR = OUT_DIR / "Previews_v22"
EXPORT_DIR = ROOT / "Build" / "Unreal" / "PlayerSuits" / "PrimaryOversuits_v22"
MANIFEST = OUT_DIR / "PrimaryOversuits_v22_Manifest.json"


CLASSES = {
    "Marine": {"role": "Security", "code": "MAR", "source": "SM_PlayerSuit_Security.fbx"},
    "Scientist": {"role": "Crew", "code": "SCI", "source": "SM_PlayerSuit_Crew.fbx"},
    "Technician": {"role": "Engineering", "code": "TEC", "source": "SM_PlayerSuit_Engineering.fbx"},
    "Medical": {"role": "Medical", "code": "MED", "source": "SM_PlayerSuit_Medical.fbx"},
}


# These were intentionally hidden in the source master before FBX export. FBX
# does not preserve Blender's render visibility, so they must be removed here.
HIDDEN_SOURCE_SUFFIXES = {
    "Boot_L", "Boot_R", "Calf_L", "Calf_R", "Forearm_L", "Forearm_R",
    "Thigh_L", "Thigh_R", "Undersuit_Head", "Undersuit_Pelvis",
    "Undersuit_Torso", "UpperArm_L", "UpperArm_R", "Visor",
}

WEARER_TOKENS = (
    "_Face", "_Eye", "Eyelid", "EyeWhite", "Pupil", "Hair", "_Mouth",
    "_Nose", "_Chin", "_Ear", "_Cheek", "_Brow", "Undersuit",
)


def descendants(root):
    result = []
    stack = list(root.children)
    while stack:
        obj = stack.pop()
        result.append(obj)
        stack.extend(obj.children)
    return result


def remove_object(obj):
    bpy.data.objects.remove(obj, do_unlink=True)


def append_armature():
    with bpy.data.libraries.load(str(MASTER), link=False) as (source, target):
        if "SK_PlayerSuit_Production" not in source.objects:
            raise RuntimeError("Production suit armature missing from master")
        target.objects = ["SK_PlayerSuit_Production"]
    rig = target.objects[0]
    bpy.context.scene.collection.objects.link(rig)
    rig.name = "SK_PrimaryOversuit_v22"
    rig.data.name = "SK_PrimaryOversuit_v22_Skeleton"
    rig.location.y = -430.0
    rig["asset_layer"] = "oversuit"
    rig["wearer_independent"] = True
    rig["concept_match_pass"] = 22
    rig["unreal_skeleton_contract"] = "SKM_Manny-compatible suit garment"
    return rig


def side_from(obj):
    name = obj.name.lower()
    if any(token in name for token in ("_l", "left", "_-", "-12", "-40")):
        return "l"
    if any(token in name for token in ("_r", "right", "_12", "_40")):
        return "r"
    return "l" if obj.matrix_world.translation.y > 0 else "r"


def bone_for(obj):
    name = obj.name.lower()
    side = side_from(obj)
    if any(token in name for token in ("helmet", "visor", "comms", "crown", "hud")):
        return "head"
    if any(token in name for token in ("collar", "neckseal", "pressurecollar")):
        return "neck_01"
    if any(token in name for token in ("finger", "glove", "hand_", "palm", "knuckle")):
        return f"hand_{side}"
    if any(token in name for token in ("forearm", "elbow", "wrist")):
        return f"lowerarm_{side}"
    if any(token in name for token in ("upperarm", "shoulder")):
        return f"upperarm_{side}"
    if any(token in name for token in ("boot", "ankle", "tread", "sole", "foot")):
        return f"foot_{side}"
    if any(token in name for token in ("knee", "shin", "calf")):
        return f"calf_{side}"
    if any(token in name for token in ("thigh",)):
        return f"thigh_{side}"
    if any(token in name for token in ("belt", "pelvis", "hip", "quickrelease")):
        return "pelvis"
    if any(token in name for token in ("pack", "backpack", "tank", "oxygen", "drone", "toolarm")):
        return "spine_03"
    return "spine_03" if obj.matrix_world.translation.z > 104 else "spine_02"


def bind_mesh(obj, rig, bone):
    world = obj.matrix_world.copy()
    obj.parent = None
    obj.matrix_world = world
    for modifier in list(obj.modifiers):
        if modifier.type == "ARMATURE":
            obj.modifiers.remove(modifier)
    for group in list(obj.vertex_groups):
        obj.vertex_groups.remove(group)
    group = obj.vertex_groups.new(name=bone)
    group.add(range(len(obj.data.vertices)), 1.0, "REPLACE")
    modifier = obj.modifiers.new("V22_ProductionSkeleton", "ARMATURE")
    modifier.object = rig
    obj["rig_attachment"] = bone


def recenter_meshes(meshes):
    corners = [obj.matrix_world @ Vector(corner) for obj in meshes for corner in obj.bound_box]
    center_x = (min(p.x for p in corners) + max(p.x for p in corners)) * .5
    center_y = (min(p.y for p in corners) + max(p.y for p in corners)) * .5
    floor_z = min(p.z for p in corners)
    offset = Vector((-center_x, -center_y, -floor_z))
    for obj in meshes:
        matrix = obj.matrix_world.copy()
        matrix.translation += offset
        obj.matrix_world = matrix
    return offset


def join_rigid_groups(meshes, class_name, code):
    joined = []
    by_bone = {}
    for obj in meshes:
        by_bone.setdefault(obj.get("rig_attachment", "spine_03"), []).append(obj)
    for bone, group in by_bone.items():
        bpy.ops.object.select_all(action="DESELECT")
        for obj in group:
            obj.select_set(True)
        active = group[0]
        bpy.context.view_layer.objects.active = active
        if len(group) > 1:
            bpy.ops.object.join()
        active = bpy.context.object
        active.name = f"SK_OVR22_{code}_{bone}"
        active["asset_layer"] = "oversuit"
        active["oversuit_class"] = class_name
        active["wearer_independent"] = True
        active["concept_match_pass"] = 22
        active["rig_attachment"] = bone
        active["joined_source_part_count"] = len(group)
        joined.append(active)
    return joined


def convert_curve(obj):
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    return bpy.context.object


def add_interface(name, position, rig, bone, stage):
    empty = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(empty)
    empty.empty_display_type = "CIRCLE"
    empty.empty_display_size = 2.5
    empty.location = position
    empty.parent = rig
    empty.parent_type = "BONE"
    empty.parent_bone = bone
    empty["asset_layer"] = "oversuit_interface"
    empty["donning_stage"] = stage
    empty["wearer_independent"] = True
    return empty


def add_interfaces(code, rig):
    specs = (
        ("Helmet", (15, 0, 151), "head", 80),
        ("Collar", (0, 0, 131), "neck_01", 70),
        ("Backpack", (-25, 0, 109), "spine_03", 60),
        ("Wrist_L", (2, 42, 72), "hand_l", 40),
        ("Wrist_R", (2, -42, 72), "hand_r", 40),
        ("Waist", (0, 0, 76), "pelvis", 50),
        ("Boot_L", (3, 12, 9), "foot_l", 20),
        ("Boot_R", (3, -12, 9), "foot_r", 20),
    )
    return [add_interface(f"IF_OVR22_{code}_{label}", position, rig, bone, stage)
            for label, position, bone, stage in specs]


def material_cleanup():
    for mat in bpy.data.materials:
        lowered = mat.name.lower()
        if any(token in lowered for token in ("skin", "eye", "hair", "mouth")):
            continue
        mat["oversuit_material"] = True
        mat["concept_match_pass"] = 22
        if "role_" in lowered:
            bsdf = mat.node_tree.nodes.get("Principled BSDF") if mat.use_nodes else None
            if bsdf:
                # Keep role colors as identification, not toy-like primary blocks.
                color = bsdf.inputs["Base Color"].default_value
                color[0] *= .72
                color[1] *= .72
                color[2] *= .72
                bsdf.inputs["Roughness"].default_value = max(.42, bsdf.inputs["Roughness"].default_value)


def setup_render():
    scene = bpy.context.scene
    for obj in list(bpy.data.objects):
        if obj.type in {"CAMERA", "LIGHT"}:
            remove_object(obj)
    world = scene.world or bpy.data.worlds.new("V22_StudioWorld")
    scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (.018, .022, .028, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = .55

    bpy.ops.mesh.primitive_plane_add(size=700, location=(0, 0, 0))
    floor = bpy.context.object
    floor.name = "PREVIEW_Floor"
    floor_mat = bpy.data.materials.new("PREVIEW_FloorMat")
    floor_mat.diffuse_color = (.035, .042, .050, 1)
    floor.data.materials.append(floor_mat)

    for name, location, energy, size, color in (
        ("Key", (250, -190, 230), 2_000_000, 130, (1.0, .82, .68)),
        ("Fill", (150, 210, 145), 1_150_000, 110, (.55, .72, 1.0)),
        ("Rim", (-150, -80, 210), 1_600_000, 90, (.35, .58, 1.0)),
    ):
        data = bpy.data.lights.new(name, "AREA")
        data.energy, data.shape, data.size, data.color = energy, "DISK", size, color
        obj = bpy.data.objects.new(name, data)
        bpy.context.scene.collection.objects.link(obj)
        obj.location = location
        direction = Vector((0, 0, 92)) - obj.location
        obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    camera_data = bpy.data.cameras.new("V22_Camera")
    camera = bpy.data.objects.new("V22_Camera", camera_data)
    bpy.context.scene.collection.objects.link(camera)
    camera_data.lens = 58
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 1100
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = .7
    return camera


def point_camera(camera, location, target=(0, 0, 87)):
    camera.location = location
    camera.rotation_euler = (Vector(target) - camera.location).to_track_quat("-Z", "Y").to_euler()


def export_fbx(path, rig, meshes, interfaces):
    bpy.ops.object.select_all(action="DESELECT")
    rig.select_set(True)
    for obj in meshes + interfaces:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True, object_types={"ARMATURE", "MESH", "EMPTY"},
        add_leaf_bones=False, apply_scale_options="FBX_SCALE_ALL", bake_anim=False,
        mesh_smooth_type="FACE", use_mesh_modifiers=True, axis_forward="-Y", axis_up="Z",
    )


def build_class(class_name, spec):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    source = SOURCE_FBX / spec["source"]
    bpy.ops.import_scene.fbx(filepath=str(source), use_anim=False)
    role = spec["role"]
    role_root = bpy.data.objects.get(f"VARIANT_{role}_Root")
    if not role_root:
        raise RuntimeError(f"Missing {role} variant root in {source}")
    role_root.location.y = -430.0
    candidates = descendants(role_root)
    removed = []
    kept = []
    prefix = role.upper() + "_"
    for obj in candidates:
        suffix = obj.name[len(prefix):] if obj.name.startswith(prefix) else obj.name
        forbidden = suffix in HIDDEN_SOURCE_SUFFIXES or any(token in obj.name for token in WEARER_TOKENS)
        if forbidden:
            removed.append(obj.name)
        else:
            kept.append(obj)

    keep_set = set(kept + [role_root])
    for obj in list(bpy.data.objects):
        if obj not in keep_set:
            remove_object(obj)
    for obj in list(kept):
        if obj.type == "CURVE":
            replacement = convert_curve(obj)
            kept[kept.index(obj)] = replacement

    # Detach from the translated variant root while preserving the centered world transform.
    for obj in kept:
        world = obj.matrix_world.copy()
        obj.parent = None
        obj.matrix_world = world
    remove_object(role_root)

    meshes = [obj for obj in kept if obj.type == "MESH"]
    center_offset = recenter_meshes(meshes)
    rig = append_armature()
    for index, obj in enumerate(meshes):
        original = obj.name
        obj.name = f"OVR22_{spec['code']}_{index:03}_{original.replace(role.upper() + '_', '')}"
        bone = bone_for(obj)
        bind_mesh(obj, rig, bone)
        obj["asset_layer"] = "oversuit"
        obj["oversuit_class"] = class_name
        obj["role_alias"] = role
        obj["wearer_independent"] = True
        obj["concept_match_pass"] = 22
        obj["concept_reference"] = "docs/concept-art/reference/suits/player-suit-role-lineup.png"
        obj["construction_reference"] = "docs/concept-art/reference/suits/standard-suit-turnaround.png"
        obj["unreal_export"] = True
    for obj in kept:
        if obj.type not in {"MESH", "EMPTY"}:
            remove_object(obj)

    meshes = join_rigid_groups(meshes, class_name, spec["code"])
    interfaces = add_interfaces(spec["code"], rig)
    material_cleanup()
    rig["oversuit_class"] = class_name
    rig["role_alias"] = role
    rig["removed_wearer_objects"] = len(removed)
    rig["source_visible_outer_parts"] = len(meshes)
    rig["source_center_offset"] = tuple(center_offset)
    rig["concept_reference"] = "docs/concept-art/reference/suits/player-suit-role-lineup.png"
    rig["construction_reference"] = "docs/concept-art/reference/suits/standard-suit-turnaround.png"

    camera = setup_render()
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    views = {
        "Front": ((340, 0, 98), (0, 0, 86)),
        "ThreeQuarter": ((285, -210, 108), (0, 0, 86)),
        "Rear": ((-340, 0, 100), (-4, 0, 88)),
        "Profile": ((0, -355, 100), (0, 0, 87)),
    }
    previews = {}
    for label, (location, target) in views.items():
        point_camera(camera, location, target)
        path = PREVIEW_DIR / f"PlayerOversuit_{class_name}_v22_{label}.png"
        bpy.context.scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True)
        previews[label] = str(path.relative_to(ROOT)).replace("\\", "/")

    # Preview-only objects never belong in the authored/exported asset.
    for obj in list(bpy.data.objects):
        if obj.name.startswith("PREVIEW_") or obj.type in {"CAMERA", "LIGHT"}:
            remove_object(obj)
    blend = OUT_DIR / f"PlayerOversuit_{class_name}_v22.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    fbx = EXPORT_DIR / f"SKM_PlayerOversuit_{class_name}_v22.fbx"
    export_fbx(fbx, rig, meshes, interfaces)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    return {
        "class": class_name, "role_alias": role,
        "source": str(source.relative_to(ROOT)).replace("\\", "/"),
        "blend": str(blend.relative_to(ROOT)).replace("\\", "/"),
        "fbx": str(fbx.relative_to(ROOT)).replace("\\", "/"),
        "mesh_count": len(meshes), "removed_wearer_objects": len(removed),
        "interface_count": len(interfaces), "previews": previews,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    entries = [build_class(name, spec) for name, spec in CLASSES.items()]
    payload = {
        "schema": 1, "asset": "PrimaryOversuits_v22", "status": "concept_match_rebuild",
        "supersedes": "PrimaryOversuits_v21",
        "references": [
            "docs/concept-art/reference/suits/player-suit-role-lineup.png",
            "docs/concept-art/reference/suits/standard-suit-turnaround.png",
        ],
        "design_direction": "realistic near-future textile pressure suit with restrained hard points",
        "classes": entries,
    }
    MANIFEST.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"PRIMARY_OVERSUITS_V22 classes={len(entries)} {MANIFEST}")


if __name__ == "__main__":
    main()
