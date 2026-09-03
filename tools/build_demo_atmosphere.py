"""
Give L_QuickDemo_FourDeck the atmosphere pass it has never had.

The map ships 245 point lights and nothing else: no post-process volume, no sky light, no fog, no
reflection captures. That is why it reads as a grey blockout in motion despite the geometry and
dressing being there, and it is the single change that affects every frame of anything filmed.

Values here are deliberate but set without seeing the result, so they are conservative and grouped
at the top to be tuned in one place. They are a starting point for a lighting pass, not the end of
one. Everything this creates is a plain actor that can be selected and adjusted in the editor.

Idempotent: actors are tagged and matched on re-run, so this updates rather than duplicating.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/build_demo_atmosphere.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound

Forward slashes matter: a Windows path containing \tools\ is read as a tab by the shell.
"""

import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"

# Marks what this script owns, so a re-run updates its own actors and never touches hand-placed ones.
TAG = "GeneratedAtmosphere"

# --- tuning -----------------------------------------------------------------------------------
# Interior horror: dark, desaturated, cool. Exposure is clamped rather than left automatic so
# corridors stay dark instead of the eye adapting them back to grey, which is the usual reason a
# horror interior looks flat on camera.
#
# The clamp was not tight enough to do that job. Corridor lighting was dropped to emergency levels
# -- amber, 340 intensity against the rooms' 560-700 -- and the corridor rendered back at very
# nearly the same brightness as before, walls washed to cream, because a floor of 0.30 leaves the
# eye roughly three stops of lift to give away. Lowering the lights and leaving the floor low is
# self-cancelling: the darker the map gets, the harder the exposure works to undo it.
#
# 0.70 is the floor the emergency pass is judged against. It is a deliberate half-measure rather
# than a hard clamp at MAX, because the shot that is currently *closest* to right -- the engine
# room, lit by instrument glow and two practicals -- is already near the bottom of what reads, and
# a floor that takes it further down turns atmosphere into an absent frame. That failure has
# happened twice in this map already.
#
# The ceiling is where the corridor problem actually lived, and it took six renders to see it.
#
# The corridor would not darken. Point lights went 1200 -> 340 -> 90 -> 420 -> 120 and every frame
# came back the same. The kit's emissive ceiling fixtures were dimmed eight-fold and it barely
# moved. Raising the floor from 0.30 to 0.70 visibly darkened the engine room and did nothing at
# all to the corridor -- and that asymmetry is the whole answer.
#
# A 3.6 m tube of near-white panels with a fixture every 12 m is genuinely bright: bright enough
# that the eye adapts all the way to MAX and stays pinned there. Every change since has moved the
# scene's luminance around underneath a clamp that was already saturated, which is why none of them
# reached the image. The rooms sit near the floor, which is why every one of those changes reached
# *them*.
#
# So the ceiling comes up, and only the ceiling. Raising MAX lets the eye adapt further to bright
# scenes, which darkens them; the rooms are nowhere near it and do not move. One lever, one effect,
# and the two ends of the range now do different jobs instead of one doing both badly.
EXPOSURE_MIN = 0.70
EXPOSURE_MAX = 8.00
EXPOSURE_BIAS = -0.60

BLOOM_INTENSITY = 0.55          # enough for practical lights to glow, short of a haze
AO_INTENSITY = 0.62             # contact shadow in a space built from hard panels
AO_RADIUS = 120.0
VIGNETTE = 0.32
SATURATION = 0.88               # slightly drained; the Bloom violet still needs to read
CONTRAST = 1.06

SKYLIGHT_INTENSITY = 0.18       # ambient fill only, so shadows are dark but not pure black
SKYLIGHT_COLOR = (0.42, 0.56, 0.62)   # cool, matched to the instrument palette ground

FOG_DENSITY = 0.018             # corridor depth falloff without visible haze in small rooms
FOG_HEIGHT_FALLOFF = 0.14
FOG_COLOR = (0.035, 0.055, 0.070)

# Reflection captures are what make wet metal and glass read as surfaces rather than flat panels.
# One per Nth room keeps the count sane on a 194-room map; captures are expensive and overlapping
# ones fight each other.
REFLECTION_EVERY_NTH_ROOM = 6
REFLECTION_RADIUS = 900.0


def tagged(actor):
    return TAG in [str(t) for t in actor.tags]


def clear_previous(actor_subsystem):
    """Removes what a previous run created, so values never merge across runs."""
    removed = 0
    for actor in actor_subsystem.get_all_level_actors():
        if tagged(actor):
            actor_subsystem.destroy_actor(actor)
            removed += 1
    return removed


def spawn(actor_subsystem, cls, location, label):
    actor = actor_subsystem.spawn_actor_from_class(cls, unreal.Vector(*location))
    if not actor:
        unreal.log_error("Failed to spawn {}".format(label))
        return None
    actor.set_actor_label(label)
    actor.tags = [TAG]
    return actor


def room_bounds(actors):
    """Extents of the playable space, from the rooms rather than from every actor in the level."""
    rooms = [a for a in actors if "ModularShipRoom" in a.get_class().get_name()]
    if not rooms:
        return None, None, 0

    xs, ys, zs = [], [], []
    for room in rooms:
        loc = room.get_actor_location()
        xs.append(loc.x)
        ys.append(loc.y)
        zs.append(loc.z)

    lo = unreal.Vector(min(xs), min(ys), min(zs))
    hi = unreal.Vector(max(xs), max(ys), max(zs))
    return lo, hi, len(rooms)


def main():
    if not unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        unreal.log_error("Map not found: {}".format(MAP_PATH))
        return

    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    level_subsystem.load_level(MAP_PATH)

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = actor_subsystem.get_all_level_actors()

    removed = clear_previous(actor_subsystem)
    if removed:
        unreal.log("Removed {} actor(s) from a previous run".format(removed))
        actors = actor_subsystem.get_all_level_actors()

    lo, hi, room_count = room_bounds(actors)
    if lo is None:
        unreal.log_error("No ModularShipRoom actors found; refusing to guess at placement")
        return

    centre = ((lo.x + hi.x) * 0.5, (lo.y + hi.y) * 0.5, (lo.z + hi.z) * 0.5)
    unreal.log("Ship spans X {:.0f}..{:.0f}  Y {:.0f}..{:.0f}  Z {:.0f}..{:.0f} across {} rooms"
               .format(lo.x, hi.x, lo.y, hi.y, lo.z, hi.z, room_count))

    # --- post process ---------------------------------------------------------------------
    ppv = spawn(actor_subsystem, unreal.PostProcessVolume, centre, "PP_DemoAtmosphere")
    if ppv:
        # Unbound: one volume covering the whole ship rather than per-deck volumes that would
        # pop as the player crosses a boundary.
        ppv.set_editor_property("unbound", True)
        ppv.set_editor_property("priority", 1.0)

        s = ppv.get_editor_property("settings")
        s.set_editor_property("auto_exposure_min_brightness", EXPOSURE_MIN)
        s.set_editor_property("auto_exposure_max_brightness", EXPOSURE_MAX)
        s.set_editor_property("auto_exposure_bias", EXPOSURE_BIAS)
        s.set_editor_property("bloom_intensity", BLOOM_INTENSITY)
        s.set_editor_property("ambient_occlusion_intensity", AO_INTENSITY)
        s.set_editor_property("ambient_occlusion_radius", AO_RADIUS)
        s.set_editor_property("vignette_intensity", VIGNETTE)
        s.set_editor_property("color_saturation", unreal.Vector4(SATURATION, SATURATION, SATURATION, 1.0))
        s.set_editor_property("color_contrast", unreal.Vector4(CONTRAST, CONTRAST, CONTRAST, 1.0))

        # Each override must be switched on explicitly or the value above is ignored entirely --
        # the most common way a post-process volume silently does nothing.
        for flag in [
            "override_auto_exposure_min_brightness", "override_auto_exposure_max_brightness",
            "override_auto_exposure_bias", "override_bloom_intensity",
            "override_ambient_occlusion_intensity", "override_ambient_occlusion_radius",
            "override_vignette_intensity", "override_color_saturation", "override_color_contrast",
        ]:
            try:
                s.set_editor_property(flag, True)
            except Exception as exc:
                unreal.log_warning("Could not set {}: {}".format(flag, exc))

        ppv.set_editor_property("settings", s)
        unreal.log("Post-process volume placed (unbound)")

    # --- sky light ------------------------------------------------------------------------
    sky = spawn(actor_subsystem, unreal.SkyLight, (centre[0], centre[1], hi.z + 2000.0), "SkyLight_DemoFill")
    if sky:
        comp = sky.get_editor_property("light_component")
        comp.set_editor_property("intensity", SKYLIGHT_INTENSITY)
        comp.set_editor_property("light_color", unreal.Color(
            int(SKYLIGHT_COLOR[0] * 255), int(SKYLIGHT_COLOR[1] * 255), int(SKYLIGHT_COLOR[2] * 255), 255))
        # Movable: the ship's lighting changes with power state, and a baked fill would not follow.
        comp.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
        unreal.log("Sky light placed for ambient fill")

    # --- fog ------------------------------------------------------------------------------
    fog = spawn(actor_subsystem, unreal.ExponentialHeightFog,
                (centre[0], centre[1], lo.z - 500.0), "Fog_DemoDepth")
    if fog:
        comp = fog.get_editor_property("component")
        comp.set_editor_property("fog_density", FOG_DENSITY)
        comp.set_editor_property("fog_height_falloff", FOG_HEIGHT_FALLOFF)
        comp.set_editor_property("fog_inscattering_luminance", unreal.LinearColor(*FOG_COLOR, 1.0))
        unreal.log("Height fog placed for corridor depth")

    # --- reflection captures --------------------------------------------------------------
    rooms = [a for a in actors if "ModularShipRoom" in a.get_class().get_name()]
    rooms.sort(key=lambda a: (a.get_actor_location().z, a.get_actor_location().x))

    placed = 0
    for index, room in enumerate(rooms):
        if index % REFLECTION_EVERY_NTH_ROOM:
            continue
        loc = room.get_actor_location()
        capture = spawn(actor_subsystem, unreal.SphereReflectionCapture,
                        (loc.x, loc.y, loc.z + 200.0), "Refl_Room_{:03d}".format(index))
        if capture:
            capture.get_editor_property("capture_component").set_editor_property(
                "influence_radius", REFLECTION_RADIUS)
            placed += 1

    unreal.log("Placed {} reflection captures (one per {} rooms)".format(placed, REFLECTION_EVERY_NTH_ROOM))

    saved = level_subsystem.save_current_level()
    unreal.log("Saved {}: {}".format(MAP_PATH, saved))


if __name__ == "__main__":
    main()
