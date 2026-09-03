"""Validate thrust-gravity and asymmetry invariants for replacement fleet packets."""

from __future__ import annotations

import json
import math
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET_ROOT = ROOT / "docs" / "concept-art" / "2026-08-29" / "production-reference"
EXPECTED_CODES = {"S01", "S02", "S03", "M01", "M02", "M03", "L01", "L02", "L03"}
EXPECTED_TRAVERSAL_SPLINES = {
    "SPL_WALK_PRIMARY", "SPL_CROUCH_ALTERNATE", "SPL_CRAWL_SERVICE",
    "SPL_VENT_BYPASS", "SPL_SQUEEZE_EMERGENCY",
}
EXPECTED_INTERDECK_SPLINES = {
    "SPL_LIFT_PRIMARY", "SPL_STAIR_PRESSURE", "SPL_LADDER_SERVICE", "SPL_TRUNK_EMERGENCY",
}
EXPECTED_ENVIRONMENT_SPLINES = {"SPL_POWER", "SPL_DATA", "SPL_COOLANT", "SPL_AIR", "SPL_BLOOM_HIDDEN"}
EXPECTED_ROOM_SOCKETS = {
    "SOCK_DOOR_Y_POS", "SOCK_DOOR_Y_NEG", "SOCK_LIFT_X_POS", "SOCK_LADDER_X_NEG",
    "SOCK_STAIR_X_POS", "SOCK_STAIR_X_NEG", "SOCK_TRUNK_X_POS", "SOCK_TRUNK_X_NEG",
    "SOCK_VENT_IN", "SOCK_VENT_OUT", "SOCK_DAMAGE_BREACH",
}


def fail(errors: list[str], packet: Path, message: str) -> None:
    errors.append(f"{packet.relative_to(ROOT).as_posix()}: {message}")


def validate_packet(path: Path, errors: list[str]) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    code = data["metadata"]["ship_code"].removeprefix("GGP-")
    build = data["build"]
    implementation = build["implementation"]

    if build["coordinate_system"] != {"units": "meters", "forward": "+X", "up": "+Z", "unreal_units_per_meter": 100}:
        fail(errors, path, "coordinate system is not the canonical +X forward, +Z display-up frame")
    if implementation["gravity_vector_ship_space"] != [-1.0, 0.0, 0.0]:
        fail(errors, path, "gravity vector must be exactly -X")
    if implementation["thrust_vector_ship_space"] != [1.0, 0.0, 0.0]:
        fail(errors, path, "thrust vector must be exactly +X")
    if implementation["floor_plane"] != "YZ" or implementation["floor_normal"] != "+X":
        fail(errors, path, "floor contract must be YZ plane with +X normal")
    if implementation["deck_stack_axis"] != "+X" or implementation["engine_base"] != "aft -X face":
        fail(errors, path, "deck stack and engine-base frame are inconsistent")
    presentation = implementation.get("visual_presentation", {})
    stack_proof = presentation.get("canonical_stack_proof", {})
    room_view = presentation.get("room_view", {})
    expected_stack_proof = {
        "ship_on_page": "vertical thrust-gravity stack",
        "page_up": "+X bow",
        "page_down": "-X engines and gravity",
        "floor_on_page": "horizontal transverse YZ slab",
        "occupant_on_page": "upright with boots on engine-facing floor and head toward +X",
        "engines_on_page": "directly below every occupied deck",
    }
    if stack_proof != expected_stack_proof:
        fail(errors, path, "canonical proof must show a vertical stack with engines below every transverse floor")
    expected_room_view = {
        "camera_relation": "local gravity-upright view derived from the same vertical stack frame",
        "page_up": "+X bow",
        "page_down": "-X engines and gravity",
        "floor_on_page": "horizontal at bottom because the room geometry is correctly authored",
    }
    if room_view != expected_room_view:
        fail(errors, path, "room view must derive from the same vertical-stack gravity frame")
    forbidden = set(presentation.get("forbidden", []))
    required_forbidden = {
        "canted or diagonal main engine",
        "main nozzle outside common aft plane",
        "floor not between occupant and engines",
        "conventional axial corridor used as a room story",
        "person pasted onto incorrectly oriented room",
        "Y-down gravity",
        "Z-down gravity",
    }
    if forbidden != required_forbidden:
        fail(errors, path, "visual-presentation forbidden set is incomplete")

    engine_part = next((part for part in build["parts"] if part["name"] == "MODULE_EngineBase"), None)
    if not engine_part:
        fail(errors, path, "missing engine-base module")
    else:
        engines = engine_part["modules"]
        radii = [round(engine["radius_norm"], 6) for engine in engines]
        if len(radii) != len(set(radii)):
            fail(errors, path, "engine radii contain copy-pasted equals")
        centroid_y = sum(engine["y_norm"] for engine in engines) / len(engines)
        centroid_z = sum(engine["z_norm"] for engine in engines) / len(engines)
        if math.hypot(centroid_y, centroid_z) < 0.02:
            fail(errors, path, "engine layout centroid is too close to a symmetric origin")
        for engine in engines:
            if engine.get("axis_ship_space") != [1.0, 0.0, 0.0]:
                fail(errors, path, f"{engine['id']} is canted or diagonal instead of parallel to X")
            if engine.get("aft_plane_x") != 0.0:
                fail(errors, path, f"{engine['id']} nozzle is outside the common aft plane")
            if engine.get("gimbal_allowed"):
                fail(errors, path, f"{engine['id']} incorrectly allows main-engine gimbal")
    alignment = implementation.get("main_engine_alignment", {})
    if alignment.get("centerline_axis_ship_space") != [1.0, 0.0, 0.0]:
        fail(errors, path, "main-engine alignment axis must be exactly X")
    if not alignment.get("all_centerlines_parallel") or alignment.get("cant_or_diagonal_allowed"):
        fail(errors, path, "main-engine parallelism contract is not enforced")
    if alignment.get("all_nozzle_exits_common_aft_plane_x_m") != 0.0:
        fail(errors, path, "common aft nozzle plane must be X=0")
    if alignment.get("gimbal_allowed") or not alignment.get("maneuvering_thrusters_separate"):
        fail(errors, path, "main engines must remain fixed and separate from maneuvering thrusters")

    room_part = next((part for part in build["parts"] if part["name"] == "KIT_Rooms"), None)
    if not room_part:
        fail(errors, path, "missing room kit")
    else:
        rooms = room_part["modules"]
        if len(rooms) != 5:
            fail(errors, path, "each ship must define exactly five role rooms")
        archetypes = [room["archetype"] for room in rooms]
        silhouettes = [room["plan_silhouette"] for room in rooms]
        if len(archetypes) != len(set(archetypes)):
            fail(errors, path, "room archetypes are duplicated")
        if len(silhouettes) != len(set(silhouettes)):
            fail(errors, path, "room plan silhouettes are duplicated")
        offsets = [room["door_offset_fraction_y"] for room in rooms]
        if not any(value < 0 for value in offsets) or not any(value > 0 for value in offsets):
            fail(errors, path, "room door offsets do not vary across port and starboard")
        for room in rooms:
            if room["floor_plane"] != "YZ" or room["floor_normal"] != "+X" or room["gravity_down"] != "-X":
                fail(errors, path, f"{room['id']} violates thrust-gravity floor orientation")
            if room["mirrored_pair_allowed"] or room["duplicate_furniture_array_allowed"]:
                fail(errors, path, f"{room['id']} permits mirrored or copy-pasted dressing")
            if room["minimum_unique_landmarks"] < 3:
                fail(errors, path, f"{room['id']} lacks the three-landmark minimum")
            if set(room.get("traversal_splines", [])) != EXPECTED_TRAVERSAL_SPLINES:
                fail(errors, path, f"{room['id']} does not include every canonical traversal spline")
            if set(room.get("interdeck_splines_available", [])) != EXPECTED_INTERDECK_SPLINES:
                fail(errors, path, f"{room['id']} does not expose every canonical interdeck spline type")
            if set(room.get("sockets", [])) != EXPECTED_ROOM_SOCKETS:
                fail(errors, path, f"{room['id']} does not include every canonical boundary socket")
            if len(room.get("required_volumes", [])) < 6:
                fail(errors, path, f"{room['id']} does not include the required traversal and streaming volumes")

    if implementation["asymmetry"]["exterior_greeble_area_fraction_max"] > 0.18:
        fail(errors, path, "exterior clutter cap exceeds 18 percent")
    if "crawl" not in {profile["id"] for profile in implementation["traversal_profiles"]}:
        fail(errors, path, "crawl traversal profile missing")
    if "squeeze_gap" not in {profile["id"] for profile in implementation["traversal_profiles"]}:
        fail(errors, path, "squeeze-gap traversal profile missing")
    profiles = {profile["id"]: profile for profile in implementation["traversal_profiles"]}
    expected_profiles = {
        "walk": {"width_m": 1.2, "height_m": 2.1},
        "crouch": {"width_m": 0.9, "height_m": 1.35},
        "crawl": {"width_m": 0.65, "height_m": 0.85, "length_m": 1.6},
        "squeeze_gap": {"width_m": 0.45, "height_m": 2.0},
        "maintenance_vent": {"width_m": 0.55, "height_m": 0.85},
        "pressure_stair": {"width_m": 1.0, "height_m": 2.1, "axis": "+/-X"},
        "service_ladder": {"width_m": 0.55, "axis": "+/-X"},
    }
    for profile_id, measurements in expected_profiles.items():
        if profile_id not in profiles or any(profiles[profile_id].get(key) != value for key, value in measurements.items()):
            fail(errors, path, f"{profile_id} clearance measurements do not match the canonical profile")
    suits = implementation.get("suit_clearance_envelopes", {})
    if set(suits) != {"scientist", "technician"}:
        fail(errors, path, "suit envelopes must use Scientist and Technician classes")
    elif any(set(suits[role]) != {"small", "medium", "large"} for role in suits):
        fail(errors, path, "each valid suit class must include small, medium, and large envelopes")

    spline_mapping = build.get("spline_mapping", {})
    if {entry["id"] for entry in spline_mapping.get("traversal_splines", [])} != EXPECTED_TRAVERSAL_SPLINES:
        fail(errors, path, "global traversal spline mapping is incomplete")
    if {entry["id"] for entry in spline_mapping.get("interdeck_splines", [])} != EXPECTED_INTERDECK_SPLINES:
        fail(errors, path, "global interdeck spline mapping is incomplete")
    environment_splines = {entry["id"]: entry for entry in spline_mapping.get("environment_splines", [])}
    if set(environment_splines) != EXPECTED_ENVIRONMENT_SPLINES:
        fail(errors, path, "environment spline mapping is incomplete")
    if environment_splines.get("SPL_BLOOM_HIDDEN", {}).get("color") != "normal-signal":
        fail(errors, path, "hidden Bloom false signal must keep normal signal color")
    if set(spline_mapping.get("room_socket_types", [])) != EXPECTED_ROOM_SOCKETS:
        fail(errors, path, "global room socket mapping is incomplete")

    circulation = build.get("circulation_network", {})
    corridor_rules = circulation.get("corridor_rules", {})
    if circulation.get("coordinate_contract", {}).get("within_deck_motion") != "YZ":
        fail(errors, path, "within-deck circulation must remain in YZ")
    if circulation.get("coordinate_contract", {}).get("interdeck_motion") != "+/-X":
        fail(errors, path, "interdeck circulation must run along +/-X")
    if corridor_rules.get("centered_axial_corridor_allowed") or corridor_rules.get("mirrored_floor_plan_allowed"):
        fail(errors, path, "circulation contract permits centered or mirrored corridor layouts")
    if corridor_rules.get("minimum_interdeck_methods_per_occupied_band", 0) < 2:
        fail(errors, path, "each occupied band requires at least two interdeck methods")
    deck_networks = circulation.get("deck_corridor_networks", [])
    topology_ids = [entry.get("topology_id") for entry in deck_networks]
    if len(deck_networks) != 5 or len(set(topology_ids)) != 5:
        fail(errors, path, "five distinct deck corridor topologies are required")
    if any(not entry.get("wraps_room_footprint") for entry in deck_networks):
        fail(errors, path, "a corridor network does not wrap its room footprint")
    devices = circulation.get("interdeck_devices", [])
    device_types = {entry.get("type") for entry in devices}
    required_device_types = {"pressure_lift", "pressure_stair", "service_ladder", "independent_pressure_trunk"}
    if not required_device_types.issubset(device_types):
        fail(errors, path, "interdeck lift, stair, ladder, or emergency-trunk definition is missing")
    room_method_counts = {room["id"]: 0 for room in room_part["modules"]} if room_part else {}
    for device in devices:
        for room_id in device.get("serves", []):
            if room_id in room_method_counts:
                room_method_counts[room_id] += 1
    if any(count < 2 for count in room_method_counts.values()):
        fail(errors, path, "an occupied room band has fewer than two interdeck methods")
    bloom_state = next((entry for entry in circulation.get("route_state_matrix", []) if entry.get("state") == "bloom_false_signal"), None)
    if not bloom_state or bloom_state.get("player_visible_difference") is not False:
        fail(errors, path, "Bloom false-signal circulation state exposes a visible tell")

    story = build.get("room_story_construction", {})
    if not story.get("engines_must_be_engineward_of_every_occupied_floor"):
        fail(errors, path, "room-story load path does not require engines below occupied floors")
    if len(story.get("ordered_layers", [])) != 7:
        fail(errors, path, "room story must define all seven construction layers")

    source_path = data.get("source_sheet", {}).get("path", "")
    if not source_path.endswith("-enlarged-room-traversal-splines-v1.png"):
        fail(errors, path, "primary source sheet is not the enlarged room and traversal reference")
    supplemental = data.get("supplemental_sheets", [])
    if len(supplemental) < 2 or not supplemental[0].get("path", "").endswith("-vertical-stack-room-production-v2.png"):
        fail(errors, path, "corrected v2 vertical-stack overview is missing from supplemental sheets")
    if len(supplemental) < 2 or not supplemental[1].get("path", "").endswith("ggp-main-engine-orthographic-alignment-authority-v1.png"):
        fail(errors, path, "orthographic main-engine geometry authority is missing from supplemental sheets")
    if code == "S01":
        supplemental_paths = {entry.get("path", "") for entry in supplemental}
        if not any(path.endswith("-exterior-deck-asymmetry-integration-v1.png") for path in supplemental_paths):
            fail(errors, path, "S01 exterior and asymmetric deck integration sheet is missing")
        if not any(path.endswith("-player-circulation-deck-connectivity-v1.png") for path in supplemental_paths):
            fail(errors, path, "S01 player circulation and deck connectivity sheet is missing")

    passes = {entry["id"]: entry for entry in build["render_mapping"]["passes"]}
    if not passes.get("RL_Bloom", {}).get("player_hidden_false_signal"):
        fail(errors, path, "Bloom false-signal concealment is not enforced")
    if data["production_ready"] or data["status"] != "ready-for-graybox":
        fail(errors, path, "reference must remain ready-for-graybox until engine validation passes")
    return code


def main() -> None:
    errors: list[str] = []
    found: set[str] = set()
    for path in sorted(PACKET_ROOT.glob("ggp-*-thrust-tower-production-v1.production.json")):
        code = validate_packet(path, errors)
        if code in found:
            fail(errors, path, f"duplicate ship code {code}")
        found.add(code)
    missing = EXPECTED_CODES - found
    extra = found - EXPECTED_CODES
    if missing:
        errors.append(f"missing ship packets: {', '.join(sorted(missing))}")
    if extra:
        errors.append(f"unexpected ship packets: {', '.join(sorted(extra))}")
    if errors:
        print("Thrust-tower validation failed:")
        for error in errors:
            print(f"  {error}")
        raise SystemExit(1)
    print(f"Validated {len(found)} thrust-tower ship packets.")
    print("Gravity -X, vertical-stack proofs, transverse YZ floors, straight parallel main engines, common aft nozzle planes, unique rooms, YZ corridor networks, +/-X interdeck systems, traversal splines, sockets, suit clearances, render layers, and readiness gates passed.")


if __name__ == "__main__":
    main()
