import unreal


MAP_PATH = "/Game/UI/MainMenu"


def main() -> None:
    level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level_subsystem.new_level(MAP_PATH):
        raise RuntimeError(f"Could not create or open {MAP_PATH}")

    editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    world = editor_subsystem.get_editor_world()
    world_settings = world.get_world_settings()
    menu_mode = unreal.load_class(None, "/Script/Ginnungagap.MainMenuGameMode")
    if not menu_mode:
        raise RuntimeError("MainMenuGameMode class is unavailable; build the C++ module first")

    world_settings.set_editor_property("default_game_mode", menu_mode)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log(f"Created {MAP_PATH} with MainMenuGameMode")


main()
