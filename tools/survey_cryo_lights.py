"""Lists every light in the cryo bay, with colour, so the blue can be attributed to a source.

The hero shot's blue population measures RGB (0.044, 0.086, 0.568) -- blue 6.6x green. The room's
own profile light is (0.72, 0.86, 1.0), a pale blue-white that cannot produce that ratio, and the
lid glass diffuse is (0.0495, 0.171, 0.216), a cyan whose green and blue sit close together. Neither
explains it, and the offending pixels are on the floor rather than on the pods.

So something else in that room is emitting saturated blue. This prints the candidates.
"""

import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
DECK_Z = 1255.0 - 195.0          # deck 3 floor
ROOM_X, ROOM_Y = -6600.0, -680.0
REACH = 800.0

unreal.EditorLoadingAndSavingUtils.load_map(MAP)

rows = []
for actor in unreal.EditorActorSubsystem().get_all_level_actors():
    loc = actor.get_actor_location()
    if abs(loc.x - ROOM_X) > REACH or abs(loc.y - ROOM_Y) > REACH:
        continue
    if abs(loc.z - DECK_Z) > 500.0:
        continue

    comp = None
    if isinstance(actor, unreal.PointLight):
        comp = actor.point_light_component
    elif isinstance(actor, unreal.SpotLight):
        comp = actor.spot_light_component
    elif isinstance(actor, unreal.RectLight):
        comp = actor.rect_light_component
    if not comp:
        continue

    c = comp.get_editor_property("light_color")
    r, g, b = c.r / 255.0, c.g / 255.0, c.b / 255.0
    rows.append((
        comp.get_editor_property("intensity"),
        actor.get_name(), loc, r, g, b,
        comp.get_editor_property("attenuation_radius"),
        [str(t) for t in actor.tags],
    ))

unreal.log("CRYOLIGHT {} light(s) in the cryo bay".format(len(rows)))
for intensity, name, loc, r, g, b, radius, tags in sorted(rows, reverse=True):
    ratio = b / g if g > 1e-6 else float("inf")
    unreal.log("CRYOLIGHT I={:7.0f} R={:5.0f}  rgb=({:.3f},{:.3f},{:.3f})  b/g={:5.2f}  "
               "at {:.0f},{:.0f},{:.0f}  {}  tags={}".format(
                   intensity, radius, r, g, b, ratio, loc.x, loc.y, loc.z, name, tags))

unreal.log("CRYOLIGHT done")
