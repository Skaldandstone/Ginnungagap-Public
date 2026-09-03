"""Stop the cryo pod lids acting like mirrors.

The lid glass was the last thing standing between the cryo bay and a usable opening shot. It is
bright from every camera position the room's geometry allows, which ruled out reframing, and it
survived both a room-light desaturation and shutting three of the four lids.

tools/inspect_material.py finally said why, and it is none of the three things that had been
assumed:

  * It is **not emissive**. EmissiveColor is (0, 0, 0).
  * It is **not transparent**. blend_mode on the parent is BLEND_OPAQUE, so the Opacity parameter
    sitting at 0.42 does nothing at all. The Blender source authored it with transmission 0.78 and
    the FBX import dropped that on the floor -- the glass has never been glass.
  * It is a **mirror**. Shininess is 79.2 on an FBXLegacyPhongSurfaceMaterial, which is an enormous
    specular exponent, over a mid cyan diffuse of (0.11, 0.38, 0.48). A hard specular surface throws
    whatever light hits it straight back at the lens, which is exactly why no camera angle helped:
    moving the camera moves the highlight, it does not remove it.

So the fix is the two parameters that actually decide it. Shininess comes down until the lid
scatters rather than reflects, and the diffuse comes down because a cryo lid seen in an unlit bay
should be dark, not mid-blue.

Edited in place rather than via a child instance, unlike the kit fixtures. This is a project-authored
material used by the pod lids and nothing shipped, so there is no vendored asset to preserve and a
child would only add indirection.

Deliberately not changing blend_mode to make it genuinely translucent. That lives on the shared
FBXLegacyPhongSurfaceMaterial parent, so it would reach every FBX-imported material in the project.
Real glass wants its own parent material and is a separate job.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/tune_cryo_glass.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

GLASS = "/Game/Assets/ShipRooms/Cryo/M_Cryo_CrackedFrostGlass"

# 79.2 is a mirror. 14 still reads as a hard, wiped surface but spreads the highlight wide enough
# that it stops being a white shape in the middle of the frame.
TARGET_SHININESS = 14.0

# How much of the authored diffuse to keep. The hue is right -- cold, slightly green-blue -- and
# only the level is wrong, so this scales rather than replaces it.
DIFFUSE_SCALE = 0.45


def main():
    if not unreal.EditorAssetLibrary.does_asset_exist(GLASS):
        unreal.log_error("No material at {}".format(GLASS))
        return

    glass = unreal.EditorAssetLibrary.load_asset(GLASS)
    if not isinstance(glass, unreal.MaterialInstanceConstant):
        unreal.log_error("{} is a {}, not a MaterialInstanceConstant; nothing to set".format(
            GLASS, type(glass).__name__))
        return

    lib = unreal.MaterialEditingLibrary

    before_shine = lib.get_material_instance_scalar_parameter_value(glass, "Shininess")
    before_diffuse = lib.get_material_instance_vector_parameter_value(glass, "DiffuseColor")

    after_diffuse = unreal.LinearColor(
        before_diffuse.r * DIFFUSE_SCALE,
        before_diffuse.g * DIFFUSE_SCALE,
        before_diffuse.b * DIFFUSE_SCALE,
        1.0)

    lib.set_material_instance_scalar_parameter_value(glass, "Shininess", TARGET_SHININESS)
    lib.set_material_instance_vector_parameter_value(glass, "DiffuseColor", after_diffuse)
    lib.update_material_instance(glass)
    unreal.EditorAssetLibrary.save_asset(GLASS)

    unreal.log("Shininess     {:.2f} -> {:.2f}".format(before_shine, TARGET_SHININESS))
    unreal.log("DiffuseColor  ({:.3f}, {:.3f}, {:.3f}) -> ({:.3f}, {:.3f}, {:.3f})".format(
        before_diffuse.r, before_diffuse.g, before_diffuse.b,
        after_diffuse.r, after_diffuse.g, after_diffuse.b))

    # Read back. Setting a parameter the parent does not expose reports nothing and leaves the value
    # untouched, which looks identical to success -- that is how an earlier pass "dimmed" an emissive
    # scalar that had been zero all along.
    check_shine = lib.get_material_instance_scalar_parameter_value(glass, "Shininess")
    check_diffuse = lib.get_material_instance_vector_parameter_value(glass, "DiffuseColor")

    ok = (abs(check_shine - TARGET_SHININESS) < 0.01
          and abs(check_diffuse.r - after_diffuse.r) < 0.001
          and abs(check_diffuse.g - after_diffuse.g) < 0.001
          and abs(check_diffuse.b - after_diffuse.b) < 0.001)

    if ok:
        unreal.log("Verified: both parameters took.")
    else:
        unreal.log_error(
            "Read back Shininess {:.2f} and diffuse ({:.3f}, {:.3f}, {:.3f}) -- the set did not "
            "take".format(check_shine, check_diffuse.r, check_diffuse.g, check_diffuse.b))


if __name__ == "__main__":
    main()
