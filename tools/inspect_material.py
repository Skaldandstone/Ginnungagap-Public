"""Report everything about a material that decides how bright it renders.

Written for M_Cryo_CrackedFrostGlass, which is the last thing standing between the cryo bay and a
usable opening shot: it is bright in every camera position the room's geometry allows, so the
material is the lever and no amount of reframing or room lighting substitutes for it.

Generalised because this is the third time a surface has turned out to be the thing lighting a room.
The corridor was the kit's emissive ceiling fixtures, the rooms were the same fixtures again, and
each time several passes were spent adjusting lights that were never the dominant term. Asking the
material directly is quicker than inferring it from renders.

Reports the class, the parent chain, shading model, blend mode, two-sidedness, and every scalar,
vector and texture parameter with its value -- for a MaterialInstance. For a plain Material there
are no instance parameters to read, so it reports what the asset itself exposes and says so, which
is itself the answer: a plain Material has to be edited or instanced, not parameterised.

Writes nothing.

Run through Unreal Editor Python, setting the target from PowerShell (not Git Bash -- MSYS rewrites
a leading / into a Windows path):
    $env:INSPECT_MATERIAL = "/Game/Assets/ShipRooms/Cryo/M_Cryo_CrackedFrostGlass"
"""

import os

import unreal

MATERIAL_PATH = os.environ.get(
    "INSPECT_MATERIAL", "/Game/Assets/ShipRooms/Cryo/M_Cryo_CrackedFrostGlass")

# Properties on a UMaterial that decide whether it glows, how it blends, and whether it is lit at
# all. Read individually and guarded, because which of these exist varies by engine version and a
# missing one should not abort the report.
MATERIAL_PROPERTIES = (
    "shading_model",
    "blend_mode",
    "two_sided",
    "use_material_attributes",
    "opacity_mask_clip_value",
)


def show(label, getter):
    try:
        unreal.log("    {:<38} {}".format(label, getter()))
    except Exception as exc:
        unreal.log("    {:<38} <unreadable: {}>".format(label, type(exc).__name__))


def main():
    if not unreal.EditorAssetLibrary.does_asset_exist(MATERIAL_PATH):
        unreal.log_error("No asset at {}".format(MATERIAL_PATH))
        return

    asset = unreal.EditorAssetLibrary.load_asset(MATERIAL_PATH)
    unreal.log("MATERIAL {}  ({})".format(MATERIAL_PATH, type(asset).__name__))

    # Parent chain first. A value set three instances up is still the value that renders, and the
    # chain is where to go looking when an instance appears to expose nothing.
    chain = []
    current = asset
    for _ in range(8):
        if current is None:
            break
        chain.append(current)
        current = current.get_editor_property("parent") if isinstance(
            current, unreal.MaterialInstance) else None
    unreal.log("  chain: {}".format(" <- ".join(m.get_name() for m in chain)))

    base = chain[-1] if chain else None
    if isinstance(base, unreal.Material):
        unreal.log("  base material properties:")
        for prop in MATERIAL_PROPERTIES:
            show(prop, lambda p=prop: base.get_editor_property(p))

    if not isinstance(asset, unreal.MaterialInstance):
        unreal.log("  This is a plain Material, so it has no instance parameters to read or set.")
        unreal.log("  To change it without editing the asset, make a MaterialInstanceConstant child")
        unreal.log("  and override there -- but only if the base exposes parameters; if it does not,")
        unreal.log("  an instance can override nothing and the asset itself has to change.")
        return

    unreal.log("  instance parameters:")
    for kind, names, get in (
        ("SCALAR", unreal.MaterialEditingLibrary.get_scalar_parameter_names,
         unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value),
        ("VECTOR", unreal.MaterialEditingLibrary.get_vector_parameter_names,
         unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value),
        ("TEX", unreal.MaterialEditingLibrary.get_texture_parameter_names,
         unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value),
    ):
        try:
            found = list(names(asset))
        except Exception as exc:
            unreal.log_warning("    could not read {} names: {}".format(kind, exc))
            continue

        if not found:
            unreal.log("    {} <none>".format(kind))
            continue

        for name in found:
            try:
                value = get(asset, name)
            except Exception:
                value = "<unreadable>"
            if hasattr(value, "get_name"):
                value = value.get_name()
            unreal.log("    {} {:<34} = {}".format(kind, str(name), value))


if __name__ == "__main__":
    main()
