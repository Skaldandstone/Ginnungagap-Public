"""Bounds of the ModSci engineering props considered for the hand-held tool, so the mesh can be
oriented on the weapon actor (whose +X is the direction the player looks) from numbers, not guesses."""
import unreal
for path in ["/Game/ModSci_EngiProps/Meshes/SM_Wrench", "/Game/ModSci_EngiProps/Meshes/SM_Screwdriver",
             "/Game/Assets/Gameplay/EarlyProjectileWeapons/Meshes/SM_PressureBottleFastenerTool"]:
    mesh = unreal.load_asset(path)
    if not mesh:
        print(f"MESHINFO {path}: missing"); continue
    b = mesh.get_bounding_box(); mn, mx = b.min, b.max
    print(f"MESHINFO {path}: X {mn.x:.1f}..{mx.x:.1f} Y {mn.y:.1f}..{mx.y:.1f} Z {mn.z:.1f}..{mx.z:.1f} materials={mesh.get_num_sections(0)}")
