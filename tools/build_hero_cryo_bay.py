"""Builds L_Hero_CryoBay from the project's own canonical cryo room, not an improvised Fab kit.

The first version of this script built a room from generic Modular_Scifi_Mechanic_Base pieces sized
by kit-module math. That ignored the production reference packet that actually governs this room --
docs/concept-art/2026-08-28/production-reference/cryo-bay-modular-kit-v1.production.json -- which
names two approved, already-built assets: /Game/Assets/ShipRooms/Cryo/SM_Room_CryoShell and
SM_Room_CryoMachinery. Those are hand-authored Blender art (source: Art/ShipRooms/CryoPodConceptV4/
CryoPod_ConceptV4.blend per the packet), not stock kit pieces, and they are already placed by real,
approved code in Source/Ginnungagap/Public/LevelSetup/ProceduralShipBuilder.cpp::AddAuthoredCryoRoom.

This copies that placement verbatim rather than re-deriving it. AddAuthoredCryoRoom's own comment
explains the numbers: "Blender's module is authored floor-up and with its hatches on local X...
rotate the module into the room and lower its floor to the section deck" -- ArtOrigin (0,0,-300),
ArtRotation yaw 90, four pods along local X at fixed local Y=-156.2, spaced by the PodX table, two
of the four already Bloom-corrupted in the real ship. Reusing exact numbers that shipped, rather than
inventing new ones and risking a second round of composition surprises.

The palette work from the first attempt is still valid and reused unchanged: Sheet 11 measures near-
neutral (blue-minus-red +0.009, mean saturation 0.209), and that has nothing to do with which room
mesh is underneath it.
"""

import unreal

MAP_PACKAGE = "/Game/Assets/Maps/Hero/L_Hero_CryoBay"

SHELL = "/Game/Assets/ShipRooms/Cryo/SM_Room_CryoShell"
MACHINERY = "/Game/Assets/ShipRooms/Cryo/SM_Room_CryoMachinery"

# Verbatim from AProceduralShipBuilder::AddAuthoredCryoRoom.
ART_ORIGIN = unreal.Vector(0.0, 0.0, -300.0)
ART_ROTATION = unreal.Rotator(0.0, 90.0, 0.0)
POD_X = [-384.3, -136.6, 112.2, 359.9]
POD_LOCAL_Y = -156.2

LAMP_DIM_MATERIAL = "/Game/Assets/Gameplay/Materials/MI_EmergencyFixture_Dim"

TAG = "HeroCryoBay"

# Sheet 11's cryo bay: mean RGB (0.175,0.174,0.184), blue-minus-red +0.009, mean saturation 0.209.
# Near-neutral and dim; nothing here should read as a strong colour.
KEY_COLOUR = unreal.LinearColor(0.86, 0.90, 0.95, 1.0)
# Raised after the first pass: 2 lights at 1400/750 left most of a ~7 x 11m room black even at
# neutral post-process bias, and locked histogram exposure cannot manufacture light that was never
# emitted -- pushing bias could not fix an under-lit room, only a mis-exposed one.
KEY_INTENSITY = 2600.0
KEY_RADIUS = 1100.0


def actors():
    return unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def spawn_mesh(path, location, rotation):
    asset = unreal.load_asset(path)
    if not asset:
        unreal.log_error("HERO missing mesh {}".format(path))
        return None
    actor = actors().spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
    if not actor:
        return None
    actor.static_mesh_component.set_static_mesh(asset)
    actor.static_mesh_component.set_mobility(unreal.ComponentMobility.STATIC)
    actor.tags = [unreal.Name(TAG)]
    return actor


def point_light(location, colour, intensity, radius, source_radius=60.0):
    light = actors().spawn_actor_from_class(unreal.PointLight, location)
    if not light:
        return None
    component = light.point_light_component
    component.set_editor_property("intensity", intensity)
    component.set_light_color(colour)   # LinearColor; never unreal.Color positionally -- see the
                                         # cryo channel-order fix earlier this session.
    component.set_editor_property("attenuation_radius", radius)
    component.set_editor_property("source_radius", source_radius)
    component.set_editor_property("cast_shadows", True)
    component.set_mobility(unreal.ComponentMobility.MOVABLE)
    light.tags = [unreal.Name(TAG)]
    return light


def rotate_yaw(vector, yaw_degrees):
    """FRotator::RotateVector for a pure yaw, matching ArtTransform.TransformPosition in the
    original C++: yaw is a rotation around +Z, +X toward +Y for positive yaw in Unreal's
    left-handed, Z-up convention."""
    import math
    rad = math.radians(yaw_degrees)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    return unreal.Vector(
        vector.x * cos_a - vector.y * sin_a,
        vector.x * sin_a + vector.y * cos_a,
        vector.z)


def build():
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    level.new_level(MAP_PACKAGE)

    shell = spawn_mesh(SHELL, ART_ORIGIN, ART_ROTATION)
    machinery = spawn_mesh(MACHINERY, ART_ORIGIN, ART_ROTATION)

    pod_class = unreal.load_class(None, "/Script/Ginnungagap.CryoPodSystem")
    pods = []
    if not pod_class:
        unreal.log_error("HERO could not load ACryoPodSystem")
    else:
        for index, pod_x in enumerate(POD_X):
            local = unreal.Vector(pod_x, POD_LOCAL_Y, 0.0)
            world = rotate_yaw(local, ART_ROTATION.yaw) + ART_ORIGIN
            pod = actors().spawn_actor_from_class(pod_class, world, ART_ROTATION)
            if not pod:
                continue
            pod.tags = [unreal.Name(TAG)]
            try:
                pod.set_editor_property("system_name", "Cryopod {:02d}".format(index + 1))
            except Exception:
                pass
            pods.append(pod)

    # One pod open -- the nearest to where the camera will stand, at the low end of POD_X --
    # so the frame carries one story: somebody got out. lid_open, not bLidOpen: the leading b is
    # dropped in the Python binding.
    opened = 0
    if pods:
        nearest = min(pods, key=lambda p: p.get_actor_location().y)
        try:
            nearest.set_editor_property("lid_open", True)
            opened = 1
        except Exception as error:
            unreal.log_warning("HERO could not open a lid: {}".format(error))

    # Two lights along the pod row, offset from every pod's own centreline so neither camera nor
    # fixture ever needs to guess around the row the way the improvised room did.
    lit = 0
    for pod in pods:
        loc = pod.get_actor_location()
        if point_light(unreal.Vector(loc.x + 200.0, loc.y, loc.z + 260.0),
                       KEY_COLOUR, KEY_INTENSITY, KEY_RADIUS):
            lit += 1

    unreal.log("HERO shell={} machinery={} pods={} ({} open) lights={}".format(
        bool(shell), bool(machinery), len(pods), opened, lit))

    level.save_current_level()
    unreal.log("HERO saved {}".format(MAP_PACKAGE))


build()
