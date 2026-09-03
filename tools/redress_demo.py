"""Loads the demo map and runs both dressing passes in one editor session."""
import os
import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
HERE = os.path.dirname(os.path.abspath(__file__))
PASSES = ("dress_demo_corridors.py", "dress_demo_slice.py")

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
for name in PASSES:
    if not levels.load_level(MAP):
        unreal.log_error("REDRESS could not load {}".format(MAP))
        break
    path = os.path.join(HERE, name)
    unreal.log("REDRESS running {}".format(name))
    with open(path, "r", encoding="utf-8") as handle:
        code = compile(handle.read(), path, "exec")
    exec(code, {"__name__": "__main__", "__file__": path})
    unreal.log("REDRESS finished {}".format(name))

# The passes change what collides, which leaves the level's saved navmesh stale. A headless
# session cannot rebuild it -- Build() produces nothing outside an interactive editor or a game
# world -- so the demo director rebuilds the navmesh from live geometry at level start instead.
