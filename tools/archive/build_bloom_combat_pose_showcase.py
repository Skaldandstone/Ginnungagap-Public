"""Build and render brightly lit combat poses for both Bloom host families."""

from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
MAP_PATH = "/Game/Assets/Maps/Bloom/L_Bloom_CombatPose_Showcase"
OUTPUT = PROJECT / "Art/Characters/BloomEnemies/Combat"
OUTPUT_FILE = "BloomCombatPoses.png"


def configure_preview(actor, label, location):
    actor.set_actor_location(location, False, False)
    actor.set_actor_label(label)
    for property_name in ("track_global_bloom_stage", "b_track_global_bloom_stage"):
        try:
            actor.set_editor_property(property_name, False)
            break
        except Exception:
            pass
    actor.set_infection_progress(1.0)
    actor.refresh_infection_presentation()


def add_text(actor_subsystem, label, location, text):
    actor = actor_subsystem.spawn_actor_from_class(
        unreal.TextRenderActor, location, unreal.Rotator()
    )
    actor.set_actor_label(label)
    component = actor.text_render
    component.set_editor_property("text", text)
    component.set_editor_property("world_size", 27.0)
    component.set_editor_property("text_render_color", unreal.Color(245, 240, 255, 255))


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

poses = (
    ("IDLE", -700.0),
    ("ATTACK WINDUP", -420.0),
    ("DEATH BURST", -140.0),
)
crew = []
for index, (pose_name, y) in enumerate(poses):
    enemy = actors.spawn_actor_from_class(
        unreal.BloomReanimatedCrewEnemy, unreal.Vector(0.0, y, 96.0), unreal.Rotator()
    )
    configure_preview(enemy, f"BLOOM_CREW_COMBAT_{index}_{pose_name}", unreal.Vector(0.0, y, 96.0))
    if index == 1:
        enemy.attack_pose_root.set_editor_property("relative_location", unreal.Vector(24.0, 0.0, -3.0))
        enemy.attack_pose_root.set_editor_property("relative_rotation", unreal.Rotator(-10.0, 0.0, 0.0))
        enemy.bloom_glow_light.set_editor_property("intensity", 2210.0)
    elif index == 2:
        enemy.preview_fab_death_pose(1)
        enemy.bloom_glow_light.set_editor_property("intensity", 3060.0)
    crew.append(enemy)
    display_name = "FAB DEATH POSE" if index == 2 else pose_name
    add_text(actors, f"LABEL_CREW_{index}", unreal.Vector(-30.0, y - 95.0, 390.0), display_name)

robot = []
for index, (pose_name, source_y) in enumerate(poses):
    y = source_y + 840.0
    enemy = actors.spawn_actor_from_class(
        unreal.BloomMechanizedEnemy, unreal.Vector(0.0, y, 125.0), unreal.Rotator()
    )
    configure_preview(enemy, f"BLOOM_ROBOT_COMBAT_{index}_{pose_name}", unreal.Vector(0.0, y, 125.0))
    if index == 1:
        enemy.attack_pose_root.set_editor_property("relative_location", unreal.Vector(12.0, 0.0, 0.0))
        enemy.attack_pose_root.set_editor_property("relative_rotation", unreal.Rotator(-3.0, 0.0, 0.0))
        enemy.right_arm.set_editor_property("relative_rotation", unreal.Rotator(-68.0, 180.0, 8.0))
        enemy.bloom_glow_light.set_editor_property("intensity", 3770.0)
    elif index == 2:
        enemy.attack_pose_root.set_editor_property("relative_location", unreal.Vector(0.0, 0.0, -34.0))
        enemy.attack_pose_root.set_editor_property("relative_rotation", unreal.Rotator(0.0, 0.0, -24.0))
        enemy.left_arm.set_editor_property("relative_rotation", unreal.Rotator(38.0, 0.0, -8.0))
        enemy.right_arm.set_editor_property("relative_rotation", unreal.Rotator(38.0, 180.0, 8.0))
        enemy.bloom_glow_light.set_editor_property("intensity", 5220.0)
    robot.append(enemy)
    add_text(actors, f"LABEL_ROBOT_{index}", unreal.Vector(-30.0, y - 95.0, 440.0), pose_name)

floor_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane")
floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, -2.0), unreal.Rotator())
floor.set_actor_label("BLOOM_COMBAT_Floor")
floor.static_mesh_component.set_static_mesh(floor_mesh)
floor.set_actor_scale3d(unreal.Vector(16.0, 24.0, 1.0))

target = unreal.Vector(0.0, 0.0, 140.0)
for label, location, intensity, size, color in (
    ("Front", unreal.Vector(1150.0, 0.0, 500.0), 460.0, 1450.0, unreal.Color(235, 230, 255)),
    ("WarmKey", unreal.Vector(850.0, -760.0, 650.0), 210.0, 620.0, unreal.Color(r=255, g=228, b=210)),
    ("CoolFill", unreal.Vector(760.0, 760.0, 470.0), 160.0, 620.0, unreal.Color(r=205, g=225, b=255)),
    ("Rim", unreal.Vector(-480.0, 0.0, 600.0), 250.0, 560.0, unreal.Color(215, 185, 255)),
):
    light = actors.spawn_actor_from_class(
        unreal.RectLight, location, unreal.MathLibrary.find_look_at_rotation(location, target)
    )
    light.set_actor_label(f"BLOOM_COMBAT_{label}")
    light.rect_light_component.set_editor_property("intensity", intensity)
    light.rect_light_component.set_editor_property("source_width", size)
    light.rect_light_component.set_editor_property("source_height", size)
    light.rect_light_component.set_editor_property("light_color", color)

for index, y in enumerate((-700.0, -420.0, -140.0, 140.0, 420.0, 700.0)):
    location = unreal.Vector(620.0, y, 430.0)
    light = actors.spawn_actor_from_class(
        unreal.RectLight,
        location,
        unreal.MathLibrary.find_look_at_rotation(location, unreal.Vector(0.0, y, 145.0)),
    )
    light.set_actor_label(f"BLOOM_COMBAT_Inspection_{index:02d}")
    light.rect_light_component.set_editor_property("intensity", 230.0)
    light.rect_light_component.set_editor_property("source_width", 240.0)
    light.rect_light_component.set_editor_property("source_height", 340.0)
    light.rect_light_component.set_editor_property(
        "light_color", unreal.Color(255, 225, 218) if index < 3 else unreal.Color(215, 230, 255)
    )

sky = actors.spawn_actor_from_class(unreal.SkyLight, target, unreal.Rotator())
sky.set_actor_label("BLOOM_COMBAT_Sky")
sky.light_component.set_editor_property("intensity", 1.0)
levels.save_current_level()

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
camera_location = unreal.Vector(2250.0, 0.0, 400.0)
capture = actors.spawn_actor_from_class(
    unreal.SceneCapture2D,
    camera_location,
    unreal.MathLibrary.find_look_at_rotation(camera_location, target),
)
component = capture.capture_component2d
component.capture_every_frame = False
component.capture_on_movement = False
component.fov_angle = 49.0
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
        raise RuntimeError(f"Invalid Bloom combat-pose render: {output_path}")
    actors.destroy_actor(capture)
    levels.save_current_level()
    unreal.log(f"BLOOM COMBAT POSE SHOWCASE complete: {output_path}")
    unreal.unregister_slate_post_tick_callback(state["handle"])
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


state["handle"] = unreal.register_slate_post_tick_callback(render_after_warmup)
