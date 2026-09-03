"""Build Iteration 07 angular hard-surface ship hulls inside Unreal.

This pass keeps the exact V06 scale authority but replaces the soft primary
volumes with stepped octagonal districts, sloped shoulder armor, shadow gaps,
and a less repetitive surface hierarchy.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import unreal


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
import build_unreal_ship_concept_hulls_v06 as base


base.ITERATION = "Iteration_07_HardSurface"
base.ACTOR_PREFIX = "HARD07_"
base.REPORT = base.PROJECT / "Saved/Reports/UnrealShipHardSurfaceV07.json"
base.SHIPS = {
    "MilitaryCorvette": {
        "map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_HardSurface07",
        "expected_cm": (240000.0, 43000.0, 62000.0),
    },
    "ExpeditionCarrier": {
        "map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_HardSurface07",
        "expected_cm": (650000.0, 140000.0, 180000.0),
    },
}
base.BEAM_SCALE_BY_SHIP = {
    "MilitaryCorvette": 0.7323908990051713,
    "ExpeditionCarrier": 0.7539318048487912,
}


def append_rotated_box(mesh, center, size, roll=0.0, pitch=0.0, yaw=0.0):
    # Geometry Script's box origin is the center of its local bottom face.
    # Compensate for that local offset so rotation still honors `center`.
    roll_radians = math.radians(roll)
    base_y = center[1] + math.sin(roll_radians) * size[2] * 0.5
    base_z = center[2] - math.cos(roll_radians) * size[2] * 0.5
    mesh.append_box(
        base.PRIMITIVE,
        base.xf(center[0], base_y, base_z,
                pitch=pitch, yaw=yaw, roll=roll),
        size[0], size[1], size[2], 2, 2, 2,
    )


def octagonal_districts(entries):
    """Build stepped octagonal sections from intersecting oriented boxes."""
    mesh = unreal.DynamicMesh()
    for center, size in entries:
        x, y, z = size
        append_rotated_box(mesh, center, (x, y, z * 0.58))
        append_rotated_box(mesh, center, (x, y * 0.68, z))
        strip = min(y, z) * 0.26
        for sy in (-1, 1):
            for sz in (-1, 1):
                append_rotated_box(
                    mesh,
                    (center[0], center[1] + sy * y * 0.315,
                     center[2] + sz * z * 0.285),
                    (x, strip, strip),
                    roll=-sy * sz * 45.0,
                )
    mesh.auto_repair_normals()
    mesh.recompute_normals(base.NORMALS)
    return mesh


def oriented_boxes(entries):
    mesh = unreal.DynamicMesh()
    for center, size, roll, pitch, yaw in entries:
        append_rotated_box(mesh, center, size, roll, pitch, yaw)
    mesh.recompute_normals(base.NORMALS)
    return mesh


def corvette_assets():
    folder = f"{base.ROOT}/MilitaryCorvette/Working/{base.ITERATION}"
    hull = octagonal_districts([
        ((-105000, 0, -3500), (30000, 28500, 33000)),
        ((-79000, 0, -2500), (36000, 36500, 41000)),
        ((-44000, 0, -1000), (42000, 42500, 44500)),
        ((-5000, 0, 0), (43000, 43000, 45000)),
        ((35000, 0, -500), (43000, 43000, 44000)),
        ((72000, 0, -1500), (38000, 39500, 41000)),
        ((105000, 0, -3000), (30000, 30000, 34000)),
    ])
    for side in (-1, 1):
        base.subtract_box(hull, (55000, side * 20200, -4500), (50000, 9200, 18000))

    armor = []
    for x, length, width, z in [
        (-104000, 26000, 25000, 14800), (-78000, 26000, 32000, 19000),
        (-47000, 30000, 36000, 21500), (-15000, 30000, 36500, 22500),
        (18000, 30000, 37000, 22000), (50000, 30000, 35500, 21000),
        (80000, 26000, 32000, 19000), (106000, 24000, 24000, 14500),
    ]:
        armor.append(((x, 0, z), (length, width * 0.58, 2200), 0, 0, 0))
        armor.append(((x, -width * 0.34, z - 2400), (length, width * 0.34, 1800), -14, 0, 0))
        armor.append(((x, width * 0.34, z - 2400), (length, width * 0.34, 1800), 14, 0, 0))

    belts = []
    for side in (-1, 1):
        for x, length, z in [(-92000, 22000, 5500), (-66000, 22000, 6500),
                             (-15000, 28000, 7500), (15000, 24000, -13500),
                             (92000, 30000, 4500)]:
            belts.append(((x, side * 20500, z), (length, 1400, 3200), 0, 0, 0))

    frames = []
    for side in (-1, 1):
        y = side * 21000
        frames += [
            ((30000, y, -4500), (3500, 1000, 22000), 0, 0, 0),
            ((80000, y, -4500), (3500, 1000, 22000), 0, 0, 0),
            ((55000, y, 6500), (53500, 1000, 3000), 0, 0, 0),
            ((55000, y, -15500), (53500, 1000, 3000), 0, 0, 0),
        ]

    command = oriented_boxes([
        ((-19000, 0, 23800), (52000, 22000, 3200), 0, 0, 0),
        ((-23000, 0, 26700), (34000, 15000, 2800), 0, 0, 0),
        ((-27000, 0, 29000), (18000, 8500, 1800), 0, 0, 0),
    ])
    keel = octagonal_districts([((-5000, 0, -26500), (155000, 19000, 9000))])

    drive, glow = [], []
    for y in (-12000, -4000, 4000, 12000):
        for z in (-11000, -3500, 4000, 11500):
            drive.append(((-112000, y, z), 2600, 8000, 32))
            glow.append(((-119600, y, z), 1750, 400, 32))

    return folder, {
        "Districts": base.create_asset(folder, "SM_MilitaryCorvette_HardDistricts07", hull, "hull", "AngularDistricts"),
        "Backbone": base.create_asset(folder, "SM_MilitaryCorvette_Backbone07", base.boxes([((0, 0, -4000), (222000, 26000, 22000))]), "structure", "Backbone"),
        "Armor": base.create_asset(folder, "SM_MilitaryCorvette_ShoulderArmor07", oriented_boxes(armor), "armor", "ShoulderArmor"),
        "Belts": base.create_asset(folder, "SM_MilitaryCorvette_ShadowBelts07", oriented_boxes(belts), "structure", "ShadowBelts"),
        "HangarFrames": base.create_asset(folder, "SM_MilitaryCorvette_HangarFrames07", oriented_boxes(frames), "structure", "HangarFrames"),
        "Command": base.create_asset(folder, "SM_MilitaryCorvette_Command07", command, "armor", "BuriedCommand"),
        "Keel": base.create_asset(folder, "SM_MilitaryCorvette_Keel07", keel, "structure", "Keel"),
        "Drive": base.create_asset(folder, "SM_MilitaryCorvette_Drive07", base.cylinders(drive), "structure", "DriveCluster"),
        "DriveGlow": base.create_asset(folder, "SM_MilitaryCorvette_DriveGlow07", base.cylinders(glow), "emissive", "DriveGlow"),
    }


def carrier_assets():
    folder = f"{base.ROOT}/ExpeditionCarrier/Working/{base.ITERATION}"
    hull = octagonal_districts([
        ((-300000, 0, -12000), (50000, 100000, 104000)),
        ((-255000, 0, -9000), (70000, 124000, 132000)),
        ((-190000, 0, -7000), (80000, 132000, 140000)),
        ((-110000, 0, -5000), (95000, 136000, 144000)),
        ((-15000, 0, -4000), (100000, 136000, 144000)),
        ((85000, 0, -5000), (105000, 136000, 144000)),
        ((180000, 0, -7000), (90000, 128000, 136000)),
        ((255000, 0, -10000), (70000, 116000, 120000)),
        ((300000, 0, -12000), (50000, 96000, 100000)),
    ])
    for side in (-1, 1):
        base.subtract_box(hull, (125000, side * 65500, -14000), (120000, 18000, 46000))

    armor = []
    top_specs = [
        (-290000, 50000, 82000, 43000), (-240000, 48000, 108000, 55000),
        (-185000, 50000, 116000, 62000), (-128000, 52000, 120000, 66000),
        (-70000, 52000, 124000, 68000), (-12000, 52000, 126000, 69000),
        (46000, 52000, 126000, 69000), (104000, 52000, 124000, 68000),
        (162000, 52000, 116000, 62000), (220000, 52000, 104000, 54000),
        (275000, 50000, 86000, 44000),
    ]
    for x, length, width, z in top_specs:
        armor.append(((x, 0, z), (length, width * 0.55, 3600), 0, 0, 0))
        armor.append(((x, -width * 0.34, z - 5200), (length, width * 0.34, 3000), -16, 0, 0))
        armor.append(((x, width * 0.34, z - 5200), (length, width * 0.34, 3000), 16, 0, 0))

    belts = []
    for side in (-1, 1):
        for x, length, z in [(-278000, 36000, 8000), (-230000, 38000, 14000),
                             (-90000, 42000, 18000), (-35000, 42000, 18000),
                             (215000, 42000, 12000), (270000, 36000, 8000)]:
            belts.append(((x, side * 66500, z), (length, 3200, 8000), 0, 0, 0))

    frames = []
    for side in (-1, 1):
        y = side * 69000
        frames += [
            ((65000, y, -14000), (5000, 2000, 52000), 0, 0, 0),
            ((185000, y, -14000), (5000, 2000, 52000), 0, 0, 0),
            ((125000, y, 12000), (125000, 2000, 5000), 0, 0, 0),
            ((125000, y, -40000), (125000, 2000, 5000), 0, 0, 0),
        ]

    command = oriented_boxes([
        ((-40000, 0, 71500), (140000, 72000, 7000), 0, 0, 0),
        ((-50000, 0, 79000), (90000, 46000, 7000), 0, 0, 0),
        ((-58000, 0, 85500), (42000, 22000, 5000), 0, 0, 0),
    ])
    keel = octagonal_districts([((-15000, 0, -84500), (430000, 76000, 11000))])

    habitats, rings = [], []
    for side in (-1, 1):
        for x in (-225000, -175000, -125000, -75000):
            habitats.append(((x, side * 62500, -14000), (20500, 7500, 23500)))
            rings.append(((x, side * 65500, -14000), 24000, 2400))

    drive, glow = [], []
    for y in (-45000, -15000, 15000, 45000):
        for z in (-38000, 0, 38000):
            drive.append(((-313000, y, z), 8500, 12000, 40))
            glow.append(((-324400, y, z), 6000, 600, 40))

    return folder, {
        "Districts": base.create_asset(folder, "SM_ExpeditionCarrier_HardDistricts07", hull, "hull", "AngularDistricts"),
        "Backbone": base.create_asset(folder, "SM_ExpeditionCarrier_Backbone07", base.boxes([((0, 0, -10000), (628000, 76000, 60000))]), "structure", "Backbone"),
        "Armor": base.create_asset(folder, "SM_ExpeditionCarrier_ShoulderArmor07", oriented_boxes(armor), "armor", "ShoulderArmor"),
        "Belts": base.create_asset(folder, "SM_ExpeditionCarrier_ShadowBelts07", oriented_boxes(belts), "structure", "ShadowBelts"),
        "HangarFrames": base.create_asset(folder, "SM_ExpeditionCarrier_HangarFrames07", oriented_boxes(frames), "structure", "ConcourseFrames"),
        "Command": base.create_asset(folder, "SM_ExpeditionCarrier_Command07", command, "armor", "CommandCity"),
        "Keel": base.create_asset(folder, "SM_ExpeditionCarrier_Keel07", keel, "structure", "Keel"),
        "Habitats": base.create_asset(folder, "SM_ExpeditionCarrier_Habitats07", base.ellipsoids(habitats), "hull", "HabitatDrums"),
        "HabitatRings": base.create_asset(folder, "SM_ExpeditionCarrier_HabitatRings07", base.tori(rings), "structure", "HabitatRings"),
        "Drive": base.create_asset(folder, "SM_ExpeditionCarrier_Drive07", base.cylinders(drive), "structure", "DriveCluster"),
        "DriveGlow": base.create_asset(folder, "SM_ExpeditionCarrier_DriveGlow07", base.cylinders(glow), "emissive", "DriveGlow"),
    }


def main():
    for material_path in base.MATERIALS.values():
        if not isinstance(unreal.EditorAssetLibrary.load_asset(material_path), unreal.MaterialInterface):
            raise RuntimeError(f"Material is unavailable: {material_path}")

    _, corvette = corvette_assets()
    _, carrier = carrier_assets()
    results = [base.build_map("MilitaryCorvette", corvette), base.build_map("ExpeditionCarrier", carrier)]
    base.REPORT.parent.mkdir(parents=True, exist_ok=True)
    base.REPORT.write_text(json.dumps({
        "version": 1,
        "iteration": base.ITERATION,
        "method": "Unreal-authored angular districts, sloped armor, shadow belts, and selective Fab detail",
        "ships": results,
    }, indent=2), encoding="utf-8")
    if not all(row["scale_verified"] for row in results):
        raise RuntimeError("Iteration 07 failed an exact scale gate")
    unreal.log("UNREAL SHIP HARD SURFACE V07: complete")


if __name__ == "__main__":
    main()
