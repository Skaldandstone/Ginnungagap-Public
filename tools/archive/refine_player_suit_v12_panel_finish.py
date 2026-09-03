"""Refine V11 conformal armor with intentional panel breaks and service details."""

from __future__ import annotations

import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerSuit_Production_v11.blend"
OUTPUT = SUIT_DIR / "PlayerSuit_Production_v12.blend"
PREVIEWS = SUIT_DIR / "Production_v12_Previews"
LEDGER = SUIT_DIR / "PlayerSuit_Production_v12_Passes.json"


def material(name, color, metallic, roughness, emission=None):
    value = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    value.use_nodes = True
    bsdf = value.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission and "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1)
        bsdf.inputs["Emission Strength"].default_value = 2.2
    return value


def attach(obj, collection, mat, bone, bevel=.003):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    obj.data.materials.append(mat)
    if obj.type == "MESH" and bevel:
        modifier = obj.modifiers.new("V12_ManufacturedEdge", "BEVEL")
        modifier.width = bevel
        modifier.segments = 3
    armature = bpy.data.objects["RIG_PlayerSuit_Production_v12"]
    world = obj.matrix_world.copy()
    obj.parent = armature
    obj.parent_type = "BONE"
    obj.parent_bone = bone
    obj.matrix_world = world
    obj["rig_attachment"] = bone
    obj["v12_panel_finish"] = True
    return obj


def box(name, location, scale, collection, mat, bone="chest", rotation=(0, 0, 0), bevel=.003):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return attach(obj, collection, mat, bone, bevel)


def cylinder(name, location, radius, depth, collection, mat, bone, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=depth,
                                       location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    return attach(obj, collection, mat, bone, .002)


def curve(name, points, radius, collection, mat, bone="chest"):
    data = bpy.data.curves.new(name + "_Curve", "CURVE")
    data.dimensions = "3D"
    data.bevel_depth = radius
    data.bevel_resolution = 3
    spline = data.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, data)
    collection.objects.link(obj)
    return attach(obj, collection, mat, bone, 0)


def render_reviews(scene, camera, visible):
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 800
    scene.render.resolution_y = 1000
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.camera = camera
    for obj in visible:
        obj.hide_render = False
    target = Vector((0, 0, .98))
    for label, position in {
        "Front": Vector((0, -4.4, 1.02)), "Back": Vector((0, 4.4, 1.02)),
        "Side": Vector((4.4, 0, 1.02)), "ThreeQuarter": Vector((3.1, -3.1, 1.06)),
    }.items():
        camera.location = position
        camera.data.lens = 60
        camera.rotation_euler = (target - position).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(PREVIEWS / f"PlayerSuit_Production_v12_{label}.png")
        bpy.ops.render.render(write_still=True)


def main():
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    armature = bpy.data.objects["RIG_PlayerSuit_Production_v11"]
    armature.name = "RIG_PlayerSuit_Production_v12"
    base = bpy.data.objects["SK_PlayerSuit_Production_v11_BaseGarment"]
    base.name = "SK_PlayerSuit_Production_v12_BaseGarment"
    collection = bpy.data.collections.new("SUIT_PRODUCTION_v12_PANEL_FINISH")
    bpy.context.scene.collection.children.link(collection)
    armor = bpy.data.materials["M_V11_MutedCeramic"]
    armor.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (.16, .19, .20, 1)
    armor.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = .43
    dark = material("M_V12_FlexibleSeal", (.008, .014, .018), .08, .76)
    metal = material("M_V12_ServiceMetal", (.035, .050, .058), .72, .27)
    orange = material("M_V12_SafetyMarking", (.46, .055, .008), .20, .37)
    glow = material("M_V12_StatusLight", (.01, .12, .15), .12, .28, (0, .65, .90))
    created, ledger = [], []

    def step(label, result):
        objects = result if isinstance(result, list) else ([result] if result else [])
        created.extend(objects)
        ledger.append({"pass": len(ledger) + 1, "label": label,
                       "objects": [obj.name for obj in objects]})

    def armor_microfinish():
        nodes = armor.node_tree.nodes
        noise = nodes.get("V12_CeramicMicroBreakup") or nodes.new("ShaderNodeTexNoise")
        noise.name = "V12_CeramicMicroBreakup"
        noise.inputs["Scale"].default_value = 55
        noise.inputs["Detail"].default_value = 2.0
        armor["v12_finish"] = "restrained ceramic micro-breakup; no painted panel illusion"
        return None
    step("Darken and roughen conformal armor", armor_microfinish())
    step("Chest center pressure seam", box("SKV12_ChestCenterSeal", (0, -.174, 1.315),
                                           (.009, .008, .095), collection, dark, bevel=.002))
    step("Chest lower gasket", curve("SKV12_ChestLowerGasket",
                                      [(-.175, -.125, 1.225), (0, -.175, 1.215), (.175, -.125, 1.225)],
                                      .006, collection, dark))
    step("Clavicle service rail", curve("SKV12_ClavicleRail",
                                         [(-.155, -.110, 1.395), (0, -.160, 1.410), (.155, -.110, 1.395)],
                                         .0045, collection, metal))
    step("Shoulder cuff seals", [cylinder(f"SKV12_ShoulderSeal_{side}", (x, -.010, 1.235),
                                          .064, .018, collection, dark, f"upperarm_{side.lower()}")
                                    for side, x in (("L", -.275), ("R", .275))])
    step("Forearm closure rails", [box(f"SKV12_ForearmClosure_{side}", (x, -.105, 1.050),
                                        (.011, .007, .090), collection, metal,
                                        f"lowerarm_{side.lower()}", bevel=.002)
                                     for side, x in (("L", -.350), ("R", .350))])
    step("Glove rotary seals", [cylinder(f"SKV12_GloveSeal_{side}", (x, -.025, .945),
                                         .046, .014, collection, dark, f"hand_{side.lower()}")
                                   for side, x in (("L", -.365), ("R", .365))])
    step("Waist pressure belt", curve("SKV12_WaistSeal",
                                       [(-.165, -.105, .900), (0, -.165, .885), (.165, -.105, .900)],
                                       .007, collection, dark, "pelvis"))
    step("Thigh access closures", [box(f"SKV12_ThighClosure_{side}", (x, -.104, .710),
                                        (.009, .006, .105), collection, metal,
                                        f"thigh_{side.lower()}", bevel=.002)
                                      for side, x in (("L", -.142), ("R", .142))])
    step("Knee flex gaskets", [curve(f"SKV12_KneeGasket_{side}",
                                      [(x-.045, -.090, .595), (x, -.125, .605), (x+.045, -.090, .595)],
                                      .005, collection, dark, f"calf_{side.lower()}")
                                  for side, x in (("L", -.128), ("R", .128))])
    step("Ankle flex gaskets", [cylinder(f"SKV12_AnkleSeal_{side}", (x, -.015, .225),
                                         .055, .018, collection, dark, f"foot_{side.lower()}")
                                    for side, x in (("L", -.128), ("R", .128))])
    step("Helmet side hinges", [cylinder(f"SKV12_HelmetHinge_{side}", (x, -.015, 1.665),
                                         .020, .020, collection, metal, "head", (0, math.pi/2, 0))
                                  for side, x in (("L", -.145), ("R", .145))])
    step("Helmet front latch", box("SKV12_HelmetFrontLatch", (0, -.145, 1.510),
                                    (.035, .012, .013), collection, orange, bevel=.003))
    step("Slim life-support chassis", box("SKV12_LifeSupportChassis", (0, .165, 1.235),
                                           (.145, .045, .195), collection, metal, bevel=.012))
    step("Replaceable life-support canisters", [cylinder(f"SKV12_Canister_{side}", (x, .225, 1.235),
                                                           .031, .260, collection, armor, "chest")
                                                  for side, x in (("L", -.088), ("R", .088))])
    step("Backpack regulator and rescue handle", [
        cylinder("SKV12_BackpackRegulator", (0, .230, 1.345), .035, .024, collection,
                 orange, "chest", (math.pi/2, 0, 0)),
        curve("SKV12_RescueHandle", [(-.070, .210, 1.430), (0, .250, 1.455), (.070, .210, 1.430)],
              .008, collection, orange),
    ])
    step("Chest telemetry recess", box("SKV12_ChestTelemetry", (.075, -.173, 1.325),
                                        (.028, .006, .020), collection, glow, bevel=.002))
    step("Suit status lamps", [box(f"SKV12_StatusLamp_{i}", (-.065+i*.018, -.176, 1.360),
                                   (.005, .004, .005), collection, glow, bevel=.001)
                                for i in range(3)])

    if len(ledger) != 18:
        raise RuntimeError(f"Expected 18 V12 passes, found {len(ledger)}")
    rejected_prefixes = (
        "SKV12_ShoulderSeal_", "SKV12_ForearmClosure_", "SKV12_GloveSeal_",
        "SKV12_ThighClosure_", "SKV12_KneeGasket_", "SKV12_AnkleSeal_",
    )
    rejected_names = []
    rejected_exact = {
        "SKV12_WaistSeal", "SKV12_ChestLowerGasket", "SKV12_ClavicleRail",
        "SKV12_RescueHandle",
    }
    for obj in created:
        if obj.name.startswith(rejected_prefixes) or obj.name in rejected_exact:
            obj.hide_render = True
            obj["v12_review_status"] = "rejected_floating_attachment"
            rejected_names.append(obj.name)
    base["asset_status"] = "ART_DIRECTION_REVIEW_V12_PANEL_FINISH"
    base["runtime_replacement"] = False
    base["v12_pass_count"] = len(ledger)
    LEDGER.write_text(json.dumps({"schema": 1, "asset": "PlayerSuit_Production_v12",
                                  "pass_count": len(ledger), "passes": ledger,
                                  "new_object_count": len(created),
                                  "rejected_after_visual_review": rejected_names}, indent=2), encoding="utf-8")
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    original = bpy.context.window.scene
    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    bpy.context.window.scene = scene
    render_reviews(scene, bpy.data.objects["CAM_HighPolyReview"],
                   [base, *[obj for obj in created if not obj.get("v12_review_status")]])
    bpy.context.window.scene = original
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V12_PANEL_FINISH", f"passes={len(ledger)}", f"objects={len(created)}", f"output={OUTPUT}")


if __name__ == "__main__":
    main()
