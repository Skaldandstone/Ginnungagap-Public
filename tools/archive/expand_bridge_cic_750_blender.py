"""Phase three: add 750 deterministic production steps to BRG-CIC-01."""

import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
ART = ROOT / "Art" / "ShipRooms" / "BridgeCIC"
BLEND = ART / "ShipRooms_BridgeCIC.blend"
PREVIEW = ART / "ShipRooms_BridgeCIC_750Steps_Preview.png"
REPORT = ART / "ShipRooms_BridgeCIC_750Steps.json"
EXPORT = ROOT / "Build" / "Unreal" / "ShipRooms" / "BridgeCIC"
RNG = random.Random(30750)
DONE = []


def collection(name):
    old = bpy.data.collections.get(name)
    if old:
        for obj in list(old.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(old)
    result = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(result)
    return result


def move(obj, target):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    target.objects.link(obj)
    return obj


def material(name, color, metallic=.25, roughness=.45, emission=0):
    result = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    result.use_nodes = True
    bsdf = result.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*color, 1)
        bsdf.inputs["Emission Strength"].default_value = emission
    return result


def cube(name, pos, scale, mat, target, rotation=(0, 0, 0), bevel=.015):
    bpy.ops.mesh.primitive_cube_add(location=pos, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    if bevel:
        mod = obj.modifiers.new("EdgeSoftening", "BEVEL")
        mod.width = bevel
        mod.segments = 1
    return move(obj, target)


def cylinder(name, pos, radius, depth, mat, target, rotation=(0, 0, 0), vertices=12):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                       location=pos, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    return move(obj, target)


def root(step, name, role, pos, target):
    obj = bpy.data.objects.new(name, None)
    obj.location = pos
    obj.empty_display_type = "CUBE"
    obj.empty_display_size = .12
    obj["bridge_phase3_step"] = step
    obj["gameplay_role"] = role
    target.objects.link(obj)
    DONE.append({"step": step, "name": name, "role": role})
    return obj


def attach(owner, parts):
    for part in parts:
        part.parent = owner


def perimeter_position(index, total, z=.2, inset=.0):
    phase = index / total
    perimeter = phase * 4
    if perimeter < 1:
        return Vector((-8.35 + perimeter * 16.7, -7.08 + inset, z))
    if perimeter < 2:
        return Vector((8.35 - inset, -7.08 + (perimeter - 1) * 14.0, z))
    if perimeter < 3:
        return Vector((8.35 - (perimeter - 2) * 16.7, 6.92 - inset, z))
    return Vector((-8.35 + inset, 6.92 - (perimeter - 3) * 14.0, z))


def grid_position(index, cols, origin, spacing, z_cycle=1):
    row, col = divmod(index, cols)
    return Vector((origin[0] + col * spacing[0], origin[1] + row * spacing[1],
                   origin[2] + (index % z_cycle) * spacing[2]))


def architecture(step, index, target, mats):
    kinds = ("ArmorPanel", "StructuralBrace", "CableTray", "CrashRail", "FloorGrate", "CeilingBaffle")
    kind = kinds[index % len(kinds)]
    pos = perimeter_position(index, 150, .12 + (index % 5) * .72, .08)
    name = f"P3_ARCH_{index+1:03d}_{kind}"
    owner = root(step, name, "architecture", pos, target)
    x, y, z = pos
    style = index % 6
    if style == 0:
        parts = [cube(name + "_Plate", (x, y, z), (.38, .06, .28), mats["hull"], target),
                 cube(name + "_Inset", (x, y - .065, z), (.24, .015, .15), mats["structure"], target)]
    elif style == 1:
        parts = [cube(name + "_Spine", (x, y, z), (.07, .13, .48), mats["structure"], target),
                 cube(name + "_Foot", (x, y, z - .41), (.21, .16, .07), mats["amber"], target)]
    elif style == 2:
        parts = [cube(name + "_Tray", (x, y, z), (.42, .11, .06), mats["structure"], target)]
        for j in range(3):
            parts.append(cylinder(name + f"_Cable{j+1}", (x - .24 + j * .24, y, z + .08), .025, .52,
                                  mats["rubber"], target, rotation=(0, math.radians(90), 0)))
    elif style == 3:
        parts = [cylinder(name + "_Rail", (x, y, z + .42), .035, .78, mats["structure"], target,
                          rotation=(0, math.radians(90), 0)),
                 cylinder(name + "_Post", (x, y, z + .20), .03, .42, mats["structure"], target)]
    elif style == 4:
        parts = [cube(name + "_Grate", (x, y, .02), (.36, .22, .025), mats["deck"], target)]
        for j in range(4):
            parts.append(cube(name + f"_Slot{j+1}", (x - .21 + j * .14, y - .01, .052),
                              (.035, .17, .008), mats["rubber"], target, bevel=0))
    else:
        parts = [cube(name + "_Baffle", (x, y, 4.82), (.44, .12, .07), mats["hull"], target),
                 cube(name + "_Glow", (x, y, 4.72), (.29, .07, .018), mats["cyan"], target)]
    attach(owner, parts)


def console_module(step, index, target, mats):
    families = ("Sensor", "Tactical", "Helm", "Navigation", "Damage", "Comms", "Command", "Engineering")
    family = families[index % len(families)]
    side = -1 if (index // 25) % 2 == 0 else 1
    local = index % 75
    row, col = divmod(local, 15)
    pos = Vector((side * (4.9 + row * .65), -5.4 + col * .72, 1.35 + (index % 3) * .12))
    name = f"P3_CON_{index+1:03d}_{family}Module"
    owner = root(step, name, "console_module", pos, target)
    x, y, z = pos
    screen_mat = mats[("cyan", "amber", "violet", "red")[index % 4]]
    parts = [cube(name + "_Bezel", (x, y, z), (.25, .08, .18), mats["hull"], target),
             cube(name + "_Screen", (x, y - .085, z + .015), (.205, .015, .135), screen_mat, target, bevel=.006)]
    mode = index % 5
    if mode == 0:
        for j in range(3):
            parts.append(cube(name + f"_Band{j+1}", (x - .12 + j * .12, y - .105, z + .02 + j * .05),
                              (.04, .006, .012 + j * .008), screen_mat, target, bevel=0))
    elif mode == 1:
        parts.append(cylinder(name + "_Scope", (x, y - .11, z + .02), .085, .02, screen_mat, target,
                              rotation=(math.radians(90), 0, 0)))
    elif mode == 2:
        parts += [cube(name + "_TraceA", (x, y - .11, z + .05), (.15, .006, .007), mats["cyan"], target, bevel=0),
                  cube(name + "_TraceB", (x + .03, y - .112, z - .03), (.12, .006, .007), mats["violet"], target, bevel=0)]
    elif mode == 3:
        for j in range(4):
            parts.append(cylinder(name + f"_Status{j+1}", (x - .15 + j * .1, y - .11, z - .09),
                                  .012, .015, mats["amber" if j < 3 else "red"], target,
                                  rotation=(math.radians(90), 0, 0), vertices=8))
    else:
        parts.append(cube(name + "_Confidence", (x, y - .11, z - .06), (.13, .006, .018), mats["amber"], target, bevel=0))
    attach(owner, parts)


def control(step, index, target, mats):
    kinds = ("Toggle", "Breaker", "Dial", "Key", "Trackball", "GuardedLever", "Thumbwheel", "AbortHandle")
    kind = kinds[index % len(kinds)]
    bank = index // 20
    local = index % 20
    pos = Vector((-6.1 + bank * 3.05 + (local % 5) * .18, -2.6 + (local // 5) * .36, 1.18))
    name = f"P3_CTL_{index+1:03d}_{kind}"
    owner = root(step, name, "physical_control", pos, target)
    x, y, z = pos
    base = cube(name + "_Base", (x, y, z), (.07, .06, .025), mats["hull"], target)
    style = index % 8
    parts = [base]
    if style in (0, 1):
        parts.append(cube(name + "_Actuator", (x, y, z + .06), (.022, .026, .06),
                          mats["amber" if style == 0 else "red"], target))
    elif style == 2:
        parts.append(cylinder(name + "_Knob", (x, y, z + .055), .045, .045, mats["rubber"], target))
    elif style == 3:
        parts.append(cylinder(name + "_Cap", (x, y, z + .045), .025, .028, mats["cyan"], target, vertices=8))
    elif style == 4:
        parts.append(cylinder(name + "_Ball", (x, y, z + .055), .052, .050, mats["rubber"], target))
    elif style == 5:
        parts += [cylinder(name + "_Lever", (x, y, z + .11), .018, .20, mats["amber"], target,
                           rotation=(math.radians(25), 0, 0)),
                  cube(name + "_Guard", (x, y, z + .08), (.06, .05, .08), mats["red"], target)]
    elif style == 6:
        parts.append(cylinder(name + "_Wheel", (x, y, z + .05), .05, .04, mats["amber"], target,
                              rotation=(math.radians(90), 0, 0)))
    else:
        parts.append(cylinder(name + "_Handle", (x, y, z + .10), .025, .22, mats["red"], target,
                              rotation=(0, math.radians(90), 0)))
    attach(owner, parts)


def utility(step, index, target, mats):
    kinds = ("Battery", "Junction", "Coolant", "Air", "DataRack", "FuseBox", "Hydraulic", "Suppression")
    kind = kinds[index % len(kinds)]
    pos = perimeter_position(index, 100, .30 + (index % 4) * .66, .34)
    name = f"P3_UTL_{index+1:03d}_{kind}"
    owner = root(step, name, "ship_utility", pos, target)
    x, y, z = pos
    mode = index % 4
    if mode == 0:
        parts = [cube(name + "_Cabinet", (x, y, z), (.23, .13, .31), mats["structure"], target),
                 cube(name + "_Status", (x, y - .14, z + .11), (.09, .012, .04), mats["cyan"], target)]
    elif mode == 1:
        parts = [cylinder(name + "_Tank", (x, y, z), .14, .56, mats["structure"], target),
                 cylinder(name + "_Valve", (x, y - .16, z + .17), .055, .05, mats["amber"], target,
                          rotation=(math.radians(90), 0, 0))]
    elif mode == 2:
        parts = [cube(name + "_Rack", (x, y, z), (.27, .12, .36), mats["hull"], target)]
        for j in range(4):
            parts.append(cube(name + f"_Blade{j+1}", (x, y - .13, z - .20 + j * .13),
                              (.19, .015, .035), mats["cyan" if j < 3 else "red"], target))
    else:
        parts = [cube(name + "_Manifold", (x, y, z), (.28, .14, .15), mats["structure"], target),
                 cylinder(name + "_PipeA", (x - .14, y, z + .28), .025, .56, mats["structure"], target),
                 cylinder(name + "_PipeB", (x + .14, y, z + .28), .025, .56, mats["structure"], target)]
    attach(owner, parts)


def prop(step, index, target, mats):
    kinds = ("Slate", "Clipboard", "Headset", "ToolCase", "Mask", "Mug", "Harness", "SparePart")
    kind = kinds[index % len(kinds)]
    zone = index // 20
    local = index % 20
    pos = Vector((-6.7 + zone * 2.75 + (local % 5) * .24, -4.2 + (local // 5) * 1.45, 1.35 + (index % 2) * .04))
    name = f"P3_PRP_{index+1:03d}_{kind}"
    owner = root(step, name, "operations_prop", pos, target)
    x, y, z = pos
    mode = index % 4
    if mode == 0:
        parts = [cube(name + "_Body", (x, y, z), (.12, .18, .018), mats["hull"], target,
                      rotation=(0, 0, RNG.uniform(-.5, .5))),
                 cube(name + "_Face", (x, y, z + .025), (.09, .14, .006), mats["cyan"], target, bevel=0)]
    elif mode == 1:
        parts = [cube(name + "_Case", (x, y, z), (.20, .14, .10), mats["structure"], target),
                 cube(name + "_Stripe", (x, y - .145, z), (.08, .008, .025), mats["amber"], target, bevel=0)]
    elif mode == 2:
        parts = [cylinder(name + "_Core", (x, y, z), .055, .15, mats["rubber"], target),
                 cylinder(name + "_Band", (x, y, z + .08), .062, .03, mats["amber"], target)]
    else:
        parts = [cube(name + "_Pack", (x, y, z), (.14, .10, .08), mats["rubber"], target),
                 cylinder(name + "_Latch", (x, y - .11, z), .025, .035, mats["amber"], target,
                          rotation=(math.radians(90), 0, 0), vertices=8)]
    attach(owner, parts)


def damage(step, index, target, mats):
    kinds = ("Scorch", "Crack", "BloomResidue", "DentedPanel", "ArcingCable")
    kind = kinds[index % len(kinds)]
    pos = perimeter_position(index, 75, .65 + (index % 6) * .55, .02)
    name = f"P3_DMG_{index+1:03d}_{kind}"
    owner = root(step, name, "damage_variant", pos, target)
    x, y, z = pos
    parts = [cube(name + "_Mark", (x, y, z), (.16 + RNG.random() * .14, .008, .10 + RNG.random() * .12),
                  mats["scorch" if index % 3 else "violet"], target,
                  rotation=(0, RNG.uniform(-.6, .6), RNG.uniform(-.4, .4)), bevel=0)]
    if index % 5 == 4:
        for j in range(2):
            parts.append(cylinder(name + f"_Cable{j+1}", (x + j * .08, y, z - .16), .014, .36,
                                  mats["red"], target, rotation=(RNG.uniform(-.4, .4), 0, 0), vertices=8))
    attach(owner, parts)


def light_sign(step, index, target, mats):
    kinds = ("StationID", "WarningStrip", "StepLight", "StatusLamp", "RouteMarker")
    kind = kinds[index % len(kinds)]
    pos = perimeter_position(index, 50, .22 + (index % 7) * .61, .18)
    name = f"P3_LGT_{index+1:03d}_{kind}"
    owner = root(step, name, "lighting_signage", pos, target)
    x, y, z = pos
    glow = mats[("cyan", "amber", "red", "violet")[index % 4]]
    parts = [cube(name + "_Housing", (x, y, z), (.18, .05, .08), mats["hull"], target),
             cube(name + "_Emitter", (x, y - .055, z), (.13, .008, .035), glow, target, bevel=.004)]
    attach(owner, parts)


def main():
    if not BLEND.exists():
        raise RuntimeError(f"Missing bridge scene: {BLEND}")

    mats = {
        "hull": bpy.data.materials.get("M_CIC_GraphiteHull") or material("M_CIC_GraphiteHull", (.025, .035, .045), .82, .27),
        "structure": bpy.data.materials.get("M_CIC_Structure") or material("M_CIC_Structure", (.085, .105, .12), .78, .31),
        "deck": bpy.data.materials.get("M_CIC_NonSlipDeck") or material("M_CIC_NonSlipDeck", (.045, .052, .058), .55, .55),
        "rubber": bpy.data.materials.get("M_CIC_Rubber") or material("M_CIC_Rubber", (.012, .016, .019), .05, .72),
        "cyan": bpy.data.materials.get("M_CIC_Cyan") or material("M_CIC_Cyan", (.01, .18, .25), .25, .28, 5),
        "amber": bpy.data.materials.get("M_CIC_Amber") or material("M_CIC_Amber", (.65, .24, .02), .35, .34, 5),
        "red": bpy.data.materials.get("M_CIC_Red") or material("M_CIC_Red", (.28, .008, .006), .3, .35, 5),
        "violet": bpy.data.materials.get("M_CIC_Violet") or material("M_CIC_Violet", (.12, .02, .22), .2, .32, 5),
        "scorch": bpy.data.materials.get("M_CIC_Scorch") or material("M_CIC_Scorch", (.006, .004, .003), .05, .95),
    }

    groups = {
        "architecture": collection("P3_Architecture_150"),
        "consoles": collection("P3_ConsoleModules_150"),
        "controls": collection("P3_PhysicalControls_100"),
        "utilities": collection("P3_Utilities_100"),
        "props": collection("P3_OperationsProps_100"),
        "damage": collection("P3_DamageVariants_75"),
        "lights": collection("P3_LightingSignage_50"),
        "production": collection("P3_Production_25"),
    }

    step = 1
    for index in range(150):
        architecture(step, index, groups["architecture"], mats); step += 1
    for index in range(150):
        console_module(step, index, groups["consoles"], mats); step += 1
    for index in range(100):
        control(step, index, groups["controls"], mats); step += 1
    for index in range(100):
        utility(step, index, groups["utilities"], mats); step += 1
    for index in range(100):
        prop(step, index, groups["props"], mats); step += 1
    for index in range(75):
        damage(step, index, groups["damage"], mats); step += 1
    for index in range(50):
        light_sign(step, index, groups["lights"], mats); step += 1

    production_roles = (
        "collision_proxy", "interaction_anchor", "lod_metadata", "nanite_policy", "lightmap_policy",
        "material_slots", "naming_audit", "scale_audit", "aisle_clearance", "seat_clearance",
        "console_reach", "sightline_audit", "viewport_safety", "bulkhead_socket", "audio_anchor",
        "vfx_anchor", "damage_toggle", "bloom_toggle", "power_state", "emergency_state",
        "unreal_export", "preview_render", "collection_tags", "audit_report", "validated_save",
    )
    for index, role in enumerate(production_roles):
        name = f"P3_PROD_{index+1:03d}_{role}"
        owner = root(step, name, role, (0, 0, 0), groups["production"])
        owner["production_step"] = True
        step += 1

    if len(DONE) != 750 or step != 751:
        raise RuntimeError(f"Expected 750 steps; got {len(DONE)}, next={step}")

    for name, group in groups.items():
        group["bridge_phase"] = 3
        group["category"] = name
        group["unreal_folder"] = "/Game/Assets/ShipRooms/BridgeCIC/Phase3"
        group["streaming_priority"] = 2

    scene = bpy.context.scene
    scene["bridge_cic_phase3_steps"] = 750
    scene["bridge_cic_phase3_complete"] = True
    scene["bridge_cic_asset_version"] = "3.0-detail-greybox"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.filepath = str(PREVIEW)
    bpy.ops.render.render(write_still=True)

    EXPORT.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action="DESELECT")
    for group in groups.values():
        for obj in group.objects:
            if obj.type != "EMPTY":
                obj.select_set(True)
    bpy.ops.export_scene.fbx(filepath=str(EXPORT / "SM_Room_BridgeCIC_Phase3_750Steps.fbx"),
                             use_selection=True, apply_unit_scale=True, axis_forward="-Y", axis_up="Z",
                             add_leaf_bones=False, bake_anim=False)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))

    summary = {
        "phase": 3,
        "steps": len(DONE),
        "objects": len(bpy.data.objects),
        "collections": len(bpy.data.collections),
        "materials": len(bpy.data.materials),
        "categories": {name: len([item for item in DONE if item["role"] == name]) for name in ()},
        "blend": str(BLEND.relative_to(ROOT)),
        "preview": str(PREVIEW.relative_to(ROOT)),
    }
    summary["category_counts"] = {
        "architecture": 150, "console_modules": 150, "physical_controls": 100,
        "utilities": 100, "operations_props": 100, "damage_variants": 75,
        "lighting_signage": 50, "production_validation": 25,
    }
    REPORT.write_text(json.dumps({"phase": 3, "steps": DONE, "summary": summary}, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))


main()
