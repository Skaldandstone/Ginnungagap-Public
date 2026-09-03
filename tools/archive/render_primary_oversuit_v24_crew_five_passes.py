"""Render a deterministic geometry-normal review of the five Crew passes."""

from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
OUTPUT = PROJECT / "Saved" / "Renders"
MAP_PATH = "/Game/Characters/PlayerSuits/PrimaryOversuits/V24Sculpt/Maps/L_PrimaryOversuit_V24_Sculpt"
MORPHS = (
    "V24_SharedFit_I01",
    "V24_Crew_01_SilhouetteCleanup",
    "V24_Crew_02_HelmetCollar",
    "V24_Crew_03_EquipmentSettle",
    "V24_Crew_04_MobilityClearance",
)


def hidden(actor, value: bool) -> None:
    actor.set_actor_hidden_in_game(value)
    actor.set_is_temporarily_hidden_in_editor(value)


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP_PATH)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = subsystem.get_all_level_actors()
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
        raise RuntimeError("Crew working actor is missing")
    mesh = crew.skeletal_mesh_component.get_skeletal_mesh_asset()
    missing = sorted(set(MORPHS).difference(mesh.get_all_morph_target_names()))
    if missing:
        raise RuntimeError(f"Crew review mesh is missing morphs: {missing}")

    for actor in actors:
        if not isinstance(actor, (unreal.DirectionalLight, unreal.SkyLight)):
            hidden(actor, actor != crew)

    crew.set_actor_location(unreal.Vector(0.0, -82.0, 0.0), False, False)
    for morph in MORPHS:
        crew.skeletal_mesh_component.set_morph_target(morph, 0.0, False)

    refined = subsystem.spawn_actor_from_class(
        unreal.SkeletalMeshActor,
        unreal.Vector(0.0, 82.0, 0.0),
        crew.get_actor_rotation(),
    )
    refined.skeletal_mesh_component.set_skinned_asset_and_update(mesh)
    for morph in MORPHS:
        refined.skeletal_mesh_component.set_morph_target(morph, 1.0, False)

    capture = subsystem.spawn_actor_from_class(
        unreal.SceneCapture2D,
        unreal.Vector(470.0, 0.0, 108.0),
        unreal.Rotator(roll=0.0, pitch=0.0, yaw=180.0),
    )
    component = capture.capture_component2d
    component.set_editor_property("capture_every_frame", False)
    component.set_editor_property("capture_on_movement", False)
    component.set_editor_property("fov_angle", 43.0)
    component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_NORMAL)
    render_target = unreal.RenderingLibrary.create_render_target2d(
        world,
        1800,
        1200,
        unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0.02, 0.02, 0.02, 1.0),
    )
    component.set_editor_property("texture_target", render_target)
    component.capture_scene()
    component.capture_scene()
    unreal.RenderingLibrary.export_render_target(
        world, render_target, str(OUTPUT), "PrimaryOversuitV24_CrewFivePasses_Normal"
    )
    unreal.log(f"Rendered Crew five-pass normal review to {OUTPUT}")


main()
