"""Seed the topology-preserving V24 shared-fit morph in Unreal.

This is an Unreal-authored fitting pass over the project-owned male working
duplicate. It preserves the source vertices, triangles, UVs, skin weights, bone
hierarchy, and materials. The result is stored as a reversible morph target and
copied to the four topology-identical role working meshes. It is not a runtime
promotion or a replacement for the later Manny/Quinn rebind and pose validation.
"""

from __future__ import annotations

import json
import math
from collections import Counter
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V24Sculpt"
WORKING = ROOT + "/Working/Iteration_01"
MAP_PATH = ROOT + "/Maps/L_PrimaryOversuit_V24_Sculpt"
MALE_FIT = WORKING + "/BodyFits/SKM_PrimaryOversuit_MaleFit_Work_I01"
ROLES = ("Crew", "Engineering", "Medical", "Security")
MORPH_NAME = "V24_SharedFit_I01"
REPORT = PROJECT / "Saved" / "Reports" / "PrimaryOversuitV24SharedFit.json"


def load_skeletal_mesh(path: str) -> unreal.SkeletalMesh:
    mesh = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(mesh, unreal.SkeletalMesh):
        raise RuntimeError(f"Required skeletal working mesh is missing: {path}")
    return mesh


def radial_scale_for_bone(bone_name: str) -> tuple[float, str]:
    """Return local radial scale and the fit region used for reporting."""

    name = bone_name.lower()
    if name.startswith(("head", "neck_")):
        return 1.0, "helmet_preserved"
    if name.startswith(("thigh", "calf")):
        return 0.92, "legs"
    if name.startswith(("foot", "ball")):
        return 0.93, "boots"
    if name.startswith(("upperarm", "lowerarm")):
        return 0.92, "arms"
    if name.startswith(("hand", "thumb", "index", "middle", "ring", "pinky")):
        return 0.94, "gloves"
    if name.startswith("clavicle"):
        return 0.96, "shoulders"
    if name == "pelvis" or name.startswith("spine_"):
        return 0.96, "torso"
    return 1.0, "preserved"


def build_fit_morph(source_asset: unreal.SkeletalMesh) -> tuple[unreal.DynamicMesh, dict]:
    dynamic_mesh = unreal.DynamicMesh()
    read_options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    read_lod = unreal.GeometryScriptMeshReadLOD()
    read_lod.lod_type = unreal.GeometryScriptLODType.SOURCE_MODEL
    read_lod.lod_index = 0
    _, copy_outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh(
        source_asset, dynamic_mesh, read_options, read_lod
    )
    if copy_outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError(f"Could not extract male fit LOD0: {copy_outcome}")

    vertex_count_before = unreal.GeometryScript_MeshQueries.get_vertex_count(dynamic_mesh)
    _, bones = unreal.GeometryScript_BoneWeights.get_all_bones_info(dynamic_mesh)
    bones_by_index = {bone.index: bone for bone in bones}
    if not bones_by_index:
        raise RuntimeError("Extracted oversuit Dynamic Mesh has no skeleton attributes")

    _, position_list, has_gaps = unreal.GeometryScript_MeshQueries.get_all_vertex_positions(
        dynamic_mesh, False
    )
    if has_gaps:
        raise RuntimeError("Shared-fit seed requires dense donor vertex IDs")
    source_positions = position_list.convert_vector_list_to_array()
    if len(source_positions) != vertex_count_before:
        raise RuntimeError("Position count does not match donor LOD0 vertex count")

    displacement_sum = 0.0
    displacement_max = 0.0
    changed_vertices = 0
    region_counts: Counter[str] = Counter()

    for vertex_id, position in enumerate(source_positions):
        _, weights, valid_weights = unreal.GeometryScript_BoneWeights.get_vertex_bone_weights(
            dynamic_mesh, vertex_id
        )
        if not valid_weights or not weights:
            continue

        blended = unreal.Vector(0.0, 0.0, 0.0)
        weight_sum = 0.0
        dominant_name = "unweighted"
        dominant_weight = -1.0
        for bone_weight in weights:
            bone = bones_by_index.get(bone_weight.bone_index)
            weight = float(bone_weight.weight)
            if not bone or weight <= 0.0:
                continue
            if weight > dominant_weight:
                dominant_weight = weight
                dominant_name = str(bone.name)

            radial_scale, _ = radial_scale_for_bone(str(bone.name))
            if radial_scale == 1.0:
                candidate = position
            else:
                local = bone.world_transform.inverse_transform_location(position)
                local.y *= radial_scale
                local.z *= radial_scale
                candidate = bone.world_transform.transform_location(local)
            blended += candidate * weight
            weight_sum += weight

        if weight_sum <= 0.0:
            continue
        if weight_sum < 1.0:
            blended += position * (1.0 - weight_sum)
        elif weight_sum > 1.00001:
            blended /= weight_sum

        displacement = (blended - position).length()
        if displacement > 0.0001:
            changed_vertices += 1
            displacement_sum += displacement
            displacement_max = max(displacement_max, displacement)
            _, region = radial_scale_for_bone(dominant_name)
            region_counts[region] += 1
            position_list.set_vector_list_item(vertex_id, blended)

    unreal.GeometryScript_MeshEdits.set_all_mesh_vertex_positions(dynamic_mesh, position_list)
    vertex_count_after = unreal.GeometryScript_MeshQueries.get_vertex_count(dynamic_mesh)
    if vertex_count_after != vertex_count_before:
        raise RuntimeError("Shared-fit deformation changed donor topology")
    if changed_vertices == 0 or not math.isfinite(displacement_max):
        raise RuntimeError("Shared-fit deformation produced no valid vertex changes")

    return dynamic_mesh, {
        "copy_outcome": str(copy_outcome),
        "vertex_count_before": vertex_count_before,
        "vertex_count_after": vertex_count_after,
        "changed_vertices": changed_vertices,
        "average_changed_vertex_displacement_cm": displacement_sum / changed_vertices,
        "maximum_vertex_displacement_cm": displacement_max,
        "dominant_bone_regions": dict(sorted(region_counts.items())),
        "topology_preserved": True,
    }


def write_morph(dynamic_mesh: unreal.DynamicMesh, mesh_asset: unreal.SkeletalMesh) -> str:
    options = unreal.GeometryScriptCopyMorphTargetToAssetOptions()
    options.overwrite_existing_target = True
    options.emit_transaction = False
    options.defer_mesh_post_edit_change = False
    options.copy_normals = False
    target_lod = unreal.GeometryScriptMeshWriteLOD()
    target_lod.lod_index = 0
    target_lod.write_hi_res_source = False
    _, outcome = unreal.GeometryScript_AssetUtils.copy_morph_target_to_skeletal_mesh(
        dynamic_mesh,
        mesh_asset,
        unreal.Name(MORPH_NAME),
        options,
        target_lod,
    )
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError(f"Could not write {MORPH_NAME} to {mesh_asset.get_path_name()}: {outcome}")
    if MORPH_NAME not in mesh_asset.get_all_morph_target_names():
        raise RuntimeError(f"Morph target was not registered on {mesh_asset.get_path_name()}")

    unreal.EditorAssetLibrary.set_metadata_tag(mesh_asset, "PlayerSuitFitMorph", MORPH_NAME)
    unreal.EditorAssetLibrary.set_metadata_tag(mesh_asset, "PlayerSuitFitIteration", "01")
    unreal.EditorAssetLibrary.set_metadata_tag(
        mesh_asset, "PlayerSuitFitMethod", "UnrealGeometryScriptBoneLocalRadialTailor"
    )
    unreal.EditorAssetLibrary.set_metadata_tag(mesh_asset, "PlayerSuitRuntimeReady", "False")
    unreal.EditorAssetLibrary.save_loaded_asset(mesh_asset, only_if_is_dirty=False)
    return str(outcome)


def apply_preview_to_workspace() -> list[str]:
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level.load_level(MAP_PATH):
        raise RuntimeError(f"Could not load V24 sculpt workspace: {MAP_PATH}")
    preview_labels = []
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        label = actor.get_actor_label()
        if not isinstance(actor, unreal.SkeletalMeshActor):
            continue
        if label.startswith("WORKING_ROLE_") or label == "WORKING_FIT_MaleDonor_I01":
            actor.skeletal_mesh_component.set_morph_target(MORPH_NAME, 1.0, False)
            preview_labels.append(label)
    level.save_current_level()
    return sorted(preview_labels)


male_fit = load_skeletal_mesh(MALE_FIT)
fit_mesh, fit_stats = build_fit_morph(male_fit)
targets = {"MaleFit": male_fit}
for role in ROLES:
    targets[role] = load_skeletal_mesh(
        f"{WORKING}/Roles/SKM_PrimaryOversuit_{role}_Work_I01"
    )

outcomes = {name: write_morph(fit_mesh, target) for name, target in targets.items()}
unreal.EditorAssetLibrary.set_metadata_tag(
    targets["Crew"], "PlayerSuitRoleSculptStatus", "CrewPass01SharedFitReady"
)
unreal.EditorAssetLibrary.set_metadata_tag(
    targets["Crew"], "PlayerSuitNextArtPass", "CrewPracticalSurveyEquipmentAndSurfaceBreakup"
)
unreal.EditorAssetLibrary.save_loaded_asset(targets["Crew"], only_if_is_dirty=False)

result = {
    "version": 24,
    "status": "shared_fit_seed_ready_not_runtime_promoted",
    "morph_target": MORPH_NAME,
    "source": male_fit.get_path_name(),
    "targets": {name: target.get_path_name() for name, target in targets.items()},
    "write_outcomes": outcomes,
    "fit": fit_stats,
    "preview_actors": apply_preview_to_workspace(),
    "crew_pass": "CrewPass01SharedFitReady",
    "next_gate": "CrewPracticalSurveyEquipmentAndSurfaceBreakup",
    "runtime_ready": False,
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"Primary oversuit V24 shared fit ready: {MORPH_NAME}")
