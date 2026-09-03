"""Presentation rerender for the phase-88 concept rebuild."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
root=Path(sys.argv[sys.argv.index('--')+1]).resolve();out=root/'Art'/'SpaceSystems';s=bpy.context.scene;cam=bpy.data.objects['Camera_R88_AAA_Rebuild']
cam.location=(-32,-41,18);cam.data.lens=58;cam.data.shift_x=-.03;cam.rotation_euler=(Vector((.8,1.5,3.4))-cam.location).to_track_quat('-Z','Y').to_euler();s.camera=cam
s.view_settings.exposure=1.35;s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.render.filepath=str(out/'Pelagos_OrbitalArrival_AAA_Rebuild_v1.png');s['aaa_rebuild_presentation_qa']=True
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(out/'SpaceSystems_PelagosOrbitalArrival_Level.blend'));bpy.ops.render.render(write_still=True)
