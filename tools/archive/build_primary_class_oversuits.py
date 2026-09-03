"""Build four standalone primary class oversuits from the separated V15 shell.

Run with Blender:
  blender --background --python tools/build_primary_class_oversuits.py -- <project-root>

The output files deliberately contain no player body or undersuit.  Each file
retains the shared oversuit armature and adds a class-specific equipment layer
that can be loaded as a modular skeletal garment over the player character.
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
SOURCE = SUIT_DIR / "PlayerOversuit_Separated_v15.blend"
OUTPUT_DIR = SUIT_DIR / "PrimaryOversuits"
PREVIEW_DIR = OUTPUT_DIR / "Previews"
EXPORT_DIR = ROOT / "Build" / "Unreal" / "PlayerSuits" / "PrimaryOversuits"
MANIFEST = OUTPUT_DIR / "PrimaryOversuits_v16_Manifest.json"


CLASS_SPECS = {
    "Marine": {
        "role_alias": "Security",
        "code": "MAR",
        "accent": (0.58, 0.018, 0.012),
        "secondary": (0.15, 0.018, 0.015),
        "description": "Reinforced boarding and recovery pressure armor",
        "modules": ["ballistic cuirass", "expanded shoulder shells", "magazine pouches",
                    "helmet camera", "high-output work light"],
    },
    "Scientist": {
        "role_alias": "Crew",
        "code": "SCI",
        "accent": (0.025, 0.22, 0.68),
        "secondary": (0.025, 0.11, 0.25),
        "description": "Survey, sampling, and anomaly-analysis pressure suit",
        "modules": ["spectral sensor mast", "sample canisters", "survey lidar",
                    "instrument chest", "navigation beacon"],
    },
    "Technician": {
        "role_alias": "Engineering",
        "code": "TEC",
        "accent": (0.92, 0.22, 0.018),
        "secondary": (0.20, 0.055, 0.012),
        "description": "Thermal, electrical, and damage-control work suit",
        "modules": ["tool-arm dock", "power cells", "cable reel", "thermal plates",
                    "forearm diagnostic terminal"],
    },
    "Medical": {
        "role_alias": "Medical",
        "code": "MED",
        "accent": (0.02, 0.56, 0.62),
        "secondary": (0.70, 0.76, 0.74),
        "description": "Triage, quarantine, and casualty-recovery pressure suit",
        "modules": ["biometric scanner", "injector bank", "trauma pouches",
                    "sterile equipment pack", "patient telemetry panel"],
    },
}


def material(name, color, metallic=0.0, roughness=0.45, emission=None):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*color, 1.0)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        emission_input = bsdf.inputs.get("Emission Color") or bsdf.inputs.get("Emission")
        strength_input = bsdf.inputs.get("Emission Strength")
        if emission_input:
            emission_input.default_value = (*emission, 1.0)
        if strength_input:
            strength_input.default_value = 3.0
    mat["oversuit_material_v16"] = True
    return mat


def move_to(obj, target):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    target.objects.link(obj)


def finish(obj, target, mat, class_name, module, bevel=0.005):
    move_to(obj, target)
    if hasattr(obj.data, "materials"):
        obj.data.materials.append(mat)
    if obj.type == "MESH" and bevel:
        modifier = obj.modifiers.new("V16_ProductionEdge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
        modifier.limit_method = "ANGLE"
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
    obj["asset_layer"] = "oversuit"
    obj["oversuit_class"] = class_name
    obj["class_module"] = module
    obj["wearer_independent"] = True
    obj["unreal_export"] = True
    return obj


def bone_parent(obj, armature, bone):
    world = obj.matrix_world.copy()
    obj.parent = armature
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = world
    obj["rig_attachment"] = bone
    return obj


def rounded_box(name, location, scale, target, mat, class_name, module,
                armature, bone="chest", rotation=(0, 0, 0), bevel=0.006):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(obj, target, mat, class_name, module, bevel)
    return bone_parent(obj, armature, bone)


def cylinder(name, location, radius, depth, target, mat, class_name, module,
             armature, bone="chest", rotation=(0, 0, 0), vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                       location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    finish(obj, target, mat, class_name, module, min(0.005, radius * 0.18))
    return bone_parent(obj, armature, bone)


def sphere(name, location, scale, target, mat, class_name, module,
           armature, bone="chest"):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    finish(obj, target, mat, class_name, module, 0.003)
    return bone_parent(obj, armature, bone)


def torus(name, location, major_radius, minor_radius, target, mat, class_name, module,
          armature, bone="chest", rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major_radius, minor_radius=minor_radius,
                                    major_segments=40, minor_segments=10,
                                    location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    finish(obj, target, mat, class_name, module, 0.002)
    return bone_parent(obj, armature, bone)


def tube_between(name, start, end, radius, target, mat, class_name, module,
                 armature, bone="chest"):
    start, end = Vector(start), Vector(end)
    delta = end - start
    obj = cylinder(name, (start + end) * 0.5, radius, delta.length, target, mat,
                   class_name, module, armature, bone)
    world = delta.to_track_quat("Z", "Y").to_matrix().to_4x4()
    world.translation = (start + end) * 0.5
    obj.matrix_world = world
    return obj


def recolor_shared_shell(class_name, spec, materials, core, armature):
    accent_names = ("Status", "Telemetry", "Safety", "FrontLatch")
    ceramic_names = ("ChestUpper", "Shoulder", "Knee", "Shin", "Canister", "Ivory")
    dark_names = ("ChestLower", "Forearm", "Thigh", "Boot", "LifeSupport", "LockBand")
    shared = []
    for obj in core.objects:
        if obj.type != "MESH":
            continue
        obj["asset_layer"] = "oversuit"
        obj["oversuit_class"] = class_name
        obj["class_module"] = "shared_pressure_envelope"
        obj["wearer_independent"] = True
        obj["unreal_export"] = True
        if any(token in obj.name for token in accent_names):
            replacement = materials["accent"]
        elif any(token in obj.name for token in ceramic_names):
            replacement = materials["armor"]
        elif any(token in obj.name for token in dark_names):
            replacement = materials["composite"]
        else:
            replacement = None
        if replacement and hasattr(obj.data, "materials"):
            obj.data.materials.clear()
            obj.data.materials.append(replacement)
        if not obj.parent and not any(mod.type == "ARMATURE" for mod in obj.modifiers):
            bone_parent(obj, armature, "head")
        shared.append(obj)
    return shared


def freeze_conformal_regions(shared):
    """Bake V11 region masks in generated copies while retaining armature skinning.

    V11 stores every conformal armor part as a complete 98k-vertex garment plus
    a mask. That is useful upstream, but wasteful in four standalone variants.
    """
    for obj in shared:
        if not obj.name.startswith("SKV11_"):
            continue
        bpy.ops.object.select_all(action="DESELECT")
        obj.hide_set(False)
        obj.hide_viewport = False
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        for modifier in list(obj.modifiers):
            if modifier.type != "ARMATURE":
                bpy.ops.object.modifier_apply(modifier=modifier.name)
        obj["v16_conformal_regions_frozen"] = True


def add_shared_class_interfaces(class_name, spec, target, armature, mats):
    prefix = f"OVR16_{spec['code']}"
    parts = []
    parts.append(rounded_box(f"{prefix}_ChestHardpointRail", (0, -.174, 1.405),
                             (.118, .012, .018), target, mats["metal"], class_name,
                             "universal_chest_rail", armature, bevel=.004))
    for side in (-1, 1):
        label = "L" if side < 0 else "R"
        parts.append(rounded_box(f"{prefix}_ShoulderID_{label}",
                                 (side * .235, -.035, 1.355), (.030, .057, .020),
                                 target, mats["accent"], class_name, "class_identification",
                                 armature, f"upperarm_{label.lower()}", bevel=.004))
        parts.append(rounded_box(f"{prefix}_WaistLatch_{label}",
                                 (side * .125, -.105, .925), (.030, .018, .038),
                                 target, mats["accent"], class_name, "quick_release",
                                 armature, "pelvis", bevel=.004))
    parts.append(rounded_box(f"{prefix}_PackDockRail", (0, .235, 1.405),
                             (.115, .018, .025), target, mats["metal"], class_name,
                             "universal_pack_interface", armature, bevel=.004))
    return parts


def build_marine(target, armature, mats, spec):
    c, p = "Marine", "OVR16_MAR"
    parts = []
    # Layered cuirass and sternum bridge create a deliberately wider, protected silhouette.
    parts.append(rounded_box(f"{p}_BallisticCuirass", (0, -.188, 1.285),
                             (.145, .028, .112), target, mats["armor"], c,
                             "ballistic_cuirass", armature, bevel=.016))
    for side in (-1, 1):
        label = "L" if side < 0 else "R"
        parts.append(sphere(f"{p}_ExpandedPauldron_{label}",
                            (side * .257, -.020, 1.365), (.092, .078, .090),
                            target, mats["armor"], c, "expanded_pauldron", armature,
                            f"upperarm_{label.lower()}"))
        parts.append(rounded_box(f"{p}_MagazinePouch_{label}",
                                 (side * .155, -.151, .965), (.054, .035, .070),
                                 target, mats["composite"], c, "sealed_magazine_pouch",
                                 armature, "pelvis", bevel=.010))
        parts.append(rounded_box(f"{p}_ForearmStrikePlate_{label}",
                                 (side * .365, -.090, 1.125), (.042, .026, .085),
                                 target, mats["armor"], c, "forearm_strike_plate",
                                 armature, f"lowerarm_{label.lower()}", bevel=.010))
    for index, z in enumerate((1.215, 1.165, 1.115)):
        parts.append(rounded_box(f"{p}_AbdominalLame_{index+1}", (0, -.184, z),
                                 (.118-index*.007, .016, .016), target, mats["metal"], c,
                                 "abdominal_lame", armature, bevel=.006))
    parts.append(cylinder(f"{p}_HelmetCamera", (.105, -.155, 1.765), .023, .070,
                          target, mats["metal"], c, "helmet_camera", armature, "head",
                          rotation=(math.pi/2, 0, 0)))
    parts.append(sphere(f"{p}_CameraLens", (.105, -.193, 1.765), (.014, .007, .014),
                        target, mats["emissive"], c, "helmet_camera", armature, "head"))
    parts.append(cylinder(f"{p}_ShoulderWorkLight", (-.255, -.102, 1.405), .025, .050,
                          target, mats["metal"], c, "work_light", armature, "upperarm_l",
                          rotation=(math.pi/2, 0, 0)))
    return parts


def build_scientist(target, armature, mats, spec):
    c, p = "Scientist", "OVR16_SCI"
    parts = []
    parts.append(rounded_box(f"{p}_InstrumentChest", (.030, -.184, 1.300),
                             (.105, .022, .082), target, mats["composite"], c,
                             "instrument_chest", armature, bevel=.012))
    parts.append(rounded_box(f"{p}_SpectralDisplay", (.030, -.209, 1.315),
                             (.072, .006, .043), target, mats["emissive"], c,
                             "spectral_display", armature, bevel=.004))
    # Articulated sensor mast and three distinct optics.
    parts.append(tube_between(f"{p}_SensorMast", (-.120, .225, 1.390),
                              (-.120, .225, 1.690), .012, target, mats["metal"], c,
                              "spectral_sensor_mast", armature))
    parts.append(rounded_box(f"{p}_SensorHead", (-.120, .205, 1.700),
                             (.055, .045, .030), target, mats["armor"], c,
                             "spectral_sensor_mast", armature, bevel=.010))
    for index, x in enumerate((-.152, -.120, -.088)):
        parts.append(cylinder(f"{p}_Optic_{index+1}", (x, .158, 1.700), .011, .018,
                              target, mats["emissive"], c, "spectral_optic", armature,
                              rotation=(math.pi/2, 0, 0), vertices=24))
    for side in (-1, 1):
        label = "L" if side < 0 else "R"
        parts.append(cylinder(f"{p}_SampleCanister_{label}",
                              (side * .145, -.118, .970), .033, .135,
                              target, mats["secondary"], c, "sample_canister", armature,
                              "pelvis"))
        parts.append(rounded_box(f"{p}_ThighSampleCase_{label}",
                                 (side * .185, -.085, .745), (.052, .030, .085),
                                 target, mats["composite"], c, "sample_case", armature,
                                 f"thigh_{label.lower()}", bevel=.010))
    parts.append(torus(f"{p}_SurveyLidar", (.150, .242, 1.420), .043, .008,
                       target, mats["accent"], c, "survey_lidar", armature,
                       rotation=(math.pi/2, 0, 0)))
    parts.append(cylinder(f"{p}_NavigationBeacon", (.135, .235, 1.555), .022, .060,
                          target, mats["emissive"], c, "navigation_beacon", armature))
    return parts


def build_technician(target, armature, mats, spec):
    c, p = "Technician", "OVR16_TEC"
    parts = []
    # Rear dock is ready for a separately equipped articulated tool arm.
    parts.append(rounded_box(f"{p}_ToolArmDock", (-.165, .245, 1.330),
                             (.060, .038, .095), target, mats["metal"], c,
                             "tool_arm_dock", armature, bevel=.012))
    parts.append(cylinder(f"{p}_ToolArmSwivel", (-.215, .250, 1.355), .045, .040,
                          target, mats["accent"], c, "tool_arm_dock", armature,
                          rotation=(0, math.pi/2, 0)))
    for side in (-1, 1):
        label = "L" if side < 0 else "R"
        parts.append(rounded_box(f"{p}_PowerCell_{label}", (side*.095, .265, 1.235),
                                 (.038, .030, .125), target, mats["secondary"], c,
                                 "replaceable_power_cell", armature, bevel=.008))
        parts.append(rounded_box(f"{p}_ThermalShoulder_{label}",
                                 (side*.245, -.025, 1.360), (.075, .055, .060),
                                 target, mats["armor"], c, "thermal_shield", armature,
                                 f"upperarm_{label.lower()}", bevel=.014))
    parts.append(torus(f"{p}_CableReel", (.170, .255, 1.390), .060, .014,
                       target, mats["composite"], c, "cable_reel", armature,
                       rotation=(math.pi/2, 0, 0)))
    parts.append(cylinder(f"{p}_CableHub", (.170, .255, 1.390), .030, .030,
                          target, mats["accent"], c, "cable_reel", armature,
                          rotation=(math.pi/2, 0, 0)))
    parts.append(rounded_box(f"{p}_DiagnosticTerminal", (-.360, -.098, 1.145),
                             (.045, .022, .075), target, mats["composite"], c,
                             "forearm_diagnostic_terminal", armature, "lowerarm_l",
                             bevel=.009))
    parts.append(rounded_box(f"{p}_DiagnosticScreen", (-.360, -.123, 1.155),
                             (.032, .005, .040), target, mats["emissive"], c,
                             "forearm_diagnostic_terminal", armature, "lowerarm_l",
                             bevel=.003))
    for index, x in enumerate((-.060, 0, .060)):
        parts.append(rounded_box(f"{p}_ChestFuse_{index+1}", (x, -.184, 1.325),
                                 (.019, .012, .042), target, mats["accent"], c,
                                 "service_fuse", armature, bevel=.005))
    return parts


def build_medical(target, armature, mats, spec):
    c, p = "Medical", "OVR16_MED"
    parts = []
    parts.append(rounded_box(f"{p}_TelemetryPanel", (.030, -.184, 1.300),
                             (.105, .022, .078), target, mats["secondary"], c,
                             "patient_telemetry_panel", armature, bevel=.012))
    parts.append(rounded_box(f"{p}_TelemetryScreen", (.030, -.209, 1.310),
                             (.072, .006, .038), target, mats["emissive"], c,
                             "patient_telemetry_panel", armature, bevel=.004))
    # Compact sterile pack and visible quick-release injector bank.
    parts.append(rounded_box(f"{p}_SterileEquipmentPack", (0, .265, 1.270),
                             (.145, .040, .155), target, mats["secondary"], c,
                             "sterile_equipment_pack", armature, bevel=.016))
    for index, x in enumerate((-.090, -.030, .030, .090)):
        parts.append(cylinder(f"{p}_Injector_{index+1}", (x, .315, 1.275),
                              .018, .120, target, mats["accent"], c,
                              "injector_bank", armature))
    for side in (-1, 1):
        label = "L" if side < 0 else "R"
        parts.append(rounded_box(f"{p}_TraumaPouch_{label}",
                                 (side*.155, -.145, .975), (.058, .035, .070),
                                 target, mats["secondary"], c, "trauma_pouch", armature,
                                 "pelvis", bevel=.012))
        # Cyan twin bars read as medical identification without relying on text.
        for offset in (-.018, .018):
            parts.append(rounded_box(f"{p}_MedicalBar_{label}_{offset:+.3f}",
                                     (side*.245+offset, -.090, 1.390),
                                     (.010, .010, .035), target, mats["accent"], c,
                                     "medical_identification", armature,
                                     f"upperarm_{label.lower()}", bevel=.003))
    parts.append(cylinder(f"{p}_BiometricScanner", (.110, -.165, 1.470), .025, .055,
                          target, mats["metal"], c, "biometric_scanner", armature,
                          rotation=(math.pi/2, 0, 0)))
    parts.append(sphere(f"{p}_BiometricLens", (.110, -.198, 1.470),
                        (.014, .007, .014), target, mats["emissive"], c,
                        "biometric_scanner", armature))
    return parts


BUILDERS = {
    "Marine": build_marine,
    "Scientist": build_scientist,
    "Technician": build_technician,
    "Medical": build_medical,
}


def configure_materials(class_name, spec):
    accent = spec["accent"]
    secondary = spec["secondary"]
    return {
        "accent": material(f"M_OVR16_{class_name}_Accent", accent, .28, .30),
        "secondary": material(f"M_OVR16_{class_name}_Secondary", secondary, .12, .42),
        "armor": material(f"M_OVR16_{class_name}_Armor", (.43, .46, .45), .18, .30),
        "composite": material(f"M_OVR16_{class_name}_Composite", (.025, .032, .036), .08, .68),
        "metal": material(f"M_OVR16_{class_name}_ServiceMetal", (.075, .085, .090), .72, .24),
        "emissive": material(f"M_OVR16_{class_name}_Status", accent, .10, .20,
                             emission=tuple(min(1.0, x*1.35+.08) for x in accent)),
    }


def render_previews(class_name, visible):
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
    scene.view_settings.exposure = .8
    for obj in visible:
        obj.hide_render = False
    target = Vector((0, 0, .98))
    for label, position in {
        "Front": Vector((0, -4.2, 1.02)),
        "ThreeQuarter": Vector((3.0, -3.0, 1.06)),
        "Rear": Vector((0, 4.2, 1.02)),
    }.items():
        camera.location = position
        camera.data.lens = 64
        camera.rotation_euler = (target-position).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(PREVIEW_DIR / f"PlayerOversuit_{class_name}_v16_{label}.png")
        bpy.ops.render.render(write_still=True)


def export_fbx(class_name, armature, meshes):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / f"SKM_PlayerOversuit_{class_name}_v16.fbx"
    bpy.ops.object.select_all(action="DESELECT")
    for obj in [armature, *meshes]:
        obj.hide_set(False)
        obj.hide_viewport = False
        obj.select_set(True)
    bpy.context.view_layer.objects.active = armature
    bpy.ops.export_scene.fbx(
        filepath=str(path), use_selection=True,
        object_types={"ARMATURE", "MESH"}, global_scale=1.0,
        apply_unit_scale=True, apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="-Z", axis_up="Y", use_mesh_modifiers=True,
        mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False,
        path_mode="RELATIVE", embed_textures=False,
    )
    return path


def build_class(class_name, spec):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    bpy.context.preferences.filepaths.save_version = 0
    armature = bpy.data.objects["RIG_PlayerOversuit_v15"]
    armature.name = f"RIG_PlayerOversuit_{class_name}_v16"
    armature["asset_layer"] = "oversuit"
    armature["oversuit_class"] = class_name
    armature["profile_role_alias"] = spec["role_alias"]
    armature["wearer_independent"] = True
    armature["assembly_policy"] = "modular skeletal garment; never embed player or undersuit"

    core = bpy.data.collections["PLAYER_OVERSUIT_V15"]
    core.name = f"OVERSUIT_{class_name.upper()}_V16_CORE"
    modules = bpy.data.collections.new(f"OVERSUIT_{class_name.upper()}_V16_CLASS_MODULES")
    bpy.context.scene.collection.children.link(modules)
    mats = configure_materials(class_name, spec)
    shared = recolor_shared_shell(class_name, spec, mats, core, armature)
    freeze_conformal_regions(shared)
    interfaces = add_shared_class_interfaces(class_name, spec, modules, armature, mats)
    class_parts = BUILDERS[class_name](modules, armature, mats, spec)
    visible = [*shared, *interfaces, *class_parts]

    armature["shared_mesh_count"] = len(shared)
    armature["class_module_count"] = len(interfaces) + len(class_parts)
    armature["class_description"] = spec["description"]
    armature["primary_modules"] = ",".join(spec["modules"])
    bpy.context.scene["asset_status"] = "PRIMARY_CLASS_OVERSUIT_V16_REVIEW"
    bpy.context.scene["contains_player_body"] = False
    bpy.context.scene["contains_undersuit"] = False
    bpy.context.scene["wearer_independent"] = True
    bpy.context.scene["gameplay_class"] = class_name
    bpy.context.scene["profile_role_alias"] = spec["role_alias"]

    output = OUTPUT_DIR / f"PlayerOversuit_{class_name}_v16.blend"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    # V15 is physically separated at object level but still contains many
    # unreferenced historical datablocks. Do not replicate that baggage into
    # every class asset.
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
    render_previews(class_name, visible)
    fbx = export_fbx(class_name, armature, visible)
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
    return {
        "gameplay_class": class_name,
        "profile_role_alias": spec["role_alias"],
        "description": spec["description"],
        "blend": str(output.relative_to(ROOT)).replace("\\", "/"),
        "fbx": str(fbx.relative_to(ROOT)).replace("\\", "/"),
        "armature": armature.name,
        "shared_mesh_count": len(shared),
        "class_module_count": len(interfaces) + len(class_parts),
        "primary_modules": spec["modules"],
        "previews": {
            label: str((PREVIEW_DIR / f"PlayerOversuit_{class_name}_v16_{label}.png")
                       .relative_to(ROOT)).replace("\\", "/")
            for label in ("Front", "ThreeQuarter", "Rear")
        },
    }


def main():
    if not SOURCE.exists():
        raise RuntimeError(f"Missing separated oversuit source: {SOURCE}")
    variants = {name: build_class(name, spec) for name, spec in CLASS_SPECS.items()}
    MANIFEST.write_text(json.dumps({
        "schema": 1,
        "version": 16,
        "status": "primary_class_oversuits_review",
        "source": str(SOURCE.relative_to(ROOT)).replace("\\", "/"),
        "separation_contract": {
            "contains_player_body": False,
            "contains_undersuit": False,
            "wearer_independent": True,
            "attachment": "modular skeletal garment using shared oversuit armature",
        },
        "class_to_existing_role": {name: spec["role_alias"] for name, spec in CLASS_SPECS.items()},
        "variants": variants,
        "runtime_note": "Review assets only; promote after fit/deformation and multiplayer loadout validation.",
    }, indent=2), encoding="utf-8")
    print("PRIMARY_OVERSUITS_V16", f"classes={len(variants)}", f"manifest={MANIFEST}")


if __name__ == "__main__":
    main()
