"""Set a deterministic animation pose for suit clipping inspection."""

import os
import unreal


MAP_PATH = "/Game/Characters/Player/Showcase/L_PlayerSuitShowcase"
POSES = {
    "combat": ("/Game/Characters/Mannequins/Anims/Rifle/MF_Rifle_Idle_ADS", 0.55),
    "attack": ("/Game/Characters/Mannequins/Anims/Unarmed/Attack/MM_Attack_02", 0.42),
    "run": ("/Game/Characters/Mannequins/Anims/Rifle/Jog/MF_Rifle_Jog_Fwd", 0.36),
}


pose_name = os.environ.get("SUIT_SHOWCASE_POSE", "combat").lower()
asset_path, normalized_time = POSES.get(pose_name, POSES["combat"])
animation = unreal.EditorAssetLibrary.load_asset(asset_path)
if not animation:
    raise RuntimeError("Unable to load suit audit animation: " + asset_path)

level_lib = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
level_lib.load_level(MAP_PATH)
for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
    if not isinstance(actor, unreal.CoopSurvivalCharacter):
        continue
    for component in actor.get_components_by_class(unreal.SkeletalMeshComponent):
        component.set_animation_mode(unreal.AnimationMode.ANIMATION_SINGLE_NODE)
        component.set_animation(animation)
        component.set_position(animation.sequence_length * normalized_time, False)
        component.set_editor_property("pause_anims", True)

level_lib.save_current_level()
unreal.log("Player suit showcase pose set to " + pose_name)
