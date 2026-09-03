"""Turn the corridor's main light fixtures down, at the material rather than at the lights.

Three passes tried to darken the demo corridors by lowering their point lights -- 1200 to 340 to 90,
a thirteenth of the original -- and the last two renders are indistinguishable. Tightening the map's
auto-exposure floor in between changed nothing either, which ruled out the eye adapting the dark
back to grey. Something else was doing the lighting.

tools/inspect_corridor_light_sources.py found it. SM_LAMP_04, the ceiling fixture placed once per
12 m bay down every deck, carries MI_EMISION_4 on its second material slot -- a self-lit material.
Emissive surfaces feed Lumen's global illumination, and in a 3.6 m tube of near-white panels a strip
of them out-lights the actual lights by a wide margin. No value of CORRIDOR_LIGHT_INTENSITY was ever
going to matter.

The brightness is not where the parameter names suggest, either. 'Emission Intensity' on that
instance is 0.0; the emission comes from EMS_COLOR, an HDR vector at (0.44, 1.66, 2.00) -- magnitude
2.6, and the cyan-white cast that every corridor render has had. A first version of this script set
the scalar, reported success, and would have changed nothing: the value was already zero and setting
zero times a fraction is still zero. Reading the parameter back is what caught it.

So this makes a dimmed child of that material and sets EMS_COLOR: same magnitude cut the point
lights were given, and amber rather than cyan, which is the emergency-circuit read the point-light
passes were reaching for and never achieved.

Deliberately a new material instance rather than an edit to MI_EMISION_4. That asset ships with the
Fab kit and is used by pack assets across the project; editing it in place would dim things this
pass has never looked at, and would be lost the moment the pack is updated.

Idempotent: re-running updates the instance rather than creating a second one.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/build_emergency_lighting_materials.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import math

import unreal

# Note the MI/ folder. The pack nests its instances one level below Material/, and the first version
# of this script had the flatter path, fell through to a registry search, and only worked by
# accident. Guessed paths in this pack have been wrong three times now.
SOURCE_MATERIAL = "/Game/Modular_Scifi_Mechanic_Base/Material/MI/MI_EMISION_4"
TARGET_PACKAGE = "/Game/Assets/Gameplay/Materials"
TARGET_NAME = "MI_EmergencyFixture_Dim"

EMISSION_COLOUR_PARAMETER = "EMS_COLOR"

# What fraction of the kit's own emissive output the emergency circuit runs at.
#
# An eighth rather than a half. The point lights were cut to a thirteenth with no visible change,
# which says the emissive is not merely dominant but very nearly all of the light in frame -- so a
# timid cut here lands exactly where the last two passes did. A fixture that is still clearly lit,
# and clearly not doing its job, is the read.
EMERGENCY_FRACTION = 0.125

# Amber, as a direction rather than a colour: the magnitude comes from the kit value times the
# fraction above, so the hue and the brightness are two separate decisions instead of one number
# that quietly does both.
EMERGENCY_HUE = (1.0, 0.45, 0.12)


def find_source():
    if unreal.EditorAssetLibrary.does_asset_exist(SOURCE_MATERIAL):
        return unreal.EditorAssetLibrary.load_asset(SOURCE_MATERIAL)

    # Registry fallback, kept because this pack's folder layout has caught this project out
    # repeatedly -- one of its directories is misspelled in the pack itself. It is a fallback and
    # not the primary path on purpose: a script that silently finds assets by name will happily
    # find the wrong one.
    unreal.log_warning("{} not at its expected path; searching the registry".format(SOURCE_MATERIAL))
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    wanted = SOURCE_MATERIAL.rsplit("/", 1)[-1]
    for asset in registry.get_assets_by_path("/Game/Modular_Scifi_Mechanic_Base", recursive=True):
        if str(asset.asset_name) == wanted:
            return unreal.EditorAssetLibrary.load_asset(str(asset.package_name))
    return None


def scaled_amber(inherited):
    """Amber at the same magnitude the kit colour had, times the emergency fraction."""
    magnitude = math.sqrt(inherited.r ** 2 + inherited.g ** 2 + inherited.b ** 2)
    target = magnitude * EMERGENCY_FRACTION

    hue_length = math.sqrt(sum(channel ** 2 for channel in EMERGENCY_HUE))
    return unreal.LinearColor(
        EMERGENCY_HUE[0] / hue_length * target,
        EMERGENCY_HUE[1] / hue_length * target,
        EMERGENCY_HUE[2] / hue_length * target,
        1.0,
    )


def main():
    source = find_source()
    if source is None:
        unreal.log_error("Could not find {}; nothing to dim".format(SOURCE_MATERIAL))
        return

    target_path = "{}/{}".format(TARGET_PACKAGE, TARGET_NAME)

    if unreal.EditorAssetLibrary.does_asset_exist(target_path):
        instance = unreal.EditorAssetLibrary.load_asset(target_path)
        unreal.log("Updating existing {}".format(target_path))
    else:
        tools = unreal.AssetToolsHelpers.get_asset_tools()
        instance = tools.create_asset(
            TARGET_NAME, TARGET_PACKAGE,
            unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        if instance is None:
            unreal.log_error("Could not create {}".format(target_path))
            return
        unreal.log("Created {}".format(target_path))

    unreal.MaterialEditingLibrary.set_material_instance_parent(instance, source)

    # Read the kit's own colour rather than assuming one. The fraction and the hue are the
    # decisions; the absolute brightness is whatever the pack shipped, and hardcoding it would
    # silently stop tracking the pack.
    inherited = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(
        instance, EMISSION_COLOUR_PARAMETER)
    dimmed = scaled_amber(inherited)

    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        instance, EMISSION_COLOUR_PARAMETER, dimmed)
    unreal.MaterialEditingLibrary.update_material_instance(instance)
    unreal.EditorAssetLibrary.save_asset(target_path)

    unreal.log("{} inherited ({:.2f}, {:.2f}, {:.2f}) -> set ({:.3f}, {:.3f}, {:.3f})".format(
        EMISSION_COLOUR_PARAMETER,
        inherited.r, inherited.g, inherited.b,
        dimmed.r, dimmed.g, dimmed.b))

    # Read it back. Setting a parameter the parent does not expose reports nothing at all, and a
    # silent no-op looks exactly like a successful run -- which is precisely how the scalar version
    # of this script came to claim it had dimmed a value that was already zero.
    readback = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(
        instance, EMISSION_COLOUR_PARAMETER)
    drift = max(abs(readback.r - dimmed.r), abs(readback.g - dimmed.g), abs(readback.b - dimmed.b))
    if drift > 0.001:
        unreal.log_error(
            "Read back ({:.3f}, {:.3f}, {:.3f}) after setting ({:.3f}, {:.3f}, {:.3f}): "
            "the parameter did not take".format(
                readback.r, readback.g, readback.b, dimmed.r, dimmed.g, dimmed.b))
    else:
        unreal.log("Verified: {} now reads ({:.3f}, {:.3f}, {:.3f})".format(
            EMISSION_COLOUR_PARAMETER, readback.r, readback.g, readback.b))


if __name__ == "__main__":
    main()
