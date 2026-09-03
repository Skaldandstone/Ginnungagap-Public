"""Validate the four class oversuits seeded into the Quick Demo cryo room."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import unreal


MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
PREFIX = "QuickDemo4D_"
SEED_TAG = unreal.Name("QuickDemoSeededOversuit")
ROLES = (
    ("Crew", unreal.PressureSuitRole.CREW),
    ("Engineering", unreal.PressureSuitRole.ENGINEERING),
    ("Medical", unreal.PressureSuitRole.MEDICAL),
    ("Security", unreal.PressureSuitRole.SECURITY),
)
REPORT = (Path(unreal.SystemLibrary.get_project_saved_directory()) /
          "Reports/QuickDemoCryoOversuitValidation.json").resolve()


levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

actors = actors_api.get_all_level_actors()
stations = sorted(
    [actor for actor in actors if actor.get_actor_label().startswith(PREFIX + "SuitStation_")],
    key=lambda actor: actor.get_actor_label(),
)
displays = [
    actor for actor in actors
    if SEED_TAG in list(actor.get_editor_property("tags"))
]

failures = []
if len(stations) != 4:
    failures.append(f"expected 4 suit stations, found {len(stations)}")
if len(displays) != 44:
    failures.append(f"expected 44 display actors, found {len(displays)}")

role_counts = Counter()
collision_violations = []
for actor in displays:
    tags = list(actor.get_editor_property("tags"))
    matched = [role for role, _enum in ROLES if unreal.Name(f"PressureSuitRole_{role}") in tags]
    if len(matched) != 1:
        failures.append(f"{actor.get_actor_label()} has invalid role tags: {[str(tag) for tag in tags]}")
    else:
        role_counts[matched[0]] += 1
    if actor.get_actor_enable_collision():
        collision_violations.append(actor.get_actor_label())

station_results = []
for index, (role, expected_enum) in enumerate(ROLES):
    if index >= len(stations):
        break
    station = stations[index]
    activity = station.get_editor_property("activity")
    actual_enum = station.get_editor_property("suit_role")
    actual_prompt = str(activity.get_editor_property("display_name"))
    expected_prompt = f"Don {role} pressure suit"
    role_tag_present = unreal.Name(f"PressureSuitRole_{role}") in list(
        station.get_editor_property("tags"))
    if actual_enum != expected_enum:
        failures.append(f"{station.get_actor_label()} role is {actual_enum}, expected {expected_enum}")
    if actual_prompt != expected_prompt:
        failures.append(f"{station.get_actor_label()} prompt is {actual_prompt!r}, expected {expected_prompt!r}")
    if not role_tag_present:
        failures.append(f"{station.get_actor_label()} is missing PressureSuitRole_{role}")
    station_results.append({
        "station": station.get_actor_label(),
        "role": role,
        "prompt": actual_prompt,
        "role_tag_present": role_tag_present,
    })

for role, _enum in ROLES:
    if role_counts[role] != 11:
        failures.append(f"{role} display has {role_counts[role]} actors, expected 11")
if collision_violations:
    failures.append("display collision enabled on: " + ", ".join(sorted(set(collision_violations))))

result = {
    "status": "passed" if not failures else "failed",
    "map": MAP,
    "station_count": len(stations),
    "display_actor_count": len(displays),
    "display_actors_per_role": dict(sorted(role_counts.items())),
    "collision_violations": sorted(set(collision_violations)),
    "stations": station_results,
    "failures": failures,
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("Quick Demo cryo oversuit validation failed: " + "; ".join(failures))
unreal.log(f"QUICK DEMO CRYO OVERSUIT VALIDATION PASSED: {REPORT}")
