"""Report the authored Quick Demo cryo suit-station anchors without changing the map."""

from __future__ import annotations

import json
from pathlib import Path

import unreal


MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
PREFIX = "QuickDemo4D_SuitStation_"
PROJECT = Path(unreal.SystemLibrary.get_project_directory()).resolve()
REPORT = PROJECT / "Saved/Reports/QuickDemoCryoSuitRecessInspection.json"


levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
stations = []
for actor in actors:
    label = actor.get_actor_label()
    if not label.startswith(PREFIX):
        continue
    origin, extent = actor.get_actor_bounds(False)
    mesh_component = actor.get_component_by_class(unreal.StaticMeshComponent)
    mesh = mesh_component.get_editor_property("static_mesh") if mesh_component else None
    stations.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "location": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
        "rotation": [actor.get_actor_rotation().pitch, actor.get_actor_rotation().yaw, actor.get_actor_rotation().roll],
        "scale": [actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z],
        "bounds_origin": [origin.x, origin.y, origin.z],
        "bounds_extent": [extent.x, extent.y, extent.z],
        "mesh": mesh.get_path_name() if mesh else None,
    })

stations.sort(key=lambda item: item["label"])
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({"map": MAP, "station_count": len(stations), "stations": stations}, indent=2), encoding="utf-8")
unreal.log(f"QUICK DEMO CRYO RECESS INSPECTION: {len(stations)} anchors -> {REPORT}")
