"""Synthesises and imports the hull strike the demo opens on.

Same approach as the hulk's roar: built from first principles, imported as a project asset. A
strike from outside a pressure hull, heard from inside: a sub thud with a fast attack, a metal
groan riding out of it (two detuned low partials sweeping down), a burst of debris crackle, and a
long structural tail. 2.6 s, mono.

Run:  UnrealEditor-Cmd.exe <project> -ExecutePythonScript=<forward-slash path to this file> -NullRHI
"""
import math
import random
import struct
import wave
from pathlib import Path

import unreal

AUDIO_PATH = "/Game/Assets/Ships/Production/Audio"
NAME = "S_Ship_HullStrike"
SOURCE_DIR = Path(unreal.SystemLibrary.get_project_directory()) / "Intermediate" / "ShipProduction" / "Environment"
SAMPLE_RATE = 44100
SECONDS = 2.6


def synth():
    random.seed(2201)
    n = int(SECONDS * SAMPLE_RATE)
    dry = [0.0] * n
    for i in range(n):
        t = i / SAMPLE_RATE
        # Thud: a pitch-dropping sine with a very fast attack.
        f = 62.0 * math.exp(-t * 3.2) + 28.0
        thud = math.sin(math.tau * f * t) * math.exp(-t * 2.6) * (min(1.0, t / 0.006))
        # Groan: two detuned partials sliding down over a second, delayed a touch.
        groan = 0.0
        if t > 0.08:
            u = t - 0.08
            fa = 138.0 * math.exp(-u * 0.9) + 40.0
            fb = 146.5 * math.exp(-u * 0.85) + 43.0
            groan = 0.28 * (math.sin(math.tau * fa * u) + 0.8 * math.sin(math.tau * fb * u + 0.6)) * math.exp(-u * 1.35)
        # Debris: crackle burst in the first third of a second.
        debris = 0.0
        if t < 0.45:
            debris = (random.random() * 2 - 1) * 0.25 * math.exp(-t * 9.0) * (1.0 if random.random() < 0.6 else 0.2)
        # Structural tail: low noise, slow decay.
        tail = (random.random() * 2 - 1) * 0.06 * math.exp(-t * 1.1)
        dry[i] = 0.9 * thud + groan + debris + tail

    out = list(dry)
    for delay_s, gain in ((0.061, 0.33), (0.127, 0.22), (0.211, 0.14)):
        d = int(delay_s * SAMPLE_RATE)
        for i in range(d, n):
            out[i] += dry[i - d] * gain
    peak = max(1e-6, max(abs(v) for v in out))
    frames = []
    for v in out:
        x = math.tanh(1.5 * v / peak) / math.tanh(1.5)
        frames.append(struct.pack("<h", int(max(-1.0, min(1.0, x * 0.95)) * 32767)))
    return b"".join(frames)


def main():
    SOURCE_DIR.mkdir(parents=True, exist_ok=True)
    source = SOURCE_DIR / (NAME + ".wav")
    with wave.open(str(source), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(synth())
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", str(source))
    task.set_editor_property("destination_path", AUDIO_PATH)
    task.set_editor_property("destination_name", NAME)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    sound = unreal.load_asset(f"{AUDIO_PATH}/{NAME}")
    if not sound:
        raise RuntimeError("Strike did not import: " + str(source))
    sound.set_editor_property("looping", False)
    unreal.EditorAssetLibrary.save_loaded_asset(sound)
    unreal.log("STRIKEAUDIO imported {} ({:.1f} s)".format(sound.get_path_name(), SECONDS))


if __name__ == "__main__":
    main()
