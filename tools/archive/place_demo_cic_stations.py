"""Put the actual ship systems into the demo map's Combat Information Center.

The last objective in the demo chain is "Bring the Combat Information Center online" -- crank the
door override, enter the command room, boot the tactical console. The room was empty. A player
completed the whole mission chain to reach a command centre containing one console and nothing to
command.

Three of these are not set dressing. Each one is the only thing standing between a written system
and a system that never runs:

  * ASensorArraySystem. ComputeFalsificationChance guards its sensor lookup with `if (Sensors)`,
    so with none in the world the array's falsification resistance was never applied and every
    jump readout was falsified at the base rate no matter what. It is also what the survey widget
    and contact tracking hang off, and the HUD's whole navigation readout is gated on a cached
    sensor array -- so that readout could never draw either.

  * AShipHelmSystem. ExecuteJump sums CurrentHeadingOffset across every helm to compute
    PendingLandingErrorSeverityBonus. With no helm the sum is always zero, so the landing-error
    branch could not fire under any circumstances -- it was unreachable rather than untested.

  * AJumpConsoleSystem. Without it there is no player-facing way to choose a destination at all,
    which leaves the entire jump loop reachable only from code. bAutoSelectFirstCandidate is the
    class's own documented demo fallback for having no Blueprint picker attached, which is exactly
    the situation here.

Deliberately not placed: life support and the self-destruct console. The district director puts
those on the same bridge, but on this ship they belong in engineering, and dropping them into the
CIC to tick a box would put them somewhere the layout argues against. They are a separate placement
question, not part of making the command room command anything.

Anchored on the CIC console the mission chain already routes the player to, and oriented to face
it, so the room reads as a command centre rather than three consoles scattered on a floor.

Also places the room's furniture -- two chairs and a holographic plot -- which is dressing rather
than system, but belongs here rather than in dress_demo_slice.py for a specific reason. The slice
dresser works in room-local coordinates and knows nothing about where the stations ended up; this
script knows exactly where they are, because it put them there. A chair placed without that
knowledge lands inside a console, and a centrepiece placed at the room origin lands inside the
tactical console, which is the anchor.

Every furniture position is checked against the room's inner wall face before it is spawned, and
skipped with a loud log if it does not clear. The jump console spent its whole life inside a
bulkhead because an offset was computed on paper and never verified; nothing here repeats that.

Idempotent: tagged and matched on re-run, so this replaces its own stations and never touches
hand-placed ones.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/place_demo_cic_stations.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import math

import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
TAG = "GeneratedDemoCICStation"

# Offsets from the CIC console, and the yaw turn that points each station back toward it. Laid out
# as a working arc rather than a row: the sensor array and the helm flank the tactical console
# because those two are read together, and the jump console sits opposite because committing to a
# destination is the decision you make after reading them.
STATIONS = [
    dict(
        cls="SensorArraySystem", label="CIC_SensorArray",
        name="Open Sensor Survey", offset=(-260.0, -300.0, 0.0), yaw=45.0,
    ),
    dict(
        cls="ShipHelmSystem", label="CIC_HelmNavigation",
        name="Helm Navigation", offset=(260.0, -300.0, 0.0), yaw=-45.0,
    ),
    dict(
        # 340 put this at y=1265 against a room whose inner wall face is at 1071, so the console
        # spent its whole life buried in the bulkhead. The offset has to clear the wall thickness,
        # not just the room's nominal half-extent: the kit's wall pieces are 109cm deep and stand
        # inside the shell. Verified against the live editor rather than recomputed on paper.
        cls="JumpConsoleSystem", label="CIC_JumpConsole",
        name="Select Jump Destination", offset=(0.0, 75.0, 0.0), yaw=180.0,
    ),
]


# Furniture, from packs the project already owns. The mechanic-base kit this map is otherwise
# dressed from has no seating and no holographic anything, so a command centre built only from it
# is a room with consoles standing in it and nobody working there.
#
# Bounds measured by tools/measure_cic_console_candidates.py before any of this was placed:
#   SM_chair             93 x  91 x 129   base pivot
#   SM_hologram_support 125 x 125 x  45   base pivot
#   SM_planet_hologram  163 x 163 x 165   CENTRE pivot
#
# The pivot difference is the only fiddly part. The support sits on the deck at Z+0; the sphere is
# authored around its own centre, so placing it the same way buries half of it in the plinth. It
# wants the plinth height plus its own half-height, plus a little air so it reads as projected
# rather than resting.
CHAIR_MESH = "/Game/Ice_Station/Meshes/Chair/SM_chair"
HOLO_SUPPORT_MESH = "/Game/Ice_Station/Meshes/Hologram/SM_hologram_support"
HOLO_SPHERE_MESH = "/Game/Ice_Station/Meshes/Hologram/SM_planet_hologram"

HOLO_SUPPORT_HEIGHT = 45.0
HOLO_SPHERE_RADIUS = 82.0
HOLO_AIR_GAP = 12.0

# How far behind a station its operator sits. Enough to clear the console's own depth and the
# chair's, without putting the occupant out of arm's reach of the thing they are operating.
CHAIR_SETBACK = 95.0

# Stations that are worked sitting down. The jump console is not one: committing to a destination
# is a thing you stand up to do, and a chair in front of it would also sit in the doorway approach.
SEATED_STATIONS = ("CIC_SensorArray", "CIC_HelmNavigation")

# How far inside the room's shell furniture has to land. Matches the margin
# Ginnungagap.Smoke.DemoReachability uses on stations: the kit's wall panels stand inside the
# room's nominal bounds, so clearing the bounds is not the same as clearing the wall.
WALL_INSET = 110.0


def containing_room(actors, point):
    """The ModularShipRoom whose inner volume contains a point, or None.

    Compared against the inner wall face rather than the room's bounds. A prop can be inside a
    room's bounding box and inside its bulkhead at the same time, which is the failure this exists
    to prevent.
    """
    for actor in actors:
        if actor.get_class().get_name() != "ModularShipRoom":
            continue
        origin, extent = actor.get_actor_bounds(False)
        if (abs(point.x - origin.x) <= extent.x - WALL_INSET
                and abs(point.y - origin.y) <= extent.y - WALL_INSET
                and abs(point.z - origin.z) <= extent.z):
            return actor
    return None


def place_prop(actor_subsystem, rooms, mesh_path, location, yaw, label):
    """Spawn one piece of dressing, refusing rather than guessing if it is not clear of the walls."""
    if containing_room(rooms, location) is None:
        unreal.log_warning(
            "Skipping {}: ({:.0f}, {:.0f}, {:.0f}) is not clear of any room's inner face".format(
                label, location.x, location.y, location.z))
        return None

    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not mesh:
        unreal.log_warning("Skipping {}: could not load {}".format(label, mesh_path))
        return None

    actor = actor_subsystem.spawn_actor_from_class(
        unreal.StaticMeshActor, location, unreal.Rotator(0.0, yaw, 0.0))
    if not actor:
        unreal.log_error("Failed to spawn {}".format(label))
        return None

    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    # Visual only. The greybox under this room already carries its collision, and a second collider
    # in the same place fights the first.
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_mobility(unreal.ComponentMobility.STATIC)

    actor.set_actor_label(label)
    actor.tags = [TAG]
    return actor


def find_by_class_name(actors, class_name):
    for actor in actors:
        if actor.get_class().get_name() == class_name:
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
        unreal.log("Removed {} station(s) from a previous run".format(removed))
        actors = actor_subsystem.get_all_level_actors()

    anchor = find_by_class_name(actors, "QuickDemoCICConsole")
    if not anchor:
        unreal.log_error("No CIC console found; refusing to place the bridge somewhere arbitrary")
        return

    origin = anchor.get_actor_location()
    base_yaw = anchor.get_actor_rotation().yaw
    unreal.log("CIC console at ({:.0f}, {:.0f}, {:.0f}) facing {:.0f}".format(
        origin.x, origin.y, origin.z, base_yaw))

    placed = 0
    station_positions = {}
    for spec in STATIONS:
        cls = getattr(unreal, spec["cls"], None)
        if cls is None:
            unreal.log_error("Class {} is not exposed to Python; skipping".format(spec["cls"]))
            continue

        location = unreal.Vector(
            origin.x + spec["offset"][0],
            origin.y + spec["offset"][1],
            origin.z + spec["offset"][2],
        )
        rotation = unreal.Rotator(0.0, base_yaw + spec["yaw"], 0.0)

        station = actor_subsystem.spawn_actor_from_class(cls, location, rotation)
        if not station:
            unreal.log_error("Failed to spawn {}".format(spec["cls"]))
            continue

        station.set_actor_label(spec["label"])
        station.tags = [TAG]

        # The interaction prompt reads this, so a station without one offers the player a nameless
        # console. AShipSystemActor loads its own mesh in OnConstruction from SystemType, so the
        # visual needs nothing set here.
        station.set_editor_property("system_name", spec["name"])

        # The demo has no Blueprint destination picker, and the class carries its own fallback for
        # exactly that case. Without this the console opens onto nothing selectable.
        if spec["cls"] == "JumpConsoleSystem":
            station.set_editor_property("auto_select_first_candidate", True)

        unreal.log("  placed {:<22} \"{}\"".format(spec["cls"], spec["name"]))
        placed += 1
        station_positions[spec["label"]] = (location, rotation.yaw)

    # --- furniture ------------------------------------------------------------------------------
    # Done after the stations, from their final positions rather than from the offsets that were
    # asked for. Those are the same number today, but a station that gets nudged in the editor
    # should take its chair with it.
    rooms = actor_subsystem.get_all_level_actors()
    furnished = 0

    for label in SEATED_STATIONS:
        if label not in station_positions:
            continue
        station, station_yaw = station_positions[label]

        # Directly behind the console, along the line it faces. The stations are turned to face the
        # tactical console, so "behind" is away from it -- and taking the direction from the yaw
        # rather than from the anchor means a re-aimed station still seats its operator correctly.
        radians = math.radians(station_yaw)
        seat = unreal.Vector(
            station.x - math.cos(radians) * CHAIR_SETBACK,
            station.y - math.sin(radians) * CHAIR_SETBACK,
            station.z,
        )
        if place_prop(actor_subsystem, rooms, CHAIR_MESH, seat, station_yaw,
                      "CIC_Chair_" + label.replace("CIC_", "")):
            furnished += 1

    # The holographic plot goes at the room's own centre, not the anchor's -- the anchor is the
    # tactical console, so anything placed at its origin is placed inside it.
    room = containing_room(rooms, origin)
    if room is None:
        unreal.log_warning("The CIC console is not inside any room; skipping the holographic plot")
    else:
        room_origin, _ = room.get_actor_bounds(False)
        plot = unreal.Vector(room_origin.x, room_origin.y, origin.z)

        # Refuse if the room centre is where something already stands. A holographic table growing
        # out of a console is worse than no holographic table.
        clash = None
        for label, (station, _) in station_positions.items():
            if (plot - station).length() < 220.0:
                clash = label
                break
        if clash:
            unreal.log_warning(
                "Skipping the holographic plot: the room centre is within 220cm of {}".format(clash))
        else:
            if place_prop(actor_subsystem, rooms, HOLO_SUPPORT_MESH, plot, base_yaw,
                          "CIC_HolographicPlot_Support"):
                furnished += 1
            sphere = unreal.Vector(
                plot.x, plot.y,
                plot.z + HOLO_SUPPORT_HEIGHT + HOLO_SPHERE_RADIUS + HOLO_AIR_GAP)
            if place_prop(actor_subsystem, rooms, HOLO_SPHERE_MESH, sphere, base_yaw,
                          "CIC_HolographicPlot_Sphere"):
                furnished += 1

    saved = level_subsystem.save_current_level()
    unreal.log("Placed {} CIC station(s) and {} piece(s) of furniture. Saved {}: {}".format(
        placed, furnished, MAP_PATH, saved))


if __name__ == "__main__":
    main()
