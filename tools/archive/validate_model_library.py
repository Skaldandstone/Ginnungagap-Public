"""Fail the commandlet when critical generated model-library assets are missing or invalid."""

import unreal

REQUIRED = [
    "/Game/Assets/Models/Equipment/SM_Tool_BioScanner",
    "/Game/Assets/Models/Pickups/SM_Pickup_OxygenCanister",
    "/Game/Assets/Models/Drones/SM_Drone_Retrieval",
    "/Game/Assets/Models/ShipSystems/SM_System_CryoPod",
    "/Game/Assets/Models/Bloom/SM_Bloom_Puppeteer_Proxy",
    "/Game/Assets/Models/Bloom/RigPrep/SM_Bloom_Puppeteer_Torso_Rig",
    "/Game/Characters/Player/Equipment/Meshes/SM_Equip_HelmetLamp",
    "/Game/Characters/Player/Equipment/Meshes/SM_Equip_OxygenFilter",
    "/Game/Assets/Ships/Exterior/Meshes/SM_Ship_SmallUtilityEscort",
    "/Game/Assets/Ships/Exterior/Meshes/SM_Ship_MediumMilitaryCorvette",
    "/Game/Assets/Ships/Exterior/Meshes/SM_Ship_LargeExpeditionCarrier",
    "/Game/Assets/Maps/ModelLibrary/L_GameplayModelLibrary",
    "/Game/Assets/Maps/ShipExterior/L_FleetScaleComparison",
    "/Game/Assets/Models/Bloom/Expansion/SM_Bloom_CeilingStalker_Proxy",
    "/Game/Assets/Models/RoomMachinery/SM_Engineering_ReactorCoil",
    "/Game/Assets/Models/GameplayItems/SM_Mission_NavigationDataCore",
    "/Game/Assets/Models/DamageControl/SM_Damage_HullBreach_Rim",
    "/Game/Assets/Ships/Exterior/Details/SM_Exterior_RCSCluster",
    "/Game/Assets/SpaceSystems/Meshes/SM_Orbital_NavigationBeacon",
    "/Game/Assets/Maps/ModelLibrary/L_CompleteAssetCatalog",
    "/Game/Assets/Maps/Bloom/L_Bloom_FabRealityScan_Prototypes",
    "/Game/Assets/Maps/Bloom/L_Bloom_Progression_Showcase",
    "/Game/Assets/Maps/Bloom/L_Bloom_CombatPose_Showcase",
]

REQUIRED_CLASSES = [
    "/Script/Ginnungagap.ProgressiveBloomEnemy",
    "/Script/Ginnungagap.BloomReanimatedCrewEnemy",
    "/Script/Ginnungagap.BloomMechanizedEnemy",
]

REQUIRED_BLOOM_FAB_ANIMATIONS = [
    "/Game/DeadBodies_Poses_nikoff/Animations/AS_DeadBody_Pose_Lie_04",
    "/Game/DeadBodies_Poses_nikoff/Animations/AS_DeadBody_Pose_Lie_11",
    "/Game/DeadBodies_Poses_nikoff/Animations/AS_DeadBody_Pose_Lie_17",
]

BLOOM_FAB_CORPSE_MESH = (
    "/Game/DeadBodies_Poses_nikoff/Demo/Mannequins/Meshes/SKM_Manny_Simple"
)


def main():
    missing = [path for path in REQUIRED if not unreal.EditorAssetLibrary.does_asset_exist(path)]
    missing.extend(path for path in REQUIRED_CLASSES if unreal.load_class(None, path) is None)
    missing.extend(
        path
        for path in [BLOOM_FAB_CORPSE_MESH, *REQUIRED_BLOOM_FAB_ANIMATIONS]
        if not unreal.EditorAssetLibrary.does_asset_exist(path)
    )
    invalid = []

    corpse_mesh = unreal.EditorAssetLibrary.load_asset(BLOOM_FAB_CORPSE_MESH)
    corpse_skeleton = corpse_mesh.get_editor_property("skeleton") if corpse_mesh else None
    if corpse_mesh and not isinstance(corpse_mesh, unreal.SkeletalMesh):
        invalid.append(BLOOM_FAB_CORPSE_MESH + " is not a SkeletalMesh")
    for path in REQUIRED_BLOOM_FAB_ANIMATIONS:
        animation = unreal.EditorAssetLibrary.load_asset(path)
        if animation and not isinstance(animation, unreal.AnimSequence):
            invalid.append(path + " is not an AnimSequence")
        elif animation and animation.get_editor_property("skeleton") != corpse_skeleton:
            invalid.append(path + " does not use the Bloom Fab corpse mesh skeleton")
    mesh_roots = [
        "/Game/Assets/Models", "/Game/Assets/Ships/Exterior/Meshes",
        "/Game/Assets/Ships/Exterior/Details", "/Game/Assets/SpaceSystems/Meshes",
        "/Game/Characters/Player/Equipment/Meshes", "/Game/Characters/Player/Suit/Meshes",
    ]
    mesh_count = 0
    for root in mesh_roots:
        for path in unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False):
            asset = unreal.EditorAssetLibrary.load_asset(path)
            if path.rsplit("/", 1)[-1].startswith("SM_"):
                mesh_count += 1
                if not isinstance(asset, unreal.StaticMesh): invalid.append(path + " is not a StaticMesh")
    if mesh_count < 120: invalid.append(f"expected at least 120 generated static meshes, found {mesh_count}")
    if missing or invalid:
        raise RuntimeError("Model validation failed:\n" + "\n".join(missing + invalid))
    unreal.log(
        f"Model validation passed: {mesh_count} static meshes, {len(REQUIRED)} critical references, "
        f"and {len(REQUIRED_BLOOM_FAB_ANIMATIONS)} compatible Bloom Fab animations."
    )


main()
