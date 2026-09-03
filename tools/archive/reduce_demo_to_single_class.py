"""Cut the demo's cryo bay down to one playable class.

The demo exists to record hero shots for a grant application, not to demonstrate every role. Four
suit stations means four things the player is told to use and three that lead nowhere on camera,
and a reviewer reads that as unfinished rather than as choice.

Engineering is the one kept because the five-objective chain is engineering work end to end --
restore main power, seal the hull breach, patch worn gear. A character who starts as anything else
spends the whole recording doing someone else's job.

The four cryo pods stay. Four pods with one occupant says the rest of the crew did not wake up,
which is the story this game is telling and a better opening shot than either a busy bay full of
unusable stations or an empty room with one pod in it. Only the suits and stations go.

Idempotent: re-running finds one station already and leaves it alone. Safe to run against a map
that has already been reduced.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/reduce_demo_to_single_class.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import re

import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"

# The role the demo ships with. Matches GinnungagapDefaults::StartingSuitRole in C++; if these two
# ever disagree the player is handed a suit their profile does not match.
KEEP_ROLE = "Engineering"


def role_of_actor(actor):
    """The role an actor is tagged with, if any.

    The oversuit seeding pass tags each garment PressureSuitRole_<Role>, which is more reliable
    than parsing the label -- labels get renamed by hand, tags rarely do.
    """
    for tag in actor.tags:
        text = str(tag)
        if text.startswith("PressureSuitRole_"):
            return text[len("PressureSuitRole_"):]
    return None


def station_role(actor):
    """The role a suit station equips, read from the property that actually drives behaviour.

    Unreal stringifies the enum as "<PressureSuitRole.ENGINEERING: 1>", so splitting on the dot
    leaves "ENGINEERING: 1>" and every comparison quietly fails. Matched with a pattern instead,
    which cannot be fooled by the decoration around the name.
    """
    try:
        value = actor.get_editor_property("suit_role")
    except Exception:
        return None
    match = re.search(r"PressureSuitRole\.([A-Za-z_]+)", str(value))
    return match.group(1).replace("_", "").lower() if match else None


def main():
    if not unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        unreal.log_error("Map not found: {}".format(MAP_PATH))
        return

    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    level_subsystem.load_level(MAP_PATH)

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = actor_subsystem.get_all_level_actors()

    wanted = KEEP_ROLE.replace("_", "").lower()

    stations = [a for a in actors if a.get_class().get_name() == "QuickDemoSuitStation"]
    suits = [a for a in actors
             if a.get_class().get_name() == "SkeletalMeshActor"
             and "Oversuit_" in a.get_actor_label()]
    pods = [a for a in actors if a.get_class().get_name() == "CryoPodSystem"]

    unreal.log("Before: {} station(s), {} oversuit(s), {} pod(s)".format(
        len(stations), len(suits), len(pods)))

    # --- stations -----------------------------------------------------------------------------
    keepers = [s for s in stations if station_role(s) == wanted]
    if not keepers:
        unreal.log_error(
            "No suit station equips {}; refusing to delete every station and leave the first "
            "objective uncompletable".format(KEEP_ROLE))
        return

    if len(keepers) > 1:
        # Worth saying: the bay shipped with two Engineering stations and none for the first role,
        # so one recess has always equipped the wrong suit. Reducing to one class hides that rather
        # than fixing it, and someone restoring the other roles later needs to know.
        unreal.log_warning(
            "{} stations equip {}; the bay was misconfigured before this pass. Keeping the first: "
            "{}".format(len(keepers), KEEP_ROLE,
                        ", ".join(k.get_actor_label() for k in keepers)))

    keep_station = keepers[0]
    removed_stations = 0
    for station in stations:
        if station is keep_station:
            continue
        actor_subsystem.destroy_actor(station)
        removed_stations += 1

    keep_location = keep_station.get_actor_location()
    unreal.log("Kept {} at ({:.0f}, {:.0f}, {:.0f})".format(
        keep_station.get_actor_label(), keep_location.x, keep_location.y, keep_location.z))

    # --- oversuits ----------------------------------------------------------------------------
    removed_suits = 0
    kept_suit = None
    for suit in suits:
        role = role_of_actor(suit)
        matches = role is not None and role.replace("_", "").lower() == wanted
        if matches and kept_suit is None:
            kept_suit = suit
            continue
        actor_subsystem.destroy_actor(suit)
        removed_suits += 1

    if kept_suit:
        unreal.log("Kept oversuit {}".format(kept_suit.get_actor_label()))
    else:
        # Not fatal: the station is what grants the suit, the garment in the recess is set
        # dressing. Worth saying out loud rather than leaving a silently emptier bay.
        unreal.log_warning(
            "No {} oversuit found in the recesses; the station still works, but the bay has no "
            "garment on display".format(KEEP_ROLE))

    unreal.log("Removed {} station(s) and {} oversuit(s); kept all {} cryo pod(s)".format(
        removed_stations, removed_suits, len(pods)))

    saved = level_subsystem.save_current_level()
    unreal.log("Saved {}: {}".format(MAP_PATH, saved))


if __name__ == "__main__":
    main()
