"""Measures the kit meshes the cryo hero map will be built from.

Guessing module sizes is what produced the 335-versus-360 grid mismatch that still blocks TRO-239.
These are cheap to measure and expensive to assume.
"""
import unreal

WANTED = [
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/FLOOR/SM_FLOOR_05",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/FLOOR/SM_FLOOR_08",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/WALL/SM_WALL_07",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/WALL/SM_WALL_12",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/CEILING/SM_CEILING_07",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/LAMP/SM_LAMP_04",
    "/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_Base",
]

for path in WANTED:
    asset = unreal.load_asset(path)
    if not asset:
        unreal.log_warning("KIT MISSING {}".format(path))
        continue
    # BoxSphereBounds exposes origin + box_extent, not a box with min/max.
    bounds = asset.get_bounds()
    origin, extent = bounds.origin, bounds.box_extent
    unreal.log("KIT {:<26} size {:7.1f} x {:7.1f} x {:7.1f}   base z {:7.1f}   origin z {:6.1f}".format(
        asset.get_name(), extent.x * 2.0, extent.y * 2.0, extent.z * 2.0,
        origin.z - extent.z, origin.z))
unreal.log("KIT done")
