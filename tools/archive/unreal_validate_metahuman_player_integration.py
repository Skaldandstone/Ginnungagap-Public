"""Validate MetaHuman selection, animation bridge, and creator layer isolation."""

import json
from pathlib import Path

import unreal


report = {"schema": 1, "status": "fail", "checks": {}}
character = None

try:
    character = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.CoopSurvivalCharacter, unreal.Vector(0.0, 0.0, 0.0)
    )
    if not character:
        raise RuntimeError("Unable to spawn CoopSurvivalCharacter")

    character.set_character_creator_preview_mode(True)
    profile = unreal.CharacterProfile()
    profile.face_preset = unreal.CharacterFacePreset.FACE01
    profile.hair_style = unreal.CharacterHairStyle.SHORT
    character.apply_character_identity(profile)

    visual = character.get_meta_human_visual_actor()
    report["checks"]["face01_visual_spawned"] = visual is not None
    report["face01_visual_class"] = visual.get_class().get_name() if visual else None

    driver = next(
        component for component in character.get_components_by_class(unreal.SkeletalMeshComponent)
        if component.get_name() == "CharacterMesh0"
    )
    report["checks"]["driver_hidden"] = not driver.is_visible()
    cryo = next(
        (component for component in character.get_components_by_class(unreal.SkeletalMeshComponent)
         if component.get_name() == "CryoBodysuitMesh"), None
    )

    body = None
    outfit = None
    hair = None
    if visual:
        for component in visual.get_components_by_class(unreal.ActorComponent):
            if component.get_name() == "Body":
                body = component
            elif component.get_name() == "SkeletalMesh":
                outfit = component
            elif component.get_name() == "Hair":
                hair = component

    anim_instance = body.get_anim_instance() if body else None
    report["body_materials"] = [
        body.get_material(index).get_path_name() if body.get_material(index) else None
        for index in range(body.get_num_materials())
    ] if body else []
    report["outfit_materials"] = [
        outfit.get_material(index).get_path_name() if outfit.get_material(index) else None
        for index in range(outfit.get_num_materials())
    ] if outfit else []
    report["checks"]["copy_pose_installed"] = (
        anim_instance is not None
        and anim_instance.get_class().get_name() == "MetaHumanCopyPoseAnimInstance"
    )
    report["cryo_materials"] = [
        cryo.get_material(index).get_path_name() if cryo.get_material(index) else None
        for index in range(cryo.get_num_materials())
    ] if cryo else []
    if cryo and cryo.get_skeletal_mesh_asset():
        bounds = cryo.get_skeletal_mesh_asset().get_bounds()
        report["cryo_bounds"] = {
            "origin": [bounds.origin.x, bounds.origin.y, bounds.origin.z],
            "extent": [bounds.box_extent.x, bounds.box_extent.y, bounds.box_extent.z],
        }
        location = cryo.get_editor_property("relative_location")
        scale = cryo.get_editor_property("relative_scale3d")
        report["cryo_component_transform"] = {
            "relative_location": [location.x, location.y, location.z],
            "scale": [scale.x, scale.y, scale.z],
        }
    report["checks"]["authored_cryo_bodysuit_visible"] = (
        cryo is not None
        and cryo.is_visible()
        and cryo.get_skeletal_mesh_asset() is not None
        and cryo.get_skeletal_mesh_asset().get_name() == "SK_CryoBodysuit_V32_Manny"
        and bool(report["cryo_materials"])
        and all("MI_MH_CryoBodysuit_Standard" in path for path in report["cryo_materials"] if path)
    )
    report["checks"]["cryo_leader_pose_compatible"] = (
        cryo is not None
        and cryo.get_skeletal_mesh_asset() is not None
        and driver.get_skeletal_mesh_asset() is not None
        and cryo.get_skeletal_mesh_asset().get_editor_property("skeleton")
        == driver.get_skeletal_mesh_asset().get_editor_property("skeleton")
    )
    report["checks"]["placeholder_garment_suppressed"] = (
        outfit is not None
        and outfit.get_attach_parent() == body
        and not outfit.is_visible()
    )
    report["checks"]["short_hair_visible"] = hair is not None and hair.is_visible()
    report["checks"]["metahuman_body_hidden"] = body is not None and not body.is_visible()

    pressure_names = {
        "HelmetShell", "HelmetVisor", "PressureCollar", "ChestPlate", "LifeSupportPack",
        "ChestControlUnit", "LeftShoulder", "RightShoulder", "LeftKneePad", "RightKneePad",
    }
    pressure_components = [
        component for component in character.get_components_by_class(unreal.PrimitiveComponent)
        if component.get_name() in pressure_names
    ]
    report["checks"]["creator_suit_layers_hidden"] = (
        bool(pressure_components) and all(not component.is_visible() for component in pressure_components)
    )

    profile.hair_style = unreal.CharacterHairStyle.SHAVED
    character.apply_character_identity(profile)
    shaved_visual = character.get_meta_human_visual_actor()
    shaved_hair = next(
        (component for component in shaved_visual.get_components_by_class(unreal.PrimitiveComponent)
         if component.get_name() == "Hair"), None
    ) if shaved_visual else None
    report["checks"]["shaved_hair_hidden"] = shaved_hair is not None and not shaved_hair.is_visible()

    profile.face_preset = unreal.CharacterFacePreset.FACE02
    character.apply_character_identity(profile)
    report["checks"]["unassembled_face_falls_back"] = (
        character.get_meta_human_visual_actor() is None and driver.is_visible()
    )

    report["status"] = "pass" if all(report["checks"].values()) else "fail"
finally:
    if character:
        unreal.EditorLevelLibrary.destroy_actor(character)

path = Path(unreal.Paths.project_saved_dir()) / "MetaHumanPlayerIntegrationValidation.json"
path.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"METAHUMAN_PLAYER_INTEGRATION {json.dumps(report, separators=(',', ':'))}")
unreal.SystemLibrary.quit_editor()
