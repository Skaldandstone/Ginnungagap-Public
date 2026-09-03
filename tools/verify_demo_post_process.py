"""Read back what the demo map's post-processing is actually set to.

Seven renders have now been spent on the corridor being too bright, and every hypothesis has been
tested by changing a value and looking at the result. That is the slow way round, and it has been
wrong four times: the point lights, the emissive fixtures, the exposure floor, and the exposure
ceiling each looked like the answer and each changed nothing visible.

When a value is set and the picture does not move, there are only two possibilities: the value is
not the cause, or the value was never applied. Every pass so far has assumed the first. This checks
the second, which should have been checked before any of them.

Post-process settings are the classic place for this. Each field on FPostProcessSettings is inert
until its matching bOverride_ flag is true, and setting the field without the flag is completely
silent -- no warning, no error, and the property genuinely holds the value you gave it. It reads
back correctly and does nothing.

Reports every post-process volume in the map, whether it is unbound, its priority, and for each
setting this project sets: the value, and whether its override is on.

Writes nothing.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/verify_demo_post_process.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"

# (property, override flag). Exactly the set build_demo_atmosphere.py writes.
CHECKED = [
    ("auto_exposure_min_brightness", "override_auto_exposure_min_brightness"),
    ("auto_exposure_max_brightness", "override_auto_exposure_max_brightness"),
    ("auto_exposure_bias", "override_auto_exposure_bias"),
    ("bloom_intensity", "override_bloom_intensity"),
    ("ambient_occlusion_intensity", "override_ambient_occlusion_intensity"),
    ("vignette_intensity", "override_vignette_intensity"),
]

# Not written by this project, but decisive if it is set: a metering mode of Manual ignores the
# min/max clamp entirely, which would make four passes of tuning those two numbers meaningless.
INFORMATIONAL = [
    "auto_exposure_method",
    "auto_exposure_apply_physical_camera_exposure",
]


def describe(volume):
    unbound = volume.get_editor_property("unbound")
    priority = volume.get_editor_property("priority")
    enabled = volume.get_editor_property("enabled")
    blend = volume.get_editor_property("blend_weight")

    unreal.log("VOLUME {}".format(volume.get_actor_label()))
    unreal.log("    enabled={}  unbound={}  priority={}  blend_weight={}".format(
        enabled, unbound, priority, blend))

    settings = volume.get_editor_property("settings")

    for prop, flag in CHECKED:
        try:
            value = settings.get_editor_property(prop)
        except Exception as exc:
            unreal.log_error("    {} could not be read: {}".format(prop, exc))
            continue

        try:
            overridden = settings.get_editor_property(flag)
        except Exception as exc:
            unreal.log_error("    {} could not be read: {}".format(flag, exc))
            continue

        # The line that matters. A value that is set with its override off is a value that does
        # nothing, and it looks identical to one that is working.
        marker = "APPLIED" if overridden else "IGNORED -- override is off"
        unreal.log("    {:<34} = {:<10} {}".format(prop, round(float(value), 4), marker))

    for prop in INFORMATIONAL:
        try:
            unreal.log("    {:<34} = {}".format(prop, settings.get_editor_property(prop)))
        except Exception:
            pass


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(MAP_PATH):
        unreal.log_error("Could not load " + MAP_PATH)
        return

    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    volumes = [a for a in actors if isinstance(a, unreal.PostProcessVolume)]

    unreal.log("{} post-process volume(s) in {}".format(len(volumes), MAP_PATH))
    if not volumes:
        unreal.log_error("No post-process volume at all; every exposure value set so far was inert")
        return

    # More than one is worth knowing about on its own: an unbound volume at a higher priority would
    # override the one this project configures, silently and completely.
    if len(volumes) > 1:
        unreal.log_warning(
            "More than one volume. The highest-priority unbound volume wins, so the settings this "
            "project writes may not be the ones in effect.")

    for volume in volumes:
        describe(volume)

    # Sky lights and fog also change how bright an interior reads, and both have been suspected in
    # this investigation. Reported so the whole lighting environment is on one page.
    for actor in actors:
        if isinstance(actor, unreal.SkyLight):
            component = actor.get_editor_property("light_component")
            unreal.log("SKYLIGHT {} intensity={} mobility={}".format(
                actor.get_actor_label(),
                component.get_editor_property("intensity"),
                component.get_editor_property("mobility")))
        elif isinstance(actor, unreal.ExponentialHeightFog):
            component = actor.get_editor_property("component")
            unreal.log("FOG {} density={}".format(
                actor.get_actor_label(), component.get_editor_property("fog_density")))


if __name__ == "__main__":
    main()
