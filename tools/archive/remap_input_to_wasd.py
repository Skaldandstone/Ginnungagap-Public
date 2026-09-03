"""Normalize the default Enhanced Input movement scheme to WASD.

Run with UnrealEditor-Cmd's -ExecutePythonScript option.
"""

import unreal


CONTEXT_PATH = "/Game/Input/IMC_Default"
MOVE_ACTION_PATH = "/Game/Input/Actions/IA_Move"
ARROW_KEYS = ("Up", "Down", "Left", "Right")


context = unreal.load_asset(CONTEXT_PATH)
move_action = unreal.load_asset(MOVE_ACTION_PATH)

if not context or not move_action:
    raise RuntimeError("Could not load the default input context and move action")

context.modify()
for key_name in ARROW_KEYS:
    key = unreal.Key()
    key.set_editor_property("key_name", key_name)
    context.unmap_key(move_action, key)

mapping_text = context.get_editor_property("default_key_mappings").export_text()
for key_name in ("W", "A", "S", "D"):
    if f"Key={key_name}" not in mapping_text:
        raise RuntimeError(f"Expected movement binding is missing: {key_name}")
for key_name in ARROW_KEYS:
    if f"Key={key_name}" in mapping_text:
        raise RuntimeError(f"Arrow-key binding was not removed: {key_name}")

if not unreal.EditorAssetLibrary.save_loaded_asset(context, only_if_is_dirty=False):
    raise RuntimeError(f"Could not save {CONTEXT_PATH}")

unreal.log("Default movement remapped to standard WASD controls")
