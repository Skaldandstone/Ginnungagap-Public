"""Render representative corridor and vertical-link views from the production escort map."""

from __future__ import annotations

from pathlib import Path

import unreal


MAP = "/Game/Assets/Maps/ShipProduction/L_SmallEscort_OperationsDeck"
PROJECT = Path(unreal.SystemLibrary.get_project_directory())
OUTPUT = PROJECT / "Saved/RoomReviews/SmallEscortOperations/Corridors"
WIDTH = 1600
HEIGHT = 900

CORRIDOR_VIEWS = (
    ("CommandForeAft", "EscortOps_Corridor_OPS-08-01_BRG-08-01"),
    ("CommandCrossDeck", "EscortOps_Corridor_BRG-08-01_SNS-08-01"),
    ("EngineeringForeAft", "EscortOps_Corridor_ENG-06-01_AUX-06-01"),
)


def room_code(actor):
    try:
        return str(actor.get_editor_property("room_code"))
    except Exception:
        return ""


def configure_camera(camera):
    component = camera.get_component_by_class(unreal.CameraComponent)
    component.set_editor_property("field_of_view", 76.0)
    component.set_editor_property("post_process_blend_weight", 1.0)
    settings = component.get_editor_property("post_process_settings")
    settings.set_editor_property("override_auto_exposure_bias", True)
    settings.set_editor_property("auto_exposure_bias", 0.35)
    component.set_editor_property("post_process_settings", settings)


def corridor_view(corridor):
    center = corridor.get_actor_location()
    forward = corridor.get_actor_forward_vector()
    up = corridor.get_actor_up_vector()
    extent = corridor.get_editor_property("section_bounds").get_scaled_box_extent()
    eye_height_from_floor = 165.0
    camera_location = center - forward * (extent.x - 82.0) + up * (-extent.z + eye_height_from_floor)
    target = center + forward * (extent.x + 310.0) + up * (-extent.z + 145.0)
    return camera_location, target


def stair_view(rooms):
    lower = rooms["FAB-06-01"].get_actor_location()
    # The generated ramp's low end is on local +X (negative UE pitch).
    camera_location = lower + unreal.Vector(650.0, 0.0, -55.0)
    target = lower + unreal.Vector(-320.0, 0.0, 125.0)
    return camera_location, target


def open_thresholds_for_review(level_actors):
    """Hide only sliding door leaves; retain frames and threshold hardpoints."""
    hidden_panels = 0
    for actor in level_actors:
        if not isinstance(actor, unreal.ProductionBulkheadDoor):
            continue
        try:
            for property_name in ("left_panel", "right_panel"):
                panel = actor.get_editor_property(property_name)
                if panel:
                    panel.set_visibility(False, True)
                    panel.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                    hidden_panels += 1
        except Exception as error:
            unreal.log_warning(f"Could not open review threshold {actor.get_actor_label()}: {error}")
    unreal.log(f"SMALL_ESCORT_CORRIDOR_REVIEW_OPENED {hidden_panels} threshold panels")


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(MAP):
        raise RuntimeError("Could not load the Small Escort Operations District")

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    for command in (
        "r.ScreenPercentage 100", "r.Nanite 1", "r.Lumen.Reflections.Allow 1",
        "ShowFlag.Grid 0", "ShowFlag.Sprites 0", "ShowFlag.SelectionOutline 0",
        "ShowFlag.CompositeEditorPrimitives 0",
    ):
        unreal.SystemLibrary.execute_console_command(world, command)

    level_actors = actors.get_all_level_actors()
    by_label = {actor.get_actor_label(): actor for actor in level_actors}
    rooms = {room_code(actor): actor for actor in level_actors if room_code(actor)}
    missing = [label for _, label in CORRIDOR_VIEWS if label not in by_label]
    if missing or "FAB-06-01" not in rooms:
        raise RuntimeError("Missing corridor review actors: " + ", ".join(missing))

    open_thresholds_for_review(level_actors)
    views = []
    for name, label in CORRIDOR_VIEWS:
        camera_location, target = corridor_view(by_label[label])
        views.append((name, camera_location, target))
    views.append(("VerticalFabricationStair", *stair_view(rooms)))

    requested_count = len(views)
    state = {"pending": list(views), "task": None, "camera": None, "output": None,
             "name": "", "finished_frames": 0, "callback": None}

    def schedule_next():
        name, camera_location, target = state["pending"].pop(0)
        camera_rotation = unreal.MathLibrary.find_look_at_rotation(camera_location, target)
        camera = actors.spawn_actor_from_class(unreal.CameraActor, camera_location, camera_rotation)
        camera.set_actor_label(f"EscortOps_CorridorReviewCamera_{name}")
        configure_camera(camera)
        output_file = (OUTPUT / f"SmallEscort_Corridor_{name}.png").resolve()
        task = unreal.AutomationLibrary.take_high_res_screenshot(
            WIDTH, HEIGHT, str(output_file), camera=camera, delay=1.0, force_game_view=True
        )
        if not task or not task.is_valid_task():
            raise RuntimeError(f"Could not schedule corridor capture {name}")
        state.update({"task": task, "camera": camera, "output": output_file,
                      "name": name, "finished_frames": 0})
        unreal.log(f"SMALL_ESCORT_CORRIDOR_CAPTURE_REQUESTED {name}: {output_file}")

    def advance(_delta_seconds):
        if not state["task"].is_task_done():
            return
        state["finished_frames"] += 1
        if state["finished_frames"] < 2:
            return
        if not state["output"].exists():
            unreal.log_error(f"Corridor capture did not write {state['output']}")
        else:
            unreal.log(f"SMALL_ESCORT_CORRIDOR_CAPTURE_WRITTEN {state['name']}: {state['output']}")
        actors.destroy_actor(state["camera"])
        if state["pending"]:
            schedule_next()
            return
        unreal.unregister_slate_post_tick_callback(state["callback"])
        unreal.log(f"Small Escort corridor review complete: {requested_count} captures")
        unreal.SystemLibrary.execute_console_command(world, "QUIT_EDITOR")

    schedule_next()
    state["callback"] = unreal.register_slate_post_tick_callback(advance)


if __name__ == "__main__":
    main()
