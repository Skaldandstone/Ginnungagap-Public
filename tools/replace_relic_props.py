"""Replaces the demo map's project-made placeholder props with Fab meshes ("relics", as James
called them): every static mesh component drawing one of the generated production props is
re-pointed at a Fab mesh, scaled per axis so it fills the original's footprint, with the Fab
mesh's own materials. Gameplay actors keep their class and transform; only what they draw
changes, and the footprint is kept so interaction focus traces still land on them.

    --survey   prints the world-space extents of each relic mesh and each candidate, no changes
    (default)  applies the mapping and saves the map

    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/replace_relic_props.py [--survey] -NullRHI
"""
import sys
import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
SURVEY = any("survey" in a for a in sys.argv)
PROD = "/Game/Assets/Ships/Production/Meshes"
MECH = "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM"
ENGI = "/Game/ModSci_Engineer/Meshes"
ENGP = "/Game/ModSci_EngiProps/Meshes"

# relic mesh -> (fab mesh, extra rotation (roll, pitch, yaw) on the component, fit mode)
# fit "axis": stretch to the relic's bounds on each axis (pipes); "uniform": scale by the largest
# axis; "none": keep the Fab mesh at authored size. All are placed with their bottom on the
# relic's bottom and their XY centre on the relic's, since props stand where they stood.
MAPPING = {
    f"{PROD}/SM_Prop_PipeStraight":   (f"{MECH}/CABLE_PIPE/SM_PIPE_01", (0.0, 0.0, 0.0), "axis"),
    f"{PROD}/SM_Prop_LightFixture":   (f"{ENGI}/SM_Light_A", (0.0, 0.0, 0.0), "uniform"),
    f"{PROD}/SM_Prop_WallTerminal":   (f"{MECH}/PROP/COMPUTER/SM_COMPUTER_02", (0.0, 0.0, 0.0), "none"),
    f"{PROD}/SM_Prop_PowerJunction":  (f"{MECH}/PROP/MACHINE/SM_ELECTRIC_BOX_01_OPEN", (0.0, 0.0, 0.0), "uniform"),
    f"{PROD}/SM_Prop_Locker":         (f"{MECH}/SRTUCTURE/DOOR_FRAME/SM_DOOR_FRAME_03_LOCKER_LEFT", (0.0, 0.0, 0.0), "uniform"),
    f"{PROD}/SM_Prop_CrashSeat":      ("/Game/SciFiWorld/Meshes/SM_Chair08", (0.0, 0.0, 0.0), "uniform"),
    "/Game/Assets/Models/Pickups/SM_Pickup_OxygenCanister": (f"{ENGP}/SM_OxygenTank_B", (90.0, 0.0, 0.0), "uniform"),
    "/Game/Assets/Models/ShipSystems/SM_System_EscapePod":  ("/Game/SciFiWorld/Meshes/SM_LabCapsule05_Capsule", (0.0, 0.0, 0.0), "uniform"),
    # Not the Ice Station crate: that pack is missing its trim texture here and renders white.
    f"{PROD}/SM_Prop_CargoCrate":     ("/Game/kb3d_missiontominerva/StaticMeshes/SM_KB3D_MTM_PropCrate_A", (0.0, 0.0, 0.0), "uniform"),
    # The earlier pass had already put the Ice Station crate on every cargo crate; carry those over.
    "/Game/Ice_Station/Meshes/Crates/SM_crate_01": ("/Game/kb3d_missiontominerva/StaticMeshes/SM_KB3D_MTM_PropCrate_A", (0.0, 0.0, 0.0), "uniform"),
}
TAG = "RelicReplaced"


def extent(mesh):
    b = mesh.get_bounding_box()
    return unreal.Vector(b.max.x - b.min.x, b.max.y - b.min.y, b.max.z - b.min.z), b


def fmt(v):
    return f"({v.x:.0f}, {v.y:.0f}, {v.z:.0f})"


les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert les.load_level(MAP)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()

if SURVEY:
    for relic, (fab, rot, fit) in MAPPING.items():
        r = unreal.load_asset(relic); f = unreal.load_asset(fab)
        print(f"RELIC {relic.split('/')[-1]}: {fmt(extent(r)[0]) if r else 'missing'}  ->  {fab.split('/')[-1]}: {fmt(extent(f)[0]) if f else 'MISSING'}")
    raise SystemExit(0)

fab_meshes = {}
for relic, (fab, rot, fit) in MAPPING.items():
    fab_meshes[relic] = unreal.load_asset(fab)
    assert fab_meshes[relic], f"missing fab mesh {fab}"

replaced = 0
per_relic = {}
for actor in actors:
    for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = comp.static_mesh
        if not mesh:
            continue
        path = mesh.get_path_name().split(".")[0]
        if path not in MAPPING:
            continue
        fab_path, (roll, pitch, yaw), fit = MAPPING[path]
        fab = fab_meshes[path]
        r_ext, r_box = extent(mesh)
        f_ext, f_box = extent(fab)
        old_scale = comp.get_editor_property("relative_scale3d")
        # World footprint of the relic as placed: its extents times the component scale.
        target = unreal.Vector(r_ext.x * abs(old_scale.x), r_ext.y * abs(old_scale.y), r_ext.z * abs(old_scale.z))
        # The Fab mesh's extents after the extra rotation (axis-swaps only; 90-degree turns).
        rx, ry, rz = f_ext.x, f_ext.y, f_ext.z
        if abs(roll) == 90.0: ry, rz = rz, ry
        if abs(pitch) == 90.0: rx, rz = rz, rx
        if abs(yaw) == 90.0: rx, ry = ry, rx
        if fit == "axis":
            scale = unreal.Vector(*(max(0.2, min(4.0, (t / f) if f > 1e-3 else 1.0)) for t, f in ((target.x, rx), (target.y, ry), (target.z, rz))))
        elif fit == "uniform":
            ratio = max(0.25, min(3.0, max(target.x, target.y, target.z) / max(rx, ry, rz, 1e-3)))
            scale = unreal.Vector(ratio, ratio, ratio)
        else:
            scale = unreal.Vector(1.0, 1.0, 1.0)
        # Where the relic's bounds sat in component space (scaled): keep the XY centre and the
        # bottom, so the Fab mesh stands where the relic stood.
        r_cx = (r_box.min.x + r_box.max.x) * 0.5 * old_scale.x
        r_cy = (r_box.min.y + r_box.max.y) * 0.5 * old_scale.y
        r_bottom = min(r_box.min.z * old_scale.z, r_box.max.z * old_scale.z)
        comp.set_static_mesh(fab)
        for slot in range(comp.get_num_materials()):
            comp.set_material(slot, None)
        # The rotation swaps axes for the bounds; recompute the Fab bounds in the rotated frame.
        fb_min = unreal.Vector(f_box.min.x, f_box.min.y, f_box.min.z); fb_max = unreal.Vector(f_box.max.x, f_box.max.y, f_box.max.z)
        if abs(roll) == 90.0:
            fb_min, fb_max = unreal.Vector(fb_min.x, -fb_max.z, fb_min.y), unreal.Vector(fb_max.x, -fb_min.z, fb_max.y)
        f_cx = (fb_min.x + fb_max.x) * 0.5 * scale.x
        f_cy = (fb_min.y + fb_max.y) * 0.5 * scale.y
        f_bottom = fb_min.z * scale.z
        comp.set_editor_property("relative_scale3d", scale)
        rot = comp.get_editor_property("relative_rotation")
        if roll or pitch or yaw:
            comp.set_editor_property("relative_rotation", unreal.Rotator(rot.roll + roll, rot.pitch + pitch, rot.yaw + yaw))
        loc = comp.get_editor_property("relative_location")
        comp.set_editor_property("relative_location", unreal.Vector(loc.x + (r_cx - f_cx), loc.y + (r_cy - f_cy), loc.z + (r_bottom - f_bottom)))
        tags = list(actor.tags)
        if unreal.Name(TAG) not in tags:
            tags.append(unreal.Name(TAG)); actor.set_editor_property("tags", tags)
        replaced += 1
        per_relic[path.split("/")[-1]] = per_relic.get(path.split("/")[-1], 0) + 1

saved = les.save_current_level()
print(f"RELIC replaced {replaced} components; saved={saved}")
for name, n in sorted(per_relic.items()):
    print(f"RELIC   {n:4d} {name}")
