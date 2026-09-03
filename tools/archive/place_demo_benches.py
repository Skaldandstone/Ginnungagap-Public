"""
Put a workshop bench and a suit repair bench into L_QuickDemo_FourDeck.

Two things the demo promised and did not have.

The second objective tells the player to "recover its basic field equipment" and there was nothing
in the workshop to recover -- no station, no supplies, no way to leave better equipped than they
arrived. And equipment protection scales continuously with durability with nothing anywhere in the
map able to restore it, so a run was a one-way slide with no bench to undo it at.

Both classes exist in C++; this places them and assigns what they hand over. The weapon is a real
choice rather than a placeholder: the Smart Soft Projectile Carbine is the least specialised of the
twenty-three definitions and the only one that reads as standard issue rather than as a salvage
tool repurposed under duress.

Idempotent: tagged and matched on re-run, so this replaces its own benches and never touches
hand-placed ones.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/place_demo_benches.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
TAG = "GeneratedDemoBench"

WEAPON_DEFINITION = "/Game/Assets/Gameplay/EarlyProjectileWeapons/Data/Weapons/DA_Weapon_SmartSoftProjectileCarbine"

# Supplies stocked on the workshop bench. Missing definitions are skipped with a warning rather
# than failing the run: a bench with fewer supplies is far better than no bench at all.
#
# These are the field supplies, not the salvage items that stood in here before the catalogue
# existed. What a crew member should leave a workshop carrying: air, a way to close a breach, a way
# to mend what the ship wears down, and something for the bleeding. Deliberately not the
# environmental countermeasures -- those are answers to specific afflictions and should be found or
# chosen, not handed out at the door.
FIELD_SUPPLIES = "/Game/Assets/Gameplay/FieldSupplies/Data/Items/DA_Item_"
ITEM_DEFINITIONS = [
    FIELD_SUPPLIES + "EmergencyOxygenCartridge",
    FIELD_SUPPLIES + "SuitPatchSealant",
    FIELD_SUPPLIES + "FieldRepairKit",
    FIELD_SUPPLIES + "TraumaKit",
]

# Offsets from the workshop prop, so the two benches do not occupy the same spot.
WORKSHOP_OFFSET = unreal.Vector(180.0, 0.0, 0.0)
REPAIR_OFFSET = unreal.Vector(-180.0, 0.0, 0.0)


def load_if_present(path):
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    unreal.log_warning("Asset not found, skipping: {}".format(path))
    return None


def find_by_label_fragment(actors, fragment):
    for actor in actors:
        if fragment.lower() in actor.get_actor_label().lower():
            return actor
    return None


def main():
    if not unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        unreal.log_error("Map not found: {}".format(MAP_PATH))
        return

    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    level_subsystem.load_level(MAP_PATH)

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = actor_subsystem.get_all_level_actors()

    removed = 0
    for actor in actors:
        if TAG in [str(t) for t in actor.tags]:
            actor_subsystem.destroy_actor(actor)
            removed += 1
    if removed:
        unreal.log("Removed {} bench(es) from a previous run".format(removed))
        actors = actor_subsystem.get_all_level_actors()

    # Anchor on the workshop prop the mission chain already routes the player to, rather than
    # guessing a position. A bench the player never walks past is no better than no bench.
    anchor = find_by_label_fragment(actors, "ConceptSpecialProp_Workshop")
    if not anchor:
        unreal.log_error("No workshop prop found; refusing to place benches somewhere arbitrary")
        return

    origin = anchor.get_actor_location()
    unreal.log("Workshop prop at ({:.0f}, {:.0f}, {:.0f})".format(origin.x, origin.y, origin.z))

    # --- workshop bench -------------------------------------------------------------------
    bench = actor_subsystem.spawn_actor_from_class(
        unreal.QuickDemoWorkshopBench, origin + WORKSHOP_OFFSET)
    if not bench:
        unreal.log_error("Failed to spawn the workshop bench")
        return

    bench.set_actor_label("WorkshopBench_DemoEquipment")
    bench.tags = [TAG]

    weapon_definition = load_if_present(WEAPON_DEFINITION)
    if weapon_definition:
        bench.set_editor_property("granted_weapon_definition", weapon_definition)
        # The actor class stays whatever the project's shipboard weapon actor is; the definition is
        # what decides how it behaves, and without it the weapon spawns inert.
        bench.set_editor_property("granted_weapon_class", unreal.ShipboardWeapon)
        unreal.log("Workshop bench grants {}".format(WEAPON_DEFINITION.rsplit("/", 1)[-1]))
    else:
        unreal.log_warning("No weapon definition assigned; the bench will hand over supplies only")

    items = [i for i in (load_if_present(p) for p in ITEM_DEFINITIONS) if i]
    if items:
        bench.set_editor_property("granted_items", items)
    unreal.log("Workshop bench stocked with {} item definition(s)".format(len(items)))

    # --- suit repair bench ----------------------------------------------------------------
    repair = actor_subsystem.spawn_actor_from_class(
        unreal.QuickDemoSuitRepairBench, origin + REPAIR_OFFSET)
    if not repair:
        unreal.log_error("Failed to spawn the suit repair bench")
        return

    repair.set_actor_label("SuitRepairBench_Demo")
    repair.tags = [TAG]
    unreal.log("Suit repair bench placed (unlimited uses)")

    saved = level_subsystem.save_current_level()
    unreal.log("Saved {}: {}".format(MAP_PATH, saved))


if __name__ == "__main__":
    main()
