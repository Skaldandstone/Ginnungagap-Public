"""Seed the four I08 primary oversuits into the Quick Demo cryo-bay recesses.

The existing QuickDemoSuitStation actors remain the authoritative gameplay
interactions.  This script adds a collision-free visible suit assembly to each
locker, assigns its class role to the station, and is safe to rerun.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
PREFIX = "QuickDemo4D_"
SEED_TAG = unreal.Name("QuickDemoSeededOversuit")
PROJECT = Path(unreal.SystemLibrary.get_project_directory()).resolve()
REPORT = PROJECT / "Saved/Reports/QuickDemoCryoOversuitSeeding.json"

ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt"
I04 = ROOT + "/Working/Iteration_04_FunctionalDetail"
I06 = ROOT + "/Working/Iteration_06_UncorruptedProductionShell"
I07_MATERIALS = ROOT + "/Working/Iteration_07_ConceptAlignedRoleLineup/Materials"
I08 = ROOT + "/Working/Iteration_08_ConceptSpecificModules"
DONOR = I06 + "/Source/SKM_V25_I06_SpaceMarshalMale"

ROLE_BY_STATION = (
    ("Crew", "CREW"),
    ("Engineering", "ENGINEERING"),
    ("Medical", "MEDICAL"),
    ("Security", "SECURITY"),
)

SHARED = (
    (I08, "SM_V25_I08_PressureDome", "visor", 0.0),
    (I08, "SM_V25_I08_IntegratedCollar", "hard", 0.0),
    (I08, "SM_V25_I08_HelmetFrame", "hard", 0.0),
    (I08, "SM_V25_I08_HarnessWebbing", "trim", 0.0),
    (I08, "SM_V25_I08_ChestComputerFrame", "hard", 0.0),
    (I08, "SM_V25_I08_ChestComputerScreen", "screen", 0.0),
    (I08, "SM_V25_I08_KneeShells", "hard", 0.0),
    (I04, "SM_V25_I04_LifeSupportPack", "hard", 15.0),
    (I04, "SM_V25_I04_LifeSupportDetail", "trim", 15.0),
)


def enum_value(enum_type, requested):
    value = getattr(enum_type, requested.upper(), None)
    if value is None:
        raise RuntimeError(f"Could not resolve {enum_type.__name__}.{requested}")
    return value


def load_material(role, kind):
    names = {
        "fabric": f"M_V25_I07_{role}_Fabric",
        "hard": f"M_V25_I07_{role}_Hard",
        "accent": f"M_V25_I07_{role}_Accent",
        "trim": f"M_V25_I07_{role}_Trim",
        "screen": f"M_V25_I07_{role}_Screen",
        "visor": "M_V25_I07_ClearPressureDome",
        "hidden": "M_V25_I07_HiddenDonorSection",
    }
    material = unreal.EditorAssetLibrary.load_asset(f"{I07_MATERIALS}/{names[kind]}")
    if not isinstance(material, unreal.MaterialInterface):
        raise RuntimeError(f"Missing cryo display material {role}/{kind}")
    return material


def display_tags(role):
    return [SEED_TAG, unreal.Name("CryoSuitRecess"), unreal.Name(f"PressureSuitRole_{role}")]


def spawn_static(actors, role, base, asset_folder, asset_name, material, z_offset):
    mesh = unreal.EditorAssetLibrary.load_asset(f"{asset_folder}/{asset_name}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing cryo display module {asset_folder}/{asset_name}")
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(base.x, base.y, base.z + z_offset),
        unreal.Rotator(yaw=180.0),
    )
    actor.set_actor_label(f"{PREFIX}Oversuit_{role}_{asset_name}")
    actor.set_actor_scale3d(unreal.Vector(0.90, 0.90, 0.90))
    actor.set_actor_enable_collision(False)
    actor.set_editor_property("tags", display_tags(role))
    component = actor.static_mesh_component
    component.set_static_mesh(mesh)
    component.set_material(0, material)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    return actor


levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for existing in actors.get_all_level_actors():
    if SEED_TAG in list(existing.get_editor_property("tags")) or existing.get_actor_label().startswith(PREFIX + "Oversuit_"):
        actors.destroy_actor(existing)

stations = sorted(
    [actor for actor in actors.get_all_level_actors()
     if actor.get_actor_label().startswith(PREFIX + "SuitStation_")],
    key=lambda actor: actor.get_actor_label(),
)
if len(stations) != 4:
    raise RuntimeError(f"Expected four Quick Demo cryo suit stations, found {len(stations)}")

donor = unreal.EditorAssetLibrary.load_asset(DONOR)
if not isinstance(donor, unreal.SkeletalMesh):
    raise RuntimeError(f"Missing I08 pressure-garment donor {DONOR}")
slots = list(donor.get_editor_property("materials"))
original_materials = [slot.get_editor_property("material_interface") for slot in slots]
seeded = []

for station, (role, enum_name) in zip(stations, ROLE_BY_STATION):
    station.set_editor_property("suit_role", enum_value(unreal.PressureSuitRole, enum_name))
    activity = station.get_editor_property("activity")
    activity.set_editor_property("display_name", f"Don {role} pressure suit")
    station.set_editor_property("activity", activity)
    station_tags = list(station.get_editor_property("tags"))
    role_tag = unreal.Name(f"PressureSuitRole_{role}")
    if role_tag not in station_tags:
        station_tags.append(role_tag)
        station.set_editor_property("tags", station_tags)

    anchor = station.get_actor_location()
    # The locker opens toward +Y in the authored cryo-room view.  Pulling the
    # suit 35 cm forward seats its pack inside the recess while keeping the
    # chest computer, helmet rim, and interaction station readable.
    base = unreal.Vector(anchor.x, anchor.y + 35.0, anchor.z + 3.0)
    materials = {kind: load_material(role, kind) for kind in (
        "fabric", "hard", "accent", "trim", "screen", "visor", "hidden"
    )}

    suit = actors.spawn_actor_from_class(
        unreal.SkeletalMeshActor, base, unreal.Rotator(yaw=0.0)
    )
    suit.set_actor_label(f"{PREFIX}Oversuit_{role}_PressureGarment")
    suit.set_actor_scale3d(unreal.Vector(0.90, 0.90, 0.90))
    suit.set_actor_enable_collision(False)
    suit.set_editor_property("tags", display_tags(role))
    component = suit.skeletal_mesh_component
    component.set_skeletal_mesh_asset(donor)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    for index, slot in enumerate(slots):
        name = str(slot.get_editor_property("material_slot_name")).lower()
        material = materials["hidden"]
        if "sm_suit" in name:
            material = materials["fabric"]
        elif "sm_boots" in name or "sm_gloves" in name:
            material = original_materials[index]
        component.set_material(index, material)

    spawned_labels = [suit.get_actor_label()]
    for folder, name, kind, z_offset in SHARED:
        module = spawn_static(actors, role, base, folder, name, materials[kind], z_offset)
        spawned_labels.append(module.get_actor_label())
    module = spawn_static(
        actors, role, base, I08, f"SM_V25_I08_{role}Modules", materials["accent"], 0.0)
    spawned_labels.append(module.get_actor_label())
    seeded.append({
        "station": station.get_actor_label(),
        "role": role,
        "anchor": [anchor.x, anchor.y, anchor.z],
        "display_base": [base.x, base.y, base.z],
        "actors": spawned_labels,
    })

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError(f"Could not save seeded cryo suits to {MAP}")

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "seeded",
    "map": MAP,
    "iteration": "V25.I08",
    "station_count": len(stations),
    "display_actor_count": sum(len(item["actors"]) for item in seeded),
    "roles": seeded,
    "collision": "disabled on all display components",
    "interaction": "QuickDemoSuitStation equips matching role and enables pressure oversuit",
}, indent=2), encoding="utf-8")
unreal.log(f"QUICK DEMO CRYO OVERSUITS SEEDED: {len(seeded)} recesses -> {REPORT}")
