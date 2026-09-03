"""Import the purchased Space Marshal mesh as the V25 I06 production shell.

I06 replaces the hand-built I05 review primitives with authored, rigged,
high-frequency pressure-suit geometry.  The source is kept intact in SourceArt;
the imported asset remains a reference shell until it has been separated into
independent wearable parts and fitted to the player skeleton.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory()).resolve()
SOURCE = PROJECT / "SourceArt/Fab/SpaceMarshalMale"
FBX = SOURCE / "FBX/SM_Male_UE5.fbx"
TEXTURES = SOURCE / "Textures"
ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt"
FOLDER = ROOT + "/Working/Iteration_06_UncorruptedProductionShell"
SOURCE_FOLDER = FOLDER + "/Source"
TEXTURE_FOLDER = FOLDER + "/Textures"
MATERIAL_FOLDER = FOLDER + "/Materials"
REPORT = PROJECT / "Saved/Reports/PrimaryOversuitV25UncorruptedProductionI06.json"

SUIT_PREFIXES = (
    "SM_Suit",
    "SM_Helm",
    "MS_Visor",
    "SM_Bags",
    "SM_Pouch",
    "SM_Boots",
    "SM_Gloves",
)


def import_texture(path: Path) -> unreal.Texture:
    asset_path = f"{TEXTURE_FOLDER}/{path.stem}"
    existing = (
        unreal.EditorAssetLibrary.load_asset(asset_path)
        if unreal.EditorAssetLibrary.does_asset_exist(asset_path)
        else None
    )
    if isinstance(existing, unreal.Texture):
        return existing

    task = unreal.AssetImportTask()
    task.filename = str(path)
    task.destination_path = TEXTURE_FOLDER
    task.destination_name = path.stem
    task.automated = True
    task.save = True
    task.replace_existing = True
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    texture = unreal.EditorAssetLibrary.load_asset(asset_path)
    if not isinstance(texture, unreal.Texture):
        raise RuntimeError(f"Could not import texture {path}")

    if path.stem.endswith("_NormalX"):
        texture.set_editor_property("srgb", False)
        texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
    elif path.stem.endswith("_ORM"):
        texture.set_editor_property("srgb", False)
        texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
    unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False)
    return texture


def solid_material(name: str, color: tuple[float, float, float], roughness: float) -> unreal.Material:
    path = f"{MATERIAL_FOLDER}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIAL_FOLDER, unreal.Material, unreal.MaterialFactoryNew()
    )
    base = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -320, -40
    )
    base.set_editor_property("constant", unreal.LinearColor(*color, 1.0))
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -320, 90
    )
    rough.set_editor_property("r", roughness)
    unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def pbr_material(prefix: str, textures: dict[str, unreal.Texture]) -> unreal.Material:
    name = f"M_V25_I06_{prefix}"
    path = f"{MATERIAL_FOLDER}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIAL_FOLDER, unreal.Material, unreal.MaterialFactoryNew()
    )
    if not isinstance(material, unreal.Material):
        raise RuntimeError(f"Could not create {path}")

    base_tex = textures.get(prefix + "_BaseColor")
    normal_tex = textures.get(prefix + "_NormalX")
    orm_tex = textures.get(prefix + "_ORM")
    emissive_tex = textures.get(prefix + "_Emissive")

    if base_tex:
        expr = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionTextureSample, -560, -100
        )
        expr.set_editor_property("texture", base_tex)
        unreal.MaterialEditingLibrary.connect_material_property(
            expr, "RGB", unreal.MaterialProperty.MP_BASE_COLOR
        )
    if normal_tex:
        expr = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionTextureSample, -560, 130
        )
        expr.set_editor_property("texture", normal_tex)
        expr.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        unreal.MaterialEditingLibrary.connect_material_property(
            expr, "RGB", unreal.MaterialProperty.MP_NORMAL
        )
    if orm_tex:
        expr = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionTextureSample, -560, 370
        )
        expr.set_editor_property("texture", orm_tex)
        unreal.MaterialEditingLibrary.connect_material_property(
            expr, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION
        )
        unreal.MaterialEditingLibrary.connect_material_property(
            expr, "G", unreal.MaterialProperty.MP_ROUGHNESS
        )
        unreal.MaterialEditingLibrary.connect_material_property(
            expr, "B", unreal.MaterialProperty.MP_METALLIC
        )
    if emissive_tex:
        expr = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionTextureSample, -560, 600
        )
        expr.set_editor_property("texture", emissive_tex)
        unreal.MaterialEditingLibrary.connect_material_property(
            expr, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )

    if prefix == "MS_Visor":
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        material.set_editor_property("two_sided", True)
        opacity = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant, -300, 520
        )
        opacity.set_editor_property("r", 0.34)
        unreal.MaterialEditingLibrary.connect_material_property(
            opacity, "", unreal.MaterialProperty.MP_OPACITY
        )

    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def import_skeletal_mesh() -> unreal.SkeletalMesh:
    task = unreal.AssetImportTask()
    task.filename = str(FBX)
    task.destination_path = SOURCE_FOLDER
    task.destination_name = "SKM_V25_I06_SpaceMarshalMale"
    task.automated = True
    task.save = True
    task.replace_existing = True

    options = unreal.FbxImportUI()
    options.import_mesh = True
    options.import_as_skeletal = True
    options.import_animations = False
    options.import_materials = False
    options.import_textures = False
    options.create_physics_asset = False
    options.mesh_type_to_import = unreal.FBXImportType.FBXIT_SKELETAL_MESH
    options.skeletal_mesh_import_data.normal_import_method = unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS_AND_TANGENTS
    task.options = options
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])

    for path in task.imported_object_paths:
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if isinstance(asset, unreal.SkeletalMesh):
            return asset
    expected = unreal.EditorAssetLibrary.load_asset(
        SOURCE_FOLDER + "/SKM_V25_I06_SpaceMarshalMale"
    )
    if isinstance(expected, unreal.SkeletalMesh):
        return expected
    raise RuntimeError(f"Skeletal import failed; created {list(task.imported_object_paths)}")


def material_for_slot(slot_name: str, materials: dict[str, unreal.MaterialInterface], fallback):
    normalized = slot_name.lower().replace("m_", "").replace("mi_", "")
    aliases = {
        "SM_Suit": ("sm_suit", "suit"),
        "SM_Helm": ("sm_helm", "helm", "helmet"),
        "MS_Visor": ("ms_visor", "visor", "glass"),
        "SM_Bags": ("sm_bags", "bags"),
        "SM_Pouch": ("sm_pouch", "pouch"),
        "SM_Boots": ("sm_boots", "boots"),
        "SM_Gloves": ("sm_gloves", "gloves"),
    }
    for prefix, names in aliases.items():
        if any(name in normalized for name in names):
            return materials[prefix]
    return fallback


def main():
    if not FBX.exists():
        raise RuntimeError(f"Missing purchased source FBX: {FBX}")
    for folder in (FOLDER, SOURCE_FOLDER, TEXTURE_FOLDER, MATERIAL_FOLDER):
        unreal.EditorAssetLibrary.make_directory(folder)

    texture_files = []
    for prefix in SUIT_PREFIXES:
        for suffix in ("BaseColor", "NormalX", "ORM", "Emissive"):
            candidate = TEXTURES / f"{prefix}_{suffix}.png"
            if candidate.exists():
                texture_files.append(candidate)
    imported_textures = {path.stem: import_texture(path) for path in texture_files}
    materials = {prefix: pbr_material(prefix, imported_textures) for prefix in SUIT_PREFIXES}
    fallback = solid_material("M_V25_I06_InteriorNeutral", (0.022, 0.025, 0.027), 0.78)
    mesh = import_skeletal_mesh()

    slots = list(mesh.get_editor_property("materials"))
    assignments = {}
    for slot in slots:
        slot_name = str(slot.get_editor_property("material_slot_name"))
        assigned = material_for_slot(slot_name, materials, fallback)
        slot.set_editor_property("material_interface", assigned)
        assignments[slot_name] = assigned.get_path_name()
    mesh.set_editor_property("materials", slots)

    metadata = {
        "Ginnungagap.AssetRole": "PrimaryOversuitProductionReferenceShell",
        "Ginnungagap.Iteration": "V25.I06",
        "Ginnungagap.ReferenceConcept": "UncorruptedHumanoidBaselineConcept",
        "Ginnungagap.SourceProduct": "Fab Space Marshal - SciFi Soldier - Male",
        "Ginnungagap.SourceListing": "92d50b0d-187a-4b4f-920c-477c07789253",
        "Ginnungagap.IndependentWearable": "pending separation and player-skeleton fit",
        "Ginnungagap.RuntimeReady": "false",
    }
    for key, value in metadata.items():
        unreal.EditorAssetLibrary.set_metadata_tag(mesh, key, value)
    unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
    unreal.EditorAssetLibrary.save_directory(FOLDER, only_if_is_dirty=False, recursive=True)

    bounds = mesh.get_bounds()
    size = bounds.box_extent * 2.0
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "status": "production_reference_shell_imported",
        "iteration": "V25.I06",
        "source": str(FBX),
        "listing": "https://www.fab.com/listings/92d50b0d-187a-4b4f-920c-477c07789253",
        "concept_reference": "docs/concept-art/reference/bloom/uncorrupted-humanoid-baselines.png",
        "skeletal_mesh": mesh.get_path_name(),
        "bounds_cm": [size.x, size.y, size.z],
        "material_assignments": assignments,
        "imported_textures": {key: value.get_path_name() for key, value in imported_textures.items()},
        "runtime_ready": False,
        "next_step": "separate authored suit components and fit them as independent wearables to the player skeleton",
    }, indent=2), encoding="utf-8")
    unreal.log(f"PRIMARY OVERSUIT V25 I06: imported production shell {mesh.get_path_name()}")


main()
