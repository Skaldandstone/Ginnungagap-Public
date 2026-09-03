"""Print the V32 cryo-bodysuit rig/mesh contract for Unreal export planning."""

import json

import bpy


rig = bpy.data.objects.get("RIG_PlayerCharacter_CryoBodysuit_v32")
body = bpy.data.objects.get("SK_PlayerCharacter_CryoBodysuit_v32")
if not rig or not body:
    raise RuntimeError("V32 rig or body is missing")

report = {
    "rig": rig.name,
    "rig_scale": list(rig.scale),
    "bones": [
        {"name": bone.name, "parent": bone.parent.name if bone.parent else None}
        for bone in rig.data.bones
    ],
    "body": body.name,
    "body_scale": list(body.scale),
    "vertices": len(body.data.vertices),
    "polygons": len(body.data.polygons),
    "vertex_groups": [group.name for group in body.vertex_groups],
    "modifiers": [
        {"name": modifier.name, "type": modifier.type,
         "object": modifier.object.name if hasattr(modifier, "object") and modifier.object else None}
        for modifier in body.modifiers
    ],
    "materials": [material.name if material else None for material in body.data.materials],
    "mesh_objects": [
        obj.name for obj in bpy.context.scene.objects
        if obj.type == "MESH" and not obj.hide_render
    ],
}
print("V32_UNREAL_CONTRACT", json.dumps(report, separators=(",", ":")))
