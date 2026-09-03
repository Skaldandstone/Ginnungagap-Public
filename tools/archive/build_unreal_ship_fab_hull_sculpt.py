"""Build concept-first capital-ship hull sculpts with native Fab pack detail.

The primary silhouettes are authored in Unreal Geometry Script.  Newly installed
Fab packs are used only for the few forms they do better than procedural blockout:
hangar interiors, command architecture, habitat machinery, and antennas.
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
REPORT = PROJECT / "Saved/Reports/UnrealShipFabHullSculpt.json"
ROOT = "/Game/Assets/Ships/Exterior"
PRIMITIVE = unreal.GeometryScriptPrimitiveOptions()
NORMALS = unreal.GeometryScriptCalculateNormalsOptions(angle_weighted=True, area_weighted=True)
IDENTITY = unreal.Transform()

MATERIALS = {
    "armor": "/Game/MaterialsScifi/Materials/Instances/MI_Scifi_Panels_09",
    "armor_light": "/Game/MaterialsScifi/Materials/Instances/MI_Scifi_Panels_06",
    "structure": "/Game/MaterialsScifi/Materials/Instances/MI_Scifi_Panels_13",
    "emissive": "/Game/MaterialsScifi/Materials/Instances/MI_Scifi_Panels_14",
}

DONORS = {
    "hangar": "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Hangar/SM_hangar",
    "command": "/Game/Ice_Station/Meshes/Building/SM_base_building_big",
    "command_detail": "/Game/Ice_Station/Meshes/Antennas/SM_building_details_01",
    "habitat": "/Game/SciFi_Cliff/Meshes/Circular_module/SM_circular_module_03",
    "antenna": "/Game/SciFi_Cliff/Meshes/Antenna/SM_antenna_02",
    "generator": "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_POWER_GENERATOR_01",
}

SHIPS = {
    "MilitaryCorvette": {
        "expected_cm": (240000.0, 43000.0, 62000.0),
        "source_map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_Sculpt",
        "map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_FabHullSculpt",
    },
    "ExpeditionCarrier": {
        "expected_cm": (650000.0, 140000.0, 180000.0),
        "source_map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_Sculpt",
        "map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_FabHullSculpt",
    },
}


def xf(x=0.0, y=0.0, z=0.0, pitch=0.0, yaw=0.0, roll=0.0,
       sx=1.0, sy=1.0, sz=1.0):
    return unreal.Transform(
        location=unreal.Vector(x, y, z),
        rotation=unreal.Rotator(pitch=pitch, yaw=yaw, roll=roll),
        scale=unreal.Vector(sx, sy, sz),
    )


def ellipsoid(center, half_size, longitude=96, latitude=64):
    mesh = unreal.DynamicMesh()
    mesh.append_sphere_lat_long(
        PRIMITIVE,
        xf(center[0], center[1], center[2],
           sx=half_size[0] / 1000.0,
           sy=half_size[1] / 1000.0,
           sz=half_size[2] / 1000.0),
        1000.0,
        longitude,
        latitude,
    )
    return mesh


def box_mesh(center, size, subdivisions=(2, 2, 2)):
    mesh = unreal.DynamicMesh()
    # Geometry Script boxes are centered in X/Y but use the transform Z as
    # their base plane, unlike spheres.  Accept bounds centers throughout the
    # authoring code and convert here.
    base = (center[0], center[1], center[2] - size[2] * 0.5)
    mesh.append_box(
        PRIMITIVE, xf(*base), size[0], size[1], size[2],
        subdivisions[0], subdivisions[1], subdivisions[2],
    )
    return mesh


def subtract_box(mesh, center, size):
    cutter = box_mesh(center, size)
    mesh.apply_mesh_boolean(
        IDENTITY, cutter, IDENTITY,
        unreal.GeometryScriptBooleanOperation.SUBTRACT,
        unreal.GeometryScriptMeshBooleanOptions(),
    )


def boxes(entries):
    mesh = unreal.DynamicMesh()
    for center, size in entries:
        base = (center[0], center[1], center[2] - size[2] * 0.5)
        mesh.append_box(PRIMITIVE, xf(*base), size[0], size[1], size[2], 2, 2, 2)
    mesh.recompute_normals(NORMALS)
    return mesh


def ellipsoids(entries, longitude=48, latitude=32):
    mesh = unreal.DynamicMesh()
    for center, half_size in entries:
        mesh.append_sphere_lat_long(
            PRIMITIVE,
            xf(center[0], center[1], center[2],
               sx=half_size[0] / 1000.0,
               sy=half_size[1] / 1000.0,
               sz=half_size[2] / 1000.0),
            1000.0,
            longitude,
            latitude,
        )
    mesh.recompute_normals(NORMALS)
    return mesh


def create_asset(folder, name, mesh, material_path, role):
    unreal.EditorAssetLibrary.make_directory(folder)
    path = f"{folder}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        if not unreal.EditorAssetLibrary.delete_asset(path):
            raise RuntimeError(f"Could not replace {path}")
    mesh.auto_repair_normals()
    mesh.recompute_normals(NORMALS)
    options = unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    asset, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
        mesh, path, options
    )
    if not asset or outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError(f"Could not create {path}: {outcome}")
    material = unreal.EditorAssetLibrary.load_asset(material_path)
    if not isinstance(material, unreal.MaterialInterface):
        raise RuntimeError(f"Missing Fab hull material {material_path}")
    slot = unreal.StaticMaterial()
    slot.set_editor_property("material_interface", material)
    slot.set_editor_property("material_slot_name", unreal.Name(role))
    asset.set_editor_property("static_materials", [slot])
    asset.set_editor_property("light_map_resolution", 256)
    asset.set_editor_property("light_map_coordinate_index", 0)
    body_setup = asset.get_editor_property("body_setup")
    if body_setup:
        body_setup.set_editor_property(
            "collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
        )
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "ShipSculpt.Iteration", "Iteration_04_FabHullSculpt")
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "ShipSculpt.Tool", "Unreal Geometry Script")
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "ShipSculpt.Role", role)
    if not unreal.EditorAssetLibrary.save_loaded_asset(asset):
        raise RuntimeError(f"Could not save {path}")
    return asset


def corvette_assets():
    folder = ROOT + "/UnrealSculpt/MilitaryCorvette/Working/Iteration_04_FabHullSculpt"
    core = ellipsoid((0, 0, -4500), (115000, 19500, 20500))
    # The concept-defining paired hangars are real recesses, cut into both flanks.
    for side in (-1, 1):
        subtract_box(core, (43000, side * 19000, -3500), (65000, 12500, 19000))
    assets = {
        "Core": create_asset(folder, "SM_MilitaryCorvette_FabHullCore", core, MATERIALS["armor"], "Armor"),
        "ArmorBlocks": create_asset(
            folder, "SM_MilitaryCorvette_FabHullArmorBlocks",
            boxes([
                ((-97000, 0, 13500), (28000, 30000, 3500)),
                ((-70000, 0, 15000), (28000, 36000, 4000)),
                ((-42000, 0, 16000), (27000, 39000, 4000)),
                ((-15000, 0, 16500), (27000, 40000, 4000)),
                ((12000, 0, 16500), (27000, 40000, 4000)),
                ((39000, 0, 16000), (27000, 39000, 4000)),
                ((66000, 0, 15000), (27000, 36000, 4000)),
                ((92000, 0, 13000), (25000, 30000, 3500)),
                ((111000, 0, 9500), (13000, 22000, 3000)),
                ((-82000, -20500, -4500), (26000, 2000, 16000)),
                ((-52000, -20500, -3000), (26000, 2000, 18000)),
                ((-22000, -20500, -2000), (26000, 2000, 19000)),
                ((8000, -20500, -2000), (26000, 2000, 19000)),
                ((-82000, 20500, -4500), (26000, 2000, 16000)),
                ((-52000, 20500, -3000), (26000, 2000, 18000)),
                ((-22000, 20500, -2000), (26000, 2000, 19000)),
                ((8000, 20500, -2000), (26000, 2000, 19000)),
            ]), MATERIALS["armor"], "SteppedArmor"
        ),
        "Crown": create_asset(
            folder, "SM_MilitaryCorvette_FabHullCrown",
            boxes([
                ((-25000, 0, 18500), (82000, 27000, 7000)),
                ((-25000, 0, 23500), (56000, 19000, 5000)),
                ((-25000, 0, 27500), (30000, 11000, 3000)),
            ]), MATERIALS["armor_light"], "BuriedCommandArmor"
        ),
        "Keel": create_asset(
            folder, "SM_MilitaryCorvette_FabHullKeel",
            ellipsoid((-10000, 0, -28600), (72000, 15500, 2400), 72, 32),
            MATERIALS["structure"], "Structure"
        ),
    }
    frame_boxes = []
    for side in (-1, 1):
        y = side * 21000
        frame_boxes.extend([
            ((10500, y, -3500), (3500, 1000, 23000)),
            ((75500, y, -3500), (3500, 1000, 23000)),
            ((43000, y, 8000), (68500, 1000, 3000)),
            ((43000, y, -15000), (68500, 1000, 3000)),
        ])
    # Exact bow/stern anchors preserve the approved 2.4 km envelope.
    frame_boxes.extend([
        ((-117000, 0, -4000), (6000, 39000, 42000)),
        ((117500, 0, -4500), (5000, 30000, 29000)),
    ])
    assets["Frames"] = create_asset(
        folder, "SM_MilitaryCorvette_FabHullFrames", boxes(frame_boxes),
        MATERIALS["structure"], "Structure"
    )
    drive = unreal.DynamicMesh()
    glow = unreal.DynamicMesh()
    for y in (-12000, -4000, 4000, 12000):
        for z in (-12000, -4000, 4000, 12000):
            drive.append_cylinder(PRIMITIVE, xf(-114000, y, z, pitch=90), 2700, 6000, 32, 2, True)
            glow.append_cylinder(PRIMITIVE, xf(-119600, y, z, pitch=90), 1900, 400, 32, 1, True)
    assets["Drive"] = create_asset(folder, "SM_MilitaryCorvette_FabHullDrive", drive, MATERIALS["structure"], "DriveHousing")
    assets["DriveGlow"] = create_asset(folder, "SM_MilitaryCorvette_FabHullDriveGlow", glow, MATERIALS["emissive"], "DriveGlow")
    return folder, assets


def carrier_assets():
    folder = ROOT + "/UnrealSculpt/ExpeditionCarrier/Working/Iteration_04_FabHullSculpt"
    core = ellipsoid((0, 0, -10000), (315000, 65000, 65000), 128, 72)
    for side in (-1, 1):
        subtract_box(core, (135000, side * 63500, -12000), (160000, 23000, 48000))
    assets = {
        "Core": create_asset(folder, "SM_ExpeditionCarrier_FabHullCore", core, MATERIALS["armor"], "Armor"),
        "ArmorBlocks": create_asset(
            folder, "SM_ExpeditionCarrier_FabHullArmorBlocks",
            boxes([
                ((-278000, 0, 43000), (70000, 90000, 7000)),
                ((-210000, 0, 51000), (66000, 116000, 8000)),
                ((-145000, 0, 56000), (63000, 126000, 8000)),
                ((-82000, 0, 59000), (62000, 130000, 8000)),
                ((-20000, 0, 59000), (62000, 130000, 8000)),
                ((42000, 0, 59000), (62000, 130000, 8000)),
                ((104000, 0, 57000), (62000, 128000, 8000)),
                ((166000, 0, 54000), (62000, 122000, 8000)),
                ((228000, 0, 49000), (62000, 110000, 8000)),
                ((282000, 0, 39000), (48000, 82000, 7000)),
                ((-250000, -67000, -12000), (52000, 6000, 50000)),
                ((-185000, -67000, -10000), (52000, 6000, 58000)),
                ((-120000, -67000, -9000), (52000, 6000, 62000)),
                ((-55000, -67000, -8000), (52000, 6000, 64000)),
                ((10000, -67000, -8000), (52000, 6000, 64000)),
                ((-250000, 67000, -12000), (52000, 6000, 50000)),
                ((-185000, 67000, -10000), (52000, 6000, 58000)),
                ((-120000, 67000, -9000), (52000, 6000, 62000)),
                ((-55000, 67000, -8000), (52000, 6000, 64000)),
                ((10000, 67000, -8000), (52000, 6000, 64000)),
            ]), MATERIALS["armor"], "SteppedArmor"
        ),
        "Crown": create_asset(
            folder, "SM_ExpeditionCarrier_FabHullCrown",
            boxes([
                ((-45000, 0, 64000), (210000, 90000, 10000)),
                ((-45000, 0, 73000), (150000, 65000, 8000)),
                ((-45000, 0, 81000), (90000, 40000, 8000)),
                ((-45000, 0, 87500), (42000, 22000, 5000)),
            ]), MATERIALS["armor_light"], "BuriedCommandArmor"
        ),
        "Keel": create_asset(
            folder, "SM_ExpeditionCarrier_FabHullKeel",
            ellipsoid((-20000, 0, -87000), (190000, 52000, 3000), 96, 32),
            MATERIALS["structure"], "Structure"
        ),
    }
    frame_boxes = []
    for side in (-1, 1):
        y = side * 69000
        frame_boxes.extend([
            ((55000, y, -12000), (5000, 2000, 56000)),
            ((215000, y, -12000), (5000, 2000, 56000)),
            ((135000, y, 16000), (165000, 2000, 5000)),
            ((135000, y, -40000), (165000, 2000, 5000)),
        ])
    frame_boxes.extend([
        ((-319000, 0, -10000), (12000, 118000, 130000)),
        ((319000, 0, -12000), (12000, 90000, 90000)),
    ])
    assets["Frames"] = create_asset(
        folder, "SM_ExpeditionCarrier_FabHullFrames", boxes(frame_boxes),
        MATERIALS["structure"], "Structure"
    )
    drive = unreal.DynamicMesh()
    glow = unreal.DynamicMesh()
    for y in (-45000, -15000, 15000, 45000):
        for z in (-33000, 0, 33000):
            drive.append_cylinder(PRIMITIVE, xf(-311000, y, z, pitch=90), 9300, 14000, 40, 2, True)
            glow.append_cylinder(PRIMITIVE, xf(-324400, y, z, pitch=90), 6700, 600, 40, 1, True)
    assets["Drive"] = create_asset(folder, "SM_ExpeditionCarrier_FabHullDrive", drive, MATERIALS["structure"], "DriveHousing")
    assets["DriveGlow"] = create_asset(folder, "SM_ExpeditionCarrier_FabHullDriveGlow", glow, MATERIALS["emissive"], "DriveGlow")
    drums = []
    for side in (-1, 1):
        for x in (-165000, -105000, -45000, 15000, 75000):
            drums.append(((x, side * 61000, -12000), (25000, 9000, 26000)))
    assets["HabitatDrums"] = create_asset(
        folder, "SM_ExpeditionCarrier_FabHullHabitatDrums",
        ellipsoids(drums), MATERIALS["structure"], "HabitatDrums"
    )
    return folder, assets


def spawn_mesh(actors, mesh, label, location=(0, 0, 0), target_size=None):
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator()
    )
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(mesh)
    if target_size:
        bounds = mesh.get_bounds()
        size = bounds.box_extent * 2.0
        if min(size.x, size.y, size.z) <= 0:
            raise RuntimeError(f"Invalid bounds for {mesh.get_path_name()}")
        scale = unreal.Vector(
            target_size[0] / size.x,
            target_size[1] / size.y,
            target_size[2] / size.z,
        )
        actor.set_actor_scale3d(scale)
        # Fab meshes commonly use a corner or floor pivot.  Treat placement
        # coordinates as the intended bounds center so modules sit cleanly in
        # the authored hull instead of drifting by their scaled source origin.
        actor.set_actor_location(unreal.Vector(
            location[0] - bounds.origin.x * scale.x,
            location[1] - bounds.origin.y * scale.y,
            location[2] - bounds.origin.z * scale.z,
        ), False, False)
    return actor


def load_donor(key):
    path = DONORS[key]
    asset = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError(f"Missing installed Fab donor {key}: {path}")
    return asset


def create_review_map(ship_name, config, generated):
    if not unreal.EditorAssetLibrary.does_asset_exist(config["map"]):
        duplicate = unreal.EditorAssetLibrary.duplicate_asset(config["source_map"], config["map"])
        if duplicate is None:
            raise RuntimeError(f"Could not duplicate {config['source_map']} to {config['map']}")
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not levels.load_level(config["map"]):
        raise RuntimeError(f"Could not load {config['map']}")
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in actors.get_all_level_actors():
        label = actor.get_actor_label()
        if label.startswith("FAB_HULL_"):
            actors.destroy_actor(actor)
        elif label.startswith("SCULPT_WORKING_") or label.startswith("FAB_CONCEPT_"):
            actor.set_actor_hidden_in_game(True)
            actor.set_is_temporarily_hidden_in_editor(True)

    built = []
    for role, mesh in generated.items():
        built.append(spawn_mesh(actors, mesh, f"FAB_HULL_{ship_name}_{role}"))

    donor_rows = []
    if ship_name == "MilitaryCorvette":
        placements = [
            ("hangar", "HangarPort", (43000, -14500, -3500), (56000, 5000, 14500)),
            ("hangar", "HangarStarboard", (43000, 14500, -3500), (56000, 5000, 14500)),
            ("command", "BuriedCommand", (-25000, 0, 29200), (23000, 10500, 3000)),
            ("command_detail", "CommandDetail", (-25000, 0, 30600), (17000, 8500, 600)),
            ("antenna", "SensorMast", (-25000, 0, 30900), (1300, 1300, 200)),
        ]
    else:
        placements = [
            ("hangar", "ConcoursePort", (135000, -56000, -12000), (145000, 12000, 37000)),
            ("hangar", "ConcourseStarboard", (135000, 56000, -12000), (145000, 12000, 37000)),
            ("command", "CommandCity", (-45000, 0, 86500), (52000, 25000, 6000)),
            ("command_detail", "CommandCityDetail", (-45000, 0, 88900), (36000, 18000, 1800)),
            ("antenna", "LongRangeSensor", (-40000, 0, 89800), (3000, 3000, 400)),
        ]
        placements.extend([
            ("generator", "RefineryGeneratorPort", (-190000, -56000, -28000), (36000, 10000, 26000)),
            ("generator", "RefineryGeneratorStarboard", (-190000, 56000, -28000), (36000, 10000, 26000)),
        ])
    for donor_key, suffix, location, target_size in placements:
        donor = load_donor(donor_key)
        actor = spawn_mesh(
            actors, donor, f"FAB_HULL_{ship_name}_DONOR_{suffix}",
            location, target_size
        )
        built.append(actor)
        donor_rows.append({
            "role": suffix,
            "source": donor.get_path_name(),
            "location_cm": list(location),
            "target_size_cm": list(target_size),
        })

    lo = unreal.Vector(1e30, 1e30, 1e30)
    hi = unreal.Vector(-1e30, -1e30, -1e30)
    for actor in built:
        origin, extent = actor.get_actor_bounds(False)
        lo.x = min(lo.x, origin.x - extent.x); lo.y = min(lo.y, origin.y - extent.y); lo.z = min(lo.z, origin.z - extent.z)
        hi.x = max(hi.x, origin.x + extent.x); hi.y = max(hi.y, origin.y + extent.y); hi.z = max(hi.z, origin.z + extent.z)
    size = [hi.x - lo.x, hi.y - lo.y, hi.z - lo.z]
    expected = config["expected_cm"]
    verified = all(abs(size[index] - expected[index]) <= 100.0 for index in range(3))
    levels.save_current_level()
    return {
        "ship": ship_name,
        "review_map": config["map"],
        "expected_cm": list(expected),
        "assembled_size_cm": size,
        "scale_verified": verified,
        "generated_assets": [mesh.get_path_name() for mesh in generated.values()],
        "donor_placements": donor_rows,
    }


for material_path in MATERIALS.values():
    if not isinstance(unreal.EditorAssetLibrary.load_asset(material_path), unreal.MaterialInterface):
        raise RuntimeError(f"Installed Fab material unavailable: {material_path}")

_, corvette = corvette_assets()
_, carrier = carrier_assets()
results = [
    create_review_map("MilitaryCorvette", SHIPS["MilitaryCorvette"], corvette),
    create_review_map("ExpeditionCarrier", SHIPS["ExpeditionCarrier"], carrier),
]

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "version": 1,
    "iteration": "Iteration_04_FabHullSculpt",
    "method": "Unreal Geometry Script primary hulls with selective native Fab detail",
    "materials": MATERIALS,
    "donors": DONORS,
    "ships": results,
}, indent=2), encoding="utf-8")
if not all(item["scale_verified"] for item in results):
    raise RuntimeError(f"Fab hull sculpt scale validation failed; inspect {REPORT}")
unreal.EditorAssetLibrary.save_directory(ROOT + "/UnrealSculpt")
unreal.log("UNREAL FAB HULL SCULPT: concept-first Iteration_04 complete")
