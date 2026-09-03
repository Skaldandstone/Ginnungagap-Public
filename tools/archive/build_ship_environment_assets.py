"""Build damage, atmosphere, audio, and staged Bloom environment assets for ship levels."""

from __future__ import annotations

import math
import random
import struct
import sys
import wave
from pathlib import Path

import unreal


TOOLS_DIR = Path(__file__).resolve().parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from build_ship_production_assets import ObjMesh, import_mesh, create_material  # noqa: E402


ROOT = "/Game/Assets/Ships/Production"
MESH_PATH = ROOT + "/Meshes"
MAT_PATH = ROOT + "/Materials"
AUDIO_PATH = ROOT + "/Audio"
BP_PATH = ROOT + "/Blueprints/Environment"
MAP_PATH = "/Game/Assets/Maps/ShipProduction"
SOURCE_DIR = Path(unreal.SystemLibrary.get_project_directory()) / "Intermediate" / "ShipProduction" / "Environment"


def load(path):
    result = unreal.load_asset(path)
    if not result:
        raise RuntimeError("Missing asset: " + path)
    return result


def build_growth_meshes():
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    meshes = {}

    nodule = ObjMesh("SM_FX_BloomNodule")
    nodule.sphere((0, 0, 35), 45, 8, 18, (1.25, 1.0, 0.8))
    for offset, radius in (((38, 4, 22), 24), ((-31, 17, 26), 19), ((4, -34, 19), 15)):
        nodule.sphere(offset, radius, 6, 14)
    meshes[nodule.name] = nodule

    tendril = ObjMesh("SM_FX_BloomTendril")
    for index in range(7):
        x = index * 65.0
        y = math.sin(index * 0.85) * 38.0
        z = 18.0 + math.cos(index * 0.55) * 14.0
        tendril.cylinder((x, y, z), max(7.0, 18.0 - index * 1.5), 82.0, 12, "x")
    meshes[tendril.name] = tendril

    rib = ObjMesh("SM_FX_BloomCalcifiedRib")
    for index in range(5):
        x = (index - 2) * 65.0
        rib.box((x, 0, 100 + abs(index - 2) * 15), (30, 55, 210 - abs(index - 2) * 25))
        rib.box((x, 0, 205), (30, 55, 130))
    meshes[rib.name] = rib

    result = {}
    for name, mesh in meshes.items():
        source = SOURCE_DIR / (name + ".obj")
        mesh.write(source)
        result[name] = import_mesh(name, source)
    return result


def create_decal_material():
    path = MAT_PATH + "/M_Damage_ScorchDecal"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return load(path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_Damage_ScorchDecal", MAT_PATH, unreal.Material, unreal.MaterialFactoryNew())
    material.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)
    material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    color = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -250, 0)
    color.set_editor_property("constant", unreal.LinearColor(0.035, 0.008, 0.003, 1.0))
    opacity = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -250, 120)
    opacity.set_editor_property("r", 0.72)
    roughness = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -250, 220)
    roughness.set_editor_property("r", 0.92)
    unreal.MaterialEditingLibrary.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(opacity, "", unreal.MaterialProperty.MP_OPACITY)
    unreal.MaterialEditingLibrary.connect_material_property(roughness, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


def write_loop(path, kind, seconds=4, sample_rate=44100):
    random.seed(4103 + len(kind))
    frames = []
    for index in range(seconds * sample_rate):
        t = index / sample_rate
        if kind == "hum":
            value = 0.18 * math.sin(math.tau * 47 * t) + 0.08 * math.sin(math.tau * 94 * t)
            value += 0.025 * (random.random() * 2 - 1)
        elif kind == "alarm":
            gate = 1.0 if (t % 1.2) < 0.52 else 0.0
            value = gate * (0.24 * math.sin(math.tau * 690 * t) + 0.12 * math.sin(math.tau * 345 * t))
        else:
            drift = 37 + 8 * math.sin(math.tau * 0.22 * t)
            value = 0.16 * math.sin(math.tau * drift * t) + 0.09 * math.sin(math.tau * 73 * t)
            value += 0.035 * (random.random() * 2 - 1)
        envelope = min(1.0, index / 800.0, (seconds * sample_rate - index) / 800.0)
        frames.append(struct.pack("<h", int(max(-1.0, min(1.0, value * envelope)) * 32767)))
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"".join(frames))


def import_sound(name, kind):
    destination = f"{AUDIO_PATH}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(destination):
        sound = load(destination)
    else:
        source = SOURCE_DIR / (name + ".wav")
        write_loop(source, kind)
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", str(source))
        task.set_editor_property("destination_path", AUDIO_PATH)
        task.set_editor_property("destination_name", name)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", False)
        task.set_editor_property("save", True)
        unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        sound = load(destination)
    sound.set_editor_property("looping", True)
    unreal.EditorAssetLibrary.save_loaded_asset(sound)
    return sound


def create_blueprint(name, defaults):
    path = f"{BP_PATH}/{name}"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        blueprint = load(path)
    else:
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.ShipEnvironmentController)
        blueprint = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, BP_PATH, unreal.Blueprint, factory)
    cdo = unreal.get_default_object(blueprint.generated_class())
    for prop, value in defaults.items():
        cdo.set_editor_property(prop, value)
    unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
    return blueprint


def build_state_blueprints(meshes, materials, sounds):
    common = {
        "bloom_nodule_mesh": meshes["SM_FX_BloomNodule"],
        "bloom_tendril_mesh": meshes["SM_FX_BloomTendril"],
        "bloom_rib_mesh": meshes["SM_FX_BloomCalcifiedRib"],
        "bloom_colony_material": materials["colony"],
        "bloom_advanced_material": materials["advanced"],
        "damage_decal_material": materials["damage"],
        "ship_hum_sound": sounds["hum"],
        "alarm_sound": sounds["alarm"],
        "bloom_sound": sounds["bloom"],
    }
    stages = unreal.BloomStage
    definitions = {
        "BP_Ship_Environment_Clean": (stages.LATENT, False, False),
        "BP_Ship_Environment_Alert": (stages.LATENT, True, False),
        "BP_Ship_Environment_Damaged": (stages.LATENT, True, True),
        "BP_Ship_Environment_Colony": (stages.COLONY, False, True),
        "BP_Ship_Environment_Swarm": (stages.SWARM, True, True),
        "BP_Ship_Environment_Puppeteer": (stages.PUPPETEER, True, True),
        "BP_Ship_Environment_Infector": (stages.INFECTOR, True, True),
        "BP_Ship_Environment_Manifestation": (stages.MANIFESTATION, True, True),
        "BP_Ship_Environment_Live": (stages.LATENT, False, False),
    }
    result = {}
    for name, (stage, alert, damage) in definitions.items():
        defaults = dict(common)
        defaults.update({"preview_bloom_stage": stage, "alert_active": alert, "damage_active": damage})
        if name == "BP_Ship_Environment_Live":
            defaults.update({"follow_live_bloom_state": True, "follow_ship_damage_state": True})
        result[name] = create_blueprint(name, defaults)
    unreal.EditorAssetLibrary.save_directory(BP_PATH)
    return result


def place_controllers(blueprints):
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    mapping = {name: "BP_Ship_Environment_Live" for name in (
        "L_Small_Companionway_Showcase",
        "L_Medium_ExpressSpine_Showcase",
        "L_Large_CarrierConcourse_Showcase",
    )}
    for map_name, bp_name in mapping.items():
        level.load_level(f"{MAP_PATH}/{map_name}")
        for existing in [a for a in actor_subsystem.get_all_level_actors()
                         if a.get_actor_label() == "ShipEnvironmentController"]:
            actor_subsystem.destroy_actor(existing)
        actor = actor_subsystem.spawn_actor_from_class(
            blueprints[bp_name].generated_class(), unreal.Vector(0, 0, 20), unreal.Rotator())
        actor.set_actor_label("ShipEnvironmentController")
        actor.set_editor_property("follow_live_bloom_state", True)
        actor.set_editor_property("follow_ship_damage_state", True)
        level.save_current_level()


def main():
    unreal.log("Building ship damage, atmosphere, audio, and Bloom environment assets...")
    meshes = build_growth_meshes()
    materials = {
        "colony": create_material("M_Bloom_ColonyWet", (0.12, 0.015, 0.2), 0.24, 0.05, 1.7),
        "advanced": create_material("M_Bloom_AdvancedCalcified", (0.31, 0.19, 0.38), 0.38, 0.08, 2.6),
        "damage": create_decal_material(),
    }
    sounds = {
        "hum": import_sound("S_Ship_AmbientHum_Loop", "hum"),
        "alarm": import_sound("S_Ship_DamageAlarm_Loop", "alarm"),
        "bloom": import_sound("S_Bloom_Atmosphere_Loop", "bloom"),
    }
    blueprints = build_state_blueprints(meshes, materials, sounds)
    place_controllers(blueprints)
    unreal.EditorAssetLibrary.save_directory(ROOT)
    unreal.log("Environment pass complete: 3 meshes, 3 materials, 3 sounds, 8 presets, and 1 live Blueprint.")


if __name__ == "__main__":
    main()
