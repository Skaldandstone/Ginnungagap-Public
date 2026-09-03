"""Validate V23 clean concept-shell oversuits."""

import json
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT=Path(sys.argv[sys.argv.index("--")+1]).resolve()
ASSET=ROOT/"Art"/"Characters"/"PlayerSuits"/"PrimaryOversuits"
EXPORT=ROOT/"Build"/"Unreal"/"PlayerSuits"/"PrimaryOversuits_v23"
REPORT=ASSET/"PrimaryOversuits_v23_Validation.json"
CLASSES=("Marine","Scientist","Technician","Medical")
FORBIDDEN=("undersuit","face","hair","pupil","eyelid","mouth","nose","cheek","wearer")

def validate(cls):
    blend=ASSET/f"PlayerOversuit_{cls}_v23.blend"; fbx=EXPORT/f"SKM_PlayerOversuit_{cls}_v23.fbx"
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    meshes=[o for o in bpy.data.objects if o.type=="MESH" and o.get("asset_layer")=="oversuit"]
    rigs=[o for o in bpy.data.objects if o.type=="ARMATURE"]
    interfaces=[o for o in bpy.data.objects if o.get("asset_layer")=="oversuit_interface"]
    forbidden=[o.name for o in bpy.data.objects if any(t in o.name.lower() for t in FORBIDDEN)]
    points=[o.matrix_world@Vector(corner) for o in meshes for corner in o.bound_box]
    dims={"height":max(p.z for p in points)-min(p.z for p in points),"width":max(p.y for p in points)-min(p.y for p in points),"depth":max(p.x for p in points)-min(p.x for p in points)}
    constructions={o.get("construction") for o in meshes}
    errors=[]
    if len(meshes)<40: errors.append(f"expected at least 40 authored garment parts, found {len(meshes)}")
    if len(rigs)!=1 or len(rigs[0].data.bones)!=22: errors.append("expected one 22-bone oversuit rig")
    if len(interfaces)!=8: errors.append(f"expected 8 donning interfaces, found {len(interfaces)}")
    if forbidden: errors.append(f"forbidden player/undersuit objects: {forbidden}")
    for required in ("continuous_textile_torso","tailored_textile_sleeve","tailored_textile_leg","sealed_clear_visor","rugged_magnetic_boot","pressure_glove"):
        if required not in constructions: errors.append(f"missing construction system: {required}")
    if not (155<=dims["height"]<=180 and 70<=dims["width"]<=100 and 35<=dims["depth"]<=65): errors.append(f"non-human suit bounds: {dims}")
    if not fbx.exists() or fbx.stat().st_size<200000: errors.append("FBX missing or unexpectedly small")
    return {"status":"passed" if not errors else "failed","errors":errors,"mesh_count":len(meshes),"bone_count":len(rigs[0].data.bones) if rigs else 0,"interface_count":len(interfaces),"forbidden_wearer_count":len(forbidden),"construction_system_count":len(constructions),"bounds_cm":{k:round(v,2) for k,v in dims.items()},"blend_bytes":blend.stat().st_size,"fbx_bytes":fbx.stat().st_size if fbx.exists() else 0}

results={cls:validate(cls) for cls in CLASSES}; status="passed" if all(v["status"]=="passed" for v in results.values()) else "failed"
REPORT.write_text(json.dumps({"schema":1,"asset":"PrimaryOversuits_v23","status":status,"classes":results},indent=2),encoding="utf-8")
if status!="passed": raise SystemExit(f"PRIMARY_OVERSUITS_V23_VALIDATION failed {REPORT}")
print(f"PRIMARY_OVERSUITS_V23_VALIDATION passed {REPORT}")
