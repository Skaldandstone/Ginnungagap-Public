"""Which doorways in the generated ship a pawn can physically pass, and what blocks the rest.

Pure bounds arithmetic, no traces: a probe box sits in each door's gap at pawn height, and any
component that would stop a pawn -- collision enabled for queries and responding to the Pawn channel
with Block -- whose bounds overlap it is a blocker. Overlap-only volumes (rooms, hazard zones) and
no-collision dressing do not count, which the first version of this audit got wrong by using actor
bounds over every colliding component.

The door's own components are tested one by one, because its actor bounds are inflated to 70 m by
the leaf mesh the Blueprint leaves parked at the world origin.

First answer, before any repair: 0 of 96.
"""
import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
PROBE_ALONG = 100.0   # half-width along the wall (the gap is 250)
PROBE_THROUGH = 30.0  # half-depth through the wall plane
PROBE_Z_LO = 40.0     # above the floor
PROBE_Z_HI = 200.0
ABSURD_EXTENT = 2000.0

QUERY_ENABLED = (unreal.CollisionEnabled.QUERY_AND_PHYSICS, unreal.CollisionEnabled.QUERY_ONLY)


def tags(actor):
    return [str(t) for t in actor.tags]


def overlaps(o, e, c, h):
    return (abs(o.x - c.x) <= e.x + h.x and abs(o.y - c.y) <= e.y + h.y and abs(o.z - c.z) <= e.z + h.z)


PAWN_CHANNEL = getattr(unreal.CollisionChannel, "ECC_PAWN", None) or getattr(unreal.CollisionChannel, "PAWN")


def blocks_pawn(component):
    if component.get_collision_enabled() not in QUERY_ENABLED:
        return False
    # Matched by name: the Python binding's enum member naming is not uniform across enums.
    return "BLOCK" in str(component.get_collision_response_to_channel(PAWN_CHANNEL)).upper()


def describe(actor, component):
    mesh = ""
    if isinstance(component, unreal.StaticMeshComponent):
        m = component.get_editor_property("static_mesh")
        mesh = m.get_name() if m else "NONE"
    else:
        mesh = component.get_class().get_name()
    return "{}.{}[{}]".format(actor.get_name(), component.get_name(), mesh)


levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    unreal.log_error("DOOR could not load {}".format(MAP))
else:
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    doors = [a for a in actors if "RoomThresholdDoor" in tags(a)]
    door_names = set(d.get_name() for d in doors)
    rooms = {}
    for a in actors:
        if a.get_class().get_name() == "ModularShipRoom":
            for t in tags(a):
                if t.startswith("QD-"):
                    rooms[t] = a

    # Every pawn-blocking component in the level, with its bounds, computed once.
    blocking = []
    for a in actors:
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            if not blocks_pawn(c):
                continue
            o, e, _r = unreal.SystemLibrary.get_component_bounds(c)
            if max(e.x, e.y, e.z) > ABSURD_EXTENT or (e.x <= 0 and e.y <= 0 and e.z <= 0):
                continue
            blocking.append((a, c, o, e))
    unreal.log("DOOR doors: {}  rooms: {}  pawn-blocking components: {}".format(len(doors), len(rooms), len(blocking)))

    # An ObstructionBarrier in a doorway is a gate the player resolves with Cut, Squeeze or
    # Breach -- the generator places ten of them on purpose. Anything else in the gap is a seal.
    open_count = gated = sealed = 0
    tally = {}
    for door in sorted(doors, key=lambda d: next((t for t in tags(d) if t.startswith("QD-")), "")):
        code = next((t for t in tags(door) if t.startswith("QD-")), "?")
        dl = door.get_actor_location()
        floor_z = dl.z + 10.0
        centre = unreal.Vector(dl.x, dl.y, floor_z + (PROBE_Z_LO + PROBE_Z_HI) / 2.0)
        half = unreal.Vector(PROBE_ALONG, PROBE_THROUGH, (PROBE_Z_HI - PROBE_Z_LO) / 2.0)
        hits = [(a, c) for a, c, o, e in blocking if overlaps(o, e, centre, half)]

        # Two kinds of gate. An ObstructionBarrier is cleared with a verb; a bulkhead's own leaves,
        # now that the door has some, are opened at its override station. Both are the level
        # working as designed. A sealed bulkhead's leaf blocking its own doorway is not a seal in
        # the sense this audit means -- something in the gap that nothing in the game can move.
        def is_sealed_leaf(a, c):
            return isinstance(a, unreal.BulkheadDoor) and a.get_editor_property("is_sealed") \
                and c.get_name() in ("LeftPanel", "RightPanel")

        gates = [describe(a, c) for a, c in hits
                 if a.get_class().get_name() == "ObstructionBarrier" or is_sealed_leaf(a, c)]
        seals = [describe(a, c) for a, c in hits
                 if a.get_class().get_name() != "ObstructionBarrier" and not is_sealed_leaf(a, c)]
        for b in seals:
            key = b.split("[")[-1].rstrip("]")
            tally[key] = tally.get(key, 0) + 1
        if seals:
            sealed += 1
            status = "SEALED  "
        elif gates:
            gated += 1
            status = "gated   "
        else:
            open_count += 1
            status = "open    "
        unreal.log("DOOR {} {} gates={} seals={}".format(code, status, gates[:2], seals[:4]))

    unreal.log("DOOR doorways: open {}  gated {}  sealed {}  of {}".format(open_count, gated, sealed, len(doors)))
    unreal.log("DOOR seal tally: {}".format(sorted(tally.items(), key=lambda kv: -kv[1])[:10]))
