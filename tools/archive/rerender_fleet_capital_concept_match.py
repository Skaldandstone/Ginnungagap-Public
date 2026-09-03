"""Re-render full-ship review frames from the capital concept-match Blender master."""
from pathlib import Path
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/"Art/Ships/Exterior/ConceptMatch/FleetCapitalConceptMatch.blend"))

def render(collection_name,length,out):
    target=bpy.data.collections[collection_name]
    for c in bpy.data.collections: c.hide_render=c.name.startswith("SM_Ship_") and c != target
    world=bpy.context.scene.world; world.use_nodes=True; world.node_tree.nodes["Background"].inputs["Color"].default_value=(.009,.012,.017,1); world.node_tree.nodes["Background"].inputs["Strength"].default_value=.3
    bpy.ops.object.light_add(type="SUN",location=(0,0,length)); sun=bpy.context.object; sun.data.energy=4.5; sun.rotation_euler=(.72,-.5,-.8)
    bpy.ops.object.light_add(type="AREA",location=(length*.25,-length*.65,length*.55)); key=bpy.context.object; key.data.energy=18000; key.data.size=length*.8; key.data.color=(.82,.9,1)
    key.rotation_euler=(Vector((0,0,0))-key.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.light_add(type="AREA",location=(-length*.3,length*.4,-length*.05)); rim=bpy.context.object; rim.data.energy=12000; rim.data.size=length*.5; rim.data.color=(.12,.3,1)
    rim.rotation_euler=(Vector((0,0,0))-rim.location).to_track_quat('-Z','Y').to_euler()
    bpy.ops.object.camera_add(location=(length*.04,-length*2.45,length*.38)); cam=bpy.context.object; cam.data.lens=55; cam.data.clip_end=40000
    cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler(); bpy.context.scene.camera=cam
    s=bpy.context.scene; s.render.engine="BLENDER_EEVEE"; s.render.resolution_x=1600; s.render.resolution_y=900; s.render.resolution_percentage=100; s.render.image_settings.file_format="PNG"; s.view_settings.look="AgX - Medium High Contrast"; s.render.filepath=str(out)
    bpy.ops.render.render(write_still=True)
    for o in (sun,key,rim,cam): bpy.data.objects.remove(o,do_unlink=True)
    for c in bpy.data.collections: c.hide_render=False

render("SM_Ship_MilitaryCorvette_ConceptMatch",2400,ROOT/"Art/Ships/Exterior/ConceptMatch/MilitaryCorvette/Previews/MilitaryCorvette_ConceptMatch_Beauty.png")
render("SM_Ship_ExpeditionCarrier_ConceptMatch",6500,ROOT/"Art/Ships/Exterior/ConceptMatch/ExpeditionCarrier/Previews/ExpeditionCarrier_ConceptMatch_Beauty.png")
print("CAPITAL_RENDERS_COMPLETE")
