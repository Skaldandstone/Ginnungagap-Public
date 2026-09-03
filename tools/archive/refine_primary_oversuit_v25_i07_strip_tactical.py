"""Strip the donor tactical-bags section from the saved I07 role lineup and recapture."""

from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory()).resolve()
OUTPUT = PROJECT / "Saved/Renders"
ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt"
MAP_PATH = ROOT + "/Maps/L_PrimaryOversuit_V25_ConceptAligned_I07"
MESH_PATH = ROOT + "/Working/Iteration_06_UncorruptedProductionShell/Source/SKM_V25_I06_SpaceMarshalMale"
HIDDEN_PATH = ROOT + "/Working/Iteration_07_ConceptAlignedRoleLineup/Materials/M_V25_I07_HiddenDonorSection"


def capture(world, actors):
    camera = actors.spawn_actor_from_class(
        unreal.SceneCapture2D,
        unreal.Vector(0, -690, 112),
        unreal.MathLibrary.find_look_at_rotation(
            unreal.Vector(0, -690, 112), unreal.Vector(0, 0, 105)
        ),
    )
    camera.set_actor_label("RENDER_I07_CONCEPT_ALIGNED_STRIPPED")
    component = camera.capture_component2d
    component.capture_every_frame = False
    component.capture_on_movement = False
    component.fov_angle = 31.0
    texture = unreal.RenderingLibrary.create_render_target2d(
        world, 1800, 1200, unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0.075, 0.080, 0.088, 1.0),
    )
    component.texture_target = texture
    component.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    pp = component.post_process_settings
    pp.set_editor_property("override_auto_exposure_method", True)
    pp.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    pp.set_editor_property("override_camera_iso", True)
    pp.set_editor_property("camera_iso", 160.0)
    pp.set_editor_property("override_camera_shutter_speed", True)
    pp.set_editor_property("camera_shutter_speed", 60.0)
    pp.set_editor_property("override_auto_exposure_bias", True)
    pp.set_editor_property("auto_exposure_bias", 1.15)
    component.post_process_settings = pp
    component.capture_scene()
    component.capture_scene()
    unreal.RenderingLibrary.export_render_target(
        world, texture, str(OUTPUT), "PrimaryOversuitV25_I07_ConceptAligned_Lineup_Stripped"
    )
    camera.destroy_actor()


levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP_PATH):
    raise RuntimeError(f"Could not load {MAP_PATH}")
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
mesh = unreal.EditorAssetLibrary.load_asset(MESH_PATH)
hidden = unreal.EditorAssetLibrary.load_asset(HIDDEN_PATH)
if not isinstance(mesh, unreal.SkeletalMesh) or not isinstance(hidden, unreal.MaterialInterface):
    raise RuntimeError("I07 refinement prerequisites are missing")

slots = list(mesh.get_editor_property("materials"))
bag_indices = [
    index for index, slot in enumerate(slots)
    if any(
        token in str(slot.get_editor_property("material_slot_name")).lower()
        for token in ("sm_bags", "sm_pouch")
    )
]
if not bag_indices:
    raise RuntimeError("Could not locate SM_Bags/SM_Pouch donor material sections")

updated = 0
for actor in actors.get_all_level_actors():
    if not isinstance(actor, unreal.SkeletalMeshActor) or not actor.get_actor_label().startswith("I07_"):
        continue
    for index in bag_indices:
        actor.skeletal_mesh_component.set_material(index, hidden)
    updated += 1

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
levels.save_current_level()
capture(world, actors)
levels.save_current_level()
unreal.log(f"PRIMARY OVERSUIT V25 I07: stripped donor tactical bags from {updated} role actors")
