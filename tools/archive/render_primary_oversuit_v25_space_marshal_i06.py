"""Render the V25 I06 authored uncorrupted-humanoid production shell."""

from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
OUTPUT = PROJECT / "Saved/Renders"
ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt"
FOLDER = ROOT + "/Working/Iteration_06_UncorruptedProductionShell"
MESH_PATH = FOLDER + "/Source/SKM_V25_I06_SpaceMarshalMale"
MAP_PATH = ROOT + "/Maps/L_PrimaryOversuit_V25_UncorruptedProduction_I06"


def add_rect_light(actors, label, location, target, intensity, width, height, color):
    light = actors.spawn_actor_from_class(
        unreal.RectLight, location, unreal.MathLibrary.find_look_at_rotation(location, target)
    )
    light.set_actor_label(label)
    component = light.rect_light_component
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("source_width", width)
    component.set_editor_property("source_height", height)
    component.set_editor_property("light_color", color)


def capture(world, actors, filename, location, target, fov=33.0):
    actor = actors.spawn_actor_from_class(
        unreal.SceneCapture2D, location, unreal.MathLibrary.find_look_at_rotation(location, target)
    )
    actor.set_actor_label(f"RENDER_{filename}")
    component = actor.capture_component2d
    component.capture_every_frame = False
    component.capture_on_movement = False
    component.fov_angle = fov
    texture = unreal.RenderingLibrary.create_render_target2d(
        world, 1200, 1600, unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0.105, 0.112, 0.120, 1.0),
    )
    component.texture_target = texture
    component.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    pp = component.post_process_settings
    pp.set_editor_property("override_auto_exposure_method", True)
    pp.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    pp.set_editor_property("override_camera_iso", True)
    pp.set_editor_property("camera_iso", 100.0)
    pp.set_editor_property("override_camera_shutter_speed", True)
    pp.set_editor_property("camera_shutter_speed", 60.0)
    pp.set_editor_property("override_auto_exposure_bias", True)
    pp.set_editor_property("auto_exposure_bias", 0.45)
    component.post_process_settings = pp
    component.capture_scene()
    component.capture_scene()
    unreal.RenderingLibrary.export_render_target(world, texture, str(OUTPUT), filename)
    actor.destroy_actor()


OUTPUT.mkdir(parents=True, exist_ok=True)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
    if not levels.load_level(MAP_PATH):
        raise RuntimeError(f"Could not load {MAP_PATH}")
else:
    if not levels.new_level(MAP_PATH):
        raise RuntimeError(f"Could not create {MAP_PATH}")

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for existing in actors.get_all_level_actors():
    actors.destroy_actor(existing)

mesh = unreal.EditorAssetLibrary.load_asset(MESH_PATH)
if not isinstance(mesh, unreal.SkeletalMesh):
    raise RuntimeError(f"Missing I06 production shell: {MESH_PATH}")
actor = actors.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(), unreal.Rotator())
actor.set_actor_label("V25_I06_UNCORRUPTED_PRODUCTION_SHELL")
actor.skeletal_mesh_component.set_skeletal_mesh_asset(mesh)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
target = unreal.Vector(0, 0, 95)
add_rect_light(actors, "I06_Key", unreal.Vector(-150, 220, 245), target, 55.0, 210.0, 240.0, unreal.Color(255, 238, 218))
add_rect_light(actors, "I06_Fill", unreal.Vector(185, 155, 145), target, 30.0, 180.0, 220.0, unreal.Color(200, 220, 255))
add_rect_light(actors, "I06_Rim", unreal.Vector(45, -205, 215), target, 62.0, 160.0, 210.0, unreal.Color(220, 235, 255))
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(), unreal.Rotator())
sky.set_actor_label("I06_Sky")
sky.light_component.set_editor_property("intensity", 0.10)

levels.save_current_level()
capture(world, actors, "PrimaryOversuitV25_I06_UncorruptedProduction_Front", unreal.Vector(0, 365, 98), target, 30.0)
capture(world, actors, "PrimaryOversuitV25_I06_UncorruptedProduction_Profile", unreal.Vector(-365, 0, 98), target, 30.0)
capture(world, actors, "PrimaryOversuitV25_I06_UncorruptedProduction_Rear", unreal.Vector(0, -365, 100), target, 30.0)
capture(world, actors, "PrimaryOversuitV25_I06_UncorruptedProduction_ThreeQuarter", unreal.Vector(-245, 285, 122), target, 31.0)
levels.save_current_level()
unreal.log("PRIMARY OVERSUIT V25 I06: uncorrupted production shell rendered")
