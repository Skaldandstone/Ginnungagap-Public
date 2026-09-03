"""Apply the corrected front view and deterministic studio lighting to the V24 review map."""

import unreal


MAP_PATH = "/Game/Characters/PlayerSuits/PrimaryOversuits/V24Review/SpaceMarshal/L_SpaceMarshal_ClassLineup"


def main() -> None:
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    levels.load_level(MAP_PATH)
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if isinstance(actor, unreal.SkeletalMeshActor):
            actor.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=-90), False)
        elif isinstance(actor, (unreal.DirectionalLight, unreal.RectLight)):
            actor.light_component.set_editor_property("cast_shadows", False)
    levels.save_current_level()
    unreal.log("Space Marshal oversuit review set to corrected front view")


main()
