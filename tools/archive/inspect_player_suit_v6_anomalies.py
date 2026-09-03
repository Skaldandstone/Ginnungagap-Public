import bpy
from mathutils import Vector

for obj in bpy.data.objects:
    if obj.type != "MESH" or obj.hide_render:
        continue
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    mins = tuple(min(v[i] for v in corners) for i in range(3))
    maxs = tuple(max(v[i] for v in corners) for i in range(3))
    if maxs[2] < 0.2 or (maxs[2] - mins[2] < 0.08 and mins[2] < 0.2):
        print("LOW_VISIBLE", obj.name, "bounds", mins, maxs, "collections", [c.name for c in obj.users_collection])
        if obj.name.startswith("V6_HEAD_"):
            print(
                "TRANSFORM",
                obj.name,
                "location", tuple(obj.location),
                "world_translation", tuple(obj.matrix_world.translation),
                "parent", obj.parent.name if obj.parent else None,
                "parent_type", obj.parent_type,
                "parent_inverse_translation", tuple(obj.matrix_parent_inverse.translation),
            )

root = bpy.data.objects.get("SK_PlayerHead_Production_v6")
if root:
    print("HEAD_ROOT", "location", tuple(root.location), "world", tuple(root.matrix_world.translation), "parent", root.parent.name if root.parent else None, "parent_type", root.parent_type)
