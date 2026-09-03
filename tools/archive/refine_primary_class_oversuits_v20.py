"""V20 tailoring and surface-construction pass for primary class oversuits.

V19 established clean dedicated shells. V20 reduces their mannequin-like volume
and adds pressure-garment seams, articulation bellows, piping, fabric response,
and class-specific manufactured surface detail.

Run with Blender:
  blender --background --python tools/refine_primary_class_oversuits_v20.py -- <project-root>
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
PREVIEW_DIR = ASSET_DIR / "Previews_v20"
EXPORT_DIR = ROOT / "Build" / "Unreal" / "PlayerSuits" / "PrimaryOversuits_v20"
MANIFEST = ASSET_DIR / "PrimaryOversuits_v20_Manifest.json"


TAILOR_SCALE = {
    "SmoothUpperTorso": (1.00, .84, .98),
    "SmoothAbdomen": (.93, .76, .90),
    "PelvisPressureBridge": (.91, .80, .86),
    "ForearmGauntlet": (.87, .82, .94),
    "GloveShell": (.80, .74, .78),
    "GloveKnuckle": (.86, .78, .82),
    "ThighGaiter": (.86, .82, .96),
    "KneeBellows": (.89, .76, .80),
    "KneePad": (.91, .82, .88),
    "ShinGaiter": (.87, .82, .96),
    "UnderarmPressureBellows": (.91, .82, .92),
    "WristPressureCuff": (.94, .94, .90),
}


def material(name, color, metallic, roughness, textile=False):
    mat = v16.material(name, color, metallic, roughness)
    if textile:
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = nodes.get("Principled BSDF")
        noise = nodes.get("V20_FinePressureWeave") or nodes.new("ShaderNodeTexNoise")
        noise.name = "V20_FinePressureWeave"
        noise.noise_dimensions = "3D"
        noise.inputs["Scale"].default_value = 135.0
        noise.inputs["Detail"].default_value = 2.2
        noise.inputs["Roughness"].default_value = .62
        texcoord = nodes.get("PBR Generated Coordinates")
        if texcoord and not noise.inputs["Vector"].is_linked:
            links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])
        bump = nodes.get("V20_TextileBump") or nodes.new("ShaderNodeBump")
        bump.name = "V20_TextileBump"
        bump.inputs["Strength"].default_value = .075
        bump.inputs["Distance"].default_value = .0015
        if not bump.inputs["Height"].is_linked:
            links.new(noise.outputs["Fac"], bump.inputs["Height"])
        if bsdf:
            for link in list(bsdf.inputs["Normal"].links):
                links.remove(link)
            links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        mat["v20_pressure_textile"] = True
    return mat


def mats_for(class_name, spec):
    inherited = v18.materials(class_name, spec)
    inherited["fabric"] = material(f"M_OVR20_{class_name}_TailoredPressureFabric",
                                   (.020, .028, .032), .015, .72, True)
    inherited["seam"] = material(f"M_OVR20_{class_name}_SeamTape",
                                 (.055, .065, .068), .02, .78)
    inherited["piping"] = material(f"M_OVR20_{class_name}_RolePiping",
                                   tuple(value*.62 for value in spec["accent"]), .08, .54)
    return inherited


def reshape_pressure_shells():
    reshaped = []
    for obj in bpy.data.objects:
        if obj.type != "MESH" or obj.get("asset_layer") != "oversuit":
            continue
        scale = next((value for token, value in TAILOR_SCALE.items() if token in obj.name), None)
        if not scale:
            continue
        obj.scale.x *= scale[0]
        obj.scale.y *= scale[1]
        obj.scale.z *= scale[2]
        obj["v20_tailored_scale"] = scale
        obj["oversuit_pass"] = 20
        reshaped.append(obj.name)
    return reshaped


def assign_pressure_fabric(mat):
    assigned = []
    tokens = ("SmoothUpperTorso", "SmoothAbdomen", "PelvisPressureBridge",
              "ForearmGauntlet", "GloveShell", "ThighGaiter", "KneeBellows",
              "ShinGaiter", "UnderarmPressureBellows", "WristPressureCuff",
              "ElbowPressureCuff", "AnkleLockRing")
    for obj in bpy.data.objects:
        if obj.type == "MESH" and any(token in obj.name for token in tokens):
            obj.data.materials.clear()
            obj.data.materials.append(mat)
            obj["v20_tailored_pressure_fabric"] = True
            assigned.append(obj.name)
    return assigned


def mark(obj, module, stage, boundary="garment_construction_detail"):
    obj["oversuit_pass"] = 20
    obj["v20_surface_construction"] = True
    obj["class_module"] = module
    obj["donning_stage"] = stage
    obj["pressure_boundary"] = boundary
    return obj


def tube(name, start, end, radius, collection, mat, class_name, module, rig,
         bone="chest", stage=50):
    obj = v16.tube_between(name, start, end, radius, collection, mat, class_name,
                           module, rig, bone)
    return mark(obj, module, stage)


def ring(name, location, major, minor, collection, mat, class_name, module,
         rig, bone, stage):
    obj = v16.torus(name, location, major, minor, collection, mat, class_name,
                    module, rig, bone)
    return mark(obj, module, stage, "articulation_bellows")


def capsule(name, location, scale, collection, mat, class_name, module,
            rig, bone="chest", stage=50):
    obj = v18.capsule(name, location, scale, collection, mat, class_name,
                      module, rig, bone, stage)
    return mark(obj, module, stage)


def torso_seams(class_name, spec, collection, rig, mats):
    p = f"OVR20_{spec['code']}"
    parts = [
        tube(f"{p}_CenterClosure", (0, -.108, .955), (0, -.128, 1.455), .0035,
             collection, mats["seam"], class_name, "center_pressure_closure", rig),
        tube(f"{p}_ChestSeam_L", (0, -.132, 1.365), (-.170, -.108, 1.205), .003,
             collection, mats["seam"], class_name, "diagonal_chest_seam", rig),
        tube(f"{p}_ChestSeam_R", (0, -.132, 1.365), (.170, -.108, 1.205), .003,
             collection, mats["seam"], class_name, "diagonal_chest_seam", rig),
    ]
    # Subtle abdominal construction lines break the featureless V19 volume.
    for index, z in enumerate((1.135, 1.075, 1.015, .965)):
        parts.append(tube(f"{p}_AbdomenSeam_{index+1}", (-.135, -.105, z),
                          (.135, -.105, z), .0025, collection, mats["seam"], class_name,
                          "abdominal_panel_seam", rig, "spine_02", 50))
    # Restrained class piping tracks one shoulder and one torso edge.
    parts += [
        tube(f"{p}_RolePiping_L", (-.155, -.118, 1.410), (-.165, -.105, 1.165), .0038,
             collection, mats["piping"], class_name, "role_piping", rig),
        tube(f"{p}_RolePiping_R", (.155, -.118, 1.410), (.165, -.105, 1.165), .0038,
             collection, mats["piping"], class_name, "role_piping", rig),
    ]
    return parts


def limb_seams(class_name, spec, collection, rig, mats, side):
    p = f"OVR20_{spec['code']}"
    label = "L" if side < 0 else "R"
    limb = label.lower()
    x_arm = side*.350
    x_leg = side*.128
    parts = []
    # Triple elbow and knee rings read as flexible accordion joints.
    for index, z in enumerate((1.050, 1.080, 1.110)):
        parts.append(ring(f"{p}_ElbowBellow_{label}_{index+1}", (x_arm, -.010, z),
                          .053, .0042, collection, mats["seam"], class_name,
                          "elbow_accordion_bellow", rig, f"lowerarm_{limb}", 40))
    for index, z in enumerate((.495, .525, .555)):
        parts.append(ring(f"{p}_KneeBellow_{label}_{index+1}", (x_leg, -.002, z),
                          .068, .0045, collection, mats["seam"], class_name,
                          "knee_accordion_bellow", rig, f"calf_{limb}", 20))
    # Longitudinal outer-leg seam and class-color piping.
    outer = side*.190
    parts += [
        tube(f"{p}_ThighOuterSeam_{label}", (outer, -.028, .865),
             (outer, -.040, .605), .003, collection, mats["seam"], class_name,
             "thigh_outer_seam", rig, f"thigh_{limb}", 30),
        tube(f"{p}_ThighRolePiping_{label}", (side*.178, -.063, .845),
             (side*.178, -.068, .625), .0032, collection, mats["piping"], class_name,
             "limb_role_piping", rig, f"thigh_{limb}", 30),
        tube(f"{p}_ShinOuterSeam_{label}", (side*.180, -.020, .455),
             (side*.170, -.025, .245), .003, collection, mats["seam"], class_name,
             "shin_outer_seam", rig, f"calf_{limb}", 20),
        capsule(f"{p}_PalmPlate_{label}", (side*.382, -.100, .955),
                (.048, .012, .040), collection, mats["armor"], class_name,
                "rounded_palm_plate", rig, f"hand_{limb}", 40),
    ]
    # Three raised knuckle pads replace a single mitten-like highlight.
    for index, offset in enumerate((-.025, 0, .025)):
        parts.append(capsule(f"{p}_KnucklePad_{label}_{index+1}",
                             (side*.382 + offset, -.118, .985), (.010, .007, .018),
                             collection, mats["secondary"], class_name, "glove_knuckle_pad",
                             rig, f"hand_{limb}", 40))
    return parts


def class_surface(class_name, spec, collection, rig, mats):
    p = f"OVR20_{spec['code']}"
    parts = []
    if class_name == "Marine":
        for index, z in enumerate((1.235, 1.285, 1.335)):
            parts.append(capsule(f"{p}_CuirassRib_{index+1}", (0, -.235, z),
                                 (.105, .006, .006), collection, mats["metal"], class_name,
                                 "ballistic_cuirass_rib", rig))
    elif class_name == "Scientist":
        for index, x in enumerate((-.035, 0, .035)):
            parts.append(capsule(f"{p}_InstrumentDial_{index+1}", (x, -.224, 1.280),
                                 (.009, .005, .009), collection, mats["piping"], class_name,
                                 "instrument_dial", rig))
    elif class_name == "Technician":
        for index, z in enumerate((1.220, 1.260, 1.300, 1.340)):
            parts.append(tube(f"{p}_ServiceBibRib_{index+1}", (-.085, -.225, z),
                              (.085, -.225, z), .0032, collection, mats["metal"], class_name,
                              "service_bib_heat_rib", rig))
    else:
        # Clean double perimeter cue rather than a symbol painted on the suit.
        parts += [
            tube(f"{p}_TelemetryCleanLine_L", (-.105, -.226, 1.225),
                 (-.105, -.226, 1.365), .0032, collection, mats["piping"], class_name,
                 "sterile_telemetry_border", rig),
            tube(f"{p}_TelemetryCleanLine_R", (.105, -.226, 1.225),
                 (.105, -.226, 1.365), .0032, collection, mats["piping"], class_name,
                 "sterile_telemetry_border", rig),
        ]
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
    scene.view_settings.exposure = .15
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
        scene.render.filepath = str(PREVIEW_DIR / f"PlayerOversuit_{class_name}_v20_{label}.png")
        bpy.ops.render.render(write_still=True)


def export(class_name, rig, meshes, interfaces):
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORT_DIR / f"SKM_PlayerOversuit_{class_name}_v20.fbx"
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
    source = ASSET_DIR / f"PlayerOversuit_{class_name}_v19.blend"
    bpy.ops.wm.open_mainfile(filepath=str(source))
    bpy.context.preferences.filepaths.save_version = 0
    rig = bpy.data.objects[f"RIG_PlayerOversuit_{class_name}_v19"]
    rig.name = f"RIG_PlayerOversuit_{class_name}_v20"
    collection = bpy.data.collections.new(f"OVERSUIT_{class_name.upper()}_V20_SURFACE_CONSTRUCTION")
    bpy.context.scene.collection.children.link(collection)
    mats = mats_for(class_name, spec)
    reshaped = reshape_pressure_shells()
    fabric_assigned = assign_pressure_fabric(mats["fabric"])
    surface = [*torso_seams(class_name, spec, collection, rig, mats),
               *limb_seams(class_name, spec, collection, rig, mats, -1),
               *limb_seams(class_name, spec, collection, rig, mats, 1),
               *class_surface(class_name, spec, collection, rig, mats)]
    meshes = [obj for obj in bpy.data.objects
              if obj.type == "MESH" and obj.get("asset_layer") == "oversuit"]
    interfaces = [obj for obj in bpy.data.objects if obj.get("asset_layer") == "oversuit_interface"]
    for obj in meshes:
        obj["oversuit_pass"] = 20
    rig["asset_status"] = "PRIMARY_CLASS_OVERSUIT_V20_TAILORED_SURFACE_REVIEW"
    rig["oversuit_pass"] = 20
    rig["v20_reshaped_shell_count"] = len(reshaped)
    rig["v20_textile_shell_count"] = len(fabric_assigned)
    rig["v20_surface_detail_count"] = len(surface)
    rig["mesh_count"] = len(meshes)
    rig["wearer_independent"] = True
    bpy.context.scene["asset_status"] = "PRIMARY_CLASS_OVERSUIT_V20_TAILORED_SURFACE_REVIEW"
    bpy.context.scene["contains_player_body"] = False
    bpy.context.scene["contains_undersuit"] = False

    output = ASSET_DIR / f"PlayerOversuit_{class_name}_v20.blend"
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
        "mesh_count": len(meshes), "reshaped_shell_count": len(reshaped),
        "textile_shell_count": len(fabric_assigned), "surface_detail_count": len(surface),
        "previews": {view: str((PREVIEW_DIR / f"PlayerOversuit_{class_name}_v20_{view}.png")
                               .relative_to(ROOT)).replace("\\", "/")
                     for view in ("Front", "ThreeQuarter", "Rear", "RearThreeQuarter")},
    }


def main():
    variants = {name: build_class(name, spec) for name, spec in v16.CLASS_SPECS.items()}
    MANIFEST.write_text(json.dumps({
        "schema": 1, "version": 20, "status": "tailored_surface_construction_review",
        "source_version": 19,
        "separation_contract": {"contains_player_body": False, "contains_undersuit": False,
                                "wearer_independent": True},
        "surface_language": ["fine bonded pressure textile", "center pressure closure",
                             "diagonal chest panels", "abdominal seams", "elbow/knee bellows",
                             "longitudinal limb seams", "palm and knuckle protection",
                             "restrained class piping", "class-specific manufactured detail"],
        "variants": variants,
        "promotion_gates": ["final shared skeleton", "animated fit", "pressure interface fit",
                            "Unreal skeletal import", "multiplayer equip replication"],
    }, indent=2), encoding="utf-8")
    print("PRIMARY_OVERSUITS_V20", f"classes={len(variants)}", MANIFEST)


if __name__ == "__main__":
    main()
