"""Render orthographic silhouette gates and beauty views for Iteration 09."""
from __future__ import annotations

import json
import math
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
OUTPUT = PROJECT / "Art/Ships/Exterior/UnrealSculptReview/ConceptReset09"
REPORT = PROJECT / "Saved/Reports/UnrealShipConceptResetRendersV09.json"
OUTPUT.mkdir(parents=True, exist_ok=True)

SHIPS = (
    ("MilitaryCorvette", "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_ConceptReset09"),
    ("ExpeditionCarrier", "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_ConceptReset09"),
)
VIEWS = ("Side", "Top", "Rear", "Front", "Beauty")
PREFIX = "RESET09_"


def visible_hulls(actor_subsystem):
    result = []
    old_prefixes = ("FAB_HULL_", "SCULPT_WORKING_", "FAB_CONCEPT_", "CONCEPT06_",
                    "HARD07_", "CLEAN08_")
    for actor in actor_subsystem.get_all_level_actors():
        label = actor.get_actor_label()
        if label.startswith(PREFIX):
            actor.set_actor_hidden_in_game(False)
            actor.set_is_temporarily_hidden_in_editor(False)
            result.append(actor)
        elif label.startswith(old_prefixes):
            actor.set_actor_hidden_in_game(True)
            actor.set_is_temporarily_hidden_in_editor(True)
    return result


def combined_bounds(hulls):
    lo = unreal.Vector(1e30, 1e30, 1e30)
    hi = unreal.Vector(-1e30, -1e30, -1e30)
    for actor in hulls:
        origin, extent = actor.get_actor_bounds(False)
        lo.x, lo.y, lo.z = min(lo.x, origin.x - extent.x), min(lo.y, origin.y - extent.y), min(lo.z, origin.z - extent.z)
        hi.x, hi.y, hi.z = max(hi.x, origin.x + extent.x), max(hi.y, origin.y + extent.y), max(hi.z, origin.z + extent.z)
    return (
        unreal.Vector((lo.x + hi.x) * 0.5, (lo.y + hi.y) * 0.5, (lo.z + hi.z) * 0.5),
        unreal.Vector(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z),
    )


def camera_for(view, center, size):
    length, beam, height = size.x, size.y, size.z
    gate_fov = 12.0
    def distance_for(span):
        return (span * 0.5) / math.tan(math.radians(gate_fov * 0.5))
    if view == "Side":
        span = length * 1.08
        return unreal.Vector(center.x, center.y - distance_for(span), center.z), gate_fov, True
    if view == "Top":
        span = length * 1.08
        return unreal.Vector(center.x, center.y, center.z + distance_for(span)), gate_fov, True
    cross_width = max(beam * 1.2, height * 1.2 * (1600.0 / 900.0))
    if view == "Rear":
        return unreal.Vector(center.x - distance_for(cross_width), center.y, center.z), gate_fov, True
    if view == "Front":
        return unreal.Vector(center.x + distance_for(cross_width), center.y, center.z), gate_fov, True
    return (
        unreal.Vector(center.x + length * 0.20, center.y - length * 1.82,
                      center.z + length * 0.38),
        38.0,
        False,
    )


def prepare_render(ship, map_path, view):
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(map_path):
        raise RuntimeError(f"Could not load {map_path}")
    world = unreal.EditorLevelLibrary.get_editor_world()
    hulls = visible_hulls(actors)
    if not hulls:
        raise RuntimeError(f"No {PREFIX} actors in {map_path}")
    center, size = combined_bounds(hulls)
    camera_location, camera_fov, gate_view = camera_for(view, center, size)
    rotation = unreal.MathLibrary.find_look_at_rotation(camera_location, center)
    if view == "Top":
        rotation.roll = 90.0

    lights = []
    for light_rotation, intensity, color in (
        (unreal.Rotator(-38, -48, -8), 2.4, unreal.Color(235, 239, 245, 255)),
        (unreal.Rotator(22, 132, 6), 1.1, unreal.Color(92, 124, 180, 255)),
        (unreal.Rotator(8, 25, 170), 0.65, unreal.Color(160, 184, 220, 255)),
        (rotation, 0.9, unreal.Color(210, 220, 238, 255)),
    ):
        light = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(), light_rotation)
        light.set_actor_label("RENDER_ConceptReset09_TemporaryLight")
        light.light_component.set_editor_property("intensity", intensity)
        light.light_component.set_editor_property("light_color", color)
        lights.append(light)

    capture = actors.spawn_actor_from_class(unreal.SceneCapture2D, camera_location, rotation)
    component = capture.get_editor_property("capture_component2d")
    target = unreal.RenderingLibrary.create_render_target2d(
        world, 1600, 900, unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0.001, 0.002, 0.004, 1.0), False, False,
    )
    target.set_editor_property("target_gamma", 2.2)
    component.set_editor_property("texture_target", target)
    component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    component.set_editor_property("capture_every_frame", False)
    component.set_editor_property("capture_on_movement", False)
    # Native orthographic capture clips to black at these kilometer-scale
    # widths.  A 12-degree long lens is an effectively orthographic gate while
    # retaining stable large-world rendering.
    component.set_editor_property("projection_type", unreal.CameraProjectionMode.PERSPECTIVE)
    component.set_editor_property("fov_angle", camera_fov)
    unreal.SystemLibrary.execute_console_command(world, "r.MotionBlurQuality 0")
    unreal.SystemLibrary.execute_console_command(world, "r.ScreenPercentage 100")
    unreal.SystemLibrary.execute_console_command(world, "r.DefaultFeature.AutoExposure 0")
    unreal.SystemLibrary.execute_console_command(world, "r.EyeAdaptationQuality 0")
    filename = f"{ship}_ConceptReset09_{view}.png"
    return {
        "world": world, "actors": actors, "capture": capture, "component": component,
        "target": target, "lights": lights, "filename": filename,
        "row": {
            "ship": ship, "view": view, "map": map_path, "file": str(OUTPUT / filename),
            "actor_count": len(hulls), "bounds_size_cm": [size.x, size.y, size.z],
            "projection": "long-lens orthographic approximation" if gate_view else "perspective",
            "camera_location_cm": [camera_location.x, camera_location.y, camera_location.z],
        },
    }


def finish(job):
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
        raise RuntimeError(f"Invalid render: {output}")
    job["row"]["bytes"] = output.stat().st_size
    return job["row"]


JOBS = [(ship, map_path, view) for ship, map_path in SHIPS for view in VIEWS]
state = {"index": 0, "seconds": 0.0, "rows": [], "handle": None,
         "job": prepare_render(*JOBS[0])}
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


def tick(delta_seconds):
    state["seconds"] += delta_seconds
    warmup = 14.0 if state["index"] in (0, len(VIEWS)) else 5.0
    if state["seconds"] < warmup:
        return
    try:
        state["rows"].append(finish(state["job"]))
        state["index"] += 1
        if state["index"] < len(JOBS):
            state["seconds"] = 0.0
            state["job"] = prepare_render(*JOBS[state["index"]])
            return
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(json.dumps({"version": 1, "renders": state["rows"]}, indent=2), encoding="utf-8")
        unreal.log("UNREAL SHIP CONCEPT RESET V09 RENDER: complete")
    finally:
        if state["index"] >= len(JOBS):
            unreal.unregister_slate_post_tick_callback(state["handle"])
            unreal.EditorPythonScripting.set_keep_python_script_alive(False)
            unreal.SystemLibrary.quit_editor()


state["handle"] = unreal.register_slate_post_tick_callback(tick)
