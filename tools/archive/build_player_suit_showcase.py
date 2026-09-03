"""Build an in-engine studio map for rendering the player suit Blueprints."""

import re
import unreal


MAP_PATH = "/Game/Characters/Player/Showcase/L_PlayerSuitShowcase"
BP_PATH = "/Game/Characters/Player/Showcase"


def set_mesh(actor, path, scale):
    mesh = unreal.EditorAssetLibrary.load_asset(path)
    actor.static_mesh_component.set_static_mesh(mesh)
    studio_material = unreal.EditorAssetLibrary.load_asset(
        "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_TopDark")
    actor.static_mesh_component.set_material(0, studio_material)
    actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    actor.set_actor_scale3d(unreal.Vector(*scale))


def main():
    match = re.search(r"-SuitYaw=(-?\d+(?:\.\d+)?)", unreal.SystemLibrary.get_command_line())
    suit_yaw = float(match.group(1)) if match else 0.0
    solo_match = re.search(r"-SoloRole=([A-Za-z]+)", unreal.SystemLibrary.get_command_line())
    solo_role = solo_match.group(1).lower() if solo_match else None
    level_lib = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        level_lib.load_level(MAP_PATH)
        role_positions = {"crew": -225.0, "engineering": -75.0, "medical": 75.0, "security": 225.0}
        material = unreal.EditorAssetLibrary.load_asset(
            "/Game/LevelPrototyping/Materials/MI_PrototypeGrid_TopDark")
        for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
            if isinstance(actor, unreal.StaticMeshActor):
                actor.static_mesh_component.set_material(0, material)
            elif isinstance(actor, unreal.CameraActor):
                actor.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=180), False)
                actor.set_actor_location(unreal.Vector(850, 0, 145), False, False)
                actor.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
            elif isinstance(actor, unreal.RectLight):
                actor.light_component.set_editor_property("intensity", 900.0)
                actor.light_component.set_editor_property("light_color", unreal.Color(238, 244, 255, 255))
            elif isinstance(actor, unreal.DirectionalLight):
                actor.light_component.set_editor_property("intensity", 1.0)
                actor.light_component.set_editor_property("light_color", unreal.Color(245, 247, 255, 255))
            elif isinstance(actor, unreal.CoopSurvivalCharacter):
                actor.set_actor_rotation(unreal.Rotator(roll=0, pitch=0, yaw=suit_yaw), False)
                for component in actor.get_components_by_class(unreal.CameraComponent):
                    component.set_editor_property("auto_activate", False)
                    component.set_active(False)
                for component in actor.get_components_by_class(unreal.SkeletalMeshComponent):
                    component.set_editor_property("pause_anims", True)
                label = actor.get_actor_label().lower()
                selected = not solo_role or solo_role in label
                actor.set_actor_hidden_in_game(not selected)
                actor.set_editor_property("auto_possess_player", unreal.AutoReceiveInput.DISABLED)
                actor.set_editor_property("auto_possess_ai", unreal.AutoPossessAI.DISABLED)
                if solo_role and selected:
                    actor.set_actor_location(unreal.Vector(0, 0, 96), False, False)
                elif not solo_role:
                    for role_name, y in role_positions.items():
                        if role_name in label:
                            actor.set_actor_location(unreal.Vector(0, y, 96), False, False)
                            break
        level_lib.save_current_level()
        return
    level_lib.new_level(MAP_PATH)

    actor_sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    roles = [
        ("BP_Player_Suit_Crew", -225.0),
        ("BP_Player_Suit_Engineering", -75.0),
        ("BP_Player_Suit_Medical", 75.0),
        ("BP_Player_Suit_Security", 225.0),
    ]
    role_colors = {
        "Crew": unreal.Color(r=90, g=150, b=255, a=255),
        "Engineering": unreal.Color(r=255, g=145, b=45, a=255),
        "Medical": unreal.Color(r=100, g=235, b=190, a=255),
        "Security": unreal.Color(r=245, g=85, b=75, a=255),
    }
    for asset_name, y in roles:
        bp = unreal.EditorAssetLibrary.load_asset("/Game/Characters/Player/Blueprints/" + asset_name)
        actor = actor_sub.spawn_actor_from_class(bp.generated_class(), unreal.Vector(0, y, 96), unreal.Rotator(0, 0, 0))
        role_name = asset_name.replace("BP_Player_Suit_", "")
        actor.set_actor_label(role_name)
        try:
            label = actor_sub.spawn_actor_from_class(
                unreal.TextRenderActor, unreal.Vector(25, y, 190), unreal.Rotator(0, 180, 0))
            label.set_actor_label(role_name + " Label")
            label.text_render.set_text(role_name.upper())
            label.text_render.set_editor_property("world_size", 16.0)
            label.text_render.set_editor_property("horizontal_alignment", unreal.HorizontalTextAligment.EHTA_CENTER)
            label.text_render.set_editor_property("text_render_color", role_colors[role_name])
        except Exception as error:
            unreal.log_warning("Unable to create showcase role label: " + str(error))

    floor = actor_sub.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator())
    floor.set_actor_label("Studio Floor")
    set_mesh(floor, "/Engine/BasicShapes/Plane.Plane", (12, 12, 12))

    backdrop = actor_sub.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-115, 0, 300), unreal.Rotator())
    backdrop.set_actor_label("Studio Backdrop")
    set_mesh(backdrop, "/Engine/BasicShapes/Cube.Cube", (0.15, 13, 6))

    key = actor_sub.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(200, -300, 500), unreal.Rotator(-38, -25, 0))
    key.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    key.light_component.set_editor_property("intensity", 0.85)
    key.light_component.set_editor_property("light_color", unreal.Color(215, 225, 238, 255))

    sky = actor_sub.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 300), unreal.Rotator())
    sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property("intensity", 0.16)
    sky.light_component.set_editor_property("source_type", unreal.SkyLightSourceType.SLS_SPECIFIED_CUBEMAP)

    for y, color in ((-320, unreal.Color(230, 240, 255, 255)), (320, unreal.Color(255, 242, 228, 255))):
        light = actor_sub.spawn_actor_from_class(unreal.RectLight, unreal.Vector(260, y, 260), unreal.Rotator(0, 180, 0))
        light.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        light.light_component.set_editor_property("intensity", 85.0)
        light.light_component.set_editor_property("light_color", color)
        light.light_component.set_editor_property("source_width", 180.0)
        light.light_component.set_editor_property("source_height", 280.0)

    camera = actor_sub.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(850, 0, 145), unreal.Rotator(roll=0, pitch=0, yaw=180))
    camera.set_actor_label("Render Camera")
    camera.camera_component.set_editor_property("field_of_view", 43.0)
    camera.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)

    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.GameModeBase)
    gm_path = BP_PATH + "/BP_SuitShowcaseGameMode"
    if unreal.EditorAssetLibrary.does_asset_exist(gm_path):
        unreal.EditorAssetLibrary.delete_asset(gm_path)
    gm = unreal.AssetToolsHelpers.get_asset_tools().create_asset("BP_SuitShowcaseGameMode", BP_PATH, unreal.Blueprint, factory)
    cdo = unreal.get_default_object(gm.generated_class())
    cdo.set_editor_property("default_pawn_class", None)
    unreal.EditorAssetLibrary.save_loaded_asset(gm)

    world = unreal.EditorLevelLibrary.get_editor_world()
    world.get_world_settings().set_editor_property("default_game_mode", gm.generated_class())
    level_lib.save_current_level()
    unreal.log("Player suit showcase map built: " + MAP_PATH)


main()
