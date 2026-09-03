"""Engine-side QA for the imported CRYO-01 room assets."""
import unreal

EXPECTED = {
    "/Game/Assets/ShipRooms/Cryo/SM_Room_CryoShell": ((1070.0, 1140.0), (640.0, 700.0), (390.0, 430.0), 4, 1),
    "/Game/Assets/ShipRooms/Cryo/SM_Room_CryoMachinery": ((1000.0, 1080.0), (580.0, 620.0), (330.0, 380.0), 7, 1),
    "/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_Base": ((190.0, 198.0), (332.0, 340.0), (167.0, 175.0), 1, 0),
    "/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_Bed": ((146.0, 154.0), (270.0, 280.0), (58.0, 74.0), 1, 0),
    "/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_Details": ((196.0, 204.0), (329.0, 337.0), (133.0, 139.0), 1, 0),
    "/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_HingeFinal": ((188.0, 195.0), (52.0, 60.0), (40.0, 48.0), 1, 0),
    "/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_Restraints": ((128.0, 136.0), (89.0, 97.0), (18.0, 26.0), 1, 0),
    "/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_StatusLights": ((130.0, 138.0), (3.0, 9.0), (6.0, 13.0), 1, 0),
    "/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_LidFrame": ((180.0, 188.0), (10.0, 20.0), (300.0, 308.0), 1, 0),
    "/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_LidGlass": ((152.0, 160.0), (30.0, 36.0), (272.0, 280.0), 1, 0),
}


def validate_mesh(path, constraints):
    name = path.rsplit("/", 1)[-1]
    mesh = unreal.EditorAssetLibrary.load_asset(path)
    if not mesh:
        raise RuntimeError(f"Missing CRYO-01 asset: {path}")
    bounds = mesh.get_bounds()
    size = bounds.box_extent * 2.0
    ranges = constraints[:3]
    values = (size.x, size.y, size.z)
    for axis, value, allowed in zip("XYZ", values, ranges):
        if not allowed[0] <= value <= allowed[1]:
            raise RuntimeError(f"{name} {axis} size {value:.1f} cm outside {allowed}")
    material_count = len(mesh.get_editor_property("static_materials"))
    if material_count < constraints[3]:
        raise RuntimeError(f"{name} has only {material_count} material slots")
    if mesh.get_editor_property("light_map_coordinate_index") != constraints[4]:
        raise RuntimeError(f"{name} has the wrong lightmap UV channel")
    body_setup = mesh.get_editor_property("body_setup")
    if not body_setup or body_setup.get_editor_property("collision_trace_flag") != unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE:
        raise RuntimeError(f"{name} is not using exact visible-mesh collision")
    unreal.log(f"CRYO-QA PASS {name}: {size.x:.1f} x {size.y:.1f} x {size.z:.1f} cm, {material_count} materials")


errors = []
for asset_path, expected in EXPECTED.items():
    try:
        validate_mesh(asset_path, expected)
    except RuntimeError as error:
        errors.append(str(error))
        unreal.log_error(f"CRYO-QA FAIL: {error}")
if errors:
    raise RuntimeError("CRYO-QA found mismatches:\n" + "\n".join(errors))
unreal.log("CRYO-QA PASS: room shell and Unreal-native reusable pod package match the concept envelope")
