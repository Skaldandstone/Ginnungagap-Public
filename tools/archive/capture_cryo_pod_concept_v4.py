"""Assemble and capture the imported concept-faithful V4 pod in a live Unreal viewport."""
import os
import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_CryoPod_ConceptV4_FinalReview"
BASE = "/Game/Assets/ShipRooms/Cryo/ConceptV4/SM_CryoPod_ConceptV4_Canted_Base"
LID = "/Game/Assets/ShipRooms/Cryo/ConceptV4/SM_CryoPod_ConceptV4_Canted_Lid"
CLOSED_REVIEW = os.environ.get("CRYO_CAPTURE_CLOSED", "0") == "1"
OUTPUT = os.path.abspath(os.path.join(unreal.Paths.project_dir(), "Art", "ShipRooms",
                                      "CryoPodConceptV4",
                                      "CryoPod_ConceptV4_CantedBerth_Unreal.png" if CLOSED_REVIEW
                                      else "CryoPod_ConceptV4_CantedBerth_Open_Unreal.png"))


def build_material(name, color, roughness, metallic, emissive=0.0, opacity=None):
    asset_name = f"M_UE_V4Final_{name}"
    asset_path = f"/Game/Assets/ShipRooms/Cryo/ConceptV4/{asset_name}"
    if unreal.EditorAssetLibrary.does_asset_exist(asset_path):
        return unreal.EditorAssetLibrary.load_asset(asset_path)
    material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        asset_name, "/Game/Assets/ShipRooms/Cryo/ConceptV4",
        unreal.Material, unreal.MaterialFactoryNew())
    base = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant3Vector, -320, -40)
    base.set_editor_property("constant", unreal.LinearColor(*color, 1.0))
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -320, 100)
    rough.set_editor_property("r", roughness)
    metal = unreal.MaterialEditingLibrary.create_material_expression(
        material, unreal.MaterialExpressionConstant, -320, 180)
    metal.set_editor_property("r", metallic)
    unreal.MaterialEditingLibrary.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    if emissive > 0.0:
        strength = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant, -300, 270)
        strength.set_editor_property("r", emissive)
        multiply = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionMultiply, -80, 250)
        unreal.MaterialEditingLibrary.connect_material_expressions(base, "", multiply, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(strength, "", multiply, "B")
        unreal.MaterialEditingLibrary.connect_material_property(
            multiply, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
    if opacity is not None:
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        material.set_editor_property("two_sided", True)
        fresnel = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionFresnel, -300, 360)
        edge_color = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant3Vector, -300, 440)
        edge_color.set_editor_property("constant", unreal.LinearColor(
            min(color[0] * 2.5 + 0.08, 1.0), min(color[1] * 2.0 + 0.12, 1.0),
            min(color[2] * 1.8 + 0.16, 1.0), 1.0))
        color_lerp = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionLinearInterpolate, -80, 400)
        unreal.MaterialEditingLibrary.connect_material_expressions(base, "", color_lerp, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(edge_color, "", color_lerp, "B")
        unreal.MaterialEditingLibrary.connect_material_expressions(fresnel, "", color_lerp, "Alpha")
        unreal.MaterialEditingLibrary.connect_material_property(
            color_lerp, "", unreal.MaterialProperty.MP_BASE_COLOR)

        alpha_center = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant, -300, 530)
        alpha_center.set_editor_property("r", opacity)
        alpha_edge = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant, -300, 590)
        alpha_edge.set_editor_property("r", min(opacity + 0.34, 0.9))
        opacity_lerp = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionLinearInterpolate, -80, 550)
        unreal.MaterialEditingLibrary.connect_material_expressions(alpha_center, "", opacity_lerp, "A")
        unreal.MaterialEditingLibrary.connect_material_expressions(alpha_edge, "", opacity_lerp, "B")
        unreal.MaterialEditingLibrary.connect_material_expressions(fresnel, "", opacity_lerp, "Alpha")
        unreal.MaterialEditingLibrary.connect_material_property(
            opacity_lerp, "", unreal.MaterialProperty.MP_OPACITY)

        refraction = unreal.MaterialEditingLibrary.create_material_expression(
            material, unreal.MaterialExpressionConstant, -80, 650)
        refraction.set_editor_property("r", 1.025)
        unreal.MaterialEditingLibrary.connect_material_property(
            refraction, "", unreal.MaterialProperty.MP_REFRACTION)
    unreal.MaterialEditingLibrary.recompile_material(material)
    unreal.EditorAssetLibrary.save_loaded_asset(material)
    return material


materials = {
    "M_Cryo_BlackenedSteel": build_material("Cryo_BlackenedSteel", (0.010, 0.014, 0.016), 0.31, 0.82),
    "M_Cryo_EdgeWear": build_material("Cryo_EdgeWear", (0.070, 0.052, 0.034), 0.26, 0.88),
    "M_Cryo_InsetPanel": build_material("Cryo_InsetPanel", (0.020, 0.023, 0.024), 0.46, 0.60),
    "M_Cryo_Cushion": build_material("Cryo_Cushion", (0.008, 0.009, 0.010), 0.82, 0.03),
    "M_Cryo_Amber": build_material("Cryo_Amber", (0.65, 0.055, 0.006), 0.28, 0.18, emissive=7.0),
    "M_Cryo_FrostedGlass": build_material("Cryo_FrostedGlass", (0.035, 0.14, 0.19), 0.16, 0.08,
                                           emissive=0.35, opacity=0.38),
}
studio_floor_material = build_material("Cryo_StudioFloor", (0.018, 0.021, 0.023), 0.74, 0.08)

if unreal.EditorAssetLibrary.does_asset_exist(MAP):
    unreal.EditorAssetLibrary.delete_asset(MAP)
unreal.EditorLevelLibrary.new_level(MAP)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
for stale_actor in list(actors.get_all_level_actors()):
    actors.destroy_actor(stale_actor)
base = unreal.EditorAssetLibrary.load_asset(BASE)
lid = unreal.EditorAssetLibrary.load_asset(LID)
if not base or not lid:
    raise RuntimeError("V4 cryo pod assets are missing")
for mesh in (base, lid):
    slots = mesh.get_editor_property("static_materials")
    for slot in slots:
        slot_name = str(slot.get_editor_property("material_slot_name"))
        replacement = next((value for key, value in materials.items() if key in slot_name), None)
        if replacement:
            slot.set_editor_property("material_interface", replacement)
    mesh.set_editor_property("static_materials", slots)
    # Review overrides stay in memory; never rewrite the production mesh
    # packages merely to capture a screenshot.

base_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
    base, unreal.Vector(0, 0, 0), unreal.Rotator())
lid_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
    lid, unreal.Vector(0, 122, 68),
    unreal.Rotator(roll=0 if CLOSED_REVIEW else -72, pitch=0, yaw=180))
if not base_actor or not lid_actor:
    raise RuntimeError("Could not spawn V4 pod assets in the live editor world")
base_actor.set_actor_label("CRYO01_ConceptV4_Base")
lid_actor.set_actor_label("CRYO01_ConceptV4_Lid")

# A neutral floor makes grounding, scale, and underside clearance readable in
# the review render without becoming part of the production pod asset.
floor_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
floor_actor = unreal.EditorLevelLibrary.spawn_actor_from_object(
    floor_mesh, unreal.Vector(0, 0, -7), unreal.Rotator())
if floor_actor:
    floor_actor.set_actor_label("CRYO01_V4_StudioFloor")
    floor_actor.set_actor_scale3d(unreal.Vector(6.0, 6.0, 0.08))
    floor_component = floor_actor.get_component_by_class(unreal.StaticMeshComponent)
    if floor_component:
        floor_component.set_material(0, studio_floor_material)

def rect(label, location, target, intensity, color, size):
    rotation = unreal.MathLibrary.find_look_at_rotation(location, target)
    light = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.RectLight, location, rotation)
    light.set_actor_label(label)
    component = light.get_component_by_class(unreal.RectLightComponent)
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("source_width", size)
    component.set_editor_property("source_height", size)
    component.set_editor_property("light_color", color)
    return light

target = unreal.Vector(0, -20, 58) if CLOSED_REVIEW else unreal.Vector(0, 0, 105)
rect("CRYO01_V4_Key", unreal.Vector(-260, -330, 340), target, 1180,
     unreal.Color(255, 205, 160, 255), 230)
rect("CRYO01_V4_Fill", unreal.Vector(330, -80, 250), target, 310,
     unreal.Color(180, 205, 235, 255), 260)
rect("CRYO01_V4_Rim", unreal.Vector(30, 340, 320), target, 940,
     unreal.Color(190, 220, 255, 255), 200)

volume = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.PostProcessVolume, unreal.Vector(0, 0, 0), unreal.Rotator())
volume.set_editor_property("unbound", True)
volume.set_editor_property("priority", 100.0)
volume.set_editor_property("blend_weight", 1.0)
volume_settings = volume.get_editor_property("settings")
volume_settings.set_editor_property("override_auto_exposure_bias", True)
volume_settings.set_editor_property("auto_exposure_bias", -0.45)
volume.set_editor_property("settings", volume_settings)

camera_location = (unreal.Vector(-255, -275, 150) if CLOSED_REVIEW
                   else unreal.Vector(-520, -90, 195))
camera_rotation = unreal.MathLibrary.find_look_at_rotation(camera_location, target)
camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.CameraActor, camera_location, camera_rotation)
camera.set_actor_label("CRYO01_V4_RenderCamera")
component = camera.get_component_by_class(unreal.CameraComponent)
component.set_editor_property("field_of_view", 44.0 if CLOSED_REVIEW else 58.0)
component.set_editor_property("post_process_blend_weight", 1.0)
settings = component.get_editor_property("post_process_settings")
settings.set_editor_property("override_auto_exposure_bias", True)
settings.set_editor_property("auto_exposure_bias", -0.72)
component.set_editor_property("post_process_settings", settings)

unreal.EditorLevelLibrary.save_current_level()
unreal.EditorLevelLibrary.set_level_viewport_camera_info(camera_location, camera_rotation)
unreal.EditorLevelLibrary.editor_invalidate_viewports()
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
for command in ("ShowFlag.Grid 0", "ShowFlag.Sprites 0", "ShowFlag.LightInfluences 0",
                "ShowFlag.SelectionOutline 0", "ShowFlag.CompositeEditorPrimitives 0"):
    unreal.SystemLibrary.execute_console_command(world, command)
try:
    unreal.EditorLevelLibrary.editor_set_game_view(True)
except Exception:
    unreal.SystemLibrary.execute_console_command(world, "GameView")
unreal.SystemLibrary.execute_console_command(
    world, f'HighResShot 1600x1000 filename="{OUTPUT.replace(chr(92), "/")}"')
unreal.log(f"CRYO-V4 SCREENSHOT REQUESTED: {OUTPUT}")
