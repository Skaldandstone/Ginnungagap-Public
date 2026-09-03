"""Inspect the assembled MetaHuman Blueprint's runtime component hierarchy."""

import json
from pathlib import Path

import unreal


blueprint_path = "/Game/Characters/MetaHumans/Assembled/PlayerFace01/BP_PlayerFace01.BP_PlayerFace01"
blueprint = unreal.load_asset(blueprint_path)
report = {"schema": 1, "status": "fail", "blueprint": blueprint_path, "components": []}
actor = None
driver_actor = None

try:
    if not isinstance(blueprint, unreal.Blueprint) or not blueprint.generated_class():
        raise RuntimeError("MetaHuman Blueprint or generated class is unavailable")
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        blueprint.generated_class(), unreal.Vector(0.0, 0.0, 0.0)
    )
    if not actor:
        raise RuntimeError("Unable to spawn assembled MetaHuman")

    for component in actor.get_components_by_class(unreal.ActorComponent):
        item = {
            "name": component.get_name(),
            "class": component.get_class().get_name(),
        }
        if isinstance(component, unreal.SceneComponent):
            parent = component.get_attach_parent()
            item["parent"] = parent.get_name() if parent else None
            transform = component.get_relative_transform()
            location = transform.translation
            rotation = transform.rotation.rotator()
            scale = transform.scale3d
            item["relative_location"] = [location.x, location.y, location.z]
            item["relative_rotation"] = [rotation.pitch, rotation.yaw, rotation.roll]
            item["relative_scale"] = [scale.x, scale.y, scale.z]
        if isinstance(component, unreal.SkeletalMeshComponent):
            mesh = component.skeletal_mesh
            item["skeletal_mesh"] = mesh.get_path_name() if mesh else None
            item["skeleton"] = mesh.skeleton.get_path_name() if mesh and mesh.skeleton else None
            anim_class = component.anim_class
            item["anim_class"] = anim_class.get_path_name() if anim_class else None
        report["components"].append(item)
    body = next(
        component
        for component in actor.get_components_by_class(unreal.SkeletalMeshComponent)
        if component.get_name() == "Body"
    )
    manny = unreal.load_asset("/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple.SKM_Manny_Simple")
    report["skeleton_api"] = sorted(
        name for name in dir(body.skeletal_mesh.skeleton)
        if "compat" in name.lower() or "bone" in name.lower() or "reference" in name.lower()
    )
    if manny and manny.skeleton:
        compatibility_method = getattr(body.skeletal_mesh.skeleton, "is_compatible_for_editor", None)
        report["manny_skeleton"] = manny.skeleton.get_path_name()
        report["manny_compatible"] = (
            bool(compatibility_method(manny.skeleton)) if compatibility_method else None
        )
        driver_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.SkeletalMeshActor, unreal.Vector(200.0, 0.0, 0.0)
        )
        driver = driver_actor.skeletal_mesh_component
        driver.set_skeletal_mesh(manny)
        body_bones = [str(body.get_bone_name(index)) for index in range(body.get_num_bones())]
        driver_bones = [str(driver.get_bone_name(index)) for index in range(driver.get_num_bones())]
        report["body_bone_count"] = len(body_bones)
        report["manny_bone_count"] = len(driver_bones)
        report["matching_bone_names"] = len(set(body_bones).intersection(driver_bones))
        report["matching_bone_indices"] = sum(
            left == right for left, right in zip(body_bones, driver_bones)
        )
        report["first_index_mismatches"] = [
            {"index": index, "metahuman": left, "manny": right}
            for index, (left, right) in enumerate(zip(body_bones, driver_bones))
            if left != right
        ][:12]
    report["status"] = "pass"
finally:
    if driver_actor:
        unreal.EditorLevelLibrary.destroy_actor(driver_actor)
    if actor:
        unreal.EditorLevelLibrary.destroy_actor(actor)

path = Path(unreal.Paths.project_saved_dir()) / "MetaHumanRuntimeInspection.json"
path.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"METAHUMAN_RUNTIME_INSPECTION {json.dumps(report, separators=(',', ':'))}")
unreal.SystemLibrary.quit_editor()
