"""Bake editable capital-ship assemblies into material-preserving Nanite modules."""
from pathlib import Path
import json
import os
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get("GINN_SHIP_SOURCE",str(ROOT/"Art/Ships/Exterior/ConceptMatch/FleetCapitalConceptMatch.blend")))
OUT=Path(os.environ.get("GINN_SHIP_OUT",str(ROOT/"Art/Ships/Exterior/Shipping")))
OUT.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))

CONFIG={
 "MilitaryCorvette":{"collection":"SM_Ship_MilitaryCorvette_ConceptMatch","length":2400,"dims":[2400,430,620]},
 "ExpeditionCarrier":{"collection":"SM_Ship_ExpeditionCarrier_ConceptMatch","length":6500,"dims":[6500,1400,1800]},
}

def bucket_for(name,x,length):
    n=name.lower()
    if any(k in n for k in ("drive","nozzle","propulsion","heat","radiator")): return "DriveThermal"
    if any(k in n for k in ("hangar","dock","approach","crane")): return "HangarDocking"
    if any(k in n for k in ("citadel","command","sensor","radar","defense","turret","mast")): return "CommandDefense"
    if any(k in n for k in ("habitat","observation","concourse")): return "HabitatCivic"
    if x < -length*.22: return "HullStern"
    if x > length*.22: return "HullBow"
    return "HullMidship"

def evaluated_duplicate(obj,deps,target):
    ev=obj.evaluated_get(deps)
    mesh=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=deps)
    mesh.transform(ev.matrix_world); mesh.validate(verbose=False,clean_customdata=False); mesh.update(calc_edges=True)
    dup=bpy.data.objects.new(obj.name+"_Baked",mesh); target.objects.link(dup)
    return dup

def join_bucket(objects,name,target):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects: o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]
    bpy.ops.object.join(); result=bpy.context.object; result.name=name; result.data.name=name+"_Mesh"
    # Collapse duplicated material slots produced by joining many one-material pieces.
    unique=[]
    for slot in result.material_slots:
        if slot.material and slot.material not in unique: unique.append(slot.material)
    old_polys=[p.material_index for p in result.data.polygons]
    old_mats=[s.material for s in result.material_slots]
    result.data.materials.clear()
    for m in unique: result.data.materials.append(m)
    remap={i:(unique.index(m) if m in unique else 0) for i,m in enumerate(old_mats)}
    for p,old in zip(result.data.polygons,old_polys): p.material_index=remap.get(old,0)
    result.data.validate(verbose=False,clean_customdata=False); result.data.update(calc_edges=True)
    # Shipping metadata consumed by the Unreal import/validation script.
    result["nanite_enabled"]=True; result["shipping_module"]=True; result["collision_policy"]="separate authored proxy"
    return result

def bounds(objects):
    ps=[o.matrix_world@Vector(v) for o in objects for v in o.bound_box]
    lo=[min(p[i] for p in ps) for i in range(3)]; hi=[max(p[i] for p in ps) for i in range(3)]
    return lo,hi,[hi[i]-lo[i] for i in range(3)]

report={"version":1,"source":str(SOURCE),"ships":[]}
for ship_name,cfg in CONFIG.items():
    source=bpy.data.collections[cfg["collection"]]
    shipping=bpy.data.collections.new("SM_Ship_"+ship_name+"_Shipping")
    bpy.context.scene.collection.children.link(shipping)
    deps=bpy.context.evaluated_depsgraph_get(); buckets={}
    source_meshes=[o for o in source.all_objects if o.type=="MESH" and not o.hide_render and not o.name.startswith(("UCX_","REF_"))]
    for obj in source_meshes:
        center=obj.evaluated_get(deps).matrix_world@Vector(obj.evaluated_get(deps).bound_box[0])
        key=bucket_for(obj.name,center.x,cfg["length"])
        buckets.setdefault(key,[]).append(evaluated_duplicate(obj,deps,shipping))
    modules=[]
    for key,objects in sorted(buckets.items()): modules.append(join_bucket(objects,f"SM_{ship_name}_{key}",shipping))
    lo,hi,size=bounds(modules); verified=all(abs(size[i]-cfg["dims"][i])<.01 for i in range(3))
    shipping["dimensions_m"]=cfg["dims"]; shipping["scale_verified"]=verified; shipping["nanite_modules"]=len(modules)
    bpy.ops.object.select_all(action="DESELECT"); [o.select_set(True) for o in modules]; bpy.context.view_layer.objects.active=modules[0]
    export=OUT/("SM_Ship_"+ship_name+"_Shipping.glb")
    bpy.ops.export_scene.gltf(filepath=str(export),export_format="GLB",use_selection=True,export_apply=True,export_attributes=True)
    report["ships"].append({"ship":ship_name,"source_meshes":len(source_meshes),"shipping_modules":len(modules),"module_names":[o.name for o in modules],"material_slots":sum(len(o.material_slots) for o in modules),"bounds_m":{"min":lo,"max":hi,"size":size},"scale_verified":verified,"export":str(export.relative_to(ROOT))})

bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"CapitalShips_ShippingModules.blend"))
(OUT/"CapitalShips_ShippingQA.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
if not all(s["scale_verified"] for s in report["ships"]): raise RuntimeError("Shipping-module scale validation failed")
print("CAPITAL_SHIPPING_MODULES_COMPLETE",[(s["ship"],s["source_meshes"],s["shipping_modules"]) for s in report["ships"]])
