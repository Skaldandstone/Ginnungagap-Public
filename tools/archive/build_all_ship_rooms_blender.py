"""Generate the complete modular ship-room Blender library and Unreal FBX exports."""

from pathlib import Path
import math
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "Art" / "ShipRooms"
EXPORT = ROOT / "Build" / "Unreal" / "ShipRooms"

ROOMS = {
    "Companionway": (10.0, 4.8, "CMP-01", "transit"),
    "Bridge": (12.0, 8.0, "BRG-01", "command"),
    "Sensors": (10.0, 7.2, "SNS-01", "sensors"),
    "Medical": (10.0, 7.2, "MED-01", "medical"),
    "Crew": (12.0, 7.2, "CRW-01", "crew"),
    "Cargo": (14.0, 9.6, "CGO-01", "cargo"),
    "DamageControl": (10.0, 7.2, "DCR-01", "damage"),
    "Engineering": (14.0, 9.0, "ENG-01", "engineering"),
    "ReactorControl": (12.0, 8.4, "RCT-01", "reactor"),
    "EscapeBay": (12.0, 8.4, "ESC-01", "escape"),
    "Armory": (10.0, 7.2, "ARM-01", "armory"),
}


def reset():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for blocks in (bpy.data.meshes, bpy.data.materials, bpy.data.curves,
                   bpy.data.cameras, bpy.data.lights):
        for block in list(blocks):
            if block.users == 0:
                blocks.remove(block)


def mat(name, color, metallic=.55, rough=.38, glow=None):
    result = bpy.data.materials.new(name)
    result.diffuse_color = (*color, 1)
    result.use_nodes = True
    shader = result.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Metallic"].default_value = metallic
    shader.inputs["Roughness"].default_value = rough
    if glow:
        shader.inputs["Emission Color"].default_value = (*glow, 1)
        shader.inputs["Emission Strength"].default_value = 5
    return result


def cube(name, loc, dims, material, bevel=.04):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("ProductionBevel", "BEVEL")
        mod.width = bevel
        mod.segments = 2
    return obj


def cyl(name, loc, radius, depth, material, rotation=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=radius, depth=depth,
                                       location=loc, rotation=rotation)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    bpy.ops.object.shade_smooth_by_angle()
    return obj


def anchor(name, loc):
    obj = bpy.data.objects.new(name, None)
    obj.location = loc
    obj.empty_display_type = "ARROWS"
    obj.empty_display_size = .3
    bpy.context.collection.objects.link(obj)
    return obj


def console(name, loc, materials, width=1.3, rotation=0):
    body = cube(name, loc, (width, .65, 1.15), materials["structure"], .08)
    body.rotation_euler.z = rotation
    screen_loc = (loc[0], loc[1] - .35 * math.cos(rotation), loc[2] + .30)
    screen = cube(name + "_Screen", screen_loc, (width * .72, .06, .38), materials["screen"], .02)
    screen.rotation_euler.z = rotation
    return body


def shell(length, width, materials):
    cube("SM_Room_Floor", (0, 0, -.12), (length, width, .24), materials["deck"], .02)
    cube("SM_Room_Ceiling", (0, 0, 3.8), (length, width, .18), materials["hull"], .02)
    for y in (-width / 2, width / 2):
        cube("SM_Room_Wall_Port" if y < 0 else "SM_Room_Wall_Starboard",
             (0, y, 1.85), (length, .18, 3.7), materials["hull"], .02)
    for x in (-length / 2, length / 2):
        for y in (-width * .34, width * .34):
            cube(f"SM_BulkheadFrame_{x}_{y}", (x, y, 1.85), (.20, width * .30, 3.7),
                 materials["structure"], .03)
    for x in [(-length / 2 + 1.0) + i * 2.0 for i in range(max(1, int((length - 2) / 2) + 1))]:
        for y in (-width / 2 + .16, width / 2 - .16):
            cube(f"SM_StructuralRib_{x:+.1f}_{y:+.1f}", (x, y, 1.9),
                 (.16, .25, 3.8), materials["structure"], .02)
    for y in (-1.25, 1.25):
        cube(f"SM_HazardLane_{y:+.2f}", (0, y, .015), (length - 1, .07, .025),
             materials["accent"], 0)


def props(kind, length, width, m):
    side = width / 2 - .72
    if kind == "transit":
        for x in (-3, 0, 3):
            cube(f"SM_CrashSeat_{x:+.0f}", (x, side, .55), (.65, .55, 1.1), m["structure"], .08)
        console("SM_TransitTerminal", (2.8, -side, .6), m, 1.0, math.pi)
    elif kind == "command":
        console("SM_HelmConsole", (3.8, 0, .62), m, 2.1)
        for x, y in ((1.4, -2.2), (1.4, 2.2), (-1.2, -2.5), (-1.2, 2.5)):
            console(f"SM_CommandStation_{x}_{y}", (x, y, .58), m, 1.35, 0 if y < 0 else math.pi)
        cyl("SM_HolographicTable", (-2.8, 0, .72), 1.05, 1.44, m["structure"])
        cyl("SM_HolographicDisplay", (-2.8, 0, 1.60), .72, .04, m["screen"])
    elif kind == "sensors":
        for x in (-3, 0, 3):
            console(f"SM_SensorConsole_{x:+.0f}", (x, -side, .62), m, 1.45, math.pi)
        for x in (-2.2, 2.2):
            cyl(f"SM_SensorProcessor_{x:+.1f}", (x, side, 1.2), .38, 2.4, m["structure"])
            cyl(f"SM_SensorGlow_{x:+.1f}", (x, side - .41, 1.2), .18, .06, m["screen"], (math.pi / 2, 0, 0))
    elif kind == "medical":
        for x in (-2.8, 0, 2.8):
            cube(f"SM_MedicalBed_{x:+.1f}", (x, side - .3, .48), (1.95, .78, .55), m["white"], .12)
        console("SM_DiagnosticStation", (2.6, -side, .62), m, 1.35, math.pi)
        cube("SM_SupplyCabinet", (-2.8, -side, 1.05), (1.2, .55, 2.1), m["structure"], .06)
    elif kind == "crew":
        for x in (-4, -1.35, 1.35, 4):
            for z in (.58, 1.68):
                cube(f"SM_Bunk_{x}_{z}", (x, side, z), (2.1, .72, .55), m["white"], .10)
        cube("SM_Galley", (3.8, -side, 1.0), (2.0, .68, 2.0), m["structure"], .06)
        cube("SM_CrewTable", (0, 0, .55), (2.3, 1.1, .18), m["white"], .08)
    elif kind == "cargo":
        for x, y in ((-4, -2.6), (-4, 2.6), (0, -2.6), (0, 2.6), (4, -2.6), (4, 2.6)):
            cube(f"SM_CargoStack_{x}_{y}", (x, y, .75), (2.0, 1.35, 1.5), m["accent"], .08)
        cube("SM_HandLoader", (4.8, 0, .45), (1.8, 1.0, .9), m["structure"], .10)
    elif kind == "damage":
        cube("SM_DamageWorkbench", (-2.5, side, .85), (2.4, .7, 1.7), m["structure"], .06)
        for x in (0, 2.2):
            cube(f"SM_RepairLocker_{x}", (x, side, 1.0), (1.25, .62, 2.0), m["accent"], .06)
        cyl("SM_FireSuppressionCart", (2.7, -side, .65), .38, 1.3, m["white"])
        console("SM_DamageConsole", (-2.5, -side, .62), m, 1.5, math.pi)
    elif kind == "engineering":
        for x in (-4.2, 0, 4.2):
            cyl(f"SM_CoolantPump_{x:+.1f}", (x, side, 1.0), .58, 2.0, m["structure"])
        for x in (-3, 0, 3):
            cube(f"SM_BreakerBank_{x:+.0f}", (x, -side, 1.2), (1.65, .65, 2.4), m["structure"], .05)
        console("SM_EngineeringControl", (0, 0, .62), m, 1.8)
    elif kind == "reactor":
        for x in (-3.2, 0, 3.2):
            cyl(f"SM_ReactorCoil_{x:+.1f}", (x, side, 1.25), .62, 2.5, m["structure"])
            cyl(f"SM_ReactorCore_{x:+.1f}", (x, side - .15, 1.25), .30, 2.0, m["screen"])
        for x in (-2.5, 0, 2.5):
            console(f"SM_ReactorConsole_{x:+.1f}", (x, -side, .62), m, 1.3, math.pi)
    elif kind == "escape":
        for x in (-3.8, 0, 3.8):
            for y in (-side, side):
                cube(f"SM_EscapePod_{x}_{y}", (x, y, .82), (2.2, 1.1, 1.65), m["white"], .22)
                cube(f"SM_EscapeStatus_{x}_{y}", (x, y - math.copysign(.58, y), 1.0),
                     (.55, .05, .42), m["screen"], .02)
        console("SM_MusterConsole", (0, 0, .62), m, 1.5)
    elif kind == "armory":
        for x in (-3.2, 0, 3.2):
            cube(f"SM_WeaponLocker_{x:+.1f}", (x, side, 1.15), (1.7, .65, 2.3), m["structure"], .06)
            cube(f"SM_ArmorLocker_{x:+.1f}", (x, -side, 1.15), (1.7, .65, 2.3), m["accent"], .06)
        console("SM_ArmoryAccess", (0, 0, .62), m, 1.25)


def build_room(room_name, spec):
    reset()
    length, width, code, kind = spec
    materials = {
        "hull": mat("M_Room_GraphiteHull", (.035, .05, .065), .78, .3),
        "structure": mat("M_Room_Structure", (.10, .13, .15), .82, .25),
        "deck": mat("M_Room_NonSlipDeck", (.05, .06, .07), .58, .52),
        "white": mat("M_Room_ServiceWhite", (.42, .48, .50), .48, .34),
        "accent": mat("M_Room_HazardAmber", (.58, .22, .025), .42, .34),
        "screen": mat("M_Room_CyanScreen", (.01, .10, .13), .25, .22, (.02, .75, 1.0)),
    }
    shell(length, width, materials)
    props(kind, length, width, materials)
    anchor("SOCKET_Bulkhead_Forward", (length / 2, 0, 0))
    anchor("SOCKET_Bulkhead_Aft", (-length / 2, 0, 0))
    anchor("ANCHOR_System", (0, 0, 0))
    anchor("ANCHOR_Loot", (length * .32, width * .30, 0))
    anchor("ANCHOR_Maintenance", (-length * .32, -width * .30, 0))
    anchor("ANCHOR_AITraversal", (0, 0, 0))

    for x in (-length * .28, 0, length * .28):
        data = bpy.data.lights.new(f"LGT_{room_name}_{x:+.1f}", "AREA")
        data.energy = 650
        data.color = (.55, .78, 1.0)
        data.shape = "RECTANGLE"
        data.size = 2.0
        obj = bpy.data.objects.new(data.name, data)
        obj.location = (x, 0, 3.5)
        bpy.context.collection.objects.link(obj)

    camera_data = bpy.data.cameras.new("CAM_RoomPreview")
    camera = bpy.data.objects.new("CAM_RoomPreview", camera_data)
    camera.location = (-length / 2 + .42, 0, 1.70)
    camera.rotation_euler = (Vector((length * .12, 0, 1.05)) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera_data.lens = 22
    bpy.context.collection.objects.link(camera)
    scene = bpy.context.scene
    scene.camera = camera
    scene["room_code"] = code
    scene["room_archetype"] = room_name
    scene["module_dimensions_m"] = f"{length} x {width} x 3.8"
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 960
    scene.render.resolution_y = 540
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.world.color = (.006, .009, .013)
    room_dir = EXPORT / room_name
    room_dir.mkdir(parents=True, exist_ok=True)
    scene.render.filepath = str(ART / f"Room_{room_name}_Preview.png")
    blend_path = ART / f"Room_{room_name}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))
    bpy.ops.render.render(write_still=True)
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.export_scene.fbx(filepath=str(room_dir / f"SM_Room_{room_name}.fbx"), use_selection=True,
                             apply_unit_scale=True, axis_forward="-Y", axis_up="Z",
                             add_leaf_bones=False, bake_anim=False)
    print(f"BUILT {code}: {blend_path}")


def main():
    ART.mkdir(parents=True, exist_ok=True)
    EXPORT.mkdir(parents=True, exist_ok=True)
    for room_name, spec in ROOMS.items():
        build_room(room_name, spec)
    print(f"Complete modular library: {len(ROOMS)} rooms plus CRYO-01")


if __name__ == "__main__":
    main()
