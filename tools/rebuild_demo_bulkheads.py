"""Gives every placed bulkhead in the demo its frame, lintel and opening leaves.

The generator's configure_bulkhead_visuals does this for a fresh build; this applies the same
settings to the map that already exists, so the ship does not have to be regenerated (and
re-dressed, and re-audited) to get doors. Also reports which doors on the mission route are
sealed, because a sealed door is now a physical fact rather than a flag, and the walkthrough has
to open it at its override station like a player would.

Run:  UnrealEditor-Cmd.exe <project> -ExecutePythonScript=<forward-slash path to this file> -NullRHI
"""
import sys
from pathlib import Path

import unreal

PROJECT = Path(unreal.SystemLibrary.get_project_directory())
TOOLS = PROJECT / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
KIT_DOOR = "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/DOOR_FRAME/"
ROOM_HEIGHT = 430.0
DOOR_FLOOR_OFFSET = 20.0
ROUTE_SPECIALS = ("cryo", "workshop", "power", "breach", "cic")


def tags(actor):
    return [str(t) for t in actor.tags]


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(MAP_PATH):
        unreal.log_error("BULKHEAD could not load " + MAP_PATH)
        return
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()

    meshes = {
        "frame_mesh_asset": unreal.load_asset(KIT_DOOR + "SM_DOOR_FRAME_01_OUTSIDE"),
        "left_leaf_mesh_asset": unreal.load_asset(KIT_DOOR + "SM_DOOR_01_LEFT"),
        "right_leaf_mesh_asset": unreal.load_asset(KIT_DOOR + "SM_DOOR_01_RIGHT"),
        "lintel_mesh_asset": unreal.load_asset(KIT_DOOR + "SM_DOOR_FRAME_02_UP"),
    }
    for key, mesh in meshes.items():
        if not mesh:
            unreal.log_error("BULKHEAD missing kit mesh for {}".format(key))
            return

    route_codes = {}
    for actor in actors:
        if actor.get_class().get_name() == "ModularShipRoom":
            t = tags(actor)
            code = next((x for x in t if x.startswith("QD-")), None)
            special = next((x for x in t if x in ROUTE_SPECIALS), None)
            if code and special:
                route_codes[code] = special

    configured = sealed_total = corridor_blocks = 0
    sealed_on_route = []
    for door in actors:
        # Every production bulkhead, not only the room-threshold ones. The generator also places
        # sealed bulkheads across corridors ("CorridorBlock_*", with an override station beside
        # each); the first version of this script skipped those, and the class then gave their
        # hidden panels collision -- an invisible wall across deck 2.
        if not isinstance(door, unreal.ProductionBulkheadDoor):
            continue
        is_room_door = "RoomThresholdDoor" in tags(door)
        is_corridor_block = not is_room_door and door.get_actor_label().find("CorridorBlock") >= 0
        if not is_room_door and not is_corridor_block:
            continue
        if is_corridor_block:
            corridor_blocks += 1
            current = [t for t in tags(door) if t != "CorridorBlockDoor"]
            door.tags = current + ["CorridorBlockDoor"]
        # Corridor blocks span the 360 cm corridor and sit on the floor slab's centre (10 below
        # the walkable floor); room doors span the 250 cm gap and sit 10 below that (20 below).
        width = 360.0 if is_corridor_block else 250.0
        floor_offset = 10.0 if is_corridor_block else DOOR_FLOOR_OFFSET
        try:
            for key, mesh in meshes.items():
                door.set_editor_property(key, mesh)
            door.set_editor_property("doorway_width", width)
            door.set_editor_property("doorway_height", 270.0)
            door.set_editor_property("ceiling_height", ROOM_HEIGHT - 20.0 - floor_offset)
            door.set_editor_property("floor_offset", floor_offset)
            door.set_editor_property("apply_door_material", False)
        except Exception as error:
            unreal.log_warning("BULKHEAD skipped {}: {}".format(door.get_actor_label(), error))
            continue
        for component in door.get_components_by_class(unreal.StaticMeshComponent):
            name = component.get_name()
            if name in ("FrameMesh", "LintelMesh", "LeftPanel", "RightPanel"):
                component.set_editor_property("use_default_collision", False)
                component.set_visibility(True)
            elif name == "VisualMesh":
                component.set_editor_property("use_default_collision", False)
                component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                component.set_visibility(False)
        # No explicit construction-script call: the Python API does not expose one on the actor,
        # and set_editor_property already runs PostEditChangeProperty, which re-runs OnConstruction.
        # Nudging a geometry property last makes sure the final pass sees every asset above.
        door.set_editor_property("leaf_slide_margin", 8.0)
        configured += 1

        code = next((x for x in tags(door) if x.startswith("QD-")), "?")
        sealed = bool(door.get_editor_property("is_sealed"))
        if sealed:
            sealed_total += 1
            if code in route_codes:
                sealed_on_route.append("{} ({})".format(code, route_codes[code]))
        blocker = next((x for x in tags(door) if x not in ("RoomThresholdDoor", code)), "?")
        unreal.log("BULKHEAD {} {} blocker={} sealed={}".format(door.get_actor_label(), code, blocker, sealed))

    unreal.log("BULKHEAD configured {} doors ({} corridor blocks); {} sealed; sealed on the mission route: {}".format(
        configured, corridor_blocks, sealed_total, sealed_on_route or "none"))
    saved = levels.save_current_level()
    unreal.log("BULKHEAD saved {}: {}".format(MAP_PATH, saved))


if __name__ == "__main__":
    main()
