"""Dress the demo's vertical-slice route with Fab kit geometry.

The map was a literal greybox: 2043 of its ~2890 static meshes were /Engine/BasicShapes/Cube. The
systems all work and the layout is sound, but nothing in it could be filmed or shown to anyone.

Technique, and the reason for it: the cubes are not decoration, they ARE the architecture -- floor
slabs, wall panels, corner ribs and a 144-metre corridor spine per deck. They also carry the
collision the navmesh and every physics query were built against. So this hides their renderers and
lays Fab geometry over them rather than replacing them. Gameplay is bit-for-bit unchanged, the
navmesh does not move, and the eighty-three passing tests keep passing; only what the camera sees
changes. Deleting the greybox would have been the obvious approach and would have quietly rebuilt
the ship's collision under a demo that currently works.

Scope is the mission route, not the ship. Ninety-six rooms dressed to this standard would read as an
asset flip; the six named rooms the five-objective chain actually routes a player through, dressed
properly, read as a game. The other ninety are left greyboxed and unlit.

Every room is exactly 1100 x 1000 x 400 cm and the kit's wall height is exactly 400, so walls sit at
their authored height with no vertical scaling at all. Horizontal spans are covered by three pieces
per side scaled to fit -- an 8% squash on the long side and 17% on the short -- rather than by
overlapping full-size pieces, because two coplanar wall faces in the same place z-fight and there is
no camera angle that hides it.

Idempotent: tagged, and re-running restores every hidden cube before dressing again, so this can be
re-run after layout changes without stranding invisible geometry.

Run through Unreal Editor Python:
    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/dress_demo_slice.py \
        -unattended -nop4 -nosplash -NullRHI -NoSound
"""

import math

import unreal

MAP_PATH = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
TAG = "GeneratedSliceDressing"
HIDDEN_TAG = "SliceDressingHidGreybox"

# What this pass supersedes and therefore hides.
#
# The engine Cube is the greybox shell, and was the whole of this set until the breach room got
# real growth. The three SM_FX_Bloom* meshes are the map's original concept dressing for an
# infestation: flat-shaded geometry-script primitives, and once six Alien_Cave_biome organisms
# stand in the same room they are simply the worse version of the same idea competing for the
# frame. They dominated the breach render entirely.
#
# Note these are *not* the meshes under Assets/Models/Bloom, which are creature rig parts and are
# used elsewhere. Same subject, different assets, and only these three are placed as room dressing.
#
# Hidden rather than destroyed, like the greybox: these carry no collision the navmesh needs, but
# keeping the rule uniform means a re-run can put any of it back.
SUPERSEDED_MESHES = {
    "Cube",
    "SM_FX_BloomNodule",
    "SM_FX_BloomTendril",
    "SM_FX_BloomCalcifiedRib",
}

KIT_ROOT = "/Game/Modular_Scifi_Mechanic_Base"

# Room interior, in centimetres. Uniform across all ninety-six rooms.
ROOM_X = 1100.0
ROOM_Y = 1000.0
ROOM_Z = 400.0

# Kit module dimensions this script relies on. Named rather than inlined because every offset below
# is derived from them, and a kit swap should fail loudly here instead of drifting silently.
WALL_W, WALL_H = 400.0, 400.0
# The generator cuts a 250 cm gap at each room's door, on the face toward the corridor.
DOOR_GAP_HALF = 125.0
FLOOR_TILE = 300.0
CEILING_TILE = 750.0

# The rooms the mission chain routes through, and how each should read. Anything not listed is left
# greyboxed on purpose.
ROOM_PROFILES = {
    "Cryogenic Recovery Bay": "cryo",
    "Player Workshop": "workshop",
    "Main Power Control": "engineering",
    "Main Engine Room": "engineering",
    "Bloom Impact / Vacuum Breach": "breach",
    "Combat Information Center": "command",
}

# Props per profile: (mesh, x, y, z-offset-from-floor, yaw). Positions are in room-local
# centimetres, kept clear of the middle so the player always has a path through and the stations
# already placed in these rooms are never buried.
# Where the growth comes from. Alien_Cave_biome rather than Alien_Biomass: the two carry the same
# thirteen organism meshes, and the cave pack also has the egg and plant groups if this ever wants
# more variety.
BIOMASS = "/Game/Alien_Cave_biome/Meshes/Alien_organism/"

# Lab capsules from SciFiWorld -- the Sci-Fi Creatures Research Lab pack, which installs under that
# name and was already in the project when its cryo capsules were wanted.
#
# Placed as bay furniture in the corners, *not* as a replacement for the four QuickDemo4D_CryoPod_*
# actors. Those are CryoPodSystem: interactable, with a LidPivot the lid animation hinges on and the
# player's wake sequence hanging off them. They are horizontal berths; these are upright capsules.
# Swapping the meshes would leave a hinge rotating a capsule's glass around an axis that means
# nothing, and would silently change where a player wakes up.
#
# Whether the crew sleeps lying down or standing is a fiction call rather than a mesh swap, so the
# functional pods keep their blockout for now and the room gains the capsules behind them. That is
# most of the visual win at none of the risk, and it is one script re-run to undo.
#
# SM_LabCapsule10 is the narrow one at 139 x 139 x 311. The wider capsules in the pack (up to
# 325 x 319) would not clear the 240cm pod spacing.
LAB_CAPSULE = "/Game/SciFiWorld/Meshes/"

# Industrial props from ModSci_EngiProps. Freestanding clutter rather than kit modules, which is the
# reason these can be used at all: the ModSci wall and floor modules are built on a 335cm grid
# against this map's 360cm corridors and 1200cm bays, and cannot go in without rebuilding the ship.
# A fire extinguisher has no grid.
#
# All measured by tools/survey_new_pack.py before placement. Nearly all are base-pivot, so they take
# the grounded path and sit on the deck without a hand-tuned Z; the few that are not are placed at an
# explicit height because they belong on a wall rather than a floor.
ENGI = "/Game/ModSci_EngiProps/Meshes/"

# Every piece of growth carries its own small light.
#
# The first pass placed the organisms and they nearly vanished. The room light was raised, and they
# were still the darkest thing in a dark room -- because these meshes are matte and organic, authored
# for a cave, and the brightest things in that frame are the kit floor's own emissive decals. The eye
# went to the floor stripes.
#
# Lighting the room harder was the wrong lever, for the same reason it was wrong in the corridors:
# the map auto-exposes, so what decides whether a thing reads is its contrast against the frame, not
# the absolute light on it. A growth lit from across the room competes with the floor. A growth lit
# from inside itself does not.
#
# Violet because that is the Bloom's colour everywhere else in the project, and because a light that
# is not one of the ship's own colours is the fastest way to say a thing does not belong here.
#
# Small radius on purpose. This is a glow in a mass, not a lamp: it should pick out the silhouette
# and the near surfaces and reach nothing else. At 380 it dies well before the walls.
# 900 across six of these lit the growth perfectly and flooded the room doing it -- walls, deck
# plating and ceiling all washed violet, and the room stopped being dark at all. Six small lights
# add up to one big one, which is obvious in hindsight and was not before seeing it.
#
# 220 keeps the growth the brightest thing in frame and lets everything past arm's reach of it fall
# away again. The room has to stay dark for the growth to be worth looking at: what makes a thing
# read is its contrast against the frame, and a violet room with violet growth in it has none.
GROWTH_LIGHT_COLOUR = unreal.LinearColor(0.62, 0.24, 1.0, 1.0)
GROWTH_LIGHT_INTENSITY = 220.0
GROWTH_LIGHT_RADIUS = 300.0

# How far up from the deck the light sits inside the mass. Low, so the growth is lit from within its
# own bulk and throws its shape upward rather than being flatly front-lit.
GROWTH_LIGHT_HEIGHT = 55.0

PROPS = {
    "engineering": [
        # Industrial clutter along the walls. Positions hug the shell where the kit dressing and the
        # station meshes are not, and yaws are deliberately off-square -- a room where every prop
        # faces an axis reads as placed rather than used.
        (ENGI + "SM_NitrogenTank_Covered", -430.0, -430.0, None, 18.0),
        (ENGI + "SM_WaterDrum", 430.0, -440.0, None, -35.0),
        (ENGI + "SM_WireReel_A", -430.0, 430.0, None, 62.0),
        (ENGI + "SM_Wire_Floor_A", 180.0, -300.0, None, 8.0),
        (ENGI + "SM_SafetySwitch", 430.0, 200.0, None, -90.0),
        (ENGI + "SM_PortableLight", 300.0, 430.0, None, 145.0),
        ("SM_POWER_GENERATOR_01", -380.0, -330.0, 0.0, 0.0),
        ("SM_CABLE_MASS_02", -480.0, 300.0, 0.0, 0.0),
        ("SM_CABLE_MASS_03", -300.0, 400.0, 0.0, 25.0),
        ("SM_ELECTRIC_BOX_01_OPEN", 480.0, -180.0, 160.0, -90.0),
        ("SM_PIPE_03", 0.0, 470.0, 330.0, 0.0),
        ("SM_PIPE_04", 0.0, -470.0, 330.0, 0.0),
        ("SM_BARREL_01", 430.0, 380.0, 0.0, 15.0),
        ("SM_BARREL_01", 470.0, 300.0, 0.0, -40.0),
    ],
    "workshop": [
        # A workshop is the one room where loose tools are the point -- a bench with nothing on the
        # floor around it reads as a showroom.
        (ENGI + "SM_Toolbox", -300.0, 430.0, None, 24.0),
        (ENGI + "SM_Case_A", 380.0, -420.0, None, -18.0),
        (ENGI + "SM_PlasticPallet", -430.0, -380.0, None, 40.0),
        (ENGI + "SM_RubberMat_Flat", 120.0, 200.0, None, 12.0),
        (ENGI + "SM_WireReel_A", 430.0, 400.0, None, -55.0),
        (ENGI + "SM_Wrench", -240.0, 250.0, None, 78.0),
        ("SM_MECHE_STAND_01", -360.0, 330.0, 0.0, 0.0),
        ("SM_COMPUTER_01", 480.0, 200.0, 0.0, -90.0),
        ("SM_BARREL_03", -480.0, -350.0, 0.0, 0.0),
        ("SM_BARREL_01", -430.0, -250.0, 0.0, 20.0),
        ("SM_ELECTRIC_BOX_01_CLOSE", 490.0, -300.0, 170.0, -90.0),
        ("SM_PIPE_01", 0.0, 470.0, 340.0, 0.0),
    ],
    "cryo": [
        # Sparse on purpose. A cryo bay is a clean room that has been left alone, not a workshop --
        # what belongs here is gas and monitoring, not tools.
        (ENGI + "SM_OxygenTank", -450.0, 120.0, None, 15.0),
        (ENGI + "SM_OxygenTank", -450.0, 190.0, None, -22.0),
        (ENGI + "SM_Wire_Floor_B", 260.0, 250.0, None, 95.0),
        ("SM_COMPUTER_02", 470.0, 330.0, 0.0, -90.0),
        # Beside the doorway, not across it: (0, 495) is the door-face centre, and the generator's
        # 250 cm gap is there. Still on the wall a player faces coming in from the corridor.
        ("SM_WALL_08_DISPLAY", -340.0, 495.0, 0.0, 0.0),
        ("SM_CABLE_MASS_01", -490.0, -400.0, 0.0, 0.0),
        ("SM_PIPE_01", 0.0, -470.0, 340.0, 0.0),

        # Standing capsules in the four corners. Positions are clear of everything the room already
        # holds, checked against the measured layout rather than eyeballed: the four functional pods
        # sit at x -360/-120/+120/+360 on y -180, and the suit recesses at y +265 across the same x
        # span. At x +-390 a 139-wide capsule spans 320..460, inboard of the 470 inner wall face and
        # outboard of both rows.
        #
        # Glass is a separate mesh with an offset pivot where the body is base-pivot, which is why
        # both go through place_grounded rather than a fixed Z.
        (LAB_CAPSULE + "SM_LabCapsule10_Capsule", -390.0, -390.0, None, 35.0, 1.0),
        (LAB_CAPSULE + "SM_LabCapsule10_Glass", -390.0, -390.0, None, 35.0, 1.0),
        (LAB_CAPSULE + "SM_LabCapsule10_Capsule", 390.0, -390.0, None, -35.0, 1.0),
        (LAB_CAPSULE + "SM_LabCapsule10_Glass", 390.0, -390.0, None, -35.0, 1.0),
        (LAB_CAPSULE + "SM_LabCapsule10_Capsule", -390.0, 390.0, None, 145.0, 1.0),
        (LAB_CAPSULE + "SM_LabCapsule10_Glass", -390.0, 390.0, None, 145.0, 1.0),
        (LAB_CAPSULE + "SM_LabCapsule10_Capsule", 390.0, 390.0, None, -145.0, 1.0),
        (LAB_CAPSULE + "SM_LabCapsule10_Glass", 390.0, 390.0, None, -145.0, 1.0),
    ],
    "command": [
        ("SM_COMPUTER_01", -470.0, -300.0, 0.0, 90.0),
        ("SM_COMPUTER_02", -470.0, 300.0, 0.0, 90.0),
        # Beside the doorway, not across it: (0, 495) is the door-face centre, and the generator's
        # 250 cm gap is there. Still on the wall a player faces coming in from the corridor.
        ("SM_WALL_08_DISPLAY", -340.0, 495.0, 0.0, 0.0),
        ("SM_LIGHTBRACKET_02", 0.0, 0.0, 390.0, 0.0),
    ],
    # A room that has already failed. Everything here is knocked out of true on purpose: the
    # difference between a breach and a store room is that nothing in a breach is where it was left.
    #
    # The Bloom growth comes from Alien_Cave_biome, which this project already owns and had never
    # used. Everything under Assets/Models/Bloom is 25-204cm and is *creature rig parts* -- head,
    # torso, leg, tendril -- so the breach had been dressed with pieces of monster. That is why the
    # render came back as white slabs and purple tubes: there was no environmental infestation asset
    # in the project at all.
    #
    # Heights are given as None where the mesh should sit on the deck. These meshes have offset and
    # centred pivots rather than based ones, so a fixed Z would bury some and float others -- see
    # place_grounded. Measured by tools/measure_bloom_dressing_candidates.py.
    "breach": [
        # Same rule as the rest of this profile: nothing is where it was left. The drum and the
        # extinguisher are on the floor because whatever happened here put them there.
        (ENGI + "SM_WaterDrum", 210.0, 300.0, None, 74.0),
        (ENGI + "SM_FireExtinguisher", -180.0, 330.0, None, -40.0),
        (ENGI + "SM_RubberMat_Rolled", 340.0, 120.0, None, 28.0),
        (ENGI + "SM_Wire_Floor_A", -80.0, 400.0, None, -12.0),
        # The mass that came through the hull. 06 is 835 x 721 x 255, so it spreads across most of
        # the floor at full size; scaled down it is a thing you walk around rather than the room.
        (BIOMASS + "SM_alien_organism_06", 120.0, -120.0, None, 24.0, 0.55),
        # A column climbing the aft corner, and two smaller nodes near it. Growth reads as growth
        # when it has a direction -- one big mass on the floor is a rock.
        (BIOMASS + "SM_alien_organism_11", -390.0, 300.0, None, -50.0, 0.85),
        (BIOMASS + "SM_alien_organism_12", -300.0, 175.0, None, 130.0, 1.0),
        (BIOMASS + "SM_alien_organism_13", -430.0, 90.0, None, 70.0, 0.9),
        # Spread toward the doorway, so the first thing visible from the corridor is that this room
        # is wrong rather than merely dark.
        (BIOMASS + "SM_alien_organism_07", 330.0, -430.0, None, -15.0, 1.0),
        (BIOMASS + "SM_alien_organism_08", 90.0, -455.0, None, 95.0, 0.8),
        ("SM_BARREL_01", -300.0, 380.0, 0.0, 62.0),
        ("SM_BARREL_02", -180.0, 430.0, 0.0, -35.0),
        ("SM_BARREL_03", 250.0, -400.0, 0.0, 78.0),
        ("SM_CABLE_MASS_04", 470.0, -420.0, 0.0, 18.0),
        ("SM_CABLE_01", -100.0, -200.0, 0.0, 41.0),
        ("SM_PIPE_02", 380.0, 430.0, 220.0, 33.0),
        ("SM_ELECTRIC_BOX_01_OPEN", -490.0, 100.0, 150.0, 90.0),
    ],
}


# Wall variety per profile, so rooms are not interchangeable at a glance.
WALL_SETS = {
    "engineering": ["SM_WALL_09", "SM_WALL_07", "SM_WALL_12"],
    "workshop": ["SM_WALL_07", "SM_WALL_12", "SM_WALL_09"],
    "cryo": ["SM_WALL_12", "SM_WALL_07", "SM_WALL_12"],
    "command": ["SM_WALL_12", "SM_WALL_09", "SM_WALL_12"],
    "breach": ["SM_WALL_09", "SM_WALL_09", "SM_WALL_07"],
}

FLOOR_BY_PROFILE = {
    "engineering": "SM_FLOOR_09",
    "workshop": "SM_FLOOR_08",
    "cryo": "SM_FLOOR_05",
    "command": "SM_FLOOR_07",
    "breach": "SM_FLOOR_09",
}

# Room lighting, corrected after the corridor pass explained what was actually happening.
#
# These values were cut to roughly a quarter on the reasoning that the slice read as a working
# research station rather than a ship that had lost main power. In an auto-exposed scene that
# reasoning is void: exposure normalises average luminance, so lowering every light in a room does
# not darken it -- the eye simply opens further. What it does do is change what dominates.
#
# And what dominated was the fixtures. Each room places two SM_LAMP_04 at the kit's own emissive,
# which is an HDR value bright enough to pin exposure on its own. With the room lights cut to a
# quarter, the workshop and the breach rendered as two blown white strips in a black field: not
# atmosphere, just a wall of nothing with two lamps stuck to it.
#
# Two changes together, and they are one idea rather than two variables. The fixtures take the same
# dimmed skin the corridors got, so they stop being the brightest thing by an order of magnitude,
# and the lights come back up so the room is lit by lights rather than by the glow of a lamp
# housing. What the values are relative to each other is what matters; the absolute numbers are
# only meaningful against the fixture they now sit alongside.
#
# The rooms stay brighter than the corridors on purpose, so arriving somewhere is a relief rather
# than more of the same, and each keeps its own colour so a room is still identifiable from its
# doorway. Engineering stays warmest -- it was the one frame that already read as this game.
LIGHT_BY_PROFILE = {
    "engineering": (unreal.LinearColor(1.0, 0.55, 0.20, 1.0), 2400.0),
    "workshop": (unreal.LinearColor(1.0, 0.72, 0.42, 1.0), 2100.0),
    # Desaturated from (0.48, 0.70, 1.0). At that saturation the cryo bay was blue light on a
    # black hull, which gives dark blue blobs and no material -- the pods had just been given six
    # authored materials and none of them could be seen. Still unmistakably cold, but enough white
    # in it that oiled metal reads as metal.
    "cryo": (unreal.LinearColor(0.72, 0.86, 1.0, 1.0), 1900.0),
    "command": (unreal.LinearColor(0.62, 0.78, 1.0, 1.0), 2100.0),
    "breach": (unreal.LinearColor(1.0, 0.22, 0.14, 1.0), 1500.0),
}

# The dimmed fixture skin built by tools/build_emergency_lighting_materials.py, applied to room
# lamps for the same reason the corridors use it: the kit's emissive is authored for a lit ship.
# Slot 1 is the emissive face; slot 0 is the housing and stays as it is.
LAMP_MATERIAL = "/Game/Assets/Gameplay/Materials/MI_EmergencyFixture_Dim"
LAMP_EMISSIVE_SLOT = 1


def build_mesh_index():
    """Map every kit mesh name to its package path.

    The pack files its meshes under Mesh/SM/SRTUCTURE/{WALL,FLOOR,...} -- the misspelling is the
    pack's own -- and scatters props across sibling folders. Indexing by name from the asset
    registry means a hardcoded guess at that layout cannot rot, and a mesh that genuinely is not
    there fails loudly at lookup instead of silently placing nothing.
    """
    registry = unreal.AssetRegistryHelpers.get_asset_registry()
    index = {}
    for asset in registry.get_assets_by_path(KIT_ROOT, recursive=True):
        if str(asset.asset_class_path.asset_name) != "StaticMesh":
            continue
        index[str(asset.asset_name)] = str(asset.package_name)
    return index


MESH_INDEX = {}


def load_mesh(name):
    """A kit mesh by name, or any mesh in the project by full package path.

    The index only covers the mechanic-base kit, which is right for almost everything here. The
    exception is the breach: infestation is not a thing that kit has, and the project already owns
    two packs that do. A name beginning with /Game/ is taken as a path and looked up directly.
    """
    if name.startswith("/Game/"):
        mesh = unreal.EditorAssetLibrary.load_asset(name)
        if not mesh:
            unreal.log_warning("Mesh not found at path, skipping: {}".format(name))
        return mesh

    path = MESH_INDEX.get(name)
    if not path:
        unreal.log_warning("Kit mesh not in index, skipping: {}".format(name))
        return None
    return unreal.EditorAssetLibrary.load_asset(path)


class Dresser(object):
    def __init__(self, actor_subsystem):
        self.actors = actor_subsystem
        self.mesh_cache = {}
        self.spawned = 0
        self.dimmed = 0
        self.lamp_material = None
        self.pending_floor_z = 0.0

    def mesh(self, name):
        if name not in self.mesh_cache:
            self.mesh_cache[name] = load_mesh(name)
        return self.mesh_cache[name]

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

        # Dressing sits on top of greybox that already carries the collision. A second collider in
        # the same place would fight the first and can push a player through a wall, so these are
        # visual only. use_default_collision has to be off first: with it on, the component
        # re-derives collision from the mesh asset on every load and this reverted on reload.
        component.set_editor_property("use_default_collision", False)
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        component.set_mobility(unreal.ComponentMobility.STATIC)

        if scale:
            actor.set_actor_scale3d(scale)

        actor.tags = [TAG]
        actor.set_actor_label("Dressing_{}_{}".format(mesh_name, self.spawned))
        self.spawned += 1
        return actor

    # --- room shell ---------------------------------------------------------------------------
    def dress_shell(self, centre, floor_z, profile):
        walls = WALL_SETS.get(profile, WALL_SETS["engineering"])

        # Three pieces per side, scaled to cover exactly. Scaling horizontally rather than
        # overlapping full-size pieces: two coplanar wall faces in one place z-fight from every
        # angle, and a seam is easier to hide than a flicker.
        span_x, span_y = ROOM_X / 3.0, ROOM_Y / 3.0
        scale_x, scale_y = span_x / WALL_W, span_y / WALL_W

        # The face toward the corridor carries the door. Its middle piece would sit straight
        # across the generator's gap -- the doorway audit found exactly that -- so that face is
        # placed separately below as two pieces that stop at the gap.
        if centre.y < 0.0:
            door_face_y, door_rotation = centre.y + ROOM_Y * 0.5, unreal.Rotator(0, 180, 0)
        else:
            door_face_y, door_rotation = centre.y - ROOM_Y * 0.5, unreal.Rotator(0, 0, 0)

        for index in range(3):
            offset_x = -ROOM_X * 0.5 + span_x * (index + 0.5)
            offset_y = -ROOM_Y * 0.5 + span_y * (index + 0.5)
            name = walls[index % len(walls)]

            # Long sides, facing in along Y; the door face is skipped here.
            for face_y, rotation in ((centre.y - ROOM_Y * 0.5, unreal.Rotator(0, 0, 0)),
                                     (centre.y + ROOM_Y * 0.5, unreal.Rotator(0, 180, 0))):
                if abs(face_y - door_face_y) < 1.0:
                    continue
                self.place(name,
                    unreal.Vector(centre.x + offset_x, face_y, floor_z),
                    rotation, unreal.Vector(scale_x, 1.0, 1.0))

            # Short sides, facing in along X.
            self.place(name,
                unreal.Vector(centre.x - ROOM_X * 0.5, centre.y + offset_y, floor_z),
                unreal.Rotator(0, 90, 0), unreal.Vector(scale_y, 1.0, 1.0))
            self.place(name,
                unreal.Vector(centre.x + ROOM_X * 0.5, centre.y + offset_y, floor_z),
                unreal.Rotator(0, -90, 0), unreal.Vector(scale_y, 1.0, 1.0))

        # Door face: two pieces flanking the gap, scaled to meet it exactly.
        for index, (a, b) in enumerate(((-ROOM_X * 0.5, -DOOR_GAP_HALF), (DOOR_GAP_HALF, ROOM_X * 0.5))):
            width = b - a
            self.place(walls[index * 2 % len(walls)],
                unreal.Vector(centre.x + (a + b) * 0.5, door_face_y, floor_z),
                door_rotation, unreal.Vector(width / WALL_W, 1.0, 1.0))

        # Floor: a four-by-four grid, mildly scaled. Fewer, larger tiles would stretch the panel
        # pattern far enough to read as a texture error rather than a floor.
        floor_mesh = FLOOR_BY_PROFILE.get(profile, "SM_FLOOR_05")
        tiles_x, tiles_y = 4, 4
        step_x, step_y = ROOM_X / tiles_x, ROOM_Y / tiles_y
        for ix in range(tiles_x):
            for iy in range(tiles_y):
                self.place(floor_mesh,
                    unreal.Vector(
                        centre.x - ROOM_X * 0.5 + step_x * (ix + 0.5),
                        centre.y - ROOM_Y * 0.5 + step_y * (iy + 0.5),
                        floor_z),
                    None,
                    unreal.Vector(step_x / FLOOR_TILE, step_y / FLOOR_TILE, 1.0))

        # Ceiling: two by two, sitting just under the deckhead.
        ceil_step_x, ceil_step_y = ROOM_X / 2.0, ROOM_Y / 2.0
        for ix in range(2):
            for iy in range(2):
                self.place("SM_CEILING_07",
                    unreal.Vector(
                        centre.x - ROOM_X * 0.5 + ceil_step_x * (ix + 0.5),
                        centre.y - ROOM_Y * 0.5 + ceil_step_y * (iy + 0.5),
                        floor_z + ROOM_Z - 25.0),
                    None,
                    unreal.Vector(ceil_step_x / CEILING_TILE, ceil_step_y / CEILING_TILE, 1.0))

    def dim_fixture(self, actor):
        """Swap a placed fixture's emissive slot for the emergency one.

        Loud about a missing material rather than silent. Two rooms rendered as a black field with
        two blown strips in it precisely because the fixtures were at full kit brightness, and a
        run that places every actor and dims none would look identical in the log.
        """
        if not actor:
            return False

        if self.lamp_material is None:
            self.lamp_material = unreal.EditorAssetLibrary.load_asset(LAMP_MATERIAL)
            if self.lamp_material is None:
                unreal.log_error(
                    "Could not load {}; room fixtures stay at kit brightness. "
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

    # --- lighting -----------------------------------------------------------------------------
    def light_room(self, centre, floor_z, profile):
        colour, intensity = LIGHT_BY_PROFILE.get(profile, LIGHT_BY_PROFILE["engineering"])

        for offset in (-260.0, 260.0):
            self.dim_fixture(self.place("SM_LAMP_04",
                unreal.Vector(centre.x + offset, centre.y, floor_z + ROOM_Z - 40.0),
                unreal.Rotator(0, 90, 0)))

            light = self.actors.spawn_actor_from_class(
                unreal.PointLight,
                unreal.Vector(centre.x + offset, centre.y, floor_z + ROOM_Z - 90.0))
            if not light:
                continue

            component = light.point_light_component
            component.set_editor_property("intensity", intensity)
            component.set_light_color(colour)
            component.set_editor_property("attenuation_radius", 900.0)
            component.set_editor_property("source_radius", 70.0)
            component.set_editor_property("cast_shadows", True)

            # Movable, not static. A static light needs a baked lightmap, and until one is built
            # Unreal stamps "Preview" across every surface it touches -- which is what covered the
            # first review renders in glowing watermarks that looked, wrongly, like the Fab assets
            # were unlicensed previews. This project renders with Lumen, where dynamic lights are
            # the normal path and a bake buys nothing, so the fix is to stop asking for one.
            component.set_mobility(unreal.ComponentMobility.MOVABLE)

            # The breach used to be dimmed a further 45% here, on the reasoning that it is lit by
            # whatever is still working. That was tuned when the room's own dressing was three
            # flat-shaded concept props bright enough to carry the frame on their own. They are
            # gone, replaced by Alien_Cave_biome growth that is dark, matte and organic -- and at
            # 45% the room came back as a clean shell with the infestation invisible in it.
            #
            # Dropped rather than reduced. The breach is already the dimmest profile in the map at
            # 1500 against engineering's 2400, so it stays the worst-lit room without also being
            # the one where the thing worth looking at cannot be seen.

            light.tags = [TAG]
            light.set_actor_label("Dressing_Light_{}".format(self.spawned))
            self.spawned += 1

    def place_grounded(self, mesh_name, x, y, yaw, scale):
        """Places a mesh with its lowest point on the deck, whatever its pivot happens to be.

        The kit's props are authored on their base, so the rest of this file can use a plain Z
        offset. The biomass meshes are not: their pivots are offset or centred, and placing them
        the same way would bury some in the floor and float others. Rather than hand-tune six
        numbers, the bottom is computed from the mesh's own bounds.

        Returns the actor so the caller can tell whether it landed.
        """
        mesh = self.mesh(mesh_name)
        if not mesh:
            return None

        bounds = mesh.get_bounds()
        # Distance from the pivot down to the lowest point, in the mesh's own space, times the
        # scale it is being placed at.
        drop = (bounds.box_extent.z - bounds.origin.z) * scale

        actor = self.place(mesh_name, unreal.Vector(x, y, self.pending_floor_z + drop),
                           unreal.Rotator(0, yaw, 0), unreal.Vector(scale, scale, scale))
        return actor

    # --- props --------------------------------------------------------------------------------
    def growth_practical(self, x, y, floor_z):
        """A small violet light inside a piece of growth.

        Derived from the growth's own placement rather than authored separately, so adding a mesh
        to the breach profile gets a light with it and the two can never drift apart. That mattered
        immediately: the first version of this pass placed six organisms and lit none of them.
        """
        light = self.actors.spawn_actor_from_class(
            unreal.PointLight, unreal.Vector(x, y, floor_z + GROWTH_LIGHT_HEIGHT))
        if not light:
            return None

        component = light.point_light_component
        component.set_editor_property("intensity", GROWTH_LIGHT_INTENSITY)
        component.set_light_color(GROWTH_LIGHT_COLOUR)
        component.set_editor_property("attenuation_radius", GROWTH_LIGHT_RADIUS)
        component.set_editor_property("source_radius", 30.0)

        # Shadows off. A light sitting inside a solid mesh with shadows on lights almost nothing --
        # the mesh occludes its own light -- and the point here is the surrounding surfaces catching
        # a colour they should not have.
        component.set_editor_property("cast_shadows", False)
        component.set_mobility(unreal.ComponentMobility.MOVABLE)

        light.tags = [TAG]
        light.set_actor_label("Dressing_GrowthGlow_{}".format(self.spawned))
        self.spawned += 1
        return light

    def dress_props(self, centre, floor_z, profile):
        # Held on the dresser so place_grounded does not need it threaded through. Set here because
        # dress_props is the only caller.
        self.pending_floor_z = floor_z

        for entry in PROPS.get(profile, []):
            name, x, y, z, yaw = entry[:5]
            scale = entry[5] if len(entry) > 5 else 1.0

            if z is None:
                self.place_grounded(name, centre.x + x, centre.y + y, yaw, scale)
                if name.startswith(BIOMASS):
                    self.growth_practical(centre.x + x, centre.y + y, floor_z)
                continue

            self.place(name,
                unreal.Vector(centre.x + x, centre.y + y, floor_z + z),
                unreal.Rotator(0, yaw, 0),
                unreal.Vector(scale, scale, scale) if scale != 1.0 else None)


def restore_greybox(actors):
    """Un-hide anything a previous run hid, so re-running never strands invisible geometry."""
    restored = 0
    for actor in actors:
        if HIDDEN_TAG not in [str(t) for t in actor.tags]:
            continue
        for component in actor.get_components_by_class(unreal.StaticMeshComponent):
            component.set_visibility(True)
        actor.tags = [t for t in actor.tags if str(t) != HIDDEN_TAG]
        restored += 1
    return restored


def hide_greybox_for_room(actors, room):
    """Hides the greybox shell of one room, keeping its collision.

    Identified by mesh, not by name. The first version matched a list of label prefixes and missed
    InnerWall, OuterWall, FloorStripe, Kickplate, UtilityRail, WearPatch and CeilingBeam -- so
    greybox walls went on standing inside the Fab walls, which is why untextured surfaces kept
    showing through in review shots. Any list of names is a guess about what a level happens to
    contain; the mesh is the fact.

    The rule: inside this room, anything drawing a mesh in SUPERSEDED_MESHES gets hidden. That is
    the engine's Cube primitive -- the greybox shell -- plus the three flat-shaded SM_FX_Bloom*
    concept props, which this pass now replaces with real growth. Anything drawing another real
    mesh -- pipes, light fixtures, power junctions, the engine machinery -- is art that predates
    this pass and is left alone.

    Still identified by mesh rather than by name, for the original reason: any list of labels is a
    guess about what a level happens to contain, and the mesh is the fact. SUPERSEDED_MESHES is a
    list of *assets this pass replaces*, which is a claim about the art and not about naming.

    Visibility rather than destruction. These actors carry the collision the navmesh was built
    against, so removing them would silently rebuild the ship's traversal under a demo that works.
    """
    origin, extent = room.get_actor_bounds(only_colliding_components=False)

    hidden = 0
    for actor in actors:
        if not isinstance(actor, unreal.StaticMeshActor):
            continue

        # Never touch what this pass placed, or a re-run hides its own dressing.
        tags = [str(t) for t in actor.tags]
        if TAG in tags:
            continue

        location = actor.get_actor_location()
        if (abs(location.x - origin.x) > extent.x
                or abs(location.y - origin.y) > extent.y
                or abs(location.z - origin.z) > extent.z):
            continue

        components = actor.get_components_by_class(unreal.StaticMeshComponent)
        greybox = [c for c in components
                   if c.get_editor_property("static_mesh")
                   and c.get_editor_property("static_mesh").get_name() in SUPERSEDED_MESHES]
        if not greybox:
            continue

        for component in greybox:
            component.set_visibility(False)

        if HIDDEN_TAG not in tags:
            actor.tags = list(actor.tags) + [HIDDEN_TAG]
        hidden += 1

    return hidden


def main():
    if not unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        unreal.log_error("Map not found: {}".format(MAP_PATH))
        return

    global MESH_INDEX
    MESH_INDEX = build_mesh_index()
    unreal.log("Indexed {} kit meshes".format(len(MESH_INDEX)))
    if not MESH_INDEX:
        unreal.log_error("No kit meshes found under {}; refusing to dress nothing".format(KIT_ROOT))
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

    rooms = [a for a in actors if a.get_class().get_name() == "ModularShipRoom"]
    dresser = Dresser(actor_subsystem)

    dressed = 0
    for room in rooms:
        name = str(room.get_editor_property("display_name"))
        profile = ROOM_PROFILES.get(name)
        if not profile:
            continue

        code = str(room.get_editor_property("room_code"))
        origin, extent = room.get_actor_bounds(only_colliding_components=False)
        centre = unreal.Vector(origin.x, origin.y, origin.z)
        floor_z = origin.z - extent.z

        hidden = hide_greybox_for_room(actors, room)

        before = dresser.spawned
        dresser.dress_shell(centre, floor_z, profile)
        dresser.light_room(centre, floor_z, profile)
        dresser.dress_props(centre, floor_z, profile)

        unreal.log("  {:<10} {:<32} {:<12} hid {:>3} greybox, placed {:>3}".format(
            code, name, profile, hidden, dresser.spawned - before))
        dressed += 1

    saved = level_subsystem.save_current_level()
    # Reported because it is the number that decides whether the rooms read at all, and nothing
    # else would show it: a run that places every actor and dims no fixture leaves the workshop as
    # two blown strips in a black field, with an identical actor count.
    if dresser.dimmed == 0:
        unreal.log_error("No fixtures were dimmed; the rooms are still lit by the kit emissive")
    else:
        unreal.log("Dimmed {} room fixture(s)".format(dresser.dimmed))

    unreal.log("Dressed {} room(s) with {} actor(s). Saved {}: {}".format(
        dressed, dresser.spawned, MAP_PATH, saved))


if __name__ == "__main__":
    main()
