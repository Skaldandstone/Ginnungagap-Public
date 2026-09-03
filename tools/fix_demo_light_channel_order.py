"""Repairs the demo lights whose colours were written with reversed channels.

tools/build_quick_demo_four_deck_ship.py set room light colours with unreal.Color(...) positionally.
That constructor is (B, G, R, A), not (R, G, B, A), so every colour it wrote came out mirrored:

    asked for (255, 70, 35)   red-orange emergency   got (35, 70, 255)   saturated blue
    asked for (185, 220, 235) cool white utility     got (235, 220, 185) warm cream

The generator is fixed to use set_light_color with a LinearColor, which has no channel-order trap.
This repairs the map that was already built from the broken version, so the level does not have to be
regenerated -- regenerating the whole four-deck ship to correct two colours would discard every
dressing and lighting pass since.

The emergency light is the one that mattered. Measuring the cryo hero shot found a blue population at
RGB (0.044, 0.086, 0.568) -- blue 6.6x green -- lying on the floor rather than on the pods, and this
was the only saturated source in that room. It is set to the amber the corridors already use rather
than back to the original red, because Sheet 11's cryo bay is near-neutral (blue-minus-red +0.009)
and wants a restrained warm accent against its pale key lights, not a saturated wash of any hue.

The utility lights are corrected for consistency. They sit at intensity 0 in the editor and are given
their runtime values by QuickDemoPowerStation, so their stored colour was never visible -- which is
exactly why nobody caught the same bug on them.
"""

import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"

WANTED = {
    "QuickDemoEmergencyLight": unreal.LinearColor(1.0, 0.749, 0.486, 1.0),
    "QuickDemoUtilityLight":   unreal.LinearColor(0.725, 0.863, 0.922, 1.0),
}


def main():
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)

    changed = 0
    for actor in unreal.EditorActorSubsystem().get_all_level_actors():
        if not isinstance(actor, unreal.PointLight):
            continue
        tags = [str(t) for t in actor.tags]
        wanted = next((WANTED[t] for t in tags if t in WANTED), None)
        if wanted is None:
            continue

        component = actor.point_light_component

        # Copy the channels out immediately. get_editor_property hands back a live reference to the
        # struct, not a snapshot, so holding it across the write makes "before" silently become
        # "after" -- which is exactly what the first run of this script printed: 121 lines all
        # claiming no change, on a pass that did change every one of them. Verified afterwards by
        # re-reading the map in a fresh editor.
        was = component.get_editor_property("light_color")
        before = (was.r, was.g, was.b)

        component.set_light_color(wanted)

        now = component.get_editor_property("light_color")
        after = (now.r, now.g, now.b)

        unreal.log("CHANNELFIX {:<28} ({:3.0f},{:3.0f},{:3.0f}) -> ({:3.0f},{:3.0f},{:3.0f}){}".format(
            actor.get_name(), *before, *after, "" if before != after else "   (already correct)"))
        changed += 1

    if not changed:
        unreal.log_error("CHANNELFIX found no tagged lights -- has the tag been renamed?")
        return

    unreal.EditorLoadingAndSavingUtils.save_map(
        unreal.EditorLevelLibrary.get_editor_world(), MAP)
    unreal.log("CHANNELFIX corrected {} light(s), map saved".format(changed))


main()
