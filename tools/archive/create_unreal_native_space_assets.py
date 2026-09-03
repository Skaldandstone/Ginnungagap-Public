"""Create the editable Unreal-native starter assets for procedural star systems.

Run with UnrealEditor-Cmd using -ExecutePythonScript. The script is idempotent and only creates
missing assets; existing artist-authored assets are preserved.
"""

import unreal


ROOT = "/Game/Assets/SpaceSystems/Native"
GRAPH_PATH = f"{ROOT}/PCG/PCG_SystemAsteroidField"
RADIATION_PATH = f"{ROOT}/Niagara/NS_SystemRadiationDust_Production"
NEBULA_PATH = f"{ROOT}/Niagara/NS_SystemNebulaWisps_Production"
BLUEPRINT_PATH = f"{ROOT}/Blueprints/BP_UnrealNativeStarSystemMap"
STAR_CATALOG_PATH = f"{ROOT}/Data/DT_GinnungagapFictionalStars"
PROOF_LEVEL_PATH = "/Game/Assets/Maps/SpaceSystems/L_Ginnos_UnrealNativeProof"
RADIATION_TEMPLATE = "/Niagara/DefaultAssets/Templates/Systems/DirectionalBurstLightweight"
NEBULA_TEMPLATE = "/Niagara/DefaultAssets/Templates/Systems/RadialBurst"
ASTEROID_MESHES = (
    ("/Game/Assets/SpaceSystems/Meshes/SM_Asteroid_Debris.SM_Asteroid_Debris", 7),
    ("/Game/Assets/SpaceSystems/Meshes/SM_Asteroid_Large_A.SM_Asteroid_Large_A", 2),
    ("/Game/Assets/SpaceSystems/Meshes/SM_Asteroid_Large_B.SM_Asteroid_Large_B", 2),
)
FAB_LANDMARK_MESHES = (
    "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Cargo/SM_cargo_02.SM_cargo_02",
    "/Game/Alien_Biomass/Meshes/rocks/SM_rock_01.SM_rock_01",
    "/Game/Alien_Biomass/Meshes/rocks/SM_rock_02.SM_rock_02",
    "/Game/Alien_Biomass/Meshes/Alien_organism/SM_alien_organism_07.SM_alien_organism_07",
)
FAB_LANDMARK_BLUEPRINTS = (
    "/Game/Alien_Portal/BP/BP_portal.BP_portal_C",
)


def ensure_directory(path):
    if not unreal.EditorAssetLibrary.does_directory_exist(path):
        unreal.EditorAssetLibrary.make_directory(path)


def create_asset_if_missing(asset_path, asset_class, factory):
    existing = unreal.EditorAssetLibrary.load_asset(asset_path)
    if existing:
        return existing
    package_path, asset_name = asset_path.rsplit("/", 1)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name, package_path, asset_class, factory
    )
    if not asset:
        raise RuntimeError(f"Could not create {asset_path}")
    return asset


def duplicate_if_missing(source_path, destination_path):
    existing = unreal.EditorAssetLibrary.load_asset(destination_path)
    if existing:
        return existing
    if not unreal.EditorAssetLibrary.duplicate_asset(source_path, destination_path):
        raise RuntimeError(f"Could not duplicate {source_path} to {destination_path}")
    return unreal.EditorAssetLibrary.load_asset(destination_path)


def create_blueprint_if_missing():
    existing = unreal.EditorAssetLibrary.load_asset(BLUEPRINT_PATH)
    if existing:
        return existing
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", unreal.ProceduralStarSystemMap)
    return create_asset_if_missing(BLUEPRINT_PATH, unreal.Blueprint, factory)


def create_star_catalog():
    table = unreal.EditorAssetLibrary.load_asset(STAR_CATALOG_PATH)
    if not table:
        factory = unreal.DataTableFactory()
        factory.set_editor_property("struct", unreal.StarInputData.static_struct())
        table = create_asset_if_missing(STAR_CATALOG_PATH, unreal.DataTable, factory)

    csv_path = unreal.Paths.convert_relative_path_to_full(
        unreal.Paths.project_dir() + "Config/SpaceSystems/GinnungagapFictionalStars.csv"
    )
    with open(csv_path, "r", encoding="utf-8") as source:
        csv_text = source.read()
    if not unreal.DataTableFunctionLibrary.fill_data_table_from_csv_string(table, csv_text):
        raise RuntimeError("Star catalog import failed; see LogCSVImportFactory")
    return table


def create_proof_level(blueprint, star_catalog):
    level_directory = PROOF_LEVEL_PATH.rsplit("/", 1)[0]
    ensure_directory(level_directory)
    if unreal.EditorAssetLibrary.does_asset_exist(PROOF_LEVEL_PATH):
        unreal.EditorLevelLibrary.load_level(PROOF_LEVEL_PATH)
    elif not unreal.EditorLevelLibrary.new_level(PROOF_LEVEL_PATH):
        raise RuntimeError(f"Could not create {PROOF_LEVEL_PATH}")

    world = unreal.EditorLevelLibrary.get_editor_world()
    subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in subsystem.get_all_level_actors():
        if actor.get_actor_label() in ("Ginnos Procedural System", "Ginnungagap Fictional Celestial Vault"):
            subsystem.destroy_actor(actor)

    system_actor = subsystem.spawn_actor_from_class(blueprint.generated_class(), unreal.Vector())
    system_actor.set_actor_label("Ginnos Procedural System")
    system_actor.set_editor_property("visual_quality_tier", unreal.SystemVisualQualityTier.CINEMATIC)

    vault = subsystem.spawn_actor_from_class(unreal.CelestialVaultDaySequenceActor, unreal.Vector())
    vault.set_actor_label("Ginnungagap Fictional Celestial Vault")
    vault.set_editor_property("fictional_star_catalog", star_catalog)
    vault.set_editor_property("max_visible_magnitude", 5.5)
    vault.set_editor_property("keep_stars_info", True)
    for component_property in (
        "sun_light_component",
        "moon_light_component",
        "sky_atmosphere_component",
        "exponential_height_fog_component",
        "volumetric_cloud_component",
    ):
        component = vault.get_editor_property(component_property)
        component.set_visibility(False, True)

    unreal.EditorLoadingAndSavingUtils.save_map(world, PROOF_LEVEL_PATH)
    return world


def build_asteroid_graph(graph):
    """Build a deterministic, local-space asteroid shell with varied instanced meshes."""
    graph.remove_nodes()

    sphere_node, sphere = graph.add_node_of_type(unreal.PCGCreatePointsSphereSettings)
    sphere.set_editor_properties(
        {
            "sphere_generation": unreal.PCGSphereGeneration.RANDOM,
            "coordinate_space": unreal.PCGCoordinateSpace.ORIGINAL_COMPONENT,
            "radius": 1800000.0,
            "sample_count": 420,
            "jitter": 0.42,
            "seed": 1103,
        }
    )

    transform_node, transform = graph.add_node_of_type(unreal.PCGTransformPointsSettings)
    transform.set_editor_properties(
        {
            "rotation_min": unreal.Rotator(-180.0, -180.0, -180.0),
            "rotation_max": unreal.Rotator(180.0, 180.0, 180.0),
            "scale_min": unreal.Vector(0.18, 0.13, 0.15),
            "scale_max": unreal.Vector(2.8, 2.2, 2.5),
            "uniform_scale": False,
            "recompute_seed": True,
            "seed": 2089,
        }
    )

    spawner_node, spawner = graph.add_node_of_type(unreal.PCGStaticMeshSpawnerSettings)
    entries = []
    for mesh_path, weight in ASTEROID_MESHES:
        entry = unreal.PCGMeshSelectorWeightedEntry()
        entry.import_text(
            f'(Descriptor=(StaticMesh="{mesh_path}",Mobility=Static,'
            'BodyInstance=(CollisionEnabled=NoCollision),bCastShadow=True,'
            'bAffectDistanceFieldLighting=False,bReceivesDecals=False),'
            f'Weight={weight})'
        )
        entries.append(entry)
    spawner.mesh_selector_parameters.set_editor_property("mesh_entries", entries)
    spawner.set_editor_properties(
        {
            "seed": 3251,
            "apply_mesh_bounds_to_points": True,
            "synchronous_load": True,
        }
    )

    sphere_node.set_node_position(-600, 0)
    transform_node.set_node_position(-250, 0)
    spawner_node.set_node_position(120, 0)
    graph.output_node.set_node_position(500, 0)
    graph.add_edge(sphere_node, "Out", transform_node, "In")
    graph.add_edge(transform_node, "Out", spawner_node, "In")
    graph.add_edge(spawner_node, "Out", graph.output_node, "Out")


def assign_assets_to_blueprint(blueprint, pcg_graph, radiation_system, nebula_system):
    generated_class = blueprint.generated_class()
    defaults = unreal.get_default_object(generated_class)
    asteroid_pcg = defaults.get_editor_property("asteroid_pcg")
    radiation_fx = defaults.get_editor_property("radiation_dust_fx")
    nebula_fx = defaults.get_editor_property("nebula_fx")

    asteroid_pcg.set_graph(pcg_graph)
    radiation_fx.set_asset(radiation_system)
    nebula_fx.set_asset(nebula_system)
    landmark_meshes = [unreal.load_asset(path) for path in FAB_LANDMARK_MESHES]
    if not all(landmark_meshes):
        raise RuntimeError("One or more Fab landmark meshes could not be loaded")
    landmark_classes = [unreal.load_class(None, path) for path in FAB_LANDMARK_BLUEPRINTS]
    if not all(landmark_classes):
        raise RuntimeError("One or more Fab landmark Blueprint classes could not be loaded")
    defaults.set_editor_property("landmark_meshes", landmark_meshes)
    defaults.set_editor_property("landmark_actor_classes", landmark_classes)
    defaults.set_editor_property("landmark_spawn_chance", 0.35)
    defaults.set_editor_property("landmark_target_diameter_cm", 30000.0)
    unreal.BlueprintEditorLibrary.compile_blueprint(blueprint)


def main():
    for directory in (
        ROOT,
        f"{ROOT}/PCG",
        f"{ROOT}/Niagara",
        f"{ROOT}/Blueprints",
        f"{ROOT}/Data",
        "/Game/Assets/SpaceSystems/TwinmotionStaging",
    ):
        ensure_directory(directory)

    pcg_graph = create_asset_if_missing(
        GRAPH_PATH, unreal.PCGGraph, unreal.PCGGraphFactory()
    )
    build_asteroid_graph(pcg_graph)
    radiation_system = duplicate_if_missing(RADIATION_TEMPLATE, RADIATION_PATH)
    nebula_system = duplicate_if_missing(NEBULA_TEMPLATE, NEBULA_PATH)
    blueprint = create_blueprint_if_missing()
    assign_assets_to_blueprint(blueprint, pcg_graph, radiation_system, nebula_system)
    star_catalog = create_star_catalog()
    create_proof_level(blueprint, star_catalog)

    for asset in (pcg_graph, radiation_system, nebula_system, blueprint, star_catalog):
        unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)

    unreal.log(
        "SPACE_ASSETS_CREATED "
        + ", ".join((GRAPH_PATH, RADIATION_PATH, NEBULA_PATH, BLUEPRINT_PATH))
    )


if __name__ == "__main__":
    main()
