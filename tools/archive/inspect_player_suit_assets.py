import bpy
from mathutils import Vector

print("BLEND", bpy.data.filepath)
for obj in bpy.data.objects:
    if obj.type != "MESH":
        continue
    mesh = obj.data
    corners = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
    mins = tuple(round(min(v[i] for v in corners), 5) for i in range(3))
    maxs = tuple(round(max(v[i] for v in corners), 5) for i in range(3))
    print(
        "MESH",
        obj.name,
        "visible=", not obj.hide_render,
        "verts=", len(mesh.vertices),
        "polys=", len(mesh.polygons),
        "uvs=", [uv.name for uv in mesh.uv_layers],
        "materials=", [slot.material.name if slot.material else None for slot in obj.material_slots],
        "bounds=", mins, maxs,
    )

for image in bpy.data.images:
    print("IMAGE", image.name, "size=", tuple(image.size), "path=", image.filepath)
