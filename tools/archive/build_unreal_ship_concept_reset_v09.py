"""Build Iteration 09 concept-reset hulls as coherent Unreal Dynamic Meshes.

The failed V07/V08 direction used repeated rectangular donor modules as the
primary hull.  This pass creates continuous station-lofted pressure hulls,
conformal armor bands, deep negative-space landmarks, and only a few Fab donor
placements inside those landmarks.  V08 assets and maps remain untouched.
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


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
ITERATION = "Iteration_09_ConceptReset"
ACTOR_PREFIX = "RESET09_"
ROOT = "/Game/Assets/Ships/Exterior/UnrealSculpt"
REPORT = PROJECT / "Saved/Reports/UnrealShipConceptResetV09.json"
MAPS = {
    "MilitaryCorvette": {
        "map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_MilitaryCorvette_ConceptReset09",
        "expected_cm": (240000.0, 43000.0, 62000.0),
    },
    "ExpeditionCarrier": {
        "map": "/Game/Assets/Maps/ShipExterior/Sculpt/L_ExpeditionCarrier_ConceptReset09",
        "expected_cm": (650000.0, 140000.0, 180000.0),
    },
}

# Restrained fleet palette.  The failed repeating cargo-body material is not
# used anywhere on the primary exterior.
MATERIALS = {
    "hull": "/Game/Assets/Ships/Exterior/ConceptRemasterV03/MilitaryCorvette/M_Remaster_Armor",
    "armor": "/Game/Assets/Ships/Exterior/ConceptRemasterV03/MilitaryCorvette/M_Remaster_ArmorLight",
    "armor_dark": "/Game/Assets/Ships/Exterior/ConceptRemasterV03/MilitaryCorvette/M_Remaster_ArmorDark",
    "structure": "/Game/Assets/Ships/Exterior/ConceptRemasterV03/MilitaryCorvette/M_Remaster_Structure",
    "orange": "/Game/Assets/Ships/Exterior/ConceptRemasterV03/MilitaryCorvette/M_Remaster_SafetyOrange",
    "blue": "/Game/Assets/Ships/Exterior/ConceptRemasterV03/MilitaryCorvette/M_Remaster_BlueLight",
    "drive": "/Game/Assets/Ships/Exterior/ConceptRemasterV03/MilitaryCorvette/M_Remaster_Drive",
    "radiator": "/Game/Assets/Ships/Exterior/ConceptRemasterV03/ExpeditionCarrier/M_Remaster_Radiator",
    # Keep the macro armor quiet.  The imported panel instances were authored
    # for small props and read as glowing cracked rock at capital-ship scale.
    "panel_light": "/Game/Assets/Ships/Exterior/ConceptRemasterV03/MilitaryCorvette/M_Remaster_ArmorLight",
    "panel_dark": "/Game/Assets/Ships/Exterior/ConceptRemasterV03/MilitaryCorvette/M_Remaster_Armor",
}

DONORS = {
    "hangar": "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Hangar/SM_hangar",
    "antenna": "/Game/SciFi_Cliff/Meshes/Antenna/SM_antenna_02",
    "command": "/Game/Ice_Station/Meshes/Antennas/SM_building_details_01",
    "reactor": "/Game/Sci-Fi_Flying_Cargo_Ship/Meshes/Reactor/SM_reactor",
}

NORMALS = unreal.GeometryScriptCalculateNormalsOptions(angle_weighted=True, area_weighted=True)


def _vertex(mesh, position):
    result = mesh.add_vertex_to_mesh(unreal.Vector(*position), True)
    return result[-1] if isinstance(result, tuple) else result


def _triangle(mesh, a, b, c, group=0):
    mesh.add_triangle_to_mesh(unreal.IntVector(int(a), int(b), int(c)), group, True)


def _profile(half_y, half_z, angle, exponent=3.25, z_offset=0.0):
    """Rounded-octagonal/superelliptic section matching the concept fronts."""
    cosine = math.cos(angle)
    sine = math.sin(angle)
    power = 2.0 / exponent
    y = half_y * math.copysign(abs(cosine) ** power, cosine)
    z = z_offset + half_z * math.copysign(abs(sine) ** power, sine)
    return y, z


def loft_mesh(stations, sides=32):
    """Create one closed hull from (x, half_y, half_z, z_offset) stations."""
    mesh = unreal.DynamicMesh()
    rings = []
    for x, half_y, half_z, z_offset in stations:
        ring = []
        for index in range(sides):
            angle = math.tau * index / sides
            y, z = _profile(half_y, half_z, angle, z_offset=z_offset)
            ring.append(_vertex(mesh, (x, y, z)))
        rings.append(ring)
    for station_index in range(len(rings) - 1):
        first = rings[station_index]
        second = rings[station_index + 1]
        for index in range(sides):
            nxt = (index + 1) % sides
            _triangle(mesh, first[index], second[index], second[nxt], station_index)
            _triangle(mesh, first[index], second[nxt], first[nxt], station_index)
    for ring, reverse in ((rings[0], True), (rings[-1], False)):
        center_x = stations[0][0] if reverse else stations[-1][0]
        center_z = stations[0][3] if reverse else stations[-1][3]
        center = _vertex(mesh, (center_x, 0.0, center_z))
        for index in range(sides):
            nxt = (index + 1) % sides
            if reverse:
                _triangle(mesh, center, ring[nxt], ring[index], 100)
            else:
                _triangle(mesh, center, ring[index], ring[nxt], 100)
    mesh.recompute_normals(NORMALS)
    return mesh


def station_at(stations, x):
    for index in range(len(stations) - 1):
        left, right = stations[index], stations[index + 1]
        if left[0] <= x <= right[0]:
            alpha = (x - left[0]) / max(1.0, right[0] - left[0])
            return (
                x,
                left[1] + (right[1] - left[1]) * alpha,
                left[2] + (right[2] - left[2]) * alpha,
                left[3] + (right[3] - left[3]) * alpha,
            )
    return stations[0] if x < stations[0][0] else stations[-1]


def armor_band_mesh(stations, pieces, angle_start_deg, angle_end_deg,
                    outer_scale=1.035, thickness_scale=0.975, angle_steps=7):
    """Build closed conformal armor plates over selected hull arcs."""
    mesh = unreal.DynamicMesh()
    angles = [
        math.radians(angle_start_deg + (angle_end_deg - angle_start_deg) * i / angle_steps)
        for i in range(angle_steps + 1)
    ]
    for piece_index, (x0, x1) in enumerate(pieces):
        samples = [x0, (x0 + x1) * 0.5, x1]
        outer = []
        inner = []
        for x in samples:
            _, half_y, half_z, z_offset = station_at(stations, x)
            outer.append([
                _vertex(mesh, (x, *_profile(half_y * outer_scale, half_z * outer_scale,
                                            angle, z_offset=z_offset)))
                for angle in angles
            ])
            inner.append([
                _vertex(mesh, (x, *_profile(half_y * outer_scale * thickness_scale,
                                            half_z * outer_scale * thickness_scale,
                                            angle, z_offset=z_offset)))
                for angle in angles
            ])
        group = piece_index
        for sample in range(len(samples) - 1):
            for angle_index in range(len(angles) - 1):
                nxt = angle_index + 1
                _triangle(mesh, outer[sample][angle_index], outer[sample + 1][angle_index],
                          outer[sample + 1][nxt], group)
                _triangle(mesh, outer[sample][angle_index], outer[sample + 1][nxt],
                          outer[sample][nxt], group)
                _triangle(mesh, inner[sample][angle_index], inner[sample + 1][nxt],
                          inner[sample + 1][angle_index], group)
                _triangle(mesh, inner[sample][angle_index], inner[sample][nxt],
                          inner[sample + 1][nxt], group)
        for sample in (0, len(samples) - 1):
            reverse = sample == 0
            for angle_index in range(len(angles) - 1):
                nxt = angle_index + 1
                quad = (outer[sample][angle_index], outer[sample][nxt],
                        inner[sample][nxt], inner[sample][angle_index])
                if reverse:
                    _triangle(mesh, quad[0], quad[2], quad[1], group)
                    _triangle(mesh, quad[0], quad[3], quad[2], group)
                else:
                    _triangle(mesh, quad[0], quad[1], quad[2], group)
                    _triangle(mesh, quad[0], quad[2], quad[3], group)
        for angle_index in (0, len(angles) - 1):
            reverse = angle_index == 0
            for sample in range(len(samples) - 1):
                quad = (outer[sample][angle_index], outer[sample + 1][angle_index],
                        inner[sample + 1][angle_index], inner[sample][angle_index])
                if reverse:
                    _triangle(mesh, quad[0], quad[1], quad[2], group)
                    _triangle(mesh, quad[0], quad[2], quad[3], group)
                else:
                    _triangle(mesh, quad[0], quad[2], quad[1], group)
                    _triangle(mesh, quad[0], quad[3], quad[2], group)
    mesh.recompute_normals(NORMALS)
    return mesh


def boxes(entries):
    return base.boxes(entries)


def tori_x(entries):
    """Append torus bands whose axis follows X, matching longitudinal drums."""
    mesh = unreal.DynamicMesh()
    for center, major, minor in entries:
        mesh.append_torus(
            base.PRIMITIVE,
            base.xf(center[0], center[1], center[2], pitch=90),
            unreal.GeometryScriptRevolveOptions(), major, minor, 48, 12,
        )
    mesh.recompute_normals(NORMALS)
    return mesh


def create_asset(folder, name, mesh, material_key, role):
    base.ITERATION = ITERATION
    base.MATERIALS.update(MATERIALS)
    return base.create_asset(folder, name, mesh, material_key, role)


def corvette_assets():
    folder = f"{ROOT}/MilitaryCorvette/Working/{ITERATION}"
    stations = [
        (-120000, 15000, 22000, -3000),
        (-110000, 19000, 25000, -3000),
        (-90000, 20500, 26500, -3000),
        (-55000, 20700, 27000, -3000),
        (-15000, 20700, 27000, -3000),
        (25000, 20600, 26800, -3000),
        (65000, 20400, 25800, -3200),
        (93000, 18400, 23500, -3400),
        (112000, 14200, 19500, -3600),
        (120000, 10500, 15500, -3800),
    ]
    hull = loft_mesh(stations)
    # One dominant hangar district per side, cut deeply enough to read as void.
    for side in (-1, 1):
        base.subtract_box(hull, (55500, side * 20200, -5000), (57000, 10500, 19000))

    dorsal_pieces = [(-108000, -81000), (-76000, -36000), (-30000, 12000),
                     (18000, 57000), (63000, 92000), (97000, 112000)]
    dorsal = armor_band_mesh(stations, dorsal_pieces, 31, 149, 1.035, 0.975, 8)
    port_belt = armor_band_mesh(stations, [(-101000, -65000), (-56000, -12000),
                                           (-4000, 34000), (82000, 108000)],
                                  166, 194, 1.038, 0.968, 4)
    starboard_belt = armor_band_mesh(stations, [(-101000, -65000), (-56000, -12000),
                                                (-4000, 34000), (82000, 108000)],
                                       -14, 14, 1.038, 0.968, 4)
    # Broad flank shoulders establish the concept's layered armored districts.
    # The forward hangar interval stays uncovered so the negative space wins.
    shoulder_pieces = [(-108000, -75000), (-68000, -30000),
                       (-22000, 18000), (83000, 112000)]
    port_shoulder = armor_band_mesh(stations, shoulder_pieces, 126, 162, 1.045, 0.958, 5)
    starboard_shoulder = armor_band_mesh(stations, shoulder_pieces, 18, 54, 1.045, 0.958, 5)
    lower_pieces = [(-102000, -62000), (-52000, -10000),
                    (0, 38000), (85000, 112000)]
    port_lower = armor_band_mesh(stations, lower_pieces, 198, 232, 1.043, 0.96, 5)
    starboard_lower = armor_band_mesh(stations, lower_pieces, 308, 342, 1.043, 0.96, 5)
    keel = armor_band_mesh(stations, [(-92000, -32000), (-25000, 36000),
                                      (43000, 93000)], 218, 322, 1.04, 0.97, 6)

    hangar_back = []
    hangar_frames = []
    for side in (-1, 1):
        y = side * 16600
        hangar_back.append(((55500, y, -5000), (51000, 900, 15000)))
        frame_y = side * 21300
        hangar_frames.extend([
            ((27000, frame_y, -5000), (3500, 1100, 22500)),
            ((84000, frame_y, -5000), (3500, 1100, 22500)),
            ((55500, frame_y, 6250), (60500, 1100, 3500)),
            ((55500, frame_y, -16250), (60500, 1100, 3500)),
        ])

    command = loft_mesh([
        (-47000, 9000, 2300, 25500),
        (-36000, 15500, 5200, 25800),
        (-7000, 15500, 5200, 25800),
        (9000, 9000, 2500, 25300),
    ], 24)
    command_tower = loft_mesh([
        (-35000, 5200, 1400, 30500),
        (-28000, 8500, 3000, 30600),
        (-15000, 7000, 2300, 30600),
        (-9000, 4000, 1200, 30400),
    ], 20)
    drive = []
    glow = []
    for y in (-10500, -3500, 3500, 10500):
        for z in (-13500, -6500, 500, 7500):
            drive.append(((-119000, y, z), 2500, 6500, 32))
            glow.append(((-125150, y, z), 1700, 350, 32))

    # Rounded/octagonal stern face continues the pressure-hull section instead
    # of exposing a rectangular kitbash plate behind the drive array.
    engine_face = loft_mesh([
        (-120650, 16500, 23500, -3000),
        (-119350, 16500, 23500, -3000),
    ], 32)

    accents = boxes([
        ((-73000, -18500, 9400), (9000, 500, 1100)),
        ((-73000, 18500, 9400), (9000, 500, 1100)),
        ((6000, -20200, 6500), (12000, 500, 1100)),
        ((6000, 20200, 6500), (12000, 500, 1100)),
        ((91000, 0, 19400), (8000, 5000, 900)),
    ])
    return folder, {
        "PrimaryHull": create_asset(folder, "SM_MilitaryCorvette_PrimaryHull09", hull, "hull", "ContinuousPressureHull"),
        "DorsalArmor": create_asset(folder, "SM_MilitaryCorvette_DorsalArmor09", dorsal, "panel_light", "ConformalDorsalArmor"),
        "PortArmor": create_asset(folder, "SM_MilitaryCorvette_PortArmor09", port_belt, "panel_dark", "PortDefenseBelt"),
        "StarboardArmor": create_asset(folder, "SM_MilitaryCorvette_StarboardArmor09", starboard_belt, "panel_dark", "StarboardDefenseBelt"),
        "PortShoulder": create_asset(folder, "SM_MilitaryCorvette_PortShoulder09", port_shoulder, "armor", "PortArmoredShoulder"),
        "StarboardShoulder": create_asset(folder, "SM_MilitaryCorvette_StarboardShoulder09", starboard_shoulder, "armor", "StarboardArmoredShoulder"),
        "PortLowerArmor": create_asset(folder, "SM_MilitaryCorvette_PortLowerArmor09", port_lower, "hull", "PortLowerMachineryArmor"),
        "StarboardLowerArmor": create_asset(folder, "SM_MilitaryCorvette_StarboardLowerArmor09", starboard_lower, "hull", "StarboardLowerMachineryArmor"),
        "KeelArmor": create_asset(folder, "SM_MilitaryCorvette_KeelArmor09", keel, "armor_dark", "ArmoredKeel"),
        "HangarBacks": create_asset(folder, "SM_MilitaryCorvette_HangarBacks09", boxes(hangar_back), "structure", "DeepHangarVoid"),
        "HangarFrames": create_asset(folder, "SM_MilitaryCorvette_HangarFrames09", boxes(hangar_frames), "armor_dark", "HangarFrames"),
        "Command": create_asset(folder, "SM_MilitaryCorvette_Command09", command, "hull", "BuriedCitadel"),
        "CommandTower": create_asset(folder, "SM_MilitaryCorvette_CommandTower09", command_tower, "armor_dark", "CitadelTerrace"),
        "EngineFace": create_asset(folder, "SM_MilitaryCorvette_EngineFace09", engine_face, "structure", "RecessedDriveFace"),
        "Drive": create_asset(folder, "SM_MilitaryCorvette_Drive09", base.cylinders(drive), "structure", "DriveHousings"),
        "DriveGlow": create_asset(folder, "SM_MilitaryCorvette_DriveGlow09", base.cylinders(glow), "drive", "DriveGlow"),
        "Accents": create_asset(folder, "SM_MilitaryCorvette_Accents09", accents, "orange", "SparseSafetyMarkings"),
    }


def carrier_assets():
    folder = f"{ROOT}/ExpeditionCarrier/Working/{ITERATION}"
    stations = [
        (-325000, 50000, 67000, -6000),
        (-308000, 61000, 77000, -6000),
        (-270000, 66000, 82000, -6000),
        (-190000, 67000, 83500, -6000),
        (-90000, 67000, 84000, -6000),
        (25000, 66800, 84000, -6000),
        (135000, 66500, 82500, -6500),
        (225000, 64500, 78000, -7000),
        (285000, 58000, 70000, -7500),
        (315000, 43000, 54000, -8000),
        (325000, 31000, 41000, -8500),
    ]
    hull = loft_mesh(stations, 36)
    for side in (-1, 1):
        # Habitat and concourse are separate, strongly readable voids.
        base.subtract_box(hull, (-135000, side * 65000, -15000), (190000, 22000, 47000))
        base.subtract_box(hull, (125000, side * 65000, -12000), (145000, 22000, 51000))

    dorsal_pieces = [(-301000, -242000), (-234000, -150000), (-141000, -54000),
                     (-44000, 52000), (62000, 148000), (158000, 235000),
                     (244000, 298000)]
    dorsal = armor_band_mesh(stations, dorsal_pieces, 28, 152, 1.03, 0.976, 8)
    port = armor_band_mesh(stations, [(-290000, -220000), (-205000, -165000),
                                      (30000, 76000), (220000, 292000)],
                                   168, 192, 1.035, 0.97, 4)
    starboard = armor_band_mesh(stations, [(-290000, -220000), (-205000, -165000),
                                           (30000, 76000), (220000, 292000)],
                                        -12, 12, 1.035, 0.97, 4)
    # Three massive shoulders frame the habitat and concourse voids instead of
    # scattering detail evenly across the carrier's flank.
    shoulder_pieces = [(-307000, -245000), (-35000, 35000), (205000, 302000)]
    port_shoulder = armor_band_mesh(stations, shoulder_pieces, 126, 162, 1.04, 0.96, 5)
    starboard_shoulder = armor_band_mesh(stations, shoulder_pieces, 18, 54, 1.04, 0.96, 5)
    lower_pieces = [(-300000, -245000), (-35000, 35000), (210000, 302000)]
    port_lower = armor_band_mesh(stations, lower_pieces, 198, 232, 1.04, 0.96, 5)
    starboard_lower = armor_band_mesh(stations, lower_pieces, 308, 342, 1.04, 0.96, 5)
    keel = armor_band_mesh(stations, [(-285000, -170000), (-155000, -20000),
                                      (-5000, 145000), (160000, 285000)],
                                   218, 322, 1.035, 0.97, 6)

    frames = []
    backs = []
    for side in (-1, 1):
        frame_y = side * 69500
        for x0, x1, z, height in ((-230000, -40000, -15000, 50000),
                                  (52500, 197500, -12000, 54000)):
            center = (x0 + x1) * 0.5
            width = x1 - x0
            frames.extend([
                ((x0, frame_y, z), (7000, 1800, height + 9000)),
                ((x1, frame_y, z), (7000, 1800, height + 9000)),
                ((center, frame_y, z + height * 0.5), (width + 7000, 1800, 7000)),
                ((center, frame_y, z - height * 0.5), (width + 7000, 1800, 7000)),
            ])
            backs.append(((center, side * 54000, z), (width - 7000, 1200, height - 7000)))

    habitats = []
    habitat_rings = []
    for side in (-1, 1):
        for x in (-210000, -170000, -130000, -90000, -50000):
            habitats.append(((x + 15500, side * 51500, -15000), 17500, 31000, 36))
            habitat_rings.extend([
                ((x - 28500, side * 51500, -15000), 18400, 2100),
                ((x, side * 51500, -15000), 18400, 2100),
            ])

    command = loft_mesh([
        (-105000, 26000, 4000, 78500),
        (-78000, 42000, 8500, 79000),
        (10000, 42000, 8500, 79000),
        (50000, 25000, 4200, 78000),
    ], 28)
    command_tower = loft_mesh([
        (-76000, 13000, 2300, 85800),
        (-62000, 23000, 5500, 86400),
        (-35000, 19000, 4300, 86500),
        (-18000, 9000, 1800, 85800),
    ], 24)
    radiators = boxes([
        ((95000, -38000, 78900), (50000, 45000, 2500)),
        ((95000, 38000, 78900), (50000, 45000, 2500)),
        ((160000, -38000, 76000), (50000, 45000, 2500)),
        ((160000, 38000, 76000), (50000, 45000, 2500)),
        ((222000, -35000, 69000), (43000, 40000, 2500)),
        ((222000, 35000, 69000), (43000, 40000, 2500)),
    ])
    drive = []
    glow = []
    for y in (-48000, -16000, 16000, 48000):
        for z in (-42000, 0, 42000):
            drive.append(((-319000, y, z - 6000), 9000, 13000, 40))
            glow.append(((-331400, y, z - 6000), 6500, 600, 40))
    engine_face = loft_mesh([
        (-326100, 58000, 66000, -6000),
        (-324300, 58000, 66000, -6000),
    ], 36)
    accents = boxes([
        ((-245000, -62000, 24000), (22000, 1000, 2400)),
        ((-245000, 62000, 24000), (22000, 1000, 2400)),
        ((25000, -66000, 19000), (26000, 1000, 2400)),
        ((25000, 66000, 19000), (26000, 1000, 2400)),
        ((250000, 0, 56500), (28000, 12000, 1800)),
    ])
    return folder, {
        "PrimaryHull": create_asset(folder, "SM_ExpeditionCarrier_PrimaryHull09", hull, "hull", "ContinuousPressureHull"),
        "DorsalArmor": create_asset(folder, "SM_ExpeditionCarrier_DorsalArmor09", dorsal, "panel_light", "ConformalDorsalArmor"),
        "PortArmor": create_asset(folder, "SM_ExpeditionCarrier_PortArmor09", port, "panel_dark", "PortDefenseBelt"),
        "StarboardArmor": create_asset(folder, "SM_ExpeditionCarrier_StarboardArmor09", starboard, "panel_dark", "StarboardDefenseBelt"),
        "PortShoulder": create_asset(folder, "SM_ExpeditionCarrier_PortShoulder09", port_shoulder, "armor", "PortArmoredShoulder"),
        "StarboardShoulder": create_asset(folder, "SM_ExpeditionCarrier_StarboardShoulder09", starboard_shoulder, "armor", "StarboardArmoredShoulder"),
        "PortLowerArmor": create_asset(folder, "SM_ExpeditionCarrier_PortLowerArmor09", port_lower, "hull", "PortLowerMachineryArmor"),
        "StarboardLowerArmor": create_asset(folder, "SM_ExpeditionCarrier_StarboardLowerArmor09", starboard_lower, "hull", "StarboardLowerMachineryArmor"),
        "KeelArmor": create_asset(folder, "SM_ExpeditionCarrier_KeelArmor09", keel, "armor_dark", "ArmoredKeel"),
        "BayBacks": create_asset(folder, "SM_ExpeditionCarrier_BayBacks09", boxes(backs), "structure", "DeepBayVoids"),
        "BayFrames": create_asset(folder, "SM_ExpeditionCarrier_BayFrames09", boxes(frames), "armor_dark", "HabitatAndConcourseFrames"),
        "Habitats": create_asset(folder, "SM_ExpeditionCarrier_Habitats09", base.cylinders(habitats), "hull", "HabitatDrums"),
        "HabitatRings": create_asset(folder, "SM_ExpeditionCarrier_HabitatRings09", tori_x(habitat_rings), "armor_dark", "HabitatBands"),
        "Command": create_asset(folder, "SM_ExpeditionCarrier_Command09", command, "hull", "BuriedCommandCity"),
        "CommandTower": create_asset(folder, "SM_ExpeditionCarrier_CommandTower09", command_tower, "armor_dark", "CommandTerrace"),
        "Radiators": create_asset(folder, "SM_ExpeditionCarrier_Radiators09", radiators, "radiator", "DorsalRadiatorFields"),
        "EngineFace": create_asset(folder, "SM_ExpeditionCarrier_EngineFace09", engine_face, "structure", "RecessedDriveFace"),
        "Drive": create_asset(folder, "SM_ExpeditionCarrier_Drive09", base.cylinders(drive), "structure", "DriveHousings"),
        "DriveGlow": create_asset(folder, "SM_ExpeditionCarrier_DriveGlow09", base.cylinders(glow), "drive", "DriveGlow"),
        "Accents": create_asset(folder, "SM_ExpeditionCarrier_Accents09", accents, "orange", "SparseSafetyMarkings"),
    }


def load_mesh(path):
    mesh = unreal.EditorAssetLibrary.load_asset(path)
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing donor mesh: {path}")
    return mesh


def spawn_mesh(actor_subsystem, mesh, label, center=(0, 0, 0), target_size=None):
    return base.spawn_mesh(actor_subsystem, mesh, label, center, target_size)


def actor_bounds(actors):
    lo = unreal.Vector(1e30, 1e30, 1e30)
    hi = unreal.Vector(-1e30, -1e30, -1e30)
    for actor in actors:
        origin, extent = actor.get_actor_bounds(False)
        lo.x, lo.y, lo.z = min(lo.x, origin.x - extent.x), min(lo.y, origin.y - extent.y), min(lo.z, origin.z - extent.z)
        hi.x, hi.y, hi.z = max(hi.x, origin.x + extent.x), max(hi.y, origin.y + extent.y), max(hi.z, origin.z + extent.z)
    return lo, hi


def normalize_to_dimensions(actors, expected):
    lo, hi = actor_bounds(actors)
    center = unreal.Vector((lo.x + hi.x) * 0.5, (lo.y + hi.y) * 0.5, (lo.z + hi.z) * 0.5)
    size = unreal.Vector(hi.x - lo.x, hi.y - lo.y, hi.z - lo.z)
    factor = unreal.Vector(expected[0] / size.x, expected[1] / size.y, expected[2] / size.z)
    for actor in actors:
        location = actor.get_actor_location()
        scale = actor.get_actor_scale3d()
        actor.set_actor_location(unreal.Vector(
            (location.x - center.x) * factor.x,
            (location.y - center.y) * factor.y,
            (location.z - center.z) * factor.z,
        ), False, False)
        actor.set_actor_scale3d(unreal.Vector(scale.x * factor.x, scale.y * factor.y, scale.z * factor.z))
    lo, hi = actor_bounds(actors)
    return [hi.x - lo.x, hi.y - lo.y, hi.z - lo.z]


def build_map(ship, assets):
    config = MAPS[ship]
    levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if not unreal.EditorAssetLibrary.does_asset_exist(config["map"]):
        if not levels.new_level(config["map"]):
            raise RuntimeError(f"Could not create {config['map']}")
    if not levels.load_level(config["map"]):
        raise RuntimeError(f"Could not load {config['map']}")
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    for actor in actors.get_all_level_actors():
        if actor.get_actor_label().startswith(ACTOR_PREFIX):
            actors.destroy_actor(actor)
    built = [spawn_mesh(actors, mesh, f"{ACTOR_PREFIX}{ship}_{role}") for role, mesh in assets.items()]
    if ship == "MilitaryCorvette":
        placements = [
            ("hangar", "HangarPortInterior", (55500, -16600, -5000), (47000, 1800, 13500)),
            ("hangar", "HangarStarboardInterior", (55500, 16600, -5000), (47000, 1800, 13500)),
            ("command", "CitadelSensors", (-24500, 0, 30600), (13500, 6500, 900)),
            ("antenna", "CitadelMast", (-24500, 0, 31000), (800, 800, 500)),
        ]
    else:
        placements = [
            ("hangar", "ConcoursePortInterior", (125000, -54500, -12000), (125000, 2500, 39000)),
            ("hangar", "ConcourseStarboardInterior", (125000, 54500, -12000), (125000, 2500, 39000)),
            ("reactor", "RefineryPortInterior", (-255000, -53500, -12000), (27000, 3500, 17000)),
            ("reactor", "RefineryStarboardInterior", (-255000, 53500, -12000), (27000, 3500, 17000)),
            ("command", "CommandSensors", (-50000, 0, 88800), (26000, 13000, 1500)),
            ("antenna", "LongRangeMast", (-50000, 0, 89500), (1500, 1500, 1000)),
        ]
    donor_rows = []
    for donor_key, role, center, target_size in placements:
        donor = load_mesh(DONORS[donor_key])
        built.append(spawn_mesh(actors, donor, f"{ACTOR_PREFIX}{ship}_FAB_{role}", center, target_size))
        donor_rows.append({"role": role, "source": DONORS[donor_key], "target_size_cm": list(target_size)})
    size = normalize_to_dimensions(built, config["expected_cm"])
    verified = all(abs(size[index] - config["expected_cm"][index]) <= 100.0 for index in range(3))
    levels.save_current_level()
    return {
        "ship": ship,
        "map": config["map"],
        "expected_cm": list(config["expected_cm"]),
        "assembled_size_cm": size,
        "scale_verified": verified,
        "generated_assets": [mesh.get_path_name() for mesh in assets.values()],
        "fab_placements": donor_rows,
        "primary_method": "single station-lofted superelliptic Dynamic Mesh",
    }


def main():
    for path in MATERIALS.values():
        if not isinstance(unreal.EditorAssetLibrary.load_asset(path), unreal.MaterialInterface):
            raise RuntimeError(f"Missing material: {path}")
    _, corvette = corvette_assets()
    corvette_result = build_map("MilitaryCorvette", corvette)
    _, carrier = carrier_assets()
    carrier_result = build_map("ExpeditionCarrier", carrier)
    results = [corvette_result, carrier_result]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "version": 1,
        "iteration": ITERATION,
        "concept_authority": [
            "docs/concept-art/reference/ships/medium-military-corvette-exterior.png",
            "docs/concept-art/reference/ships/large-expedition-carrier-exterior.png",
        ],
        "rejected_iteration_preserved": "Iteration_08_Declutter",
        "method": "continuous concept-silhouette hulls, conformal macro armor, landmark voids, localized Fab detail",
        "ships": results,
    }, indent=2), encoding="utf-8")
    if not all(result["scale_verified"] for result in results):
        raise RuntimeError("Iteration 09 failed its exact scale gate")
    unreal.log("UNREAL SHIP CONCEPT RESET V09: complete")


if __name__ == "__main__":
    main()
