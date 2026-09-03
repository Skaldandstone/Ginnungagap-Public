"""Print relevant Unreal DynamicMesh Python methods for tooling diagnostics."""
import unreal

for name in sorted(item for item in dir(unreal.DynamicMesh) if any(token in item.lower() for token in ("transform", "rotate", "translate", "scale"))):
    unreal.log(f"DYNAMIC_MESH_API {name}")
for name in ("rotate_mesh", "transform_mesh"):
    unreal.log(f"DYNAMIC_MESH_DOC {name}: {getattr(unreal.DynamicMesh, name).__doc__}")
