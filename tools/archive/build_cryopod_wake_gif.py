from pathlib import Path

from PIL import Image, ImageEnhance


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Content" / "ConceptArt" / "Cryopods" / "CryopodWakeStoryboard.png"
OUTPUT = ROOT / "Content" / "ConceptArt" / "Cryopods" / "CryopodWakeAnimatic.gif"


def main() -> None:
    sheet = Image.open(SOURCE).convert("RGB")
    width, height = sheet.size
    cell_width = width // 3
    cell_height = height // 2
    inset = max(2, width // 700)
    frames: list[Image.Image] = []

    for row in range(2):
        for column in range(3):
            left = column * cell_width + inset
            top = row * cell_height + inset
            right = (column + 1) * cell_width - inset
            bottom = (row + 1) * cell_height - inset
            frame = sheet.crop((left, top, right, bottom))
            frame.thumbnail((720, 405), Image.Resampling.LANCZOS)
            frame = ImageEnhance.Contrast(frame).enhance(1.04)
            frames.append(frame)

    # Longer holds sell the initial grogginess, failed release, and final recovery.
    durations = [1200, 900, 850, 1050, 1000, 1500]
    frames[0].save(
        OUTPUT,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        optimize=True,
        disposal=2,
    )
    print(f"Created {OUTPUT} ({OUTPUT.stat().st_size} bytes, {frames[0].size[0]}x{frames[0].size[1]})")


if __name__ == "__main__":
    main()
