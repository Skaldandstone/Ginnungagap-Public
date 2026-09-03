"""Measures the existing canonical cryo shell and machinery, plus the CryoPodSystem actor.

The production reference packet for this room (cryo-bay-modular-kit-v1.production.json) names
these as the approved existing assets and gives an "expected range" from
tools/validate_cryo_room_assets.py: roughly 1070-1140 x 640-700 x 390-430 cm. Measuring rather than
trusting that range, the way every other dimension in this project has been measured rather than
assumed since the 300/400 kit mismatch that blocked TRO-239.
"""
import unreal

TARGETS = [
    "/Game/Assets/ShipRooms/Cryo/SM_Room_CryoShell",
    "/Game/Assets/ShipRooms/Cryo/SM_Room_CryoMachinery",
]

for path in TARGETS:
    asset = unreal.load_asset(path)
    if not asset:
        unreal.log_error("SHELL missing {}".format(path))
        continue
    bounds = asset.get_bounds()
    origin, extent = bounds.origin, bounds.box_extent
    unreal.log("SHELL {:<24} size {:7.1f} x {:7.1f} x {:7.1f}   base z {:7.1f}   origin {:.1f},{:.1f},{:.1f}".format(
        asset.get_name(), extent.x*2, extent.y*2, extent.z*2,
        origin.z - extent.z, origin.x, origin.y, origin.z))

pod_class = unreal.load_class(None, "/Script/Ginnungagap.CryoPodSystem")
unreal.log("SHELL CryoPodSystem class loaded: {}".format(bool(pod_class)))
unreal.log("SHELL done")
