"""Log the critical V24 donor-review material and component bindings."""

import unreal


ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V24Review/SpaceMarshal"
MAP = ROOT + "/L_SpaceMarshal_ClassLineup"


def main() -> None:
    for role in ("Crew", "Engineering", "Medical", "Security"):
        instance = unreal.EditorAssetLibrary.load_asset(f"{ROOT}/Materials/MI_{role}_SM_Suit")
        texture = unreal.MaterialEditingLibrary.get_material_instance_texture_parameter_value(
            instance, "BaseColorTexture"
        )
        unreal.log(f"SPACE_MARSHAL_INSPECT role={role} base={texture.get_path_name() if texture else 'NONE'}")
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP)
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if not isinstance(actor, unreal.SkeletalMeshActor):
            continue
        component = actor.skeletal_mesh_component
        bindings = []
        for index in range(component.get_num_materials()):
            material = component.get_material(index)
            bindings.append(material.get_name() if material else "NONE")
        unreal.log(f"SPACE_MARSHAL_INSPECT actor={actor.get_actor_label()} materials={bindings}")


main()
