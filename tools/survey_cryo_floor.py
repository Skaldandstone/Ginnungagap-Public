"""Reports the cryo bay's floor meshes and the materials on them.

The cryo hero shot now matches Sheet 11 on hue (blue-minus-red -0.002 against the reference's
+0.009) but not on tone: 5.4% of the frame is clipped above 0.95 and its p90 luminance is 0.916,
where the reference's p90 is 0.348 and never approaches white.

That gap is albedo, not exposure. Sheet 11's cryo floor is dark steel; the demo's aisle is a pale
panel, and a pale floor under a 1900-intensity pair clips no matter what the exposure does -- which
is consistent with the earlier finding that moving the depth light 3x further away and then halving
it left the strip exactly as white.

So: what is that floor, and what is on it.
"""

import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
DECK_Z = 1255.0 - 195.0
ROOM_X, ROOM_Y = -6600.0, -680.0
REACH = 800.0

unreal.EditorLoadingAndSavingUtils.load_map(MAP)

seen = {}
for actor in unreal.EditorActorSubsystem().get_all_level_actors():
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    loc = actor.get_actor_location()
    if abs(loc.x - ROOM_X) > REACH or abs(loc.y - ROOM_Y) > REACH:
        continue
    # Floors only: at or just below standing level.
    if not (-40.0 <= loc.z - DECK_Z <= 60.0):
        continue

    comp = actor.static_mesh_component
    mesh = comp.get_editor_property("static_mesh") if comp else None
    if not mesh:
        continue

    name = mesh.get_name()
    overrides = comp.get_editor_property("override_materials") or []
    mats = []
    for i in range(comp.get_num_materials()):
        m = comp.get_material(i)
        overridden = i < len(overrides) and overrides[i] is not None
        mats.append("{}{}".format(m.get_name() if m else "None", "*" if overridden else ""))

    key = (name, tuple(mats))
    entry = seen.setdefault(key, {"count": 0, "tags": set()})
    entry["count"] += 1
    entry["tags"].update(str(t) for t in actor.tags)

unreal.log("CRYOFLOOR {} distinct floor mesh/material combinations".format(len(seen)))
for (name, mats), entry in sorted(seen.items(), key=lambda kv: -kv[1]["count"]):
    unreal.log("CRYOFLOOR x{:<3} {:<22} mats={}  tags={}".format(
        entry["count"], name, list(mats), sorted(entry["tags"])))
unreal.log("CRYOFLOOR (* marks a per-actor material override)")
unreal.log("CRYOFLOOR done")
