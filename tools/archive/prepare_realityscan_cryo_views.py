"""Split the concept-derived CRYO-01 turnaround into RealityScan input cameras."""
from pathlib import Path
from PIL import Image

SOURCE = Path(r"C:\Users\James\.codex\generated_images\01a02290-ec29-79d1-87e3-991ce761ce91\exec-b4241b10-5f24-4011-a9d9-460d82b5bc67.png")
ROOT = Path(__file__).resolve().parents[1]
SHEET = ROOT / "docs" / "concept-art" / "ship-rooms" / "cryo-pod-realityscan-turnaround-v2.png"
VIEWS = ROOT / "Build" / "RealityScan" / "CryoTurnaround" / "InputViews"
NAMES = (
    "01_front_three_quarter.png", "02_strict_side.png", "03_rear_three_quarter.png",
    "04_front_elevation.png", "05_rear_elevation.png", "06_top_three_quarter.png",
)

VIEWS.mkdir(parents=True, exist_ok=True)
image = Image.open(SOURCE).convert("RGB")
image.save(SHEET, quality=95)
panel_w, panel_h = image.width // 3, image.height // 2
for index, name in enumerate(NAMES):
    col, row = index % 3, index // 3
    # Trim the one-pixel contact-sheet divider so it cannot become a false feature.
    box = (col * panel_w + 2, row * panel_h + 2, (col + 1) * panel_w - 2, (row + 1) * panel_h - 2)
    image.crop(box).save(VIEWS / name, quality=95)
print(f"Prepared {len(NAMES)} RealityScan views at {VIEWS}")
