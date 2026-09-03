"""Export the renderable Pelagos environment as a combined Unreal-ready FBX."""

import json
import sys
from pathlib import Path

import bpy


ROOT = Path(sys.argv[sys.argv.index("--") + 1]).resolve()
OUT = ROOT / "Art" / "SpaceSystems" / "Exports"
FBX = OUT / "SM_PelagosOrbitalArrival_Set.fbx"
MANIFEST = OUT / "PelagosOrbitalArrival_ExportManifest.json"


def is_runtime_only(obj):
    if obj.hide_render:
        return True
    for collection in obj.users_collection:
        if collection.get("logic_only") or collection.name.startswith(("P21_DockState", "P21_Traffic", "P21_Mission", "P21_Service", "P21_UX")):
            return True
    return False


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    source_objects = [obj for obj in bpy.data.objects if obj.type == "MESH" and not is_runtime_only(obj)]
    if not source_objects:
        raise RuntimeError("No renderable Pelagos meshes were found")

    bpy.ops.object.select_all(action="DESELECT")
    duplicates = []
    for source in source_objects:
        duplicate = source.copy()
        duplicate.data = source.data.copy()
        duplicate.animation_data_clear()
        bpy.context.scene.collection.objects.link(duplicate)
        duplicate.matrix_world = source.matrix_world.copy()
        duplicate.hide_viewport = False
        duplicate.hide_render = False
        duplicate.select_set(True)
        duplicates.append(duplicate)

    bpy.context.view_layer.objects.active = duplicates[0]
    bpy.ops.object.join()
    export_mesh = bpy.context.view_layer.objects.active
    export_mesh.name = "SM_PelagosOrbitalArrival_Set"
    export_mesh.data.name = "SM_PelagosOrbitalArrival_Set"
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    export_mesh.data.calc_loop_triangles()

    bpy.ops.export_scene.fbx(
        filepath=str(FBX),
        use_selection=True,
        object_types={"MESH"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_UNITS",
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        add_leaf_bones=False,
        bake_anim=False,
        path_mode="AUTO",
    )

    material_names = sorted({slot.material.name for slot in export_mesh.material_slots if slot.material})
    manifest = {
        "asset": "Pelagos Orbital Arrival",
        "source_blend": "Art/SpaceSystems/SpaceSystems_PelagosOrbitalArrival_Level.blend",
        "fbx": str(FBX.relative_to(ROOT)).replace("\\", "/"),
        "source_mesh_objects": len(source_objects),
        "vertices": len(export_mesh.data.vertices),
        "triangles": len(export_mesh.data.loop_triangles),
        "materials": material_names,
        "material_count": len(material_names),
        "unreal_scale": "centimeters via FBX unit metadata",
        "pivot": [0.0, 0.0, 0.0],
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps(manifest, indent=2))


main()
