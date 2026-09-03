"""Find out what is actually lighting the demo corridors.

Three passes have now tried to darken the corridor by changing its point lights, and the third
proved they are not the cause. Corridor light intensity went 1200 -> 340 -> 90 -- roughly a
thirteenth of where it started -- and the rendered frame is indistinguishable across the last two.
The map's auto-exposure floor was tightened in between, which also changed nothing, so the eye
adapting the darkness back to grey is ruled out as well.

That leaves emissive materials. The kit's ceiling fixtures and wall panels light themselves, and
emissive surfaces contribute to Lumen's global illumination, so in a narrow white-panelled tube they
can easily out-light the actual lights. If that is what is happening then no amount of turning the
lights down will ever work, which is exactly the symptom.

This reports, for each mesh the corridor dresser places:

  * every material slot, and whether its material or any parent in its chain uses emission
  * the emissive parameters exposed on any material instance, which is what a fix would set

Writes nothing. The point is to find the source before changing anything else, having now spent
three renders changing the wrong thing.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/inspect_corridor_light_sources.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

# The meshes dress_demo_corridors.py places, by kit name. The lamp is the prime suspect, but the
# wall and ceiling panels are included because a self-lit wall would look exactly like this too and
# assuming it is the lamp is how the last three passes went wrong.
SUSPECTS = [
    "SM_LAMP_04",
    "SM_CEILING_09",
    "SM_WALL_07",
    "SM_WALL_09",
    "SM_WALL_12",
    "SM_FLOOR_05",
    "SM_CABLE_01",
]

KIT_ROOT = "/Game/Modular_Scifi_Mechanic_Base"

# Parameter names worth reporting if a material instance exposes them. Different packs spell this
# differently, so matching on a substring beats a fixed list.
EMISSIVE_HINTS = ("emiss", "glow", "light", "bright")


def index_kit():
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    index = {}
    for asset in registry.get_assets_by_path(KIT_ROOT, recursive=True):
        if str(asset.asset_class_path.asset_name) == "StaticMesh":
            index[str(asset.asset_name)] = str(asset.package_name)
    return index


def material_chain(material):
    """The instance, its parents, up to the base material."""
    chain = []
    current = material
    # Bounded rather than while-true: a corrupt asset with a cyclic parent would otherwise hang the
    # editor with no output at all.
    for _ in range(8):
        if current is None:
            break
        chain.append(current)
        current = current.get_editor_property("parent") if isinstance(
            current, unreal.MaterialInstance) else None
    return chain


def report_material(slot_index, material):
    if material is None:
        unreal.log("    slot {}: <empty>".format(slot_index))
        return

    chain = material_chain(material)
    names = " <- ".join(m.get_name() for m in chain)
    unreal.log("    slot {}: {}".format(slot_index, names))

    base = chain[-1] if chain else None
    if isinstance(base, unreal.Material):
        # The authoritative answer: does the base material connect anything to emissive at all.
        # A shading model of Unlit is worth knowing about for the same reason.
        try:
            unreal.log("        base shading model: {}".format(
                base.get_editor_property("shading_model")))
        except Exception as exc:
            unreal.log_warning("        could not read shading model: {}".format(exc))

    for material_instance in chain:
        if not isinstance(material_instance, unreal.MaterialInstance):
            continue
        try:
            scalars = unreal.MaterialEditingLibrary.get_scalar_parameter_names(material_instance)
            vectors = unreal.MaterialEditingLibrary.get_vector_parameter_names(material_instance)
        except Exception as exc:
            unreal.log_warning("        could not read parameters: {}".format(exc))
            continue

        for name in list(scalars) + list(vectors):
            if any(hint in str(name).lower() for hint in EMISSIVE_HINTS):
                unreal.log("        {} exposes '{}'".format(material_instance.get_name(), name))


def main():
    index = index_kit()
    unreal.log("Indexed {} kit meshes".format(len(index)))

    for name in SUSPECTS:
        path = index.get(name)
        if not path:
            unreal.log_warning("{} is not in the kit index".format(name))
            continue

        mesh = unreal.EditorAssetLibrary.load_asset(path)
        if not isinstance(mesh, unreal.StaticMesh):
            unreal.log_warning("{} is not a static mesh".format(name))
            continue

        unreal.log("SUSPECT {}".format(name))
        for slot_index, slot in enumerate(mesh.static_materials):
            report_material(slot_index, slot.material_interface)


if __name__ == "__main__":
    main()
