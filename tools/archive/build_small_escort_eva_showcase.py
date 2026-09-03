"""Build the Small Utility Escort EVA validation level and production support assets."""

from __future__ import annotations

import json
from pathlib import Path

import unreal


ROOT = "/Game/Assets/Ships/Exterior/ConceptMatch/SmallUtilityEscort"
MAT_ROOT = ROOT + "/ProductionMaterials"
MAP = "/Game/Assets/Maps/ShipExterior/L_SmallEscort_EVAValidation"
PROJECT = Path(unreal.SystemLibrary.get_project_directory())
REPORT = PROJECT / "Saved/Reports/SmallEscortEVAValidation.json"
EXPECTED = (140000.0, 26000.0, 32000.0)


def make_master():
    path = MAT_ROOT + "/M_SmallEscort_Surface_Master"
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        return unreal.EditorAssetLibrary.load_asset(path)
    mat = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
        "M_SmallEscort_Surface_Master", MAT_ROOT, unreal.Material, unreal.MaterialFactoryNew())
    color = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionVectorParameter, -420, -80)
    color.set_editor_property("parameter_name", "BaseColor")
    color.set_editor_property("default_value", unreal.LinearColor(0.17, 0.19, 0.2, 1))
    rough = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionScalarParameter, -420, 80)
    rough.set_editor_property("parameter_name", "Roughness")
    rough.set_editor_property("default_value", 0.58)
    metal = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionScalarParameter, -420, 170)
    metal.set_editor_property("parameter_name", "Metallic")
    metal.set_editor_property("default_value", 0.62)
    unreal.MaterialEditingLibrary.connect_material_property(color, "", unreal.MaterialProperty.MP_BASE_COLOR)
    unreal.MaterialEditingLibrary.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    unreal.MaterialEditingLibrary.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def make_instance(name, parent, color, roughness, metallic):
    path = MAT_ROOT + "/" + name
    if unreal.EditorAssetLibrary.does_asset_exist(path):
        inst = unreal.EditorAssetLibrary.load_asset(path)
    else:
        inst = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            name, MAT_ROOT, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    unreal.MaterialEditingLibrary.set_material_instance_parent(inst, parent)
    unreal.MaterialEditingLibrary.set_material_instance_vector_parameter_value(
        inst, "BaseColor", unreal.LinearColor(*color, 1))
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, "Roughness", roughness)
    unreal.MaterialEditingLibrary.set_material_instance_scalar_parameter_value(inst, "Metallic", metallic)
    unreal.EditorAssetLibrary.save_loaded_asset(inst)
    return inst


def meshes():
    visible, reference, collision = [], [], []
    for path in unreal.EditorAssetLibrary.list_assets(ROOT, recursive=True, include_folder=False):
        asset = unreal.EditorAssetLibrary.load_asset(path)
        if not isinstance(asset, unreal.StaticMesh):
            continue
        name = asset.get_name()
        if name.startswith("REF_"):
            reference.append(asset)
        elif name.startswith("UCX_"):
            collision.append(asset)
        else:
            visible.append(asset)
    return visible, reference, collision


def spawn_mesh(mesh, location=(0, 0, 0), scale=(1, 1, 1), label=None, material=None):
    actor = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    actor.set_actor_label(label or mesh.get_name())
    actor.set_actor_scale3d(unreal.Vector(*scale))
    actor.static_mesh_component.set_static_mesh(mesh)
    if material:
        actor.static_mesh_component.set_material(0, material)
    return actor


def actor_bounds(actors):
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for actor in actors:
        origin, extent = actor.get_actor_bounds(False)
        values_lo = (origin.x - extent.x, origin.y - extent.y, origin.z - extent.z)
        values_hi = (origin.x + extent.x, origin.y + extent.y, origin.z + extent.z)
        for i in range(3):
            lo[i] = min(lo[i], values_lo[i]); hi[i] = max(hi[i], values_hi[i])
    return lo, hi, [hi[i] - lo[i] for i in range(3)]


def add_scale_reference(cube, material, location, scale, label):
    return spawn_mesh(cube, location, scale, label, material)


def main():
    unreal.EditorAssetLibrary.make_directory(MAT_ROOT)
    master = make_master()
    pristine = make_instance("MI_SmallEscort_Pristine", master, (0.22, .24, .235), .62, .55)
    scorched = make_instance("MI_SmallEscort_Scorched", master, (.055, .045, .04), .82, .42)
    breached = make_instance("MI_SmallEscort_BreachedEdges", master, (.12, .07, .035), .72, .68)
    eva = make_instance("MI_EVA_ScaleReference", master, (.72, .25, .035), .48, .22)
    visible, references, collision = meshes()
    if not visible:
        raise RuntimeError("No imported Small Escort meshes found")

    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(MAP):
        unreal.EditorAssetLibrary.delete_asset(MAP)
    if not level.new_level(MAP):
        raise RuntimeError("Could not create EVA validation level")
    ship_actors = [spawn_mesh(mesh) for mesh in visible]
    lo, hi, size = actor_bounds(ship_actors)
    scale_verified = all(abs(size[i] - EXPECTED[i]) <= max(10.0, EXPECTED[i] * .001) for i in range(3))

    cube = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube.Cube")
    # UE cube is 100 cm. Human, cargo tug, service shuttle, and docking-volume refs.
    add_scale_reference(cube, eva, (-52000, -14500, -15000), (.55, .35, 1.8), "EVA_Tech_1p8m")
    add_scale_reference(cube, eva, (-48000, -14500, -14750), (8, 3, 2.5), "CargoTug_8m")
    add_scale_reference(cube, eva, (-39000, -15000, -14000), (22, 8, 7), "ServiceShuttle_22m")
    add_scale_reference(cube, breached, (42000, -17000, -11500), (80, .25, .25), "TraversalRoute_80m")

    sun = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
        unreal.DirectionalLight, unreal.Vector(0, 0, 90000), unreal.Rotator(-28, -35, 0))
    sun.set_actor_label("Key_Sun"); sun.light_component.set_editor_property("intensity", 4.0)
    sky = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(0, 0, 50000), unreal.Rotator())
    sky.set_actor_label("LowFill_Sky"); sky.light_component.set_editor_property("intensity", .35)
    for label, loc, rot, fov in (
        ("CAM_EVA_Hangar", (-47000, -22000, -9000), (0, 58, -6), 55),
        ("CAM_EVA_Drive", (61000, -24000, -3000), (0, 125, -3), 58),
        ("CAM_FullShip", (90000, -100000, 52000), (0, 135, -19), 48)):
        cam = unreal.get_editor_subsystem(unreal.EditorActorSubsystem).spawn_actor_from_class(
            unreal.CameraActor, unreal.Vector(*loc), unreal.Rotator(rot[2], rot[1], rot[0]))
        cam.set_actor_label(label); cam.camera_component.set_editor_property("field_of_view", fov)

    level.save_current_level()
    unreal.EditorAssetLibrary.save_directory(ROOT)
    unreal.EditorAssetLibrary.save_directory("/Game/Assets/Maps/ShipExterior")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps({
        "map": MAP, "visible_mesh_actors": len(ship_actors), "excluded_reference_meshes": len(references),
        "excluded_ucx_meshes": len(collision), "actor_bounds_cm": {"min": lo, "max": hi, "size": size},
        "expected_cm": EXPECTED, "scale_verified": scale_verified,
        "traversal_references": ["EVA_Tech_1p8m", "CargoTug_8m", "ServiceShuttle_22m", "TraversalRoute_80m"],
        "material_variants": [pristine.get_path_name(), scorched.get_path_name(), breached.get_path_name()],
        "streaming_policy": {"nanite": True, "hlod_zones": ["bow", "midship", "drive"],
                             "world_partition_recommended_cell_cm": 25600},
    }, indent=2), encoding="utf-8")
    if not scale_verified:
        raise RuntimeError(f"Actor-space scale mismatch: {size}, expected {EXPECTED}")
    unreal.log(f"EVA showcase complete; exact scale verified: {size}")


if __name__ == "__main__":
    main()
