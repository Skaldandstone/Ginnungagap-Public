"""Build and render the V25 I07 concept-aligned four-role oversuit lineup.

The purchased Space Marshal mesh is retained only for authored pressure-garment,
boot, and glove detail.  Its helmet, visor, body/head, and tactical luggage are
hidden on the shared baseline.  The bubble helmet, pressure collar, compact
life-support pack, harness, and restrained limb protection come from the
concept-guided I03/I04 modules.  Role differences are material and equipment
variants, matching the canonical player-suit lineup rather than donor fiction.
"""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory()).resolve()
OUTPUT = PROJECT / "Saved/Renders"
REPORT = PROJECT / "Saved/Reports/PrimaryOversuitV25ConceptAlignedI07.json"
ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt"
I03 = ROOT + "/Working/Iteration_03_ConceptSculpt"
I04 = ROOT + "/Working/Iteration_04_FunctionalDetail"
I06 = ROOT + "/Working/Iteration_06_UncorruptedProductionShell"
I07 = ROOT + "/Working/Iteration_07_ConceptAlignedRoleLineup"
MATERIALS = I07 + "/Materials"
MESH_PATH = I06 + "/Source/SKM_V25_I06_SpaceMarshalMale"
MAP_PATH = ROOT + "/Maps/L_PrimaryOversuit_V25_ConceptAligned_I07"

ROLE_DATA = {
    "Crew": {
        "x": -96.0,
        "fabric": (0.50, 0.52, 0.50),
        "hard": (0.66, 0.64, 0.57),
        "accent": (0.08, 0.22, 0.34),
        "luggage": (),
    },
    "Engineering": {
        "x": -32.0,
        "fabric": (0.075, 0.105, 0.15),
        "hard": (0.18, 0.20, 0.21),
        "accent": (0.78, 0.27, 0.055),
        "luggage": (),
    },
    "Medical": {
        "x": 32.0,
        "fabric": (0.63, 0.64, 0.60),
        "hard": (0.76, 0.75, 0.69),
        "accent": (0.62, 0.035, 0.025),
        "luggage": (),
    },
    "Security": {
        "x": 96.0,
        "fabric": (0.045, 0.052, 0.06),
        "hard": (0.085, 0.095, 0.105),
        "accent": (0.54, 0.025, 0.018),
        "luggage": (),
    },
}

SHARED_MODULES = (
    (I03, "SM_V25_I03_HelmetBubble", "visor"),
    (I03, "SM_V25_I03_PressureCollar", "hard"),
    (I03, "SM_V25_I03_HarnessStraps", "trim"),
    (I04, "SM_V25_I04_ChestMount", "hard"),
    (I04, "SM_V25_I04_ChestComputer", "screen"),
    (I04, "SM_V25_I04_WaistHarness", "trim"),
    (I04, "SM_V25_I04_WaistBuckle", "accent"),
    (I04, "SM_V25_I04_ForearmGuards", "hard"),
    (I04, "SM_V25_I04_ForearmDisplay", "screen"),
    (I04, "SM_V25_I04_KneeGuards", "hard"),
    (I04, "SM_V25_I04_LifeSupportPack", "hard"),
    (I04, "SM_V25_I04_LifeSupportDetail", "trim"),
)


def make_solid(name, color, roughness=0.62, metallic=0.05, emissive=None):
    path = f"{MATERIALS}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIALS, unreal.Material, unreal.MaterialFactoryNew()
    )
    unreal.MaterialEditingLibrary.set_material_usage(
        material, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH
    )
    base = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -360, -60
    )
    base.set_editor_property("constant", unreal.LinearColor(*color, 1.0))
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -360, 90
    )
    rough.set_editor_property("r", roughness)
    metal = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -360, 180
    )
    metal.set_editor_property("r", metallic)
    unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emissive:
        glow = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant3Vector, -360, 285
        )
        glow.set_editor_property("constant", unreal.LinearColor(*emissive, 1.0))
        unreal.MaterialEditingLibrary.connect_material_property(
            glow, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR
        )
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def make_hidden():
    name = "M_V25_I07_HiddenDonorSection"
    path = f"{MATERIALS}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIALS, unreal.Material, unreal.MaterialFactoryNew()
    )
    unreal.MaterialEditingLibrary.set_material_usage(
        material, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH
    )
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property("two_sided", True)
    opacity = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -220, 0
    )
    opacity.set_editor_property("r", 0.0)
    unreal.MaterialEditingLibrary.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def make_visor():
    name = "M_V25_I07_ClearPressureDome"
    path = f"{MATERIALS}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIALS, unreal.Material, unreal.MaterialFactoryNew()
    )
    unreal.MaterialEditingLibrary.set_material_usage(
        material, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH
    )
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    material.set_editor_property("two_sided", True)
    color = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -360, -80
    )
    color.set_editor_property("constant", unreal.LinearColor(0.035, 0.12, 0.16, 1.0))
    opacity = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -360, 60
    )
    opacity.set_editor_property("r", 0.16)
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -360, 160
    )
    rough.set_editor_property("r", 0.055)
    unreal.MaterialEditingLibrary.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def make_tinted_suit(name, tint):
    path = f"{MATERIALS}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        unreal.EditorAssetLibrary.delete_asset(path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        name, MATERIALS, unreal.Material, unreal.MaterialFactoryNew()
    )
    unreal.MaterialEditingLibrary.set_material_usage(
        material, unreal.MaterialUsage.MATUSAGE_SKELETAL_MESH
    )
    normal_texture = unreal.EditorAssetLibrary.load_asset(I06 + "/Textures/SM_Suit_NormalX")
    orm_texture = unreal.EditorAssetLibrary.load_asset(I06 + "/Textures/SM_Suit_ORM")
    if not all(isinstance(value, unreal.Texture) for value in (normal_texture, orm_texture)):
        raise RuntimeError("I06 suit texture set is incomplete")
    color = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -520, -100
    )
    color.set_editor_property("constant", unreal.LinearColor(*tint, 1.0))
    unreal.MaterialEditingLibrary.connect_material_property(
        color, "", unreal.MaterialProperty.MP_BASE_COLOR
    )
    normal = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -700, 230
    )
    normal.set_editor_property("texture", normal_texture)
    normal.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    unreal.MaterialEditingLibrary.connect_material_property(normal, "RGB", unreal.MaterialProperty.MP_NORMAL)
    orm = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionTextureSample, -700, 470
    )
    orm.set_editor_property("texture", orm_texture)
    unreal.MaterialEditingLibrary.connect_material_property(orm, "R", unreal.MaterialProperty.MP_AMBIENT_OCCLUSION)
    unreal.MaterialEditingLibrary.connect_material_property(orm, "G", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(orm, "B", unreal.MaterialProperty.MP_METALLIC)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)
    return material


def slot_map(mesh):
    result = {}
    for index, slot in enumerate(mesh.get_editor_property("materials")):
        result[index] = str(slot.get_editor_property("material_slot_name")).lower()
    return result


def spawn_module(actors, folder, asset_name, role, x_offset, z_offset, role_materials):
    asset = unreal.EditorAssetLibrary.load_asset(f"{folder}/{asset_name}")
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError(f"Missing module {folder}/{asset_name}")
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(x_offset, 0.0, z_offset), unreal.Rotator()
    )
    actor.set_actor_label(f"I07_{role}_{asset_name}")
    actor.static_mesh_component.set_static_mesh(asset)
    actor.static_mesh_component.set_material(0, role_materials[role])
    return actor


def add_rect_light(actors, label, location, target, intensity, width, height, color):
    light = actors.spawn_actor_from_class(
        unreal.RectLight, location, unreal.MathLibrary.find_look_at_rotation(location, target)
    )
    light.set_actor_label(label)
    component = light.rect_light_component
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("source_width", width)
    component.set_editor_property("source_height", height)
    component.set_editor_property("light_color", color)


def capture(world, actors, filename, location, target, width, height, fov):
    actor = actors.spawn_actor_from_class(
        unreal.SceneCapture2D, location, unreal.MathLibrary.find_look_at_rotation(location, target)
    )
    actor.set_actor_label(f"RENDER_{filename}")
    component = actor.capture_component2d
    component.capture_every_frame = False
    component.capture_on_movement = False
    component.fov_angle = fov
    texture = unreal.RenderingLibrary.create_render_target2d(
        world, width, height, unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0.075, 0.080, 0.088, 1.0),
    )
    component.texture_target = texture
    component.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    pp = component.post_process_settings
    pp.set_editor_property("override_auto_exposure_method", True)
    pp.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    pp.set_editor_property("override_camera_iso", True)
    pp.set_editor_property("camera_iso", 160.0)
    pp.set_editor_property("override_camera_shutter_speed", True)
    pp.set_editor_property("camera_shutter_speed", 60.0)
    pp.set_editor_property("override_auto_exposure_bias", True)
    pp.set_editor_property("auto_exposure_bias", 1.15)
    component.post_process_settings = pp
    component.capture_scene()
    component.capture_scene()
    unreal.RenderingLibrary.export_render_target(world, texture, str(OUTPUT), filename)
    actor.destroy_actor()


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    unreal.EditorAssetLibrary.make_directory(I07)
    unreal.EditorAssetLibrary.make_directory(MATERIALS)

    mesh = unreal.EditorAssetLibrary.load_asset(MESH_PATH)
    if not isinstance(mesh, unreal.SkeletalMesh):
        raise RuntimeError(f"Missing I06 donor mesh {MESH_PATH}")

    hidden = make_hidden()
    visor = make_visor()
    role_material_sets = {}
    for role, data in ROLE_DATA.items():
        role_material_sets[role] = {
            "visor": visor,
            "fabric": make_tinted_suit(f"M_V25_I07_{role}_Fabric", data["fabric"]),
            "hard": make_solid(f"M_V25_I07_{role}_Hard", data["hard"], 0.56, 0.14),
            "accent": make_solid(f"M_V25_I07_{role}_Accent", data["accent"], 0.48, 0.20),
            "trim": make_solid(f"M_V25_I07_{role}_Trim", (0.035, 0.042, 0.05), 0.72, 0.10),
            "screen": make_solid(
                f"M_V25_I07_{role}_Screen", (0.015, 0.07, 0.09), 0.25, 0.12,
                (0.02, 0.32, 0.44),
            ),
        }

    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        if not levels.load_level(MAP_PATH):
            raise RuntimeError(f"Could not load {MAP_PATH}")
    elif not levels.new_level(MAP_PATH):
        raise RuntimeError(f"Could not create {MAP_PATH}")

    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for existing in actors.get_all_level_actors():
        actors.destroy_actor(existing)

    slots = slot_map(mesh)
    donor_originals = [slot.get_editor_property("material_interface") for slot in mesh.get_editor_property("materials")]
    spawned = {}
    module_z_offset = 15.0
    for role, data in ROLE_DATA.items():
        x = data["x"]
        materials = role_material_sets[role]
        suit = actors.spawn_actor_from_class(
            unreal.SkeletalMeshActor, unreal.Vector(x, 0.0, 0.0), unreal.Rotator(yaw=180.0)
        )
        suit.set_actor_label(f"I07_{role}_AUTHORED_PRESSURE_GARMENT")
        suit.skeletal_mesh_component.set_skeletal_mesh_asset(mesh)
        for index, name in slots.items():
            replacement = hidden
            if "sm_suit" in name:
                replacement = materials["fabric"]
            elif "sm_helm" in name:
                replacement = materials["hard"]
            elif "sm_boots" in name or "sm_gloves" in name:
                replacement = donor_originals[index]
            elif any(token in name for token in data["luggage"]):
                replacement = materials["accent"]
            suit.skeletal_mesh_component.set_material(index, replacement)

        module_actors = []
        for folder, asset_name, material_role in SHARED_MODULES:
            module_actors.append(
                spawn_module(
                    actors, folder, asset_name, material_role, x, module_z_offset, materials
                )
            )
        spawned[role] = {
            "skeletal_actor": suit.get_actor_label(),
            "modules": [actor.get_actor_label() for actor in module_actors],
        }

    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    target = unreal.Vector(0.0, 0.0, 105.0)
    add_rect_light(actors, "I07_Key", unreal.Vector(-220, -285, 270), target, 95.0, 260.0, 300.0, unreal.Color(255, 238, 220))
    add_rect_light(actors, "I07_Fill", unreal.Vector(250, -180, 165), target, 52.0, 235.0, 270.0, unreal.Color(205, 224, 255))
    add_rect_light(actors, "I07_Rim", unreal.Vector(35, 260, 235), target, 92.0, 220.0, 260.0, unreal.Color(220, 235, 255))
    sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(), unreal.Rotator())
    sky.set_actor_label("I07_Sky")
    sky.light_component.set_editor_property("intensity", 0.22)

    levels.save_current_level()
    capture(world, actors, "PrimaryOversuitV25_I07_ConceptAligned_Lineup", unreal.Vector(0, -690, 112), target, 1800, 1200, 31.0)
    for role, data in ROLE_DATA.items():
        x = data["x"]
        capture(
            world, actors, f"PrimaryOversuitV25_I07_{role}_Front",
            unreal.Vector(x, -385, 103), unreal.Vector(x, 0, 103), 1200, 1600, 31.0,
        )
    levels.save_current_level()

    REPORT.write_text(json.dumps({
        "status": "concept_aligned_role_lineup_built",
        "iteration": "V25.I07",
        "canonical_concepts": [
            "docs/concept-art/reference/suits/standard-suit-turnaround.png",
            "docs/concept-art/reference/suits/player-suit-role-lineup.png",
            "docs/concept-art/reference/suits/player-suit-hands-free-equipment-concept-v2.png",
        ],
        "donor_policy": "garment, boot, glove, and surface-detail donor only",
        "hidden_donor_sections": ["body/head", "helmet", "visor", "baseline tactical bags", "baseline tactical pouch"],
        "shared_silhouette": ["bubble visor", "pressure collar", "compact pack", "visible soft garment", "restrained hard protection"],
        "roles": ROLE_DATA,
        "spawned": spawned,
        "map": MAP_PATH,
        "runtime_ready": False,
        "next_step": "replace pose-fit review modules with separated/skinned authored pieces after silhouette approval",
    }, indent=2), encoding="utf-8")
    unreal.EditorAssetLibrary.save_directory(I07, only_if_is_dirty=False, recursive=True)
    unreal.log("PRIMARY OVERSUIT V25 I07: concept-aligned role lineup rendered")


main()
