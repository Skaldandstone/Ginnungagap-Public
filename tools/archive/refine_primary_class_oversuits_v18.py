"""V18 form-language pass for the standalone primary class oversuits.

This pass removes the most obvious blockout primitives from V17 and replaces
them with curved, tapered, manufactured shells while preserving every garment,
rig, donning-interface, and separation contract.

Run with Blender:
  blender --background --python tools/refine_primary_class_oversuits_v18.py -- <project-root>
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
PREVIEW_DIR = ASSET_DIR / "Previews_v18"
EXPORT_DIR = ROOT / "Build" / "Unreal" / "PlayerSuits" / "PrimaryOversuits_v18"
MANIFEST = ASSET_DIR / "PrimaryOversuits_v18_Manifest.json"


def inherited_material(class_name, suffix, fallback):
    for version in (18, 17, 16):
        mat = bpy.data.materials.get(f"M_OVR{version}_{class_name}_{suffix}")
        if mat:
            return mat
    color, metallic, roughness = fallback
    return v16.material(f"M_OVR18_{class_name}_{suffix}", color, metallic, roughness)


def materials(class_name, spec):
    return {
        "accent": inherited_material(class_name, "Accent", (spec["accent"], .28, .30)),
        "secondary": inherited_material(class_name, "Secondary", (spec["secondary"], .12, .42)),
        "armor": inherited_material(class_name, "Armor", ((.43, .46, .45), .18, .30)),
        "composite": inherited_material(class_name, "Composite", ((.025, .032, .036), .08, .68)),
        "metal": inherited_material(class_name, "ServiceMetal", ((.075, .085, .090), .72, .24)),
        "gasket": inherited_material(class_name, "PressureGasket", ((.018, .024, .027), .02, .82)),
    }


def remove_matching(tokens):
    removed = []
    for obj in list(bpy.data.objects):
        if any(token in obj.name for token in tokens):
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    return removed


def finish(obj, collection, mat, class_name, module, rig, bone, stage, bevel=.008):
    v16.finish(obj, collection, mat, class_name, module, bevel)
    v16.bone_parent(obj, rig, bone)
    obj["oversuit_pass"] = 18
    obj["donning_stage"] = stage
    obj["v18_form_refinement"] = True
    obj["pressure_boundary"] = "external_nonpressure_module"
    return obj


def bulged_panel(name, center, width_top, width_bottom, height, depth, bulge,
                 collection, mat, class_name, module, rig, bone="chest", stage=50,
                 facing=-1, segments=12, bevel=.010):
    """Create a convex tapered panel with a manufactured compound curve."""
    cx, cy, cz = center
    vertices = []
    # Front and rear skins, each with bottom/top rows.
    for skin in (0, 1):
        for row, width in ((0, width_bottom), (1, width_top)):
            z = cz + (-.5 if row == 0 else .5) * height
            for index in range(segments + 1):
                t = index / segments
                x = (t - .5) * width
                curve = bulge * (1.0 - (2*t - 1.0) ** 2)
                surface = cy + facing * (depth*.5 + curve) if skin == 0 else cy - facing*depth*.5
                vertices.append((cx + x, surface, z))
    row_len = segments + 1
    faces = []
    # Front and rear grids.
    for skin in (0, 1):
        base = skin * row_len * 2
        for index in range(segments):
            a, b = base + index, base + index + 1
            c, d = base + row_len + index + 1, base + row_len + index
            faces.append((a, b, c, d) if skin == 0 else (d, c, b, a))
    front, rear = 0, row_len*2
    for index in range(segments):
        # top and bottom closures
        faces.append((front+index, rear+index, rear+index+1, front+index+1))
        faces.append((front+row_len+index+1, rear+row_len+index+1,
                      rear+row_len+index, front+row_len+index))
    # left and right closures
    faces += [
        (front, front+row_len, rear+row_len, rear),
        (front+segments, rear+segments, rear+row_len+segments, front+row_len+segments),
    ]
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return finish(obj, collection, mat, class_name, module, rig, bone, stage, bevel)


def elliptical_band(name, center, radius_x, radius_y, radial_width, height,
                    collection, mat, class_name, module, rig, bone="pelvis", stage=30,
                    segments=48):
    cx, cy, cz = center
    vertices = []
    for z in (cz-height*.5, cz+height*.5):
        for radius_offset in (-radial_width*.5, radial_width*.5):
            for index in range(segments):
                angle = math.tau * index / segments
                x = cx + (radius_x + radius_offset) * math.sin(angle)
                y = cy - (radius_y + radius_offset) * math.cos(angle)
                vertices.append((x, y, z))
    ring = segments
    faces = []
    # indexes: bottom inner, bottom outer, top inner, top outer
    for index in range(segments):
        nxt = (index+1) % segments
        bi, bo = index, ring+index
        ti, to = 2*ring+index, 3*ring+index
        nbi, nbo = nxt, ring+nxt
        nti, nto = 2*ring+nxt, 3*ring+nxt
        faces += [(bo, nbo, nto, to), (nbi, bi, ti, nti),
                  (to, nto, nti, ti), (bi, nbi, nbo, bo)]
    mesh = bpy.data.meshes.new(name + "_Mesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    collection.objects.link(obj)
    return finish(obj, collection, mat, class_name, module, rig, bone, stage, .006)


def capsule(name, location, scale, collection, mat, class_name, module, rig,
            bone="chest", stage=50):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=20, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, collection, mat, class_name, module, rig, bone, stage, .003)


def tube(name, start, end, radius, collection, mat, class_name, module, rig,
         bone="chest", stage=50):
    obj = v16.tube_between(name, start, end, radius, collection, mat, class_name,
                           module, rig, bone)
    obj["oversuit_pass"] = 18
    obj["donning_stage"] = stage
    obj["v18_form_refinement"] = True
    obj["pressure_boundary"] = "external_nonpressure_module"
    return obj


def soften_existing_geometry():
    softened = 0
    for obj in bpy.data.objects:
        if obj.type != "MESH" or obj.get("asset_layer") != "oversuit":
            continue
        if not obj.name.startswith(("OVR16_", "OVR17_", "SKV12_")):
            continue
        dimensions = [value for value in obj.dimensions if value > 1e-5]
        if not dimensions:
            continue
        target_width = min(.018, min(dimensions) * .22)
        bevels = [modifier for modifier in obj.modifiers if modifier.type == "BEVEL"]
        bevel = bevels[0] if bevels else obj.modifiers.new("V18_FormRadius", "BEVEL")
        bevel.width = max(bevel.width, target_width)
        bevel.segments = max(bevel.segments, 4)
        bevel.limit_method = "ANGLE"
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        obj["oversuit_pass"] = 18
        obj["v18_softened_edges"] = True
        softened += 1
    return softened


def add_shared_forms(class_name, spec, collection, rig, mats):
    p = f"OVR18_{spec['code']}"
    parts = []
    parts.append(elliptical_band(f"{p}_ContinuousWaistRing", (0, 0, .925), .178, .125,
                                 .038, .060, collection, mats["composite"], class_name,
                                 "continuous_waist_ring", rig))
    # Soft accent pads interrupt the ring without rebuilding it from boxes.
    for side in (-1, 1):
        label = "L" if side < 0 else "R"
        parts.append(capsule(f"{p}_WaistLockPad_{label}", (side*.177, -.015, .925),
                             (.026, .050, .036), collection, mats["accent"], class_name,
                             "waist_lock_pad", rig, "pelvis", 30))
        # Tubular harness struts replace the previous rectangular chest bars.
        parts.append(tube(f"{p}_HarnessStrut_{label}", (side*.125, -.172, 1.175),
                          (side*.120, -.172, 1.400), .010, collection, mats["metal"],
                          class_name, "chest_harness_strut", rig))
    # Curved rear shroud visually unifies the life-support chassis while leaving
    # role hardware, entry latches, and quick-disconnects exposed.
    parts.append(bulged_panel(f"{p}_LifeSupportShroud", (0, .205, 1.265), .275, .300,
                              .310, .035, .022, collection, mats["metal"], class_name,
                              "curved_life_support_shroud", rig, facing=1, bevel=.014))
    parts.append(capsule(f"{p}_HelmetCrownPad", (0, -.090, 1.845),
                         (.082, .038, .020), collection, mats["armor"], class_name,
                         "conformal_helmet_crown_pad", rig, "head", 70))
    return parts


def add_marine_forms(collection, rig, mats):
    parts = [
        bulged_panel("OVR18_MAR_CurvedCuirass", (0, -.185, 1.285), .315, .250,
                     .235, .045, .030, collection, mats["armor"], "Marine",
                     "curved_ballistic_cuirass", rig, bevel=.016),
        bulged_panel("OVR18_MAR_AbdominalGuard", (0, -.170, 1.095), .220, .190,
                     .105, .032, .018, collection, mats["composite"], "Marine",
                     "curved_abdominal_guard", rig, bevel=.012),
    ]
    for side in (-1, 1):
        label = "L" if side < 0 else "R"
        limb = label.lower()
        parts.append(capsule(f"OVR18_MAR_ThighPod_{label}", (side*.185, -.105, .755),
                             (.050, .038, .090), collection, mats["metal"], "Marine",
                             "rounded_thigh_hardpoint", rig, f"thigh_{limb}", 30))
    # Recessed class stripe follows the curved shell instead of framing it as a box.
    parts.append(bulged_panel("OVR18_MAR_CuirassInset", (0, -.233, 1.315), .065, .055,
                              .155, .008, .006, collection, mats["accent"], "Marine",
                              "cuirass_recessed_identity", rig, bevel=.005))
    return parts


def add_scientist_forms(collection, rig, mats):
    parts = [
        bulged_panel("OVR18_SCI_InstrumentPod", (.025, -.184, 1.305), .245, .205,
                     .180, .042, .025, collection, mats["composite"], "Scientist",
                     "curved_instrument_pod", rig, bevel=.014),
        capsule("OVR18_SCI_SampleVault_L", (-.145, -.110, .970), (.035, .035, .075),
                collection, mats["secondary"], "Scientist", "rounded_sample_vault", rig,
                "pelvis", 30),
        capsule("OVR18_SCI_SampleVault_R", (.145, -.110, .970), (.035, .035, .075),
                collection, mats["secondary"], "Scientist", "rounded_sample_vault", rig,
                "pelvis", 30),
    ]
    # A swept shoulder-to-pack fairing integrates the mast base.
    parts.append(bulged_panel("OVR18_SCI_SensorFairing", (-.115, .205, 1.510), .115, .085,
                              .210, .030, .018, collection, mats["armor"], "Scientist",
                              "sensor_mast_fairing", rig, facing=1, bevel=.012))
    return parts


def add_technician_forms(collection, rig, mats):
    parts = [
        bulged_panel("OVR18_TEC_ServiceBib", (0, -.180, 1.285), .275, .225,
                     .205, .040, .026, collection, mats["secondary"], "Technician",
                     "curved_service_bib", rig, bevel=.014),
        bulged_panel("OVR18_TEC_ThermalBackplane", (.095, .240, 1.260), .120, .145,
                     .245, .030, .018, collection, mats["composite"], "Technician",
                     "thermal_backplane", rig, facing=1, bevel=.012),
    ]
    for side in (-1, 1):
        label = "L" if side < 0 else "R"
        parts.append(capsule(f"OVR18_TEC_PowerCellShell_{label}",
                             (side*.095, .270, 1.235), (.041, .034, .125),
                             collection, mats["accent"], "Technician",
                             "rounded_power_cell_shell", rig))
    return parts


def add_medical_forms(collection, rig, mats):
    parts = [
        bulged_panel("OVR18_MED_TelemetryShell", (.025, -.184, 1.305), .285, .235,
                     .205, .040, .024, collection, mats["secondary"], "Medical",
                     "curved_telemetry_shell", rig, bevel=.016),
        bulged_panel("OVR18_MED_SterilePackShell", (0, .250, 1.270), .275, .245,
                     .275, .045, .026, collection, mats["secondary"], "Medical",
                     "curved_sterile_pack_shell", rig, facing=1, bevel=.016),
    ]
    for side in (-1, 1):
        label = "L" if side < 0 else "R"
        parts.append(capsule(f"OVR18_MED_TraumaPod_{label}", (side*.155, -.125, .975),
                             (.055, .038, .068), collection, mats["secondary"], "Medical",
                             "rounded_trauma_pod", rig, "pelvis", 30))
    return parts


CLASS_BUILDERS = {
    "Marine": add_marine_forms,
    "Scientist": add_scientist_forms,
    "Technician": add_technician_forms,
    "Medical": add_medical_forms,
}


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
    scene.view_settings.exposure = .25
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
        scene.render.filepath = str(PREVIEW_DIR / f"PlayerOversuit_{class_name}_v18_{label}.png")
        bpy.ops.render.render(write_still=True)


def export(class_name, rig, meshes, interfaces):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / f"SKM_PlayerOversuit_{class_name}_v18.fbx"
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


REMOVALS = {
    "Marine": ("OVR16_MAR_BallisticCuirass", "OVR17_MAR_CuirassEdge",
               "OVR17_MAR_ThighHardpoint"),
    "Scientist": ("OVR16_SCI_InstrumentChest", "OVR16_SCI_SampleCanister"),
    "Technician": ("OVR16_TEC_PowerCell_",),
    "Medical": ("OVR16_MED_TelemetryPanel", "OVR16_MED_SterileEquipmentPack",
                "OVR16_MED_TraumaPouch"),
}
COMMON_REMOVALS = ("WaistYokeFront", "WaistYokeRear", "HipYoke_",
                   "ChestHarness_", "HelmetCrownRail")


def build_class(class_name, spec):
    source = ASSET_DIR / f"PlayerOversuit_{class_name}_v17.blend"
    bpy.ops.wm.open_mainfile(filepath=str(source))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects[f"RIG_PlayerOversuit_{class_name}_v17"]
    rig.name = f"RIG_PlayerOversuit_{class_name}_v18"
    removed = remove_matching((*COMMON_REMOVALS, *REMOVALS[class_name]))
    collection = bpy.data.collections.new(f"OVERSUIT_{class_name.upper()}_V18_CURVED_FORMS")
    bpy.context.scene.collection.children.link(collection)
    mats = materials(class_name, spec)
    shared = add_shared_forms(class_name, spec, collection, rig, mats)
    class_forms = CLASS_BUILDERS[class_name](collection, rig, mats)
    softened = soften_existing_geometry()
    meshes = [obj for obj in bpy.data.objects
              if obj.type == "MESH" and obj.get("asset_layer") == "oversuit"]
    interfaces = [obj for obj in bpy.data.objects if obj.get("asset_layer") == "oversuit_interface"]
    for obj in meshes:
        obj["oversuit_pass"] = 18
    rig["asset_status"] = "PRIMARY_CLASS_OVERSUIT_V18_FORM_REVIEW"
    rig["oversuit_pass"] = 18
    rig["v18_removed_blockout_parts"] = len(removed)
    rig["v18_curved_form_parts"] = len(shared) + len(class_forms)
    rig["v18_softened_existing_parts"] = softened
    rig["mesh_count"] = len(meshes)
    rig["wearer_independent"] = True
    bpy.context.scene["asset_status"] = "PRIMARY_CLASS_OVERSUIT_V18_FORM_REVIEW"
    bpy.context.scene["contains_player_body"] = False
    bpy.context.scene["contains_undersuit"] = False

    output = ASSET_DIR / f"PlayerOversuit_{class_name}_v18.blend"
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
        "removed_blockout_parts": removed,
        "curved_form_part_count": len(shared) + len(class_forms),
        "softened_existing_part_count": softened,
        "previews": {
            view: str((PREVIEW_DIR / f"PlayerOversuit_{class_name}_v18_{view}.png")
                      .relative_to(ROOT)).replace("\\", "/")
            for view in ("Front", "ThreeQuarter", "Rear", "RearThreeQuarter")
        },
    }


def main():
    variants = {name: build_class(name, spec) for name, spec in v16.CLASS_SPECS.items()}
    MANIFEST.write_text(json.dumps({
        "schema": 1, "version": 18, "status": "curved_form_language_review",
        "source_version": 17,
        "separation_contract": {"contains_player_body": False, "contains_undersuit": False,
                                "wearer_independent": True},
        "form_changes": ["continuous elliptical waist ring", "curved life-support shroud",
                         "conformal helmet crown pad", "tubular chest harness",
                         "tapered bulged class chest shells", "rounded class equipment housings",
                         "four-segment edge radii on retained blockout hardware"],
        "variants": variants,
        "promotion_gates": ["final shared skeleton", "animated fit", "pressure interface fit",
                            "Unreal skeletal import", "multiplayer equip replication"],
    }, indent=2), encoding="utf-8")
    print("PRIMARY_OVERSUITS_V18", f"classes={len(variants)}", MANIFEST)


if __name__ == "__main__":
    main()
