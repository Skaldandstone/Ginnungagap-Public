"""Render the polished 2.5D CGI trailer from approved Ginnungagap key art."""

from __future__ import annotations

import math
import subprocess
import wave
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "Content" / "Assets" / "ConceptArt"
KEYS = ART / "Trailer"
OUT_DIR = ROOT / "Saved" / "Demo"
VIDEO_ONLY = OUT_DIR / "Ginnungagap_CGI_Trailer_Video.mp4"
SOUNDTRACK = OUT_DIR / "Ginnungagap_CGI_Trailer_Soundtrack.wav"
OUTPUT = OUT_DIR / "Ginnungagap_CGI_Trailer.mp4"

FPS = 30
WIDTH, HEIGHT = 1280, 720
LETTERBOX = 34
SAMPLE_RATE = 48000
RNG = np.random.default_rng(260804)


def font(size: int, bold: bool = False):
    try:
        return ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def cover(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    ratio = WIDTH / HEIGHT
    if image.width / image.height > ratio:
        crop_w = int(image.height * ratio)
        x = (image.width - crop_w) // 2
        image = image.crop((x, 0, x + crop_w, image.height))
    else:
        crop_h = int(image.width / ratio)
        y = (image.height - crop_h) // 2
        image = image.crop((0, y, image.width, y + crop_h))
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def smooth(value: float) -> float:
    return value * value * (3.0 - 2.0 * value)


def camera_frame(base: Image.Image, t: float, zoom: float, pan_x: float, pan_y: float,
                 roll: float = 0.0, shake: float = 0.0) -> Image.Image:
    eased = smooth(t)
    current_zoom = 1.015 + (zoom - 1.015) * eased
    scaled = base.resize((int(WIDTH * current_zoom), int(HEIGHT * current_zoom)), Image.Resampling.LANCZOS)
    overflow_x, overflow_y = scaled.width - WIDTH, scaled.height - HEIGHT
    jitter_x = math.sin(t * 83.0) * shake + math.sin(t * 137.0) * shake * 0.45
    jitter_y = math.sin(t * 101.0) * shake * 0.55
    x = overflow_x * (0.5 + pan_x * (eased - 0.5)) + jitter_x
    y = overflow_y * (0.5 + pan_y * (eased - 0.5)) + jitter_y
    x = int(np.clip(x, 0, max(0, overflow_x)))
    y = int(np.clip(y, 0, max(0, overflow_y)))
    frame = scaled.crop((x, y, x + WIDTH, y + HEIGHT))
    angle = math.sin(t * math.pi * 2.0) * roll
    if abs(angle) > 0.01:
        frame = frame.rotate(angle, Image.Resampling.BICUBIC, expand=False)
    return frame


def add_atmosphere(frame: Image.Image, global_time: float, purple: float, sparks: float,
                   alarm: float, motes: int = 38) -> Image.Image:
    frame = frame.convert("RGBA")
    fx = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(fx)

    pulse = 0.55 + 0.45 * math.sin(global_time * 3.2)
    if purple > 0:
        glow = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        for x, y, radius in ((1060, 195, 190), (830, 430, 120), (410, 250, 90)):
            gd.ellipse((x - radius, y - radius, x + radius, y + radius), fill=(104, 22, 210, int(38 * purple * pulse)))
        glow = glow.filter(ImageFilter.GaussianBlur(75))
        frame = Image.alpha_composite(frame, glow)

    if alarm > 0:
        red = int(42 * alarm * max(0.0, math.sin(global_time * 7.5)))
        draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(190, 18, 5, red))

    for index in range(motes):
        seed = index * 17.731
        x = (seed * 97 + global_time * (9 + index % 5)) % WIDTH
        y = (seed * 53 - global_time * (13 + index % 7)) % HEIGHT
        radius = 1 + index % 3
        alpha = 20 + index % 5 * 8
        color = (174, 101, 255, alpha) if purple > 0.35 and index % 3 == 0 else (220, 224, 210, alpha)
        draw.ellipse((x - radius, y - radius, x + radius, y + radius), fill=color)

    if sparks > 0:
        for index in range(int(18 * sparks)):
            phase = (global_time * (0.8 + index * 0.03) + index * 0.173) % 1.0
            x = WIDTH * (0.72 + 0.22 * math.sin(index * 2.7)) - phase * 220
            y = HEIGHT * (0.18 + 0.6 * phase) + math.sin(index * 4.1) * 80
            draw.line((x, y, x - 16, y + 34), fill=(255, 174, 55, int(210 * sparks)), width=2)

    frame = Image.alpha_composite(frame, fx)
    grade = Image.new("RGBA", frame.size, (5, 12, 20, 25))
    return Image.alpha_composite(frame, grade).convert("RGB")


def caption(frame: Image.Image, heading: str, detail: str, progress: float) -> Image.Image:
    if not heading:
        return frame
    opacity = int(235 * min(1.0, progress / 0.12, (1.0 - progress) / 0.15))
    if opacity <= 0:
        return frame
    layer = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    draw.rectangle((0, HEIGHT - 172, WIDTH, HEIGHT), fill=(1, 4, 7, int(opacity * 0.62)))
    draw.rectangle((56, HEIGHT - 136, 63, HEIGHT - 48), fill=(156, 69, 245, opacity))
    draw.text((88, HEIGHT - 137), heading, font=font(31, True), fill=(245, 247, 246, opacity))
    draw.text((90, HEIGHT - 91), detail, font=font(17), fill=(184, 197, 199, opacity))
    return Image.alpha_composite(frame.convert("RGBA"), layer).convert("RGB")


def cinematic_shot(path: Path, heading: str, detail: str, duration: float, zoom: float,
                   pan_x: float, pan_y: float, purple: float, sparks: float = 0.0,
                   alarm: float = 0.0, shake: float = 0.0, roll: float = 0.0):
    base = cover(path)
    frames = int(duration * FPS)
    for index in range(frames):
        t = index / max(1, frames - 1)
        frame = camera_frame(base, t, zoom, pan_x, pan_y, roll, shake)
        frame = add_atmosphere(frame, index / FPS, purple, sparks, alarm)

        # Soft motion smear on the most aggressive action beats.
        if shake > 2.0:
            shifted = frame.transform(frame.size, Image.Transform.AFFINE, (1, 0, -5, 0, 1, 1), Image.Resampling.BILINEAR)
            frame = Image.blend(frame, shifted, 0.16)
        frame = caption(frame, heading, detail, t)

        fade = min(1.0, index / 8.0, (frames - 1 - index) / 8.0)
        frame = ImageEnhance.Brightness(frame).enhance(0.12 + 0.88 * fade)
        yield np.asarray(frame, dtype=np.uint8)


def card(title: str, subtitle: str, duration: float, final: bool = False):
    frames = int(duration * FPS)
    accent = (160, 72, 248) if final else (226, 131, 46)
    for index in range(frames):
        t = index / max(1, frames - 1)
        image = Image.new("RGB", (WIDTH, HEIGHT), (2, 4, 7))
        glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        radius = 210 + 25 * math.sin(index * 0.12)
        gd.ellipse((WIDTH / 2 - radius, HEIGHT / 2 - radius, WIDTH / 2 + radius, HEIGHT / 2 + radius), fill=(*accent, 38))
        glow = glow.filter(ImageFilter.GaussianBlur(90))
        image = Image.alpha_composite(image.convert("RGBA"), glow).convert("RGB")
        draw = ImageDraw.Draw(image)
        draw.rectangle((85, 126, 93, 594), fill=accent)
        draw.text((135, 280), title, font=font(60, True), fill=(241, 245, 244))
        draw.text((140, 360), subtitle, font=font(23), fill=(158, 176, 179))
        draw.text((140, 558), "CGI CINEMATIC CONCEPT", font=font(14, True), fill=accent)
        fade = min(1.0, index / 14.0, (frames - 1 - index) / 14.0)
        yield np.asarray(ImageEnhance.Brightness(image).enhance(max(0.0, fade)), dtype=np.uint8)


def build_soundtrack(duration: float, impacts: list[float]) -> None:
    total = int(duration * SAMPLE_RATE)
    t = np.arange(total, dtype=np.float64) / SAMPLE_RATE
    drone = 0.11 * np.sin(2 * np.pi * 43 * t) + 0.055 * np.sin(2 * np.pi * 67 * t)
    pulse = 0.035 * np.sin(2 * np.pi * (91 + 4 * np.sin(t * 0.2)) * t)
    noise = RNG.normal(0.0, 0.013, total)
    kernel = np.ones(180) / 180.0
    noise = np.convolve(noise, kernel, mode="same") * 4.0
    audio = drone + pulse + noise

    for point in impacts:
        start = int(point * SAMPLE_RATE)
        length = min(int(1.2 * SAMPLE_RATE), total - start)
        if length <= 0:
            continue
        local_t = np.arange(length) / SAMPLE_RATE
        hit = (0.42 * np.sin(2 * np.pi * 58 * local_t) + 0.22 * RNG.normal(0, 1, length)) * np.exp(-local_t * 6.2)
        audio[start:start + length] += hit

    fade = np.minimum(np.clip(t / 1.8, 0, 1), np.clip((duration - t) / 2.8, 0, 1))
    audio = np.clip(audio * fade, -0.92, 0.92)
    stereo = np.column_stack((audio, audio * 0.94)).reshape(-1)
    pcm = (stereo * 32767).astype(np.int16)
    with wave.open(str(SOUNDTRACK), "wb") as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(SAMPLE_RATE)
        wav.writeframes(pcm.tobytes())


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shots = [
        (ART / "Corvette_MainCorridor_Concept.png", "A DEAD SHIP DRIFTS", "No response from command. No pressure beyond deck three.", 3.2, 1.09, .55, 0, .12, 0, 0, 0, .35),
        (KEYS / "Player_Run_Corridor.png", "RUN", "Restore power before the infection reaches navigation.", 3.0, 1.13, .72, 0, .25, .25, .8, 2.4, .6),
        (KEYS / "Player_Run_Cargo.png", "THE CARGO BAY MOVES", "The Bloom has learned to use the ship.", 3.0, 1.12, -.68, .08, .65, .7, .6, 3.0, .5),
        (ART / "Corvette_MedBay_Concept.png", "CONTAINMENT FAILED", "The bodies were sealed. Something opened them.", 3.2, 1.10, .42, .1, .52, .15, .35, .8, .3),
        (KEYS / "Bloom_Infected_Crew.png", "CREW STATUS: UNKNOWN", "Bloom hosts retain movement, memory, and access.", 2.6, 1.12, .62, 0, .85, .15, .65, 1.8, .4),
        (KEYS / "Bloom_Robotics.png", "MACHINES COMPROMISED", "Maintenance frames become hunters.", 2.6, 1.13, -.55, 0, 1.0, .7, .6, 2.4, .45),
        (KEYS / "Player_Combat_Struggle.png", "HOLD THE CORRIDOR", "Infected creatures. Reanimated corpses. Corrupted robotics.", 4.5, 1.16, .58, -.08, 1.0, 1.0, 1.0, 5.0, .8),
        (KEYS / "ZeroG_Crew.png", "GRAVITY FAILURE", "Cross the breach before life support collapses.", 2.8, 1.11, -.62, 0, .35, .35, .2, 1.5, .8),
        (ART / "Corvette_BloomReactor_Concept.png", "THE COLONY IS IN THE REACTOR", "Purge it—or destroy the ship.", 4.2, 1.14, .4, 0, 1.0, .4, .35, 1.2, .25),
        (KEYS / "Bloom_Threat_Lineup.png", "THE BLOOM ADAPTS", "Every corpse and every machine is another possible body.", 3.0, 1.10, .45, 0, .9, .1, .35, 1.4, .2),
    ]

    intro_duration, final_duration = 2.7, 3.2
    duration = intro_duration + sum(s[3] for s in shots) + final_duration
    cut_times = []
    cursor = intro_duration
    for item in shots:
        cut_times.append(cursor)
        cursor += item[3]

    writer = imageio.get_writer(str(VIDEO_ONLY), fps=FPS, codec="libx264", quality=7, macro_block_size=None)
    try:
        for frame in card("GINNUNGAGAP", "Something on board is rebuilding itself", intro_duration):
            writer.append_data(frame)
        for item in shots:
            for frame in cinematic_shot(*item):
                # Cinematic letterbox is applied after all overlays.
                frame = np.array(frame, copy=True)
                frame[:LETTERBOX, :, :] = 0
                frame[HEIGHT - LETTERBOX:, :, :] = 0
                writer.append_data(frame)
        for frame in card("DO NOT LET IT JUMP", "Survive the ship. Burn out the Bloom.", final_duration, True):
            writer.append_data(frame)
    finally:
        writer.close()

    build_soundtrack(duration, cut_times + [cut_times[6] + 1.0, cut_times[6] + 2.5])
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([
        ffmpeg, "-y", "-i", str(VIDEO_ONLY), "-i", str(SOUNDTRACK),
        "-map", "0:v", "-map", "1:a", "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(OUTPUT)
    ], check=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
