"""Report dimensions for the Fab meshes selected as Bloom prototype sources."""

import json
from pathlib import Path

import unreal


SOURCES = [
    "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple",
    "/Game/DeadBodies_Poses_nikoff/Demo/Mannequins/Meshes/SKM_Manny_Simple",
    "/Game/Characters/Player/Suit/PackagedCombined/SkeletalPrototype/SKM_PlayerSuit_Prototype",
    "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt/Working/Iteration_02_ConceptSilhouette/SKM_PrimaryOversuit_QuinnProjectionShell_I02",
    "/Game/Assets/Models/Drones/SM_Drone_Repair",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_BODY",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_HEAD",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_ARM",
    "/Game/Modular_Scifi_Mechanic_Base/Mesh/SM/PROP/MACHINE/SM_JACK_LEG",
    "/Game/SF_White_desert/Meshes/Crystals/SM_crystal_01",
    "/Game/SF_White_desert/Meshes/Crystals/SM_crystal_02",
    "/Game/SF_White_desert/Meshes/Crystals/SM_crystal_03",
    *[
        f"/Game/Alien_Biomass/Meshes/Alien_organism/SM_alien_organism_{index:02d}"
        for index in (1, 3, 5, 7, 10, 13)
    ],
]


def mesh_bounds(asset):
    if isinstance(asset, unreal.StaticMesh):
        box = asset.get_bounding_box()
        return {
            "min": [box.min.x, box.min.y, box.min.z],
            "max": [box.max.x, box.max.y, box.max.z],
            "size": [box.max.x - box.min.x, box.max.y - box.min.y, box.max.z - box.min.z],
        }
    if isinstance(asset, unreal.SkeletalMesh):
        bounds = asset.get_bounds()
        extent = bounds.box_extent
        origin = bounds.origin
        return {
            "min": [origin.x - extent.x, origin.y - extent.y, origin.z - extent.z],
            "max": [origin.x + extent.x, origin.y + extent.y, origin.z + extent.z],
            "size": [extent.x * 2.0, extent.y * 2.0, extent.z * 2.0],
        }
    return None


report = []
for path in SOURCES:
    asset = unreal.EditorAssetLibrary.load_asset(path)
    report.append(
        {
            "path": path,
            "class": asset.get_class().get_name() if asset else None,
            "bounds": mesh_bounds(asset) if asset else None,
        }
    )

output = Path(unreal.SystemLibrary.get_project_saved_directory()) / "Reports/BloomFabSourceAudit.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(report, indent=2), encoding="utf-8")
unreal.log(f"Bloom Fab source audit written to {output}")
