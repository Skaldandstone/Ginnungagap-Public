"""Report role and resolved suit assets for the showcase lineup."""

import unreal


MAP_PATH = "/Game/Characters/Player/Showcase/L_PlayerSuitShowcase"


unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP_PATH)
for role_name in ("Crew", "Engineering", "Medical", "Security"):
    instance = unreal.EditorAssetLibrary.load_asset(
        "/Game/Characters/Player/Suit/Materials/MI_Suit_" + role_name)
    color = unreal.MaterialEditingLibrary.get_material_instance_vector_parameter_value(
        instance, "SuitColor")
    strength = unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(
        instance, "RoleColorStrength")
    unreal.log_warning("SUIT_AUDIT instance=%s color=%s strength=%s" % (
        role_name, color, strength))
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
for actor in actors:
    if not isinstance(actor, unreal.CoopSurvivalCharacter):
        continue
    role = actor.get_editor_property("pressure_suit_role")
    unreal.log_warning("SUIT_AUDIT actor=%s class=%s role=%s" % (
        actor.get_actor_label(), actor.get_class().get_name(), role))
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        if component.get_name() not in ("ChestControlUnit", "ChestPlate"):
            continue
        mesh = component.get_editor_property("static_mesh")
        material = component.get_material(0)
        unreal.log_warning("SUIT_AUDIT part=%s mesh=%s material=%s" % (
            component.get_name(), mesh.get_path_name() if mesh else "None",
            material.get_path_name() if material else "None"))
