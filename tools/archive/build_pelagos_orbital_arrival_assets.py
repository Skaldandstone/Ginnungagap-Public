"""Build Pelagos data, Blueprint, imported environment, and playable Unreal level."""

from pathlib import Path

import unreal


PROJECT_ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE_FBX = PROJECT_ROOT / "Art" / "SpaceSystems" / "Exports" / "SM_PelagosOrbitalArrival_Set.fbx"
ROOT = "/Game/Assets/SpaceSystems/Pelagos"
MESH_PATH = f"{ROOT}/Meshes"
DATA_PATH = f"{ROOT}/Data"
BLUEPRINT_PATH = f"{ROOT}/Blueprints"
LEVEL_PATH = "/Game/Assets/Maps/SpaceSystems/L_PelagosOrbitalArrival"


def ensure_directory(path):
    unreal.EditorAssetLibrary.make_directory(path)


def create_or_load_data_asset():
    asset_path = f"{DATA_PATH}/DA_PelagosOrbitalArrival"
    asset = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not asset:
        definition_class = unreal.load_class(None, "/Script/Ginnungagap.PelagosArrivalDefinition")
        if not definition_class:
            raise RuntimeError("PelagosArrivalDefinition class is unavailable; compile the C++ module first")
        factory = unreal.DataAssetFactory()
        factory.set_editor_property("data_asset_class", definition_class)
        asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            "DA_PelagosOrbitalArrival", DATA_PATH, definition_class, factory
        )
    asset.set_editor_property("destination_id", "Pelagos")
    asset.set_editor_property("display_name", unreal.TextLibrary.conv_string_to_text("Pelagos Orbital Arrival"))
    asset.set_editor_property("max_active_traffic", 24)
    asset.set_editor_property("max_traffic_near_docks", 5)
    asset.set_editor_property("max_concurrent_missions", 8)
    asset.set_editor_property("auto_start_on_jump_arrival", True)

    docks = []
    dock_specs = [
        ("Dock_01", (-1210.0, 38.0, -120.0), True, False),
        ("Dock_02", (-1210.0, 38.0, 110.0), False, False),
        ("Dock_03", (-1210.0, 38.0, 410.0), True, True),
        ("Dock_04", (-1210.0, 38.0, 680.0), True, False),
    ]
    for dock_id, dock_location, supports_large, emergency in dock_specs:
        dock = unreal.PelagosDockDefinition()
        dock.set_editor_property("dock_id", dock_id)
        dock.set_editor_property("dock_transform", unreal.Transform(location=unreal.Vector(*dock_location)))
        dock.set_editor_property(
            "approach_transform",
            unreal.Transform(location=unreal.Vector(dock_location[0] - 8000.0, dock_location[1], dock_location[2])),
        )
        dock.set_editor_property("capture_radius", 2200.0)
        dock.set_editor_property("supports_large_ships", supports_large)
        dock.set_editor_property("emergency_dock", emergency)
        docks.append(dock)
    asset.set_editor_property("docks", docks)

    routes = []
    route_specs = [
        ("PlayerArrival", [(-32000, -9000, 7000), (-22000, -4500, 4200), (-12000, -1500, 1800), (-4500, 0, 600)], 220.0, True),
        ("CivilianInbound", [(-28000, 12000, 5000), (-18000, 7500, 3200), (-9000, 3200, 1500), (-3500, 800, 400)], 180.0, False),
        ("CargoInbound", [(-34000, 5000, -3000), (-23000, 4200, -1200), (-13000, 2100, 200), (-5000, 400, 700)], 140.0, False),
        ("EmergencyVector", [(-24000, -14000, 9000), (-15000, -7000, 5200), (-7000, -2500, 2100), (-3000, 200, 450)], 320.0, False),
    ]
    for route_id, points, speed, player_route in route_specs:
        route = unreal.PelagosArrivalRouteDefinition()
        route.set_editor_property("route_id", route_id)
        route.set_editor_property("control_points", [unreal.Vector(*point) for point in points])
        route.set_editor_property("speed_limit", speed)
        route.set_editor_property("clearance_radius", 1800.0)
        route.set_editor_property("player_route", player_route)
        routes.append(route)
    asset.set_editor_property("routes", routes)

    if hasattr(unreal, "PelagosTrafficSpawnDefinition"):
        traffic_spawns = []
        traffic_routes = ("PlayerArrival", "CivilianInbound", "CargoInbound", "EmergencyVector")
        for index in range(24):
            ring = index // 8
            slot = index % 8
            spawn = unreal.PelagosTrafficSpawnDefinition()
            spawn.set_editor_property("spawn_id", f"Traffic_{index + 1:02d}")
            spawn.set_editor_property("route_id", traffic_routes[index % len(traffic_routes)])
            spawn.set_editor_property("spawn_transform", unreal.Transform(location=unreal.Vector(
                -18000 + ring * 4500, -12000 + slot * 3400, -2500 + ((index * 7) % 9) * 850
            )))
            spawn.set_editor_property("local_capacity", 2 if ring < 2 else 1)
            spawn.set_editor_property("minimum_respawn_delay", 12.0 + (index % 5) * 3.0)
            spawn.set_editor_property("allows_large_ships", index % 6 == 0)
            traffic_spawns.append(spawn)
        asset.set_editor_property("traffic_spawns", traffic_spawns)

        hazard_specs = [
            ("SolarShear", "SOLAR_SHEAR", (19000, -12000, 8000), (4500, 3000, 2500), 0.85, 18.0),
            ("IonWake", "ION_WAKE", (-16000, 21000, -5000), (3500, 4000, 2500), 0.65, 8.0),
            ("DebrisAlpha", "DEBRIS_FIELD", (9000, 17000, 1500), (3000, 5500, 1800), 0.55, 12.0),
            ("DebrisBeta", "DEBRIS_FIELD", (-24000, -18000, -3500), (4000, 2800, 2000), 0.45, 9.0),
            ("NoBurn", "NO_BURN_ZONE", (-2000, 0, 600), (1800, 1800, 1800), 0.25, 0.0),
            ("EmergencyClear", "EMERGENCY_CLEAR_LANE", (-9000, 0, 450), (1600, 1200, 1200), 0.35, 0.0),
        ]
        hazards = []
        for hazard_id, enum_name, location, extent, severity, damage in hazard_specs:
            hazard = unreal.PelagosHazardDefinition()
            hazard.set_editor_property("hazard_id", hazard_id)
            hazard.set_editor_property("hazard_type", getattr(unreal.PelagosHazardType, enum_name))
            hazard.set_editor_property("transform", unreal.Transform(location=unreal.Vector(*location)))
            hazard.set_editor_property("extent", unreal.Vector(*extent))
            hazard.set_editor_property("severity", severity)
            hazard.set_editor_property("damage_per_second", damage)
            hazards.append(hazard)
        asset.set_editor_property("hazards", hazards)

        service_names = ("Fuel", "Repair", "Medical", "Cargo", "Customs", "Crew", "Upgrade", "Market", "Navigation", "Salvage")
        services = []
        for index, service_name in enumerate(service_names):
            service = unreal.PelagosServiceDefinition()
            service.set_editor_property("service_id", service_name)
            service.set_editor_property("service_type", getattr(unreal.PelagosServiceType, service_name.upper()))
            service.set_editor_property("interaction_transform", unreal.Transform(location=unreal.Vector(
                -2200, -1400 + index * 310, 250 + (index % 3) * 180
            )))
            service.set_editor_property("interaction_radius", 1500.0)
            service.set_editor_property("requires_hard_dock", service_name not in ("Navigation", "Customs"))
            services.append(service)
        asset.set_editor_property("services", services)
    asset.set_editor_property(
        "player_arrival_transform",
        unreal.Transform(location=unreal.Vector(-32000.0, -9000.0, 7000.0)),
    )
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def create_or_load_director_blueprint():
    asset_path = f"{BLUEPRINT_PATH}/BP_PelagosOrbitalArrivalDirector"
    blueprint = unreal.EditorAssetLibrary.load_asset(asset_path)
    if blueprint:
        return blueprint
    parent_class = unreal.load_class(None, "/Script/Ginnungagap.PelagosOrbitalArrivalDirector")
    if not parent_class:
        raise RuntimeError("PelagosOrbitalArrivalDirector class is unavailable; compile the C++ module first")
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent_class)
    blueprint = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "BP_PelagosOrbitalArrivalDirector", BLUEPRINT_PATH, unreal.Blueprint, factory
    )
    unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
    return blueprint


def import_environment():
    if not SOURCE_FBX.exists():
        raise RuntimeError(f"Missing Blender export: {SOURCE_FBX}")
    existing_mesh = unreal.EditorAssetLibrary.load_asset(f"{MESH_PATH}/SM_PelagosOrbitalArrival_Set")
    mesh_package = PROJECT_ROOT / "Content" / "Assets" / "SpaceSystems" / "Pelagos" / "Meshes" / "SM_PelagosOrbitalArrival_Set.uasset"
    if existing_mesh and mesh_package.exists() and mesh_package.stat().st_mtime >= SOURCE_FBX.stat().st_mtime:
        configure_environment_mesh(existing_mesh)
        return existing_mesh
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(SOURCE_FBX))
    task.set_editor_property("destination_path", MESH_PATH)
    task.set_editor_property("destination_name", "SM_PelagosOrbitalArrival_Set")
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_as_skeletal", False)
    options.set_editor_property("import_materials", True)
    options.set_editor_property("import_textures", False)
    options.get_editor_property("static_mesh_import_data").set_editor_property("combine_meshes", True)
    options.get_editor_property("static_mesh_import_data").set_editor_property("generate_lightmap_u_vs", True)
    task.set_editor_property("options", options)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    mesh = unreal.EditorAssetLibrary.load_asset(f"{MESH_PATH}/SM_PelagosOrbitalArrival_Set")
    if not mesh:
        raise RuntimeError(f"Environment import failed: {task.get_editor_property('imported_object_paths')}")
    configure_environment_mesh(mesh)
    return mesh


def configure_environment_mesh(mesh):
    try:
        nanite = mesh.get_editor_property("nanite_settings")
        nanite.set_editor_property("enabled", True)
        mesh.set_editor_property("nanite_settings", nanite)
        mesh.set_editor_property("light_map_resolution", 128)
        body_setup = mesh.get_editor_property("body_setup")
        body_setup.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
        mesh.set_editor_property("allow_cpu_access", False)
        unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    except Exception as error:
        unreal.log_warning(f"Pelagos mesh production settings were partially applied: {error}")


def tagged_actor(tag):
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in actor_subsystem.get_all_level_actors():
        if tag in [str(value) for value in actor.tags]:
            return actor
    return None


def spawn_once(actor_object, location, label, tag):
    existing = tagged_actor(tag)
    if existing:
        return existing
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actor = actor_subsystem.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location))
    if not actor:
        raise RuntimeError(f"Could not spawn static mesh actor for {tag}")
    actor.static_mesh_component.set_static_mesh(actor_object)
    actor.set_actor_label(label)
    actor.tags = [tag]
    return actor


def spawn_marker_once(location, label, tag):
    existing = tagged_actor(tag)
    if existing:
        return existing
    marker = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
        unreal.TargetPoint, unreal.Vector(*location)
    )
    marker.set_actor_label(label)
    marker.tags = [tag]
    return marker


def spawn_trigger_once(location, scale, label, tag):
    existing = tagged_actor(tag)
    if existing:
        return existing
    trigger = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
        unreal.TriggerBox, unreal.Vector(*location)
    )
    trigger.set_actor_label(label)
    trigger.set_actor_scale3d(unreal.Vector(*scale))
    trigger.tags = [tag]
    return trigger


def spawn_native_gate(location, extent, label, tag, action, required_state, dock_id="", route_id="PlayerArrival"):
    gate_class = unreal.load_class(None, "/Script/Ginnungagap.PelagosArrivalGateVolume")
    if not gate_class:
        return spawn_trigger_once(location, extent, label, tag)
    existing = tagged_actor(tag)
    if existing and existing.get_class() != gate_class:
        unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(existing)
        existing = None
    gate = existing or unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
        gate_class, unreal.Vector(*location)
    )
    gate.set_actor_label(label)
    gate.tags = [tag]
    gate.set_editor_property("gate_id", tag)
    gate.set_editor_property("action", action)
    gate.set_editor_property("required_state", required_state)
    gate.set_editor_property("dock_id", dock_id)
    gate.set_editor_property("route_id", route_id)
    gate.set_editor_property("required_actor_tag", "PlayerShip")
    gate.get_editor_property("trigger_volume").set_box_extent(unreal.Vector(*extent))
    return gate


def spawn_native_hazard(location, extent, label, tag, definition):
    hazard_class = unreal.load_class(None, "/Script/Ginnungagap.PelagosHazardVolume")
    if not hazard_class:
        return spawn_trigger_once(location, extent, label, tag)
    existing = tagged_actor(tag)
    if existing and existing.get_class() != hazard_class:
        unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actor(existing)
        existing = None
    hazard = existing or unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
        hazard_class, unreal.Vector(*location)
    )
    hazard.set_actor_label(label)
    hazard.tags = [tag]
    hazard.set_editor_property("definition", definition)
    hazard.get_editor_property("hazard_bounds").set_box_extent(unreal.Vector(*extent))
    return hazard


def build_level(environment_mesh, definition, blueprint):
    if unreal.EditorAssetLibrary.does_asset_exist(LEVEL_PATH):
        unreal.EditorLevelLibrary.load_level(LEVEL_PATH)
    else:
        if not unreal.EditorLevelLibrary.new_level(LEVEL_PATH):
            raise RuntimeError(f"Could not create {LEVEL_PATH}")

    spawn_once(environment_mesh, (0, 0, 0), "Pelagos Environment Set", "Pelagos.Environment")
    director_class = unreal.EditorAssetLibrary.load_blueprint_class(f"{BLUEPRINT_PATH}/BP_PelagosOrbitalArrivalDirector")
    director = tagged_actor("Pelagos.Director")
    if not director:
        director = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
            director_class, unreal.Vector(0, 0, 0)
        )
        director.set_actor_label("Pelagos Arrival Director")
        director.tags = ["Pelagos.Director"]
    director.set_editor_property("arrival_definition", definition)

    marker_specs = [
        ("Arrival_Player", (-32000, -9000, 7000), "Pelagos.Arrival.Player"),
        ("Dock_01", (-1210, 38, -120), "Pelagos.Dock.01"),
        ("Dock_02", (-1210, 38, 110), "Pelagos.Dock.02"),
        ("Dock_03_Emergency", (-1210, 38, 410), "Pelagos.Dock.03"),
        ("Dock_04", (-1210, 38, 680), "Pelagos.Dock.04"),
    ]
    for label, location, tag in marker_specs:
        spawn_marker_once(location, label, tag)

    route_specs = {
        "PlayerArrival": [(-32000, -9000, 7000), (-22000, -4500, 4200), (-12000, -1500, 1800), (-4500, 0, 600)],
        "CivilianInbound": [(-28000, 12000, 5000), (-18000, 7500, 3200), (-9000, 3200, 1500), (-3500, 800, 400)],
        "CargoInbound": [(-34000, 5000, -3000), (-23000, 4200, -1200), (-13000, 2100, 200), (-5000, 400, 700)],
        "EmergencyVector": [(-24000, -14000, 9000), (-15000, -7000, 5200), (-7000, -2500, 2100), (-3000, 200, 450)],
    }
    for route_name, points in route_specs.items():
        for index, point in enumerate(points, 1):
            spawn_marker_once(point, f"{route_name} Checkpoint {index:02d}", f"Pelagos.Route.{route_name}.{index:02d}")

    advance = unreal.PelagosGateAction.ADVANCE_STATE
    arrival_gates = [
        ("Sensor Acquisition Gate", (-26000, -6200, 5400), (2000, 2000, 2000), "Pelagos.Gate.Sensor", unreal.PelagosArrivalState.JUMP_EXIT),
        ("IFF Challenge Gate", (-19000, -3600, 3500), (1800, 1800, 1800), "Pelagos.Gate.IFF", unreal.PelagosArrivalState.SENSOR_ACQUISITION),
        ("Control Handoff Gate", (-12500, -1700, 2000), (1600, 1600, 1600), "Pelagos.Gate.Handoff", unreal.PelagosArrivalState.IFF_CHALLENGE),
        ("Traffic Contact Gate", (-7500, -500, 1000), (1400, 1400, 1400), "Pelagos.Gate.Traffic", unreal.PelagosArrivalState.CONTROL_HANDOFF),
        ("Dock Request Gate", (-6100, 0, 750), (900, 1200, 900), "Pelagos.Gate.DockRequest", unreal.PelagosArrivalState.TRAFFIC_CONTACT),
    ]
    for label, location, extent, tag, required_state in arrival_gates:
        spawn_native_gate(location, extent, label, tag, advance, required_state)

    dock_locations = [(-1210, 38, -120), (-1210, 38, 110), (-1210, 38, 410), (-1210, 38, 680)]
    for index, location in enumerate(dock_locations, 1):
        approach = (location[0] - 8000, location[1], location[2])
        dock_id = f"Dock_{index:02d}"
        spawn_native_gate(approach, (1200, 1200, 800), f"Dock {index:02d} Request", f"Pelagos.Dock.{index:02d}.Approach",
                          unreal.PelagosGateAction.REQUEST_DOCK, unreal.PelagosArrivalState.DOCK_REQUEST, dock_id=dock_id)
        spawn_native_gate((location[0] - 4800, location[1], location[2]), (900, 900, 650),
                          f"Dock {index:02d} Final Approach", f"Pelagos.Dock.{index:02d}.FinalApproach",
                          unreal.PelagosGateAction.BEGIN_FINAL_APPROACH, unreal.PelagosArrivalState.DOCK_ASSIGNMENT,
                          dock_id=dock_id)
        spawn_native_gate((location[0] - 1900, location[1], location[2]), (500, 500, 400),
                          f"Dock {index:02d} Soft Capture", f"Pelagos.Dock.{index:02d}.SoftCapture",
                          unreal.PelagosGateAction.CONFIRM_SOFT_CAPTURE, unreal.PelagosArrivalState.FINAL_APPROACH,
                          dock_id=dock_id)
        spawn_native_gate(location, (400, 400, 400), f"Dock {index:02d} Hard Capture", f"Pelagos.Dock.{index:02d}.Capture",
                          unreal.PelagosGateAction.CONFIRM_HARD_DOCK, unreal.PelagosArrivalState.SOFT_CAPTURE,
                          dock_id=dock_id)

    for index in range(24):
        ring = index // 8
        slot = index % 8
        x = -18000 + ring * 4500
        y = -12000 + slot * 3400
        z = -2500 + ((index * 7) % 9) * 850
        spawn_marker_once((x, y, z), f"Traffic Spawn {index + 1:02d}", f"Pelagos.Traffic.Spawn.{index + 1:02d}")

    service_names = ("Fuel", "Repair", "Medical", "Cargo", "Customs", "Crew", "Upgrade", "Market", "Navigation", "Salvage")
    for index, service in enumerate(service_names):
        spawn_marker_once((-2200, -1400 + index * 310, 250 + (index % 3) * 180), f"{service} Service Anchor", f"Pelagos.Service.{service}")

    hazard_specs = [
        ("Solar Shear Exclusion", (19000, -12000, 8000), (45, 30, 25), "Pelagos.Hazard.SolarShear"),
        ("Ion Wake Exclusion", (-16000, 21000, -5000), (35, 40, 25), "Pelagos.Hazard.IonWake"),
        ("Debris Belt Alpha", (9000, 17000, 1500), (30, 55, 18), "Pelagos.Hazard.DebrisAlpha"),
        ("Debris Belt Beta", (-24000, -18000, -3500), (40, 28, 20), "Pelagos.Hazard.DebrisBeta"),
        ("Station No Burn Zone", (-2000, 0, 600), (18, 18, 18), "Pelagos.Hazard.NoBurn"),
        ("Emergency Clear Zone", (-9000, 0, 450), (16, 12, 12), "Pelagos.Hazard.EmergencyClear"),
    ]
    hazard_definitions = list(definition.get_editor_property("hazards")) if hasattr(unreal, "PelagosHazardDefinition") else []
    for hazard_index, (label, location, scale, tag) in enumerate(hazard_specs):
        if hazard_index < len(hazard_definitions):
            spawn_native_hazard(location, (scale[0] * 100, scale[1] * 100, scale[2] * 100), label, tag, hazard_definitions[hazard_index])
        else:
            spawn_trigger_once(location, scale, label, tag)

    beacon_colors = (
        unreal.Color(50, 220, 255, 255),
        unreal.Color(255, 154, 48, 255),
        unreal.Color(90, 255, 178, 255),
    )
    for index in range(12):
        tag = f"Pelagos.Beacon.{index + 1:02d}"
        if tagged_actor(tag):
            continue
        side = -1 if index % 2 == 0 else 1
        beacon = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
            unreal.PointLight, unreal.Vector(-5200 + (index // 2) * 720, side * (1200 + (index % 3) * 420), 350 + (index % 4) * 280)
        )
        beacon.set_actor_label(f"Pelagos Navigation Beacon {index + 1:02d}")
        beacon.tags = [tag]
        component = beacon.get_component_by_class(unreal.PointLightComponent)
        component.set_editor_property("intensity", 850.0)
        component.set_editor_property("attenuation_radius", 2600.0)
        component.set_editor_property("light_color", beacon_colors[index % len(beacon_colors)])

    camera_specs = [
        ("Arrival Overview", (-30000, -16000, 12000), unreal.Rotator(-12, 24, 0), "Pelagos.Camera.Arrival"),
        ("Station Reveal", (-14000, -9000, 6200), unreal.Rotator(-8, 30, 0), "Pelagos.Camera.Station"),
        ("Dock Operations", (-6500, -3500, 2800), unreal.Rotator(-4, 22, 0), "Pelagos.Camera.Dock"),
        ("Planet Vista", (8000, -18000, 14000), unreal.Rotator(-18, 132, 0), "Pelagos.Camera.Planet"),
    ]
    for label, location, rotation, tag in camera_specs:
        if tagged_actor(tag):
            continue
        camera = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
            unreal.CameraActor, unreal.Vector(*location), rotation
        )
        camera.set_actor_label(label)
        camera.tags = [tag]
        camera.get_component_by_class(unreal.CameraComponent).set_editor_property("field_of_view", 60.0)

    if not tagged_actor("Pelagos.PostProcess.Main"):
        post_process = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
            unreal.PostProcessVolume, unreal.Vector(0, 0, 0)
        )
        post_process.set_actor_label("Pelagos Orbital Color Grade")
        post_process.tags = ["Pelagos.PostProcess.Main"]
        post_process.set_editor_property("unbound", True)
        post_process.set_editor_property("priority", 10.0)
        post_process.set_editor_property("blend_weight", 1.0)

    traffic_controller_class = unreal.load_class(None, "/Script/Ginnungagap.PelagosTrafficController")
    if traffic_controller_class and not tagged_actor("Pelagos.Traffic.Controller"):
        controller = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
            traffic_controller_class, unreal.Vector(0, 0, 0)
        )
        controller.set_actor_label("Pelagos Traffic Controller")
        controller.tags = ["Pelagos.Traffic.Controller"]
        controller.set_editor_property("arrival_definition", definition)

    if not tagged_actor("Pelagos.Light.Key"):
        light = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
            unreal.DirectionalLight, unreal.Vector(0, 0, 12000)
        )
        light.set_actor_label("Pelagos Stellar Key")
        light.tags = ["Pelagos.Light.Key"]
        component = light.get_component_by_class(unreal.DirectionalLightComponent)
        component.set_editor_property("intensity", 5.5)
        component.set_editor_property("light_color", unreal.Color(255, 214, 176, 255))
    if not tagged_actor("Pelagos.Light.Sky"):
        sky = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
            unreal.SkyLight, unreal.Vector(0, 0, 0)
        )
        sky.set_actor_label("Pelagos Space Fill")
        sky.tags = ["Pelagos.Light.Sky"]
        sky.get_component_by_class(unreal.SkyLightComponent).set_editor_property("intensity", 0.18)

    unreal.EditorLevelLibrary.save_current_level()
    unreal.EditorAssetLibrary.save_directory(ROOT, only_if_is_dirty=False, recursive=True)


def main():
    for directory in (ROOT, MESH_PATH, DATA_PATH, BLUEPRINT_PATH, "/Game/Assets/Maps/SpaceSystems"):
        ensure_directory(directory)
    definition = create_or_load_data_asset()
    blueprint = create_or_load_director_blueprint()
    environment = import_environment()
    build_level(environment, definition, blueprint)
    unreal.log("Pelagos Orbital Arrival assets and functional map built successfully")


main()
