"""Build and capture the current Unreal-native Ginnos proof system."""

import os
import unreal


MAP = "/Game/Assets/Maps/SpaceSystems/L_Ginnos_UnrealNativeProof"
OUTPUT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "Art", "GalaxyMap", "Unreal", "Ginnos_UnrealNative_Current.png")
)

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
unreal.EditorLevelLibrary.load_level(MAP)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

system_actor = next(
    actor for actor in actors.get_all_level_actors() if actor.get_actor_label() == "Ginnos Procedural System"
)
system_actor.set_editor_property("visual_quality_tier", unreal.SystemVisualQualityTier.CINEMATIC)
system_actor.set_editor_property("landmark_spawn_chance", 1.0)

system_data = unreal.StarSystemData()
system_data.set_editor_property("display_name", "Ginnos")
system_data.set_editor_property("danger_tier", 3)
solar_hazard = unreal.HazardEntry()
solar_hazard.set_editor_property("category", unreal.HazardCategory.SOLAR_RADIATION_STORM)
solar_hazard.set_editor_property("severity", 0.82)
debris_hazard = unreal.HazardEntry()
debris_hazard.set_editor_property("category", unreal.HazardCategory.MICRO_DEBRIS_FIELD)
debris_hazard.set_editor_property("severity", 0.58)
system_data.set_editor_property(
    "hazards",
    [solar_hazard, debris_hazard],
)
system_actor.build_system(system_data, unreal.Vector())

camera_location = unreal.Vector(-900000.0, -4700000.0, 1150000.0)
camera_target = unreal.Vector(250000.0, 250000.0, 100000.0)
camera_rotation = unreal.MathLibrary.find_look_at_rotation(camera_location, camera_target)
camera = actors.spawn_actor_from_class(unreal.CameraActor, camera_location, camera_rotation)
camera.set_actor_label("Ginnos Review Camera Temporary")
camera_component = camera.get_component_by_class(unreal.CameraComponent)
camera_component.set_editor_property("field_of_view", 54.0)

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "r.ScreenPercentage 100")
unreal.SystemLibrary.execute_console_command(world, "r.VolumetricFog 1")
unreal.SystemLibrary.execute_console_command(world, "r.Nanite 1")
unreal.AutomationLibrary.finish_loading_before_screenshot()
unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera_location, camera_rotation)
unreal.EditorLevelLibrary.editor_invalidate_viewports()
task = unreal.AutomationLibrary.take_high_res_screenshot(
    1920, 1080, OUTPUT, camera=camera, delay=2.0, force_game_view=True
)
if not task or not task.is_valid_task():
    raise RuntimeError("Unreal rejected the Ginnos screenshot task")
unreal.log(f"GINNOS_SCREENSHOT_REQUESTED {OUTPUT} LANDMARK={system_actor.get_editor_property('selected_landmark_id')}")
