"""Apply category materials and stage the generated model library for review."""

import unreal

MODEL_ROOT = "/Game/Assets/Models"
MATERIAL_ROOT = MODEL_ROOT + "/Materials"
MAP_PATH = "/Game/Assets/Maps/ModelLibrary/L_GameplayModelLibrary"


def material(name, color, roughness, metallic=0.0, emissive=0.0):
    path = MATERIAL_ROOT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIAL_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    base = unreal.MaterialEditingLibrary.create_material_expression(asset, unreal.MaterialExpressionVectorParameter, -360, -50)
    base.set_editor_property("parameter_name", "BaseColor")
    base.set_editor_property("default_value", unreal.LinearColor(*color, 1.0))
    rough = unreal.MaterialEditingLibrary.create_material_expression(asset, unreal.MaterialExpressionScalarParameter, -360, 100)
    rough.set_editor_property("parameter_name", "Roughness"); rough.set_editor_property("default_value", roughness)
    metal = unreal.MaterialEditingLibrary.create_material_expression(asset, unreal.MaterialExpressionScalarParameter, -360, 190)
    metal.set_editor_property("parameter_name", "Metallic"); metal.set_editor_property("default_value", metallic)
    unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emissive:
        multiply = unreal.MaterialEditingLibrary.create_material_expression(asset, unreal.MaterialExpressionMultiply, -100, -120)
        strength = unreal.MaterialEditingLibrary.create_material_expression(asset, unreal.MaterialExpressionConstant, -250, -170)
        strength.set_editor_property("r", emissive)
        unreal.MaterialEditingLibrary.connect_material_expressions(base, "", multiply, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(strength, "", multiply, "B")
        unreal.MaterialEditingLibrary.connect_material_property(multiply, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(asset)
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def main():
    materials = {
        "Equipment": material("M_Model_Equipment_UtilityOrange", (.31, .075, .018), .48, .38),
        "Pickups": material("M_Model_Pickup_SafetyYellow", (.42, .25, .025), .58, .25),
        "Drones": material("M_Model_Drone_ServiceBlue", (.035, .11, .17), .42, .62),
        "ShipSystems": material("M_Model_System_OffWhite", (.30, .32, .31), .63, .25),
        "Environment": material("M_Model_Environment_Gunmetal", (.035, .045, .05), .54, .75),
        "Bloom": material("M_Model_Bloom_Amethyst", (.16, .018, .22), .32, .08, 1.8),
    }
    grouped = {category: [] for category in materials}
    for path in unreal.EditorAssetLibrary.list_assets(MODEL_ROOT, recursive=True, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if not isinstance(asset, unreal.StaticMesh):
            continue
        category = path.split("/")[-2]
        if category in materials:
            asset.set_material(0, materials[category]); unreal.EditorAssetLibrary.save_loaded_asset(asset)
            grouped[category].append(asset)

    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        unreal.EditorAssetLibrary.delete_asset(MAP_PATH)
    level.new_level(MAP_PATH)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for row, category in enumerate(materials):
        for column, mesh in enumerate(sorted(grouped[category], key=lambda value: value.get_name())):
            actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(column*300, row*360, 10), unreal.Rotator())
            actor.set_actor_label(mesh.get_name()); actor.static_mesh_component.set_static_mesh(mesh)
            actor.static_mesh_component.set_material(0, materials[category])

    floor_mat = material("M_Model_ShowcaseFloor", (.018, .022, .026), .78, .12)
    floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(700, 900, -5), unreal.Rotator())
    floor.set_actor_label("Model Library Floor")
    floor.static_mesh_component.set_static_mesh(unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane.Plane"))
    floor.static_mesh_component.set_material(0, floor_mat); floor.set_actor_scale3d(unreal.Vector(22, 26, 1))
    key = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(700, 900, 900), unreal.Rotator(-42, -32, 0))
    key.light_component.set_editor_property("intensity", 4.0)
    key.light_component.set_editor_property("light_color", unreal.Color(220, 232, 255, 255))
    sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(700, 900, 500), unreal.Rotator())
    sky.light_component.set_editor_property("intensity", .65)
    for y, color in ((-160, unreal.Color(65,125,255,255)), (2200, unreal.Color(255,95,42,255))):
        light = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(750, y, 500), unreal.Rotator())
        light.light_component.set_editor_property("intensity", 4200.0)
        light.light_component.set_editor_property("light_color", color)
        light.light_component.set_editor_property("source_width", 500.0)
        light.light_component.set_editor_property("source_height", 500.0)
    camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(3100, 900, 1100), unreal.Rotator(-14, 180, 0))
    camera.set_actor_label("Model Library Camera"); camera.camera_component.set_editor_property("field_of_view", 48.0)
    level.save_current_level()
    unreal.log("Gameplay model showcase ready: 24 meshes, 7 materials.")


main()
