"""Measures everything lighting-related in and around the Player Workshop.

Written before changing anything, because this room has now had several passes aimed at it and the
useful lesson of the last one was that a render is a slow and ambiguous way to answer a question the
map can answer directly.

What the render shows: two blown vertical fixtures near the left and right frame edges and near
black everywhere else. What that image cannot tell us is which of these is true --

  1. the room's point lights are not in the map at all (a dressing pass dropped them),
  2. they are there but weak, or radius-limited, so nothing they should reach is reached,
  3. they are there and fine, and the fixture emissive is so much brighter that auto-exposure
     stops down until everything that is not a fixture is black,
  4. the room is simply bigger than the lights, and the camera looks at a far wall nothing lights.

Those want four different fixes, and guessing between them is what the previous attempts did.

Prints a table rather than judging. The one thing it does assert is the arithmetic that matters:
distance from the hero camera to each light, and to the far wall behind the subject.
"""

import math

import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"

# Straight from tools/capture_demo_hero_shots.py, so this measures the shot that is actually taken.
EYE = 165.0
DECK = {1: 215.0, 2: 735.0, 3: 1255.0, 4: 1775.0}
FLOOR_DROP = 195.0
DOORWAY_OFFSET = 260.0
LOOK_PAST = 300.0

DECK_NUMBER = 3
ROOM_X, ROOM_Y = -5400.0, -680.0

FLOOR_Z = DECK[DECK_NUMBER] - FLOOR_DROP
SIDE = 1.0 if ROOM_Y > 0.0 else -1.0
CAMERA = unreal.Vector(ROOM_X, SIDE * DOORWAY_OFFSET, FLOOR_Z + EYE)
TARGET = unreal.Vector(ROOM_X, ROOM_Y + SIDE * LOOK_PAST, FLOOR_Z + EYE - 45.0)

# Generous enough to catch anything that could plausibly light this room, including fixtures that
# belong to the corridor outside its door.
REACH = 1600.0


def near(location):
    return (abs(location.x - ROOM_X) < REACH
            and abs(location.y - ROOM_Y) < REACH
            and abs(location.z - FLOOR_Z) < 900.0)


def distance(a, b):
    return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2 + (a.z - b.z) ** 2)


unreal.EditorLoadingAndSavingUtils.load_map(MAP)
actors = unreal.EditorActorSubsystem().get_all_level_actors()

unreal.log("WS camera {:.0f},{:.0f},{:.0f} -> target {:.0f},{:.0f},{:.0f}".format(
    CAMERA.x, CAMERA.y, CAMERA.z, TARGET.x, TARGET.y, TARGET.z))

lights = []
meshes = []

for actor in actors:
    location = actor.get_actor_location()
    if not near(location):
        continue

    component = None
    if isinstance(actor, unreal.PointLight):
        component = actor.point_light_component
    elif isinstance(actor, unreal.SpotLight):
        component = actor.spot_light_component
    elif isinstance(actor, unreal.RectLight):
        component = actor.rect_light_component

    if component:
        try:
            intensity = component.get_editor_property("intensity")
            radius = component.get_editor_property("attenuation_radius")
            colour = component.get_editor_property("light_color")
        except Exception as error:
            unreal.log_warning("WS light {} unreadable: {}".format(actor.get_name(), error))
            continue

        gap = distance(CAMERA, location)
        lights.append((gap, actor.get_name(), location, intensity, radius, colour))
        continue

    if isinstance(actor, unreal.StaticMeshActor):
        mesh_component = actor.static_mesh_component
        mesh = mesh_component.get_editor_property("static_mesh") if mesh_component else None
        if not mesh:
            continue
        name = mesh.get_name()
        # Only the things that could be emitting light or blocking it.
        if "LAMP" in name.upper() or "LIGHT" in name.upper():
            overrides = mesh_component.get_editor_property("override_materials")
            slot_one = None
            if overrides and len(overrides) > 1 and overrides[1]:
                slot_one = overrides[1].get_name()
            meshes.append((distance(CAMERA, location), actor.get_name(), name,
                           location, slot_one))

unreal.log("WS ---- lights within {:.0f} of room centre ----".format(REACH))
for gap, name, location, intensity, radius, colour in sorted(lights):
    reaches_target = distance(location, TARGET) <= radius
    unreal.log("WS   {:7.0f}cm  {:<28} at {:.0f},{:.0f},{:.0f}  I={:.0f}  R={:.0f}  "
               "rgb=({:.2f},{:.2f},{:.2f})  reaches target: {}".format(
                   gap, name, location.x, location.y, location.z,
                   intensity, radius, colour.r, colour.g, colour.b,
                   "YES" if reaches_target else "NO"))
if not lights:
    unreal.log_error("WS   none -- the room has no lights at all")

unreal.log("WS ---- lamp meshes ----")
for gap, name, mesh_name, location, slot_one in sorted(meshes):
    unreal.log("WS   {:7.0f}cm  {:<28} mesh={:<18} slot1={}".format(
        gap, name, mesh_name, slot_one if slot_one else "NOT OVERRIDDEN"))
if not meshes:
    unreal.log("WS   none")

unreal.log("WS camera to target: {:.0f}cm".format(distance(CAMERA, TARGET)))

# What is actually in shot.
#
# The first version of this survey filtered meshes down to things with LAMP or LIGHT in the name,
# which answered "what is emitting" and left the more basic question unasked: is there anything in
# front of the lens at all? A correctly lit room containing nothing renders exactly as black as an
# unlit one, and the two want opposite fixes.
#
# Cone test rather than a box: everything within the horizontal field of view, ordered by distance,
# so the list reads as "what the camera sees first".
FOV = 76.0
HALF_FOV = math.radians(FOV * 0.5)

forward = unreal.Vector(TARGET.x - CAMERA.x, TARGET.y - CAMERA.y, TARGET.z - CAMERA.z)
forward_length = math.sqrt(forward.x ** 2 + forward.y ** 2 + forward.z ** 2)

in_shot = []
for actor in actors:
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    component = actor.static_mesh_component
    mesh = component.get_editor_property("static_mesh") if component else None
    if not mesh:
        continue

    location = actor.get_actor_location()
    to_actor = unreal.Vector(location.x - CAMERA.x, location.y - CAMERA.y, location.z - CAMERA.z)
    gap = math.sqrt(to_actor.x ** 2 + to_actor.y ** 2 + to_actor.z ** 2)
    if gap < 1.0 or gap > 1800.0:
        continue

    dot = (to_actor.x * forward.x + to_actor.y * forward.y + to_actor.z * forward.z)
    cosine = dot / (gap * forward_length)
    if cosine < math.cos(HALF_FOV):
        continue

    in_shot.append((gap, mesh.get_name(), math.degrees(math.acos(min(1.0, max(-1.0, cosine))))))

unreal.log("WS ---- meshes inside the {:.0f} degree cone, nearest first ----".format(FOV))
for gap, mesh_name, angle in sorted(in_shot)[:25]:
    unreal.log("WS   {:7.0f}cm  {:5.1f} off-axis  {}".format(gap, angle, mesh_name))
unreal.log("WS {} meshes in shot within 18m".format(len(in_shot)))

unreal.log("WS survey complete")
