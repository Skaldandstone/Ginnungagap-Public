"""Assemble and render the V25 I04 full-body functional-detail review map."""

from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
OUTPUT = PROJECT / "Saved/Renders"
MAP_PATH = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt/Maps/L_PrimaryOversuit_V25_FunctionalDetail_I04"
ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt"
SHELL_PATH = ROOT + "/Working/Iteration_02_ConceptSilhouette/SKM_PrimaryOversuit_QuinnProjectionShell_I02"
I03_ROOT = ROOT + "/Working/Iteration_03_ConceptSculpt"
I04_ROOT = ROOT + "/Working/Iteration_04_FunctionalDetail"
I03_MODULES = (
    "SM_V25_I03_HelmetBubble",
    "SM_V25_I03_HelmetHardware",
    "SM_V25_I03_PressureCollar",
    "SM_V25_I03_HarnessStraps",
)
I04_MODULES = (
    "SM_V25_I04_ChestMount",
    "SM_V25_I04_ChestComputer",
    "SM_V25_I04_WaistHarness",
    "SM_V25_I04_WaistBuckle",
    "SM_V25_I04_ForearmGuards",
    "SM_V25_I04_ForearmDisplay",
    "SM_V25_I04_KneeGuards",
    "SM_V25_I04_BootArmor",
    "SM_V25_I04_LifeSupportPack",
    "SM_V25_I04_LifeSupportDetail",
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
        world,
        1200,
        1600,
        unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0.075, 0.080, 0.085, 1.0),
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


def spawn_static(actors, folder, name, prefix):
    path = f"{folder}/{name}"
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError(f"Missing concept module: {path}")
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(), unreal.Rotator())
    actor.set_actor_label(f"{prefix}_{name}")
    actor.static_mesh_component.set_static_mesh(asset)


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
    raise RuntimeError(f"Missing I02 Quinn shell: {SHELL_PATH}")
soft_material = unreal.EditorAssetLibrary.load_asset(
    I03_ROOT + "/Materials/M_V25_I03_SoftSuitReview"
)
if not isinstance(soft_material, unreal.MaterialInterface):
    raise RuntimeError("Missing I03 soft-suit review material")

shell = actors.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(), unreal.Rotator())
shell.set_actor_label("V25_I04_SOFT_PRESSURE_GARMENT")
shell.skeletal_mesh_component.set_skeletal_mesh_asset(shell_asset)
for material_index in range(4):
    shell.skeletal_mesh_component.set_material(material_index, soft_material)

for name in I03_MODULES:
    spawn_static(actors, I03_ROOT, name, "V25_I04_REUSED")
for name in I04_MODULES:
    spawn_static(actors, I04_ROOT, name, "V25_I04_NEW")

# Wait for the skeletal-use material permutation and every new static-mesh
# shader before capturing; otherwise commandlet rendering shows white fallback.
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
unreal.EditorAssetLibrary.save_loaded_asset(soft_material, only_if_is_dirty=False)

target = unreal.Vector(0, 0, 94)
add_rect_light(
    actors, "I04_Key", unreal.Vector(-145, -215, 240), target,
    65.0, 175.0, 210.0, unreal.Color(255, 238, 218)
)
add_rect_light(
    actors, "I04_Fill", unreal.Vector(175, -150, 135), target,
    32.0, 140.0, 190.0, unreal.Color(205, 225, 255)
)
add_rect_light(
    actors, "I04_Rim", unreal.Vector(40, 195, 205), target,
    75.0, 125.0, 180.0, unreal.Color(220, 232, 255)
)
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(), unreal.Rotator())
sky.set_actor_label("I04_Sky")
sky.light_component.set_editor_property("intensity", 0.08)

levels.save_current_level()
capture(world, actors, "PrimaryOversuitV25_I04_FunctionalDetail_Front", unreal.Vector(0, -395, 96), target)
capture(world, actors, "PrimaryOversuitV25_I04_FunctionalDetail_Profile", unreal.Vector(-395, 0, 96), target)
capture(world, actors, "PrimaryOversuitV25_I04_FunctionalDetail_Rear", unreal.Vector(0, 395, 98), target)
capture(world, actors, "PrimaryOversuitV25_I04_FunctionalDetail_ThreeQuarter", unreal.Vector(-255, -305, 122), target)
levels.save_current_level()
unreal.log("PRIMARY OVERSUIT V25 I04: functional-detail review rendered")
