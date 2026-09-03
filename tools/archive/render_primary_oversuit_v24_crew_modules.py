"""Render the current V24 Crew oversuit and its two authored equipment modules."""

from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
OUTPUT = PROJECT / "Saved" / "Renders"
MAP_PATH = "/Game/Characters/PlayerSuits/PrimaryOversuits/V24Sculpt/Maps/L_PrimaryOversuit_V24_Sculpt"
VISIBLE_LABELS = {
    "WORKING_ROLE_Crew_I01",
    "WORKING_CREW_HarnessMonitor_I01",
    "WORKING_CREW_SurveyToolMount_I01",
}
MORPHS = (
    "V24_SharedFit_I01",
    "V24_Crew_01_SilhouetteCleanup",
    "V24_Crew_02_HelmetCollar",
    "V24_Crew_03_EquipmentSettle",
    "V24_Crew_04_MobilityClearance",
)


def set_hidden(actor, value: bool) -> None:
    actor.set_actor_hidden_in_game(value)
    actor.set_is_temporarily_hidden_in_editor(value)


def capture_view(world, subsystem, name, location, target, fov, width, height) -> None:
    rotation = unreal.MathLibrary.find_look_at_rotation(location, target)
    capture = subsystem.spawn_actor_from_class(unreal.SceneCapture2D, location, rotation)
    capture.set_actor_label(f"RENDER_{name}")
    component = capture.capture_component2d
    component.set_editor_property("capture_every_frame", False)
    component.set_editor_property("capture_on_movement", False)
    component.set_editor_property("fov_angle", fov)

    render_target = unreal.RenderingLibrary.create_render_target2d(
        world,
        width,
        height,
        unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0.012, 0.016, 0.022, 1.0),
    )
    component.set_editor_property("texture_target", render_target)
    component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    post_process = component.get_editor_property("post_process_settings")
    post_process.set_editor_property("override_auto_exposure_bias", True)
    post_process.set_editor_property("auto_exposure_bias", -1.0)
    component.set_editor_property("post_process_settings", post_process)
    component.capture_scene()
    component.capture_scene()
    unreal.RenderingLibrary.export_render_target(
        world, render_target, str(OUTPUT), f"{name}_Review"
    )


def add_review_light(subsystem, label, location, target, intensity, width, height) -> None:
    rotation = unreal.MathLibrary.find_look_at_rotation(location, target)
    light = subsystem.spawn_actor_from_class(unreal.RectLight, location, rotation)
    light.set_actor_label(label)
    component = light.rect_light_component
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("source_width", width)
    component.set_editor_property("source_height", height)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level.load_level(MAP_PATH):
        raise RuntimeError(f"Could not load module review map: {MAP_PATH}")
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = subsystem.get_all_level_actors()
    by_label = {actor.get_actor_label(): actor for actor in actors}

    missing = sorted(VISIBLE_LABELS.difference(by_label))
    if missing:
        raise RuntimeError(f"Module review actors are missing: {missing}")
    crew = by_label["WORKING_ROLE_Crew_I01"]
    if not isinstance(crew, unreal.SkeletalMeshActor):
        raise RuntimeError("Crew review actor is not a skeletal mesh actor")

    for actor in actors:
        set_hidden(actor, actor.get_actor_label() not in VISIBLE_LABELS)
    for label in VISIBLE_LABELS:
        set_hidden(by_label[label], False)
    for morph in MORPHS:
        crew.skeletal_mesh_component.set_morph_target(morph, 1.0, False)

    crew_origin, crew_extent = crew.get_actor_bounds(False, False)
    module_origins = [
        by_label["WORKING_CREW_HarnessMonitor_I01"].get_actor_bounds(False, False)[0],
        by_label["WORKING_CREW_SurveyToolMount_I01"].get_actor_bounds(False, False)[0],
    ]
    module_target = unreal.Vector(
        sum(origin.x for origin in module_origins) / len(module_origins),
        sum(origin.y for origin in module_origins) / len(module_origins),
        sum(origin.z for origin in module_origins) / len(module_origins),
    )
    full_target = unreal.Vector(crew_origin.x, crew_origin.y, crew_origin.z + 5.0)
    full_camera = unreal.Vector(
        crew_origin.x + max(crew_extent.x * 4.25, 440.0),
        crew_origin.y,
        crew_origin.z + 8.0,
    )
    close_camera = unreal.Vector(
        module_target.x + 235.0,
        module_target.y,
        module_target.z + 8.0,
    )
    add_review_light(
        subsystem,
        "RENDER_KEY",
        unreal.Vector(full_camera.x - 60.0, full_camera.y - 175.0, full_target.z + 135.0),
        full_target,
        1800.0,
        250.0,
        250.0,
    )
    add_review_light(
        subsystem,
        "RENDER_FILL",
        unreal.Vector(full_camera.x - 120.0, full_camera.y + 190.0, full_target.z + 35.0),
        full_target,
        700.0,
        220.0,
        220.0,
    )
    add_review_light(
        subsystem,
        "RENDER_RIM",
        unreal.Vector(crew_origin.x - 170.0, crew_origin.y, full_target.z + 110.0),
        full_target,
        1200.0,
        180.0,
        180.0,
    )
    capture_view(
        world,
        subsystem,
        "PrimaryOversuitV24_CrewModules_Full",
        full_camera,
        full_target,
        42.0,
        1200,
        1600,
    )
    capture_view(
        world,
        subsystem,
        "PrimaryOversuitV24_CrewModules_Closeup",
        close_camera,
        module_target,
        34.0,
        1600,
        1200,
    )
    unreal.log(f"Rendered V24 Crew module review to {OUTPUT}")


main()
