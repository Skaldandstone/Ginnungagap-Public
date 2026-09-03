"""Author the field-supply seed catalogue and put seed points in the demo ship.

Ten pickup Blueprints existed and nothing in the world placed a single one, so every supply in the
game could only ever be handed over at the workshop bench. Once that bench was used the ship
contained nothing else to find, which makes exploring it pointless in the most literal way.

This uses the seeding system the project already has rather than scattering pickups by hand.
AWorldItemSeedPoint reads a weighted catalogue, filters it by room profile, rolls a deterministic
number of times, and scatters what it picks. Hand-placed pickups would have bypassed all of that
and frozen the layout permanently.

Placement is driven by the loot tiers already authored on the rooms, not by my judgement about
where supplies belong. Twelve of the ninety-six rooms carry a non-zero tier; the other eighty-four
are generic compartments and are deliberately left empty. The tier sets how many rolls a room gets
and how likely each is to land, so a reactor room stays richer than a berthing compartment without
anyone restating that here.

Room profiles gate what can appear where. A coolant pack in the engine room and a splint in the
recovery bay are findable in the places a crew would actually have stowed them, which is what makes
searching a specific room worth doing rather than searching any room.

Idempotent: tagged and matched on re-run.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/build_field_supply_seeding.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
TAG = "GeneratedFieldSupplySeed"

ROOT = "/Game/Assets/Gameplay/FieldSupplies"
CATALOG_FOLDER = ROOT + "/Data"
CATALOG_NAME = "DA_FieldSupplies_SeedCatalog"
CATALOG_PATH = CATALOG_FOLDER + "/" + CATALOG_NAME
PICKUP_FOLDER = ROOT + "/Blueprints/BP_Pickup_"

# Room profiles, derived from the display names the ship was authored with. Anything not listed
# falls back to Berthing: a compartment nobody named is somewhere the crew lived, and general
# supplies are the only thing that should turn up there.
PROFILE_BY_ROOM_NAME = {
    "Main Power Control": "Engineering",
    "Main Engine Room": "Engineering",
    "Cryogenic Recovery Bay": "Cryo",
    "Player Workshop": "Workshop",
    "Bloom Impact / Vacuum Breach": "Breach",
    "Combat Information Center": "Command",
}
DEFAULT_PROFILE = "Berthing"

# How generous a room is, keyed by the loot tier already on it. Tier 0 rooms get no seed point at
# all rather than a point that rolls and finds nothing -- an actor that can only ever do nothing is
# worse than no actor, because it looks like it works.
TIER_RULES = {
    1: dict(rolls=1, chance=0.50),
    2: dict(rolls=2, chance=0.60),
    3: dict(rolls=2, chance=0.75),
    4: dict(rolls=3, chance=0.80),
    5: dict(rolls=3, chance=0.90),
}

SCATTER_RADIUS_CM = 220.0

# Weight is relative within whatever survives the room filter, so the two supplies a crew member
# always wants are common everywhere and the targeted countermeasures are uncommon and local.
# An empty profile list means the entry is valid in every room.
ENTRIES = [
    dict(id="EmergencyOxygenCartridge", weight=1.4, qty=(1, 2), profiles=[],
         tags=["Supply.LifeSupport"]),
    dict(id="SuitPatchSealant", weight=1.2, qty=(1, 2), profiles=[],
         tags=["Supply.LifeSupport"]),
    dict(id="GeneralMedicalAmpoule", weight=1.1, qty=(1, 2), profiles=[],
         tags=["Supply.Medical"]),

    dict(id="FieldRepairKit", weight=1.0, qty=(1, 1),
         profiles=["Engineering", "Workshop", "Breach"], tags=["Supply.Repair"]),
    dict(id="TraumaKit", weight=1.0, qty=(1, 1),
         profiles=["Cryo", "Berthing", "Command"], tags=["Supply.Medical"]),
    dict(id="CompoundSplint", weight=0.7, qty=(1, 1),
         profiles=["Cryo", "Berthing"], tags=["Supply.Medical"]),

    # Local to the hazard that causes them. A chelation injector belongs near the reactor, not in a
    # bunk room, and finding one is supposed to tell you something about where you are standing.
    dict(id="ChelationInjector", weight=0.8, qty=(1, 1),
         profiles=["Engineering", "Breach"], tags=["Supply.Medical", "Hazard.Radiation"]),
    dict(id="RecompressionAmpoule", weight=0.8, qty=(1, 1),
         profiles=["Breach", "Cryo"], tags=["Supply.Medical", "Hazard.Decompression"]),
    dict(id="ThermalRegulationWrap", weight=0.6, qty=(1, 1),
         profiles=["Breach", "Engineering"], tags=["Supply.Medical", "Hazard.Thermal"]),
    dict(id="CoolantGelPack", weight=0.6, qty=(1, 1),
         profiles=["Engineering"], tags=["Supply.Medical", "Hazard.Thermal"]),
]


def load_if_present(path):
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    unreal.log_warning("Asset not found, skipping: {}".format(path))
    return None


def build_catalog():
    if unreal.EditorAssetLibrary.does_asset_exist(CATALOG_PATH):
        unreal.EditorAssetLibrary.delete_asset(CATALOG_PATH)

    factory = unreal.DataAssetFactory()
    factory.set_editor_property("data_asset_class", unreal.WorldItemSeedCatalog)
    catalog = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        CATALOG_NAME, CATALOG_FOLDER, unreal.WorldItemSeedCatalog, factory)
    if not catalog:
        raise RuntimeError("Could not create " + CATALOG_PATH)

    catalog.set_editor_property("catalog_id", unreal.Name("FieldSupplies"))

    entries = []
    for spec in ENTRIES:
        blueprint = load_if_present(PICKUP_FOLDER + spec["id"])
        if not blueprint:
            continue

        entry = unreal.WorldItemSeedEntry()
        entry.set_editor_property("content_id", unreal.Name(spec["id"]))
        entry.set_editor_property("actor_class", blueprint.generated_class())
        entry.set_editor_property("weight", spec["weight"])
        entry.set_editor_property("min_quantity", spec["qty"][0])
        entry.set_editor_property("max_quantity", spec["qty"][1])
        entry.set_editor_property(
            "room_profiles", [unreal.Name(p) for p in spec["profiles"]])
        entry.set_editor_property(
            "content_tags", [unreal.Name(t) for t in spec["tags"]])
        entries.append(entry)

    catalog.set_editor_property("entries", entries)
    unreal.EditorAssetLibrary.save_loaded_asset(catalog)
    unreal.log("Catalogue {} holds {} entries".format(CATALOG_NAME, len(entries)))
    return catalog


def floor_location(room):
    """Bottom of the room's bounds, not its origin.

    Room origins sit well above the deck -- the workshop prop is roughly two metres below its own
    room's origin -- so seeding at the origin would leave supplies floating at chest height or
    higher. Taking the bounds and adding a small clearance puts them on the deck wherever a room
    happens to be shaped differently.
    """
    origin, extent = room.get_actor_bounds(only_colliding_components=False)
    return unreal.Vector(origin.x, origin.y, origin.z - extent.z + 30.0)


def main():
    if not unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        unreal.log_error("Map not found: {}".format(MAP_PATH))
        return

    catalog = build_catalog()

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
        unreal.log("Removed {} seed point(s) from a previous run".format(removed))
        actors = actor_subsystem.get_all_level_actors()

    rooms = [a for a in actors if a.get_class().get_name() == "ModularShipRoom"]
    if not rooms:
        unreal.log_error("No rooms in the map; refusing to place seed points blind")
        return

    placed = 0
    skipped = 0
    for room in rooms:
        profile_struct = room.get_editor_property("gameplay_profile")
        tier = profile_struct.get_editor_property("loot_tier")

        rules = TIER_RULES.get(tier)
        if not rules:
            skipped += 1
            continue

        room_name = str(room.get_editor_property("display_name"))
        room_profile = PROFILE_BY_ROOM_NAME.get(room_name, DEFAULT_PROFILE)

        point = actor_subsystem.spawn_actor_from_class(
            unreal.WorldItemSeedPoint, floor_location(room))
        if not point:
            unreal.log_error("Failed to spawn a seed point in {}".format(room_name))
            continue

        point.set_actor_label("SupplySeed_{}".format(
            str(room.get_editor_property("room_code"))))
        point.tags = [TAG]
        point.set_editor_property("catalog", catalog)
        point.set_editor_property("room_profile", unreal.Name(room_profile))
        point.set_editor_property("spawn_rolls", rules["rolls"])
        point.set_editor_property("spawn_chance", rules["chance"])
        point.set_editor_property("scatter_radius_cm", SCATTER_RADIUS_CM)
        point.set_editor_property("seed_on_begin_play", True)

        # An author-set offset, not the randomness itself: the stream folds this in with the run
        # seed and the actor path, so points stay distinguishable while still varying run to run.
        point.set_editor_property("seed", 1000 + placed)

        unreal.log("  {:<10} tier {}  {:<10} {} roll(s) @ {:.0%}  {}".format(
            str(room.get_editor_property("room_code")), tier, room_profile,
            rules["rolls"], rules["chance"], room_name))
        placed += 1

    saved = level_subsystem.save_current_level()
    unreal.log("Placed {} seed point(s), left {} tier-0 room(s) empty. Saved {}: {}".format(
        placed, skipped, MAP_PATH, saved))


if __name__ == "__main__":
    main()
