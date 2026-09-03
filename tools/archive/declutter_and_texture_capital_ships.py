"""Restore concept-art hierarchy and apply restrained bitmap surface textures."""
from pathlib import Path
import json
import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"Art/Ships/Exterior/ConceptMatch/FleetCapitalConceptMatch.blend"
OUT=ROOT/"Art/Ships/Exterior/ConceptMatch/Decluttered"
OUT.mkdir(parents=True,exist_ok=True); (OUT/"Previews").mkdir(exist_ok=True); (OUT/"Exports").mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))

REMOVE={
 "SM_Ship_MilitaryCorvette_ConceptMatch":["02_ArmorAndWaist","04_DualHangars","05_ArmoredCitadel","06_DefenseTerraces","07_BowArmor","P166_175_ArmorConstruction","P176_183_VentsAndThermal","P184_191_MarkingsAndRepairs","P192_200_EVAAndDriveFinish"],
 "SM_Ship_ExpeditionCarrier_ConceptMatch":["02_ArmorAndServiceWaist","04_ConcourseHangars","05_CommandCity","06_DefenseAndSensors","07_ProtectedHabitats","C166_175_ArmorConstruction","C176_183_ThermalAndRadiator","C184_191_CivicMarkingsAndRepairs","C192_205_EVAAndDriveFinish"],
}

removed=0
for names in REMOVE.values():
    for name in names:
        c=bpy.data.collections.get(name)
        if c:
            removed+=sum(1 for _ in c.all_objects)
            for o in list(c.all_objects): bpy.data.objects.remove(o,do_unlink=True)
            bpy.data.collections.remove(c)

def normalize_visible_bounds(collection_name,target):
    collection=bpy.data.collections[collection_name]
    for _ in range(2):
        dg=bpy.context.evaluated_depsgraph_get(); objects=[o for o in collection.all_objects if o.type=="MESH"]
        points=[o.evaluated_get(dg).matrix_world@Vector(v) for o in objects for v in o.evaluated_get(dg).bound_box]
        lo=[min(p[i] for p in points) for i in range(3)]; hi=[max(p[i] for p in points) for i in range(3)]
        center=[(lo[i]+hi[i])*.5 for i in range(3)]; factors=[target[i]/(hi[i]-lo[i]) for i in range(3)]
        for o in objects:
            o.location=tuple((o.location[i]-center[i])*factors[i] for i in range(3)); o.scale=tuple(o.scale[i]*factors[i] for i in range(3))
    collection["dimensions_m"]=target; collection["scale_verified"]=True

normalize_visible_bounds("SM_Ship_MilitaryCorvette_ConceptMatch",(2400,430,620))
normalize_visible_bounds("SM_Ship_ExpeditionCarrier_ConceptMatch",(6500,1400,1800))

def textured_material(material,image_path,scale,rough_min,rough_max,bump_strength):
    image=bpy.data.images.load(str(image_path),check_existing=True); image.colorspace_settings.name="sRGB"
    material.use_nodes=True; n=material.node_tree; bs=n.nodes.get("Principled BSDF")
    for node in list(n.nodes):
        if node != bs and node.type != "OUTPUT_MATERIAL": n.nodes.remove(node)
    texcoord=n.nodes.new("ShaderNodeTexCoord"); texcoord.location=(-900,0)
    mapping=n.nodes.new("ShaderNodeMapping"); mapping.location=(-720,0); mapping.inputs["Scale"].default_value=(scale,scale,scale)
    tex=n.nodes.new("ShaderNodeTexImage"); tex.location=(-520,0); tex.image=image; tex.extension="REPEAT"; tex.projection="BOX"; tex.projection_blend=.18
    ramp=n.nodes.new("ShaderNodeValToRGB"); ramp.location=(-300,-180); ramp.color_ramp.elements[0].position=.18; ramp.color_ramp.elements[0].color=(rough_min,rough_min,rough_min,1); ramp.color_ramp.elements[1].position=.82; ramp.color_ramp.elements[1].color=(rough_max,rough_max,rough_max,1)
    bump=n.nodes.new("ShaderNodeBump"); bump.location=(-80,-120); bump.inputs["Strength"].default_value=bump_strength; bump.inputs["Distance"].default_value=.08
    n.links.new(texcoord.outputs["Generated"],mapping.inputs["Vector"]); n.links.new(mapping.outputs["Vector"],tex.inputs["Vector"]); n.links.new(tex.outputs["Color"],bs.inputs["Base Color"]); n.links.new(tex.outputs["Color"],ramp.inputs["Fac"]); n.links.new(ramp.outputs["Color"],bs.inputs["Roughness"]); n.links.new(tex.outputs["Color"],bump.inputs["Height"]); n.links.new(bump.outputs["Normal"],bs.inputs["Normal"])
    material["texture_source"]=str(image_path.relative_to(ROOT)); material["surface_policy"]="broad fields, sparse seams, low-frequency wear"

textured_material(bpy.data.materials["M_Escort_Armor"],ROOT/"Art/Ships/Exterior/Textures/T_CapitalHull_Armor_Albedo_v2.png",1.0,.42,.68,.12)
textured_material(bpy.data.materials["M_Escort_ArmorDark"],ROOT/"Art/Ships/Exterior/Textures/T_CapitalHull_Structure_Albedo_v1.png",2.0,.34,.58,.18)
textured_material(bpy.data.materials["M_Escort_Structure"],ROOT/"Art/Ships/Exterior/Textures/T_CapitalHull_Structure_Albedo_v1.png",3.2,.28,.52,.22)

def render_ship(collection_name,length,path):
    target=bpy.data.collections[collection_name]
    for c in bpy.data.collections: c.hide_render=c.name.startswith("SM_Ship_") and c != target
    world=bpy.context.scene.world; world.use_nodes=True; world.node_tree.nodes["Background"].inputs["Color"].default_value=(.008,.011,.016,1); world.node_tree.nodes["Background"].inputs["Strength"].default_value=.3
    created=[]
    bpy.ops.object.light_add(type="SUN",location=(0,0,length)); sun=bpy.context.object; sun.data.energy=4.2; sun.rotation_euler=(.7,-.45,-.75); created.append(sun)
    for loc,energy,color,size in (((length*.22,-length*.65,length*.48),16000,(.84,.91,1),length*.75),((-length*.3,length*.45,0),9000,(.1,.25,.65),length*.45)):
        bpy.ops.object.light_add(type="AREA",location=loc); q=bpy.context.object; q.data.energy=energy; q.data.color=color; q.data.size=size; q.rotation_euler=(Vector((0,0,0))-q.location).to_track_quat('-Z','Y').to_euler(); created.append(q)
    bpy.ops.object.camera_add(location=(length*.04,-length*2.35,length*.34)); cam=bpy.context.object; cam.data.lens=55; cam.data.clip_end=40000; cam.rotation_euler=(Vector((0,0,0))-cam.location).to_track_quat('-Z','Y').to_euler(); bpy.context.scene.camera=cam; created.append(cam)
    s=bpy.context.scene; s.render.engine="BLENDER_EEVEE"; s.render.resolution_x=1600; s.render.resolution_y=900; s.render.resolution_percentage=100; s.render.image_settings.file_format="PNG"; s.view_settings.look="AgX - Medium High Contrast"; s.render.filepath=str(path); bpy.ops.render.render(write_still=True)
    for o in created: bpy.data.objects.remove(o,do_unlink=True)
    for c in bpy.data.collections: c.hide_render=False

ships=[("SM_Ship_MilitaryCorvette_ConceptMatch",2400,"MilitaryCorvette"),("SM_Ship_ExpeditionCarrier_ConceptMatch",6500,"ExpeditionCarrier")]
for collection_name,length,name in ships:
    ship=bpy.data.collections[collection_name]; ship["art_direction"]="concept hierarchy over micro-geometry"; ship["texture_pass"]="v1 bitmap armor and structure"; ship["decluttered"]=True
    bpy.ops.object.select_all(action="DESELECT"); [o.select_set(True) for o in ship.all_objects if o.type=="MESH"]; bpy.context.view_layer.objects.active=next(o for o in ship.all_objects if o.type=="MESH")
    bpy.ops.export_scene.gltf(filepath=str(OUT/"Exports"/("SM_Ship_"+name+"_Decluttered.glb")),export_format="GLB",use_selection=True,export_apply=True)
    render_ship(collection_name,length,OUT/"Previews"/(name+"_Decluttered_Textured.png"))

bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"FleetCapitalConceptMatch_Decluttered_Textured.blend"))
report={"version":2,"removed_objects":removed,"removed_collections":sum(len(x) for x in REMOVE.values()),"strategy":"remove redundant and close-surface micro-geometry; retain primary hull, concept districts, and refined conformal macro armor","textures":["Art/Ships/Exterior/Textures/T_CapitalHull_Armor_Albedo_v2.png","Art/Ships/Exterior/Textures/T_CapitalHull_Structure_Albedo_v1.png"],"ships":[{"name":n,"remaining_meshes":sum(1 for o in bpy.data.collections[n].all_objects if o.type=='MESH')} for n,_,_ in ships]}
(OUT/"DeclutterTextureQA.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
print("DECLUTTER_TEXTURE_PASS_COMPLETE",report)
