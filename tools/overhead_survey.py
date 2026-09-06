"""Overhead stills of every room on the corvette, deck by deck, for a placement review.

For each deck everything above the deck's ceiling line is hidden in the editor viewport, the
ceiling slabs and the deck's own pipe runs with it, and the viewport camera looks straight down
on the whole deck and then on each room: main, second, service, corridor and trunk. One PNG per
view under Saved/Screenshots/WindowsEditor/Overhead_D<deck>_<room>.png. Run in the windowed
editor (the stills need a renderer):

    UnrealEditor.exe <project> -ExecCmds="py tools/overhead_survey.py" -WINDOWED -ResX=1920 -ResY=1080

The script steps through the views on editor ticks and quits the editor when the last still is
requested. What to look for in the pictures: props through walls or through each other, props
away from the wall they should stand against, and props at angles the room does not explain.
"""
import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_Corvette_ThrustStack"
DECK_PITCH = 430.0
DECKS = 11
FOOT = (0.0, 2400.0, 0.0, 1800.0)
ROOMS = {
    "Deck": (0.0, 2400.0, 0.0, 1800.0),
    "Main": (0.0, 1500.0, 1000.0, 1800.0),
    "Second": (1500.0, 2400.0, 1000.0, 1800.0),
    "Service": (1400.0, 2400.0, 0.0, 600.0),
    "Corridor": (0.0, 2400.0, 600.0, 1000.0),
    "Trunk": (0.0, 1400.0, 0.0, 600.0),
}
SETTLE_TICKS = 6

unreal.EditorLoadingAndSavingUtils.load_map(MAP)
# Lit, and fully: the ship is dark by design, so the review floods it. Every light aboard is
# switched on and turned up, and a sun straight down with a strong sky fills the rest. Nothing
# is saved: the map is left as it was loaded.
unreal.SystemLibrary.execute_console_command(None, "viewmode lit")
unreal.SystemLibrary.execute_console_command(None, "r.EyeAdaptation.ExposureOverride 1.0")
_actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for _a in unreal.EditorLevelLibrary.get_all_level_actors():
    for _c in _a.get_components_by_class(unreal.LightComponent):
        _c.set_visibility(True)
        if isinstance(_c, unreal.PointLightComponent):
            # One flat, even level everywhere: the review wants every room the same brightness.
            _c.set_editor_property("use_inverse_squared_falloff", False)
            _c.set_editor_property("light_falloff_exponent", 1.5)
            _c.set_intensity(18.0)
            _c.set_editor_property("attenuation_radius", max(_c.get_editor_property("attenuation_radius"), 900.0))
    if isinstance(_a, unreal.PostProcessVolume):
        _s = _a.get_editor_property("settings")
        _s.set_editor_property("override_auto_exposure_min_brightness", True); _s.set_editor_property("auto_exposure_min_brightness", 1.0)
        _s.set_editor_property("override_auto_exposure_max_brightness", True); _s.set_editor_property("auto_exposure_max_brightness", 1.0)
        _s.set_editor_property("override_auto_exposure_bias", True); _s.set_editor_property("auto_exposure_bias", 0.0)
        _a.set_editor_property("settings", _s)
_sun = _actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 6000), unreal.Rotator(pitch=-89.0, yaw=0.0, roll=0.0))
_sun.get_component_by_class(unreal.DirectionalLightComponent).set_intensity(6.0)
_sky = _actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(1200, 900, 6000), unreal.Rotator())
_sky.get_component_by_class(unreal.SkyLightComponent).set_intensity(3.0)
level = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Bounds of the rack and locker candidates, for the placement work that follows the review.
for path in ["/Game/Assets/Ships/Production/Meshes/SM_Prop_Locker", "/Game/Assets/Gameplay/SalvageBatch03/Meshes/SM_SalvageToolRack",
             "/Game/ModSci_EngiProps/Meshes/SM_WallBracket_A", "/Game/SciFiRoomsCorridors/Meshes/SM_Shelf02", "/Game/SciFiRoomsCorridors/Meshes/SM_Shelf01"]:
    m = unreal.load_asset(path)
    if m:
        b = m.get_bounding_box()
        print(f"OVERHEAD bounds {path.split('/')[-1]}: X {b.min.x:.0f}..{b.max.x:.0f} Y {b.min.y:.0f}..{b.max.y:.0f} Z {b.min.z:.0f}..{b.max.z:.0f}")
    else:
        print(f"OVERHEAD bounds {path.split('/')[-1]}: missing")

views = []
for deck in range(1, DECKS + 1):
    z = (deck - 1) * DECK_PITCH
    for room, (x0, x1, y0, y1) in ROOMS.items():
        w, h = x1 - x0, y1 - y0
        # Height so the room fills the frame at a 90 degree horizontal FOV (16:9 makes the vertical ~59 degrees).
        height = max(w * 0.55, h * 0.95) + 60.0
        views.append((deck, room, z, ((x0 + x1) * 0.5, (y0 + y1) * 0.5, z + height)))

state = {"i": 0, "tick": 0, "deck": None, "handle": None, "taken": set()}


def hide_above(z_deck):
    """Hide everything above this deck's ceiling line, and the deck's own ceiling and pipe runs."""
    ceiling = z_deck + 245.0
    for a in all_actors:
        try:
            loc = a.get_actor_location()
        except Exception:
            continue
        label = a.get_actor_label()
        hide = loc.z > ceiling or "Ceiling" in label or "Pipe" in label or "_Fixture_" in label or "Lamp" in label or "_Hang" in label
        a.set_is_temporarily_hidden_in_editor(hide)
        # Hidden is not enough for the sun: a hidden slab still shadows what is under it.
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            c.set_cast_shadow(not hide)


def tick(delta):
    state["tick"] += 1
    if state["tick"] % SETTLE_TICKS != 0:
        return
    i = state["i"]
    if i >= len(views):
        unreal.unregister_slate_post_tick_callback(state["handle"])
        for a in all_actors:
            try:
                a.set_is_temporarily_hidden_in_editor(False)
            except Exception:
                pass
        print("OVERHEAD done")
        unreal.SystemLibrary.quit_editor()
        return
    deck, room, z, cam = views[i]
    if state["deck"] != deck:
        hide_above(z)
        state["deck"] = deck
        return  # give the hide a frame before the first still of the deck
    level.set_level_viewport_camera_info(unreal.Vector(*cam), unreal.Rotator(pitch=-90.0, yaw=0.0, roll=0.0))
    name = f"Overhead_D{deck:02d}_{room}"
    if name in state["taken"]:
        state["i"] = i + 1
        return
    state["taken"].add(name)
    unreal.AutomationLibrary.take_high_res_screenshot(1920, 1080, name)
    print(f"OVERHEAD D{deck:02d} {room} from {cam[2] - z:.0f} above the deck")
    state["i"] = i + 1


state["handle"] = unreal.register_slate_post_tick_callback(tick)
