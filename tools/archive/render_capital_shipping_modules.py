"""Render shipping-module assemblies for visual equivalence QA."""
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/"Art/Ships/Exterior/Shipping/CapitalShips_ShippingModules.blend"))

def render(name,length,path):
    target=bpy.data.collections[name]
    for c in bpy.data.collections: c.hide_render=c.name.startswith("SM_Ship_") and c != target
    w=bpy.context.scene.world; w.use_nodes=True; w.node_tree.nodes["Background"].inputs["Color"].default_value=(.009,.012,.017,1); w.node_tree.nodes["Background"].inputs["Strength"].default_value=.3
    lights=[]
    bpy.ops.object.light_add(type="SUN",location=(0,0,length)); lights.append(bpy.context.object); lights[-1].data.energy=4.5; lights[-1].rotation_euler=(.72,-.5,-.8)
    for loc,energy,color,size in (((length*.25,-length*.65,length*.55),18000,(.82,.9,1),length*.8),((-length*.3,length*.4,-length*.05),12000,(.12,.3,1),length*.5)):
        bpy.ops.object.light_add(type="AREA",location=loc); q=bpy.context.object; q.data.energy=energy; q.data.color=color; q.data.size=size; q.rotation_euler=(Vector((0,0,0))-q.location).to_track_quat('-Z','Y').to_euler(); lights.append(q)
    bpy.ops.object.camera_add(location=(length*.04,-length*2.45,length*.38)); cam=bpy.context.object; cam.data.lens=55; cam.data.clip_end=40000; cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler(); bpy.context.scene.camera=cam
    s=bpy.context.scene; s.render.engine="BLENDER_EEVEE"; s.render.resolution_x=1600; s.render.resolution_y=900; s.render.resolution_percentage=100; s.render.image_settings.file_format="PNG"; s.view_settings.look="AgX - Medium High Contrast"; s.render.filepath=str(path); bpy.ops.render.render(write_still=True)
    for o in lights+[cam]: bpy.data.objects.remove(o,do_unlink=True)
    for c in bpy.data.collections: c.hide_render=False

render("SM_Ship_MilitaryCorvette_Shipping",2400,ROOT/"Art/Ships/Exterior/Shipping/MilitaryCorvette_ShippingBeauty.png")
render("SM_Ship_ExpeditionCarrier_Shipping",6500,ROOT/"Art/Ships/Exterior/Shipping/ExpeditionCarrier_ShippingBeauty.png")
print("SHIPPING_RENDER_QA_COMPLETE")
