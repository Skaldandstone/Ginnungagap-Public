"""Render the five clean Fab modular weapon composites for visual QA."""

from pathlib import Path

import unreal


MAP = "/Game/Assets/Maps/ModelLibrary/L_SalvageGameplayBatch03_Unreal"
ROOT = "/Game/Assets/Gameplay/SalvageBatch03/Blueprints/Gear"
PROJECT = Path(unreal.SystemLibrary.get_project_directory())
OUTPUT = PROJECT / "Saved/WeaponReviews/FabCompositeBatch03"
WEAPONS = (
    "ThermalMiningLance",
    "RegolithAuger",
    "ExplosiveBoltRemover",
    "MagneticScrapFlinger",
    "DiamondCableSaw",
)


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(MAP):
        raise RuntimeError(f"Could not load {MAP}")
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    base = unreal.Vector(5000, 0, 90)

    key = actors.spawn_actor_from_class(unreal.DirectionalLight, base, unreal.Rotator(-35, -35, 0))
    key.light_component.set_editor_property("intensity", 5.0)
    key.light_component.set_editor_property("light_color", unreal.Color(235, 242, 255, 255))
    fill = actors.spawn_actor_from_class(unreal.RectLight, base + unreal.Vector(20, -180, 180), unreal.Rotator())
    fill.light_component.set_editor_property("intensity", 3800.0)
    fill.light_component.set_editor_property("source_width", 220.0)
    fill.light_component.set_editor_property("source_height", 220.0)

    camera_location = base + unreal.Vector(190, -310, 145)
    target = base + unreal.Vector(0, 0, 20)
    rotation = unreal.MathLibrary.find_look_at_rotation(camera_location, target)

    for weapon_id in WEAPONS:
        bp = unreal.EditorAssetLibrary.load_asset(f"{ROOT}/BP_Weapon_{weapon_id}")
        if not isinstance(bp, unreal.Blueprint):
            raise RuntimeError(f"Missing weapon Blueprint: {weapon_id}")
        weapon = actors.spawn_actor_from_class(bp.generated_class(), base, unreal.Rotator())
        capture = actors.spawn_actor_from_class(unreal.SceneCapture2D, camera_location, rotation)
        component = capture.get_editor_property("capture_component2d")
        render_target = unreal.RenderingLibrary.create_render_target2d(
            world,
            900,
            600,
            unreal.TextureRenderTargetFormat.RTF_RGBA8,
            unreal.LinearColor(.004, .007, .012, 1.0),
            False,
            False,
        )
        render_target.set_editor_property("target_gamma", 2.2)
        component.set_editor_property("texture_target", render_target)
        component.set_editor_property("fov_angle", 42.0)
        component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
        component.set_editor_property("capture_every_frame", False)
        component.set_editor_property("capture_on_movement", False)
        component.capture_scene()
        unreal.RenderingLibrary.export_render_target(world, render_target, str(OUTPUT), f"{weapon_id}.png")
        actors.destroy_actor(capture)
        actors.destroy_actor(weapon)

    actors.destroy_actor(fill)
    actors.destroy_actor(key)
    missing = [name for name in WEAPONS if not (OUTPUT / f"{name}.png").is_file()]
    if missing:
        raise RuntimeError("Missing weapon review renders: " + ", ".join(missing))
    unreal.log(f"Rendered {len(WEAPONS)} Fab modular weapon reviews to {OUTPUT}")


if __name__ == "__main__":
    main()
