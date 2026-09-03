"""V19 dedicated smooth-shell replacement pass for primary class oversuits.

Removes the remaining jagged V11 masked torso/limb regions and replaces them
with purpose-built pressure-envelope and armor meshes. The V11 boots are kept.

Run with Blender:
  blender --background --python tools/refine_primary_class_oversuits_v19.py -- <project-root>
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_primary_class_oversuits as v16
import refine_primary_class_oversuits_v18 as v18


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
ASSET_DIR = ROOT / "Art" / "Characters" / "PlayerSuits" / "PrimaryOversuits"
PREVIEW_DIR = ASSET_DIR / "Previews_v19"
EXPORT_DIR = ROOT / "Build" / "Unreal" / "PlayerSuits" / "PrimaryOversuits_v19"
MANIFEST = ASSET_DIR / "PrimaryOversuits_v19_Manifest.json"
REMOVE_V11 = ("SKV11_Chest", "SKV11_Forearm", "SKV11_Knee", "SKV11_Shin",
              "SKV11_Shoulder", "SKV11_Thigh")


def mats_for(class_name, spec):
    return v18.materials(class_name, spec)


def mark(obj, boundary, stage):
    obj["oversuit_pass"] = 19
    obj["v19_dedicated_shell"] = True
    obj["pressure_boundary"] = boundary
    obj["donning_stage"] = stage
    return obj


def capsule(name, location, scale, collection, mat, class_name, module, rig,
            bone="chest", stage=50, boundary="flexible_pressure_envelope"):
    obj = v18.capsule(name, location, scale, collection, mat, class_name, module,
                      rig, bone, stage)
    return mark(obj, boundary, stage)


def panel(name, center, width_top, width_bottom, height, depth, bulge,
          collection, mat, class_name, module, rig, bone, stage, bevel=.008):
    obj = v18.bulged_panel(name, center, width_top, width_bottom, height, depth, bulge,
                           collection, mat, class_name, module, rig, bone, stage,
                           facing=-1, segments=12, bevel=bevel)
    return mark(obj, "external_hard_shell", stage)


def ring(name, location, major, minor, collection, mat, class_name, module,
         rig, bone, stage):
    obj = v16.torus(name, location, major, minor, collection, mat, class_name,
                    module, rig, bone)
    return mark(obj, "articulation_pressure_cuff", stage)


def remove_masked_regions():
    removed = []
    for obj in list(bpy.data.objects):
        if any(obj.name.startswith(token) for token in REMOVE_V11):
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    return removed


def add_torso(class_name, spec, collection, rig, mats):
    p = f"OVR19_{spec['code']}"
    return [
        capsule(f"{p}_SmoothUpperTorso", (0, 0, 1.285), (.215, .125, .215),
                collection, mats["composite"], class_name, "smooth_upper_pressure_torso",
                rig, "chest", 50),
        capsule(f"{p}_SmoothAbdomen", (0, 0, 1.055), (.177, .110, .185),
                collection, mats["gasket"], class_name, "smooth_abdominal_pressure_torso",
                rig, "spine_02", 50),
        capsule(f"{p}_PelvisPressureBridge", (0, 0, .865), (.155, .102, .115),
                collection, mats["composite"], class_name, "pelvis_pressure_bridge",
                rig, "pelvis", 30),
    ]


def add_limb(class_name, spec, collection, rig, mats, side):
    p = f"OVR19_{spec['code']}"
    label = "L" if side < 0 else "R"
    limb = label.lower()
    x_arm = side * .350
    x_leg = side * .128
    parts = [
        capsule(f"{p}_ForearmGauntlet_{label}", (x_arm, -.015, 1.105),
                (.064, .066, .145), collection, mats["composite"], class_name,
                "smooth_forearm_gauntlet", rig, f"lowerarm_{limb}", 40),
        panel(f"{p}_ForearmArmor_{label}", (x_arm, -.070, 1.115), .090, .082,
              .205, .025, .012, collection, mats["armor"], class_name,
              "curved_forearm_armor", rig, f"lowerarm_{limb}", 40, .007),
        capsule(f"{p}_GloveShell_{label}", (side*.382, -.035, .965),
                (.076, .092, .072), collection, mats["composite"], class_name,
                "sealed_glove_shell", rig, f"hand_{limb}", 40),
        capsule(f"{p}_GloveKnuckle_{label}", (side*.382, -.112, .980),
                (.060, .025, .038), collection, mats["armor"], class_name,
                "rounded_glove_knuckle", rig, f"hand_{limb}", 40,
                "external_hard_shell"),
        ring(f"{p}_WristPressureCuff_{label}", (x_arm, -.015, .990), .058, .009,
             collection, mats["gasket"], class_name, "wrist_pressure_cuff", rig,
             f"hand_{limb}", 40),
        capsule(f"{p}_ThighGaiter_{label}", (x_leg, 0, .720),
                (.088, .074, .190), collection, mats["composite"], class_name,
                "smooth_thigh_pressure_gaiter", rig, f"thigh_{limb}", 30),
        capsule(f"{p}_KneeBellows_{label}", (x_leg, -.005, .525),
                (.074, .064, .075), collection, mats["gasket"], class_name,
                "knee_pressure_bellows", rig, f"calf_{limb}", 20),
        capsule(f"{p}_KneePad_{label}", (x_leg, -.070, .530),
                (.070, .030, .068), collection, mats["armor"], class_name,
                "rounded_knee_pad", rig, f"calf_{limb}", 20,
                "external_hard_shell"),
        capsule(f"{p}_ShinGaiter_{label}", (x_leg, 0, .355),
                (.073, .062, .168), collection, mats["composite"], class_name,
                "smooth_shin_pressure_gaiter", rig, f"calf_{limb}", 20),
        panel(f"{p}_ShinArmorPlate_{label}", (x_leg, -.060, .365), .125, .105,
              .245, .022, .010, collection, mats["armor"], class_name,
              "curved_shin_armor", rig, f"calf_{limb}", 20, .008),
    ]
    # A small color insert gives class readability without rebuilding the limb
    # silhouette around a rectangular stripe.
    parts.append(capsule(f"{p}_KneeStatusInset_{label}", (x_leg, -.101, .535),
                         (.028, .007, .012), collection, mats["accent"], class_name,
                         "knee_status_insert", rig, f"calf_{limb}", 20,
                         "external_identity_insert"))
    return parts


def refine_retained_boots(class_name):
    retained = []
    for obj in bpy.data.objects:
        if not obj.name.startswith("SKV11_Boot_"):
            continue
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        bevels = [modifier for modifier in obj.modifiers if modifier.type == "BEVEL"]
        bevel = bevels[0] if bevels else obj.modifiers.new("V19_BootEdgeFinish", "BEVEL")
        bevel.width = max(bevel.width, .006)
        bevel.segments = max(bevel.segments, 4)
        obj["oversuit_pass"] = 19
        obj["v19_retained_boot_shell"] = True
        obj["oversuit_class"] = class_name
        retained.append(obj.name)
    return retained


def render(class_name, meshes):
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    bpy.context.window.scene = scene
    camera = bpy.data.objects["CAM_HighPolyReview"]
    scene.camera = camera
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = .20
    target = Vector((0, 0, .98))
    for obj in meshes:
        obj.hide_render = False
    for label, position in {
        "Front": Vector((0, -4.0, 1.02)),
        "ThreeQuarter": Vector((2.8, -2.8, 1.06)),
        "Rear": Vector((0, 4.0, 1.02)),
        "RearThreeQuarter": Vector((-2.8, 2.8, 1.06)),
    }.items():
        camera.location = position
        camera.data.lens = 68
        camera.rotation_euler = (target-position).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(PREVIEW_DIR / f"PlayerOversuit_{class_name}_v19_{label}.png")
        bpy.ops.render.render(write_still=True)


def export(class_name, rig, meshes, interfaces):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / f"SKM_PlayerOversuit_{class_name}_v19.fbx"
    bpy.ops.object.select_all(action="DESELECT")
    for obj in [rig, *meshes, *interfaces]:
        obj.hide_set(False)
        obj.hide_viewport = False
        obj.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True,
        object_types={"ARMATURE", "MESH", "EMPTY"}, global_scale=1.0,
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="-Z", axis_up="Y", use_mesh_modifiers=True,
        mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False,
        path_mode="RELATIVE", embed_textures=False,
    )
    return path


def build_class(class_name, spec):
    source = ASSET_DIR / f"PlayerOversuit_{class_name}_v18.blend"
    bpy.ops.wm.open_mainfile(filepath=str(source))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects[f"RIG_PlayerOversuit_{class_name}_v18"]
    rig.name = f"RIG_PlayerOversuit_{class_name}_v19"
    removed = remove_masked_regions()
    collection = bpy.data.collections.new(f"OVERSUIT_{class_name.upper()}_V19_SMOOTH_SHELLS")
    bpy.context.scene.collection.children.link(collection)
    mats = mats_for(class_name, spec)
    torso = add_torso(class_name, spec, collection, rig, mats)
    limbs = [*add_limb(class_name, spec, collection, rig, mats, -1),
             *add_limb(class_name, spec, collection, rig, mats, 1)]
    retained_boots = refine_retained_boots(class_name)
    meshes = [obj for obj in bpy.data.objects
              if obj.type == "MESH" and obj.get("asset_layer") == "oversuit"]
    interfaces = [obj for obj in bpy.data.objects if obj.get("asset_layer") == "oversuit_interface"]
    for obj in meshes:
        obj["oversuit_pass"] = 19
    rig["asset_status"] = "PRIMARY_CLASS_OVERSUIT_V19_SMOOTH_SHELL_REVIEW"
    rig["oversuit_pass"] = 19
    rig["v19_removed_masked_regions"] = len(removed)
    rig["v19_dedicated_shell_count"] = len(torso) + len(limbs)
    rig["v19_retained_boot_count"] = len(retained_boots)
    rig["mesh_count"] = len(meshes)
    rig["wearer_independent"] = True
    bpy.context.scene["asset_status"] = "PRIMARY_CLASS_OVERSUIT_V19_SMOOTH_SHELL_REVIEW"
    bpy.context.scene["contains_player_body"] = False
    bpy.context.scene["contains_undersuit"] = False

    output = ASSET_DIR / f"PlayerOversuit_{class_name}_v19.blend"
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
    render(class_name, meshes)
    fbx = export(class_name, rig, meshes, interfaces)
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
    return {
        "gameplay_class": class_name,
        "profile_role_alias": spec["role_alias"],
        "blend": str(output.relative_to(ROOT)).replace("\\", "/"),
        "fbx": str(fbx.relative_to(ROOT)).replace("\\", "/"),
        "mesh_count": len(meshes),
        "removed_v11_regions": removed,
        "dedicated_smooth_shell_count": len(torso) + len(limbs),
        "retained_v11_boots": retained_boots,
        "previews": {
            view: str((PREVIEW_DIR / f"PlayerOversuit_{class_name}_v19_{view}.png")
                      .relative_to(ROOT)).replace("\\", "/")
            for view in ("Front", "ThreeQuarter", "Rear", "RearThreeQuarter")
        },
    }


def main():
    variants = {name: build_class(name, spec) for name, spec in v16.CLASS_SPECS.items()}
    MANIFEST.write_text(json.dumps({
        "schema": 1, "version": 19, "status": "dedicated_smooth_shell_review",
        "source_version": 18,
        "separation_contract": {"contains_player_body": False, "contains_undersuit": False,
                                "wearer_independent": True},
        "replacement_policy": "V11 masked torso and limb regions removed; only V11 boots retained",
        "new_shells": ["smooth upper torso", "smooth abdomen", "pelvis bridge",
                       "forearm gauntlets", "sealed gloves", "thigh gaiters", "knee bellows",
                       "rounded knee pads", "shin gaiters", "curved shin plates"],
        "variants": variants,
        "promotion_gates": ["final shared skeleton", "animated fit", "pressure interface fit",
                            "Unreal skeletal import", "multiplayer equip replication"],
    }, indent=2), encoding="utf-8")
    print("PRIMARY_OVERSUITS_V19", f"classes={len(variants)}", MANIFEST)


if __name__ == "__main__":
    main()
