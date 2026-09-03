"""Refine V16 standalone class oversuits into V17 production-review assets.

V17 strengthens suit continuity and authored construction without importing a
player or undersuit. It also declares explicit don/doff interfaces for the later
runtime equipment integration.

Run with Blender:
  blender --background --python tools/refine_primary_class_oversuits_v17.py -- <project-root>
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


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
ASSET_DIR = ROOT / "Art" / "Characters" / "PlayerSuits" / "PrimaryOversuits"
PREVIEW_DIR = ASSET_DIR / "Previews_v17"
EXPORT_DIR = ROOT / "Build" / "Unreal" / "PlayerSuits" / "PrimaryOversuits_v17"
MANIFEST = ASSET_DIR / "PrimaryOversuits_v17_Manifest.json"
FIT_REFERENCE = "Art/Characters/PlayerSuits/PlayerCharacter_CryoBodysuit_Concept_v28.blend"


def mats_for(class_name, spec):
    defaults = {
        "Accent": (spec["accent"], .28, .30, None),
        "Secondary": (spec["secondary"], .12, .42, None),
        "Armor": ((.43, .46, .45), .18, .30, None),
        "Composite": ((.025, .032, .036), .08, .68, None),
        "ServiceMetal": ((.075, .085, .090), .72, .24, None),
        "Status": (spec["accent"], .10, .20,
                   tuple(min(1.0, value*1.35+.08) for value in spec["accent"])),
    }

    def get(suffix):
        mat = bpy.data.materials.get(f"M_OVR16_{class_name}_{suffix}")
        if not mat:
            color, metallic, roughness, emission = defaults[suffix]
            mat = v16.material(f"M_OVR17_{class_name}_{suffix}", color, metallic,
                               roughness, emission)
        return mat
    return {
        "accent": get("Accent"),
        "secondary": get("Secondary"),
        "armor": get("Armor"),
        "composite": get("Composite"),
        "metal": get("ServiceMetal"),
        "emissive": get("Status"),
        "gasket": v16.material(f"M_OVR17_{class_name}_PressureGasket", (.018, .024, .027),
                               .02, .82),
    }


def rb(name, loc, scale, collection, mat, class_name, module, rig, bone="chest",
       rotation=(0, 0, 0), bevel=.006):
    return v16.rounded_box(name, loc, scale, collection, mat, class_name, module, rig,
                           bone, rotation, bevel)


def cy(name, loc, radius, depth, collection, mat, class_name, module, rig,
       bone="chest", rotation=(0, 0, 0), vertices=32):
    return v16.cylinder(name, loc, radius, depth, collection, mat, class_name, module,
                        rig, bone, rotation, vertices)


def sp(name, loc, scale, collection, mat, class_name, module, rig, bone="chest"):
    return v16.sphere(name, loc, scale, collection, mat, class_name, module, rig, bone)


def tr(name, loc, major, minor, collection, mat, class_name, module, rig,
       bone="chest", rotation=(0, 0, 0)):
    return v16.torus(name, loc, major, minor, collection, mat, class_name, module,
                     rig, bone, rotation)


def tb(name, start, end, radius, collection, mat, class_name, module, rig, bone="chest"):
    return v16.tube_between(name, start, end, radius, collection, mat, class_name,
                            module, rig, bone)


def mark_part(obj, stage, interface=None):
    obj["oversuit_pass"] = 17
    obj["donning_stage"] = stage
    obj["pressure_boundary"] = interface or "external_nonpressure_module"
    return obj


def add_interface(name, location, collection, class_name, rig, bone, stage, lock_type):
    obj = bpy.data.objects.new(name, None)
    collection.objects.link(obj)
    obj.location = location
    obj.empty_display_type = "CUBE"
    obj.empty_display_size = .025
    obj["asset_layer"] = "oversuit_interface"
    obj["oversuit_class"] = class_name
    obj["interface_type"] = lock_type
    obj["donning_stage"] = stage
    obj["unreal_socket"] = True
    obj["wearer_independent"] = True
    v16.bone_parent(obj, rig, bone)
    return obj


def tag_inherited_parts(class_name):
    stages = {
        "Boot": 10, "Shin": 20, "Knee": 20, "Thigh": 30,
        "Forearm": 40, "Shoulder": 40, "Chest": 50,
        "LifeSupport": 50, "Backpack": 50, "Canister": 50,
        "Neck": 60, "Helmet": 70,
    }
    for obj in bpy.data.objects:
        if obj.type != "MESH" or obj.get("asset_layer") != "oversuit":
            continue
        stage = next((value for token, value in stages.items() if token in obj.name), 50)
        obj["oversuit_pass"] = 17
        obj["donning_stage"] = stage
        obj["pressure_boundary"] = "shared_pressure_envelope" if obj.name.startswith("SKV") else \
            "external_nonpressure_module"
        obj["oversuit_class"] = class_name


def add_shared_construction(class_name, spec, collection, rig, mats):
    p = f"OVR17_{spec['code']}"
    parts = []
    # Continuous waist yoke closes the largest visual gap in V16 while remaining
    # four discrete service pieces around the pelvis.
    parts += [
        mark_part(rb(f"{p}_WaistYokeFront", (0, -.125, .925), (.160, .024, .038),
                     collection, mats["composite"], class_name, "waist_pressure_yoke", rig,
                     "pelvis", bevel=.010), 30, "waist_lock"),
        mark_part(rb(f"{p}_WaistYokeRear", (0, .115, .925), (.160, .024, .038),
                     collection, mats["metal"], class_name, "rear_entry_yoke", rig,
                     "pelvis", bevel=.010), 30, "waist_lock"),
    ]
    for side in (-1, 1):
        label = "L" if side < 0 else "R"
        limb = label.lower()
        parts += [
            mark_part(rb(f"{p}_HipYoke_{label}", (side*.178, 0, .900),
                         (.035, .090, .080), collection, mats["armor"], class_name,
                         "hip_yoke", rig, "pelvis", bevel=.014), 30, "waist_lock"),
            mark_part(sp(f"{p}_UnderarmPressureBellows_{label}",
                         (side*.205, -.005, 1.285), (.075, .067, .115),
                         collection, mats["gasket"], class_name,
                         "underarm_pressure_bellows", rig, f"upperarm_{limb}"), 40,
                      "arm_lock"),
            mark_part(sp(f"{p}_UpperArmShell_{label}", (side*.270, -.010, 1.270),
                         (.068, .062, .105), collection, mats["secondary"], class_name,
                         "upper_arm_shell", rig, f"upperarm_{limb}"), 40),
            mark_part(tr(f"{p}_ElbowPressureCuff_{label}", (side*.335, -.020, 1.090),
                         .052, .010, collection, mats["gasket"], class_name,
                         "elbow_pressure_cuff", rig, f"lowerarm_{limb}"), 40, "arm_lock"),
            mark_part(tr(f"{p}_AnkleLockRing_{label}", (side*.127, -.020, .190),
                         .067, .010, collection, mats["gasket"], class_name,
                         "ankle_lock_ring", rig, f"foot_{limb}"), 10, "boot_lock"),
            mark_part(rb(f"{p}_MagSoleRailA_{label}", (side*.127, -.055, .035),
                         (.060, .085, .010), collection, mats["metal"], class_name,
                         "magnetic_sole_rail", rig, f"foot_{limb}", bevel=.004), 10),
            mark_part(rb(f"{p}_MagSoleRailB_{label}", (side*.127, .055, .035),
                         (.060, .055, .010), collection, mats["accent"], class_name,
                         "magnetic_sole_contact", rig, f"foot_{limb}", bevel=.004), 10),
            mark_part(rb(f"{p}_ChestHarness_{label}", (side*.125, -.168, 1.285),
                         (.018, .012, .125), collection, mats["metal"], class_name,
                         "chest_load_harness", rig, bevel=.005), 50),
        ]
    # Rear entry seam, four over-center latches, and a protected helmet crown rail.
    parts.append(mark_part(rb(f"{p}_RearEntrySpine", (0, .220, 1.255),
                              (.022, .016, .175), collection, mats["metal"], class_name,
                              "rear_entry_spine", rig, bevel=.006), 50, "rear_entry_seal"))
    for index, z in enumerate((1.120, 1.205, 1.290, 1.375)):
        parts.append(mark_part(rb(f"{p}_RearEntryLatch_{index+1}", (0, .242, z),
                                  (.055, .012, .014), collection, mats["accent"], class_name,
                                  "rear_entry_latch", rig, bevel=.004), 50,
                               "rear_entry_seal"))
    parts += [
        mark_part(rb(f"{p}_HelmetCrownRail", (0, -.105, 1.865), (.090, .020, .014),
                     collection, mats["armor"], class_name, "helmet_crown_rail", rig,
                     "head", bevel=.006), 70),
        mark_part(cy(f"{p}_HelmetComms_L", (-.160, -.010, 1.690), .027, .026,
                     collection, mats["metal"], class_name, "helmet_comms", rig, "head",
                     rotation=(0, math.pi/2, 0)), 70),
        mark_part(cy(f"{p}_HelmetComms_R", (.160, -.010, 1.690), .027, .026,
                     collection, mats["metal"], class_name, "helmet_comms", rig, "head",
                     rotation=(0, math.pi/2, 0)), 70),
    ]
    return parts


def refine_marine(class_name, spec, collection, rig, mats):
    p = "OVR17_MAR"
    parts = []
    for side in (-1, 1):
        label = "L" if side < 0 else "R"
        limb = label.lower()
        parts += [
            mark_part(rb(f"{p}_CuirassEdge_{label}", (side*.148, -.218, 1.285),
                         (.012, .010, .110), collection, mats["accent"], class_name,
                         "cuirass_edge_guard", rig, bevel=.004), 50),
            mark_part(rb(f"{p}_ThighHardpoint_{label}", (side*.188, -.125, .755),
                         (.050, .018, .095), collection, mats["metal"], class_name,
                         "thigh_hardpoint", rig, f"thigh_{limb}", bevel=.008), 30),
            mark_part(cy(f"{p}_PauldronRivet_{label}", (side*.268, -.104, 1.375),
                         .010, .008, collection, mats["accent"], class_name,
                         "pauldron_fastener", rig, f"upperarm_{limb}",
                         rotation=(math.pi/2, 0, 0), vertices=20), 40),
        ]
    for index, x in enumerate((-.075, -.025, .025, .075)):
        parts.append(mark_part(rb(f"{p}_BeltCell_{index+1}", (x, -.165, .900),
                                  (.018, .022, .035), collection, mats["composite"], class_name,
                                  "belt_cell", rig, "pelvis", bevel=.005), 30))
    return parts


def refine_scientist(class_name, spec, collection, rig, mats):
    p = "OVR17_SCI"
    parts = []
    # Protective mast cage and cross-braced sample rack make the asymmetry read
    # as deliberate survey equipment rather than floating primitives.
    for side in (-1, 1):
        x = -.120 + side*.062
        parts.append(mark_part(tb(f"{p}_MastCage_{'L' if side < 0 else 'R'}",
                                  (x, .205, 1.635), (x, .205, 1.750), .006,
                                  collection, mats["metal"], class_name, "sensor_mast_cage", rig), 50))
    parts += [
        mark_part(rb(f"{p}_SampleRackTop", (0, -.105, 1.035), (.190, .014, .012),
                     collection, mats["metal"], class_name, "sample_rack", rig,
                     "pelvis", bevel=.004), 30),
        mark_part(rb(f"{p}_SampleRackBottom", (0, -.105, .900), (.190, .014, .012),
                     collection, mats["metal"], class_name, "sample_rack", rig,
                     "pelvis", bevel=.004), 30),
        mark_part(tb(f"{p}_LidarBrace", (.105, .215, 1.365), (.175, .240, 1.420), .008,
                     collection, mats["metal"], class_name, "lidar_brace", rig), 50),
    ]
    for index, x in enumerate((-.025, .005, .035, .065)):
        parts.append(mark_part(cy(f"{p}_InstrumentKey_{index+1}", (x, -.220, 1.265),
                                  .007, .006, collection, mats["accent"], class_name,
                                  "instrument_controls", rig, rotation=(math.pi/2, 0, 0),
                                  vertices=16), 50))
    return parts


def refine_technician(class_name, spec, collection, rig, mats):
    p = "OVR17_TEC"
    parts = []
    # Folded service manipulator proves the dock's volume and reach without
    # making the arm a permanent part of the pressure envelope.
    points = [(-.215, .250, 1.355), (-.285, .235, 1.255), (-.250, .215, 1.125)]
    parts += [
        mark_part(tb(f"{p}_FoldedToolLink_1", points[0], points[1], .020, collection,
                     mats["metal"], class_name, "folded_tool_arm", rig), 50),
        mark_part(tb(f"{p}_FoldedToolLink_2", points[1], points[2], .017, collection,
                     mats["armor"], class_name, "folded_tool_arm", rig), 50),
    ]
    for index, point in enumerate(points):
        parts.append(mark_part(sp(f"{p}_ToolJoint_{index+1}", point, (.032, .032, .032),
                                  collection, mats["accent"], class_name,
                                  "folded_tool_arm_joint", rig), 50))
    for index, z in enumerate((1.175, 1.225, 1.275, 1.325)):
        parts.append(mark_part(rb(f"{p}_PackHeatSink_{index+1}", (.105, .318, z),
                                  (.050, .008, .008), collection, mats["metal"], class_name,
                                  "pack_heat_sink", rig, bevel=.003), 50))
    parts.append(mark_part(tb(f"{p}_PowerConduit", (-.095, .275, 1.235),
                              (-.165, .255, 1.330), .008, collection, mats["accent"],
                              class_name, "power_conduit", rig), 50))
    return parts


def refine_medical(class_name, spec, collection, rig, mats):
    p = "OVR17_MED"
    parts = []
    parts += [
        mark_part(tr(f"{p}_RearRescueHandle", (0, .335, 1.445), .080, .012,
                     collection, mats["accent"], class_name, "casualty_rescue_handle", rig,
                     rotation=(math.pi/2, 0, 0)), 50),
        mark_part(rb(f"{p}_InjectorRackTop", (0, .337, 1.345), (.125, .010, .010),
                     collection, mats["metal"], class_name, "injector_rack", rig,
                     bevel=.004), 50),
        mark_part(rb(f"{p}_InjectorRackBottom", (0, .337, 1.205), (.125, .010, .010),
                     collection, mats["metal"], class_name, "injector_rack", rig,
                     bevel=.004), 50),
        mark_part(rb(f"{p}_ForearmAidPanel", (-.355, -.105, 1.135), (.045, .020, .075),
                     collection, mats["secondary"], class_name, "forearm_aid_panel", rig,
                     "lowerarm_l", bevel=.009), 40),
    ]
    for side in (-1, 1):
        label = "L" if side < 0 else "R"
        limb = label.lower()
        parts.append(mark_part(cy(f"{p}_TriageBeacon_{label}", (side*.250, -.115, 1.430),
                                  .018, .045, collection, mats["emissive"], class_name,
                                  "triage_beacon", rig, f"upperarm_{limb}"), 40))
    for index, x in enumerate((-.060, -.020, .020, .060)):
        parts.append(mark_part(rb(f"{p}_TelemetryTick_{index+1}", (x, -.222, 1.275),
                                  (.007, .004, .022+index*.004), collection, mats["accent"],
                                  class_name, "telemetry_tick", rig, bevel=.002), 50))
    return parts


REFINERS = {
    "Marine": refine_marine,
    "Scientist": refine_scientist,
    "Technician": refine_technician,
    "Medical": refine_medical,
}


def add_interfaces(class_name, spec, collection, rig):
    p = f"IF_OVR17_{spec['code']}"
    return [
        add_interface(f"{p}_NeckSeal", (0, 0, 1.505), collection, class_name, rig,
                      "head", 60, "pressure_neck_seal"),
        add_interface(f"{p}_ChestLock", (0, -.165, 1.300), collection, class_name, rig,
                      "chest", 50, "rear_entry_chest_lock"),
        add_interface(f"{p}_WaistLock", (0, -.125, .925), collection, class_name, rig,
                      "pelvis", 30, "circumferential_waist_lock"),
        add_interface(f"{p}_Wrist_L", (-.365, -.020, 1.015), collection, class_name, rig,
                      "hand_l", 40, "wrist_pressure_lock"),
        add_interface(f"{p}_Wrist_R", (.365, -.020, 1.015), collection, class_name, rig,
                      "hand_r", 40, "wrist_pressure_lock"),
        add_interface(f"{p}_Boot_L", (-.127, -.020, .190), collection, class_name, rig,
                      "foot_l", 10, "boot_pressure_lock"),
        add_interface(f"{p}_Boot_R", (.127, -.020, .190), collection, class_name, rig,
                      "foot_r", 10, "boot_pressure_lock"),
        add_interface(f"{p}_PackDock", (0, .245, 1.385), collection, class_name, rig,
                      "chest", 50, "life_support_quick_disconnect"),
    ]


def render(class_name, visible):
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
    scene.view_settings.exposure = .45
    target = Vector((0, 0, .98))
    for obj in visible:
        obj.hide_render = False
    for label, position in {
        "Front": Vector((0, -4.1, 1.02)),
        "ThreeQuarter": Vector((2.9, -2.9, 1.06)),
        "Rear": Vector((0, 4.1, 1.02)),
        "RearThreeQuarter": Vector((-2.9, 2.9, 1.06)),
    }.items():
        camera.location = position
        camera.data.lens = 66
        camera.rotation_euler = (target-position).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(PREVIEW_DIR / f"PlayerOversuit_{class_name}_v17_{label}.png")
        bpy.ops.render.render(write_still=True)


def export(class_name, rig, meshes, interfaces):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / f"SKM_PlayerOversuit_{class_name}_v17.fbx"
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
    source = ASSET_DIR / f"PlayerOversuit_{class_name}_v16.blend"
    bpy.ops.wm.open_mainfile(filepath=str(source))
    bpy.context.preferences.filepaths.save_version = 0
    old_rig = bpy.data.objects[f"RIG_PlayerOversuit_{class_name}_v16"]
    old_rig.name = f"RIG_PlayerOversuit_{class_name}_v17"
    rig = old_rig
    rig["asset_status"] = "PRIMARY_CLASS_OVERSUIT_V17_REVIEW"
    rig["oversuit_pass"] = 17
    rig["provisional_fit_reference"] = FIT_REFERENCE
    rig["don_sequence"] = "boots>legs>waist>arms>chest_pack>neck_seal>helmet>pressure_check"
    rig["doff_sequence"] = "depressurize>helmet>neck_seal>chest_pack>arms>waist>legs>boots"
    rig["rack_pose"] = "neutral_A_pose_empty_garment"
    rig["runtime_equip_slot"] = "Chest"
    rig["wearer_independent"] = True

    tag_inherited_parts(class_name)
    construction = bpy.data.collections.new(f"OVERSUIT_{class_name.upper()}_V17_CONSTRUCTION")
    interfaces_collection = bpy.data.collections.new(f"OVERSUIT_{class_name.upper()}_V17_INTERFACES")
    bpy.context.scene.collection.children.link(construction)
    bpy.context.scene.collection.children.link(interfaces_collection)
    mats = mats_for(class_name, spec)
    shared = add_shared_construction(class_name, spec, construction, rig, mats)
    class_detail = REFINERS[class_name](class_name, spec, construction, rig, mats)
    interfaces = add_interfaces(class_name, spec, interfaces_collection, rig)
    meshes = [obj for obj in bpy.data.objects
              if obj.type == "MESH" and obj.get("asset_layer") == "oversuit"]

    rig["mesh_count"] = len(meshes)
    rig["v17_new_shared_parts"] = len(shared)
    rig["v17_new_class_parts"] = len(class_detail)
    rig["donning_interface_count"] = len(interfaces)
    bpy.context.scene["asset_status"] = "PRIMARY_CLASS_OVERSUIT_V17_REVIEW"
    bpy.context.scene["contains_player_body"] = False
    bpy.context.scene["contains_undersuit"] = False
    bpy.context.scene["wearer_independent"] = True
    bpy.context.scene["provisional_fit_reference"] = FIT_REFERENCE

    output = ASSET_DIR / f"PlayerOversuit_{class_name}_v17.blend"
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
        "armature": rig.name,
        "mesh_count": len(meshes),
        "new_shared_construction_parts": len(shared),
        "new_class_detail_parts": len(class_detail),
        "donning_interfaces": [obj.name for obj in interfaces],
        "previews": {
            view: str((PREVIEW_DIR / f"PlayerOversuit_{class_name}_v17_{view}.png")
                      .relative_to(ROOT)).replace("\\", "/")
            for view in ("Front", "ThreeQuarter", "Rear", "RearThreeQuarter")
        },
    }


def main():
    variants = {name: build_class(name, spec) for name, spec in v16.CLASS_SPECS.items()}
    MANIFEST.write_text(json.dumps({
        "schema": 1,
        "version": 17,
        "status": "construction_and_donning_review",
        "source_version": 16,
        "provisional_fit_reference": FIT_REFERENCE,
        "separation_contract": {
            "contains_player_body": False,
            "contains_undersuit": False,
            "wearer_independent": True,
        },
        "don_sequence": ["boots", "legs", "waist", "arms", "chest_pack",
                         "neck_seal", "helmet", "pressure_check"],
        "equipment_slot": "Chest",
        "variants": variants,
        "promotion_gates": ["final shared skeleton", "animated fit", "pressure interface fit",
                            "Unreal skeletal import", "multiplayer equip replication"],
    }, indent=2), encoding="utf-8")
    print("PRIMARY_OVERSUITS_V17", f"classes={len(variants)}", MANIFEST)


if __name__ == "__main__":
    main()
