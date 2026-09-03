"""Build the reusable CRYO-01 pod entirely with Unreal Geometry Scripting."""
import math
import os
import unreal

DEST = "/Game/Assets/ShipRooms/Cryo/GeneratedV3"
IDENTITY = unreal.Transform()
PRIMITIVE = unreal.GeometryScriptPrimitiveOptions()
NORMALS = unreal.GeometryScriptCalculateNormalsOptions()
CANT_DEGREES = -9.0
CANT_LIFT = 27.0
CONCEPT_REFERENCE = "docs/concept-art/reference/rooms/cryo-pod-realityscan-turnaround-v2.png"
HINGE_ONLY = os.environ.get("CRYO_HINGE_ONLY") == "1"


def xf(x=0, y=0, z=0, pitch=0, yaw=0, roll=0, sx=1, sy=1, sz=1):
    return unreal.Transform(
        location=unreal.Vector(x, y, z),
        rotation=unreal.Rotator(pitch=pitch, yaw=yaw, roll=roll),
        scale=unreal.Vector(sx, sy, sz),
    )


def canted_xf(x=0, y=0, z=0, pitch=0, yaw=0, roll=0, sx=1, sy=1, sz=1):
    radians = math.radians(CANT_DEGREES)
    transformed_y = y * math.cos(radians) - z * math.sin(radians)
    transformed_z = y * math.sin(radians) + z * math.cos(radians) + CANT_LIFT
    return xf(x, transformed_y, transformed_z, pitch, yaw, roll + CANT_DEGREES, sx, sy, sz)


def capsule_solid(width, length, height, base_z=0, canted=False):
    mesh = unreal.DynamicMesh()
    radius = width * 0.5
    straight = max(1.0, length - width)
    center = straight * 0.5
    transform = canted_xf if canted else xf
    mesh.append_box(PRIMITIVE, transform(z=base_z), width, straight, height, 2, 4, 2)
    mesh.append_cylinder(PRIMITIVE, transform(y=center, z=base_z), radius, height, 48, 2, True)
    mesh.append_cylinder(PRIMITIVE, transform(y=-center, z=base_z), radius, height, 48, 2, True)
    mesh.apply_mesh_self_union(unreal.GeometryScriptMeshSelfUnionOptions())
    return mesh


def hollow_base():
    outer = capsule_solid(194.0, 326.0, 92.0, 34.0, canted=True)
    cavity = capsule_solid(152.0, 282.0, 82.0, 72.0, canted=True)
    outer.apply_mesh_boolean(
        IDENTITY, cavity, IDENTITY,
        unreal.GeometryScriptBooleanOperation.SUBTRACT,
        unreal.GeometryScriptMeshBooleanOptions(),
    )
    # Level rounded skid and graduated machinery struts support the baked-in cant.
    # The shell slopes; the object itself remains grounded and unrotated.
    outer.append_mesh(capsule_solid(184.0, 318.0, 10.0, 0.0), IDENTITY)
    for y, width, depth, height in ((-104, 118, 30, 68), (-30, 104, 28, 54), (48, 92, 26, 42), (118, 78, 22, 29)):
        outer.append_box(PRIMITIVE, xf(y=y, z=10), width, depth, height, 3, 2, 3)
    outer.apply_mesh_self_union(unreal.GeometryScriptMeshSelfUnionOptions())
    outer.recompute_normals(NORMALS)
    return outer


def bed_insert():
    # Low mattress and a separate padded bolster ring create a clearly open,
    # concave berth rather than a glassy or convex cap over the shell.
    bed = capsule_solid(124.0, 246.0, 7.0, 70.0, canted=True)
    bolster = capsule_solid(150.0, 276.0, 15.0, 77.0, canted=True)
    bolster_cut = capsule_solid(124.0, 244.0, 24.0, 80.0, canted=True)
    bolster.apply_mesh_boolean(
        IDENTITY, bolster_cut, IDENTITY,
        unreal.GeometryScriptBooleanOperation.SUBTRACT,
        unreal.GeometryScriptMeshBooleanOptions(),
    )
    bed.append_mesh(bolster, IDENTITY)
    # Segmented anatomical cushions remain below the bolster and shell rim.
    for y, width, depth, height in ((-91, 72, 38, 11), (-42, 104, 34, 7), (4, 108, 34, 7), (50, 104, 34, 7), (92, 82, 30, 8)):
        bed.append_box(PRIMITIVE, canted_xf(y=y, z=76), width, depth, height, 4, 3, 2)
    bed.apply_mesh_self_union(unreal.GeometryScriptMeshSelfUnionOptions())
    bed.recompute_normals(NORMALS)
    return bed


def hard_surface_details():
    details = unreal.DynamicMesh()
    # A second rounded rim breaks the silhouette without returning to a rectangular block.
    outer_rim = capsule_solid(200.0, 332.0, 8.0, 116.0, canted=True)
    inner_cut = capsule_solid(170.0, 298.0, 18.0, 111.0, canted=True)
    outer_rim.apply_mesh_boolean(
        IDENTITY, inner_cut, IDENTITY,
        unreal.GeometryScriptBooleanOperation.SUBTRACT,
        unreal.GeometryScriptMeshBooleanOptions(),
    )
    details.append_mesh(outer_rim, IDENTITY)
    # Circular foot-end service coupling. The functional hinge is its own asset.
    revolve = unreal.GeometryScriptRevolveOptions()
    details.append_torus(PRIMITIVE, canted_xf(y=164, z=67, roll=90), revolve, 24, 5, 40, 10)
    # Repeated inset ribs add authored machinery rhythm along both sides.
    for x in (-97, 97):
        for y, height in ((-72, 36), (-12, 44), (52, 42), (108, 34)):
            details.append_box(PRIMITIVE, canted_xf(x=x, y=y, z=48), 5, 31, height, 1, 2, 2)
    details.apply_mesh_self_union(unreal.GeometryScriptMeshSelfUnionOptions())
    details.recompute_normals(NORMALS)
    return details


def hinge_assembly():
    hinge = unreal.DynamicMesh()
    # A centered full-width barrel with symmetric seated pivots. Keeping this
    # independent makes the reusable lid mechanism easy to refine or animate.
    # UE's tessellated cylinder bounds are wider than the nominal height after
    # this rotated transform; these calibrated values finish inside the shell.
    hinge.append_cylinder(PRIMITIVE, canted_xf(y=-145, z=116, pitch=90), 15, 126, 40, 3, True)
    for x in (-63, 63):
        hinge.append_cylinder(PRIMITIVE, canted_xf(x=x, y=-145, z=116, pitch=90), 22, 10, 32, 2, True)
    hinge.apply_mesh_self_union(unreal.GeometryScriptMeshSelfUnionOptions())
    hinge.recompute_normals(NORMALS)
    return hinge


def restraints():
    straps = unreal.DynamicMesh()
    for y in (-28, 48):
        straps.append_box(PRIMITIVE, canted_xf(y=y, z=86), 126, 12, 4, 8, 2, 1)
        straps.append_box(PRIMITIVE, canted_xf(x=-62, y=y, z=87), 8, 17, 7, 2, 2, 2)
        straps.append_box(PRIMITIVE, canted_xf(x=62, y=y, z=87), 8, 17, 7, 2, 2, 2)
    straps.apply_mesh_self_union(unreal.GeometryScriptMeshSelfUnionOptions())
    straps.recompute_normals(NORMALS)
    return straps


def status_lights():
    lights = unreal.DynamicMesh()
    for x in (-52, 52):
        lights.append_box(PRIMITIVE, canted_xf(x=x, y=164, z=74), 30, 5, 9, 3, 1, 2)
    lights.recompute_normals(NORMALS)
    return lights


def lid_frame():
    frame = unreal.DynamicMesh()
    revolve = unreal.GeometryScriptRevolveOptions()
    # Torus is generated in XY, rotated into XZ, then stretched into the concept oval.
    frame.append_torus(PRIMITIVE, xf(z=154, roll=90, sx=.92, sy=1.52, sz=1.0), revolve, 92, 8, 64, 14)
    frame.append_torus(PRIMITIVE, xf(y=2, z=154, roll=90, sx=.84, sy=1.40, sz=1.0), revolve, 82, 4.5, 64, 12)
    frame.recompute_normals(NORMALS)
    return frame


def lid_glass():
    glass = unreal.DynamicMesh()
    # The whole lens sits on the outward side of the frame: a centered bubble
    # canopy on the lid, never a second dome over the recessed mattress.
    glass.append_sphere_lat_long(PRIMITIVE, xf(y=17, z=154, sx=.95, sy=.20, sz=1.68), 82, 64, 32)
    glass.recompute_normals(NORMALS)
    return glass


def create_asset(name, mesh, material_path, slot_name):
    path = f"{DEST}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        if not unreal.EditorAssetLibrary.delete_asset(path):
            raise RuntimeError(f"Could not replace generated asset {path}")
    options = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    asset, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(mesh, path, options)
    if not asset or outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError(f"Geometry Scripting failed to create {path}: {outcome}")
    material = unreal.EditorAssetLibrary.load_asset(material_path)
    if material:
        slot = unreal.StaticMaterial()
        slot.set_editor_property("material_interface", material)
        slot.set_editor_property("material_slot_name", unreal.Name(slot_name))
        asset.set_editor_property("static_materials", [slot])
    asset.set_editor_property("light_map_resolution", 128)
    asset.set_editor_property("light_map_coordinate_index", 0)
    body_setup = asset.get_editor_property("body_setup")
    if body_setup:
        body_setup.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "CryoPod.Source", "Unreal Geometry Scripting")
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "CryoPod.Generator", "tools/build_cryo_pod_geometry_script.py")
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "CryoPod.ConceptReference", CONCEPT_REFERENCE)
    if not unreal.EditorAssetLibrary.save_loaded_asset(asset):
        raise RuntimeError(f"Could not save generated asset {path}; close any Unreal Editor session holding it open")
    size = asset.get_bounds().box_extent * 2.0
    unreal.log(f"CRYO-GEOM PASS {name}: {size.x:.1f} x {size.y:.1f} x {size.z:.1f} cm")
    return asset


unreal.EditorAssetLibrary.make_directory(DEST)
if not HINGE_ONLY:
    create_asset("SM_CryoPod_GS_Base", hollow_base(), "/Game/Assets/ShipRooms/Cryo/M_Cryo_OiledBlackHull", "Hull")
    create_asset("SM_CryoPod_GS_Bed", bed_insert(), "/Game/Assets/ShipRooms/Cryo/M_Cryo_RestraintCushion", "Bed")
    create_asset("SM_CryoPod_GS_Details", hard_surface_details(), "/Game/Assets/ShipRooms/Cryo/M_Cryo_WornGunmetal", "Details")
create_asset("SM_CryoPod_GS_HingeFinal", hinge_assembly(), "/Game/Assets/ShipRooms/Cryo/M_Cryo_WornGunmetal", "Hinge")
if not HINGE_ONLY:
    create_asset("SM_CryoPod_GS_Restraints", restraints(), "/Game/Assets/ShipRooms/Cryo/M_Cryo_WetCable", "Restraints")
    create_asset("SM_CryoPod_GS_StatusLights", status_lights(), "/Game/Assets/ShipRooms/Cryo/M_Cryo_AmberPractical", "StatusLights")
    create_asset("SM_CryoPod_GS_LidFrame", lid_frame(), "/Game/Assets/ShipRooms/Cryo/M_Cryo_WornGunmetal", "Frame")
    create_asset("SM_CryoPod_GS_LidGlass", lid_glass(), "/Game/Assets/ShipRooms/Cryo/M_Cryo_CrackedFrostGlass", "Glass")
unreal.log("CRYO-GEOM PASS: Unreal-native reusable pod package complete")
