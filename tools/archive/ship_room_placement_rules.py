"""Deterministic identity and proximity rules for procedural ship-room placement.

`room_id` identifies one persistent room instance. `room_type_id` identifies a reusable room
function and may appear many times across a ship. Same-type instances are kept apart unless their
type explicitly permits clustering inside a named placement section (for example, dormitories in
habitation).
"""

from __future__ import annotations

import random
from copy import deepcopy


def type_catalog_by_id(catalog):
    result = {}
    for entry in catalog:
        type_id = int(entry["room_type_id"])
        if type_id <= 0 or type_id in result:
            raise ValueError(f"Invalid or duplicate room_type_id {type_id}")
        result[type_id] = entry
    return result


def placement_distance(left, right, deck_distance_weight=2):
    """Return Manhattan placement distance, treating one deck as two grid cells."""
    return (
        abs(int(left["grid"][0]) - int(right["grid"][0]))
        + abs(int(left["grid"][1]) - int(right["grid"][1]))
        + abs(int(left["deck"]) - int(right["deck"])) * int(deck_distance_weight)
    )


def cluster_exception_applies(left, right, rule):
    section = str(left.get("placement_section", ""))
    return (
        section
        and section == str(right.get("placement_section", ""))
        and section in set(rule.get("allow_same_type_cluster_in_sections", ()))
    )


def can_place_room(candidate, placed_rooms, catalog_by_id, policy):
    """Return `(allowed, reason)` for a candidate that already contains deck/grid coordinates."""
    candidate_type = int(candidate["room_type_id"])
    rule = catalog_by_id.get(candidate_type)
    if not rule:
        return False, f"unknown room_type_id {candidate_type}"

    minimum = int(rule.get(
        "same_type_min_grid_distance",
        policy.get("default_same_type_min_grid_distance", 3),
    ))
    deck_weight = int(policy.get("deck_distance_weight", 2))
    for existing in placed_rooms:
        if int(existing["room_type_id"]) != candidate_type:
            continue
        if cluster_exception_applies(candidate, existing, rule):
            continue
        distance = placement_distance(candidate, existing, deck_weight)
        if distance < minimum:
            return False, (
                f"type {candidate_type} room {candidate['room_id']} is distance {distance} from "
                f"room {existing['room_id']}; minimum is {minimum}"
            )
    return True, ""


def validate_room_placements(rooms, catalog, policy):
    catalog_by_id = type_catalog_by_id(catalog)
    errors = []
    room_ids = set()
    occupied = set()
    placed = []
    for room in rooms:
        room_id = int(room.get("room_id", 0))
        if room_id <= 0:
            errors.append(f"room {room.get('code', '<unknown>')} has no positive room_id")
        elif room_id in room_ids:
            errors.append(f"duplicate room_id {room_id}")
        room_ids.add(room_id)

        cell = (int(room["deck"]), int(room["grid"][0]), int(room["grid"][1]))
        if cell in occupied:
            errors.append(f"multiple rooms occupy cell {cell}")
        occupied.add(cell)

        allowed, reason = can_place_room(room, placed, catalog_by_id, policy)
        if not allowed:
            errors.append(f"room {room.get('code', room_id)}: {reason}")
        placed.append(room)
    return errors


def assign_room_locations(room_instances, available_slots, catalog, policy, seed=0):
    """Assign slots with deterministic backtracking while enforcing same-type proximity.

    Instances must contain identity/type/section fields but no grid location. Slots contain `deck`
    and `grid`. The returned room dictionaries are copies; inputs are never mutated.
    """
    if len(room_instances) > len(available_slots):
        raise ValueError("There are more room instances than available placement slots")
    catalog_by_id = type_catalog_by_id(catalog)
    randomizer = random.Random(seed)
    instances = [deepcopy(room) for room in room_instances]
    slots = [deepcopy(slot) for slot in available_slots]
    randomizer.shuffle(slots)

    frequency = {}
    for room in instances:
        frequency[int(room["room_type_id"])] = frequency.get(int(room["room_type_id"]), 0) + 1
    instances.sort(key=lambda room: (-frequency[int(room["room_type_id"])], int(room["room_id"])))

    placed = []

    def visit(index, remaining_slots):
        if index == len(instances):
            return True
        instance = instances[index]
        for slot_index, slot in enumerate(remaining_slots):
            candidate = {**instance, **slot}
            allowed, _ = can_place_room(candidate, placed, catalog_by_id, policy)
            if not allowed:
                continue
            placed.append(candidate)
            if visit(index + 1, remaining_slots[:slot_index] + remaining_slots[slot_index + 1:]):
                return True
            placed.pop()
        return False

    if not visit(0, slots):
        raise ValueError("No placement satisfies the configured room-type proximity rules")
    return sorted(placed, key=lambda room: int(room["room_id"]))
