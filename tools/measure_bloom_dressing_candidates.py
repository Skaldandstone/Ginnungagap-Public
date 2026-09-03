"""Measure the organic-growth meshes the project already owns, before recommending any of them.

The breach room currently dresses its infestation with project-authored blockouts, and the render
shows what that gets you: flat-shaded white slabs and purple tubes that read as programmer geometry
rather than as something growing through a bulkhead.

Two Fab packs already in Content solve that, and were bought for other reasons: Alien_Biomass and
Alien_Cave_biome, both by LAYA DESIGN, each carrying thirteen alien organism meshes plus spore
effects. Nothing needs downloading.

This measures them rather than assuming, for the reason that keeps recurring here: a mesh being
the right *kind* of thing is not the same as it being the right size, and unmeasured props have
already put a wall panel free-standing in a room, a 610cm lamp through two walls, and a console
inside a bulkhead.

Reports bounds, pivot, material count and material names -- the last because a mesh with one plain
material is a blockout by another name, and swapping one blockout for another would be no gain at
all.

Writes nothing.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/measure_bloom_dressing_candidates.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

# The two owned packs, plus what the breach room uses today so the two can be compared directly.
GROUPS = [
    ("Alien_Biomass organisms", "/Game/Alien_Biomass/Meshes/Alien_organism"),
    ("Alien_Cave_biome organisms", "/Game/Alien_Cave_biome/Meshes/Alien_organism"),
    ("Alien_Cave_biome eggs and plants", "/Game/Alien_Cave_biome/Meshes/Egg"),
    ("Currently used Bloom blockouts", "/Game/Assets/Models/Bloom"),
]

# A room is 1100 x 1000 x 430. Growth that wants scaling down by more than this is furniture, not
# dressing, and should be placed deliberately rather than scattered.
ROOM_LIMIT = 500.0


def describe(path):
    mesh = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        return

    bounds = mesh.get_bounds()
    extent = bounds.box_extent
    origin = bounds.origin
    size = (extent.x * 2.0, extent.y * 2.0, extent.z * 2.0)

    materials = [str(slot.material_slot_name) for slot in mesh.static_materials]

    pivot = "base" if abs(origin.z - extent.z) < 5.0 else (
        "centre" if abs(origin.z) < 5.0 else "offset")

    # The judgement that matters. One material slot on an organic mesh usually means a single flat
    # surface treatment, which is exactly what the current blockouts already are.
    verdict = "dressing-ready" if len(materials) >= 1 and max(size) <= ROOM_LIMIT else (
        "large -- place deliberately" if len(materials) >= 1 else "no materials")

    unreal.log("    {:<34} {:5.0f} x {:5.0f} x {:5.0f}   pivot {:<6} {} material(s)  {}".format(
        path.rsplit("/", 1)[-1], size[0], size[1], size[2], pivot, len(materials), verdict))


def main():
    registry = unreal.AssetRegistryHelpers.get_asset_registry()

    for label, folder in GROUPS:
        assets = [a for a in registry.get_assets_by_path(folder, recursive=True)
                  if str(a.asset_class_path.asset_name) == "StaticMesh"]
        unreal.log("{}  ({} static mesh(es) under {})".format(label, len(assets), folder))

        if not assets:
            unreal.log_warning("    nothing found -- the path may have moved")
            continue

        for asset in sorted(assets, key=lambda a: str(a.asset_name)):
            describe(str(asset.package_name))


if __name__ == "__main__":
    main()
