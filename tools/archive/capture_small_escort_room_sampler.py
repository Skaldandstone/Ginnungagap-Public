"""Render a representative sampler of the Fab-dressed Small Escort rooms."""

from __future__ import annotations

import os
from pathlib import Path

import unreal


MAP = "/Game/Assets/Maps/ShipProduction/L_SmallEscort_OperationsDeck"
PROJECT = Path(unreal.SystemLibrary.get_project_directory())
OUTPUT = PROJECT / "Saved/RoomReviews/SmallEscortOperations"
WIDTH = 1600
HEIGHT = 900

# Room center plus a local camera offset and local look-at offset. Cameras sit at roughly
# human eye height and aim across the room toward its principal dressing cluster.
VIEWS = (
    ("Bridge", "BRG-08-01", (-580.0, -330.0, -55.0), (180.0, 120.0, -105.0)),
    ("CrewCommons", "CCM-07-01", (-580.0, -330.0, -55.0), (180.0, 120.0, -110.0)),
    ("EmergencyTriage", "MED-07-01", (-580.0, 0.0, -55.0), (180.0, 0.0, -110.0)),
    ("CargoStaging", "CGO-06-01", (-580.0, 0.0, -55.0), (180.0, 0.0, -110.0)),
    ("DriveAccess", "ENG-06-01", (-580.0, 0.0, -55.0), (180.0, 0.0, -100.0)),
)


def room_code(actor):
    try:
        return str(actor.get_editor_property("room_code"))
    except Exception:
        return ""


def capture(world, actors, name, room, camera_offset, target_offset):
    center = room.get_actor_location()
    camera_location = center + unreal.Vector(*camera_offset)
    target = center + unreal.Vector(*target_offset)
    camera_rotation = unreal.MathLibrary.find_look_at_rotation(camera_location, target)
    filename = f"SmallEscort_{name}.png"
    output_file = (OUTPUT / filename).resolve()
    camera = actors.spawn_actor_from_class(unreal.CameraActor, camera_location, camera_rotation)
    camera.set_actor_label(f"EscortOps_ReviewCamera_{name}")
    camera_component = camera.get_component_by_class(unreal.CameraComponent)
    camera_component.set_editor_property("field_of_view", 72.0)
    camera_component.set_editor_property("post_process_blend_weight", 1.0)
    post_process = camera_component.get_editor_property("post_process_settings")
    post_process.set_editor_property("override_auto_exposure_bias", True)
    post_process.set_editor_property("auto_exposure_bias", -0.65)
    camera_component.set_editor_property("post_process_settings", post_process)
    task = unreal.AutomationLibrary.take_high_res_screenshot(
        WIDTH, HEIGHT, str(output_file), camera=camera, delay=1.0, force_game_view=True
    )
    if not task or not task.is_valid_task():
        raise RuntimeError(f"Could not schedule viewport capture for {name}")
    unreal.log(f"SMALL_ESCORT_ROOM_CAPTURE_REQUESTED {name}: {output_file}")
    return task, camera, output_file


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(MAP):
        raise RuntimeError("Could not load the Small Escort Operations District")

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.SystemLibrary.execute_console_command(world, "r.ScreenPercentage 100")
    unreal.SystemLibrary.execute_console_command(world, "r.Nanite 1")
    unreal.SystemLibrary.execute_console_command(world, "r.Lumen.Reflections.Allow 1")
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    for command in (
        "ShowFlag.Grid 0", "ShowFlag.Sprites 0", "ShowFlag.SelectionOutline 0",
        "ShowFlag.CompositeEditorPrimitives 0",
    ):
        unreal.SystemLibrary.execute_console_command(world, command)

    rooms = {room_code(actor): actor for actor in actors.get_all_level_actors() if room_code(actor)}
    missing = [code for _, code, _, _ in VIEWS if code not in rooms]
    if missing:
        raise RuntimeError("Missing sampler rooms: " + ", ".join(missing))

    requested_name = os.environ.get("GINNUNGAGAP_ROOM_CAPTURE", "")
    selected = [view for view in VIEWS if not requested_name or view[0] == requested_name]
    if requested_name and not selected:
        raise RuntimeError(f"Unknown Small Escort room capture: {requested_name}")

    state = {
        "pending": list(selected), "task": None, "camera": None, "output": None,
        "name": "", "finished_frames": 0, "callback": None,
    }

    def schedule_next():
        name, code, camera_offset, target_offset = state["pending"].pop(0)
        task, camera, output_file = capture(
            world, actors, name, rooms[code], camera_offset, target_offset
        )
        state.update({
            "task": task, "camera": camera, "output": output_file,
            "name": name, "finished_frames": 0,
        })

    def advance_sampler(_delta_seconds):
        if not state["task"].is_task_done():
            return
        state["finished_frames"] += 1
        if state["finished_frames"] < 2:
            return
        if not state["output"].exists():
            unreal.log_error(
                f"Small Escort capture task completed without writing {state['output']}"
            )
        else:
            unreal.log(
                f"SMALL_ESCORT_ROOM_CAPTURE_WRITTEN {state['name']}: {state['output']}"
            )
        actors.destroy_actor(state["camera"])
        if state["pending"]:
            schedule_next()
            return
        unreal.unregister_slate_post_tick_callback(state["callback"])
        unreal.log(f"Small Escort room sampler complete: {len(selected)} captures")
        unreal.SystemLibrary.execute_console_command(world, "QUIT_EDITOR")

    schedule_next()
    state["callback"] = unreal.register_slate_post_tick_callback(advance_sampler)


if __name__ == "__main__":
    main()
