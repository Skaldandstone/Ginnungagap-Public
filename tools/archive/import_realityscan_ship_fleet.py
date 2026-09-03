"""Import all passed RealityScan ship reconstructions as isolated Unreal candidates."""

from __future__ import annotations

import json
from pathlib import Path

import unreal


PROJECT = Path(unreal.SystemLibrary.get_project_directory())
SAFE_MAP = "/Game/Assets/Maps/ModelLibrary/L_GameplayModelLibrary"
REPORT = PROJECT / "Saved/Reports/RealityScanShipFleetImport.json"

SHIPS = (
    {
        "key": "SmallUtilityEscort",
        "mesh_name": "SM_RS_SmallUtilityEscort",
        "design_authority": "docs/concept-art/reference/ships/small-utility-escort-exterior.png",
        "target_cm": (140000.0, 26000.0, 32000.0),
    },
    {
        "key": "MilitaryCorvette",
        "mesh_name": "SM_RS_MilitaryCorvette",
        "design_authority": "docs/concept-art/reference/ships/medium-military-corvette-exterior.png",
        "target_cm": (240000.0, 43000.0, 62000.0),
    },
    {
        "key": "ExpeditionCarrier",
        "mesh_name": "SM_RS_ExpeditionCarrier",
        "design_authority": "docs/concept-art/reference/ships/large-expedition-carrier-exterior.png",
        "target_cm": (650000.0, 140000.0, 180000.0),
    },
)


def paths_for(ship: dict[str, object]) -> dict[str, object]:
    key = str(ship["key"])
    source_root = PROJECT / "Art" / "Ships" / "Exterior" / "RealityScan" / key
    return {
        **ship,
        "source": source_root / "RealityScanOutput" / f"{key}_RS.obj",
        "gate": source_root / "RealityScanOutput" / "RealityScanGate.json",
        "dest": f"/Game/Assets/Ships/Exterior/RealityScan/{key}",
        "map": f"/Game/Assets/Maps/ShipExterior/RealityScan/L_{key}_RealityScan",
    }


def load_and_check_gate(config: dict[str, object]) -> dict[str, object]:
    source = Path(config["source"])
    gate_path = Path(config["gate"])
    if not source.exists():
        raise RuntimeError(f"RealityScan OBJ missing: {source}")
    if not gate_path.exists():
        raise RuntimeError(f"RealityScan gate missing: {gate_path}")
    gate = json.loads(gate_path.read_text(encoding="utf-8"))
    if gate.get("PromotionGate") != "pass":
        raise RuntimeError(f"RealityScan gate did not pass for {config['key']}: {gate}")
    return gate


def load_safe_map_if_needed() -> None:
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(SAFE_MAP):
        if not level.load_level(SAFE_MAP):
            raise RuntimeError(f"Could not load safe map {SAFE_MAP}")


def refresh_destination(dest: str) -> None:
    if unreal.EditorAssetLibrary.does_directory_exist(dest):
        if not unreal.EditorAssetLibrary.delete_directory(dest):
            raise RuntimeError(f"Could not refresh generated RealityScan directory {dest}")
    unreal.EditorAssetLibrary.make_directory(dest)


def import_scan(config: dict[str, object], gate: dict[str, object]):
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(config["source"]))
    task.set_editor_property("destination_path", str(config["dest"]))
    task.set_editor_property("destination_name", str(config["mesh_name"]))
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", False)

    options = unreal.FbxImportUI()
    options.set_editor_property("import_mesh", True)
    options.set_editor_property("import_materials", True)
    options.set_editor_property("import_textures", True)
    options.set_editor_property("import_as_skeletal", False)
    static_data = options.get_editor_property("static_mesh_import_data")
    static_data.set_editor_property("combine_meshes", True)
    static_data.set_editor_property("auto_generate_collision", False)
    static_data.set_editor_property("generate_lightmap_u_vs", True)
    task.set_editor_property("options", options)

    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    meshes = []
    for asset_path in unreal.EditorAssetLibrary.list_assets(
        str(config["dest"]), recursive=True, include_folder=False
    ):
        asset = unreal.EditorAssetLibrary.load_asset(asset_path)
        if isinstance(asset, unreal.StaticMesh):
            meshes.append(asset)
    if len(meshes) != 1:
        raise RuntimeError(
            f"Expected one Static Mesh for {config['key']}, found {len(meshes)}: {meshes}"
        )

    mesh = meshes[0]
    nanite = mesh.get_editor_property("nanite_settings")
    nanite.set_editor_property("enabled", True)
    mesh.set_editor_property("nanite_settings", nanite)
    body_setup = mesh.get_editor_property("body_setup")
    if body_setup:
        body_setup.set_editor_property(
            "collision_trace_flag", unreal.CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE
        )

    unreal.EditorAssetLibrary.set_metadata_tag(
        mesh, "Ginnungagap.Source", "RealityScan 2.2 locked-camera virtual capture"
    )
    unreal.EditorAssetLibrary.set_metadata_tag(
        mesh, "Ginnungagap.DesignAuthority", str(config["design_authority"])
    )
    unreal.EditorAssetLibrary.set_metadata_tag(
        mesh,
        "Ginnungagap.RealityScanGate",
        f"pass; {gate['LargestComponentRegisteredImages']}/{gate['InputImageCount']} registered; {gate['FaceCount']} faces",
    )
    unreal.EditorAssetLibrary.set_metadata_tag(
        mesh,
        "Ginnungagap.PromotionStatus",
        "Review candidate; does not replace production sculpt without visual approval",
    )
    unreal.EditorAssetLibrary.save_loaded_asset(mesh)
    return mesh, list(task.get_editor_property("imported_object_paths"))


def build_review_map(config: dict[str, object], mesh: unreal.StaticMesh):
    map_path = str(config["map"])
    level = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    if unreal.EditorAssetLibrary.does_asset_exist(map_path):
        if not level.load_level(map_path):
            raise RuntimeError(f"Could not load existing review map {map_path}")
        existing = actors.get_all_level_actors()
        if existing:
            actors.destroy_actors(existing)
    elif not level.new_level(map_path):
        raise RuntimeError(f"Could not create review map {map_path}")

    raw_bounds = mesh.get_bounds().box_extent * 2.0
    raw = (raw_bounds.x, raw_bounds.y, raw_bounds.z)
    target = tuple(float(value) for value in config["target_cm"])
    scale = unreal.Vector(
        target[0] / raw[0] if raw[0] > 0 else 1.0,
        target[1] / raw[1] if raw[1] > 0 else 1.0,
        target[2] / raw[2] if raw[2] > 0 else 1.0,
    )

    ship_actor = actors.spawn_actor_from_class(
        unreal.StaticMeshActor, unreal.Vector(0.0, 0.0, 0.0), unreal.Rotator()
    )
    ship_actor.set_actor_label(f"RS_{config['key']}_ExactDimensions")
    ship_actor.static_mesh_component.set_static_mesh(mesh)
    ship_actor.set_actor_scale3d(scale)

    length, beam, height = target
    key = actors.spawn_actor_from_class(
        unreal.DirectionalLight,
        unreal.Vector(0.0, 0.0, height * 2.0),
        unreal.Rotator(-38.0, -32.0, 0.0),
    )
    key.set_actor_label("RS_KeyLight")
    key.light_component.set_editor_property("intensity", 5.0)
    sky = actors.spawn_actor_from_class(
        unreal.SkyLight, unreal.Vector(0.0, 0.0, height * 1.5), unreal.Rotator()
    )
    sky.set_actor_label("RS_SkyLight")
    sky.light_component.set_editor_property("intensity", 1.0)

    camera_location = unreal.Vector(length * 0.12, -length * 0.72, length * 0.28)
    camera_rotation = unreal.MathLibrary.find_look_at_rotation(
        camera_location, unreal.Vector(0.0, 0.0, 0.0)
    )
    camera = actors.spawn_actor_from_class(unreal.CameraActor, camera_location, camera_rotation)
    camera.set_actor_label(f"RS_{config['key']}_ReviewCamera")
    camera.camera_component.set_editor_property("field_of_view", 48.0)

    label = actors.spawn_actor_from_class(
        unreal.TextRenderActor,
        unreal.Vector(-length * 0.45, -beam * 0.7, height * 0.7),
        unreal.Rotator(0.0, 180.0, 0.0),
    )
    label.set_actor_label(f"Label_RS_{config['key']}")
    label.text_render.set_text(
        f"REALITYSCAN REVIEW — {config['key']} — {length/100000.0:.1f} km"
    )
    label.text_render.set_editor_property("world_size", max(length * 0.012, 1200.0))
    label.text_render.set_editor_property(
        "text_render_color", unreal.Color(95, 205, 255, 255)
    )

    if not level.save_current_level():
        raise RuntimeError(f"Could not save review map {map_path}")
    return {
        "raw_bounds_cm": list(raw),
        "actor_scale": [scale.x, scale.y, scale.z],
        "placed_bounds_cm": list(target),
        "map": map_path,
        "actor": ship_actor.get_actor_label(),
    }


def main() -> None:
    configs = [paths_for(ship) for ship in SHIPS]
    gates = {str(config["key"]): load_and_check_gate(config) for config in configs}
    load_safe_map_if_needed()

    results = []
    for config in configs:
        refresh_destination(str(config["dest"]))
        gate = gates[str(config["key"])]
        mesh, imported_paths = import_scan(config, gate)
        review = build_review_map(config, mesh)
        unreal.EditorAssetLibrary.save_directory(
            str(config["dest"]), only_if_is_dirty=False, recursive=True
        )
        results.append(
            {
                "ship": config["key"],
                "source": str(config["source"]),
                "destination": config["dest"],
                "mesh": mesh.get_path_name(),
                "imported_paths": imported_paths,
                "gate": gate,
                "review": review,
            }
        )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(
        json.dumps({"status": "pass", "ship_count": len(results), "ships": results}, indent=2),
        encoding="utf-8",
    )
    unreal.log(f"Imported {len(results)} RealityScan ship candidates; report: {REPORT}")


if __name__ == "__main__":
    main()
