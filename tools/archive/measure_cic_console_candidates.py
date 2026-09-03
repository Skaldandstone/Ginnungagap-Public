"""Measure candidate CIC console meshes before anything is placed on them.

`upgrade_demo_station_meshes.py` left CIC_SensorArray and CIC_JumpConsole on their project
blockouts, and said why: the kit meshes whose bounds had actually been measured were used up, and
picking an unmeasured one is how a wall panel ended up standing free in the middle of a room. That
has already happened twice in this map -- SM_WALL_08_DISPLAY used as a console, and SM_LAMP_04
rotated across a corridor it was 250cm too long for.

James asked whether there are free Fab assets that would make the CIC read better. There are, and
they did not need downloading: the project already owns several packs with purpose-built consoles
and holographic tables, which the kit does not have at all. This measures them so the choice is made
on numbers rather than on a filename.

Reports bounds, pivot offset, and material slot count for each candidate. Pivot offset matters as
much as size here: a mesh authored around its centre and a mesh authored around its base need
different Z placement, and a console sunk half into the deck looks like a bug rather than a prop.

Writes nothing. Reading a report and then deciding is the point.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/measure_cic_console_candidates.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

# Candidates, grouped by the pack they came with. Everything here is already in Content/, so it is
# free in the sense that matters: no download, no new licence to read.
CANDIDATES = [
    # Purpose-built consoles. The kit has generic computer terminals; these are consoles.
    "/Game/Scifi_Hideout/Meshes/Console/SM_console",
    "/Game/Scifi_Hideout/Meshes/Small_console/SM_small_console",

    # Holographic tables. A CIC's centrepiece is the thing everyone stands around, and neither the
    # kit nor the project blockouts have anything of the kind.
    "/Game/Ice_Station/Meshes/Hologram/SM_planet_hologram",
    "/Game/Ice_Station/Meshes/Hologram/SM_hologram_support",
    "/Game/kb3d_missiontominerva/StaticMeshes/SM_KB3D_MTM_PropHologramMap_A",

    # Seating. A command centre with no chairs reads as a corridor with consoles in it.
    "/Game/Ice_Station/Meshes/Chair/SM_chair",
    "/Game/kb3d_missiontominerva/StaticMeshes/SM_KB3D_MTM_PropChair_A",
]

# What the CIC can actually accept, measured from the room rather than guessed. Stations stand on
# the deck against the inner wall face; anything over this is furniture the room cannot hold.
MAX_FOOTPRINT = 300.0
MAX_HEIGHT = 260.0


def describe(path):
    if not unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.log_error("MISSING {}".format(path))
        return

    mesh = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        unreal.log_error("NOT A STATIC MESH {} ({})".format(path, type(mesh).__name__))
        return

    bounds = mesh.get_bounds()
    extent = bounds.box_extent
    origin = bounds.origin
    size = (extent.x * 2.0, extent.y * 2.0, extent.z * 2.0)

    # A mesh authored on its base has origin.z ~= extent.z; one authored on its centre has ~0.
    # Anything between the two needs its placement Z worked out rather than assumed.
    pivot = "base" if abs(origin.z - extent.z) < 5.0 else ("centre" if abs(origin.z) < 5.0 else "offset")

    fits = size[0] <= MAX_FOOTPRINT and size[1] <= MAX_FOOTPRINT and size[2] <= MAX_HEIGHT

    unreal.log(
        "CANDIDATE {name}\n"
        "    size      {sx:.0f} x {sy:.0f} x {sz:.0f}\n"
        "    origin    ({ox:.1f}, {oy:.1f}, {oz:.1f})  pivot: {pivot}\n"
        "    materials {mats}\n"
        "    verdict   {verdict}".format(
            name=path.rsplit("/", 1)[-1],
            sx=size[0], sy=size[1], sz=size[2],
            ox=origin.x, oy=origin.y, oz=origin.z,
            pivot=pivot,
            mats=len(mesh.static_materials),
            verdict="fits the CIC as-is" if fits else "too large at scale 1.0 -- needs scaling or a different role",
        ))


def main():
    unreal.log("Measuring {} CIC console candidates".format(len(CANDIDATES)))
    unreal.log("Room allows footprint <= {:.0f} and height <= {:.0f}".format(MAX_FOOTPRINT, MAX_HEIGHT))
    for path in CANDIDATES:
        describe(path)


if __name__ == "__main__":
    main()
