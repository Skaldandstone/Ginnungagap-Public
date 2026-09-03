"""Grades L_Hero_CryoBay toward Sheet 11's measured tone.

The room's hue landed on the first build -- blue minus red -0.002 against the reference's +0.009 --
but its tone did not, and the map had no post process volume at all, so it was running whatever
default auto-exposure does.

Measured, new room against reference:

    p50 luminance   0.470  vs  0.138
    p90 luminance   0.910  vs  0.348
    clipped         4.4%   vs  1.2%
    crushed         26.6%  vs  6.1%

Clipping and crushing at once is the signature of too much contrast, not too much light, and it is
why simply dimming the lights would not fix it: the scene is auto-exposed, so lowering every light
lowers the average and the eye opens back up. Three levers instead, all in the grade:

  Exposure is LOCKED. min and max brightness set equal, so the frame stops renormalising and the
  numbers below mean something from one render to the next. For a hero still that is worth more
  than adaptivity.

  The toe comes down, which lifts the shadows. 26.6% of the frame at pure black against the
  reference's 6.1% is the larger of the two faults, and the reference's darks are lifted rather
  than crushed -- it is a low-key image, not a contrasty one.

  The shoulder comes up, which rolls off the highlights instead of clipping them.
"""

import unreal

MAP = "/Game/Assets/Maps/Hero/L_Hero_CryoBay"

# Histogram auto-exposure with the range pinched shut, NOT AEM_MANUAL.
#
# The first attempt used AEM_MANUAL and produced p50 0.005 with 77.7% of the frame crushed to black.
# AEM_MANUAL ignores min/max brightness completely -- it is driven by the camera's aperture, shutter
# and ISO -- so the 0.55 set below was discarded and the -1.2 bias landed on a default physical
# exposure metered for daylight. Locking the range only means anything in a metered mode.
#
# Range left slightly open rather than truly equal: a hair of adaptation costs nothing on a still
# and stops a single bright fixture from pinning the whole frame.
# v3 (bias -2.25) measured p50 0.325 against target 0.138 -- still about 1.2 stops bright.
# too bright, having fixed the crush the manual mode caused. Bias moved the remaining distance;
# min/max left alone since the range itself was not the problem, the exposure level was.
EXPOSURE_MIN = 0.9
EXPOSURE_MAX = 1.1
EXPOSURE_BIAS = 1.5

# Default film curve is Slope 0.88, Toe 0.55, Shoulder 0.26. Flatter, with lifted darks and a longer
# highlight roll-off.
FILM_SLOPE = 0.70
FILM_TOE = 0.28
FILM_SHOULDER = 0.46
FILM_BLACK_CLIP = 0.0
FILM_WHITE_CLIP = 0.10

TAG = "HeroCryoBayGrade"


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(MAP):
        unreal.log_error("GRADE could not load {}".format(MAP))
        return

    # Replace rather than stack, so re-running converges instead of compounding.
    removed = 0
    for actor in actors.get_all_level_actors():
        if actor.actor_has_tag(TAG):
            actors.destroy_actor(actor)
            removed += 1

    volume = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 200))
    if not volume:
        unreal.log_error("GRADE could not spawn the post process volume")
        return
    volume.tags = [unreal.Name(TAG)]
    volume.set_editor_property("unbound", True)
    volume.set_editor_property("priority", 100.0)

    settings = volume.get_editor_property("settings")

    settings.set_editor_property("override_auto_exposure_method", True)
    settings.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_HISTOGRAM)
    settings.set_editor_property("override_auto_exposure_min_brightness", True)
    settings.set_editor_property("auto_exposure_min_brightness", EXPOSURE_MIN)
    settings.set_editor_property("override_auto_exposure_max_brightness", True)
    settings.set_editor_property("auto_exposure_max_brightness", EXPOSURE_MAX)
    settings.set_editor_property("override_auto_exposure_bias", True)
    settings.set_editor_property("auto_exposure_bias", EXPOSURE_BIAS)

    for name, value in (("film_slope", FILM_SLOPE), ("film_toe", FILM_TOE),
                        ("film_shoulder", FILM_SHOULDER), ("film_black_clip", FILM_BLACK_CLIP),
                        ("film_white_clip", FILM_WHITE_CLIP)):
        settings.set_editor_property("override_" + name, True)
        settings.set_editor_property(name, value)

    volume.set_editor_property("settings", settings)

    # Read back rather than trust the write.
    check = volume.get_editor_property("settings")
    unreal.log("GRADE removed {}, placed 1 volume".format(removed))
    unreal.log("GRADE exposure {:.2f}..{:.2f}  bias {:+.2f}  slope {:.2f} toe {:.2f} shoulder {:.2f}".format(
        check.get_editor_property("auto_exposure_min_brightness"),
        check.get_editor_property("auto_exposure_max_brightness"),
        check.get_editor_property("auto_exposure_bias"),
        check.get_editor_property("film_slope"),
        check.get_editor_property("film_toe"),
        check.get_editor_property("film_shoulder")))

    levels.save_current_level()
    unreal.log("GRADE saved")


main()
