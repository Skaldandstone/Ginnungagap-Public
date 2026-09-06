"""Overhead plans of every room on the corvette, deck by deck, for a placement review.

A top-down orthographic scene capture, lit and flooded (every light aboard on and evened out,
a sun straight down, exposure pinned), with everything above the deck's ceiling line and the
deck's own ceiling and pipe runs left out of the picture. One PNG per view under
Saved/Screenshots/Overhead/Overhead_D<deck>_<room>.png: the whole deck, then main, second,
service, corridor and trunk. Run in the windowed editor (the captures need a renderer):

    UnrealEditor.exe <project> -ExecCmds="py <abs path>/tools/overhead_survey.py" -WINDOWED -ResX=1920 -ResY=1080

Nothing is saved: the lights and the capture rig are changed in memory and the editor quits.
What to look for: props through walls or through each other, props away from the wall they
should stand against, and props at angles the room does not explain.
"""
import os
import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_Corvette_ThrustStack"
DECK_PITCH = 430.0
DECKS = 11
ROOMS = {
    "Deck": (0.0, 2400.0, 0.0, 1800.0),
    "Main": (0.0, 1500.0, 1000.0, 1800.0),
    "Second": (1500.0, 2400.0, 1000.0, 1800.0),
    "Service": (1400.0, 2400.0, 0.0, 600.0),
    "Corridor": (0.0, 2400.0, 600.0, 1000.0),
    "Trunk": (0.0, 1400.0, 0.0, 600.0),
}
OUT_DIR = os.path.join(unreal.SystemLibrary.get_project_saved_directory(), "Screenshots", "Overhead")
SETTLE_TICKS = 4
SIZE = 2048

unreal.EditorLoadingAndSavingUtils.load_map(MAP)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

# Flood the ship: every point light on, one flat level, exposure pinned, a sun overhead.
for a in all_actors:
    for c in a.get_components_by_class(unreal.LightComponent):
        c.set_visibility(True)
        if isinstance(c, unreal.PointLightComponent):
            c.set_editor_property("use_inverse_squared_falloff", False)
            c.set_editor_property("light_falloff_exponent", 1.5)
            c.set_intensity(14.0)
            c.set_editor_property("attenuation_radius", max(c.get_editor_property("attenuation_radius"), 900.0))
    if isinstance(a, unreal.PostProcessVolume):
        s = a.get_editor_property("settings")
        s.set_editor_property("override_auto_exposure_min_brightness", True); s.set_editor_property("auto_exposure_min_brightness", 1.0)
        s.set_editor_property("override_auto_exposure_max_brightness", True); s.set_editor_property("auto_exposure_max_brightness", 1.0)
        s.set_editor_property("override_auto_exposure_bias", True); s.set_editor_property("auto_exposure_bias", 0.0)
        a.set_editor_property("settings", s)
sun = actor_sub.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 8000), unreal.Rotator(pitch=-89.0, yaw=30.0, roll=0.0))
sun.get_component_by_class(unreal.DirectionalLightComponent).set_intensity(5.0)
sky = actor_sub.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(1200, 900, 8000), unreal.Rotator())
sky.get_component_by_class(unreal.SkyLightComponent).set_intensity(2.0)

# Bounds of the rack and locker candidates, for the placement work that follows the review.
for path in ["/Game/Assets/Ships/Production/Meshes/SM_Prop_Locker", "/Game/Assets/Gameplay/SalvageBatch03/Meshes/SM_SalvageToolRack",
             "/Game/SciFiRoomsCorridors/Meshes/SM_Shelf02", "/Game/SciFiRoomsCorridors/Meshes/SM_Shelf01"]:
    m = unreal.load_asset(path)
    if m:
        b = m.get_bounding_box()
        print(f"OVERHEAD bounds {path.split('/')[-1]}: X {b.min.x:.0f}..{b.max.x:.0f} Y {b.min.y:.0f}..{b.max.y:.0f} Z {b.min.z:.0f}..{b.max.z:.0f}")

# The capture rig.
rig = actor_sub.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(0, 0, 0), unreal.Rotator(pitch=-90.0, yaw=0.0, roll=0.0))
cap = rig.get_component_by_class(unreal.SceneCaptureComponent2D)
rt = unreal.RenderingLibrary.create_render_target2d(world, SIZE, SIZE, unreal.TextureRenderTargetFormat.RTF_RGBA8)
cap.set_editor_property("texture_target", rt)
cap.set_editor_property("projection_type", unreal.CameraProjectionMode.ORTHOGRAPHIC)
cap.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
cap.set_editor_property("capture_every_frame", False)
cap.set_editor_property("capture_on_movement", False)
os.makedirs(OUT_DIR, exist_ok=True)

views = []
for deck in range(1, DECKS + 1):
    z = (deck - 1) * DECK_PITCH
    for room, (x0, x1, y0, y1) in ROOMS.items():
        views.append((deck, room, z, ((x0 + x1) * 0.5, (y0 + y1) * 0.5), max(x1 - x0, y1 - y0) + 80.0))

state = {"i": 0, "tick": 0, "deck": None, "handle": None, "pending": None}


def above(z_deck):
    """Everything above this deck's ceiling line, plus its ceiling slabs, pipe runs and lamps."""
    ceiling = z_deck + 245.0
    out = []
    for a in all_actors:
        try:
            loc = a.get_actor_location()
        except Exception:
            continue
        label = a.get_actor_label()
        if loc.z > ceiling or "Ceiling" in label or "Pipe" in label or "_Fixture_" in label or "Lamp" in label or "_Hang" in label or "NavMesh" in label:
            out.append(a)
    return out


def tick(delta):
    try:
        step()
    except Exception as e:
        print(f"OVERHEAD failed: {e}")
        unreal.unregister_slate_post_tick_callback(state["handle"])
        unreal.SystemLibrary.quit_editor()


def step():
    state["tick"] += 1
    if state["tick"] % SETTLE_TICKS != 0:
        return
    if state["pending"]:
        name = state["pending"]
        unreal.RenderingLibrary.export_render_target(world, rt, OUT_DIR, name + ".png")
        print(f"OVERHEAD wrote {name}")
        state["pending"] = None
        return
    i = state["i"]
    if i >= len(views):
        unreal.unregister_slate_post_tick_callback(state["handle"])
        print("OVERHEAD done")
        unreal.SystemLibrary.quit_editor()
        return
    deck, room, z, (cx, cy), width = views[i]
    if state["deck"] != deck:
        cap.clear_hidden_components()
        for a in above(z):
            cap.hide_actor_components(a, True)
        state["deck"] = deck
    rig.set_actor_location(unreal.Vector(cx, cy, z + 2400.0), False, False)
    rig.set_actor_rotation(unreal.Rotator(pitch=-90.0, yaw=0.0, roll=0.0), False)
    cap.set_editor_property("ortho_width", width)
    cap.capture_scene()
    state["pending"] = f"Overhead_D{deck:02d}_{room}"
    state["i"] = i + 1


state["handle"] = unreal.register_slate_post_tick_callback(tick)
