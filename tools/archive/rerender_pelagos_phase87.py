"""Re-render the phase-87 master after final exposure calibration."""
import bpy,sys
from pathlib import Path
root=Path(sys.argv[sys.argv.index('--')+1]).resolve();scene=bpy.context.scene
scene.view_settings.exposure=1.15;scene.render.resolution_x=1920;scene.render.resolution_y=1080;scene.render.resolution_percentage=100
scene.render.filepath=str(root/'Art'/'SpaceSystems'/'SpaceSystems_Pelagos_Phase87_Final.png')
scene['phase87_exposure_qa']=True
bpy.ops.wm.save_as_mainfile(filepath=str(root/'Art'/'SpaceSystems'/'SpaceSystems_PelagosOrbitalArrival_Level.blend'))
bpy.ops.render.render(write_still=True)
