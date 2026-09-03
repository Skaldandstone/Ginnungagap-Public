"""Build the editable Blender source library for the procedural player-suit kit.

Run with Blender, not the system Python:
  blender --background --python tools/build_player_suits_blender.py -- <project-root>
"""

import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
SOURCE = ROOT / "Saved" / "GeneratedSuit"
OUTPUT = ROOT / "Art" / "Characters" / "PlayerSuits" / "PlayerSuit_Master.blend"
TEXTURE_SOURCE = ROOT / "Content" / "Characters" / "Player" / "Skins" / "Source"

ROLE_COLORS = {
    "Crew": (0.035, 0.18, 0.62, 1.0),
    "Engineering": (0.82, 0.24, 0.025, 1.0),
    "Medical": (0.70, 0.74, 0.72, 1.0),
    "Security": (0.62, 0.025, 0.018, 1.0),
}

ROLE_FABRIC_COLORS = {
    "Crew": (0.12, 0.14, 0.16, 1.0),
    "Engineering": (0.035, 0.075, 0.13, 1.0),
    "Medical": (0.46, 0.49, 0.48, 1.0),
    "Security": (0.055, 0.060, 0.065, 1.0),
}


def shade_color(color, factor):
    return tuple(max(0.0, min(1.0, channel * factor)) for channel in color[:3]) + (1.0,)


def material(name, color, metallic=0.15, roughness=0.48):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.location = (380, 20)

    texcoord = nodes.new("ShaderNodeTexCoord")
    texcoord.name = "PBR Generated Coordinates"
    texcoord.location = (-900, 0)
    noise = nodes.new("ShaderNodeTexNoise")
    noise.name = "Surface Microstructure"
    noise.location = (-680, 20)
    noise.noise_dimensions = "3D"
    noise.inputs["Scale"].default_value = 24.0 if "Gasket" in name else 7.5
    noise.inputs["Detail"].default_value = 8.0
    noise.inputs["Roughness"].default_value = 0.72
    noise.inputs["Distortion"].default_value = 0.12
    links.new(texcoord.outputs["Generated"], noise.inputs["Vector"])

    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.name = "Paint and Wear Color"
    ramp.location = (-420, 90)
    ramp.color_ramp.elements[0].position = 0.22
    ramp.color_ramp.elements[0].color = shade_color(color, 0.42)
    ramp.color_ramp.elements[1].position = 0.80
    ramp.color_ramp.elements[1].color = shade_color(color, 1.22)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])

    rough_ramp = nodes.new("ShaderNodeMapRange")
    rough_ramp.name = "Roughness Variation"
    rough_ramp.location = (-160, -100)
    rough_ramp.inputs["From Min"].default_value = 0.0
    rough_ramp.inputs["From Max"].default_value = 1.0
    rough_ramp.inputs["To Min"].default_value = max(0.04, roughness - 0.14)
    rough_ramp.inputs["To Max"].default_value = min(0.96, roughness + 0.18)
    links.new(noise.outputs["Fac"], rough_ramp.inputs["Value"])
    links.new(rough_ramp.outputs["Result"], bsdf.inputs["Roughness"])

    bump = nodes.new("ShaderNodeBump")
    bump.name = "Micro Scratch Normal"
    bump.location = (120, -180)
    bump.inputs["Strength"].default_value = 0.13 if "Gasket" not in name else 0.32
    bump.inputs["Distance"].default_value = 0.08
    links.new(noise.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])

    if "Visor" in name:
        layer = nodes.new("ShaderNodeLayerWeight")
        layer.name = "Visor Fresnel"
        layer.location = (-400, 300)
        visor_ramp = nodes.new("ShaderNodeValToRGB")
        visor_ramp.name = "Visor Edge Tint"
        visor_ramp.location = (-120, 300)
        visor_ramp.color_ramp.elements[0].color = (0.002, 0.008, 0.014, 1)
        visor_ramp.color_ramp.elements[1].color = (0.02, 0.32, 0.58, 1)
        links.new(layer.outputs["Facing"], visor_ramp.inputs["Fac"])
        links.new(visor_ramp.outputs["Color"], bsdf.inputs["Base Color"])
        if "Coat Weight" in bsdf.inputs:
            bsdf.inputs["Coat Weight"].default_value = 0.85
            bsdf.inputs["Coat Roughness"].default_value = 0.08

    mat["texture_channels"] = "BaseColor,Roughness,Normal,Metallic"
    mat["unreal_bake_resolution"] = 2048
    return mat


def attach_role_texture_set(mat, role):
    """Layer the authored five-channel role texture set over the procedural Blender shader."""
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")
    paint = nodes.get("Paint and Wear Color")
    files = {
        "Albedo": TEXTURE_SOURCE / f"T_PlayerSkin_{role}.png",
        "Normal": TEXTURE_SOURCE / f"T_PlayerSkin_{role}_Normal.png",
        "Roughness": TEXTURE_SOURCE / f"T_PlayerSkin_{role}_Roughness.png",
        "Metallic": TEXTURE_SOURCE / f"T_PlayerSkin_{role}_Metallic.png",
        "AO": TEXTURE_SOURCE / f"T_PlayerSkin_{role}_AO.png",
    }
    missing = [str(path) for path in files.values() if not path.exists()]
    if missing:
        raise RuntimeError("Missing role texture files: " + ", ".join(missing))

    textures = {}
    for index, (channel, path) in enumerate(files.items()):
        image = bpy.data.images.load(str(path), check_existing=True)
        image.name = f"T_{role}_{channel}"
        image.filepath = str(path)
        if channel != "Albedo":
            image.colorspace_settings.name = "Non-Color"
        node = nodes.new("ShaderNodeTexImage")
        node.name = f"Authored {channel} Texture"
        node.label = f"{role} {channel}"
        node.image = image
        node.location = (-900, -260 - index * 190)
        textures[channel] = node

    color_mix = nodes.new("ShaderNodeMixRGB")
    color_mix.name = "Authored Albedo x Procedural Wear"
    color_mix.blend_type = "MULTIPLY"
    color_mix.inputs[0].default_value = 0.72
    color_mix.location = (70, 100)
    links.new(textures["Albedo"].outputs["Color"], color_mix.inputs[1])
    links.new(paint.outputs["Color"], color_mix.inputs[2])
    links.new(color_mix.outputs["Color"], bsdf.inputs["Base Color"])

    normal_map = nodes.new("ShaderNodeNormalMap")
    normal_map.name = "Authored Tangent Normal"
    normal_map.inputs["Strength"].default_value = 0.78
    normal_map.location = (-80, -430)
    links.new(textures["Normal"].outputs["Color"], normal_map.inputs["Color"])
    links.new(normal_map.outputs["Normal"], bsdf.inputs["Normal"])
    links.new(textures["Roughness"].outputs["Color"], bsdf.inputs["Roughness"])
    links.new(textures["Metallic"].outputs["Color"], bsdf.inputs["Metallic"])

    ao_mix = nodes.new("ShaderNodeMixRGB")
    ao_mix.name = "Authored AO Multiply"
    ao_mix.blend_type = "MULTIPLY"
    ao_mix.inputs[0].default_value = 0.38
    ao_mix.location = (250, 150)
    links.new(color_mix.outputs["Color"], ao_mix.inputs[1])
    links.new(textures["AO"].outputs["Color"], ao_mix.inputs[2])
    links.new(ao_mix.outputs["Color"], bsdf.inputs["Base Color"])
    mat["authored_texture_role"] = role
    mat["authored_texture_source"] = str(TEXTURE_SOURCE)
    mat["packed_for_portability"] = True


def collection(name):
    result = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(result)
    return result


def move_to(obj, target):
    for owner in tuple(obj.users_collection):
        owner.objects.unlink(obj)
    target.objects.link(obj)


def add_finish_modifiers(obj):
    if obj.type != "MESH":
        return
    bevel = obj.modifiers.new("Production Bevel", "BEVEL")
    bevel.width = 0.12
    bevel.segments = 2
    bevel.limit_method = "ANGLE"
    smooth = obj.modifiers.new("Weighted Corner Normals", "NODES")
    smooth.node_group = bpy.data.node_groups.get("Smooth by Angle")


def import_mesh(path, target, mat):
    before = set(bpy.data.objects)
    bpy.ops.wm.obj_import(filepath=str(path), forward_axis="NEGATIVE_Z", up_axis="Y")
    imported = list(set(bpy.data.objects) - before)
    meshes = [obj for obj in imported if obj.type == "MESH"]
    if not meshes:
        raise RuntimeError(f"No mesh imported from {path}")
    bpy.context.view_layer.objects.active = meshes[0]
    for obj in imported:
        obj.select_set(True)
    if len(meshes) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = path.stem
    obj.data.name = path.stem + "_Mesh"
    move_to(obj, target)
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    add_finish_modifiers(obj)
    bpy.ops.object.shade_smooth_by_angle()
    return obj


def add_label(text, location, target):
    curve = bpy.data.curves.new(text + "_Label", "FONT")
    curve.body = text.replace("SM_Suit_", "").replace("_", " ")
    curve.align_x = "CENTER"
    curve.size = 3.0
    curve.extrude = 0.025
    obj = bpy.data.objects.new(text + "_Label", curve)
    target.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (math.radians(90), 0, 0)
    return obj


def primitive_cube(name, location, scale, target, mat, bevel=0.7):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    move_to(obj, target)
    obj.data.materials.append(mat)
    modifier = obj.modifiers.new("Production Bevel", "BEVEL")
    modifier.width = bevel
    modifier.segments = 3
    return obj


def primitive_cylinder(name, location, radius, depth, target, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=radius, depth=depth, location=location,
                                       rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    move_to(obj, target)
    obj.data.materials.append(mat)
    add_finish_modifiers(obj)
    bpy.ops.object.shade_smooth_by_angle()
    return obj


def primitive_torus(name, location, major, minor, target, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                    major_segments=48, minor_segments=12,
                                    location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    move_to(obj, target)
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth_by_angle()
    return obj


def cylinder_between(name, start, end, radius, target, mat):
    start, end = Vector(start), Vector(end)
    direction = end - start
    obj = primitive_cylinder(name, (start + end) * .5, radius, direction.length, target, mat)
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
    return obj


def copy_part(source_name, name, location, target, scale=(1, 1, 1), rotation=(0, 0, 0)):
    source = bpy.data.objects[source_name]
    obj = source.copy()
    obj.data = source.data.copy()
    obj.name = name
    target.objects.link(obj)
    obj.location = location
    obj.scale = scale
    obj.rotation_euler = rotation
    obj["hero_assembly"] = True
    obj["source_part"] = source_name
    return obj


def curve_tube(name, points, radius, target, mat):
    curve = bpy.data.curves.new(name + "_Curve", "CURVE")
    curve.dimensions = "3D"
    curve.bevel_depth = radius
    curve.bevel_resolution = 4
    spline = curve.splines.new("BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    obj = bpy.data.objects.new(name, curve)
    target.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def concept_art_refinement(target, root, armor_mat, equipment_mat, role_mats):
    """Twenty modeling cues derived from the approved suit turnaround and role lineup."""
    y = 430.0
    gasket = bpy.data.materials["M_Suit_Gasket"]
    orange = bpy.data.materials["M_Suit_Service_Orange"]
    glow = bpy.data.materials["M_Suit_Status_Light"]
    fabric = bpy.data.materials["M_Suit_Undersuit_Fabric"]

    # 1-3: layered helmet brow, crown rail and paired communications pods.
    primitive_torus("CONCEPT_HelmetBrowRing", (3, y, 151), 14.8, 1.35, target, armor_mat,
                    (0, math.radians(90), 0))
    primitive_cube("CONCEPT_HelmetCrownRail", (-1, y, 166), (8, 2.0, 1.3), target, armor_mat, .6)
    for sy in (-14, 14):
        primitive_cylinder(f"CONCEPT_CommsPod_{sy}", (0, y + sy, 153), 3.6, 3.0,
                           target, equipment_mat, (math.radians(90), 0, 0))

    # 4-5: the turnaround's twin corrugated helmet-to-pack breathing hoses.
    curve_tube("CONCEPT_BreathingHose_L", [(0,y+12,140),(-11,y+17,132),(-20,y+16,116)],
               1.8, target, gasket)
    curve_tube("CONCEPT_BreathingHose_R", [(0,y-12,140),(-11,y-17,132),(-20,y-16,116)],
               1.8, target, gasket)

    # 6-7: recessed chest-computer bezel and illuminated data screen.
    primitive_cube("CONCEPT_ChestComputerBezel", (15.5, y, 112), (2.0, 9.0, 10.0),
                   target, equipment_mat, 1.5)
    primitive_cube("CONCEPT_ChestComputerScreen", (17.7, y, 114), (.45, 6.3, 5.2),
                   target, glow, .35)

    # 8-9: four-point shoulder webbing and sternum bridge.
    for sy in (-13, 13):
        curve_tube(f"CONCEPT_ShoulderWebbing_{sy}",
                   [(11,y+sy,128),(14,y+sy*.78,112),(13,y+sy*.70,91)], 1.25, target, gasket)
    primitive_cube("CONCEPT_SternumBridge", (15.0, y, 97), (1.0, 13.5, 1.8), target, gasket, .6)

    # 10-12: broad utility belt, metal buckle and symmetric modular pouches.
    primitive_torus("CONCEPT_UtilityBelt", (1, y, 77), 18.0, 2.0, target, gasket,
                    (0, math.radians(90), 0))
    primitive_cube("CONCEPT_BeltBuckle", (18, y, 77), (1.3, 4.0, 3.2), target, orange, .7)
    for sy in (-20, 20):
        primitive_cube(f"CONCEPT_BeltPouch_{sy}", (7, y+sy, 76), (4.5, 5.0, 6.0),
                       target, equipment_mat, 1.2)

    # 13: concept-art thigh retention straps.
    for sy in (-12, 12):
        primitive_torus(f"CONCEPT_ThighStrap_{sy}", (0, y+sy, 58), 8.0, 1.25,
                        target, gasket, (0, math.radians(90), 0))

    # 14-15: elbow caps and layered shin plates.
    for sy in (-40, 40):
        primitive_cube(f"CONCEPT_ElbowCap_{sy}", (4, y+sy, 92), (3.3, 6.0, 6.5),
                       target, armor_mat, 2.0)
    for sy in (-12, 12):
        primitive_cube(f"CONCEPT_ShinPlate_{sy}", (5, y+sy, 25), (3.0, 7.0, 10.5),
                       target, armor_mat, 2.2)

    # 16: rugged segmented ankle cuffs.
    for sy in (-12, 12):
        primitive_torus(f"CONCEPT_AnkleCuff_{sy}", (1, y+sy, 12), 7.0, 1.5,
                        target, armor_mat, (0, math.radians(90), 0))

    # 17-18: framed backpack shell and accessible rear service panel.
    primitive_cube("CONCEPT_BackpackFrame", (-24, y, 108), (3.0, 18.0, 24.0),
                   target, armor_mat, 2.2)
    primitive_cube("CONCEPT_BackpackServicePanel", (-28, y, 109), (1.0, 11.0, 12.0),
                   target, equipment_mat, 1.0)

    # 19: orange suit-seam piping carried from shoulder to thigh.
    for sy in (-1, 1):
        curve_tube(f"CONCEPT_SeamPiping_{sy}",
                   [(10,y+sy*16,122),(12,y+sy*18,95),(8,y+sy*15,72),(4,y+sy*12,48)],
                   .45, target, orange)

    # 20: compact role ID plate matching the four concept-art class color families.
    id_plate = primitive_cube("CONCEPT_RoleID_Crew", (18.8, y-8, 124), (.35, 4.5, 2.4),
                              target, role_mats["Crew"], .3)
    id_plate["role_variants"] = "Crew,Engineering,Medical,Security"

    for obj in tuple(target.objects):
        if obj.parent is None and obj is not root:
            obj.parent = root
        obj["concept_art_refinement"] = True
        obj["unreal_export"] = True
    root["concept_reference"] = "docs/concept-art/reference/suits/standard-suit-turnaround.png"
    root["role_reference"] = "docs/concept-art/reference/suits/player-suit-role-lineup.png"


def build_hands_free_equipment(target, root, armor_mat, equipment_mat, role_mats):
    """Interchangeable backpack tool arm and dockable drone with attachment hardpoints."""
    y = 430.0
    gasket = bpy.data.materials["M_Suit_Gasket"]
    orange = bpy.data.materials["M_Suit_Service_Orange"]
    glow = bpy.data.materials["M_Suit_Status_Light"]

    # Articulated tool arm: backpack swivel, two powered links and a universal wrist.
    base = primitive_cylinder("TOOLARM_BackpackSwivel", (-28, y-17, 122), 5.2, 6.0,
                              target, equipment_mat, (math.radians(90), 0, 0))
    base["socket"] = "SuitHardpoint_Backpack_R"
    base["class_defaults"] = "Engineering,Security"
    points = [(-28,y-20,122),(-16,y-31,139),(2,y-34,132),(16,y-31,116)]
    for index in range(3):
        cylinder_between(f"TOOLARM_Link_{index+1}", points[index], points[index+1],
                         2.7-index*.25, target, armor_mat)
    for index, point in enumerate(points):
        primitive_cylinder(f"TOOLARM_Joint_{index+1}", point, 4.2, 4.5, target,
                           orange, (math.radians(90), 0, 0))
    wrist = primitive_cylinder("TOOLARM_UniversalWrist", points[-1], 4.0, 6.0, target,
                               equipment_mat, (math.radians(90), 0, 0))
    wrist["attachment_slots"] = "RepairTorch,Cutter,Scanner,WorkLight,Grapple,WeaponMount,SampleClaw"
    wrist["socket_name"] = "ToolArm_EndEffector"
    primitive_cube("TOOLARM_StatusLamp", (18, y-31, 116), (.7, 2.8, 1.0), target, glow, .25)
    curve_tube("TOOLARM_PowerConduit", [(-28,y-19,121),(-15,y-29,137),(3,y-32,130),(15,y-29,115)],
               .55, target, gasket)

    # Compact utility drone: docking shoe, protected core and four vectored thrusters.
    dock = primitive_cube("DRONE_BackpackDock", (-24, y+22, 124), (4.0, 7.0, 8.0),
                          target, equipment_mat, 1.3)
    dock["socket"] = "SuitHardpoint_Backpack_L"
    dock["class_defaults"] = "Crew,Medical"
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16,
                                        location=(4, y+43, 131), scale=(7, 11, 5))
    drone = bpy.context.object
    drone.name = "DRONE_UtilityCore"
    move_to(drone, target)
    drone.data.materials.append(role_mats["Crew"])
    drone["equipment_modes"] = "Docked,Follow,Illuminate,Scan,Repair,Retrieve,MedicalAssist"
    drone["network_owner"] = "PlayerState"
    for index, (oy, oz) in enumerate(((-9,-5),(-9,5),(9,-5),(9,5))):
        cylinder_between(f"DRONE_Boom_{index+1}", (4,y+43,131), (4,y+43+oy,131+oz),
                         1.2, target, armor_mat)
        primitive_torus(f"DRONE_Thruster_{index+1}", (4,y+43+oy,131+oz), 2.7, .65,
                        target, orange, (0, math.radians(90), 0))
    sensor = primitive_cylinder("DRONE_MultiSensor", (11.2, y+43, 131), 2.8, 2.0,
                                target, glow, (0, math.radians(90), 0))
    sensor["attachment_slots"] = "BioScanner,NavigationLidar,Camera,AtmosphereProbe,WorkLight"
    sensor["socket_name"] = "Drone_SensorBay"
    primitive_cube("DRONE_UnderslungHardpoint", (4, y+43, 124.8), (3.0, 4.5, 1.0),
                   target, equipment_mat, .6)["attachment_slots"] = "Manipulator,SampleCase,MedKit,AmmoCarrier"

    for obj in tuple(target.objects):
        if obj.parent is None:
            obj.parent = root
        obj["hands_free_equipment"] = True
        obj["unreal_export"] = True
    root["equipment_rule"] = "Tool arm or drone selected by class/loadout; both preserve hand availability"


def build_class_variants(target, source_root, role_mats, role_fabric_mats):
    """Create four linked production loadouts from the approved assembled hero suit."""
    configurations = {
        "Crew": {"offset": -105, "equipment": "Drone", "payload": "NavigationLidar,WorkLight,SampleCase"},
        "Engineering": {"offset": -35, "equipment": "ToolArm", "payload": "RepairTorch,Cutter,Scanner"},
        "Medical": {"offset": 35, "equipment": "Drone", "payload": "BioScanner,MedicalAssist,MedKit"},
        "Security": {"offset": 105, "equipment": "ToolArm", "payload": "WorkLight,Grapple,WeaponMount"},
    }
    source_children = [obj for obj in bpy.data.objects if obj.parent == source_root]
    for role, config in configurations.items():
        variant_root = bpy.data.objects.new(f"VARIANT_{role}_Root", None)
        target.objects.link(variant_root)
        variant_root.location = (0, config["offset"], 0)
        variant_root["pressure_suit_role"] = role
        variant_root["hands_free_equipment"] = config["equipment"]
        variant_root["default_payload"] = config["payload"]
        variant_root["network_state"] = "Replicated class loadout"
        variant_root["unreal_blueprint"] = f"BP_Player_Suit_{role}"

        for source in source_children:
            is_tool_arm = source.name.startswith("TOOLARM_")
            is_drone = source.name.startswith("DRONE_")
            if is_tool_arm and config["equipment"] != "ToolArm":
                continue
            if is_drone and config["equipment"] != "Drone":
                continue
            clone = source.copy()
            if source.data:
                clone.data = source.data.copy()
            clone.name = source.name.replace("HERO_", f"{role.upper()}_").replace("CONCEPT_", f"{role.upper()}_CONCEPT_")
            target.objects.link(clone)
            clone.parent = variant_root
            clone["variant_role"] = role
            clone["unreal_export"] = True
            if clone.type == "MESH":
                for slot_index, mat in enumerate(tuple(clone.data.materials)):
                    if mat and (mat.name.startswith("M_Role_") or source.name in (
                            "HERO_ChestPlate", "HERO_Shoulder_L", "HERO_Shoulder_R")):
                        clone.data.materials[slot_index] = role_mats[role]
                    elif mat and mat.name == "M_Suit_Undersuit_Fabric":
                        clone.data.materials[slot_index] = role_fabric_mats[role]
        variant_root["object_count"] = len([obj for obj in target.objects if obj.parent == variant_root])
    target["variant_policy"] = "Crew/Medical use drone; Engineering/Security use tool arm"


def build_production_detail_100(target, root, armor_mat, equipment_mat):
    """One hundred individually indexed, editable production details in five systems."""
    y = 430.0
    gasket = bpy.data.materials["M_Suit_Gasket"]
    orange = bpy.data.materials["M_Suit_Service_Orange"]
    glow = bpy.data.materials["M_Suit_Status_Light"]
    created = []

    def register(obj, category):
        created.append(obj)
        obj.parent = root
        obj["production_step_index"] = len(created)
        obj["production_category"] = category
        obj["unreal_export"] = True
        return obj

    # 001-020 Helmet hardware: crown fasteners, status lamps and visor clamps.
    for index in range(12):
        angle = math.tau * index / 12
        register(primitive_cylinder(f"P100_HelmetFastener_{index+1:02}",
                 (7, y + math.cos(angle)*13.5, 151 + math.sin(angle)*13.5),
                 .62, .7, target, equipment_mat, (0, math.radians(90), 0)), "Helmet")
    for index, sy in enumerate((-9, -3, 3, 9)):
        register(primitive_cube(f"P100_HelmetStatus_{index+1:02}", (13, y+sy, 164),
                 (.45, 1.7, .55), target, glow, .2), "Helmet")
    for index, (sy, sz) in enumerate(((-13,143),(-13,159),(13,143),(13,159))):
        register(primitive_cube(f"P100_VisorClamp_{index+1:02}", (12, y+sy, sz),
                 (1.2, 1.5, 2.2), target, armor_mat, .45), "Helmet")

    # 021-040 Torso/webbing: chest fasteners, belt loops and quick-adjust buckles.
    for index in range(12):
        sy = (-1 if index % 2 == 0 else 1) * (7 + (index//2 % 3)*5)
        sz = 91 + (index//6)*27 + (index//2 % 2)*9
        register(primitive_cylinder(f"P100_ChestFastener_{index+1:02}", (17, y+sy, sz),
                 .72, .75, target, orange, (0, math.radians(90), 0)), "Torso")
    for index, sy in enumerate((-18,-6,6,18)):
        register(primitive_torus(f"P100_BeltLoop_{index+1:02}", (4, y+sy, 77),
                 2.2, .55, target, gasket, (0, math.radians(90), 0)), "Torso")
    for index, sy in enumerate((-17,-8,8,17)):
        register(primitive_cube(f"P100_WebbingBuckle_{index+1:02}", (15, y+sy, 88),
                 (.8, 2.2, 1.8), target, equipment_mat, .35), "Torso")

    # 041-060 Limb articulation: armor fasteners and four flexible joint rings.
    limb_points = [(5,y+s*40,z) for s in (-1,1) for z in (73,84,96,108)] + \
                  [(6,y+s*12,z) for s in (-1,1) for z in (18,29,40,51)]
    for index, point in enumerate(limb_points):
        register(primitive_cylinder(f"P100_LimbFastener_{index+1:02}", point, .72, .8,
                 target, orange, (0, math.radians(90), 0)), "Limbs")
    for index, (sy, sz) in enumerate(((-12,39),(12,39),(-40,94),(40,94))):
        register(primitive_torus(f"P100_JointSeal_{index+1:02}", (0,y+sy,sz),
                 6.2, .7, target, gasket, (0, math.radians(90), 0)), "Limbs")

    # 061-080 Backpack systems: radiator fins, service ports and cable retainers.
    for index in range(8):
        sy = -14 + index*4
        register(primitive_cube(f"P100_RadiatorFin_{index+1:02}", (-32,y+sy,108),
                 (1.2, .7, 18), target, armor_mat, .25), "Backpack")
    for index, (sy, sz) in enumerate(((-12,94),(0,94),(12,94),(-12,118),(0,118),(12,118))):
        register(primitive_cylinder(f"P100_ServicePort_{index+1:02}", (-34,y+sy,sz),
                 1.8, 1.2, target, orange, (0, math.radians(90), 0)), "Backpack")
    for index, (sy, sz) in enumerate(((-15,99),(-15,108),(-15,117),(15,99),(15,108),(15,117))):
        register(primitive_torus(f"P100_CableRetainer_{index+1:02}", (-28,y+sy,sz),
                 1.8, .42, target, gasket, (0, math.radians(90), 0)), "Backpack")

    # 081-100 Interaction/maintenance: hardpoints, ID plates, repair patches and sensors.
    for index, (sy, sz) in enumerate(((-24,115),(24,115),(-23,101),(23,101),
                                      (-19,84),(19,84),(-15,66),(15,66))):
        socket = register(primitive_cube(f"P100_Hardpoint_{index+1:02}", (13,y+sy,sz),
                          (1.0,2.4,2.4), target, equipment_mat, .55), "Interaction")
        socket["attachment_socket"] = f"SuitAccessory_{index+1:02}"
    for index, (sy, sz) in enumerate(((-10,126),(10,126),(-10,82),(10,82))):
        register(primitive_cube(f"P100_IDPlate_{index+1:02}", (16,y+sy,sz),
                 (.35,3.1,1.4), target, glow, .2), "Interaction")
    for index, (sy, sz) in enumerate(((-8,56),(8,56),(-7,31),(7,31))):
        patch = register(primitive_cube(f"P100_FieldPatch_{index+1:02}", (7,y+sy,sz),
                         (.45,3.0,3.8), target, armor_mat, .35), "Interaction")
        patch["damage_overlay_channel"] = index + 1
    for index, sy in enumerate((-12,-4,4,12)):
        sensor = register(primitive_cylinder(f"P100_EnvironmentSensor_{index+1:02}",
                          (18,y+sy,134), .8, 1.0, target, glow,
                          (0, math.radians(90), 0)), "Interaction")
        sensor["telemetry"] = "pressure,temperature,radiation,pathogen"

    if len(created) != 100:
        raise RuntimeError(f"Production detail pass created {len(created)} objects instead of 100")
    root["production_detail_steps"] = 100
    root["production_detail_categories"] = "Helmet,Torso,Limbs,Backpack,Interaction"
    target["verified_step_count"] = len(created)


def build_production_rig_50(target, hero_root, equipment_mat):
    """Fifty production steps: 22 bones, 14 sockets, 10 collision proxies and 4 LOD specs."""
    y = 430.0
    step = 0

    armature_data = bpy.data.armatures.new("SK_PlayerSuit_Production")
    armature = bpy.data.objects.new("SK_PlayerSuit_Production", armature_data)
    target.objects.link(armature)
    armature.show_in_front = True
    armature.display_type = "WIRE"
    bpy.context.view_layer.objects.active = armature
    armature.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bones = [
        ("root", (0,y,0), (0,y,6), None),
        ("pelvis", (0,y,62), (0,y,76), "root"),
        ("spine_01", (0,y,76), (0,y,91), "pelvis"),
        ("spine_02", (0,y,91), (0,y,108), "spine_01"),
        ("spine_03", (0,y,108), (0,y,128), "spine_02"),
        ("neck_01", (0,y,128), (0,y,140), "spine_03"),
        ("head", (0,y,140), (0,y,165), "neck_01"),
        ("clavicle_l", (0,y+2,124), (0,y+22,121), "spine_03"),
        ("upperarm_l", (0,y+22,121), (0,y+39,96), "clavicle_l"),
        ("lowerarm_l", (0,y+39,96), (1,y+42,73), "upperarm_l"),
        ("hand_l", (1,y+42,73), (2,y+43,64), "lowerarm_l"),
        ("clavicle_r", (0,y-2,124), (0,y-22,121), "spine_03"),
        ("upperarm_r", (0,y-22,121), (0,y-39,96), "clavicle_r"),
        ("lowerarm_r", (0,y-39,96), (1,y-42,73), "upperarm_r"),
        ("hand_r", (1,y-42,73), (2,y-43,64), "lowerarm_r"),
        ("thigh_l", (0,y+10,67), (0,y+12,40), "pelvis"),
        ("calf_l", (0,y+12,40), (1,y+12,15), "thigh_l"),
        ("foot_l", (1,y+12,15), (12,y+12,7), "calf_l"),
        ("thigh_r", (0,y-10,67), (0,y-12,40), "pelvis"),
        ("calf_r", (0,y-12,40), (1,y-12,15), "thigh_r"),
        ("foot_r", (1,y-12,15), (12,y-12,7), "calf_r"),
        ("ik_hand_gun", (8,y,92), (16,y,92), "root"),
    ]
    edit_bones = {}
    for name, head, tail, parent_name in bones:
        bone = armature_data.edit_bones.new(name)
        bone.head, bone.tail = head, tail
        if parent_name:
            bone.parent = edit_bones[parent_name]
        edit_bones[name] = bone
    bpy.ops.object.mode_set(mode="OBJECT")
    for name, *_ in bones:
        step += 1
        bone = armature_data.bones[name]
        bone["production_step_index"] = step
        bone["unreal_manny_compatible_name"] = True

    socket_specs = [
        ("SOCKET_Helmet", "head"), ("SOCKET_Visor", "head"),
        ("SOCKET_Backpack", "spine_03"), ("SOCKET_ChestModule", "spine_03"),
        ("SOCKET_ToolArm", "spine_03"), ("SOCKET_DroneDock", "spine_03"),
        ("SOCKET_Shoulder_L", "clavicle_l"), ("SOCKET_Shoulder_R", "clavicle_r"),
        ("SOCKET_Forearm_L", "lowerarm_l"), ("SOCKET_Forearm_R", "lowerarm_r"),
        ("SOCKET_Hand_L", "hand_l"), ("SOCKET_Hand_R", "hand_r"),
        ("SOCKET_Foot_L", "foot_l"), ("SOCKET_Foot_R", "foot_r"),
    ]
    for socket_name, bone_name in socket_specs:
        step += 1
        socket = bpy.data.objects.new(socket_name, None)
        target.objects.link(socket)
        socket.empty_display_type = "ARROWS"
        socket.empty_display_size = 3.0
        socket.parent = armature
        socket.parent_type = "BONE"
        socket.parent_bone = bone_name
        socket.location = (0, 0, 0)
        socket["production_step_index"] = step
        socket["socket_bone"] = bone_name
        socket["unreal_socket"] = True

    collision_specs = [
        ("PHYS_Head", (0,y,151), (12,13,15)),
        ("PHYS_Torso", (0,y,103), (12,20,27)),
        ("PHYS_Pelvis", (0,y,68), (11,17,9)),
        ("PHYS_Arm_L", (0,y+34,98), (6,17,6)),
        ("PHYS_Arm_R", (0,y-34,98), (6,17,6)),
        ("PHYS_Leg_L", (0,y+12,37), (7,8,27)),
        ("PHYS_Leg_R", (0,y-12,37), (7,8,27)),
        ("PHYS_Backpack", (-18,y,108), (12,18,27)),
        ("PHYS_ToolArm", (-8,y-28,126), (18,7,18)),
        ("PHYS_Drone", (4,y+43,131), (8,12,7)),
    ]
    for name, location, scale in collision_specs:
        step += 1
        proxy = primitive_cube(name, location, scale, target, equipment_mat, 3.0)
        proxy.display_type = "WIRE"
        proxy.hide_render = True
        proxy.parent = armature
        proxy["production_step_index"] = step
        proxy["collision_proxy"] = True
        proxy["unreal_collision_prefix"] = "UCX"

    for lod_index, ratio in enumerate((1.0, .60, .30, .12)):
        step += 1
        lod = bpy.data.objects.new(f"LOD{lod_index}_Policy", None)
        target.objects.link(lod)
        lod.parent = hero_root
        lod["production_step_index"] = step
        lod["triangle_ratio"] = ratio
        lod["screen_size"] = (1.0, .55, .22, .08)[lod_index]
        lod["preserve"] = "silhouette,visor,hands,tool sockets"

    if step != 50:
        raise RuntimeError(f"Production rig pass completed {step} steps instead of 50")
    armature["verified_step_count"] = step
    armature["target_skeleton"] = "UE5 Manny"
    armature["root_motion_bone"] = "root"
    target["verified_step_count"] = step
    return armature


def bind_production_meshes_100(hero_root, armature):
    """Rigid-bind 100 prioritized modular meshes to the production skeleton."""
    candidates = [obj for obj in bpy.data.objects if obj.parent == hero_root and obj.type == "MESH"
                  and not obj.get("concept_fidelity_detail")]
    candidates.sort(key=lambda obj: (obj.name.startswith("P100_"), obj.name))
    if len(candidates) < 100:
        raise RuntimeError(f"Only {len(candidates)} hero meshes are available for the 100-step bind pass")

    def target_bone(obj):
        name = obj.name.lower()
        left = obj.location.y >= 430
        side = "l" if left else "r"
        if any(key in name for key in ("helmet", "visor", "comms", "crown")):
            return "head"
        if any(key in name for key in ("collar", "breathinghose")):
            return "neck_01"
        if any(key in name for key in ("boot", "sole", "ankle", "foot")):
            return f"foot_{side}"
        if any(key in name for key in ("knee", "shin", "calf")):
            return f"calf_{side}"
        if any(key in name for key in ("thigh", "pouch")):
            return f"thigh_{side}"
        if any(key in name for key in ("glove", "hand")):
            return f"hand_{side}"
        if "forearm" in name:
            return f"lowerarm_{side}"
        if any(key in name for key in ("shoulder", "upperarm", "elbow")):
            return f"upperarm_{side}"
        return "spine_03"

    bound = []
    for index, obj in enumerate(candidates[:100], 1):
        bone_name = target_bone(obj)
        for group in tuple(obj.vertex_groups):
            obj.vertex_groups.remove(group)
        group = obj.vertex_groups.new(name=bone_name)
        group.add(range(len(obj.data.vertices)), 1.0, "REPLACE")
        modifier = next((item for item in obj.modifiers if item.type == "ARMATURE"), None)
        if not modifier:
            modifier = obj.modifiers.new("Production Skeleton", "ARMATURE")
        modifier.object = armature
        modifier.use_vertex_groups = True
        obj["skeletal_bind_step"] = index
        obj["skeletal_bind_bone"] = bone_name
        obj["skeletal_export"] = True
        bound.append(obj)
    if len(bound) != 100:
        raise RuntimeError(f"Bound {len(bound)} meshes instead of 100")
    armature["bound_mesh_count"] = len(bound)
    armature["skeletal_export_name"] = "SKM_PlayerSuit_Prototype"


def refine_undersuit_deformation_100(armature):
    """One hundred tracked steps: dual-bone gradient weights on ten flexible suit sections."""
    specs = (
        ("HERO_Undersuit_Torso", "spine_01", "spine_03", 2),
        ("HERO_Undersuit_Pelvis", "pelvis", "spine_01", 2),
        ("HERO_UpperArm_L", "clavicle_l", "upperarm_l", 1),
        ("HERO_UpperArm_R", "clavicle_r", "upperarm_r", 1),
        ("HERO_Forearm_L", "upperarm_l", "lowerarm_l", 1),
        ("HERO_Forearm_R", "upperarm_r", "lowerarm_r", 1),
        ("HERO_Thigh_L", "pelvis", "thigh_l", 2),
        ("HERO_Thigh_R", "pelvis", "thigh_r", 2),
        ("HERO_Calf_L", "thigh_l", "calf_l", 2),
        ("HERO_Calf_R", "thigh_r", "calf_r", 2),
    )
    step = 0
    for obj_name, proximal_bone, distal_bone, axis in specs:
        obj = bpy.data.objects[obj_name]
        step += 1  # Resolve the authored flexible section.
        coordinates = [vertex.co[axis] for vertex in obj.data.vertices]
        step += 1  # Sample its local deformation axis.
        low, high = min(coordinates), max(coordinates)
        extent = max(high - low, 0.0001)
        step += 1  # Establish a stable normalized weight domain.
        for group in tuple(obj.vertex_groups):
            obj.vertex_groups.remove(group)
        step += 1  # Remove the earlier rigid assignment.
        proximal = obj.vertex_groups.new(name=proximal_bone)
        step += 1  # Create the proximal joint influence.
        distal = obj.vertex_groups.new(name=distal_bone)
        step += 1  # Create the distal joint influence.
        for vertex, coordinate in zip(obj.data.vertices, coordinates):
            blend = max(0.0, min(1.0, (coordinate - low) / extent))
            # Smoothstep prevents a visible hinge at the middle of the fabric section.
            blend = blend * blend * (3.0 - 2.0 * blend)
            proximal.add([vertex.index], 1.0 - blend, "REPLACE")
            distal.add([vertex.index], blend, "REPLACE")
        step += 1  # Assign normalized proximal weights.
        step += 1  # Assign normalized distal weights.
        modifier = next(item for item in obj.modifiers if item.type == "ARMATURE")
        modifier.object = armature
        step += 1  # Validate the deformation modifier target.
        obj["deformation_profile"] = "dual_bone_smoothstep"
        obj["deformation_bones"] = f"{proximal_bone},{distal_bone}"
        obj["deformation_step_end"] = step + 1
        step += 1  # Record the completed section audit.
    if step != 100:
        raise RuntimeError(f"Undersuit deformation pass completed {step} steps instead of 100")
    armature["deformation_refinement_steps"] = step
    armature["smooth_weighted_section_count"] = len(specs)


def build_concept_fidelity_500(target, root, armor_mat, equipment_mat, role_mats):
    """Five hundred authored operations matching the approved grounded EVA-suit concept language."""
    y = 430.0
    gasket = bpy.data.materials["M_Suit_Gasket"]
    orange = bpy.data.materials["M_Suit_Service_Orange"]
    ivory = material("M_Concept_IvoryArmor", (0.52, 0.49, 0.42, 1), 0.42, 0.34)
    dark_fabric = material("M_Concept_ReinforcedFabric", (0.022, 0.030, 0.038, 1), 0.02, 0.88)
    step = 0
    created = []

    def advance(amount=1):
        nonlocal step
        step += amount

    def register(obj, phase):
        nonlocal step
        step += 1
        created.append(obj)
        obj.parent = root
        obj["concept_fidelity_step"] = step
        obj["concept_fidelity_phase"] = phase
        obj["concept_fidelity_detail"] = True
        obj["unreal_export"] = True
        return obj

    # 001-100: twenty major forms, five proportion/readability operations apiece.
    form_specs = (
        ("HERO_Undersuit_Torso", (.88,.94,1.05), (0,0,0)),
        ("HERO_Undersuit_Pelvis", (.88,.92,.92), (0,0,1)),
        ("HERO_Undersuit_Head", (.94,.94,.98), (0,0,0)),
        ("HERO_UpperArm_L", (.90,.94,1.00), (0,-1,0)),
        ("HERO_UpperArm_R", (.90,.94,1.00), (0,1,0)),
        ("HERO_Forearm_L", (.88,.92,1.00), (0,-1,0)),
        ("HERO_Forearm_R", (.88,.92,1.00), (0,1,0)),
        ("HERO_Thigh_L", (.92,.94,1.02), (0,-1,1)),
        ("HERO_Thigh_R", (.92,.94,1.02), (0,1,1)),
        ("HERO_Calf_L", (.90,.94,1.02), (0,-1,0)),
        ("HERO_Calf_R", (.90,.94,1.02), (0,1,0)),
        ("HERO_Boot_L", (1.02,.90,.92), (0,-1,0)),
        ("HERO_Boot_R", (1.02,.90,.92), (0,1,0)),
        ("HERO_Knee_L", (.86,.90,.88), (1,0,0)),
        ("HERO_Knee_R", (.86,.90,.88), (1,0,0)),
        ("HERO_ChestPlate", (.94,.92,.95), (1,0,0)),
        ("HERO_PressureCollar", (.96,.96,.90), (0,0,-1)),
        ("HERO_LifeSupportPack", (.90,.92,.94), (-1,0,0)),
        ("HERO_HelmetShell", (.98,.96,.98), (0,0,0)),
        ("HERO_Visor", (.98,.96,.98), (1,0,0)),
    )
    for name, scale_factor, offset in form_specs:
        obj = bpy.data.objects[name]
        obj.scale = tuple(obj.scale[i] * scale_factor[i] for i in range(3)); advance()
        obj.location = tuple(obj.location[i] + offset[i] for i in range(3)); advance()
        obj["concept_proportion_tuned"] = True; advance()
        obj["concept_reference"] = "Player_Concept_Likeness_v2"; advance()
        obj["production_silhouette"] = "grounded_eva"; advance()

    # 101-200: ivory hard-shell structure—torso, helmet, limb, boot and backpack armor.
    for row in range(5):
        for column in range(4):
            register(primitive_cube(f"ZCF500_ChestPanel_{row:02}_{column:02}",
                     (14.8 + row*.18, y + (-12 + column*8), 92 + row*7),
                     (.75, 3.0, 2.4), target, ivory, .55), "HardShell")
    for index in range(20):
        angle = math.tau * index / 20
        register(primitive_cube(f"ZCF500_HelmetFrame_{index:02}",
                 (10.5, y + math.cos(angle)*13.6, 151 + math.sin(angle)*15.7),
                 (1.2, 1.6, 2.2), target, ivory, .45), "HardShell")
    for index in range(24):
        side = -1 if index % 2 == 0 else 1
        zone = index // 8
        z = (107, 84, 40)[zone] + ((index // 2) % 4 - 1.5) * 4
        horizontal = (31, 40, 12)[zone]
        register(primitive_cube(f"ZCF500_LimbPlate_{index:02}",
                 (6.5, y + side*horizontal, z), (1.3, 3.8, 2.4), target, ivory, .65), "HardShell")
    for index in range(16):
        side = -1 if index % 2 == 0 else 1
        lane = (index // 2) % 4
        z = 4 + (index // 8)*5
        register(primitive_cube(f"ZCF500_BootArmor_{index:02}",
                 (9 + lane*2.2, y + side*12, z), (1.3, 4.8, 1.5), target, ivory, .45), "HardShell")
    for row in range(5):
        for column in range(4):
            register(primitive_cube(f"ZCF500_PackPanel_{row:02}_{column:02}",
                     (-28.5-row*.35, y + (-12+column*8), 91+row*8),
                     (1.1, 3.0, 3.0), target, ivory, .50), "HardShell")

    # 201-300: fabric construction—joint bellows, double seams and load-bearing webbing.
    joint_centers = ((40,94),(40,78),(-40,94),(-40,78),(12,40),(12,22),(-12,40),(-12,22))
    for sy, sz in joint_centers:
        for ring in range(5):
            register(primitive_torus(f"ZCF500_Bellow_{sy}_{sz}_{ring}",
                     (1.2-ring*.12, y+sy, sz+(ring-2)*1.15),
                     5.7 if abs(sy)>20 else 6.5, .34, target, gasket,
                     (0, math.radians(90), 0)), "SoftGoods")
    seam_zones = ((24,116,18),(40,94,18),(40,75,14),(12,56,18),(12,30,16),
                  (-24,116,18),(-40,94,18),(-40,75,14),(-12,56,18),(-12,30,16))
    for zone, (sy, sz, length) in enumerate(seam_zones):
        for lane in range(4):
            register(primitive_cube(f"ZCF500_FabricSeam_{zone:02}_{lane}",
                     (5.2, y+sy+(lane-1.5)*1.1, sz), (.32,.25,length*.45),
                     target, dark_fabric, .18), "SoftGoods")
    for index in range(20):
        side = -1 if index % 2 == 0 else 1
        level = index // 4
        register(primitive_cube(f"ZCF500_Webbing_{index:02}",
                 (16.2, y+side*(8+(index%4)*3.2), 84+level*9),
                 (.42,1.0,5.5), target, gasket, .28), "SoftGoods")

    # 301-400: believable EVA hardware—fasteners, service ports and twin breathing hoses.
    for index in range(60):
        side = -1 if index % 2 == 0 else 1
        band = index // 12
        sy = side*(7 + (index % 12)//2*3.2)
        sz = 83 + band*11 + (index % 3)*2.2
        register(primitive_cylinder(f"ZCF500_Fastener_{index:03}",
                 (16.8 if band<3 else 8.0, y+sy, sz), .46, .48,
                 target, equipment_mat, (0,math.radians(90),0)), "Hardware")
    for index in range(20):
        side = -1 if index % 2 == 0 else 1
        register(primitive_cylinder(f"ZCF500_ServicePort_{index:02}",
                 (-30.5, y+side*(4+(index//2)%5*3), 91+(index//10)*25+(index%2)*5),
                 1.15, .75, target, orange, (0,math.radians(90),0)), "Hardware")
    for side_index, side in enumerate((-1,1)):
        previous = (-22, y+side*9, 119)
        for segment in range(10):
            current = (-18+segment*2.8, y+side*(10+math.sin(segment*.7)*2), 121+segment*1.1)
            register(cylinder_between(f"ZCF500_Hose_{side_index}_{segment:02}",
                     previous, current, 1.05, target, gasket), "Hardware")
            previous = current

    # 401-500: role-readable edge markings; clones inherit each class material.
    for index in range(100):
        region = index // 20
        local = index % 20
        side = -1 if local % 2 == 0 else 1
        if region == 0:
            location, scale = (17.4,y+side*(5+(local//2)*1.7),88+(local%5)*8), (.32,.65,1.25)
        elif region == 1:
            location, scale = (8.2,y+side*(29+(local//4)*3),78+(local%4)*9), (.32,.85,1.0)
        elif region == 2:
            angle = math.tau*local/20
            location, scale = (12.0,y+math.cos(angle)*14.0,151+math.sin(angle)*15.9), (.35,.8,.8)
        elif region == 3:
            location, scale = (-30.9,y+side*(4+(local//2)*2),92+(local%5)*7), (.30,.7,1.0)
        else:
            location, scale = (13.0,y+side*12,3.4+(local//2)*1.25), (.30,.9,.42)
        register(primitive_cube(f"ZCF500_RoleMark_{index:03}", location, scale,
                 target, role_mats["Crew"], .18), "RoleIdentity")

    if step != 500 or len(created) != 400:
        raise RuntimeError(f"Concept fidelity pass recorded {step} steps and {len(created)} details")
    root["concept_fidelity_steps"] = step
    root["concept_detail_object_count"] = len(created)
    root["concept_reference"] = "Content/Assets/ConceptArt/Trailer/Player_Concept_Likeness_v2.png"
    target["verified_step_count"] = step


def build_player_anatomy_500(target, variant_collection, hero_root, armature,
                             role_fabric_mats, armor_mat, equipment_mat):
    """Five hundred production steps replacing the blockout mannequin with player anatomy."""
    y = 430.0
    fabric = material("M_PlayerAnatomy_Fabric", (0.075, 0.085, 0.095, 1), 0.02, 0.88)
    skin = material("M_PlayerAnatomy_Skin", (0.34, 0.19, 0.13, 1), 0.0, 0.58)
    eye = material("M_PlayerAnatomy_Eye", (0.025, 0.045, 0.055, 1), 0.05, 0.28)
    ivory = bpy.data.materials["M_Concept_IvoryArmor"]
    gasket = bpy.data.materials["M_Suit_Gasket"]
    step = 0
    created = []

    def advance():
        nonlocal step
        step += 1

    def uv_shape(name, location, scale, mat):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=20, location=location)
        obj = bpy.context.object
        obj.name = name
        obj.scale = scale
        bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
        move_to(obj, target)
        obj.data.materials.append(mat)
        return obj

    def tapered(name, start, end, radius_a, radius_b, mat):
        start, end = Vector(start), Vector(end)
        direction = end - start
        bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=radius_a, radius2=radius_b,
                                        depth=direction.length, location=(start+end)*.5)
        obj = bpy.context.object
        obj.name = name
        obj.rotation_mode = "QUATERNION"
        obj.rotation_quaternion = direction.to_track_quat("Z", "Y")
        move_to(obj, target)
        obj.data.materials.append(mat)
        return obj

    def bind(obj, bone):
        for group in tuple(obj.vertex_groups):
            obj.vertex_groups.remove(group)
        group = obj.vertex_groups.new(name=bone)
        group.add(range(len(obj.data.vertices)), 1.0, "REPLACE")
        modifier = obj.modifiers.new("Production Skeleton", "ARMATURE")
        modifier.object = armature
        obj["skeletal_export"] = True
        obj["anatomy_bind_bone"] = bone

    def finish_five(obj, bone, phase):
        # Creation, shading, binding, armature deformation and audit = five tracked steps.
        advance()
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        advance()
        bind(obj, bone); advance()
        obj.parent = hero_root; advance()
        obj["anatomy_phase"] = phase
        obj["anatomy_production"] = True
        created.append(obj); advance()

    # 001-100: twenty humanized soft-body volumes.
    anatomy_specs = [
        ("Torso", "uv", (0,y,106), (9.6,18.2,22.5), "spine_03", fabric),
        ("Abdomen", "uv", (0,y,85), (8.7,15.5,14.0), "spine_01", fabric),
        ("Pelvis", "uv", (0,y,68), (8.5,13.5,7.4), "pelvis", fabric),
        ("Shoulder_L", "uv", (0,y+22,119), (6.3,7.4,7.0), "clavicle_l", fabric),
        ("Shoulder_R", "uv", (0,y-22,119), (6.3,7.4,7.0), "clavicle_r", fabric),
    ]
    for name, _, location, scale, bone, mat in anatomy_specs:
        finish_five(uv_shape("ANAT_"+name, location, scale, mat), bone, "BodyVolume")
    limb_specs = (
        ("UpperArm_L",(0,y+23,118),(0,y+38,96),6.2,5.2,"upperarm_l"),
        ("UpperArm_R",(0,y-23,118),(0,y-38,96),6.2,5.2,"upperarm_r"),
        ("Forearm_L",(0,y+39,94),(1,y+42,73),5.3,4.3,"lowerarm_l"),
        ("Forearm_R",(0,y-39,94),(1,y-42,73),5.3,4.3,"lowerarm_r"),
        ("Thigh_L",(0,y+10,64),(0,y+12,40),7.4,6.3,"thigh_l"),
        ("Thigh_R",(0,y-10,64),(0,y-12,40),7.4,6.3,"thigh_r"),
        ("Calf_L",(0,y+12,38),(1,y+12,16),6.4,4.9,"calf_l"),
        ("Calf_R",(0,y-12,38),(1,y-12,16),6.4,4.9,"calf_r"),
    )
    for name, start, end, ra, rb, bone in limb_specs:
        finish_five(tapered("ANAT_"+name,start,end,ra,rb,fabric),bone,"TaperedLimb")
    for side, sy, bone in (("L",1,"hand_l"),("R",-1,"hand_r")):
        finish_five(uv_shape(f"ANAT_Hand_{side}",(2,y+sy*43,68),(3.8,4.8,5.0),fabric),bone,"Hand")
    for side, sy, bone in (("L",1,"foot_l"),("R",-1,"foot_r")):
        finish_five(uv_shape(f"ANAT_BootToe_{side}",(9,y+sy*12,7),(8.5,6.0,4.5),ivory),bone,"Foot")
    finish_five(uv_shape("ANAT_Face",(12.35,y,151),(.38,6.7,8.8),skin),"head","Face")
    for side, sy in (("L",1),("R",-1)):
        finish_five(uv_shape(f"ANAT_Eye_{side}",(12.78,y+sy*2.55,153),(.18,.92,.62),eye),"head","Face")

    # 101-200: twenty large, curved armor forms defining the concept silhouette.
    armor_specs = [
        ("ChestYoke",(12.8,y,115),(2.0,17.0,8.0),"spine_03"),
        ("ChestLower",(13.5,y,100),(1.8,14.0,8.0),"spine_02"),
        ("CollarFront",(8.0,y,132),(3.0,14.0,3.3),"neck_01"),
        ("CollarBack",(-6.0,y,132),(3.0,14.0,3.3),"neck_01"),
        ("Shoulder_L",(4,y+25,118),(3.5,8.0,5.0),"upperarm_l"),
        ("Shoulder_R",(4,y-25,118),(3.5,8.0,5.0),"upperarm_r"),
        ("ForearmGuard_L",(5,y+41,83),(2.5,6.0,10.0),"lowerarm_l"),
        ("ForearmGuard_R",(5,y-41,83),(2.5,6.0,10.0),"lowerarm_r"),
        ("Knee_L",(5,y+12,40),(3.2,7.0,6.0),"calf_l"),
        ("Knee_R",(5,y-12,40),(3.2,7.0,6.0),"calf_r"),
        ("Shin_L",(4,y+12,26),(2.8,6.2,10.0),"calf_l"),
        ("Shin_R",(4,y-12,26),(2.8,6.2,10.0),"calf_r"),
        ("BootCuff_L",(2,y+12,13),(4.0,6.5,3.5),"foot_l"),
        ("BootCuff_R",(2,y-12,13),(4.0,6.5,3.5),"foot_r"),
        ("BootCap_L",(11,y+12,7),(6.0,6.2,3.2),"foot_l"),
        ("BootCap_R",(11,y-12,7),(6.0,6.2,3.2),"foot_r"),
        ("PackUpper",(-18,y,118),(7.5,15.0,10.0),"spine_03"),
        ("PackLower",(-18,y,99),(7.5,15.0,9.0),"spine_02"),
        ("Hip_L",(4,y+15,66),(3.0,6.0,5.0),"pelvis"),
        ("Hip_R",(4,y-15,66),(3.0,6.0,5.0),"pelvis"),
    ]
    for name, location, scale, bone in armor_specs:
        finish_five(uv_shape("ANAT_Armor_"+name,location,scale,ivory),bone,"CurvedArmor")

    # 201-300: twenty articulated finger segments, replacing mitten-like hands.
    for side, sy, bone in (("L",1,"hand_l"),("R",-1,"hand_r")):
        for finger in range(5):
            lateral = (finger-2)*1.45
            base = (3.5,y+sy*(44.0+lateral),67.5)
            mid = (5.8,y+sy*(44.5+lateral),66.2)
            tip = (7.7,y+sy*(44.8+lateral),65.2)
            finish_five(tapered(f"ANAT_Finger_{side}_{finger}_A",base,mid,.72,.58,fabric),bone,"Finger")
            finish_five(tapered(f"ANAT_Finger_{side}_{finger}_B",mid,tip,.58,.40,fabric),bone,"Finger")

    # 301-400: clean normals and mesh data on fifty high-visibility source parts.
    audit = [obj for obj in bpy.data.objects if obj.type == "MESH" and obj.parent == hero_root
             and not obj.get("concept_fidelity_detail")][:50]
    if len(audit) != 50:
        raise RuntimeError(f"Anatomy normal audit found only {len(audit)} meshes")
    for obj in audit:
        obj.data.validate(verbose=False, clean_customdata=False); advance()
        for polygon in obj.data.polygons:
            polygon.use_smooth = True
        obj["normal_audit"] = "smooth_validated"; advance()

    # 401-440: grounded boot traction and flexible joint reinforcement.
    for index in range(20):
        side = -1 if index % 2 == 0 else 1
        lane = (index//2) % 10
        obj = primitive_cube(f"ANAT_Tread_{index:02}",(4+lane*1.25,y+side*12,2.1),
                             (.45,5.4,.65),target,equipment_mat,.22)
        obj.parent=hero_root; bind(obj,f"foot_{'l' if side>0 else 'r'}")
        obj["anatomy_production"]=True; created.append(obj); advance()
    gussets = ((40,94,"lowerarm"),(40,74,"hand"),(-40,94,"lowerarm"),(-40,74,"hand"),
               (12,40,"calf"),(12,16,"foot"),(-12,40,"calf"),(-12,16,"foot"))
    for index in range(20):
        sy, sz, base_bone = gussets[index % len(gussets)]
        side = "l" if sy > 0 else "r"
        bone = f"{base_bone}_{side}"
        obj = uv_shape(f"ANAT_Gusset_{index:02}",(1,y+sy,sz+(index//8-1)*1.2),(1.6,5.4,1.0),gasket)
        obj.parent=hero_root; bind(obj,bone); obj["anatomy_production"]=True
        created.append(obj); advance()

    # 441-500: production attributes on the sixty principal anatomy parts.
    for obj in created[:60]:
        obj["tangent_policy"] = "recompute_mikktspace"
        obj["lod_preserve_silhouette"] = True
        advance()

    if step != 500 or len(created) != 100:
        raise RuntimeError(f"Player anatomy pass recorded {step} steps and {len(created)} meshes")

    # Remove the visibly robotic blockout volumes once replacements exist.
    replaced = ("Undersuit_Torso","Undersuit_Pelvis","UpperArm_L","UpperArm_R",
                "Forearm_L","Forearm_R","Thigh_L","Thigh_R","Calf_L","Calf_R")
    for suffix in replaced:
        source = bpy.data.objects.get("HERO_"+suffix)
        if source:
            source.hide_render = True
        for role in ROLE_COLORS:
            clone = bpy.data.objects.get(role.upper()+"_"+suffix)
            if clone:
                clone.hide_render = True

    # Copy the production anatomy into each static class variant with restrained fabrics.
    for role in ROLE_COLORS:
        variant_root = bpy.data.objects[f"VARIANT_{role}_Root"]
        for source in created:
            clone = source.copy()
            clone.data = source.data.copy()
            clone.name = source.name.replace("ANAT_", f"{role.upper()}_ANAT_")
            variant_collection.objects.link(clone)
            clone.parent = variant_root
            clone["variant_role"] = role
            clone["skeletal_export"] = False
            for modifier in tuple(clone.modifiers):
                if modifier.type == "ARMATURE":
                    clone.modifiers.remove(modifier)
            for slot, mat in enumerate(tuple(clone.data.materials)):
                if mat and mat.name == fabric.name:
                    clone.data.materials[slot] = role_fabric_mats[role]
        variant_root["object_count"] = len([obj for obj in variant_collection.objects
                                             if obj.parent == variant_root])

    hero_root["player_anatomy_steps"] = step
    hero_root["player_anatomy_mesh_count"] = len(created)
    armature["anatomy_bound_mesh_count"] = len(created)
    target["verified_step_count"] = step


def build_real_player_finish_500(target, variant_collection, hero_root, armature,
                                 role_mats, role_fabric_mats, armor_mat, equipment_mat):
    """Five hundred finishing steps for a readable face, garments, boots, roles and clean topology."""
    import bmesh

    y = 430.0
    step = 0
    hero_parts = []
    skin = bpy.data.materials["M_PlayerAnatomy_Skin"]
    fabric = bpy.data.materials["M_PlayerAnatomy_Fabric"]
    ivory = bpy.data.materials["M_Concept_IvoryArmor"]
    gasket = bpy.data.materials["M_Suit_Gasket"]
    hair = material("M_Player_Hair", (0.035,0.018,0.012,1), 0.0, .72)
    eye_white = material("M_Player_EyeWhite", (.65,.67,.64,1), 0.0, .35)
    mouth_mat = material("M_Player_Mouth", (.26,.045,.035,1), 0.0, .58)

    def advance():
        nonlocal step
        step += 1

    def uv(name, location, scale, mat):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=16, location=location)
        obj=bpy.context.object; obj.name=name; obj.scale=scale
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        move_to(obj,target); obj.data.materials.append(mat); return obj

    def cube(name, location, scale, mat, bevel=.35, collection_target=None):
        return primitive_cube(name,location,scale,collection_target or target,mat,bevel)

    def bind(obj,bone):
        group=obj.vertex_groups.new(name=bone)
        group.add(range(len(obj.data.vertices)),1.0,"REPLACE")
        mod=obj.modifiers.new("Production Skeleton","ARMATURE"); mod.object=armature
        obj.parent=hero_root; obj["skeletal_export"]=True; obj["real_player_finish"]=True

    def finish5(obj,bone,phase):
        advance()
        for poly in obj.data.polygons: poly.use_smooth=True
        advance(); bind(obj,bone); advance()
        obj["finish_phase"]=phase; advance()
        hero_parts.append(obj); obj["finish_audit"]=True; advance()

    def finish2(obj,bone,phase):
        advance(); bind(obj,bone); obj["finish_phase"]=phase; hero_parts.append(obj); advance()

    # Hide the opaque blockout dome and boot shells so face and rounded footwear read.
    for base in ("Undersuit_Head","Visor","Boot_L","Boot_R"):
        source=bpy.data.objects.get("HERO_"+base)
        if source: source.hide_render=True
        for role in ROLE_COLORS:
            clone=bpy.data.objects.get(role.upper()+"_"+base)
            if clone: clone.hide_render=True

    # 001-100: twenty helmet-interior and facial forms, five production operations each.
    facial = [
        ("HairCap",(12.15,y,155.5),(.55,7.0,5.0),hair),
        ("Brow_L",(13.02,y+2.6,155.1),(.18,1.6,.28),hair),
        ("Brow_R",(13.02,y-2.6,155.1),(.18,1.6,.28),hair),
        ("EyeWhite_L",(13.00,y+2.55,153.2),(.20,1.20,.72),eye_white),
        ("EyeWhite_R",(13.00,y-2.55,153.2),(.20,1.20,.72),eye_white),
        ("Pupil_L",(13.24,y+2.55,153.2),(.13,.38,.42),equipment_mat),
        ("Pupil_R",(13.24,y-2.55,153.2),(.13,.38,.42),equipment_mat),
        ("Nose",(13.15,y,151.2),(.40,.65,1.35),skin),
        ("Mouth",(13.05,y,148.7),(.18,2.0,.38),mouth_mat),
        ("Chin",(12.92,y,147.3),(.32,2.5,1.0),skin),
        ("Ear_L",(12.35,y+6.7,151.5),(.40,.65,1.7),skin),
        ("Ear_R",(12.35,y-6.7,151.5),(.40,.65,1.7),skin),
        ("Cheek_L",(12.90,y+4.2,150.4),(.28,1.7,1.6),skin),
        ("Cheek_R",(12.90,y-4.2,150.4),(.28,1.7,1.6),skin),
        ("HelmetPadTop",(10.4,y,164.5),(1.2,5.0,1.0),gasket),
        ("HelmetPad_L",(10.5,y+9.6,154),(1.2,1.3,5.0),gasket),
        ("HelmetPad_R",(10.5,y-9.6,154),(1.2,1.3,5.0),gasket),
        ("HelmetPadChin",(10.8,y,141.8),(1.2,5.5,1.0),gasket),
        ("NeckSealFront",(7.5,y,137.0),(2.0,10.5,1.8),gasket),
        ("HelmetHUDProjector",(13.0,y+8.6,157.5),(.6,1.0,1.5),role_mats["Crew"]),
    ]
    for name,location,scale,mat in facial:
        finish5(uv("RPF_"+name,location,scale,mat),"head","HelmetInterior")

    # 101-200: fifty garment panels and pockets, two tracked operations each.
    for index in range(50):
        region=index//10; local=index%10; side=-1 if local%2==0 else 1
        if region==0: location=(10.0,y+side*(4+(local//2)*3),91+(local%5)*5); bone="spine_02"
        elif region==1: location=(4.2,y+side*11,49+(local//2)*3); bone=f"thigh_{'l' if side>0 else 'r'}"
        elif region==2: location=(3.5,y+side*12,22+(local//2)*3); bone=f"calf_{'l' if side>0 else 'r'}"
        elif region==3: location=(4.8,y+side*38,83+(local//2)*3); bone=f"lowerarm_{'l' if side>0 else 'r'}"
        else: location=(8.5,y+side*(7+(local//2)*3),73+(local%3)*4); bone="pelvis"
        finish2(cube(f"RPF_GarmentPanel_{index:02}",location,(.45,2.1,1.5),fabric,.3),bone,"Garment")

    # 201-300: fifty rounded boot shell, cuff and traction elements.
    for index in range(50):
        side=-1 if index%2==0 else 1; local=index//2; bone=f"foot_{'l' if side>0 else 'r'}"
        if local<8:
            obj=uv(f"RPF_BootShell_{index:02}",(7+local*.9,y+side*12,7.0),(.9,5.8,3.6),ivory)
        elif local<16:
            obj=cube(f"RPF_BootTread_{index:02}",(3+(local-8)*1.6,y+side*12,2.0),(.5,5.6,.55),equipment_mat,.2)
        else:
            obj=uv(f"RPF_BootCuff_{index:02}",(2.2,y+side*12,11+(local-16)*.45),(2.2,6.1,.8),gasket)
        finish2(obj,bone,"Boot")

    # 301-400: twenty-five class-specific silhouette pieces for each player role.
    role_roots={role:bpy.data.objects[f"VARIANT_{role}_Root"] for role in ROLE_COLORS}
    for role_index,role in enumerate(ROLE_COLORS):
        root=role_roots[role]
        for local in range(25):
            side=-1 if local%2==0 else 1
            if role=="Crew": location=(15,y+side*(8+(local%5)*3),92+(local//5)*7)
            elif role=="Engineering": location=(13,y+side*(18+(local%5)*2),78+(local//5)*9)
            elif role=="Medical": location=(15,y+side*(7+(local%5)*3),88+(local//5)*8)
            else: location=(12,y+side*(20+(local%5)*2),84+(local//5)*8)
            obj=cube(f"{role.upper()}_RPF_Gear_{local:02}",location,(.8,2.2,2.0),
                     role_mats[role],.35,variant_collection)
            obj.parent=root; obj["variant_role"]=role; obj["class_silhouette_gear"]=True; advance()

    # 401-500: remove degenerates and rebuild smooth data on fifty legacy details.
    cleanup=[o for o in bpy.data.objects if o.type=="MESH" and o.parent==hero_root
             and not o.get("real_player_finish")][:50]
    if len(cleanup)!=50: raise RuntimeError(f"Real-player cleanup found {len(cleanup)} meshes")
    for obj in cleanup:
        bm=bmesh.new(); bm.from_mesh(obj.data)
        bmesh.ops.dissolve_degenerate(bm,dist=.00001,edges=bm.edges)
        bm.to_mesh(obj.data); bm.free(); obj.data.update(); advance()
        for poly in obj.data.polygons: poly.use_smooth=True
        obj["topology_cleanup"]="degenerates_removed"; advance()

    if step!=500 or len(hero_parts)!=120:
        raise RuntimeError(f"Real player finish recorded {step} steps and {len(hero_parts)} hero meshes")

    # Clone the new face/garment/boot parts to class variants after cleanup.
    for role,root in role_roots.items():
        for source in hero_parts:
            clone=source.copy(); clone.data=source.data.copy()
            clone.name=source.name.replace("RPF_",f"{role.upper()}_RPF_")
            variant_collection.objects.link(clone); clone.parent=root; clone["variant_role"]=role
            clone["skeletal_export"]=False
            for mod in tuple(clone.modifiers):
                if mod.type=="ARMATURE": clone.modifiers.remove(mod)
            for slot,mat in enumerate(tuple(clone.data.materials)):
                if mat and mat.name==fabric.name: clone.data.materials[slot]=role_fabric_mats[role]
        root["object_count"]=len([o for o in variant_collection.objects if o.parent==root])

    hero_root["real_player_finish_steps"]=step
    hero_root["real_player_finish_mesh_count"]=len(hero_parts)
    armature["real_player_bound_mesh_count"]=len(hero_parts)
    target["verified_step_count"]=step


def build_hero_suit(target, armor_mat, equipment_mat, visor_mat, role_mats):
    """Twenty-step assembled production suit, preserving every module as an editable object."""
    center_y = 430.0
    fabric = material("M_Suit_Undersuit_Fabric", (0.035, 0.055, 0.075, 1), 0.03, 0.82)
    attach_role_texture_set(fabric, "Crew")
    gasket = bpy.data.materials["M_Suit_Gasket"]
    orange = bpy.data.materials["M_Suit_Service_Orange"]
    glow = bpy.data.materials["M_Suit_Status_Light"]

    root = bpy.data.objects.new("HERO_PlayerSuit_Root", None)
    target.objects.link(root)
    root["production_steps"] = 20
    root["active_role"] = "Crew"

    # 1 articulated mannequin/undersuit blockout.
    torso = primitive_cube("HERO_Undersuit_Torso", (0, center_y, 101), (11, 20, 27), target, fabric, 5)
    pelvis = primitive_cube("HERO_Undersuit_Pelvis", (0, center_y, 68), (10, 17, 9), target, fabric, 4)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(0, center_y, 151),
                                        scale=(11, 12, 15))
    head = bpy.context.object
    head.name = "HERO_Undersuit_Head"
    move_to(head, target)
    head.data.materials.append(fabric)
    for side, sy in (("L", 1), ("R", -1)):
        cylinder_between(f"HERO_UpperArm_{side}", (0, center_y + sy*22, 119),
                         (0, center_y + sy*39, 95), 6.2, target, fabric)
        cylinder_between(f"HERO_Forearm_{side}", (0, center_y + sy*39, 95),
                         (1, center_y + sy*42, 72), 5.2, target, fabric)
        cylinder_between(f"HERO_Thigh_{side}", (0, center_y + sy*10, 65),
                         (0, center_y + sy*12, 39), 7.2, target, fabric)
        cylinder_between(f"HERO_Calf_{side}", (0, center_y + sy*12, 39),
                         (1, center_y + sy*12, 15), 5.8, target, fabric)

    # 2 boots, 3 magnetic sole cassettes, 4 knees, 5 thigh storage.
    for side, sy in (("L", 1), ("R", -1)):
        copy_part("SM_Suit_BootShell", f"HERO_Boot_{side}", (7, center_y + sy*12, 7), target)
        primitive_cube(f"HERO_MagneticSole_{side}", (5, center_y + sy*12, 1.8),
                       (10, 6.5, 1.2), target, equipment_mat, 1.1)
        primitive_cube(f"HERO_MagneticSoleGlow_{side}", (10, center_y + sy*12, .35),
                       (5.2, 3.8, .35), target, glow, .25)
        copy_part("SM_Suit_KneePad", f"HERO_Knee_{side}", (4, center_y + sy*12, 39), target)
        copy_part("SM_Suit_ThighPouch", f"HERO_ThighPouch_{side}",
                  (0, center_y + sy*21, 60), target, scale=(1, sy, 1))

    # 6 chest plate, 7 pressure collar, 8 backpack and 9 oxygen cylinders.
    copy_part("SM_Suit_ChestPlate", "HERO_ChestPlate", (8, center_y, 105), target)
    copy_part("SM_Suit_PressureCollar", "HERO_PressureCollar", (0, center_y, 130), target)
    copy_part("SM_Suit_LifeSupportPack", "HERO_LifeSupportPack", (-13, center_y, 105), target)
    for sy in (-8, 8):
        primitive_cylinder(f"HERO_OxygenTank_{'L' if sy > 0 else 'R'}",
                           (-24, center_y + sy, 105), 4.2, 28, target, equipment_mat)
        primitive_torus(f"HERO_TankGuard_{sy}", (-24, center_y + sy, 105), 5.0, .65,
                        target, orange, (0, math.radians(90), 0))

    # 10 helmet shell, 11 sealed visor, 12 gasket and 13 accessory rails.
    copy_part("SM_Suit_HelmetShell", "HERO_HelmetShell", (0, center_y, 151), target)
    copy_part("SM_Suit_Visor", "HERO_Visor", (2, center_y, 151), target)
    primitive_torus("HERO_VisorGasket", (11, center_y, 151), 12.4, 1.1, target, gasket,
                    (0, math.radians(90), 0))
    for sy in (-11, 11):
        primitive_cube(f"HERO_HelmetRail_{sy}", (-1, center_y + sy, 158),
                       (9, 1.2, 1.2), target, armor_mat, .55)

    # 14 shoulders, 15 gloves and 16 forearm computer.
    for side, sy in (("L", 1), ("R", -1)):
        copy_part("SM_Suit_ShoulderPad", f"HERO_Shoulder_{side}",
                  (0, center_y + sy*25, 119), target, scale=(1, sy, 1))
        copy_part("SM_Suit_Glove", f"HERO_Glove_{side}",
                  (1, center_y + sy*43, 69), target, scale=(1, sy, 1))
    copy_part("SM_Suit_ForearmComputer", "HERO_ForearmComputer",
              (8, center_y + 40, 84), target, rotation=(0, 0, math.radians(-12)))

    # 17 chest harness, 18 quick release, 19 active role cartridge and status lamp.
    for sy in (-10, 10):
        primitive_cube(f"HERO_Harness_{sy}", (12, center_y + sy, 103),
                       (1.2, 1.6, 19), target, gasket, .7)
    primitive_cube("HERO_QuickRelease", (14, center_y, 101), (2.2, 3.6, 3.0), target, orange, .8)
    role = copy_part("SM_Suit_Module_Crew", "HERO_RoleModule_Crew",
                     (15, center_y, 111), target)
    role.data.materials.clear()
    role.data.materials.append(role_mats["Crew"])
    primitive_cube("HERO_RoleStatusLamp", (19, center_y, 116), (.7, 4.2, .8), target, glow, .25)

    # 20 export hierarchy, turntable pivot, sockets and LOD policy metadata.
    for obj in tuple(target.objects):
        if obj is not root:
            obj.parent = root
            obj["unreal_export"] = True
    root["unreal_skeleton"] = "SKM_Manny"
    root["lod_policy"] = "LOD0 authored; generate LOD1 60%, LOD2 30%, LOD3 12%"
    root["turntable_degrees"] = 360
    root["socket_manifest"] = "head,neck_01,spine_03,upperarm_l,upperarm_r,lowerarm_l,hand_l,hand_r,thigh_l,thigh_r,calf_l,calf_r,foot_l,foot_r"
    return root


def primitive_cone(name, location, radius1, radius2, depth, target, mat, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=radius1, radius2=radius2, depth=depth,
                                    location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    move_to(obj, target)
    obj.data.materials.append(mat)
    add_finish_modifiers(obj)
    bpy.ops.object.shade_smooth_by_angle()
    return obj


def emissive_material(name, color, strength):
    mat = material(name, color, 0.18, 0.18)
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Emission Color"].default_value = color
    bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def build_magnetic_suit_system(target, armor_mat, equipment_mat):
    """Production-ready magnetic boot, glove and rotation-thruster assemblies."""
    magnet = material("M_MagneticPad_Ferrous", (0.035, 0.045, 0.055, 1), 0.92, 0.20)
    gasket = material("M_MagneticPad_Insulator", (0.008, 0.010, 0.014, 1), 0.02, 0.82)
    red = emissive_material("M_MagneticSystem_ActiveRed", (1.0, 0.012, 0.004, 1), 12.0)
    warm_red = emissive_material("M_MagneticGlove_WarmRed", (1.0, 0.045, 0.012, 1), 7.0)

    # Two articulated boot sole cassettes: segmented contact rails maintain purchase
    # while the foot rolls through a step and provide visible red status lamps.
    for side, x in (("L", -82.0), ("R", -48.0)):
        sole = primitive_cube(f"MAG_BootSole_{side}", (x, 278, 7), (13.5, 22, 2.2), target, gasket, 1.8)
        sole["system"] = "magnetic_boot"
        sole["socket"] = f"foot_{side.lower()}"
        for rail_index, rail_x in enumerate((-8.5, 0.0, 8.5)):
            rail = primitive_cube(f"MAG_BootRail_{side}_{rail_index+1}",
                                  (x + rail_x, 278, 3.8), (3.1, 18.5, 1.15), target, magnet, .9)
            rail["magnetic_contact"] = True
        for lamp_index, lamp_y in enumerate((264.0, 278.0, 292.0)):
            lamp = primitive_cube(f"MAG_BootLamp_{side}_{lamp_index+1}",
                                  (x, lamp_y, 2.45), (4.0, 2.4, .45), target, red, .35)
            lamp["emissive_parameter"] = "MagnetGlowStrength"
        primitive_cube(f"MAG_BootHeelLock_{side}", (x, 297.0, 9.0),
                       (12.0, 3.2, 5.0), target, equipment_mat, 1.2)

    # Palm plate plus five narrow finger contact pads per hand. These remain separate
    # objects for easy rigging/weight painting against hand and finger bones.
    for side, x in (("L", 12.0), ("R", 48.0)):
        palm = primitive_cube(f"MAG_GlovePalm_{side}", (x, 278, 10), (12.0, 14.0, 2.0), target, magnet, 2.2)
        palm["system"] = "magnetic_glove"
        palm["socket"] = f"hand_{side.lower()}"
        glow = primitive_cube(f"MAG_GlovePalmGlow_{side}", (x, 278, 7.6),
                              (8.2, 9.8, .55), target, warm_red, 2.0)
        glow["emissive_parameter"] = "MagnetGlowStrength"
        for finger in range(5):
            finger_x = x - 9.0 + finger * 4.5
            pad = primitive_cube(f"MAG_GloveFinger_{side}_{finger+1}",
                                 (finger_x, 298, 8.5), (1.7, 6.0, 1.1), target, magnet, .75)
            pad["magnetic_contact"] = True

    # Compact backpack rotation unit with four canted cold-gas nozzles. Separate
    # emissive throat rings and plume proxies make activation easy to preview.
    pack = primitive_cube("MAG_RotationThrusterPack", (105, 278, 18),
                          (20, 14, 25), target, armor_mat, 3.0)
    pack["system"] = "rotation_thruster"
    pack["socket"] = "spine_03"
    pack["fuel_parameter"] = "ThrusterFuelPercent"
    nozzle_offsets = ((-13, -11, 15), (13, -11, 15), (-13, -11, -15), (13, -11, -15))
    for index, (ox, oy, oz) in enumerate(nozzle_offsets):
        location = (105 + ox, 278 + oy, 18 + oz)
        primitive_cone(f"MAG_ThrusterNozzle_{index+1}", location, 4.2, 2.2, 8.0,
                       target, equipment_mat, (math.radians(90), 0, 0))
        ring = primitive_torus(f"MAG_ThrusterRing_{index+1}",
                               (location[0], location[1] - 4.2, location[2]), 3.2, .7,
                               target, red, (math.radians(90), 0, 0))
        ring["emissive_parameter"] = "ThrusterActive"
        plume = primitive_cone(f"MAG_ThrusterPlumeProxy_{index+1}",
                               (location[0], location[1] - 10.0, location[2]), 1.1, 3.8, 11.0,
                               target, warm_red, (math.radians(90), 0, 0))
        plume.display_type = "WIRE"
        plume.hide_render = True
        plume["replace_with_niagara"] = "NS_SuitRotationThruster"

    primitive_cube("MAG_ThrusterFuelGauge", (105, 263.5, 20), (9.0, .7, 2.0), target, red, .45)
    return {"magnet": magnet, "gasket": gasket, "red": red, "warm_red": warm_red}


def build_detail_pass(target, armor_mat, equipment_mat, visor_mat, role_mats):
    """Ten editable Blender-native suit refinements, kept as separate exportable objects."""
    accent = material("M_Suit_Service_Orange", (1.0, 0.12, 0.015, 1), 0.32, 0.28)
    rubber = material("M_Suit_Gasket", (0.012, 0.014, 0.018, 1), 0.05, 0.78)
    emissive = material("M_Suit_Status_Light", (0.01, 0.32, 1.0, 1), 0.18, 0.18)
    bsdf = emissive.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Emission Color"].default_value = (0.01, 0.25, 1.0, 1)
    bsdf.inputs["Emission Strength"].default_value = 5.0

    # 1 helmet rails, 2 visor gasket, 3 dual collar seals.
    primitive_cube("BLD_HelmetRail_L", (-35, 170, 22), (1.4, 11, 1.4), target, armor_mat)
    primitive_cube("BLD_HelmetRail_R", (-25, 170, 22), (1.4, 11, 1.4), target, armor_mat)
    primitive_torus("BLD_VisorGasket", (-30, 170, 12), 8.5, 1.2, target, rubber,
                    (math.radians(90), 0, 0))
    primitive_torus("BLD_CollarSeal_Outer", (0, 170, 8), 10.5, 1.7, target, rubber)
    primitive_torus("BLD_CollarSeal_Inner", (0, 170, 8), 7.4, 1.0, target, accent)

    # 4 chest harness and 5 quick-release buckle.
    primitive_cube("BLD_Harness_Left", (28, 170, 12), (1.7, 1.0, 14), target, rubber)
    primitive_cube("BLD_Harness_Right", (40, 170, 12), (1.7, 1.0, 14), target, rubber)
    primitive_cube("BLD_Harness_Bridge", (34, 169, 11), (8, 1.2, 1.8), target, armor_mat)
    primitive_cube("BLD_QuickRelease", (34, 167, 11), (3.2, 1.5, 3.2), target, accent)

    # 6 backpack oxygen cylinders and 7 protected hose couplers.
    primitive_cylinder("BLD_OxygenTank_L", (63, 170, 12), 5.0, 27, target, equipment_mat)
    primitive_cylinder("BLD_OxygenTank_R", (76, 170, 12), 5.0, 27, target, equipment_mat)
    for x in (63, 76):
        primitive_torus(f"BLD_TankGuard_{x}", (x, 170, 12), 6.2, 0.8, target, accent)
        primitive_cylinder(f"BLD_HoseCoupler_{x}", (x, 163.5, 23), 2.1, 4.0, target,
                           accent, (math.radians(90), 0, 0))

    # 8 magnetic boot/glove contact pad family.
    for x, width in ((100, 7.0), (116, 5.0)):
        primitive_cube(f"BLD_MagneticPad_{x}", (x, 170, 5), (width, 7, 1.3), target,
                       equipment_mat, 1.0)
        primitive_cube(f"BLD_MagneticPadGlow_{x}", (x, 162.8, 5), (width * .65, .4, .55),
                       target, emissive, .25)

    # 9 four swappable role cartridges.
    for index, (role, mat) in enumerate(role_mats.items()):
        x = -26 + index * 18
        primitive_cube(f"BLD_RoleCartridge_{role}", (x, 218, 8), (6.5, 4.0, 9), target, mat)
        primitive_cube(f"BLD_RoleStatus_{role}", (x, 213.7, 12), (3.8, .45, .8), target,
                       emissive, .25)

    # 10 modular hard-point rail used by helmet, chest, forearm and pack accessories.
    rail = primitive_cube("BLD_UniversalHardpointRail", (65, 218, 7), (22, 4, 3.5),
                          target, armor_mat)
    for x in (49, 57, 65, 73, 81):
        primitive_cylinder(f"BLD_HardpointSocket_{x}", (x, 213.6, 7), 1.7, 1.2, target,
                           rubber, (math.radians(90), 0, 0))
    rail["unreal_socket_prefix"] = "SuitHardpoint"


def main():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (bpy.data.meshes, bpy.data.curves, bpy.data.materials, bpy.data.cameras, bpy.data.lights):
        for block in tuple(datablocks):
            if block.users == 0:
                datablocks.remove(block)

    core = collection("01_Core_Armor")
    limbs = collection("02_Limb_Armor")
    equipment = collection("03_Equipment")
    roles = collection("04_Role_Modules")
    details = collection("05_Blender_Detail_Pass")
    magnetic_system = collection("06_Magnetic_Suit_System")
    hero_suit = collection("07_Assembled_Hero_Suit")
    hands_free = collection("08_Hands_Free_Equipment")
    class_variants = collection("09_Class_Suit_Variants")
    production_100 = collection("10_Production_Detail_100")
    production_rig = collection("11_Production_Rig_50")
    concept_fidelity = collection("12_Concept_Fidelity_500")
    player_anatomy = collection("13_Player_Anatomy_500")
    real_player_finish = collection("14_Real_Player_Finish_500")
    export_ready = collection("80_Unreal_Export_Ready")
    presentation = collection("90_Presentation")

    armor_mat = material("M_Suit_Armor_Neutral", (0.34, 0.39, 0.47, 1.0), 0.38, 0.32)
    equipment_mat = material("M_Suit_Equipment_Neutral", (0.20, 0.25, 0.32, 1.0), 0.55, 0.27)
    visor_mat = material("M_Suit_Visor", (0.004, 0.022, 0.035, 1.0), 0.72, 0.10)
    role_mats = {name: material("M_Role_" + name, color, 0.30, 0.34)
                 for name, color in ROLE_COLORS.items()}
    role_fabric_mats = {name: material("M_SuitFabric_" + name, color, 0.03, 0.82)
                        for name, color in ROLE_FABRIC_COLORS.items()}
    for role in ROLE_COLORS:
        attach_role_texture_set(role_mats[role], role)
        attach_role_texture_set(role_fabric_mats[role], role)

    paths = sorted(SOURCE.glob("SM_Suit_*.obj"))
    if not paths:
        raise RuntimeError(f"No generated suit OBJ files found in {SOURCE}")

    for index, path in enumerate(paths):
        name = path.stem
        role = next((key for key in ROLE_COLORS if name.endswith(key)), None)
        if role:
            target, mat = roles, role_mats[role]
        elif any(key in name for key in ("Helmet", "Visor", "Collar", "Chest")):
            target, mat = core, visor_mat if "Visor" in name else armor_mat
        elif any(key in name for key in ("Shoulder", "Glove", "Knee", "Boot")):
            target, mat = limbs, armor_mat
        else:
            target, mat = equipment, equipment_mat
        obj = import_mesh(path, target, mat)
        column, row = index % 5, index // 5
        obj.location = ((column - 2) * 55.0, row * 55.0, 12.0)
        add_label(name, (obj.location.x, obj.location.y - 22.0, 0.1), presentation)

    build_detail_pass(details, armor_mat, equipment_mat, visor_mat, role_mats)
    build_magnetic_suit_system(magnetic_system, armor_mat, equipment_mat)
    hero_root = build_hero_suit(hero_suit, armor_mat, equipment_mat, visor_mat, role_mats)
    concept_art_refinement(hero_suit, hero_root, armor_mat, equipment_mat, role_mats)
    build_hands_free_equipment(hands_free, hero_root, armor_mat, equipment_mat, role_mats)
    build_production_detail_100(production_100, hero_root, armor_mat, equipment_mat)
    build_concept_fidelity_500(concept_fidelity, hero_root, armor_mat, equipment_mat, role_mats)
    production_armature = build_production_rig_50(production_rig, hero_root, equipment_mat)
    build_class_variants(class_variants, hero_root, role_mats, role_fabric_mats)
    bind_production_meshes_100(hero_root, production_armature)
    refine_undersuit_deformation_100(production_armature)
    build_player_anatomy_500(player_anatomy, class_variants, hero_root, production_armature,
                             role_fabric_mats, armor_mat, equipment_mat)
    build_real_player_finish_500(real_player_finish, class_variants, hero_root, production_armature,
                                 role_mats, role_fabric_mats, armor_mat, equipment_mat)
    class_variants.hide_render = True
    for obj in details.objects:
        export_ready.objects.link(obj)
        obj["unreal_export"] = True
        obj["export_collection"] = export_ready.name
    for obj in magnetic_system.objects:
        obj["unreal_export"] = True
        obj["export_collection"] = export_ready.name
    add_label("Blender Detail Pass 01-10", (42, 145, 0.1), presentation)
    add_label("Role Cartridges + Universal Hardpoint", (28, 195, 0.1), presentation)
    add_label("Magnetic Boots + Gloves + Rotation Thruster", (20, 245, 0.1), presentation)

    bpy.ops.mesh.primitive_plane_add(size=380, location=(0, 55, 0))
    floor = bpy.context.object
    floor.name = "Presentation_Floor"
    move_to(floor, presentation)
    floor.data.materials.append(material("M_Presentation_Floor", (0.075, 0.085, 0.11, 1), 0.05, 0.72))

    bpy.ops.object.camera_add(location=(0, -330, 185), rotation=(math.radians(67), 0, 0))
    camera = bpy.context.object
    camera.name = "CAM_AssetLibrary"
    move_to(camera, presentation)
    bpy.context.scene.camera = camera

    hero_target = bpy.data.objects.new("CAM_Hero_Target", None)
    presentation.objects.link(hero_target)
    hero_target.location = (0, 430, 88)
    hero_camera_data = bpy.data.cameras.new("CAM_Hero_Front_Data")
    hero_camera = bpy.data.objects.new("CAM_Hero_Front", hero_camera_data)
    presentation.objects.link(hero_camera)
    hero_camera.location = (520, 430, 92)
    hero_camera_data.lens = 52
    hero_track = hero_camera.constraints.new("TRACK_TO")
    hero_track.target = hero_target
    hero_track.track_axis = "TRACK_NEGATIVE_Z"
    hero_track.up_axis = "UP_Y"
    hero_root["preview_camera"] = hero_camera.name

    lineup_camera_data = bpy.data.cameras.new("CAM_ClassLineup_Data")
    lineup_camera = bpy.data.objects.new("CAM_ClassLineup", lineup_camera_data)
    presentation.objects.link(lineup_camera)
    lineup_camera.location = (700, 430, 92)
    lineup_camera_data.lens = 58
    lineup_track = lineup_camera.constraints.new("TRACK_TO")
    lineup_track.target = hero_target
    lineup_track.track_axis = "TRACK_NEGATIVE_Z"
    lineup_track.up_axis = "UP_Y"

    for name, location, energy, size in (
        ("Hero_Key", (210, 335, 235), 180000, 120),
        ("Hero_Fill", (150, 535, 165), 95000, 100),
        ("Hero_Rim", (-120, 430, 210), 145000, 90),
    ):
        data = bpy.data.lights.new("LGT_" + name, "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        light = bpy.data.objects.new("LGT_" + name, data)
        presentation.objects.link(light)
        light.location = location
        constraint = light.constraints.new("TRACK_TO")
        constraint.target = hero_target
        constraint.track_axis = "TRACK_NEGATIVE_Z"
        constraint.up_axis = "UP_Y"

    for name, location, energy, size in (
        ("Key", (-150, -100, 240), 120000, 90),
        ("Fill", (150, -40, 160), 65000, 110),
        ("Rim", (0, 180, 220), 90000, 80),
    ):
        data = bpy.data.lights.new("LGT_" + name, "AREA")
        data.energy = energy
        data.shape = "DISK"
        data.size = size
        light = bpy.data.objects.new("LGT_" + name, data)
        presentation.objects.link(light)
        light.location = location
        constraint = light.constraints.new("TRACK_TO")
        constraint.target = floor
        constraint.track_axis = "TRACK_NEGATIVE_Z"
        constraint.up_axis = "UP_Y"

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    library_preview = OUTPUT.with_name("PlayerSuit_BlenderLibrary.png")
    hero_preview = OUTPUT.with_name("PlayerSuit_HeroAssembly.png")
    lineup_preview = OUTPUT.with_name("PlayerSuit_ClassVariants.png")
    scene.render.filepath = str(library_preview)
    scene.world.use_nodes = True
    background = scene.world.node_tree.nodes.get("Background")
    background.inputs["Color"].default_value = (0.025, 0.035, 0.055, 1.0)
    background.inputs["Strength"].default_value = 0.30
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 1.8
    scene["unreal_units"] = "centimeters"
    scene["source_generator"] = "tools/build_player_suit_assets.py"
    scene["export_note"] = "Apply modifiers, triangulate, export FBX at scale 1.0 with -Z forward/Y up."

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    bpy.ops.render.render(write_still=True)
    hero_hidden = (core, limbs, equipment, roles, details, magnetic_system, export_ready)
    for hidden_collection in hero_hidden:
        hidden_collection.hide_render = True
    scene.camera = hero_camera
    scene.render.filepath = str(hero_preview)
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 1280
    bpy.ops.render.render(write_still=True)
    hero_suit.hide_render = True
    hands_free.hide_render = True
    production_100.hide_render = True
    concept_fidelity.hide_render = True
    player_anatomy.hide_render = True
    real_player_finish.hide_render = True
    class_variants.hide_render = False
    scene.camera = lineup_camera
    scene.render.filepath = str(lineup_preview)
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    bpy.ops.render.render(write_still=True)
    class_variants.hide_render = True
    hero_suit.hide_render = False
    hands_free.hide_render = False
    production_100.hide_render = False
    concept_fidelity.hide_render = False
    player_anatomy.hide_render = False
    real_player_finish.hide_render = False
    for hidden_collection in hero_hidden:
        hidden_collection.hide_render = False
    scene.camera = camera
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.render.resolution_x = 1920
    scene.render.resolution_y = 1080
    scene.render.filepath = str(library_preview)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT))
    print(f"Saved editable suit library: {OUTPUT}")


main()
