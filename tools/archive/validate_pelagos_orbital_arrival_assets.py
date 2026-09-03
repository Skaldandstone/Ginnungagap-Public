"""Validate the generated Pelagos Unreal assets and functional map anchors."""

import json
from pathlib import Path

import unreal


PROJECT_ROOT = Path(unreal.Paths.project_dir()).resolve()
REPORT = PROJECT_ROOT / "Art" / "SpaceSystems" / "PelagosUnrealValidation.json"
LEVEL = "/Game/Assets/Maps/SpaceSystems/L_PelagosOrbitalArrival"
DATA = "/Game/Assets/SpaceSystems/Pelagos/Data/DA_PelagosOrbitalArrival"
MESH = "/Game/Assets/SpaceSystems/Pelagos/Meshes/SM_PelagosOrbitalArrival_Set"
BLUEPRINT = "/Game/Assets/SpaceSystems/Pelagos/Blueprints/BP_PelagosOrbitalArrivalDirector"


def tag_strings(actor):
    return [str(value) for value in actor.tags]


def count_prefix(actors, prefix):
    return sum(1 for actor in actors if any(tag.startswith(prefix) for tag in tag_strings(actor)))


def main():
    if not unreal.EditorAssetLibrary.does_asset_exist(LEVEL):
        raise RuntimeError(f"Missing Pelagos level: {LEVEL}")
    unreal.EditorLevelLibrary.load_level(LEVEL)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    definition = unreal.EditorAssetLibrary.load_asset(DATA)
    mesh = unreal.EditorAssetLibrary.load_asset(MESH)
    nanite_enabled = False
    complex_collision = False
    if mesh:
        try:
            nanite_enabled = bool(mesh.get_editor_property("nanite_settings").get_editor_property("enabled"))
            complex_collision = (
                mesh.get_editor_property("body_setup").get_editor_property("collision_trace_flag")
                == unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
            )
        except Exception as error:
            unreal.log_warning(f"Could not inspect Pelagos mesh production settings: {error}")
    checks = {
        "level_exists": unreal.EditorAssetLibrary.does_asset_exist(LEVEL),
        "data_asset_exists": definition is not None,
        "director_blueprint_exists": unreal.EditorAssetLibrary.does_asset_exist(BLUEPRINT),
        "environment_mesh_exists": unreal.EditorAssetLibrary.does_asset_exist(MESH),
        "environment_actor": count_prefix(actors, "Pelagos.Environment") == 1,
        "director_actor": count_prefix(actors, "Pelagos.Director") == 1,
        "arrival_routes": len(definition.get_editor_property("routes")) == 4,
        "dock_definitions": len(definition.get_editor_property("docks")) == 4,
        "route_checkpoints": count_prefix(actors, "Pelagos.Route.") == 16,
        "arrival_gates": count_prefix(actors, "Pelagos.Gate.") == 5,
        "dock_approach_volumes": count_prefix(actors, "Pelagos.Dock.") >= 12,
        "traffic_spawn_points": count_prefix(actors, "Pelagos.Traffic.Spawn.") == 24,
        "service_anchors": count_prefix(actors, "Pelagos.Service.") == 10,
        "hazard_volumes": count_prefix(actors, "Pelagos.Hazard.") == 6,
        "stellar_lights": count_prefix(actors, "Pelagos.Light.") == 2,
        "navigation_beacons": count_prefix(actors, "Pelagos.Beacon.") == 12,
        "cinematic_cameras": count_prefix(actors, "Pelagos.Camera.") == 4,
        "post_process_volume": count_prefix(actors, "Pelagos.PostProcess.") == 1,
        "nanite_enabled": nanite_enabled,
        "complex_environment_collision": complex_collision,
        "native_arrival_gates": sum(1 for actor in actors if actor.get_class().get_name() == "PelagosArrivalGateVolume") == 21,
        "native_hazard_volumes": sum(1 for actor in actors if actor.get_class().get_name() == "PelagosHazardVolume") == 6,
        "traffic_controller_actor": count_prefix(actors, "Pelagos.Traffic.Controller") == 1,
        "traffic_definitions": len(definition.get_editor_property("traffic_spawns")) == 24,
        "hazard_definitions": len(definition.get_editor_property("hazards")) == 6,
        "service_definitions": len(definition.get_editor_property("services")) == 10,
    }
    reflected_contracts = {
        "traffic_spawn_definition": hasattr(unreal, "PelagosTrafficSpawnDefinition"),
        "hazard_definition": hasattr(unreal, "PelagosHazardDefinition"),
        "service_definition": hasattr(unreal, "PelagosServiceDefinition"),
        "arrival_gate_volume": unreal.load_class(None, "/Script/Ginnungagap.PelagosArrivalGateVolume") is not None,
        "hazard_volume": unreal.load_class(None, "/Script/Ginnungagap.PelagosHazardVolume") is not None,
        "traffic_controller": unreal.load_class(None, "/Script/Ginnungagap.PelagosTrafficController") is not None,
    }
    payload = {
        "map": LEVEL,
        "actor_count": len(actors),
        "checks": checks,
        "reflected_runtime_contracts": reflected_contracts,
        "passed": all(checks.values()),
    }
    REPORT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    unreal.log(json.dumps(payload, indent=2))
    if not payload["passed"]:
        raise RuntimeError(f"Pelagos validation failed; see {REPORT}")


main()
