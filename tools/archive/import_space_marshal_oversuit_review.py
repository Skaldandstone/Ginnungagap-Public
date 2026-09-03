"""Import garment-only Space Marshal donor suits into an isolated Unreal review area.

The purchased source files stay under ignored Intermediate/Fab. This script imports
only prepared garment FBXs and the PBR maps needed for an in-engine class lineup.
It does not promote either donor skeleton to the runtime player-suit contract.
"""

from __future__ import annotations

from pathlib import Path

import unreal


PROJECT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = PROJECT / "Intermediate" / "Fab" / "SpaceMarshal"
PREPARED = SOURCE / "Prepared"
TEXTURES = SOURCE / "Male" / "Textures"
ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V24Review/SpaceMarshal"
MESH_ROOT = ROOT + "/Meshes"
TEXTURE_ROOT = ROOT + "/Textures"
MATERIAL_ROOT = ROOT + "/Materials"
MAP_PATH = ROOT + "/L_SpaceMarshal_ClassLineup"

ROLE_SUIT_TEXTURE = {
    "Crew": "SM_Suit_Var01_BaseColor",
    "Engineering": "SM_Suit_Var03_BaseColor",
    "Medical": "SM_Suit_BaseColor",
    "Security": "SM_Suit_Var02_BaseColor",
}
ROLE_TINT = {
    "Crew": unreal.LinearColor(0.08, 0.25, 0.78, 1.0),
    "Engineering": unreal.LinearColor(0.95, 0.30, 0.035, 1.0),
    "Medical": unreal.LinearColor(0.62, 0.84, 0.84, 1.0),
    "Security": unreal.LinearColor(0.92, 0.035, 0.025, 1.0),
}
GARMENT_SLOTS = ("SM_Suit", "SM_Helm", "SM_Gloves", "SM_Boots", "SM_Bags", "SM_Pouch")
SHARED_SLOTS = ("SM_Helm", "SM_Gloves", "SM_Boots", "SM_Bags", "SM_Pouch")


def import_skeletal_mesh(source: Path) -> str:
    if not source.is_file():
        raise RuntimeError(f"Prepared garment FBX is missing: {source}")
    task = unreal.AssetImportTask()
    task.filename = str(source)
    task.destination_path = MESH_ROOT
    task.destination_name = source.stem
    task.automated = True
    task.save = True
    task.replace_existing = True
    task.replace_existing_settings = False
    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = True
    options.import_animations = False
    options.import_materials = False
    options.import_textures = False
    options.create_physics_asset = False
    options.skeletal_mesh_import_data.normal_import_method = (
        unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    )
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    meshes = [
        path for path in task.imported_object_paths
        if isinstance(unreal.EditorAssetLibrary.load_asset(path), unreal.SkeletalMesh)
    ]
    if not meshes:
        meshes = [path for path in task.imported_object_paths if path.rsplit(".", 1)[-1] == source.stem]
    if not meshes:
        raise RuntimeError(f"Unreal did not import a skeletal mesh from {source.name}: {task.imported_object_paths}")
    mesh_path = meshes[0]
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    unreal.EditorAssetLibrary.set_metadata_tag(mesh, "PlayerSuitStatus", "ReviewOnlyDonor")
    unreal.EditorAssetLibrary.set_metadata_tag(mesh, "PlayerSuitSource", "FabSpaceMarshal")
    unreal.EditorAssetLibrary.set_metadata_tag(mesh, "PlayerSuitPromotionGate", "RebindToProjectMannyQuinnSkeleton")
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    return mesh_path


def required_texture_names() -> list[str]:
    names = {
        "SM_Suit_BaseColor",
        "SM_Suit_Var01_BaseColor",
        "SM_Suit_Var02_BaseColor",
        "SM_Suit_Var03_BaseColor",
        "SM_Suit_Normal",
        "SM_Suit_ORM",
        "MS_Visor_BaseColor",
        "MS_Visor_Normal",
        "MS_Visor_ORM",
    }
    for slot in SHARED_SLOTS:
        names.update((f"{slot}_BaseColor", f"{slot}_Normal", f"{slot}_ORM"))
    return sorted(names)


def import_textures() -> dict[str, unreal.Texture2D]:
    tasks = []
    for name in required_texture_names():
        source = TEXTURES / f"{name}.png"
        if not source.is_file():
            raise RuntimeError(f"Required Space Marshal texture is missing: {source}")
        task = unreal.AssetImportTask()
        task.filename = str(source)
        task.destination_path = TEXTURE_ROOT
        task.destination_name = name
        task.automated = True
        task.save = True
        task.replace_existing = True
        tasks.append(task)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks(tasks)

    imported = {}
    for name in required_texture_names():
        texture = unreal.EditorAssetLibrary.load_asset(f"{TEXTURE_ROOT}/{name}")
        if not texture:
            raise RuntimeError(f"Imported texture could not be loaded: {name}")
        if name.endswith("_Normal"):
            texture.set_editor_property("srgb", False)
            texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        elif name.endswith("_ORM"):
            texture.set_editor_property("srgb", False)
            texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
        unreal.EditorAssetLibrary.set_metadata_tag(texture, "PlayerSuitSource", "FabSpaceMarshal")
        unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
        imported[name] = texture
    return imported


def replace_asset(path: str) -> None:
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)


def create_opaque_master(textures: dict[str, unreal.Texture2D]) -> unreal.Material:
    path = f"{MATERIAL_ROOT}/M_SpaceMarshal_Opaque"
    replace_asset(path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_SpaceMarshal_Opaque", MATERIAL_ROOT, unreal.Material, unreal.MaterialFactoryNew()
    )
    unreal.MaterialEditingLibrary.set_material_usage(
        material, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH
    )
    base = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSampleParameter2D, -520, -180
    )
    base.set_editor_property("parameter_name", "BaseColorTexture")
    base.set_editor_property("texture", textures["SM_Suit_BaseColor"])
    tint = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionVectorParameter, -520, -330
    )
    tint.set_editor_property("parameter_name", "RoleTint")
    tint.set_editor_property("default_value", unreal.LinearColor(1.0, 1.0, 1.0, 1.0))
    tint_strength = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionScalarParameter, -280, -330
    )
    tint_strength.set_editor_property("parameter_name", "RoleTintStrength")
    tint_strength.set_editor_property("default_value", 0.0)
    tinted_base = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionLinearInterpolate, -60, -180
    )
    normal = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSampleParameter2D, -520, 20
    )
    normal.set_editor_property("parameter_name", "NormalTexture")
    normal.set_editor_property("texture", textures["SM_Suit_Normal"])
    normal.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    orm = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSampleParameter2D, -520, 220
    )
    orm.set_editor_property("parameter_name", "ORMTexture")
    orm.set_editor_property("texture", textures["SM_Suit_ORM"])
    orm.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    unreal.MaterialEditingLibrary.connect_material_expressions(base, "RGB", tinted_base, "A")
    unreal.MaterialEditingLibrary.connect_material_expressions(tint, "", tinted_base, "B")
    unreal.MaterialEditingLibrary.connect_material_expressions(tint_strength, "", tinted_base, "Alpha")
    unreal.MaterialEditingLibrary.connect_material_property(tinted_base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(normal, "RGB", unreal.MaterialProperty.MP_NORMAL)
    unreal.MaterialEditingLibrary.connect_material_property(orm, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    unreal.MaterialEditingLibrary.connect_material_property(orm, "G", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(orm, "B", unreal.MaterialProperty.MP_METALLIC)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def create_visor_material(textures: dict[str, unreal.Texture2D]) -> unreal.Material:
    path = f"{MATERIAL_ROOT}/M_SpaceMarshal_Visor"
    replace_asset(path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_SpaceMarshal_Visor", MATERIAL_ROOT, unreal.Material, unreal.MaterialFactoryNew()
    )
    unreal.MaterialEditingLibrary.set_material_usage(
        material, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH
    )
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property("two_sided", True)
    base = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -400, -100
    )
    base.set_editor_property("texture", textures["MS_Visor_BaseColor"])
    opacity = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -400, 80
    )
    opacity.set_editor_property("r", 0.42)
    roughness = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -400, 170
    )
    roughness.set_editor_property("r", 0.16)
    unreal.MaterialEditingLibrary.connect_material_property(base, "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)
    unreal.MaterialEditingLibrary.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def create_instance(name: str, parent: unreal.Material, base: unreal.Texture2D,
                    normal: unreal.Texture2D, orm: unreal.Texture2D,
                    tint: unreal.LinearColor | None = None,
                    tint_strength: float = 0.0) -> unreal.MaterialInstanceConstant:
    path = f"{MATERIAL_ROOT}/{name}"
    replace_asset(path)
    instance = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIAL_ROOT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew()
    )
    unreal.MaterialEditingLibrary.set_material_instance_parent(instance, parent)
    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(instance, "BaseColorTexture", base)
    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(instance, "NormalTexture", normal)
    unreal.MaterialEditingLibrary.set_material_instance_texture_parameter_value(instance, "ORMTexture", orm)
    if tint:
        unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(instance, "RoleTint", tint)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(
        instance, "RoleTintStrength", tint_strength
    )
    unreal.EditorAssetLibrary.save_loaded_asset(instance, only_if_is_dirty=False)
    return instance


def build_material_sets(textures: dict[str, unreal.Texture2D]) -> dict[str, dict[str, unreal.MaterialInterface]]:
    master = create_opaque_master(textures)
    visor = create_visor_material(textures)
    shared = {}
    for slot in SHARED_SLOTS:
        shared[slot] = create_instance(
            f"MI_Shared_{slot}", master, textures[f"{slot}_BaseColor"],
            textures[f"{slot}_Normal"], textures[f"{slot}_ORM"]
        )
    material_sets = {}
    for role, base_name in ROLE_SUIT_TEXTURE.items():
        role_set = dict(shared)
        role_set["SM_Suit"] = create_instance(
            f"MI_{role}_SM_Suit", master, textures[base_name],
            textures["SM_Suit_Normal"], textures["SM_Suit_ORM"], ROLE_TINT[role], 0.32
        )
        role_set["MS_Visor"] = visor
        material_sets[role] = role_set
    return material_sets


def set_component_materials(component: unreal.SkeletalMeshComponent, mesh: unreal.SkeletalMesh,
                            materials: dict[str, unreal.MaterialInterface]) -> None:
    for index, skeletal_material in enumerate(mesh.get_editor_property("materials")):
        slot_name = str(skeletal_material.get_editor_property("material_slot_name"))
        material = materials.get(slot_name)
        if material:
            component.set_material(index, material)
        else:
            unreal.log_warning(f"No review material mapping for skeletal slot {slot_name}")


def set_static_mesh(actor: unreal.StaticMeshActor, mesh_path: str, scale: tuple[float, float, float]) -> None:
    actor.static_mesh_component.set_static_mesh(unreal.EditorAssetLibrary.load_asset(mesh_path))
    actor.static_mesh_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    actor.set_actor_scale3d(unreal.Vector(*scale))


def build_lineup(mesh_path: str, material_sets: dict[str, dict[str, unreal.MaterialInterface]]) -> None:
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        unreal.EditorAssetLibrary.delete_asset(MAP_PATH)
    if not level.new_level(MAP_PATH):
        raise RuntimeError(f"Could not create Space Marshal review level: {MAP_PATH}")
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mesh = unreal.EditorAssetLibrary.load_asset(mesh_path)
    if not mesh:
        raise RuntimeError(f"Review skeletal mesh could not be loaded: {mesh_path}")

    positions = {"Crew": -225.0, "Engineering": -75.0, "Medical": 75.0, "Security": 225.0}
    label_colors = {
        "Crew": unreal.Color(r=80, g=135, b=235, a=255),
        "Engineering": unreal.Color(r=235, g=135, b=45, a=255),
        "Medical": unreal.Color(205, 220, 220, 255),
        "Security": unreal.Color(r=220, g=55, b=50, a=255),
    }
    for role, y in positions.items():
        actor = actors.spawn_actor_from_class(
            unreal.SkeletalMeshActor, unreal.Vector(0, y, 0), unreal.Rotator(roll=0, pitch=0, yaw=-90)
        )
        actor.set_actor_label(f"{role} Primary Oversuit - Space Marshal Review")
        component = actor.skeletal_mesh_component
        component.set_skeletal_mesh(mesh)
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
        set_component_materials(component, mesh, material_sets[role])
        label = actors.spawn_actor_from_class(
            unreal.TextRenderActor, unreal.Vector(30, y, 205), unreal.Rotator(0, 180, 0)
        )
        label.set_actor_label(f"{role} Label")
        label.text_render.set_text(role.upper())
        label.text_render.set_editor_property("world_size", 15.0)
        label.text_render.set_editor_property("text_render_color", label_colors[role])

    floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, -2), unreal.Rotator())
    floor.set_actor_label("Studio Floor")
    set_static_mesh(floor, "/Engine/BasicShapes/Plane.Plane", (12, 12, 12))
    backdrop = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-110, 0, 300), unreal.Rotator())
    backdrop.set_actor_label("Studio Backdrop")
    set_static_mesh(backdrop, "/Engine/BasicShapes/Cube.Cube", (0.12, 13, 6))

    key = actors.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(250, -300, 500), unreal.Rotator(-34, -20, 0)
    )
    key.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    key.light_component.set_editor_property("cast_shadows", False)
    key.light_component.set_editor_property("intensity", 0.8)
    key.light_component.set_editor_property("light_color", unreal.Color(220, 232, 248, 255))
    sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 300), unreal.Rotator())
    sky.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
    sky.light_component.set_editor_property("intensity", 0.15)
    for y, color in ((-330, unreal.Color(215, 230, 255, 255)), (330, unreal.Color(255, 225, 205, 255))):
        light = actors.spawn_actor_from_class(
            unreal.RectLight, unreal.Vector(300, y, 260), unreal.Rotator(0, 180, 0)
        )
        light.light_component.set_mobility(unreal.ComponentMobility.MOVABLE)
        light.light_component.set_editor_property("cast_shadows", False)
        light.light_component.set_editor_property("intensity", 180.0)
        light.light_component.set_editor_property("light_color", color)
        light.light_component.set_editor_property("source_width", 180.0)
        light.light_component.set_editor_property("source_height", 280.0)

    camera = actors.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(820, 0, 112), unreal.Rotator(roll=0, pitch=0, yaw=180)
    )
    camera.set_actor_label("Space Marshal Review Camera")
    camera.camera_component.set_editor_property("field_of_view", 45.0)
    camera.set_editor_property("auto_activate_for_player", unreal.AutoReceiveInput.PLAYER0)
    level.save_current_level()


def main() -> None:
    male_mesh = import_skeletal_mesh(PREPARED / "SM_Male_Oversuit_UE5.fbx")
    female_mesh = import_skeletal_mesh(PREPARED / "SM_Female_Oversuit_Biped.fbx")
    textures = import_textures()
    material_sets = build_material_sets(textures)
    build_lineup(male_mesh, material_sets)
    unreal.EditorAssetLibrary.save_directory(ROOT, only_if_is_dirty=False, recursive=True)
    unreal.log(f"Space Marshal oversuit review ready. Male={male_mesh}; Female={female_mesh}; Map={MAP_PATH}")


main()
