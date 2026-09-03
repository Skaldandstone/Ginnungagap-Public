"""Create a single review map containing every generated static-model library."""

import unreal

MAP="/Game/Assets/Maps/ModelLibrary/L_CompleteAssetCatalog"
ROOTS=[
    "/Game/Assets/Models",
    "/Game/Characters/Player/Equipment/Meshes",
    "/Game/Characters/Player/Suit/Meshes",
    "/Game/Assets/Ships/Exterior/Details",
    "/Game/Assets/Ships/Exterior/Meshes",
    "/Game/Assets/SpaceSystems/Meshes",
]


def main():
    meshes=[]
    for root in ROOTS:
        for path in unreal.EditorAssetLibrary.list_assets(root,recursive=True,include_folder=False):
            asset=unreal.EditorAssetLibrary.load_asset(path)
            if isinstance(asset,unreal.StaticMesh): meshes.append((path,asset))
    meshes.sort(key=lambda item:item[0])
    level=unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP): unreal.EditorAssetLibrary.delete_asset(MAP)
    level.new_level(MAP); actors=unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    # Exterior fleet hulls are kept out of the grid; their dedicated scale map is authoritative.
    review=[item for item in meshes if "/SM_Ship_" not in item[0] and not item[0].endswith("SM_Celestial_Star")]
    columns=12; spacing_x=330.0; spacing_y=340.0
    for index,(path,mesh) in enumerate(review):
        x=(index%columns)*spacing_x; y=(index//columns)*spacing_y
        actor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector(x,y,15),unreal.Rotator())
        actor.set_actor_label(path.rsplit("/",1)[-1]); actor.static_mesh_component.set_static_mesh(mesh)
        bounds=mesh.get_bounds().box_extent
        largest=max(bounds.x,bounds.y,bounds.z)
        if largest>2000:
            scale=min(1.0,900.0/largest); actor.set_actor_scale3d(unreal.Vector(scale,scale,scale))
    floor=actors.spawn_actor_from_class(unreal.StaticMeshActor,unreal.Vector((columns-1)*spacing_x*.5,(len(review)//columns)*spacing_y*.5,-10),unreal.Rotator())
    floor.set_actor_label("Complete Catalog Floor"); floor.static_mesh_component.set_static_mesh(unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane.Plane"))
    floor.set_actor_scale3d(unreal.Vector(45,55,1)); floor.static_mesh_component.set_material(0,unreal.EditorAssetLibrary.load_asset("/Game/Assets/Models/Materials/M_Model_ShowcaseFloor"))
    sun=actors.spawn_actor_from_class(unreal.DirectionalLight,unreal.Vector(1800,1800,3000),unreal.Rotator(-40,-35,0)); sun.light_component.set_editor_property("intensity",4.5)
    sky=actors.spawn_actor_from_class(unreal.SkyLight,unreal.Vector(1800,1800,1800),unreal.Rotator()); sky.light_component.set_editor_property("intensity",.75)
    camera=actors.spawn_actor_from_class(unreal.CameraActor,unreal.Vector(7000,2200,5200),unreal.Rotator(-25,180,0)); camera.camera_component.set_editor_property("field_of_view",52.0); camera.set_actor_label("Complete Catalog Camera")
    level.save_current_level(); unreal.log(f"Complete asset catalog ready: {len(review)} staged meshes ({len(meshes)} discovered).")


main()
