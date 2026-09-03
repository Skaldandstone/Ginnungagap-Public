"""Render the V24 Space Marshal primary-oversuit review lineup in Unreal."""

from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
OUTPUT = PROJECT / "Saved" / "Renders"
MAP_PATH = "/Game/Characters/PlayerSuits/PrimaryOversuits/V24Review/SpaceMarshal/L_SpaceMarshal_ClassLineup"


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP_PATH)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    for command in (
        "r.Lumen.DiffuseIndirect.Allow 0",
        "r.Lumen.Reflections.Allow 0",
        "r.Shadow.Virtual.Enable 0",
        "r.AntiAliasingMethod 1",
    ):
        unreal.SystemLibrary.execute_console_command(world, command)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    camera = next(
        (
            actor for actor in actors.get_all_level_actors()
            if isinstance(actor, unreal.CameraActor)
            and actor.get_actor_label() == "Space Marshal Review Camera"
        ),
        None,
    )
    if not camera:
        raise RuntimeError("Space Marshal review camera is missing")

    capture = actors.spawn_actor_from_class(
        unreal.SceneCapture2D, camera.get_actor_location(), camera.get_actor_rotation()
    )
    capture.set_actor_label("Space Marshal V24 Render Capture")
    component = capture.capture_component2d
    component.set_editor_property("capture_every_frame", False)
    component.set_editor_property("capture_on_movement", False)
    component.set_editor_property("fov_angle", camera.camera_component.get_editor_property("field_of_view"))
    for source, name in (
        (unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR, "SpaceMarshalOversuitV24_Lineup"),
        (unreal.SceneCaptureSource.SCS_BASE_COLOR, "SpaceMarshalOversuitV24_BaseColor"),
    ):
        render_target = unreal.RenderingLibrary.create_render_target2d(
            world,
            1920,
            1080,
            unreal.TextureRenderTargetFormat.RTF_RGBA8,
            unreal.LinearColor(0.006, 0.008, 0.012, 1.0),
        )
        component.set_editor_property("texture_target", render_target)
        component.set_editor_property("capture_source", source)
        component.capture_scene()
        unreal.RenderingLibrary.export_render_target(world, render_target, str(OUTPUT), name)
    unreal.log(f"Rendered Space Marshal oversuit review to {OUTPUT}")


main()
