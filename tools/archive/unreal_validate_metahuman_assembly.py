"""Validate the assembled gameplay MetaHuman and its critical runtime assets."""

import json
from pathlib import Path

import unreal


root = "/Game/Characters/MetaHumans/Assembled/PlayerFace01"
required = {
    "blueprint": f"{root}/BP_PlayerFace01.BP_PlayerFace01",
    "face_mesh": f"{root}/Face/SKM_MHC_Face01_Ada_FaceMesh.SKM_MHC_Face01_Ada_FaceMesh",
    "body_mesh": f"{root}/Body/SKM_MHC_Face01_Ada_BodyMesh.SKM_MHC_Face01_Ada_BodyMesh",
    "face_dna": f"{root}/Face/SKM_MHC_Face01_Ada_FaceMesh_DNA.SKM_MHC_Face01_Ada_FaceMesh_DNA",
    "body_dna": f"{root}/Body/SKM_MHC_Face01_Ada_BodyMesh_DNA.SKM_MHC_Face01_Ada_BodyMesh_DNA",
    "common_live_link": "/Game/Characters/MetaHumans/Common/Animation/ABP_MH_LiveLink.ABP_MH_LiveLink",
    "common_face_anim": "/Game/Characters/MetaHumans/Common/Face/ABP_Face.ABP_Face",
    "common_facial_hair_material": "/Game/Characters/MetaHumans/Common/Materials/MI_Facial_Hair.MI_Facial_Hair",
}

loaded = {name: unreal.load_asset(path) for name, path in required.items()}
assets = sorted(unreal.EditorAssetLibrary.list_assets(root, recursive=True, include_folder=False))
checks = {
    "blueprint": isinstance(loaded["blueprint"], unreal.Blueprint),
    "blueprint_generated_class": bool(loaded["blueprint"] and loaded["blueprint"].generated_class()),
    "face_mesh": isinstance(loaded["face_mesh"], unreal.SkeletalMesh),
    "body_mesh": isinstance(loaded["body_mesh"], unreal.SkeletalMesh),
    "face_dna": loaded["face_dna"] is not None,
    "body_dna": loaded["body_dna"] is not None,
    "common_live_link": loaded["common_live_link"] is not None,
    "common_face_anim": loaded["common_face_anim"] is not None,
    "common_facial_hair_material": loaded["common_facial_hair_material"] is not None,
    "production_asset_count": len(assets) >= 80,
}
report = {
    "schema": 1,
    "status": "pass" if all(checks.values()) else "fail",
    "root": root,
    "asset_count": len(assets),
    "checks": checks,
}
report_path = Path(unreal.Paths.project_saved_dir()) / "MetaHumanAssemblyValidation.json"
report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"METAHUMAN_ASSEMBLY_VALIDATION {json.dumps(report, separators=(',', ':'))}")
unreal.SystemLibrary.quit_editor()
