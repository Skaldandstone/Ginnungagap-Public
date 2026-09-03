"""Build the Bloom Fab prototype review map and render RealityScan turntables.

The source actors stay articulated: Manny drives the reanimated crew host and the
Fab JACK kit remains a set of rigid robot parts.  RealityScan output is therefore
a surface/retopology reference, not a replacement for either gameplay rig.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
MAP_PATH = "/Game/Assets/Maps/Bloom/L_Bloom_FabRealityScan_Prototypes"
CAPTURE_ROOT = PROJECT / "Art/Characters/BloomEnemies/RealityScan"
REPORT_PATH = PROJECT / "Saved/Reports/BloomFabRealityScanCapture.json"
RENDER_SIZE = 768
FOV_DEGREES = 42.0
AZIMUTHS = tuple(range(0, 360, 20))
ELEVATIONS = (-18, 18)

PROTOTYPES = (
    {
        "asset": "BloomReanimatedCrew",
        "class": unreal.BloomReanimatedCrewEnemy,
        "label": "BLOOM_FAB_RS_ReanimatedCrew",
        "target": unreal.Vector(0.0, 0.0, -5.0),
        "radius_cm": 430.0,
        "design_authority": "docs/concept-art/reference/bloom/reanimated-crew-variants.png",
        "fab_sources": [
            "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple",
            "/Game/DeadBodies_Poses_nikoff/Animations",
            "/Game/SF_White_desert/Meshes/Crystals/SM_crystal_02",
            "/Game/SF_White_desert/Meshes/Crystals/SM_crystal_03",
            "/Game/Alien_Biomass/Meshes/Alien_organism/SM_alien_organism_13",
        ],
        "project_sources": [
            "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt/Working/Iteration_02_ConceptSilhouette/SKM_PrimaryOversuit_QuinnProjectionShell_I02",
            "/Game/Assets/Materials/Production/Instances/MI_Surface_Bloom",
        ],
    },
    {
        "asset": "BloomMechanizedHost",
        "class": unreal.BloomMechanizedEnemy,
        "label": "BLOOM_FAB_RS_MechanizedHost",
        "target": unreal.Vector(0.0, 0.0, 10.0),
        "radius_cm": 520.0,
        "design_authority": "docs/concept-art/reference/bloom/infested-drones-and-robots.png",
        "fab_sources": [
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_BODY",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_HEAD",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_ARM",
            "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_LEG",
            "/Game/SF_White_desert/Meshes/Crystals/SM_crystal_01",
            "/Game/SF_White_desert/Meshes/Crystals/SM_crystal_02",
            "/Game/Alien_Biomass/Meshes/Alien_organism/SM_alien_organism_13",
        ],
        "project_sources": [
            "/Game/Assets/Materials/Production/Instances/MI_Surface_Bloom",
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
    settings.set_editor_property("auto_exposure_bias", 0.5)
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
    actor.set_actor_location(unreal.Vector(), False, False)
    actor.set_actor_rotation(unreal.Rotator(), False)
    actor.set_actor_label(prototype["label"])
    actor.set_actor_hidden_in_game(True)
    actor.set_is_temporarily_hidden_in_editor(True)
    spawned[prototype["asset"]] = actor

lighting_target = unreal.Vector(0.0, 0.0, 10.0)
lights = [
    add_light(
        actors,
        "BLOOM_RS_Key",
        unreal.Vector(-220.0, -260.0, 310.0),
        lighting_target,
        72.0,
        180.0,
        unreal.Color(255, 235, 216),
    ),
    add_light(
        actors,
        "BLOOM_RS_Fill",
        unreal.Vector(260.0, -120.0, 120.0),
        lighting_target,
        42.0,
        155.0,
        unreal.Color(195, 220, 255),
    ),
    add_light(
        actors,
        "BLOOM_RS_Rim",
        unreal.Vector(50.0, 280.0, 250.0),
        lighting_target,
        85.0,
        135.0,
        unreal.Color(215, 190, 255),
    ),
]
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(), unreal.Rotator())
sky.set_actor_label("BLOOM_RS_Sky")
sky.light_component.set_editor_property("intensity", 0.18)
lights.append(sky)

levels.save_current_level()
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "r.MotionBlurQuality 0")
unreal.SystemLibrary.execute_console_command(world, "r.ScreenPercentage 100")
unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()

capture = actors.spawn_actor_from_class(unreal.SceneCapture2D, unreal.Vector(), unreal.Rotator())
capture.set_actor_location(unreal.Vector(), False, False)
capture.set_actor_label("BLOOM_RS_Capture")
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
    unreal.LinearColor(0.012, 0.014, 0.02, 1.0),
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
        "method": "Unreal fixed-pose virtual capture of articulated Fab-derived Bloom prototype",
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
                    str(CAPTURE_ROOT / item["asset"] / "CaptureManifest.json")
                    for item in PROTOTYPES
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    levels.save_current_level()
    unreal.log(f"BLOOM FAB REALITYSCAN CAPTURE complete: {len(jobs)} frames")
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
        unreal.log(f"BLOOM FAB REALITYSCAN CAPTURE progress: {state['index']}/{len(jobs)}")


state["handle"] = unreal.register_slate_post_tick_callback(capture_next)
