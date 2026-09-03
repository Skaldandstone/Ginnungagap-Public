"""Validate the non-runtime V24 primary-oversuit Unreal sculpt workspace."""

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V24Sculpt"
MAP = ROOT + "/Maps/L_PrimaryOversuit_V24_Sculpt"
WORKING = ROOT + "/Working/Iteration_01"
REPORT = PROJECT / "Saved" / "Reports" / "PrimaryOversuitV24SculptValidation.json"
ROLES = ("Crew", "Engineering", "Medical", "Security")
SHARED_FIT_MORPH = "V24_SharedFit_I01"
CREW_MORPHS = (
    "V24_Crew_01_SilhouetteCleanup",
    "V24_Crew_02_HelmetCollar",
    "V24_Crew_03_EquipmentSettle",
    "V24_Crew_04_MobilityClearance",
)
CREW_MATERIAL = WORKING + "/Materials/MI_PrimaryOversuit_Crew_Work_I01"
CREW_PASS_REPORT = PROJECT / "Saved" / "Reports" / "PrimaryOversuitV24CrewFivePasses.json"
CREW_MODULE_REPORT = PROJECT / "Saved" / "Reports" / "PrimaryOversuitV24CrewModules.json"
CREW_MODULES = {
    "HarnessMonitor": WORKING + "/CrewModules/SM_Crew_HarnessMonitor_Work_I01",
    "SurveyToolMount": WORKING + "/CrewModules/SM_Crew_SurveyToolMount_Work_I01",
}
REQUIRED_EDITOR_PLUGINS = {
    "ModelingToolsEditorMode",
    "GeometryScripting",
    "SkeletalMeshModelingTools",
    "SkeletalMeshMorphTargetEditingTools",
}


def require_asset(path: str, expected_type):
    value = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(value, expected_type):
        raise RuntimeError(f"Missing or invalid V24 sculpt asset: {path}")
    return value


def validate() -> dict:
    role_meshes = {}
    for role in ROLES:
        path = f"{WORKING}/Roles/SKM_PrimaryOversuit_{role}_Work_I01"
        mesh = require_asset(path, unreal.SkeletalMesh)
        if unreal.EditorAssetLibrary.get_metadata_tag(mesh, "PlayerSuitRuntimeReady") != "False":
            raise RuntimeError(f"Role mesh lost its non-runtime promotion gate: {role}")
        if unreal.EditorAssetLibrary.get_metadata_tag(mesh, "PlayerSuitStatus") != "SculptWorkingRole":
            raise RuntimeError(f"Role mesh has an invalid workspace status: {role}")
        if SHARED_FIT_MORPH not in mesh.get_all_morph_target_names():
            raise RuntimeError(f"Role mesh is missing the shared-fit morph: {role}")
        if unreal.EditorAssetLibrary.get_metadata_tag(mesh, "PlayerSuitFitMorph") != SHARED_FIT_MORPH:
            raise RuntimeError(f"Role mesh is missing shared-fit metadata: {role}")
        morph_names = set(mesh.get_all_morph_target_names())
        if role == "Crew":
            missing_crew_morphs = sorted(set(CREW_MORPHS).difference(morph_names))
            if missing_crew_morphs:
                raise RuntimeError(f"Crew is missing refinement morphs: {missing_crew_morphs}")
        else:
            leaked_crew_morphs = sorted(set(CREW_MORPHS).intersection(morph_names))
            if leaked_crew_morphs:
                raise RuntimeError(f"Crew refinement leaked onto {role}: {leaked_crew_morphs}")
        role_meshes[role] = mesh

    body_fits = {}
    for name in ("MaleFit", "FemaleFit"):
        mesh = require_asset(
            f"{WORKING}/BodyFits/SKM_PrimaryOversuit_{name}_Work_I01", unreal.SkeletalMesh
        )
        if unreal.EditorAssetLibrary.get_metadata_tag(mesh, "PlayerSuitRuntimeReady") != "False":
            raise RuntimeError(f"Body-fit mesh lost its non-runtime promotion gate: {name}")
        body_fits[name] = mesh
    if SHARED_FIT_MORPH not in body_fits["MaleFit"].get_all_morph_target_names():
        raise RuntimeError("Male body-fit mesh is missing the shared-fit morph")
    if SHARED_FIT_MORPH in body_fits["FemaleFit"].get_all_morph_target_names():
        raise RuntimeError("Male shared-fit morph was incorrectly copied to female topology")

    project_descriptor = json.loads((PROJECT / "Ginnungagap.uproject").read_text(encoding="utf-8"))
    enabled_plugins = {
        plugin["Name"] for plugin in project_descriptor.get("Plugins", []) if plugin.get("Enabled")
    }
    missing_plugins = sorted(REQUIRED_EDITOR_PLUGINS.difference(enabled_plugins))
    if missing_plugins:
        raise RuntimeError(f"V24 sculpt editor plugins are not enabled: {missing_plugins}")

    for name in ("StandardTurnaround", "RoleLineup", "SuitingArmory", "V24Target"):
        require_asset(f"{ROOT}/References/Textures/T_REF_Oversuit_{name}", unreal.Texture2D)
        require_asset(f"{ROOT}/References/Materials/M_REF_Oversuit_{name}", unreal.Material)

    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    labels = {actor.get_actor_label() for actor in actors}
    required_labels = {
        *(f"WORKING_ROLE_{role}_I01" for role in ROLES),
        "WORKING_FIT_MaleDonor_I01",
        "WORKING_FIT_FemaleDonor_I01",
        "FIT_REFERENCE_Manny",
        "FIT_REFERENCE_Quinn",
        "REFERENCE_StandardTurnaround",
        "REFERENCE_RoleLineup",
        "REFERENCE_SuitingArmory",
        "REFERENCE_V24Target",
        "CAM_Sculpt_Front",
        "CAM_Sculpt_Profile",
        "CAM_Sculpt_ThreeQuarter",
        "WORKING_CREW_HarnessMonitor_I01",
        "WORKING_CREW_SurveyToolMount_I01",
        "CAM_Crew_Modules_Closeup",
    }
    missing = sorted(required_labels.difference(labels))
    if missing:
        raise RuntimeError(f"V24 sculpt map is missing actors: {missing}")

    skeletons = {
        role: mesh.get_editor_property("skeleton").get_path_name()
        for role, mesh in role_meshes.items()
    }
    project_skeleton = require_asset(
        "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple", unreal.SkeletalMesh
    ).get_editor_property("skeleton").get_path_name()
    if any(skeleton == project_skeleton for skeleton in skeletons.values()):
        raise RuntimeError("A sculpt-working donor was incorrectly marked as project-skeleton rebound")

    if unreal.EditorAssetLibrary.get_metadata_tag(
        role_meshes["Crew"], "PlayerSuitRoleSculptStatus"
    ) != "CrewPass07ModuleReview":
        raise RuntimeError("Crew was not advanced through the authored-module review gate")
    if unreal.EditorAssetLibrary.get_metadata_tag(
        role_meshes["Crew"], "PlayerSuitCrewPassCount"
    ) != "7":
        raise RuntimeError("Crew seven-pass ledger metadata is missing")

    crew_modules = {}
    for module_type, path in CREW_MODULES.items():
        module = require_asset(path, unreal.StaticMesh)
        if unreal.EditorAssetLibrary.get_metadata_tag(module, "PlayerSuitRole") != "Crew":
            raise RuntimeError(f"Crew module has invalid role metadata: {module_type}")
        if unreal.EditorAssetLibrary.get_metadata_tag(module, "PlayerSuitModuleType") != module_type:
            raise RuntimeError(f"Crew module has invalid type metadata: {module_type}")
        if unreal.EditorAssetLibrary.get_metadata_tag(module, "PlayerSuitSource") != "FabSpaceMarshalDonorGeometry":
            raise RuntimeError(f"Crew module lost donor-geometry provenance: {module_type}")
        if unreal.EditorAssetLibrary.get_metadata_tag(module, "PlayerSuitAIGenerationUsed") != "False":
            raise RuntimeError(f"Crew module has an invalid AI-use provenance gate: {module_type}")
        if unreal.EditorAssetLibrary.get_metadata_tag(module, "PlayerSuitRuntimeReady") != "False":
            raise RuntimeError(f"Crew module was incorrectly promoted to runtime: {module_type}")
        crew_modules[module_type] = module

    crew_material = require_asset(CREW_MATERIAL, unreal.MaterialInstanceConstant)
    crew_suit_materials = {
        str(material.material_slot_name): material.material_interface
        for material in role_meshes["Crew"].get_editor_property("materials")
    }
    if crew_suit_materials.get("SM_Suit") != crew_material:
        raise RuntimeError("Crew working material is not assigned to the SM_Suit slot")

    if not CREW_PASS_REPORT.is_file():
        raise RuntimeError("Crew five-pass report is missing")
    crew_pass_report = json.loads(CREW_PASS_REPORT.read_text(encoding="utf-8"))
    if not crew_pass_report.get("topology_preserved"):
        raise RuntimeError("Crew five-pass report did not preserve topology")
    mobility = crew_pass_report["geometry_passes"]["V24_Crew_04_MobilityClearance"]
    if mobility["maximum_displacement_cm"] > 1.0:
        raise RuntimeError("Crew mobility-clearance mask exceeded the 1 cm safety envelope")

    if not CREW_MODULE_REPORT.is_file():
        raise RuntimeError("Crew authored-module report is missing")
    crew_module_report = json.loads(CREW_MODULE_REPORT.read_text(encoding="utf-8"))
    if crew_module_report.get("module_count") != 2:
        raise RuntimeError("Crew authored-module report has the wrong module count")
    if not crew_module_report.get("donor_geometry_only"):
        raise RuntimeError("Crew modules were not certified as donor geometry only")
    if crew_module_report.get("ai_generation_used"):
        raise RuntimeError("Crew donor assets were incorrectly marked as AI generated")
    if any(
        not module.get("authored_topology_preserved")
        for module in crew_module_report.get("modules", {}).values()
    ):
        raise RuntimeError("A Crew module failed the authored-topology preservation gate")

    return {
        "status": "passed_crew_seven_pass_module_workspace_not_runtime_promoted",
        "map": MAP,
        "role_count": len(role_meshes),
        "required_actor_count": len(required_labels),
        "role_skeletons": skeletons,
        "project_skeleton": project_skeleton,
        "shared_fit_morph": SHARED_FIT_MORPH,
        "shared_fit_targets": ["MaleFit", *ROLES],
        "female_fit_separate_topology": True,
        "crew_sculpt_status": "CrewPass07ModuleReview",
        "crew_refinement_morphs": list(CREW_MORPHS),
        "crew_material": crew_material.get_path_name(),
        "crew_pass_count": 7,
        "crew_modules": {
            module_type: module.get_path_name()
            for module_type, module in crew_modules.items()
        },
        "crew_module_preview_actors": [
            "WORKING_CREW_HarnessMonitor_I01",
            "WORKING_CREW_SurveyToolMount_I01",
        ],
        "crew_module_donor_geometry_only": True,
        "crew_module_ai_generation_used": False,
        "crew_mobility_max_displacement_cm": mobility["maximum_displacement_cm"],
        "crew_refinement_isolated_from_other_roles": True,
        "required_editor_plugins": sorted(REQUIRED_EDITOR_PLUGINS),
        "promotion_gate_preserved": True,
    }


result = validate()
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(result, indent=2), encoding="utf-8")
unreal.log("Primary oversuit V24 sculpt workspace validation passed")
