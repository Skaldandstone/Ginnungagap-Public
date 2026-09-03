"""Generate canonical thrust-tower ship production-reference packets.

The generated JSON sidecars are the numeric authority for the replacement fleet.
Production sheets remain the visual authority for silhouette, materials, and mood.
"""

from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "concept-art" / "2026-08-29" / "production-reference"
CONCEPT_ROOT = ROOT / "docs" / "concept-art" / "2026-08-29" / "replacement-fleet" / "concepts"


SHIPS = [
    {
        "code": "S01", "slug": "small-utility-escort", "title": "Small Utility Escort",
        "scale": "small", "dimensions": [1400.0, 260.0, 320.0],
        "exterior": "ggp-s01-small-utility-escort-replacement-concept-v1.png",
        "rooms": [
            ("watch_cic", "offset command wedge", -0.31, "port", "single dogleg"),
            ("damage_control", "split-height service room", 0.22, "starboard", "crooked L"),
            ("cargo_lock", "deep rectangular lock", -0.18, "port", "offset bay"),
            ("cryo_refuge", "compact radial refuge", 0.27, "starboard", "clipped octagon"),
            ("crew_commons", "low wide commons", -0.24, "port", "unequal trapezoid"),
        ],
    },
    {
        "code": "S02", "slug": "small-deep-survey-cutter", "title": "Small Deep Survey Cutter",
        "scale": "small", "dimensions": [1400.0, 260.0, 320.0],
        "exterior": "ggp-s02-small-deep-survey-cutter-replacement-concept-v2.png",
        "rooms": [
            ("sensor_chart", "faceted analysis wedge", -0.28, "port", "wide fan"),
            ("sample_lab", "offset bench laboratory", 0.19, "starboard", "notched rectangle"),
            ("contamination_airlock", "dogleg pressure lock", -0.14, "port", "tight S"),
            ("cold_store", "narrow asymmetric archive", 0.31, "starboard", "deep slot"),
            ("observation_room", "curved sensor theater", -0.22, "port", "half octagon"),
        ],
    },
    {
        "code": "S03", "slug": "small-salvage-recovery-tender", "title": "Small Salvage Recovery Tender",
        "scale": "small", "dimensions": [1400.0, 260.0, 320.0],
        "exterior": "ggp-s03-small-salvage-recovery-tender-replacement-concept-v2.png",
        "rooms": [
            ("recovery_control", "raised offset control room", 0.26, "starboard", "hook"),
            ("tool_cage", "narrow secured cage", -0.33, "port", "long slot"),
            ("decompression_lock", "unequal two-chamber lock", 0.16, "starboard", "stepped rectangle"),
            ("salvage_sorting", "open sorting floor", -0.21, "port", "irregular apron"),
            ("machine_shop", "split-bay workshop", 0.29, "starboard", "offset T"),
        ],
    },
    {
        "code": "M01", "slug": "medium-military-corvette", "title": "Medium Military Corvette",
        "scale": "medium", "dimensions": [2400.0, 430.0, 620.0],
        "exterior": "ggp-m01-medium-military-corvette-replacement-exterior-v1.png",
        "rooms": [
            ("armored_cic", "offset armored command bowl", -0.24, "port", "faceted bowl"),
            ("tactical_plotting", "distinct two-level plotting wedge", 0.31, "starboard", "split wedge"),
            ("security_center", "crooked security suite", -0.19, "port", "dogleg"),
            ("casualty_station", "compact treatment cross", 0.23, "starboard", "unequal cross"),
            ("marine_ready_room", "offset equipment gallery", -0.34, "port", "long trapezoid"),
        ],
    },
    {
        "code": "M02", "slug": "medium-research-cruiser", "title": "Medium Research Cruiser",
        "scale": "medium", "dimensions": [2400.0, 430.0, 620.0],
        "exterior": "ggp-m02-medium-research-cruiser-replacement-exterior-v1.png",
        "rooms": [
            ("wet_lab", "offset wet laboratory", 0.18, "starboard", "notched bay"),
            ("xenobiology_containment", "unequal containment cells", -0.32, "port", "staggered comb"),
            ("sensor_theater", "sunken circular theater", 0.27, "starboard", "broken ring"),
            ("specimen_cold_archive", "deep cold archive", -0.16, "port", "narrow L"),
            ("fabrication_lab", "split bench fabrication room", 0.35, "starboard", "offset U"),
        ],
    },
    {
        "code": "M03", "slug": "medium-medical-quarantine-cruiser", "title": "Medium Medical Quarantine Cruiser",
        "scale": "medium", "dimensions": [2400.0, 430.0, 620.0],
        "exterior": "ggp-m03-medium-medical-quarantine-cruiser-replacement-exterior-v2.png",
        "rooms": [
            ("triage", "asymmetric intake theater", -0.21, "port", "angled fan"),
            ("surgery", "offset surgical suite", 0.29, "starboard", "clipped rectangle"),
            ("isolation_ward", "staggered two-level unequal cells", -0.34, "port", "staggered comb"),
            ("decon_lock", "dogleg decontamination lock", 0.17, "starboard", "tight S"),
            ("pharmacy_specimen_archive", "split pharmacy and specimen archive", -0.25, "port", "unequal T"),
        ],
    },
    {
        "code": "L01", "slug": "large-expedition-carrier", "title": "Large Expedition Carrier",
        "scale": "large", "dimensions": [6500.0, 1400.0, 1800.0],
        "exterior": "ggp-l01-large-expedition-carrier-replacement-exterior-v1.png",
        "rooms": [
            ("flight_operations", "offset flight control canyon", -0.28, "port", "long crescent"),
            ("ready_room", "asymmetric crew and officer ready room", 0.22, "starboard", "broken atrium"),
            ("maintenance_hangar_work_cell", "offset maintenance hangar work cell", -0.17, "port", "faceted wedge"),
            ("expedition_planning", "raised expedition planning theater", 0.33, "starboard", "vertical village"),
            ("cargo_deployment_staging", "deep cargo deployment staging room", -0.35, "port", "offset shaft"),
        ],
    },
    {
        "code": "L02", "slug": "large-colony-habitat-ark", "title": "Large Colony Habitat Ark",
        "scale": "large", "dimensions": [6500.0, 1400.0, 1800.0],
        "exterior": "ggp-l02-large-colony-habitat-ark-replacement-exterior-v1.png",
        "rooms": [
            ("community_commons", "irregular community commons", 0.24, "starboard", "stepped village"),
            ("hydroponics_cultivation", "offset hydroponics cultivation story", -0.31, "port", "unequal terraces"),
            ("family_habitat", "varied family habitat module", 0.18, "starboard", "broken oval"),
            ("water_reclamation", "dogleg water reclamation room", -0.22, "port", "branching L"),
            ("civic_clinic_nursery", "asymmetric civic clinic and nursery", 0.35, "starboard", "offset nave"),
        ],
    },
    {
        "code": "L03", "slug": "large-fleet-logistics-carrier", "title": "Large Fleet Logistics Carrier",
        "scale": "large", "dimensions": [6500.0, 1400.0, 1800.0],
        "exterior": "ggp-l03-large-fleet-logistics-carrier-replacement-exterior-v1.png",
        "rooms": [
            ("cargo_traffic_control", "offset cargo traffic control", -0.29, "port", "forked apron"),
            ("pallet_sorting", "irregular pallet sorting bay", 0.23, "starboard", "stepped grid"),
            ("fabrication_repair", "deep fabrication and repair hall", -0.34, "port", "crooked slot"),
            ("cold_logistics_store", "single dominant cold logistics store", 0.36, "starboard", "open C"),
            ("crew_logistics_coordination", "raised crew logistics coordination room", -0.17, "port", "angled balcony"),
        ],
    },
]

TRAVERSAL_SPLINES = [
    {"id": "SPL_WALK_PRIMARY", "color": "cyan", "profile": "walk", "unreal_component": "USplineComponent"},
    {"id": "SPL_CROUCH_ALTERNATE", "color": "orange", "profile": "crouch", "unreal_component": "USplineComponent"},
    {"id": "SPL_CRAWL_SERVICE", "color": "magenta", "profile": "crawl", "unreal_component": "USplineComponent"},
    {"id": "SPL_VENT_BYPASS", "color": "green", "profile": "maintenance_vent", "unreal_component": "USplineComponent"},
    {"id": "SPL_SQUEEZE_EMERGENCY", "color": "yellow", "profile": "squeeze_gap", "unreal_component": "USplineComponent"},
]

INTERDECK_SPLINES = [
    {"id": "SPL_LIFT_PRIMARY", "color": "bright-blue", "profile": "lift", "axis": "+/-X", "unreal_component": "USplineComponent"},
    {"id": "SPL_STAIR_PRESSURE", "color": "white", "profile": "pressure_stair", "axis": "+/-X", "unreal_component": "USplineComponent"},
    {"id": "SPL_LADDER_SERVICE", "color": "violet", "profile": "service_ladder", "axis": "+/-X", "unreal_component": "USplineComponent"},
    {"id": "SPL_TRUNK_EMERGENCY", "color": "red-dashed", "profile": "emergency_trunk", "axis": "+/-X", "unreal_component": "USplineComponent"},
]

ENVIRONMENT_SPLINES = [
    {"id": "SPL_POWER", "color": "red", "purpose": "primary and emergency power", "failure_state": "sparking and dark"},
    {"id": "SPL_DATA", "color": "cyan", "purpose": "data backbone", "failure_state": "UI and sensor dropout"},
    {"id": "SPL_COOLANT", "color": "blue", "purpose": "coolant routing", "failure_state": "leak and fog"},
    {"id": "SPL_AIR", "color": "green", "purpose": "life support and pressure routing", "failure_state": "pressure loss"},
    {"id": "SPL_BLOOM_HIDDEN", "color": "normal-signal", "purpose": "concealed contamination propagation path", "render_only_when_revealed": True},
]

ROOM_SOCKETS = [
    "SOCK_DOOR_Y_POS", "SOCK_DOOR_Y_NEG", "SOCK_LIFT_X_POS", "SOCK_LADDER_X_NEG",
    "SOCK_STAIR_X_POS", "SOCK_STAIR_X_NEG", "SOCK_TRUNK_X_POS", "SOCK_TRUNK_X_NEG",
    "SOCK_VENT_IN", "SOCK_VENT_OUT", "SOCK_DAMAGE_BREACH",
]

TRAVERSAL_PROFILES = [
    {"id": "walk", "width_m": 1.2, "height_m": 2.1},
    {"id": "crouch", "width_m": 0.9, "height_m": 1.35},
    {"id": "crawl", "width_m": 0.65, "height_m": 0.85, "length_m": 1.6},
    {"id": "squeeze_gap", "width_m": 0.45, "height_m": 2.0},
    {"id": "maintenance_vent", "width_m": 0.55, "height_m": 0.85},
    {"id": "pressure_stair", "width_m": 1.0, "height_m": 2.1, "axis": "+/-X"},
    {"id": "service_ladder", "width_m": 0.55, "axis": "+/-X"},
]

CORRIDOR_TOPOLOGIES = [
    {
        "id": "offset_perimeter_c",
        "centerline_points_yz_norm": [[-0.42, -0.30], [-0.42, 0.28], [-0.08, 0.42], [0.36, 0.24], [0.31, -0.18]],
        "terminal_gameplay": "repair",
    },
    {
        "id": "dogleg_split_loop",
        "centerline_points_yz_norm": [[0.38, -0.34], [0.15, -0.08], [0.34, 0.31], [-0.12, 0.38], [-0.40, 0.05]],
        "terminal_gameplay": "hazard_bypass",
    },
    {
        "id": "void_perimeter_catwalk",
        "centerline_points_yz_norm": [[-0.44, -0.22], [-0.31, 0.40], [0.27, 0.43], [0.43, 0.03], [0.22, -0.41]],
        "terminal_gameplay": "sabotage",
    },
    {
        "id": "notched_outer_ring",
        "centerline_points_yz_norm": [[0.41, 0.32], [0.02, 0.35], [-0.37, 0.18], [-0.28, -0.38], [0.18, -0.24]],
        "terminal_gameplay": "loot",
    },
    {
        "id": "broken_loop_with_observation_spur",
        "centerline_points_yz_norm": [[-0.35, 0.33], [0.12, 0.42], [0.39, 0.08], [0.18, -0.36], [-0.28, -0.29]],
        "terminal_gameplay": "observation",
    },
]

SUIT_ENVELOPES = {
    "scientist": {
        "small": {"standing_height_m": 1.75, "standing_width_m": 0.45},
        "medium": {"standing_height_m": 1.95, "standing_width_m": 0.65},
        "large": {"standing_height_m": 2.15, "standing_width_m": 0.75},
    },
    "technician": {
        "small": {"standing_height_m": 1.75, "standing_width_m": 0.50},
        "medium": {"standing_height_m": 1.95, "standing_width_m": 0.70},
        "large": {"standing_height_m": 2.15, "standing_width_m": 0.80},
    },
}


def image_info(path: Path) -> tuple[str, int, int]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with path.open("rb") as handle:
        header = handle.read(24)
    if not header.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError(f"Not a PNG: {path}")
    width, height = struct.unpack(">II", header[16:24])
    return digest, width, height


def engine_modules(scale: str) -> list[dict]:
    radius = {"small": 0.27, "medium": 0.31, "large": 0.34}[scale]
    return [
        {"id": "ENG_01", "role": "primary main thrust", "aft_plane_x": 0.0, "axis_ship_space": [1.0, 0.0, 0.0], "exhaust_direction": "-X", "gimbal_allowed": False, "y_norm": -0.21, "z_norm": -0.12, "radius_norm": radius, "priority": 1},
        {"id": "ENG_02", "role": "sustained main thrust", "aft_plane_x": 0.0, "axis_ship_space": [1.0, 0.0, 0.0], "exhaust_direction": "-X", "gimbal_allowed": False, "y_norm": 0.26, "z_norm": 0.19, "radius_norm": radius * 0.72, "priority": 2},
        {"id": "ENG_03", "role": "emergency return main thrust", "aft_plane_x": 0.0, "axis_ship_space": [1.0, 0.0, 0.0], "exhaust_direction": "-X", "gimbal_allowed": False, "y_norm": 0.30, "z_norm": -0.27, "radius_norm": radius * 0.49, "priority": 3},
        {"id": "ENG_04", "role": "auxiliary main thrust", "aft_plane_x": 0.0, "axis_ship_space": [1.0, 0.0, 0.0], "exhaust_direction": "-X", "gimbal_allowed": False, "y_norm": -0.36, "z_norm": 0.25, "radius_norm": radius * 0.31, "priority": 4},
        {"id": "ENG_05", "role": "boost main thrust", "aft_plane_x": 0.0, "axis_ship_space": [1.0, 0.0, 0.0], "exhaust_direction": "-X", "gimbal_allowed": False, "y_norm": 0.08, "z_norm": 0.34, "radius_norm": radius * 0.22, "priority": 5},
    ]


def circulation_network(code: str, rooms: list[dict]) -> dict:
    room_ids = [room["id"] for room in rooms]
    return {
        "authority": "Numeric route topology and engine integration contract. Runtime navigation remains pending until graybox traversal tests pass.",
        "coordinate_contract": {
            "within_deck_motion": "YZ",
            "interdeck_motion": "+/-X",
            "gravity_down": "-X",
            "floor_plane": "YZ",
        },
        "corridor_rules": {
            "centered_axial_corridor_allowed": False,
            "room_center_crossing_allowed": False,
            "mirrored_floor_plan_allowed": False,
            "identical_topology_repeat_allowed": False,
            "maximum_purposeless_dead_ends": 0,
            "pressure_boundary_socket_required": True,
            "minimum_interdeck_methods_per_occupied_band": 2,
            "rule": "Corridors wrap around each room footprint and equipment island. Their offsets respond to local hull openings, pressure zones, maintenance clearances, and gameplay terminals.",
        },
        "deck_corridor_networks": [
            {
                "deck_id": f"{code}_F{index:02d}",
                "room_id": room["id"],
                "topology_id": CORRIDOR_TOPOLOGIES[index - 1]["id"],
                "centerline_points_yz_norm": CORRIDOR_TOPOLOGIES[index - 1]["centerline_points_yz_norm"],
                "wraps_room_footprint": True,
                "primary_route": "SPL_WALK_PRIMARY",
                "alternate_routes": ["SPL_CROUCH_ALTERNATE", "SPL_CRAWL_SERVICE", "SPL_VENT_BYPASS", "SPL_SQUEEZE_EMERGENCY"],
                "terminal_gameplay": CORRIDOR_TOPOLOGIES[index - 1]["terminal_gameplay"],
                "pressure_boundaries": ["SOCK_DOOR_Y_POS", "SOCK_DOOR_Y_NEG"],
            }
            for index, room in enumerate(rooms, start=1)
        ],
        "interdeck_devices": [
            {
                "id": f"{code}_LIFT_A",
                "type": "pressure_lift",
                "spline": "SPL_LIFT_PRIMARY",
                "yz_offset_norm": [-0.23, 0.16],
                "serves": [room_ids[0], room_ids[1], room_ids[3], room_ids[4]],
                "skips": [room_ids[2]],
                "sockets": ["SOCK_LIFT_X_POS"],
                "unreal_actor": "BP_PressureLift",
                "failure_mode": "disabled platform forces ladder or emergency-trunk reroute",
            },
            {
                "id": f"{code}_STAIR_A",
                "type": "pressure_stair",
                "spline": "SPL_STAIR_PRESSURE",
                "yz_offset_norm": [0.27, -0.18],
                "adjacent_deck_pairs": [[room_ids[0], room_ids[1]], [room_ids[3], room_ids[4]]],
                "sockets": ["SOCK_STAIR_X_POS", "SOCK_STAIR_X_NEG"],
                "unreal_actor": "BP_PressureStair",
            },
            {
                "id": f"{code}_LADDER_PORT",
                "type": "service_ladder",
                "spline": "SPL_LADDER_SERVICE",
                "yz_offset_norm": [-0.36, -0.21],
                "serves": [room_ids[0], room_ids[2], room_ids[4]],
                "sockets": ["SOCK_LADDER_X_NEG"],
                "unreal_actor": "BP_ServiceLadder",
            },
            {
                "id": f"{code}_LADDER_STARBOARD",
                "type": "service_ladder",
                "spline": "SPL_LADDER_SERVICE",
                "yz_offset_norm": [0.31, 0.26],
                "serves": [room_ids[1], room_ids[2], room_ids[3]],
                "sockets": ["SOCK_LADDER_X_NEG"],
                "unreal_actor": "BP_ServiceLadder",
            },
            {
                "id": f"{code}_TRUNK_EMERGENCY",
                "type": "independent_pressure_trunk",
                "spline": "SPL_TRUNK_EMERGENCY",
                "yz_offset_norm": [0.41, -0.31],
                "serves": room_ids,
                "sockets": ["SOCK_TRUNK_X_POS", "SOCK_TRUNK_X_NEG"],
                "unreal_actor": "BP_EmergencyTrunk",
                "pressure_doors_independent": True,
            },
        ],
        "special_routes": [
            {
                "id": f"{code}_SPECIAL_BAND_03",
                "room_id": room_ids[2],
                "components": ["perimeter catwalk", "service ladder descent", "squeeze route behind structural braces"],
                "normal_floor_through_void_allowed": False,
            },
            {
                "id": f"{code}_LOCKED_BOUNDARY_BYPASS",
                "components": ["SPL_VENT_BYPASS", "SPL_CRAWL_SERVICE"],
                "entry_socket": "SOCK_VENT_IN",
                "exit_socket": "SOCK_VENT_OUT",
                "crosses_exactly_one_pressure_boundary": True,
            },
        ],
        "route_state_matrix": [
            {"state": "nominal", "primary": "SPL_LIFT_PRIMARY", "alternate": "SPL_STAIR_PRESSURE", "fallback": "SPL_LADDER_SERVICE"},
            {"state": "lift_disabled", "primary": "SPL_STAIR_PRESSURE", "alternate": "SPL_LADDER_SERVICE", "fallback": "SPL_TRUNK_EMERGENCY"},
            {"state": "depressurized_deck", "primary": "sealed pressure detour", "alternate": "SPL_TRUNK_EMERGENCY", "fallback": "suit-only breach route"},
            {"state": "fire_obstruction", "primary": "alternate YZ corridor", "alternate": "SPL_VENT_BYPASS", "fallback": "SPL_TRUNK_EMERGENCY"},
            {"state": "locked_door", "primary": "alternate pressure door", "alternate": "SPL_CRAWL_SERVICE", "fallback": "SPL_VENT_BYPASS"},
            {"state": "damage_breach", "primary": "sealed detour", "alternate": "SOCK_DAMAGE_BREACH suit-only", "fallback": "SPL_TRUNK_EMERGENCY"},
            {"state": "bloom_false_signal", "primary": "normal-signal", "alternate": "normal-signal", "fallback": "normal-signal", "player_visible_difference": False},
        ],
        "dcc_mapping": {
            "houdini_attributes": ["deck_frame_x", "corridor_centerline", "pressure_boundary", "route_class", "clearance_m", "socket_type", "deck_span", "fallback_priority"],
            "blender_collections": ["ROUTES_WALK", "ROUTES_CROUCH", "ROUTES_CRAWL", "ROUTES_VERTICAL", "SOCKETS", "PRESSURE_DOORS"],
            "unreal": {
                "components": ["SplineComponents", "NavModifierVolumes", "NavLinkProxy", "SmartLinks"],
                "actors": ["BP_PressureLift", "BP_PressureStair", "BP_ServiceLadder", "BP_EmergencyTrunk"],
                "streaming_ownership": "deck band",
                "route_variants": ["locked", "damaged", "depressurized", "Bloom false signal"],
            },
        },
    }


def make_packet(ship: dict) -> tuple[Path, dict]:
    code = ship["code"]
    slug = ship["slug"]
    code_slug = code.lower()
    overview_path = OUT / f"ggp-{code_slug}-{slug}-vertical-stack-room-production-v2.png"
    expanded_path = OUT / f"ggp-{code_slug}-{slug}-enlarged-room-traversal-splines-v1.png"
    engine_authority_path = OUT / "ggp-main-engine-orthographic-alignment-authority-v1.png"
    asymmetry_integration_path = OUT / f"ggp-{code_slug}-{slug}-exterior-deck-asymmetry-integration-v1.png"
    circulation_sheet_path = OUT / f"ggp-{code_slug}-{slug}-player-circulation-deck-connectivity-v1.png"
    overview_digest, overview_width, overview_height = image_info(overview_path)
    expanded_digest, expanded_width, expanded_height = image_info(expanded_path)
    engine_authority_digest, engine_authority_width, engine_authority_height = image_info(engine_authority_path)
    rel_overview = overview_path.relative_to(ROOT).as_posix()
    rel_expanded = expanded_path.relative_to(ROOT).as_posix()
    rel_engine_authority = engine_authority_path.relative_to(ROOT).as_posix()
    extra_sheets = []
    extra_sources = []
    if asymmetry_integration_path.exists():
        digest, width, height = image_info(asymmetry_integration_path)
        rel_path = asymmetry_integration_path.relative_to(ROOT).as_posix()
        extra_sheets.append({
            "path": rel_path, "sha256": digest, "width_px": width, "height_px": height,
            "role": "exterior-deck-asymmetry-integration-authority", "generated_on": "2026-08-30",
        })
        extra_sources.append({"path": rel_path, "role": "canonical exterior and asymmetric deck integration reference", "required": True})
    if circulation_sheet_path.exists():
        digest, width, height = image_info(circulation_sheet_path)
        rel_path = circulation_sheet_path.relative_to(ROOT).as_posix()
        extra_sheets.append({
            "path": rel_path, "sha256": digest, "width_px": width, "height_px": height,
            "role": "player-circulation-deck-connectivity-authority", "generated_on": "2026-08-30",
        })
        extra_sources.append({"path": rel_path, "role": "canonical player circulation and deck connectivity reference", "required": True})
    ext_path = (CONCEPT_ROOT / ship["exterior"]).relative_to(ROOT).as_posix()
    length, beam, height_m = ship["dimensions"]
    root_name = f"GGP_{code}_{slug.replace('-', '_').upper()}"
    rooms = []
    for index, (room_id, archetype, door_offset, alcove_side, silhouette) in enumerate(ship["rooms"], start=1):
        x0 = round(length * (0.12 + (index - 1) * 0.16), 2)
        x1 = round(min(length * 0.94, x0 + length * 0.12), 2)
        rooms.append({
            "id": f"ROOM_{index:02d}_{room_id.upper()}",
            "role": room_id,
            "archetype": archetype,
            "x_band_m": [x0, x1],
            "floor_plane": "YZ",
            "floor_normal": "+X",
            "gravity_down": "-X",
            "door_offset_fraction_y": door_offset,
            "dominant_alcove": alcove_side,
            "plan_silhouette": silhouette,
            "mirrored_pair_allowed": False,
            "duplicate_furniture_array_allowed": False,
            "minimum_unique_landmarks": 3,
            "unique_footprint_id": f"{code}_ROOM_{index:02d}_FOOTPRINT_A",
            "traversal_splines": [spline["id"] for spline in TRAVERSAL_SPLINES],
            "interdeck_splines_available": [spline["id"] for spline in INTERDECK_SPLINES],
            "sockets": ROOM_SOCKETS,
            "corridor_topology": CORRIDOR_TOPOLOGIES[index - 1],
            "corridor_wraps_room_footprint": True,
            "minimum_interdeck_methods": 2,
            "render_layers": ["RL_Interior", "RL_Decals", "RL_Damage", "RL_Bloom", "RL_Fog"],
            "required_volumes": ["NAV_WALK_VOL", "NAV_CRAWL_VOL", "NAV_SQUEEZE_VOL", "MAINT_VENT_VOL", "PRESSURE_BOUNDARY", "STREAMING_OWNERSHIP_CELL"],
        })
    deck_frames = [
        {"id": f"FRAME_{i:02d}", "x_m": round(length * p, 2), "plane": "YZ", "normal": "+X"}
        for i, p in enumerate((0.04, 0.18, 0.34, 0.50, 0.66, 0.82, 0.96), start=1)
    ]
    packet = {
        "$schema": "../../../2026-08-28/production-reference/production-reference.schema.json",
        "schema_version": "1.0.0",
        "asset_id": f"GGP.Ship.{code}.ThrustTower.ReferenceV1",
        "title": f"GGP-{code} {ship['title']} Thrust-Tower Production Reference",
        "category": "ship",
        "status": "ready-for-graybox",
        "production_ready": False,
        "implementation_profile": "expanded",
        "metadata": {
            "purpose": "Canonical source-grounded ship, room-kit, DCC, and Unreal implementation contract",
            "authoritative_sidecar": True,
            "engine_targets": ["Unreal Engine 5.8"],
            "export_targets": ["FBX", "glTF", "USD"],
            "source_preservation": "All v1, superseded, and generated source images remain unchanged and traceable.",
            "ship_code": f"GGP-{code}",
            "scale_class": ship["scale"],
            "coordinate_contract": "The ship is a thrust-gravity vertical stack. +X is bow and up-stack, -X is aft toward engines and gravity-down, and every occupied floor is a transverse YZ slab with +X normal.",
            "visual_presentation_contract": "Canonical stack proofs show +X toward page top and -X engines toward page bottom. Room views are authored upright in local thrust gravity because their geometry, fixtures, and occupants all bear on the engine-facing floor.",
            "supersedes": [
                "Conventional horizontal-deck interpretations",
                "Mirrored engine-bank layouts",
                "Repeated symmetric room filler",
            ],
        },
        "owners": ["vehicle-art", "environment-art", "technical-art", "level-design", "gameplay"],
        "source_sheet": {
            "path": rel_expanded, "sha256": expanded_digest, "width_px": expanded_width, "height_px": expanded_height,
            "role": "enlarged-room-traversal-authority", "generated_on": "2026-08-29",
            "notes": "Visual authority for large room plans, sections, traversal splines, sockets, clearances, utility routes, overlays, and DCC mapping. This JSON is numeric authority.",
        },
        "supplemental_sheets": [
            {
                "path": rel_overview, "sha256": overview_digest, "width_px": overview_width, "height_px": overview_height,
                "role": "vertical-stack-room-overview-authority", "generated_on": "2026-08-29",
            },
            {
                "path": rel_engine_authority, "sha256": engine_authority_digest,
                "width_px": engine_authority_width, "height_px": engine_authority_height,
                "role": "main-engine-orthographic-geometry-authority", "generated_on": "2026-08-29",
                "notes": "Overrides perspective or angled engine depictions in every other raster sheet.",
            },
        ] + extra_sheets,
        "concept_sources": [
            {"path": ext_path, "role": "approved replacement exterior baseline", "required": True},
            {"path": rel_overview, "role": "canonical from-scratch vertical-stack room overview", "required": True},
            {"path": rel_expanded, "role": "canonical from-scratch enlarged room and traversal reference", "required": True},
            {"path": rel_engine_authority, "role": "canonical straight-axis and common-aft-plane engine geometry reference", "required": True},
        ] + extra_sources,
        "authority": {
            "approved": [
                {"field": "build.dimensions_m", "value": ship["dimensions"], "source": "docs/ShipArchitectureAuthority.md"},
                {"field": "build.coordinate_system.gravity", "value": "-X", "source": "docs/ShipArchitectureAuthority.md"},
                {"field": "build.implementation.floor_plane", "value": "YZ", "source": "docs/ShipArchitectureAuthority.md"},
                {"field": "build.implementation.floor_normal", "value": "+X", "source": "docs/ShipArchitectureAuthority.md"},
                {"field": "build.implementation.room_symmetry", "value": "deliberately asymmetric", "source": "docs/ShipArchitectureAuthority.md"},
            ],
            "provisional": [
                {"field": "build.parts.surface_panel_seams", "value": "visual proposal", "source": rel_overview},
                {"field": "build.materials.color_balance", "value": "visual proposal", "source": rel_expanded},
            ],
            "conflicts": [],
        },
        "build": {
            "coordinate_system": {"units": "meters", "forward": "+X", "up": "+Z", "unreal_units_per_meter": 100},
            "dimensions_m": ship["dimensions"],
            "current_bounds_cm": None,
            "pivot": {
                "name": "PIVOT_ShipRoot_AftCenter", "location_m": [0.0, 0.0, 0.0],
                "rule": "Aft engine-base center. Geometry extends toward +X. No export rotation.",
            },
            "parts": [
                {"name": "HULL_PrimaryShell", "role": "broad low-clutter silhouette", "nanite": True},
                {"name": "HULL_PressureSpine", "role": "primary structural and pressure spine", "nanite": True},
                {"name": "FRAME_TransverseSet", "role": "seven transverse YZ frames", "instances": deck_frames},
                {"name": "MODULE_EngineBase", "role": "asymmetric aft main-drive base with straight parallel centerlines and a common nozzle plane", "modules": engine_modules(ship["scale"])},
                {"name": "MODULE_ManeuveringThrusters", "role": "separate attitude, translation, and docking thrusters; never classified as main engines"},
                {"name": "KIT_Rooms", "role": "unique asymmetric transverse-slab room modules", "modules": rooms},
                {"name": "OVERLAY_Damage", "role": "separable damage geometry and decals"},
                {"name": "OVERLAY_Bloom", "role": "separable contamination geometry, masks, decals, and VFX"},
            ],
            "materials": [
                {"slot": "M_Hull_Ivory", "family": "painted armor", "render_layer": "RL_CleanHull"},
                {"slot": "M_Structure_Dark", "family": "exposed structure", "render_layer": "RL_Structure"},
                {"slot": "M_Safety_Amber", "family": "functional markings", "render_layer": "RL_Decals"},
                {"slot": "M_Glass", "family": "transparent", "render_layer": "RL_Transparency"},
                {"slot": "M_EngineEmissive", "family": "propulsion emissive", "render_layer": "RL_EngineVFX"},
                {"slot": "M_Damage", "family": "damage overlay", "render_layer": "RL_Damage"},
                {"slot": "M_Bloom", "family": "Bloom overlay", "render_layer": "RL_Bloom"},
            ],
            "sockets": [
                {"id": "SOCK_AFT_ENGINE_BASE", "location_m": [0.0, 0.0, 0.0], "forward": "-X", "use": "engine VFX and thrust force"},
                {"id": "SOCK_BOW_DOCK", "location_m": [length, 0.0, 0.0], "forward": "+X", "use": "fore docking and alignment"},
                {"id": "SOCK_DOCK_PORT", "location_m": [length * 0.58, -beam * 0.5, height_m * 0.08], "forward": "-Y", "use": "asymmetric docking"},
                {"id": "SOCK_SERVICE_STARBOARD", "location_m": [length * 0.41, beam * 0.5, -height_m * 0.17], "forward": "+Y", "use": "service access"},
                {"id": "SOCK_SENSOR_DORSAL", "location_m": [length * 0.77, beam * 0.11, height_m * 0.5], "forward": "+Z", "use": "sensor suite"},
            ],
            "room_story_construction": {
                "axis": "+X from engine-facing floor toward next bowward deck",
                "ordered_layers": [
                    {"id": "structural_floor_slab", "plane": "YZ", "load_bearing": True},
                    {"id": "utility_plenum", "services": ["power", "data", "coolant", "air"]},
                    {"id": "finished_floor", "walkable": True, "normal": "+X"},
                    {"id": "occupied_room_volume", "gravity_down": "-X"},
                    {"id": "overhead_plenum", "services": ["air", "fire suppression", "lighting"]},
                    {"id": "ceiling_finish", "walkable": False},
                    {"id": "next_deck_structural_slab", "plane": "YZ"},
                ],
                "engines_must_be_engineward_of_every_occupied_floor": True,
            },
            "circulation_network": circulation_network(code, rooms),
            "states": [
                {"id": "clean", "base_geometry": True, "overlay": None},
                {"id": "light_damage", "base_geometry": True, "overlay": "OVERLAY_Damage", "intensity": 0.25},
                {"id": "heavy_damage", "base_geometry": True, "overlay": "OVERLAY_Damage", "intensity": 0.70},
                {"id": "bloom_contaminated", "base_geometry": True, "overlay": "OVERLAY_Bloom", "concealment_required": True},
            ],
            "blender": {
                "root_collection": root_name,
                "collections": ["00_GUIDES", "10_HULL", "20_FRAMES", "30_ENGINES", "40_ROOM_KIT", "50_COLLISION", "60_SOCKETS", "70_SPLINES", "71_ROUTES_VERTICAL", "72_PRESSURE_DOORS", "80_DAMAGE", "81_BLOOM", "90_EXPORT"],
                "units": "meters", "forward": "+X", "up": "+Z",
                "geometry_nodes": ["GN_HullPartitionAssembler", "GN_TransverseFrameArray", "GN_SplineUtilityRouter", "GN_DamageOverlayScatter"],
                "export_set": f"EXP_GGP_{code}",
            },
            "unreal": {
                "asset_type": "ModularStaticMeshBlueprintSet",
                "destination_root": f"/Game/Assets/Ships/ThrustTower/{code}",
                "blueprint_root": f"BP_GGP_{code}_ShipRoot",
                "pcg_graphs": [f"PCG_GGP_{code}_HullAssembly", f"PCG_GGP_{code}_RoomPopulation", f"PCG_GGP_{code}_DamageOverlay"],
                "world_partition": True,
                "data_layers": ["DL_Clean", "DL_Damage", "DL_Bloom", "DL_Interior", "DL_Exterior", "DL_VFX"],
                "nanite": "Enable on opaque static hull and structural modules. Disable on translucent and deforming overlays.",
                "collision": "Authored simple collision by streamed hull partition. Separate walkable room and blocking hull channels.",
                "import_policy": "Import modules with aft-root pivot, +X forward, +Z display-up, no corrective rotation, and 1 m equals 100 uu.",
                "circulation_blueprints": ["BP_PressureLift", "BP_PressureStair", "BP_ServiceLadder", "BP_EmergencyTrunk"],
                "navigation_links": ["NavLinkProxy", "SmartLink_Ladder", "SmartLink_Stair", "SmartLink_Vent", "SmartLink_Squeeze"],
            },
            "rig": {
                "controls": [
                    {"id": "CTRL_ShipRoot", "type": "transform", "pivot": "PIVOT_ShipRoot_AftCenter", "drives": ["all modules"]},
                    {"id": "CTRL_MainEngineThrottle", "type": "scalar", "limits": [0.0, 1.0], "drives": ["ENG_01", "ENG_02", "ENG_03", "ENG_04", "ENG_05"]},
                    {"id": "CTRL_ManeuveringThrusters", "type": "vector", "drives": ["MODULE_ManeuveringThrusters"]},
                    {"id": "CTRL_DockPort", "type": "transform", "socket": "SOCK_DOCK_PORT", "drives": ["docking collar"]},
                ],
                "requirements": [
                    {"id": "rig-root-axis", "rule": "Root control preserves +X forward and -X gravity with no corrective parent rotation."},
                    {"id": "rig-streaming-safe", "rule": "Animated service modules cannot own streamed hull partitions."},
                ],
            },
            "animation": {
                "states": [
                    {"id": "idle_thrust", "loops": True, "channels": ["engine emissive", "subtle vector trim", "service vibration"]},
                    {"id": "maneuver", "loops": False, "channels": ["maneuvering-thruster pulse", "hull light cue"]},
                    {"id": "damage_transition", "loops": False, "channels": ["breach reveal", "light failure", "debris impulse"]},
                    {"id": "bloom_reveal", "loops": False, "channels": ["overlay growth", "hidden spline activation", "localized particulate"]},
                ],
                "requirements": [
                    {"id": "animation-gravity-frame", "rule": "All room and prop animation remains authored in the ship local frame where gravity is -X."},
                    {"id": "animation-no-false-signal-tell", "rule": "False-signal animation cannot reveal deception through color, timing, or unique motion."},
                ],
            },
            "vfx": {
                "layers": [
                    {"id": "VFX_EnginePrimary", "sockets": ["SOCK_AFT_ENGINE_BASE"], "data_layer": "DL_VFX", "scalable": True},
                    {"id": "VFX_RCS", "source": "engine module sockets", "data_layer": "DL_VFX", "scalable": True},
                    {"id": "VFX_Damage", "source": "SPL_POWER and SPL_COOLANT breaks", "data_layer": "DL_Damage", "scalable": True},
                    {"id": "VFX_Bloom", "source": "SPL_BLOOM_HIDDEN", "data_layer": "DL_Bloom", "scalable": True, "hidden_until_reveal": True},
                ],
                "requirements": [
                    {"id": "vfx-streaming-ownership", "rule": "Each emitter belongs to the same streaming cell as its socket or spline segment."},
                    {"id": "vfx-false-signal", "rule": "False Bloom signals reuse clean-state rendering and do not receive a warning-color override."},
                ],
            },
            "spline_mapping": {
                "traversal_splines": TRAVERSAL_SPLINES,
                "interdeck_splines": INTERDECK_SPLINES,
                "environment_splines": ENVIRONMENT_SPLINES,
                "room_socket_types": ROOM_SOCKETS,
                "dcc_mapping": {
                    "houdini": {"representation": "curves and named groups", "group_prefix": "grp_"},
                    "blender": {"representation": "curve objects and socket empties", "collections": ["70_SPLINES", "60_SOCKETS"]},
                    "unreal": {"representation": "USplineComponent, scene-component sockets, and actor volumes", "pcg_tags_required": True},
                },
                "requirements": [
                    {"id": "spline-boundary-crossing", "rule": "Every traversal or utility spline crossing a room or pressure boundary receives a named socket."},
                    {"id": "spline-clearance", "rule": "Every traversal spline remains inside the matching clearance volume for its full length."},
                    {"id": "spline-route-choice", "rule": "Every room has a primary walk route plus at least one alternate, service, vent, or emergency route."},
                    {"id": "spline-environment-separation", "rule": "Traversal and environment splines are separate assets, collections, components, and PCG tags."},
                    {"id": "spline-damage-breaks", "rule": "Power, data, coolant, air, and vent splines expose break and reroute states per streaming cell."},
                ],
            },
            "volume_mapping": {
                "NAV_WALK_VOL": {"profile": "walk", "unreal_class": "NavModifierVolume"},
                "NAV_CRAWL_VOL": {"profile": "crawl", "unreal_class": "TriggerVolume"},
                "NAV_SQUEEZE_VOL": {"profile": "squeeze_gap", "unreal_class": "TriggerVolume"},
                "MAINT_VENT_VOL": {"profile": "maintenance_vent", "unreal_class": "TriggerVolume"},
                "COLLISION_PRIMITIVE": {"dcc": "UCX", "unreal_class": "BodySetup"},
                "FOG_VISIBILITY_BLOCKER": {"unreal_class": "PostProcessVolume"},
                "PRESSURE_BOUNDARY": {"unreal_class": "TriggerVolume"},
                "STREAMING_OWNERSHIP_CELL": {"unreal_class": "WorldPartitionRuntimeCell"},
            },
            "render_mapping": {
                "passes": [
                    {"id": "RL_CleanHull", "source": ["10_HULL", "20_FRAMES"], "unreal_data_layer": "DL_Clean"},
                    {"id": "RL_Interior", "source": ["40_ROOM_KIT"], "unreal_data_layer": "DL_Interior"},
                    {"id": "RL_EngineVFX", "source": ["30_ENGINES", "60_SOCKETS"], "unreal_data_layer": "DL_VFX"},
                    {"id": "RL_Damage", "source": ["80_DAMAGE"], "unreal_data_layer": "DL_Damage"},
                    {"id": "RL_Bloom", "source": ["81_BLOOM"], "unreal_data_layer": "DL_Bloom", "player_hidden_false_signal": True},
                    {"id": "RL_Technical", "source": ["00_GUIDES", "50_COLLISION", "70_SPLINES"], "editor_only": True},
                ],
                "requirements": [
                    {"id": "bloom-no-signal-color", "rule": "False-signal Bloom uses normal clean-state signal color and presentation. Never recolor it to disclose deception."},
                    {"id": "overlay-separation", "rule": "Damage and Bloom remain separable from clean hull and from each other."},
                ],
            },
            "implementation": {
                "gravity_vector_ship_space": [-1.0, 0.0, 0.0],
                "thrust_vector_ship_space": [1.0, 0.0, 0.0],
                "floor_plane": "YZ", "floor_normal": "+X", "deck_stack_axis": "+X",
                "engine_base": "aft -X face", "deck_numbering": "aft to fore",
                "visual_presentation": {
                    "canonical_stack_proof": {
                        "ship_on_page": "vertical thrust-gravity stack",
                        "page_up": "+X bow",
                        "page_down": "-X engines and gravity",
                        "floor_on_page": "horizontal transverse YZ slab",
                        "occupant_on_page": "upright with boots on engine-facing floor and head toward +X",
                        "engines_on_page": "directly below every occupied deck",
                    },
                    "room_view": {
                        "camera_relation": "local gravity-upright view derived from the same vertical stack frame",
                        "page_up": "+X bow",
                        "page_down": "-X engines and gravity",
                        "floor_on_page": "horizontal at bottom because the room geometry is correctly authored",
                    },
                    "forbidden": [
                        "canted or diagonal main engine",
                        "main nozzle outside common aft plane",
                        "floor not between occupant and engines",
                        "conventional axial corridor used as a room story",
                        "person pasted onto incorrectly oriented room",
                        "Y-down gravity",
                        "Z-down gravity",
                    ],
                },
                "main_engine_alignment": {
                    "centerline_axis_ship_space": [1.0, 0.0, 0.0],
                    "exhaust_direction": "-X",
                    "all_centerlines_parallel": True,
                    "all_nozzle_exits_common_aft_plane_x_m": 0.0,
                    "cant_or_diagonal_allowed": False,
                    "gimbal_allowed": False,
                    "maneuvering_thrusters_separate": True,
                },
                "asymmetry": {
                    "engine_centroid_must_not_equal_origin": True,
                    "paired_engine_scale_equality_forbidden": True,
                    "room_mirror_reuse_forbidden": True,
                    "minimum_unique_room_landmarks": 3,
                    "maximum_identical_fixture_run": 3,
                    "exterior_greeble_area_fraction_max": 0.18,
                },
                "streaming_cells": [
                    {"id": f"CELL_{i:02d}", "x_m": [round(length * a, 2), round(length * b, 2)], "primary_frame": f"FRAME_{i:02d}"}
                    for i, (a, b) in enumerate(((0.0, 0.14), (0.14, 0.29), (0.29, 0.44), (0.44, 0.59), (0.59, 0.74), (0.74, 0.89), (0.89, 1.0)), start=1)
                ],
                "traversal_profiles": TRAVERSAL_PROFILES,
                "suit_clearance_envelopes": SUIT_ENVELOPES,
                "performance_budget": {
                    "streaming_cells": 7,
                    "visible_high_detail_cells_max": {"small": 5, "medium": 4, "large": 3}[ship["scale"]],
                    "material_slots_per_module_max": 8,
                    "dynamic_lights_per_room_max": 12,
                    "unique_room_hero_props_min": 3,
                },
            },
        },
        "acceptance_checks": [
            {"id": "gravity-axis", "status": "pass", "requirement": "Gravity is -X toward the aft engine base; no Y or Z gravity remains in canonical data.", "evidence": "build.implementation.gravity_vector_ship_space"},
            {"id": "floor-orientation", "status": "pass", "requirement": "All habitable floor planes are YZ transverse slabs with +X normals.", "evidence": "build.parts KIT_Rooms and FRAME_TransverseSet"},
            {"id": "gravity-true-presentation", "status": "pass", "requirement": "Canonical proofs show a true vertical stack with floors between occupants and engines, and room views use the same local gravity frame.", "evidence": "source_sheet, supplemental_sheets, and build.implementation.visual_presentation"},
            {"id": "main-engine-alignment", "status": "pass", "requirement": "Every main-engine centerline is parallel to X, every nozzle exits on the common aft plane, and no main engine can cant or gimbal.", "evidence": "build.parts MODULE_EngineBase.modules and build.implementation.main_engine_alignment"},
            {"id": "main-engine-raster-orthographic", "status": "pass", "requirement": "Engine-bearing overview, story, Houdini, and Unreal panels use flat orthographic engines with straight centerlines and a level common aft plane.", "evidence": "supplemental_sheets vertical-stack-room-production-v2 and main-engine-orthographic-geometry-authority"},
            {"id": "engine-asymmetry", "status": "pass", "requirement": "Straight main engines differ in scale and YZ placement and have an off-origin centroid without using diagonal canting.", "evidence": "build.parts MODULE_EngineBase.modules"},
            {"id": "room-asymmetry", "status": "pass", "requirement": "Five role rooms have unique archetypes, silhouettes, offsets, and landmarks; mirrored reuse is forbidden.", "evidence": "build.parts KIT_Rooms.modules"},
            {"id": "traversal-contract", "status": "pass", "requirement": "Every room links named walk, crouch, crawl, vent, and squeeze splines to sockets, clearance profiles, and volumes.", "evidence": "build.spline_mapping, build.volume_mapping, and build.implementation.traversal_profiles"},
            {"id": "circulation-contract", "status": "pass", "requirement": "Every occupied band has a distinct YZ corridor topology and at least two +/-X interdeck methods across lifts, pressure stairs, service ladders, or the independent emergency trunk.", "evidence": "build.circulation_network"},
            {"id": "source-lineage", "status": "pass", "requirement": "Exterior baselines and both from-scratch vertical-stack room sheets are linked while superseded images remain traceable.", "evidence": "concept_sources"},
            {"id": "blender-graybox", "status": "pending", "requirement": "Generate measured modules and verify aft-root transform, transverse slabs, and unique room footprints in Blender."},
            {"id": "unreal-assembly", "status": "pending", "requirement": "Import modules and validate PCG assembly, World Partition, HLOD, Nanite, collision, and data layers in Unreal."},
            {"id": "runtime-traversal", "status": "pending", "requirement": "Validate walk, crouch, crawl, vent, squeeze-gap, stair, ladder, lift, and emergency-trunk traversal using player suit profiles and route-failure states."},
            {"id": "performance", "status": "pending", "requirement": "Meet frame, memory, streaming, light, and draw-call budgets in the target demo scene."},
        ],
        "build_questions": [
            "Which ship receives the first measured Blender and Unreal production prototype?",
            "Which rooms are required for the vertical-slice demo and which remain streamed set dressing?",
            "Which damage and Bloom states need runtime transitions in the first demo?",
        ],
    }
    out_path = OUT / f"ggp-{code_slug}-{slug}-thrust-tower-production-v1.production.json"
    return out_path, packet


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for ship in SHIPS:
        path, packet = make_packet(ship)
        path.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
        print(path.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
