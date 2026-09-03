"""Build a calmer, concept-led hard-surface hierarchy for both large ships."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import unreal


TOOLS = Path(__file__).resolve().parent
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))
import build_unreal_ship_hardsurface_v07 as hard


base = hard.base
base.ITERATION = "Iteration_08_Declutter"
base.ACTOR_PREFIX = "CLEAN08_"
base.REPORT = base.PROJECT / "Saved/Reports/UnrealShipDeclutterV08.json"
base.MATERIALS.update({
    "hull": "/Game/Sci-Fi_Flying_Cargo_Ship/Materials/Material_instances/MI_cargo_body_01",
    "armor": "/Game/Assets/Materials/Production/Instances/MI_Surface_ExteriorHull",
    "structure": "/Game/Assets/Materials/Production/Instances/MI_Surface_Environment",
})
base.SHIPS = {
    "MilitaryCorvette": {
        "map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_Declutter08",
        "expected_cm": (240000.0, 43000.0, 62000.0),
    },
    "ExpeditionCarrier": {
        "map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_Declutter08",
        "expected_cm": (650000.0, 140000.0, 180000.0),
    },
}
base.BEAM_SCALE_BY_SHIP = {
    "MilitaryCorvette": 0.7323908990051713,
    "ExpeditionCarrier": 0.7539318048487912,
}


def armor_groups(specs, shoulder_angle, shoulder_drop):
    entries = []
    for x, length, width, z in specs:
        entries.append(((x, 0, z), (length, width * 0.56, 2300 if width < 50000 else 3800), 0, 0, 0))
        entries.append(((x, -width * 0.34, z - shoulder_drop),
                        (length, width * 0.32, 1800 if width < 50000 else 3000),
                        -shoulder_angle, 0, 0))
        entries.append(((x, width * 0.34, z - shoulder_drop),
                        (length, width * 0.32, 1800 if width < 50000 else 3000),
                        shoulder_angle, 0, 0))
    return hard.oriented_boxes(entries)


def corvette_assets():
    folder = f"{base.ROOT}/MilitaryCorvette/Working/{base.ITERATION}"
    hull = hard.octagonal_districts([
        ((-105000, 0, -3500), (30000, 29000, 34000)),
        ((-73000, 0, -2200), (52000, 39000, 42000)),
        ((-15000, 0, -500), (76000, 43000, 45000)),
        ((52000, 0, -900), (70000, 42500, 43500)),
        ((105000, 0, -3000), (30000, 30000, 34000)),
    ])
    for side in (-1, 1):
        base.subtract_box(hull, (55000, side * 20200, -4500), (50000, 9200, 18000))

    armor = armor_groups([
        (-94000, 40000, 30000, 17500),
        (-46000, 44000, 39000, 22000),
        (0, 42000, 40000, 22800),
        (46000, 42000, 38000, 21400),
        (92000, 40000, 30000, 17000),
    ], 13, 2400)
    belts = hard.oriented_boxes([
        ((-76000, side * 20500, 5500), (36000, 1400, 3200), 0, 0, 0)
        for side in (-1, 1)
    ] + [
        ((-5000, side * 20700, -13500), (42000, 1200, 3000), 0, 0, 0)
        for side in (-1, 1)
    ] + [
        ((93000, side * 17800, 4000), (30000, 1600, 3400), 0, 0, 0)
        for side in (-1, 1)
    ])
    frames = []
    for side in (-1, 1):
        y = side * 21000
        frames += [
            ((30000, y, -4500), (3500, 1000, 22000), 0, 0, 0),
            ((80000, y, -4500), (3500, 1000, 22000), 0, 0, 0),
            ((55000, y, 6500), (53500, 1000, 3000), 0, 0, 0),
            ((55000, y, -15500), (53500, 1000, 3000), 0, 0, 0),
        ]
    command = hard.oriented_boxes([
        ((-18000, 0, 24200), (48000, 21000, 3000), 0, 0, 0),
        ((-23000, 0, 27100), (30000, 14000, 2600), 0, 0, 0),
        ((-27000, 0, 29200), (15000, 8000, 1500), 0, 0, 0),
    ])
    keel = hard.octagonal_districts([((-5000, 0, -26500), (145000, 17000, 9000))])

    drive, glow = [], []
    for y in (-12000, -4000, 4000, 12000):
        for z in (-11000, -3500, 4000, 11500):
            drive.append(((-112000, y, z), 2600, 8000, 32))
            glow.append(((-119600, y, z), 1750, 400, 32))
    return folder, {
        "Hull": base.create_asset(folder, "SM_MilitaryCorvette_CleanHull08", hull, "hull", "PrimaryHull"),
        "Backbone": base.create_asset(folder, "SM_MilitaryCorvette_Backbone08", base.boxes([((0, 0, -4000), (222000, 25000, 21000))]), "structure", "Backbone"),
        "Armor": base.create_asset(folder, "SM_MilitaryCorvette_Armor08", armor, "armor", "ArmorGroups"),
        "Belts": base.create_asset(folder, "SM_MilitaryCorvette_ShadowChannels08", belts, "structure", "ShadowChannels"),
        "HangarFrames": base.create_asset(folder, "SM_MilitaryCorvette_HangarFrames08", hard.oriented_boxes(frames), "structure", "HangarFrames"),
        "Command": base.create_asset(folder, "SM_MilitaryCorvette_Command08", command, "armor", "BuriedCommand"),
        "Keel": base.create_asset(folder, "SM_MilitaryCorvette_Keel08", keel, "structure", "Keel"),
        "Drive": base.create_asset(folder, "SM_MilitaryCorvette_Drive08", base.cylinders(drive), "structure", "DriveCluster"),
        "DriveGlow": base.create_asset(folder, "SM_MilitaryCorvette_DriveGlow08", base.cylinders(glow), "emissive", "DriveGlow"),
    }


def carrier_assets():
    folder = f"{base.ROOT}/ExpeditionCarrier/Working/{base.ITERATION}"
    hull = hard.octagonal_districts([
        ((-300000, 0, -12000), (50000, 100000, 104000)),
        ((-245000, 0, -9000), (90000, 126000, 134000)),
        ((-130000, 0, -5500), (150000, 136000, 144000)),
        ((20000, 0, -4500), (160000, 136000, 144000)),
        ((170000, 0, -6500), (140000, 130000, 138000)),
        ((285000, 0, -11500), (80000, 104000, 104000)),
    ])
    for side in (-1, 1):
        base.subtract_box(hull, (125000, side * 65500, -14000), (120000, 18000, 46000))

    armor = armor_groups([
        (-280000, 65000, 90000, 45500),
        (-205000, 65000, 116000, 61000),
        (-125000, 70000, 124000, 68000),
        (-40000, 70000, 126000, 70000),
        (45000, 70000, 126000, 70000),
        (130000, 70000, 120000, 66000),
        (215000, 70000, 106000, 57000),
        (285000, 60000, 82000, 42500),
    ], 15, 5000)
    belt_entries = []
    for side in (-1, 1):
        belt_entries += [
            ((-255000, side * 62000, 9000), (52000, 3600, 9000), 0, 0, 0),
            ((-35000, side * 66500, 17000), (70000, 3000, 8000), 0, 0, 0),
            ((245000, side * 61000, 9000), (60000, 3400, 9000), 0, 0, 0),
        ]
    belts = hard.oriented_boxes(belt_entries)
    frames = []
    for side in (-1, 1):
        y = side * 69000
        frames += [
            ((65000, y, -14000), (5000, 2000, 52000), 0, 0, 0),
            ((185000, y, -14000), (5000, 2000, 52000), 0, 0, 0),
            ((125000, y, 12000), (125000, 2000, 5000), 0, 0, 0),
            ((125000, y, -40000), (125000, 2000, 5000), 0, 0, 0),
        ]
    command = hard.oriented_boxes([
        ((-40000, 0, 72000), (125000, 65000, 6500), 0, 0, 0),
        ((-50000, 0, 79500), (76000, 40000, 6500), 0, 0, 0),
        ((-58000, 0, 85800), (36000, 20000, 4600), 0, 0, 0),
    ])
    keel = hard.octagonal_districts([((-15000, 0, -84500), (400000, 70000, 11000))])
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
        "Hull": base.create_asset(folder, "SM_ExpeditionCarrier_CleanHull08", hull, "hull", "PrimaryHull"),
        "Backbone": base.create_asset(folder, "SM_ExpeditionCarrier_Backbone08", base.boxes([((0, 0, -10000), (628000, 76000, 60000))]), "structure", "Backbone"),
        "Armor": base.create_asset(folder, "SM_ExpeditionCarrier_Armor08", armor, "armor", "ArmorGroups"),
        "Belts": base.create_asset(folder, "SM_ExpeditionCarrier_ShadowChannels08", belts, "structure", "ShadowChannels"),
        "HangarFrames": base.create_asset(folder, "SM_ExpeditionCarrier_HangarFrames08", hard.oriented_boxes(frames), "structure", "ConcourseFrames"),
        "Command": base.create_asset(folder, "SM_ExpeditionCarrier_Command08", command, "armor", "CommandCity"),
        "Keel": base.create_asset(folder, "SM_ExpeditionCarrier_Keel08", keel, "structure", "Keel"),
        "Habitats": base.create_asset(folder, "SM_ExpeditionCarrier_Habitats08", base.ellipsoids(habitats), "hull", "HabitatDrums"),
        "HabitatRings": base.create_asset(folder, "SM_ExpeditionCarrier_HabitatRings08", base.tori(rings), "structure", "HabitatRings"),
        "Drive": base.create_asset(folder, "SM_ExpeditionCarrier_Drive08", base.cylinders(drive), "structure", "DriveCluster"),
        "DriveGlow": base.create_asset(folder, "SM_ExpeditionCarrier_DriveGlow08", base.cylinders(glow), "emissive", "DriveGlow"),
    }


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
    "method": "Calm primary masses, limited textured armor groups, and functional Fab landmarks",
    "ships": results,
}, indent=2), encoding="utf-8")
if not all(row["scale_verified"] for row in results):
    raise RuntimeError("Iteration 08 failed an exact scale gate")
unreal.log("UNREAL SHIP DECLUTTER V08: complete")
