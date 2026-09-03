"""Build the first ship-scale interior district for the Small Utility Escort.

The generated level contains 24 gameplay-addressable rooms on three connected decks. It is
registered in the 1.4 km escort's local coordinate system but remains a separate streamed map,
so the unoptimized 705-component exterior does not inflate the interior draw-call budget.
"""

from __future__ import annotations

import json
import math
import sys
from collections import defaultdict, deque
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
TOOLS = PROJECT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
from ship_room_placement_rules import type_catalog_by_id, validate_room_placements

CONFIG = PROJECT / "Config/Ships/SmallUtilityEscortInterior.json"
MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_SmallEscort_OperationsDeck"
PREFIX = "EscortOps_"
REPORT = PROJECT / "Saved/Reports/SmallEscortOperationsDistrict.json"

DEFAULT_ROOM_SIZE = (1500.0, 1400.0, 430.0)
CORRIDOR_SIZE = (500.0, 360.0, 430.0)
MIN_CORRIDOR_LENGTH = 200.0
DECK_SPACING = 520.0
DECK_Z = {6: 215.0, 7: 735.0, 8: 1255.0}
DECK_FLOOR_Z = {deck: center - DEFAULT_ROOM_SIZE[2] * 0.5 for deck, center in DECK_Z.items()}
GRID_X = (-3000.0, -1000.0, 1000.0, 3000.0)
GRID_Y = (-950.0, 950.0)

ARCHETYPES = {
    "companionway": "COMPANIONWAY", "bridge": "BRIDGE", "sensors": "SENSOR_OPERATIONS",
    "medical": "MEDICAL_BAY", "crew": "CREW_BERTHING", "cargo": "CARGO_BAY",
    "damage": "DAMAGE_CONTROL", "engineering": "ENGINEERING", "reactor": "REACTOR_CONTROL",
    "escape": "ESCAPE_BAY", "armory": "ARMORY",
}
SECTIONS = {
    "corridor": "CORRIDOR", "bridge": "BRIDGE", "medical": "MED_BAY",
    "crew": "CREW_QUARTERS", "cargo": "CARGO_BAY", "deck": "DECK",
    "engineering": "ENGINE_ROOM", "airlock": "AIRLOCK",
}
COLORS = {
    "companionway": (55, 155, 220), "bridge": (70, 145, 255), "sensors": (45, 200, 235),
    "medical": (55, 230, 145), "crew": (100, 145, 230), "cargo": (240, 170, 45),
    "damage": (255, 75, 25), "engineering": (255, 105, 30), "reactor": (255, 45, 20),
    "escape": (255, 205, 55), "armory": (230, 120, 35),
}
# priority, kW, occupancy, hazard, loot, access, jump-critical
PROFILES = {
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

# One authored interaction per room. These are the same native activity classes used by the
# procedural ship builder, so they launch the existing player activity/minigame component and
# persist stable station identity instead of behaving like decorative console props.
ROOM_ACTIVITY_CLASSES = {
    "OPS-08-01": "MechanicalOverrideStation",
    "BRG-08-01": "SensorCalibrationStation",
    "CIC-08-01": "TurretServiceStation",
    "NAV-08-01": "SensorCalibrationStation",
    "COM-08-01": "BreakerReroutingStation",
    "SNS-08-01": "BloomPurgingStation",
    "ARM-08-01": "TurretServiceStation",
    "CMP-08-01": "MechanicalOverrideStation",
    "CRW-07-01": "SuitPatchingStation",
    "CCM-07-01": "BreakerReroutingStation",
    "GAL-07-01": "FireSuppressionStation",
    "REC-07-01": "ComponentReplacementStation",
    "MED-07-01": "MedicalStabilizationStation",
    "SUR-07-01": "MedicalStabilizationStation",
    "QRT-07-01": "DecontaminationStation",
    "CRY-07-01": "SampleContainmentStation",
    "DCR-06-01": "HullPatchingStation",
    "FAB-06-01": "FabricationStation",
    "LIF-06-01": "OxygenScrubberServiceStation",
    "WTR-06-01": "PipeSealingStation",
    "CGO-06-01": "DroneRepairStation",
    "EVA-06-01": "AirlockRepressurizationStation",
    "ENG-06-01": "CoolantBalancingStation",
    "AUX-06-01": "ReactorStartupStation",
}

# Deliberately sparse survival supplies: they reward exploration without turning every work bay
# into a pickup shelf. Type names match EPickupType's reflected Python enum.
ROOM_SURVIVAL_PICKUPS = {
    "MED-07-01": ("HEALTH", 35.0),
    "SUR-07-01": ("HEALTH", 25.0),
    "LIF-06-01": ("OXYGEN", 30.0),
    "EVA-06-01": ("OXYGEN", 30.0),
}
ROOM_CHECKPOINTS = {
    "OPS-08-01": "EscortOps_Deck08_Entry",
    "CCM-07-01": "EscortOps_Deck07_CrewCommons",
    "DCR-06-01": "EscortOps_Deck06_DamageControl",
}
# Curated imported Fab dressing. Transforms are explicit because vendor packs use different source
# scales and pivot conventions. Offsets are relative to room center, with Z measured from the deck.
PROP_SPECS = {
    "companionway": (
        {"path": "/Game/Ice_Station/Meshes/Walls/SM_module_01_interior", "offset": (-520.0, -640.0, 20.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.65, 0.35, 0.75)},
        {"path": "/Game/Ice_Station/Meshes/Crates/SM_crate_01", "offset": (420.0, 480.0, 22.0), "rotation": (0.0, 20.0, 0.0), "scale": (0.72, 0.72, 0.72)},
        {"path": "/Game/Ice_Station/Meshes/Crates/SM_crate_04", "offset": (240.0, 500.0, 22.0), "rotation": (0.0, -10.0, 0.0), "scale": (0.70, 0.70, 0.70)},
        {"path": "/Game/Ice_Station/Meshes/Chair/SM_chair", "offset": (-360.0, 470.0, 22.0), "rotation": (0.0, 25.0, 0.0), "scale": (0.72, 0.72, 0.72)},
        {"path": "/Game/Ice_Station/Meshes/Table/SM_bench", "offset": (-250.0, -500.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.52, 0.52, 0.52)},
        {"path": "/Game/Ice_Station/Meshes/Computer/SM_top_computer", "offset": (360.0, -500.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.48, 0.48, 0.48)},
    ),
    "bridge": (
        {"path": "/Game/Ice_Station/Meshes/Table/SM_Table", "offset": (0.0, -470.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.50, 0.50, 0.50)},
        {"path": "/Game/Ice_Station/Meshes/Computer/SM_computer_01", "offset": (-390.0, 480.0, 22.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.66, 0.66, 0.66)},
        {"path": "/Game/Ice_Station/Meshes/Computer/SM_computer_02", "offset": (390.0, 480.0, 22.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.66, 0.66, 0.66)},
        {"path": "/Game/Ice_Station/Meshes/Chair/SM_chair", "offset": (0.0, -360.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.72, 0.72, 0.72)},
        {"path": "/Game/Ice_Station/Meshes/Computer/SM_top_computer", "offset": (0.0, 500.0, 22.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.52, 0.52, 0.52)},
        {"path": "/Game/Ice_Station/Meshes/Chair/SM_chair", "offset": (300.0, -360.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.68, 0.68, 0.68)},
    ),
    "sensors": (
        {"path": "/Game/Ice_Station/Meshes/Computer/SM_computer_01", "offset": (-390.0, -490.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.64, 0.64, 0.64)},
        {"path": "/Game/Ice_Station/Meshes/Computer/SM_computer_02", "offset": (390.0, -490.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.64, 0.64, 0.64)},
        {"path": "/Game/Ice_Station/Meshes/Computer/SM_computer_circular", "offset": (-300.0, 470.0, 22.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.13, 0.13, 0.13)},
        {"path": "/Game/Ice_Station/Meshes/Computer/SM_top_computer", "offset": (390.0, 490.0, 22.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.66, 0.66, 0.66)},
        {"path": "/Game/Ice_Station/Meshes/Chair/SM_chair", "offset": (-40.0, -360.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.68, 0.68, 0.68)},
        {"path": "/Game/Ice_Station/Meshes/Computer/Sm_circular_computer_02", "offset": (40.0, 500.0, 22.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.13, 0.13, 0.13)},
    ),
    "medical": (
        {"path": "/Game/Ice_Station/Meshes/Bed/SM_bed_01", "offset": (-380.0, 535.0, 185.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.18, 0.18, 0.18)},
        {"path": "/Game/Ice_Station/Meshes/Bed/SM_bed_02", "offset": (380.0, 535.0, 185.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.18, 0.18, 0.18)},
        {"path": "/Game/Ice_Station/Meshes/Table/SM_Table", "offset": (-300.0, 480.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.42, 0.42, 0.42)},
        {"path": "/Game/Ice_Station/Meshes/Chair/SM_chair", "offset": (350.0, 480.0, 22.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.72, 0.72, 0.72)},
        {"path": "/Game/Ice_Station/Meshes/Crates/SM_crate_01", "offset": (-360.0, -500.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.58, 0.58, 0.58)},
        {"path": "/Game/Ice_Station/Meshes/Table/SM_bench", "offset": (330.0, -500.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.48, 0.48, 0.48)},
    ),
    "crew": (
        {"path": "/Game/Ice_Station/Meshes/Bed/SM_bed_01", "offset": (-350.0, 535.0, 185.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.18, 0.18, 0.18)},
        {"path": "/Game/Ice_Station/Meshes/Bed/SM_bed_02", "offset": (350.0, 535.0, 185.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.18, 0.18, 0.18)},
        {"path": "/Game/Ice_Station/Meshes/Table/SM_Table", "offset": (-260.0, 480.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.42, 0.42, 0.42)},
        {"path": "/Game/Ice_Station/Meshes/Chair/SM_chair", "offset": (340.0, 480.0, 22.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.72, 0.72, 0.72)},
        {"path": "/Game/Ice_Station/Meshes/Table/SM_bench", "offset": (-320.0, -500.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.48, 0.48, 0.48)},
        {"path": "/Game/Ice_Station/Meshes/Chair/SM_chair", "offset": (320.0, -360.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.68, 0.68, 0.68)},
    ),
    "cargo": (
        {"path": "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Container/SM_container_blue", "offset": (-360.0, -500.0, 22.0), "rotation": (0.0, 90.0, 0.0), "scale": (0.22, 0.22, 0.22)},
        {"path": "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Container/SM_container_orange", "offset": (360.0, -500.0, 22.0), "rotation": (0.0, -90.0, 0.0), "scale": (0.22, 0.22, 0.22)},
        {"path": "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Container/SM_container_red", "offset": (-360.0, 500.0, 22.0), "rotation": (0.0, 90.0, 0.0), "scale": (0.20, 0.20, 0.20)},
        {"path": "/Game/Ice_Station/Meshes/Crates/SM_large_crate_01", "offset": (360.0, 500.0, 24.0), "rotation": (0.0, -10.0, 0.0), "scale": (0.28, 0.28, 0.28)},
        {"path": "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Container/SM_container_white", "offset": (0.0, 510.0, 22.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.18, 0.18, 0.18)},
        {"path": "/Game/Ice_Station/Meshes/Crates/SM_crate_04", "offset": (0.0, -500.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.62, 0.62, 0.62)},
    ),
    "damage": (
        {"path": "/Game/Ice_Station/Meshes/Table/SM_Table", "offset": (-300.0, -480.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.48, 0.48, 0.48)},
        {"path": "/Game/Ice_Station/Meshes/Crates/SM_large_crate_01", "offset": (350.0, -480.0, 24.0), "rotation": (0.0, 15.0, 0.0), "scale": (0.30, 0.30, 0.30)},
        {"path": "/Game/Ice_Station/Meshes/Crates/SM_crate_01", "offset": (-360.0, 490.0, 22.0), "rotation": (0.0, -15.0, 0.0), "scale": (0.72, 0.72, 0.72)},
        {"path": "/Game/Ice_Station/Meshes/Pipe/SM_pipe_group_01", "offset": (330.0, 470.0, 24.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.13, 0.13, 0.13)},
        {"path": "/Game/Ice_Station/Meshes/Chair/SM_chair", "offset": (20.0, -360.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.68, 0.68, 0.68)},
        {"path": "/Game/Ice_Station/Meshes/Computer/SM_top_computer", "offset": (20.0, 500.0, 22.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.48, 0.48, 0.48)},
    ),
    "engineering": (
        {"path": "/Game/Ice_Station/Meshes/interior/SM_generator", "offset": (-350.0, -480.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.28, 0.28, 0.28)},
        {"path": "/Game/Ice_Station/Meshes/Pipe/SM_pipe_group_02", "offset": (350.0, -480.0, 24.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.13, 0.13, 0.13)},
        {"path": "/Game/Ice_Station/Meshes/Pipe/SM_pipe_group_01", "offset": (-350.0, 480.0, 24.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.13, 0.13, 0.13)},
        {"path": "/Game/Ice_Station/Meshes/Computer/SM_top_computer", "offset": (390.0, 490.0, 22.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.64, 0.64, 0.64)},
        {"path": "/Game/Ice_Station/Meshes/Table/SM_Table", "offset": (-300.0, 500.0, 22.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.38, 0.38, 0.38)},
        {"path": "/Game/Ice_Station/Meshes/Chair/SM_chair", "offset": (300.0, 360.0, 22.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.68, 0.68, 0.68)},
    ),
    "reactor": (
        {"path": "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Reactor/SM_small_reactor", "offset": (-300.0, -470.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.11, 0.11, 0.11)},
        {"path": "/Game/Ice_Station/Meshes/interior/SM_generator", "offset": (390.0, -470.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.23, 0.23, 0.23)},
        {"path": "/Game/Ice_Station/Meshes/Pipe/SM_pipe_group_01", "offset": (-340.0, 480.0, 24.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.12, 0.12, 0.12)},
        {"path": "/Game/Ice_Station/Meshes/Computer/SM_computer_02", "offset": (390.0, 490.0, 22.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.62, 0.62, 0.62)},
        {"path": "/Game/Ice_Station/Meshes/Computer/SM_top_computer", "offset": (0.0, 500.0, 22.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.46, 0.46, 0.46)},
        {"path": "/Game/Ice_Station/Meshes/Chair/SM_chair", "offset": (0.0, -360.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.68, 0.68, 0.68)},
    ),
    "escape": (
        {"path": "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Container/SM_container_red", "offset": (-360.0, -500.0, 22.0), "rotation": (0.0, 90.0, 0.0), "scale": (0.20, 0.20, 0.20)},
        {"path": "/Game/Ice_Station/Meshes/Crates/SM_crate_04", "offset": (370.0, -500.0, 22.0), "rotation": (0.0, -15.0, 0.0), "scale": (0.72, 0.72, 0.72)},
        {"path": "/Game/Ice_Station/Meshes/Table/SM_Table", "offset": (-300.0, 480.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.40, 0.40, 0.40)},
        {"path": "/Game/Ice_Station/Meshes/Chair/SM_chair", "offset": (350.0, 480.0, 22.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.72, 0.72, 0.72)},
        {"path": "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Container/SM_container_white", "offset": (0.0, -500.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.16, 0.16, 0.16)},
        {"path": "/Game/Ice_Station/Meshes/Table/SM_bench", "offset": (0.0, 500.0, 22.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.48, 0.48, 0.48)},
    ),
    "armory": (
        {"path": "/Game/Ice_Station/Meshes/Crates/SM_crate_04", "offset": (-380.0, -500.0, 22.0), "rotation": (0.0, 15.0, 0.0), "scale": (0.72, 0.72, 0.72)},
        {"path": "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Container/SM_container_red", "offset": (350.0, -500.0, 22.0), "rotation": (0.0, -90.0, 0.0), "scale": (0.18, 0.18, 0.18)},
        {"path": "/Game/Ice_Station/Meshes/Crates/SM_crate_01", "offset": (-360.0, 500.0, 22.0), "rotation": (0.0, -15.0, 0.0), "scale": (0.72, 0.72, 0.72)},
        {"path": "/Game/Ice_Station/Meshes/Crates/SM_large_crate_01", "offset": (350.0, 490.0, 24.0), "rotation": (0.0, 10.0, 0.0), "scale": (0.27, 0.27, 0.27)},
        {"path": "/Game/Ice_Station/Meshes/Crates/SM_crate_01_group", "offset": (0.0, -500.0, 22.0), "rotation": (0.0, 0.0, 0.0), "scale": (0.38, 0.38, 0.38)},
        {"path": "/Game/Ice_Station/Meshes/Crates/SM_crate_02_group", "offset": (0.0, 500.0, 22.0), "rotation": (0.0, 180.0, 0.0), "scale": (0.38, 0.38, 0.38)},
    ),
}


def enum_value(enum_type, name):
    try:
        return getattr(enum_type, name)
    except AttributeError as exc:
        raise RuntimeError(f"Missing {enum_type.__name__}.{name}; rebuild the editor target") from exc


def load_required(path):
    asset = unreal.load_asset(path)
    if not asset:
        raise RuntimeError("Missing required interior asset: " + path)
    return asset


def load_optional(path):
    asset = unreal.load_asset(path)
    if not asset:
        unreal.log_warning("Optional room dressing is unavailable: " + path)
    return asset


def room_location(spec):
    height = room_size(spec)[2]
    return (
        GRID_X[spec["grid"][0]],
        GRID_Y[spec["grid"][1]],
        DECK_FLOOR_Z[spec["deck"]] + height * 0.5,
    )


def room_floor_z(spec):
    return DECK_FLOOR_Z[spec["deck"]]


def room_size(spec):
    """Return this room's authored full X/Y/Z dimensions in centimeters."""
    return tuple(float(value) for value in spec.get("size_cm", DEFAULT_ROOM_SIZE))


def room_scale(spec):
    size = room_size(spec)
    return tuple(size[index] / DEFAULT_ROOM_SIZE[index] for index in range(3))


def district_envelope(room_specs):
    bounds = []
    for spec in room_specs:
        location = room_location(spec)
        size = room_size(spec)
        bounds.append(tuple((location[index] - size[index] * 0.5,
                             location[index] + size[index] * 0.5) for index in range(3)))
    minimum = tuple(min(item[index][0] for item in bounds) for index in range(3))
    maximum = tuple(max(item[index][1] for item in bounds) for index in range(3))
    center = tuple((minimum[index] + maximum[index]) * 0.5 for index in range(3))
    size = tuple(maximum[index] - minimum[index] for index in range(3))
    return center, size


def make_connections(rooms, district):
    by_deck_lane = defaultdict(list)
    for spec in rooms:
        by_deck_lane[(spec["deck"], spec["grid"][1])].append(spec)

    links = []
    for lane in by_deck_lane.values():
        lane.sort(key=lambda item: item["grid"][0])
        for left, right in zip(lane, lane[1:]):
            links.append((left["code"], "FORWARD", right["code"], "AFT", 1.0, "horizontal"))
    for a, b in district["crosslinks"]:
        links.append((a, "STARBOARD", b, "PORT", 0.9, "horizontal"))
    for lower, upper in district["vertical_links"]:
        links.append((lower, "UP", upper, "DOWN", 0.75, "vertical"))
    return links


def validate_plan(payload):
    districts = payload["streamed_districts"]
    target = payload["explorable_room_target"]
    if sum(item["room_target"] for item in districts) != target:
        raise RuntimeError("Ship district room targets do not sum to the explorable-room target")

    district = payload["first_district"]
    if tuple(float(value) for value in district.get("corridor_size_cm", ())) != CORRIDOR_SIZE:
        raise RuntimeError(f"Operations district corridor_size_cm must be {CORRIDOR_SIZE}")
    if district.get("bulkheads_per_horizontal_link") != 2:
        raise RuntimeError("Every horizontal room link requires a bulkhead at both corridor thresholds")
    room_policy = district.get("hardpoint_policy", {}).get("rooms", {})
    corridor_policy = district.get("hardpoint_policy", {}).get("corridors", {})
    for kind in ("body", "obstacle", "bloom_growth", "activity", "damage_repair"):
        if room_policy.get(kind, 0) < 1:
            raise RuntimeError(f"Room hardpoint policy requires at least one {kind} location")
    for kind in ("doorway", "body", "obstacle", "bloom_growth", "activity", "damage_repair"):
        if corridor_policy.get(kind, 0) < 1:
            raise RuntimeError(f"Corridor hardpoint policy requires at least one {kind} location")
    rooms = district["rooms"]
    placement_errors = validate_room_placements(
        rooms, district.get("room_type_catalog", ()), district.get("room_placement_policy", {})
    )
    if placement_errors:
        raise RuntimeError("Invalid room placement identities/rules:\n" + "\n".join(placement_errors))
    if len(rooms) != 24:
        raise RuntimeError(f"Operations district requires 24 rooms, found {len(rooms)}")
    codes = [room["code"] for room in rooms]
    if len(codes) != len(set(codes)):
        raise RuntimeError("Operations district contains duplicate room codes")
    cells = [(room["deck"], *room["grid"]) for room in rooms]
    if len(cells) != len(set(cells)):
        raise RuntimeError("Operations district contains overlapping room cells")
    for room in rooms:
        if room["archetype"] not in ARCHETYPES or room["section"] not in SECTIONS:
            raise RuntimeError("Unknown room classification: " + room["code"])
        if room["deck"] not in DECK_Z or room["grid"][0] not in range(4) or room["grid"][1] not in range(2):
            raise RuntimeError("Room is outside the supported three-deck grid: " + room["code"])
        size = room_size(room)
        limits = district.get("room_size_limits_cm", {})
        minimum = tuple(float(value) for value in limits.get("minimum", (1200.0, 1100.0, 400.0)))
        maximum = tuple(float(value) for value in limits.get("maximum", (1800.0, 1600.0, 460.0)))
        if len(size) != 3 or any(size[index] < minimum[index] or size[index] > maximum[index]
                                 for index in range(3)):
            raise RuntimeError(
                f"Room {room['code']} size {size} is outside supported limits {minimum}..{maximum}"
            )

    links = make_connections(rooms, district)
    sockets = set()
    graph = defaultdict(set)
    for a, socket_a, b, socket_b, _, _ in links:
        if a not in codes or b not in codes or a == b:
            raise RuntimeError(f"Invalid connection {a} -> {b}")
        for endpoint in ((a, socket_a), (b, socket_b)):
            if endpoint in sockets:
                raise RuntimeError(f"Socket assigned more than once: {endpoint[0]}.{endpoint[1]}")
            sockets.add(endpoint)
        graph[a].add(b); graph[b].add(a)
        if socket_a not in ("UP", "DOWN"):
            start, _ = portal_location(next(room for room in rooms if room["code"] == a), socket_a)
            end, _ = portal_location(next(room for room in rooms if room["code"] == b), socket_b)
            corridor_length = math.hypot(end[0] - start[0], end[1] - start[1])
            if corridor_length < MIN_CORRIDOR_LENGTH:
                raise RuntimeError(
                    f"Room sizes leave only {corridor_length:.0f} cm for corridor {a} -> {b}; "
                    f"minimum is {MIN_CORRIDOR_LENGTH:.0f} cm"
                )
    visited = set()
    queue = deque([codes[0]])
    while queue:
        code = queue.popleft()
        if code in visited:
            continue
        visited.add(code); queue.extend(graph[code] - visited)
    if visited != set(codes):
        raise RuntimeError("Operations district graph is not fully reachable")
    return district, rooms, links


def spawn_box(actors, cube, material, location, size, label, rotation=(0.0, 0.0, 0.0)):
    pitch, yaw, roll = rotation
    actor_rotation = unreal.Rotator(pitch=pitch, yaw=yaw, roll=roll)
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), actor_rotation)
    actor.set_actor_label(PREFIX + label)
    actor.set_actor_scale3d(unreal.Vector(size[0] / 100.0, size[1] / 100.0, size[2] / 100.0))
    actor.static_mesh_component.set_static_mesh(cube)
    if material:
        actor.static_mesh_component.set_material(0, material)
    return actor


def spawn_mesh(actors, mesh, location, rotation, scale, label):
    if not mesh:
        return None
    pitch, yaw, roll = rotation
    actor_rotation = unreal.Rotator(pitch=pitch, yaw=yaw, roll=roll)
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), actor_rotation)
    actor.set_actor_label(PREFIX + label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_editor_property("tags", [unreal.Name("FabRoomDressing"), unreal.Name("SmallEscortOperations")])
    return actor


def configure_corridor_detail(actor, corridor_code, detail_kind):
    """Make concept dressing visual-only so hardpoint and traversal clearance stays authoritative."""
    if not actor:
        return None
    actor.set_editor_property(
        "tags",
        [unreal.Name("CorridorConceptDetail"), unreal.Name(corridor_code), unreal.Name(detail_kind)],
    )
    mesh_component = actor.get_component_by_class(unreal.StaticMeshComponent)
    if mesh_component:
        mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return actor


def corridor_rib_count(length):
    return max(1, int(math.ceil(length / 280.0)))


def spawn_aperture_slab(actors, cube, material, center, z, size, label):
    # A 1100 x 420 cm stair opening with walkable landings around it.
    cx, cy = center
    full_x, full_y = size[0], size[1]
    opening_x, opening_y = min(1100.0, full_x - 200.0), min(420.0, full_y - 400.0)
    side_y = (full_y - opening_y) * 0.5
    end_x = (full_x - opening_x) * 0.5
    spawn_box(actors, cube, material, (cx, cy - (opening_y + side_y) * 0.5, z),
              (full_x, side_y, 20.0), label + "_Port")
    spawn_box(actors, cube, material, (cx, cy + (opening_y + side_y) * 0.5, z),
              (full_x, side_y, 20.0), label + "_Starboard")
    spawn_box(actors, cube, material, (cx - (opening_x + end_x) * 0.5, cy, z),
              (end_x, opening_y, 20.0), label + "_Aft")
    spawn_box(actors, cube, material, (cx + (opening_x + end_x) * 0.5, cy, z),
              (end_x, opening_y, 20.0), label + "_Forward")


def boundary_key(spec, socket):
    x, y, z = room_location(spec)
    width, depth, height = room_size(spec)
    hx, hy = width * 0.5, depth * 0.5
    if socket == "FORWARD": return ("x", round(x + hx), round(y), round(z), depth, height)
    if socket == "AFT": return ("x", round(x - hx), round(y), round(z), depth, height)
    if socket == "STARBOARD": return ("y", round(x), round(y + hy), round(z), width, height)
    if socket == "PORT": return ("y", round(x), round(y - hy), round(z), width, height)
    raise ValueError(socket)


def spawn_wall(actors, cube, material, key, open_door, label):
    axis, a, b, z, span, wall_h = key
    floor_z = z - wall_h * 0.5
    wall_t, door_w, door_h = 30.0, 280.0, 285.0
    if axis == "x":
        center = (a, b, z); thickness = (wall_t, span, wall_h)
    else:
        center = (a, b, z); thickness = (span, wall_t, wall_h)
    if not open_door:
        spawn_box(actors, cube, material, center, thickness, label)
        return

    side = (span - door_w) * 0.5
    header_h = wall_h - door_h
    if axis == "x":
        spawn_box(actors, cube, material, (a, b - (door_w + side) * 0.5, z), (wall_t, side, wall_h), label + "_Left")
        spawn_box(actors, cube, material, (a, b + (door_w + side) * 0.5, z), (wall_t, side, wall_h), label + "_Right")
        spawn_box(actors, cube, material, (a, b, floor_z + door_h + header_h * 0.5), (wall_t, door_w, header_h), label + "_Header")
    else:
        spawn_box(actors, cube, material, (a - (door_w + side) * 0.5, b, z), (side, wall_t, wall_h), label + "_Left")
        spawn_box(actors, cube, material, (a + (door_w + side) * 0.5, b, z), (side, wall_t, wall_h), label + "_Right")
        spawn_box(actors, cube, material, (a, b, floor_z + door_h + header_h * 0.5), (door_w, wall_t, header_h), label + "_Header")


def make_section_connection(target, door, coefficient):
    value = unreal.SectionConnection()
    value.set_editor_property("target", target)
    value.set_editor_property("door", door)
    value.set_editor_property("transfer_coefficient", coefficient)
    return value


def make_gameplay_hardpoint(section_code, index, kind, location, rotation=(0.0, 0.0, 0.0),
                            clearance=100.0, context=""):
    value = unreal.ShipGameplayHardpoint()
    value.set_editor_property("hardpoint_id", unreal.Name(f"{section_code}-HP-{index:02d}"))
    value.set_editor_property(
        "hardpoint_type", enum_value(unreal.ShipGameplayHardpointType, kind)
    )
    value.set_editor_property("relative_location", unreal.Vector(*location))
    value.set_editor_property(
        "relative_rotation", unreal.Rotator(pitch=rotation[0], yaw=rotation[1], roll=rotation[2])
    )
    value.set_editor_property("clearance_radius", clearance)
    value.set_editor_property("context_tag", unreal.Name(context))
    return value


def room_gameplay_hardpoints(spec, sockets):
    code = spec["code"]
    width, depth, height = room_size(spec)
    scale_x, scale_y, _ = room_scale(spec)
    floor_z = -height * 0.5 + 24.0
    raw = [
        ("BODY", (-250.0 * scale_x, -120.0 * scale_y, floor_z), (0.0, 25.0, 0.0), 105.0, "NarrativeBody"),
        ("BODY", (230.0 * scale_x, 140.0 * scale_y, floor_z), (0.0, -35.0, 0.0), 105.0, "NarrativeBody"),
        ("OBSTACLE", (-210.0 * scale_x, 390.0 * scale_y, floor_z), (0.0, 0.0, 0.0), 135.0, "MoveableBlocker"),
        ("OBSTACLE", (260.0 * scale_x, -390.0 * scale_y, floor_z), (0.0, 90.0, 0.0), 135.0, "MoveableBlocker"),
        ("BLOOM_GROWTH", (-510.0 * scale_x, 500.0 * scale_y, floor_z), (0.0, 0.0, 0.0), 115.0, "FloorGrowth"),
        ("BLOOM_GROWTH", (520.0 * scale_x, -500.0 * scale_y, floor_z), (0.0, 0.0, 0.0), 115.0, "FloorGrowth"),
        ("ACTIVITY", (-440.0 * scale_x, -depth * 0.416, floor_z + 95.0), (0.0, 90.0, 0.0), 100.0, "FloorMount"),
        ("ACTIVITY", (-440.0 * scale_x, depth * 0.416, floor_z + 95.0), (0.0, -90.0, 0.0), 100.0, "FloorMount"),
        ("ACTIVITY", (440.0 * scale_x, -depth * 0.463, floor_z + 175.0), (0.0, 90.0, 0.0), 85.0, "WallMount"),
        ("ACTIVITY", (440.0 * scale_x, depth * 0.463, floor_z + 175.0), (0.0, -90.0, 0.0), 85.0, "WallMount"),
        ("DAMAGE_REPAIR", (160.0 * scale_x, -depth * 0.464, floor_z + 170.0), (0.0, 90.0, 0.0), 90.0, "BulkheadRepair"),
        ("DAMAGE_REPAIR", (160.0 * scale_x, depth * 0.464, floor_z + 170.0), (0.0, -90.0, 0.0), 90.0, "BulkheadRepair"),
    ]
    doorway_locations = {
        "FORWARD": ((width * 0.5, 0.0, (CORRIDOR_SIZE[2] - height) * 0.5), (0.0, 0.0, 0.0)),
        "AFT": ((-width * 0.5, 0.0, (CORRIDOR_SIZE[2] - height) * 0.5), (0.0, 180.0, 0.0)),
        "STARBOARD": ((0.0, depth * 0.5, (CORRIDOR_SIZE[2] - height) * 0.5), (0.0, 90.0, 0.0)),
        "PORT": ((0.0, -depth * 0.5, (CORRIDOR_SIZE[2] - height) * 0.5), (0.0, -90.0, 0.0)),
        "UP": ((0.0, 0.0, height * 0.5), (-90.0, 0.0, 0.0)),
        "DOWN": ((0.0, 0.0, -height * 0.5), (90.0, 0.0, 0.0)),
    }
    for socket in sockets:
        location, rotation = doorway_locations[socket]
        raw.append(("DOORWAY", location, rotation, 145.0, socket))
    return [make_gameplay_hardpoint(code, index, *entry) for index, entry in enumerate(raw)]


def corridor_gameplay_hardpoints(code, length):
    floor_z = -CORRIDOR_SIZE[2] * 0.5 + 24.0
    raw = [
        ("DOORWAY", (-length * 0.5, 0.0, 0.0), (0.0, 180.0, 0.0), 145.0, "RoomThreshold"),
        ("DOORWAY", (length * 0.5, 0.0, 0.0), (0.0, 0.0, 0.0), 145.0, "RoomThreshold"),
        ("BODY", (-length * 0.18, -55.0, floor_z), (0.0, 15.0, 0.0), 95.0, "CorridorBody"),
        ("OBSTACLE", (length * 0.12, 35.0, floor_z), (0.0, 90.0, 0.0), 115.0, "PartialBlocker"),
        ("BLOOM_GROWTH", (0.0, -135.0, floor_z), (0.0, 0.0, 0.0), 90.0, "WallFloorGrowth"),
        ("ACTIVITY", (length * 0.24, 135.0, floor_z + 150.0), (0.0, -90.0, 0.0), 80.0, "WallMount"),
        ("DAMAGE_REPAIR", (-length * 0.24, -135.0, floor_z + 150.0), (0.0, 90.0, 0.0), 80.0, "UtilityRepair"),
    ]
    return [make_gameplay_hardpoint(code, index, *entry) for index, entry in enumerate(raw)]


def activity_class(name):
    value = getattr(unreal, name, None)
    if not value:
        raise RuntimeError(f"Missing native activity class unreal.{name}; rebuild the editor target")
    return value


def choose_gameplay_side(sockets):
    """Choose a wall bay that is not also a side-door approach."""
    names = set(sockets)
    if "PORT" in names and "STARBOARD" not in names:
        return 1.0, 0.0
    if "STARBOARD" in names and "PORT" not in names:
        return -1.0, 0.0
    # A rare room with both side sockets keeps the station clear of the centered door opening.
    if "PORT" in names and "STARBOARD" in names:
        return -1.0, 500.0
    return -1.0, 0.0


def add_room_gameplay(actors, room, spec, sockets, activity_mesh, pickup_meshes):
    x, y, z = room_location(spec)
    width, depth, height = room_size(spec)
    floor_z = z - height * 0.5
    side, _ = choose_gameplay_side(sockets)
    damage_repair_type = enum_value(unreal.ShipGameplayHardpointType, "DAMAGE_REPAIR")
    repair_slots = [
        item for item in room.get_editor_property("gameplay_hardpoints")
        if item.get_editor_property("hardpoint_type") == damage_repair_type
        and item.get_editor_property("relative_location").y * side > 0.0
    ]
    if not repair_slots:
        raise RuntimeError(f"Room {spec['code']} has no clear damage/activity repair hardpoint")
    activity_hardpoint = repair_slots[0]
    activity_local = activity_hardpoint.get_editor_property("relative_location")
    activity_rotation = activity_hardpoint.get_editor_property("relative_rotation")
    station_type = ROOM_ACTIVITY_CLASSES[spec["code"]]
    station = actors.spawn_actor_from_class(
        activity_class(station_type),
        unreal.Vector(x + activity_local.x, y + activity_local.y, z + activity_local.z),
        activity_rotation,
    )
    if not station:
        raise RuntimeError(f"Could not spawn {station_type} in {spec['code']}")
    station.set_actor_label(f"{PREFIX}Activity_{spec['code']}_{station_type}")
    station.set_editor_property("target_actor", room)
    station.set_editor_property("cooldown_seconds", 6.0)
    station.set_editor_property(
        "tags",
        [unreal.Name("GameplayActivity"), unreal.Name("DamageRepairHardpoint"),
         unreal.Name("RoomInteraction"), unreal.Name(spec["code"])],
    )
    station_mesh = station.get_editor_property("mesh")
    station_mesh.set_static_mesh(activity_mesh)
    station.set_actor_scale3d(unreal.Vector(0.82, 0.82, 0.82))
    station.configure_procedural_station(
        unreal.Name(f"{spec['code']}-ACT-00"),
        unreal.Name(spec["code"]),
        6100 + spec["deck"] * 100 + spec["grid"][0] * 10 + spec["grid"][1],
        0,
        enum_value(unreal.ActivityStationMount, "WALL_PANEL"),
        enum_value(unreal.ActivityStationCondition, "SERVICEABLE"),
        enum_value(unreal.ActivityStationRarity, "SPECIALIZED"),
        0.9,
        -1,
    )
    room.set_editor_property("maintenance_anchor", station)

    pickup_spec = ROOM_SURVIVAL_PICKUPS.get(spec["code"])
    if not pickup_spec:
        return station, None

    pickup_type_name, amount = pickup_spec
    pickup_side = -side
    pickup = actors.spawn_actor_from_class(
        unreal.SurvivalPickup,
        unreal.Vector(x + width * 0.32, y + pickup_side * depth * 0.357, floor_z + 48.0),
        unreal.Rotator(),
    )
    if not pickup:
        raise RuntimeError(f"Could not spawn survival pickup in {spec['code']}")
    pickup.set_actor_label(f"{PREFIX}Pickup_{spec['code']}_{pickup_type_name.title()}")
    pickup.set_editor_property("pickup_type", enum_value(unreal.PickupType, pickup_type_name))
    pickup.set_editor_property("amount", amount)
    pickup.set_editor_property(
        "tags", [unreal.Name("SurvivalSupply"), unreal.Name(pickup_type_name.title()), unreal.Name(spec["code"])],
    )
    pickup.get_editor_property("visual_mesh").set_static_mesh(pickup_meshes[pickup_type_name])
    pickup.set_actor_scale3d(unreal.Vector(0.32, 0.32, 0.32))
    room.set_editor_property("loot_anchor", pickup)
    return station, pickup


def spawn_room_checkpoint(actors, room, spec, checkpoint_id):
    x, y, z = room_location(spec)
    width, depth, height = room_size(spec)
    floor_z = z - height * 0.5
    checkpoint = actors.spawn_actor_from_class(
        unreal.ShipCheckpointVolume, unreal.Vector(x, y, floor_z + 90.0), unreal.Rotator()
    )
    if not checkpoint:
        raise RuntimeError(f"Could not spawn checkpoint in {spec['code']}")
    checkpoint.set_actor_label(f"{PREFIX}Checkpoint_{spec['code']}")
    checkpoint.set_editor_property("checkpoint_id", unreal.Name(checkpoint_id))
    checkpoint.set_editor_property("respawn_offset", unreal.Vector(260.0, 0.0, 0.0))
    checkpoint.set_editor_property(
        "tags", [unreal.Name("DeckCheckpoint"), unreal.Name("RespawnSafe"), unreal.Name(spec["code"])]
    )
    checkpoint.get_editor_property("trigger").set_box_extent(
        unreal.Vector(min(260.0, width * 0.18), min(260.0, depth * 0.18), 120.0)
    )
    return checkpoint


def add_room_presentation(actors, room, spec, props, cube, materials, sockets):
    x, y, z = room_location(spec)
    width, depth, height = room_size(spec)
    scale_x, scale_y, _ = room_scale(spec)
    half_x, half_y = width * 0.5, depth * 0.5
    floor_z = z - height * 0.5
    kind = spec["archetype"]
    color = unreal.Color(*COLORS[kind])
    socket_names = set(sockets)
    light = actors.spawn_actor_from_class(
        unreal.PointLight, unreal.Vector(x, y - depth * 0.357, z + 55.0), unreal.Rotator()
    )
    light.set_actor_label(f"{PREFIX}Light_{spec['code']}")
    component = light.get_component_by_class(unreal.PointLightComponent)
    component.set_editor_property("intensity", 240.0)
    component.set_editor_property("attenuation_radius", 520.0)
    component.set_editor_property("source_radius", 65.0)
    component.set_editor_property("light_color", color)
    component.set_editor_property("cast_shadows", False)

    for side_name, side in (("Port", -1.0), ("Starboard", 1.0)):
        work_light = actors.spawn_actor_from_class(
            unreal.PointLight, unreal.Vector(x, y + side * depth * 0.243, z + 45.0), unreal.Rotator()
        )
        work_light.set_actor_label(f"{PREFIX}WorkLight_{spec['code']}_{side_name}")
        work_component = work_light.get_component_by_class(unreal.PointLightComponent)
        work_component.set_editor_property("intensity", 600.0)
        work_component.set_editor_property("attenuation_radius", 720.0)
        work_component.set_editor_property("source_radius", 90.0)
        work_component.set_editor_property("light_color", unreal.Color(225, 235, 245))
        work_component.set_editor_property("cast_shadows", False)

        zone = spawn_box(
            actors, cube, materials["accent"], (x, y + side * (half_y - 200.0), floor_z + 22.0),
            (max(760.0, width - 440.0), 260.0, 4.0), f"WorkZone_{spec['code']}_{side_name}"
        )
        zone.set_editor_property(
            "tags", [unreal.Name("FunctionalZone"), unreal.Name(side_name + "WorkBay"), unreal.Name(spec["code"])]
        )
    for index, (dx, dy) in enumerate(((-half_x + 100.0, -half_y + 90.0),
                                      (half_x - 100.0, -half_y + 90.0),
                                      (-half_x + 100.0, half_y - 90.0),
                                      (half_x - 100.0, half_y - 90.0)), start=1):
        rib = spawn_box(
            actors, cube, materials["dark"], (x + dx, y + dy, floor_z + height * 0.5),
            (18.0, 18.0, max(330.0, height - 70.0)), f"Rib_{spec['code']}_{index}"
        )
        rib.set_editor_property("tags", [unreal.Name("InteriorStructure"), unreal.Name(spec["code"])])

    panel_material = materials["hull"] if kind in ("companionway", "medical", "crew", "escape") else materials["dark"]
    for side_name, side in (("Port", -1.0), ("Starboard", 1.0)):
        for segment_name, dx in (("Aft", -width * 0.26), ("Forward", width * 0.26)):
            panel = spawn_box(
                actors, cube, panel_material, (x + dx, y + side * (half_y - 38.0), floor_z + 190.0),
                (width / 3.0, 16.0, min(280.0, height - 140.0)),
                f"ArchPanel_{spec['code']}_{side_name}_{segment_name}"
            )
            panel.set_editor_property(
                "tags", [unreal.Name("ArchitecturalPanel"), unreal.Name(side_name + "WorkBay"), unreal.Name(spec["code"])]
            )
            post = spawn_box(
                actors, cube, materials["dark"],
                (x + dx + (width * 0.147 if dx < 0.0 else -width * 0.147),
                 y + side * (half_y - 50.0), floor_z + 190.0),
                (18.0, 24.0, min(320.0, height - 100.0)),
                f"BayPost_{spec['code']}_{side_name}_{segment_name}"
            )
            post.set_editor_property(
                "tags", [unreal.Name("WorkBayDivider"), unreal.Name(side_name + "WorkBay"), unreal.Name(spec["code"])]
            )
        trim = spawn_box(
            actors, cube, materials["accent"], (x, y + side * (half_y - 52.0), floor_z + height - 95.0),
            (max(780.0, width - 420.0), 12.0, 12.0), f"ArchTrim_{spec['code']}_{side_name}"
        )
        trim.set_editor_property(
            "tags", [unreal.Name("ArchitecturalTrim"), unreal.Name(side_name + "WorkBay"), unreal.Name(spec["code"])]
        )
        housing = spawn_box(
            actors, cube, materials["hull"],
            (x, y + side * depth * 0.279, floor_z + height - 36.0),
            (440.0 * scale_x, 130.0 * scale_y, 10.0), f"CeilingHousing_{spec['code']}_{side_name}"
        )
        housing.set_editor_property(
            "tags", [unreal.Name("CeilingFixture"), unreal.Name(side_name + "WorkBay"), unreal.Name(spec["code"])]
        )
        strip = spawn_box(
            actors, cube, materials["accent"],
            (x, y + side * depth * 0.279, floor_z + height - 43.0),
            (340.0 * scale_x, 42.0 * scale_y, 6.0), f"CeilingStrip_{spec['code']}_{side_name}"
        )
        strip.set_editor_property(
            "tags", [unreal.Name("CeilingLightStrip"), unreal.Name(side_name + "WorkBay"), unreal.Name(spec["code"])]
        )
    for end_name, end in (("Aft", -1.0), ("Forward", 1.0)):
        for segment_name, dy in (("Port", -depth * 0.279), ("Starboard", depth * 0.279)):
            end_panel = spawn_box(
                actors, cube, materials["hull"],
                (x + end * (half_x - 18.0), y + dy, floor_z + 190.0),
                (16.0, depth / 3.0, min(280.0, height - 140.0)),
                f"EndPanel_{spec['code']}_{end_name}_{segment_name}"
            )
            end_panel.set_editor_property(
                "tags", [unreal.Name("ArchitecturalPanel"), unreal.Name(end_name + "Bulkhead"), unreal.Name(spec["code"])]
            )
            end_post = spawn_box(
                actors, cube, materials["dark"],
                (x + end * (half_x - 30.0),
                 y + dy + (depth * 0.157 if dy < 0.0 else -depth * 0.157), floor_z + 190.0),
                (24.0, 18.0, min(320.0, height - 100.0)),
                f"EndPost_{spec['code']}_{end_name}_{segment_name}"
            )
            end_post.set_editor_property(
                "tags", [unreal.Name("BulkheadDivider"), unreal.Name(end_name + "Bulkhead"), unreal.Name(spec["code"])]
            )
        end_trim = spawn_box(
            actors, cube, materials["accent"],
            (x + end * (half_x - 32.0), y, floor_z + height - 95.0),
            (12.0, max(680.0, depth - 320.0), 12.0), f"EndTrim_{spec['code']}_{end_name}"
        )
        end_trim.set_editor_property(
            "tags", [unreal.Name("ArchitecturalTrim"), unreal.Name(end_name + "Bulkhead"), unreal.Name(spec["code"])]
        )

    signs = []
    for suffix, text, world_size, dz in (("Code", spec["code"], 28.0, 0.0), ("Name", spec["name"].upper(), 18.0, -42.0)):
        sign_rotation = unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0)
        sign = actors.spawn_actor_from_class(
            unreal.TextRenderActor,
            unreal.Vector(x - min(480.0, half_x - 120.0), y - half_y + 35.0, z + 90.0 + dz),
            sign_rotation,
        )
        sign.set_actor_label(f"{PREFIX}Sign_{spec['code']}_{suffix}")
        text_component = sign.get_component_by_class(unreal.TextRenderComponent)
        text_component.set_editor_property("text", text)
        text_component.set_editor_property("world_size", world_size)
        text_component.set_editor_property("text_render_color", color if suffix == "Code" else unreal.Color(205, 220, 225))
        signs.append(sign)

    anchors = []
    for index, anchor_kind in enumerate(("System", "Loot", "Maintenance")):
        anchor = actors.spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(x - 320.0 + index * 320.0, y, floor_z + 35.0), unreal.Rotator())
        anchor.set_actor_label(f"{PREFIX}Anchor_{spec['code']}_{anchor_kind}")
        anchor.set_editor_property("tags", [unreal.Name("RoomAnchor"), unreal.Name(anchor_kind + "Anchor"), unreal.Name(spec["code"])])
        anchors.append(anchor)

    suffixes = ("Primary", "Secondary", "Tertiary", "Quaternary", "Quinary", "Senary")
    for suffix, (mesh, placement) in zip(suffixes, props[kind]):
        dx, dy, dz = placement["offset"]
        dx *= scale_x
        dy *= scale_y
        side_socket = "STARBOARD" if dy > 0.0 else "PORT"
        if side_socket in socket_names:
            if abs(dx) < 80.0:
                dy = -dy
                dx = min(600.0 * scale_x, half_x - 150.0)
            elif abs(dx) < 340.0:
                dx = min(520.0 * scale_x, half_x - 150.0) * (1.0 if dx > 0.0 else -1.0)
        prop_actor = spawn_mesh(
            actors,
            mesh,
            (x + dx, y + dy, floor_z + dz),
            placement["rotation"],
            placement["scale"],
            f"Prop_{spec['code']}_{suffix}",
        )
        final_side_socket = "STARBOARD" if dy > 0.0 else "PORT"
        if prop_actor and final_side_socket in socket_names:
            origin, extent = prop_actor.get_actor_bounds(False)
            x_offset = origin.x - x
            clearance = abs(x_offset) - extent.x
            if clearance < 190.0:
                direction = 1.0 if x_offset >= 0.0 else -1.0
                correction = direction * (190.0 - clearance)
                prop_actor.add_actor_world_offset(unreal.Vector(correction, 0.0, 0.0), False, False)

    room.set_editor_property("identity_light", light)
    room.set_editor_property("code_sign", signs[0])
    room.set_editor_property("name_sign", signs[1])
    room.set_editor_property("system_anchor", anchors[0])
    room.set_editor_property("loot_anchor", anchors[1])
    room.set_editor_property("maintenance_anchor", anchors[2])


def portal_location(spec, socket):
    x, y, _ = room_location(spec)
    width, depth, _ = room_size(spec)
    portal_z = room_floor_z(spec) + CORRIDOR_SIZE[2] * 0.5
    if socket == "FORWARD": return (x + width * 0.5, y, portal_z), "x"
    if socket == "AFT": return (x - width * 0.5, y, portal_z), "x"
    if socket == "STARBOARD": return (x, y + depth * 0.5, portal_z), "y"
    if socket == "PORT": return (x, y - depth * 0.5, portal_z), "y"
    raise ValueError(socket)


def spawn_corridor(actors, cube, materials, corridor_meshes,
                   spec_a, socket_a, spec_b, socket_b, index):
    start, _ = portal_location(spec_a, socket_a)
    end, _ = portal_location(spec_b, socket_b)
    dx, dy = end[0] - start[0], end[1] - start[1]
    length = math.hypot(dx, dy)
    if length < 10.0 or abs(start[2] - end[2]) > 1.0:
        raise RuntimeError(f"Invalid horizontal corridor {spec_a['code']} -> {spec_b['code']}")
    if length < MIN_CORRIDOR_LENGTH:
        raise RuntimeError(
            f"Corridor {spec_a['code']} -> {spec_b['code']} is only {length:.0f} cm; "
            f"minimum is {MIN_CORRIDOR_LENGTH:.0f} cm"
        )

    code = f"COR-{spec_a['code']}-{spec_b['code']}"
    yaw = math.degrees(math.atan2(dy, dx))
    center = ((start[0] + end[0]) * 0.5, (start[1] + end[1]) * 0.5, start[2])
    rotation = unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0)
    corridor = actors.spawn_actor_from_class(unreal.ShipSection, unreal.Vector(*center), rotation)
    corridor.set_actor_label(f"{PREFIX}Corridor_{spec_a['code']}_{spec_b['code']}")
    corridor.set_editor_property("section_id", 1000 + index)
    corridor.set_editor_property("section_type", enum_value(unreal.ShipSectionType, "CORRIDOR"))
    corridor.set_editor_property(
        "tags", [unreal.Name("FittedShipCorridor"), unreal.Name("SmallEscortOperations"), unreal.Name(code)]
    )
    corridor.get_editor_property("section_bounds").set_box_extent(
        unreal.Vector(length * 0.5, CORRIDOR_SIZE[1] * 0.5, CORRIDOR_SIZE[2] * 0.5)
    )
    corridor.set_editor_property("gameplay_hardpoints", corridor_gameplay_hardpoints(code, length))

    floor_z = center[2] - CORRIDOR_SIZE[2] * 0.5 + 10.0
    ceiling_z = center[2] + CORRIDOR_SIZE[2] * 0.5 - 10.0
    rotation_tuple = (0.0, yaw, 0.0)
    spawn_box(actors, cube, materials["corridor_deck"], (center[0], center[1], floor_z),
              (length, CORRIDOR_SIZE[1], 20.0), f"CorridorFloor_{spec_a['code']}_{spec_b['code']}", rotation_tuple)
    spawn_box(actors, cube, materials["dark"], (center[0], center[1], ceiling_z),
              (length, CORRIDOR_SIZE[1], 20.0), f"CorridorCeiling_{spec_a['code']}_{spec_b['code']}", rotation_tuple)
    perpendicular = (-dy / length, dx / length)
    for side_name, side in (("Port", -1.0), ("Starboard", 1.0)):
        wall_center = (
            center[0] + perpendicular[0] * side * CORRIDOR_SIZE[1] * 0.5,
            center[1] + perpendicular[1] * side * CORRIDOR_SIZE[1] * 0.5,
            center[2],
        )
        wall = spawn_box(actors, cube, materials["corridor_wall"], wall_center,
                         (length, 30.0, CORRIDOR_SIZE[2]),
                         f"CorridorWall_{spec_a['code']}_{spec_b['code']}_{side_name}", rotation_tuple)
        wall.set_editor_property(
            "tags", [unreal.Name("CorridorShell"), unreal.Name(code), unreal.Name(side_name)]
        )

    # Concept-art pass: a dark tread, twin orange route lines, rib cadence, service rails,
    # exposed ceiling pipes, and a visible practical fixture. Every piece is visual-only;
    # the ShipSection bounds and gameplay hardpoints remain the navigation authority.
    forward = (dx / length, dy / length)

    def point(along, lateral, world_z):
        return (
            center[0] + forward[0] * along + perpendicular[0] * lateral,
            center[1] + forward[1] * along + perpendicular[1] * lateral,
            world_z,
        )

    detail_length = max(120.0, length - 36.0)
    floor_inset = spawn_box(
        actors, cube, materials["dark"], point(0.0, 0.0, floor_z + 12.0),
        (detail_length, 205.0, 4.0),
        f"ConceptCorridorFloorInset_{spec_a['code']}_{spec_b['code']}", rotation_tuple,
    )
    configure_corridor_detail(floor_inset, code, "FloorTread")
    for side_name, side in (("Port", -1.0), ("Starboard", 1.0)):
        stripe = spawn_box(
            actors, cube, materials["accent"], point(0.0, side * 112.0, floor_z + 15.0),
            (detail_length, 8.0, 6.0),
            f"ConceptCorridorFloorStripe_{spec_a['code']}_{spec_b['code']}_{side_name}",
            rotation_tuple,
        )
        configure_corridor_detail(stripe, code, "RouteStripe")
        kickplate = spawn_box(
            actors, cube, materials["dark"], point(0.0, side * 161.0, floor_z + 55.0),
            (detail_length, 8.0, 76.0),
            f"ConceptCorridorKickplate_{spec_a['code']}_{spec_b['code']}_{side_name}",
            rotation_tuple,
        )
        configure_corridor_detail(kickplate, code, "Kickplate")
        utility_rail = spawn_box(
            actors, cube, materials["accent"], point(0.0, side * 158.0, center[2] + 112.0),
            (detail_length, 10.0, 12.0),
            f"ConceptCorridorUtilityRail_{spec_a['code']}_{spec_b['code']}_{side_name}",
            rotation_tuple,
        )
        configure_corridor_detail(utility_rail, code, "UtilityRail")

        wall_panel = spawn_box(
            actors, cube, materials["corridor_hazard"], point(0.0, side * 160.0, center[2] + 18.0),
            (max(100.0, detail_length - 12.0), 7.0, 218.0),
            f"ConceptCorridorWallPanel_{spec_a['code']}_{spec_b['code']}_{side_name}",
            rotation_tuple,
        )
        configure_corridor_detail(wall_panel, code, "WallInset")
        access_along = side * min(length * 0.18, 90.0)
        access_panel = spawn_box(
            actors, cube, materials["hull"],
            point(access_along, side * 155.5, center[2] + 18.0),
            (min(108.0, detail_length * 0.34), 5.0, 104.0),
            f"ConceptCorridorAccessPanel_{spec_a['code']}_{spec_b['code']}_{side_name}",
            rotation_tuple,
        )
        configure_corridor_detail(access_panel, code, "AccessPanel")

        pipe = spawn_mesh(
            actors, corridor_meshes["pipe"],
            point(0.0, side * 96.0, ceiling_z - 48.0), rotation_tuple,
            (detail_length / 400.0, 1.0, 1.0),
            f"ConceptCorridorPipe_{spec_a['code']}_{spec_b['code']}_{side_name}",
        )
        pipe.static_mesh_component.set_material(0, materials["dark"])
        configure_corridor_detail(pipe, code, "CeilingService")

    rib_count = corridor_rib_count(length)
    for rib_index in range(rib_count):
        along = -length * 0.5 + (rib_index + 1) * length / (rib_count + 1)
        rib = spawn_mesh(
            actors, corridor_meshes["rib"], point(along, 0.0, floor_z + 10.0),
            (0.0, yaw + 90.0, 0.0),
            (CORRIDOR_SIZE[1] / 430.0, 0.72, CORRIDOR_SIZE[2] / 400.0),
            f"ConceptCorridorRib_{spec_a['code']}_{spec_b['code']}_{rib_index + 1:02d}",
        )
        rib.static_mesh_component.set_material(
            0, materials["accent"] if rib_index == 0 else materials["dark"]
        )
        configure_corridor_detail(rib, code, "PressureRib")

    fixture = spawn_mesh(
        actors, corridor_meshes["fixture"], point(0.0, 0.0, ceiling_z - 24.0),
        rotation_tuple, (0.78, 0.78, 0.78),
        f"ConceptCorridorLightFixture_{spec_a['code']}_{spec_b['code']}",
    )
    fixture.static_mesh_component.set_material(0, materials["light"])
    configure_corridor_detail(fixture, code, "UtilityLight")

    light = actors.spawn_actor_from_class(
        unreal.PointLight,
        unreal.Vector(center[0], center[1], center[2] + 95.0),
        unreal.Rotator(),
    )
    light.set_actor_label(f"{PREFIX}CorridorLight_{spec_a['code']}_{spec_b['code']}")
    light_component = light.get_component_by_class(unreal.PointLightComponent)
    light_component.set_editor_property("intensity", 310.0)
    light_component.set_editor_property("attenuation_radius", max(320.0, length * 0.78))
    light_component.set_editor_property("source_radius", 34.0)
    light_component.set_editor_property("light_color", unreal.Color(190, 215, 235))
    light_component.set_editor_property("cast_shadows", True)
    return corridor, start, end, code


def spawn_stair_ramp(actors, cube, deck_material, accent_material, lower_spec, upper_spec):
    x, y, lower_z = room_location(lower_spec)
    _, _, upper_z = room_location(upper_spec)
    lower_size = room_size(lower_spec)
    upper_size = room_size(upper_spec)
    lower_floor_top = lower_z - lower_size[2] * 0.5 + 20.0
    upper_floor_top = upper_z - upper_size[2] * 0.5 + 20.0
    rise = upper_floor_top - lower_floor_top
    run = min(1050.0, lower_size[0] - 250.0, upper_size[0] - 250.0)
    length = math.sqrt(run * run + rise * rise)
    pitch = -math.degrees(math.atan2(rise, run))
    mid_z = lower_floor_top + rise * 0.5
    ramp = spawn_box(actors, cube, deck_material, (x, y, mid_z), (length, 320.0, 24.0),
                     f"VerticalRamp_{lower_spec['code']}_{upper_spec['code']}", (pitch, 0.0, 0.0))
    ramp.set_editor_property("tags", [unreal.Name("VerticalTraversal"), unreal.Name(lower_spec["code"]), unreal.Name(upper_spec["code"])])
    for side in (-1.0, 1.0):
        spawn_box(actors, cube, accent_material, (x, y + side * 185.0, mid_z + 55.0),
                  (length, 18.0, 18.0), f"VerticalRail_{lower_spec['code']}_{upper_spec['code']}_{side:+.0f}", (pitch, 0.0, 0.0))
    guard_length = min(1100.0, upper_size[0] - 200.0)
    for side_name, side in (("Port", -1.0), ("Starboard", 1.0)):
        guard = spawn_box(
            actors, cube, accent_material, (x, y + side * 235.0, upper_floor_top + 108.0),
            (guard_length, 14.0, 14.0),
            f"StairGuardRail_{lower_spec['code']}_{upper_spec['code']}_{side_name}",
        )
        guard.set_editor_property(
            "tags", [unreal.Name("VerticalSafety"), unreal.Name(lower_spec["code"]), unreal.Name(upper_spec["code"])]
        )
        for end_name, end in (("Aft", -1.0), ("Forward", 1.0)):
            post = spawn_box(
                actors, cube, deck_material,
                (x + end * (guard_length * 0.5 - 15.0), y + side * 235.0, upper_floor_top + 65.0),
                (18.0, 18.0, 130.0),
                f"StairGuardPost_{lower_spec['code']}_{upper_spec['code']}_{side_name}_{end_name}",
            )
            post.set_editor_property(
                "tags", [unreal.Name("VerticalSafety"), unreal.Name(lower_spec["code"]), unreal.Name(upper_spec["code"])]
            )


def build_level(district, room_specs, links):
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        if not levels.load_level(MAP_PATH):
            raise RuntimeError("Could not load operations district")
        generated = [actor for actor in actors.get_all_level_actors() if actor.get_actor_label().startswith(PREFIX)]
        if generated:
            actors.destroy_actors(generated)
    elif not levels.new_level(MAP_PATH):
        raise RuntimeError("Could not create operations district")

    cube = load_required("/Engine/BasicShapes/Cube.Cube")
    materials = {
        "hull": load_required("/Game/Assets/Ships/Production/Materials/M_Ship_Hull_OffWhite"),
        "deck": load_required("/Game/Assets/Ships/Production/Materials/M_Ship_Deck_NonSlip"),
        "dark": load_required("/Game/Assets/Ships/Production/Materials/M_Ship_Structure_Gunmetal"),
        "accent": load_required("/Game/Assets/Ships/Production/Materials/M_Ship_Accent_Utility"),
        "light": load_required("/Game/Assets/Ships/Production/Materials/M_Ship_Light_Cold"),
        "corridor_wall": load_required(
            "/Game/Assets/Ships/Production/Materials/M_QuickDemo_BulkheadLargePanel"
        ),
        "corridor_deck": load_required("/Game/Assets/Materials/M_ShipDeck_NonSlip"),
        "corridor_hazard": load_required("/Game/Assets/Materials/M_ShipUtility_Hazard"),
    }
    corridor_meshes = {
        "rib": load_required("/Game/Assets/Ships/Production/Meshes/SM_Kit_StructuralRib"),
        "pipe": load_required("/Game/Assets/Ships/Production/Meshes/SM_Prop_PipeStraight"),
        "fixture": load_required("/Game/Assets/Ships/Production/Meshes/SM_Prop_LightFixture"),
    }
    props = {
        kind: tuple((load_required(placement["path"]), placement) for placement in placements)
        for kind, placements in PROP_SPECS.items()
    }
    activity_mesh = load_required("/Game/Assets/Ships/Production/Meshes/SM_Prop_WallTerminal")
    population_assets = {
        "body": load_required("/Game/DeadBodies_Poses_nikoff/Demo/Mannequins/Meshes/SKM_Manny_Simple"),
        "obstacle": load_required("/Game/Ice_Station/Meshes/Crates/SM_crate_02_group"),
        "bloom": load_required(
            "/Game/Alien_Biomass/Meshes/Alien_organism/SM_alien_organism_13"
        ),
    }
    pickup_meshes = {
        "HEALTH": load_required("/Game/Ice_Station/Meshes/Crates/SM_crate_01"),
        "OXYGEN": load_required("/Game/Ice_Station/Meshes/Crates/SM_crate_04"),
    }
    bulkhead_asset = load_optional("/Game/Assets/Ships/Production/Blueprints/BP_Ship_ProductionBulkhead")
    bulkhead_class = bulkhead_asset.generated_class() if bulkhead_asset else unreal.BulkheadDoor
    objective_asset = load_required(
        "/Game/Assets/Ships/Production/Blueprints/Gameplay/BP_Ship_ObjectiveConsole"
    )

    specs = {spec["code"]: spec for spec in room_specs}
    type_catalog = type_catalog_by_id(district["room_type_catalog"])
    placement_policy = district["room_placement_policy"]
    envelope_center, envelope_size = district_envelope(room_specs)
    sockets_by_room = defaultdict(list)
    open_boundaries = set()
    for a, socket_a, b, socket_b, _, link_type in links:
        sockets_by_room[a].append(socket_a); sockets_by_room[b].append(socket_b)
        if link_type == "horizontal":
            open_boundaries.add(boundary_key(specs[a], socket_a))
            open_boundaries.add(boundary_key(specs[b], socket_b))

    vertical_up = {a for a, _, _, _, _, kind in links if kind == "vertical"}
    vertical_down = {b for _, _, b, _, _, kind in links if kind == "vertical"}
    rooms = {}
    for spec in room_specs:
        x, y, z = room_location(spec)
        size = room_size(spec)
        floor_z = z - size[2] * 0.5 + 10.0
        ceiling_z = z + size[2] * 0.5 - 10.0
        if spec["code"] in vertical_down:
            spawn_aperture_slab(
                actors, cube, materials["deck"], (x, y), floor_z, size, f"Floor_{spec['code']}"
            )
        else:
            spawn_box(actors, cube, materials["deck"], (x, y, floor_z),
                      (size[0], size[1], 20.0), f"Floor_{spec['code']}")
        if spec["code"] in vertical_up:
            spawn_aperture_slab(
                actors, cube, materials["dark"], (x, y), ceiling_z, size, f"Ceiling_{spec['code']}"
            )
        else:
            spawn_box(actors, cube, materials["dark"], (x, y, ceiling_z),
                      (size[0], size[1], 20.0), f"Ceiling_{spec['code']}")

        room = actors.spawn_actor_from_class(unreal.ModularShipRoom, unreal.Vector(x, y, z), unreal.Rotator())
        room.set_actor_label(f"{PREFIX}Room_{spec['code']}")
        room.set_editor_property("room_code", spec["code"])
        room.set_editor_property("display_name", spec["name"])
        room.set_editor_property("archetype", enum_value(unreal.ShipRoomArchetype, ARCHETYPES[spec["archetype"]]))
        room.set_editor_property("section_type", enum_value(unreal.ShipSectionType, SECTIONS[spec["section"]]))
        room.set_editor_property("module_size", unreal.Vector(*size))
        room.get_editor_property("section_bounds").set_box_extent(
            unreal.Vector(size[0] * 0.5, size[1] * 0.5, size[2] * 0.5)
        )
        room.set_editor_property("enabled_sockets", [enum_value(unreal.ShipRoomSocket, name) for name in sockets_by_room[spec["code"]]])
        room.set_editor_property("tags", [unreal.Name("FittedShipRoom"), unreal.Name("SmallEscortOperations"), unreal.Name(spec["code"])])
        type_rule = type_catalog[int(spec["room_type_id"])]
        room.configure_placement_identity(
            int(spec["room_id"]),
            int(spec["room_type_id"]),
            unreal.Name(spec["placement_section"]),
            int(type_rule.get(
                "same_type_min_grid_distance",
                placement_policy["default_same_type_min_grid_distance"],
            )),
            spec["placement_section"] in type_rule.get("allow_same_type_cluster_in_sections", ()),
        )
        profile_values = PROFILES[spec["archetype"]]
        profile = unreal.ShipRoomGameplayProfile()
        for prop, value in zip(("power_priority", "nominal_power_draw", "safe_occupancy", "hazard_tier", "loot_tier"), profile_values[:5]):
            profile.set_editor_property(prop, value)
        profile.set_editor_property("access_tier", enum_value(unreal.ShipRoomAccessTier, profile_values[5]))
        profile.set_editor_property("critical_for_jump", profile_values[6])
        room.set_editor_property("gameplay_profile", profile)
        room.set_editor_property(
            "gameplay_hardpoints", room_gameplay_hardpoints(spec, sockets_by_room[spec["code"]])
        )
        add_room_presentation(actors, room, spec, props, cube, materials, sockets_by_room[spec["code"]])
        add_room_gameplay(
            actors, room, spec, sockets_by_room[spec["code"]], activity_mesh, pickup_meshes
        )
        rooms[spec["code"]] = room

    seen_boundaries = set()
    for spec in room_specs:
        for socket in ("FORWARD", "AFT", "PORT", "STARBOARD"):
            key = boundary_key(spec, socket)
            if key in seen_boundaries:
                continue
            seen_boundaries.add(key)
            spawn_wall(actors, cube, materials["hull"], key, key in open_boundaries,
                       f"Wall_{spec['code']}_{socket}")

    doors = {}
    corridors = {}
    for link_index, (a, socket_a, b, socket_b, coefficient, link_type) in enumerate(links):
        if link_type == "horizontal":
            corridor, portal_a, portal_b, corridor_code = spawn_corridor(
                actors, cube, materials, corridor_meshes,
                specs[a], socket_a, specs[b], socket_b, link_index
            )
            corridors[(a, b)] = corridor
            door_pair = []
            for room_code, portal, socket, side_name in (
                (a, portal_a, socket_a, "A"), (b, portal_b, socket_b, "B")
            ):
                _, axis = portal_location(specs[room_code], socket)
                floor_z = room_floor_z(specs[room_code])
                rotation = unreal.Rotator(pitch=0.0, yaw=90.0 if axis == "x" else 0.0, roll=0.0)
                door = actors.spawn_actor_from_class(
                    bulkhead_class, unreal.Vector(portal[0], portal[1], floor_z), rotation
                )
                door.set_actor_label(f"{PREFIX}Bulkhead_{a}_{b}_{side_name}")
                door.set_editor_property(
                    "tags", [unreal.Name("RoomThresholdDoor"), unreal.Name(room_code), unreal.Name(corridor_code)]
                )
                door.configure_threshold_sides(rooms[room_code], corridor)
                door_pair.append(door)
            doors[(a, b)] = tuple(door_pair)
            if not rooms[a].connect_room(enum_value(unreal.ShipRoomSocket, socket_a),
                                         rooms[b], enum_value(unreal.ShipRoomSocket, socket_b)):
                raise RuntimeError(f"Could not reserve room connection {a}.{socket_a} -> {b}.{socket_b}")
        else:
            if not rooms[a].connect_room(enum_value(unreal.ShipRoomSocket, socket_a),
                                         rooms[b], enum_value(unreal.ShipRoomSocket, socket_b)):
                raise RuntimeError(f"Could not reserve vertical room connection {a}.{socket_a} -> {b}.{socket_b}")
            spawn_stair_ramp(actors, cube, materials["deck"], materials["accent"], specs[a], specs[b])
            doors[(a, b)] = (None, None)

    room_connections = defaultdict(list)
    corridor_connections = defaultdict(list)
    for a, _, b, _, coefficient, link_type in links:
        if link_type == "horizontal":
            corridor = corridors[(a, b)]
            door_a, door_b = doors[(a, b)]
            room_connections[a].append(make_section_connection(corridor, door_a, coefficient))
            corridor_connections[corridor].append(make_section_connection(rooms[a], door_a, coefficient))
            room_connections[b].append(make_section_connection(corridor, door_b, coefficient))
            corridor_connections[corridor].append(make_section_connection(rooms[b], door_b, coefficient))
        else:
            room_connections[a].append(make_section_connection(rooms[b], None, coefficient))
            room_connections[b].append(make_section_connection(rooms[a], None, coefficient))
    for code, room in rooms.items():
        room.set_editor_property("connections", room_connections[code])
    for corridor, connections in corridor_connections.items():
        corridor.set_editor_property("connections", connections)

    for room_code, checkpoint_id in ROOM_CHECKPOINTS.items():
        spawn_room_checkpoint(actors, rooms[room_code], specs[room_code], checkpoint_id)

    deployment_room = specs["OPS-08-01"]
    deploy_x, deploy_y, deploy_z = room_location(deployment_room)
    deploy_size = room_size(deployment_room)
    player = actors.spawn_actor_from_class(
        unreal.PlayerStart,
        unreal.Vector(deploy_x + 150.0, deploy_y, deploy_z - deploy_size[2] * 0.5 + 110.0),
        unreal.Rotator(),
    )
    player.set_actor_label(PREFIX + "PlayerStart")
    nav = actors.spawn_actor_from_class(
        unreal.NavMeshBoundsVolume, unreal.Vector(*envelope_center), unreal.Rotator()
    )
    nav.set_actor_label(PREFIX + "NavMeshBounds")
    nav.set_actor_scale3d(unreal.Vector(32.0, 18.0, 9.0))
    sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0.0, 0.0, 735.0), unreal.Rotator())
    sky.set_actor_label(PREFIX + "InteriorFill")
    sky.light_component.set_editor_property("intensity", 0.35)

    director = actors.spawn_actor_from_class(
        unreal.ShipDistrictGameplayDirector, unreal.Vector(*envelope_center), unreal.Rotator()
    )
    director.set_actor_label(PREFIX + "GameplayDirector")
    director.set_editor_property("district_scale", enum_value(unreal.ShipDistrictScale, "SMALL"))
    director.set_editor_property(
        "district_extent", unreal.Vector(*(value * 0.5 for value in envelope_size))
    )
    director.set_editor_property("primary_objective_id", "EscortOps_RestoreOperations")
    director.set_editor_property("primary_objective_title", "Restore the escort operations district")
    director.set_editor_property("objective_reward", 350)
    director.set_editor_property("encounter_count", 0)
    director.set_editor_property("oxygen_pickup_count", 0)
    director.set_editor_property("health_pickup_count", 0)
    director.set_editor_property("spawn_gameplay_on_begin_play", False)
    director.set_editor_property("spawn_demo_systems", False)
    director.set_editor_property(
        "tags", [unreal.Name("GameplayDirector"), unreal.Name("SmallEscortOperations")]
    )

    population = actors.spawn_actor_from_class(
        unreal.ShipHardpointPopulationDirector,
        unreal.Vector(0.0, 0.0, 735.0),
        unreal.Rotator(),
    )
    population.set_actor_label(PREFIX + "HardpointPopulationDirector")
    population.set_editor_property("population_seed", 81173)
    population.set_editor_property("body_count", 6)
    population.set_editor_property("obstacle_count", 10)
    population.set_editor_property("bloom_growth_count", 8)
    population.set_editor_property("body_mesh", population_assets["body"])
    population.set_editor_property("obstacle_mesh", population_assets["obstacle"])
    population.set_editor_property("bloom_growth_mesh", population_assets["bloom"])
    population.set_editor_property(
        "tags", [unreal.Name("HardpointPopulation"), unreal.Name("SmallEscortOperations")]
    )

    objective_spec = specs["DCR-06-01"]
    objective_x, objective_y, objective_z = room_location(objective_spec)
    objective_size = room_size(objective_spec)
    objective_floor = objective_z - objective_size[2] * 0.5
    objective = actors.spawn_actor_from_class(
        objective_asset.generated_class(),
        unreal.Vector(objective_x, objective_y + objective_size[1] * 0.429, objective_floor + 25.0),
        unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0),
    )
    objective.set_actor_label(PREFIX + "ObjectiveConsole_DCR-06-01")
    objective.set_editor_property("objective_id", "EscortOps_RestoreOperations")
    objective.set_editor_property("system_name", "Operations District Restoration Console")
    objective.set_editor_property(
        "tags", [unreal.Name("PrimaryObjective"), unreal.Name("RoomInteraction"), unreal.Name("DCR-06-01")]
    )
    rooms["DCR-06-01"].set_editor_property("system_anchor", objective)

    registration = actors.spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator())
    registration.set_actor_label(PREFIX + "ShipLocalRegistration")
    origin = district["ship_local_origin_cm"]
    registration.set_editor_property("tags", [unreal.Name("SmallUtilityEscort"), unreal.Name("StreamedInteriorDistrict"),
                                               unreal.Name(f"ShipLocalX={origin[0]}"), unreal.Name(f"ShipLocalY={origin[1]}"),
                                               unreal.Name(f"ShipLocalZ={origin[2]}")])

    levels.save_current_level()
    unreal.EditorAssetLibrary.save_directory("/Game/Assets/Maps/ShipProduction")
    generated = [actor for actor in actors.get_all_level_actors() if actor.get_actor_label().startswith(PREFIX)]
    return len(generated)


def main():
    if not CONFIG.exists():
        raise RuntimeError("Missing Small Utility Escort interior plan: " + str(CONFIG))
    payload = json.loads(CONFIG.read_text(encoding="utf-8"))
    district, rooms, links = validate_plan(payload)
    generated_actor_count = build_level(district, rooms, links)
    _, envelope_size = district_envelope(rooms)
    authored_sizes = [room_size(room) for room in rooms]
    horizontal_lengths = [
        math.hypot(
            portal_location(next(room for room in rooms if room["code"] == b), socket_b)[0][0]
            - portal_location(next(room for room in rooms if room["code"] == a), socket_a)[0][0],
            portal_location(next(room for room in rooms if room["code"] == b), socket_b)[0][1]
            - portal_location(next(room for room in rooms if room["code"] == a), socket_a)[0][1],
        )
        for a, socket_a, b, socket_b, _, kind in links if kind == "horizontal"
    ]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "map": MAP_PATH,
        "ship_class": payload["ship_class"],
        "ship_explorable_room_target": payload["explorable_room_target"],
        "streamed_district_target": len(payload["streamed_districts"]),
        "first_district": district["name"],
        "rooms": len(rooms),
        "numeric_room_ids": len({int(room["room_id"]) for room in rooms}),
        "room_type_ids": len({int(room["room_type_id"]) for room in rooms}),
        "placement_sections": sorted({room["placement_section"] for room in rooms}),
        "same_type_default_min_grid_distance": district["room_placement_policy"][
            "default_same_type_min_grid_distance"
        ],
        "unique_room_sizes": len(set(authored_sizes)),
        "room_size_range_cm": {
            "minimum": [min(size[index] for size in authored_sizes) for index in range(3)],
            "maximum": [max(size[index] for size in authored_sizes) for index in range(3)],
        },
        "decks": sorted({room["deck"] for room in rooms}),
        "graph_edges": len(links),
        "vertical_edges": sum(link[5] == "vertical" for link in links),
        "navigable_corridors": sum(link[5] == "horizontal" for link in links),
        "corridor_length_range_cm": [min(horizontal_lengths), max(horizontal_lengths)],
        "corridor_concept_detail_actors": sum(
            14 + corridor_rib_count(length) for length in horizontal_lengths
        ),
        "room_threshold_bulkheads": sum(link[5] == "horizontal" for link in links) * 2,
        "room_gameplay_hardpoints": sum(len(room_gameplay_hardpoints(room, [
            socket for a, socket_a, b, socket_b, _, kind in links
            for code, socket in ((a, socket_a), (b, socket_b)) if code == room["code"]
        ])) for room in rooms),
        "corridor_gameplay_hardpoints": sum(link[5] == "horizontal" for link in links) * 7,
        "fab_room_dressing_actors": sum(len(PROP_SPECS[room["archetype"]]) for room in rooms),
        "fab_room_dressing_sources": ["Ice Station", "Sci-Fi Flying Cargo Ship"],
        "neutral_work_lights": len(rooms) * 2,
        "corridor_work_lights": sum(link[5] == "horizontal" for link in links),
        "functional_floor_zones": len(rooms) * 2,
        "interior_structural_ribs": len(rooms) * 4,
        "architectural_wall_panels": len(rooms) * 4,
        "architectural_wall_trims": len(rooms) * 2,
        "ceiling_fixture_housings": len(rooms) * 2,
        "ceiling_fixture_strips": len(rooms) * 2,
        "work_bay_divider_posts": len(rooms) * 4,
        "architectural_end_panels": len(rooms) * 4,
        "architectural_end_trims": len(rooms) * 2,
        "bulkhead_divider_posts": len(rooms) * 4,
        "vertical_safety_rails": len(district["vertical_links"]) * 2,
        "vertical_safety_posts": len(district["vertical_links"]) * 4,
        "interactive_activity_stations": len(ROOM_ACTIVITY_CLASSES),
        "survival_supply_pickups": len(ROOM_SURVIVAL_PICKUPS),
        "district_gameplay_directors": 1,
        "hardpoint_population_directors": 1,
        "runtime_hardpoint_population": {"bodies": 6, "obstacles": 10, "bloom_growths": 8},
        "primary_objective_consoles": 1,
        "deck_respawn_checkpoints": len(ROOM_CHECKPOINTS),
        "generated_actors": generated_actor_count,
        "envelope_cm": list(envelope_size),
        "ship_local_origin_cm": district["ship_local_origin_cm"],
        "exterior_policy": "stream separately until the 705-component exterior is merged to the approved 18-30 Nanite modules"
    }, indent=2), encoding="utf-8")
    unreal.log(f"Small Escort operations district complete: {len(rooms)} rooms, {len(links)} links, {generated_actor_count} actors")


if __name__ == "__main__":
    main()
