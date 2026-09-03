"""Render the player suit showcase through a SceneCapture2D render target."""

import os
import unreal


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(ROOT, "Saved", "Renders")
MAP_PATH = "/Game/Characters/Player/Showcase/L_PlayerSuitShowcase"


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    levels.load_level(MAP_PATH)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

    camera = None
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    for actor in actors:
        if isinstance(actor, unreal.CameraActor) and actor.get_actor_label() == "Render Camera":
            camera = actor
            break
    if not camera:
        raise RuntimeError("Render Camera not found in showcase map")

    rt = unreal.RenderingLibrary.create_render_target2d(
        world, 1600, 900, unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0.008, 0.01, 0.015, 1.0))

    capture = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
        unreal.SceneCapture2D, camera.get_actor_location(), camera.get_actor_rotation())
    capture.set_actor_label("Suit Render Capture")
    component = capture.capture_component2d
    component.set_editor_property("texture_target", rt)
    component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    component.set_editor_property("capture_every_frame", False)
    component.set_editor_property("capture_on_movement", False)
    component.set_editor_property("fov_angle", camera.camera_component.get_editor_property("field_of_view"))
    component.capture_scene()

    unreal.RenderingLibrary.export_render_target(world, rt, OUTPUT_DIR, "PlayerSuitLineup")
    unreal.log("Rendered player suit lineup to " + OUTPUT_DIR)


main()
