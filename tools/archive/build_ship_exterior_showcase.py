"""Create exterior materials and a one-percent fleet scale-comparison map."""

import unreal

MESH_ROOT = "/Game/Assets/Ships/Exterior/Meshes"
MAT_ROOT = "/Game/Assets/Ships/Exterior/Materials"
MAP = "/Game/Assets/Maps/ShipExterior/L_FleetScaleComparison"


def make_material(name, color, roughness, metallic, emissive=0.0):
    path = MAT_ROOT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path): return unreal.EditorAssetLibrary.load_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, MAT_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    base = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant3Vector, -250, -30)
    base.set_editor_property("constant", unreal.LinearColor(*color, 1))
    rough = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -250, 90); rough.set_editor_property("r", roughness)
    metal = unreal.MaterialEditingLibrary.create_material_expression(mat, unreal.MaterialExpressionConstant, -250, 170); metal.set_editor_property("r", metallic)
    unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emissive:
        mul=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionMultiply,-60,-80)
        strength=unreal.MaterialEditingLibrary.create_material_expression(mat,unreal.MaterialExpressionConstant,-170,-130); strength.set_editor_property("r",emissive)
        unreal.MaterialEditingLibrary.connect_material_expressions(base,"",mul,"A"); unreal.MaterialEditingLibrary.connect_material_expressions(strength,"",mul,"B")
        unreal.MaterialEditingLibrary.connect_material_property(mul,"",unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    unreal.MaterialEditingLibrary.recompile_material(mat); unreal.EditorAssetLibrary.save_loaded_asset(mat); return mat


def main():
    hull=make_material("M_Exterior_HullCeramic",(.22,.24,.235),.64,.38)
    dark=make_material("M_Exterior_ArmorGraphite",(.025,.032,.038),.46,.78)
    make_material("M_Exterior_Radiator",(.08,.095,.105),.38,.65)
    make_material("M_Exterior_EngineGlow",(.03,.18,.42),.2,.15,14)
    make_material("M_Exterior_UtilityAccent",(.42,.105,.018),.55,.32)
    for path in unreal.EditorAssetLibrary.list_assets(MESH_ROOT,recursive=False,include_folder=False):
        mesh=unreal.EditorAssetLibrary.load_asset(path)
        if isinstance(mesh,unreal.StaticMesh): mesh.set_material(0,hull if "Ship_" in path else dark); unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP): unreal.EditorAssetLibrary.delete_asset(MAP)
    level.new_level(MAP); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    ships=[("SM_Ship_SmallUtilityEscort",-1700), ("SM_Ship_MediumMilitaryCorvette",0), ("SM_Ship_LargeExpeditionCarrier",2500)]
    for name,y in ships:
        actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,y,120),unreal.Rotator())
        actor.set_actor_label(name); actor.static_mesh_component.set_static_mesh(unreal.EditorAssetLibrary.load_asset(MESH_ROOT+"/"+name)); actor.set_actor_scale3d(unreal.Vector(.01,.01,.01))
    floor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(0,800,0),unreal.Rotator())
    floor.static_mesh_component.set_static_mesh(unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane.Plane")); floor.static_mesh_component.set_material(0,dark); floor.set_actor_scale3d(unreal.Vector(90,55,1))
    sun=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(0,0,3000),unreal.Rotator(-35,-30,0)); sun.light_component.set_editor_property("intensity",5.0)
    sky=actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(0,0,2000),unreal.Rotator()); sky.light_component.set_editor_property("intensity",.7)
    cam=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(8000,800,4200),unreal.Rotator(-18,180,0)); cam.camera_component.set_editor_property("field_of_view",50.0)
    level.save_current_level(); unreal.log("Fleet exterior showcase ready: 3 ships, 5 materials.")


main()
