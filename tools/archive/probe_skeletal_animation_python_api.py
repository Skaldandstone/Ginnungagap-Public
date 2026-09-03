"""Log editor-callable skeletal animation helpers for showcase tooling."""

import unreal


names = [
    name
    for name in dir(unreal.SkeletalMeshComponent)
    if any(token in name.lower() for token in ("anim", "position", "bone", "refresh", "tick"))
]
unreal.log("SKELETAL ANIMATION PYTHON API: " + ", ".join(sorted(names)))
