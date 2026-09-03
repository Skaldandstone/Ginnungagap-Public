"""Build three early, permanently upgradable physical-projectile weapons in Unreal."""

from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = "/Game/Assets/Gameplay/EarlyProjectileWeapons"
MESH_PATH = ROOT + "/Meshes"
MATERIAL_PATH = ROOT + "/Materials"
DATA_PATH = ROOT + "/Data/Weapons"
BP_PATH = ROOT + "/Blueprints"
CATALOG_PATH = ROOT + "/Data/DA_EarlyProjectileWeaponCatalog"
MAP_PATH = "/Game/Assets/Maps/ModelLibrary/L_EarlyProjectileWeapons_Unreal"
SAFE_MAP_PATH = "/Game/Assets/Maps/ModelLibrary/L_GameplayModelLibrary"
PROJECT = Path(unreal.SystemLibrary.get_project_directory())
MAPPING_PATH = PROJECT / "Art/Weapons/ConceptMappings/EarlyProjectileWeapons.json"
REPORT_PATH = PROJECT / "Saved/Reports/EarlyProjectileWeaponsUnreal.json"

PRIMITIVE = unreal.GeometryScriptPrimitiveOptions()
NORMALS = unreal.GeometryScriptCalculateNormalsOptions()
REVOLVE = unreal.GeometryScriptRevolveOptions()

WEAPONS = (
    dict(
        id="BearingDispenser", label="Bearing Dispenser", concept=61,
        size=(68, 28, 34), envelope="COMPACT", chassis_scale=.76,
        rooms=["MachineShop", "Cargo", "CrewCommons"], weight=.88,
        tags=["Weapon.Projectile", "Weapon.Early", "Tool.Salvaged", "Ammo.Bearing"],
        player=True, aerial=True, robotic=True,
        base=dict(range=850, speed=2600, gravity=.22, damage=9, impulse=11500, recoil=1050, cooldown=.55, spread=2.2),
        upgrades=(
            dict(id="RegulatedFeed", label="Regulated Feed", description="Meters one bearing cleanly and cycles faster.", resource="STRUCTURAL_ALLOY", cost=4,
                 range=1000, speed=3000, gravity=.18, damage=11, impulse=13500, recoil=1150, cooldown=.42, spread=1.4),
            dict(id="FerricSleeve", label="Ferric Sleeve", description="Magnetic stabilization improves velocity and grouping.", resource="SENSOR_COMPONENTS", cost=5,
                 range=1300, speed=3500, gravity=.12, damage=15, impulse=16500, recoil=1450, cooldown=.36, spread=.7),
        ),
        unsafe=dict(range=1500, speed=4200, gravity=.08, damage=24, impulse=24000, recoil=2800, cooldown=.42, spread=1.2, hull=.07, breach=.025),
    ),
    dict(
        id="PressureBottleFastenerTool", label="Pressure-Bottle Fastener Tool", concept=63,
        size=(74, 30, 36), envelope="COMPACT", chassis_scale=.72,
        rooms=["Fabrication", "MachineShop", "Cargo"], weight=.76,
        tags=["Weapon.Projectile", "Weapon.Early", "Tool.Fastener", "Ammo.Fastener"],
        player=True, aerial=True, robotic=True,
        base=dict(range=1050, speed=3150, gravity=.12, damage=14, impulse=14500, recoil=1300, cooldown=.72, spread=1.0),
        upgrades=(
            dict(id="MeteredValve", label="Metered Valve", description="Recovers pressure between shots and flattens the fastener path.", resource="POWER_CELLS", cost=4,
                 range=1250, speed=3600, gravity=.09, damage=17, impulse=17000, recoil=1450, cooldown=.58, spread=.65),
            dict(id="StripFeeder", label="Strip Feeder", description="Adds an indexed fastener strip and reinforced guide collar.", resource="STRUCTURAL_ALLOY", cost=7,
                 range=1450, speed=4050, gravity=.06, damage=21, impulse=20500, recoil=1750, cooldown=.40, spread=.45),
        ),
        unsafe=dict(range=1650, speed=4700, gravity=.04, damage=36, impulse=32000, recoil=3900, cooldown=.48, spread=.6, hull=.11, breach=.045),
    ),
    dict(
        id="SmartSoftProjectileCarbine", label="Smart Soft-Projectile Carbine", concept=60,
        size=(102, 36, 40), envelope="STANDARD", chassis_scale=.84,
        rooms=["Security", "Armory", "Bridge", "CrewCommons"], weight=.42,
        tags=["Weapon.Projectile", "Weapon.Early", "Weapon.Carbine", "Ammo.SoftSlug"],
        player=True, aerial=False, robotic=True,
        base=dict(range=2200, speed=5000, gravity=.055, damage=12, impulse=15000, recoil=1450, cooldown=.20, spread=1.6),
        upgrades=(
            dict(id="GyroFireControl", label="Gyro Fire Control", description="Smart optic and inertial correction tighten follow-up shots.", resource="SENSOR_COMPONENTS", cost=8,
                 range=2700, speed=5400, gravity=.045, damage=14, impulse=16500, recoil=1250, cooldown=.17, spread=.75),
            dict(id="HighPressureReceiver", label="High-Pressure Receiver", description="Reinforced chamber accelerates denser frangible projectiles.", resource="STRUCTURAL_ALLOY", cost=10,
                 range=3200, speed=6200, gravity=.035, damage=19, impulse=21000, recoil=1900, cooldown=.14, spread=.45),
        ),
        unsafe=dict(range=3800, speed=7200, gravity=.025, damage=31, impulse=30000, recoil=3600, cooldown=.16, spread=.55, hull=.09, breach=.035),
    ),
)


def text(value):
    return unreal.TextLibrary.conv_string_to_text(value)


def xf(x=0, y=0, z=0, pitch=0, yaw=0, roll=0, sx=1, sy=1, sz=1):
    return unreal.Transform(
        location=unreal.Vector(x, y, z),
        rotation=unreal.Rotator(pitch=pitch, yaw=yaw, roll=roll),
        scale=unreal.Vector(sx, sy, sz),
    )


def box(mesh, loc, dims, rotation=(0, 0, 0)):
    mesh.append_box(PRIMITIVE, xf(*loc, pitch=rotation[0], yaw=rotation[1], roll=rotation[2]), *dims, 2, 2, 2)


def cylinder(mesh, loc, radius, length, axis="x"):
    rotation = {"x": (90, 0, 0), "y": (0, 0, 90), "z": (0, 0, 0)}[axis]
    mesh.append_cylinder(PRIMITIVE, xf(*loc, pitch=rotation[0], yaw=rotation[1], roll=rotation[2]), radius, length, 24, 2, True)


def torus(mesh, loc, major, minor, axis="x"):
    rotation = {"x": (90, 0, 0), "y": (0, 0, 90), "z": (0, 0, 0)}[axis]
    mesh.append_torus(PRIMITIVE, xf(*loc, pitch=rotation[0], yaw=rotation[1], roll=rotation[2]), REVOLVE, major, minor, 32, 10)


def copy_chassis(mesh, descriptor, mapping):
    asset = unreal.EditorAssetLibrary.load_asset(mapping["unrealAsset"])
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError("Fab chassis unavailable: " + mapping["unrealAsset"])
    donor = unreal.DynamicMesh()
    donor, outcome = unreal.GeometryScript_AssetUtils.copy_mesh_from_static_mesh_v2(
        asset, donor, unreal.GeometryScriptCopyMeshFromAssetOptions(), unreal.GeometryScriptMeshReadLOD(), False)
    if outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError(f"Could not copy {mapping['unrealAsset']}: {outcome}")
    bounds = asset.get_bounds()
    size = bounds.box_extent * 2.0
    dimensions = (size.x, size.y, size.z)
    longest_axis = max(range(3), key=lambda index: dimensions[index])
    uniform = descriptor["size"][0] * descriptor["chassis_scale"] / max(dimensions[longest_axis], .001)
    scale = unreal.Vector(uniform, uniform, uniform)
    origin = bounds.origin
    if longest_axis == 1:
        rotation = unreal.Rotator(pitch=0, yaw=-90, roll=0)
        transformed_origin = unreal.Vector(origin.y*uniform, -origin.x*uniform, origin.z*uniform)
    elif longest_axis == 2:
        rotation = unreal.Rotator(pitch=90, yaw=0, roll=0)
        transformed_origin = unreal.Vector(origin.z*uniform, origin.y*uniform, -origin.x*uniform)
    else:
        rotation = unreal.Rotator()
        transformed_origin = origin * uniform
    target_center = unreal.Vector(-descriptor["size"][0]*.08, 0, descriptor["size"][2]*.48)
    unreal.GeometryScript_MeshTransforms.transform_mesh(donor, unreal.Transform(
        location=target_center-transformed_origin, rotation=rotation, scale=scale))
    unreal.GeometryScript_MeshEdits.append_mesh(mesh, donor, unreal.Transform())


def weapon_mesh(descriptor, mapping):
    mesh = unreal.DynamicMesh()
    copy_chassis(mesh, descriptor, mapping)
    length, width, height = descriptor["size"]
    if descriptor["id"] == "BearingDispenser":
        cylinder(mesh, (length*.36, 0, height*.55), height*.20, length*.30)
        torus(mesh, (length*.50, 0, height*.55), height*.23, 3.0)
        cylinder(mesh, (-length*.10, width*.28, height*.56), height*.10, length*.22)
    elif descriptor["id"] == "PressureBottleFastenerTool":
        cylinder(mesh, (length*.34, 0, height*.56), height*.10, length*.34)
        torus(mesh, (length*.46, 0, height*.56), height*.24, 3.2)
        for side in (-1, 1):
            box(mesh, (length*.56, side*width*.16, height*.56), (length*.18, width*.08, height*.09))
    else:
        for side in (-1, 1):
            cylinder(mesh, (length*.35, side*width*.14, height*.57), height*.075, length*.34)
        cylinder(mesh, (length*.05, 0, height*.80), height*.085, length*.26)
        torus(mesh, (length*.50, 0, height*.57), height*.13, 2.4)
    mesh.discard_mesh_attributes()
    mesh.auto_generate_x_atlas_mesh_u_vs(0, unreal.GeometryScriptXAtlasOptions())
    mesh.recompute_normals(NORMALS)
    return mesh


def material():
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_EarlyProjectile_FirstUseCeramic", MATERIAL_PATH, unreal.Material, unreal.MaterialFactoryNew())
    base = unreal.MaterialEditingLibrary.create_material_expression(asset, unreal.MaterialExpressionConstant3Vector, -300, -20)
    base.set_editor_property("constant", unreal.LinearColor(.42, .36, .25, 1))
    rough = unreal.MaterialEditingLibrary.create_material_expression(asset, unreal.MaterialExpressionConstant, -300, 120)
    rough.set_editor_property("r", .38)
    metal = unreal.MaterialEditingLibrary.create_material_expression(asset, unreal.MaterialExpressionConstant, -300, 210)
    metal.set_editor_property("r", .18)
    unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    unreal.MaterialEditingLibrary.recompile_material(asset)
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def static_mesh(descriptor, dynamic_mesh, assigned_material, mapping):
    path = f"{MESH_PATH}/SM_{descriptor['id']}"
    asset, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
        dynamic_mesh, path, unreal.GeometryScriptCreateNewStaticMeshAssetOptions())
    if not asset or outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError(f"Could not create {path}: {outcome}")
    slot = unreal.StaticMaterial()
    slot.set_editor_property("material_interface", assigned_material)
    slot.set_editor_property("material_slot_name", unreal.Name("FirstUseSurface"))
    asset.set_editor_property("static_materials", [slot])
    body = asset.get_editor_property("body_setup")
    if body:
        body.set_editor_property("collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE)
    metadata = {
        "Ginnungagap.ContentId": descriptor["id"],
        "Ginnungagap.Concept": descriptor["concept"],
        "Ginnungagap.VisualState": "FactoryFirstUse",
        "Ginnungagap.FabChassis": mapping["unrealAsset"],
        "Ginnungagap.UpgradePath": ",".join(stage["id"] for stage in descriptor["upgrades"]),
    }
    for key, value in metadata.items():
        unreal.EditorAssetLibrary.set_metadata_tag(asset, key, str(value))
    unreal.EditorAssetLibrary.save_loaded_asset(asset)
    return asset


def firing_profile(values, unsafe=False):
    profile = unreal.WeaponFiringProfile()
    profile.set_editor_property("max_range_cm", values["range"])
    profile.set_editor_property("trace_radius_cm", 1.7)
    profile.set_editor_property("biological_damage", values["damage"])
    profile.set_editor_property("impact_impulse", values["impulse"])
    profile.set_editor_property("recoil_impulse", values["recoil"])
    profile.set_editor_property("cooldown_seconds", values["cooldown"])
    profile.set_editor_property("delivery_mode", unreal.WeaponDeliveryMode.PROJECTILE)
    profile.set_editor_property("projectile_speed_cm_per_second", values["speed"])
    profile.set_editor_property("projectile_gravity_scale", values["gravity"])
    profile.set_editor_property("projectiles_per_shot", 1)
    profile.set_editor_property("spread_half_angle_degrees", values["spread"])
    profile.set_editor_property("can_damage_hull", unsafe)
    profile.set_editor_property("hull_impact_severity", values.get("hull", 0))
    profile.set_editor_property("breach_severity", values.get("breach", 0))
    return profile


def envelope(descriptor):
    value = unreal.WeaponCollisionEnvelope()
    value.set_editor_property("envelope_class", getattr(unreal.WeaponEnvelopeClass, descriptor["envelope"]))
    value.set_editor_property("half_extents_cm", unreal.Vector(*(component*.5 for component in descriptor["size"])))
    value.set_editor_property("center_offset_cm", unreal.Vector(0, 0, descriptor["size"][2]*.5))
    return value


def data_asset(name, folder, cls):
    factory = unreal.DataAssetFactory()
    factory.set_editor_property("data_asset_class", cls)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, cls, factory)
    if not asset:
        raise RuntimeError(f"Could not create {folder}/{name}")
    return asset


def blueprint(name, folder, parent):
    factory = unreal.BlueprintFactory()
    factory.set_editor_property("parent_class", parent)
    asset = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, folder, unreal.Blueprint, factory)
    if not asset:
        raise RuntimeError(f"Could not create {folder}/{name}")
    return asset


def build_weapon(descriptor, mesh):
    definition = data_asset("DA_Weapon_" + descriptor["id"], DATA_PATH, unreal.ShipboardWeaponDefinition)
    definition.set_editor_property("weapon_id", unreal.Name(descriptor["id"]))
    definition.set_editor_property("display_name", text(descriptor["label"]))
    definition.set_editor_property("description", text("Early civilian projectile platform with two permanent upgrades and a removable hazardous conversion."))
    definition.set_editor_property("weapon_mesh", mesh)
    definition.set_editor_property("muzzle_offset", unreal.Vector(descriptor["size"][0]*.50, 0, descriptor["size"][2]*.56))
    definition.set_editor_property("safe_profile", firing_profile(descriptor["base"]))
    definition.set_editor_property("unsafe_modified_profile", firing_profile(descriptor["unsafe"], True))
    stages = []
    for source in descriptor["upgrades"]:
        stage = unreal.WeaponUpgradeStage()
        stage.set_editor_property("upgrade_id", unreal.Name(source["id"]))
        stage.set_editor_property("display_name", text(source["label"]))
        stage.set_editor_property("description", text(source["description"]))
        stage.set_editor_property("firing_profile", firing_profile(source))
        stage.set_editor_property("cost_resource", getattr(unreal.WeaponUpgradeResource, source["resource"]))
        stage.set_editor_property("resource_cost", source["cost"])
        stages.append(stage)
    definition.set_editor_property("upgrade_stages", stages)
    definition.set_editor_property("collision_envelope", envelope(descriptor))
    definition.set_editor_property("player_compatible", descriptor["player"])
    definition.set_editor_property("aerial_drone_compatible", descriptor["aerial"])
    definition.set_editor_property("robotic_drone_compatible", descriptor["robotic"])
    definition.set_editor_property("unsafe_modification_requires_soldier", True)
    unreal.EditorAssetLibrary.save_loaded_asset(definition)

    bp = blueprint("BP_Weapon_" + descriptor["id"], BP_PATH, unreal.ShipboardWeapon)
    cdo = unreal.get_default_object(bp.generated_class())
    cdo.set_editor_property("definition", definition)
    cdo.get_editor_property("visual_mesh").set_static_mesh(mesh)
    cdo.get_editor_property("muzzle").set_relative_location(
        unreal.Vector(descriptor["size"][0]*.50, 0, descriptor["size"][2]*.56), False, False)
    unreal.EditorAssetLibrary.save_loaded_asset(bp)
    return definition, bp


def build_catalog(blueprints):
    catalog = data_asset("DA_EarlyProjectileWeaponCatalog", ROOT + "/Data", unreal.WorldItemSeedCatalog)
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
    catalog.set_editor_property("catalog_id", unreal.Name("EarlyProjectileWeapons"))
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
        location = unreal.Vector(0, (index-1)*240, 18)
        actor = actors.spawn_actor_from_class(blueprints[descriptor["id"]].generated_class(), location, unreal.Rotator())
        actor.set_actor_label(f"EarlyProjectile_{descriptor['concept']}_{descriptor['id']}")
        label = actors.spawn_actor_from_class(unreal.TextRenderActor, location+unreal.Vector(0, -70, 105), unreal.Rotator(0, 180, 0))
        label.text_render.set_text(f"{descriptor['concept']}  {descriptor['label'].upper()}")
        label.text_render.set_editor_property("world_size", 13)
    floor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(0, 0, 0), unreal.Rotator())
    floor.static_mesh_component.set_static_mesh(unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Plane.Plane"))
    floor.static_mesh_component.set_material(0, review_material)
    floor.set_actor_scale3d(unreal.Vector(6, 8, 1))
    light = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 500), unreal.Rotator(-38, -32, 0))
    light.light_component.set_editor_property("intensity", 4.0)
    camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(650, -650, 330), unreal.Rotator(-18, 135, 0))
    camera.set_actor_label("EarlyProjectile_ReviewCamera")
    if not levels.save_current_level():
        raise RuntimeError("Could not save " + MAP_PATH)


def clean():
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
        if unreal.EditorAssetLibrary.does_asset_exist(SAFE_MAP_PATH):
            levels.load_level(SAFE_MAP_PATH)
        unreal.EditorAssetLibrary.delete_asset(MAP_PATH)
    if unreal.EditorAssetLibrary.does_directory_exist(ROOT):
        unreal.EditorAssetLibrary.delete_directory(ROOT)
    for path in (ROOT, MESH_PATH, MATERIAL_PATH, DATA_PATH, BP_PATH):
        unreal.EditorAssetLibrary.make_directory(path)


def main():
    mappings = {entry["id"]: entry for entry in json.loads(MAPPING_PATH.read_text(encoding="utf-8"))["mappings"]}
    clean()
    first_use_material = material()
    meshes, definitions, blueprints = {}, {}, {}
    for descriptor in WEAPONS:
        mapping = mappings[descriptor["id"]]
        meshes[descriptor["id"]] = static_mesh(descriptor, weapon_mesh(descriptor, mapping), first_use_material, mapping)
        definitions[descriptor["id"]], blueprints[descriptor["id"]] = build_weapon(descriptor, meshes[descriptor["id"]])
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
        "weapon_count": len(WEAPONS), "upgrade_stage_count": sum(len(d["upgrades"]) for d in WEAPONS),
        "catalog_entries": len(catalog.get_editor_property("entries")), "validated_asset_count": len(expected),
        "mapping": str(MAPPING_PATH), "catalog": catalog.get_path_name(), "review_map": MAP_PATH,
        "weapons": records,
    }, indent=2), encoding="utf-8")
    unreal.log("Built three early physical-projectile weapon platforms with six permanent upgrade stages")


if __name__ == "__main__":
    main()
