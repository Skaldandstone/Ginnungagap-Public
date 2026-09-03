"""Measures the demo's cryo bay against the Sheet 11 concept reference, numerically.

"Too blue" is not something to fix by eye, because the two candidate causes want opposite fixes and
look identical in a thumbnail:

  - the room *light* is too saturated, in which case LIGHT_BY_PROFILE["cryo"] is the lever; or
  - the light is fine and the saturated blue is coming from the pods' own materials -- the frost
    glass, the status panels, the thaw-cyan emissives -- in which case changing the light will wash
    the whole room and still leave blue pods.

The demo's cryo profile is already (0.72, 0.86, 1.0), which is a pale blue-white, so the first
explanation is not obviously right and is worth testing rather than assuming.

What this prints, for the reference and the render side by side:

  mean RGB          overall cast
  mean saturation   how far from neutral the image sits
  blue-minus-red    the specific complaint, as a number, on lit pixels only
  luminance spread  p10/p50/p90 plus the clipped and crushed fractions

and then the same figures for the most-saturated decile alone. That last split is the one that
separates the two causes: if the whole frame is uniformly blue the light is doing it, and if only a
small bright population is extremely blue while the bulk sits near neutral, it is the pod materials.

Plain Python. No Unreal, no editor.
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
REFERENCE = ROOT / "Content/Assets/ConceptArt/Rooms/Interiors_2026-08/GGP01_Interior_CryoQuarters_Sheet11.png"
RENDER = ROOT / "Saved/HeroShots/Hero_01_CryoWake.png"

# Sheet 11's cryo bay is the top-left quadrant; the other three are quarters and stores.
REFERENCE_QUADRANT = "top-left"


def load(path, quadrant=None):
    if not path.exists():
        sys.exit("Missing: {}".format(path))
    image = Image.open(path).convert("RGB")
    if quadrant == "top-left":
        w, h = image.size
        image = image.crop((0, 0, w // 2, h // 2))
    return np.asarray(image).astype(np.float64) / 255.0


def stats(label, rgb):
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b

    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    sat = np.where(mx > 1e-6, (mx - mn) / np.maximum(mx, 1e-6), 0.0)

    # Only pixels with something in them. Averaging blue-minus-red over crushed blacks measures the
    # size of the shadows, not the colour of the room.
    lit = lum > 0.05
    bmr = (b - r)[lit] if lit.any() else np.array([0.0])

    print("  {}".format(label))
    print("    mean RGB        ({:.3f}, {:.3f}, {:.3f})".format(r.mean(), g.mean(), b.mean()))
    print("    saturation      mean {:.3f}   median {:.3f}   p90 {:.3f}".format(
        sat.mean(), np.median(sat), np.percentile(sat, 90)))
    print("    blue - red      mean {:+.3f}   p90 {:+.3f}   (lit pixels, {:.0f}% of frame)".format(
        bmr.mean(), np.percentile(bmr, 90), 100.0 * lit.mean()))
    print("    luminance       p10 {:.3f}  p50 {:.3f}  p90 {:.3f}".format(
        *np.percentile(lum, [10, 50, 90])))
    print("    clipped >0.95   {:.1%}      crushed <0.02   {:.1%}".format(
        (lum > 0.95).mean(), (lum < 0.02).mean()))

    # The diagnostic split. A uniform cast moves both rows together; a material-driven cast leaves
    # the bulk near neutral and puts all the colour in the top decile.
    if lit.any():
        flat = sat[lit]
        cut = np.percentile(flat, 90)
        top = (sat >= cut) & lit
        bulk = (sat < cut) & lit
        for name, mask in (("most saturated 10%", top), ("remaining 90%", bulk)):
            if mask.any():
                print("      {:<20} mean RGB ({:.3f}, {:.3f}, {:.3f})  blue-red {:+.3f}".format(
                    name,
                    r[mask].mean(), g[mask].mean(), b[mask].mean(),
                    (b - r)[mask].mean()))
    print()


print("REFERENCE  Sheet 11, {} quadrant (cryo bay)".format(REFERENCE_QUADRANT))
stats(REFERENCE.name, load(REFERENCE, REFERENCE_QUADRANT))

print("RENDER     current demo hero shot")
stats(RENDER.name, load(RENDER))

print("Read the last two rows of each block together. If the render's 'remaining 90%' is much bluer")
print("than the reference's, the room light is the cause. If only its 'most saturated 10%' is, the")
print("pod materials are, and the light should be left alone.")
