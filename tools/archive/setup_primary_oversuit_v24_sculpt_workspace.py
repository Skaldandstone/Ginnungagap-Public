"""Build the Unreal Modeling Mode workspace for the V24 primary oversuits.

The purchased Space Marshal review meshes remain immutable. This script creates
project working duplicates, approved concept-reference boards, fit references for
Manny and Quinn, and an isolated sculpt map. It deliberately does not promote a
vendor skeleton to the runtime Leader Pose contract.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
REVIEW = "/Game/Characters/PlayerSuits/PrimaryOversuits/V24Review/SpaceMarshal"
ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V24Sculpt"
WORKING = ROOT + "/Working/Iteration_01"
ROLE_ROOT = WORKING + "/Roles"
FIT_ROOT = WORKING + "/BodyFits"
REFERENCE_ROOT = ROOT + "/References"
MAP_PATH = ROOT + "/Maps/L_PrimaryOversuit_V24_Sculpt"
REPORT = PROJECT / "Saved" / "Reports" / "PrimaryOversuitV24SculptWorkspace.json"

MALE_DONOR = REVIEW + "/Meshes/SM_Male_Oversuit_UE5"
FEMALE_DONOR = REVIEW + "/Meshes/SM_Female_Oversuit_Biped"
MANNY = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"
QUINN = "/Game/Characters/Mannequins/Meshes/SKM_Quinn_Simple"

REFERENCES = {
    "StandardTurnaround": PROJECT / "docs/concept-art/reference/suits/standard-suit-turnaround.png",
    "RoleLineup": PROJECT / "docs/concept-art/reference/suits/player-suit-role-lineup.png",
    "SuitingArmory": PROJECT / "docs/concept-art/reference/suits/player-suiting-up-armory-concept.png",
    "V24Target": PROJECT / "docs/concept-art/reference/suits/unreal-primary-oversuit-v24-target.png",
}

ROLE_MATERIALS = {
    "Crew": "MI_Crew_SM_Suit",
    "Engineering": "MI_Engineering_SM_Suit",
    "Medical": "MI_Medical_SM_Suit",
    "Security": "MI_Security_SM_Suit",
}


def asset(path: str, expected_type=None):
    value = unreal.EditorAssetLibrary.load_asset(path)
    if not value:
        raise RuntimeError(f"Required Unreal asset is missing: {path}")
    if expected_type and not isinstance(value, expected_type):
        raise RuntimeError(f"Unexpected asset type at {path}: {type(value)}")
    return value


def duplicate_skeletal(source_path: str, destination_path: str, status: str) -> unreal.SkeletalMesh:
    if unreal.EditorAssetLibrary.does_asset_exist(destination_path):
        unreal.EditorAssetLibrary.delete_asset(destination_path)
    duplicate = unreal.EditorAssetLibrary.duplicate_asset(source_path, destination_path)
    if not isinstance(duplicate, unreal.SkeletalMesh):
        raise RuntimeError(f"Could not create skeletal working copy: {destination_path}")
    unreal.EditorAssetLibrary.set_metadata_tag(duplicate, "PlayerSuitVersion", "24")
    unreal.EditorAssetLibrary.set_metadata_tag(duplicate, "PlayerSuitStatus", status)
    unreal.EditorAssetLibrary.set_metadata_tag(duplicate, "PlayerSuitIteration", "01")
    unreal.EditorAssetLibrary.set_metadata_tag(duplicate, "PlayerSuitRuntimeReady", "False")
    unreal.EditorAssetLibrary.set_metadata_tag(
        duplicate, "PlayerSuitPromotionGate", "FitSculptRebindMannyQuinnDeformationMultiplayer"
    )
    unreal.EditorAssetLibrary.save_loaded_asset(duplicate, only_if_is_dirty=False)
    return duplicate


def import_reference(name: str, source: Path) -> unreal.Texture2D:
    if not source.is_file():
        raise RuntimeError(f"Approved oversuit concept reference is missing: {source}")
    destination = REFERENCE_ROOT + "/Textures"
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = destination
    task.destination_name = f"T_REF_Oversuit_{name}"
    task.automated = True
    task.save = True
    task.replace_existing = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = asset(f"{destination}/T_REF_Oversuit_{name}", unreal.Texture2D)
    unreal.EditorAssetLibrary.set_metadata_tag(texture, "PlayerSuitReferenceAuthority", "V24Approved")
    unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    return texture


def make_reference_material(name: str, texture: unreal.Texture2D) -> unreal.Material:
    destination = REFERENCE_ROOT + "/Materials"
    path = f"{destination}/M_REF_Oversuit_{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        f"M_REF_Oversuit_{name}", destination, unreal.Material, unreal.MaterialFactoryNew()
    )
    material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    material.set_editor_property("two_sided", True)
    sample = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -300, 0
    )
    sample.set_editor_property("texture", texture)
    unreal.MaterialEditingLibrary.connect_material_property(
        sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR
    )
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def spawn_skeletal(mesh: unreal.SkeletalMesh, label: str, location, rotation_yaw=-90.0):
    actor = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
        unreal.SkeletalMeshActor,
        unreal.Vector(*location),
        unreal.Rotator(roll=0, pitch=0, yaw=rotation_yaw),
    )
    actor.set_actor_label(label)
    actor.skeletal_mesh_component.set_skinned_asset_and_update(mesh)
    actor.skeletal_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    return actor


def apply_role_material(actor: unreal.SkeletalMeshActor, mesh: unreal.SkeletalMesh, role: str) -> None:
    shared = {
        "SM_Helm": asset(REVIEW + "/Materials/MI_Shared_SM_Helm"),
        "SM_Gloves": asset(REVIEW + "/Materials/MI_Shared_SM_Gloves"),
        "SM_Boots": asset(REVIEW + "/Materials/MI_Shared_SM_Boots"),
        "SM_Bags": asset(REVIEW + "/Materials/MI_Shared_SM_Bags"),
        "SM_Pouch": asset(REVIEW + "/Materials/MI_Shared_SM_Pouch"),
        "MS_Visor": asset(REVIEW + "/Materials/M_SpaceMarshal_Visor"),
        "SM_Suit": asset(REVIEW + f"/Materials/{ROLE_MATERIALS[role]}"),
    }
    for index, skeletal_material in enumerate(mesh.get_editor_property("materials")):
        slot_name = str(skeletal_material.get_editor_property("material_slot_name"))
        if slot_name in shared:
            actor.skeletal_mesh_component.set_material(index, shared[slot_name])


def spawn_reference_board(name: str, material: unreal.Material, location, scale) -> None:
    plane = asset("/Engine/BasicShapes/Plane.Plane", unreal.StaticMesh)
    actor = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(roll=0, pitch=90, yaw=0)
    )
    actor.set_actor_label(f"REFERENCE_{name}")
    actor.static_mesh_component.set_static_mesh(plane)
    actor.static_mesh_component.set_material(0, material)
    actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    actor.set_actor_scale3d(unreal.Vector(*scale))


def build_workspace() -> dict:
    source_male = asset(MALE_DONOR, unreal.SkeletalMesh)
    source_female = asset(FEMALE_DONOR, unreal.SkeletalMesh)
    manny = asset(MANNY, unreal.SkeletalMesh)
    quinn = asset(QUINN, unreal.SkeletalMesh)

    role_meshes = {}
    for role in ROLE_MATERIALS:
        role_meshes[role] = duplicate_skeletal(
            MALE_DONOR, f"{ROLE_ROOT}/SKM_PrimaryOversuit_{role}_Work_I01", "SculptWorkingRole"
        )
    male_fit = duplicate_skeletal(
        MALE_DONOR, f"{FIT_ROOT}/SKM_PrimaryOversuit_MaleFit_Work_I01", "SculptWorkingBodyFit"
    )
    female_fit = duplicate_skeletal(
        FEMALE_DONOR, f"{FIT_ROOT}/SKM_PrimaryOversuit_FemaleFit_Work_I01", "SculptWorkingBodyFit"
    )

    reference_materials = {}
    for name, source in REFERENCES.items():
        reference_materials[name] = make_reference_material(name, import_reference(name, source))

    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        unreal.EditorAssetLibrary.delete_asset(MAP_PATH)
    if not level.new_level(MAP_PATH):
        raise RuntimeError(f"Could not create primary-oversuit sculpt map: {MAP_PATH}")

    role_positions = {"Crew": -270.0, "Engineering": -90.0, "Medical": 90.0, "Security": 270.0}
    for role, y in role_positions.items():
        actor = spawn_skeletal(role_meshes[role], f"WORKING_ROLE_{role}_I01", (0, y, 0))
        apply_role_material(actor, role_meshes[role], role)

    # Body-fit pairs are intentionally overlapped; toggle donor/mannequin actors in the
    # Outliner to inspect clearance without baking mannequin geometry into the garment.
    spawn_skeletal(male_fit, "WORKING_FIT_MaleDonor_I01", (-420, -85, 0))
    spawn_skeletal(manny, "FIT_REFERENCE_Manny", (-420, -85, 0), 0.0)
    spawn_skeletal(female_fit, "WORKING_FIT_FemaleDonor_I01", (-420, 85, 0))
    spawn_skeletal(quinn, "FIT_REFERENCE_Quinn", (-420, 85, 0), 0.0)

    board_specs = {
        "StandardTurnaround": ((-720, -360, 180), (3.2, 1.8, 1.0)),
        "RoleLineup": ((-720, 0, 180), (3.2, 1.8, 1.0)),
        "V24Target": ((-720, 360, 180), (3.2, 1.8, 1.0)),
        "SuitingArmory": ((-720, 720, 180), (3.2, 1.8, 1.0)),
    }
    for name, (location, scale) in board_specs.items():
        spawn_reference_board(name, reference_materials[name], location, scale)

    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    sun = actor_subsystem.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(300, -300, 500), unreal.Rotator(-32, -28, 0)
    )
    sun.set_actor_label("SCULPT_KeyLight")
    sun.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sun.light_component.set_editor_property("intensity", 1.0)
    sky = actor_subsystem.spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(0, 0, 300), unreal.Rotator()
    )
    sky.set_actor_label("SCULPT_FillLight")
    sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property("intensity", 0.25)

    for label, location, rotation, fov in (
        ("CAM_Sculpt_Front", (850, 0, 110), (0, 180, 0), 44.0),
        ("CAM_Sculpt_Profile", (0, -850, 110), (0, 90, 0), 44.0),
        ("CAM_Sculpt_ThreeQuarter", (650, -650, 145), (-5, 135, 0), 48.0),
    ):
        camera = actor_subsystem.spawn_actor_from_class(
            unreal.CameraActor,
            unreal.Vector(*location),
            unreal.Rotator(roll=rotation[2], pitch=rotation[0], yaw=rotation[1]),
        )
        camera.set_actor_label(label)
        camera.camera_component.set_editor_property("field_of_view", fov)

    level.save_current_level()
    unreal.EditorAssetLibrary.save_directory(ROOT, only_if_is_dirty=False, recursive=True)
    return {
        "version": 24,
        "status": "sculpt_workspace_not_runtime_promoted",
        "map": MAP_PATH,
        "working_root": WORKING,
        "roles": {role: mesh.get_path_name() for role, mesh in role_meshes.items()},
        "body_fits": {"male": male_fit.get_path_name(), "female": female_fit.get_path_name()},
        "fit_references": {"Manny": manny.get_path_name(), "Quinn": quinn.get_path_name()},
        "concept_references": {name: str(path) for name, path in REFERENCES.items()},
        "workflow": [
            "Keep V24Review SpaceMarshal donor assets immutable",
            "Edit only V24Sculpt Working Iteration_01 duplicates",
            "Use concept boards for silhouette and equipment-language authority",
            "Use future RealityScan mannequin capture only as fold and proportion reference",
            "Rebind approved role meshes to the common project Manny/Quinn skeleton",
            "Validate deformation and multiplayer equip before runtime promotion",
        ],
    }


result = build_workspace()
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log(f"Primary oversuit V24 sculpt workspace ready: {MAP_PATH}")
