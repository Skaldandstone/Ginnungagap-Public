"""Capture one generated RealityScan ship review map for visual QA."""

from __future__ import annotations

import os
from pathlib import Path

import unreal


SHIP = os.environ.get("GINNUNGAGAP_RS_CAPTURE", "SmallUtilityEscort")
VALID_SHIPS = {"SmallUtilityEscort", "MilitaryCorvette", "ExpeditionCarrier"}
if SHIP not in VALID_SHIPS:
    raise RuntimeError(f"Unknown RealityScan review ship: {SHIP}")

MAP = f"/Game/Assets/Maps/ShipExterior/RealityScan/L_{SHIP}_RealityScan"
OUTPUT = (
    Path(unreal.SystemLibrary.get_project_directory())
    / "Saved"
    / "Reports"
    / "RealityScanShipFleet"
    / f"{SHIP}_UnrealReview.png"
)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

unreal.EditorLevelLibrary.load_level(MAP)

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
camera = next(
    (
        actor
        for actor in actors.get_all_level_actors()
        if actor.get_actor_label() == f"RS_{SHIP}_ReviewCamera"
    ),
    None,
)
if camera is None:
    raise RuntimeError(f"Review camera missing in {MAP}")

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "r.ScreenPercentage 100")
unreal.SystemLibrary.execute_console_command(world, "r.Nanite 1")
unreal.AutomationLibrary.finish_loading_before_screenshot()
unreal.EditorLevelLibrary.set_level_viewport_camera_info(
    camera.get_actor_location(), camera.get_actor_rotation()
)
unreal.EditorLevelLibrary.editor_invalidate_viewports()
command = f'HighResShot 1600x900 filename="{str(OUTPUT).replace(chr(92), "/")}"'
unreal.SystemLibrary.execute_console_command(world, command)
unreal.log(f"REALITYSCAN_SHIP_SCREENSHOT_REQUESTED {SHIP} {OUTPUT}")
