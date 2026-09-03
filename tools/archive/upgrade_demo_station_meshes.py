"""Give the demo's interactive stations Fab meshes instead of project blockouts.

Once the six route rooms were dressed, the stations became the crudest objects in frame. They are
also the things the player is told to walk up to and use, so they are what a camera lingers on.
`SM_Prop_WallTerminal`, `SM_Prop_Locker` and the geometry-scripted system consoles are fine as
blockouts and wrong as the subject of a grant-application shot.

This overrides the mesh per instance rather than changing the classes, on purpose. Two of these are
`AShipSystemActor`s whose `OnConstruction` picks a mesh from `SystemType`, and that lookup only
fires when the component has no mesh already -- so a per-instance override sticks, and the class
default stays correct for every other map. The activity stations set their mesh per instance in the
first place.

Meshes are chosen so two stations standing near each other never read as the same object twice.
The CIC in particular has four interactives within a few metres of one another.

Idempotent: re-running assigns the same meshes. Tagged so a later pass can find what was changed.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/upgrade_demo_station_meshes.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
TAG = "UpgradedStationMesh"

KIT = "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/"
STRUCT = "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/SRTUCTURE/"

# A second pack, used only for the CIC. The mechanic-base kit has no consoles in it -- its
# COMPUTER folder is generic terminals -- and a command centre built from four of those reads as
# one object repeated. Scifi_Hideout has purpose-built consoles and the project already owns it.
HIDEOUT = "/Game/Scifi_Hideout/Meshes/"

# Matched on actor label, because that identifies a specific placed station rather than a class of
# them. Value is (mesh path, uniform scale).
#
# Every mesh here is one whose bounds were measured before use rather than assumed. That
# restriction is deliberate: an unmeasured prop is how you get a wall panel floating free-standing
# in the middle of a room, and it is not visible in a log line that says the assignment succeeded.
# The two non-kit meshes were measured by tools/measure_cic_console_candidates.py.
#
# Measured sizes, for whoever changes these:
#   SM_COMPUTER_01                102 x  76 x 189   upright operator terminal
#   SM_COMPUTER_02                126 x  77 x 121   lower console
#   SM_ELECTRIC_BOX_01_OPEN       111 x  46 x   9   flat, wall-mounted
#   SM_WALL_08_DISPLAY            400 x 100 x 400   display wall
#   SM_DOOR_FRAME_03_LOCKER_LEFT  117 x  26 x 202   locker door
#   SM_console                    130 x 154 x 231   upright console  (Scifi_Hideout)
#   SM_small_console              222 x  75 x  96   low wide console (Scifi_Hideout)
BY_LABEL = {
    # Deck 2, main power control. A lower console rather than the kit's power generator, because
    # the engineering room dressing already places a generator and two of them in one room reads
    # as a duplicated actor.
    "QuickDemo4D_PowerRestoreStation": (KIT + "COMPUTER/SM_COMPUTER_02", 1.4),

    # Deck 3, the breach. Free-standing, so it needs a prop that stands up on its own.
    "QuickDemo4D_BreachPatchActivity": (KIT + "COMPUTER/SM_COMPUTER_01", 1.2),

    # The CIC cluster. The tactical console is the objective, so it gets the tallest silhouette.
    #
    # It previously got SM_WALL_08_DISPLAY, which was a mistake: that is a wall piece, and used as
    # a free-standing console it rendered as a featureless slab standing in the middle of the room.
    # A mesh being the right size is not the same as it being the right kind of thing, and a bounds
    # check cannot tell the difference.
    "QuickDemo4D_CICMissionConsole": (KIT + "COMPUTER/SM_COMPUTER_01", 1.3),
    "CIC_HelmNavigation": (KIT + "COMPUTER/SM_COMPUTER_02", 1.2),

    # The other two CIC stations, off the project blockouts at last. See the note below the table
    # for why these come from a different pack than everything else here.
    "CIC_SensorArray": (HIDEOUT + "Console/SM_console", 1.0),
    "CIC_JumpConsole": (HIDEOUT + "Small_console/SM_small_console", 1.0),

    # Cryo bay. A locker door is what a suit recess actually is.
    "QuickDemo4D_SuitStation_01": (STRUCT + "DOOR_FRAME/SM_DOOR_FRAME_03_LOCKER_LEFT", 1.4),
}

# CIC_SensorArray and CIC_JumpConsole are handled above now, and not with kit meshes.
#
# The blocker last pass was that the kit meshes with measured bounds were used up, and the kit has
# no actual consoles in it -- only generic computer terminals, which is why the CIC read as the same
# object four times. Asked whether any free Fab assets would help, the answer turned out to be that
# the project already owns two purpose-built consoles it was not using, in Scifi_Hideout. Nothing
# needed downloading.
#
# Both were measured before being placed, by tools/measure_cic_console_candidates.py:
#   SM_console        130 x 154 x 231   base pivot, 1 material   upright operator station
#   SM_small_console  222 x  75 x  96   base pivot, 1 material   low wide console
#
# The pairing is deliberate. One is tall and narrow, the other low and wide, so the two stations
# either side of the room have different silhouettes from the doorway -- which was the whole
# objection to using a third and fourth generic terminal.
#
# Both are authored on their base, so they sit on the deck at the station's own Z with no offset.
# That is worth stating because it is not general: SM_planet_hologram, the obvious CIC centrepiece,
# is authored on its centre and would sink halfway into the floor placed the same way.
#
# Still open, and deliberately not done here: a holographic table as the room's centrepiece. The
# meshes exist and fit (SM_hologram_support 125 x 125 x 45 on its base, SM_planet_hologram 163^3 on
# its centre, so the sphere wants Z + 127). It is not placed because the CIC stations are positioned
# as offsets from an anchor actor whose position in the room this script does not know, and a
# centrepiece dropped at the room origin could land inside the jump console. That is a placement
# question for place_demo_cic_stations.py, which does know.

# The door cranks. Matched by prefix because there are thirty-two of them across the ship and they
# all want the same treatment -- wall-mounted, flat, on a bulkhead.
BY_PREFIX = {
    "QuickDemo4D_BlockActivity_": (KIT + "MACHINE/SM_ELECTRIC_BOX_01_OPEN", 1.5),
    "QuickDemo4D_CorridorBlockActivity_": (KIT + "MACHINE/SM_ELECTRIC_BOX_01_OPEN", 1.5),
}


def mesh_component(actor):
    """The component a station actually draws with.

    Activity stations root themselves on a component called Mesh; ship systems use VisualMesh.
    Anything else is left alone rather than guessed at.
    """
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        if component.get_name() in ("Mesh", "VisualMesh"):
            return component
    return None


def resolve(label):
    if label in BY_LABEL:
        return BY_LABEL[label]
    for prefix, spec in BY_PREFIX.items():
        if label.startswith(prefix):
            return spec
    return None


def main():
    if not unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        unreal.log_error("Map not found: {}".format(MAP_PATH))
        return

    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    level_subsystem.load_level(MAP_PATH)

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = actor_subsystem.get_all_level_actors()

    upgraded = 0
    missing = []
    seen = set()

    for actor in actors:
        label = actor.get_actor_label()
        spec = resolve(label)
        if not spec:
            continue

        seen.add(label)
        path, scale = spec

        if not unreal.EditorAssetLibrary.does_asset_exist(path):
            missing.append("{} -> {}".format(label, path))
            continue

        component = mesh_component(actor)
        if not component:
            unreal.log_warning("{} has no Mesh or VisualMesh component; skipped".format(label))
            continue

        mesh = unreal.EditorAssetLibrary.load_asset(path)
        component.set_static_mesh(mesh)
        actor.set_actor_scale3d(unreal.Vector(scale, scale, scale))

        tags = [str(t) for t in actor.tags]
        if TAG not in tags:
            actor.tags = list(actor.tags) + [unreal.Name(TAG)]

        origin, extent = actor.get_actor_bounds(only_colliding_components=False)
        unreal.log("  {:<34} -> {:<28} {:>4.0f}x{:>4.0f}x{:>4.0f}".format(
            label, path.split("/")[-1], extent.x * 2, extent.y * 2, extent.z * 2))
        upgraded += 1

    for label in BY_LABEL:
        if label not in seen:
            # Said out loud rather than passed over: a label that matches nothing means the map
            # changed or the station was renamed, and the station is still a blockout on camera.
            unreal.log_warning("No actor labelled {} in the map; still a blockout".format(label))

    for entry in missing:
        unreal.log_error("Kit mesh missing for {}".format(entry))

    saved = level_subsystem.save_current_level()
    unreal.log("Upgraded {} station mesh(es). Saved {}: {}".format(upgraded, MAP_PATH, saved))


if __name__ == "__main__":
    main()
