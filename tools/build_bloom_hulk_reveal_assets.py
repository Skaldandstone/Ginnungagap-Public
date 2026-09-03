"""Synthesises and imports the Bloom hulk's roar.

There is no roar anywhere in the project's audio -- the Fab packs carry ambient drones and UI
clicks, the project's own production audio is three loops built by tools/archive/
build_ship_environment_assets.py. This follows that script's approach: write a WAV from first
principles and import it, so the asset is project-authored rather than a placeholder borrowed
from a pack that will need replacing.

The sound is built as what a roar from something that size, in that body, would be: a sub growl
whose pitch swells and breaks (a low harmonic stack under frequency modulation), vocal-fry rasp
(noise gated at ~28 Hz), a metallic screech riding the top of it (two ringing partials falling in
pitch -- this is a pressure shell, not a throat), and a short early-reflection tail so it sits in a
steel room. Soft-clipped, normalised, 3.4 s, mono.

Idempotent: re-importing replaces the asset in place.

Run:  UnrealEditor-Cmd.exe <project> -ExecutePythonScript=<forward-slash path to this file> -NullRHI
"""
import math
import random
import struct
import wave
from pathlib import Path

import unreal

AUDIO_PATH = "/Game/Assets/Ships/Production/Audio"
NAME = "S_Bloom_Hulk_Roar"
SOURCE_DIR = Path(unreal.SystemLibrary.get_project_directory()) / "Intermediate" / "ShipProduction" / "Environment"
SAMPLE_RATE = 44100
SECONDS = 3.4


def envelope(t, attack, hold, release, total):
    if t < attack:
        return t / attack
    if t < attack + hold:
        return 1.0
    tail = total - (attack + hold)
    return max(0.0, 1.0 - (t - attack - hold) / max(release, tail)) ** 1.6


def synth():
    random.seed(9181)
    n = int(SECONDS * SAMPLE_RATE)
    dry = [0.0] * n
    phase = 0.0
    fry_phase = 0.0
    for i in range(n):
        t = i / SAMPLE_RATE
        # Pitch contour: rises into the roar, breaks upward, then falls away.
        f0 = 34.0 + 22.0 * math.sin(math.pi * min(1.0, t / 2.2)) + (9.0 if 0.9 < t < 1.6 else 0.0)
        f0 += 3.5 * math.sin(math.tau * 6.3 * t)                      # vibrato / instability
        phase += math.tau * f0 / SAMPLE_RATE
        growl = 0.0
        for h in range(1, 9):
            growl += math.sin(phase * h + 0.35 * math.sin(phase * 0.5 * h)) / (h ** 0.85)
        growl *= 0.42 * envelope(t, 0.28, 1.3, 1.5, SECONDS)

        # Vocal fry: noise gated at ~28 Hz, opening as the roar commits.
        fry_phase += math.tau * (26.0 + 6.0 * math.sin(math.tau * 0.7 * t)) / SAMPLE_RATE
        gate = 1.0 if math.sin(fry_phase) > 0.15 else 0.12
        rasp = gate * (random.random() * 2.0 - 1.0) * 0.20 * envelope(t, 0.45, 1.1, 1.2, SECONDS)

        # Metallic screech on the shell: two partials falling, only through the middle.
        screech = 0.0
        if 0.55 < t < 1.75:
            u = (t - 0.55) / 1.2
            fa = 1900.0 * (1.0 - 0.35 * u)
            fb = 2720.0 * (1.0 - 0.42 * u)
            window = math.sin(math.pi * u) ** 1.4
            screech = window * 0.10 * (math.sin(math.tau * fa * t) + 0.6 * math.sin(math.tau * fb * t + 1.1))

        dry[i] = growl + rasp + screech

    # Early reflections: three delayed copies, a steel compartment rather than a hall.
    out = list(dry)
    for delay_s, gain in ((0.087, 0.38), (0.141, 0.26), (0.233, 0.17)):
        d = int(delay_s * SAMPLE_RATE)
        for i in range(d, n):
            out[i] += dry[i - d] * gain

    # Soft clip and normalise.
    peak = max(1e-6, max(abs(v) for v in out))
    frames = []
    for v in out:
        x = math.tanh(1.6 * v / peak) / math.tanh(1.6)
        frames.append(struct.pack("<h", int(max(-1.0, min(1.0, x * 0.92)) * 32767)))
    return b"".join(frames)


def write_wav(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(synth())


def import_roar():
    source = SOURCE_DIR / (NAME + ".wav")
    write_wav(source)
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
        raise RuntimeError("Roar did not import: " + str(source))
    sound.set_editor_property("looping", False)
    unreal.EditorAssetLibrary.save_loaded_asset(sound)
    unreal.log("HULKAUDIO imported {} ({:.1f} s) from {}".format(sound.get_path_name(), SECONDS, source))
    return sound


if __name__ == "__main__":
    import_roar()
