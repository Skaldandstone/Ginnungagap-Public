"""Fail-fast validation for the 24-room Small Utility Escort operations district."""

import json
import math
import sys
from pathlib import Path

import unreal


MAP = "/Game/Assets/Maps/ShipProduction/L_SmallEscort_OperationsDeck"
PREFIX = "EscortOps_"
HARDPOINT_KINDS = ("DOORWAY", "BODY", "OBSTACLE", "BLOOM_GROWTH", "ACTIVITY", "DAMAGE_REPAIR")
PROJECT = Path(unreal.SystemLibrary.get_project_directory())
TOOLS = PROJECT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
from ship_room_placement_rules import validate_room_placements


def hardpoint_kind(value):
    for name in HARDPOINT_KINDS:
        if value == getattr(unreal.ShipGameplayHardpointType, name):
            return name
    return str(value).upper()


def validate_hardpoints(section, required, failures):
    label = section.get_actor_label()
    hardpoints = list(section.get_editor_property("gameplay_hardpoints"))
    ids = [str(item.get_editor_property("hardpoint_id")) for item in hardpoints]
    if len(ids) != len(set(ids)) or any(not value or value == "None" for value in ids):
        failures.append(f"{label} has missing or duplicate gameplay hardpoint IDs")
    counts = {}
    for hardpoint in hardpoints:
        kind = hardpoint_kind(hardpoint.get_editor_property("hardpoint_type"))
        counts[kind] = counts.get(kind, 0) + 1
        if hardpoint.get_editor_property("clearance_radius") <= 0.0:
            hardpoint_id = hardpoint.get_editor_property("hardpoint_id")
            failures.append(f"{label} hardpoint {hardpoint_id} has no clearance")
    for kind, minimum in required.items():
        if counts.get(kind, 0) < minimum:
            failures.append(f"{label} has {counts.get(kind, 0)} {kind} hardpoints; requires {minimum}")
    return counts


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if not levels.load_level(MAP):
        raise RuntimeError("Could not load Small Escort operations district")

    level_actors = actors.get_all_level_actors()
    by_label = {actor.get_actor_label(): actor for actor in level_actors}
    failures = []
    rooms = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "Room_")]
    if len(rooms) != 24:
        failures.append(f"room count {len(rooms)} != 24")
    codes = [str(room.get_editor_property("room_code")) for room in rooms]
    if len(codes) != len(set(codes)):
        failures.append("room codes are not unique")
    rooms_by_code = {str(room.get_editor_property("room_code")): room for room in rooms}
    payload = json.loads((PROJECT / "Config/Ships/SmallUtilityEscortInterior.json").read_text(encoding="utf-8"))
    district = payload["first_district"]
    configured_rooms = {room["code"]: room for room in district["rooms"]}
    placement_errors = validate_room_placements(
        district["rooms"], district["room_type_catalog"], district["room_placement_policy"]
    )
    failures.extend(f"placement policy: {error}" for error in placement_errors)
    numeric_ids = set()
    for code, room in rooms_by_code.items():
        configured = configured_rooms.get(code)
        if not configured:
            failures.append(f"room {code} is absent from the placement plan")
            continue
        room_id = int(room.get_editor_property("room_id"))
        room_type_id = int(room.get_editor_property("room_type_id"))
        placement_section = str(room.get_editor_property("placement_section"))
        if room_id != int(configured["room_id"]):
            failures.append(f"room {code} numeric id {room_id} != {configured['room_id']}")
        if room_type_id != int(configured["room_type_id"]):
            failures.append(f"room {code} type id {room_type_id} != {configured['room_type_id']}")
        if placement_section != configured["placement_section"]:
            failures.append(
                f"room {code} placement section {placement_section} != {configured['placement_section']}"
            )
        if room_id in numeric_ids:
            failures.append(f"duplicate reflected room id {room_id}")
        numeric_ids.add(room_id)
        tags = {str(tag) for tag in room.get_editor_property("tags")}
        for expected_tag in (f"RoomId={room_id}", f"RoomTypeId={room_type_id}",
                             f"PlacementSection={placement_section}"):
            if expected_tag not in tags:
                failures.append(f"room {code} lacks identity tag {expected_tag}")
    if len(numeric_ids) != 24:
        failures.append(f"numeric room identity count {len(numeric_ids)} != 24")
    room_sizes = {}
    for code, room in rooms_by_code.items():
        size = room.get_editor_property("module_size")
        authored = (round(size.x), round(size.y), round(size.z))
        room_sizes[code] = authored
        if any(value <= 0 for value in authored):
            failures.append(f"room {code} has invalid module size {authored}")
        extent = room.get_editor_property("section_bounds").get_unscaled_box_extent()
        expected_extent = tuple(value * 0.5 for value in authored)
        actual_extent = (extent.x, extent.y, extent.z)
        if any(abs(actual_extent[index] - expected_extent[index]) > 1.0 for index in range(3)):
            failures.append(
                f"room {code} bounds {actual_extent} do not match module size {authored}"
            )
    unique_room_sizes = set(room_sizes.values())
    if len(unique_room_sizes) < 8:
        failures.append(
            f"room sizing is effectively uniform: only {len(unique_room_sizes)} distinct footprints"
        )
    axis_minimum = tuple(min(size[index] for size in room_sizes.values()) for index in range(3))
    axis_maximum = tuple(max(size[index] for size in room_sizes.values()) for index in range(3))
    if axis_minimum != (1200, 1100, 400) or axis_maximum != (1800, 1600, 460):
        failures.append(
            f"room size range {axis_minimum}..{axis_maximum} != (1200, 1100, 400)..(1800, 1600, 460)"
        )
    corridors = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "Corridor_")]
    if len(corridors) != 24:
        failures.append(f"navigable corridor count {len(corridors)} != 24")
    population_directors = [
        actor for actor in level_actors
        if actor.get_actor_label() == PREFIX + "HardpointPopulationDirector"
    ]
    if len(population_directors) != 1:
        failures.append(f"hardpoint population director count {len(population_directors)} != 1")
    else:
        population = population_directors[0]
        expected_counts = {"body_count": 6, "obstacle_count": 10, "bloom_growth_count": 8}
        for property_name, expected in expected_counts.items():
            actual = population.get_editor_property(property_name)
            if actual != expected:
                failures.append(
                    f"hardpoint population {property_name} {actual} != {expected}"
                )
        for property_name in ("body_mesh", "obstacle_mesh", "bloom_growth_mesh"):
            if not population.get_editor_property(property_name):
                failures.append(f"hardpoint population has no {property_name}")
    side_door_directions = {}
    for code, room in rooms_by_code.items():
        center = room.get_actor_location()
        directions = []
        for connection in room.get_editor_property("connections"):
            target = connection.get_editor_property("target")
            if target:
                target_center = target.get_actor_location()
                if abs(target_center.x - center.x) < 1.0 and abs(target_center.y - center.y) > 1.0:
                    directions.append(1.0 if target_center.y > center.y else -1.0)
        side_door_directions[code] = directions

    deck_counts = {6: 0, 7: 0, 8: 0}
    for room in rooms:
        z = room.get_actor_location().z
        code = str(room.get_editor_property("room_code"))
        height = room_sizes[code][2]
        floor_z = z - height * 0.5
        deck = min(deck_counts, key=lambda value: abs(floor_z - {6: 0.0, 7: 520.0, 8: 1040.0}[value]))
        if abs(floor_z - {6: 0.0, 7: 520.0, 8: 1040.0}[deck]) > 1.0:
            failures.append(
                f"room {room.get_actor_label()} has off-grid floor {floor_z} for height {height}"
            )
        else:
            deck_counts[deck] += 1
        for binding in ("system_anchor", "loot_anchor", "maintenance_anchor",
                        "identity_light", "code_sign", "name_sign"):
            if not room.get_editor_property(binding):
                failures.append(f"room {room.get_actor_label()} has no {binding}")
        counts = validate_hardpoints(room, {
            "BODY": 2, "OBSTACLE": 2, "BLOOM_GROWTH": 2,
            "ACTIVITY": 4, "DAMAGE_REPAIR": 2,
        }, failures)
        section_thresholds = sum(
            1 for connection in room.get_editor_property("connections")
            if connection.get_editor_property("target")
        )
        if counts.get("DOORWAY", 0) != section_thresholds:
            failures.append(
                f"{room.get_actor_label()} doorway hardpoints {counts.get('DOORWAY', 0)} "
                f"!= connected section thresholds {section_thresholds}"
            )
    if any(count != 8 for count in deck_counts.values()):
        failures.append(f"deck room distribution {deck_counts} != 8/8/8")

    reciprocal_edges = sum(len(room.get_editor_property("connections")) for room in rooms)
    if reciprocal_edges != 56:
        failures.append(f"reciprocal section links {reciprocal_edges} != 56")
    bulkheads = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "Bulkhead_")]
    if len(bulkheads) != 48:
        failures.append(f"room-threshold bulkheads {len(bulkheads)} != 48")
    for door in bulkheads:
        for binding in ("room_side_hardpoint", "corridor_side_hardpoint", "room_section", "corridor_section"):
            if not door.get_editor_property(binding):
                failures.append(f"{door.get_actor_label()} has no {binding}")
    for corridor in corridors:
        if len(corridor.get_editor_property("connections")) != 2:
            failures.append(f"{corridor.get_actor_label()} does not connect exactly two room thresholds")
        validate_hardpoints(corridor, {
            "DOORWAY": 2, "BODY": 1, "OBSTACLE": 1, "BLOOM_GROWTH": 1,
            "ACTIVITY": 1, "DAMAGE_REPAIR": 1,
        }, failures)
    corridor_lengths = [
        corridor.get_editor_property("section_bounds").get_unscaled_box_extent().x * 2.0
        for corridor in corridors
    ]
    if corridor_lengths and min(corridor_lengths) < 200.0:
        failures.append(f"corridor length {min(corridor_lengths):.1f} cm is below 200 cm")
    if len({round(length) for length in corridor_lengths}) < 3:
        failures.append("corridors did not adapt to variable room footprints")
    corridor_details = [
        actor for actor in level_actors
        if "CorridorConceptDetail" in {
            str(tag) for tag in actor.get_editor_property("tags")
        }
    ]
    expected_corridor_details = len(corridors) * 14 + sum(
        max(1, int(math.ceil(length / 280.0))) for length in corridor_lengths
    )
    if len(corridor_details) != expected_corridor_details:
        failures.append(
            f"corridor concept detail count {len(corridor_details)} != {expected_corridor_details}"
        )
    detail_kinds = {
        str(tag)
        for actor in corridor_details
        for tag in actor.get_editor_property("tags")
    }
    required_detail_kinds = {
        "FloorTread", "RouteStripe", "Kickplate", "UtilityRail",
        "WallInset", "AccessPanel", "CeilingService", "PressureRib", "UtilityLight",
    }
    if not required_detail_kinds.issubset(detail_kinds):
        failures.append(
            f"corridor concept detail vocabulary is incomplete: {sorted(required_detail_kinds - detail_kinds)}"
        )
    ramps = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "VerticalRamp_")]
    if len(ramps) != 4:
        failures.append(f"vertical ramps {len(ramps)} != 4")
    vertical_pairs = (("FAB-06-01", "CCM-07-01"), ("CCM-07-01", "BRG-08-01"),
                      ("AUX-06-01", "CRY-07-01"), ("CRY-07-01", "CMP-08-01"))
    up_socket = unreal.ShipRoomSocket.UP
    down_socket = unreal.ShipRoomSocket.DOWN
    for lower_code, upper_code in vertical_pairs:
        lower = rooms_by_code.get(lower_code)
        upper = rooms_by_code.get(upper_code)
        if not lower or not upper:
            failures.append(f"vertical socket pair {lower_code}/{upper_code} has a missing room")
            continue
        if not lower.is_socket_connected(up_socket) or lower.get_connected_room(up_socket) != upper:
            failures.append(f"{lower_code}.UP is not connected to {upper_code}")
        if not upper.is_socket_connected(down_socket) or upper.get_connected_room(down_socket) != lower:
            failures.append(f"{upper_code}.DOWN is not connected to {lower_code}")
    fab_props = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "Prop_")]
    if len(fab_props) != 144:
        failures.append(f"Fab room dressing count {len(fab_props)} != 144")
    for prop in fab_props:
        label = prop.get_actor_label()
        component = prop.get_component_by_class(unreal.StaticMeshComponent)
        mesh = component.get_editor_property("static_mesh") if component else None
        source_path = mesh.get_path_name() if mesh else ""
        if not source_path.startswith(("/Game/Ice_Station/", "/Game/Sci-Fi_Flying_Cargo_Ship/")):
            failures.append(f"room dressing {label} is not sourced from an approved Fab pack")
        tags = {str(tag) for tag in prop.get_editor_property("tags")}
        if "FabRoomDressing" not in tags:
            failures.append(f"room dressing {label} lacks FabRoomDressing provenance tag")

        room_code = label[len(PREFIX + "Prop_"):].rsplit("_", 1)[0]
        room = rooms_by_code.get(room_code)
        if not room:
            failures.append(f"room dressing {label} does not identify a valid room")
            continue
        origin, extent = prop.get_actor_bounds(False)
        room_center = room.get_actor_location()
        tolerance = 2.0
        room_size = room_sizes[room_code]
        limits = ((room_size[0] * 0.5, origin.x, extent.x, room_center.x, "X"),
                  (room_size[1] * 0.5, origin.y, extent.y, room_center.y, "Y"),
                  (room_size[2] * 0.5, origin.z, extent.z, room_center.z, "Z"))
        for half_size, prop_center, prop_extent, room_axis, axis_name in limits:
            if abs(prop_center - room_axis) + prop_extent > half_size + tolerance:
                failures.append(
                    f"room dressing {label} exceeds its room on {axis_name}: "
                    f"prop center={prop_center:.2f} extent={prop_extent:.2f}, "
                    f"room center={room_axis:.2f} half={half_size:.2f}"
                )
        if abs(origin.y - room_center.y) - extent.y < 180.0:
            failures.append(f"room dressing {label} intrudes into the 3.6 m central circulation lane")
        for side in side_door_directions.get(room_code, []):
            if (origin.y - room_center.y) * side > 0.0 and abs(origin.x - room_center.x) - extent.x < 180.0:
                failures.append(
                    f"room dressing {label} intrudes into a 3.6 m side-door approach: "
                    f"offset={origin.x - room_center.x:.2f} extent={extent.x:.2f}"
                )

    work_lights = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "WorkLight_")]
    corridor_lights = [
        actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "CorridorLight_")
    ]
    work_zones = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "WorkZone_")]
    structural_ribs = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "Rib_")]
    arch_panels = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "ArchPanel_")]
    arch_trims = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "ArchTrim_")]
    ceiling_housings = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "CeilingHousing_")]
    ceiling_strips = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "CeilingStrip_")]
    bay_posts = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "BayPost_")]
    end_panels = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "EndPanel_")]
    end_trims = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "EndTrim_")]
    end_posts = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "EndPost_")]
    stair_guard_rails = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "StairGuardRail_")]
    stair_guard_posts = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "StairGuardPost_")]
    if len(work_lights) != 48:
        failures.append(f"neutral work light count {len(work_lights)} != 48")
    if len(corridor_lights) != 24:
        failures.append(f"corridor work light count {len(corridor_lights)} != 24")
    if len(work_zones) != 48:
        failures.append(f"functional floor zone count {len(work_zones)} != 48")
    if len(structural_ribs) != 96:
        failures.append(f"structural rib count {len(structural_ribs)} != 96")
    if len(arch_panels) != 96:
        failures.append(f"architectural wall panel count {len(arch_panels)} != 96")
    if len(arch_trims) != 48:
        failures.append(f"architectural wall trim count {len(arch_trims)} != 48")
    if len(ceiling_housings) != 48 or len(ceiling_strips) != 48:
        failures.append(
            f"ceiling fixture counts housing={len(ceiling_housings)} strip={len(ceiling_strips)} != 48/48"
        )
    if len(bay_posts) != 96:
        failures.append(f"work-bay divider post count {len(bay_posts)} != 96")
    if len(end_panels) != 96:
        failures.append(f"architectural end panel count {len(end_panels)} != 96")
    if len(end_trims) != 48:
        failures.append(f"architectural end trim count {len(end_trims)} != 48")
    if len(end_posts) != 96:
        failures.append(f"bulkhead divider post count {len(end_posts)} != 96")
    if len(stair_guard_rails) != 8 or len(stair_guard_posts) != 16:
        failures.append(
            f"vertical safety counts rails={len(stair_guard_rails)} posts={len(stair_guard_posts)} != 8/16"
        )

    activities = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "Activity_")]
    if len(activities) != 24:
        failures.append(f"interactive activity station count {len(activities)} != 24")
    activity_rooms = set()
    for station in activities:
        label = station.get_actor_label()
        room_code = label[len(PREFIX + "Activity_"):].split("_", 1)[0]
        activity_rooms.add(room_code)
        room = rooms_by_code.get(room_code)
        if not room:
            failures.append(f"activity station {label} does not identify a valid room")
            continue
        if station.get_editor_property("target_actor") != room:
            failures.append(f"activity station {label} does not target its owning room")
        if str(station.get_editor_property("station_id")) != f"{room_code}-ACT-00":
            failures.append(f"activity station {label} has no stable station id")
        if str(station.get_editor_property("owning_room_code")) != room_code:
            failures.append(f"activity station {label} has wrong owning room code")
        station_tags = {str(tag) for tag in station.get_editor_property("tags")}
        if "DamageRepairHardpoint" not in station_tags:
            failures.append(f"activity station {label} is not marked as hardpoint-placed")
        station_location = station.get_actor_location()
        room_location = room.get_actor_location()
        repair_locations = []
        for hardpoint in room.get_editor_property("gameplay_hardpoints"):
            if hardpoint.get_editor_property("hardpoint_type") == unreal.ShipGameplayHardpointType.DAMAGE_REPAIR:
                local = hardpoint.get_editor_property("relative_location")
                repair_locations.append((room_location.x + local.x, room_location.y + local.y, room_location.z + local.z))
        if not any(
            (station_location.x - location[0]) ** 2
            + (station_location.y - location[1]) ** 2
            + (station_location.z - location[2]) ** 2 < 1.0
            for location in repair_locations
        ):
            failures.append(f"activity station {label} is not on a damage-repair hardpoint")
        mesh_component = station.get_editor_property("mesh")
        if not mesh_component or not mesh_component.get_editor_property("static_mesh"):
            failures.append(f"activity station {label} has no visible terminal mesh")
        origin, extent = station.get_actor_bounds(False)
        room_center = room.get_actor_location()
        if abs(origin.y - room_center.y) - extent.y < 180.0:
            failures.append(f"activity station {label} intrudes into the 3.6 m central circulation lane")
        for side in side_door_directions.get(room_code, []):
            if (origin.y - room_center.y) * side > 0.0 and abs(origin.x - room_center.x) - extent.x < 180.0:
                failures.append(f"activity station {label} blocks a side-door approach")
    if activity_rooms != set(rooms_by_code):
        failures.append("activity stations do not cover every room exactly once")

    pickups = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "Pickup_")]
    if len(pickups) != 4:
        failures.append(f"survival supply pickup count {len(pickups)} != 4")
    pickup_rooms = set()
    for pickup in pickups:
        label = pickup.get_actor_label()
        room_code = label[len(PREFIX + "Pickup_"):].split("_", 1)[0]
        pickup_rooms.add(room_code)
        if room_code not in rooms_by_code:
            failures.append(f"survival pickup {label} does not identify a valid room")
        visual = pickup.get_editor_property("visual_mesh")
        if not visual or not visual.get_editor_property("static_mesh"):
            failures.append(f"survival pickup {label} has no visible mesh")
    if pickup_rooms != {"MED-07-01", "SUR-07-01", "LIF-06-01", "EVA-06-01"}:
        failures.append(f"survival pickup room coverage is incorrect: {sorted(pickup_rooms)}")

    expected_checkpoints = {
        "OPS-08-01": "EscortOps_Deck08_Entry",
        "CCM-07-01": "EscortOps_Deck07_CrewCommons",
        "DCR-06-01": "EscortOps_Deck06_DamageControl",
    }
    checkpoints = [
        actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX + "Checkpoint_")
    ]
    if len(checkpoints) != len(expected_checkpoints):
        failures.append(f"deck checkpoint count {len(checkpoints)} != {len(expected_checkpoints)}")
    checkpoint_rooms = set()
    for checkpoint in checkpoints:
        label = checkpoint.get_actor_label()
        room_code = label[len(PREFIX + "Checkpoint_"):]
        checkpoint_rooms.add(room_code)
        expected_id = expected_checkpoints.get(room_code)
        if not expected_id or str(checkpoint.get_editor_property("checkpoint_id")) != expected_id:
            failures.append(f"checkpoint {label} has an invalid stable id")
        room = rooms_by_code.get(room_code)
        if not room:
            failures.append(f"checkpoint {label} has no owning room")
            continue
        delta = checkpoint.get_actor_location() - room.get_actor_location()
        if abs(delta.x) > 1.0 or abs(delta.y) > 1.0:
            failures.append(f"checkpoint {label} is outside its room's safe center lane")
    if checkpoint_rooms != set(expected_checkpoints):
        failures.append(f"deck checkpoint room coverage is incorrect: {sorted(checkpoint_rooms)}")

    directors = [actor for actor in level_actors if actor.get_actor_label() == PREFIX + "GameplayDirector"]
    objectives = [actor for actor in level_actors if actor.get_actor_label() == PREFIX + "ObjectiveConsole_DCR-06-01"]
    if len(directors) != 1:
        failures.append(f"district gameplay director count {len(directors)} != 1")
    else:
        director = directors[0]
        if str(director.get_editor_property("primary_objective_id")) != "EscortOps_RestoreOperations":
            failures.append("district gameplay director objective id is incorrect")
        if director.get_editor_property("spawn_gameplay_on_begin_play"):
            failures.append("district gameplay director would duplicate authored encounters or pickups")
    if len(objectives) != 1:
        failures.append(f"primary objective console count {len(objectives)} != 1")
    elif str(objectives[0].get_editor_property("objective_id")) != "EscortOps_RestoreOperations":
        failures.append("primary objective console is not linked to the district objective")

    for label in (PREFIX + "PlayerStart", PREFIX + "NavMeshBounds",
                  PREFIX + "InteriorFill", PREFIX + "ShipLocalRegistration"):
        if label not in by_label:
            failures.append("missing " + label)
    registration = by_label.get(PREFIX + "ShipLocalRegistration")
    if registration:
        tags = {str(tag) for tag in registration.get_editor_property("tags")}
        required = {"SmallUtilityEscort", "StreamedInteriorDistrict",
                    "ShipLocalX=-22000", "ShipLocalY=0", "ShipLocalZ=1800"}
        if not required.issubset(tags):
            failures.append("ship-local registration tags are incomplete")

    generated = [actor for actor in level_actors if actor.get_actor_label().startswith(PREFIX)]
    expected_generated = 1610 + expected_corridor_details
    if len(generated) != expected_generated:
        failures.append(f"generated actor count {len(generated)} != {expected_generated}")
    if failures:
        raise RuntimeError("Small Escort operations validation failed:\n" + "\n".join(failures))
    unreal.log(
        f"Small Escort operations validation passed: {len(rooms)} rooms, {len(corridors)} corridors, "
        f"{len(bulkheads)} threshold bulkheads, "
        f"{len(ramps)} vertical links, {len(fab_props)} Fab-dressed props, "
        f"{len(unique_room_sizes)} room sizes ({axis_minimum}..{axis_maximum}), "
        f"{len(corridor_details)} concept corridor details, "
        f"{len(work_lights)} room work lights, {len(corridor_lights)} corridor lights, "
        f"{len(activities)} activities, {len(pickups)} pickups, "
        f"{len(checkpoints)} checkpoints, "
        f"{len(generated)} generated actors")


if __name__ == "__main__":
    main()
