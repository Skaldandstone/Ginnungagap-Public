"""Fit gameplay-aware modular rooms into the three production ship districts.

The pass owns only actors prefixed ``ModularFit_``. It partitions existing showcase geometry,
places non-overlapping AModularShipRoom volumes, connects them through production bulkheads, and
retires the legacy district-wide pressure section from navigation without deleting it.
"""

from __future__ import annotations

import unreal


MAP_ROOT = "/Game/Assets/Maps/ShipProduction"
MESH_ROOT = "/Game/Assets/Ships/Production/Meshes"
BP_ROOT = "/Game/Assets/Ships/Production/Blueprints"
PREFIX = "ModularFit_"


DRESSING_PROFILES = {
    "companionway": (
        "/Game/Assets/Ships/Production/Meshes/SM_Prop_Locker",
        "/Game/Assets/Ships/Production/Meshes/SM_Prop_PowerJunction"),
    "bridge": (
        "/Game/Assets/Models/RoomMachinery/SM_Command_HolographicTable",
        "/Game/Assets/Models/RoomMachinery/SM_Command_HelmChair"),
    "sensors": (
        "/Game/Assets/Models/ShipSystems/SM_System_SensorConsole",
        "/Game/Assets/Models/RoomMachinery/SM_Engineering_BreakerBank"),
    "medical": (
        "/Game/Assets/Models/Environment/SM_Prop_MedicalBed",
        "/Game/Assets/Models/RoomMachinery/SM_Medical_DiagnosticArch"),
    "crew": (
        "/Game/Assets/Models/Environment/SM_Prop_Bunk",
        "/Game/Assets/Models/Environment/SM_Prop_GalleyUnit"),
    "cargo": (
        "/Game/Assets/Models/RoomMachinery/SM_Cargo_Pallet",
        "/Game/Assets/Models/RoomMachinery/SM_Cargo_HandLoader"),
    "damage": (
        "/Game/Assets/Models/Environment/SM_Prop_Workbench",
        "/Game/Assets/Models/DamageControl/SM_Emergency_FireSuppressionCart"),
    "engineering": (
        "/Game/Assets/Models/RoomMachinery/SM_Engineering_BreakerBank",
        "/Game/Assets/Models/RoomMachinery/SM_Engineering_CoolantPump"),
    "reactor": (
        "/Game/Assets/Models/RoomMachinery/SM_Engineering_ReactorCoil",
        "/Game/Assets/Models/RoomMachinery/SM_Engineering_BreakerBank"),
    "escape": (
        "/Game/Assets/Models/Environment/SM_Prop_AirlockBench",
        "/Game/Assets/Models/ShipSystems/SM_System_EscapePod"),
    "armory": (
        "/Game/Assets/Models/Environment/SM_Prop_ToolCabinet",
        "/Game/Assets/Ships/Production/Meshes/SM_Prop_CargoCrate"),
}

ROOM_COLORS = {
    "companionway": unreal.Color(55, 155, 220),
    "bridge": unreal.Color(70, 145, 255),
    "sensors": unreal.Color(45, 200, 235),
    "medical": unreal.Color(r=55, g=230, b=145),
    "crew": unreal.Color(r=100, g=145, b=230),
    "cargo": unreal.Color(240, 170, 45),
    "damage": unreal.Color(255, 75, 25),
    "engineering": unreal.Color(r=255, g=105, b=30),
    "reactor": unreal.Color(255, 45, 20),
    "escape": unreal.Color(255, 205, 55),
    "armory": unreal.Color(230, 120, 35),
}

# power priority, kW draw, occupancy, hazard tier, loot tier, access tier, jump-critical
GAMEPLAY_PROFILES = {
    "companionway": (7, 4.0, 18, 1, 0, "PUBLIC", True),
    "bridge": (10, 18.0, 12, 2, 3, "SECURE", True),
    "sensors": (9, 14.0, 8, 2, 3, "RESTRICTED", True),
    "medical": (9, 12.0, 14, 1, 4, "RESTRICTED", False),
    "crew": (4, 8.0, 24, 1, 2, "CREW", False),
    "cargo": (3, 6.0, 16, 2, 5, "CREW", False),
    "damage": (8, 10.0, 10, 4, 4, "RESTRICTED", True),
    "engineering": (10, 24.0, 12, 4, 4, "SECURE", True),
    "reactor": (10, 32.0, 8, 5, 5, "SECURE", True),
    "escape": (8, 7.0, 30, 2, 2, "PUBLIC", False),
    "armory": (5, 5.0, 6, 3, 5, "SECURE", False),
}


ROOM_ARCHETYPES = {
    "companionway": "COMPANIONWAY",
    "bridge": "BRIDGE",
    "sensors": "SENSOR_OPERATIONS",
    "medical": "MEDICAL_BAY",
    "crew": "CREW_BERTHING",
    "cargo": "CARGO_BAY",
    "damage": "DAMAGE_CONTROL",
    "engineering": "ENGINEERING",
    "reactor": "REACTOR_CONTROL",
    "escape": "ESCAPE_BAY",
    "armory": "ARMORY",
}

SECTION_TYPES = {
    "companionway": "CORRIDOR",
    "bridge": "BRIDGE",
    "sensors": "BRIDGE",
    "medical": "MED_BAY",
    "crew": "CREW_QUARTERS",
    "cargo": "CARGO_BAY",
    "damage": "DECK",
    "engineering": "ENGINE_ROOM",
    "reactor": "ENGINE_ROOM",
    "escape": "AIRLOCK",
    "armory": "CARGO_BAY",
}


LAYOUTS = {
    "L_Small_Companionway_Showcase": {
        "width": 1200.0,
        "length": 5200.0,
        "height": 430.0,
        "rooms": (
            ("SML-CMP-01", "Forward Companionway", "companionway"),
            ("SML-OPS-01", "Utility Operations", "sensors"),
            ("SML-MED-01", "Emergency Treatment", "medical"),
            ("SML-ENG-01", "Drive Access", "engineering"),
        ),
    },
    "L_Medium_ExpressSpine_Showcase": {
        "width": 3200.0,
        "length": 7200.0,
        "height": 760.0,
        "rooms": (
            ("MED-BRG-01", "Corvette Bridge", "bridge"),
            ("MED-CIC-01", "Combat Information Center", "bridge"),
            ("MED-SNS-01", "Sensor Operations", "sensors"),
            ("MED-CMP-01", "Express Companionway", "companionway"),
            ("MED-CGO-01", "Mission Cargo", "cargo"),
            ("MED-ENG-01", "Engineering Control", "engineering"),
        ),
    },
    "L_Large_CarrierConcourse_Showcase": {
        "width": 4800.0,
        "length": 9200.0,
        "height": 1200.0,
        "rooms": (
            ("LRG-BRG-01", "Flight Operations", "bridge"),
            ("LRG-MED-01", "Carrier Medical", "medical"),
            ("LRG-CRW-01", "Duty Berthing", "crew"),
            ("LRG-CMP-01", "Carrier Concourse", "companionway"),
            ("LRG-CGO-01", "Expedition Stores", "cargo"),
            ("LRG-DCR-01", "Damage Control Central", "damage"),
            ("LRG-ENG-01", "Power Distribution", "engineering"),
            ("LRG-ESC-01", "Evacuation Muster", "escape"),
        ),
    },
}


def load(path):
    asset = unreal.load_asset(path)
    if not asset:
        raise RuntimeError("Missing required fitting asset: " + path)
    return asset


def enum_value(enum_type, name):
    try:
        return getattr(enum_type, name)
    except AttributeError as exc:
        raise RuntimeError(f"Missing {enum_type.__name__}.{name}; rebuild C++ before fitting rooms") from exc


def clear_generated(actors):
    generated = [actor for actor in actors.get_all_level_actors()
                 if actor.get_actor_label().startswith(PREFIX)]
    if generated:
        actors.destroy_actors(generated)


def spawn_partition_wall(actors, wall_mesh, x, width, height, partition_index):
    tile = 400.0
    tile_count = max(1, round(width / tile))
    for tile_index in range(tile_count):
        y = (tile_index - (tile_count - 1) * 0.5) * tile
        if abs(y) < 250.0:
            continue
        wall = actors.spawn_actor_from_class(
            unreal.StaticMeshActor, unreal.Vector(x, y, 0.0), unreal.Rotator(0.0, 90.0, 0.0))
        wall.set_actor_label(f"{PREFIX}Partition_{partition_index:02d}_{tile_index:02d}")
        wall.set_actor_scale3d(unreal.Vector(1.0, 1.0, height / 400.0))
        wall.static_mesh_component.set_static_mesh(wall_mesh)


def make_section_connection(target, door):
    connection = unreal.SectionConnection()
    connection.set_editor_property("target", target)
    connection.set_editor_property("door", door)
    connection.set_editor_property("transfer_coefficient", 1.0)
    return connection


def spawn_static_dressing(actors, mesh, location, rotation, label, scale=(1.0, 1.0, 1.0), material=None):
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(*rotation))
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    actor.static_mesh_component.set_static_mesh(mesh)
    if material:
        actor.static_mesh_component.set_material(0, material)
    return actor


def spawn_room_sign(actors, code, text, location, height, color, suffix):
    sign = actors.spawn_actor_from_class(
        unreal.TextRenderActor, unreal.Vector(*location), unreal.Rotator(0.0, 90.0, 0.0))
    sign.set_actor_label(f"{PREFIX}Sign_{code}_{suffix}")
    component = sign.get_component_by_class(unreal.TextRenderComponent)
    component.set_editor_property("text", text)
    component.set_editor_property("world_size", height)
    component.set_editor_property("text_render_color", color)
    return sign


def spawn_room_anchor(actors, code, anchor_kind, location):
    anchor = actors.spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(*location), unreal.Rotator())
    anchor.set_actor_label(f"{PREFIX}Anchor_{code}_{anchor_kind}")
    anchor.set_editor_property(
        "tags", [unreal.Name("RoomAnchor"), unreal.Name(anchor_kind + "Anchor"), unreal.Name(code)])
    return anchor


def dress_room(actors, assets, accent_material, code, display_name, kind, center_x,
               room_length, width, height):
    primary, secondary = assets[kind]
    margin_y = min(width * 0.36, width * 0.5 - 90.0)
    primary_actor = spawn_static_dressing(
        actors, primary, (center_x - room_length * 0.18, margin_y, 15.0), (0.0, 180.0, 0.0),
        f"{PREFIX}Dressing_{code}_Primary")
    secondary_actor = spawn_static_dressing(
        actors, secondary, (center_x + room_length * 0.18, -margin_y, 15.0), (0.0, 0.0, 0.0),
        f"{PREFIX}Dressing_{code}_Secondary")
    terminal = spawn_static_dressing(
        actors, assets["terminal"], (center_x, -width * 0.5 + 65.0, 15.0), (0.0, 0.0, 0.0),
        f"{PREFIX}Dressing_{code}_Terminal")

    sign_z = min(height - 70.0, max(190.0, height * 0.55))
    code_sign = spawn_room_sign(
        actors, code, code, (center_x - room_length * 0.28, -width * 0.5 + 34.0, sign_z),
        32.0, ROOM_COLORS[kind], "Code")
    name_sign = spawn_room_sign(
        actors, code, display_name.upper(),
        (center_x - room_length * 0.28, -width * 0.5 + 33.0, sign_z - 48.0),
        20.0, unreal.Color(205, 220, 225), "Name")

    light = actors.spawn_actor_from_class(
        unreal.PointLight, unreal.Vector(center_x, 0.0, height - 65.0), unreal.Rotator())
    light.set_actor_label(f"{PREFIX}Light_{code}")
    light_component = light.get_component_by_class(unreal.PointLightComponent)
    light_component.set_editor_property("intensity", 1250.0)
    light_component.set_editor_property("attenuation_radius", min(1000.0, max(450.0, room_length * 0.7)))
    light_component.set_editor_property("light_color", ROOM_COLORS[kind])
    light_component.set_editor_property("cast_shadows", False)

    system_anchor = spawn_room_anchor(actors, code, "System", (center_x, margin_y * 0.55, 30.0))
    loot_anchor = spawn_room_anchor(actors, code, "Loot", (center_x + room_length * 0.28, margin_y * 0.25, 30.0))
    maintenance_anchor = spawn_room_anchor(
        actors, code, "Maintenance", (center_x - room_length * 0.28, -margin_y * 0.25, 30.0))

    for side, y in (("Port", -width * 0.28), ("Starboard", width * 0.28)):
        spawn_static_dressing(
            actors, assets["floor"], (center_x, y, 3.0), (0.0, 0.0, 0.0),
            f"{PREFIX}Hazard_{code}_{side}",
            scale=(max(0.2, room_length / 400.0 * 0.72), 0.08, 0.08), material=accent_material)

    return {
        "primary": primary_actor,
        "secondary": secondary_actor,
        "terminal": terminal,
        "code_sign": code_sign,
        "name_sign": name_sign,
        "identity_light": light,
        "system_anchor": system_anchor,
        "loot_anchor": loot_anchor,
        "maintenance_anchor": maintenance_anchor,
    }


def fit_level(map_name, spec, wall_mesh, bulkhead_class, assets, accent_material):
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(f"{MAP_ROOT}/{map_name}"):
        raise RuntimeError("Could not load ship district: " + map_name)

    clear_generated(actors)
    level_actors = actors.get_all_level_actors()
    aggregate = next((actor for actor in level_actors
                      if actor.get_actor_label() == "Gameplay_PressureSection"), None)
    if not aggregate:
        raise RuntimeError(map_name + " is missing Gameplay_PressureSection")
    aggregate.set_editor_property("register_with_navigation", False)
    if map_name == "L_Small_Companionway_Showcase":
        director = next((actor for actor in level_actors
                         if actor.get_actor_label() == "Gameplay_DistrictDirector"), None)
        if not director:
            raise RuntimeError(map_name + " is missing Gameplay_DistrictDirector")
        director.set_editor_property("spawn_demo_systems", True)

    room_specs = spec["rooms"]
    room_length = spec["length"] / len(room_specs)
    rooms = []
    for index, (code, display_name, kind) in enumerate(room_specs):
        x = -spec["length"] * 0.5 + room_length * (index + 0.5)
        room = actors.spawn_actor_from_class(
            unreal.ModularShipRoom,
            unreal.Vector(x, 0.0, spec["height"] * 0.5),
            unreal.Rotator())
        room.set_actor_label(f"{PREFIX}Room_{code}")
        room.set_editor_property("room_code", code)
        room.set_editor_property("display_name", display_name)
        room.set_editor_property(
            "archetype", enum_value(unreal.ShipRoomArchetype, ROOM_ARCHETYPES[kind]))
        room.set_editor_property(
            "section_type", enum_value(unreal.ShipSectionType, SECTION_TYPES[kind]))
        room.set_editor_property("module_size", unreal.Vector(room_length, spec["width"], spec["height"]))
        room.get_editor_property("section_bounds").set_box_extent(
            unreal.Vector(room_length * 0.5, spec["width"] * 0.5, spec["height"] * 0.5))
        enabled = []
        if index > 0:
            enabled.append(unreal.ShipRoomSocket.AFT)
        if index + 1 < len(room_specs):
            enabled.append(unreal.ShipRoomSocket.FORWARD)
        room.set_editor_property("enabled_sockets", enabled)
        room.set_editor_property("tags", [unreal.Name("FittedShipRoom"), unreal.Name(code)])
        profile_values = GAMEPLAY_PROFILES[kind]
        profile = unreal.ShipRoomGameplayProfile()
        for property_name, value in zip(
                ("power_priority", "nominal_power_draw", "safe_occupancy", "hazard_tier", "loot_tier"),
                profile_values[:5]):
            profile.set_editor_property(property_name, value)
        profile.set_editor_property(
            "access_tier", enum_value(unreal.ShipRoomAccessTier, profile_values[5]))
        profile.set_editor_property("critical_for_jump", profile_values[6])
        room.set_editor_property("gameplay_profile", profile)

        bindings = dress_room(actors, assets, accent_material, code, display_name, kind, x,
                              room_length, spec["width"], spec["height"])
        for property_name in ("system_anchor", "loot_anchor", "maintenance_anchor",
                              "identity_light", "code_sign", "name_sign"):
            room.set_editor_property(property_name, bindings[property_name])
        rooms.append(room)

    doors = []
    for index in range(len(rooms) - 1):
        boundary_x = -spec["length"] * 0.5 + room_length * (index + 1)
        door = actors.spawn_actor_from_class(
            bulkhead_class, unreal.Vector(boundary_x, 0.0, 0.0), unreal.Rotator(0.0, 90.0, 0.0))
        door.set_actor_label(f"{PREFIX}Bulkhead_{room_specs[index][0]}_{room_specs[index + 1][0]}")
        doors.append(door)
        spawn_partition_wall(actors, wall_mesh, boundary_x, spec["width"], spec["height"], index)

    for index, room in enumerate(rooms):
        connections = []
        if index > 0:
            connections.append(make_section_connection(rooms[index - 1], doors[index - 1]))
        if index + 1 < len(rooms):
            connections.append(make_section_connection(rooms[index + 1], doors[index]))
        room.set_editor_property("connections", connections)
        if index + 1 < len(rooms):
            if not room.connect_room(unreal.ShipRoomSocket.FORWARD, rooms[index + 1], unreal.ShipRoomSocket.AFT):
                raise RuntimeError(f"Could not reserve sockets between {room_specs[index][0]} and {room_specs[index + 1][0]}")

    levels.save_current_level()
    unreal.log(
        f"Fitted {map_name}: {len(rooms)} rooms, {len(doors)} pressure bulkheads, "
        f"{spec['length']:.0f}x{spec['width']:.0f}x{spec['height']:.0f} cm envelope")


def main():
    wall_mesh = load(MESH_ROOT + "/SM_Kit_Wall_4m")
    assets = {kind: tuple(load(path) for path in paths)
              for kind, paths in DRESSING_PROFILES.items()}
    assets["terminal"] = load(MESH_ROOT + "/SM_Prop_WallTerminal")
    assets["floor"] = load(MESH_ROOT + "/SM_Kit_Floor_4m")
    accent_material = load("/Game/Assets/Ships/Production/Materials/M_Ship_Accent_Utility")
    bulkhead_blueprint = load(BP_ROOT + "/BP_Ship_ProductionBulkhead")
    bulkhead_class = bulkhead_blueprint.generated_class()
    for map_name, spec in LAYOUTS.items():
        fit_level(map_name, spec, wall_mesh, bulkhead_class, assets, accent_material)
    unreal.log("Modular room fitting complete: 18 rooms installed across three ship districts.")


if __name__ == "__main__":
    main()
