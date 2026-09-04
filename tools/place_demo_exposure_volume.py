"""Places (or updates) the demo map's global post-process volume: a fixed exposure bias.

Every recorded frame of L_QuickDemo_FourDeck came out blown to sepia-white: the rooms' utility
lights are bright and auto exposure chases the dark corridors between them. One unbound volume
with a negative exposure bias brings the walls back; the value is chosen by looking at the
look-test and walk captures, not by theory.

    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/place_demo_exposure_volume.py -NullRHI
"""
import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
LABEL = "QuickDemo4D_Exposure"
BIAS = -0.75
MIN_EV, MAX_EV = 5.0, 11.0

les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
assert les.load_level(MAP), "map failed to load"
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
volume = None
for a in actors.get_all_level_actors():
    if a.get_actor_label() == LABEL:
        volume = a
        break
if not volume:
    volume = actors.spawn_actor_from_class(unreal.PostProcessVolume, unreal.Vector(0, 0, 0))
    volume.set_actor_label(LABEL)
volume.set_editor_property("unbound", True)
volume.set_editor_property("priority", 10.0)
settings = volume.get_editor_property("settings")
settings.set_editor_property("override_auto_exposure_bias", True)
settings.set_editor_property("auto_exposure_bias", BIAS)
settings.set_editor_property("override_auto_exposure_min_brightness", True)
settings.set_editor_property("auto_exposure_min_brightness", MIN_EV)
settings.set_editor_property("override_auto_exposure_max_brightness", True)
settings.set_editor_property("auto_exposure_max_brightness", MAX_EV)
volume.set_editor_property("settings", settings)
saved = les.save_current_level()
print(f"EXPOSURE {LABEL} bias={BIAS} ev={MIN_EV}..{MAX_EV} saved={saved}")
