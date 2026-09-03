"""Dress the corridor spine on the decks the mission route uses.

The six route rooms were dressed first because they are where the objectives are. The corridor was
left greybox, and it is on screen more than any of them: it is the connection between every
objective, so a player walks its length four times. Cutting from a dressed room to a raw grey tube
and back reads worse than a level that is roughly finished all the way through.

All four decks. The mission route only uses decks 2 and 3, and the first version of this script
dressed only those on the grounds that nothing sends a player down the others.
That was right for a player and wrong for a camera: decks 1 and 4 are reachable through the hatches,
so leaving them grey turns "do not point the camera there" into a constraint on every shot. Another
320 actors is a cheap price for not having to think about it while filming.

The corridor is 144 m long, 3.6 m wide, and about 3.9 m from deck to deckhead. Wall pieces are 50 cm
deep and stand inside that width, which leaves 2.6 m of walkable floor -- exactly the
`corridorWidthMeters: 2.6` in Config/ShipLayout.json. That the numbers agree is a coincidence worth
recording rather than relying on, since the map disagrees with that config on every other dimension
(see TRO-243).

Same technique as the room pass: hide the greybox renderers and lay kit geometry over them, never
delete. The greybox carries the collision the navmesh was built against.

Idempotent: tagged, and re-running restores every hidden actor before dressing again.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/dress_demo_corridors.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
TAG = "GeneratedCorridorDressing"
HIDDEN_TAG = "CorridorDressingHidGreybox"

KIT_ROOT = "/Game/Modular_Scifi_Mechanic_Base"

# Corridor geometry, measured from the map rather than assumed. Centre of each deck's corridor
# section sits at these Z values; the floor is 205 below and the deckhead 205 above.
DECK_CENTRE_Z = {1: 215.0, 2: 735.0, 3: 1255.0, 4: 1775.0}
DECKS = [1, 2, 3, 4]

CORRIDOR_HALF_LENGTH = 7200.0
CORRIDOR_HALF_WIDTH = 180.0
FLOOR_DROP = 195.0          # floor surface below the section centre
CEILING_RISE = 195.0        # deckhead above it

# Kit module dimensions every offset below is derived from.
FLOOR_TILE = 300.0
WALL_DEPTH = 50.0          # kit wall panels stand this far inside the shell
CEILING_TILE = 900.0

# Structural bay spacing. The greybox ribs sit every 12 m and the rooms are on the same pitch, so
# lighting and detail land on the existing rhythm rather than fighting it.
BAY = 1200.0

# Corridor lighting, and the thing seven renders were needed to understand.
#
# The corridor would not get darker. Point lights went 1200 -> 340 -> 90 -> 420 -> 120; the kit's
# emissive ceiling fixtures were dimmed eight-fold; the map's auto-exposure floor was raised and
# then its ceiling. Every frame came back looking the same. tools/verify_demo_post_process.py then
# confirmed the post-process volume was real, unbound, and had every override actually applied --
# so the settings were not being ignored, and the changes genuinely were not reaching the image.
#
# They could not have. The map auto-exposes, and auto-exposure normalises average scene luminance
# to mid grey. Halving every light in a space is exactly the thing the eye then compensates for.
# Absolute brightness is not an available lever in an auto-exposed scene; it never was.
#
# What that leaves is *contrast*, and it explains the whole investigation. The engine room reads
# dark because it is lit by two practicals and instrument glow: exposure settles on the bright
# parts and everything else falls away. The corridor read bright because a fixture every 12 m with
# 14 m of reach lights every surface to roughly the same value -- and a frame that is uniform at any
# level normalises to mid grey. It was not too bright. It was too even.
#
# So the fixtures are now sparse and strong rather than dense and weak: one every other bay, with
# reach deliberately shorter than the gap so the pools do not join. What is lit is properly lit and
# what is not is properly dark, and the dark between them is what the emergency-lighting read was
# always meant to be.
#
# One earlier pass tried one light per 24 m and called the result black. That verdict is worth
# re-testing rather than trusting: it was recorded before any of this was understood, and a corridor
# with real gaps in it is supposed to have frames that are mostly dark.
BAY_PER_LIGHT = 2

CORRIDOR_LIGHT_COLOUR = unreal.LinearColor(1.0, 0.52, 0.20, 1.0)
CORRIDOR_LIGHT_INTENSITY = 1100.0

# Shorter than the 24 m spacing on purpose. Reach that exceeds the gap is what made every previous
# pass uniform, and uniform is the actual fault.
#
# 850 was the first value tried and it overshot: with 8.5 m of reach against a 24 m spacing, roughly
# two thirds of the corridor received nothing at all and the render came back as a lit pocket in a
# black field. Right idea, too much of it.
#
# 1150 leaves the pools just short of meeting. There is still a measurable dip between fixtures --
# which is the whole point, and what was missing for five passes -- but the dark is a fall rather
# than an absence, and a player walking the corridor is never in a stretch with no light reaching
# them at all.
CORRIDOR_LIGHT_RADIUS = 1150.0


LAMP_MATERIAL = "/Game/Assets/Gameplay/Materials/MI_EmergencyFixture_Dim"
LAMP_EMISSIVE_SLOT = 1


MESH_INDEX = {}


def build_mesh_index():
    """Map kit mesh names to package paths.

    The pack files meshes under Mesh/SM/SRTUCTURE/... -- the misspelling is the pack's -- and
    scatters props across sibling folders, so a hardcoded path is a guess that rots.
    """
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    index = {}
    for asset in registry.get_assets_by_path(KIT_ROOT, recursive=True):
        if str(asset.asset_class_path.asset_name) == "StaticMesh":
            index[str(asset.asset_name)] = str(asset.package_name)
    return index


class Dresser(object):
    def __init__(self, actor_subsystem):
        self.actors = actor_subsystem
        self.cache = {}
        self.spawned = 0
        self.dimmed = 0
        self.lamp_material = None

    def mesh(self, name):
        if name not in self.cache:
            path = MESH_INDEX.get(name)
            if not path:
                unreal.log_warning("Kit mesh not in index: {}".format(name))
                self.cache[name] = None
            else:
                self.cache[name] = unreal.EditorAssetLibrary.load_asset(path)
        return self.cache[name]

    def place(self, mesh_name, location, rotation=None, scale=None):
        mesh = self.mesh(mesh_name)
        if not mesh:
            return None

        actor = self.actors.spawn_actor_from_class(
            unreal.StaticMeshActor, location, rotation or unreal.Rotator(0, 0, 0))
        if not actor:
            return None

        component = actor.static_mesh_component
        component.set_static_mesh(mesh)
        # Visual only: the greybox underneath still carries the collision, and a second collider in
        # the same place can push a player through a wall. use_default_collision has to be off
        # first: with it on, the component re-derives collision from the mesh asset on every load,
        # and the NO_COLLISION below silently reverted on reload -- every panel in the map was solid.
        component.set_editor_property("use_default_collision", False)
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        component.set_mobility(unreal.ComponentMobility.STATIC)
        if scale:
            actor.set_actor_scale3d(scale)

        actor.tags = [TAG]
        actor.set_actor_label("CorridorDress_{}_{}".format(mesh_name, self.spawned))
        self.spawned += 1
        return actor

    def dim_fixture(self, actor):
        """Swap a placed fixture's emissive slot for the emergency one.

        Silent about a missing material would be the wrong failure here: the whole corridor lighting
        pass hinges on this override landing, and three earlier passes were spent on a change that
        was not doing anything. If the material is not there, say so.
        """
        if not actor:
            return False

        if self.lamp_material is None:
            self.lamp_material = unreal.EditorAssetLibrary.load_asset(LAMP_MATERIAL)
            if self.lamp_material is None:
                unreal.log_error(
                    "Could not load {}; corridor fixtures will stay at kit brightness. "
                    "Run tools/build_emergency_lighting_materials.py first.".format(LAMP_MATERIAL))

        if self.lamp_material is None:
            return False

        component = actor.static_mesh_component
        if component.get_num_materials() <= LAMP_EMISSIVE_SLOT:
            unreal.log_warning("{} has no slot {}; leaving it alone".format(
                actor.get_actor_label(), LAMP_EMISSIVE_SLOT))
            return False

        component.set_material(LAMP_EMISSIVE_SLOT, self.lamp_material)
        self.dimmed += 1
        return True

    def light(self, location):
        light = self.actors.spawn_actor_from_class(unreal.PointLight, location)
        if not light:
            return None
        component = light.point_light_component
        component.set_editor_property("intensity", CORRIDOR_LIGHT_INTENSITY)
        component.set_light_color(CORRIDOR_LIGHT_COLOUR)
        component.set_editor_property("attenuation_radius", CORRIDOR_LIGHT_RADIUS)
        component.set_editor_property("source_radius", 60.0)
        component.set_editor_property("cast_shadows", True)
        # Movable, not static. A static light needs a baked lightmap and until one exists Unreal
        # stamps "Preview" over every surface it touches, which is what ruined the first review
        # renders of the room pass. Lumen wants dynamic anyway.
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
        light.tags = [TAG]
        light.set_actor_label("CorridorDress_Light_{}".format(self.spawned))
        self.spawned += 1
        return light


# The generator cuts a 250 cm gap between InnerWall segments at every door. A wall run laid
# straight across it is not a collision problem -- dressing is visual only -- but it is a wall
# drawn over a doorway, and the doorway audit found exactly that on 88 of 96 doors.
DOOR_GAP_HALF = 125.0


def door_gaps(actor_subsystem, floor_z, side_y):
    """X-intervals of the door gaps along one corridor wall of one deck, from the placed doors."""
    gaps = []
    for actor in actor_subsystem.get_all_level_actors():
        if "RoomThresholdDoor" not in [str(t) for t in actor.tags]:
            continue
        loc = actor.get_actor_location()
        # Doors are spawned at floor_z - 10; decks are far more than 200 apart.
        if abs(loc.z + 10.0 - floor_z) > 200.0:
            continue
        if (loc.y > 0.0) != (side_y > 0.0):
            continue
        gaps.append((loc.x - DOOR_GAP_HALF, loc.x + DOOR_GAP_HALF))
    return gaps


def place_wall_pieces(dresser, mesh_name, x0, x1, y, rotation, floor_z, gaps, native_width):
    """Places a wall run as whatever pieces remain once the door gaps crossing it are removed."""
    intervals = [(x0, x1)]
    for gap_start, gap_end in gaps:
        remaining = []
        for a, b in intervals:
            if gap_end <= a or gap_start >= b:
                remaining.append((a, b))
                continue
            if a < gap_start:
                remaining.append((a, gap_start))
            if gap_end < b:
                remaining.append((gap_end, b))
        intervals = remaining
    for a, b in intervals:
        width = b - a
        if width < 20.0:
            continue
        dresser.place(mesh_name, unreal.Vector((a + b) * 0.5, y, floor_z), rotation,
            unreal.Vector(width / native_width, 1.0, 1.0))


def dress_deck(dresser, centre_z):
    floor_z = centre_z - FLOOR_DROP
    ceiling_z = centre_z + CEILING_RISE

    # --- floor ------------------------------------------------------------------------------
    # 400 x 360 tiles, mildly scaled from the 300 square. Larger tiles would stretch the panel
    # pattern far enough to read as a texture error rather than as a deck.
    tile_x = 400.0
    tiles = int((CORRIDOR_HALF_LENGTH * 2.0) / tile_x)
    for index in range(tiles):
        x = -CORRIDOR_HALF_LENGTH + tile_x * (index + 0.5)
        dresser.place("SM_FLOOR_05",
            unreal.Vector(x, 0.0, floor_z), None,
            unreal.Vector(tile_x / FLOOR_TILE, (CORRIDOR_HALF_WIDTH * 2.0) / FLOOR_TILE, 1.0))

    # --- side walls -------------------------------------------------------------------------
    # Every panel here is natively 400 wide and placed on a 400 pitch, so nothing is scaled at all
    # and 144 m divides into exactly 36 of them.
    #
    # The first version mixed SM_WALL_10 (700 native) with SM_WALL_07 (400 native) on a shared 600
    # run, which stretched the narrower panel by half its width. Wall panels are the one surface a
    # player walks past slowly and close to, and a 50% horizontal stretch on a regular panel
    # pattern is obvious at that range. Variety is better bought from three different meshes than
    # from distorting one.
    run = 400.0
    panels = ["SM_WALL_09", "SM_WALL_12", "SM_WALL_07"]
    runs = int((CORRIDOR_HALF_LENGTH * 2.0) / run)
    gaps_near = door_gaps(dresser.actors, floor_z, -CORRIDOR_HALF_WIDTH)
    gaps_far = door_gaps(dresser.actors, floor_z, CORRIDOR_HALF_WIDTH)
    for index in range(runs):
        x = -CORRIDOR_HALF_LENGTH + run * (index + 0.5)
        # Different offsets per side, so the two walls are not mirror images of each other.
        near = panels[index % len(panels)]
        far = panels[(index + 1) % len(panels)]
        place_wall_pieces(dresser, near, x - run * 0.5, x + run * 0.5, -CORRIDOR_HALF_WIDTH,
            unreal.Rotator(0, 0, 0), floor_z, gaps_near, run)
        place_wall_pieces(dresser, far, x - run * 0.5, x + run * 0.5, CORRIDOR_HALF_WIDTH,
            unreal.Rotator(0, 180, 0), floor_z, gaps_far, run)

    # --- deckhead ---------------------------------------------------------------------------
    ceil_x = 900.0
    ceil_tiles = int((CORRIDOR_HALF_LENGTH * 2.0) / ceil_x)
    for index in range(ceil_tiles):
        x = -CORRIDOR_HALF_LENGTH + ceil_x * (index + 0.5)
        dresser.place("SM_CEILING_09",
            unreal.Vector(x, 0.0, ceiling_z - 25.0), None,
            unreal.Vector(ceil_x / CEILING_TILE,
                          (CORRIDOR_HALF_WIDTH * 2.0) / CEILING_TILE, 1.0))

    # --- bay rhythm: lamps, and a cable run overhead -------------------------------------------
    bays = int((CORRIDOR_HALF_LENGTH * 2.0) / BAY)
    for index in range(bays):
        x = -CORRIDOR_HALF_LENGTH + BAY * (index + 0.5)

        # Along the corridor, not across it. SM_LAMP_04 is 610 long and the corridor is 360 wide,
        # so turning it broadside pushed 125cm of emissive fixture through each wall and lit them
        # from inside -- one side of every review render was blown to white and the lamp read as a
        # cyan pole standing in the middle of the floor. Run with the axis it fits on.
        lamp = dresser.place("SM_LAMP_04",
            unreal.Vector(x, 0.0, ceiling_z - 45.0), unreal.Rotator(0, 0, 0))
        dresser.dim_fixture(lamp)

        # Every other bay, not every bay. The dark between fixtures is the point: with
        # auto-exposure normalising the average, a corridor lit evenly end to end reads as mid grey
        # however little light is in it, and only real gaps produce real darkness.
        if index % BAY_PER_LIGHT == 0:
            dresser.light(unreal.Vector(x, 0.0, ceiling_z - 110.0))

        # Cable trunk along one side only, so the two walls are not mirror images.
        dresser.place("SM_CABLE_01",
            unreal.Vector(x - BAY * 0.25, -CORRIDOR_HALF_WIDTH + 70.0, ceiling_z - 70.0),
            unreal.Rotator(0, 0, 0), unreal.Vector(BAY / 200.0, 1.0, 1.0))


def restore_greybox(actors):
    restored = 0
    for actor in actors:
        if HIDDEN_TAG not in [str(t) for t in actor.tags]:
            continue
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            component.set_visibility(True)
        actor.tags = [t for t in actor.tags if str(t) != HIDDEN_TAG]
        restored += 1
    return restored


def hide_corridor_greybox(actors, deck):
    """Hide the greybox tube for one deck, keeping its collision.

    Matched on both the deck suffix in the label and the mesh being the engine Cube primitive.
    Label alone was not enough in the room pass -- it missed seven kinds of actor -- and mesh alone
    would reach into the rooms, which have already been dressed by another script.
    """
    suffix = "_D{:02d}".format(deck)
    hidden = 0
    for actor in actors:
        if not isinstance(actor, unreal.StaticMeshActor):
            continue
        tags = [str(t) for t in actor.tags]
        if TAG in tags:
            continue

        label = actor.get_actor_label()
        if "Corridor" not in label or suffix not in label:
            continue

        greybox = [c for c in actor.get_components_by_class(unreal.StaticMeshComponent)
                   if c.get_editor_property("static_mesh")
                   and c.get_editor_property("static_mesh").get_name() == "Cube"]
        if not greybox:
            continue

        for component in greybox:
            component.set_visibility(False)
        if HIDDEN_TAG not in tags:
            actor.tags = list(actor.tags) + [HIDDEN_TAG]
        hidden += 1
    return hidden


def main():
    global MESH_INDEX
    MESH_INDEX = build_mesh_index()
    unreal.log("Indexed {} kit meshes".format(len(MESH_INDEX)))
    if not MESH_INDEX:
        unreal.log_error("No kit meshes under {}; refusing to dress nothing".format(KIT_ROOT))
        return

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

    actors = actor_subsystem.get_all_level_actors()
    restored = restore_greybox(actors)
    if removed or restored:
        unreal.log("Cleared {} dressing actor(s), restored {} greybox actor(s)".format(
            removed, restored))
        actors = actor_subsystem.get_all_level_actors()

    dresser = Dresser(actor_subsystem)
    for deck in DECKS:
        before = dresser.spawned
        hidden = hide_corridor_greybox(actors, deck)
        dress_deck(dresser, DECK_CENTRE_Z[deck])
        unreal.log("  Deck {:02d}: hid {:>3} greybox, placed {:>4}".format(
            deck, hidden, dresser.spawned - before))

    saved = level_subsystem.save_current_level()
    unreal.log("Dressed {} deck(s) with {} actor(s), {} fixture(s) dimmed. Saved {}: {}".format(
        len(DECKS), dresser.spawned, dresser.dimmed, MAP_PATH, saved))

    # Reported because it is the number that matters and the one nothing else would show. A run
    # that places 640 actors and dims zero fixtures has the corridor lighting exactly as wrong as
    # it was for three passes, and the actor count would look identical.
    if dresser.dimmed == 0:
        unreal.log_error("No fixtures were dimmed; the corridors are still lit by the kit emissive")


if __name__ == "__main__":
    main()
