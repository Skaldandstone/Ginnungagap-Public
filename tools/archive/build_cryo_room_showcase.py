"""Create the in-engine CRYO-01 art and interaction review map."""
import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_CryoRoom_Review"
SHELL = "/Game/Assets/ShipRooms/Cryo/SM_Room_CryoShell"
MACHINERY = "/Game/Assets/ShipRooms/Cryo/SM_Room_CryoMachinery"


def static_mesh_actor(actors, label, asset_path):
    mesh = unreal.load_asset(asset_path)
    if not mesh:
        raise RuntimeError("Missing CRYO-01 mesh: " + asset_path)
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator(0, 90, 0))
    actor.set_actor_label(label)
    actor.tags = [unreal.Name("CRYO-01"), unreal.Name("ReviewMap")]
    actor.static_mesh_component.set_static_mesh(mesh)
    return actor


def rect_light(actors, label, location, rotation, color, intensity, width, height):
    actor = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(*location), unreal.Rotator(*rotation))
    actor.set_actor_label(label)
    component = actor.get_component_by_class(unreal.RectLightComponent)
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("light_color", unreal.Color(*color))
    component.set_editor_property("source_width", width)
    component.set_editor_property("source_height", height)
    component.set_editor_property("attenuation_radius", 650.0)
    return actor


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP):
        unreal.EditorLevelLibrary.load_level(MAP)
        existing = actors.get_all_level_actors()
        if existing:
            actors.destroy_actors(existing)
    elif not levels.new_level(MAP):
        raise RuntimeError("Could not create CRYO-01 review map")
    static_mesh_actor(actors, "CRYO01_Art_Shell", SHELL)
    static_mesh_actor(actors, "CRYO01_Art_Machinery", MACHINERY)

    player = actors.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(210, -470, 110), unreal.Rotator(0, 90, 0))
    player.set_actor_label("CRYO01_PlayerStart")

    pod_class = unreal.load_class(None, "/Script/Ginnungagap.CryoPodSystem")
    if not pod_class:
        raise RuntimeError("CryoPodSystem class is unavailable; compile GinnungagapEditor")
    for index, local_x in enumerate((-384.3, -136.6, 112.2, 359.9), 1):
        pod = actors.spawn_actor_from_class(pod_class, unreal.Vector(156.2, local_x, 0), unreal.Rotator(0, 90, 0))
        pod.set_actor_label(f"CRYO01_GameplayPod_{index:02d}")
        pod.set_editor_property("system_name", f"Cryopod {index:02d}")
        pod.tags = [unreal.Name("CRYO-01"), unreal.Name(f"CryoPod.{index:02d}"),
                    unreal.Name("Damaged" if index >= 3 else "Nominal")]

    for index, y in enumerate((-315, -112, 92, 295), 1):
        rect_light(actors, f"CRYO01_ThawLight_{index:02d}", (120, y, 155), (0, -90, 0),
                   (55, 165, 255), 850.0 if index < 3 else 430.0, 100.0, 35.0)
    for index, y in enumerate((-330, 0, 310), 1):
        rect_light(actors, f"CRYO01_EmergencyLight_{index:02d}", (-170, y, 255), (0, 90, 0),
                   (255, 55, 12), 170.0, 38.0, 16.0)

    sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 150), unreal.Rotator())
    sky.set_actor_label("CRYO01_AmbientFill")
    sky_component = sky.get_component_by_class(unreal.SkyLightComponent)
    sky_component.set_editor_property("intensity", 0.08)

    fog = actors.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, 0), unreal.Rotator())
    fog.set_actor_label("CRYO01_CondensationHaze")
    fog_component = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    fog_component.set_editor_property("fog_density", 0.012)
    fog_component.set_editor_property("fog_height_falloff", 0.2)

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    game_mode = unreal.load_class(None, "/Script/Ginnungagap.GinnungagapGameMode")
    if game_mode:
        world.get_world_settings().set_editor_property("default_game_mode", game_mode)
    levels.save_current_level()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log("CRYO-01 review map ready: " + MAP)


main()
