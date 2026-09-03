"""Inventory and measure an unfamiliar asset pack, before anything is placed from it.

Written for the Sci-Fi Creatures Research Lab pack, whose blurb promises "cryogenic capsules for
storing creatures, samples, or humanoid characters in stasis" -- which would make it a stand-in for
Ginnungagap's cryo pods, currently four generations of geometry-scripted blockout.

Generalised because this keeps happening. Every pack that has come into this project has needed the
same three questions answered before anything could be placed from it: what is in it, how big are
those things, and where does the pack actually keep them. Guessing at any of the three has cost real
time -- a wall panel used as a free-standing desk, a 610cm lamp turned across a 360cm corridor, a
console placed 200cm inside a bulkhead, and a folder path misspelled by the pack itself.

Point PACK_ROOT at a newly added pack and run it. Reports every static and skeletal mesh with its
size, pivot convention and material count, grouped by folder, and flags anything that would fit the
demo's rooms as-is.

Writes nothing.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/survey_new_pack.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound

Point it at a pack with the SURVEY_PACK environment variable, which -ExecutePythonScript has no
way of passing as an argument:
    $env:SURVEY_PACK = "/Game/ModSciInteriors"

Set it from PowerShell, not from Git Bash. MSYS rewrites a value beginning with / into a Windows
path, so SURVEY_PACK=/Game/SciFiWorld arrives as C:/Program Files/Git/Game/SciFiWorld and the
survey reports an empty pack. Same family of trap as the 	ools\ path being read as a tab.
"""

import os

import unreal

# Set SURVEY_PACK to a /Game path to point this somewhere else. Falls back to the constant so the
# script is still runnable with no environment set, and logs which one it used -- a survey that
# silently reports on the wrong folder is worse than one that refuses.
PACK_ROOT = os.environ.get("SURVEY_PACK", "/Game/SciFi_Creatures_Research_Lab")

# What the demo's rooms can take. A room is 1100 x 1000 x 430 with wall panels standing inside that,
# so anything past this is furniture to be placed deliberately rather than dressing to be scattered.
ROOM_FOOTPRINT = 500.0
ROOM_HEIGHT = 400.0

# Names worth calling out for this project specifically. Purely a convenience for reading the report
# -- everything is listed regardless, because the interesting find in a pack is usually the thing
# nobody thought to search for.
OF_INTEREST = ("cryo", "capsule", "stasis", "pod", "tank", "tube", "chamber",
               "specimen", "jar", "container", "vat")


def describe(path):
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if asset is None:
        unreal.log_warning("    could not load {}".format(path))
        return

    name = path.rsplit("/", 1)[-1]

    if isinstance(asset, unreal.StaticMesh):
        bounds = asset.get_bounds()
        extent = bounds.box_extent
        origin = bounds.origin
        size = (extent.x * 2.0, extent.y * 2.0, extent.z * 2.0)
        materials = len(asset.static_materials)

        # A mesh authored on its base can be placed at floor height directly; one authored on its
        # centre or at an offset cannot, and mixing the two up is how props end up buried or
        # floating. Worth knowing per mesh rather than per pack, because packs are not consistent.
        pivot = "base" if abs(origin.z - extent.z) < 5.0 else (
            "centre" if abs(origin.z) < 5.0 else "offset")

        fits = (size[0] <= ROOM_FOOTPRINT and size[1] <= ROOM_FOOTPRINT
                and size[2] <= ROOM_HEIGHT)
        flag = "*" if any(hint in name.lower() for hint in OF_INTEREST) else " "

        unreal.log("  {} {:<44} {:5.0f} x {:5.0f} x {:5.0f}  pivot {:<6} {:2d} mat  {}".format(
            flag, name, size[0], size[1], size[2], pivot, materials,
            "fits a room" if fits else "large"))

    elif isinstance(asset, unreal.SkeletalMesh):
        skeleton = asset.get_editor_property("skeleton")
        unreal.log("  {} {:<44} SKELETAL, skeleton: {}".format(
            "*" if any(h in name.lower() for h in OF_INTEREST) else " ",
            name, skeleton.get_name() if skeleton else "none"))


def main():
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    assets = registry.get_assets_by_path(PACK_ROOT, recursive=True)

    if not assets:
        unreal.log_error(
            "Nothing under {}. Claiming a pack on Fab adds it to the library; it still has to be "
            "added to a project from the launcher or the in-editor Fab plugin. Check the path.".format(
                PACK_ROOT))
        return

    by_folder = {}
    for asset in assets:
        class_name = str(asset.asset_class_path.asset_name)
        if class_name not in ("StaticMesh", "SkeletalMesh"):
            continue
        package = str(asset.package_name)
        by_folder.setdefault(package.rsplit("/", 1)[0], []).append(package)

    total = sum(len(v) for v in by_folder.values())
    unreal.log("{} carries {} mesh(es) across {} folder(s). * marks a possible cryo stand-in.".format(
        PACK_ROOT, total, len(by_folder)))

    for folder in sorted(by_folder):
        unreal.log("{}".format(folder))
        for package in sorted(by_folder[folder]):
            describe(package)


if __name__ == "__main__":
    main()
