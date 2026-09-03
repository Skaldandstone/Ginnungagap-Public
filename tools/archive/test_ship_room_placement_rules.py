"""Fast tests for procedural room identity and same-type spacing."""

import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from ship_room_placement_rules import assign_room_locations, validate_room_placements


CATALOG = [
    {"room_type_id": 10, "key": "utility"},
    {"room_type_id": 20, "key": "dormitory",
     "allow_same_type_cluster_in_sections": ["habitation"]},
]
POLICY = {"default_same_type_min_grid_distance": 3, "deck_distance_weight": 2}


class ShipRoomPlacementRulesTest(unittest.TestCase):
    def test_rejects_nearby_duplicate_type(self):
        rooms = [
            {"room_id": 1, "room_type_id": 10, "placement_section": "engineering",
             "deck": 1, "grid": [0, 0]},
            {"room_id": 2, "room_type_id": 10, "placement_section": "engineering",
             "deck": 1, "grid": [1, 0]},
        ]
        self.assertTrue(validate_room_placements(rooms, CATALOG, POLICY))

    def test_allows_dormitory_cluster_inside_habitation(self):
        rooms = [
            {"room_id": 1, "room_type_id": 20, "placement_section": "habitation",
             "deck": 1, "grid": [0, 0]},
            {"room_id": 2, "room_type_id": 20, "placement_section": "habitation",
             "deck": 1, "grid": [1, 0]},
        ]
        self.assertEqual(validate_room_placements(rooms, CATALOG, POLICY), [])

    def test_dormitory_exception_does_not_leak_to_other_sections(self):
        rooms = [
            {"room_id": 1, "room_type_id": 20, "placement_section": "command",
             "deck": 1, "grid": [0, 0]},
            {"room_id": 2, "room_type_id": 20, "placement_section": "command",
             "deck": 1, "grid": [1, 0]},
        ]
        self.assertTrue(validate_room_placements(rooms, CATALOG, POLICY))

    def test_seeded_assignment_is_deterministic_and_separates_duplicates(self):
        rooms = [
            {"room_id": 1, "room_type_id": 10, "placement_section": "engineering"},
            {"room_id": 2, "room_type_id": 10, "placement_section": "engineering"},
            {"room_id": 3, "room_type_id": 20, "placement_section": "habitation"},
        ]
        slots = [
            {"deck": 1, "grid": [0, 0]}, {"deck": 1, "grid": [1, 0]},
            {"deck": 1, "grid": [2, 0]}, {"deck": 1, "grid": [3, 0]},
        ]
        first = assign_room_locations(rooms, slots, CATALOG, POLICY, seed=8173)
        second = assign_room_locations(rooms, slots, CATALOG, POLICY, seed=8173)
        self.assertEqual(first, second)
        self.assertEqual(validate_room_placements(first, CATALOG, POLICY), [])


if __name__ == "__main__":
    unittest.main()
