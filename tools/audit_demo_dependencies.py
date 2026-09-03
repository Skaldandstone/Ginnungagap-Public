"""Lists every content pack the demo actually depends on, transitively, from the asset registry.

Written before deleting anything. The keep/cut triage said the demo references about seven of the
sixty packs in Content, and that number came from grepping the dressing scripts for "/Game/" paths.
That is good enough to plan with and nowhere near good enough to delete 40 GB on: a script names the
meshes it places, not the materials those meshes reference, nor the textures under those materials,
nor anything a Blueprint pulls in that no script mentions.

So this asks Unreal instead. It walks the hard dependencies of the maps worth keeping, transitively,
and reports which top-level /Game/<Pack> folders those dependencies land in. A pack that appears is
load-bearing. A pack that does not appear is a deletion candidate -- still a candidate rather than a
verdict, because the registry sees hard references and not soft paths built from strings at runtime,
which this project does use (the cryo pod materials are loaded by path in a C++ constructor).

Keep roots are listed explicitly rather than discovered, so adding a map to the demo means adding it
here on purpose.
"""

import unreal

KEEP_MAPS = [
    "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck",
]

# Packs a string-loaded path can reach without the registry knowing. Sourced from the C++ that calls
# LoadObject/ConstructorHelpers with a literal, which the registry cannot see.
SOFT_REFERENCED = {
    "Assets",          # /Game/Assets/... cryo pod materials, weapons, field supplies, UI cues
    "SciFiUISFX",      # UUiSoundSubsystem resolves cue paths as strings
}


def pack_of(package_name):
    """Top-level folder under /Game, which is how Fab packs land."""
    parts = package_name.split("/")
    if len(parts) > 2 and parts[1] == "Game":
        return parts[2]
    return None


def main():
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    registry.wait_for_completion()

    seen = set()
    frontier = [unreal.Name(m) for m in KEEP_MAPS]

    while frontier:
        package = frontier.pop()
        if package in seen:
            continue
        seen.add(package)

        options = unreal.AssetRegistryDependencyOptions(
            include_soft_package_references=True,
            include_hard_package_references=True,
            include_searchable_names=False,
            include_soft_management_references=False,
            include_hard_management_references=False,
        )
        try:
            deps = registry.get_dependencies(package, options) or []
        except Exception as error:
            unreal.log_warning("DEP could not read dependencies of {}: {}".format(package, error))
            continue

        for dep in deps:
            if dep not in seen:
                frontier.append(dep)

    packs = {}
    for package in seen:
        name = str(package)
        pack = pack_of(name)
        if pack:
            packs[pack] = packs.get(pack, 0) + 1

    unreal.log("DEP {} package(s) reachable from {} map(s)".format(len(seen), len(KEEP_MAPS)))
    unreal.log("DEP ---- packs the demo depends on ----")
    for pack, count in sorted(packs.items(), key=lambda kv: -kv[1]):
        unreal.log("DEP   {:<44} {:5d} asset(s)".format(pack, count))

    for pack in sorted(SOFT_REFERENCED):
        if pack not in packs:
            unreal.log("DEP   {:<44} (soft-referenced by C++ path, not in registry)".format(pack))

    unreal.log("DEP ---- end ----")


main()
