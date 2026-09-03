"""Assemble and render V25 Iteration 02 concept modules around the fitted skeletal shell."""

from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
OUTPUT = PROJECT / "Saved/Renders"
MAP_PATH = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt/Maps/L_PrimaryOversuit_V25_ConceptSilhouette_I02"
SHELL_PATH = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt/Working/Iteration_02_ConceptSilhouette/SKM_PrimaryOversuit_QuinnProjectionShell_I02"
MODULE_ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt/Working/Iteration_02_ConceptSilhouette"
MODULES = [
    "V25_HelmetShell", "V25_Visor", "V25_VisorGasket", "V25_PressureCollar",
    "V25_CONCEPT_HelmetBrowRing", "V25_CONCEPT_HelmetCrownRail",
    "V25_ChestPlate", "V25_CONCEPT_ChestComputerBezel", "V25_CONCEPT_ChestComputerScreen",
    "V25_LifeSupportPack", "V25_CONCEPT_BackpackFrame", "V25_CONCEPT_BackpackServicePanel",
    "V25_Forearm_L", "V25_Forearm_R", "V25_ForearmComputer",
    "V25_Knee_L", "V25_Knee_R", "V25_Boot_L", "V25_Boot_R",
]


def add_rect_light(actors, label, location, target, intensity, width, height):
    light = actors.spawn_actor_from_class(unreal.RectLight, location, unreal.MathLibrary.find_look_at_rotation(location, target))
    light.set_actor_label(label)
    light.rect_light_component.set_editor_property("intensity", intensity)
    light.rect_light_component.set_editor_property("source_width", width)
    light.rect_light_component.set_editor_property("source_height", height)


def capture(world, actors, filename, location, target, fov=35.0):
    actor = actors.spawn_actor_from_class(unreal.SceneCapture2D, location, unreal.MathLibrary.find_look_at_rotation(location, target))
    actor.set_actor_label(f"RENDER_{filename}")
    component = actor.capture_component2d
    component.capture_every_frame = False
    component.capture_on_movement = False
    component.fov_angle = fov
    texture = unreal.RenderingLibrary.create_render_target2d(
        world, 1200, 1600, unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0.012, 0.016, 0.022, 1.0),
    )
    component.texture_target = texture
    component.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    pp = component.post_process_settings
    pp.override_auto_exposure_bias = True
    pp.auto_exposure_bias = -1.5
    component.post_process_settings = pp
    component.capture_scene()
    component.capture_scene()
    unreal.RenderingLibrary.export_render_target(world, texture, str(OUTPUT), filename)
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
shell = actors.spawn_actor_from_class(unreal.SkeletalMeshActor, unreal.Vector(), unreal.Rotator())
shell.set_actor_label("WORKING_V25_ProjectionShell_I01")
shell.skeletal_mesh_component.set_skeletal_mesh_asset(shell_asset)

# These authored modules used X for body depth and Y for left/right, while Manny
# uses Y for depth and X for left/right. Rotate -90 degrees and remove the old
# 325 m lateral staging offset while converting millimetres to centimetres.
module_transform_location = unreal.Vector(325, 0, 0)
module_transform_scale = unreal.Vector(0.01, 0.01, 0.01)
module_transform_rotation = unreal.Rotator(yaw=-90.0)
for name in MODULES:
    asset = unreal.EditorAssetLibrary.load_asset(f"{MODULE_ROOT}/{name}")
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError(f"Missing V25 I02 module: {name}")
    location = unreal.Vector(module_transform_location.x, 0, 0)
    scale = unreal.Vector(module_transform_scale.x, module_transform_scale.y, module_transform_scale.z)
    if any(token in name for token in ("Helmet", "Visor", "PressureCollar")):
        # Enlarge the pressure enclosure about its authored centre without lifting it.
        location = unreal.Vector(357.5, 0, -14.5)
        scale = unreal.Vector(0.011, 0.011, 0.011)
    elif any(token in name for token in ("Chest", "Forearm", "Knee", "Boot")):
        # Give forward hard points enough clearance over the new soft shell.
        location = unreal.Vector(325, -6.0, 0)
    elif any(token in name for token in ("LifeSupport", "Backpack")):
        location = unreal.Vector(325, 10.0, 0)
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, location, module_transform_rotation)
    actor.set_actor_label(f"WORKING_{name}")
    actor.set_actor_scale3d(scale)
    actor.static_mesh_component.set_static_mesh(asset)

target = unreal.Vector(0, 3, 92)
add_rect_light(actors, "REVIEW_Key", unreal.Vector(-150, -210, 245), target, 350.0, 160.0, 160.0)
add_rect_light(actors, "REVIEW_Fill", unreal.Vector(170, -150, 130), target, 150.0, 120.0, 180.0)
add_rect_light(actors, "REVIEW_Rim", unreal.Vector(0, 190, 210), target, 280.0, 110.0, 150.0)
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(), unreal.Rotator())
sky.set_actor_label("REVIEW_Sky")
sky.light_component.set_editor_property("intensity", 0.22)

level.save_current_level()
capture(world, actors, "PrimaryOversuitV25_I02_ConceptAligned_Front", unreal.Vector(0, -390, 95), target)
capture(world, actors, "PrimaryOversuitV25_I02_ConceptAligned_Profile", unreal.Vector(-390, 5, 95), target)
capture(world, actors, "PrimaryOversuitV25_I02_ConceptAligned_Rear", unreal.Vector(0, 395, 100), target)
capture(world, actors, "PrimaryOversuitV25_I02_ConceptAligned_ThreeQuarter", unreal.Vector(-255, -300, 125), target)
level.save_current_level()
unreal.log("Rendered V25 I02 concept silhouette review")
