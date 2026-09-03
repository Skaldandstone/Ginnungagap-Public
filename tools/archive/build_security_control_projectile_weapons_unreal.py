"""Build five clean, upgradable security-control projectile weapons in Unreal."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
SHARED_PATH = PROJECT / "tools/build_early_projectile_weapons_unreal.py"
SPEC = importlib.util.spec_from_file_location("projectile_weapon_builder_shared", SHARED_PATH)
shared = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(shared)

ROOT = "/Game/Assets/Gameplay/SecurityControlProjectileWeapons"
MESH_PATH = ROOT + "/Meshes"
MATERIAL_PATH = ROOT + "/Materials"
DATA_PATH = ROOT + "/Data/Weapons"
BP_PATH = ROOT + "/Blueprints"
CATALOG_PATH = ROOT + "/Data/DA_SecurityControlProjectileWeaponCatalog"
MAP_PATH = "/Game/Assets/Maps/ModelLibrary/L_SecurityControlProjectileWeapons_Unreal"
SAFE_MAP_PATH = "/Game/Assets/Maps/ModelLibrary/L_GameplayModelLibrary"
MAPPING_PATH = PROJECT / "Art/Weapons/ConceptMappings/SecurityControlProjectileWeapons.json"
REPORT_PATH = PROJECT / "Saved/Reports/SecurityControlProjectileWeaponsUnreal.json"

WEAPONS = (
    dict(
        id="FrangibleBatonLauncher", label="Frangible Baton Launcher", concept=51,
        size=(88, 34, 40), envelope="STANDARD", chassis_scale=.70,
        rooms=["Security", "Armory", "Brig", "CrewCommons"], weight=.58,
        tags=["Weapon.Projectile", "Weapon.Control", "Security.LessLethal", "Ammo.Baton"],
        player=True, aerial=True, robotic=True,
        base=dict(range=1450, speed=3900, gravity=.10, damage=8, impulse=21000, recoil=1800, cooldown=.62, spread=1.4,
                  control="STAGGER", duration=.75, movement=.30),
        upgrades=(
            dict(id="IndexedCassette", label="Indexed Cassette", description="Indexes the four-tube cassette for faster follow-up shots.", resource="STRUCTURAL_ALLOY", cost=7,
                 range=1650, speed=4200, gravity=.08, damage=10, impulse=23500, recoil=1800, cooldown=.42, spread=1.0,
                 control="STAGGER", duration=1.0, movement=.25),
            dict(id="RecoilShunt", label="Recoil Shunt", description="Routes launch impulse through the receiver and tightens baton placement.", resource="SENSOR_COMPONENTS", cost=9,
                 range=1950, speed=4700, gravity=.06, damage=13, impulse=27000, recoil=1350, cooldown=.34, spread=.55,
                 control="STAGGER", duration=1.25, movement=.20),
        ),
        unsafe=dict(range=2300, speed=5400, gravity=.04, damage=29, impulse=36000, recoil=3300, cooldown=.38, spread=.75,
                    control="STAGGER", duration=1.5, movement=.12, hull=.08, breach=.025),
    ),
    dict(
        id="InflatableRestraintBagProjector", label="Inflatable Restraint Bag Projector", concept=52,
        size=(82, 46, 48), envelope="BULKY", chassis_scale=.62,
        rooms=["Brig", "Medical", "Security", "Rescue"], weight=.42,
        tags=["Weapon.Projectile", "Weapon.Control", "Security.Restraint", "Ammo.RestraintBag"],
        player=True, aerial=False, robotic=True,
        base=dict(range=900, speed=1800, gravity=.42, damage=1, impulse=24000, recoil=1500, cooldown=1.20, spread=2.0,
                  control="RESTRAIN", duration=2.5, movement=0.0),
        upgrades=(
            dict(id="QuickInflateValve", label="Quick-Inflate Valve", description="Inflates the restraint envelope sooner and extends useful launch distance.", resource="POWER_CELLS", cost=6,
                 range=1100, speed=2150, gravity=.34, damage=2, impulse=27000, recoil=1450, cooldown=.98, spread=1.5,
                 control="RESTRAIN", duration=3.5, movement=0.0),
            dict(id="ReinforcedBagPack", label="Reinforced Bag Pack", description="A stronger folded envelope tolerates a faster, more accurate launch.", resource="STRUCTURAL_ALLOY", cost=10,
                 range=1350, speed=2550, gravity=.26, damage=3, impulse=32000, recoil=1650, cooldown=.82, spread=.9,
                 control="RESTRAIN", duration=4.5, movement=0.0),
        ),
        unsafe=dict(range=1550, speed=3100, gravity=.20, damage=18, impulse=45000, recoil=4100, cooldown=.90, spread=1.2,
                    control="RESTRAIN", duration=5.0, movement=0.0, hull=.045, breach=.01),
    ),
    dict(
        id="ConductiveNetCaster", label="Conductive Net Caster", concept=53,
        size=(94, 42, 44), envelope="STANDARD", chassis_scale=.68,
        rooms=["Security", "Brig", "Cargo", "Engineering"], weight=.38,
        tags=["Weapon.Projectile", "Weapon.Control", "Security.Net", "Ammo.NetWeights"],
        player=True, aerial=True, robotic=True,
        base=dict(range=1250, speed=2550, gravity=.26, damage=3, impulse=8000, recoil=1900, cooldown=1.05, spread=4.8, projectiles=4,
                  control="CONDUCTIVE_STUN", duration=1.2, movement=0.0),
        upgrades=(
            dict(id="WeightedCorners", label="Weighted Corners", description="Matched corner masses make the net open evenly in flight.", resource="STRUCTURAL_ALLOY", cost=8,
                 range=1550, speed=3000, gravity=.20, damage=4, impulse=9500, recoil=2050, cooldown=.88, spread=3.5, projectiles=4,
                 control="CONDUCTIVE_STUN", duration=1.8, movement=0.0),
            dict(id="PulseCapacitor", label="Pulse Capacitor", description="Smart timing improves net deployment and conductive contact energy.", resource="POWER_CELLS", cost=11,
                 range=1850, speed=3450, gravity=.15, damage=5, impulse=11000, recoil=2100, cooldown=.72, spread=2.6, projectiles=4,
                 control="CONDUCTIVE_STUN", duration=2.4, movement=0.0),
        ),
        unsafe=dict(range=2100, speed=4100, gravity=.10, damage=8, impulse=15000, recoil=3900, cooldown=.78, spread=3.0, projectiles=4,
                    control="CONDUCTIVE_STUN", duration=2.8, movement=0.0, hull=.07, breach=.02),
    ),
    dict(
        id="MarkerDyeCapsuleLauncher", label="Marker-Dye Capsule Launcher", concept=57,
        size=(76, 30, 36), envelope="COMPACT", chassis_scale=.70,
        rooms=["Security", "Cargo", "Science", "Airlock"], weight=.66,
        tags=["Weapon.Projectile", "Weapon.Control", "Security.Marker", "Ammo.DyeCapsule"],
        player=True, aerial=True, robotic=True,
        base=dict(range=1700, speed=3600, gravity=.14, damage=2, impulse=6500, recoil=850, cooldown=.52, spread=1.5,
                  control="MARK", duration=8.0, movement=1.0),
        upgrades=(
            dict(id="PressureRegulator", label="Pressure Regulator", description="Consistent capsule pressure improves range and shot cadence.", resource="POWER_CELLS", cost=5,
                 range=2100, speed=4100, gravity=.10, damage=3, impulse=7000, recoil=800, cooldown=.38, spread=.9,
                 control="MARK", duration=12.0, movement=1.0),
            dict(id="SmartCapsuleFuse", label="Smart Capsule Fuse", description="Proximity sensing bursts the dye capsule close to the intended target.", resource="SENSOR_COMPONENTS", cost=8,
                 range=2500, speed=4700, gravity=.07, damage=4, impulse=7500, recoil=780, cooldown=.30, spread=.4,
                 control="MARK", duration=16.0, movement=1.0),
        ),
        unsafe=dict(range=2800, speed=5200, gravity=.05, damage=16, impulse=12000, recoil=1700, cooldown=.34, spread=.55,
                    control="MARK", duration=20.0, movement=1.0, hull=.035, breach=.008),
    ),
    dict(
        id="AdhesiveBolaThrower", label="Adhesive Bola Thrower", concept=59,
        size=(84, 38, 40), envelope="STANDARD", chassis_scale=.66,
        rooms=["Security", "Brig", "Cargo", "Maintenance"], weight=.47,
        tags=["Weapon.Projectile", "Weapon.Control", "Security.Bola", "Ammo.AdhesiveBola"],
        player=True, aerial=True, robotic=True,
        base=dict(range=1050, speed=2300, gravity=.30, damage=4, impulse=10000, recoil=1450, cooldown=.92, spread=3.8, projectiles=2,
                  control="ADHESIVE_SLOW", duration=4.0, movement=.45),
        upgrades=(
            dict(id="BalancedWeights", label="Balanced Weights", description="Matched bola masses extend flight and close around the target predictably.", resource="STRUCTURAL_ALLOY", cost=7,
                 range=1350, speed=2750, gravity=.24, damage=5, impulse=12000, recoil=1500, cooldown=.75, spread=2.8, projectiles=2,
                 control="ADHESIVE_SLOW", duration=5.0, movement=.35),
            dict(id="QuickCureAdhesive", label="Quick-Cure Adhesive", description="A fast-setting compound improves control at longer engagement distances.", resource="SENSOR_COMPONENTS", cost=10,
                 range=1650, speed=3200, gravity=.18, damage=6, impulse=14500, recoil=1600, cooldown=.62, spread=2.0, projectiles=2,
                 control="ADHESIVE_SLOW", duration=7.0, movement=.25),
        ),
        unsafe=dict(range=1900, speed=3750, gravity=.13, damage=12, impulse=21000, recoil=3200, cooldown=.68, spread=2.3, projectiles=2,
                    control="ADHESIVE_SLOW", duration=8.0, movement=.15, hull=.065, breach=.018),
    ),
)


def weapon_mesh(descriptor, mapping):
    mesh = unreal.DynamicMesh()
    shared.copy_chassis(mesh, descriptor, mapping)
    length, width, height = descriptor["size"]
    weapon_id = descriptor["id"]

    if weapon_id == "FrangibleBatonLauncher":
        for side_y in (-1, 1):
            for side_z in (-1, 1):
                location = (length * .40, side_y * width * .14, height * (.55 + side_z * .13))
                shared.cylinder(mesh, location, height * .085, length * .34)
                shared.torus(mesh, (length * .57, location[1], location[2]), height * .105, 1.8)
    elif weapon_id == "InflatableRestraintBagProjector":
        shared.box(mesh, (length * .30, 0, height * .58), (length * .34, width * .74, height * .60))
        for side in (-1, 1):
            shared.box(mesh, (length * .28, side * width * .39, height * .58), (length * .28, width * .07, height * .48))
        shared.torus(mesh, (length * .49, 0, height * .58), height * .21, 3.4)
    elif weapon_id == "ConductiveNetCaster":
        front_x = length * .48
        for side_y in (-1, 1):
            shared.box(mesh, (front_x, side_y * width * .32, height * .58), (length * .25, width * .07, height * .60))
        for side_z in (-1, 1):
            shared.box(mesh, (front_x, 0, height * (.58 + side_z * .28)), (length * .25, width * .64, height * .06))
        for side_y in (-1, 1):
            for side_z in (-1, 1):
                shared.cylinder(mesh, (length * .62, side_y * width * .29, height * (.58 + side_z * .25)), height * .065, length * .18)
    elif weapon_id == "MarkerDyeCapsuleLauncher":
        shared.cylinder(mesh, (length * .28, 0, height * .58), height * .17, length * .44)
        shared.torus(mesh, (length * .49, 0, height * .58), height * .19, 2.6)
        shared.cylinder(mesh, (length * .56, 0, height * .58), height * .075, length * .20)
        shared.box(mesh, (length * .04, 0, height * .82), (length * .22, width * .30, height * .12))
    else:
        for side in (-1, 1):
            shared.cylinder(mesh, (length * .28, side * width * .18, height * .58), height * .13, length * .36)
            shared.torus(mesh, (length * .46, side * width * .18, height * .58), height * .15, 2.4)
        shared.box(mesh, (length * .51, 0, height * .58), (length * .22, width * .14, height * .14))
        shared.torus(mesh, (length * .61, 0, height * .58), height * .13, 2.2)

    mesh.discard_mesh_attributes()
    mesh.auto_generate_x_atlas_mesh_u_vs(0, unreal.GeometryScriptXAtlasOptions())
    mesh.recompute_normals(shared.NORMALS)
    return mesh


def material():
    result = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_SecurityControl_FirstUseCeramic", MATERIAL_PATH, unreal.Material, unreal.MaterialFactoryNew())
    base = unreal.MaterialEditingLibrary.create_material_expression(result, unreal.MaterialExpressionConstant3Vector, -300, -20)
    base.set_editor_property("constant", unreal.LinearColor(.50, .48, .40, 1))
    rough = unreal.MaterialEditingLibrary.create_material_expression(result, unreal.MaterialExpressionConstant, -300, 120)
    rough.set_editor_property("r", .42)
    metal = unreal.MaterialEditingLibrary.create_material_expression(result, unreal.MaterialExpressionConstant, -300, 210)
    metal.set_editor_property("r", .14)
    unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    unreal.MaterialEditingLibrary.recompile_material(result)
    unreal.EditorAssetLibrary.save_loaded_asset(result)
    return result


def firing_profile(values, unsafe=False):
    profile = shared.firing_profile(values, unsafe)
    profile.set_editor_property("projectiles_per_shot", values.get("projectiles", 1))
    if values.get("control"):
        profile.set_editor_property("control_effect", getattr(unreal.WeaponControlEffect, values["control"]))
        profile.set_editor_property("control_duration_seconds", values["duration"])
        profile.set_editor_property("control_movement_multiplier", values["movement"])
    return profile


def build_weapon(descriptor, mesh):
    definition = shared.data_asset("DA_Weapon_" + descriptor["id"], DATA_PATH, unreal.ShipboardWeaponDefinition)
    definition.set_editor_property("weapon_id", unreal.Name(descriptor["id"]))
    definition.set_editor_property("display_name", shared.text(descriptor["label"]))
    definition.set_editor_property("description", shared.text("Clean security-control projectile platform with two permanent upgrades and a removable illegal conversion."))
    definition.set_editor_property("weapon_mesh", mesh)
    definition.set_editor_property("muzzle_offset", unreal.Vector(descriptor["size"][0] * .50, 0, descriptor["size"][2] * .58))
    definition.set_editor_property("safe_profile", firing_profile(descriptor["base"]))
    definition.set_editor_property("unsafe_modified_profile", firing_profile(descriptor["unsafe"], True))
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

    blueprint = shared.blueprint("BP_Weapon_" + descriptor["id"], BP_PATH, unreal.ShipboardWeapon)
    cdo = unreal.get_default_object(blueprint.generated_class())
    cdo.set_editor_property("definition", definition)
    cdo.get_editor_property("visual_mesh").set_static_mesh(mesh)
    cdo.get_editor_property("muzzle").set_relative_location(
        unreal.Vector(descriptor["size"][0] * .50, 0, descriptor["size"][2] * .58), False, False)
    unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
    return definition, blueprint


def build_catalog(blueprints):
    catalog = shared.data_asset("DA_SecurityControlProjectileWeaponCatalog", ROOT + "/Data", unreal.WorldItemSeedCatalog)
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
    catalog.set_editor_property("catalog_id", unreal.Name("SecurityControlProjectileWeapons"))
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
        location = unreal.Vector(0, (index - 2) * 190, 20)
        actor = actors.spawn_actor_from_class(blueprints[descriptor["id"]].generated_class(), location, unreal.Rotator())
        actor.set_actor_label(f"SecurityControl_{descriptor['concept']}_{descriptor['id']}")
        label = actors.spawn_actor_from_class(unreal.TextRenderActor, location + unreal.Vector(0, -65, 100), unreal.Rotator(0, 180, 0))
        label.text_render.set_text(f"{descriptor['concept']}  {descriptor['label'].upper()}")
        label.text_render.set_editor_property("world_size", 11)
    floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator())
    floor.static_mesh_component.set_static_mesh(unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane.Plane"))
    floor.static_mesh_component.set_material(0, review_material)
    floor.set_actor_scale3d(unreal.Vector(7, 11, 1))
    light = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 500), unreal.Rotator(-38, -32, 0))
    light.light_component.set_editor_property("intensity", 4.0)
    camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(700, -850, 380), unreal.Rotator(-18, 135, 0))
    camera.set_actor_label("SecurityControlProjectile_ReviewCamera")
    if not levels.save_current_level():
        raise RuntimeError("Could not save " + MAP_PATH)


def main():
    mappings = {entry["id"]: entry for entry in json.loads(MAPPING_PATH.read_text(encoding="utf-8"))["mappings"]}
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
            "id": descriptor["id"], "concept": descriptor["concept"],
            "mesh": meshes[descriptor["id"]].get_path_name(),
            "definition": definitions[descriptor["id"]].get_path_name(),
            "blueprint": blueprints[descriptor["id"]].get_path_name(),
            "size_cm": [bounds.x, bounds.y, bounds.z],
            "delivery_mode": "PhysicalProjectile", "upgrade_levels": 2,
            "unsafe_conversion": True, "visual_state": "FactoryFirstUse",
            "fab_chassis": mappings[descriptor["id"]]["unrealAsset"],
        })
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps({
        "weapon_count": len(WEAPONS),
        "upgrade_stage_count": sum(len(descriptor["upgrades"]) for descriptor in WEAPONS),
        "catalog_entries": len(catalog.get_editor_property("entries")),
        "validated_asset_count": len(expected),
        "mapping": str(MAPPING_PATH), "catalog": catalog.get_path_name(), "review_map": MAP_PATH,
        "weapons": records,
    }, indent=2), encoding="utf-8")
    unreal.log("Built five security-control projectile platforms with ten permanent upgrade stages")


for name, value in {
    "ROOT": ROOT, "MESH_PATH": MESH_PATH, "MATERIAL_PATH": MATERIAL_PATH,
    "DATA_PATH": DATA_PATH, "BP_PATH": BP_PATH, "CATALOG_PATH": CATALOG_PATH,
    "MAP_PATH": MAP_PATH, "SAFE_MAP_PATH": SAFE_MAP_PATH, "MAPPING_PATH": MAPPING_PATH,
    "REPORT_PATH": REPORT_PATH, "WEAPONS": WEAPONS,
}.items():
    setattr(shared, name, value)


if __name__ == "__main__":
    main()
