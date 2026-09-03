"""Measures every hero-shot room the way the workshop was measured, and says which share its fault.

The workshop's black render turned out to have a specific, measurable cause: its lights and all of
its near geometry sat at the frame *edges* (17-35 degrees off-axis, 374-520 cm out) while the centre
of frame was empty until 7-8 m -- several metres past where the lights had anything left. Adding one
fill light on the camera axis fixed it.

Generalising that fix to the other five rooms is only correct for rooms that actually have the same
problem. A room whose centre is already occupied and lit does not need a third light, and giving it
one is how the workshop's first attempt blew its back wall to flat white. So this measures first.

The verdict is a ratio of computed illuminance, not a distance comparison.

The first version of this compared the on-axis subject's distance from the camera against the
nearest light's distance plus its attenuation radius, and pronounced every room -- the workshop
included -- "already covered". That was worthless twice over. Attenuation radius is where a light
reaches exactly zero, and inverse-square has made it negligible long before then; and camera-to-light
distance says nothing about light-to-subject distance when the light is 32 degrees off to one side,
which is exactly the workshop's geometry. A metric that cannot distinguish the one room whose fault
is known and fixed cannot be trusted on the five that are not.

So this computes, at two points, what the room's lights actually deliver:

    CENTRE = the nearest mesh within 12 degrees of the camera axis -- what the shot is pointed at
    EDGE   = the nearest mesh at any angle -- what the shot already shows

using Unreal's inverse-square falloff with its radius window, summed over every light in the room.
A room whose centre gets a small fraction of what its edge gets is the workshop's fault: a lit frame
with a dark hole in the middle of it. A room where the two are comparable is fine and adding a third
light to it would flatten it, which is what the workshop's own first attempt did to its back wall.

Validated rather than asserted: run with SKIP_DEPTH_LIGHTS=1 to exclude the tagged depth lights and
reproduce the state the workshop was in before it was fixed. If the verdict does not flip between
the two runs, the metric is still not measuring anything and should not be believed.
"""

import os

import math

import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"

# Straight from tools/capture_demo_hero_shots.py so this measures the shots that are actually taken.
EYE = 165.0
DECK = {1: 215.0, 2: 735.0, 3: 1255.0, 4: 1775.0}
FLOOR_DROP = 195.0
DOORWAY_OFFSET = 260.0
LOOK_PAST = 300.0

# (name, deck, room x, room y, fov, cam dx, cam dy, cam h, tgt dx, tgt dy, tgt h)
ROOM_SHOTS = [
    ("01_CryoWake",     3, -6600.0, -680.0, 78.0,    0.0,   0.0,   0.0,    0.0,    0.0,   0.0),
    ("03_EngineRoom",   2, -6600.0, -680.0, 78.0,    0.0,   0.0,   0.0,    0.0,    0.0,   0.0),
    ("04_CIC",          3,  6600.0,  680.0, 74.0, -400.0, 400.0, EYE,    300.0, -300.0, EYE + 35.0),
    ("05_BloomBreach",  3,  5400.0, -680.0, 76.0,    0.0,   0.0,   0.0,    0.0,    0.0,   0.0),
    ("07_Workshop",     3, -5400.0, -680.0, 76.0,    0.0,   0.0,   0.0,    0.0,    0.0,   0.0),
    ("08_PowerControl", 2, -5400.0,  680.0, 76.0,    0.0,   0.0,   0.0,    0.0,    0.0,   0.0),
]

ON_AXIS_DEGREES = 12.0

# Tag written by the depth-light pass. Excluding these reproduces the pre-fix state, which is how
# the metric below gets validated against a room whose answer is already known.
DEPTH_TAG = "RoomDepthLight"
LEGACY_WORKSHOP_TAG = "WorkshopDepthLight"
SKIP_DEPTH_LIGHTS = os.environ.get("SKIP_DEPTH_LIGHTS", "") == "1"

# Below this share of the frame's own edge brightness, the middle of the shot reads as a hole.
# 0.35 is a judgement, and it is stated here rather than buried: it sits well below the ratio a room
# that already works produces, and well above zero, so it is not merely detecting "any light at all".
CENTRE_DEFICIT_RATIO = 0.35


def illuminance(lights, point):
    """What the room's lights deliver at a point, in Unreal's inverse-square falloff.

    Not calibrated to any real unit and it does not need to be -- every use below is a ratio between
    two points lit by the same set of lights, so the constant cancels.
    """
    total = 0.0
    for location, intensity, radius in lights:
        gap = length(delta(location, point))
        if gap >= radius or gap < 1.0:
            continue
        # The radius window Unreal applies on top of 1/d^2, so a light fades to nothing at its
        # attenuation radius instead of being clipped there.
        window = 1.0 - (gap / radius) ** 4
        total += intensity * (window * window) / (gap * gap)
    return total


def at(deck, x, y, height=EYE):
    return unreal.Vector(x, y, DECK[deck] - FLOOR_DROP + height)


def camera_and_target(shot):
    (_, deck, room_x, room_y, _, cam_dx, cam_dy, cam_h, tgt_dx, tgt_dy, tgt_h) = shot
    if cam_dx or cam_dy or tgt_dx or tgt_dy:
        return at(deck, room_x + cam_dx, room_y + cam_dy, cam_h), \
               at(deck, room_x + tgt_dx, room_y + tgt_dy, tgt_h)
    side = 1.0 if room_y > 0.0 else -1.0
    return at(deck, room_x, side * DOORWAY_OFFSET), \
           at(deck, room_x, room_y + side * LOOK_PAST, EYE - 45.0)


def length(v):
    return math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)


def delta(a, b):
    return unreal.Vector(b.x - a.x, b.y - a.y, b.z - a.z)


def survey(shot, actors):
    name, deck, room_x, room_y = shot[0], shot[1], shot[2], shot[3]
    camera, target = camera_and_target(shot)
    forward = delta(camera, target)
    forward_length = length(forward)
    floor_z = DECK[deck] - FLOOR_DROP

    lights = []
    on_axis_gap = None
    on_axis_point = None
    nearest_any = None
    nearest_any_point = None

    for actor in actors:
        location = actor.get_actor_location()

        # Same room, same deck. Rooms are 1360 apart across the centreline and decks 520 apart.
        if abs(location.x - room_x) > 900.0 or abs(location.y - room_y) > 900.0:
            continue
        if abs(location.z - floor_z) > 500.0:
            continue

        if isinstance(actor, unreal.PointLight):
            tags = [str(t) for t in actor.tags]
            if SKIP_DEPTH_LIGHTS and (DEPTH_TAG in tags or LEGACY_WORKSHOP_TAG in tags):
                continue
            component = actor.point_light_component
            intensity = component.get_editor_property("intensity")
            if intensity <= 1.0:
                # The identity lights sit at 0 in the editor; they are set at runtime only, so they
                # contribute nothing to a hero shot and must not be counted here.
                continue
            lights.append((location, intensity,
                           component.get_editor_property("attenuation_radius")))
            continue

        if not isinstance(actor, unreal.StaticMeshActor):
            continue
        component = actor.static_mesh_component
        if not component or not component.get_editor_property("static_mesh"):
            continue

        to_actor = delta(camera, location)
        gap = length(to_actor)
        if gap < 1.0:
            continue
        cosine = (to_actor.x * forward.x + to_actor.y * forward.y + to_actor.z * forward.z) \
            / (gap * forward_length)
        angle = math.degrees(math.acos(min(1.0, max(-1.0, cosine))))

        if nearest_any is None or gap < nearest_any:
            nearest_any = gap
            nearest_any_point = location
        if angle <= ON_AXIS_DEGREES and (on_axis_gap is None or gap < on_axis_gap):
            on_axis_gap = gap
            on_axis_point = location

    unreal.log("ROOM {}{}".format(name, "  [depth lights excluded]" if SKIP_DEPTH_LIGHTS else ""))
    unreal.log("ROOM   lights contributing: {}".format(len(lights)))

    if not lights:
        unreal.log("ROOM   VERDICT: no lit sources at all -- a depth light is not the whole answer")
        return
    if on_axis_point is None:
        unreal.log("ROOM   VERDICT: NEEDS DEPTH LIGHT (nothing within {:.0f} deg of axis)".format(
            ON_AXIS_DEGREES))
        return

    centre = illuminance(lights, on_axis_point)
    edge = illuminance(lights, nearest_any_point)
    ratio = (centre / edge) if edge > 0.0 else 0.0

    unreal.log("ROOM   centre subject at {:.0f}cm  illum {:.3f}".format(on_axis_gap, centre))
    unreal.log("ROOM   edge   subject at {:.0f}cm  illum {:.3f}".format(nearest_any, edge))
    unreal.log("ROOM   centre/edge ratio {:.3f}".format(ratio))

    if ratio < CENTRE_DEFICIT_RATIO:
        unreal.log("ROOM   VERDICT: NEEDS DEPTH LIGHT (centre gets {:.0f}% of what the edge gets)".format(
            ratio * 100.0))
    else:
        unreal.log("ROOM   VERDICT: already covered (centre gets {:.0f}% of the edge)".format(
            ratio * 100.0))


unreal.EditorLoadingAndSavingUtils.load_map(MAP)
actors = unreal.EditorActorSubsystem().get_all_level_actors()
for shot in ROOM_SHOTS:
    survey(shot, actors)
unreal.log("ROOM survey complete")
