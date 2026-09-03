"""Execute five non-destructive Crew oversuit refinement passes in Unreal.

The four geometry passes are additive morph targets derived from the authored
Space Marshal sections. No primitives are appended and no topology, UV, skin
weight, or skeleton data is replaced. The fifth pass creates the restrained
Crew material treatment and assigns it only to the Crew working copy.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V24Sculpt"
WORKING = ROOT + "/Working/Iteration_01"
CREW_PATH = WORKING + "/Roles/SKM_PrimaryOversuit_Crew_Work_I01"
MAP_PATH = ROOT + "/Maps/L_PrimaryOversuit_V24_Sculpt"
MATERIAL_ROOT = WORKING + "/Materials"
SOURCE_CREW_MATERIAL = (
    "/Game/Characters/PlayerSuits/PrimaryOversuits/V24Review/SpaceMarshal/"
    "Materials/MI_Crew_SM_Suit"
)
CREW_MATERIAL_PATH = MATERIAL_ROOT + "/MI_PrimaryOversuit_Crew_Work_I01"
SHARED_FIT = "V24_SharedFit_I01"
MORPHS = (
    "V24_Crew_01_SilhouetteCleanup",
    "V24_Crew_02_HelmetCollar",
    "V24_Crew_03_EquipmentSettle",
    "V24_Crew_04_MobilityClearance",
)
REPORT = PROJECT / "Saved" / "Reports" / "PrimaryOversuitV24CrewFivePasses.json"


def require_asset(path: str, expected_type):
    value = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(value, expected_type):
        raise RuntimeError(f"Missing or invalid Unreal asset: {path}")
    return value


def extract_source_mesh(asset: unreal.SkeletalMesh) -> unreal.DynamicMesh:
    dynamic_mesh = unreal.DynamicMesh()
    options = unreal.GeometryScriptCopyMeshFromAssetOptions()
    lod = unreal.GeometryScriptMeshReadLOD()
    lod.lod_type = unreal.GeometryScriptLODType.SOURCE_MODEL
    lod.lod_index = 0
    _, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_skeletal_mesh(
        asset, dynamic_mesh, options, lod
    )
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError(f"Could not extract Crew source LOD0: {outcome}")
    return dynamic_mesh


def material_slots(asset: unreal.SkeletalMesh) -> dict[str, int]:
    return {
        str(material.material_slot_name): index
        for index, material in enumerate(asset.get_editor_property("materials"))
    }


def section_vertex_sets(dynamic_mesh: unreal.DynamicMesh, slots: dict[str, int]) -> dict[str, set[int]]:
    by_material = {material_id: set() for material_id in slots.values()}
    _, triangle_ids, _ = unreal.GeometryScript_MeshQueries.get_all_triangle_i_ds(dynamic_mesh)
    for triangle_id in triangle_ids.convert_index_list_to_array():
        material_id, valid_material = unreal.GeometryScript_Materials.get_triangle_material_id(
            dynamic_mesh, triangle_id
        )
        if not valid_material or material_id not in by_material:
            continue
        triangle, valid_triangle = unreal.GeometryScript_MeshQueries.get_triangle_indices(
            dynamic_mesh, triangle_id
        )
        if valid_triangle:
            by_material[material_id].update((triangle.x, triangle.y, triangle.z))
    return {name: by_material[index] for name, index in slots.items()}


def bone_map(dynamic_mesh: unreal.DynamicMesh) -> dict[str, unreal.GeometryScriptBoneInfo]:
    _, bones = unreal.GeometryScript_BoneWeights.get_all_bones_info(dynamic_mesh)
    return {str(bone.name): bone for bone in bones}


def position_data(dynamic_mesh: unreal.DynamicMesh):
    _, position_list, has_gaps = unreal.GeometryScript_MeshQueries.get_all_vertex_positions(
        dynamic_mesh, False
    )
    if has_gaps:
        raise RuntimeError("Crew refinement requires dense donor vertex IDs")
    return position_list, position_list.convert_vector_list_to_array()


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 0.0
    t = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def finish_positions(
    dynamic_mesh: unreal.DynamicMesh,
    position_list: unreal.GeometryScriptVectorList,
    source_positions: list[unreal.Vector],
    changed: dict[int, unreal.Vector],
) -> dict:
    displacement_sum = 0.0
    displacement_max = 0.0
    for vertex_id, target in changed.items():
        displacement = (target - source_positions[vertex_id]).length()
        if not math.isfinite(displacement):
            raise RuntimeError(f"Non-finite Crew deformation at vertex {vertex_id}")
        displacement_sum += displacement
        displacement_max = max(displacement_max, displacement)
        position_list.set_vector_list_item(vertex_id, target)
    unreal.GeometryScript_MeshEdits.set_all_mesh_vertex_positions(dynamic_mesh, position_list)
    if not changed:
        raise RuntimeError("Crew refinement pass produced no vertex changes")
    return {
        "changed_vertices": len(changed),
        "average_displacement_cm": displacement_sum / len(changed),
        "maximum_displacement_cm": displacement_max,
    }


def cleanup_radial_scale(bone_name: str) -> float:
    name = bone_name.lower()
    if name == "pelvis" or name.startswith("spine_"):
        return 0.980
    if name.startswith(("thigh", "calf", "upperarm", "lowerarm")):
        return 0.985
    if name.startswith("clavicle"):
        return 0.990
    return 1.0


def pass_silhouette_cleanup(
    asset: unreal.SkeletalMesh, section_vertices: dict[str, set[int]]
) -> tuple[unreal.DynamicMesh, dict]:
    mesh = extract_source_mesh(asset)
    positions, source = position_data(mesh)
    _, bones = unreal.GeometryScript_BoneWeights.get_all_bones_info(mesh)
    bones_by_index = {bone.index: bone for bone in bones}
    changed = {}
    for vertex_id in section_vertices["SM_Suit"]:
        position = source[vertex_id]
        _, weights, valid = unreal.GeometryScript_BoneWeights.get_vertex_bone_weights(mesh, vertex_id)
        if not valid:
            continue
        target = unreal.Vector(0.0, 0.0, 0.0)
        weight_sum = 0.0
        has_scaled_weight = False
        for bone_weight in weights:
            bone = bones_by_index.get(bone_weight.bone_index)
            weight = float(bone_weight.weight)
            if not bone or weight <= 0.0:
                continue
            scale = cleanup_radial_scale(str(bone.name))
            local = bone.world_transform.inverse_transform_location(position)
            if scale != 1.0:
                local.y *= scale
                local.z *= scale
                has_scaled_weight = True
            target += bone.world_transform.transform_location(local) * weight
            weight_sum += weight
        if not has_scaled_weight or weight_sum <= 0.0:
            continue
        if weight_sum < 1.0:
            target += position * (1.0 - weight_sum)
        elif weight_sum > 1.00001:
            target /= weight_sum
        if (target - position).length() > 0.0001:
            changed[vertex_id] = target
    stats = finish_positions(mesh, positions, source, changed)
    stats["intent"] = "Reduce remaining inflated flexible-shell volume without changing limb length"
    return mesh, stats


def pass_helmet_collar(
    asset: unreal.SkeletalMesh, section_vertices: dict[str, set[int]]
) -> tuple[unreal.DynamicMesh, dict]:
    mesh = extract_source_mesh(asset)
    positions, source = position_data(mesh)
    bones = bone_map(mesh)
    head = bones["head"].world_transform.translation
    neck = bones["neck_01"].world_transform.translation
    changed = {}
    helmet_vertices = section_vertices["SM_Helm"] | section_vertices["MS_Visor"]
    for vertex_id in helmet_vertices:
        position = source[vertex_id]
        offset = position - head
        changed[vertex_id] = unreal.Vector(
            head.x + offset.x * 0.950,
            head.y + offset.y * 0.940,
            head.z + offset.z * 0.970 - 0.80,
        )
    for vertex_id in section_vertices["SM_Suit"]:
        position = source[vertex_id]
        z_weight = smoothstep(148.0, 154.0, position.z) * (
            1.0 - smoothstep(164.0, 170.0, position.z)
        )
        x_weight = 1.0 - smoothstep(20.0, 29.0, abs(position.x))
        weight = z_weight * x_weight
        if weight <= 0.0:
            continue
        target = unreal.Vector(
            neck.x + (position.x - neck.x) * 0.965,
            neck.y + (position.y - neck.y) * 0.955,
            position.z - 0.35,
        )
        changed[vertex_id] = position + (target - position) * weight
    stats = finish_positions(mesh, positions, source, changed)
    stats["intent"] = "Bring the donor helmet and collar closer to the compact pressure-bubble concept"
    return mesh, stats


def pass_equipment_settle(
    asset: unreal.SkeletalMesh, section_vertices: dict[str, set[int]]
) -> tuple[unreal.DynamicMesh, dict]:
    mesh = extract_source_mesh(asset)
    positions, source = position_data(mesh)
    changed = {}
    equipment = section_vertices["SM_Bags"] | section_vertices["SM_Pouch"]
    backpack_count = 0
    harness_count = 0
    for vertex_id in equipment:
        position = source[vertex_id]
        if position.y < -12.0 and position.z > 105.0:
            target = unreal.Vector(
                position.x * 0.960,
                -10.0 + (position.y + 10.0) * 0.880,
                125.0 + (position.z - 125.0) * 0.975,
            )
            backpack_count += 1
        else:
            target = unreal.Vector(
                position.x * 0.970,
                -2.5 + (position.y + 2.5) * 0.950,
                105.0 + (position.z - 105.0) * 0.985 + 0.30,
            )
            harness_count += 1
        if (target - position).length() > 0.0001:
            changed[vertex_id] = target
    stats = finish_positions(mesh, positions, source, changed)
    stats.update(
        {
            "intent": "Settle authored packs and pouches into a compact practical Crew harness",
            "backpack_vertices": backpack_count,
            "harness_vertices": harness_count,
        }
    )
    return mesh, stats


def pass_mobility_clearance(
    asset: unreal.SkeletalMesh, section_vertices: dict[str, set[int]]
) -> tuple[unreal.DynamicMesh, dict]:
    mesh = extract_source_mesh(asset)
    positions, source = position_data(mesh)
    bones = bone_map(mesh)
    joints = {
        "lowerarm_r": (0.950, 12.0, 14.0),
        "lowerarm_l": (0.950, 12.0, 14.0),
        "calf_r": (0.950, 13.5, 18.0),
        "calf_l": (0.950, 13.5, 18.0),
        "hand_r": (0.975, 8.0, 12.0),
        "hand_l": (0.975, 8.0, 12.0),
        "foot_r": (0.975, 8.0, 15.0),
        "foot_l": (0.975, 8.0, 15.0),
    }
    eligible = (
        section_vertices["SM_Suit"]
        | section_vertices["SM_Gloves"]
        | section_vertices["SM_Boots"]
    )
    changed = {}
    joint_counts = {name: 0 for name in joints}
    for vertex_id in eligible:
        position = source[vertex_id]
        target = position
        influenced = False
        for bone_name, (radial_scale, axial_reach, radial_reach) in joints.items():
            transform = bones[bone_name].world_transform
            local = transform.inverse_transform_location(target)
            axial_weight = 1.0 - smoothstep(
                axial_reach * 0.45, axial_reach, abs(local.x)
            )
            radial_distance = math.sqrt(local.y * local.y + local.z * local.z)
            neighborhood_weight = 1.0 - smoothstep(
                radial_reach * 0.70, radial_reach, radial_distance
            )
            weight = axial_weight * neighborhood_weight
            if weight <= 0.0:
                continue
            scale = 1.0 - (1.0 - radial_scale) * weight
            local.y *= scale
            local.z *= scale
            target = transform.transform_location(local)
            joint_counts[bone_name] += 1
            influenced = True
        if influenced and (target - position).length() > 0.0001:
            changed[vertex_id] = target
    stats = finish_positions(mesh, positions, source, changed)
    stats.update(
        {
            "intent": "Open restrained elbow, knee, wrist, and ankle articulation clearance",
            "joint_vertex_counts": joint_counts,
        }
    )
    return mesh, stats


def write_morph(
    source: unreal.DynamicMesh, asset: unreal.SkeletalMesh, morph_name: str
) -> str:
    options = unreal.GeometryScriptCopyMorphTargetToAssetOptions()
    options.overwrite_existing_target = True
    options.emit_transaction = False
    options.copy_normals = False
    target_lod = unreal.GeometryScriptMeshWriteLOD()
    target_lod.lod_index = 0
    _, outcome = unreal.GeometryScript_AssetUtils.copy_morph_target_to_skeletal_mesh(
        source, asset, unreal.Name(morph_name), options, target_lod
    )
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError(f"Could not write Crew morph {morph_name}: {outcome}")
    return str(outcome)


def build_crew_material(crew: unreal.SkeletalMesh, slots: dict[str, int]):
    source = require_asset(SOURCE_CREW_MATERIAL, unreal.MaterialInstanceConstant)
    if not unreal.EditorAssetLibrary.does_asset_exist(CREW_MATERIAL_PATH):
        duplicate = unreal.EditorAssetLibrary.duplicate_asset(SOURCE_CREW_MATERIAL, CREW_MATERIAL_PATH)
        if not isinstance(duplicate, unreal.MaterialInstanceConstant):
            raise RuntimeError("Could not create Crew working material instance")
    material = require_asset(CREW_MATERIAL_PATH, unreal.MaterialInstanceConstant)
    tint = unreal.LinearColor(0.20, 0.31, 0.46, 1.0)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        material, "RoleTint", tint
    )
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        material, "RoleTintStrength", 0.14
    )
    unreal.EditorAssetLibrary.set_metadata_tag(material, "PlayerSuitRole", "Crew")
    unreal.EditorAssetLibrary.set_metadata_tag(material, "PlayerSuitSurfacePass", "V24Crew05")
    unreal.EditorAssetLibrary.set_metadata_tag(material, "PlayerSuitRuntimeReady", "False")
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)

    skeletal_materials = list(crew.get_editor_property("materials"))
    suit_index = slots["SM_Suit"]
    suit_slot = skeletal_materials[suit_index]
    suit_slot.material_interface = material
    skeletal_materials[suit_index] = suit_slot
    crew.set_editor_property("materials", skeletal_materials)
    return material, source, tint, suit_index


def update_workspace_preview(
    crew: unreal.SkeletalMesh,
    material: unreal.MaterialInstanceConstant,
    suit_index: int,
) -> list[str]:
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not level.load_level(MAP_PATH):
        raise RuntimeError(f"Could not load Crew sculpt workspace: {MAP_PATH}")
    applied = []
    for actor in unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors():
        if not isinstance(actor, unreal.SkeletalMeshActor):
            continue
        label = actor.get_actor_label()
        if label == "WORKING_ROLE_Crew_I01":
            actor.skeletal_mesh_component.set_skinned_asset_and_update(crew)
            actor.skeletal_mesh_component.set_morph_target(SHARED_FIT, 1.0, False)
            for morph in MORPHS:
                actor.skeletal_mesh_component.set_morph_target(morph, 1.0, False)
            actor.skeletal_mesh_component.set_material(suit_index, material)
            applied.append(label)
        elif label.startswith("WORKING_ROLE_"):
            actor.skeletal_mesh_component.set_morph_target(SHARED_FIT, 1.0, False)
    level.save_current_level()
    return applied


crew = require_asset(CREW_PATH, unreal.SkeletalMesh)
if SHARED_FIT not in crew.get_all_morph_target_names():
    raise RuntimeError(f"Crew must contain {SHARED_FIT} before the five-pass refinement")

probe_mesh = extract_source_mesh(crew)
slots = material_slots(crew)
required_slots = {"SM_Suit", "SM_Helm", "MS_Visor", "SM_Gloves", "SM_Boots", "SM_Bags", "SM_Pouch"}
missing_slots = sorted(required_slots.difference(slots))
if missing_slots:
    raise RuntimeError(f"Crew source is missing authored garment sections: {missing_slots}")
sections = section_vertex_sets(probe_mesh, slots)
vertex_count = unreal.GeometryScript_MeshQueries.get_vertex_count(probe_mesh)

builders = (
    pass_silhouette_cleanup,
    pass_helmet_collar,
    pass_equipment_settle,
    pass_mobility_clearance,
)
pass_results = {}
for morph_name, builder in zip(MORPHS, builders):
    morph_mesh, stats = builder(crew, sections)
    if unreal.GeometryScript_MeshQueries.get_vertex_count(morph_mesh) != vertex_count:
        raise RuntimeError(f"Crew pass changed topology: {morph_name}")
    stats["write_outcome"] = write_morph(morph_mesh, crew, morph_name)
    pass_results[morph_name] = stats

crew_material, source_material, tint, suit_material_index = build_crew_material(crew, slots)
unreal.EditorAssetLibrary.set_metadata_tag(crew, "PlayerSuitCrewPassCount", "5")
unreal.EditorAssetLibrary.set_metadata_tag(crew, "PlayerSuitCrewMorphStack", ",".join(MORPHS))
unreal.EditorAssetLibrary.set_metadata_tag(crew, "PlayerSuitRoleSculptStatus", "CrewPass05ConceptReview")
unreal.EditorAssetLibrary.set_metadata_tag(
    crew, "PlayerSuitNextArtPass", "CrewAuthoredHarnessMonitorAndSurveyToolMount"
)
unreal.EditorAssetLibrary.set_metadata_tag(crew, "PlayerSuitRuntimeReady", "False")
unreal.EditorAssetLibrary.save_loaded_asset(crew, only_if_is_dirty=False)

result = {
    "version": 24,
    "status": "crew_five_pass_concept_review_not_runtime_promoted",
    "crew_mesh": crew.get_path_name(),
    "source_vertex_count": vertex_count,
    "authored_section_vertex_counts": {
        name: len(vertices) for name, vertices in sorted(sections.items())
    },
    "shared_fit": SHARED_FIT,
    "geometry_passes": pass_results,
    "surface_pass": {
        "material": crew_material.get_path_name(),
        "source_material": source_material.get_path_name(),
        "role_tint": [tint.r, tint.g, tint.b, tint.a],
        "role_tint_strength": 0.14,
        "suit_material_index": suit_material_index,
        "intent": "Desaturated Crew identification over the donor PBR surface",
    },
    "preview_actors": update_workspace_preview(crew, crew_material, suit_material_index),
    "topology_preserved": True,
    "runtime_ready": False,
    "next_gate": "CrewAuthoredHarnessMonitorAndSurveyToolMount",
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log("Primary oversuit V24 Crew five-pass refinement complete")
