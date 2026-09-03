"""Render repaired Unreal ship sculpt assemblies from their saved review cameras."""
from pathlib import Path
import json
import unreal

PROJECT = Path(unreal.SystemLibrary.get_project_directory())
OUTPUT = PROJECT / "Art/Ships/Exterior/UnrealSculptReview"
REPORT = PROJECT / "Saved/Reports/UnrealShipSculptReviewRenders.json"
OUTPUT.mkdir(parents=True, exist_ok=True)

SHIPS = (
    ("MilitaryCorvette", "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_Sculpt"),
    ("ExpeditionCarrier", "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_Sculpt"),
)


def actor_by_label(label):
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if actor.get_actor_label() == label:
            return actor
    return None


def render_ship(ship, map_path):
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level.load_level(map_path):
        raise RuntimeError(f"Could not load {map_path}")
    world = unreal.EditorLevelLibrary.get_editor_world()
    camera = actor_by_label("CAM_Sculpt_ThreeQuarter")
    if not isinstance(camera, unreal.CameraActor):
        raise RuntimeError(f"Three-quarter review camera missing in {map_path}")

    # Neutral clay/grid override makes this a silhouette review and avoids waiting
    # for unrelated editor-material permutations during an automated capture.
    review_material = unreal.EditorAssetLibrary.load_asset(
        "/Engine/EngineMaterials/WorldGridMaterial.WorldGridMaterial"
    )
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if not isinstance(actor, unreal.StaticMeshActor) or not actor.get_actor_label().startswith("SCULPT_WORKING_"):
            continue
        component = actor.static_mesh_component
        for material_index in range(component.get_num_materials()):
            component.set_material(material_index, review_material)

    # Add a restrained camera-side fill so the dark sculpt material remains readable
    # against space without flattening the primary directional-light form.
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    fill = actor_subsystem.spawn_actor_from_class(
        unreal.DirectionalLight,
        camera.get_actor_location(),
        unreal.Rotator(18.0, -80.0, 0.0),
    )
    fill.set_actor_label("RENDER_TemporaryFill")
    fill.light_component.set_editor_property("intensity", 1.75)
    fill.light_component.set_editor_property("light_color", unreal.Color(92, 122, 160, 255))

    capture = actor_subsystem.spawn_actor_from_class(
        unreal.SceneCapture2D,
        camera.get_actor_location(),
        camera.get_actor_rotation(),
    )
    component = capture.get_editor_property("capture_component2d")
    target = unreal.RenderingLibrary.create_render_target2d(
        world,
        1600,
        900,
        unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0.002, 0.004, 0.009, 1.0),
        False,
        False,
    )
    target.set_editor_property("target_gamma", 2.2)
    component.set_editor_property("texture_target", target)
    component.set_editor_property("fov_angle", camera.camera_component.get_editor_property("field_of_view"))
    component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    component.set_editor_property("capture_every_frame", False)
    component.set_editor_property("capture_on_movement", False)

    unreal.SystemLibrary.execute_console_command(world, "r.ScreenPercentage 100")
    unreal.SystemLibrary.execute_console_command(world, "r.MotionBlurQuality 0")
    unreal.SystemLibrary.execute_console_command(world, "r.TemporalAA.Upsampling 1")
    component.capture_scene()
    filename = f"{ship}_Cleanup01_ThreeQuarter.png"
    unreal.RenderingLibrary.export_render_target(world, target, str(OUTPUT), filename)
    actor_subsystem.destroy_actor(capture)
    actor_subsystem.destroy_actor(fill)
    path = OUTPUT / filename
    if not path.exists() or path.stat().st_size < 10000:
        raise RuntimeError(f"Review render was not written correctly: {path}")
    unreal.log(f"SHIP SCULPT REVIEW rendered {path}")
    return {"ship": ship, "map": map_path, "file": str(path), "bytes": path.stat().st_size}


renders = [render_ship(ship, map_path) for ship, map_path in SHIPS]
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"version": 1, "renders": renders}, indent=2), encoding="utf-8")
unreal.log("Unreal ship sculpt review renders complete")
