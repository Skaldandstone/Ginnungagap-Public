"""Build clean Fab-derived robot prototypes and render RealityScan turntables.

The Unreal rigid-part assemblies remain the gameplay and animation masters.
RealityScan output is used only as a unified surface and retopology reference.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
MAP_PATH = "/Game/Assets/Maps/Robotics/L_Uncorrupted_FabRealityScan_Prototypes"
CAPTURE_ROOT = PROJECT / "Art/Robots/Uncorrupted/RealityScan"
REPORT_PATH = PROJECT / "Saved/Reports/UncorruptedRobotFabRealityScanCapture.json"
RENDER_SIZE = 1600
FOV_DEGREES = 42.0
AZIMUTHS = tuple(range(0, 360, 20))
ELEVATIONS = (-20, 20)

PROTOTYPES = (
    {
        "asset": "CompactMaintenanceRobot",
        "class": unreal.CompactMaintenanceRobot,
        "label": "ROBOT_CLEAN_RS_CompactMaintenance",
        "target": unreal.Vector(0.0, 0.0, 50.0),
        "radius_cm": 265.0,
        "design_authority": "docs/concept-art/reference/bloom/uncorrupted-robot-baselines.png",
        "fab_sources": [
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_BODY",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_ARM",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/LAMP/SM_SCANNER_01",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_MECHA_ARM_01",
        ],
        "project_sources": [
            "/Game/Assets/Ships/Exterior/ConceptRemasterV03/SmallUtilityEscort/M_Remaster_ArmorLight",
            "/Game/Assets/Ships/Exterior/ConceptRemasterV03/SmallUtilityEscort/M_Remaster_Structure",
        ],
    },
    {
        "asset": "TallUtilityRobot",
        "class": unreal.TallUtilityRobot,
        "label": "ROBOT_CLEAN_RS_TallUtility",
        "target": unreal.Vector(0.0, 0.0, 125.0),
        "radius_cm": 470.0,
        "design_authority": "docs/concept-art/reference/bloom/uncorrupted-robot-baselines.png",
        "fab_sources": [
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_BODY",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_HEAD",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_ARM",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_LEG",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/OTHERS/SM_PANEL_01",
        ],
        "project_sources": [
            "/Game/Assets/Ships/Exterior/ConceptRemasterV03/SmallUtilityEscort/M_Remaster_ArmorLight",
            "/Game/Assets/Ships/Exterior/ConceptRemasterV03/SmallUtilityEscort/M_Remaster_Structure",
        ],
    },
    {
        "asset": "HeavyCargoRobot",
        "class": unreal.HeavyCargoRobot,
        "label": "ROBOT_CLEAN_RS_HeavyCargo",
        "target": unreal.Vector(0.0, 0.0, 155.0),
        "radius_cm": 585.0,
        "design_authority": "docs/concept-art/reference/bloom/uncorrupted-robot-baselines.png",
        "fab_sources": [
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_BODY",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_HEAD",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_ARM",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_LEG",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_ELECTRIC_BOX_01_CLOSE",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_MECHA_ARM_03",
        ],
        "project_sources": [
            "/Game/Assets/Ships/Exterior/ConceptRemasterV03/SmallUtilityEscort/M_Remaster_ArmorLight",
            "/Game/Assets/Ships/Exterior/ConceptRemasterV03/SmallUtilityEscort/M_Remaster_Structure",
            "/Game/Assets/Ships/Exterior/ConceptRemasterV03/SmallUtilityEscort/M_Remaster_SafetyOrange",
        ],
    },
    {
        "asset": "SecuritySentryRobot",
        "class": unreal.SecuritySentryRobot,
        "label": "ROBOT_CLEAN_RS_SecuritySentry",
        "target": unreal.Vector(0.0, 0.0, 85.0),
        "radius_cm": 330.0,
        "design_authority": "docs/concept-art/reference/bloom/uncorrupted-robot-baselines.png",
        "fab_sources": [
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_POWER_GENERATOR_01",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_ARM",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/OTHERS/SM_PANEL_01",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_BODY",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/LAMP/SM_SCANNER_01",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_MECHA_ARM_02",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_ELECTRIC_BOX_01_CLOSE",
        ],
        "project_sources": [
            "/Game/Assets/Ships/Exterior/ConceptRemasterV03/SmallUtilityEscort/M_Remaster_ArmorLight",
            "/Game/Assets/Ships/Exterior/ConceptRemasterV03/SmallUtilityEscort/M_Remaster_Structure",
            "/Game/Assets/Ships/Exterior/ConceptRemasterV03/SmallUtilityEscort/M_Remaster_SafetyOrange",
        ],
    },
)


def configure_exposure(component):
    settings = component.post_process_settings
    settings.set_editor_property("override_auto_exposure_method", True)
    settings.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    settings.set_editor_property("override_camera_iso", True)
    settings.set_editor_property("camera_iso", 100.0)
    settings.set_editor_property("override_camera_shutter_speed", True)
    settings.set_editor_property("camera_shutter_speed", 60.0)
    settings.set_editor_property("override_auto_exposure_bias", True)
    settings.set_editor_property("auto_exposure_bias", 0.55)
    component.post_process_settings = settings


def add_light(actors, label, location, target, intensity, size, color):
    light = actors.spawn_actor_from_class(
        unreal.RectLight,
        location,
        unreal.MathLibrary.find_look_at_rotation(location, target),
    )
    light.set_actor_label(label)
    light.rect_light_component.set_editor_property("intensity", intensity)
    light.rect_light_component.set_editor_property("source_width", size)
    light.rect_light_component.set_editor_property("source_height", size)
    light.rect_light_component.set_editor_property("light_color", color)
    return light


levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
    if not levels.load_level(MAP_PATH):
        raise RuntimeError(f"Could not load {MAP_PATH}")
else:
    if not levels.new_level(MAP_PATH):
        raise RuntimeError(f"Could not create {MAP_PATH}")

for existing in actors.get_all_level_actors():
    actors.destroy_actor(existing)

spawned = {}
for prototype in PROTOTYPES:
    actor = actors.spawn_actor_from_class(prototype["class"], unreal.Vector(), unreal.Rotator())
    actor.set_actor_label(prototype["label"])
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    spawned[prototype["asset"]] = actor

lighting_target = unreal.Vector(0.0, 0.0, 125.0)
lights = [
    add_light(
        actors,
        "ROBOT_RS_Key",
        unreal.Vector(-260.0, -310.0, 365.0),
        lighting_target,
        110.0,
        190.0,
        unreal.Color(255, 235, 216),
    ),
    add_light(
        actors,
        "ROBOT_RS_Fill",
        unreal.Vector(310.0, -140.0, 160.0),
        lighting_target,
        85.0,
        170.0,
        unreal.Color(195, 220, 255),
    ),
    add_light(
        actors,
        "ROBOT_RS_Rim",
        unreal.Vector(60.0, 330.0, 285.0),
        lighting_target,
        120.0,
        150.0,
        unreal.Color(212, 226, 255),
    ),
]
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(), unreal.Rotator())
sky.set_actor_label("ROBOT_RS_Sky")
sky.light_component.set_editor_property("intensity", 0.3)
lights.append(sky)

levels.save_current_level()
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "r.MotionBlurQuality 0")
unreal.SystemLibrary.execute_console_command(world, "r.ScreenPercentage 100")
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

capture = actors.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(), unreal.Rotator())
capture.set_actor_label("ROBOT_RS_Capture")
component = capture.capture_component2d
component.capture_every_frame = False
component.capture_on_movement = False
component.fov_angle = FOV_DEGREES
component.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
configure_exposure(component)
target_texture = unreal.RenderingLibrary.create_render_target2d(
    world,
    RENDER_SIZE,
    RENDER_SIZE,
    unreal.TextureRenderTargetFormat.RTF_RGBA8,
    unreal.LinearColor(0.12, 0.12, 0.12, 1.0),
)
target_texture.set_editor_property("target_gamma", 2.2)
component.texture_target = target_texture

jobs = []
for prototype in PROTOTYPES:
    output = CAPTURE_ROOT / prototype["asset"] / "InputFrames"
    output.mkdir(parents=True, exist_ok=True)
    for prior in output.glob(f"{prototype['asset']}_RS_*.png"):
        prior.unlink()
    frame_index = 0
    for elevation_deg in ELEVATIONS:
        elevation = math.radians(elevation_deg)
        horizontal = prototype["radius_cm"] * math.cos(elevation)
        z = prototype["target"].z + prototype["radius_cm"] * math.sin(elevation)
        for azimuth_deg in AZIMUTHS:
            azimuth = math.radians(azimuth_deg)
            location = unreal.Vector(
                prototype["target"].x + horizontal * math.cos(azimuth),
                prototype["target"].y + horizontal * math.sin(azimuth),
                z,
            )
            filename = (
                f"{prototype['asset']}_RS_{frame_index:03d}_"
                f"A{azimuth_deg:03d}_E{elevation_deg:+03d}.png"
            )
            jobs.append(
                {
                    "prototype": prototype,
                    "actor": spawned[prototype["asset"]],
                    "output": output,
                    "filename": filename,
                    "azimuth_deg": azimuth_deg,
                    "elevation_deg": elevation_deg,
                    "location": location,
                }
            )
            frame_index += 1

manifests = {
    prototype["asset"]: {
        "version": 1,
        "asset": prototype["asset"],
        "method": "Unreal fixed-pose virtual capture of an articulated clean Fab-derived robot",
        "design_authority": prototype["design_authority"],
        "fab_sources": prototype["fab_sources"],
        "project_sources": prototype["project_sources"],
        "gameplay_class": prototype["class"].static_class().get_path_name(),
        "capture_frame_count": len(AZIMUTHS) * len(ELEVATIONS),
        "render_size_px": [RENDER_SIZE, RENDER_SIZE],
        "fov_degrees": FOV_DEGREES,
        "capture_radius_cm": prototype["radius_cm"],
        "target_cm": [prototype["target"].x, prototype["target"].y, prototype["target"].z],
        "realityscan_role": "surface and retopology reference; never the animation source",
        "corruption_state": "clean baseline; no Bloom geometry or material",
        "frames": [],
    }
    for prototype in PROTOTYPES
}

state = {"index": 0, "warmup": 0.0, "handle": None, "finished": False}
unreal.EditorPythonScripting.set_keep_python_script_alive(True)


def finish():
    if state["finished"]:
        return
    state["finished"] = True
    if capture in actors.get_all_level_actors():
        actors.destroy_actor(capture)
    for asset, manifest in manifests.items():
        manifest_path = CAPTURE_ROOT / asset / "CaptureManifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(
            {
                "map": MAP_PATH,
                "prototype_count": len(PROTOTYPES),
                "frame_count": len(jobs),
                "manifests": [
                    (CAPTURE_ROOT / item["asset"] / "CaptureManifest.json")
                    .relative_to(PROJECT)
                    .as_posix()
                    for item in PROTOTYPES
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    levels.save_current_level()
    unreal.log(f"CLEAN ROBOT FAB REALITYSCAN CAPTURE complete: {len(jobs)} frames")
    unreal.unregister_slate_post_tick_callback(state["handle"])
    unreal.EditorPythonScripting.set_keep_python_script_alive(False)
    unreal.SystemLibrary.quit_editor()


def capture_next(delta_seconds):
    if state["finished"]:
        return
    state["warmup"] += delta_seconds
    if state["warmup"] < 15.0:
        return
    if state["index"] >= len(jobs):
        finish()
        return
    job = jobs[state["index"]]
    for actor in spawned.values():
        visible = actor == job["actor"]
        actor.set_actor_hidden_in_game(not visible)
        actor.set_is_temporarily_hidden_in_editor(not visible)
    capture.set_actor_location(job["location"], False, False)
    rotation = unreal.MathLibrary.find_look_at_rotation(
        job["location"], job["prototype"]["target"]
    )
    capture.set_actor_rotation(rotation, False)
    component.capture_scene()
    component.capture_scene()
    unreal.RenderingLibrary.export_render_target(
        world, target_texture, str(job["output"]), job["filename"]
    )
    output_path = job["output"] / job["filename"]
    if not output_path.exists() or output_path.stat().st_size < 5000:
        raise RuntimeError(f"Invalid RealityScan capture: {output_path}")
    manifests[job["prototype"]["asset"]]["frames"].append(
        {
            "file": job["filename"],
            "azimuth_deg": job["azimuth_deg"],
            "elevation_deg": job["elevation_deg"],
            "camera_location_cm": [
                job["location"].x,
                job["location"].y,
                job["location"].z,
            ],
            "camera_rotation_deg": [rotation.pitch, rotation.yaw, rotation.roll],
            "bytes": output_path.stat().st_size,
        }
    )
    state["index"] += 1
    if state["index"] % 12 == 0:
        unreal.log(f"CLEAN ROBOT FAB REALITYSCAN CAPTURE progress: {state['index']}/{len(jobs)}")


state["handle"] = unreal.register_slate_post_tick_callback(capture_next)
