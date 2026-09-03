"""Report per-actor bounds in the Fab hull sculpt review maps."""
import json
from pathlib import Path

import unreal


project = Path(unreal.SystemLibrary.get_project_directory())
report = project / "Saved/Reports/UnrealShipFabHullActorBounds.json"
maps = (
    "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_FabHullSculpt",
    "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_FabHullSculpt",
)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
payload = []
for map_path in maps:
    if not levels.load_level(map_path):
        raise RuntimeError(f"Could not load {map_path}")
    rows = []
    for actor in actors.get_all_level_actors():
        if not actor.get_actor_label().startswith("FAB_HULL_"):
            continue
        origin, extent = actor.get_actor_bounds(False)
        rows.append({
            "label": actor.get_actor_label(),
            "origin_cm": [origin.x, origin.y, origin.z],
            "size_cm": [extent.x * 2, extent.y * 2, extent.z * 2],
            "min_cm": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
            "max_cm": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
        })
    rows.sort(key=lambda row: row["label"])
    payload.append({"map": map_path, "actors": rows})
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text(json.dumps({"version": 1, "maps": payload}, indent=2), encoding="utf-8")
unreal.log(f"FAB HULL ACTOR BOUNDS -> {report}")
