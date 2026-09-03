import bpy
from mathutils import Vector

obj = bpy.data.objects.get("SRC_PlayerHead_MakeHuman")
if obj is None:
    raise RuntimeError("SRC_PlayerHead_MakeHuman not found")

for group in obj.vertex_groups:
    if not any(token in group.name.lower() for token in ("eye", "head", "face", "neck", "body")):
        continue
    indices = []
    for vert in obj.data.vertices:
        for membership in vert.groups:
            if membership.group == group.index and membership.weight > 0.001:
                indices.append(vert.index)
                break
    if not indices:
        continue
    coords = [obj.matrix_world @ obj.data.vertices[i].co for i in indices]
    mins = Vector((min(v.x for v in coords), min(v.y for v in coords), min(v.z for v in coords)))
    maxs = Vector((max(v.x for v in coords), max(v.y for v in coords), max(v.z for v in coords)))
    center = sum(coords, Vector()) / len(coords)
    print("GROUP", group.name, "count", len(indices), "min", tuple(mins), "max", tuple(maxs), "center", tuple(center))

