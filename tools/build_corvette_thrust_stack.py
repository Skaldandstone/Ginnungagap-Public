"""Builds L_Corvette_ThrustStack: the GGP-M01 corvette's thrust-gravity deck stack as a playable
map, from Fab kit geometry only.

The concept (docs/concept-art/2026-08-29/production-reference/ggp-m01-medium-military-corvette-
vertical-stack-room-production-v2.png and its thrust-tower packet) stacks eleven one-storey decks
along the thrust axis, engines below, each a transverse slab with its own role room, an X-axis
ladder/lift trunk and a service plenum. In Unreal that axis is Z: eleven decks 4.3 m apart, floors
in XY, bow up. This lays each deck out the same way -- an access trunk with a ramp to the deck
above, a corridor, the role room, a secondary room and a service room -- so the stack reads as one
ship and a player can walk the whole height without a lift.

Everything drawn is Modular Scifi Mechanic Base / ModSci / Ice Station / SciFiWorld / the Fab pod
kit; the gameplay actors are the project's (rooms, production bulkheads, activity stations, the
quick-demo mission director and its objective chain, the opening sequence). The chain is the
demo's: seal a suit (D03 Casualty Station), draw equipment (D02 Engineering Control), restore
power (D01 Power & Distribution), seal the breach (D07 Comms), bring the CIC online (D08).
Obstacles: a buckled bulkhead on D04's trunk landing, a sealed CIC door with its override, an
unpressurised airlock on D06. No Bloom, no enemies.

Re-runnable: the map is recreated from scratch every time.

    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/build_corvette_thrust_stack.py -NullRHI
"""
import math
import random
import unreal

MAP_DIR = "/Game/Assets/Maps/ShipProduction"
MAP_NAME = "L_Corvette_ThrustStack"
MAP = f"{MAP_DIR}/{MAP_NAME}"
PREFIX = "CVT_"
# Which rooms are damaged and how, and how the furniture falls: a different ship each regenerate
# when the seed changes.
BUILD_SEED = 7

KIT = "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM"
ENGI = "/Game/ModSci_Engineer/Meshes"
ENGP = "/Game/ModSci_EngiProps/Meshes"
ICE = "/Game/Ice_Station/Meshes"
SCIW = "/Game/SciFiWorld/Meshes"

DECK_PITCH = 430.0
WALL_H = 400.0          # kit wall height; the ceiling slab sits on top, underside at 350
WALL_D = 53.0           # kit panel: face 53 cm from its origin on the +Y side at yaw 0
FLOOR_T = 20.0
FOOT_X, FOOT_Y = 2400.0, 1800.0
DOOR_GAP = 260.0
DOORWAY_WIDTH, DOORWAY_HEIGHT = 250.0, 270.0

# Deck plan, in cm, identical on every deck. Partition lines carry a 100 cm slab of two back-to-back
# kit panels (PARTITION inset each side); hull walls stand outside their line. Clear spans: the
# corridor 650..950, the trunk 0..550 across, rooms from 1050 to the fore hull at 1800.
PARTITION = 50.0
TRUNK = (0.0, 1400.0, 0.0, 600.0)        # x0, x1, y0, y1
RAMP_LANE = (0.0, 300.0)                  # y band the ramps climb in
RAMP_X0, RAMP_X1 = 300.0, 1000.0          # the ramp itself: foot at x1 on this deck, head at x0 on the next
RAMP_RUN = RAMP_X1 - RAMP_X0
LANDING = (300.0, 550.0)                  # flat y band beside the lane, full trunk length
# The lane's flat ends: x 0..RAMP_X0 is where a ramp from below arrives (and the player steps off
# sideways onto the landing), x RAMP_X1..trunk end is the foot of this deck's ramp up.
CORRIDOR = (0.0, 2400.0, 600.0, 1000.0)
MAIN = (0.0, 1500.0, 1000.0, 1800.0)
SECOND = (1500.0, 2400.0, 1000.0, 1800.0)
SERVICE = (1400.0, 2400.0, 0.0, 600.0)
MAIN_DOOR_X, SECOND_DOOR_X, SERVICE_DOOR_X = 750.0, 1950.0, 1750.0

# The plan is the same shell on every deck; what varies is where it is cut. Three door plans cycle
# up the stack so no two neighbouring decks read alike from the ramp; some decks join their two
# rooms with a hatch (a loop through the deck instead of two dead ends off the corridor); two are
# one open bay; and three deck pairs are linked a second way, by a ramp through the service
# plenums, so the trunk is not the only way up the ship.
DOOR_PLANS = [(750.0, 1950.0, 1750.0), (450.0, 2150.0, 1550.0), (1050.0, 1750.0, 2050.0)]
ROOM_HATCH_DECKS = {2, 4, 8, 9}          # a door in the main/second partition
OPEN_BAY_DECKS = {6, 11}                 # the partition stands open across most of its length
HATCH_Y = 1240.0                         # aft end of the partition, clear of the side stations (the plotter core sat beside a fore hatch)
OPEN_BAY_GAP = (1150.0, 1700.0)
SERVICE_RAMP_DECKS = {2, 6, 9}           # the lower deck of each plenum link (up to deck + 1)
SERVICE_RAMP_X0, SERVICE_RAMP_X1 = 1500.0, 2200.0    # head (upper deck) and foot (lower deck)
SERVICE_LANE = (0.0, 300.0)
SERVICE_LANDING = (300.0, 600.0)


def door_plan(deck):
    return DOOR_PLANS[(deck - 1) % len(DOOR_PLANS)]

DECKS = [
    (1, "Power & Distribution", "power"),
    (2, "Engineering Control", "workshop"),
    (3, "Casualty Station", "cryo"),
    (4, "Security Center", "security"),
    (5, "Marine Ready Room", "marine"),
    (6, "Crew Commons", "commons"),
    (7, "Comms", "breach"),
    (8, "Armored CIC", "cic"),
    (9, "Tactical Plotting", "tactical"),
    (10, "Observation", "observation"),
    (11, "Sensor Suite", "sensors"),
]
SECOND_NAMES = {1: "Breaker Gallery", 2: "Parts Store", 3: "Suit Bay", 4: "Holding Cells", 5: "Gear Issue",
                6: "Galley", 7: "Data Vault", 8: "Ready Room", 9: "Chart Store", 10: "Gallery", 11: "Sensor Racks"}
SERVICE_NAMES = {n: "Service Plenum" for n, _, _ in DECKS}

ARCHETYPE = {"power": "REACTOR_CONTROL", "workshop": "ENGINEERING", "cryo": "MEDICAL_BAY", "security": "ARMORY",
             "marine": "ARMORY", "commons": "CREW_BERTHING", "breach": "DAMAGE_CONTROL", "cic": "BRIDGE",
             "tactical": "BRIDGE", "observation": "CREW_BERTHING", "sensors": "SENSOR_OPERATIONS", "service": "ENGINEERING"}
SECTION = {"power": "ENGINE_ROOM", "workshop": "ENGINE_ROOM", "cryo": "MED_BAY", "cic": "BRIDGE", "tactical": "BRIDGE", "commons": "CREW_QUARTERS", "service": "ENGINE_ROOM"}

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = None
spawned = 0


def deck_floor_z(deck):
    return (deck - 1) * DECK_PITCH


def load(path):
    asset = unreal.load_asset(path)
    if not asset:
        unreal.log_warning(f"missing asset {path}")
    return asset


def enum_value(enum_type, name):
    return getattr(enum_type, name)


def label(actor, text):
    global spawned
    actor.set_actor_label(f"{PREFIX}{text}")
    spawned += 1
    return actor


def place(mesh, location, rotation=(0.0, 0.0, 0.0), scale=(1.0, 1.0, 1.0), name="Kit", collide=True):
    """A static mesh actor from a Fab mesh, with the mesh's own collision (there is no greybox)."""
    if not mesh:
        return None
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location),
                                          unreal.Rotator(roll=rotation[0], pitch=rotation[1], yaw=rotation[2]))
    comp = actor.static_mesh_component
    comp.set_static_mesh(mesh)
    comp.set_mobility(unreal.ComponentMobility.STATIC)
    if not collide:
        comp.set_editor_property("use_default_collision", False)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    actor.set_editor_property("tags", [unreal.Name("CorvetteKit")])
    return label(actor, name)


class Kit:
    def __init__(self):
        self.wall = [load(f"{KIT}/SRTUCTURE/WALL/SM_WALL_12"), load(f"{KIT}/SRTUCTURE/WALL/SM_WALL_07"), load(f"{KIT}/SRTUCTURE/WALL/SM_WALL_09")]
        self.wall_display = load(f"{KIT}/SRTUCTURE/WALL/SM_WALL_08_DISPLAY")
        self.floor = load(f"{KIT}/SRTUCTURE/FLOOR/SM_FLOOR_05")
        self.floor_grate = load(f"{KIT}/SRTUCTURE/FLOOR/SM_FLOOR_09")
        self.ceiling = load(f"{KIT}/SRTUCTURE/CEILING/SM_CEILING_09")
        self.lamp = load(f"{KIT}/PROP/LAMP/SM_LAMP_04")
        self.computer = load(f"{KIT}/PROP/COMPUTER/SM_COMPUTER_01")
        self.computer2 = load(f"{KIT}/PROP/COMPUTER/SM_COMPUTER_02")
        self.electric_box = load(f"{KIT}/PROP/MACHINE/SM_ELECTRIC_BOX_01_OPEN")
        self.generator = load(f"{KIT}/PROP/MACHINE/SM_POWER_GENERATOR_01")
        self.barrel = load(f"{KIT}/PROP/BARREL/SM_BARREL_01")
        self.cable = load(f"{KIT}/CABLE_PIPE/SM_CABLE_MASS_04")
        self.pipe = load(f"{KIT}/CABLE_PIPE/SM_PIPE_03")
        self.glass = load(f"{KIT}/SRTUCTURE/WALL/SM_GLASS_01")
        self.locker = load(f"{KIT}/SRTUCTURE/DOOR_FRAME/SM_DOOR_FRAME_03_LOCKER_LEFT")
        # No Ice Station props: that pack is missing its main trim texture in this project, so
        # everything from it renders flat white (crates, beds, tables, the computer racks).
        self.crate = load("/Game/kb3d_missiontominerva/StaticMeshes/SM_KB3D_MTM_PropCrate_A")
        self.big_crate = self.crate
        self.table = load(f"{SCIW}/SM_LabDesk03_2")
        self.chair = load(f"{SCIW}/SM_Chair08")
        self.control_panel = load(f"{SCIW}/SM_ControlPanel01")
        self.ice_computer = self.computer   # SM_COMPUTER_01: pivot 78 up its body, place at z + 78
        self.circular = self.table
        self.oxygen = load(f"{ENGP}/SM_OxygenTank")
        self.nitrogen = load(f"{ENGP}/SM_NitrogenTank_Covered")
        self.toolbox = load(f"{ENGP}/SM_Toolbox")
        self.ceiling_frame = load(f"{ENGI}/SM_Ceiling_HB_A")
        # Sci-fi Rooms and Corridors (Denys Rutkovskyi): 300 cm glass walls, rails, light fixtures and
        # furniture. The industrial shell stays the Modular SciFi kit; these dress it.
        RC = "/Game/SciFiRoomsCorridors/Meshes"
        self.rc_glass = load(f"{RC}/SM_WallGlass01")          # 203 wide x 243 tall pane, min x -53
        self.rc_glass_wide = load(f"{RC}/SM_WallGlass02")     # 406 wide
        self.rc_rail = load(f"{RC}/SM_Railing01")             # 300 long along Y, 20 tall
        self.rc_light_bar = load(f"{RC}/SM_Light02")          # 44 cm bar, glows
        self.rc_light_round = load(f"{RC}/SM_Light03")        # 12 cm puck
        self.rc_bed = load(f"{RC}/SM_Bed01")                  # 220 x 97 x 109, origin at the head end
        self.rc_table = load(f"{RC}/SM_Table01")              # 154 x 92 x 68
        self.rc_chair = load(f"{RC}/SM_Chair01")              # 40 x 46 x 80
        self.rc_shelf = load(f"{RC}/SM_Shelf01")              # 85 x 83 x 189, origin at a corner
        self.rc_locker = load(f"{RC}/SM_Shelf02")             # 54 x 52 x 68
        self.rc_bin = load(f"{RC}/SM_Bin01")                  # 24 x 24 x 48
        self.rc_pillar = load(f"{RC}/SM_Pillar01")            # 24 x 50 x 300
        # Sign plates: the engine cube in the kit wall material, a dark panel behind the lettering.
        self.sign_material = load(f"{KIT}/../Material/M_WALL_01") or (self.wall[0].get_material(0) if self.wall[0] else None)
        self.duct_run = load(f"{ENGI}/SM_AirDuct_Mid")   # a 3.6 m duct section: fallen, it fills a corridor
        self.rail = load(f"{ENGI}/SM_Rail_A")             # 164 x 8 x 78, pivot at the bottom centre
        self.alarm = load(f"{ENGP}/SM_AlarmLight")
        self.portable_light = load(f"{ENGP}/SM_PortableLight")
        self.distrib = load(f"{ENGI}/SM_ElectricDistribBox")
        self.duct = load(f"{ENGI}/SM_AirDuct_Vent")
        self.lab_capsule = load(f"{SCIW}/SM_LabCapsule10_Capsule")
        self.terminal = self.computer2


K = None


# --- geometry -------------------------------------------------------------------------------------

def wall_run(along, fixed, start, end, face, z, gaps=(), name="Wall", variant=0, inset=0.0):
    """Kit wall panels along one line.

    along: "x" for a wall running along X at y=fixed, "y" for one along Y at x=fixed.
    face: +1 if the decorated face looks toward +Y (or +X), -1 the other way. The panel's face is
    WALL_D from its origin, so the origin steps back from the line by that much.
    gaps: (start, end) spans along the run to leave open (doorways).
    """
    intervals = [(start, end)]
    for g0, g1 in gaps:
        kept = []
        for a, b in intervals:
            if g1 <= a or g0 >= b:
                kept.append((a, b)); continue
            if a < g0: kept.append((a, g0))
            if g1 < b: kept.append((g1, b))
        intervals = kept
    made = 0
    for a, b in intervals:
        pos = a
        while pos < b - 1.0:
            seg = min(400.0, b - pos)
            centre = pos + seg * 0.5
            mesh = K.wall[(variant + made) % len(K.wall)]
            face_pos = fixed + face * inset      # where the decorated face stands
            if along == "x":
                loc = (centre, face_pos - face * WALL_D, z)
                yaw = 0.0 if face > 0 else 180.0
            else:
                loc = (face_pos - face * WALL_D, centre, z)
                yaw = -90.0 if face > 0 else 90.0
            place(mesh, loc, (0.0, 0.0, yaw), (seg / 400.0, 1.0, 1.0), f"{name}_{made:02d}")
            pos += seg
            made += 1
    return made


def floor_area(x0, x1, y0, y1, z_top, name, skip=None, mesh=None):
    """300 cm tiles over a rectangle, top surface at z_top; skip(x0,x1,y0,y1) says which to leave out."""
    mesh = mesh or K.floor
    tile = 300.0
    nx, ny = max(1, int(round((x1 - x0) / tile))), max(1, int(round((y1 - y0) / tile)))
    sx, sy = (x1 - x0) / nx / tile, (y1 - y0) / ny / tile
    made = 0
    for i in range(nx):
        for j in range(ny):
            tx0, ty0 = x0 + i * tile * sx, y0 + j * tile * sy
            tx1, ty1 = tx0 + tile * sx, ty0 + tile * sy
            if skip and skip(tx0, tx1, ty0, ty1):
                continue
            place(mesh, ((tx0 + tx1) * 0.5, (ty0 + ty1) * 0.5, z_top - FLOOR_T), (0, 0, 0), (sx, sy, 1.0), f"{name}_{i}_{j}")
            made += 1
    return made


def ceiling_area(x0, x1, y0, y1, z_underside, name, skip=None):
    """Ceiling slabs (900 kit piece, scaled to 600 grid), underside at z_underside."""
    tile = 600.0
    nx, ny = max(1, int(round((x1 - x0) / tile))), max(1, int(round((y1 - y0) / tile)))
    sx, sy = (x1 - x0) / nx / 900.0, (y1 - y0) / ny / 900.0
    for i in range(nx):
        for j in range(ny):
            tx0, ty0 = x0 + i * (x1 - x0) / nx, y0 + j * (y1 - y0) / ny
            tx1, ty1 = tx0 + (x1 - x0) / nx, ty0 + (y1 - y0) / ny
            if skip and skip(tx0, tx1, ty0, ty1):
                continue
            place(K.ceiling, ((tx0 + tx1) * 0.5, (ty0 + ty1) * 0.5, z_underside + 50.0), (0, 0, 0), (sx, sy, 1.0), f"{name}_{i}_{j}")


def ramp(deck, z_bottom, x_foot=RAMP_X1, x_head=RAMP_X0, lane=RAMP_LANE, name="Ramp"):
    """A ramp: floor tiles pitched from (x=x_foot, z_bottom) up to (x=x_head, z_bottom + pitch),
    climbing toward -X in the given y lane. The trunk's by default; the plenum links pass theirs."""
    rise = DECK_PITCH
    run = x_foot - x_head
    length = math.hypot(run, rise)
    angle = math.degrees(math.atan2(rise, run))
    n = 3
    seg = length / n
    lane_y = (lane[0] + lane[1]) * 0.5
    lane_w = lane[1] - lane[0]
    cos_a, sin_a = math.cos(math.radians(angle)), math.sin(math.radians(angle))
    for i in range(n):
        s_ = (i + 0.5) * seg
        x = x_foot - s_ * cos_a
        z = z_bottom + s_ * sin_a
        # Tile top is 20 above its origin; drop the origin along the slope normal so the top rides the line.
        loc = (x - FLOOR_T * sin_a, lane_y, z - FLOOR_T * cos_a)
        tile = place(K.floor_grate, loc, (0.0, angle, 180.0), (seg / 300.0, lane_w / 300.0, 1.0), f"D{deck:02d}_{name}_{i}")
        if tile and i == 1:
            # The look tour stops at every ramp's middle tile.
            tile.set_editor_property("tags", [unreal.Name("CorvetteRamp")])
    # A rail down the ramp's open side (the landing is the other way; the hull is behind the
    # far side), riding the slope.
    if K.rail:
        rail_n = max(1, int(round(length / 164.0)))
        rail_seg = length / rail_n
        for i in range(rail_n):
            s_ = (i + 0.5) * rail_seg
            # Yaw 180 like the tiles: pitch raises the mesh's +X, and the ramp climbs toward -X. At yaw 0
            # each rail tilted against the slope, one end in the air and the other under the grating.
            place(K.rail, (x_foot - s_ * cos_a, lane[1] - 6.0, z_bottom + s_ * sin_a + FLOOR_T), (0.0, angle, 180.0),
                  (rail_seg / 164.0, 1.0, 1.0), f"D{deck:02d}_{name}Rail_{i}")
    # A rail along the ramp's open side so the eye reads the edge (no collision).
    place(K.pipe, ((x_head + x_foot) * 0.5, lane[1] + 6.0, z_bottom + rise * 0.5 + 95.0), (0.0, angle, 180.0),
          (length / 200.0, 0.6, 0.6), f"D{deck:02d}_{name}Rail", collide=False)


def edge_rail(deck, x0, x1, y, z, name):
    """A rail along the open edge of a floor over a ramp hole."""
    if not K.rail:
        return
    rail_n = max(1, int(round((x1 - x0) / 164.0)))
    rail_seg = (x1 - x0) / rail_n
    for i in range(rail_n):
        place(K.rail, (x0 + (i + 0.5) * rail_seg, y, z + FLOOR_T), (0.0, 0.0, 0.0), (rail_seg / 164.0, 1.0, 1.0), f"D{deck:02d}_{name}_{i}")


# --- gameplay helpers -----------------------------------------------------------------------------

def no_nav(comp):
    """Volumes the gameplay reads (triggers, hazard zones, room bounds) are not walls: a box
    that spans a room otherwise carves the whole room out of the navmesh."""
    comp.set_editor_property("can_ever_affect_navigation", False)


def spawn_room(code, name, kind, bounds, z_floor, powered=False, alert=False, tags=()):
    x0, x1, y0, y1 = bounds
    size = unreal.Vector(x1 - x0, y1 - y0, WALL_H)
    room = actors.spawn_actor_from_class(unreal.ModularShipRoom, unreal.Vector((x0 + x1) * 0.5, (y0 + y1) * 0.5, z_floor + WALL_H * 0.5), unreal.Rotator())
    label(room, f"Room_{code}")
    room.set_editor_property("room_code", code)
    room.set_editor_property("display_name", name)
    archetype = ARCHETYPE.get(kind, "COMPANIONWAY")
    room.set_editor_property("archetype", enum_value(unreal.ShipRoomArchetype, archetype if hasattr(unreal.ShipRoomArchetype, archetype) else "COMPANIONWAY"))
    section = SECTION.get(kind, "DECK")
    if hasattr(unreal.ShipSectionType, section):
        room.set_editor_property("section_type", enum_value(unreal.ShipSectionType, section))
    room.set_editor_property("module_size", size)
    room.get_editor_property("section_bounds").set_box_extent(size * 0.5)
    no_nav(room.get_editor_property("section_bounds"))
    room.set_editor_property("powered", powered)
    room.set_editor_property("operational_state", enum_value(unreal.ShipRoomOperationalState, "ALERT" if alert else ("NOMINAL" if powered else "UNPOWERED")))
    room.set_editor_property("tags", [unreal.Name("QuickDemoShipRoom"), unreal.Name(code), unreal.Name("CorvetteRoom")] + [unreal.Name(t) for t in tags])
    return room


def spawn_room_light(code, x, y, z_floor, colour, intensity, radius=900.0, emergency=False):
    light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x, y, z_floor + 320.0), unreal.Rotator())
    label(light, f"Light_{code}")
    comp = light.get_component_by_class(unreal.PointLightComponent)
    comp.set_editor_property("attenuation_radius", radius)
    comp.set_light_color(colour)
    comp.set_editor_property("intensity", intensity)
    if emergency:
        light.set_editor_property("tags", [unreal.Name("QuickDemoEmergencyLight"), unreal.Name(code)])
    else:
        light.set_editor_property("tags", [unreal.Name("QuickDemoUtilityLight"), unreal.Name(code)])
        comp.set_editor_property("intensity", 0.0)
        comp.set_visibility(False)
    return light


def spawn_practical(code, x, y, z_floor, intensity, colour=None, radius=800.0, height=300.0):
    """An always-on fixture light the mission director leaves alone (no utility tag): the dim
    practicals a ship runs on before the main bus is back. The tagged utility lights come on red
    over these when power is restored."""
    light = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(x, y, z_floor + height), unreal.Rotator())
    label(light, f"Practical_{code}")
    comp = light.get_component_by_class(unreal.PointLightComponent)
    comp.set_editor_property("attenuation_radius", radius)
    comp.set_light_color(colour or unreal.LinearColor(1.0, 0.62, 0.32, 1.0))
    comp.set_editor_property("intensity", intensity)
    comp.set_editor_property("cast_shadows", False)
    # Dark until power is restored; the director brings practicals up dull and flickering.
    comp.set_visibility(False)
    light.set_editor_property("tags", [unreal.Name("CorvettePractical"), unreal.Name(code)])
    return light


def spawn_door(bulkhead_class, x, y, z_floor, yaw, name, seal=False, tags=()):
    door = actors.spawn_actor_from_class(bulkhead_class, unreal.Vector(x, y, z_floor - 20.0), unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
    label(door, name)
    door.set_editor_property("tags", [unreal.Name("CorvetteDoor")] + [unreal.Name(t) for t in tags])
    try:
        # A real bulkhead: Fab's "Sci-fi New Door" (CGGame) as portal and leaves, imported by
        # tools/import_fab_scifi_door.py. Its leaves are 100 x 270 each, so the portal's native
        # opening is 200 wide; the kit frame stays the fallback if the import is missing.
        fab_portal, fab_left, fab_right = load("/Game/Fab_SciFiDoor/Meshes/Prtal_Door"), load("/Game/Fab_SciFiDoor/Meshes/Left_Door"), load("/Game/Fab_SciFiDoor/Meshes/Right_Door")
        if fab_portal and fab_left and fab_right:
            door.set_editor_property("frame_mesh_asset", fab_portal)
            door.set_editor_property("left_leaf_mesh_asset", fab_left)
            door.set_editor_property("right_leaf_mesh_asset", fab_right)
            door.set_editor_property("frame_native_opening_width", 200.0)
            door.set_editor_property("frame_native_opening_height", 270.0)
        else:
            door.set_editor_property("frame_mesh_asset", load(f"{KIT}/SRTUCTURE/DOOR_FRAME/SM_DOOR_FRAME_01_OUTSIDE"))
            door.set_editor_property("left_leaf_mesh_asset", load(f"{KIT}/SRTUCTURE/DOOR_FRAME/SM_DOOR_01_LEFT"))
            door.set_editor_property("right_leaf_mesh_asset", load(f"{KIT}/SRTUCTURE/DOOR_FRAME/SM_DOOR_01_RIGHT"))
        door.set_editor_property("lintel_mesh_asset", load(f"{KIT}/SRTUCTURE/DOOR_FRAME/SM_DOOR_FRAME_02_UP"))
        door.set_editor_property("doorway_width", DOORWAY_WIDTH)
        door.set_editor_property("doorway_height", DOORWAY_HEIGHT)
        door.set_editor_property("ceiling_height", WALL_H - 50.0 - 20.0)
        door.set_editor_property("floor_offset", 20.0)
        door.set_editor_property("apply_door_material", False)
        for component in door.get_components_by_class(unreal.StaticMeshComponent):
            n = component.get_name()
            if n in ("FrameMesh", "LintelMesh", "LeftPanel", "RightPanel"):
                component.set_editor_property("use_default_collision", False)
                component.set_visibility(True)
            elif n == "VisualMesh":
                component.set_editor_property("use_default_collision", False)
                component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
                component.set_visibility(False)
        door.set_editor_property("leaf_slide_margin", 8.0)
    except Exception as error:
        unreal.log_warning(f"door visuals not configured on {name}: {error}")
    if seal:
        door.seal()
    return door


def spawn_station(cls, x, y, z_floor, yaw, name, target=None, display=None, mount="WALL_PANEL", condition="FAULTED", rarity="SPECIALIZED", seed=7, wear=0.3, tags=()):
    # The terminal mesh (SM_COMPUTER_02) reaches 41 cm below its origin: at z + 90 every station
    # hung half a metre off the deck. Its feet are on the deck now, its top at 121.
    station = actors.spawn_actor_from_class(cls, unreal.Vector(x, y, z_floor + 41.0), unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
    label(station, name)
    if target is not None:
        station.set_editor_property("target_actor", target)
    station.get_editor_property("mesh").set_static_mesh(K.terminal)
    if display:
        activity = station.get_editor_property("activity")
        activity.set_editor_property("display_name", display)
        station.set_editor_property("activity", activity)
    try:
        station.configure_procedural_station(unreal.Name(f"CVT-{name}"), unreal.Name(name), seed, 0,
                                             enum_value(unreal.ActivityStationMount, mount), enum_value(unreal.ActivityStationCondition, condition),
                                             enum_value(unreal.ActivityStationRarity, rarity), wear, -1)
    except Exception as error:
        unreal.log_warning(f"procedural station config failed on {name}: {error}")
    if tags:
        station.set_editor_property("tags", [unreal.Name(t) for t in tags])
    return station


def spawn_beacon(objective_id, text, x, y, z_floor, yaw, code):
    beacon = actors.spawn_actor_from_class(unreal.QuickDemoObjectiveBeacon, unreal.Vector(x, y, z_floor + 145.0), unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
    label(beacon, f"Beacon_{objective_id}_{code}")
    beacon.set_editor_property("objective_id", unreal.Name(objective_id))
    beacon.set_editor_property("marker_label", text)
    beacon.set_editor_property("tags", [unreal.Name("QuickDemoGameplay"), unreal.Name("ObjectiveBeacon")])
    return beacon


def spawn_sign(text, x, y, z_floor, yaw, code, big=False, both_sides=False):
    """A text sign on a plate. Text renders two-sided and reads mirrored from behind, so every sign
    gets an opaque plate at its back; a sign read from either side of a line (the trunk's) is two
    signs on the two faces of one plate."""
    size = 22.0 if big else 15.0
    colour = unreal.Color(r=120, g=226, b=211) if big else unreal.Color(r=150, g=165, b=170)
    width, height = max(120.0, len(text) * size * 0.62), size * 2.2
    # The sign's facing: text faces its local +X.
    rad = math.radians(yaw)
    nx, ny = math.cos(rad), math.sin(rad)
    plate = load("/Engine/BasicShapes/Cube")
    if plate:
        cube = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, y, z_floor + 230.0), unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
        label(cube, f"SignPlate_{code}")
        comp = cube.static_mesh_component
        comp.set_static_mesh(plate)
        comp.set_editor_property("can_ever_affect_navigation", False)
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        cube.set_actor_scale3d(unreal.Vector(0.04, width / 100.0, height / 100.0))
        if K.sign_material:
            comp.set_material(0, K.sign_material)

    def one(face_yaw, suffix):
        fx, fy = math.cos(math.radians(face_yaw)), math.sin(math.radians(face_yaw))
        sign = actors.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(x + fx * 3.0, y + fy * 3.0, z_floor + 230.0), unreal.Rotator(pitch=0.0, yaw=face_yaw, roll=0.0))
        label(sign, f"Sign_{code}{suffix}")
        comp = sign.get_component_by_class(unreal.TextRenderComponent)
        comp.set_editor_property("text", text)
        comp.set_editor_property("world_size", size)
        comp.set_editor_property("text_render_color", colour)
        comp.set_editor_property("horizontal_alignment", unreal.HorizTextAligment.EHTA_CENTER)
        comp.set_editor_property("vertical_alignment", unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
        return sign

    sign = one(yaw, "")
    if both_sides:
        one(yaw + 180.0, "_Back")
    return sign


# --- the deck -------------------------------------------------------------------------------------

def build_deck(deck, name, kind, bulkhead_class, state):
    global MAIN_DOOR_X, SECOND_DOOR_X, SERVICE_DOOR_X
    MAIN_DOOR_X, SECOND_DOOR_X, SERVICE_DOOR_X = door_plan(deck)
    z = deck_floor_z(deck)
    plenum_ramp_up = deck in SERVICE_RAMP_DECKS          # this plenum's ramp climbs to the deck above
    plenum_hole = (deck - 1) in SERVICE_RAMP_DECKS       # the deck below's ramp arrives in this plenum
    top = z + WALL_H
    ceiling_under = top - 50.0
    code = f"CVT-D{deck:02d}"
    has_hole = deck > 1          # the ramp from the deck below arrives in the ramp lane
    has_ramp = deck < len(DECKS)

    # The landing's edge over the ramp hole: a rail from just past the ramp head to the foot, so
    # a step off the landing is not a drop of up to a deck onto the ramp below.
    if has_hole and K.rail:
        edge_x0, edge_x1 = RAMP_X0 + 180.0, RAMP_X1
        rail_n = max(1, int(round((edge_x1 - edge_x0) / 164.0)))
        rail_seg = (edge_x1 - edge_x0) / rail_n
        for i in range(rail_n):
            place(K.rail, (edge_x0 + (i + 0.5) * rail_seg, RAMP_LANE[1] + 6.0, z + FLOOR_T), (0.0, 0.0, 0.0),
                  (rail_seg / 164.0, 1.0, 1.0), f"D{deck:02d}_LandingRail_{i}")

    def in_ramp_lane(x0, x1, y0, y1):
        return x0 < RAMP_X1 and x1 > RAMP_X0 and y0 < RAMP_LANE[1] and y1 > RAMP_LANE[0]

    # Floors. The trunk is laid as pieces so the lane keeps a flat head strip (where the ramp from
    # below arrives) and a flat foot (where this deck's ramp starts) around the open run between.
    floor_area(TRUNK[0], TRUNK[1], LANDING[0], TRUNK[3], z, f"D{deck:02d}_TrunkLanding")
    floor_area(TRUNK[0], RAMP_X0, RAMP_LANE[0], RAMP_LANE[1], z, f"D{deck:02d}_LaneHead")
    floor_area(RAMP_X1, TRUNK[1], RAMP_LANE[0], RAMP_LANE[1], z, f"D{deck:02d}_LaneFoot")
    if not has_hole:
        floor_area(RAMP_X0, RAMP_X1, RAMP_LANE[0], RAMP_LANE[1], z, f"D{deck:02d}_LaneRun")
    floor_area(CORRIDOR[0], CORRIDOR[1], CORRIDOR[2], CORRIDOR[3], z, f"D{deck:02d}_CorridorFloor")
    floor_area(*MAIN, z, f"D{deck:02d}_MainFloor")
    floor_area(*SECOND, z, f"D{deck:02d}_SecondFloor")
    if plenum_hole:
        # Laid as pieces around the hole the ramp from below rises through: a landing strip along
        # the corridor side, a head strip to step off onto, and the far end past the foot.
        floor_area(SERVICE[0], SERVICE[1], SERVICE_LANDING[0], SERVICE_LANDING[1], z, f"D{deck:02d}_ServiceLanding", mesh=K.floor_grate)
        floor_area(SERVICE[0], SERVICE_RAMP_X0, SERVICE_LANE[0], SERVICE_LANE[1], z, f"D{deck:02d}_ServiceHead", mesh=K.floor_grate)
        floor_area(SERVICE_RAMP_X1, SERVICE[1], SERVICE_LANE[0], SERVICE_LANE[1], z, f"D{deck:02d}_ServiceFootEnd", mesh=K.floor_grate)
        edge_rail(deck, SERVICE_RAMP_X0 + 180.0, SERVICE_RAMP_X1, SERVICE_LANE[1] + 6.0, z, "ServiceEdgeRail")
    else:
        floor_area(*SERVICE, z, f"D{deck:02d}_ServiceFloor", mesh=K.floor_grate)
    if has_ramp:
        ramp(deck, z)
    if plenum_ramp_up:
        ramp(deck, z, x_foot=SERVICE_RAMP_X1, x_head=SERVICE_RAMP_X0, lane=SERVICE_LANE, name="ServiceRamp")
    # Ceilings: open over the ramp lane so the ramp can rise through, and over the top deck's trunk
    # too (it reads as the shaft continuing to the sensor mast).
    ceiling_area(TRUNK[0], TRUNK[1], TRUNK[2], TRUNK[3], ceiling_under, f"D{deck:02d}_TrunkCeiling", skip=in_ramp_lane if has_ramp else None)
    ceiling_area(CORRIDOR[0], CORRIDOR[1], CORRIDOR[2], CORRIDOR[3], ceiling_under, f"D{deck:02d}_CorridorCeiling")
    ceiling_area(*MAIN, ceiling_under, f"D{deck:02d}_MainCeiling")
    ceiling_area(*SECOND, ceiling_under, f"D{deck:02d}_SecondCeiling")
    def in_service_lane(x0, x1, y0, y1):
        return x0 < SERVICE_RAMP_X1 and x1 > SERVICE_RAMP_X0 and y0 < SERVICE_LANE[1] and y1 > SERVICE_LANE[0]
    ceiling_area(*SERVICE, ceiling_under, f"D{deck:02d}_ServiceCeiling", skip=in_service_lane if plenum_ramp_up else None)

    # Hull walls, decorated face inward.
    wall_run("x", 0.0, 0.0, FOOT_X, +1, z, name=f"D{deck:02d}_HullAft", variant=deck)
    # The observation deck's fore hull is glass across its main room (placed with the deck's
    # dressing); the hull panels there would otherwise stand behind the glass and the windows
    # would look out on a wall.
    wall_run("x", FOOT_Y, 0.0, FOOT_X, -1, z, name=f"D{deck:02d}_HullFore", variant=deck + 1,
             gaps=([(MAIN[0], MAIN[1])] if kind == "observation" else ([(50.0, 750.0)] if kind == "breach" else [])))
    wall_run("y", 0.0, 0.0, FOOT_Y, +1, z, name=f"D{deck:02d}_HullPort", variant=deck + 2)
    wall_run("y", FOOT_X, 0.0, FOOT_Y, -1, z, name=f"D{deck:02d}_HullStbd", variant=deck)
    # Partitions, both faces. Corridor/rooms line y=900 with the two room doors; trunk/service line
    # y=600 from the trunk's end with the service door; main/second split at x=1500; trunk/service at x=1100.
    room_gaps = [(MAIN_DOOR_X - DOOR_GAP * 0.5, MAIN_DOOR_X + DOOR_GAP * 0.5), (SECOND_DOOR_X - DOOR_GAP * 0.5, SECOND_DOOR_X + DOOR_GAP * 0.5)]
    wall_run("x", CORRIDOR[3], 0.0, FOOT_X, -1, z, gaps=room_gaps, name=f"D{deck:02d}_CorridorFore", variant=deck + 1, inset=PARTITION)
    wall_run("x", CORRIDOR[3], 0.0, FOOT_X, +1, z, gaps=room_gaps, name=f"D{deck:02d}_RoomsAft", variant=deck + 2, inset=PARTITION)
    service_gap = [(SERVICE_DOOR_X - DOOR_GAP * 0.5, SERVICE_DOOR_X + DOOR_GAP * 0.5)]
    wall_run("x", CORRIDOR[2], SERVICE[0], FOOT_X, +1, z, gaps=service_gap, name=f"D{deck:02d}_CorridorAft", variant=deck, inset=PARTITION)
    wall_run("x", CORRIDOR[2], SERVICE[0], FOOT_X, -1, z, gaps=service_gap, name=f"D{deck:02d}_ServiceFore", variant=deck + 1, inset=PARTITION)
    partition_gaps = []
    if deck in ROOM_HATCH_DECKS:
        partition_gaps = [(HATCH_Y - DOOR_GAP * 0.5, HATCH_Y + DOOR_GAP * 0.5)]
    elif deck in OPEN_BAY_DECKS:
        partition_gaps = [OPEN_BAY_GAP]
    wall_run("y", MAIN[1], MAIN[2], MAIN[3], -1, z, gaps=partition_gaps, name=f"D{deck:02d}_MainStbd", variant=deck, inset=PARTITION)
    wall_run("y", MAIN[1], MAIN[2], MAIN[3], +1, z, gaps=partition_gaps, name=f"D{deck:02d}_SecondPort", variant=deck + 1, inset=PARTITION)
    wall_run("y", TRUNK[1], TRUNK[2], TRUNK[3], -1, z, name=f"D{deck:02d}_TrunkStbd", variant=deck + 2, inset=PARTITION)
    wall_run("y", TRUNK[1], TRUNK[2], TRUNK[3], +1, z, name=f"D{deck:02d}_ServicePort", variant=deck, inset=PARTITION)

    # Rooms.
    main = spawn_room(code, name, kind, MAIN, z, powered=(kind == "cryo"), alert=(kind == "cryo"))
    second = spawn_room(f"{code}-B", SECOND_NAMES[deck], kind, SECOND, z)
    service = spawn_room(f"{code}-S", SERVICE_NAMES[deck], "service", SERVICE, z)
    state["rooms"][code] = main

    # Doors. A locked door starts sealed: an open leaf with a lock on it reads as nothing at all.
    main_door_class = unreal.WeldableBulkheadDoor if kind == "breach" else bulkhead_class
    main_door = spawn_door(main_door_class, MAIN_DOOR_X, CORRIDOR[3], z, 0.0, f"Door_{code}",
                           seal=(kind in ("cic", "cryo", "breach")), tags=(["QuickDemoCICDoor"] if kind == "cic" else (["CorvetteWeldedDoor"] if kind == "breach" else [])))
    if kind == "breach":
        # Comms was welded shut from the corridor when it lost pressure: the crew cut their way in.
        main_door.set_editor_property("welded_shut", True)
    if kind == "cryo":
        # The casualty station is the one room with air. Its door is locked against the vacuum in
        # the corridor beyond (the Comms rupture vented this deck's corridor); the override panel
        # on the room side refuses anyone who is not sealed in a suit.
        main_door.set_editor_property("locked", True)
        main_door.set_editor_property("locked_reason", unreal.Text("vacuum beyond: suit up, then override from the panel"))
        cryo_override = spawn_station(unreal.MechanicalOverrideStation, MAIN_DOOR_X + 360.0, MAIN[2] + PARTITION + 40.0, z, 90.0, "CryoDoorOverride",
                                      target=main_door, display="Override casualty station door", condition="WORN", rarity="ROUTINE",
                                      tags=("QuickDemoGameplay", "CorvetteOverride", code))
        cryo_override.set_editor_property("requires_pressure_suit", True)
        vacuum = actors.spawn_actor_from_class(unreal.HazardZoneActor, unreal.Vector((CORRIDOR[0] + CORRIDOR[1]) * 0.5, (CORRIDOR[2] + CORRIDOR[3]) * 0.5, z + 200.0), unreal.Rotator())
        label(vacuum, "CorridorVacuum_D03")
        vacuum.set_editor_property("tags", [unreal.Name("QuickDemoVacuumHazard"), unreal.Name(code)])
        venv = unreal.PhysicsEnvironmentState()
        venv.set_editor_property("ambient_pressure_k_pa", 0.3); venv.set_editor_property("vacuum_zone", True); venv.set_editor_property("temperature_c", -60.0)
        vacuum.set_editor_property("environment_state", venv)
        vacuum.get_editor_property("zone_bounds").set_box_extent(unreal.Vector((CORRIDOR[1] - CORRIDOR[0]) * 0.5, (CORRIDOR[3] - CORRIDOR[2]) * 0.5, 200.0))
        no_nav(vacuum.get_editor_property("zone_bounds"))
    if kind == "workshop":
        # Engineering Control's door lost its bus with the main power: the corridor's override
        # panel winds it open by hand.
        main_door.set_editor_property("locked", True)
        main_door.set_editor_property("locked_reason", unreal.Text("no bus: override from the corridor panel"))
        spawn_station(unreal.MechanicalOverrideStation, MAIN_DOOR_X + 380.0, CORRIDOR[3] - PARTITION - 40.0, z, -90.0, "EngineeringOverride",
                      target=main_door, display="Override Engineering Control door", condition="WORN", rarity="ROUTINE",
                      tags=("QuickDemoGameplay", "CorvetteOverride", code))
    if kind == "cic":
        # Sealed and locked: its own panel refuses, the access station in the corridor releases it.
        main_door.set_editor_property("locked", True)
        main_door.set_editor_property("locked_reason", unreal.Text("override from the CIC access panel"))
    if kind == "observation":
        welded = spawn_door(unreal.WeldableBulkheadDoor, SECOND_DOOR_X, CORRIDOR[3], z, 0.0, f"Door_{code}-B", tags=("CorvetteWeldedDoor",))
        welded.set_editor_property("welded_shut", True)
    else:
        spawn_door(bulkhead_class, SECOND_DOOR_X, CORRIDOR[3], z, 0.0, f"Door_{code}-B")
    spawn_door(bulkhead_class, SERVICE_DOOR_X, CORRIDOR[2], z, 0.0, f"Door_{code}-S")
    if deck in ROOM_HATCH_DECKS:
        spawn_door(bulkhead_class, MAIN[1], HATCH_Y, z, 90.0, f"Door_{code}-H", tags=("CorvetteRoomHatch",))
    state["doors"][code] = main_door

    # Lights: one per room (utility, dark until power), corridor fixtures, the trunk.
    cx, cy = (MAIN[0] + MAIN[1]) * 0.5, (MAIN[2] + MAIN[3]) * 0.5
    warm = unreal.LinearColor(1.0, 0.749, 0.486, 1.0)
    cool = unreal.LinearColor(0.725, 0.863, 0.922, 1.0)
    # Every room light is a utility light, dark until the bus is back: the cryo bay has only the
    # pods' own blue glow before the crew suit up and light their way with the wrist lamp.
    main_light = spawn_room_light(code, cx, cy, z, cool, 0.0)
    main.set_editor_property("identity_light", main_light)
    second.set_editor_property("identity_light", spawn_room_light(f"{code}-B", (SECOND[0] + SECOND[1]) * 0.5, cy, z, cool, 0.0))
    service.set_editor_property("identity_light", spawn_room_light(f"{code}-S", (SERVICE[0] + SERVICE[1]) * 0.5, 300.0, z, cool, 0.0, radius=1200.0))
    for i, lx in enumerate((400.0, 1200.0, 2000.0)):
        spawn_room_light(f"{code}-C{i}", lx, 800.0, z, cool, 0.0, radius=700.0)
        place(K.lamp, (lx, 800.0, ceiling_under - 8.0), (0, 0, 0), (0.6, 1.0, 1.0), f"D{deck:02d}_CorridorLamp_{i}", collide=False)
    spawn_room_light(f"{code}-T", 550.0, 450.0, z, cool, 0.0, radius=900.0)
    place(K.lamp, (cx, cy, ceiling_under - 8.0), (0, 0, 90.0), (0.8, 1.0, 1.0), f"D{deck:02d}_MainLamp", collide=False)
    kit_light(cx, cy, ceiling_under, f"{deck:02d}", 0)
    kit_light((SECOND[0] + SECOND[1]) * 0.5, cy, ceiling_under, f"{deck:02d}", 1)
    # Practicals: dim amber everywhere, the casualty station brighter and cooler (it is the bay
    # the sleeper wakes in and the one room on its own circuit).
    bay = kind == "cryo"
    spawn_practical(code, cx, cy, z, 1600.0 if bay else 320.0, colour=unreal.LinearColor(0.85, 0.92, 1.0, 1.0) if bay else None, radius=1300.0 if bay else 800.0)
    if bay:
        pass  # the pods light themselves (blue glow on ACryoPodSystem)
    spawn_practical(f"{code}-B", (SECOND[0] + SECOND[1]) * 0.5, cy, z, 220.0)
    spawn_practical(f"{code}-S", (SERVICE[0] + SERVICE[1]) * 0.5, 300.0, z, 180.0, radius=1000.0)
    for i, lx in enumerate((400.0, 1200.0, 2000.0)):
        spawn_practical(f"{code}-C{i}", lx, 800.0, z, 160.0, radius=650.0, height=330.0)
    spawn_practical(f"{code}-T", 550.0, 450.0, z, 220.0, radius=900.0)

    # Signs at the room doors.
    # Text faces its local +X; -90 turns it to face -Y, toward a reader in the corridor.
    # Signs sit on walls, plate to the panel. The corridor's fore wall face is at y=950 and the
    # aft hull's inward face at y=53: the room-door signs go beside their doors on the former,
    # the trunk's deck and ramp signs onto the latter, read from the landing.
    wall_fore = CORRIDOR[3] - PARTITION - 3.0
    hull_aft = WALL_D + 3.0
    spawn_sign(f"{code} // {name.upper()}", MAIN_DOOR_X - 260.0, wall_fore, z, -90.0, code, big=True)
    spawn_sign(f"{code}-B // {SECOND_NAMES[deck].upper()}", SECOND_DOOR_X - 260.0, wall_fore, z, -90.0, f"{code}-B")
    spawn_sign(f"DECK {deck:02d}", 550.0, hull_aft, z, 90.0, f"{code}-T", big=True)
    # Wayfinding at the trunk: what the ramp beside you leads to.
    if has_ramp:
        spawn_sign(f"UP  >  DECK {deck + 1:02d}", RAMP_X1 + 120.0, hull_aft, z, 90.0, f"{code}-Up")
    if has_hole:
        spawn_sign(f"DOWN  >  DECK {deck - 1:02d}", RAMP_X0 - 120.0, hull_aft, z, 90.0, f"{code}-Down")
    if plenum_ramp_up:
        spawn_sign(f"SERVICE WAY  >  DECK {deck + 1:02d}", SERVICE_RAMP_X1 + 100.0, hull_aft, z, 90.0, f"{code}-SvcUp")
    if plenum_hole:
        spawn_sign(f"SERVICE WAY  >  DECK {deck - 1:02d}", SERVICE_RAMP_X0 - 60.0, hull_aft, z, 90.0, f"{code}-SvcDown")

    # Dressing by role, then the gameplay of the deck.
    dress_and_play(deck, kind, code, z, main, second, service, main_door, bulkhead_class, state)


def side_station(cls, deck, code, z, name, display, port=False, dy=0.0, condition="WORN", rarity="ROUTINE", mount="WALL_PANEL"):
    """Optional work on a deck's side wall: a real activity station off the objective chain, so
    every deck has something to do besides walk through it."""
    cy = (MAIN[2] + MAIN[3]) * 0.5
    # Back to the wall: the port hull's inward face is at WALL_D, the partition's at MAIN[1] - PARTITION,
    # and the terminal is 38 cm deep from its origin.
    x = WALL_D + 40.0 if port else MAIN[1] - PARTITION - 40.0
    station = spawn_station(cls, x, cy + dy, z, 0.0 if port else 180.0, name, display=display, condition=condition, rarity=rarity, mount=mount,
                            tags=("QuickDemoGameplay", "CorvetteSideStation", code))
    # A work light over each side station: they sit on the side walls, away from the room's
    # practical, and read as black panels otherwise.
    spawn_practical(f"{code}-{name}", x + (120.0 if port else -120.0), cy + dy, z, 140.0, radius=500.0, height=230.0)
    return station


ITEMS = "/Game/Assets/Gameplay/FieldSupplies/Data/Items"


def supply(item, x, y, z_floor, code, quantity=1, name=None):
    """A field supply on the deck: an inventory pickup drawing the item's own world mesh."""
    definition = load(f"{ITEMS}/DA_Item_{item}")
    if not definition:
        unreal.log_warning(f"no item definition DA_Item_{item}")
        return None
    pickup = actors.spawn_actor_from_class(unreal.InventoryItemPickup, unreal.Vector(x, y, z_floor + 6.0), unreal.Rotator(pitch=0.0, yaw=35.0, roll=0.0))
    label(pickup, name or f"Supply_{item}_{code[-3:]}")
    pickup.set_editor_property("item_definition", definition)
    pickup.set_editor_property("quantity", quantity)
    pickup.set_editor_property("tags", [unreal.Name("CorvetteSupply"), unreal.Name(code)])
    return pickup


def oxygen_canister(x, y, z_floor, code, amount=35.0):
    """A loose oxygen canister: walked over, it tops the suit up."""
    pickup = actors.spawn_actor_from_class(unreal.SurvivalPickup, unreal.Vector(x, y, z_floor + 30.0), unreal.Rotator())
    label(pickup, f"O2Canister_{code[-3:]}")
    pickup.set_editor_property("pickup_type", unreal.PickupType.OXYGEN)
    pickup.set_editor_property("amount", amount)
    pickup.set_editor_property("tags", [unreal.Name("CorvetteSupply"), unreal.Name(code)])
    return pickup


def spawn_barrier(x, y, z_floor, yaw, name, display, bypassable, cut_seconds, squeeze_seconds, squeeze_entrapment=0.25,
                  visual=None, visual_offset=(0.0, 0.0, 0.0), visual_rotation=(0.0, 0.0, 0.0), visual_scale=(1.0, 1.0, 1.0), allow_cut=True):
    """An obstruction across a passage: cut through with the tool, or squeeze past. The blocker is
    a box (depth x, width y, height z in the barrier's frame); the visual is a Fab mesh posed to
    fill it, since an invisible box with a prompt is a bug, not an obstacle."""
    barrier = actors.spawn_actor_from_class(unreal.ObstructionBarrier, unreal.Vector(x, y, z_floor + 160.0), unreal.Rotator(pitch=0.0, yaw=yaw, roll=0.0))
    label(barrier, name)
    if visual:
        comp = barrier.get_editor_property("visual_mesh")
        comp.set_static_mesh(visual)
        comp.set_editor_property("relative_location", unreal.Vector(*visual_offset))
        comp.set_editor_property("relative_rotation", unreal.Rotator(roll=visual_rotation[0], pitch=visual_rotation[1], yaw=visual_rotation[2]))
        comp.set_editor_property("relative_scale3d", unreal.Vector(*visual_scale))
    barrier.set_editor_property("display_name", display)
    barrier.set_editor_property("bypassable", bypassable)
    cut = unreal.ObstructionVerbOption(); cut.set_editor_property("allowed", allow_cut); cut.set_editor_property("duration_seconds", cut_seconds)
    cut.set_editor_property("minimum_equipment_condition", 0.2); cut.set_editor_property("noise_loudness", 0.3)
    squeeze = unreal.ObstructionVerbOption(); squeeze.set_editor_property("allowed", True); squeeze.set_editor_property("duration_seconds", squeeze_seconds)
    squeeze.set_editor_property("noise_loudness", 0.15); squeeze.set_editor_property("near_entrapment_chance", squeeze_entrapment)
    barrier.set_editor_property("options", {unreal.ObstructionVerb.CUT: cut, unreal.ObstructionVerb.SQUEEZE: squeeze})
    return barrier


STARFIELD_MATERIAL = "/Game/Assets/Ships/Production/Materials/Space/M_Starfield"
AMBIENT = "/Game/HorrorAmbientSFX/HorrorAmbientSFX_cue"


def starfield_material():
    """A black emissive sky with sparse white points from world-space noise: what the observation
    deck's windows look out on. Built once, reused by every regeneration."""
    if unreal.EditorAssetLibrary.does_asset_exist(STARFIELD_MATERIAL):
        return unreal.load_asset(STARFIELD_MATERIAL)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mel = unreal.MaterialEditingLibrary
    mat = tools.create_asset("M_Starfield", STARFIELD_MATERIAL.rsplit("/", 1)[0], unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", True)
    stars = load("/Engine/EngineSky/T_Sky_Stars")
    if stars:
        # The engine's own tiling star map on the sphere's UVs, tiled so a star is a point.
        uv = mel.create_material_expression(mat, unreal.MaterialExpressionTextureCoordinate, -700, 0)
        uv.set_editor_property("u_tiling", 3.0); uv.set_editor_property("v_tiling", 3.0)
        sample = mel.create_material_expression(mat, unreal.MaterialExpressionTextureSample, -500, 0)
        sample.set_editor_property("texture", stars)
        mel.connect_material_expressions(uv, "", sample, "UVs")
        bright = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -200, 0)
        gain = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -350, 200); gain.set_editor_property("r", 4.0)
        mel.connect_material_expressions(sample, "RGB", bright, "A"); mel.connect_material_expressions(gain, "", bright, "B")
    else:
        # No star map: sparse points from world-space Voronoi noise.
        pos = mel.create_material_expression(mat, unreal.MaterialExpressionWorldPosition, -900, 0)
        scale = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -900, 200); scale.set_editor_property("r", 0.00001)
        mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -700, 60)
        mel.connect_material_expressions(pos, "", mul, "A"); mel.connect_material_expressions(scale, "", mul, "B")
        noise = mel.create_material_expression(mat, unreal.MaterialExpressionNoise, -520, 60)
        noise.set_editor_property("noise_function", unreal.NoiseFunction.NOISEFUNCTION_VORONOI_ALU)
        noise.set_editor_property("levels", 1); noise.set_editor_property("output_min", 0.0); noise.set_editor_property("output_max", 1.0)
        mel.connect_material_expressions(mul, "", noise, "Position")
        one = mel.create_material_expression(mat, unreal.MaterialExpressionOneMinus, -340, 60)
        mel.connect_material_expressions(noise, "", one, "")
        power = mel.create_material_expression(mat, unreal.MaterialExpressionPower, -180, 60)
        exponent = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -340, 220); exponent.set_editor_property("r", 200.0)
        mel.connect_material_expressions(one, "", power, "Base"); mel.connect_material_expressions(exponent, "", power, "Exp")
        bright = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -20, 60)
        gain = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -180, 220); gain.set_editor_property("r", 25.0)
        mel.connect_material_expressions(power, "", bright, "A"); mel.connect_material_expressions(gain, "", bright, "B")
    mel.connect_material_property(bright, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


OBSERVATION_GLASS = "/Game/Assets/Ships/Production/Materials/Space/M_ObservationGlass"


def observation_glass():
    """Clean armoured glass: translucent, a little blue, a little reflective. The kit's own glass
    panel is dirty enough to hide the stars behind it."""
    if unreal.EditorAssetLibrary.does_asset_exist(OBSERVATION_GLASS):
        return unreal.load_asset(OBSERVATION_GLASS)
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    mel = unreal.MaterialEditingLibrary
    mat = tools.create_asset("M_ObservationGlass", OBSERVATION_GLASS.rsplit("/", 1)[0], unreal.Material, unreal.MaterialFactoryNew())
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    mat.set_editor_property("two_sided", True)
    mat.set_editor_property("translucency_lighting_mode", unreal.TranslucencyLightingMode.TLM_SURFACE)
    colour = mel.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -400, -100)
    colour.set_editor_property("constant", unreal.LinearColor(0.02, 0.04, 0.06, 1.0))
    mel.connect_material_property(colour, "", unreal.MaterialProperty.MP_BASE_COLOR)
    opacity = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 100); opacity.set_editor_property("r", 0.12)
    mel.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)
    rough = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 220); rough.set_editor_property("r", 0.08)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    spec = mel.create_material_expression(mat, unreal.MaterialExpressionConstant, -400, 340); spec.set_editor_property("r", 0.9)
    mel.connect_material_property(spec, "", unreal.MaterialProperty.MP_SPECULAR)
    mel.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def spawn_space(height):
    """The sky sphere around the whole stack, inside-out black with stars, far enough out that no
    deck's hull glass meets it. The Dam_city sphere mesh is 82 m across at scale 1."""
    sphere = load("/Game/Dam_city/Meshes/Sky_sphere/SM_SkySphere")
    if not sphere:
        return None
    star = starfield_material()
    sky = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(FOOT_X * 0.5, FOOT_Y * 0.5, height * 0.5), unreal.Rotator())
    comp = sky.static_mesh_component
    comp.set_static_mesh(sphere)
    comp.set_mobility(unreal.ComponentMobility.STATIC)
    comp.set_editor_property("use_default_collision", False)
    comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    comp.set_editor_property("cast_shadow", False)
    comp.set_editor_property("can_ever_affect_navigation", False)
    if star:
        for slot in range(comp.get_num_materials()):
            comp.set_material(slot, star)
    sky.set_actor_scale3d(unreal.Vector(6.0, 6.0, 6.0))
    sky.set_editor_property("tags", [unreal.Name("CorvetteSpace")])
    return label(sky, "Space")


def spawn_ambient(cue_name, x, y, z, code, volume=0.35, radius=1400.0):
    """A looping drone in a room or corridor, falling off before the next deck hears it."""
    cue = load(f"{AMBIENT}/{cue_name}")
    if not cue:
        return None
    sound = actors.spawn_actor_from_class(unreal.AmbientSound, unreal.Vector(x, y, z + 200.0), unreal.Rotator())
    label(sound, f"Ambient_{cue_name.replace('AMB_Drone_', '').replace('_Cue', '')}_{code[-3:]}")
    audio = sound.get_editor_property("audio_component")
    audio.set_sound(cue)
    audio.set_editor_property("volume_multiplier", volume)
    audio.set_editor_property("override_attenuation", True)
    att = audio.get_editor_property("attenuation_overrides")
    att.set_editor_property("falloff_distance", radius)
    att.set_editor_property("attenuation_shape_extents", unreal.Vector(300.0, 300.0, 300.0))
    audio.set_editor_property("attenuation_overrides", att)
    sound.set_editor_property("tags", [unreal.Name("CorvetteAmbient"), unreal.Name(code)])
    return sound


def kit_light(x, y, z_ceiling_under, code, i, colour=None, intensity=90.0):
    """A real ceiling fixture where the room's practical light is: the kit's light bar, glowing,
    with a soft point light under it. Replaces a bare bulb hanging in the air."""
    if K.rc_light_bar:
        place(K.rc_light_bar, (x, y, z_ceiling_under - 2.0), (0, 0, 0), (2.4, 2.4, 1.0), f"D{code}_Fixture_{i}", collide=False)


def atmosphere(deck, kind, z, seed):
    """Smoke hanging in the rooms that still hold air: a dead ship's atmosphere is not clean. The
    hanging smoke from the city pack, low over the deck in the main and second rooms. Nothing in
    the breach deck (vacuum), nothing in the corridor beyond the casualty station (vacuum)."""
    if kind == "breach":
        return
    smoke = unreal.load_asset("/Game/Sci_Fi_city/FX/NS_Hanging_smoke_floor")
    if not smoke:
        print("CORVETTE no hanging smoke asset; rooms stay clear")
        return
    rng = random.Random(seed * 131 + deck)
    name = f"D{deck:02d}"
    rooms = [((MAIN[0] + MAIN[1]) * 0.5, (MAIN[2] + MAIN[3]) * 0.5, "Main"), ((SECOND[0] + SECOND[1]) * 0.5, (SECOND[2] + SECOND[3]) * 0.5, "Second")]
    for x, y, label_name in rooms:
        for i in range(2):
            fx = actors.spawn_actor_from_class(unreal.NiagaraActor, unreal.Vector(x + rng.uniform(-220.0, 220.0), y + rng.uniform(-160.0, 160.0), z + 30.0 + i * 60.0), unreal.Rotator(yaw=rng.uniform(0.0, 360.0)))
            comp = fx.get_editor_property("niagara_component")
            comp.set_asset(smoke)
            fx.set_actor_scale3d(unreal.Vector(1.6, 1.6, 1.0))
            label(fx, f"{name}_Smoke_{label_name}_{i}")
            fx.set_editor_property("tags", [unreal.Name("CorvetteAtmosphere"), unreal.Name(f"D{deck:02d}")])


def furnish(deck, kind, z, seed):
    """Furniture by what the deck is for, from the Rooms and Corridors kit: bunks in the marine
    ready room, a mess in the commons, plotting tables in tactical, lockers and shelving in the
    workshop and the casualty station. Seeded so a regenerate shuffles the details, not the plan."""
    rng = random.Random(seed * 7919 + deck)
    cx, cy = (MAIN[0] + MAIN[1]) * 0.5, (MAIN[2] + MAIN[3]) * 0.5
    sx, sy = (SECOND[0] + SECOND[1]) * 0.5, (SECOND[2] + SECOND[3]) * 0.5
    name = f"D{deck:02d}"
    # The second room, by deck: what is kept there.
    if kind == "marine" and K.rc_bed:
        for i in range(3):
            place(K.rc_bed, (SECOND[0] + 120.0 + i * 260.0, SECOND[3] - WALL_D - 8.0, z), (0, 0, -90.0), (1, 1, 1), f"{name}_Bunk_{i}")
        for i in range(2):
            place(K.rc_locker, (SECOND[0] + 180.0 + i * 300.0, SECOND[2] + PARTITION + 30.0, z), (0, 0, 0), (1, 1, 1), f"{name}_KitLocker_{i}")
    elif kind == "commons" and K.rc_table:
        for i, (tx, ty) in enumerate(((cx - 300.0, cy + 120.0), (cx + 300.0, cy + 120.0), (cx, cy - 220.0))):
            place(K.rc_table, (tx, ty, z), (0, 0, rng.choice((0.0, 90.0))), (1, 1, 1), f"{name}_MessTable_{i}")
            for j, (dx, dy) in enumerate(((-110.0, 0.0), (110.0, 0.0))):
                place(K.rc_chair, (tx + dx, ty + dy, z), (0, 0, 90.0 if dx < 0 else -90.0), (1, 1, 1), f"{name}_MessChair_{i}_{j}")
        for i in range(3):
            place(K.rc_bin, (SECOND[0] + 100.0 + i * 120.0, SECOND[2] + PARTITION + 30.0, z), (0, 0, 0), (1, 1, 1), f"{name}_Bin_{i}")
    elif kind in ("tactical", "cic") and K.rc_table:
        place(K.rc_table, (sx, sy, z), (0, 0, 0), (1.3, 1.3, 1.0), f"{name}_PlotTable")
        for j, (dx, dy) in enumerate(((-140.0, 0.0), (140.0, 0.0), (0.0, -90.0))):
            place(K.rc_chair, (sx + dx, sy + dy, z), (0, 0, (90.0, -90.0, 0.0)[j]), (1, 1, 1), f"{name}_PlotChair_{j}")
    elif kind in ("workshop", "power", "sensors") and K.rc_shelf:
        for i in range(2):
            place(K.rc_shelf, (SECOND[0] + 60.0 + i * 420.0, SECOND[3] - WALL_D - 90.0, z), (0, 0, 0), (1, 1, 1), f"{name}_Shelving_{i}")
        place(K.rc_bin, (SECOND[1] - 120.0, SECOND[2] + PARTITION + 40.0, z), (0, 0, 0), (1, 1, 1), f"{name}_Bin_0")
    elif kind in ("cryo", "security", "observation") and K.rc_locker:
        for i in range(3):
            place(K.rc_locker, (SECOND[0] + 120.0 + i * 200.0, SECOND[3] - WALL_D - 30.0, z), (0, 0, 180.0), (1, 1, 1), f"{name}_Locker_{i}")
    # Pillars at the partition ends, so the rooms read as framed structure rather than boxes.
    if K.rc_pillar:
        for i, py in enumerate((MAIN[2] + PARTITION + 30.0, MAIN[3] - WALL_D - 80.0)):
            place(K.rc_pillar, (MAIN[1] - PARTITION - 14.0, py, z), (0, 0, 90.0), (1, 1, 1.0), f"{name}_Pillar_{i}")


def damage(deck, kind, z, seed):
    """Seeded damage in the second room of some decks, distinguishable at a glance (art guide):
    arcing (a torn-open electrical box, a dropped cable run, a dead fixture and a flickering red
    warning), or impact (a toppled barrel, a fallen duct section, dust light). The chain decks'
    authored damage is untouched; only the rooms off the chain vary run to run."""
    rng = random.Random(seed * 104729 + deck * 31)
    if kind in ("cryo", "breach", "cic"):
        return
    roll = rng.random()
    sx, sy = (SECOND[0] + SECOND[1]) * 0.5, (SECOND[2] + SECOND[3]) * 0.5
    name = f"D{deck:02d}"
    if roll < 0.4:
        # Arcing.
        place(K.electric_box, (sx - 200.0, SECOND[2] + PARTITION + 60.0, z + 20.0), (0, 35.0, 0), (1, 1, 1), f"{name}_DamageBox", collide=False)
        place(K.cable, (sx - 120.0, sy - 80.0, z + 8.0), (0, 0, rng.uniform(0, 180)), (1.4, 1.2, 1.0), f"{name}_DamageCable", collide=False)
        arc = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(sx - 160.0, SECOND[2] + PARTITION + 80.0, z + 90.0), unreal.Rotator())
        label(arc, f"{name}_DamageArc")
        lc = arc.get_component_by_class(unreal.PointLightComponent)
        lc.set_editor_property("intensity", 260.0); lc.set_editor_property("attenuation_radius", 500.0)
        lc.set_editor_property("light_color", unreal.Color(r=255, g=90, b=40))
        arc.set_editor_property("tags", [unreal.Name("CorvetteDamage"), unreal.Name("Arcing")])
    elif roll < 0.7:
        # Impact.
        place(K.barrel, (sx + 150.0, sy + 60.0, z + 11.0), (88.0, 0, rng.uniform(0, 360)), (1, 1, 1), f"{name}_DamageBarrel")
        place(K.duct_run, (sx - 60.0, sy + 200.0, z + 10.0), (0, 0, rng.uniform(-30, 30)), (0.5, 1.0, 1.0), f"{name}_DamageDuct", collide=False)
    else:
        # Collapse: the second room's doorway half-blocked by a fallen duct section the crew cut
        # through or squeeze past, and a spill of crates behind it. The room stays reachable.
        # Half the collapses are crawled under, on hands and knees in third person; the rest are
        # cut through or squeezed past.
        if rng.random() < 0.5:
            spawn_barrier(SECOND[0] + 40.0, HATCH_Y, z, 90.0, f"{name}_RoomCollapse", "Collapsed duct: crawl under", True, 0.0, 8.0, squeeze_entrapment=0.2,
                          visual=K.duct_run, visual_offset=(0.0, 60.0, -120.0), visual_rotation=(0.0, 20.0, 80.0), visual_scale=(0.6, 1.0, 1.0), allow_cut=False)
        else:
            spawn_barrier(SECOND[0] + 40.0, HATCH_Y, z, 90.0, f"{name}_RoomCollapse", "Collapsed duct section", True, 6.0, 4.0, squeeze_entrapment=0.15,
                          visual=K.duct_run, visual_offset=(0.0, 60.0, -120.0), visual_rotation=(0.0, 20.0, 80.0), visual_scale=(0.6, 1.0, 1.0))
        for i in range(2):
            place(K.crate, (SECOND[0] + 260.0 + i * 130.0, HATCH_Y + rng.uniform(-90.0, 90.0), z), (0, 0, rng.uniform(0, 360)), (0.8, 0.8, 0.8), f"{name}_CollapseCrate_{i}")
    # Every deck off the chain: one more thing in the corridor to work round, seeded so the
    # walk differs run to run: a fallen cable tray across the corridor (squeeze or cut).
    if kind in ("security", "marine", "commons", "tactical", "observation", "sensors") and rng.random() < 0.6:
        bx = rng.choice((700.0, 1100.0, 1900.0))
        spawn_barrier(bx, (CORRIDOR[2] + CORRIDOR[3]) * 0.5, z, 0.0, f"{name}_CorridorTray", "Fallen cable tray", True, 6.0, 4.0, squeeze_entrapment=0.1,
                      visual=K.duct_run, visual_offset=(0.0, 0.0, -110.0), visual_rotation=(0.0, 12.0, 90.0), visual_scale=(0.7, 1.0, 1.0))


def dress_and_play(deck, kind, code, z, main, second, service, main_door, bulkhead_class, state):
    cx, cy = (MAIN[0] + MAIN[1]) * 0.5, (MAIN[2] + MAIN[3]) * 0.5
    sx, sy = (SECOND[0] + SECOND[1]) * 0.5, (SECOND[2] + SECOND[3]) * 0.5
    vx, vy = (SERVICE[0] + SERVICE[1]) * 0.5, (SERVICE[2] + SERVICE[3]) * 0.5
    back_y = MAIN[3] - 120.0   # along the fore hull wall of the main room
    # Every service plenum: machinery and cabling.
    linked = deck in SERVICE_RAMP_DECKS or (deck - 1) in SERVICE_RAMP_DECKS
    if linked:
        # The lane is the ramp's; the machinery stands along the corridor-side wall.
        place(K.generator, (SERVICE[0] + 160.0, SERVICE_LANDING[1] - 110.0, z), (0, 0, 0), (0.7, 0.7, 0.7), f"D{deck:02d}_ServiceGen")
        place(K.electric_box, (SERVICE[1] - 120.0, SERVICE_LANDING[1] - 90.0, z), (0, 0, 180.0), (1, 1, 1), f"D{deck:02d}_ServiceBox")
    else:
        place(K.generator, (vx - 300.0, vy, z), (0, 0, 90.0), (0.8, 0.8, 0.8), f"D{deck:02d}_ServiceGen")
        place(K.electric_box, (vx + 250.0, SERVICE[2] + 90.0, z), (0, 0, 0), (1, 1, 1), f"D{deck:02d}_ServiceBox")
    place(K.cable, (vx, SERVICE[2] + 70.0, z + 300.0), (0, 0, 0), (1.5, 1, 1), f"D{deck:02d}_ServiceCable", collide=False)
    place(K.duct, (vx + 450.0, vy, z + 330.0), (0, 0, 0), (1, 1, 1), f"D{deck:02d}_ServiceDuct", collide=False)
    # Every secondary room: storage.
    for i, dx in enumerate((-250.0, 0.0, 250.0)):
        place(K.crate, (sx + dx, SECOND[3] - 150.0, z), (0, 0, 15.0 * i), (1.5, 1.5, 1.5) if i == 1 else (1, 1, 1), f"D{deck:02d}_SecondCrate_{i}")

    if kind == "power":
        for i, dx in enumerate((-400.0, 0.0, 400.0)):
            place(K.generator, (cx + dx, back_y - 60.0, z), (0, 0, 0), (1, 1, 1), f"D{deck:02d}_MainGen_{i}")
        station = spawn_station(unreal.QuickDemoPowerStation, cx, cy - 150.0, z, 0.0, "PowerRestore", target=main,
                                mount="FLOOR_CONSOLE", rarity="CRITICAL", wear=0.2)
        main.set_editor_property("system_anchor", station)
        spawn_beacon("QD_RestorePower", "MAIN POWER", MAIN_DOOR_X, CORRIDOR[3] + 130.0, z, 90.0, code)
        place(K.distrib, (MAIN[0] + 60.0, cy, z + 120.0), (0, 0, -90.0), (1, 1, 1), f"D{deck:02d}_Distrib", collide=False)
        side_station(unreal.BatteryRecoveryStation, deck, code, z, "BatteryRecovery", "Recover backup batteries", dy=-200.0)
    elif kind == "workshop":
        trigger = actors.spawn_actor_from_class(unreal.QuickDemoObjectiveTrigger, unreal.Vector(cx, cy, z + 150.0), unreal.Rotator())
        label(trigger, "WorkshopTrigger")
        trigger.set_editor_property("objective_id", unreal.Name("QD_ReachWorkshop"))
        trigger.get_editor_property("trigger_bounds").set_box_extent(unreal.Vector(700.0, 420.0, 180.0))
        no_nav(trigger.get_editor_property("trigger_bounds"))
        bench = actors.spawn_actor_from_class(unreal.QuickDemoWorkshopBench, unreal.Vector(cx - 200.0, back_y, z + 90.0), unreal.Rotator(pitch=0.0, yaw=180.0, roll=0.0))
        label(bench, "WorkshopBench")
        # The bench is the toolbox itself, on the table where a person looks for a tool; the
        # console it used to be read as furniture and nobody found the tool.
        bench.get_editor_property("mesh").set_static_mesh(K.toolbox)
        bench.get_editor_property("mesh").set_relative_scale3d(unreal.Vector(1.6, 1.6, 1.6))
        bench.set_actor_location(unreal.Vector(cx + 550.0, cy, z + 92.0), False, False)
        weapon = load("/Game/Assets/Gameplay/EarlyProjectileWeapons/Data/Weapons/DA_Weapon_PressureBottleFastenerTool")
        weapon_class = load("/Game/Assets/Gameplay/EarlyProjectileWeapons/Blueprints/BP_Weapon_PressureBottleFastenerTool")
        if weapon:
            bench.set_editor_property("granted_weapon_definition", weapon)
        if weapon_class:
            bench.set_editor_property("granted_weapon_class", weapon_class.generated_class())
        items = [i for i in (load(p) for p in ("/Game/Assets/Gameplay/FieldSupplies/Data/Items/DA_Item_FieldRepairKit", "/Game/Assets/Gameplay/FieldSupplies/Data/Items/DA_Item_TraumaKit")) if i]
        if items:
            bench.set_editor_property("granted_items", items)
        repair = actors.spawn_actor_from_class(unreal.QuickDemoSuitRepairBench, unreal.Vector(cx + 300.0, MAIN[3] - WALL_D - 40.0, z + 41.0), unreal.Rotator(pitch=0.0, yaw=-90.0, roll=0.0))
        label(repair, "SuitRepairBench")
        repair.get_editor_property("mesh").set_static_mesh(K.terminal)
        # (No second toolbox: one is the bench, and two would send the player to the wrong one.)
        place(K.table, (cx + 550.0, cy, z), (0, 0, 0), (1, 1, 1), f"D{deck:02d}_Table")
        spawn_beacon("QD_ReachWorkshop", "ENGINEERING CONTROL", MAIN_DOOR_X, CORRIDOR[3] + 130.0, z, 90.0, code)
    elif kind == "cryo":
        pod_class = unreal.CryoPodSystem
        for i, px in enumerate((cx - 250.0, cx + 250.0)):
            pod = actors.spawn_actor_from_class(pod_class, unreal.Vector(px, back_y - 40.0, z), unreal.Rotator(pitch=0.0, yaw=-90.0, roll=0.0))
            label(pod, f"CryoPod_{i + 1:02d}")
            state["pods"].append(pod)
        for i, (px, role) in enumerate(((MAIN[0] + 120.0, "MEDICAL"), (MAIN[0] + 120.0, "ENGINEERING"))):
            station = actors.spawn_actor_from_class(unreal.QuickDemoSuitStation, unreal.Vector(px, cy - 200.0 + i * 400.0, z + 100.0), unreal.Rotator(pitch=0.0, yaw=0.0, roll=0.0))
            label(station, f"SuitStation_{i + 1:02d}")
            station.get_editor_property("mesh").set_static_mesh(K.locker)
            station.set_editor_property("suit_role", enum_value(unreal.PressureSuitRole, role))
            station.set_editor_property("tags", [unreal.Name("QuickDemoGameplay"), unreal.Name("CryoSuitStation")])
            place(K.nitrogen, (px + 90.0, cy - 200.0 + i * 400.0 + 130.0, z), (0, 0, 0), (1, 1, 1), f"D{deck:02d}_SuitTank_{i}", collide=False)
        # The treatment table is the kit's table, not the Ice Station bed: SM_bed_01 is authored at
        # four times life size with its pivot on top (bounds 856 x 322, 0 down to -600), so at
        # scale one it hung six metres through the deck below and sealed that deck's doorway with
        # its collision, and at quarter scale its floor trim sheet reads as a white slab.
        place(K.table, (cx, cy - 150.0, z), (0, 0, 90.0), (1, 1, 1), f"D{deck:02d}_TreatmentTable")
        place(K.toolbox, (cx + 40.0, cy - 150.0, z + 92.0), (0, 0, -20.0), (0.9, 0.9, 0.9), f"D{deck:02d}_TraumaKit", collide=False)
        place(K.lab_capsule, (MAIN[1] - 200.0, cy, z), (0, 0, 0), (0.6, 0.6, 0.6), f"D{deck:02d}_MedCapsule")
        start = actors.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(cx - 250.0, back_y - 300.0, z + 100.0), unreal.Rotator(pitch=0.0, yaw=90.0, roll=0.0))
        label(start, "PlayerStart_Casualty")
        start.set_editor_property("tags", [unreal.Name("CryoWakeStart"), unreal.Name("CorvetteShip")])
        state["start"] = start
        spawn_beacon("QD_SuitUp", "SUIT STATIONS", MAIN_DOOR_X, CORRIDOR[3] + 130.0, z, 90.0, code)
    elif kind == "security":
        # The trunk landing is buckled: cut or squeeze past to keep climbing.
        # A collapsed ceiling frame section across the mouth of the ramp head, where the climb from
        # deck 3 steps onto this landing: the one place on the trunk with no way round it.
        # It also covers the top of the ramp's open edge (x 300..470), where the ramp is still within
        # a step of the landing; further along it is a metre down and no step at all.
        trunk = spawn_barrier(230.0, 345.0, z, 0.0, "TrunkBarrier", "Buckled trunk frame", False, 8.0, 6.0,
                              visual=K.ceiling_frame, visual_offset=(40.0, 240.0, -160.0), visual_rotation=(0.0, -68.0, 0.0), visual_scale=(1.0, 1.0, 1.0))
        trunk.get_editor_property("blocker").set_box_extent(unreal.Vector(60.0, 245.0, 160.0))
        for i, dx in enumerate((-350.0, 0.0, 350.0)):
            place(K.locker, (cx + dx, back_y, z + 100.0), (0, 0, 0), (1, 1, 1), f"D{deck:02d}_ArmoryLocker_{i}", collide=False)
        place(K.computer, (cx, cy - 100.0, z + 80.0), (0, 0, 0), (1, 1, 1), f"D{deck:02d}_SecurityDesk")
        place(K.alarm, (MAIN_DOOR_X + 200.0, CORRIDOR[3] - 60.0, z + 300.0), (0, 0, 0), (1, 1, 1), f"D{deck:02d}_Alarm", collide=False)
        side_station(unreal.MechanicalOverrideStation, deck, code, z, "ArmoryOverride", "Override armory lock", port=True, dy=200.0)
    elif kind == "marine":
        for i, dx in enumerate((-450.0, -150.0, 150.0, 450.0)):
            place(K.locker, (cx + dx, back_y, z + 100.0), (0, 0, 0), (1, 1, 1), f"D{deck:02d}_GearLocker_{i}", collide=False)
        place(K.table, (cx, cy, z), (0, 0, 0), (1, 1, 1), f"D{deck:02d}_BriefingTable")
        place(K.oxygen, (MAIN[0] + 100.0, cy + 250.0, z), (0, 0, 0), (1, 1, 1), f"D{deck:02d}_O2")
        side_station(unreal.TurretServiceStation, deck, code, z, "TurretService", "Service point-defence turret", dy=-200.0)
        side_station(unreal.SuitPatchingStation, deck, code, z, "SuitPatching", "Patch pressure suit", port=True, dy=-150.0)
    elif kind == "commons":
        for i, dx in enumerate((-400.0, 0.0, 400.0)):
            place(K.crate, (cx + dx, back_y - 20.0, z), (0, 0, 90.0), (1, 1, 1), f"D{deck:02d}_GearCrate_{i}")
        place(K.table, (cx, cy - 150.0, z), (0, 0, 0), (1, 1, 1), f"D{deck:02d}_MessTable")
        for i, dx in enumerate((-160.0, 160.0)):
            place(K.chair, (cx + dx, cy - 150.0, z), (0, 0, 90.0 if dx < 0 else -90.0), (1, 1, 1), f"D{deck:02d}_Chair_{i}")
        # The secondary room is an airlock that has lost pressure: repressurise before it opens.
        outer = spawn_door(bulkhead_class, sx, SECOND[3], z, 0.0, f"Airlock_{code}", seal=True)
        station = spawn_station(unreal.AirlockRepressurizationStation, sx - 250.0, SECOND[3] - 90.0, z, 0.0, "AirlockRepressurize", target=outer, display="Repressurise airlock")
        side_station(unreal.OxygenScrubberServiceStation, deck, code, z, "ScrubberService", "Service CO2 scrubbers", dy=200.0)
    elif kind == "breach":
        hazard = actors.spawn_actor_from_class(unreal.HazardZoneActor, unreal.Vector(cx, cy, z + 200.0), unreal.Rotator())
        label(hazard, "VacuumHazard")
        hazard.set_editor_property("tags", [unreal.Name("QuickDemoVacuumHazard"), unreal.Name(code)])
        env = unreal.PhysicsEnvironmentState()
        env.set_editor_property("ambient_pressure_k_pa", 0.25); env.set_editor_property("gravity_multiplier", 0.05)
        env.set_editor_property("vacuum_zone", True); env.set_editor_property("microgravity_zone", True); env.set_editor_property("temperature_c", -90.0)
        hazard.set_editor_property("environment_state", env)
        hazard.get_editor_property("zone_bounds").set_box_extent(unreal.Vector((MAIN[1] - MAIN[0]) * 0.5, (MAIN[3] - MAIN[2]) * 0.5, 200.0))
        no_nav(hazard.get_editor_property("zone_bounds"))
        warning = actors.spawn_actor_from_class(unreal.PointLight, unreal.Vector(cx, cy, z + 240.0), unreal.Rotator())
        label(warning, "BreachWarningLight")
        wc = warning.get_component_by_class(unreal.PointLightComponent)
        wc.set_editor_property("intensity", 0.0); wc.set_editor_property("attenuation_radius", 950.0)
        wc.set_editor_property("light_color", unreal.Color(r=255, g=20, b=8)); wc.set_visibility(False)
        warning.set_editor_property("tags", [unreal.Name("QuickDemoUtilityLight"), unreal.Name(code)])
        patch = spawn_station(unreal.QuickDemoBreachStation, cx - 300.0, MAIN[3] - WALL_D - 40.0, z, -90.0, "BreachPatch", target=hazard, condition="FAULTED", rarity="CRITICAL", wear=0.25)
        # Racks flank the door, not the doorway itself: the middle of the aft wall stays clear so
        # the room is enterable (a rack across the door left 66 cm and no navmesh into the room).
        for i, dx in enumerate((-550.0, 550.0)):
            # Against the aft wall, well clear of the door and the walk to the patch: the survey's
            # character caught its shoulder on a rack standing in the room.
            place(K.ice_computer, (cx + dx * 1.1, MAIN[2] + PARTITION + 40.0, z + 78.0), (0, 0, 0), (1, 1, 1), f"D{deck:02d}_CommsRack_{i}")
        # The rupture itself: the fore hull is torn open beside the patch station (the hull panels
        # there are left out at the wall run), a buckled plate hangs into the room, stars show
        # through, and an unseen wall keeps the crew aboard.
        place(K.ceiling_frame, (cx - 420.0, MAIN[3] - 60.0, z + 60.0), (12.0, -55.0, 0.0), (0.7, 0.55, 1.0), f"D{deck:02d}_BreachPlate")
        place(K.duct_run, (cx - 120.0, MAIN[3] - 140.0, z), (0, 0, 70.0), (0.6, 1.0, 1.0), f"D{deck:02d}_BreachDebris", collide=False)
        for i, bx in enumerate((cx - 500.0, cx - 100.0)):
            seal = place(K.wall[0], (bx, MAIN[3] + 30.0, z), (0, 0, 180.0), (1.0, 1.0, 1.0), f"D{deck:02d}_BreachSeal_{i}")
            if seal:
                seal.static_mesh_component.set_visibility(False)
        wc.set_editor_property("intensity", 900.0); wc.set_visibility(True)
        spawn_beacon("QD_SealBreach", "HULL BREACH", MAIN_DOOR_X, CORRIDOR[3] + 130.0, z, 90.0, code)
    elif kind == "cic":
        # Off the door frame and the sign, out in the corridor, so the eye-line finds the panel.
        access = spawn_station(unreal.QuickDemoCICAccessStation, MAIN_DOOR_X + 380.0, CORRIDOR[3] - PARTITION - 40.0, z, -90.0, "CICAccess", target=main_door, rarity="SPECIALIZED", wear=0.35)
        main.set_editor_property("maintenance_anchor", access)
        console = spawn_station(unreal.QuickDemoCICConsole, cx, cy + 120.0, z, 180.0, "CICConsole", mount="FLOOR_CONSOLE", rarity="CRITICAL", wear=0.3)
        main.set_editor_property("system_anchor", console)
        # The plotting table stands to port of the console, not behind it: the console sits on the
        # deck now and a table on its eye-line took the prompt away.
        place(K.circular, (cx - 380.0, back_y - 60.0, z), (0, 0, 0), (1, 1, 1), f"D{deck:02d}_TacticalTable")
        place(K.control_panel, (cx - 320.0, back_y - 60.0, z + 90.0), (0, 0, 180.0), (0.8, 0.8, 0.8), f"D{deck:02d}_TacticalPlot", collide=False)
        for i, dx in enumerate((-500.0, 500.0)):
            place(K.computer, (cx + dx, cy - 200.0, z + 80.0), (0, 0, 0), (1, 1, 1), f"D{deck:02d}_CICDesk_{i}")
        place(K.wall_display, (cx, MAIN[3] - WALL_D, z), (0, 0, 180.0), (1, 1, 1), f"D{deck:02d}_CICDisplay", collide=False)
        spawn_beacon("QD_ReachCIC", "CIC TACTICAL CONSOLE", MAIN_DOOR_X, CORRIDOR[3] + 130.0, z, 90.0, code)
    elif kind == "tactical":
        place(K.circular, (cx - 75.0, cy, z), (0, 0, 0), (1.2, 1.2, 1.0), f"D{deck:02d}_PlottingTable")
        for i, dx in enumerate((-450.0, 450.0)):
            # SM_ControlPanel01 stands on its origin; SM_COMPUTER_02 reaches 41 below it.
            place(K.control_panel or K.computer2, (cx + dx, MAIN[3] - WALL_D - 40.0, z + (0.0 if K.control_panel else 41.0)), (0, 0, 180.0), (1, 1, 1), f"D{deck:02d}_Plotter_{i}")
        side_station(unreal.ComponentReplacementStation, deck, code, z, "PlotterCore", "Replace plotter core", dy=200.0)
    elif kind == "observation":
        # A glass wall to space along the fore hull.
        for i, dx in enumerate((-550.0, -183.0, 183.0, 550.0)):
            # Solid: the hull behind it is open to space, and the glass is what keeps the crew in.
            pane = place(K.glass, (cx + dx, MAIN[3] - 20.0, z + 200.0), (0, 0, 0), (1, 1, 1.8), f"D{deck:02d}_Window_{i}")
            clear = observation_glass()
            if pane and clear:
                for slot in range(pane.static_mesh_component.get_num_materials()):
                    pane.static_mesh_component.set_material(slot, clear)
        for i, dx in enumerate((-300.0, 300.0)):
            place(K.chair, (cx + dx, cy, z), (0, 0, 90.0), (1, 1, 1), f"D{deck:02d}_ObsChair_{i}")
        side_station(unreal.DecontaminationStation, deck, code, z, "ObsDecon", "Run decontamination cycle", port=True, dy=-200.0)
    elif kind == "sensors":
        for i, dx in enumerate((-500.0, -167.0, 167.0, 500.0)):
            place(K.ice_computer, (cx + dx, back_y, z + 78.0), (0, 0, 180.0), (1, 1, 1), f"D{deck:02d}_SensorRack_{i}")
        place(K.computer2, (cx, cy - 150.0, z + 41.0), (0, 0, 0), (1, 1, 1), f"D{deck:02d}_SensorDesk")
        side_station(unreal.SensorCalibrationStation, deck, code, z, "SensorCalibration", "Calibrate sensor suite", dy=200.0)

    # Supplies. Two spots inside every main room's aft corners, clear of the door, the side
    # stations and each deck's furniture; loose oxygen in a few corridors. Enough to keep the
    # suit's meters honest on the climb, not enough to ignore them.
    SUPPLIES = {
        "power": ("FieldRepairKit", "CoolantGelPack"), "workshop": ("SuitPatchSealant", None), "cryo": ("TraumaKit", "GeneralMedicalAmpoule"),
        "security": ("SuitPatchSealant", "EmergencyOxygenCartridge"), "marine": ("EmergencyOxygenCartridge", "CompoundSplint"),
        "commons": ("GeneralMedicalAmpoule", "EmergencyOxygenCartridge"), "breach": ("SuitPatchSealant", "RecompressionAmpoule"),
        "cic": ("CoolantGelPack", "ChelationInjector"), "tactical": ("FieldRepairKit", None), "observation": ("RecompressionAmpoule", "ThermalRegulationWrap"),
        "sensors": ("EmergencyOxygenCartridge", "FieldRepairKit"),
    }
    a, b = SUPPLIES.get(kind, (None, None))
    if a:
        supply(a, MAIN[0] + 400.0, MAIN[2] + 300.0, z, code)
    if b:
        supply(b, MAIN[1] - 350.0, MAIN[2] + 300.0, z, code)
    if kind in ("marine", "breach", "observation"):
        oxygen_canister(300.0, 800.0, z, code)
    furnish(deck, kind, z, BUILD_SEED)
    damage(deck, kind, z, BUILD_SEED)
    atmosphere(deck, kind, z, BUILD_SEED)
    # The ship's sound: a hum in every main room, the corridor drone along the corridor, and a
    # deeper machine note where the machinery is.
    cx_, cy_ = (MAIN[0] + MAIN[1]) * 0.5, (MAIN[2] + MAIN[3]) * 0.5
    room_cue = {"power": "AMB_Drone_ServerBass_Cue", "workshop": "AMB_Drone_Server_Cue", "breach": "AMB_Drone_Beneath_Cue",
                "cic": "AMB_Drone_Server_Cue", "sensors": "AMB_Drone_AC_Cue"}.get(kind, "AMB_Drone_Hum_Cue")
    spawn_ambient(room_cue, cx_, cy_, z, code, volume=0.3)
    spawn_ambient("AMB_Drone_Corridor_Cue", 1200.0, 800.0, z, code, volume=0.22, radius=1600.0)
    # Obstacles beyond the security deck's trunk: a fallen cable tray across the tactical deck's
    # corridor (squeeze past, or cut it clear). The observation deck's secondary room is welded
    # shut from some earlier emergency and cut free with the tool (see the door spawn).
    # A crawl space: the marine deck's service plenum is reached through a collapsed duct run in
    # its doorway that can only be crawled, on hands and knees, in third person.
    if kind == "marine":
        spawn_barrier(SERVICE_DOOR_X, SERVICE[3] - 90.0, z, 0.0, "PlenumCrawl", "Collapsed duct: crawl through", False, 0.0, 9.0,
                      squeeze_entrapment=0.15, allow_cut=False,
                      visual=K.duct_run, visual_offset=(0.0, 180.0, -60.0), visual_rotation=(0.0, 0.0, 90.0), visual_scale=(1.0, 1.4, 1.0))
    if kind == "commons":
        # A conduit bundle down across the ramp head from the marine deck: no way past but the tool.
        conduit = spawn_barrier(230.0, 345.0, z, 0.0, "ConduitBarrier", "Fallen conduit bundle", False, 7.0, 0.0,
                                visual=K.cable, visual_offset=(0.0, 0.0, -40.0), visual_rotation=(0.0, 0.0, 90.0), visual_scale=(1.6, 2.2, 2.2))
        conduit.get_editor_property("blocker").set_box_extent(unreal.Vector(60.0, 245.0, 160.0))
        options = conduit.get_editor_property("options")
        squeeze = options[unreal.ObstructionVerb.SQUEEZE]
        squeeze.set_editor_property("allowed", False)
        options[unreal.ObstructionVerb.SQUEEZE] = squeeze
        conduit.set_editor_property("options", options)
    if kind == "observation":
        # A ruptured coolant line across the ramp head: squeeze past it, and the line may catch you.
        coolant = spawn_barrier(230.0, 345.0, z, 0.0, "CoolantBarrier", "Ruptured coolant line", True, 9.0, 5.0, squeeze_entrapment=0.4,
                                visual=K.pipe, visual_offset=(0.0, 0.0, -30.0), visual_rotation=(15.0, 0.0, 90.0), visual_scale=(2.4, 1.2, 1.2))
        coolant.get_editor_property("blocker").set_box_extent(unreal.Vector(60.0, 245.0, 160.0))
    if kind == "tactical":
        spawn_barrier(1400.0, 800.0, z, 0.0, "CorridorDebris", "Fallen cable tray", True, 6.0, 4.0, squeeze_entrapment=0.1,
                      visual=K.duct_run, visual_offset=(0.0, 185.0, -120.0), visual_rotation=(18.0, 0.0, 90.0), visual_scale=(1.05, 1.0, 1.0))


# --- the ship -------------------------------------------------------------------------------------

def build():
    global actors, K
    # Rebuilt from scratch. A saved map cannot be deleted while it is the one to create, so an
    # existing map is loaded and emptied instead of recreated.
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP):
        assert les.load_level(MAP), "could not load the existing level"
        old = actors.get_all_level_actors()
        for a in old:
            actors.destroy_actor(a)
        print(f"CORVETTE emptied {len(old)} actors from the existing map")
    else:
        assert les.new_level(MAP), "could not create the level"
    K = Kit()
    bulkhead_asset = load("/Game/Assets/Ships/Production/Blueprints/BP_Ship_ProductionBulkhead")
    bulkhead_class = bulkhead_asset.generated_class() if bulkhead_asset else unreal.BulkheadDoor
    state = {"rooms": {}, "doors": {}, "pods": [], "start": None}

    for deck, name, kind in DECKS:
        build_deck(deck, name, kind, bulkhead_class, state)

    # The ship's mission director, the opening on the sleeper, the exposure, the navmesh, the sky.
    director = actors.spawn_actor_from_class(unreal.QuickDemoMissionDirector, unreal.Vector(1200.0, 900.0, deck_floor_z(3)), unreal.Rotator())
    label(director, "MissionDirector")
    if state["start"] and state["pods"]:
        nearest = min(state["pods"], key=lambda p: (p.get_actor_location() - state["start"].get_actor_location()).length())
        nearest.set_editor_property("tags", list(nearest.tags) + [unreal.Name("QuickDemoPlayerPod")])
        opening = actors.spawn_actor_from_class(unreal.QuickDemoOpeningSequence, state["start"].get_actor_location(), unreal.Rotator())
        label(opening, "OpeningSequence")
        opening.set_editor_property("tags", [unreal.Name("GeneratedDemoOpening")])
        try:
            opening.set_editor_property("room_tag", unreal.Name("CVT-D03"))
        except Exception:
            pass
    volume = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0), unreal.Rotator())
    label(volume, "Exposure")
    volume.set_editor_property("unbound", True); volume.set_editor_property("priority", 10.0)
    settings = volume.get_editor_property("settings")
    # The eye may open up in a dark ship (the pods' glow, the wrist lamp), but not so far that
    # black reads as grey: the floor is low, the bias slightly under.
    settings.set_editor_property("override_auto_exposure_bias", True); settings.set_editor_property("auto_exposure_bias", -0.9)
    settings.set_editor_property("override_auto_exposure_min_brightness", True); settings.set_editor_property("auto_exposure_min_brightness", 1.4)
    settings.set_editor_property("override_auto_exposure_max_brightness", True); settings.set_editor_property("auto_exposure_max_brightness", 11.0)
    volume.set_editor_property("settings", settings)
    height = DECK_PITCH * len(DECKS)
    nav = actors.spawn_actor_from_class(unreal.NavMeshBoundsVolume, unreal.Vector(FOOT_X * 0.5, FOOT_Y * 0.5, height * 0.5), unreal.Rotator())
    label(nav, "NavMeshBounds")
    nav.set_actor_scale3d(unreal.Vector(FOOT_X / 200.0 + 1.0, FOOT_Y / 200.0 + 1.0, height / 200.0 + 1.0))
    # The navmesh itself: the bounds volume makes the editor create a RecastNavMesh, which must be
    # saved with the map. Its tiles are baked afterwards by the editor automation step
    # Ginnungagap.Tools.BakeNavmesh (a commandlet exits before the asynchronous build finishes);
    # static generation, like the old demo map, so PIE uses the saved tiles.
    recast = None
    for a in actors.get_all_level_actors():
        if a.get_class().get_name() == "RecastNavMesh":
            recast = a
    if not recast:
        recast = actors.spawn_actor_from_class(unreal.RecastNavMesh, unreal.Vector(0, 0, 0), unreal.Rotator())
    if recast:
        # Dynamic: the baked mesh is the start, and clearing an obstruction (or a test hiding one)
        # rebuilds the tiles around it so paths past it exist once it is gone.
        recast.set_editor_property("runtime_generation", unreal.RuntimeGenerationType.DYNAMIC)
        # Eleven decks are eleven navmesh layers in every XY tile; the default fixed pool of
        # tiles filled at 27 and the generator dropped the rest ("27 tile limit reached").
        recast.set_editor_property("fixed_tile_pool_size", True)
        recast.set_editor_property("tile_pool_size", 4096)
        label(recast, "NavMesh")
    unreal.SystemLibrary.execute_console_command(None, "RebuildNavigation")
    sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(FOOT_X * 0.5, FOOT_Y * 0.5, height + 500.0), unreal.Rotator())
    label(sky, "SkyLight")
    # Near nothing: a dead ship is dark, and the only fill is what the lamp and the fixtures throw.
    sky.get_component_by_class(unreal.SkyLightComponent).set_editor_property("intensity", 0.02)
    spawn_space(height)
    # Under drive: the stack's "down" is toward the engines. The ship is zero-g until something
    # thrusts, and the crew would float off every deck.
    drive = actors.spawn_actor_from_class(unreal.ShipThrustGravity, unreal.Vector(FOOT_X * 0.5, FOOT_Y * 0.5, 0.0), unreal.Rotator())
    label(drive, "DriveThrustGravity")
    drive.set_editor_property("thrust_direction", unreal.Vector(0.0, 0.0, 1.0))
    drive.set_editor_property("acceleration", 9800.0)
    # Dead until the main bus is back: the crew wake in zero-g and float to the suit rack.
    drive.set_editor_property("engaged_at_start", False)
    drive.set_editor_property("tags", [unreal.Name("CorvetteShip")])

    saved = les.save_current_level()
    unreal.EditorAssetLibrary.save_directory(MAP_DIR)
    print(f"CORVETTE built {MAP}: {spawned} actors, {len(DECKS)} decks, saved={saved}")


build()
