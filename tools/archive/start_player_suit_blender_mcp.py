"""Enable the locally installed Blender modeling bridge for this UI session."""

import bpy

bpy.ops.preferences.addon_enable(module="blender_mcp")
