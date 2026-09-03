"""Capture the generated Unreal weapon review maps for visual QA."""

from pathlib import Path
import time

import unreal


OUTPUT = Path(unreal.SystemLibrary.get_project_saved_directory()) / "Renders" / "Weapons"
REVIEWS = [
    (
        "EarlyProjectile",
        "/Game/Assets/Maps/ModelLibrary/L_EarlyProjectileWeapons_Unreal",
        "EarlyProjectile_ReviewCamera",
    ),
    (
        "SecurityControl",
        "/Game/Assets/Maps/ModelLibrary/L_SecurityControlProjectileWeapons_Unreal",
        "SecurityControlProjectile_ReviewCamera",
    ),
    (
        "EmergencySupport",
        "/Game/Assets/Maps/ModelLibrary/L_EmergencySupportWeapons_Unreal",
        "EmergencySupport_ReviewCamera",
    ),
]


def configure_camera(camera):
    component = camera.get_component_by_class(unreal.CameraComponent)
    component.set_editor_property("field_of_view", 58.0)
    component.set_editor_property("post_process_blend_weight", 1.0)
    settings = component.get_editor_property("post_process_settings")
    settings.set_editor_property("override_auto_exposure_bias", True)
    settings.set_editor_property("auto_exposure_bias", 1.1)
    component.set_editor_property("post_process_settings", settings)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    editor = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    state = {
        "pending": list(REVIEWS),
        "task": None,
        "output": None,
        "frames": 0,
        "started": 0.0,
        "callback": None,
        "scheduling": False,
    }

    def schedule_next():
        state["scheduling"] = True
        name, map_path, camera_label = state["pending"].pop(0)
        if not levels.load_level(map_path):
            raise RuntimeError(f"Could not load {map_path}")
        unreal.AutomationLibrary.finish_loading_before_screenshot()
        camera = next(
            (
                actor
                for actor in actors_api.get_all_level_actors()
                if actor.get_actor_label() == camera_label
            ),
            None,
        )
        if camera is None:
            raise RuntimeError(f"Missing {camera_label} in {map_path}")
        configure_camera(camera)
        world = editor.get_editor_world()
        for command in (
            "viewmode lit",
            "r.ScreenPercentage 100",
            "ShowFlag.Grid 0",
            "ShowFlag.Sprites 0",
            "ShowFlag.SelectionOutline 0",
            "ShowFlag.CompositeEditorPrimitives 0",
        ):
            unreal.SystemLibrary.execute_console_command(world, command)
        output = (OUTPUT / f"WeaponReview_{name}.png").resolve()
        if output.exists():
            output.unlink()
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            1600, 900, str(output), camera=camera, delay=1.0, force_game_view=True)
        if not task or not task.is_valid_task():
            raise RuntimeError(f"Could not schedule {name} capture")
        state.update(task=task, output=output, frames=0, started=time.monotonic())
        state["scheduling"] = False

    def advance(_delta_seconds):
        if state["scheduling"]:
            return
        state["frames"] += 1
        elapsed = time.monotonic() - state["started"]
        if not state["output"].exists() and elapsed < 15.0:
            return
        if not state["output"].exists():
            unreal.log_error(f"Weapon review capture missing: {state['output']}")
        if state["pending"]:
            schedule_next()
            return
        unreal.unregister_slate_post_tick_callback(state["callback"])
        unreal.log("Weapon review captures complete")
        unreal.SystemLibrary.execute_console_command(editor.get_editor_world(), "QUIT_EDITOR")

    schedule_next()
    state["callback"] = unreal.register_slate_post_tick_callback(advance)


if __name__ == "__main__":
    main()
