"""Assembles the recorded walkthrough frames into the demo video.

The walkthrough test, run under a windowed editor with -GinnungagapRecordWalk and a fixed 30 Hz
timestep, writes one screenshot per frame -- Frame_000000.png onward -- of the player's own view,
HUD included, from the opening shot on the sleeper through the title card. This turns that
sequence into an H.264 MP4 with ffmpeg, which is on this machine through winget's yt-dlp bundle.

A screenshot has no audio, so the track is laid in afterwards on the same fixed timeline: the
walk writes Saved/Video/cues.json (cue name and frame) while it records, and this mixes the
synthesized in-game cues from Intermediate/ShipProduction/Environment (the hull strike, the
hulk's roar) at those frames over a low ship-hum bed, with a soft tone under the title card.
It is an edit, not a capture, and says so in the file name. --no-audio skips it.

    python tools/assemble_demo_video.py [--fps 30] [--keep-frames] [--no-audio]
"""
import json
import argparse
import datetime as dt
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRAMES = ROOT / "Saved" / "Screenshots" / "WindowsEditor"
OUT_DIR = ROOT / "Saved" / "Video"


def find_ffmpeg():
    found = shutil.which("ffmpeg")
    if found:
        return found
    candidates = list((Path.home() / "AppData/Local/Microsoft/WinGet/Packages").glob("**/ffmpeg*/bin/ffmpeg.exe"))
    if candidates:
        return str(candidates[0])
    raise SystemExit("ffmpeg not found on PATH or under WinGet packages")


CUE_SOUNDS = {
    "strike": ROOT / "Intermediate" / "ShipProduction" / "Environment" / "S_Ship_HullStrike.wav",
    "roar": ROOT / "Intermediate" / "ShipProduction" / "Environment" / "S_Bloom_Hulk_Roar.wav",
}


def load_cues(skip_lead_in):
    """The cue list the walk wrote, with frames shifted by the dropped lead-in; None if absent."""
    path = OUT_DIR / "cues.json"
    if not path.exists():
        print("no cues.json; assembling without audio")
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    cues = [(c["name"], max(0, c["frame"] - skip_lead_in)) for c in data.get("cues", [])]
    print("cues:", ", ".join(f"{n}@{f}" for n, f in cues))
    return cues


def audio_inputs_and_filter(cues, fps, seconds):
    """ffmpeg inputs and a filter graph: hum bed, the cue WAVs delayed to their frames, a title tone."""
    inputs = ["-f", "lavfi", "-t", f"{seconds:.3f}", "-i", "anoisesrc=color=brown:amplitude=0.035:seed=7"]
    labels = ["[1:a]lowpass=f=180,volume=1.0[bed]"]
    mix = ["[bed]"]
    index = 2
    for name, frame in cues:
        wav = CUE_SOUNDS.get(name)
        if wav and wav.exists():
            inputs += ["-i", str(wav)]
            ms = int(frame / fps * 1000)
            labels.append(f"[{index}:a]adelay={ms}|{ms},volume=0.9[c{index}]")
            mix.append(f"[c{index}]")
            index += 1
        elif name == "title":
            start = frame / fps
            inputs += ["-f", "lavfi", "-t", f"{max(0.5, seconds - start):.3f}", "-i", "sine=frequency=55:sample_rate=44100"]
            ms = int(start * 1000)
            labels.append(f"[{index}:a]afade=t=in:d=2.5,volume=0.25,adelay={ms}|{ms}[c{index}]")
            mix.append(f"[c{index}]")
            index += 1
    graph = ";".join(labels) + ";" + "".join(mix) + f"amix=inputs={len(mix)}:duration=first:normalize=0[aout]"
    return inputs + ["-filter_complex", graph, "-map", "0:v", "-map", "[aout]"]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--keep-frames", action="store_true")
    parser.add_argument("--no-audio", action="store_true")
    parser.add_argument("--skip-lead-in", type=int, default=2,
                        help="frames to drop from the start; the first two are the editor viewport before PIE has drawn")
    args = parser.parse_args()

    frames = sorted(FRAMES.glob("Frame_*.png"))[args.skip_lead_in:]
    if not frames:
        raise SystemExit("No Frame_*.png under " + str(FRAMES) + "; record the walk first")
    # ffmpeg's image sequence demuxer wants contiguous numbering from a start index.
    staging = OUT_DIR / "frames"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    for index, frame in enumerate(frames):
        (staging / f"f_{index:06d}.png").hardlink_to(frame) if hasattr(Path, "hardlink_to") else shutil.copy2(frame, staging / f"f_{index:06d}.png")

    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M")
    seconds = len(frames) / args.fps
    cues = None if args.no_audio else load_cues(args.skip_lead_in)
    output = OUT_DIR / (f"Ginnungagap_DemoWalk_{stamp}_audio.mp4" if cues else f"Ginnungagap_DemoWalk_{stamp}.mp4")
    command = [find_ffmpeg(), "-y", "-framerate", str(args.fps), "-i", str(staging / "f_%06d.png")]
    if cues:
        command += audio_inputs_and_filter(cues, args.fps, seconds)
    command += ["-c:v", "libx264", "-preset", "slow", "-crf", "17", "-pix_fmt", "yuv420p",
                "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-movflags", "+faststart"]
    if cues:
        command += ["-c:a", "aac", "-b:a", "192k", "-shortest"]
    command.append(str(output))
    print(" ".join(command))
    subprocess.run(command, check=True)
    print(f"wrote {output} ({len(frames)} frames, {seconds:.1f} s at {args.fps} fps{', with audio' if cues else ''})")
    if not args.keep_frames:
        shutil.rmtree(staging)


if __name__ == "__main__":
    main()
