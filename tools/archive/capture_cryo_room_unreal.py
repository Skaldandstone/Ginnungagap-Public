"""Capture an actual Unreal-rendered review image of the CRYO-01 room."""
import os
import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_CryoPod_Modeling_V2"
OUTPUT = os.path.abspath(os.path.join(unreal.Paths.project_dir(), "Art", "ShipRooms", "CryoPod_Unreal_V2.png"))

unreal.EditorLevelLibrary.load_level(MAP)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

# Keep the capture focused on the assembled runtime master, not the exploded edit copies.
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith("CRYO01_Edit_") or label == "CRYO01_HumanScale_180cm":
        actor.set_is_temporarily_hidden_in_editor(True)
    if label == "CRYO01_Modeling_Key":
        actor.get_component_by_class(unreal.RectLightComponent).set_editor_property("intensity", 2600.0)
    elif label == "CRYO01_Modeling_Fill":
        actor.get_component_by_class(unreal.RectLightComponent).set_editor_property("intensity", 1400.0)

# A neutral camera-side fill keeps the dark lower shell readable without flattening
# the warm/cool modeling lights already authored into the review map.
fill = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(-230.0, -260.0, 170.0), unreal.Rotator())
fill.set_actor_label("CRYO01_RenderFill_Temporary")
fill_component = fill.get_component_by_class(unreal.PointLightComponent)
fill_component.set_editor_property("intensity", 1100.0)
fill_component.set_editor_property("attenuation_radius", 650.0)
fill_component.set_editor_property("light_color", unreal.Color(190, 215, 255, 255))

camera_location = unreal.Vector(-360.0, -350.0, 225.0)
camera_target = unreal.Vector(0.0, 0.0, 82.0)
camera_rotation = unreal.MathLibrary.find_look_at_rotation(camera_location, camera_target)
camera = actors.spawn_actor_from_class(unreal.CameraActor, camera_location, camera_rotation)
camera.set_actor_label("CRYO01_RenderCamera_Temporary")
camera_component = camera.get_component_by_class(unreal.CameraComponent)
camera_component.set_editor_property("field_of_view", 62.0)
camera_component.set_editor_property("post_process_blend_weight", 1.0)
post_process = camera_component.get_editor_property("post_process_settings")
post_process.set_editor_property("override_auto_exposure_bias", True)
post_process.set_editor_property("auto_exposure_bias", 1.25)
camera_component.set_editor_property("post_process_settings", post_process)

unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera_location, camera_rotation)
unreal.EditorLevelLibrary.editor_invalidate_viewports()
command = f'HighResShot 1600x900 filename="{OUTPUT.replace(chr(92), "/")}"'
unreal.SystemLibrary.execute_console_command(world, command)
unreal.log(f"CRYO-SCREENSHOT REQUESTED: {OUTPUT}")
