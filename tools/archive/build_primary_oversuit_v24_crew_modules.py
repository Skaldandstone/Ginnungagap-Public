"""Build two Crew equipment modules from purchased, authored donor geometry.

The generated assets stay in the V24 sculpt workspace. They are independent
static review meshes and are not promoted to the runtime oversuit contract.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V24Sculpt"
WORKING = ROOT + "/Working/Iteration_01"
CREW_PATH = WORKING + "/Roles/SKM_PrimaryOversuit_Crew_Work_I01"
MODULE_ROOT = WORKING + "/CrewModules"
MAP_PATH = ROOT + "/Maps/L_PrimaryOversuit_V24_Sculpt"
POUCH_MATERIAL = (
    "/Game/Characters/PlayerSuits/PrimaryOversuits/V24Review/SpaceMarshal/"
    "Materials/MI_Shared_SM_Pouch"
)
REPORT = PROJECT / "Saved" / "Reports" / "PrimaryOversuitV24CrewModules.json"

MODULES = {
    "HarnessMonitor": {
        "asset_name": "SM_Crew_HarnessMonitor_Work_I01",
        "actor_label": "WORKING_CREW_HarnessMonitor_I01",
        "source_center": unreal.Vector(-0.00096, 11.33371, 108.38388),
        "scale": unreal.Vector(0.90, 1.15, 1.40),
        "placement": unreal.Vector(0.0, 22.0, 144.0),
        "rotation": unreal.Rotator(roll=0.0, pitch=-4.0, yaw=0.0),
        "intent": "Low-profile chest harness monitor housing",
    },
    "SurveyToolMount": {
        "asset_name": "SM_Crew_SurveyToolMount_Work_I01",
        "actor_label": "WORKING_CREW_SurveyToolMount_I01",
        "source_center": unreal.Vector(-12.65544, 8.98702, 109.53549),
        "scale": unreal.Vector(0.85, 0.80, 1.60),
        "placement": unreal.Vector(-30.5, 7.5, 105.0),
        "rotation": unreal.Rotator(roll=0.0, pitch=0.0, yaw=-12.0),
        "intent": "Vertical hip carrier for the Crew survey tool",
    },
}


def require_asset(path: str, expected_type):
    value = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(value, expected_type):
        raise RuntimeError(f"Missing or invalid asset: {path}")
    return value


def vec(value: unreal.Vector) -> list[float]:
    return [round(value.x, 5), round(value.y, 5), round(value.z, 5)]


def triangle_count(mesh: unreal.DynamicMesh) -> int:
    _, triangle_ids, _ = unreal.GeometryScript_MeshQueries.get_all_triangle_i_ds(mesh)
    return len(triangle_ids.convert_index_list_to_array())


def copy_crew_source(crew: unreal.SkeletalMesh) -> unreal.DynamicMesh:
    dynamic_mesh = unreal.DynamicMesh()
    read_lod = unreal.GeometryScriptMeshReadLOD()
    read_lod.lod_type = unreal.GeometryScriptLODType.SOURCE_MODEL
    read_lod.lod_index = 0
    unreal.GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh(
        crew,
        dynamic_mesh,
        unreal.GeometryScriptCopyMeshFromAssetOptions(),
        read_lod,
    )
    return dynamic_mesh


def pouch_islands(source: unreal.DynamicMesh, pool) -> list[unreal.DynamicMesh]:
    _, material_meshes, material_ids = (
        unreal.GeometryScript_MeshDecomposition.split_mesh_by_material_i_ds(source, pool)
    )
    for section, material_id in zip(material_meshes, material_ids):
        if material_id == 4:
            _, islands = unreal.GeometryScript_MeshDecomposition.split_mesh_by_components(
                section, pool
            )
            return list(islands)
    raise RuntimeError("Crew mesh no longer contains the authored SM_Pouch material section")


def closest_island(islands: list[unreal.DynamicMesh], target: unreal.Vector):
    ranked = []
    for island in islands:
        bounds = island.get_mesh_bounding_box()
        center = (bounds.min + bounds.max) * 0.5
        delta = center - target
        ranked.append((delta.length(), island, bounds, center))
    distance, island, bounds, center = min(ranked, key=lambda item: item[0])
    if distance > 0.25:
        raise RuntimeError(f"Authored module island drifted {distance:.3f} cm from its source signature")
    return island, bounds, center, distance


def build_module(module_type: str, spec: dict, islands, material) -> tuple[unreal.StaticMesh, dict]:
    island, source_bounds, source_center, source_distance = closest_island(
        islands, spec["source_center"]
    )
    source_triangles = triangle_count(island)
    source_vertices = unreal.GeometryScript_MeshQueries.get_vertex_count(island)

    unreal.GeometryScript_MeshTransforms.translate_pivot_to_location(island, source_center)
    unreal.GeometryScript_MeshTransforms.scale_mesh(island, spec["scale"], unreal.Vector())
    unreal.GeometryScript_Materials.clear_material_i_ds(island, 0)

    destination = f"{MODULE_ROOT}/{spec['asset_name']}"
    if unreal.EditorAssetLibrary.does_asset_exist(destination):
        if not unreal.EditorAssetLibrary.delete_asset(destination):
            raise RuntimeError(f"Could not replace Crew working module: {destination}")

    options = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    options.enable_recompute_normals = False
    options.enable_recompute_tangents = False
    options.enable_nanite = False
    options.enable_collision = False
    static_mesh, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
        island, destination, options
    )
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS or not isinstance(
        static_mesh, unreal.StaticMesh
    ):
        raise RuntimeError(f"Could not create {module_type}: {outcome}")

    static_mesh.set_material(0, material)
    metadata = {
        "PlayerSuitSource": "FabSpaceMarshalDonorGeometry",
        "PlayerSuitSourceSection": "SM_Pouch",
        "PlayerSuitRole": "Crew",
        "PlayerSuitModuleType": module_type,
        "PlayerSuitModuleIntent": spec["intent"],
        "PlayerSuitStatus": "SculptWorkingModule",
        "PlayerSuitIteration": "01",
        "PlayerSuitRuntimeReady": "False",
        "PlayerSuitPromotionGate": "RebindOrSocketAttachDeformationMultiplayer",
        "PlayerSuitAIGenerationUsed": "False",
    }
    for key, value in metadata.items():
        unreal.EditorAssetLibrary.set_metadata_tag(static_mesh, key, value)
    unreal.EditorAssetLibrary.save_loaded_asset(static_mesh, only_if_is_dirty=False)

    final_bounds = island.get_mesh_bounding_box()
    return static_mesh, {
        "asset": static_mesh.get_path_name(),
        "source_section": "SM_Pouch",
        "source_center_cm": vec(source_center),
        "source_signature_distance_cm": round(source_distance, 5),
        "source_size_cm": vec(source_bounds.max - source_bounds.min),
        "source_triangle_count": source_triangles,
        "source_vertex_count": source_vertices,
        "authored_topology_preserved": (
            triangle_count(island) == source_triangles
            and unreal.GeometryScript_MeshQueries.get_vertex_count(island) == source_vertices
        ),
        "module_size_cm": vec(final_bounds.max - final_bounds.min),
        "placement_local_cm": vec(spec["placement"]),
        "runtime_ready": False,
    }


def install_preview(module_assets: dict[str, unreal.StaticMesh]) -> list[str]:
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level.load_level(MAP_PATH):
        raise RuntimeError(f"Could not load Crew sculpt workspace: {MAP_PATH}")

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    actors = actor_subsystem.get_all_level_actors()
    by_label = {actor.get_actor_label(): actor for actor in actors}
    crew_actor = by_label.get("WORKING_ROLE_Crew_I01")
    if not isinstance(crew_actor, unreal.SkeletalMeshActor):
        raise RuntimeError("Crew working actor is missing from the V24 sculpt map")

    replace_labels = {spec["actor_label"] for spec in MODULES.values()}
    replace_labels.add("CAM_Crew_Modules_Closeup")
    for actor in actors:
        if actor.get_actor_label() in replace_labels:
            actor_subsystem.destroy_actor(actor)

    crew_transform = crew_actor.get_actor_transform()
    crew_rotation = crew_actor.get_actor_rotation()
    installed = []
    for module_type, spec in MODULES.items():
        location = crew_transform.transform_location(spec["placement"])
        relative_rotation = spec["rotation"]
        rotation = unreal.Rotator(
            roll=crew_rotation.roll + relative_rotation.roll,
            pitch=crew_rotation.pitch + relative_rotation.pitch,
            yaw=crew_rotation.yaw + relative_rotation.yaw,
        )
        actor = actor_subsystem.spawn_actor_from_class(
            unreal.StaticMeshActor, location, rotation
        )
        actor.set_actor_label(spec["actor_label"])
        actor.static_mesh_component.set_static_mesh(module_assets[module_type])
        actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        actor.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        installed.append(actor.get_actor_label())

    camera_location = crew_transform.transform_location(unreal.Vector(0.0, 360.0, 138.0))
    camera = actor_subsystem.spawn_actor_from_class(
        unreal.CameraActor,
        camera_location,
        unreal.Rotator(roll=0.0, pitch=-1.0, yaw=crew_rotation.yaw - 90.0),
    )
    camera.set_actor_label("CAM_Crew_Modules_Closeup")
    camera.camera_component.set_editor_property("field_of_view", 32.0)

    crew_actor.skeletal_mesh_component.set_morph_target("V24_SharedFit_I01", 1.0, False)
    for morph in (
        "V24_Crew_01_SilhouetteCleanup",
        "V24_Crew_02_HelmetCollar",
        "V24_Crew_03_EquipmentSettle",
        "V24_Crew_04_MobilityClearance",
    ):
        crew_actor.skeletal_mesh_component.set_morph_target(morph, 1.0, False)

    level.save_current_level()
    return installed


crew = require_asset(CREW_PATH, unreal.SkeletalMesh)
material = require_asset(POUCH_MATERIAL, unreal.MaterialInstanceConstant)
pool = unreal.GeometryScript_SceneUtils.create_dynamic_mesh_pool()
islands = pouch_islands(copy_crew_source(crew), pool)

module_assets = {}
module_report = {}
for module_type, spec in MODULES.items():
    module_assets[module_type], module_report[module_type] = build_module(
        module_type, spec, islands, material
    )

installed = install_preview(module_assets)
unreal.EditorAssetLibrary.set_metadata_tag(crew, "PlayerSuitCrewPassCount", "7")
unreal.EditorAssetLibrary.set_metadata_tag(
    crew, "PlayerSuitRoleSculptStatus", "CrewPass07ModuleReview"
)
unreal.EditorAssetLibrary.set_metadata_tag(
    crew, "PlayerSuitCrewModules", "HarnessMonitor,SurveyToolMount"
)
unreal.EditorAssetLibrary.set_metadata_tag(
    crew, "PlayerSuitNextArtPass", "CrewModuleSocketRiggingAndScreenSurface"
)
unreal.EditorAssetLibrary.set_metadata_tag(crew, "PlayerSuitRuntimeReady", "False")
unreal.EditorAssetLibrary.save_loaded_asset(crew, only_if_is_dirty=False)
unreal.EditorAssetLibrary.save_directory(ROOT, only_if_is_dirty=False, recursive=True)

result = {
    "version": 24,
    "status": "crew_modules_installed_for_concept_review_not_runtime_promoted",
    "crew_mesh": crew.get_path_name(),
    "module_count": len(module_assets),
    "modules": module_report,
    "preview_actors": installed,
    "review_camera": "CAM_Crew_Modules_Closeup",
    "donor_geometry_only": True,
    "ai_generation_used": False,
    "runtime_ready": False,
    "promotion_gate": "RebindOrSocketAttachDeformationMultiplayer",
    "next_gate": "CrewModuleSocketRiggingAndScreenSurface",
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log("Primary oversuit V24 Crew authored modules installed")
