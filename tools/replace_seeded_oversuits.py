"""Takes the built suit modules off the cryo bay's suit rack and stands Fab tanks in the recesses.

The rack's four display suits are the project's V25 sculpt modules (StaticMeshActors tagged
QuickDemoSeededOversuit), which James called relics. They are hidden (not deleted: the seeding
script may want them back) and each recess gets a covered nitrogen tank from ModSci_EngiProps,
standing on the suit station's floor, so the rack still reads as stocked. The suit station's
interaction is untouched.

    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/replace_seeded_oversuits.py -NullRHI
"""
import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
SEEDED_TAG = "QuickDemoSeededOversuit"
STAND_IN_TAG = "QuickDemoRackStandIn"
STAND_IN_MESH = "/Game/ModSci_EngiProps/Meshes/SM_NitrogenTank_Covered"

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert les.load_level(MAP)
actors_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
actors = actors_sub.get_all_level_actors()

# Idempotent: clear earlier stand-ins first.
for a in actors:
    if unreal.Name(STAND_IN_TAG) in a.tags:
        actors_sub.destroy_actor(a)
actors = actors_sub.get_all_level_actors()

stations = [a for a in actors if unreal.Name("CryoSuitStation") in a.tags]
seeded = [a for a in actors if unreal.Name(SEEDED_TAG) in a.tags]
hidden = 0
recesses = {}
for a in seeded:
    a.set_actor_hidden_in_game(True)
    a.set_editor_property("hidden", True)
    for c in a.get_components_by_class(unreal.PrimitiveComponent):
        c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    hidden += 1
    loc = a.get_actor_location()
    key = (round(loc.x), round(loc.y))
    recesses.setdefault(key, []).append(loc)

mesh = unreal.load_asset(STAND_IN_MESH)
assert mesh, "stand-in mesh missing"
placed = 0
for (x, y), locs in sorted(recesses.items()):
    # The floor is the suit station's own base on this deck; the nearest station gives it.
    nearest = min(stations, key=lambda s: abs(s.get_actor_location().x - x) + abs(s.get_actor_location().y - y)) if stations else None
    floor_z = nearest.get_actor_location().z if nearest else min(l.z for l in locs) - 90.0
    actor = actors_sub.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, floor_z), unreal.Rotator(0.0, 0.0, 90.0))
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_label(f"QuickDemo4D_RackStandIn_{placed + 1:02d}")
    actor.set_editor_property("tags", [unreal.Name(STAND_IN_TAG), unreal.Name("QuickDemoDressing")])
    placed += 1
saved = les.save_current_level()
print(f"RACK hid {hidden} built suit modules in {len(recesses)} recesses, placed {placed} stand-ins; saved={saved}")
