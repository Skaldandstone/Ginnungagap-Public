"""Field supplies draw Fab props, not the project's greybox item meshes.

The ten DA_Item_* definitions under FieldSupplies carried 48-to-418-vertex placeholder meshes with
flat-colour materials. Each is re-pointed at a Fab prop of about the right kind and scaled to a
hand-held size (world_mesh / world_mesh_scale on the item definition); every pickup draws the
definition's mesh at construction, so the maps need no edit.

    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/fab_field_supply_meshes.py -NullRHI
"""
import unreal

ITEMS = "/Game/Assets/Gameplay/FieldSupplies/Data/Items"
ENGP = "/Game/ModSci_EngiProps/Meshes"
FRONT = "/Game/Frontier_EngineersToolbox/Tools"
# item -> (fab mesh, target longest side in cm)
MAPPING = {
    "EmergencyOxygenCartridge": (f"{ENGP}/SM_OxygenTank_B", 40.0),
    "FieldRepairKit": (f"{ENGP}/SM_Toolbox", 38.0),
    "TraumaKit": (f"{ENGP}/SM_Case_A", 34.0),
    "CoolantGelPack": (f"{ENGP}/SM_Case_A", 26.0),
    "SuitPatchSealant": (f"{ENGP}/SM_WireReel_A", 22.0),
    "ThermalRegulationWrap": (f"{ENGP}/SM_RubberMat_Rolled", 38.0),
    "CompoundSplint": (f"{ENGP}/SM_RubberMat_Rolled", 40.0),
    "ChelationInjector": (f"{FRONT}/SM_Frontier_Scanner", 24.0),
    "GeneralMedicalAmpoule": (f"{FRONT}/SM_Frontier_Scanner", 18.0),
    "RecompressionAmpoule": (f"{FRONT}/SM_Frontier_Scanner", 18.0),
}

done = 0
for item, (mesh_path, target) in MAPPING.items():
    definition = unreal.load_asset(f"{ITEMS}/DA_Item_{item}")
    mesh = unreal.load_asset(mesh_path)
    if not definition or not mesh:
        print(f"SUPPLYMESH skip {item}: definition={bool(definition)} mesh={bool(mesh)}")
        continue
    b = mesh.get_bounding_box()
    longest = max(b.max.x - b.min.x, b.max.y - b.min.y, b.max.z - b.min.z, 1e-3)
    s = target / longest
    definition.set_editor_property("world_mesh", mesh)
    definition.set_editor_property("world_mesh_scale", unreal.Vector(s, s, s))
    unreal.EditorAssetLibrary.save_loaded_asset(definition)
    print(f"SUPPLYMESH {item}: {mesh.get_name()} x{s:.2f}")
    done += 1
print(f"SUPPLYMESH re-pointed {done}/{len(MAPPING)} items")
