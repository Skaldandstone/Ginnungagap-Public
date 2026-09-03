import json
import os

import unreal


PROJECT_DIR = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
OUTPUT_DIR = os.path.join(PROJECT_DIR, "Saved", "Renders", "CharacterCreator")
OUTPUT_NAME = "PlayerFace01_CryoBodysuit_V34_Assembled"
REPORT_PATH = os.path.join(PROJECT_DIR, "Saved", "PlayerCryoBodysuitV32LayerValidation.json")
CRYO_MATERIAL = "/Game/Characters/Player/Undersuit/MetaHuman/MI_MH_CryoBodysuit_Standard"
CRYO_V34_MESH = "/Game/Characters/Player/Undersuit/CryoBodysuitV34/SK_CryoBodysuit_V34_Face01"


def look_at(source, target):
    return unreal.MathLibrary.find_look_at_rotation(source, target)


def spawn_light(actor_class, location, rotation, intensity, color):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, location, rotation)
    component = actor.get_component_by_class(
        unreal.RectLightComponent if actor_class == unreal.RectLight else unreal.DirectionalLightComponent
    )
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("light_color", color)
    if isinstance(component, unreal.RectLightComponent):
        component.set_editor_property("source_width", 180.0)
        component.set_editor_property("source_height", 180.0)
        component.set_editor_property("attenuation_radius", 900.0)
    return actor


def set_hidden(component, hidden):
    component.set_hidden_in_game(hidden, False)


def configure_v34_metahuman_layers(child, cryo_mesh, cryo_material):
    if not child or not isinstance(cryo_mesh, unreal.SkeletalMesh):
        return
    components = child.get_components_by_class(unreal.SkeletalMeshComponent)
    body = next((component for component in components if component.get_name() == "Body"), None)
    garment = next((component for component in components if component.get_name() == "SkeletalMesh"), None)
    if not garment:
        garment = next((
            component for component in components
            if component.get_skeletal_mesh_asset()
            and "/Clothing/" in component.get_skeletal_mesh_asset().get_path_name()
        ), None)
    if body:
        body.set_visibility(True, False)
        set_hidden(body, True)
    if garment:
        garment.set_skeletal_mesh_asset(cryo_mesh)
        if body:
            garment.set_leader_pose_component(body)
        garment.set_visibility(True, False)
        set_hidden(garment, False)
        if cryo_material:
            for material_index in range(len(cryo_mesh.get_editor_property("materials"))):
                garment.set_material(material_index, cryo_material)


def collect_model_state(character):
    state = {
        "status": "pass",
        "character_class": character.get_class().get_path_name(),
        "oversuit_equipped": bool(character.get_editor_property("pressure_oversuit_equipped")),
        "skeletal_layers": [],
        "static_oversuit_layers": [],
    }
    for component in character.get_components_by_class(unreal.SkeletalMeshComponent):
        mesh = component.get_skeletal_mesh_asset()
        state["skeletal_layers"].append({
            "name": component.get_name(),
            "mesh": mesh.get_path_name() if mesh else None,
            "hidden_in_game": bool(component.get_editor_property("hidden_in_game")),
            "visible": bool(component.get_editor_property("visible")),
        })
    for component in character.get_components_by_class(unreal.StaticMeshComponent):
        name = component.get_name()
        if any(token in name for token in ("Helmet", "PressureCollar", "ChestPlate", "LifeSupport", "Shoulder", "KneePad", "BootShell", "Glove", "ThighPouch")):
            state["static_oversuit_layers"].append({
                "name": name,
                "visible": bool(component.get_editor_property("visible")),
            })

    child_component = character.get_component_by_class(unreal.ChildActorComponent)
    child = child_component.get_editor_property("child_actor") if child_component else None
    state["metahuman_child"] = child.get_class().get_path_name() if child else None
    if child:
        state["metahuman_layers"] = []
        for component in child.get_components_by_class(unreal.SkeletalMeshComponent):
            mesh = component.get_skeletal_mesh_asset()
            state["metahuman_layers"].append({
                "name": component.get_name(),
                "mesh": mesh.get_path_name() if mesh else None,
                "hidden_in_game": bool(component.get_editor_property("hidden_in_game")),
                "visible": bool(component.get_editor_property("visible")),
            })

    cryo_layers = [layer for layer in state["skeletal_layers"] if layer["name"] == "CryoBodysuitMesh"]
    metahuman_body = [layer for layer in state.get("metahuman_layers", []) if layer["name"] == "Body"]
    metahuman_v34 = [
        layer for layer in state.get("metahuman_layers", [])
        if layer["mesh"] and "/CryoBodysuitV34/" in layer["mesh"]
    ]
    if len(cryo_layers) != 1 or not cryo_layers[0]["hidden_in_game"]:
        state["status"] = "fail"
    if len(metahuman_body) != 1 or not metahuman_body[0]["hidden_in_game"]:
        state["status"] = "fail"
    if len(metahuman_v34) != 1 or metahuman_v34[0]["hidden_in_game"] or not metahuman_v34[0]["visible"]:
        state["status"] = "fail"
    if state["oversuit_equipped"] or any(layer["visible"] for layer in state["static_oversuit_layers"]):
        state["status"] = "fail"
    if not state["metahuman_child"]:
        state["status"] = "fail"
    return state


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    world = unreal.EditorLevelLibrary.get_editor_world()

    character_class = unreal.load_class(None, "/Script/Ginnungagap.CoopSurvivalCharacter")
    if not character_class:
        raise RuntimeError("Could not load CoopSurvivalCharacter class")

    character = unreal.EditorLevelLibrary.spawn_actor_from_class(
        character_class, unreal.Vector(0.0, 0.0, 96.0), unreal.Rotator(0.0, 0.0, 0.0)
    )
    character.set_actor_label("CryoBodysuitV32_LayerValidation")
    character.set_editor_property("pressure_oversuit_equipped", False)

    # The preserved V32 garment has malformed rest geometry. V34 replaces the assembled
    # MetaHuman clothing component and follows the hidden body driver on the exact body skeleton.
    for component in character.get_components_by_class(unreal.SkeletalMeshComponent):
        if component.get_name() == "CryoBodysuitMesh":
            component.set_visibility(False, False)
            set_hidden(component, True)

    child_component = character.get_component_by_class(unreal.ChildActorComponent)
    child = child_component.get_editor_property("child_actor") if child_component else None
    cryo_material = unreal.EditorAssetLibrary.load_asset(CRYO_MATERIAL)
    cryo_v34_mesh = unreal.EditorAssetLibrary.load_asset(CRYO_V34_MESH)
    configure_v34_metahuman_layers(child, cryo_v34_mesh, cryo_material)

    ground = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, -2.0), unreal.Rotator(0.0, 0.0, 0.0)
    )
    ground_component = ground.static_mesh_component
    ground_component.set_static_mesh(unreal.load_asset("/Engine/BasicShapes/Cube"))
    ground.set_actor_scale3d(unreal.Vector(8.0, 8.0, 0.02))

    spawn_light(
        unreal.RectLight,
        unreal.Vector(240.0, -180.0, 260.0),
        look_at(unreal.Vector(240.0, -180.0, 260.0), unreal.Vector(0.0, 0.0, 115.0)),
        650.0,
        unreal.Color(205, 225, 255, 255),
    )
    spawn_light(
        unreal.RectLight,
        unreal.Vector(80.0, 220.0, 175.0),
        look_at(unreal.Vector(80.0, 220.0, 175.0), unreal.Vector(0.0, 0.0, 120.0)),
        350.0,
        unreal.Color(255, 122, 72, 255),
    )
    spawn_light(
        unreal.RectLight,
        unreal.Vector(-140.0, -40.0, 250.0),
        look_at(unreal.Vector(-140.0, -40.0, 250.0), unreal.Vector(0.0, 0.0, 135.0)),
        450.0,
        unreal.Color(150, 195, 255, 255),
    )

    capture = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.SceneCapture2D,
        unreal.Vector(340.0, 0.0, 125.0),
        look_at(unreal.Vector(340.0, 0.0, 125.0), unreal.Vector(0.0, 0.0, 105.0)),
    )
    capture_component = capture.capture_component2d
    capture_component.set_editor_property("fov_angle", 31.0)
    capture_component.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    capture_component.set_editor_property(
        "primitive_render_mode", unreal.SceneCapturePrimitiveRenderMode.PRM_USE_SHOW_ONLY_LIST
    )
    capture_component.show_only_actor_components(character, True)
    if child:
        capture_component.show_only_actor_components(child, True)
    capture_component.show_only_actor_components(ground, True)

    render_target = unreal.RenderingLibrary.create_render_target2d(
        world,
        1080,
        1440,
        unreal.TextureRenderTargetFormat.RTF_RGBA8,
        unreal.LinearColor(0.008, 0.012, 0.018, 1.0),
    )
    capture_component.set_editor_property("texture_target", render_target)

    unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
    # Apply once more after child-actor construction and compilation settle.
    for component in character.get_components_by_class(unreal.SkeletalMeshComponent):
        if component.get_name() == "CryoBodysuitMesh":
            component.set_visibility(False, False)
            set_hidden(component, True)
    configure_v34_metahuman_layers(child, cryo_v34_mesh, cryo_material)
    capture_component.capture_scene()
    capture_component.capture_scene()
    unreal.RenderingLibrary.export_render_target(world, render_target, OUTPUT_DIR, OUTPUT_NAME)
    try:
        state = collect_model_state(character)
    except Exception as error:
        state = {"status": "report_error", "reason": str(error)}
    with open(REPORT_PATH, "w", encoding="utf-8") as report_file:
        json.dump(state, report_file, indent=2)
    unreal.log("Cryo bodysuit V32 layered render exported: " + os.path.join(OUTPUT_DIR, OUTPUT_NAME))


main()
