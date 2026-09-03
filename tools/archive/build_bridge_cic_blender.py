"""Build the BRG-CIC-01 armored bridge greybox as native Blender assets."""

from pathlib import Path
import math
import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "Art" / "ShipRooms" / "BridgeCIC"
EXPORT = ROOT / "Build" / "Unreal" / "ShipRooms" / "BridgeCIC"
BLEND = ART / "ShipRooms_BridgeCIC.blend"
PREVIEW = ART / "ShipRooms_BridgeCIC_Preview.png"


def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for blocks in (bpy.data.materials, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for block in list(blocks):
            blocks.remove(block)


def collection(name):
    result = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(result)
    return result


def move_to(obj, target):
    for owner in list(obj.users_collection):
        owner.objects.unlink(obj)
    target.objects.link(obj)
    return obj


def material(name, color, metallic=0.0, roughness=0.5, emission=None):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1.0)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1.0)
        bsdf.inputs["Emission Strength"].default_value = 5.0
    return mat


def box(name, location, dimensions, mat, target, bevel=0.04, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        modifier = obj.modifiers.new("EdgeSoftening", "BEVEL")
        modifier.width = bevel
        modifier.segments = 2
    obj.data.materials.append(mat)
    return move_to(obj, target)


def cylinder(name, location, radius, depth, mat, target, rotation=(0, 0, 0), vertices=24):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                       location=location, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    bpy.ops.object.shade_smooth_by_angle()
    return move_to(obj, target)


def empty(name, location, target, display="ARROWS"):
    obj = bpy.data.objects.new(name, None)
    obj.location = location
    obj.empty_display_type = display
    obj.empty_display_size = 0.45
    target.objects.link(obj)
    return obj


def text_label(name, body, location, rotation, size, mat, target):
    curve = bpy.data.curves.new(name + "_Curve", "FONT")
    curve.body = body
    curve.align_x = "CENTER"
    curve.align_y = "CENTER"
    curve.size = size
    curve.extrude = 0.006
    curve.materials.append(mat)
    obj = bpy.data.objects.new(name, curve)
    obj.location = location
    obj.rotation_euler = rotation
    target.objects.link(obj)
    return obj


def console(name, x, y, facing, width, mats, target, screen_count=2):
    root = empty(name + "_ROOT", (x, y, 0), target)
    body = box(name + "_Body", (x, y, 0.68), (width, 0.86, 1.05), mats["structure"], target, 0.08,
               rotation=(0, 0, facing))
    body.parent = root
    direction = Vector((0, -1, 0))
    direction.rotate(Vector((0, 0, 1)).rotation_difference(Vector((0, 0, 1))))
    sy = y - math.cos(facing) * 0.39
    sx = x + math.sin(facing) * 0.39
    for index in range(screen_count):
        offset = (index - (screen_count - 1) / 2) * min(0.56, width / max(screen_count, 1) * 0.72)
        px = sx + math.cos(facing) * offset
        py = sy + math.sin(facing) * offset
        screen = box(name + f"_Screen_{index+1:02d}", (px, py, 1.02),
                     (width / screen_count * 0.70, 0.035, 0.39), mats["screen"], target, 0.015,
                     rotation=(math.radians(14), 0, facing))
        screen.parent = root
    for index, offset in enumerate((-0.25, 0.0, 0.25), 1):
        px = x + math.cos(facing) * offset
        py = y + math.sin(facing) * offset
        control = cylinder(name + f"_Control_{index:02d}", (px, py, 1.22), 0.055, 0.055,
                           mats["amber" if index == 2 else "rubber"], target,
                           rotation=(math.radians(90), 0, facing))
        control.parent = root
    root["station_type"] = name.replace("SM_CIC_", "")
    return root


def chair(name, location, rotation, mats, target):
    x, y, z = location
    root = empty(name + "_ROOT", location, target)
    pedestal = cylinder(name + "_Pedestal", (x, y, z + 0.34), 0.18, 0.62, mats["structure"], target)
    pedestal.parent = root
    seat = box(name + "_Seat", (x, y, z + 0.69), (0.62, 0.58, 0.16), mats["rubber"], target, 0.09,
               rotation=(0, 0, rotation))
    seat.parent = root
    back = box(name + "_Back", (x, y + 0.20 * math.cos(rotation), z + 1.16),
               (0.62, 0.16, 0.90), mats["rubber"], target, 0.10,
               rotation=(math.radians(-7), 0, rotation))
    back.parent = root
    for side in (-1, 1):
        arm = box(name + f"_Arm_{side:+d}", (x + side * 0.38, y, z + 0.90),
                  (0.10, 0.62, 0.10), mats["structure"], target, 0.04,
                  rotation=(0, 0, rotation))
        arm.parent = root
    return root


def build():
    reset()
    ART.mkdir(parents=True, exist_ok=True)
    EXPORT.mkdir(parents=True, exist_ok=True)
    shell = collection("KIT_BridgeShell")
    stations = collection("KIT_CICStations")
    interaction = collection("KIT_InteractionControls")
    gameplay = collection("GAMEPLAY_Anchors")
    presentation = collection("PRESENTATION")

    mats = {
        "hull": material("M_CIC_GraphiteHull", (0.025, 0.035, 0.045), 0.82, 0.27),
        "structure": material("M_CIC_Structure", (0.085, 0.105, 0.12), 0.78, 0.31),
        "deck": material("M_CIC_NonSlipDeck", (0.045, 0.052, 0.058), 0.55, 0.55),
        "rubber": material("M_CIC_Rubber", (0.012, 0.016, 0.019), 0.05, 0.72),
        "amber": material("M_CIC_Amber", (0.65, 0.24, 0.02), 0.35, 0.34, (1.0, 0.28, 0.015)),
        "cyan": material("M_CIC_Cyan", (0.01, 0.18, 0.25), 0.25, 0.28, (0.01, 0.75, 1.0)),
        "red": material("M_CIC_Red", (0.28, 0.008, 0.006), 0.3, 0.35, (1.0, 0.015, 0.008)),
        "violet": material("M_CIC_Violet", (0.12, 0.02, 0.22), 0.2, 0.32, (0.5, 0.04, 1.0)),
        "screen": material("M_CIC_Screen", (0.008, 0.045, 0.060), 0.22, 0.24, (0.01, 0.32, 0.45)),
    }

    # Overall armored room: 18 m wide, 15 m long, 5.4 m high. Forward is +Y.
    box("SM_CIC_Deck", (0, 0, -0.15), (18.0, 15.0, 0.30), mats["deck"], shell, 0.02)
    box("SM_CIC_Ceiling", (0, 0, 5.35), (18.0, 15.0, 0.28), mats["hull"], shell, 0.03)
    for x in (-8.9, 8.9):
        box(f"SM_CIC_Wall_{'Port' if x < 0 else 'Starboard'}", (x, 0, 2.6),
            (0.22, 15.0, 5.2), mats["hull"], shell, 0.03)
    box("SM_CIC_AftWall", (0, -7.4, 2.6), (18.0, 0.22, 5.2), mats["hull"], shell, 0.03)

    # Forward armored viewport wall and three recessed panes.
    box("SM_CIC_ForwardWall", (0, 7.38, 3.75), (18.0, 0.35, 3.2), mats["hull"], shell, 0.05)
    for x in (-5.7, 0, 5.7):
        box(f"SM_CIC_ViewportRecess_{x:+.1f}", (x, 7.16, 3.45), (4.75, 0.10, 2.25),
            mats["violet"], shell, 0.03)
    for x in (-8.4, -3.0, 3.0, 8.4):
        box(f"SM_CIC_ViewportMullion_{x:+.1f}", (x, 6.96, 3.45), (0.34, 0.48, 3.05),
            mats["structure"], shell, 0.04)

    # Structural ribs and descending ceiling beams.
    for y in (-6.0, -3.0, 0.0, 3.0, 6.0):
        for x in (-8.55, 8.55):
            box(f"SM_CIC_Rib_{x:+.1f}_{y:+.1f}", (x, y, 2.65), (0.40, 0.34, 5.1),
                mats["structure"], shell, 0.04)
        box(f"SM_CIC_CeilingBeam_{y:+.1f}", (0, y, 5.02), (17.2, 0.38, 0.42),
            mats["structure"], shell, 0.05)

    # Stepped command pit and central tactical well.
    box("SM_CIC_ForwardDais", (0, 4.65, 0.18), (13.8, 4.1, 0.36), mats["structure"], shell, 0.03)
    box("SM_CIC_AftDais", (0, -4.75, 0.28), (14.2, 3.6, 0.56), mats["structure"], shell, 0.03)
    box("SM_CIC_PortGallery", (-6.95, 0, 0.28), (3.1, 9.2, 0.56), mats["structure"], shell, 0.03)
    box("SM_CIC_StarboardGallery", (6.95, 0, 0.28), (3.1, 9.2, 0.56), mats["structure"], shell, 0.03)
    for x in (-4.65, 4.65):
        box(f"SM_CIC_AisleAmber_{x:+.1f}", (x, 0, 0.02), (0.09, 10.4, 0.025), mats["amber"], shell, 0)

    # Central recessed tactical table with physical crash rail.
    cylinder("SM_CIC_TacticalTable_Base", (0, 0, 0.57), 2.18, 0.72, mats["structure"], stations, vertices=48)
    cylinder("SM_CIC_TacticalTable_Display", (0, 0, 0.96), 1.82, 0.07, mats["screen"], stations, vertices=48)
    cylinder("SM_CIC_TacticalTable_Rail", (0, 0, 1.02), 2.35, 0.08, mats["amber"], stations, vertices=48)
    for angle in range(0, 360, 45):
        a = math.radians(angle)
        cylinder(f"SM_CIC_TablePost_{angle:03d}", (math.cos(a) * 2.28, math.sin(a) * 2.28, 0.62),
                 0.055, 0.74, mats["structure"], stations)

    # Main stations: scanning, analysis, damage control, comms, helm, command.
    station_specs = (
        ("SM_CIC_SensorAcquisition", -5.85, 1.55, math.radians(-90), 2.6, 3),
        ("SM_CIC_ContactAnalysis", -5.85, -1.60, math.radians(-90), 2.6, 3),
        ("SM_CIC_PowerRouting", 5.85, -1.60, math.radians(90), 2.6, 2),
        ("SM_CIC_DamageControl", 5.85, 1.55, math.radians(90), 2.6, 2),
        ("SM_CIC_Helm", -1.65, 4.75, 0, 2.8, 3),
        ("SM_CIC_Navigation", 1.65, 4.75, 0, 2.8, 3),
        ("SM_CIC_Command", 0, -4.78, math.pi, 3.2, 3),
    )
    for name, x, y, facing, width, screens in station_specs:
        console(name, x, y, facing, width, mats, stations, screens)

    # Operator chairs facing their consoles.
    chair_specs = (
        ("SM_CIC_Chair_Sensors", (-4.75, 1.55, 0.15), math.radians(-90)),
        ("SM_CIC_Chair_Analysis", (-4.75, -1.60, 0.15), math.radians(-90)),
        ("SM_CIC_Chair_Power", (4.75, -1.60, 0.15), math.radians(90)),
        ("SM_CIC_Chair_Damage", (4.75, 1.55, 0.15), math.radians(90)),
        ("SM_CIC_Chair_Helm", (-1.65, 3.72, 0.18), 0),
        ("SM_CIC_Chair_Nav", (1.65, 3.72, 0.18), 0),
        ("SM_CIC_Chair_Command", (0, -3.55, 0.28), math.pi),
    )
    for name, loc, rot in chair_specs:
        chair(name, loc, rot, mats, stations)

    # Hero physical controls from the interaction concept.
    cylinder("SM_CIC_SensorTrackball", (-5.27, 1.55, 1.28), 0.18, 0.17, mats["rubber"], interaction)
    cylinder("SM_CIC_AzimuthWheel", (-5.30, 1.98, 1.27), 0.13, 0.08, mats["amber"], interaction,
             rotation=(math.radians(90), 0, 0))
    cylinder("SM_CIC_ElevationWheel", (-5.30, 1.12, 1.27), 0.13, 0.08, mats["amber"], interaction,
             rotation=(math.radians(90), 0, 0))
    box("SM_CIC_HelmCommitGuard", (-0.65, 4.28, 1.30), (0.34, 0.42, 0.34), mats["red"], interaction, 0.05)
    cylinder("SM_CIC_HelmCommitLever", (-0.65, 4.20, 1.48), 0.055, 0.52, mats["amber"], interaction,
             rotation=(math.radians(38), 0, 0))
    for index, x in enumerate((5.28, 5.52, 5.76, 6.00, 6.24), 1):
        box(f"SM_CIC_PowerBreaker_{index:02d}", (x, -1.58, 1.28), (0.13, 0.26, 0.36),
            mats["amber" if index < 4 else "red"], interaction, 0.025)

    # Readable location labels.
    text_label("TXT_CIC", "BRG-CIC-01", (0, -7.10, 3.86), (math.radians(90), 0, 0), 0.46,
               mats["amber"], presentation)
    text_label("TXT_SENSORS", "SENSORS", (-8.73, 1.55, 2.05), (math.radians(90), 0, math.radians(90)),
               0.30, mats["cyan"], presentation)
    text_label("TXT_HELM", "HELM / NAV", (0, 6.84, 1.08), (math.radians(90), 0, 0),
               0.30, mats["amber"], presentation)

    # Gameplay and interaction anchors.
    for name, loc in (
        ("SOCKET_Bulkhead_Aft", (0, -7.5, 0)),
        ("ANCHOR_PlayerEntry", (0, -6.6, 0)),
        ("ANCHOR_Captain", (0, -3.55, 0.55)),
        ("ANCHOR_SensorOperator", (-4.75, 1.55, 0.45)),
        ("ANCHOR_HelmOperator", (-1.65, 3.72, 0.55)),
        ("ANCHOR_NavigationOperator", (1.65, 3.72, 0.55)),
        ("ANCHOR_TacticalTable", (0, 0, 1.05)),
        ("INTERACT_SensorScan", (-5.25, 1.55, 1.28)),
        ("INTERACT_SendToHelm", (-5.25, 1.08, 1.28)),
        ("INTERACT_RoutePower", (5.75, -1.58, 1.28)),
        ("INTERACT_CommitJump", (-0.65, 4.22, 1.45)),
    ):
        empty(name, loc, gameplay)

    # Presentation lighting and hero camera.
    for index, (x, y, color, energy) in enumerate((
        (-5.5, 0.0, (0.18, 0.62, 1.0), 1050),
        (5.5, 0.0, (1.0, 0.34, 0.08), 850),
        (0.0, 4.8, (0.22, 0.62, 1.0), 1200),
        (0.0, -4.8, (1.0, 0.16, 0.05), 650),
    ), 1):
        data = bpy.data.lights.new(f"LGT_CIC_{index:02d}", "AREA")
        data.energy = energy
        data.shape = "RECTANGLE"
        data.size = 3.6
        data.color = color
        light = bpy.data.objects.new(data.name, data)
        light.location = (x, y, 4.72)
        light.rotation_euler = (0, 0, 0)
        presentation.objects.link(light)

    camera_data = bpy.data.cameras.new("CAM_BridgeCIC_Hero")
    camera = bpy.data.objects.new("CAM_BridgeCIC_Hero", camera_data)
    camera.location = (7.85, -6.70, 4.45)
    camera.rotation_euler = ((Vector((0.0, 1.0, 1.35)) - camera.location).to_track_quat("-Z", "Y").to_euler())
    camera_data.lens = 23
    presentation.objects.link(camera)
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene["room_code"] = "BRG-CIC-01"
    scene["module_dimensions_m"] = "18.0 x 15.0 x 5.4"
    scene["design_stage"] = "interaction greybox v1"
    scene["unreal_scale"] = "1 Blender meter = 100 Unreal centimeters"
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(PREVIEW)
    scene.render.film_transparent = False
    scene.world.color = (0.003, 0.005, 0.009)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    bpy.ops.render.render(write_still=True)

    for group, filename in ((shell, "SM_Room_BridgeCIC_Shell.fbx"),
                            (stations, "SM_Room_BridgeCIC_Stations.fbx"),
                            (interaction, "SM_Room_BridgeCIC_Controls.fbx"),
                            (gameplay, "SOCKETS_Room_BridgeCIC.fbx")):
        bpy.ops.object.select_all(action="DESELECT")
        for obj in group.objects:
            obj.select_set(True)
        bpy.ops.export_scene.fbx(filepath=str(EXPORT / filename), use_selection=True,
                                 apply_unit_scale=True, axis_forward="-Y", axis_up="Z",
                                 add_leaf_bones=False, bake_anim=False)
    bpy.ops.object.select_all(action="DESELECT")
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))
    print(f"BRG-CIC-01 built: {BLEND}")


if __name__ == "__main__":
    build()
