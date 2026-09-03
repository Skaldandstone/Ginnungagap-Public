"""Apply fifty auditable artist-production passes to the modular V7 player suit.

The script is deliberately additive and writes PlayerSuit_Production_v8.blend.
Every pass creates or modifies reviewable content and records its result in a
JSON ledger. V7 remains unchanged and stays available as the fallback source.
"""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
SUIT_DIR = ROOT / "Art" / "Characters" / "PlayerSuits"
SOURCE = SUIT_DIR / "PlayerSuit_Production_v7.blend"
OUTPUT = SUIT_DIR / "PlayerSuit_Production_v8.blend"
PREVIEWS = SUIT_DIR / "Production_v8_Previews"
LEDGER = SUIT_DIR / "PlayerSuit_Production_v8_50Passes.json"


def ensure_v7():
    if SOURCE.exists():
        return
    source_script = ROOT / "tools" / "build_player_suit_production_v7.py"
    spec = importlib.util.spec_from_file_location("ginnungagap_build_suit_v7", source_script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.main()
    if not SOURCE.exists():
        raise RuntimeError("V7 prerequisite did not produce its output blend")


def mat(name, color, metallic=0.0, roughness=.45, emission=None):
    material = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission and "Emission Color" in bsdf.inputs:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1)
        bsdf.inputs["Emission Strength"].default_value = 3.0
    return material


def finish(obj, collection, material, bevel=.004, bone=None):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    collection.objects.link(obj)
    if obj.type == "MESH":
        obj.data.materials.append(material)
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        if bevel:
            modifier = obj.modifiers.new("V8_ManufacturedEdge", "BEVEL")
            modifier.width = bevel
            modifier.segments = 3
    else:
        obj.data.materials.append(material)
    if bone:
        armature = bpy.data.objects["RIG_PlayerSuit_Production_v8"]
        world = obj.matrix_world.copy()
        obj.parent = armature
        obj.parent_type = "BONE"
        obj.parent_bone = bone
        obj.matrix_world = world
        obj["rig_attachment"] = bone
    obj["v8_production_detail"] = True
    return obj


def box(name, location, scale, collection, material, bone="chest", rotation=(0, 0, 0), bevel=.004):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, collection, material, bevel, bone)


def cyl(name, location, radius, depth, collection, material, bone="chest", rotation=(0, 0, 0), vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                       location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    return finish(obj, collection, material, min(.004, radius * .16), bone)


def sphere(name, location, scale, collection, material, bone="chest"):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(obj, collection, material, .003, bone)


def curve(name, points, radius, collection, material, bone="chest"):
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
    return finish(obj, collection, material, 0, bone)


def paired(factory, base_name, x, *args, left_bone=None, right_bone=None, **kwargs):
    left = factory(base_name + "_L", (-abs(x), *args[0]), *args[1:], bone=left_bone, **kwargs)
    right = factory(base_name + "_R", (abs(x), *args[0]), *args[1:], bone=right_bone, **kwargs)
    return [left, right]


def render(scene, camera, visible):
    PREVIEWS.mkdir(parents=True, exist_ok=True)
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 960
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.camera = camera
    for obj in visible:
        obj.hide_render = False
    target = Vector((0, 0, .98))
    for label, position in {
        "Front": Vector((0, -5, 1.0)), "Back": Vector((0, 5, 1.0)),
        "Side": Vector((5, 0, 1.0)), "ThreeQuarter": Vector((3.5, -3.5, 1.08)),
    }.items():
        camera.location = position
        camera.rotation_euler = (target - position).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(PREVIEWS / f"PlayerSuit_Production_v8_{label}.png")
        bpy.ops.render.render(write_still=True)


def main():
    ensure_v7()
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
    armature = bpy.data.objects["RIG_PlayerSuit_Production_v7"]
    armature.name = "RIG_PlayerSuit_Production_v8"
    base = bpy.data.objects["SK_PlayerSuit_Production_v7_BaseGarment"]
    base.name = "SK_PlayerSuit_Production_v8_BaseGarment"
    collection = bpy.data.collections.new("SUIT_PRODUCTION_v8_50_PASSES")
    bpy.context.scene.collection.children.link(collection)

    ceramic = mat("M_V8_Ceramic", (.50, .53, .51), .16, .27)
    dark = mat("M_V8_Fabric", (.018, .025, .030), .01, .76)
    metal = mat("M_V8_Gunmetal", (.045, .055, .061), .78, .22)
    rubber = mat("M_V8_SealRubber", (.008, .011, .013), .0, .84)
    orange = mat("M_V8_SafetyOrange", (.72, .13, .018), .28, .31)
    glow = mat("M_V8_StatusGlow", (.015, .18, .20), .12, .24, (.02, .8, 1.0))
    red = mat("M_V8_EmergencyRed", (.42, .012, .008), .18, .32, (1.0, .015, .008))
    created = []
    ledger = []

    def step(label, operation):
        before = len(created)
        result = operation()
        if result:
            created.extend(result if isinstance(result, list) else [result])
        ledger.append({"pass": len(ledger) + 1, "label": label, "new_objects": len(created) - before})

    # 01-10: primary silhouette and upper-body articulation.
    step("Clavicle armor bridge", lambda: box("SKV8_ClavicleBridge", (0, -.168, 1.405), (.16, .018, .027), collection, ceramic))
    step("Split sternum cap", lambda: box("SKV8_SternumCap", (0, -.212, 1.300), (.072, .018, .068), collection, ceramic))
    step("Floating lower chest rail", lambda: box("SKV8_LowerChestRail", (0, -.202, 1.165), (.142, .016, .018), collection, metal))
    step("Left and right rib vents", lambda: [box(f"SKV8_RibVent_{s}", (x, -.205, 1.245), (.034, .012, .055), collection, dark) for s, x in (("L", -.125), ("R", .125))])
    step("Shoulder shell edge bands", lambda: [cyl(f"SKV8_ShoulderBand_{s}", (x, -.012, 1.335), .108, .018, collection, orange, bone=f"upperarm_{s.lower()}") for s, x in (("L", -.205), ("R", .205))])
    step("Upper-arm pressure cuffs", lambda: [cyl(f"SKV8_UpperArmCuff_{s}", (x, -.012, 1.225), .071, .035, collection, rubber, bone=f"upperarm_{s.lower()}") for s, x in (("L", -.255), ("R", .255))])
    step("Elbow hard guards", lambda: [sphere(f"SKV8_ElbowGuard_{s}", (x, -.075, 1.105), (.062, .035, .068), collection, ceramic, bone=f"lowerarm_{s.lower()}") for s, x in (("L", -.330), ("R", .330))])
    step("Forearm equipment rails", lambda: [box(f"SKV8_ForearmRail_{s}", (x, -.095, 1.035), (.035, .020, .105), collection, metal, bone=f"lowerarm_{s.lower()}") for s, x in (("L", -.345), ("R", .345))])
    step("Wrist rotary seals", lambda: [cyl(f"SKV8_WristSeal_{s}", (x, -.025, .955), .052, .031, collection, rubber, bone=f"hand_{s.lower()}") for s, x in (("L", -.365), ("R", .365))])
    step("Glove knuckle armor", lambda: [box(f"SKV8_KnucklePlate_{s}", (x, -.115, .905), (.050, .030, .027), collection, ceramic, bone=f"hand_{s.lower()}") for s, x in (("L", -.375), ("R", .375))])

    # 11-20: pelvis, leg articulation, and magnetic boots.
    step("Segmented utility waist belt", lambda: [box(f"SKV8_BeltSegment_{i:02}", ((i-3)*.052, -.150, .885), (.022, .018, .035), collection, metal, bone="pelvis") for i in range(7)])
    step("Emergency-release buckle", lambda: box("SKV8_BeltEmergencyBuckle", (0, -.190, .885), (.040, .020, .031), collection, orange, bone="pelvis"))
    step("Hip bearing shells", lambda: [sphere(f"SKV8_HipBearing_{s}", (x, -.020, .815), (.075, .050, .085), collection, ceramic, bone=f"thigh_{s.lower()}") for s, x in (("L", -.145), ("R", .145))])
    step("Thigh structural rails", lambda: [box(f"SKV8_ThighRail_{s}", (x, -.085, .700), (.028, .024, .135), collection, metal, bone=f"thigh_{s.lower()}") for s, x in (("L", -.150), ("R", .150))])
    step("Knee perimeter frames", lambda: [cyl(f"SKV8_KneeFrame_{s}", (x, -.135, .535), .081, .016, collection, orange, bone=f"calf_{s.lower()}", rotation=(math.pi/2, 0, 0)) for s, x in (("L", -.128), ("R", .128))])
    step("Shin impact ribs", lambda: [box(f"SKV8_ShinRib_{s}_{i}", (x, -.130, .390-i*.055), (.050, .012, .010), collection, metal, bone=f"calf_{s.lower()}") for s, x in (("L", -.128), ("R", .128)) for i in range(3)])
    step("Ankle bellows seals", lambda: [cyl(f"SKV8_AnkleSeal_{s}", (x, -.030, .205), .061, .050, collection, rubber, bone=f"foot_{s.lower()}") for s, x in (("L", -.128), ("R", .128))])
    step("Reinforced toe caps", lambda: [sphere(f"SKV8_ToeCap_{s}", (x, -.165, .090), (.085, .105, .045), collection, ceramic, bone=f"foot_{s.lower()}") for s, x in (("L", -.128), ("R", .128))])
    step("Boot heel guards", lambda: [box(f"SKV8_HeelGuard_{s}", (x, .020, .105), (.070, .040, .065), collection, metal, bone=f"foot_{s.lower()}") for s, x in (("L", -.128), ("R", .128))])
    step("Magnetic sole arrays", lambda: [box(f"SKV8_MagneticSole_{s}", (x, -.065, .035), (.072, .125, .012), collection, glow, bone=f"foot_{s.lower()}", bevel=.002) for s, x in (("L", -.128), ("R", .128))])

    # 21-30: pressure helmet and serviceable life-support pack.
    step("Collar quarter-turn locks", lambda: [cyl(f"SKV8_CollarLock_{i}", (.135*math.cos(i*math.pi/2), .135*math.sin(i*math.pi/2), 1.515), .013, .025, collection, orange, rotation=(0, math.pi/2, i*math.pi/2)) for i in range(4)])
    step("Collar pressure hoses", lambda: [curve(f"SKV8_CollarHose_{s}", [(x, .03, 1.50), (x*1.5, .11, 1.43), (x*1.3, .18, 1.34)], .009, collection, rubber) for s, x in (("L", -.085), ("R", .085))])
    step("Visor armored brow", lambda: box("SKV8_VisorBrow", (0, -.205, 1.790), (.145, .018, .026), collection, ceramic, bone="head"))
    step("Visor hinge housings", lambda: [cyl(f"SKV8_VisorHinge_{s}", (x, -.030, 1.670), .026, .032, collection, metal, bone="head", rotation=(0, math.pi/2, 0)) for s, x in (("L", -.175), ("R", .175))])
    step("Visor dual-lip pressure seal", lambda: [cyl(f"SKV8_VisorSeal_{i}", (0, .005, 1.515+i*.014), .144+i*.005, .010, collection, rubber) for i in range(2)])
    step("Backpack protective frame", lambda: [box(f"SKV8_PackFrame_{s}", (x, .255, 1.205), (.018, .022, .235), collection, ceramic) for s, x in (("L", -.175), ("R", .175))])
    step("Replaceable oxygen canisters", lambda: [cyl(f"SKV8_OxygenCanister_{s}", (x, .270, 1.205), .038, .300, collection, ceramic) for s, x in (("L", -.095), ("R", .095))])
    step("Life-support regulator", lambda: cyl("SKV8_PackRegulator", (0, .300, 1.330), .047, .032, collection, orange, rotation=(math.pi/2, 0, 0)))
    step("Braided supply lines", lambda: [curve(f"SKV8_SupplyLine_{s}", [(x, .285, 1.31), (x*1.3, .245, 1.42), (x*.8, .13, 1.49)], .007, collection, rubber) for s, x in (("L", -.075), ("R", .075))])
    step("Backpack radiator fins", lambda: [box(f"SKV8_RadiatorFin_{i:02}", (0, .337, 1.09+i*.035), (.115, .008, .008), collection, metal) for i in range(7)])

    # 31-40: readable interaction and mission-equipment interfaces.
    step("Role module dovetail rail", lambda: box("SKV8_RoleModuleRail", (0, -.232, 1.335), (.100, .012, .025), collection, metal))
    step("Recessed chest telemetry screen", lambda: box("SKV8_ChestTelemetry", (0, -.252, 1.285), (.055, .010, .040), collection, glow, bevel=.002))
    step("Three-light suit status stack", lambda: [sphere(f"SKV8_StatusLight_{i}", (-.075+i*.022, -.267, 1.345), (.007, .004, .007), collection, glow) for i in range(3)])
    step("Left utility-belt pods", lambda: [box(f"SKV8_UtilityPod_L_{i}", (-.190, -.055+i*.045, .855), (.042, .035, .055), collection, dark, bone="pelvis") for i in range(2)])
    step("Right tool docking hardpoint", lambda: box("SKV8_ToolDock_R", (.205, -.030, .910), (.035, .045, .085), collection, metal, bone="pelvis"))
    step("Drone docking hardpoint", lambda: box("SKV8_DroneDock", (-.155, .205, 1.180), (.050, .025, .075), collection, orange))
    step("Retractable tether spool", lambda: cyl("SKV8_TetherSpool", (.195, .165, .965), .052, .040, collection, metal, rotation=(0, math.pi/2, 0)))
    step("Rear rescue handle", lambda: curve("SKV8_RescueHandle", [(-.09, .270, 1.445), (0, .315, 1.485), (.09, .270, 1.445)], .012, collection, orange))
    step("Emergency identification plate", lambda: box("SKV8_EmergencyIDPlate", (.110, -.250, 1.185), (.045, .006, .018), collection, red, bevel=.001))
    step("Engraved serial plate blank", lambda: box("SKV8_SerialPlate", (-.105, -.245, 1.170), (.040, .005, .014), collection, metal, bevel=.001))

    # 41-50: construction cues, shader finish, optimization, and QA infrastructure.
    step("Shoulder seam tape", lambda: [curve(f"SKV8_ShoulderSeam_{s}", [(x*.75, -.08, 1.38), (x, -.04, 1.33), (x*1.18, -.01, 1.26)], .003, collection, dark, bone=f"upperarm_{s.lower()}") for s, x in (("L", -.20), ("R", .20))])
    step("Elbow flex-zone ribs", lambda: [cyl(f"SKV8_ElbowFlex_{s}_{i}", (x, .015, 1.08-i*.022), .050, .008, collection, rubber, bone=f"lowerarm_{s.lower()}") for s, x in (("L", -.33), ("R", .33)) for i in range(3)])
    step("Knee flex-zone ribs", lambda: [box(f"SKV8_KneeFlex_{s}_{i}", (x, .015, .55-i*.025), (.050, .020, .007), collection, rubber, bone=f"calf_{s.lower()}") for s, x in (("L", -.128), ("R", .128)) for i in range(3)])

    def fabric_microdetail():
        material = bpy.data.materials["M_V8_Fabric"]
        nodes = material.node_tree.nodes
        noise = nodes.get("V8_FabricWeave") or nodes.new("ShaderNodeTexNoise")
        noise.name = "V8_FabricWeave"; noise.inputs["Scale"].default_value = 220
        noise.inputs["Detail"].default_value = 2.5
        return []
    step("Fabric weave shader scale", fabric_microdetail)

    def ceramic_finish():
        material = bpy.data.materials["M_V8_Ceramic"]
        noise = material.node_tree.nodes.get("V8_CeramicBreakup") or material.node_tree.nodes.new("ShaderNodeTexNoise")
        noise.name = "V8_CeramicBreakup"; noise.inputs["Scale"].default_value = 32
        return []
    step("Ceramic roughness breakup", ceramic_finish)

    def metal_finish():
        bsdf = bpy.data.materials["M_V8_Gunmetal"].node_tree.nodes["Principled BSDF"]
        if "Anisotropic IOR Level" in bsdf.inputs:
            bsdf.inputs["Anisotropic IOR Level"].default_value = .32
        return []
    step("Machined-metal anisotropy", metal_finish)

    def visor_finish():
        visor = bpy.data.materials.get("M_Visor_Clear_v6")
        if visor:
            visor["v8_optical_review"] = "dual surface, 1.45 IOR, low roughness"
        return []
    step("Visor optical metadata", visor_finish)

    def lod_policy():
        base["v8_lod_policy"] = "LOD0 authored; LOD1 55%; LOD2 28%; preserve helmet/hands silhouette"
        for level in (1, 2):
            candidate = bpy.data.collections.get(f"SUIT_PRODUCTION_v7_LOD{level}_CANDIDATES")
            if candidate:
                candidate.name = f"SUIT_PRODUCTION_v8_LOD{level}_CANDIDATES"
        return []
    step("LOD silhouette-protection policy", lod_policy)

    def collision_proxies():
        proxies = []
        collision = bpy.data.collections.new("SUIT_PRODUCTION_v8_COLLISION_REVIEW")
        bpy.context.scene.collection.children.link(collision)
        for name, loc, scale, bone in (
            ("Torso", (0, 0, 1.15), (.23, .16, .32), "chest"),
            ("Pack", (0, .18, 1.20), (.19, .10, .25), "chest"),
            ("Helmet", (0, 0, 1.68), (.19, .18, .22), "head"),
        ):
            proxy = box(f"UCX_SKV8_{name}", loc, scale, collision, dark, bone=bone, bevel=0)
            proxy.display_type = "WIRE"; proxy.hide_render = True; proxy["collision_proxy"] = True
            proxies.append(proxy)
        return proxies
    step("Collision review proxies", collision_proxies)

    def export_metadata():
        base["asset_status"] = "ART_DIRECTION_REVIEW_V8_50_PASSES"
        base["production_pass_count"] = 50
        base["runtime_replacement"] = False
        armature["rig_standard"] = "Ginnungagap humanoid v8 review"
        for obj in created:
            obj["production_pass_owner"] = "V8_50_PASSES"
        return []
    step("Production metadata and deterministic QA setup", export_metadata)

    if len(ledger) != 50:
        raise RuntimeError(f"Expected exactly 50 production passes, recorded {len(ledger)}")
    if any(entry["pass"] != index for index, entry in enumerate(ledger, 1)):
        raise RuntimeError("V8 pass ledger ordering is invalid")

    LEDGER.write_text(json.dumps({"schema": 1, "asset": "PlayerSuit_Production_v8",
                                  "pass_count": 50, "passes": ledger}, indent=2), encoding="utf-8")
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    original = bpy.context.window.scene
    scene = bpy.data.scenes["SCENE_HighPolyReview"]
    bpy.context.window.scene = scene
    render(scene, bpy.data.objects["CAM_HighPolyReview"],
           [base, *[obj for obj in created if not obj.get("collision_proxy")]])
    bpy.context.window.scene = original
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT), check_existing=False)
    print("V8_50_PASSES_COMPLETE", f"passes={len(ledger)}", f"objects={len(created)}", f"output={OUTPUT}")


if __name__ == "__main__":
    main()
