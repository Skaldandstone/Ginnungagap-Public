"""Build a focused Unreal Modeling Mode workspace for the reusable cryo pod."""
import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_CryoPod_Modeling_V2"
PARTS = {
    "Base": "/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_Base",
    "Bed": "/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_Bed",
    "Details": "/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_Details",
    "Hinge": "/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_HingeFinal",
    "Restraints": "/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_Restraints",
    "StatusLights": "/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_StatusLights",
    "LidFrame": "/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_LidFrame",
    "LidGlass": "/Game/Assets/ShipRooms/Cryo/GeneratedV3/SM_CryoPod_GS_LidGlass",
}


def mesh_actor(actors, label, asset_path, location, rotation=unreal.Rotator(), scale=unreal.Vector(1, 1, 1)):
    mesh = unreal.load_asset(asset_path)
    if not mesh:
        raise RuntimeError(f"Missing modeling asset: {asset_path}")
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), rotation)
    actor.set_actor_label(label)
    actor.tags = [unreal.Name("CRYO-01"), unreal.Name("ModelingWorkspace")]
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.set_actor_scale3d(scale)
    return actor


def main():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP):
        unreal.EditorLevelLibrary.load_level(MAP)
        actors.destroy_actors(actors.get_all_level_actors())
    elif not levels.new_level(MAP):
        raise RuntimeError("Could not create cryo pod Modeling Mode workspace")

    pod_class = unreal.load_class(None, "/Script/Ginnungagap.CryoPodSystem")
    if not pod_class:
        raise RuntimeError("CryoPodSystem is unavailable; compile GinnungagapEditor first")
    master = actors.spawn_actor_from_class(pod_class, unreal.Vector(0, 0, 0), unreal.Rotator())
    master.set_actor_label("CRYO01_MasterPod_Functional")
    master.tags = [unreal.Name("CRYO-01"), unreal.Name("ReusableMaster"), unreal.Name("OpenCloseReview")]

    # Exploded copies make each generated asset immediately selectable in Modeling Mode (Shift+5).
    mesh_actor(actors, "CRYO01_Edit_Base", PARTS["Base"], (330, -160, 0))
    mesh_actor(actors, "CRYO01_Edit_Bed", PARTS["Bed"], (330, 190, 0))
    mesh_actor(actors, "CRYO01_Edit_Details", PARTS["Details"], (330, 520, 0))
    mesh_actor(actors, "CRYO01_Edit_Hinge", PARTS["Hinge"], (610, -430, 0))
    mesh_actor(actors, "CRYO01_Edit_Restraints", PARTS["Restraints"], (610, 450, 0))
    mesh_actor(actors, "CRYO01_Edit_StatusLights", PARTS["StatusLights"], (610, 560, 0))
    mesh_actor(actors, "CRYO01_Edit_LidFrame", PARTS["LidFrame"], (610, -150, 0))
    mesh_actor(actors, "CRYO01_Edit_LidGlass", PARTS["LidGlass"], (610, 150, 0))

    cube = "/Engine/BasicShapes/Cube.Cube"
    cylinder = "/Engine/BasicShapes/Cylinder.Cylinder"
    mesh_actor(actors, "CRYO01_NeutralFloor", cube, (250, 0, -7), scale=unreal.Vector(10, 8, .1))
    # 180 cm reference volume prevents accidental return to undersized pod proportions.
    mesh_actor(actors, "CRYO01_HumanScale_180cm", cylinder, (-270, 0, 90), scale=unreal.Vector(.55, .55, 1.8))

    key = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(-80, -180, 360), unreal.Rotator(-55, 25, 0))
    key.set_actor_label("CRYO01_Modeling_Key")
    key_comp = key.get_component_by_class(unreal.RectLightComponent)
    key_comp.set_editor_property("intensity", 2600.0)
    key_comp.set_editor_property("source_width", 250.0)
    key_comp.set_editor_property("source_height", 180.0)

    fill = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(500, 300, 260), unreal.Rotator(-40, -130, 0))
    fill.set_actor_label("CRYO01_Modeling_Fill")
    fill_comp = fill.get_component_by_class(unreal.RectLightComponent)
    fill_comp.set_editor_property("intensity", 1100.0)
    fill_comp.set_editor_property("light_color", unreal.Color(105, 175, 255))

    levels.save_current_level()
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log("CRYO-MODELING PASS: focused reusable-pod workspace ready at " + MAP)


main()
