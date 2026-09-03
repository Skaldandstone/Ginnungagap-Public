"""Build a deterministic, playable four-deck derelict ship demo in Unreal Editor.

The map is intentionally compact and production-asset aware: it uses the project's native
ModularShipRoom, bulkhead, activity, pickup, hazard, cryo, escape-pod, and power systems while
keeping the requested layout a strict 12 x 2 rectangle on each of four decks.
"""

from __future__ import annotations

import json
import math
import os
import random
import sys
from collections import defaultdict
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
TOOLS = PROJECT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
import build_small_escort_operations_district as shared  # noqa: E402


CONFIG = PROJECT / "Config/Ships/QuickDemoFourDeck.json"
REPORT = PROJECT / "Saved/Reports/QuickDemoFourDeckShip.json"
PREFIX = "QuickDemo4D_"

payload = json.loads(CONFIG.read_text(encoding="utf-8"))
MAP_PATH = payload["map"]
SEED = int(os.environ.get("GINNUNGAGAP_SHIP_SEED", payload["seed"]))
ROOM_SIZE = tuple(float(value) for value in payload["room_size_cm"])
CORRIDOR_WIDTH = float(payload["corridor_width_cm"])
COLUMN_SPACING = float(payload["column_spacing_cm"])
DECK_SPACING = float(payload["deck_spacing_cm"])
ROOM_HEIGHT = ROOM_SIZE[2]
DECK_Z = {deck: ROOM_HEIGHT * 0.5 + (deck - 1) * DECK_SPACING for deck in range(1, 5)}
MISSION_ROOM_TYPES = payload["mission_room_types"]
DECK_ROOM_TYPE_POOLS = {
    int(deck): entries for deck, entries in payload["deck_room_type_pools"].items()
}

shared.PREFIX = PREFIX
shared.ROOM_SIZE = ROOM_SIZE
shared.CORRIDOR_SIZE = (COLUMN_SPACING - ROOM_SIZE[0], CORRIDOR_WIDTH, ROOM_HEIGHT)


def enum_value(enum_type, name):
    value = getattr(enum_type, name, None)
    if value is None:
        raise RuntimeError(f"Missing reflected enum {enum_type.__name__}.{name}; rebuild the editor target")
    return value


def load_required(path):
    value = unreal.load_asset(path)
    if not value:
        raise RuntimeError("Missing required quick-demo asset: " + path)
    return value


def load_optional(path):
    value = unreal.load_asset(path)
    if not value:
        unreal.log_warning("Optional quick-demo asset unavailable: " + path)
    return value


def ensure_large_panel_bulkhead_material():
    """Build a large-scale worn-metal variant that reads as plating, not masonry."""
    path = "/Game/Assets/Ships/Production/Materials/M_QuickDemo_BulkheadLargePanel"
    existing = unreal.load_asset(path)
    if existing:
        return existing

    texture = load_required("/Game/Assets/Textures/T_ShipBulkhead_WornSteel")
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_QuickDemo_BulkheadLargePanel",
        "/Game/Assets/Ships/Production/Materials",
        unreal.Material,
        unreal.MaterialFactoryNew(),
    )
    if not material:
        raise RuntimeError("Could not create the quick-demo large-panel bulkhead material")

    uv = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureCoordinate, -620, 0)
    uv.set_editor_property("u_tiling", 0.85)
    uv.set_editor_property("v_tiling", 0.85)
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -390, 0)
    sample.set_editor_property("texture", texture)
    unreal.MaterialEditingLibrary.connect_material_expressions(uv, "", sample, "UVs")
    unreal.MaterialEditingLibrary.connect_material_property(
        sample, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)

    roughness = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -350, 220)
    roughness.set_editor_property("r", 0.66)
    unreal.MaterialEditingLibrary.connect_material_property(
        roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
    metallic = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -350, 310)
    metallic.set_editor_property("r", 0.42)
    unreal.MaterialEditingLibrary.connect_material_property(
        metallic, "", unreal.MaterialProperty.MP_METALLIC)

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def room_code(deck, row, column):
    return f"QD-{deck:02d}-{row * 12 + column + 1:02d}"


def room_location(spec):
    x = (spec["column"] - 5.5) * COLUMN_SPACING
    side = -1.0 if spec["row"] == 0 else 1.0
    y = side * (CORRIDOR_WIDTH * 0.5 + ROOM_SIZE[1] * 0.5)
    return x, y, DECK_Z[spec["deck"]]


def room_type_slug(name):
    return "".join(character.lower() if character.isalnum() else "_" for character in name).strip("_")


def seed_room_types(rooms, rng):
    """Guarantee the Wayfarer sector catalog, then fill remaining cells from its deck pool."""
    for deck, pool in DECK_ROOM_TYPE_POOLS.items():
        if not pool:
            raise RuntimeError(f"Deck {deck} room-type pool is empty")
        for entry in pool:
            if entry["kind"] not in shared.ARCHETYPES:
                raise RuntimeError(f"Unknown room archetype {entry['kind']} for {entry['name']}")

        candidates = [room for room in rooms if room["deck"] == deck and not room["special"]]
        if len(pool) > len(candidates):
            raise RuntimeError(
                f"Deck {deck} needs {len(pool)} catalog rooms but has only {len(candidates)} free cells")
        rng.shuffle(candidates)

        assignments = list(pool)
        assignments.extend(rng.choice(pool) for _ in range(len(candidates) - len(pool)))
        rng.shuffle(assignments)
        occurrences = defaultdict(int)
        for room, entry in zip(candidates, assignments):
            room_type = entry["name"]
            occurrences[room_type] += 1
            room["room_type"] = room_type
            room["kind"] = entry["kind"]
            room["name"] = room_type if occurrences[room_type] == 1 else f"{room_type} {occurrences[room_type]:02d}"


def build_layout(seed):
    rng = random.Random(seed)
    rooms = []
    for deck in range(1, 5):
        for row in range(2):
            for column in range(12):
                rooms.append({
                    "code": room_code(deck, row, column),
                    "deck": deck,
                    "row": row,
                    "column": column,
                    "name": f"Deck {deck:02d} Compartment {row * 12 + column + 1:02d}",
                    "room_type": None,
                    "kind": "companionway",
                    "special": None,
                    "airlock": False,
                    "escape_pod": False,
                    "hatch_links": [],
                    "blocker": None,
                    "activity": None,
                    "equipment": None,
                })
    by_cell = {(room["deck"], room["row"], room["column"]): room for room in rooms}

    def special(deck, row, column, special_id, name, kind):
        room = by_cell[(deck, row, column)]
        room.update(special=special_id, name=name, room_type=MISSION_ROOM_TYPES[special_id], kind=kind)
        return room

    cryo = special(3, 0, 0, "cryo", "Cryogenic Recovery Bay", "medical")
    workshop = special(3, 0, rng.choice((1, 2)), "workshop", "Player Workshop", "damage")
    engine = special(2, 0, 0, "engine", "Main Engine Room", "engineering")
    power = special(2, 1, rng.choice((0, 1)), "power", "Main Power Control", "reactor")
    cic_row = rng.randrange(2)
    cic = special(3, cic_row, 11, "cic", "Combat Information Center", "bridge")
    breach_row = rng.randrange(2)
    breach_column = rng.choice((10, 11))
    if (breach_row, breach_column) == (cic_row, 11):
        breach_row = 1 - cic_row
    breach = special(3, breach_row, breach_column, "breach", "Bloom Impact / Vacuum Breach", "damage")

    seed_room_types(rooms, rng)

    hatches = []
    for upper, lower, ranges in (
        (4, 3, ((3, 6), (8, 10))),
        (3, 2, ((4, 5), (8, 9))),
        (2, 1, ((2, 5), (8, 10))),
    ):
        for low, high in ranges:
            row, column = rng.randrange(2), rng.randint(low, high)
            hatches.append({"upper": upper, "lower": lower, "row": row, "column": column})
            by_cell[(upper, row, column)]["hatch_links"].append(lower)
            by_cell[(lower, row, column)]["hatch_links"].append(upper)

    for deck in range(1, 5):
        for low, high in ((3, 4), (9, 10)):
            by_cell[(deck, rng.randrange(2), rng.randint(low, high))]["airlock"] = True

    pod_candidates = [room for room in rooms if room["column"] >= 9 and not room["special"] and not room["airlock"]]
    rng.shuffle(pod_candidates)
    for room in pod_candidates[: payload["escape_pod_sites"]]:
        room["escape_pod"] = True
        room["kind"] = "escape"

    activity_text = {
        "locked": ("MechanicalOverrideStation", "Crank the manual lock override"),
        "shorted": ("MechanicalOverrideStation", "Isolate the short and bypass the door bus"),
        "debris": ("MechanicalOverrideStation", "Tether and winch the impact debris clear"),
    }
    advanced_equipment = [
        "Arc Cutter", "Seal Drone", "Diagnostic Wand", "Reserve O2 Pack",
        "High-Capacity Power Cell", "Nav Override Key", "Pressure Patch Kit", "Inspection Eye",
    ]
    for deck in range(1, 5):
        candidates = [room for room in rooms if room["deck"] == deck and not room["special"]
                      and not room["airlock"] and not room["escape_pod"]
                      and not (deck == 3 and room["row"] == 0 and room["column"] <= workshop["column"])]
        rng.shuffle(candidates)
        for room in candidates[: payload["room_blockers_per_deck"]]:
            blocker = rng.choice(("locked", "shorted", "debris"))
            room["blocker"] = blocker
            room["activity"] = activity_text[blocker]
            if blocker == "locked":
                room["equipment"] = rng.choice(advanced_equipment)

    cic["blocker"] = "locked"
    cic["activity"] = ("MechanicalOverrideStation", "Restore command bus and release the CIC shutter")
    cic["equipment"] = "Command Authorization Wafer"

    corridor_blocks = []
    for deck in range(1, 5):
        columns = list(range(1, 11))
        if deck == 3:
            columns = [column for column in columns if column > workshop["column"] + 1]
        rng.shuffle(columns)
        for index, column in enumerate(columns[: payload["corridor_blockers_per_deck"]]):
            blocker = rng.choice(("locked", "shorted", "debris"))
            corridor_blocks.append({
                "deck": deck, "column": column, "blocker": blocker,
                "activity": activity_text[blocker][1], "index": index,
            })

    return {
        "seed": seed, "rooms": rooms, "hatches": hatches, "corridor_blocks": corridor_blocks,
        "cryo": cryo, "workshop": workshop, "engine": engine, "power": power, "cic": cic, "breach": breach,
    }


def validate_layout(layout):
    rooms = layout["rooms"]
    if len(rooms) != 96:
        raise RuntimeError(f"Expected 96 rooms, found {len(rooms)}")
    for deck in range(1, 5):
        cells = {(room["row"], room["column"]) for room in rooms if room["deck"] == deck}
        if cells != {(row, column) for row in range(2) for column in range(12)}:
            raise RuntimeError(f"Deck {deck} is not a complete 12 x 2 rectangle")
        if sum(room["airlock"] for room in rooms if room["deck"] == deck) != 2:
            raise RuntimeError(f"Deck {deck} does not have exactly two airlocks")
    if layout["cryo"]["deck"] != 3 or (layout["cryo"]["row"], layout["cryo"]["column"]) != (0, 0):
        raise RuntimeError("Cryo must be aft-port on deck 03")
    if layout["workshop"]["deck"] != 3 or layout["workshop"]["row"] != 0 or layout["workshop"]["column"] > 2:
        raise RuntimeError("Workshop must be accessible within three room positions of cryo")
    if (layout["engine"]["deck"], layout["engine"]["row"], layout["engine"]["column"]) != (2, 0, 0):
        raise RuntimeError("Engine must be directly below cryo")
    if any(link["upper"] == 3 and link["lower"] == 2 and link["column"] < 4 for link in layout["hatches"]):
        raise RuntimeError("A direct cryo-to-engine hatch violates the route constraint")
    if layout["cic"]["deck"] != 3 or layout["cic"]["column"] != 11:
        raise RuntimeError("CIC must be at the nose of a middle deck")
    if layout["breach"]["deck"] != 3 or layout["breach"]["column"] < 10:
        raise RuntimeError("Vacuum breach must be near the CIC")
    pods = [room for room in rooms if room["escape_pod"]]
    if len(pods) != 6 or any(room["column"] < 9 for room in pods):
        raise RuntimeError("Escape pods must use exactly six outer-edge sites at least nine columns forward of cryo")
    if len(layout["hatches"]) != 6:
        raise RuntimeError("Expected two hatch links between every adjacent deck pair")
    required_types = set(MISSION_ROOM_TYPES.values())
    required_types.update(entry["name"] for pool in DECK_ROOM_TYPE_POOLS.values() for entry in pool)
    present_types = {room["room_type"] for room in rooms}
    missing_types = sorted(required_types - present_types)
    if missing_types:
        raise RuntimeError("Missing required Wayfarer sector room types: " + ", ".join(missing_types))
    if None in present_types:
        raise RuntimeError("Every generated room must have a semantic room type")


KIT_DOOR = "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/"
DOORWAY_WIDTH, DOORWAY_HEIGHT = 250.0, 270.0
# The door actor sits 10 below the floor slab's centre; the slab is 20 thick, so the walkable
# floor is 20 above the actor, and the ceiling slab's underside is ROOM_HEIGHT - 20 above that.
DOOR_FLOOR_OFFSET = 20.0


def configure_bulkhead_visuals(door, doorway_width=DOORWAY_WIDTH, floor_offset=DOOR_FLOOR_OFFSET):
    """Gives a placed production bulkhead the kit frame, lintel and leaves it now knows how to fit.

    History, because the previous behaviour was the opposite of this one. BP_Ship_ProductionBulkhead
    used to ship four solid slabs parented at the gap's centre -- a full-size door mesh as the
    "frame", two wall sections as "panels" that opened 135 cm (not enough for a 200 cm panel to
    clear a 250 cm gap), and a leaf never attached to the actor at all -- so every door in the ship
    was a wall: 0 of 96 passable. The first fix hid all of it and let the greybox gap be the door.

    AProductionBulkheadDoor now derives its geometry from the gap and the meshes: the frame is
    scaled to open exactly DoorwayWidth x DoorwayHeight, each leaf covers half and slides fully into
    the wall, the lintel fills up to the ceiling, and only the leaves ever block -- only while
    sealed. So the components come back on, with the kit meshes, and the class does the rest in
    OnConstruction. The Blueprint's stray VisualMesh stays hidden: it is not the door.
    """
    if not hasattr(door, "get_editor_property"):
        return
    try:
        door.set_editor_property("frame_mesh_asset", load_optional(KIT_DOOR + "SM_DOOR_FRAME_01_OUTSIDE"))
        door.set_editor_property("left_leaf_mesh_asset", load_optional(KIT_DOOR + "SM_DOOR_01_LEFT"))
        door.set_editor_property("right_leaf_mesh_asset", load_optional(KIT_DOOR + "SM_DOOR_01_RIGHT"))
        door.set_editor_property("lintel_mesh_asset", load_optional(KIT_DOOR + "SM_DOOR_FRAME_02_UP"))
        door.set_editor_property("doorway_width", doorway_width)
        door.set_editor_property("doorway_height", DOORWAY_HEIGHT)
        door.set_editor_property("ceiling_height", ROOM_HEIGHT - 20.0 - floor_offset)
        door.set_editor_property("floor_offset", floor_offset)
        door.set_editor_property("apply_door_material", False)
    except Exception as error:  # a plain BulkheadDoor fallback has none of these
        unreal.log_warning("Bulkhead visuals not configured on {}: {}".format(door.get_actor_label(), error))
        return
    for component in door.get_components_by_class(unreal.StaticMeshComponent):
        name = component.get_name()
        if name in ("FrameMesh", "LintelMesh", "LeftPanel", "RightPanel"):
            component.set_editor_property("use_default_collision", False)
            component.set_visibility(True)
        elif name == "VisualMesh":
            component.set_editor_property("use_default_collision", False)
            component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            component.set_visibility(False)
    # set_editor_property runs PostEditChangeProperty, which re-runs OnConstruction; a last nudge
    # to a geometry property makes the final pass see every asset set above.
    door.set_editor_property("leaf_slide_margin", 8.0)


def spawn_box(actors, cube, material, location, size, label, rotation=(0.0, 0.0, 0.0), collision=True):
    actor = shared.spawn_box(actors, cube, material, location, size, label, rotation)
    actor.set_editor_property("tags", [unreal.Name("QuickDemoShip"), unreal.Name(label.split("_")[0])])
    if not collision:
        # use_default_collision has to be off first. With it on, the component re-derives its
        # collision from the mesh asset on every load and this NO_COLLISION silently reverted on
        # reload -- which is how every "collision=False" rib ended up standing solid in a doorway.
        actor.static_mesh_component.set_editor_property("use_default_collision", False)
        actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return actor


def spawn_dressing_mesh(actors, mesh, material, location, label, rotation=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0)):
    """Spawn a non-blocking production-kit detail owned by this generated map."""
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(*rotation))
    actor.set_actor_label(f"{PREFIX}{label}")
    actor.set_actor_scale3d(unreal.Vector(*scale))
    actor.set_editor_property("tags", [unreal.Name("QuickDemoShip"), unreal.Name("ConceptDressing")])
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_material(0, material)
    component.set_editor_property("use_default_collision", False)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return actor


def dress_corridor_concept(actors, cube, meshes, materials, deck, z, floor_z, ceiling_z, ship_length):
    """Add the ribbed, service-heavy visual language from the corridor concept art."""
    spawn_box(actors, cube, materials["dark"], (0.0, 0.0, floor_z + 12.0),
              (ship_length - 100.0, 205.0, 4.0), f"ConceptCorridorFloorInset_D{deck:02d}", collision=False)
    for side in (-1.0, 1.0):
        spawn_box(actors, cube, materials["accent"], (0.0, side * 118.0, floor_z + 15.0),
                  (ship_length - 120.0, 10.0, 6.0), f"ConceptCorridorFloorStripe_D{deck:02d}_{side:+.0f}", collision=False)

    for column in range(12):
        x = (column - 5.5) * COLUMN_SPACING
        for side in (-1.0, 1.0):
            spawn_box(actors, cube, materials["dark"], (x, side * (CORRIDOR_WIDTH * 0.5 - 18.0), z),
                      (28.0, 34.0, ROOM_HEIGHT - 28.0),
                      f"ConceptCorridorRib_D{deck:02d}_C{column:02d}_{side:+.0f}", collision=False)
        rib_material = materials["accent"] if column in (0, 5, 11) else materials["dark"]
        spawn_box(actors, cube, rib_material, (x, 0.0, ceiling_z - 28.0),
                  (32.0, CORRIDOR_WIDTH - 20.0, 28.0),
                  f"ConceptCorridorRib_D{deck:02d}_C{column:02d}_Top", collision=False)

    pipe_scale = (ship_length / 400.0, 1.0, 1.0)
    for side in (-1.0, 1.0):
        spawn_dressing_mesh(actors, meshes["pipe"], materials["dark"],
                            (0.0, side * 92.0, ceiling_z - 54.0),
                            f"ConceptCorridorPipe_D{deck:02d}_{side:+.0f}", scale=pipe_scale)


def dress_room_concept(actors, cube, meshes, materials, spec, x, y, z, side, floor_z, ceiling_z, outer_y):
    """Layer deterministic industrial paneling and sparse production props into a room."""
    room_key = spec["deck"] * 100 + spec["row"] * 20 + spec["column"]
    room_dark = materials["cryo_dark"] if spec["special"] == "cryo" else materials["dark"]
    room_deck = materials["cryo_deck"] if spec["special"] == "cryo" else materials["dark"]
    room_accent = materials["cryo_accent"] if spec["special"] == "cryo" else materials["accent"]
    panel_y = outer_y - side * 18.0

    spawn_box(actors, cube, room_deck, (x, y, floor_z + 12.0), (780.0, 500.0, 4.0),
              f"ConceptRoomFloorInset_{spec['code']}", collision=False)
    for stripe in (-1.0, 1.0):
        spawn_box(actors, cube, room_accent, (x, y + stripe * 285.0, floor_z + 15.0), (820.0, 10.0, 6.0),
                  f"ConceptRoomFloorStripe_{spec['code']}_{stripe:+.0f}", collision=False)

    for panel_index, dx in enumerate((-350.0, 0.0, 350.0), start=1):
        panel_material = room_dark if (room_key + panel_index) % 7 == 0 else materials["panel"]
        spawn_box(actors, cube, panel_material, (x + dx, panel_y, z + 18.0), (312.0, 12.0, 244.0),
                  f"ConceptWallPanel_{spec['code']}_{panel_index:02d}", collision=False)
    spawn_box(actors, cube, room_dark, (x, panel_y - side * 2.0, floor_z + 48.0), (1030.0, 14.0, 62.0),
              f"ConceptKickplate_{spec['code']}", collision=False)
    spawn_box(actors, cube, room_accent, (x, panel_y - side * 4.0, z + 148.0), (1010.0, 18.0, 22.0),
              f"ConceptUtilityRail_{spec['code']}", collision=False)

    wear_x = x + (-270.0 if room_key % 2 else 260.0)
    spawn_box(actors, cube, room_dark, (wear_x, panel_y - side * 9.0, z + (-35.0 if room_key % 3 else 62.0)),
              (138.0, 7.0, 74.0), f"ConceptWearPatch_{spec['code']}",
              (0.0, 0.0, -4.0 if room_key % 2 else 5.0), False)

    for rib_index, dx in enumerate((-510.0, 510.0), start=1):
        spawn_box(actors, cube, room_dark, (x + dx, outer_y - side * 42.0, z),
                  (30.0, 64.0, ROOM_HEIGHT - 24.0),
                  f"ConceptCornerRib_{spec['code']}_{rib_index:02d}", collision=False)
    spawn_box(actors, cube, room_dark, (x, outer_y - side * 42.0, ceiling_z - 28.0),
              (1035.0, 64.0, 28.0), f"ConceptCeilingBeam_{spec['code']}", collision=False)

    pipe_scale = (2.35, 1.0, 1.0)
    for pipe_index, inward in enumerate((122.0, 184.0), start=1):
        pipe_material = room_accent if pipe_index == 2 and room_key % 4 == 0 else room_dark
        spawn_dressing_mesh(actors, meshes["pipe"], pipe_material,
                            (x, outer_y - side * inward, ceiling_z - 55.0),
                            f"ConceptCeilingPipe_{spec['code']}_{pipe_index:02d}", scale=pipe_scale)

    facing_yaw = 180.0 if side < 0.0 else 0.0
    prop_mesh = {
        "bridge": meshes["terminal"], "sensors": meshes["terminal"],
        "medical": meshes["locker"], "crew": meshes["locker"],
        "cargo": meshes["crate"], "escape": meshes["locker"], "armory": meshes["locker"],
        "damage": meshes["junction"], "engineering": meshes["junction"],
        "reactor": meshes["junction"], "companionway": meshes["junction"],
    }[spec["kind"]]
    spawn_dressing_mesh(actors, prop_mesh, room_accent if room_key % 5 == 0 else room_dark,
                        (x + (-320.0 if room_key % 2 else 320.0), outer_y - side * 62.0, floor_z + 11.0),
                        f"ConceptUtilityProp_{spec['code']}", rotation=(0.0, facing_yaw, 0.0))
    spawn_dressing_mesh(actors, meshes["fixture"], room_dark,
                        (x, y, ceiling_z - 28.0), f"ConceptLightFixture_{spec['code']}")

    if spec["special"] == "cic":
        for index, dx in enumerate((-250.0, 0.0, 250.0), start=1):
            spawn_dressing_mesh(actors, meshes["seat"], room_dark,
                                (x + dx, y - side * 70.0, floor_z + 10.0),
                                f"ConceptSpecialProp_CIC_{index:02d}", rotation=(0.0, facing_yaw, 0.0))
    elif spec["special"] == "workshop":
        for index, dx in enumerate((-280.0, 0.0, 280.0), start=1):
            mesh = meshes["crate"] if index == 2 else meshes["locker"]
            spawn_dressing_mesh(actors, mesh, room_accent if index == 2 else room_dark,
                                (x + dx, outer_y - side * 125.0, floor_z + 10.0),
                                f"ConceptSpecialProp_Workshop_{index:02d}", rotation=(0.0, facing_yaw, 0.0))
    elif spec["special"] in ("engine", "power"):
        count = 2 if spec["special"] == "engine" else 3
        for index in range(count):
            dx = (index - (count - 1) * 0.5) * 250.0
            spawn_dressing_mesh(actors, meshes["junction"], room_accent,
                                (x + dx, outer_y - side * 118.0, floor_z + 10.0),
                                f"ConceptSpecialProp_{spec['special'].title()}_{index + 1:02d}",
                                rotation=(0.0, facing_yaw, 0.0))
    elif spec["special"] == "breach":
        bloom_specs = (("bloom_nodule", materials["bloom_wet"], (-260.0, -150.0, 42.0), (0.9, 0.9, 0.9)),
                       ("bloom_tendril", materials["bloom_wet"], (60.0, -190.0, 28.0), (1.1, 1.1, 1.1)),
                       ("bloom_rib", materials["bloom_calcified"], (285.0, -130.0, 75.0), (0.85, 0.85, 0.85)))
        for index, (mesh_name, bloom_material, offset, scale) in enumerate(bloom_specs, start=1):
            spawn_dressing_mesh(actors, meshes[mesh_name], bloom_material,
                                (x + offset[0], y + side * abs(offset[1]), floor_z + offset[2]),
                                f"ConceptSpecialProp_Breach_{index:02d}",
                                rotation=(0.0, (room_key * 37 + index * 41) % 360, 0.0), scale=scale)


def spawn_equipment(actors, room, name, location, mesh, ordinal):
    pickup = actors.spawn_actor_from_class(unreal.EquipmentPickup, unreal.Vector(*location), unreal.Rotator())
    pickup.set_actor_label(f"{PREFIX}Equipment_{room['code']}_{ordinal:02d}_{name.replace(' ', '')}")
    item = unreal.EquipmentItem()
    item.set_editor_property("display_name", name)
    item.set_editor_property("description", f"Seeded ship equipment recovered from {room['name']}.")
    type_name, slot_name = {
        "Utility Light": ("HELMET_VISOR", "HEAD"),
        "Hand Pry": ("ARMOR_PLATING", "ARMS"),
        "Patch Foam": ("PRESSURE_SEAL", "CHEST"),
        "Tether Spool": ("THERMAL_PLATING", "ACCESSORY"),
    }.get(name, ("PRESSURE_SEAL", "ACCESSORY"))
    item.set_editor_property("type", enum_value(unreal.EquipmentType, type_name))
    item.set_editor_property("slot", enum_value(unreal.EquipmentSlot, slot_name))
    pickup.set_editor_property("equipment_item", item)
    pickup.get_editor_property("visual_mesh").set_static_mesh(mesh)
    pickup.set_actor_scale3d(unreal.Vector(0.28, 0.28, 0.28))
    pickup.set_editor_property("tags", [unreal.Name("SeededEquipment"), unreal.Name(room["code"])])
    return pickup


def spawn_objective_beacon(actors, room, objective_id, label, x, inner_y, floor_z, side):
    """Place a non-lighting mission breadcrumb just inside the room threshold."""
    beacon = actors.spawn_actor_from_class(
        unreal.QuickDemoObjectiveBeacon,
        unreal.Vector(x, inner_y + side * 95.0, floor_z + 145.0),
        unreal.Rotator(pitch=0.0, yaw=90.0 if side < 0.0 else -90.0, roll=0.0))
    beacon.set_actor_label(f"{PREFIX}ObjectiveBeacon_{objective_id}_{room['code']}")
    beacon.set_editor_property("objective_id", unreal.Name(objective_id))
    beacon.set_editor_property("marker_label", label)
    beacon.set_editor_property("tags", [unreal.Name("QuickDemoGameplay"), unreal.Name("ObjectiveBeacon")])
    return beacon


def spawn_aperture_slab(actors, cube, material, center, z, label):
    """Build a deck slab around a compact zero-g hatch opening."""
    cx, cy = center
    full_x, full_y = ROOM_SIZE[0], ROOM_SIZE[1]
    opening_x, opening_y = 700.0, 360.0
    side_y = (full_y - opening_y) * 0.5
    end_x = (full_x - opening_x) * 0.5
    shared.spawn_box(actors, cube, material, (cx, cy - (opening_y + side_y) * 0.5, z), (full_x, side_y, 20.0), label + "_Port")
    shared.spawn_box(actors, cube, material, (cx, cy + (opening_y + side_y) * 0.5, z), (full_x, side_y, 20.0), label + "_Starboard")
    shared.spawn_box(actors, cube, material, (cx - (opening_x + end_x) * 0.5, cy, z), (end_x, opening_y, 20.0), label + "_Aft")
    shared.spawn_box(actors, cube, material, (cx + (opening_x + end_x) * 0.5, cy, z), (end_x, opening_y, 20.0), label + "_Forward")


def spawn_hatch_ramp(actors, cube, deck_material, accent_material, lower_spec, upper_spec):
    """Add a traversal rail and pull holds between paired hatch rooms."""
    x, y, lower_z = room_location(lower_spec)
    _, _, upper_z = room_location(upper_spec)
    rise = upper_z - lower_z
    run = 700.0
    length = math.sqrt(run * run + rise * rise)
    pitch = -math.degrees(math.atan2(rise, run))
    mid_z = lower_z - ROOM_SIZE[2] * 0.5 + rise * 0.5
    ramp = shared.spawn_box(actors, cube, deck_material, (x, y, mid_z), (length, 280.0, 24.0), f"HatchRamp_{lower_spec['code']}_{upper_spec['code']}", (pitch, 0.0, 0.0))
    ramp.set_editor_property("tags", [unreal.Name("VerticalTraversal"), unreal.Name("ZeroGPullRoute")])
    for side in (-1.0, 1.0):
        shared.spawn_box(actors, cube, accent_material, (x, y + side * 170.0, mid_z + 45.0), (length, 16.0, 16.0), f"HatchRail_{lower_spec['code']}_{side:+.0f}", (pitch, 0.0, 0.0))
    for step in range(6):
        z = lower_z - ROOM_SIZE[2] * 0.5 + 65.0 + step * (rise / 6.0)
        hold = shared.spawn_box(actors, cube, accent_material, (x, y - 225.0, z), (90.0, 18.0, 18.0), f"PullHold_{lower_spec['code']}_{step:02d}")
        hold.set_editor_property("tags", [unreal.Name("ZeroGPullHold"), unreal.Name(lower_spec["code"]), unreal.Name(upper_spec["code"])])


def make_room_profile(kind):
    values = shared.PROFILES[kind]
    profile = unreal.ShipRoomGameplayProfile()
    for prop, value in zip(("power_priority", "nominal_power_draw", "safe_occupancy", "hazard_tier", "loot_tier"), values[:5]):
        profile.set_editor_property(prop, value)
    profile.set_editor_property("access_tier", enum_value(unreal.ShipRoomAccessTier, values[5]))
    profile.set_editor_property("critical_for_jump", values[6])
    return profile


def build_level(layout):
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        if not levels.load_level(MAP_PATH):
            raise RuntimeError("Could not load existing quick-demo map")
        prior = [actor for actor in actors.get_all_level_actors() if actor.get_actor_label().startswith(PREFIX)]
        if prior:
            actors.destroy_actors(prior)
    elif not levels.new_level(MAP_PATH):
        raise RuntimeError("Could not create quick-demo map")

    required_gameplay_classes = (
        "QuickDemoMissionDirector",
        "QuickDemoObjectiveBeacon",
        "QuickDemoObjectiveTrigger",
        "QuickDemoSuitStation",
        "QuickDemoPowerStation",
        "QuickDemoBreachStation",
        "QuickDemoCICAccessStation",
        "QuickDemoCICConsole",
    )
    missing_classes = [name for name in required_gameplay_classes if not getattr(unreal, name, None)]
    if missing_classes:
        raise RuntimeError(
            "Quick-demo gameplay classes are not reflected; rebuild GinnungagapEditor: "
            + ", ".join(missing_classes)
        )

    cube = load_required("/Engine/BasicShapes/Cube.Cube")
    materials = {
        "hull": ensure_large_panel_bulkhead_material(),
        "panel": load_required("/Game/Assets/Ships/Production/Materials/M_Ship_Hull_OffWhite"),
        "deck": load_required("/Game/Assets/Materials/M_ShipDeck_NonSlip"),
        "dark": load_required("/Game/Assets/Ships/Production/Materials/M_Ship_Structure_Gunmetal"),
        "accent": load_required("/Game/Assets/Materials/M_ShipUtility_Hazard"),
        "cryo_dark": load_required("/Game/Assets/ShipRooms/Cryo/M_Cryo_WornGunmetal"),
        "cryo_deck": load_required("/Game/Assets/ShipRooms/Cryo/M_Cryo_WetDeck"),
        "cryo_accent": load_required("/Game/Assets/ShipRooms/Cryo/M_Cryo_AmberPractical"),
        "bloom_wet": load_required("/Game/Assets/Ships/Production/Materials/M_Bloom_ColonyWet"),
        "bloom_calcified": load_required("/Game/Assets/Ships/Production/Materials/M_Bloom_AdvancedCalcified"),
    }
    terminal_mesh = load_required("/Game/Assets/Ships/Production/Meshes/SM_Prop_WallTerminal")
    concept_meshes = {
        "terminal": terminal_mesh,
        "locker": load_required("/Game/Assets/Ships/Production/Meshes/SM_Prop_Locker"),
        "junction": load_required("/Game/Assets/Ships/Production/Meshes/SM_Prop_PowerJunction"),
        "pipe": load_required("/Game/Assets/Ships/Production/Meshes/SM_Prop_PipeStraight"),
        "fixture": load_required("/Game/Assets/Ships/Production/Meshes/SM_Prop_LightFixture"),
        "crate": load_required("/Game/Assets/Ships/Production/Meshes/SM_Prop_CargoCrate"),
        "seat": load_required("/Game/Assets/Ships/Production/Meshes/SM_Prop_CrashSeat"),
        "bloom_nodule": load_required("/Game/Assets/Ships/Production/Meshes/SM_FX_BloomNodule"),
        "bloom_tendril": load_required("/Game/Assets/Ships/Production/Meshes/SM_FX_BloomTendril"),
        "bloom_rib": load_required("/Game/Assets/Ships/Production/Meshes/SM_FX_BloomCalcifiedRib"),
    }
    crate_mesh = load_required("/Game/Ice_Station/Meshes/Crates/SM_crate_04")
    generator_mesh = load_required("/Game/Ice_Station/Meshes/interior/SM_generator")
    pod_mesh = load_optional("/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Container/SM_container_white") or crate_mesh
    bulkhead_asset = load_optional("/Game/Assets/Ships/Production/Blueprints/BP_Ship_ProductionBulkhead")
    bulkhead_class = bulkhead_asset.generated_class() if bulkhead_asset else unreal.BulkheadDoor

    mission_director = actors.spawn_actor_from_class(
        unreal.QuickDemoMissionDirector, unreal.Vector(0.0, 0.0, DECK_Z[3]), unreal.Rotator())
    mission_director.set_actor_label(f"{PREFIX}MissionDirector")
    mission_director.set_editor_property("tags", [unreal.Name("QuickDemoGameplay"), unreal.Name("MissionDirector")])

    by_code = {room["code"]: room for room in layout["rooms"]}
    hatch_rooms = defaultdict(list)
    for link in layout["hatches"]:
        hatch_rooms[room_code(link["upper"], link["row"], link["column"])].append(link["lower"])
        hatch_rooms[room_code(link["lower"], link["row"], link["column"])].append(link["upper"])

    corridor_sections = {}
    ship_length = 12 * COLUMN_SPACING
    for deck in range(1, 5):
        z = DECK_Z[deck]
        floor_z = z - ROOM_HEIGHT * 0.5 + 10.0
        ceiling_z = z + ROOM_HEIGHT * 0.5 - 10.0
        corridor = actors.spawn_actor_from_class(unreal.ShipSection, unreal.Vector(0.0, 0.0, z), unreal.Rotator())
        corridor.set_actor_label(f"{PREFIX}PrimaryCorridor_D{deck:02d}")
        corridor.set_editor_property("section_id", 9000 + deck)
        corridor.set_editor_property("section_type", enum_value(unreal.ShipSectionType, "CORRIDOR"))
        corridor.get_editor_property("section_bounds").set_box_extent(unreal.Vector(ship_length * 0.5, CORRIDOR_WIDTH * 0.5, ROOM_HEIGHT * 0.5))
        corridor.set_editor_property("tags", [unreal.Name("PrimaryCorridor"), unreal.Name("QuickDemoShip")])
        corridor_sections[deck] = corridor
        spawn_box(actors, cube, materials["deck"], (0.0, 0.0, floor_z), (ship_length, CORRIDOR_WIDTH, 20.0), f"CorridorFloor_D{deck:02d}")
        spawn_box(actors, cube, materials["dark"], (0.0, 0.0, ceiling_z), (ship_length, CORRIDOR_WIDTH, 20.0), f"CorridorCeiling_D{deck:02d}")
        spawn_box(actors, cube, materials["hull"], (-ship_length * 0.5, 0.0, z), (24.0, CORRIDOR_WIDTH, ROOM_HEIGHT), f"CorridorAftCap_D{deck:02d}")
        spawn_box(actors, cube, materials["hull"], (ship_length * 0.5, 0.0, z), (24.0, CORRIDOR_WIDTH, ROOM_HEIGHT), f"CorridorNoseCap_D{deck:02d}")
        dress_corridor_concept(actors, cube, concept_meshes, materials, deck, z, floor_z, ceiling_z, ship_length)

        for column in range(0, 12, 2):
            light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector((column - 5.5) * COLUMN_SPACING, 0.0, z + 70.0), unreal.Rotator())
            light.set_actor_label(f"{PREFIX}CorridorLight_D{deck:02d}_{column:02d}")
            light.set_editor_property("tags", [unreal.Name("QuickDemoUtilityLight"), unreal.Name("QuickDemoShip")])
            component = light.get_component_by_class(unreal.PointLightComponent)
            component.set_editor_property("intensity", 0.0)
            component.set_editor_property("attenuation_radius", 900.0)
            component.set_visibility(False)

    room_actors = {}
    doors = {}
    for spec in layout["rooms"]:
        x, y, z = room_location(spec)
        side = -1.0 if spec["row"] == 0 else 1.0
        floor_z = z - ROOM_HEIGHT * 0.5 + 10.0
        ceiling_z = z + ROOM_HEIGHT * 0.5 - 10.0
        inner_y = side * CORRIDOR_WIDTH * 0.5
        outer_y = side * (CORRIDOR_WIDTH * 0.5 + ROOM_SIZE[1])
        has_floor_hatch = any(target < spec["deck"] for target in hatch_rooms[spec["code"]])
        has_ceiling_hatch = any(target > spec["deck"] for target in hatch_rooms[spec["code"]])

        if has_floor_hatch:
            spawn_aperture_slab(actors, cube, materials["deck"], (x, y), floor_z, f"Floor_{spec['code']}")
        else:
            spawn_box(actors, cube, materials["deck"], (x, y, floor_z), (ROOM_SIZE[0], ROOM_SIZE[1], 20.0), f"Floor_{spec['code']}")
        if has_ceiling_hatch:
            spawn_aperture_slab(actors, cube, materials["dark"], (x, y), ceiling_z, f"Ceiling_{spec['code']}")
        else:
            spawn_box(actors, cube, materials["dark"], (x, y, ceiling_z), (ROOM_SIZE[0], ROOM_SIZE[1], 20.0), f"Ceiling_{spec['code']}")

        sockets = ["STARBOARD" if spec["row"] == 0 else "PORT"]
        if spec["airlock"]:
            sockets.append("PORT" if spec["row"] == 0 else "STARBOARD")
        if has_floor_hatch: sockets.append("DOWN")
        if has_ceiling_hatch: sockets.append("UP")

        room = actors.spawn_actor_from_class(unreal.ModularShipRoom, unreal.Vector(x, y, z), unreal.Rotator())
        room.set_actor_label(f"{PREFIX}Room_{spec['code']}")
        room.set_editor_property("room_code", spec["code"])
        room.set_editor_property("display_name", spec["name"])
        room.set_editor_property("archetype", enum_value(unreal.ShipRoomArchetype, shared.ARCHETYPES[spec["kind"]]))
        section_name = "AIRLOCK" if spec["airlock"] else "BRIDGE" if spec["kind"] == "bridge" else "ENGINE_ROOM" if spec["kind"] in ("engineering", "reactor") else "MED_BAY" if spec["kind"] == "medical" else "DECK"
        room.set_editor_property("section_type", enum_value(unreal.ShipSectionType, section_name))
        room.set_editor_property("module_size", unreal.Vector(*ROOM_SIZE))
        room.get_editor_property("section_bounds").set_box_extent(unreal.Vector(ROOM_SIZE[0] * 0.5, ROOM_SIZE[1] * 0.5, ROOM_HEIGHT * 0.5))
        room.set_editor_property("enabled_sockets", [enum_value(unreal.ShipRoomSocket, name) for name in sockets])
        room.set_editor_property("gameplay_profile", make_room_profile(spec["kind"]))
        room.set_editor_property("powered", spec["special"] == "cryo")
        room.set_editor_property("operational_state", enum_value(unreal.ShipRoomOperationalState, "ALERT" if spec["special"] == "cryo" else "UNPOWERED"))
        room.set_editor_property("tags", [
            unreal.Name("QuickDemoShipRoom"), unreal.Name(spec["code"]),
            unreal.Name(spec["special"] or "StandardRoom"),
            unreal.Name("RoomType_" + room_type_slug(spec["room_type"])),
        ])
        room_actors[spec["code"]] = room

        door_gap, segment = 250.0, (ROOM_SIZE[0] - 250.0) * 0.5
        offset = door_gap * 0.5 + segment * 0.5
        for direction in (-1.0, 1.0):
            spawn_box(actors, cube, materials["hull"], (x + direction * offset, inner_y, z), (segment, 24.0, ROOM_HEIGHT), f"InnerWall_{spec['code']}_{direction:+.0f}")
        spawn_box(actors, cube, materials["hull"], (x - ROOM_SIZE[0] * 0.5, y, z), (24.0, ROOM_SIZE[1], ROOM_HEIGHT), f"AftWall_{spec['code']}")
        if spec["column"] == 11:
            spawn_box(actors, cube, materials["hull"], (x + ROOM_SIZE[0] * 0.5, y, z), (24.0, ROOM_SIZE[1], ROOM_HEIGHT), f"NoseWall_{spec['code']}")
        if spec["special"] == "breach":
            spawn_box(actors, cube, materials["accent"], (x - 340.0, outer_y, z + 40.0), (260.0, 30.0, 210.0), f"BreachFragmentA_{spec['code']}", (14.0, 0.0, 22.0), False)
            spawn_box(actors, cube, materials["accent"], (x + 350.0, outer_y, z - 55.0), (240.0, 26.0, 180.0), f"BreachFragmentB_{spec['code']}", (-18.0, 0.0, -15.0), False)
        elif spec["airlock"]:
            for direction in (-1.0, 1.0):
                spawn_box(actors, cube, materials["hull"], (x + direction * offset, outer_y, z), (segment, 24.0, ROOM_HEIGHT), f"OuterWall_{spec['code']}_{direction:+.0f}")
        else:
            spawn_box(actors, cube, materials["hull"], (x, outer_y, z), (ROOM_SIZE[0], 24.0, ROOM_HEIGHT), f"OuterWall_{spec['code']}")

        dress_room_concept(actors, cube, concept_meshes, materials, spec, x, y, z, side, floor_z, ceiling_z, outer_y)

        door = actors.spawn_actor_from_class(bulkhead_class, unreal.Vector(x, inner_y, floor_z - 10.0), unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
        door.set_actor_label(f"{PREFIX}Door_{spec['code']}")
        configure_bulkhead_visuals(door)
        door_tags = [unreal.Name("RoomThresholdDoor"), unreal.Name(spec["code"]), unreal.Name(spec["blocker"] or "Clear")]
        if spec["special"] == "cic":
            door_tags.append(unreal.Name("QuickDemoCICDoor"))
        door.set_editor_property("tags", door_tags)
        door.configure_threshold_sides(room, corridor_sections[spec["deck"]])
        if spec["blocker"]:
            door.seal()
        doors[spec["code"]] = door

        # LinearColor, not unreal.Color, and the reason is a bug this line shipped with.
        #
        # unreal.Color's positional constructor is (B, G, R, A), not (R, G, B, A). The old code read
        # `unreal.Color(255, 70, 35)` for the cryo bay -- plainly meant as a red-orange emergency
        # light -- and put (35, 70, 255) into the map: saturated blue. The other branch had the same
        # fault, asking for cool white (185, 220, 235) and getting warm cream (235, 220, 185); it went
        # unnoticed only because those lights are spawned at intensity 0.
        #
        # That inversion is what made the cryo hero shot blue. Measuring the shot found a population
        # at RGB (0.044, 0.086, 0.568) -- blue 6.6x green -- on the floor rather than on the pods,
        # and this was the only saturated source in the room.
        #
        # set_light_color takes a LinearColor and has no channel-order trap, so the values below say
        # what they mean.
        #
        # Amber rather than the original red: (1.0, 0.749, 0.486) is the emergency-fixture colour the
        # corridors already use, so the cryo practical now speaks the ship's existing visual language
        # instead of introducing a third hue. Sheet 11's cryo bay is near-neutral -- mean RGB
        # (0.175, 0.174, 0.184), blue-minus-red +0.009 -- so what that room wants is a restrained
        # warm accent against its pale key lights, not a saturated wash of any colour.
        colour = (unreal.LinearColor(1.0, 0.749, 0.486, 1.0) if spec["special"] == "cryo"
                  else unreal.LinearColor(0.725, 0.863, 0.922, 1.0))
        light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x, y, z + 55.0), unreal.Rotator())
        light.set_actor_label(f"{PREFIX}RoomLight_{spec['code']}")
        component = light.get_component_by_class(unreal.PointLightComponent)
        component.set_editor_property("attenuation_radius", 650.0)
        component.set_light_color(colour)
        if spec["special"] == "cryo":
            component.set_editor_property("intensity", 180.0)
            light.set_editor_property("tags", [unreal.Name("QuickDemoEmergencyLight"), unreal.Name(spec["code"])])
        else:
            component.set_editor_property("intensity", 0.0)
            component.set_visibility(False)
            light.set_editor_property("tags", [unreal.Name("QuickDemoUtilityLight"), unreal.Name(spec["code"])])
        room.set_editor_property("identity_light", light)

        # Beside the door frame on the corridor face, clear of the frame's 30 cm protrusion, at a
        # height a first-person camera reads without looking up. A text render's glyphs face its
        # local +X, so yaw 90 faces +Y: toward the corridor for a row-0 room, whose wall is at -Y.
        sign = actors.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(x - 215.0, inner_y - side * 42.0, z + 30.0), unreal.Rotator(pitch=0.0, yaw=90.0 if spec["row"] == 0 else -90.0, roll=0.0))
        sign.set_actor_label(f"{PREFIX}Sign_{spec['code']}")
        text = sign.get_component_by_class(unreal.TextRenderComponent)
        text.set_editor_property("text", f"{spec['code']} // {spec['name'].upper()}")
        text.set_editor_property("world_size", 20.0 if spec["special"] else 14.0)
        text.set_editor_property("text_render_color", unreal.Color(r=120, g=226, b=211) if spec["special"] else unreal.Color(r=95, g=110, b=115))
        room.set_editor_property("code_sign", sign)

    for spec in layout["rooms"]:
        x, y, z = room_location(spec)
        side = -1.0 if spec["row"] == 0 else 1.0
        floor_z = z - ROOM_HEIGHT * 0.5
        room = room_actors[spec["code"]]

        if spec["blocker"]:
            station_class = unreal.QuickDemoCICAccessStation if spec["special"] == "cic" else unreal.MechanicalOverrideStation
            station = actors.spawn_actor_from_class(station_class, unreal.Vector(x + 190.0, side * (CORRIDOR_WIDTH * 0.5 - 55.0), floor_z + 100.0), unreal.Rotator(pitch=0.0, yaw=0.0 if side < 0 else 180.0, roll=0.0))
            station.set_actor_label(f"{PREFIX}BlockActivity_{spec['code']}_{spec['blocker'].title()}")
            station.set_editor_property("target_actor", doors[spec["code"]])
            station.set_editor_property("cooldown_seconds", 2.0)
            station.get_editor_property("mesh").set_static_mesh(terminal_mesh)
            activity = station.get_editor_property("activity")
            activity.set_editor_property("display_name", spec["activity"][1])
            station.set_editor_property("activity", activity)
            station.configure_procedural_station(unreal.Name(f"{spec['code']}-BLOCK"), unreal.Name(spec["code"]), layout["seed"], 0, enum_value(unreal.ActivityStationMount, "WALL_PANEL"), enum_value(unreal.ActivityStationCondition, "FAULTED"), enum_value(unreal.ActivityStationRarity, "SPECIALIZED"), 0.35, 1)
            room.set_editor_property("maintenance_anchor", station)
        if spec["equipment"]:
            pickup = spawn_equipment(actors, spec, spec["equipment"], (x, y + side * 260.0, floor_z + 55.0), crate_mesh, 1)
            room.set_editor_property("loot_anchor", pickup)

        if spec["special"] == "cryo":
            # Row 0's outer hull is on negative Y. The pod's opening face is local
            # +Y at yaw 0, so turn it around to open toward the outer wall.
            pod_rotation = unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0)
            suit_roles = ("CREW", "ENGINEERING", "MEDICAL", "SECURITY")
            for index in range(4):
                px = x - 360.0 + index * 240.0
                system = actors.spawn_actor_from_class(unreal.CryoPodSystem, unreal.Vector(px, y - 180.0, floor_z + 22.0), pod_rotation)
                system.set_actor_label(f"{PREFIX}CryoPod_{index + 1:02d}")
                suit_station = actors.spawn_actor_from_class(
                    unreal.QuickDemoSuitStation,
                    unreal.Vector(px, y + 230.0, floor_z + 100.0),
                    unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0))
                suit_station.set_actor_label(f"{PREFIX}SuitStation_{index + 1:02d}")
                suit_station.get_editor_property("mesh").set_static_mesh(concept_meshes["locker"])
                suit_station.set_editor_property(
                    "suit_role", enum_value(unreal.PressureSuitRole, suit_roles[index]))
                suit_station.set_editor_property(
                    "tags", [unreal.Name("QuickDemoGameplay"), unreal.Name("CryoSuitStation")])
            spawn_objective_beacon(
                actors, spec, "QD_SuitUp", "SUIT STATIONS", x, side * CORRIDOR_WIDTH * 0.5,
                floor_z, side)
        elif spec["special"] == "workshop":
            trigger = actors.spawn_actor_from_class(
                unreal.QuickDemoObjectiveTrigger, unreal.Vector(x, y, z), unreal.Rotator())
            trigger.set_actor_label(f"{PREFIX}WorkshopObjectiveTrigger")
            trigger.set_editor_property("objective_id", unreal.Name("QD_ReachWorkshop"))
            trigger.get_editor_property("trigger_bounds").set_box_extent(unreal.Vector(420.0, 340.0, 150.0))
            for index, name in enumerate(("Utility Light", "Hand Pry", "Patch Foam", "Tether Spool")):
                spawn_equipment(actors, spec, name, (x - 330.0 + index * 220.0, y, floor_z + 55.0), crate_mesh, index + 1)
            spawn_objective_beacon(
                actors, spec, "QD_ReachWorkshop", "STARTER WORKSHOP", x,
                side * CORRIDOR_WIDTH * 0.5, floor_z, side)
        elif spec["special"] == "engine":
            for index, dx in enumerate((-260.0, 0.0, 260.0), start=1):
                prop = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x + dx, y, floor_z + 30.0), unreal.Rotator())
                prop.set_actor_label(f"{PREFIX}EngineMachinery_{index:02d}")
                prop.static_mesh_component.set_static_mesh(generator_mesh)
                prop.set_actor_scale3d(unreal.Vector(0.24, 0.24, 0.24))
        elif spec["special"] == "power":
            station = actors.spawn_actor_from_class(unreal.QuickDemoPowerStation, unreal.Vector(x, y, floor_z + 90.0), unreal.Rotator())
            station.set_actor_label(f"{PREFIX}PowerRestoreStation")
            station.set_editor_property("target_actor", room)
            station.get_editor_property("mesh").set_static_mesh(terminal_mesh)
            station.configure_procedural_station(unreal.Name("QD-POWER-MAIN"), unreal.Name(spec["code"]), layout["seed"], 0, enum_value(unreal.ActivityStationMount, "FLOOR_CONSOLE"), enum_value(unreal.ActivityStationCondition, "FAULTED"), enum_value(unreal.ActivityStationRarity, "CRITICAL"), 0.2, 1)
            room.set_editor_property("system_anchor", station)
            spawn_objective_beacon(
                actors, spec, "QD_RestorePower", "MAIN POWER", x,
                side * CORRIDOR_WIDTH * 0.5, floor_z, side)
        elif spec["special"] == "breach":
            hazard = actors.spawn_actor_from_class(unreal.HazardZoneActor, unreal.Vector(x, y, z), unreal.Rotator())
            hazard.set_actor_label(f"{PREFIX}VacuumHazard_{spec['code']}")
            hazard.set_editor_property("tags", [unreal.Name("QuickDemoVacuumHazard"), unreal.Name(spec["code"])])
            state = unreal.PhysicsEnvironmentState()
            state.set_editor_property("ambient_pressure_k_pa", 0.25)
            state.set_editor_property("gravity_multiplier", 0.05)
            state.set_editor_property("vacuum_zone", True)
            state.set_editor_property("microgravity_zone", True)
            state.set_editor_property("temperature_c", -90.0)
            hazard.set_editor_property("environment_state", state)
            hazard.get_editor_property("zone_bounds").set_box_extent(unreal.Vector(ROOM_SIZE[0] * 0.6, ROOM_SIZE[1] * 0.75, ROOM_HEIGHT * 0.5))
            warning = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x, y, z + 40.0), unreal.Rotator())
            warning.set_actor_label(f"{PREFIX}BreachWarningLight")
            warning_component = warning.get_component_by_class(unreal.PointLightComponent)
            warning_component.set_editor_property("intensity", 0.0)
            warning_component.set_editor_property("attenuation_radius", 950.0)
            warning_component.set_editor_property("light_color", unreal.Color(r=255, g=20, b=8))
            warning_component.set_visibility(False)
            warning.set_editor_property("tags", [unreal.Name("QuickDemoUtilityLight"), unreal.Name(spec["code"])])
            patch = actors.spawn_actor_from_class(unreal.QuickDemoBreachStation, unreal.Vector(x - 260.0, y - side * 250.0, floor_z + 90.0), unreal.Rotator())
            patch.set_actor_label(f"{PREFIX}BreachPatchActivity")
            patch.set_editor_property("target_actor", hazard)
            patch.get_editor_property("mesh").set_static_mesh(terminal_mesh)
            patch.configure_procedural_station(unreal.Name("QD-BREACH-PATCH"), unreal.Name(spec["code"]), layout["seed"], 0, enum_value(unreal.ActivityStationMount, "WALL_PANEL"), enum_value(unreal.ActivityStationCondition, "BLOOM_TOUCHED"), enum_value(unreal.ActivityStationRarity, "CRITICAL"), 0.25, 1)
            spawn_objective_beacon(
                actors, spec, "QD_SealBreach", "VACUUM BREACH", x,
                side * CORRIDOR_WIDTH * 0.5, floor_z, side)

        if spec["special"] == "cic":
            console = actors.spawn_actor_from_class(
                unreal.QuickDemoCICConsole, unreal.Vector(x, y + side * 245.0, floor_z + 90.0),
                unreal.Rotator(pitch=0.0, yaw=90.0 if side < 0.0 else -90.0, roll=0.0))
            console.set_actor_label(f"{PREFIX}CICMissionConsole")
            console.get_editor_property("mesh").set_static_mesh(terminal_mesh)
            console.configure_procedural_station(unreal.Name("QD-CIC-CONSOLE"), unreal.Name(spec["code"]), layout["seed"], 0, enum_value(unreal.ActivityStationMount, "FLOOR_CONSOLE"), enum_value(unreal.ActivityStationCondition, "FAULTED"), enum_value(unreal.ActivityStationRarity, "CRITICAL"), 0.3, 1)
            room.set_editor_property("system_anchor", console)
            spawn_objective_beacon(
                actors, spec, "QD_ReachCIC", "CIC TACTICAL CONSOLE", x,
                side * CORRIDOR_WIDTH * 0.5, floor_z, side)

        if spec["airlock"]:
            outer_y = side * (CORRIDOR_WIDTH * 0.5 + ROOM_SIZE[1])
            door = actors.spawn_actor_from_class(bulkhead_class, unreal.Vector(x, outer_y, floor_z), unreal.Rotator())
            door.set_actor_label(f"{PREFIX}Airlock_{spec['code']}")
            neutralise_bulkhead_slabs(door)
            station = actors.spawn_actor_from_class(unreal.AirlockRepressurizationStation, unreal.Vector(x + 190.0, outer_y - side * 80.0, floor_z + 100.0), unreal.Rotator())
            station.set_actor_label(f"{PREFIX}AirlockActivity_{spec['code']}")
            station.set_editor_property("target_actor", door)
            station.get_editor_property("mesh").set_static_mesh(terminal_mesh)

        if spec["escape_pod"]:
            pod = actors.spawn_actor_from_class(unreal.EscapePodSystem, unreal.Vector(x, y + side * 260.0, floor_z + 45.0), unreal.Rotator())
            pod.set_actor_label(f"{PREFIX}EscapePod_{spec['code']}")
            visual = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y + side * 290.0, floor_z + 70.0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0))
            visual.set_actor_label(f"{PREFIX}EscapePodVisual_{spec['code']}")
            visual.static_mesh_component.set_static_mesh(pod_mesh)
            visual.set_actor_scale3d(unreal.Vector(0.18, 0.18, 0.18))

    for link in layout["hatches"]:
        lower = by_code[room_code(link["lower"], link["row"], link["column"])]
        upper = by_code[room_code(link["upper"], link["row"], link["column"])]
        spawn_hatch_ramp(actors, cube, materials["deck"], materials["accent"], lower, upper)
        x, y, _ = room_location(lower)
        for index in range(6):
            z = DECK_Z[link["lower"]] + index * (DECK_SPACING / 6.0)
            spawn_box(actors, cube, materials["accent"], (x + 450.0, y, z), (24.0, 170.0, 18.0), f"PullHold_{link['lower']}_{link['upper']}_{link['column']}_{index}", collision=False)
        room_actors[lower["code"]].connect_room(enum_value(unreal.ShipRoomSocket, "UP"), room_actors[upper["code"]], enum_value(unreal.ShipRoomSocket, "DOWN"))

    for block in layout["corridor_blocks"]:
        x = (block["column"] - 5.0) * COLUMN_SPACING
        z = DECK_Z[block["deck"]]
        floor_z = z - ROOM_HEIGHT * 0.5
        door = actors.spawn_actor_from_class(bulkhead_class, unreal.Vector(x, 0.0, floor_z), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0))
        door.set_actor_label(f"{PREFIX}CorridorBlock_D{block['deck']:02d}_{block['index']:02d}_{block['blocker'].title()}")
        door.set_editor_property("tags", [unreal.Name("CorridorBlockDoor"), unreal.Name(f"D{block['deck']:02d}"), unreal.Name(block["blocker"])])
        door.seal()
        # Across the whole corridor, and this actor sits on the floor slab's centre rather than
        # 10 below it, so the walkable floor is 10 above the origin. Found the hard way: a corridor
        # block left unconfigured kept its hidden panels but gained the new class's collision --
        # an invisible wall across deck 2 that sent the walkthrough's path up a ramp.
        configure_bulkhead_visuals(door, doorway_width=CORRIDOR_WIDTH, floor_offset=10.0)
        # An override panel on each face. A corridor block is met from whichever direction the
        # route happens to run, and a panel on one face only is a door that can be opened from one
        # side: the demo's deck-2 route reached its block from the east and found the only panel
        # on the west, behind the door it was meant to open.
        for face_name, dx, yaw in (("West", -90.0, -90.0), ("East", 90.0, 90.0)):
            station = actors.spawn_actor_from_class(unreal.MechanicalOverrideStation, unreal.Vector(x + dx, 125.0, floor_z + 90.0), unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
            station.set_actor_label(f"{PREFIX}CorridorBlockActivity_D{block['deck']:02d}_{block['index']:02d}_{face_name}")
            station.set_editor_property("target_actor", door)
            station.set_editor_property("tags", [unreal.Name("CorridorBlockStation"), unreal.Name(f"D{block['deck']:02d}")])
            station.get_editor_property("mesh").set_static_mesh(terminal_mesh)
            activity = station.get_editor_property("activity")
            activity.set_editor_property("display_name", block["activity"])
            station.set_editor_property("activity", activity)

    cryo_x, cryo_y, cryo_z = room_location(layout["cryo"])
    # Keep the 42 cm radius / 96 cm half-height capsule clear of pod ends and raised floor dressing.
    start = actors.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(cryo_x, cryo_y + 360.0, cryo_z - ROOM_HEIGHT * 0.5 + 130.0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0))
    start.set_actor_label(f"{PREFIX}PlayerStart_Cryo")
    start.set_editor_property("tags", [unreal.Name("CryoWakeStart"), unreal.Name("QuickDemoShip")])

    nav = actors.spawn_actor_from_class(unreal.NavMeshBoundsVolume, unreal.Vector(0.0, 0.0, (DECK_Z[1] + DECK_Z[4]) * 0.5), unreal.Rotator())
    nav.set_actor_label(f"{PREFIX}NavMeshBounds")
    nav.set_actor_scale3d(unreal.Vector(75.0, 18.0, 12.0))

    # Production bulkheads carry their own practical point lights. The wake state
    # is intentionally blacked out everywhere except the cryo emergency lamp.
    cryo_light_label = f"{PREFIX}RoomLight_{layout['cryo']['code']}"
    for actor in actors.get_all_level_actors():
        if not actor.get_actor_label().startswith(PREFIX) or actor.get_actor_label() == cryo_light_label:
            continue
        for component in actor.get_components_by_class(unreal.PointLightComponent):
            component.set_editor_property("intensity", 0.0)
            component.set_visibility(False)

    if not levels.save_current_level():
        raise RuntimeError("Could not save quick-demo ship map")
    unreal.EditorAssetLibrary.save_directory("/Game/Assets/Maps/ShipProduction")


def main():
    layout = build_layout(SEED)
    validate_layout(layout)
    build_level(layout)
    report = {
        "map": MAP_PATH,
        "seed": layout["seed"],
        "decks": 4,
        "rooms": len(layout["rooms"]),
        "rooms_per_deck": 24,
        "escape_pod_sites": sum(room["escape_pod"] for room in layout["rooms"]),
        "airlocks": sum(room["airlock"] for room in layout["rooms"]),
        "hatch_links": len(layout["hatches"]),
        "room_blockers": sum(bool(room["blocker"]) for room in layout["rooms"]),
        "corridor_blockers": len(layout["corridor_blocks"]),
        "special_rooms": {name: layout[name]["code"] for name in ("cryo", "workshop", "engine", "power", "cic", "breach")},
        "room_type_counts": dict(sorted((room_type, sum(room["room_type"] == room_type for room in layout["rooms"])) for room_type in {room["room_type"] for room in layout["rooms"]})),
        "room_type_placements": {room["code"]: room["room_type"] for room in layout["rooms"]},
        "hatches": layout["hatches"],
        "escape_pods": [room["code"] for room in layout["rooms"] if room["escape_pod"]],
        "validation": "passed",
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    unreal.log(f"Quick four-deck demo complete: seed {SEED}, 96 rooms, 8 airlocks, 6 hatches, 6 escape pods")


if __name__ == "__main__":
    main()
