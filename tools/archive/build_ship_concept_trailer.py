"""Build a cinematic concept trailer from approved Ginnungagap key art."""

from __future__ import annotations

import subprocess
from pathlib import Path

import imageio.v2 as imageio
import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont


ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "Content" / "Assets" / "ConceptArt"
TRAILER_ART = ART / "Trailer"
OUTPUT_DIR = ROOT / "Saved" / "Demo"
SILENT_OUTPUT = OUTPUT_DIR / "Ginnungagap_Concept_Trailer_Silent.mp4"
OUTPUT = OUTPUT_DIR / "Ginnungagap_Concept_Trailer.mp4"
FPS = 24
WIDTH, HEIGHT = 1280, 720


def font(size: int, bold: bool = False):
    try:
        return ImageFont.truetype("arialbd.ttf" if bold else "arial.ttf", size)
    except OSError:
        return ImageFont.load_default()


def fit_image(path: Path) -> Image.Image:
    image = Image.open(path).convert("RGB")
    source_ratio = image.width / image.height
    target_ratio = WIDTH / HEIGHT
    if source_ratio > target_ratio:
        crop_width = int(image.height * target_ratio)
        left = (image.width - crop_width) // 2
        image = image.crop((left, 0, left + crop_width, image.height))
    else:
        crop_height = int(image.width / target_ratio)
        top = (image.height - crop_height) // 2
        image = image.crop((0, top, image.width, top + crop_height))
    return image.resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)


def title_card(title: str, subtitle: str, seconds: float, purple: bool = False):
    total = int(seconds * FPS)
    accent = (155, 76, 240) if purple else (225, 132, 48)
    for index in range(total):
        image = Image.new("RGB", (WIDTH, HEIGHT), (3, 5, 8))
        draw = ImageDraw.Draw(image)
        glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        glow_draw = ImageDraw.Draw(glow)
        radius = 170 + int(25 * np.sin(index / 8))
        glow_draw.ellipse((WIDTH // 2 - radius, HEIGHT // 2 - radius, WIDTH // 2 + radius, HEIGHT // 2 + radius), fill=(*accent, 28))
        glow = glow.filter(ImageFilter.GaussianBlur(70))
        image = Image.alpha_composite(image.convert("RGBA"), glow).convert("RGB")
        draw = ImageDraw.Draw(image)
        draw.rectangle((94, 142, 101, 578), fill=accent)
        draw.text((140, 278), title, font=font(54, True), fill=(240, 244, 243))
        draw.text((144, 350), subtitle, font=font(22), fill=(159, 174, 178))
        draw.text((144, 548), "CINEMATIC CONCEPT TRAILER", font=font(14, True), fill=accent)
        fade = min(1.0, index / 12.0, (total - 1 - index) / 12.0)
        yield np.asarray(ImageEnhance.Brightness(image).enhance(max(0.0, fade)), dtype=np.uint8)


def shot(path: Path, heading: str, detail: str, seconds: float, pan_x: float, pan_y: float, zoom_end: float = 1.08):
    base = fit_image(path)
    total = int(seconds * FPS)
    for index in range(total):
        t = index / max(1, total - 1)
        eased = t * t * (3.0 - 2.0 * t)
        zoom = 1.0 + (zoom_end - 1.0) * eased
        scaled = base.resize((int(WIDTH * zoom), int(HEIGHT * zoom)), Image.Resampling.LANCZOS)
        overflow_x = scaled.width - WIDTH
        overflow_y = scaled.height - HEIGHT
        center_x = overflow_x * 0.5 + pan_x * overflow_x * (eased - 0.5)
        center_y = overflow_y * 0.5 + pan_y * overflow_y * (eased - 0.5)
        left = int(np.clip(center_x, 0, overflow_x))
        top = int(np.clip(center_y, 0, overflow_y))
        frame = scaled.crop((left, top, left + WIDTH, top + HEIGHT)).convert("RGBA")

        overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        draw.rectangle((0, HEIGHT - 150, WIDTH, HEIGHT), fill=(2, 5, 8, 145))
        draw.rectangle((50, HEIGHT - 120, 57, HEIGHT - 42), fill=(158, 77, 241, 235))
        draw.text((82, HEIGHT - 119), heading, font=font(29, True), fill=(244, 247, 246, 255))
        draw.text((84, HEIGHT - 78), detail, font=font(17), fill=(181, 195, 198, 255))
        frame = Image.alpha_composite(frame, overlay).convert("RGB")

        fade = min(1.0, index / 10.0, (total - 1 - index) / 10.0)
        frame = ImageEnhance.Brightness(frame).enhance(0.2 + 0.8 * fade)
        yield np.asarray(frame, dtype=np.uint8)


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    timeline = [
        (ART / "Corvette_MainCorridor_Concept.png", "THE SHIP IS NOT EMPTY", "A military corvette wakes after a failed containment event", 3.0, 0.45, 0.0, 1.07),
        (TRAILER_ART / "Player_Run_Corridor.png", "RUN THE COMPANIONWAY", "The player races toward engineering as the Bloom spreads through the deck", 3.0, 0.7, 0.0, 1.10),
        (TRAILER_ART / "Player_Run_Cargo.png", "CARGO BREAKS LOOSE", "Corrupted machinery and unstable freight turn every room into a hazard", 3.0, -0.65, 0.1, 1.09),
        (ART / "Corvette_MedBay_Concept.png", "THE CREW DID NOT ESCAPE", "Damaged suits and abandoned treatment bays reveal the cost of containment", 3.0, 0.35, 0.15, 1.08),
        (TRAILER_ART / "Bloom_Infected_Crew.png", "THE DEAD ARE CHANGING", "Bloom-infected hosts retain fragments of movement and purpose", 2.7, 0.55, 0.0, 1.10),
        (TRAILER_ART / "Bloom_Robotics.png", "IT LEARNS THE MACHINES", "Maintenance drones and heavy robotics become new bodies", 2.7, -0.55, 0.0, 1.10),
        (TRAILER_ART / "Player_Combat_Struggle.png", "FIGHT THROUGH THE BLOOM", "Hold the corridor against infected crew, corpses, and corrupted robotics", 4.0, 0.5, -0.1, 1.12),
        (TRAILER_ART / "ZeroG_Crew.png", "SURVIVE ZERO-G", "Cross ruptured sections before pressure and power collapse", 2.8, -0.6, 0.0, 1.09),
        (ART / "Corvette_BloomReactor_Concept.png", "REACH THE REACTOR", "Burn out the colony—or carry it into the next system", 4.0, 0.35, 0.0, 1.11),
        (TRAILER_ART / "Bloom_Threat_Lineup.png", "THE BLOOM ADAPTS", "Crew. Corpses. Robotics. Every system is a possible host.", 2.8, 0.4, 0.0, 1.08),
    ]

    writer = imageio.get_writer(str(SILENT_OUTPUT), fps=FPS, codec="libx264", quality=9, macro_block_size=None)
    try:
        for frame in title_card("GINNUNGAGAP", "Something survived the jump", 2.3):
            writer.append_data(frame)
        for args in timeline:
            for frame in shot(*args):
                writer.append_data(frame)
        for frame in title_card("DO NOT LET IT JUMP", "A co-op military science-fiction survival horror concept", 2.8, True):
            writer.append_data(frame)
    finally:
        writer.close()

    duration = 2.3 + sum(entry[3] for entry in timeline) + 2.8
    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    subprocess.run([
        ffmpeg, "-y", "-i", str(SILENT_OUTPUT),
        "-f", "lavfi", "-i", f"sine=frequency=52:sample_rate=48000:duration={duration:.2f}",
        "-filter_complex", "[1:a]volume=0.045,lowpass=f=180,afade=t=in:st=0:d=2,afade=t=out:st=31:d=3[a]",
        "-map", "0:v", "-map", "[a]", "-c:v", "libx264", "-preset", "medium", "-crf", "20",
        "-c:a", "aac", "-b:a", "160k", "-shortest", str(OUTPUT)
    ], check=True)
    print(OUTPUT)


if __name__ == "__main__":
    main()
