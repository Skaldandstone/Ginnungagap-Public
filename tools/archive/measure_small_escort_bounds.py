import bpy
from mathutils import Vector

def bounds(objects):
    pts=[]
    deps=bpy.context.evaluated_depsgraph_get()
    for o in objects:
        if o.type != 'MESH': continue
        ev=o.evaluated_get(deps)
        pts += [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    lo=[min(p[i] for p in pts) for i in range(3)]; hi=[max(p[i] for p in pts) for i in range(3)]
    return lo,hi,[hi[i]-lo[i] for i in range(3)]

meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
primary=[o for o in meshes if o.name.startswith(('Hull_ContinuousPressureEnvelope','Hull_DorsalCrown','Hull_VentralKeel'))]
for label,objects in [('PRIMARY_HULL',primary),('TOTAL_MESH',meshes)]:
    lo,hi,size=bounds(objects); print(label,'MIN',*[round(v,3) for v in lo],'MAX',*[round(v,3) for v in hi],'SIZE_M',*[round(v,3) for v in size])
