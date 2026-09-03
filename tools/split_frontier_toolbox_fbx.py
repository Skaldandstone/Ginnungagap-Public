"""Blender (headless): splits the Frontier Engineer's Toolbox FBX into one LOD0 mesh per hand tool.

The pack's single FBX carries every part of every tool as its own object with LOD suffixes, which
Unreal imports as 274 static meshes. For a tool held in the hand we want one mesh each, so this
joins each tool's LOD0 parts (with the parts that make it read as complete: battery, glass,
switch, trigger; the three drill bits sit apart from the chuck in the file as variants, so
none is joined) and exports them as separate FBX files.

    "C:/Program Files/Blender Foundation/Blender 5.2/blender.exe" -b --python tools/split_frontier_toolbox_fbx.py
"""
import bpy, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "Art", "Fab", "Frontier_EngineersToolbox")
FBX = os.path.join(SRC, "frontier_engineerstoolbox_fbx.fbx")
OUT = os.path.join(SRC, "split")
TOOLS = {
    "Powertool": ["Powertool_Main", "Powertool_Battery", "Powertool_FrontRotator", "Powertool_Glass", "Powertool_Switch", "Powertool_Trigger"],
    "PlasmaCutter": ["PlasmaCutter_Main", "PlasmaCutter_Trigger"],
    "Scanner": ["Scanner_Main", "Scanner_Glass", "Scanner_Knob", "Scanner_Scanner1", "Scanner_Scanner2", "Scanner_Switch"],
    "Pipewrench": ["Pipewrench_Body", "Pipewrench_Rotator", "Pipewrench_Switch", "Pipewrench_Top"],
}

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX)
all_objects = {o.name: o for o in bpy.data.objects}
print("SPLIT imported objects:", len(all_objects))

for tool, parts in TOOLS.items():
    picked = []
    for part in parts:
        cands = [o for n, o in all_objects.items() if o.type == "MESH" and (n == part + "_LOD0" or n == part or n.startswith(part + "_LOD0"))]
        if not cands:
            print(f"SPLIT {tool}: missing part {part}")
        picked += cands
    bpy.ops.object.select_all(action="DESELECT")
    for o in picked:
        o.select_set(True)
    bpy.context.view_layer.objects.active = picked[0]
    bpy.ops.object.duplicate()
    dup = [o for o in bpy.context.selected_objects]
    bpy.context.view_layer.objects.active = dup[0]
    bpy.ops.object.join()
    joined = bpy.context.view_layer.objects.active
    joined.name = f"SM_Frontier_{tool}"
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    # Origin at the centre of the bounds so the hand transform is about the tool's middle.
    bpy.ops.object.origin_set(type="ORIGIN_GEOMETRY", center="BOUNDS")
    joined.location = (0, 0, 0)
    bpy.ops.object.select_all(action="DESELECT")
    joined.select_set(True)
    path = os.path.join(OUT, f"SM_Frontier_{tool}.fbx")
    bpy.ops.export_scene.fbx(filepath=path, use_selection=True, apply_scale_options="FBX_SCALE_ALL", mesh_smooth_type="FACE", add_leaf_bones=False, bake_anim=False, path_mode="COPY", embed_textures=False)
    d = joined.dimensions
    print(f"SPLIT {tool}: {len(picked)} parts -> {path} dims {d.x:.1f} x {d.y:.1f} x {d.z:.1f}")
