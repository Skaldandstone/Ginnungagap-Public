"""Rebuild CRYO-01 from the compact cryopod-awakening concept art."""
from pathlib import Path
import math
import os
import time
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "Art" / "ShipRooms"
EXPORT = ROOT / "Build" / "Unreal" / "ShipRooms" / "Cryo"
BLEND = ART / "ShipRooms_CryoRoom.blend"
PREVIEW = ART / "ShipRooms_CryoRoom_Preview.png"
REFERENCE = ROOT / "docs/concept-art/reference/rooms/cryo-awakening-compact-damaged-concept.png"
HUMAN_SCALE = Vector((1.22, 1.22, 1.18))

def reset():
    bpy.ops.object.select_all(action="SELECT"); bpy.ops.object.delete(use_global=False)
    for blocks in (bpy.data.materials, bpy.data.curves, bpy.data.cameras, bpy.data.lights):
        for block in list(blocks): blocks.remove(block)

def collection(name):
    c = bpy.data.collections.new(name); bpy.context.scene.collection.children.link(c); return c

def move_to(obj, target):
    for owner in list(obj.users_collection): owner.objects.unlink(obj)
    target.objects.link(obj); return obj

def material(name, color, metallic=0.0, roughness=0.5, emission=None, transmission=0.0):
    mat = bpy.data.materials.new(name); mat.diffuse_color = (*color, 1); mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1); bsdf.inputs["Metallic"].default_value = metallic; bsdf.inputs["Roughness"].default_value = roughness
    if emission:
        bsdf.inputs["Emission Color"].default_value = (*emission, 1); bsdf.inputs["Emission Strength"].default_value = 7
    if transmission:
        bsdf.inputs["Transmission Weight"].default_value = transmission; bsdf.inputs["Alpha"].default_value = .42; mat.surface_render_method = "DITHERED"
    # Fine procedural breakup prevents large hard-surface pieces from reading as
    # pristine CG plastic while remaining subtle enough for a reusable game asset.
    if metallic > .45 or "Glass" in name or "Wet" in name:
        noise=mat.node_tree.nodes.new("ShaderNodeTexNoise"); noise.inputs["Scale"].default_value=34 if metallic > .45 else 18; noise.inputs["Detail"].default_value=5; noise.inputs["Roughness"].default_value=.68
        remap=mat.node_tree.nodes.new("ShaderNodeMapRange"); remap.inputs["To Min"].default_value=max(.025,roughness-.10); remap.inputs["To Max"].default_value=min(.92,roughness+.14)
        mat.node_tree.links.new(noise.outputs["Fac"],remap.inputs["Value"]); mat.node_tree.links.new(remap.outputs["Result"],bsdf.inputs["Roughness"])
        bump=mat.node_tree.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value=.10 if metallic > .45 else .045; bump.inputs["Distance"].default_value=.035
        mat.node_tree.links.new(noise.outputs["Fac"],bump.inputs["Height"]); mat.node_tree.links.new(bump.outputs["Normal"],bsdf.inputs["Normal"])
    return mat

def box(name, loc, dims, mat, target, bevel=.04, rotation=(0,0,0)):
    bpy.ops.mesh.primitive_cube_add(location=loc, rotation=rotation); obj=bpy.context.object; obj.name=name; obj.dimensions=dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        mod=obj.modifiers.new("EdgeSoftening","BEVEL"); mod.width=bevel; mod.segments=6 if bevel >= .20 else 2
    obj.data.materials.append(mat); return move_to(obj,target)

def capsule_prism(name,loc,width,length,height,mat,target,rotation=(0,0,0),segments=24):
    radius=width*.5; straight=max(0.0,length*.5-radius); outline=[]
    for i in range(segments+1):
        angle=math.pi*i/segments
        outline.append((radius*math.cos(angle),straight+radius*math.sin(angle)))
    for i in range(segments+1):
        angle=math.pi+math.pi*i/segments
        outline.append((radius*math.cos(angle),-straight+radius*math.sin(angle)))
    z0,z1=-height*.5,height*.5; verts=[(px,py,z0) for px,py in outline]+[(px,py,z1) for px,py in outline]; count=len(outline)
    faces=[tuple(reversed(range(count))),tuple(range(count,count*2))]
    faces.extend((i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count))
    mesh=bpy.data.meshes.new(name+"_Mesh"); mesh.from_pydata(verts,[],faces); mesh.update()
    obj=bpy.data.objects.new(name,mesh); obj.location=loc; obj.rotation_euler=rotation; target.objects.link(obj); obj.data.materials.append(mat)
    mod=obj.modifiers.new("EdgeSoftening","BEVEL"); mod.width=min(.055,height*.18); mod.segments=3
    return obj

def capsule_ring(name,loc,outer_width,outer_length,inner_width,inner_length,height,mat,target,rotation=(0,0,0),segments=24):
    def outline(width,length):
        radius=width*.5; straight=max(0.0,length*.5-radius); points=[]
        for i in range(segments+1):
            angle=math.pi*i/segments; points.append((radius*math.cos(angle),straight+radius*math.sin(angle)))
        for i in range(segments+1):
            angle=math.pi+math.pi*i/segments; points.append((radius*math.cos(angle),-straight+radius*math.sin(angle)))
        return points
    outer,inner=outline(outer_width,outer_length),outline(inner_width,inner_length); count=len(outer); z0,z1=-height*.5,height*.5
    verts=[(x,y,z0) for x,y in outer]+[(x,y,z1) for x,y in outer]+[(x,y,z0) for x,y in inner]+[(x,y,z1) for x,y in inner]
    faces=[]
    for i in range(count):
        j=(i+1)%count; ob,ot,ib,it=i,i+count,i+count*2,i+count*3; obj_,ojt,ijb,ijt=j,j+count,j+count*2,j+count*3
        faces.extend(((ob,obj_,ojt,ot),(ijb,ib,it,ijt),(ot,ojt,ijt,it),(obj_,ob,ib,ijb)))
    mesh=bpy.data.meshes.new(name+"_Mesh"); mesh.from_pydata(verts,[],faces); mesh.update()
    obj=bpy.data.objects.new(name,mesh); obj.location=loc; obj.rotation_euler=rotation; target.objects.link(obj); obj.data.materials.append(mat)
    mod=obj.modifiers.new("RimSoftening","BEVEL"); mod.width=.035; mod.segments=3
    return obj

def cylinder(name, loc, radius, depth, mat, target, rotation=(0,0,0), vertices=20):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=loc,rotation=rotation)
    obj=bpy.context.object; obj.name=name; obj.data.materials.append(mat); bpy.ops.object.shade_smooth_by_angle(); return move_to(obj,target)

def pipe(name,a,b,radius,mat,target):
    a,b=Vector(a),Vector(b); d=b-a; obj=cylinder(name,(a+b)*.5,radius,d.length,mat,target); obj.rotation_euler=d.to_track_quat("Z","Y").to_euler(); return obj

def sphere(name,loc,scale,mat,target):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=loc)
    obj=bpy.context.object; obj.name=name; obj.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(mat); bpy.ops.object.shade_smooth_by_angle(); return move_to(obj,target)

def torus(name,loc,scale,mat,target,rotation=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=1.0,minor_radius=.08,major_segments=48,minor_segments=10,location=loc,rotation=rotation)
    obj=bpy.context.object; obj.name=name; obj.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    obj.data.materials.append(mat); bpy.ops.object.shade_smooth_by_angle(); return move_to(obj,target)

def empty(name,loc,target):
    obj=bpy.data.objects.new(name,None); obj.location=loc; obj.empty_display_type="ARROWS"; obj.empty_display_size=.25; target.objects.link(obj); return obj

def linked_collection_instance(source,target,name,offset):
    """Duplicate a hierarchy while sharing every underlying mesh datablock."""
    mapping={}
    for source_obj in source.objects:
        duplicate=source_obj.copy()
        if source_obj.data is not None: duplicate.data=source_obj.data
        duplicate.name=f"{name}_{source_obj.name}"
        target.objects.link(duplicate); mapping[source_obj]=duplicate
    for source_obj,duplicate in mapping.items():
        if source_obj.parent in mapping:
            duplicate.parent=mapping[source_obj.parent]
        else:
            duplicate.location += Vector(offset)
    return list(mapping.values())

def pod(index,x,damaged,mats,target):
    p=f"SM_CryoPod_{index:02d}"; yaw=math.radians(-5 if index%2 else 4)
    # Lift the declined berth enough that its lowered foot does not penetrate the deck.
    hinge_pivot=Vector((x,-2.30,.98)); bed_tilt=math.radians(-9 if index%2 else -8)
    root=empty(p+"_ROOT",hinge_pivot,target); root.rotation_euler.x=bed_tilt
    parts=[]
    # A genuine full-body cavity: 2.44 m of usable couch inside a 3.23 m service shell
    # after the authored human-scale conversion below.
    parts.append(capsule_prism(p+"_Base",(x,-1.28,.45),1.58,2.65,.62,mats["hull"],target,rotation=(0,0,yaw)))
    parts.append(capsule_ring(p+"_LowerTub",(x,-1.18,.90),1.34,2.34,1.04,2.04,.28,mats["structure"],target,rotation=(0,0,yaw)))
    parts.append(capsule_prism(p+"_ThawBath",(x,-1.12,.805),1.03,2.06,.07,mats["cyan"],target,rotation=(0,0,yaw)))
    parts.append(capsule_prism(p+"_Couch",(x,-1.18,.845),.91,1.88,.10,mats["cushion"],target,rotation=(0,0,yaw)))
    # Rim fasteners, inset service lamps, and small condensation beads provide a
    # believable manufactured scale without changing the master silhouette.
    for side in (-.68,.68):
        for fastener_y in (-1.76,-1.25,-.74,-.28):
            parts.append(cylinder(p+f"_RimFastener_{side:+.2f}_{fastener_y:+.2f}",(x+side,fastener_y,.94),.035,.035,mats["structure"],target,rotation=(0,math.pi/2,0),vertices=16))
    for lamp_x in (-.34,.34):
        parts.append(box(p+f"_FootServiceLamp_{lamp_x:+.2f}",(x+lamp_x,.035,.52),(.24,.035,.075),mats["amber"],target,.025,rotation=(0,0,yaw)))
    for n,(dx,dy,size) in enumerate(((-.34,-1.72,.028),(.22,-1.48,.022),(-.18,-1.12,.018),(.31,-.78,.025),(-.29,-.43,.020),(.08,-.23,.017))):
        parts.append(sphere(p+f"_CondensationBead_{n}",(x+dx,dy,.985),(size,size*.72,size*.38),mats["wet"],target))
    # Anatomical landmarks make the 2.44 m berth readable at a glance and provide
    # believable support/restraint hardware for an unconscious occupant.
    parts.append(box(p+"_Headrest",(x,-1.88,.91),(.64,.42,.14),mats["cushion"],target,.10,rotation=(math.radians(-8),0,yaw)))
    for label, restraint_y in (("Shoulder",-1.55),("Waist",-.92),("Thigh",-.48)):
        parts.append(box(p+f"_{label}Restraint",(x,restraint_y,.925),(.98,.075,.045),mats["rubber"],target,.02,rotation=(0,0,yaw)))
        for side in (-.56,.56):
            parts.append(box(p+f"_{label}Buckle_{side:+.2f}",(x+side*.86,restraint_y,.945),(.09,.13,.065),mats["structure"],target,.015,rotation=(0,0,yaw)))
    # Open clamshell: its lower hinge is behind the tub and its frosted pane leans overhead.
    lid_z=1.78; lid_y=-2.03; lid_tilt=math.radians(-32 if not damaged else -41)
    parts.append(torus(p+"_CanopyFrame",(x,lid_y,lid_z),(.72,1.18,1.0),mats["structure"],target,rotation=(math.pi/2+lid_tilt,0,yaw)))
    parts.append(torus(p+"_CanopyInnerFrame",(x,lid_y+.018,lid_z),(.655,1.075,.82),mats["hull"],target,rotation=(math.pi/2+lid_tilt,0,yaw)))
    canopy=sphere(p+"_Canopy",(x,lid_y+.10,lid_z),(.62,.045,1.06),mats["glass"],target); canopy.rotation_euler=(lid_tilt,0,yaw); parts.append(canopy)
    for side in (-.64,.64):
        parts.append(box(p+f"_Rim_{side:+.2f}",(x+side,-1.35,.78),(.14,1.86,.42),mats["structure"],target,.07,rotation=(0,0,yaw)))
        # Compact trunnion hinge replaces the unsupported full-height strut.
        parts.append(cylinder(p+f"_LidHinge_{side:+.2f}",(x+side,-2.08,.82),.10,.20,mats["structure"],target,rotation=(0,math.pi/2,0),vertices=24))
        parts.append(cylinder(p+f"_LidHingePin_{side:+.2f}",(x+side,-2.08,.82),.045,.18,mats["structure"],target,rotation=(0,math.pi/2,0),vertices=20))
    parts.append(box(p+"_Status",(x,-.40,.52),(.50,.07,.12),mats["red" if damaged else "amber"],target,.025))
    parts.append(box(p+"_Terminal",(x+.53,-.45,.86),(.30,.12,.42),mats["screen"],target,.035))
    if damaged:
        canopy.hide_render=True
        for n,(sx,sy,sz,rz) in enumerate(((-.34,-1.91,1.62,-18),(.26,-1.85,1.25,21),(.38,-2.00,2.02,8))): parts.append(box(p+f"_GlassShard_{n}",(x+sx,sy,sz),(.38,.055,.65),mats["glass"],target,.015,rotation=(lid_tilt,0,math.radians(rz))))
        parts.append(pipe(p+"_BentFrame",(x-.62,-1.62,.94),(x+.48,-1.92,2.40),.07,mats["structure"],target))
        parts.append(pipe(p+"_LooseCable",(x+.62,-2.42,2.72),(x+.30,-.55,.40),.028,mats["rubber"],target))
        parts.append(box(p+"_ScorchPlate",(x,-2.48,1.72),(1.15,.045,.88),mats["scorch"],target,.02,rotation=(0,0,yaw)))
    for obj in parts:
        obj.location -= hinge_pivot
        obj.parent=root
    # Two compact machinery mounts carry the angled shell while preserving a clear
    # collision gap beneath and between neighboring pods.
    box(p+"_RearMount",(x,-1.84,.30),(1.08,.34,.58),mats["structure"],target,.08,rotation=(0,0,yaw))
    box(p+"_ForwardMount",(x,-.54,.25),(.92,.30,.48),mats["hull"],target,.07,rotation=(0,0,yaw))
    root["gameplay_socket"]="CryoPod"; root["pod_index"]=index; root["operational_state"]="Damaged" if damaged else "Nominal"; root["design_location"]=(x,-1.28,0); root["bed_decline_degrees"]=math.degrees(bed_tilt)

def build():
    reset(); ART.mkdir(parents=True,exist_ok=True); EXPORT.mkdir(parents=True,exist_ok=True)
    shell=collection("KIT_RoomShell"); machinery=collection("KIT_CryoMachinery"); runtime_pod=collection("KIT_CryoRuntimePod"); runtime_lid=collection("KIT_CryoRuntimeLid"); gameplay=collection("GAMEPLAY_Anchors"); presentation=collection("PRESENTATION")
    mats={
      "hull":material("M_Cryo_OiledBlackHull",(.012,.019,.023),.82,.25), "structure":material("M_Cryo_WornGunmetal",(.045,.058,.064),.88,.23),
      "deck":material("M_Cryo_WetDeck",(.022,.030,.034),.62,.18), "grate":material("M_Cryo_DeckGrate",(.009,.013,.016),.90,.32),
      "amber":material("M_Cryo_AmberPractical",(.42,.10,.015),emission=(1,.24,.035)), "red":material("M_Cryo_FaultRed",(.34,.008,.004),emission=(1,.015,.005)),
      "cyan":material("M_Cryo_ThawCyan",(.008,.12,.16),emission=(.012,.28,.38)), "screen":material("M_Cryo_DiagnosticScreen",(.006,.035,.045),emission=(.012,.22,.30)),
      "glass":material("M_Cryo_CrackedFrostGlass",(.11,.38,.48),.04,.11,transmission=.78), "rubber":material("M_Cryo_WetCable",(.004,.006,.007),.02,.55),
      "cushion":material("M_Cryo_RestraintCushion",(.055,.065,.062),.08,.72),
      "service":material("M_Cryo_AgedServicePanel",(.17,.19,.18),.54,.42), "wet":material("M_Cryo_Condensation",(.015,.055,.065),.18,.04,transmission=.18),
      "scorch":material("M_Cryo_ScorchedFailure",(.006,.004,.003),.10,.86)}
    box("SM_CryoRoom_Floor",(0,0,-.10),(9,5.4,.20),mats["deck"],shell,.02); box("SM_CryoRoom_Ceiling",(0,0,3.20),(9,5.4,.20),mats["hull"],shell,.02)
    for y in (-2.65,2.65): box(f"SM_CryoRoom_Wall_{y:+.2f}",(0,y,1.55),(9,.18,3.1),mats["hull"],shell,.025)
    for x in (-4.45,4.45):
        for y in (-1.82,1.82): box(f"SM_CryoRoom_Bulkhead_{x:+.2f}_{y:+.2f}",(x,y,1.55),(.18,1.54,3.1),mats["structure"],shell,.03)
    box("SM_CryoRoom_AftHatch",(-4.43,0,1.55),(.14,2.02,3.02),mats["hull"],shell,.06)
    box("SM_CryoRoom_AftHatchInset",(-4.34,0,1.52),(.06,1.48,2.48),mats["hull"],shell,.05)
    box("SM_CryoRoom_AftHatchStatus",(-4.29,0,2.55),(.025,.64,.10),mats["amber"],machinery,.01)
    box("SM_CryoRoom_ForwardHatch",(4.43,0,1.55),(.14,2.02,3.02),mats["hull"],shell,.06)
    box("SM_CryoRoom_ForwardHatchInset",(4.34,0,1.52),(.06,1.48,2.48),mats["hull"],shell,.05)
    box("SM_CryoRoom_ForwardHatchStatus",(4.29,0,2.55),(.025,.64,.10),mats["amber"],machinery,.01)
    for x in (-3.4,-1.7,0,1.7,3.4):
        box(f"SM_Cryo_DeckPanel_{x:+.1f}",(x,.45,.015),(1.55,3.05,.07),mats["deck"],shell,.025)
        for y in (-.75,.05,.85,1.65): box(f"SM_Cryo_DeckGrate_{x:+.1f}_{y:+.2f}",(x,y,.06),(1.25,.52,.045),mats["grate"],shell,.015)
    for x in (-3.6,-1.8,0,1.8,3.6):
        box(f"SM_CryoRoom_Rib_{x:+.1f}",(x,-2.52,1.60),(.16,.28,3.08),mats["structure"],shell,.04); box(f"SM_CryoRoom_CeilingRib_{x:+.1f}",(x,0,3.04),(.16,5,.18),mats["structure"],shell,.04)
    # Layered service panels, fastener rails and low ceiling trays replace the blockout walls.
    for n,x in enumerate((-3.45,-1.72,0,1.72,3.45)):
        box(f"SM_Cryo_ServicePanel_{n}",(x,2.54,1.62),(1.46,.08,1.78),mats["service"],shell,.045)
        for z in (.78,1.62,2.45):
            box(f"SM_Cryo_ServiceRail_{n}_{z:.2f}",(x,2.47,z),(1.18,.07,.055),mats["structure"],shell,.015)
    for x in (-3.25,-1.08,1.08,3.25):
        box(f"SM_Cryo_CeilingCassette_{x:+.2f}",(x,.15,2.91),(1.62,2.55,.12),mats["structure"],shell,.035)
    for n,y in enumerate((-2.25,-2.02,1.92,2.18)): pipe(f"SM_Cryo_OverheadPipe_{n}",(-4.25,y,2.92),(4.25,y,2.92),.055+n*.008,mats["rubber"],machinery)
    for n,x in enumerate((-3.2,-1.4,.4,2.2,3.55)): pipe(f"SM_Cryo_HangingCable_{n}",(x,2.45,3),(x+.18,2.15,1.85+.12*(n%2)),.025,mats["rubber"],machinery)
    # One centered master is exported for every interactive Unreal pod instance.
    pod(0,0,False,mats,runtime_pod)
    for obj in runtime_pod.objects:
        if obj.parent is None: obj.location.y += 1.28
    for index,x in enumerate((-3.15,-1.12,.92,2.95),1):
        linked_collection_instance(runtime_pod,machinery,f"INSTANCE_CryoPod_{index:02d}",(x,-1.28,0))
    for obj in runtime_pod.objects:
        obj.hide_render=True
    # Single concept-matched lid asset used by every interactive Unreal pod.
    runtime_frame=torus("SM_CryoPodRuntimeLid_Frame",(0,0,1.27),(.72,1.18,1.0),mats["structure"],runtime_lid,rotation=(math.pi/2,0,0))
    runtime_inner=torus("SM_CryoPodRuntimeLid_InnerFrame",(0,.018,1.27),(.655,1.075,.82),mats["hull"],runtime_lid,rotation=(math.pi/2,0,0))
    runtime_glass=sphere("SM_CryoPodRuntimeLid_Glass",(0,.05,1.27),(.62,.045,1.06),mats["glass"],runtime_lid)
    runtime_frame.hide_render=True; runtime_inner.hide_render=True; runtime_glass.hide_render=True
    # Thin irregular condensation pools catch the cyan pod light without blocking traversal.
    for n,(x,y,sx,sy) in enumerate(((-3.0,.05,.95,.38),(-1.25,.72,.60,.25),(.30,.20,.82,.34),(2.10,.78,.72,.28),(3.35,.10,.55,.22))):
        sphere(f"SM_Cryo_CondensationPool_{n}",(x,y,.088),(sx,sy,.012),mats["wet"],machinery)
    for x in (-2.8,-2.38): cylinder(f"SM_Cryo_CoolantBottle_{x:+.2f}",(x,2.36,.72),.14,1.30,mats["structure"],machinery)
    box("SM_Cryo_DiagnosticBank",(.05,2.52,1.28),(2.25,.24,1.78),mats["structure"],machinery,.06)
    for x in (-.62,.05,.72): box(f"SM_Cryo_DiagnosticScreen_{x:+.2f}",(x,2.38,1.52),(.48,.055,.42),mats["screen"],machinery,.02)
    for name,loc in (("SOCKET_Bulkhead_Forward",(4.5,0,0)),("SOCKET_Bulkhead_Aft",(-4.5,0,0)),("ANCHOR_System",(0,.5,0)),("ANCHOR_Loot",(3.65,2.25,0)),("ANCHOR_Maintenance",(0,2.3,0)),("ANCHOR_PlayerEntry",(-3.9,.85,0)),("ANCHOR_AITraversal",(0,1,0))): empty(name,loc,gameplay)
    for x in (-3.15,-1.12,.92,2.95):
        d=bpy.data.lights.new(f"LGT_CryoThaw_{x:+.2f}","AREA"); d.energy=360 if x<0 else 210; d.shape="RECTANGLE"; d.size=1.25; d.color=(.16,.58,1)
        o=bpy.data.objects.new(d.name,d); o.location=(x,-.95,1.48); o.rotation_euler=(math.radians(90),0,0); presentation.objects.link(o)
    for x in (-3.75,-.2,3.35):
        d=bpy.data.lights.new(f"LGT_CryoAmber_{x:+.2f}","AREA"); d.energy=95; d.shape="RECTANGLE"; d.size=.42; d.color=(1,.18,.025)
        o=bpy.data.objects.new(d.name,d); o.location=(x,1.8,2.72); o.rotation_euler=(math.radians(30),0,math.pi); presentation.objects.link(o)
    # Final human-scale correction: 2.18 m blockout pods become 2.66 m full-body berths,
    # with service clearance and ceiling height increased by the same authored ratio.
    for group in (shell, machinery, runtime_pod, runtime_lid, gameplay, presentation):
        for obj in group.objects:
            obj.location = Vector((obj.location.x * HUMAN_SCALE.x,
                                   obj.location.y * HUMAN_SCALE.y,
                                   obj.location.z * HUMAN_SCALE.z))
            if obj.type == "MESH":
                obj.scale = Vector((obj.scale.x * HUMAN_SCALE.x,
                                    obj.scale.y * HUMAN_SCALE.y,
                                    obj.scale.z * HUMAN_SCALE.z))
    cd=bpy.data.cameras.new("CAM_CryoRoom_Hero"); cam=bpy.data.objects.new("CAM_CryoRoom_Hero",cd); cam.location=(-4.35,2.92,1.78); cam.rotation_euler=((Vector((.18,-1.28,1.34))-cam.location).to_track_quat("-Z","Y").to_euler()); cd.lens=27; presentation.objects.link(cam)
    scene=bpy.context.scene; scene.camera=cam; scene["room_code"]="CRYO-01"; scene["concept_reference"]=str(REFERENCE); scene["concept_revision"]="full-body-cavity-operable-clamshell"; scene["module_dimensions_m"]="11.0 x 6.6 x 3.8"; scene["pod_envelope_m"]="1.93 x 3.23 x 2.38"; scene["usable_couch_length_m"]="2.44"; scene["unreal_scale"]="1 Blender meter = 100 Unreal centimeters"
    scene.render.engine="BLENDER_EEVEE"; scene.render.resolution_x=1600; scene.render.resolution_y=900; scene.render.resolution_percentage=100; scene.render.image_settings.file_format="PNG"; scene.render.filepath=str(PREVIEW); scene.world.color=(.001,.003,.005)
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND)); bpy.ops.render.render(write_still=True)
    for group,filename in ((shell,"SM_Room_CryoShell.fbx"),(machinery,"SM_Room_CryoMachinery.fbx"),(runtime_pod,"SM_CryoPod_Base.fbx"),(runtime_lid,"SM_CryoPod_RuntimeLid.fbx"),(gameplay,"SOCKETS_Room_Cryo.fbx")):
        bpy.ops.object.select_all(action="DESELECT")
        # Runtime CryoPodSystem actors provide the operable lids. Keep these pieces in
        # the Blender art preview, but do not bake a second, immovable lid into Unreal.
        runtime_lid_tokens = ("_CanopyFrame", "_Canopy", "_LidRam", "_GlassShard", "_BentFrame")
        for obj in group.objects:
            if group == machinery and ("SM_CryoPod_" in obj.name or any(token in obj.name for token in runtime_lid_tokens)):
                continue
            if group == runtime_pod and any(token in obj.name for token in runtime_lid_tokens):
                continue
            obj.select_set(True)
        destination = EXPORT / filename
        staging = EXPORT / (filename + ".staging.fbx")
        bpy.ops.export_scene.fbx(filepath=str(staging),use_selection=True,apply_unit_scale=True,axis_forward="-Y",axis_up="Z",add_leaf_bones=False,bake_anim=False)
        for attempt in range(12):
            try:
                os.replace(staging, destination)
                break
            except PermissionError:
                if attempt == 11:
                    raise
                time.sleep(.25)
    bpy.ops.object.select_all(action="DESELECT"); bpy.ops.wm.save_as_mainfile(filepath=str(BLEND)); print(f"CRYO-01 concept rebuild complete: {BLEND}")

if __name__ == "__main__": build()
