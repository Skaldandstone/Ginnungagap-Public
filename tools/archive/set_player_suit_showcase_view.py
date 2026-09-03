"""Set the saved player-suit showcase to a neutral front, side, or rear view."""

import os
import unreal


MAP_PATH = "/Game/Characters/Player/Showcase/L_PlayerSuitShowcase"
VIEW_YAWS = {"front": 0.0, "side": 90.0, "rear": 180.0}


def main():
    view = os.environ.get("SUIT_SHOWCASE_VIEW", "front").lower()
    if view not in VIEW_YAWS:
        raise RuntimeError("Unknown suit showcase view: " + view)
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    levels.load_level(MAP_PATH)
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if isinstance(actor, unreal.CoopSurvivalCharacter):
            actor.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=VIEW_YAWS[view]), False)
            for component in actor.get_components_by_class(unreal.CameraComponent):
                component.set_editor_property("auto_activate", False)
                component.set_active(False)
            for component in actor.get_components_by_class(unreal.SkeletalMeshComponent):
                component.set_editor_property("pause_anims", True)
        elif isinstance(actor, unreal.CameraActor):
            actor.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
        elif isinstance(actor, unreal.RectLight):
            actor.light_component.set_editor_property("intensity", 900.0)
            actor.light_component.set_editor_property("light_color", unreal.Color(238, 244, 255, 255))
        elif isinstance(actor, unreal.DirectionalLight):
            actor.light_component.set_editor_property("intensity", 1.0)
            actor.light_component.set_editor_property("light_color", unreal.Color(245, 247, 255, 255))
    levels.save_current_level()
    unreal.log("Player suit showcase view set to " + view)


main()
