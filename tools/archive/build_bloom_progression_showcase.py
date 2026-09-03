"""Build and render a four-phase lineup for both progressive Bloom enemies."""

from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
MAP_PATH = "/Game/Assets/Maps/Bloom/L_Bloom_Progression_Showcase"
OUTPUT = PROJECT / "Art/Characters/BloomEnemies/Progression"
OUTPUT_FILE = "BloomProgression_Lineup.png"
PHASES = (
    ("SEEDED", 0.18),
    ("COLONIZING", 0.42),
    ("PUPPETEERED", 0.70),
    ("OVERGROWN", 1.0),
)


def set_preview_progress(actor, progress):
    # Editor review actors must remain at their authored phase instead of following
    # the runtime game-instance director when the map is played for inspection.
    for property_name in ("track_global_bloom_stage", "b_track_global_bloom_stage"):
        try:
            actor.set_editor_property(property_name, False)
            break
        except Exception:
            pass
    actor.set_infection_progress(progress)
    actor.refresh_infection_presentation()


def add_text(actors, label, location, text, size=34.0):
    actor = actors.spawn_actor_from_class(unreal.TextRenderActor, location, unreal.Rotator())
    actor.set_actor_label(label)
    component = actor.text_render
    component.set_editor_property("text", text)
    component.set_editor_property("world_size", size)
    component.set_editor_property("text_render_color", unreal.Color(245, 240, 255, 255))
    return actor


levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
    if not levels.load_level(MAP_PATH):
        raise RuntimeError(f"Could not load {MAP_PATH}")
else:
    if not levels.new_level(MAP_PATH):
        raise RuntimeError(f"Could not create {MAP_PATH}")

for existing in actors.get_all_level_actors():
    actors.destroy_actor(existing)

crew_positions = (-980.0, -700.0, -420.0, -140.0)
robot_positions = (140.0, 420.0, 700.0, 980.0)
for index, ((phase_name, progress), y) in enumerate(zip(PHASES, crew_positions)):
    crew = actors.spawn_actor_from_class(
        unreal.BloomReanimatedCrewEnemy, unreal.Vector(0.0, y, 96.0), unreal.Rotator()
    )
    crew.set_actor_location(unreal.Vector(0.0, y, 96.0), False, False)
    crew.set_actor_label(f"BLOOM_CREW_{index}_{phase_name}")
    set_preview_progress(crew, progress)

    add_text(
        actors,
        f"LABEL_CREW_{phase_name}",
        unreal.Vector(-20.0, y - 95.0, 330.0),
        f"{phase_name}\n{progress * 100:.0f}%",
        22.0,
    )

for index, ((phase_name, progress), y) in enumerate(zip(PHASES, robot_positions)):
    robot = actors.spawn_actor_from_class(
        unreal.BloomMechanizedEnemy, unreal.Vector(0.0, y, 125.0), unreal.Rotator()
    )
    robot.set_actor_location(unreal.Vector(0.0, y, 125.0), False, False)
    robot.set_actor_label(f"BLOOM_ROBOT_{index}_{phase_name}")
    set_preview_progress(robot, progress)

    add_text(
        actors,
        f"LABEL_ROBOT_{phase_name}",
        unreal.Vector(-20.0, y - 95.0, 400.0),
        f"{phase_name}\n{progress * 100:.0f}%",
        22.0,
    )

floor_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane")
floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, -2.0), unreal.Rotator())
floor.set_actor_label("BLOOM_PROGRESSION_Floor")
floor.static_mesh_component.set_static_mesh(floor_mesh)
floor.set_actor_scale3d(unreal.Vector(16.0, 28.0, 1.0))

target = unreal.Vector(0.0, 0.0, 140.0)
for label, location, intensity, size, color in (
    ("Front", unreal.Vector(1200.0, 0.0, 480.0), 420.0, 1500.0, unreal.Color(232, 226, 255)),
    ("Key", unreal.Vector(850.0, -900.0, 650.0), 180.0, 650.0, unreal.Color(255, 232, 210)),
    ("Fill", unreal.Vector(700.0, 900.0, 420.0), 120.0, 600.0, unreal.Color(190, 218, 255)),
    ("Rim", unreal.Vector(-450.0, 0.0, 580.0), 220.0, 520.0, unreal.Color(205, 175, 255)),
):
    light = actors.spawn_actor_from_class(
        unreal.RectLight, location, unreal.MathLibrary.find_look_at_rotation(location, target)
    )
    light.set_actor_label(f"BLOOM_PROGRESSION_{label}")
    light.rect_light_component.set_editor_property("intensity", intensity)
    light.rect_light_component.set_editor_property("source_width", size)
    light.rect_light_component.set_editor_property("source_height", size)
    light.rect_light_component.set_editor_property("light_color", color)

# Give every authored infection phase its own neutral inspection key. This keeps
# silhouettes and attachment thresholds readable without flattening the colored
# infection light emitted by the enemy itself.
for index, y in enumerate(crew_positions + robot_positions):
    is_crew = index < len(crew_positions)
    location = unreal.Vector(620.0, y, 430.0)
    light = actors.spawn_actor_from_class(
        unreal.RectLight,
        location,
        unreal.MathLibrary.find_look_at_rotation(location, unreal.Vector(0.0, y, 145.0)),
    )
    light.set_actor_label(f"BLOOM_PROGRESSION_Inspection_{index:02d}")
    light.rect_light_component.set_editor_property("intensity", 210.0)
    light.rect_light_component.set_editor_property("source_width", 230.0)
    light.rect_light_component.set_editor_property("source_height", 330.0)
    light.rect_light_component.set_editor_property(
        "light_color",
        unreal.Color(255, 225, 218) if is_crew else unreal.Color(218, 230, 255),
    )

sky = actors.spawn_actor_from_class(unreal.SkyLight, target, unreal.Rotator())
sky.set_actor_label("BLOOM_PROGRESSION_Sky")
sky.light_component.set_editor_property("intensity", 1.0)
levels.save_current_level()

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
camera_location = unreal.Vector(2400.0, 0.0, 400.0)
capture = actors.spawn_actor_from_class(
    unreal.SceneCapture2D,
    camera_location,
    unreal.MathLibrary.find_look_at_rotation(camera_location, target),
)
capture.set_actor_location(camera_location, False, False)
component = capture.capture_component2d
component.capture_every_frame = False
component.capture_on_movement = False
component.fov_angle = 54.0
component.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
texture = unreal.RenderingLibrary.create_render_target2d(
    world,
    1600,
    1000,
    unreal.TextureRenderTargetFormat.RTF_RGBA8,
    unreal.LinearColor(0.008, 0.01, 0.015, 1.0),
)
texture.set_editor_property("target_gamma", 2.2)
component.texture_target = texture
settings = component.post_process_settings
settings.set_editor_property("override_auto_exposure_method", True)
settings.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
settings.set_editor_property("override_camera_iso", True)
settings.set_editor_property("camera_iso", 1000.0)
settings.set_editor_property("override_camera_shutter_speed", True)
settings.set_editor_property("camera_shutter_speed", 60.0)
component.post_process_settings = settings

OUTPUT.mkdir(parents=True, exist_ok=True)
state = {"elapsed": 0.0, "finished": False, "handle": None}
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


def render_after_warmup(delta_seconds):
    if state["finished"]:
        return
    state["elapsed"] += delta_seconds
    if state["elapsed"] < 15.0:
        return
    state["finished"] = True
    component.capture_scene()
    component.capture_scene()
    unreal.RenderingLibrary.export_render_target(world, texture, str(OUTPUT), OUTPUT_FILE)
    output_path = OUTPUT / OUTPUT_FILE
    if not output_path.exists() or output_path.stat().st_size < 10000:
        raise RuntimeError(f"Invalid Bloom progression render: {output_path}")
    if capture in actors.get_all_level_actors():
        actors.destroy_actor(capture)
    levels.save_current_level()
    unreal.log(f"BLOOM PROGRESSION SHOWCASE complete: {output_path}")
    unreal.unregister_slate_post_tick_callback(state["handle"])
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


state["handle"] = unreal.register_slate_post_tick_callback(render_after_warmup)
