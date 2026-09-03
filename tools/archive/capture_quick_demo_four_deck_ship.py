"""Capture visual QA views of the quick four-deck demo map."""

import os
from pathlib import Path

import unreal


MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
OUTPUT = Path(unreal.SystemLibrary.get_project_saved_directory()) / "RoomReviews" / "QuickDemoFourDeck"
PREFIX = "QuickDemo4D_"


def configure_camera(camera, fov=78.0):
    component = camera.get_component_by_class(unreal.CameraComponent)
    component.set_editor_property("field_of_view", fov)
    component.set_editor_property("post_process_blend_weight", 1.0)
    settings = component.get_editor_property("post_process_settings")
    settings.set_editor_property("override_auto_exposure_bias", True)
    settings.set_editor_property("auto_exposure_bias", 0.0)
    component.set_editor_property("post_process_settings", settings)


def room_view(center, side):
    """Frame a room from its corridor threshold toward the dressed outer wall."""
    location = center + unreal.Vector(385.0, -side * 360.0, -52.0)
    target = center + unreal.Vector(-170.0, side * 285.0, -38.0)
    return location, target


def add_review_light(actors_api, location, label, intensity=1100.0, radius=1450.0,
                     color=unreal.Color(188, 210, 220)):
    """Temporary visual-QA fill light; the capture process never saves the map."""
    light = actors_api.spawn_actor_from_class(unreal.PointLight, location, unreal.Rotator())
    light.set_actor_label(label)
    component = light.get_component_by_class(unreal.PointLightComponent)
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("attenuation_radius", radius)
    component.set_editor_property("light_color", color)
    component.set_editor_property("cast_shadows", True)
    return light


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")
    unreal.AutomationLibrary.finish_loading_before_screenshot()
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors = actors_api.get_all_level_actors()
    by_label = {actor.get_actor_label(): actor for actor in actors}
    cryo = by_label[PREFIX + "Room_QD-03-01"].get_actor_location()
    workshop = by_label[PREFIX + "Room_QD-03-02"].get_actor_location()
    engine = by_label[PREFIX + "Room_QD-02-01"].get_actor_location()
    power = by_label[PREFIX + "Room_QD-02-14"].get_actor_location()
    cic = by_label[PREFIX + "Room_QD-03-24"].get_actor_location()
    breach = by_label[PREFIX + "Room_QD-03-11"].get_actor_location()

    for actor in actors:
        if actor.get_actor_label().startswith(PREFIX + "Ceiling_"):
            actor.set_actor_hidden_in_game(True)

    for index, center in enumerate((cryo, workshop, engine, power, cic, breach), start=1):
        tint = unreal.Color(255, 132, 68) if center == cryo else unreal.Color(188, 210, 220)
        add_review_light(actors_api, center + unreal.Vector(0.0, 0.0, 105.0),
                         f"QuickDemoReviewLight_Room_{index:02d}", 1100.0, 1250.0, tint)
    for index, x in enumerate((-6000.0, -3600.0, -1200.0, 1200.0, 3600.0, 6000.0), start=1):
        add_review_light(actors_api, unreal.Vector(x, 0.0, cryo.z + 80.0),
                         f"QuickDemoReviewLight_Corridor_{index:02d}", 700.0, 1750.0)

    cryo_camera, cryo_target = room_view(cryo, -1.0)
    workshop_camera, workshop_target = room_view(workshop, -1.0)
    engine_camera, engine_target = room_view(engine, -1.0)
    power_camera, power_target = room_view(power, 1.0)
    cic_camera, cic_target = room_view(cic, 1.0)
    breach_camera, breach_target = room_view(breach, -1.0)

    views = [
        ("CryoWake", cryo_camera, cryo_target, "lit", 78.0),
        ("PrimaryCorridor", unreal.Vector(cryo.x + 120.0, 0.0, cryo.z - 55.0), unreal.Vector(cryo.x + 4700.0, 0.0, cryo.z - 42.0), "lit", 76.0),
        ("Workshop", workshop_camera, workshop_target, "lit", 76.0),
        ("EngineRoom", engine_camera, engine_target, "lit", 76.0),
        ("PowerControl", power_camera, power_target, "lit", 76.0),
        ("CIC", cic_camera, cic_target, "lit", 76.0),
        ("BloomBreach", breach_camera, breach_target, "lit", 76.0),
    ]
    requested_names = {
        name.strip() for name in os.environ.get("QUICK_DEMO_CAPTURE_VIEWS", "").split(",") if name.strip()
    }
    if requested_names:
        views = [view for view in views if view[0] in requested_names]
        if not views:
            raise RuntimeError(f"No requested quick-demo capture views matched: {sorted(requested_names)}")
    state = {"pending": list(views), "task": None, "camera": None, "output": None, "name": "", "frames": 0, "callback": None}

    def schedule_next():
        name, location, target, viewmode, fov = state["pending"].pop(0)
        unreal.SystemLibrary.execute_console_command(world, f"viewmode {viewmode}")
        for command in ("ShowFlag.Grid 0", "ShowFlag.Sprites 0", "ShowFlag.SelectionOutline 0", "ShowFlag.CompositeEditorPrimitives 0"):
            unreal.SystemLibrary.execute_console_command(world, command)
        camera = actors_api.spawn_actor_from_class(unreal.CameraActor, location, unreal.MathLibrary.find_look_at_rotation(location, target))
        camera.set_actor_label(f"QuickDemoReviewCamera_{name}")
        configure_camera(camera, fov)
        output = (OUTPUT / f"QuickDemo_{name}.png").resolve()
        task = unreal.AutomationLibrary.take_high_res_screenshot(1600, 900, str(output), camera=camera, delay=1.0, force_game_view=True)
        if not task or not task.is_valid_task():
            raise RuntimeError(f"Could not schedule {name} capture")
        state.update(task=task, camera=camera, output=output, name=name, frames=0)

    def advance(_delta_seconds):
        state["frames"] += 1
        # UE can report a newly queued screenshot task as done for one frame while
        # the next render request is still entering the viewport queue.
        if state["frames"] < 45 or not state["task"].is_task_done():
            return
        if not state["output"].exists():
            unreal.log_error(f"Quick-demo capture missing: {state['output']}")
        actors_api.destroy_actor(state["camera"])
        if state["pending"]:
            schedule_next()
        else:
            unreal.unregister_slate_post_tick_callback(state["callback"])
            unreal.log("Quick-demo visual QA captures complete")
            unreal.SystemLibrary.execute_console_command(world, "QUIT_EDITOR")

    schedule_next()
    state["callback"] = unreal.register_slate_post_tick_callback(advance)


if __name__ == "__main__":
    main()
