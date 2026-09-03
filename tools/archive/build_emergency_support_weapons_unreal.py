"""Build five clean emergency-support and salvage weapons in Unreal."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
SHARED_PATH = PROJECT / "tools/build_early_projectile_weapons_unreal.py"
SPEC = importlib.util.spec_from_file_location("emergency_weapon_builder_shared", SHARED_PATH)
shared = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(shared)

ROOT = "/Game/Assets/Gameplay/EmergencySupportWeapons"
MESH_PATH = ROOT + "/Meshes"
MATERIAL_PATH = ROOT + "/Materials"
DATA_PATH = ROOT + "/Data/Weapons"
BP_PATH = ROOT + "/Blueprints"
CATALOG_PATH = ROOT + "/Data/DA_EmergencySupportWeaponCatalog"
MAP_PATH = "/Game/Assets/Maps/ModelLibrary/L_EmergencySupportWeapons_Unreal"
SAFE_MAP_PATH = "/Game/Assets/Maps/ModelLibrary/L_GameplayModelLibrary"
MAPPING_PATH = PROJECT / "Art/Weapons/ConceptMappings/EmergencySupportWeapons.json"
REPORT_PATH = PROJECT / "Saved/Reports/EmergencySupportWeaponsUnreal.json"

WEAPONS = (
    dict(
        id="AcousticComplianceEmitter", label="Acoustic Compliance Emitter", concept=54,
        size=(86, 34, 40), envelope="STANDARD", chassis_scale=.68,
        rooms=["Security", "Brig", "CrewCommons", "Medical"], weight=.46,
        tags=["Weapon.Control", "Weapon.Acoustic", "Security.LessLethal"],
        player=True, aerial=True, robotic=True,
        base=dict(mode="TRACE", range=1250, radius=34, damage=1, impulse=3500, recoil=650,
                  cooldown=.95, control="ACOUSTIC_DISORIENT", duration=2.0, movement=.62),
        upgrades=(
            dict(id="PhasedTransducer", label="Phased Transducer", description="Phase-matched emitters extend the compliant acoustic lobe.", resource="SENSOR_COMPONENTS", cost=7,
                 mode="TRACE", range=1550, radius=30, damage=2, impulse=4000, recoil=600,
                 cooldown=.76, control="ACOUSTIC_DISORIENT", duration=2.8, movement=.52),
            dict(id="DirectionalBaffle", label="Directional Baffle", description="A tighter baffle reduces spill while sustaining target disorientation.", resource="STRUCTURAL_ALLOY", cost=9,
                 mode="TRACE", range=1900, radius=24, damage=3, impulse=4500, recoil=550,
                 cooldown=.62, control="ACOUSTIC_DISORIENT", duration=3.6, movement=.42),
        ),
        unsafe=dict(mode="TRACE", range=2200, radius=42, damage=14, impulse=8500, recoil=1600,
                    cooldown=.58, control="ACOUSTIC_DISORIENT", duration=5.0, movement=.25,
                    hull=.025, breach=.0),
    ),
    dict(
        id="DoorBreachRam", label="Door-Breach Ram", concept=55,
        size=(98, 48, 46), envelope="BULKY", chassis_scale=.64,
        rooms=["Security", "DamageControl", "Airlock", "Rescue"], weight=.25,
        tags=["Weapon.Impact", "Tool.Breach", "Security.Authorized"],
        player=True, aerial=False, robotic=True,
        base=dict(mode="TRACE", range=115, radius=18, damage=8, impulse=52000, recoil=9000,
                  cooldown=1.45, control="STAGGER", duration=.8, movement=.25,
                  hull=.025, breach=.005),
        upgrades=(
            dict(id="PressureAccumulator", label="Pressure Accumulator", description="Stores a second hydraulic impulse without enlarging the ram face.", resource="POWER_CELLS", cost=8,
                 mode="TRACE", range=125, radius=18, damage=10, impulse=64000, recoil=8800,
                 cooldown=1.15, control="STAGGER", duration=1.0, movement=.20,
                 hull=.035, breach=.008),
            dict(id="RecoilCradle", label="Recoil Cradle", description="A sliding cradle routes the return stroke into the weapon body.", resource="STRUCTURAL_ALLOY", cost=11,
                 mode="TRACE", range=135, radius=20, damage=12, impulse=76000, recoil=6200,
                 cooldown=.92, control="STAGGER", duration=1.2, movement=.15,
                 hull=.045, breach=.012),
        ),
        unsafe=dict(mode="TRACE", range=150, radius=22, damage=28, impulse=105000, recoil=14500,
                    cooldown=1.0, control="STAGGER", duration=1.8, movement=.05,
                    hull=.14, breach=.085),
    ),
    dict(
        id="RescueShield", label="Rescue Shield", concept=56,
        size=(58, 76, 112), envelope="BULKY", chassis_scale=.36,
        rooms=["Rescue", "Medical", "Security", "DamageControl"], weight=.30,
        tags=["Tool.Rescue", "Equipment.Shield", "Security.Defensive"],
        player=True, aerial=False, robotic=True,
        base=dict(mode="RESCUE_SHIELD", range=120, radius=4, damage=0, impulse=0, recoil=0,
                  cooldown=5.5, shield_duration=3.0, shield_extents=(7, 40, 66)),
        upgrades=(
            dict(id="ExpandedProjector", label="Expanded Projector", description="Wider field rails cover a second responder moving shoulder-to-shoulder.", resource="STRUCTURAL_ALLOY", cost=8,
                 mode="RESCUE_SHIELD", range=120, radius=4, damage=0, impulse=0, recoil=0,
                 cooldown=5.0, shield_duration=4.0, shield_extents=(7, 48, 72)),
            dict(id="ReserveCell", label="Reserve Cell", description="A protected reserve cell sustains the barrier through a longer extraction window.", resource="POWER_CELLS", cost=12,
                 mode="RESCUE_SHIELD", range=120, radius=4, damage=0, impulse=0, recoil=0,
                 cooldown=4.5, shield_duration=5.5, shield_extents=(8, 50, 76)),
        ),
        unsafe=dict(mode="RESCUE_SHIELD", range=120, radius=4, damage=0, impulse=0, recoil=0,
                    cooldown=4.0, shield_duration=7.0, shield_extents=(10, 54, 80)),
    ),
    dict(
        id="FlashDazzleArray", label="Flash-Dazzle Array", concept=58,
        size=(90, 44, 46), envelope="STANDARD", chassis_scale=.64,
        rooms=["Security", "Brig", "Bridge", "Cargo"], weight=.40,
        tags=["Weapon.Control", "Weapon.Optical", "Security.LessLethal"],
        player=True, aerial=True, robotic=True,
        base=dict(mode="TRACE", range=1100, radius=38, damage=0, impulse=1200, recoil=450,
                  cooldown=1.15, control="FLASH_DAZZLE", duration=1.6, movement=.45),
        upgrades=(
            dict(id="SequencedEmitters", label="Sequenced Emitters", description="Staggered emitters prevent a target from adapting between pulses.", resource="POWER_CELLS", cost=7,
                 mode="TRACE", range=1400, radius=34, damage=0, impulse=1400, recoil=420,
                 cooldown=.92, control="FLASH_DAZZLE", duration=2.4, movement=.35),
            dict(id="AdaptiveExposure", label="Adaptive Exposure", description="Range sensing meters flash energy while preserving the intended dazzle window.", resource="SENSOR_COMPONENTS", cost=10,
                 mode="TRACE", range=1750, radius=28, damage=1, impulse=1600, recoil=400,
                 cooldown=.74, control="FLASH_DAZZLE", duration=3.2, movement=.25),
        ),
        unsafe=dict(mode="TRACE", range=2050, radius=46, damage=9, impulse=2500, recoil=900,
                    cooldown=.68, control="FLASH_DAZZLE", duration=4.5, movement=.10,
                    hull=.018, breach=.0),
    ),
    dict(
        id="MagneticScrapFlinger", label="Magnetic Scrap Flinger", concept=45,
        size=(108, 46, 48), envelope="LONG", chassis_scale=.72,
        rooms=["Cargo", "Salvage", "MachineShop", "Airlock"], weight=.34,
        tags=["Weapon.Projectile", "Tool.Salvage", "Ammo.FerrousScrap"],
        player=True, aerial=False, robotic=True,
        base=dict(mode="PROJECTILE", range=1350, radius=3, speed=3100, gravity=.16, spread=3.2,
                  damage=10, impulse=22000, recoil=2100, cooldown=.78,
                  control="STAGGER", duration=.6, movement=.55),
        upgrades=(
            dict(id="FerricSorter", label="Ferric Sorter", description="Rejects unstable fragments and feeds a repeatable ferrous projectile.", resource="SENSOR_COMPONENTS", cost=7,
                 mode="PROJECTILE", range=1700, radius=3, speed=3650, gravity=.11, spread=1.8,
                 damage=13, impulse=27000, recoil=2150, cooldown=.62,
                 control="STAGGER", duration=.8, movement=.45),
            dict(id="FluxAccelerator", label="Flux Accelerator", description="A reinforced coil jacket raises velocity while tightening the launch field.", resource="POWER_CELLS", cost=11,
                 mode="PROJECTILE", range=2150, radius=3, speed=4450, gravity=.07, spread=.9,
                 damage=18, impulse=34000, recoil=2600, cooldown=.50,
                 control="STAGGER", duration=1.0, movement=.35),
        ),
        unsafe=dict(mode="PROJECTILE", range=2550, radius=4, speed=5200, gravity=.045, spread=2.2,
                    damage=34, impulse=52000, recoil=5400, cooldown=.54,
                    control="STAGGER", duration=1.4, movement=.18,
                    hull=.12, breach=.05),
    ),
)


def weapon_mesh(descriptor, mapping):
    mesh = unreal.DynamicMesh()
    shared.copy_chassis(mesh, descriptor, mapping)
    length, width, height = descriptor["size"]
    weapon_id = descriptor["id"]

    if weapon_id == "AcousticComplianceEmitter":
        shared.cylinder(mesh, (length*.34, 0, height*.58), height*.22, length*.28)
        for offset in (0, 4.0, 8.0):
            shared.torus(mesh, (length*.48 + offset, 0, height*.58), height*.25, 2.4)
    elif weapon_id == "DoorBreachRam":
        shared.box(mesh, (length*.42, 0, height*.57), (length*.28, width*.76, height*.72))
        shared.box(mesh, (length*.59, 0, height*.57), (length*.08, width*.92, height*.84))
        for side in (-1, 1):
            shared.cylinder(mesh, (length*.30, side*width*.28, height*.57), height*.08, length*.42)
    elif weapon_id == "RescueShield":
        shared.box(mesh, (length*.12, 0, height*.52), (length*.12, width*.92, height*.92))
        shared.box(mesh, (length*.04, 0, height*.52), (length*.08, width*.72, height*.72))
        for side in (-1, 1):
            shared.box(mesh, (length*.18, side*width*.42, height*.52), (length*.18, width*.08, height*.82))
    elif weapon_id == "FlashDazzleArray":
        for side_y in (-1, 0, 1):
            for side_z in (-1, 0, 1):
                location = (length*.48, side_y*width*.20, height*(.58 + side_z*.19))
                shared.cylinder(mesh, location, height*.075, length*.14)
                shared.torus(mesh, (length*.55, location[1], location[2]), height*.09, 1.6)
    else:
        shared.cylinder(mesh, (length*.31, 0, height*.58), height*.20, length*.36)
        for offset in (0, 5.0, 10.0):
            shared.torus(mesh, (length*.46 + offset, 0, height*.58), height*.24, 3.0)
        shared.box(mesh, (-length*.02, 0, height*.82), (length*.28, width*.34, height*.14))

    mesh.discard_mesh_attributes()
    mesh.auto_generate_x_atlas_mesh_u_vs(0, unreal.GeometryScriptXAtlasOptions())
    mesh.recompute_normals(shared.NORMALS)
    return mesh


def material():
    result = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_EmergencySupport_FirstUseCeramic", MATERIAL_PATH,
        unreal.Material, unreal.MaterialFactoryNew())
    base = unreal.MaterialEditingLibrary.create_material_expression(
        result, unreal.MaterialExpressionConstant3Vector, -300, -20)
    base.set_editor_property("constant", unreal.LinearColor(.48, .49, .46, 1))
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        result, unreal.MaterialExpressionConstant, -300, 120)
    rough.set_editor_property("r", .40)
    metal = unreal.MaterialEditingLibrary.create_material_expression(
        result, unreal.MaterialExpressionConstant, -300, 210)
    metal.set_editor_property("r", .20)
    unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    unreal.MaterialEditingLibrary.recompile_material(result)
    unreal.EditorAssetLibrary.save_loaded_asset(result)
    return result


def firing_profile(values):
    profile = unreal.WeaponFiringProfile()
    profile.set_editor_property("max_range_cm", values["range"])
    profile.set_editor_property("trace_radius_cm", values["radius"])
    profile.set_editor_property("biological_damage", values["damage"])
    profile.set_editor_property("impact_impulse", values["impulse"])
    profile.set_editor_property("recoil_impulse", values["recoil"])
    profile.set_editor_property("cooldown_seconds", values["cooldown"])
    profile.set_editor_property("delivery_mode", getattr(unreal.WeaponDeliveryMode, values["mode"]))
    profile.set_editor_property("projectile_speed_cm_per_second", values.get("speed", 4500))
    profile.set_editor_property("projectile_gravity_scale", values.get("gravity", 0.0))
    profile.set_editor_property("spread_half_angle_degrees", values.get("spread", 0.0))
    profile.set_editor_property("projectiles_per_shot", values.get("projectiles", 1))
    if values.get("control"):
        profile.set_editor_property("control_effect", getattr(unreal.WeaponControlEffect, values["control"]))
        profile.set_editor_property("control_duration_seconds", values["duration"])
        profile.set_editor_property("control_movement_multiplier", values["movement"])
    if values["mode"] == "RESCUE_SHIELD":
        profile.set_editor_property("shield_duration_seconds", values["shield_duration"])
        profile.set_editor_property("shield_half_extents_cm", unreal.Vector(*values["shield_extents"]))
    profile.set_editor_property("can_damage_hull", values.get("hull", 0.0) > 0.0)
    profile.set_editor_property("hull_impact_severity", values.get("hull", 0.0))
    profile.set_editor_property("breach_severity", values.get("breach", 0.0))
    return profile


def build_weapon(descriptor, mesh):
    definition = shared.data_asset(
        "DA_Weapon_" + descriptor["id"], DATA_PATH, unreal.ShipboardWeaponDefinition)
    definition.set_editor_property("weapon_id", unreal.Name(descriptor["id"]))
    definition.set_editor_property("display_name", shared.text(descriptor["label"]))
    definition.set_editor_property("description", shared.text(
        "Clean emergency-support platform with two permanent upgrades and an authorization-locked conversion."))
    definition.set_editor_property("weapon_mesh", mesh)
    definition.set_editor_property("muzzle_offset", unreal.Vector(
        descriptor["size"][0]*.50, 0, descriptor["size"][2]*.56))
    definition.set_editor_property("safe_profile", firing_profile(descriptor["base"]))
    definition.set_editor_property("unsafe_modified_profile", firing_profile(descriptor["unsafe"]))
    stages = []
    for source in descriptor["upgrades"]:
        stage = unreal.WeaponUpgradeStage()
        stage.set_editor_property("upgrade_id", unreal.Name(source["id"]))
        stage.set_editor_property("display_name", shared.text(source["label"]))
        stage.set_editor_property("description", shared.text(source["description"]))
        stage.set_editor_property("firing_profile", firing_profile(source))
        stage.set_editor_property("cost_resource", getattr(unreal.WeaponUpgradeResource, source["resource"]))
        stage.set_editor_property("resource_cost", source["cost"])
        stages.append(stage)
    definition.set_editor_property("upgrade_stages", stages)
    definition.set_editor_property("collision_envelope", shared.envelope(descriptor))
    definition.set_editor_property("player_compatible", descriptor["player"])
    definition.set_editor_property("aerial_drone_compatible", descriptor["aerial"])
    definition.set_editor_property("robotic_drone_compatible", descriptor["robotic"])
    definition.set_editor_property("unsafe_modification_requires_soldier", True)
    unreal.EditorAssetLibrary.save_loaded_asset(definition)

    blueprint = shared.blueprint(
        "BP_Weapon_" + descriptor["id"], BP_PATH, unreal.ShipboardWeapon)
    cdo = unreal.get_default_object(blueprint.generated_class())
    cdo.set_editor_property("definition", definition)
    cdo.get_editor_property("visual_mesh").set_static_mesh(mesh)
    cdo.get_editor_property("muzzle").set_relative_location(
        unreal.Vector(descriptor["size"][0]*.50, 0, descriptor["size"][2]*.56), False, False)
    unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
    return definition, blueprint


def build_catalog(blueprints):
    catalog = shared.data_asset(
        "DA_EmergencySupportWeaponCatalog", ROOT + "/Data", unreal.WorldItemSeedCatalog)
    entries = []
    for descriptor in WEAPONS:
        entry = unreal.WorldItemSeedEntry()
        entry.set_editor_property("content_id", unreal.Name(descriptor["id"]))
        entry.set_editor_property("actor_class", blueprints[descriptor["id"]].generated_class())
        entry.set_editor_property("weight", descriptor["weight"])
        entry.set_editor_property("min_quantity", 1)
        entry.set_editor_property("max_quantity", 1)
        entry.set_editor_property("room_profiles", [unreal.Name(room) for room in descriptor["rooms"]])
        entry.set_editor_property("content_tags", [unreal.Name(tag) for tag in descriptor["tags"]])
        entries.append(entry)
    catalog.set_editor_property("catalog_id", unreal.Name("EmergencySupportWeapons"))
    catalog.set_editor_property("entries", entries)
    unreal.EditorAssetLibrary.save_loaded_asset(catalog)
    return catalog


def build_review_map(blueprints, review_material):
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        levels.load_level(MAP_PATH)
        actors.destroy_actors(actors.get_all_level_actors())
    elif not levels.new_level(MAP_PATH):
        raise RuntimeError("Could not create " + MAP_PATH)
    for index, descriptor in enumerate(WEAPONS):
        location = unreal.Vector(0, (index-2)*210, 24)
        actor = actors.spawn_actor_from_class(
            blueprints[descriptor["id"]].generated_class(), location, unreal.Rotator())
        actor.set_actor_label(f"EmergencySupport_{descriptor['concept']}_{descriptor['id']}")
        label = actors.spawn_actor_from_class(
            unreal.TextRenderActor, location+unreal.Vector(0, -70, 125), unreal.Rotator(0, 180, 0))
        label.text_render.set_text(f"{descriptor['concept']}  {descriptor['label'].upper()}")
        label.text_render.set_editor_property("world_size", 11)
    floor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator())
    floor.static_mesh_component.set_static_mesh(
        unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane.Plane"))
    floor.static_mesh_component.set_material(0, review_material)
    floor.set_actor_scale3d(unreal.Vector(8, 12, 1))
    light = actors.spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0, 0, 500), unreal.Rotator(-38, -32, 0))
    light.light_component.set_editor_property("intensity", 4.0)
    camera = actors.spawn_actor_from_class(
        unreal.CameraActor, unreal.Vector(760, -900, 420), unreal.Rotator(-20, 136, 0))
    camera.set_actor_label("EmergencySupport_ReviewCamera")
    if not levels.save_current_level():
        raise RuntimeError("Could not save " + MAP_PATH)


def main():
    mappings = {
        entry["id"]: entry
        for entry in json.loads(MAPPING_PATH.read_text(encoding="utf-8"))["mappings"]
    }
    shared.clean()
    first_use_material = material()
    meshes, definitions, blueprints = {}, {}, {}
    for descriptor in WEAPONS:
        mapping = mappings[descriptor["id"]]
        meshes[descriptor["id"]] = shared.static_mesh(
            descriptor, weapon_mesh(descriptor, mapping), first_use_material, mapping)
        definitions[descriptor["id"]], blueprints[descriptor["id"]] = build_weapon(
            descriptor, meshes[descriptor["id"]])
    catalog = build_catalog(blueprints)
    build_review_map(blueprints, first_use_material)
    unreal.EditorAssetLibrary.save_directory(ROOT, only_if_is_dirty=False, recursive=True)

    expected = (
        [f"{MESH_PATH}/SM_{descriptor['id']}" for descriptor in WEAPONS]
        + [f"{DATA_PATH}/DA_Weapon_{descriptor['id']}" for descriptor in WEAPONS]
        + [f"{BP_PATH}/BP_Weapon_{descriptor['id']}" for descriptor in WEAPONS]
        + [CATALOG_PATH, MAP_PATH]
    )
    missing = [path for path in expected if not unreal.EditorAssetLibrary.does_asset_exist(path)]
    if missing:
        raise RuntimeError("Missing generated assets: " + ", ".join(missing))
    records = []
    for descriptor in WEAPONS:
        bounds = meshes[descriptor["id"]].get_bounds().box_extent * 2.0
        records.append({
            "id": descriptor["id"],
            "concept": descriptor["concept"],
            "mesh": meshes[descriptor["id"]].get_path_name(),
            "definition": definitions[descriptor["id"]].get_path_name(),
            "blueprint": blueprints[descriptor["id"]].get_path_name(),
            "size_cm": [bounds.x, bounds.y, bounds.z],
            "delivery_mode": descriptor["base"]["mode"],
            "upgrade_levels": 2,
            "visual_state": "FactoryFirstUse",
            "fab_chassis": mappings[descriptor["id"]]["unrealAsset"],
        })
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps({
        "weapon_count": len(WEAPONS),
        "upgrade_stage_count": sum(len(item["upgrades"]) for item in WEAPONS),
        "catalog_entries": len(catalog.get_editor_property("entries")),
        "validated_asset_count": len(expected),
        "mapping": str(MAPPING_PATH),
        "catalog": catalog.get_path_name(),
        "review_map": MAP_PATH,
        "weapons": records,
    }, indent=2), encoding="utf-8")
    unreal.log("Built five emergency-support weapons with ten permanent upgrade stages")


for name, value in {
    "ROOT": ROOT, "MESH_PATH": MESH_PATH, "MATERIAL_PATH": MATERIAL_PATH,
    "DATA_PATH": DATA_PATH, "BP_PATH": BP_PATH, "CATALOG_PATH": CATALOG_PATH,
    "MAP_PATH": MAP_PATH, "SAFE_MAP_PATH": SAFE_MAP_PATH, "MAPPING_PATH": MAPPING_PATH,
    "REPORT_PATH": REPORT_PATH, "WEAPONS": WEAPONS,
}.items():
    setattr(shared, name, value)


if __name__ == "__main__":
    main()
