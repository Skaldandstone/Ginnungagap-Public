"""Render a non-destructive before/after review of the V24 shared-fit morph."""

from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
OUTPUT = PROJECT / "Saved" / "Renders"
MAP_PATH = "/Game/Characters/PlayerSuits/PrimaryOversuits/V24Sculpt/Maps/L_PrimaryOversuit_V24_Sculpt"
MORPH_NAME = "V24_SharedFit_I01"
DIAGNOSTIC_MATERIAL_ROOT = (
    "/Game/Characters/PlayerSuits/PrimaryOversuits/V24Sculpt/References/Materials"
)


def set_hidden(actor, hidden: bool) -> None:
    actor.set_actor_hidden_in_game(hidden)
    actor.set_is_temporarily_hidden_in_editor(hidden)


def diagnostic_material(name: str, color: unreal.LinearColor) -> unreal.Material:
    path = f"{DIAGNOSTIC_MATERIAL_ROOT}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name,
        DIAGNOSTIC_MATERIAL_ROOT,
        unreal.Material,
        unreal.MaterialFactoryNew(),
    )
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    constant = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -250, 0
    )
    constant.set_editor_property("constant", color)
    unreal.MaterialEditingLibrary.connect_material_property(
        constant, "", unreal.MaterialProperty.MP_BASE_COLOR
    )
    unreal.MaterialEditingLibrary.connect_material_property(
        constant, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP_PATH)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = actor_subsystem.get_all_level_actors()

    crew = next(
        (
            actor
            for actor in actors
            if isinstance(actor, unreal.SkeletalMeshActor)
            and actor.get_actor_label() == "WORKING_ROLE_Crew_I01"
        ),
        None,
    )
    if not crew:
        raise RuntimeError("Crew working actor is missing from the V24 sculpt map")
    if MORPH_NAME not in crew.skeletal_mesh_component.get_skeletal_mesh_asset().get_all_morph_target_names():
        raise RuntimeError(f"Crew working mesh does not contain {MORPH_NAME}")

    for actor in actors:
        if isinstance(actor, (unreal.DirectionalLight, unreal.SkyLight)):
            continue
        set_hidden(actor, actor != crew)

    before = crew
    before.set_actor_label("REVIEW_BeforeSharedFit")
    before.set_actor_location(unreal.Vector(0.0, -82.0, 0.0), False, False)
    before.skeletal_mesh_component.set_morph_target(MORPH_NAME, 0.0, False)

    before_material = diagnostic_material(
        "M_DIAG_OversuitFit_Before", unreal.LinearColor(0.42, 0.37, 0.30, 1.0)
    )
    after_material = diagnostic_material(
        "M_DIAG_OversuitFit_After", unreal.LinearColor(0.16, 0.42, 0.52, 1.0)
    )

    after = actor_subsystem.spawn_actor_from_class(
        unreal.SkeletalMeshActor,
        unreal.Vector(0.0, 82.0, 0.0),
        before.get_actor_rotation(),
    )
    after.skeletal_mesh_component.set_skinned_asset_and_update(
        before.skeletal_mesh_component.get_skeletal_mesh_asset()
    )
    for material_index in range(before.skeletal_mesh_component.get_num_materials()):
        after.skeletal_mesh_component.set_material(
            material_index, before.skeletal_mesh_component.get_material(material_index)
        )
    after.set_actor_label("REVIEW_AfterSharedFit")
    set_hidden(after, False)
    after.skeletal_mesh_component.set_morph_target(MORPH_NAME, 1.0, False)
    for material_index in range(before.skeletal_mesh_component.get_num_materials()):
        before.skeletal_mesh_component.set_material(material_index, before_material)
        after.skeletal_mesh_component.set_material(material_index, after_material)

    for text, y in (("DONOR FIT", -82.0), ("V24 SHARED FIT", 82.0)):
        label = actor_subsystem.spawn_actor_from_class(
            unreal.TextRenderActor,
            unreal.Vector(25.0, y, 202.0),
            unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0),
        )
        label.text_render.set_text(text)
        label.text_render.set_editor_property("world_size", 8.0)
        label.text_render.set_editor_property("text_render_color", unreal.Color(210, 220, 225, 255))

    camera = actor_subsystem.spawn_actor_from_class(
        unreal.CameraActor,
        unreal.Vector(470.0, 0.0, 108.0),
        unreal.Rotator(roll=0.0, pitch=0.0, yaw=180.0),
    )
    camera.camera_component.set_editor_property("field_of_view", 43.0)

    for command in (
        "r.Lumen.DiffuseIndirect.Allow 0",
        "r.Lumen.Reflections.Allow 0",
        "r.Shadow.Virtual.Enable 0",
        "r.AntiAliasingMethod 1",
    ):
        unreal.SystemLibrary.execute_console_command(world, command)

    capture = actor_subsystem.spawn_actor_from_class(
        unreal.SceneCapture2D, camera.get_actor_location(), camera.get_actor_rotation()
    )
    component = capture.capture_component2d
    component.set_editor_property("capture_every_frame", False)
    component.set_editor_property("capture_on_movement", False)
    component.set_editor_property("fov_angle", 43.0)
    post_process = component.get_editor_property("post_process_settings")
    post_process.set_editor_property("override_auto_exposure_bias", True)
    post_process.set_editor_property("auto_exposure_bias", 6.0)
    component.set_editor_property("post_process_settings", post_process)
    component.set_editor_property("post_process_blend_weight", 1.0)
    render_target = unreal.RenderingLibrary.create_render_target2d(
        world,
        1800,
        1200,
        unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0.008, 0.010, 0.014, 1.0),
    )
    component.set_editor_property("texture_target", render_target)
    component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    component.capture_scene()
    component.capture_scene()
    unreal.RenderingLibrary.export_render_target(
        world, render_target, str(OUTPUT), "PrimaryOversuitV24_SharedFit_BeforeAfter"
    )
    unreal.log(f"Rendered V24 shared-fit comparison to {OUTPUT}")


main()
