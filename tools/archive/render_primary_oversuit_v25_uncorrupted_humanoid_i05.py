"""Assemble and render the V25 I05 uncorrupted-humanoid suit pass."""

from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
OUTPUT = PROJECT / "Saved/Renders"
MAP_PATH = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt/Maps/L_PrimaryOversuit_V25_UncorruptedHumanoid_I05"
ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt"
SHELL_PATH = ROOT + "/Working/Iteration_02_ConceptSilhouette/SKM_PrimaryOversuit_QuinnProjectionShell_I02"
MODULE_ROOT = ROOT + "/Working/Iteration_05_UncorruptedHumanoid"
MODULES = (
    "SM_V25_I05_VisorEnvelope",
    "SM_V25_I05_HelmetPressureHardware",
    "SM_V25_I05_LoadBearingHarness",
    "SM_V25_I05_ChestRigBacking",
    "SM_V25_I05_ChestEquipment",
    "SM_V25_I05_ChestDisplay",
    "SM_V25_I05_UtilityPouches",
    "SM_V25_I05_ForearmHousings",
    "SM_V25_I05_ForearmDisplay",
    "SM_V25_I05_KneeShinArmor",
    "SM_V25_I05_PressureBootHardware",
    "SM_V25_I05_LifeSupportPack",
    "SM_V25_I05_LifeSupportServicePanel",
    "SM_V25_I05_OrangeIndexing",
)


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
        unreal.LinearColor(0.055, 0.058, 0.062, 1.0),
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
    pp.set_editor_property("auto_exposure_bias", 1.0)
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

shell_asset = unreal.EditorAssetLibrary.load_asset(SHELL_PATH)
if not isinstance(shell_asset, unreal.SkeletalMesh):
    raise RuntimeError(f"Missing Quinn shell: {SHELL_PATH}")
fabric = unreal.EditorAssetLibrary.load_asset(
    MODULE_ROOT + "/Materials/M_V25_I05B_WarmPressureFabric"
)
if not isinstance(fabric, unreal.MaterialInterface):
    raise RuntimeError("Missing I05 pressure-fabric material")

shell = actors.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(), unreal.Rotator())
shell.set_actor_label("V25_I05_WARM_PRESSURE_GARMENT")
shell.skeletal_mesh_component.set_skeletal_mesh_asset(shell_asset)
for material_index in range(4):
    shell.skeletal_mesh_component.set_material(material_index, fabric)

for name in MODULES:
    path = f"{MODULE_ROOT}/{name}"
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError(f"Missing I05 concept module: {path}")
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(), unreal.Rotator())
    actor.set_actor_label(f"V25_I05_{name}")
    actor.static_mesh_component.set_static_mesh(asset)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.EditorAssetLibrary.save_loaded_asset(fabric, only_if_is_dirty=False)

target = unreal.Vector(0, 0, 94)
add_rect_light(
    actors, "I05_Key", unreal.Vector(-145, -215, 240), target,
    60.0, 175.0, 210.0, unreal.Color(255, 235, 210)
)
add_rect_light(
    actors, "I05_Fill", unreal.Vector(175, -150, 135), target,
    30.0, 140.0, 190.0, unreal.Color(200, 220, 255)
)
add_rect_light(
    actors, "I05_Rim", unreal.Vector(40, 195, 205), target,
    70.0, 125.0, 180.0, unreal.Color(220, 232, 255)
)
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(), unreal.Rotator())
sky.set_actor_label("I05_Sky")
sky.light_component.set_editor_property("intensity", 0.075)

levels.save_current_level()
capture(world, actors, "PrimaryOversuitV25_I05_UncorruptedHumanoid_Front", unreal.Vector(0, -395, 96), target)
capture(world, actors, "PrimaryOversuitV25_I05_UncorruptedHumanoid_Profile", unreal.Vector(-395, 0, 96), target)
capture(world, actors, "PrimaryOversuitV25_I05_UncorruptedHumanoid_Rear", unreal.Vector(0, 395, 98), target)
capture(world, actors, "PrimaryOversuitV25_I05_UncorruptedHumanoid_ThreeQuarter", unreal.Vector(-255, -305, 122), target)
levels.save_current_level()
unreal.log("PRIMARY OVERSUIT V25 I05: uncorrupted-humanoid review rendered")
