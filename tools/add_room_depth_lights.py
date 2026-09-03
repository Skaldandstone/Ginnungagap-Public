"""Places a depth light in each hero-shot room, along that shot's own camera axis.

Generalises the light that fixed the workshop. Read the caveat before trusting the premise.

WHAT IS ACTUALLY KNOWN. Adding one light at the workshop's mid-depth took that shot from unusable
to readable. That is verified by render and is not in doubt.

WHAT WAS WRONGLY CLAIMED. The first version of this reasoning said the workshop's fault was that its
light sat at the frame edges while the centre of frame was empty -- and that raising the existing
lights would have achieved nothing, because auto-exposure renormalises average luminance. Measuring
it properly, with tools/survey_room_lighting.py computing inverse-square illuminance at both points,
says otherwise: before the depth light the workshop's centre subject was already receiving ~189% of
what its nearest edge geometry received. There was no hole in the middle. The room was uniformly
under-lit, and what the third light supplied was more total light.

The auto-exposure argument was misapplied. Exposure does renormalise, but it is clamped at
EXPOSURE_MAX = 8.0 in build_demo_atmosphere.py, and a scene too dim to reach a usable level within
that gain simply stays black. Absolute brightness was very likely the real lever.

WHAT FOLLOWS FOR THE OTHER FIVE ROOMS. They render fine and none of them shows a centre deficit, so
the measurement predicts a depth light will not help them and may flatten them -- which is precisely
what happened to the workshop's own back wall on the first attempt. That prediction is worth exactly
as much as the last one, which is why this script exists: apply it, render all six, and let the
images decide per room. ROOMS below carries an `enabled` flag so any room the renders reject can be
switched off without unpicking the rest.
"""

import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"

EYE = 165.0
DECK = {1: 215.0, 2: 735.0, 3: 1255.0, 4: 1775.0}
FLOOR_DROP = 195.0
DOORWAY_OFFSET = 260.0
LOOK_PAST = 300.0

# Where along the camera-to-target ray the light sits.
#
# 0.89 rather than a fixed offset in centimetres, so this transfers to the CIC, whose camera is
# hand-placed on a diagonal from the back corner rather than square-on from a doorway. For the
# workshop it reproduces the position three renders converged on: 0.89 x 720 = 641, which is the
# (-5400, -901) that shot was tuned to.
RAY_FRACTION = 0.89

# Work-lamp height rather than the ceiling height the room pairs use. A ceiling light washes the far
# wall evenly and an evenly lit wall carries no depth; at this height the falloff grazes the floor
# and mid-ground instead.
LIGHT_HEIGHT = 170.0

# The fill sits below its room's key pair at the same ratio the workshop settled on: 1500 of 2100.
FILL_RATIO = 1500.0 / 2100.0
RADIUS = 650.0

TAG = "RoomDepthLight"
# The workshop's light was placed by the earlier single-room script under its own tag. Cleared here
# too, so this pass owns every depth light rather than stacking a second one beside it.
LEGACY_TAG = "WorkshopDepthLight"

# Colour and key intensity per room, matching LIGHT_BY_PROFILE in tools/dress_demo_slice.py. A fill
# in a different colour would read as a different kind of source; this is meant to be the same
# failing emergency system, nearer the camera.
PROFILE = {
    "cryo":        (unreal.LinearColor(0.72, 0.86, 1.0, 1.0), 1900.0),
    "engineering": (unreal.LinearColor(1.0, 0.55, 0.20, 1.0), 2400.0),
    "workshop":    (unreal.LinearColor(1.0, 0.72, 0.42, 1.0), 2100.0),
    "command":     (unreal.LinearColor(0.62, 0.78, 1.0, 1.0), 2100.0),
    "breach":      (unreal.LinearColor(1.0, 0.22, 0.14, 1.0), 1500.0),
}

# (name, enabled, profile, deck, room x, room y, cam dx, cam dy, cam h, tgt dx, tgt dy, tgt h)
#
# The enabled flags are render results, not predictions. All six were placed, all six shot, and each
# judged on its own image:
#
#   04_CIC          win      -- the holographic plot became a readable focal subject; it had been the
#                              darkest shot in the set at 1.66 MB.
#   05_BloomBreach  win      -- the biomass now reads amber against purple with a dark ceiling. Best
#                              frame in the set.
#   08_PowerControl win      -- the console reads backlit and centred.
#   07_Workshop     win      -- the room this rule came from.
#   01_CryoWake     tuned    -- revealed the suited figure, which is a real gain, but at 170 above a
#                              narrow white aisle it blew the floor strip to pure white. Raised.
#   03_EngineRoom   REVERTED -- see below.
ROOMS = [
    ("01_CryoWake",     True,  "cryo",        3, -6600.0, -680.0,    0.0,   0.0,  0.0,    0.0,    0.0,  0.0),
    # Off, and this is the useful result of the whole exercise.
    #
    # The engine room did not have the workshop's problem, and the survey said so before the render
    # did: it renders three large reactor housings close to the lens with deep blacks behind them,
    # and it was the strongest frame in the set. Adding a fill turned it into an evenly lit beige
    # room -- more of it visible, all of it flat, every black gone. That is the same flattening the
    # workshop's own first attempt did to its back wall, and "more is visible" is not the goal.
    ("03_EngineRoom",   False, "engineering", 2, -6600.0, -680.0,    0.0,   0.0,  0.0,    0.0,    0.0,  0.0),
    ("04_CIC",          True,  "command",     3,  6600.0,  680.0, -400.0, 400.0, EYE,  300.0, -300.0, EYE + 35.0),
    ("05_BloomBreach",  True,  "breach",      3,  5400.0, -680.0,    0.0,   0.0,  0.0,    0.0,    0.0,  0.0),
    ("07_Workshop",     True,  "workshop",    3, -5400.0, -680.0,    0.0,   0.0,  0.0,    0.0,    0.0,  0.0),
    ("08_PowerControl", True,  "engineering", 2, -5400.0,  680.0,    0.0,   0.0,  0.0,    0.0,    0.0,  0.0),
]

# Per-room departures from the defaults above, each one earned by a render rather than guessed.
OVERRIDES = {
    # The cryo aisle is narrow, white and specular, so a light at work-lamp height sits far closer to
    # the floor than to anything else in frame and blows the strip out. Same ratio fault as the
    # workshop's first attempt, on the floor instead of a wall, and the same fix: move it, do not dim
    # it. 300 puts it level with the pod tops, which is what the shot is actually about.
    # Height alone was not enough. 170 -> 300 cuts what the floor directly beneath receives by about
    # 3x and the aisle stayed blown, which says it was well past clipping rather than just over it.
    # Halving the fill on top of that is another 2x. If the strip is still white after this, my light
    # was never what was blowing it and the cause is the room's own pair.
    "01_CryoWake": {"height": 300.0, "intensity_scale": 0.5},
}


def at(deck, x, y, height=EYE):
    return unreal.Vector(x, y, DECK[deck] - FLOOR_DROP + height)


def camera_and_target(room):
    (_, _, _, deck, room_x, room_y, cam_dx, cam_dy, cam_h, tgt_dx, tgt_dy, tgt_h) = room
    if cam_dx or cam_dy or tgt_dx or tgt_dy:
        return at(deck, room_x + cam_dx, room_y + cam_dy, cam_h), \
               at(deck, room_x + tgt_dx, room_y + tgt_dy, tgt_h)
    side = 1.0 if room_y > 0.0 else -1.0
    return at(deck, room_x, side * DOORWAY_OFFSET), \
           at(deck, room_x, room_y + side * LOOK_PAST, EYE - 45.0)


def main():
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    actors = unreal.EditorActorSubsystem()

    removed = 0
    for actor in actors.get_all_level_actors():
        tags = [str(t) for t in actor.tags]
        if TAG in tags or LEGACY_TAG in tags:
            actors.destroy_actor(actor)
            removed += 1
    unreal.log("DEPTH cleared {} existing depth light(s)".format(removed))

    placed = 0
    for room in ROOMS:
        name, enabled, profile, deck = room[0], room[1], room[2], room[3]
        if not enabled:
            unreal.log("DEPTH {} skipped (disabled)".format(name))
            continue

        camera, target = camera_and_target(room)
        floor_z = DECK[deck] - FLOOR_DROP

        # Along the ray in plan only; the height is set independently below.
        override = OVERRIDES.get(name, {})
        height = override.get("height", LIGHT_HEIGHT)

        dx, dy = target.x - camera.x, target.y - camera.y
        location = unreal.Vector(camera.x + dx * RAY_FRACTION,
                                 camera.y + dy * RAY_FRACTION,
                                 floor_z + height)

        colour, key_intensity = PROFILE[profile]
        intensity = round(key_intensity * FILL_RATIO * override.get("intensity_scale", 1.0))

        light = actors.spawn_actor_from_class(unreal.PointLight, location)
        if not light:
            unreal.log_error("DEPTH {} could not spawn".format(name))
            continue

        light.tags = [TAG, name]
        component = light.point_light_component
        component.set_editor_property("intensity", intensity)
        component.set_light_color(colour)
        component.set_editor_property("attenuation_radius", RADIUS)
        component.set_editor_property("source_radius", 70.0)
        component.set_editor_property("cast_shadows", True)
        component.set_mobility(unreal.ComponentMobility.MOVABLE)

        # Read back rather than trust the write, as everywhere else in this project since an
        # emissive scalar was set, ignored, and reported as a success.
        unreal.log("DEPTH {:<16} at {:.0f},{:.0f},{:.0f}  I={:.0f} (key {:.0f})  R={:.0f}".format(
            name, location.x, location.y, location.z,
            component.get_editor_property("intensity"), key_intensity,
            component.get_editor_property("attenuation_radius")))
        placed += 1

    unreal.EditorLoadingAndSavingUtils.save_map(
        unreal.EditorLevelLibrary.get_editor_world(), MAP)
    unreal.log("DEPTH placed {} light(s), map saved".format(placed))


main()
