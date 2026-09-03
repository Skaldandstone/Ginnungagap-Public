"""Phase 88.1: replace the pod-chain wheel with a continuous armored habitat ring."""
import bpy,math,sys
from pathlib import Path
root=Path(sys.argv[sys.argv.index('--')+1]).resolve();out=root/'Art'/'SpaceSystems';scene=bpy.context.scene;c=bpy.data.collections.get('AAA_REBUILD_88')
def finish(o,n,m):
 o.name=n;o.data.materials.append(m)
 for p in o.data.polygons:p.use_smooth=True
 for q in list(o.users_collection):q.objects.unlink(o)
 c.objects.link(o);return o
def torus(n,major,minor,m):
 bpy.ops.mesh.primitive_torus_add(major_radius=major,minor_radius=minor,major_segments=144,minor_segments=28,location=(-6.2,0,3),rotation=(0,math.pi/2,0));return finish(bpy.context.object,n,m)
for o in bpy.data.objects:
 if o.name.startswith(('R88_WheelModule_','R88_WheelPanel_','R88_WheelWindow_','R88_WheelOuterRib','R88_WheelInnerRib')):o.hide_render=True
hull=bpy.data.materials['R88_WeatheredTitanium'];white=bpy.data.materials['R88_ThermalCeramic'];dark=bpy.data.materials['R88_Recess'];foil=bpy.data.materials['R88_ThermalFoil'];cyan=bpy.data.materials['R88_NavCyan']
torus('R88R_HabitatPressureRing',7.2,1.02,white);torus('R88R_OuterArmorRail',8.18,.14,hull);torus('R88R_InnerServiceRail',6.22,.13,dark);torus('R88R_WindowBand',7.2,1.035,dark)
# Armor ribs sit just above the shell and visually segment it without breaking continuity.
for i in range(24):
 a=i*math.tau/24;y=math.cos(a)*7.2;z=3+math.sin(a)*7.2
 bpy.ops.mesh.primitive_torus_add(major_radius=1.045,minor_radius=.055,major_segments=32,minor_segments=8,location=(-6.2,y,z),rotation=(a,0,0));finish(bpy.context.object,f'R88R_ArmorRib_{i:02d}',foil if i%6==0 else hull)
 # paired windows on the camera-facing outer surface
 for off in (-.24,.24):
  bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.055,location=(-7.24,y+math.cos(a)*off,z+math.sin(a)*off));w=finish(bpy.context.object,f'R88R_Window_{i:02d}_{off}',cyan);w.scale=(.35,1,.7)
scene['aaa_concept_rebuild']='88.1';scene.render.filepath=str(out/'Pelagos_OrbitalArrival_AAA_Rebuild_v1.png');bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'SpaceSystems_PelagosOrbitalArrival_Level.blend'));bpy.ops.render.render(write_still=True)
