"""V21 seam-integration, articulated-glove, and dedicated-boot pass.

The pass converts proud V20 seam rods into surface-following mesh seams, reduces
joint bellows, replaces mitten gloves with articulated pieces, and removes the
last V11 boot meshes in favor of dedicated magnetic boots.

Run with Blender:
  blender --background --python tools/refine_primary_class_oversuits_v21.py -- <project-root>
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
PREVIEW_DIR = ASSET_DIR / "Previews_v21"
EXPORT_DIR = ROOT / "Build" / "Unreal" / "PlayerSuits" / "PrimaryOversuits_v21"
MANIFEST = ASSET_DIR / "PrimaryOversuits_v21_Manifest.json"


REMOVE_TOKENS = (
    "OVR20_",  # rebuilt below except class-specific surface pieces, restored selectively
    "GloveShell_", "GloveKnuckle_", "PalmPlate_", "KnucklePad_", "SKV11_Boot_",
)
KEEP_V20_CLASS_TOKENS = ("CuirassRib", "InstrumentDial", "ServiceBibRib",
                         "TelemetryCleanLine")


def mats_for(class_name):
    def required(name):
        mat = bpy.data.materials.get(name)
        if not mat:
            raise RuntimeError(f"Missing V20 material: {name}")
        return mat
    return {
        "fabric": required(f"M_OVR20_{class_name}_TailoredPressureFabric"),
        "seam": required(f"M_OVR20_{class_name}_SeamTape"),
        "piping": required(f"M_OVR20_{class_name}_RolePiping"),
        "armor": next(mat for mat in bpy.data.materials
                      if mat.name in {f"M_OVR16_{class_name}_Armor", f"M_OVR17_{class_name}_Armor"}),
        "composite": next(mat for mat in bpy.data.materials
                          if mat.name in {f"M_OVR16_{class_name}_Composite", f"M_OVR17_{class_name}_Composite"}),
        "metal": next(mat for mat in bpy.data.materials
                      if mat.name in {f"M_OVR16_{class_name}_ServiceMetal", f"M_OVR17_{class_name}_ServiceMetal"}),
        "accent": next(mat for mat in bpy.data.materials
                       if mat.name in {f"M_OVR16_{class_name}_Accent", f"M_OVR17_{class_name}_Accent"}),
    }


def remove_rebuilt_geometry():
    removed = []
    for obj in list(bpy.data.objects):
        remove = any(token in obj.name for token in REMOVE_TOKENS)
        if obj.name.startswith("OVR20_") and any(token in obj.name for token in KEEP_V20_CLASS_TOKENS):
            remove = False
        if remove:
            removed.append(obj.name)
            bpy.data.objects.remove(obj, do_unlink=True)
    return removed


def mark(obj, module, stage, kind):
    obj["oversuit_pass"] = 21
    obj["v21_integrated_component"] = kind
    obj["class_module"] = module
    obj["donning_stage"] = stage
    obj["pressure_boundary"] = "garment_surface" if kind == "surface_seam" else kind
    return obj


def curve_mesh(name, points, radius, collection, mat, class_name, module, rig,
               bone="chest", stage=50, kind="surface_seam"):
    curve = bpy.data.curves.new(name + "_Curve", "CURVE")
    curve.dimensions = "3D"
    curve.resolution_u = 3
    curve.bevel_depth = radius
    curve.bevel_resolution = 3
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points)-1)
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.convert(target="MESH")
    obj = bpy.context.object
    obj.name = name
    for owner in list(obj.users_collection):
        if owner != collection:
            owner.objects.unlink(obj)
    if collection.objects.get(obj.name) is None:
        collection.objects.link(obj)
    v16.bone_parent(obj, rig, bone)
    obj["asset_layer"] = "oversuit"
    obj["oversuit_class"] = class_name
    obj["wearer_independent"] = True
    obj["unreal_export"] = True
    obj["v21_curve_converted_to_mesh"] = True
    return mark(obj, module, stage, kind)


def capsule(name, location, scale, collection, mat, class_name, module, rig,
            bone, stage, kind):
    obj = v18.capsule(name, location, scale, collection, mat, class_name,
                      module, rig, bone, stage)
    return mark(obj, module, stage, kind)


def ring(name, location, major, minor, collection, mat, class_name, module,
         rig, bone, stage):
    obj = v16.torus(name, location, major, minor, collection, mat, class_name,
                    module, rig, bone)
    return mark(obj, module, stage, "articulation_bellow")


def ellipsoid_front_y(x, z, center_x, center_z, rx, ry, rz, offset=.002):
    value = 1.0 - ((x-center_x)/rx)**2 - ((z-center_z)/rz)**2
    return -ry * math.sqrt(max(.02, value)) - offset


def torso_front_y(x, z, offset=.002):
    if z >= 1.155:
        return ellipsoid_front_y(x, z, 0, 1.285, .215, .105, .211, offset)
    return ellipsoid_front_y(x, z, 0, 1.055, .165, .084, .167, offset)


def torso_surface_seams(class_name, spec, collection, rig, mats):
    p = f"OVR21_{spec['code']}"
    parts = []
    # Center closure follows the two tailored torso ellipsoids.
    center_points = [(0, torso_front_y(0, z, .003), z)
                     for z in (.955, 1.015, 1.075, 1.135, 1.195, 1.260, 1.330, 1.395, 1.450)]
    parts.append(curve_mesh(f"{p}_ConformalCenterClosure", center_points, .0032,
                            collection, mats["seam"], class_name, "conformal_center_closure", rig))
    for side in (-1, 1):
        label = "L" if side < 0 else "R"
        diagonal = []
        piping = []
        for index in range(7):
            t = index/6
            x = side * (.020 + .145*t)
            z = 1.385 - .205*t
            diagonal.append((x, torso_front_y(x, z, .0025), z))
            xp = side * (.155 + .010*t)
            zp = 1.410 - .245*t
            piping.append((xp, torso_front_y(xp, zp, .003), zp))
        parts += [
            curve_mesh(f"{p}_ConformalChestSeam_{label}", diagonal, .0025,
                       collection, mats["seam"], class_name, "conformal_chest_seam", rig),
            curve_mesh(f"{p}_ConformalRolePiping_{label}", piping, .0030,
                       collection, mats["piping"], class_name, "conformal_role_piping", rig),
        ]
    for index, z in enumerate((1.130, 1.075, 1.020, .970)):
        points = []
        for step in range(13):
            x = -.135 + .270*step/12
            points.append((x, torso_front_y(x, z, .002), z))
        parts.append(curve_mesh(f"{p}_ConformalAbdomenSeam_{index+1}", points, .0022,
                                collection, mats["seam"], class_name,
                                "conformal_abdominal_seam", rig, "spine_02", 50))
    return parts


def limb_surface_seams(class_name, spec, collection, rig, mats, side):
    p = f"OVR21_{spec['code']}"
    label = "L" if side < 0 else "R"
    limb = label.lower()
    parts = []
    # Two compact dark rings replace the three bright, oversized V20 rings.
    for index, z in enumerate((1.066, 1.096)):
        parts.append(ring(f"{p}_IntegratedElbowBellow_{label}_{index+1}",
                          (side*.350, -.010, z), .046, .0035, collection, mats["seam"],
                          class_name, "integrated_elbow_bellow", rig,
                          f"lowerarm_{limb}", 40))
    for index, z in enumerate((.510, .540)):
        parts.append(ring(f"{p}_IntegratedKneeBellow_{label}_{index+1}",
                          (side*.128, -.002, z), .056, .0038, collection, mats["seam"],
                          class_name, "integrated_knee_bellow", rig, f"calf_{limb}", 20))
    # Surface-following leg seams account for the tailored ellipsoid cross-section.
    thigh_points, role_points = [], []
    for step in range(8):
        z = .845 - .220*step/7
        x = side*(.128 + .052)
        local_x = abs(x-side*.128)
        y = -.061*math.sqrt(max(.05, 1-(local_x/.075)**2-((z-.720)/.182)**2))-.002
        thigh_points.append((x, y, z))
        role_points.append((side*(.128+.043), y-.002, z))
    shin_points = []
    for step in range(8):
        z = .455 - .205*step/7
        x = side*(.128+.043)
        local_x = abs(x-side*.128)
        y = -.051*math.sqrt(max(.05, 1-(local_x/.064)**2-((z-.355)/.161)**2))-.002
        shin_points.append((x, y, z))
    parts += [
        curve_mesh(f"{p}_ConformalThighSeam_{label}", thigh_points, .0026,
                   collection, mats["seam"], class_name, "conformal_thigh_seam", rig,
                   f"thigh_{limb}", 30),
        curve_mesh(f"{p}_ConformalThighPiping_{label}", role_points, .0028,
                   collection, mats["piping"], class_name, "conformal_limb_piping", rig,
                   f"thigh_{limb}", 30),
        curve_mesh(f"{p}_ConformalShinSeam_{label}", shin_points, .0025,
                   collection, mats["seam"], class_name, "conformal_shin_seam", rig,
                   f"calf_{limb}", 20),
    ]
    return parts


def articulated_glove(class_name, spec, collection, rig, mats, side):
    p = f"OVR21_{spec['code']}"
    label = "L" if side < 0 else "R"
    limb = label.lower()
    cx = side*.382
    parts = [
        capsule(f"{p}_GlovePalm_{label}", (cx, -.040, .965), (.052, .060, .062),
                collection, mats["fabric"], class_name, "articulated_glove_palm", rig,
                f"hand_{limb}", 40, "flexible_pressure_glove"),
        capsule(f"{p}_GloveKnuckleGuard_{label}", (cx, -.096, .982), (.048, .012, .030),
                collection, mats["armor"], class_name, "glove_knuckle_guard", rig,
                f"hand_{limb}", 40, "external_hard_shell"),
    ]
    for index, offset in enumerate((-.030, -.010, .010, .030)):
        parts.append(capsule(f"{p}_GloveFinger_{label}_{index+1}",
                             (cx+offset, -.063, .920), (.010, .016, .042),
                             collection, mats["fabric"], class_name,
                             "articulated_glove_finger", rig, f"hand_{limb}", 40,
                             "flexible_pressure_glove"))
    thumb_x = cx - side*.054
    thumb = capsule(f"{p}_GloveThumb_{label}", (thumb_x, -.058, .955),
                    (.013, .022, .034), collection, mats["fabric"], class_name,
                    "articulated_glove_thumb", rig, f"hand_{limb}", 40,
                    "flexible_pressure_glove")
    thumb.rotation_euler.y = side*math.radians(28)
    parts.append(thumb)
    return parts


def dedicated_boot(class_name, spec, collection, rig, mats, side):
    p = f"OVR21_{spec['code']}"
    label = "L" if side < 0 else "R"
    limb = label.lower()
    x = side*.128
    parts = [
        capsule(f"{p}_BootAnkleEnvelope_{label}", (x, .005, .155), (.076, .068, .075),
                collection, mats["fabric"], class_name, "boot_ankle_envelope", rig,
                f"foot_{limb}", 10, "boot_pressure_envelope"),
        capsule(f"{p}_BootHeelShell_{label}", (x, .055, .080), (.076, .082, .050),
                collection, mats["composite"], class_name, "rounded_boot_heel", rig,
                f"foot_{limb}", 10, "external_hard_shell"),
        capsule(f"{p}_BootInstepShell_{label}", (x, -.035, .105), (.079, .095, .055),
                collection, mats["composite"], class_name, "rounded_boot_instep", rig,
                f"foot_{limb}", 10, "external_hard_shell"),
        capsule(f"{p}_BootToeCap_{label}", (x, -.125, .070), (.082, .105, .043),
                collection, mats["armor"], class_name, "rounded_boot_toe", rig,
                f"foot_{limb}", 10, "external_hard_shell"),
        capsule(f"{p}_BootMagSole_{label}", (x, -.040, .025), (.088, .150, .016),
                collection, mats["metal"], class_name, "magnetic_boot_sole", rig,
                f"foot_{limb}", 10, "magnetic_contact_surface"),
    ]
    for index, y in enumerate((-.125, -.060, .010, .075)):
        parts.append(capsule(f"{p}_BootTread_{label}_{index+1}", (x, y, .010),
                             (.065, .021, .007), collection, mats["accent"], class_name,
                             "magnetic_boot_tread", rig, f"foot_{limb}", 10,
                             "magnetic_contact_surface"))
    return parts


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
    scene.view_settings.exposure = .12
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
        scene.render.filepath = str(PREVIEW_DIR / f"PlayerOversuit_{class_name}_v21_{label}.png")
        bpy.ops.render.render(write_still=True)


def export(class_name, rig, meshes, interfaces):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / f"SKM_PlayerOversuit_{class_name}_v21.fbx"
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
    source = ASSET_DIR / f"PlayerOversuit_{class_name}_v20.blend"
    bpy.ops.wm.open_mainfile(filepath=str(source))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects[f"RIG_PlayerOversuit_{class_name}_v20"]
    rig.name = f"RIG_PlayerOversuit_{class_name}_v21"
    removed = remove_rebuilt_geometry()
    collection = bpy.data.collections.new(f"OVERSUIT_{class_name.upper()}_V21_INTEGRATED_CONSTRUCTION")
    bpy.context.scene.collection.children.link(collection)
    mats = mats_for(class_name)
    seams = [*torso_surface_seams(class_name, spec, collection, rig, mats),
             *limb_surface_seams(class_name, spec, collection, rig, mats, -1),
             *limb_surface_seams(class_name, spec, collection, rig, mats, 1)]
    gloves = [*articulated_glove(class_name, spec, collection, rig, mats, -1),
              *articulated_glove(class_name, spec, collection, rig, mats, 1)]
    boots = [*dedicated_boot(class_name, spec, collection, rig, mats, -1),
             *dedicated_boot(class_name, spec, collection, rig, mats, 1)]
    meshes = [obj for obj in bpy.data.objects
              if obj.type == "MESH" and obj.get("asset_layer") == "oversuit"]
    interfaces = [obj for obj in bpy.data.objects if obj.get("asset_layer") == "oversuit_interface"]
    for obj in meshes:
        obj["oversuit_pass"] = 21
    rig["asset_status"] = "PRIMARY_CLASS_OVERSUIT_V21_INTEGRATION_REVIEW"
    rig["oversuit_pass"] = 21
    rig["v21_removed_rebuild_parts"] = len(removed)
    rig["v21_surface_seam_count"] = len(seams)
    rig["v21_articulated_glove_part_count"] = len(gloves)
    rig["v21_dedicated_boot_part_count"] = len(boots)
    rig["v21_legacy_v11_mesh_count"] = 0
    rig["mesh_count"] = len(meshes)
    rig["wearer_independent"] = True
    bpy.context.scene["asset_status"] = "PRIMARY_CLASS_OVERSUIT_V21_INTEGRATION_REVIEW"
    bpy.context.scene["contains_player_body"] = False
    bpy.context.scene["contains_undersuit"] = False

    output = ASSET_DIR / f"PlayerOversuit_{class_name}_v21.blend"
    bpy.ops.outliner.orphans_purge(do_recursive=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
    render(class_name, meshes)
    fbx = export(class_name, rig, meshes, interfaces)
    bpy.ops.wm.save_as_mainfile(filepath=str(output), check_existing=False)
    return {
        "gameplay_class": class_name, "profile_role_alias": spec["role_alias"],
        "blend": str(output.relative_to(ROOT)).replace("\\", "/"),
        "fbx": str(fbx.relative_to(ROOT)).replace("\\", "/"),
        "mesh_count": len(meshes), "removed_rebuild_part_count": len(removed),
        "surface_seam_count": len(seams), "articulated_glove_part_count": len(gloves),
        "dedicated_boot_part_count": len(boots), "legacy_v11_mesh_count": 0,
        "previews": {view: str((PREVIEW_DIR / f"PlayerOversuit_{class_name}_v21_{view}.png")
                               .relative_to(ROOT)).replace("\\", "/")
                     for view in ("Front", "ThreeQuarter", "Rear", "RearThreeQuarter")},
    }


def main():
    variants = {name: build_class(name, spec) for name, spec in v16.CLASS_SPECS.items()}
    MANIFEST.write_text(json.dumps({
        "schema": 1, "version": 21, "status": "integrated_construction_review",
        "source_version": 20,
        "separation_contract": {"contains_player_body": False, "contains_undersuit": False,
                                "wearer_independent": True},
        "legacy_policy": "no V11 mesh remains",
        "integration_changes": ["surface-following converted mesh seams",
                                "two-ring elbow and knee bellows", "articulated glove pieces",
                                "dedicated rounded magnetic boots", "exportable seam topology"],
        "variants": variants,
        "promotion_gates": ["final shared skeleton", "animated fit", "pressure interface fit",
                            "Unreal skeletal import", "multiplayer equip replication"],
    }, indent=2), encoding="utf-8")
    print("PRIMARY_OVERSUITS_V21", f"classes={len(variants)}", MANIFEST)


if __name__ == "__main__":
    main()
