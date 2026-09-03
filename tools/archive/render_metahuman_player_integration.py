"""Render the integrated Face01 player without pressure-suit layers."""

import os
from pathlib import Path

import unreal


output_dir = Path(unreal.Paths.project_saved_dir()) / "Renders" / "CharacterCreator"
output_dir.mkdir(parents=True, exist_ok=True)
spawned = []

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
origin = unreal.Vector(0.0, 0.0, -120000.0)

character = actors.spawn_actor_from_class(
    unreal.CoopSurvivalCharacter, origin, unreal.Rotator()
)
spawned.append(character)
character.set_actor_enable_collision(False)
character.set_character_creator_preview_mode(True)
profile = unreal.CharacterProfile()
profile.face_preset = unreal.CharacterFacePreset.FACE01
profile.hair_style = unreal.CharacterHairStyle.SHORT
profile.body_preset = unreal.CharacterBodyPreset.AVERAGE
character.apply_character_identity(profile)

backdrop_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane.Plane")
backdrop_material = unreal.EditorAssetLibrary.load_asset(
    "/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial"
)
backdrop = actors.spawn_actor_from_class(
    unreal.StaticMeshActor, origin + unreal.Vector(-115.0, 0.0, 105.0),
    unreal.Rotator(pitch=90.0, yaw=0.0, roll=0.0)
)
spawned.append(backdrop)
backdrop.static_mesh_component.set_static_mesh(backdrop_mesh)
backdrop.static_mesh_component.set_material(0, backdrop_material)
backdrop.set_actor_scale3d(unreal.Vector(5.0, 5.0, 5.0))

directional = actors.spawn_actor_from_class(
    unreal.DirectionalLight, origin + unreal.Vector(0.0, 0.0, 300.0), unreal.Rotator(-30.0, 160.0, -15.0)
)
spawned.append(directional)
directional.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property("intensity", 0.8)

sky = actors.spawn_actor_from_class(unreal.SkyLight, origin + unreal.Vector(0.0, 0.0, 250.0), unreal.Rotator())
spawned.append(sky)
sky.get_component_by_class(unreal.SkyLightComponent).set_editor_property("intensity", 0.3)

for location, intensity, color in (
    (unreal.Vector(200.0, -120.0, 165.0), 170.0, unreal.Color(219, 240, 255, 255)),
    (unreal.Vector(80.0, 150.0, 135.0), 80.0, unreal.Color(77, 133, 255, 255)),
):
    light = actors.spawn_actor_from_class(unreal.PointLight, origin + location, unreal.Rotator())
    spawned.append(light)
    point = light.get_component_by_class(unreal.PointLightComponent)
    point.set_editor_property("intensity", intensity)
    point.set_editor_property("attenuation_radius", 500.0)
    point.set_editor_property("light_color", color)

camera_location = origin + unreal.Vector(235.0, 0.0, 95.0)
target_location = origin + unreal.Vector(0.0, 0.0, 70.0)
camera_rotation = unreal.MathLibrary.find_look_at_rotation(camera_location, target_location)
capture = actors.spawn_actor_from_class(unreal.SceneCapture2D, camera_location, camera_rotation)
spawned.append(capture)
render_target = unreal.RenderingLibrary.create_render_target2d(
    world, 900, 1200, unreal.TextureRenderTargetFormat.RTF_RGBA8,
    unreal.LinearColor(0.006, 0.009, 0.014, 1.0),
)
component = capture.capture_component2d
component.set_editor_property("texture_target", render_target)
component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
component.set_editor_property("capture_every_frame", False)
component.set_editor_property("capture_on_movement", False)
component.set_editor_property("fov_angle", 25.0)
state = {"seconds": 0.0, "handle": None}
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


def capture_after_streaming(delta_seconds):
    state["seconds"] += delta_seconds
    if state["seconds"] < 20.0:
        return

    component.capture_scene()
    unreal.RenderingLibrary.export_render_target(
        world, render_target, str(output_dir), "PlayerFace01_CryoBodysuit_V32_Manny"
    )
    for actor in reversed(spawned):
        if actor:
            actors.destroy_actor(actor)
    unreal.unregister_slate_post_tick_callback(state["handle"])
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.log(f"METAHUMAN_PLAYER_RENDER {output_dir / 'PlayerFace01_CryoBodysuit_V32_Manny'}")
    unreal.SystemLibrary.quit_editor()


state["handle"] = unreal.register_slate_post_tick_callback(capture_after_streaming)
