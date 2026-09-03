"""Lists every pawn-blocking component inside a box of the demo map.

Read-only diagnostic. Default box: the deck-2 corridor between the hatch base and the corridor
obstruction, where the walkthrough's path started going a deck up instead of along the deck.

    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=<forward-slash path> -NullRHI
Optional: PROBE_BOX="minx,miny,minz,maxx,maxy,maxz" in the environment.
"""
import os

import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
DEFAULT_BOX = (-3400.0, -260.0, 520.0, -1500.0, 260.0, 900.0)
QUERY_ENABLED = (unreal.CollisionEnabled.QUERY_AND_PHYSICS, unreal.CollisionEnabled.QUERY_ONLY)
PAWN_CHANNEL = getattr(unreal.CollisionChannel, "ECC_PAWN", None) or getattr(unreal.CollisionChannel, "PAWN")

box = DEFAULT_BOX
if os.environ.get("PROBE_BOX"):
    box = tuple(float(v) for v in os.environ["PROBE_BOX"].split(","))
lo = unreal.Vector(box[0], box[1], box[2]); hi = unreal.Vector(box[3], box[4], box[5])


def blocks_pawn(c):
    if c.get_collision_enabled() not in QUERY_ENABLED:
        return False
    return "BLOCK" in str(c.get_collision_response_to_channel(PAWN_CHANNEL)).upper()


levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    unreal.log_error("PROBE could not load " + MAP)
else:
    hits = 0
    for a in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        for c in a.get_components_by_class(unreal.PrimitiveComponent):
            if not blocks_pawn(c):
                continue
            o, e, _ = unreal.SystemLibrary.get_component_bounds(c)
            if max(e.x, e.y, e.z) > 3000.0:
                continue
            if (o.x + e.x < lo.x or o.x - e.x > hi.x or o.y + e.y < lo.y or o.y - e.y > hi.y or o.z + e.z < lo.z or o.z - e.z > hi.z):
                continue
            mesh = ""
            if isinstance(c, unreal.StaticMeshComponent):
                m = c.get_editor_property("static_mesh"); mesh = m.get_name() if m else "NONE"
            hits += 1
            unreal.log("PROBE {} / {} [{}] {} centre=({:.0f},{:.0f},{:.0f}) extent=({:.0f},{:.0f},{:.0f}) tags={}".format(
                a.get_actor_label(), c.get_name(), a.get_class().get_name(), mesh, o.x, o.y, o.z, e.x, e.y, e.z, [str(t) for t in a.tags][:3]))
    unreal.log("PROBE {} pawn-blocking components in box {}".format(hits, box))
