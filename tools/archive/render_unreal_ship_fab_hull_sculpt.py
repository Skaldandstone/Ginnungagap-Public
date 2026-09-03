"""Render the textured Fab hull sculpt maps from deterministic review cameras."""
from pathlib import Path
import json

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
OUTPUT = PROJECT / "Art/Ships/Exterior/UnrealSculptReview/FabHullSculpt"
REPORT = PROJECT / "Saved/Reports/UnrealShipFabHullSculptRenders.json"
OUTPUT.mkdir(parents=True, exist_ok=True)

SHIPS = (
    ("MilitaryCorvette", "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_FabHullSculpt"),
    ("ExpeditionCarrier", "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_FabHullSculpt"),
)


def hull_actors(actor_subsystem):
    result = []
    for actor in actor_subsystem.get_all_level_actors():
        label = actor.get_actor_label()
        if label.startswith("FAB_HULL_"):
            actor.set_actor_hidden_in_game(False)
            actor.set_is_temporarily_hidden_in_editor(False)
            result.append(actor)
        elif label.startswith("SCULPT_WORKING_") or label.startswith("FAB_CONCEPT_"):
            actor.set_actor_hidden_in_game(True)
            actor.set_is_temporarily_hidden_in_editor(True)
    return result


def combined_bounds(hulls):
    lo = unreal.Vector(1e30, 1e30, 1e30)
    hi = unreal.Vector(-1e30, -1e30, -1e30)
    for actor in hulls:
        origin, extent = actor.get_actor_bounds(False)
        lo.x = min(lo.x, origin.x - extent.x)
        lo.y = min(lo.y, origin.y - extent.y)
        lo.z = min(lo.z, origin.z - extent.z)
        hi.x = max(hi.x, origin.x + extent.x)
        hi.y = max(hi.y, origin.y + extent.y)
        hi.z = max(hi.z, origin.z + extent.z)
    center = unreal.Vector((lo.x + hi.x) * 0.5, (lo.y + hi.y) * 0.5, (lo.z + hi.z) * 0.5)
    size = unreal.Vector(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
    return center, size


def prepare_render(ship, map_path):
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(map_path):
        raise RuntimeError(f"Could not load {map_path}")
    world = unreal.EditorLevelLibrary.get_editor_world()
    hulls = hull_actors(actors)
    if not hulls:
        raise RuntimeError(f"No FAB_HULL actors found in {map_path}")
    center, size = combined_bounds(hulls)
    length = size.x
    camera_location = unreal.Vector(
        center.x + length * 0.18,
        center.y - length * 1.62,
        center.z + length * 0.34,
    )
    camera_rotation = unreal.MathLibrary.find_look_at_rotation(camera_location, center)

    # Soft key/fill/rim keeps the native Fab materials legible without washing
    # out their normal maps, emissive strips, and roughness breakup.
    lights = []
    for rotation, intensity, color in (
        (unreal.Rotator(-32, -52, -12), 12.0, unreal.Color(230, 238, 255, 255)),
        (unreal.Rotator(18, 128, 6), 6.0, unreal.Color(88, 126, 200, 255)),
        (unreal.Rotator(6, 28, 168), 3.0, unreal.Color(160, 188, 255, 255)),
        (camera_rotation, 9.0, unreal.Color(210, 222, 242, 255)),
    ):
        light = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(), rotation)
        light.set_actor_label("RENDER_FabHull_TemporaryLight")
        light.light_component.set_editor_property("intensity", intensity)
        light.light_component.set_editor_property("light_color", color)
        lights.append(light)

    capture = actors.spawn_actor_from_class(
        unreal.SceneCapture2D, camera_location, camera_rotation
    )
    component = capture.get_editor_property("capture_component2d")
    target = unreal.RenderingLibrary.create_render_target2d(
        world, 1600, 900, unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0.002, 0.004, 0.009, 1.0), False, False
    )
    target.set_editor_property("target_gamma", 2.2)
    component.set_editor_property("texture_target", target)
    component.set_editor_property("fov_angle", 38.0)
    component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    component.set_editor_property("capture_every_frame", False)
    component.set_editor_property("capture_on_movement", False)
    unreal.SystemLibrary.execute_console_command(world, "r.MotionBlurQuality 0")
    unreal.SystemLibrary.execute_console_command(world, "r.ScreenPercentage 100")
    unreal.SystemLibrary.execute_console_command(world, "r.DefaultFeature.AutoExposure 1")
    unreal.SystemLibrary.execute_console_command(world, "r.EyeAdaptationQuality 2")
    # The first capture primes scene proxies/material resources in commandlet mode.
    filename = f"{ship}_FabHullSculpt_ThreeQuarter.png"
    row = {
        "ship": ship,
        "map": map_path,
        "file": str(OUTPUT / filename),
        "hull_actor_count": len(hulls),
        "bounds_center_cm": [center.x, center.y, center.z],
        "bounds_size_cm": [size.x, size.y, size.z],
        "camera_location_cm": [camera_location.x, camera_location.y, camera_location.z],
        "camera_rotation_deg": [camera_rotation.pitch, camera_rotation.yaw, camera_rotation.roll],
    }
    return {
        "world": world,
        "actors": actors,
        "capture": capture,
        "component": component,
        "target": target,
        "lights": lights,
        "filename": filename,
        "row": row,
    }


def finish_render(job):
    # Commandlet shader compilation and scene-proxy creation are asynchronous.
    # This is deliberately called from a delayed editor tick, after the map has
    # had enough rendered frames to finish both rather than exporting fallback black.
    job["component"].capture_scene()
    job["component"].capture_scene()
    unreal.RenderingLibrary.export_render_target(
        job["world"], job["target"], str(OUTPUT), job["filename"]
    )
    job["actors"].destroy_actor(job["capture"])
    for light in job["lights"]:
        job["actors"].destroy_actor(light)
    output = Path(job["row"]["file"])
    if not output.exists() or output.stat().st_size < 10000:
        raise RuntimeError(f"Render output invalid: {output}")
    job["row"]["bytes"] = output.stat().st_size
    return job["row"]


state = {"index": 0, "seconds": 0.0, "job": prepare_render(*SHIPS[0]), "rows": [], "handle": None}
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


def capture_after_shader_warmup(delta_seconds):
    state["seconds"] += delta_seconds
    if state["seconds"] < 20.0:
        return
    try:
        state["rows"].append(finish_render(state["job"]))
        state["index"] += 1
        if state["index"] < len(SHIPS):
            state["seconds"] = 0.0
            state["job"] = prepare_render(*SHIPS[state["index"]])
            return
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(
            json.dumps({"version": 2, "renders": state["rows"]}, indent=2), encoding="utf-8"
        )
        unreal.log("UNREAL FAB HULL SCULPT RENDER: complete after shader warmup")
    finally:
        if state["index"] >= len(SHIPS):
            unreal.unregister_slate_post_tick_callback(state["handle"])
            unreal.EditorPythonScripting.set_keep_python_script_alive(False)
            unreal.SystemLibrary.quit_editor()


state["handle"] = unreal.register_slate_post_tick_callback(capture_after_shader_warmup)
