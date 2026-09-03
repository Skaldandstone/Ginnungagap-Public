"""Build concept-first ship hulls in Unreal Geometry Script.

Iteration 06 deliberately abandons the capsule-plus-panels direction.  Each
ship is composed from overlapping armored districts with its own proportion,
command, hangar, habitat, radiator, and drive hierarchy.  Fab meshes remain
secondary embedded detail only.
"""
from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
REPORT = PROJECT / "Saved/Reports/UnrealShipConceptHullsV06.json"
ROOT = "/Game/Assets/Ships/Exterior/UnrealSculpt"
ITERATION = "Iteration_06_ConceptHull"
ACTOR_PREFIX = "CONCEPT06_"
BEAM_SCALE_BY_SHIP = {}
PRIMITIVE = unreal.GeometryScriptPrimitiveOptions()
NORMALS = unreal.GeometryScriptCalculateNormalsOptions(angle_weighted=True, area_weighted=True)
IDENTITY = unreal.Transform()

MATERIALS = {
    "hull": "/Game/Sci-Fi_Flying_Cargo_Ship/Materials/Material_instances/MI_cargo_body_01",
    "armor": "/Game/Assets/Materials/Production/Instances/MI_Surface_ExteriorHull",
    "structure": "/Game/Assets/Materials/Production/Instances/MI_Surface_Environment",
    "emissive": "/Game/Ice_Station/Materials/Light/MI_light1",
}

DONORS = {
    "hangar": "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Hangar/SM_hangar",
    "command_detail": "/Game/Ice_Station/Meshes/Antennas/SM_building_details_01",
    "antenna": "/Game/SciFi_Cliff/Meshes/Antenna/SM_antenna_02",
    "generator": "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_POWER_GENERATOR_01",
    "reactor": "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Reactor/SM_reactor",
}

SHIPS = {
    "MilitaryCorvette": {
        "map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_ConceptHull06",
        "expected_cm": (240000.0, 43000.0, 62000.0),
    },
    "ExpeditionCarrier": {
        "map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_ConceptHull06",
        "expected_cm": (650000.0, 140000.0, 180000.0),
    },
}


def xf(x=0.0, y=0.0, z=0.0, pitch=0.0, yaw=0.0, roll=0.0,
       sx=1.0, sy=1.0, sz=1.0):
    return unreal.Transform(
        location=unreal.Vector(x, y, z),
        rotation=unreal.Rotator(pitch=pitch, yaw=yaw, roll=roll),
        scale=unreal.Vector(sx, sy, sz),
    )


def append_ellipsoid(mesh, center, half_size, longitude=48, latitude=32):
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


def ellipsoids(entries, longitude=48, latitude=32):
    mesh = unreal.DynamicMesh()
    for center, half_size in entries:
        append_ellipsoid(mesh, center, half_size, longitude, latitude)
    mesh.recompute_normals(NORMALS)
    return mesh


def union_ellipsoids(entries, longitude=48, latitude=32):
    """Join the primary pressure volumes into one continuous armored hull.

    Appending separate spheres left visible interpenetration seams, which made
    the ships read as rows of tanks.  A boolean union preserves the district
    changes while producing a single continuous skin.
    """
    mesh = unreal.DynamicMesh()
    for index, (center, half_size) in enumerate(entries):
        part = unreal.DynamicMesh()
        append_ellipsoid(part, center, half_size, longitude, latitude)
        if index == 0:
            mesh = part
        else:
            mesh.apply_mesh_boolean(
                IDENTITY, part, IDENTITY,
                unreal.GeometryScriptBooleanOperation.UNION,
                unreal.GeometryScriptMeshBooleanOptions(),
            )
    mesh.recompute_normals(NORMALS)
    return mesh


def append_box(mesh, center, size):
    # Geometry Script boxes use transform Z as the base plane.
    mesh.append_box(
        PRIMITIVE,
        xf(center[0], center[1], center[2] - size[2] * 0.5),
        size[0], size[1], size[2], 2, 2, 2,
    )


def boxes(entries):
    mesh = unreal.DynamicMesh()
    for center, size in entries:
        append_box(mesh, center, size)
    mesh.recompute_normals(NORMALS)
    return mesh


def subtract_box(mesh, center, size):
    cutter = boxes([(center, size)])
    mesh.apply_mesh_boolean(
        IDENTITY, cutter, IDENTITY,
        unreal.GeometryScriptBooleanOperation.SUBTRACT,
        unreal.GeometryScriptMeshBooleanOptions(),
    )


def cylinders(entries):
    """Entries are (base, radius, height, sides); pitch 90 points toward -X."""
    mesh = unreal.DynamicMesh()
    for base, radius, height, sides in entries:
        mesh.append_cylinder(
            PRIMITIVE, xf(base[0], base[1], base[2], pitch=90),
            radius, height, sides, 2, True,
        )
    mesh.recompute_normals(NORMALS)
    return mesh


def tori(entries):
    """Entries are (center, major_radius, minor_radius); roll 90 faces ±Y."""
    mesh = unreal.DynamicMesh()
    for center, major, minor in entries:
        mesh.append_torus(
            PRIMITIVE, xf(center[0], center[1], center[2], roll=90),
            unreal.GeometryScriptRevolveOptions(), major, minor, 48, 12,
        )
    mesh.recompute_normals(NORMALS)
    return mesh


def create_asset(folder, name, mesh, material_key, role):
    unreal.EditorAssetLibrary.make_directory(folder)
    path = f"{folder}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        if not unreal.EditorAssetLibrary.delete_asset(path):
            raise RuntimeError(f"Could not replace {path}")
    mesh.auto_repair_normals()
    mesh.recompute_normals(NORMALS)
    asset, outcome = unreal.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(
        mesh, path, unreal.GeometryScriptCreateNewStaticMeshAssetOptions()
    )
    if not asset or outcome != unreal.GeometryScriptOutcomePins.SUCCESS:
        raise RuntimeError(f"Could not create {path}: {outcome}")
    material = unreal.EditorAssetLibrary.load_asset(MATERIALS[material_key])
    if not isinstance(material, unreal.MaterialInterface):
        raise RuntimeError(f"Missing material {MATERIALS[material_key]}")
    slot = unreal.StaticMaterial()
    slot.set_editor_property("material_interface", material)
    slot.set_editor_property("material_slot_name", unreal.Name(role))
    asset.set_editor_property("static_materials", [slot])
    asset.set_editor_property("light_map_resolution", 256)
    body_setup = asset.get_editor_property("body_setup")
    if body_setup:
        body_setup.set_editor_property(
            "collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
        )
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "ShipSculpt.Iteration", ITERATION)
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "ShipSculpt.Role", role)
    unreal.EditorAssetLibrary.set_metadata_tag(asset, "ShipSculpt.Direction", "ConceptFirst")
    if not unreal.EditorAssetLibrary.save_loaded_asset(asset):
        raise RuntimeError(f"Could not save {path}")
    return asset


def corvette_assets():
    folder = f"{ROOT}/MilitaryCorvette/Working/{ITERATION}"
    districts = union_ellipsoids([
        ((-105000, 0, -3500), (15000, 15500, 16000)),
        ((-76000, 0, -2500), (35000, 20000, 21000)),
        ((-15000, 0, 0), (65000, 21500, 22500)),
        ((55000, 0, -1000), (55000, 21500, 22000)),
        ((105000, 0, -2500), (15000, 16500, 17000)),
    ])
    for side in (-1, 1):
        subtract_box(districts, (55000, side * 20500, -4500), (48000, 9000, 17000))

    armor = []
    belts = []
    top_specs = [
        (-105000, 25000, 26000, 14500), (-80000, 26000, 35000, 18000),
        (-50000, 30000, 40000, 20500), (-18000, 30000, 38000, 21000),
        (16000, 30000, 39000, 20500), (50000, 30000, 40000, 20500),
        (82000, 28000, 34000, 17000), (108000, 20000, 24000, 11500),
    ]
    for x, length, width, z in top_specs:
        armor.append(((x, 0, z), (length, width, 2500)))
    # Longitudinal defense belts and lower structural rails.
    for side in (-1, 1):
        belts.extend([
            ((-88000, side * 20250, 7000), (30000, 1800, 4000)),
            ((-50000, side * 20750, 7000), (32000, 1200, 3500)),
            ((-88000, side * 20250, -13000), (30000, 1800, 4000)),
            ((-50000, side * 20750, -13000), (32000, 1200, 3500)),
            ((-5000, side * 20750, 8000), (32000, 1200, 3500)),
            ((-5000, side * 20750, -14000), (32000, 1200, 3500)),
            ((92000, side * 17750, 5000), (34000, 1800, 4000)),
        ])

    hangar_frames = []
    for side in (-1, 1):
        y = side * 21000
        hangar_frames.extend([
            ((31000, y, -4500), (3000, 1000, 21000)),
            ((79000, y, -4500), (3000, 1000, 21000)),
            ((55000, y, 6000), (51000, 1000, 3000)),
            ((55000, y, -15000), (51000, 1000, 3000)),
        ])

    command = boxes([
        ((-18000, 0, 23250), (55000, 22000, 3500)),
        ((-23000, 0, 26500), (34000, 15000, 3000)),
        ((-27000, 0, 28850), (18000, 8500, 1700)),
    ])
    keel = ellipsoids([((-5000, 0, -26000), (90000, 13000, 5000))], 64, 24)

    drive_entries = []
    glow_entries = []
    for y in (-12000, -4000, 4000, 12000):
        for z in (-11000, -3500, 4000, 11500):
            drive_entries.append(((-112000, y, z), 2600, 8000, 32))
            glow_entries.append(((-119600, y, z), 1750, 400, 32))

    assets = {
        "Districts": create_asset(folder, "SM_MilitaryCorvette_ConceptDistricts06", districts, "hull", "ArmoredDistricts"),
        "Backbone": create_asset(folder, "SM_MilitaryCorvette_Backbone06", boxes([((0, 0, -4000), (222000, 27000, 23000))]), "structure", "Backbone"),
        "Armor": create_asset(folder, "SM_MilitaryCorvette_Armor06", boxes(armor), "armor", "ArmorHierarchy"),
        "Belts": create_asset(folder, "SM_MilitaryCorvette_DefenseBelts06", boxes(belts), "structure", "DefenseBelts"),
        "HangarFrames": create_asset(folder, "SM_MilitaryCorvette_HangarFrames06", boxes(hangar_frames), "structure", "HangarFrames"),
        "Command": create_asset(folder, "SM_MilitaryCorvette_Command06", command, "armor", "BuriedCommand"),
        "Keel": create_asset(folder, "SM_MilitaryCorvette_Keel06", keel, "structure", "Keel"),
        "Drive": create_asset(folder, "SM_MilitaryCorvette_Drive06", cylinders(drive_entries), "structure", "DriveCluster"),
        "DriveGlow": create_asset(folder, "SM_MilitaryCorvette_DriveGlow06", cylinders(glow_entries), "emissive", "DriveGlow"),
    }
    return folder, assets


def carrier_assets():
    folder = f"{ROOT}/ExpeditionCarrier/Working/{ITERATION}"
    districts = union_ellipsoids([
        ((-300000, 0, -12000), (25000, 52000, 52000)),
        ((-245000, 0, -9000), (75000, 64000, 69000)),
        ((-100000, 0, -5000), (160000, 68000, 72000)),
        ((110000, 0, -5000), (155000, 68000, 72000)),
        ((280000, 0, -12000), (45000, 55000, 52000)),
    ], 64, 40)
    for side in (-1, 1):
        subtract_box(districts, (125000, side * 66000, -14000), (115000, 16000, 44000))

    armor = []
    belts = []
    top_specs = [
        (-290000, 60000, 90000, 42000), (-235000, 60000, 116000, 53500),
        (-175000, 60000, 112000, 60000), (-115000, 60000, 112000, 60000),
        (-55000, 60000, 122000, 62000), (5000, 60000, 132000, 64500),
        (65000, 60000, 134000, 64500), (125000, 60000, 132000, 61000),
        (185000, 60000, 120000, 54000), (245000, 60000, 98000, 44000),
        (295000, 50000, 76000, 34000),
    ]
    for x, length, width, z in top_specs:
        armor.append(((x, 0, z), (length, width, 4500)))
    # Broad radiator fields sit flush with the dorsal armor instead of reading
    # as repeated wall tiles.
    for x in (155000, 190000, 225000, 260000):
        armor.append(((x, 0, 58500 - (x - 155000) * 0.12), (26000, 126000, 2500)))
    for side in (-1, 1):
        belts.extend([
            ((-275000, side * 60000, 8000), (45000, 5000, 12000)),
            ((-215000, side * 63000, 12000), (48000, 3500, 9000)),
            ((-70000, side * 67500, 18000), (48000, 3500, 9000)),
            ((-5000, side * 67500, 18000), (48000, 3500, 9000)),
            ((205000, side * 62500, 12000), (48000, 3500, 9000)),
            ((265000, side * 60000, 8000), (42000, 4500, 11000)),
        ])

    hangar_frames = []
    for side in (-1, 1):
        y = side * 69000
        hangar_frames.extend([
            ((67500, y, -14000), (5000, 2000, 50000)),
            ((182500, y, -14000), (5000, 2000, 50000)),
            ((125000, y, 11000), (120000, 2000, 5000)),
            ((125000, y, -39000), (120000, 2000, 5000)),
        ])

    command = boxes([
        ((-40000, 0, 70000), (150000, 72000, 8000)),
        ((-50000, 0, 78000), (95000, 46000, 8000)),
        ((-58000, 0, 85000), (45000, 24000, 6000)),
    ])
    keel = ellipsoids([((-15000, 0, -84000), (240000, 48000, 6000))], 72, 24)
    habitats = []
    habitat_rings = []
    for side in (-1, 1):
        for x in (-225000, -175000, -125000, -75000):
            habitats.append(((x, side * 62500, -14000), (20500, 7500, 23500)))
            # Keep the torus envelope inside the exact 1.4 km beam; the
            # concourse frames remain the authoritative ±70,000 cm extents.
            habitat_rings.append(((x, side * 65500, -14000), 24000, 2400))

    drive_entries = []
    glow_entries = []
    for y in (-45000, -15000, 15000, 45000):
        for z in (-38000, 0, 38000):
            drive_entries.append(((-313000, y, z), 8500, 12000, 40))
            glow_entries.append(((-324400, y, z), 6000, 600, 40))

    assets = {
        "Districts": create_asset(folder, "SM_ExpeditionCarrier_ConceptDistricts06", districts, "hull", "ArmoredDistricts"),
        "Backbone": create_asset(folder, "SM_ExpeditionCarrier_Backbone06", boxes([((0, 0, -10000), (628000, 76000, 60000))]), "structure", "Backbone"),
        "Armor": create_asset(folder, "SM_ExpeditionCarrier_Armor06", boxes(armor), "armor", "ArmorAndRadiators"),
        "Belts": create_asset(folder, "SM_ExpeditionCarrier_DefenseBelts06", boxes(belts), "structure", "DefenseBelts"),
        "HangarFrames": create_asset(folder, "SM_ExpeditionCarrier_HangarFrames06", boxes(hangar_frames), "structure", "ConcourseFrames"),
        "Command": create_asset(folder, "SM_ExpeditionCarrier_Command06", command, "armor", "CommandCity"),
        "Keel": create_asset(folder, "SM_ExpeditionCarrier_Keel06", keel, "structure", "Keel"),
        "Habitats": create_asset(folder, "SM_ExpeditionCarrier_Habitats06", ellipsoids(habitats), "hull", "HabitatDrums"),
        "HabitatRings": create_asset(folder, "SM_ExpeditionCarrier_HabitatRings06", tori(habitat_rings), "structure", "HabitatRings"),
        "Drive": create_asset(folder, "SM_ExpeditionCarrier_Drive06", cylinders(drive_entries), "structure", "DriveCluster"),
        "DriveGlow": create_asset(folder, "SM_ExpeditionCarrier_DriveGlow06", cylinders(glow_entries), "emissive", "DriveGlow"),
    }
    return folder, assets


def load_donor(key):
    asset = unreal.EditorAssetLibrary.load_asset(DONORS[key])
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError(f"Missing Fab donor {key}: {DONORS[key]}")
    return asset


def spawn_mesh(actor_subsystem, mesh, label, center=(0, 0, 0), target_size=None):
    actor = actor_subsystem.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*center), unreal.Rotator()
    )
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(mesh)
    if target_size:
        bounds = mesh.get_bounds()
        size = bounds.box_extent * 2.0
        scale = unreal.Vector(
            target_size[0] / size.x,
            target_size[1] / size.y,
            target_size[2] / size.z,
        )
        actor.set_actor_scale3d(scale)
        actor.set_actor_location(
            unreal.Vector(
                center[0] - bounds.origin.x * scale.x,
                center[1] - bounds.origin.y * scale.y,
                center[2] - bounds.origin.z * scale.z,
            ), False, False
        )
    return actor


def overall_bounds(actors):
    lo = unreal.Vector(1e30, 1e30, 1e30)
    hi = unreal.Vector(-1e30, -1e30, -1e30)
    for actor in actors:
        origin, extent = actor.get_actor_bounds(False)
        lo.x = min(lo.x, origin.x - extent.x)
        lo.y = min(lo.y, origin.y - extent.y)
        lo.z = min(lo.z, origin.z - extent.z)
        hi.x = max(hi.x, origin.x + extent.x)
        hi.y = max(hi.y, origin.y + extent.y)
        hi.z = max(hi.z, origin.z + extent.z)
    return [hi.x - lo.x, hi.y - lo.y, hi.z - lo.z]


def build_map(ship, assets):
    config = SHIPS[ship]
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not unreal.EditorAssetLibrary.does_asset_exist(config["map"]):
        if not levels.new_level(config["map"]):
            raise RuntimeError(f"Could not create {config['map']}")
    if not levels.load_level(config["map"]):
        raise RuntimeError(f"Could not load {config['map']}")
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in actor_subsystem.get_all_level_actors():
        if actor.get_actor_label().startswith(ACTOR_PREFIX):
            actor_subsystem.destroy_actor(actor)

    built = [
        spawn_mesh(actor_subsystem, mesh, f"{ACTOR_PREFIX}{ship}_{role}")
        for role, mesh in assets.items()
    ]
    if ship == "ExpeditionCarrier":
        # Torus tessellation adds a small conservative Y bound beyond the
        # authored ring radius.  Pull only that decorative shell inward; the
        # hangar frame remains the exact ±70,000 cm beam authority.
        for actor in built:
            if actor.get_actor_label().endswith("_HabitatRings"):
                actor.set_actor_scale3d(unreal.Vector(1.0, 0.99, 1.0))
    donor_rows = []
    if ship == "MilitaryCorvette":
        placements = [
            ("hangar", "HangarPort", (55000, -16500, -4500), (44000, 4500, 14000)),
            ("hangar", "HangarStarboard", (55000, 16500, -4500), (44000, 4500, 14000)),
            ("command_detail", "CommandSensors", (-27000, 0, 30100), (18000, 8000, 1200)),
            ("antenna", "SensorMast", (-27000, 0, 30700), (1200, 1200, 600)),
            ("reactor", "EngineeringDetailPort", (-76000, -17500, -7000), (22000, 5000, 10000)),
            ("reactor", "EngineeringDetailStarboard", (-76000, 17500, -7000), (22000, 5000, 10000)),
        ]
    else:
        placements = [
            ("hangar", "ConcoursePort", (125000, -61000, -14000), (105000, 9000, 36000)),
            ("hangar", "ConcourseStarboard", (125000, 61000, -14000), (105000, 9000, 36000)),
            ("command_detail", "CommandSensors", (-60000, 0, 89000), (30000, 16000, 1800)),
            ("antenna", "LongRangeMast", (-60000, 0, 89500), (2200, 2200, 1000)),
            ("generator", "RefineryPort", (-260000, -60000, -22000), (30000, 8000, 22000)),
            ("generator", "RefineryStarboard", (-260000, 60000, -22000), (30000, 8000, 22000)),
        ]
    for donor_key, suffix, center, target_size in placements:
        donor = load_donor(donor_key)
        actor = spawn_mesh(
            actor_subsystem, donor, f"{ACTOR_PREFIX}{ship}_FAB_{suffix}", center, target_size
        )
        built.append(actor)
        donor_rows.append({
            "role": suffix,
            "source": donor.get_path_name(),
            "center_cm": list(center),
            "target_size_cm": list(target_size),
        })

    beam_scale = BEAM_SCALE_BY_SHIP.get(ship)
    if beam_scale:
        for actor in built:
            location = actor.get_actor_location()
            scale = actor.get_actor_scale3d()
            actor.set_actor_location(
                unreal.Vector(location.x, location.y * beam_scale, location.z),
                False, False,
            )
            actor.set_actor_scale3d(unreal.Vector(scale.x, scale.y * beam_scale, scale.z))

    size = overall_bounds(built)
    expected = config["expected_cm"]
    verified = all(abs(size[index] - expected[index]) <= 100.0 for index in range(3))
    levels.save_current_level()
    return {
        "ship": ship,
        "map": config["map"],
        "expected_cm": list(expected),
        "assembled_size_cm": size,
        "scale_verified": verified,
        "generated_assets": [mesh.get_path_name() for mesh in assets.values()],
        "fab_placements": donor_rows,
    }


def main():
    for path in MATERIALS.values():
        if not isinstance(unreal.EditorAssetLibrary.load_asset(path), unreal.MaterialInterface):
            raise RuntimeError(f"Material is unavailable: {path}")

    _, corvette = corvette_assets()
    _, carrier = carrier_assets()
    results = [build_map("MilitaryCorvette", corvette), build_map("ExpeditionCarrier", carrier)]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "version": 1,
        "iteration": ITERATION,
        "method": "Concept-specific armored districts with selective embedded Fab detail",
        "ships": results,
    }, indent=2), encoding="utf-8")
    if not all(row["scale_verified"] for row in results):
        raise RuntimeError("Iteration 06 failed an exact scale gate")
    unreal.log("UNREAL SHIP CONCEPT HULL V06: complete")


if __name__ == "__main__":
    main()
