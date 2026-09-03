"""Apply the corrected neutral material hierarchy to existing V06 hull assets."""

import unreal


ARMOR = "/Game/Assets/Materials/Production/Instances/MI_Surface_ExteriorHull"
STRUCTURE = "/Game/Assets/Materials/Production/Instances/MI_Surface_Environment"
ROOT = "/Game/Assets/Ships/Exterior/UnrealSculpt"
ITERATION = "Iteration_06_ConceptHull"

ASSIGNMENTS = {
    "MilitaryCorvette": {
        "armor": ["SM_MilitaryCorvette_Armor06", "SM_MilitaryCorvette_Command06"],
        "structure": [
            "SM_MilitaryCorvette_Backbone06", "SM_MilitaryCorvette_DefenseBelts06",
            "SM_MilitaryCorvette_HangarFrames06", "SM_MilitaryCorvette_Keel06",
            "SM_MilitaryCorvette_Drive06",
        ],
    },
    "ExpeditionCarrier": {
        "armor": ["SM_ExpeditionCarrier_Armor06", "SM_ExpeditionCarrier_Command06"],
        "structure": [
            "SM_ExpeditionCarrier_Backbone06", "SM_ExpeditionCarrier_DefenseBelts06",
            "SM_ExpeditionCarrier_HangarFrames06", "SM_ExpeditionCarrier_Keel06",
            "SM_ExpeditionCarrier_HabitatRings06", "SM_ExpeditionCarrier_Drive06",
        ],
    },
}

materials = {
    "armor": unreal.EditorAssetLibrary.load_asset(ARMOR),
    "structure": unreal.EditorAssetLibrary.load_asset(STRUCTURE),
}
if not all(isinstance(value, unreal.MaterialInterface) for value in materials.values()):
    raise RuntimeError("Neutral V06 materials are missing")

changed = []
for ship, groups in ASSIGNMENTS.items():
    folder = f"{ROOT}/{ship}/Working/{ITERATION}"
    for material_role, names in groups.items():
        for name in names:
            path = f"{folder}/{name}"
            asset = unreal.EditorAssetLibrary.load_asset(path)
            if not isinstance(asset, unreal.StaticMesh):
                raise RuntimeError(f"Missing V06 mesh: {path}")
            asset.set_material(0, materials[material_role])
            if not unreal.EditorAssetLibrary.save_loaded_asset(asset):
                raise RuntimeError(f"Could not save V06 mesh: {path}")
            changed.append(path)

unreal.log(f"CONCEPT HULL V06: corrected neutral materials on {len(changed)} meshes")
