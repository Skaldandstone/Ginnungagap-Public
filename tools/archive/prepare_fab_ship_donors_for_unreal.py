"""Remove non-geometry helpers and standardize Fab ship donors for Unreal."""
from pathlib import Path
import math
import re

import bpy


ROOT = Path(__file__).resolve().parents[1]
JOBS = (
    {
        "source": ROOT / "Art/Ships/Exterior/FabDonors/BC304/stargate_bc_304.glb",
        "output": ROOT / "Art/Ships/Exterior/FabDonors/BC304/SM_FabDonor_BC304_Clean.glb",
        "name": "SM_FabDonor_BC304_Clean",
        "rotate_z": 0.0,
        "reject_tokens": (),
    },
    {
        "source": ROOT / "Art/Ships/Exterior/FabDonors/Spaceship4/spaceship_4.glb",
        "output": ROOT / "Art/Ships/Exterior/FabDonors/Spaceship4/SM_FabDonor_Spaceship4_Clean.glb",
        "name": "SM_FabDonor_Spaceship4_Clean",
        "rotate_z": 90.0,
        "reject_tokens": ("emit",),
    },
)


def clear_scene():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def hierarchy_names(obj):
    result = []
    while obj is not None:
        result.append(obj.name.lower())
        obj = obj.parent
    return result


for job in JOBS:
    clear_scene()
    bpy.ops.import_scene.gltf(filepath=str(job["source"]))
    meshes = [obj for obj in bpy.context.scene.objects if obj.type == "MESH"]
    keep = []
    for obj in meshes:
        hierarchy = hierarchy_names(obj)
        if any(token in node_name for token in job["reject_tokens"] for node_name in hierarchy):
            bpy.data.objects.remove(obj, do_unlink=True)
        else:
            keep.append(obj)
    if not keep:
        raise RuntimeError(f"No retained donor meshes for {job['name']}")

    bpy.ops.object.select_all(action="DESELECT")
    for obj in keep:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = keep[0]
    bpy.ops.object.join()
    merged = bpy.context.active_object
    merged.name = job["name"]
    merged.rotation_euler.z = math.radians(job["rotate_z"])
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    # Center the standardized donor on the origin for predictable Unreal scaling.
    corners = [merged.matrix_world @ __import__("mathutils").Vector(corner) for corner in merged.bound_box]
    center = tuple((min(point[i] for point in corners) + max(point[i] for point in corners)) * 0.5 for i in range(3))
    merged.location.x -= center[0]
    merged.location.y -= center[1]
    merged.location.z -= center[2]
    bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

    job["output"].parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=str(job["output"]),
        export_format="GLB",
        use_selection=True,
        export_apply=True,
        export_yup=True,
    )
    print(f"Prepared {job['name']} -> {job['output']}")
