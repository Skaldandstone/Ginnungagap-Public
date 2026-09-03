"""Create a clean V25 projection-sculpt review level and render front/profile/three-quarter views."""

from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
OUTPUT = PROJECT / "Saved/Renders"
MAP_PATH = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt/Maps/L_PrimaryOversuit_V25_ProjectionSculpt"
SHELL_PATH = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt/Working/Iteration_01/SKM_PrimaryOversuit_ProjectionShell_I01"


def add_rect_light(actors, label, location, target, intensity, width, height):
    light = actors.spawn_actor_from_class(
        unreal.RectLight,
        location,
        unreal.MathLibrary.find_look_at_rotation(location, target),
    )
    light.set_actor_label(label)
    component = light.rect_light_component
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("source_width", width)
    component.set_editor_property("source_height", height)


def capture(world, actors, filename, location, target, fov=35.0):
    actor = actors.spawn_actor_from_class(
        unreal.SceneCapture2D,
        location,
        unreal.MathLibrary.find_look_at_rotation(location, target),
    )
    actor.set_actor_label(f"RENDER_{filename}")
    component = actor.capture_component2d
    component.capture_every_frame = False
    component.capture_on_movement = False
    component.fov_angle = fov
    target_texture = unreal.RenderingLibrary.create_render_target2d(
        world,
        1200,
        1600,
        unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0.012, 0.016, 0.022, 1.0),
    )
    component.texture_target = target_texture
    component.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    pp = component.post_process_settings
    pp.override_auto_exposure_bias = True
    pp.auto_exposure_bias = -1.8
    component.post_process_settings = pp
    component.capture_scene()
    component.capture_scene()
    unreal.RenderingLibrary.export_render_target(world, target_texture, str(OUTPUT), filename)
    actor.destroy_actor()


OUTPUT.mkdir(parents=True, exist_ok=True)
level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
    level.load_level(MAP_PATH)
else:
    level.new_level(MAP_PATH)

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for existing in actors.get_all_level_actors():
    actors.destroy_actor(existing)

shell_asset = unreal.EditorAssetLibrary.load_asset(SHELL_PATH)
if not isinstance(shell_asset, unreal.SkeletalMesh):
    raise RuntimeError(f"Missing V25 projection shell: {SHELL_PATH}")

shell = actors.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator())
shell.set_actor_label("WORKING_V25_ProjectionShell_I01")
shell.skeletal_mesh_component.set_skeletal_mesh_asset(shell_asset)

target = unreal.Vector(0, 3, 92)
add_rect_light(actors, "REVIEW_Key", unreal.Vector(-150, -210, 245), target, 300.0, 160.0, 160.0)
add_rect_light(actors, "REVIEW_Fill", unreal.Vector(170, -150, 130), target, 120.0, 120.0, 180.0)
add_rect_light(actors, "REVIEW_Rim", unreal.Vector(0, 190, 210), target, 240.0, 110.0, 150.0)

sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(), unreal.Rotator())
sky.set_actor_label("REVIEW_Sky")
sky.light_component.set_editor_property("intensity", 0.18)

level.save_current_level()
capture(world, actors, "PrimaryOversuitV25_ProjectionSculpt_Front", unreal.Vector(0, -390, 95), target)
capture(world, actors, "PrimaryOversuitV25_ProjectionSculpt_Profile", unreal.Vector(-390, 5, 95), target)
capture(world, actors, "PrimaryOversuitV25_ProjectionSculpt_ThreeQuarter", unreal.Vector(-255, -300, 125), target)
level.save_current_level()
unreal.log(f"Rendered V25 projection sculpt to {OUTPUT}")
