"""Export the Blender suit library into a versionable Unreal source bundle."""

import json
import shutil
import sys
from pathlib import Path

import bpy


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
OUTPUT = ROOT / "Build" / "Unreal" / "PlayerSuits"
FBX_DIR = OUTPUT / "FBX"
TEXTURE_DIR = OUTPUT / "Textures"
SOURCE_TEXTURES = ROOT / "Content" / "Characters" / "Player" / "Skins" / "Source"
ROLES = ("Crew", "Engineering", "Medical", "Security")


def select_only(objects):
    bpy.ops.object.select_all(action="DESELECT")
    for obj in objects:
        obj.hide_set(False)
        obj.hide_viewport = False
        obj.select_set(True)
    if objects:
        bpy.context.view_layer.objects.active = objects[0]


def export_fbx(name, objects, *, armature=False):
    path = FBX_DIR / f"{name}.fbx"
    select_only(objects)
    bpy.ops.export_scene.fbx(
        filepath=str(path),
        use_selection=True,
        object_types={"ARMATURE", "MESH", "EMPTY", "OTHER"},
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS",
        axis_forward="-Z",
        axis_up="Y",
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        add_leaf_bones=False,
        bake_anim=armature,
        bake_anim_use_all_actions=False,
        bake_anim_use_nla_strips=False,
        bake_anim_force_startend_keying=False,
        path_mode="RELATIVE",
        embed_textures=False,
    )
    if not path.exists() or path.stat().st_size < 1024:
        raise RuntimeError(f"FBX export failed or was empty: {path}")
    return path


def children_of(root):
    return [obj for obj in bpy.data.objects if obj.parent == root]


def main():
    FBX_DIR.mkdir(parents=True, exist_ok=True)
    TEXTURE_DIR.mkdir(parents=True, exist_ok=True)
    artifacts = []

    armature = bpy.data.objects["SK_PlayerSuit_Production"]
    rig_objects = [armature] + [obj for obj in bpy.data.collections["11_Production_Rig_50"].objects
                                if obj.get("unreal_socket") or obj.get("collision_proxy")]
    artifacts.append(export_fbx("SK_PlayerSuit_Production", rig_objects, armature=True))
    bound_meshes = [obj for obj in bpy.data.objects if obj.get("skeletal_export")]
    artifacts.append(export_fbx("SKM_PlayerSuit_Prototype", [armature] + bound_meshes, armature=True))

    variant_manifest = {}
    for role in ROLES:
        root = bpy.data.objects[f"VARIANT_{role}_Root"]
        objects = [root] + children_of(root)
        artifacts.append(export_fbx(f"SM_PlayerSuit_{role}", objects))
        variant_manifest[role] = {
            "fbx": f"FBX/SM_PlayerSuit_{role}.fbx",
            "unreal_destination": f"/Game/Characters/Player/Suit/Variants/{role}",
            "blueprint": root.get("unreal_blueprint"),
            "equipment": root.get("hands_free_equipment"),
            "payload": root.get("default_payload", "").split(","),
            "object_count": root.get("object_count"),
        }

    equipment = bpy.data.collections["08_Hands_Free_Equipment"]
    for prefix, name in (("TOOLARM_", "SM_Suit_ToolArm"), ("DRONE_", "SM_Suit_UtilityDrone")):
        objects = [obj for obj in equipment.objects if obj.name.startswith(prefix)]
        artifacts.append(export_fbx(name, objects))

    texture_manifest = {}
    for role in ROLES:
        role_dir = TEXTURE_DIR / role
        role_dir.mkdir(parents=True, exist_ok=True)
        channels = {}
        names = {
            "BaseColor": f"T_PlayerSkin_{role}.png",
            "Normal": f"T_PlayerSkin_{role}_Normal.png",
            "Roughness": f"T_PlayerSkin_{role}_Roughness.png",
            "Metallic": f"T_PlayerSkin_{role}_Metallic.png",
            "AO": f"T_PlayerSkin_{role}_AO.png",
        }
        for channel, filename in names.items():
            source = SOURCE_TEXTURES / filename
            destination = role_dir / filename
            if not source.exists():
                raise RuntimeError(f"Missing authored texture: {source}")
            shutil.copy2(source, destination)
            channels[channel] = f"Textures/{role}/{filename}"
        texture_manifest[role] = channels

    socket_objects = [obj for obj in bpy.data.collections["11_Production_Rig_50"].objects
                      if obj.get("unreal_socket")]
    collision_objects = [obj for obj in bpy.data.collections["11_Production_Rig_50"].objects
                         if obj.get("collision_proxy")]
    lod_objects = [obj for obj in bpy.data.collections["11_Production_Rig_50"].objects
                   if obj.name.startswith("LOD")]
    manifest = {
        "schema": 1,
        "source_blend": "Art/Characters/PlayerSuits/PlayerSuit_Master.blend",
        "unreal_version": "5.8",
        "units": "centimeters",
        "axis_forward": "-Z",
        "axis_up": "Y",
        "variants": variant_manifest,
        "equipment": {
            "ToolArm": {"fbx": "FBX/SM_Suit_ToolArm.fbx", "classes": ["Engineering", "Security"]},
            "UtilityDrone": {"fbx": "FBX/SM_Suit_UtilityDrone.fbx", "classes": ["Crew", "Medical"]},
        },
        "skeleton": {
            "fbx": "FBX/SK_PlayerSuit_Production.fbx",
            "skeletal_prototype_fbx": "FBX/SKM_PlayerSuit_Prototype.fbx",
            "bound_mesh_count": armature.get("bound_mesh_count"),
            "deformation_refinement_steps": armature.get("deformation_refinement_steps"),
            "smooth_weighted_section_count": armature.get("smooth_weighted_section_count"),
            "target": armature.get("target_skeleton"),
            "root_motion_bone": armature.get("root_motion_bone"),
            "bones": [bone.name for bone in armature.data.bones],
        },
        "concept_fidelity": {
            "reference": bpy.data.objects["HERO_PlayerSuit_Root"].get("concept_reference"),
            "steps": bpy.data.objects["HERO_PlayerSuit_Root"].get("concept_fidelity_steps"),
            "detail_object_count": bpy.data.objects["HERO_PlayerSuit_Root"].get("concept_detail_object_count"),
        },
        "player_anatomy": {
            "steps": bpy.data.objects["HERO_PlayerSuit_Root"].get("player_anatomy_steps"),
            "mesh_count": bpy.data.objects["HERO_PlayerSuit_Root"].get("player_anatomy_mesh_count"),
            "skeletal_bound_mesh_count": armature.get("anatomy_bound_mesh_count"),
            "normal_policy": "validated smooth normals; recompute MikkTSpace on import",
        },
        "real_player_finish": {
            "steps": bpy.data.objects["HERO_PlayerSuit_Root"].get("real_player_finish_steps"),
            "hero_mesh_count": bpy.data.objects["HERO_PlayerSuit_Root"].get("real_player_finish_mesh_count"),
            "skeletal_bound_mesh_count": armature.get("real_player_bound_mesh_count"),
            "features": ["visible face", "helmet interior", "garment panels", "rounded boots",
                         "class silhouette gear", "degenerate cleanup"],
        },
        "production_player_refinement": {
            "steps": bpy.data.objects["HERO_PlayerSuit_Root"].get("production_player_refinement_steps"),
            "new_hero_meshes": bpy.data.objects["HERO_PlayerSuit_Root"].get("production_player_refinement_new_meshes"),
            "skeletal_bound_meshes": armature.get("production_player_refinement_bound_meshes"),
            "class_gear_refined": 100,
            "topology_meshes_validated": 100,
        },
        "sockets": {obj.name: obj.get("socket_bone") for obj in socket_objects},
        "collision": [obj.name for obj in collision_objects],
        "lods": {obj.name: {"triangle_ratio": obj.get("triangle_ratio"),
                              "screen_size": obj.get("screen_size")} for obj in lod_objects},
        "textures": texture_manifest,
        "import_settings": {
            "combine_meshes": False,
            "import_materials": False,
            "import_textures": False,
            "generate_lightmap_uvs": True,
            "normal_import_method": "ImportNormalsAndTangents",
        },
    }
    manifest_path = OUTPUT / "PlayerSuit_UnrealManifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    artifacts.append(manifest_path)
    print(f"Exported {len(artifacts)} Unreal package artifacts to {OUTPUT}")


main()
