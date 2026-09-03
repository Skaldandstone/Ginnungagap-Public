"""Tune the V32 cryo suit for readable dark technical fabric under creator lighting."""

import json
from pathlib import Path

import unreal


PATH = (
    "/Game/Characters/Player/Undersuit/MetaHuman/"
    "MI_MH_CryoBodysuit_Standard.MI_MH_CryoBodysuit_Standard"
)
material = unreal.EditorAssetLibrary.load_asset(PATH)
if not isinstance(material, unreal.MaterialInstanceConstant):
    raise RuntimeError(f"Missing cryo material instance: {PATH}")

unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
    material, "SuitColor", unreal.LinearColor(0.055, 0.11, 0.13, 1.0)
)
unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
    material, "FiberColor", unreal.LinearColor(0.16, 0.28, 0.31, 1.0)
)
unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
    material, "EdgeColor", unreal.LinearColor(0.04, 0.22, 0.26, 1.0)
)
for name, value in {
    "FiberAmount": 0.22,
    "EdgeStrength": 0.20,
    "Roughness": 0.61,
    "Specular": 0.34,
    "Metallic": 0.01,
}.items():
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(material, name, value)
unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False)

report = {"status": "pass", "material": material.get_path_name(), "finish": "dark teal technical compression fabric"}
(Path(unreal.Paths.project_saved_dir()) / "MetaHumanCryoBodysuitMaterialTune.json").write_text(
    json.dumps(report, indent=2), encoding="utf-8"
)
unreal.log(f"METAHUMAN_CRYO_MATERIAL_TUNE {json.dumps(report, separators=(',', ':'))}")
unreal.SystemLibrary.quit_editor()
