"""Assemble and render the V25 I08 concept-specific four-role lineup."""

from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory()).resolve()
OUTPUT = PROJECT / "Saved/Renders"
ROOT = "/Game/Characters/PlayerSuits/PrimaryOversuits/V25ProjectionSculpt"
I04 = ROOT + "/Working/Iteration_04_FunctionalDetail"
I06 = ROOT + "/Working/Iteration_06_UncorruptedProductionShell"
I07_MATERIALS = ROOT + "/Working/Iteration_07_ConceptAlignedRoleLineup/Materials"
I08 = ROOT + "/Working/Iteration_08_ConceptSpecificModules"
MESH_PATH = I06 + "/Source/SKM_V25_I06_SpaceMarshalMale"
MAP_PATH = ROOT + "/Maps/L_PrimaryOversuit_V25_ConceptSpecific_I08"

# Camera-facing order is Crew, Engineering, Medical, Security.
ROLES = {
    "Crew": 96.0,
    "Engineering": 32.0,
    "Medical": -32.0,
    "Security": -96.0,
}

SHARED = (
    (I08, "SM_V25_I08_PressureDome", "visor", 0.0),
    (I08, "SM_V25_I08_IntegratedCollar", "hard", 0.0),
    (I08, "SM_V25_I08_HelmetFrame", "hard", 0.0),
    (I08, "SM_V25_I08_HarnessWebbing", "trim", 0.0),
    (I08, "SM_V25_I08_ChestComputerFrame", "hard", 0.0),
    (I08, "SM_V25_I08_ChestComputerScreen", "screen", 0.0),
    (I08, "SM_V25_I08_KneeShells", "hard", 0.0),
    (I04, "SM_V25_I04_LifeSupportPack", "hard", 15.0),
    (I04, "SM_V25_I04_LifeSupportDetail", "trim", 15.0),
)


def load_material(role, kind):
    names = {
        "fabric": f"M_V25_I07_{role}_Fabric",
        "hard": f"M_V25_I07_{role}_Hard",
        "accent": f"M_V25_I07_{role}_Accent",
        "trim": f"M_V25_I07_{role}_Trim",
        "screen": f"M_V25_I07_{role}_Screen",
        "visor": "M_V25_I07_ClearPressureDome",
        "hidden": "M_V25_I07_HiddenDonorSection",
        "preview": "M_V25_I07_Crew_Trim",
    }
    material = unreal.EditorAssetLibrary.load_asset(f"{I07_MATERIALS}/{names[kind]}")
    if not isinstance(material, unreal.MaterialInterface):
        raise RuntimeError(f"Missing I08 assembly material: {role}/{kind}")
    return material


def spawn_static(actors, folder, name, x, z, material, label):
    asset = unreal.EditorAssetLibrary.load_asset(f"{folder}/{name}")
    if not isinstance(asset, unreal.StaticMesh):
        raise RuntimeError(f"Missing I08 module {folder}/{name}")
    actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(x, 0.0, z), unreal.Rotator()
    )
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(asset)
    actor.static_mesh_component.set_material(0, material)
    return actor


def add_rect_light(actors, label, location, target, intensity, width, height, color):
    light = actors.spawn_actor_from_class(
        unreal.RectLight, location, unreal.MathLibrary.find_look_at_rotation(location, target)
    )
    light.set_actor_label(label)
    light.rect_light_component.set_editor_property("intensity", intensity)
    light.rect_light_component.set_editor_property("source_width", width)
    light.rect_light_component.set_editor_property("source_height", height)
    light.rect_light_component.set_editor_property("light_color", color)


def capture(world, actors, filename, location, target, width, height, fov):
    camera = actors.spawn_actor_from_class(
        unreal.SceneCapture2D, location, unreal.MathLibrary.find_look_at_rotation(location, target)
    )
    camera.set_actor_label("RENDER_" + filename)
    component = camera.capture_component2d
    component.capture_every_frame = False
    component.capture_on_movement = False
    component.fov_angle = fov
    texture = unreal.RenderingLibrary.create_render_target2d(
        world, width, height, unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0.115, 0.125, 0.142, 1.0),
    )
    component.texture_target = texture
    component.capture_source = unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR
    pp = component.post_process_settings
    pp.set_editor_property("override_auto_exposure_method", True)
    pp.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    pp.set_editor_property("override_camera_iso", True)
    pp.set_editor_property("camera_iso", 180.0)
    pp.set_editor_property("override_camera_shutter_speed", True)
    pp.set_editor_property("camera_shutter_speed", 60.0)
    pp.set_editor_property("override_auto_exposure_bias", True)
    pp.set_editor_property("auto_exposure_bias", 1.25)
    component.post_process_settings = pp
    component.capture_scene()
    component.capture_scene()
    unreal.RenderingLibrary.export_render_target(world, texture, str(OUTPUT), filename)
    camera.destroy_actor()


OUTPUT.mkdir(parents=True, exist_ok=True)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
if unreal.EditorAssetLibrary.does_asset_exist(MAP_PATH):
    if not levels.load_level(MAP_PATH):
        raise RuntimeError(f"Could not load {MAP_PATH}")
elif not levels.new_level(MAP_PATH):
    raise RuntimeError(f"Could not create {MAP_PATH}")

world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for actor in actors.get_all_level_actors():
    actors.destroy_actor(actor)

mesh = unreal.EditorAssetLibrary.load_asset(MESH_PATH)
if not isinstance(mesh, unreal.SkeletalMesh):
    raise RuntimeError(f"Missing authored garment donor {MESH_PATH}")
slots = list(mesh.get_editor_property("materials"))
original_materials = [slot.get_editor_property("material_interface") for slot in slots]
role_actors = {role: [] for role in ROLES}

for role, x in ROLES.items():
    materials = {kind: load_material(role, kind) for kind in (
        "fabric", "hard", "accent", "trim", "screen", "visor", "hidden", "preview"
    )}
    suit = actors.spawn_actor_from_class(
        unreal.SkeletalMeshActor, unreal.Vector(x, 0.0, 0.0), unreal.Rotator(yaw=180.0)
    )
    suit.set_actor_label(f"I08_{role}_PRESSURE_GARMENT")
    role_actors[role].append(suit)
    suit.skeletal_mesh_component.set_skeletal_mesh_asset(mesh)
    for index, slot in enumerate(slots):
        name = str(slot.get_editor_property("material_slot_name")).lower()
        material = materials["hidden"]
        if "sm_suit" in name:
            material = materials["fabric"]
        elif "sm_boots" in name or "sm_gloves" in name:
            material = original_materials[index]
        suit.skeletal_mesh_component.set_material(index, material)

    for folder, name, material_kind, z in SHARED:
        role_actors[role].append(spawn_static(
            actors, folder, name, x, z, materials[material_kind],
            f"I08_{role}_{name}",
        ))
    role_actors[role].append(spawn_static(
        actors, I08, f"SM_V25_I08_{role}Modules", x, 0.0, materials["accent"],
        f"I08_{role}_ROLE_MODULES",
    ))

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
target = unreal.Vector(0.0, 0.0, 106.0)
add_rect_light(actors, "I08_Key", unreal.Vector(-225, -295, 275), target, 115.0, 275.0, 320.0, unreal.Color(255, 239, 221))
add_rect_light(actors, "I08_Fill", unreal.Vector(260, -190, 170), target, 64.0, 245.0, 285.0, unreal.Color(202, 224, 255))
add_rect_light(actors, "I08_Rim", unreal.Vector(20, 285, 240), target, 105.0, 230.0, 270.0, unreal.Color(220, 236, 255))
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(), unreal.Rotator())
sky.set_actor_label("I08_Sky")
sky.light_component.set_editor_property("intensity", 0.30)

levels.save_current_level()
capture(world, actors, "PrimaryOversuitV25_I08_ConceptSpecific_Lineup", unreal.Vector(0, -700, 114), target, 1800, 1200, 31.0)
for role, spawned in role_actors.items():
    if role != "Crew":
        for actor in spawned:
            actor.set_actor_hidden_in_game(True)
capture(world, actors, "PrimaryOversuitV25_I08_Crew_ThreeQuarter", unreal.Vector(96, -720, 114), unreal.Vector(96, 0, 105), 1200, 1600, 16.0)
for role, spawned in role_actors.items():
    if role != "Crew":
        for actor in spawned:
            actor.set_actor_hidden_in_game(False)
levels.save_current_level()
unreal.log("PRIMARY OVERSUIT V25 I08: concept-specific lineup rendered")
