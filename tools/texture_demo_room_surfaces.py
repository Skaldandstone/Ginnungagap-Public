"""Textures the demo ship's greybox rooms: world-aligned PBR materials on every room-surface cube.

L_QuickDemo_FourDeck's rooms are 1,700-odd engine cubes drawing four flat generated materials
(structure gunmetal, hull off-white, large bulkhead panels, hazard stripes); only the corridors
use the textured Fab kit. Cubes have one 0..1 UV per face, so any ordinary tiled material would
stretch one texture across a whole wall. This builds one master material that projects textures
in world space (the engine's WorldAlignedTexture / WorldAlignedNormal functions, tiling every
TILE_CM) with a tint, and three instances on ModSci_Engineer's texture sets, then retargets the
cubes' materials in the map:

    M_Ship_Structure_Gunmetal      -> MI_Room_Structure   (scratched dark metal)
    M_Ship_Hull_OffWhite           -> MI_Room_Hull        (wall cover panels, light)
    M_QuickDemo_BulkheadLargePanel -> MI_Room_Panel       (brushed metal pattern)

The hazard-stripe material is procedural and stays. Re-runnable: it rebuilds the materials and
skips cubes already retargeted.

    UnrealEditor-Cmd.exe <project> -ExecutePythonScript=tools/texture_demo_room_surfaces.py -NullRHI
"""
import unreal

MAP = "/Game/Assets/Maps/ShipProduction/L_QuickDemo_FourDeck"
DEST = "/Game/Assets/Ships/Production/Materials/Rooms"
TILE_CM = 200.0
ENGI = "/Game/ModSci_Engineer/Textures"
SETS = {
    # instance name: (base colour, normal, roughness, tint, tiling cm)
    "MI_Room_Structure": (f"{ENGI}/Base/ScratchedMetal/T_ScratchedMetal_Diff", f"{ENGI}/Base/ScratchedMetal/T_ScratchedMetal_Normal",
                          f"{ENGI}/Base/ScratchedMetal/T_ScratchedMetal_Rough", (0.42, 0.45, 0.47), 200.0),
    "MI_Room_Hull": (f"{ENGI}/WallCover/T_WallCover_Diff", f"{ENGI}/WallCover/T_WallCover_normals",
                     f"{ENGI}/WallCover/T_WallCover_Rough", (0.95, 0.95, 0.92), 300.0),
    "MI_Room_Panel": (f"{ENGI}/Base/BrushedMetal/T_Metal_Pattern_Diff", f"{ENGI}/Base/BrushedMetal/T_BrushedMetal_Normal",
                      f"{ENGI}/Base/BrushedMetal/T_BrushedMetal_Rough", (0.62, 0.64, 0.66), 250.0),
}
RETARGET = {
    "/Game/Assets/Ships/Production/Materials/M_Ship_Structure_Gunmetal": "MI_Room_Structure",
    "/Game/Assets/Ships/Production/Materials/M_Ship_Hull_OffWhite": "MI_Room_Hull",
    "/Game/Assets/Ships/Production/Materials/M_QuickDemo_BulkheadLargePanel": "MI_Room_Panel",
}
CUBE = "/Engine/BasicShapes/Cube"

mel = unreal.MaterialEditingLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()
eal = unreal.EditorAssetLibrary


def connect_any(src, src_out, dst, candidates):
    """Connects to the first of the candidate pin names the call accepts."""
    for name in candidates:
        if mel.connect_material_expressions(src, src_out, dst, name):
            return name
    raise SystemExit(f"none of {candidates} accepted on {dst.get_name()}")


def build_master():
    path = f"{DEST}/M_Room_WorldAligned"
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    mat = tools.create_asset("M_Room_WorldAligned", DEST, unreal.Material, unreal.MaterialFactoryNew())
    wat = unreal.load_asset("/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedTexture")
    wan = unreal.load_asset("/Engine/Functions/Engine_MaterialFunctions01/Texturing/WorldAlignedNormal")
    assert wat and wan, "engine world-aligned functions missing"

    tiling = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -1100, -200)
    tiling.set_editor_property("parameter_name", "TileCm"); tiling.set_editor_property("default_value", TILE_CM)
    tint = mel.create_material_expression(mat, unreal.MaterialExpressionVectorParameter, -600, -500)
    tint.set_editor_property("parameter_name", "Tint"); tint.set_editor_property("default_value", unreal.LinearColor(1, 1, 1, 1))

    def texture_param(name, y, is_normal=False):
        node = mel.create_material_expression(mat, unreal.MaterialExpressionTextureObjectParameter, -1100, y)
        node.set_editor_property("parameter_name", name)
        if is_normal:
            node.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
        return node

    def aligned(function, texture_node, y, out_names):
        call = mel.create_material_expression(mat, unreal.MaterialExpressionMaterialFunctionCall, -800, y)
        call.set_editor_property("material_function", function)
        for method in ("update_from_function_resource",):
            if hasattr(call, method):
                getattr(call, method)()
        connect_any(texture_node, "", call, ["TextureObject", "Texture Object", "Texture"])
        connect_any(tiling, "", call, ["TextureSize", "Texture Size", "Size"])
        return call, out_names

    base_tex = texture_param("BaseColorTex", 0)
    base_call, base_outs = aligned(wat, base_tex, 0, ["XYZ Texture", "XYZ", "Result"])
    mul = mel.create_material_expression(mat, unreal.MaterialExpressionMultiply, -400, -100)
    for out in base_outs:
        if mel.connect_material_expressions(base_call, out, mul, "A"): break
    else: raise SystemExit("no XYZ output on WorldAlignedTexture")
    mel.connect_material_expressions(tint, "", mul, "B")
    mel.connect_material_property(mul, "", unreal.MaterialProperty.MP_BASE_COLOR)

    normal_tex = texture_param("NormalTex", 300, is_normal=True)
    normal_call, normal_outs = aligned(wan, normal_tex, 300, ["XYZ Normal", "XYZ Texture", "XYZ", "Result"])
    for out in normal_outs:
        if mel.connect_material_property(normal_call, out, unreal.MaterialProperty.MP_NORMAL): break
    else: raise SystemExit("no XYZ output on WorldAlignedNormal")

    rough_tex = texture_param("RoughnessTex", 600)
    rough_call, rough_outs = aligned(wat, rough_tex, 600, ["XYZ Texture", "XYZ", "Result"])
    mask = mel.create_material_expression(mat, unreal.MaterialExpressionComponentMask, -400, 600)
    mask.set_editor_property("r", True); mask.set_editor_property("g", False); mask.set_editor_property("b", False); mask.set_editor_property("a", False)
    for out in rough_outs:
        if mel.connect_material_expressions(rough_call, out, mask, ""): break
    else: raise SystemExit("no XYZ output for roughness")
    mel.connect_material_property(mask, "", unreal.MaterialProperty.MP_ROUGHNESS)

    metal = mel.create_material_expression(mat, unreal.MaterialExpressionScalarParameter, -400, 800)
    metal.set_editor_property("parameter_name", "Metallic"); metal.set_editor_property("default_value", 0.6)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)

    mel.recompile_material(mat)
    eal.save_loaded_asset(mat)
    return mat


def build_instances(master):
    out = {}
    for name, (base, normal, rough, tint, tile) in SETS.items():
        path = f"{DEST}/{name}"
        if eal.does_asset_exist(path):
            eal.delete_asset(path)
        factory = unreal.MaterialInstanceConstantFactoryNew()
        inst = tools.create_asset(name, DEST, unreal.MaterialInstanceConstant, factory)
        inst.set_editor_property("parent", master)
        for pname, tpath in (("BaseColorTex", base), ("NormalTex", normal), ("RoughnessTex", rough)):
            tex = unreal.load_asset(tpath)
            assert tex, f"missing texture {tpath}"
            mel.set_material_instance_texture_parameter_value(inst, pname, tex)
        mel.set_material_instance_vector_parameter_value(inst, "Tint", unreal.LinearColor(*tint, 1.0))
        mel.set_material_instance_scalar_parameter_value(inst, "TileCm", tile)
        mel.update_material_instance(inst)
        eal.save_loaded_asset(inst)
        out[name] = inst
        print(f"ROOMTEX built {path}")
    return out


def retarget(instances):
    les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assert les.load_level(MAP)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).get_all_level_actors()
    changed = 0
    for actor in actors:
        for comp in actor.get_components_by_class(unreal.StaticMeshComponent):
            mesh = comp.static_mesh
            if not mesh or mesh.get_path_name().split(".")[0] != CUBE:
                continue
            for slot in range(comp.get_num_materials()):
                mat = comp.get_material(slot)
                if not mat:
                    continue
                target = RETARGET.get(mat.get_path_name().split(".")[0])
                if target:
                    comp.set_material(slot, instances[target])
                    changed += 1
    saved = les.save_current_level()
    print(f"ROOMTEX retargeted {changed} cube material slots; saved={saved}")


master = build_master()
instances = build_instances(master)
retarget(instances)
