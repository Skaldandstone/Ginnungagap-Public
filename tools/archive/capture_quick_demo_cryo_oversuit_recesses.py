"""Capture the four seeded oversuit recesses in the Quick Demo cryo room."""

from __future__ import annotations

from pathlib import Path

import unreal


MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
OUTPUT_DIR = (Path(unreal.SystemLibrary.get_project_saved_directory()) /
              "RoomReviews/QuickDemoFourDeck").resolve()
OUTPUT_NAME = "QuickDemo_CryoOversuitRecesses"
OUTPUT = OUTPUT_DIR / f"{OUTPUT_NAME}.png"
PREFIX = "QuickDemo4D_"


levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")
unreal.AutomationLibrary.finish_loading_before_screenshot()
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors = actors_api.get_all_level_actors()
stations = sorted(
    [actor for actor in actors if actor.get_actor_label().startswith(PREFIX + "SuitStation_")],
    key=lambda actor: actor.get_actor_label(),
)
if len(stations) != 4:
    raise RuntimeError(f"Expected four suit stations, found {len(stations)}")

center_x = sum(actor.get_actor_location().x for actor in stations) / len(stations)
center_y = sum(actor.get_actor_location().y for actor in stations) / len(stations)
center_z = sum(actor.get_actor_location().z for actor in stations) / len(stations) + 102.0
target = unreal.Vector(center_x, center_y, center_z)

for actor in actors:
    label = actor.get_actor_label()
    # Open only the review sightline into the cryo room; the saved map is not
    # modified because these are transient hidden-in-game flags.
    is_near_cryo = abs(actor.get_actor_location().x - center_x) < 520.0
    if label.startswith(PREFIX + "Ceiling_") or (
        is_near_cryo and (
            label.startswith(PREFIX + "InnerWall_") or
            label.startswith(PREFIX + "Door_") or
            label.startswith(PREFIX + "ConceptCorridorRib_")
        )
    ):
        actor.set_actor_hidden_in_game(True)

for index, station in enumerate(stations, start=1):
    location = station.get_actor_location() + unreal.Vector(0.0, 115.0, 105.0)
    light = actors_api.spawn_actor_from_class(
        unreal.RectLight, location, unreal.MathLibrary.find_look_at_rotation(location, station.get_actor_location()))
    light.set_actor_label(f"QuickDemoRecessReviewLight_{index:02d}")
    component = light.rect_light_component
    component.set_editor_property("intensity", 24.0)
    component.set_editor_property("source_width", 105.0)
    component.set_editor_property("source_height", 210.0)
    component.set_editor_property("light_color", unreal.Color(205, 224, 238))

camera_location = unreal.Vector(center_x, center_y + 620.0, center_z + 4.0)
camera = actors_api.spawn_actor_from_class(
    unreal.SceneCapture2D, camera_location,
    unreal.MathLibrary.find_look_at_rotation(camera_location, target))
camera.set_actor_label("QuickDemoReviewCamera_CryoOversuitRecesses")
component = camera.capture_component2d
component.capture_every_frame = False
component.capture_on_movement = False
component.fov_angle = 74.0
component.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
texture = unreal.RenderingLibrary.create_render_target2d(
    world, 1800, 1100, unreal.TextureRenderTargetFormat.RTF_RGBA8,
    unreal.LinearColor(0.008, 0.01, 0.015, 1.0),
)
texture.set_editor_property("target_gamma", 2.2)
component.texture_target = texture
settings = component.post_process_settings
settings.set_editor_property("override_auto_exposure_method", True)
settings.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
settings.set_editor_property("override_camera_iso", True)
settings.set_editor_property("camera_iso", 100.0)
settings.set_editor_property("override_camera_shutter_speed", True)
settings.set_editor_property("camera_shutter_speed", 125.0)
settings.set_editor_property("override_auto_exposure_bias", True)
settings.set_editor_property("auto_exposure_bias", -0.5)
component.post_process_settings = settings

for command in (
    "viewmode lit", "ShowFlag.Grid 0", "ShowFlag.Sprites 0",
    "ShowFlag.SelectionOutline 0", "ShowFlag.CompositeEditorPrimitives 0",
):
    unreal.SystemLibrary.execute_console_command(world, command)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
component.capture_scene()
component.capture_scene()
unreal.RenderingLibrary.export_render_target(
    world, texture, str(OUTPUT_DIR), f"{OUTPUT_NAME}.png")
if not OUTPUT.exists() or OUTPUT.stat().st_size < 10000:
    raise RuntimeError(f"Cryo oversuit recess capture missing or invalid: {OUTPUT}")
unreal.log(f"QUICK DEMO CRYO OVERSUIT RECESS CAPTURE: {OUTPUT}")
