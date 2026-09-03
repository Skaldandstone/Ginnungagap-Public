"""Promote the restrained concept-matching suit modules into V25 Iteration 02."""

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
SOURCE_ROOT = "/Game/Characters/Player/Suit/Packaged/Variants/Crew"
TARGET_ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt/Working/Iteration_02_ConceptSilhouette"
REPORT = PROJECT / "Saved/Reports/PrimaryOversuitV25ConceptModules.json"

MODULES = [
    "CREW_HelmetShell",
    "CREW_Visor",
    "CREW_VisorGasket",
    "CREW_PressureCollar",
    "CREW_CONCEPT_HelmetBrowRing",
    "CREW_CONCEPT_HelmetCrownRail",
    "CREW_ChestPlate",
    "CREW_CONCEPT_ChestComputerBezel",
    "CREW_CONCEPT_ChestComputerScreen",
    "CREW_LifeSupportPack",
    "CREW_CONCEPT_BackpackFrame",
    "CREW_CONCEPT_BackpackServicePanel",
    "CREW_Forearm_L",
    "CREW_Forearm_R",
    "CREW_ForearmComputer",
    "CREW_Knee_L",
    "CREW_Knee_R",
    "CREW_Boot_L",
    "CREW_Boot_R",
]

created = []
for name in MODULES:
    source_path = f"{SOURCE_ROOT}/{name}"
    target_path = f"{TARGET_ROOT}/{name.replace('CREW_', 'V25_')}"
    source = unreal.EditorAssetLibrary.load_asset(source_path)
    if not isinstance(source, unreal.StaticMesh):
        raise RuntimeError(f"Missing concept module: {source_path}")
    if unreal.EditorAssetLibrary.does_asset_exist(target_path):
        asset = unreal.EditorAssetLibrary.load_asset(target_path)
    else:
        asset = unreal.EditorAssetLibrary.duplicate_asset(source_path, target_path)
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError(f"Could not create V25 module: {target_path}")
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.AssetRole", "PrimaryOversuitConceptModule")
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.Iteration", "V25.I02")
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.IndependentWearable", "true")
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "Ginnungagap.ReferenceMethod", "front_profile_rear_concept_projection")
    unreal.EditorAssetLibrary.save_loaded_asset(asset, only_if_is_dirty=False)
    bounds = asset.get_bounds()
    created.append({
        "asset": asset.get_path_name(),
        "origin": [bounds.origin.x, bounds.origin.y, bounds.origin.z],
        "extent": [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z],
    })

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "concept_modules_promoted",
    "iteration": "V25.I02",
    "module_count": len(created),
    "modules": created,
    "design_intent": [
        "large clear bubble helmet with layered pressure collar",
        "compact rectangular back-mounted life support",
        "central chest computer with soft harness transition",
        "restrained forearm, knee, and boot hard points",
    ],
    "runtime_ready": False,
}, indent=2), encoding="utf-8")
unreal.log(f"V25 I02 concept modules created: {len(created)}")
