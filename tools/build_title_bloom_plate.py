"""Bakes the title plate: GINNUNGAGAP as ceramic plating taken by the Bloom, left to right.

Built from the Bloom threat family production system's own layering -- clean host, infection
meshes, crystal growths, tendrils, emissive core, VFX -- applied to eleven letters in the order the
game's stages run. The first letters are clean off-white ceramic plating with panel seams; from
the third, dark black-violet fibre bundles root at the edges and wrap the forms; from the fifth,
clusters of translucent violet crystal prisms grow out of the edges; from the sixth, small
white-violet cores sit sunk in the plating; from the seventh, root bundles hang from the baseline
and the fibre gains mass; a low violet haze gathers behind the last letters. Charcoal ground; no
colour that is not on the reference sheet.

Two layers, because the in-game widget animates only one of them:
  Title_Ginnungagap_Plate.png  -- everything that is matter (ceramic, fibre, crystal, tendril).
  Title_Ginnungagap_Glow.png   -- the cores and the haze; the widget breathes this over the plate.
Plus Title_Ginnungagap_Preview.png, the two composited on charcoal, for the concept page.

Plain Python (Pillow + numpy), not Unreal's: Unreal's embedded Python has neither. Run:
    python tools/build_title_bloom_plate.py
then import with tools/import_title_bloom_plate.py under UnrealEditor-Cmd.
Deterministic: seeded, so a re-run is the same plate.
"""
import math
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "Intermediate" / "UI" / "Title"
WORD = "GINNUNGAGAP"
W, H = 2400, 640
BASELINE = 420
FONT_SIZE = 250
TRACKING = 26

CERAMIC = (214, 208, 196)
CERAMIC_SHADE = (168, 163, 154)
SEAM = (120, 116, 110)
GRAPHITE = (44, 47, 52)
FIBRE = (30, 16, 44)
FIBRE_MID = (58, 31, 84)
FIBRE_HI = (104, 66, 140)
CRYSTAL_DARK = (74, 36, 140)
CRYSTAL = (128, 78, 220)
CRYSTAL_LIGHT = (186, 150, 255)
CORE = (190, 130, 255)
HAZE = (96, 46, 190)

rng = random.Random(9181)


def stage_of(index):
    """Six stages over eleven letters: two letters each, the last alone."""
    return min(5, index * 6 // len(WORD))


def load_font():
    for path, axes in (("C:/Windows/Fonts/bahnschrift.ttf", [700, 100]),
                       ("C:/Windows/Fonts/ariblk.ttf", None),
                       ("C:/Windows/Fonts/impact.ttf", None)):
        try:
            font = ImageFont.truetype(path, FONT_SIZE)
            if axes:
                try:
                    font.set_variation_by_axes(axes)
                except Exception:
                    pass
            return font
        except OSError:
            continue
    return ImageFont.load_default()


def glyph_masks(font):
    widths = [font.getlength(c) for c in WORD]
    total = sum(widths) + TRACKING * (len(WORD) - 1)
    x = (W - total) / 2.0
    masks, boxes = [], []
    for ch, cw in zip(WORD, widths):
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).text((x, BASELINE), ch, font=font, fill=255, anchor="ls")
        masks.append(m)
        boxes.append(m.getbbox())
        x += cw + TRACKING
    union = Image.new("L", (W, H), 0)
    for m in masks:
        union = ImageChops.lighter(union, m)
    return masks, boxes, union


def noise(scale, amplitude, seed):
    r = np.random.default_rng(seed)
    small = r.random((H // scale + 2, W // scale + 2)).astype(np.float32)
    img = Image.fromarray((small * 255).astype(np.uint8), "L").resize((W, H), Image.BICUBIC)
    arr = 128 + (np.asarray(img, dtype=np.float32) - 128) * amplitude
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "L")


def smooth_curve(points, samples=10):
    """Catmull-Rom through the points, so strands bend rather than kink."""
    if len(points) < 3:
        return points
    out = []
    pts = [points[0]] + points + [points[-1]]
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for k in range(samples):
            t = k / samples
            t2, t3 = t * t, t * t * t
            x = 0.5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * t + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * t2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * t3)
            y = 0.5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * t + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * t2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * t3)
            out.append((x, y))
    out.append(points[-1])
    return out


def strand(draw, pts, width, base, highlight):
    """A fibre with body: dark stroke, then a thinner lighter stroke offset up-left for volume."""
    draw.line(pts, fill=base, width=width, joint="curve")
    if width >= 3:
        hi = [(x - 1, y - 1) for x, y in pts]
        draw.line(hi, fill=highlight, width=max(1, width // 3), joint="curve")


def ceramic_plate(union, masks, boxes):
    plate = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    under = Image.new("RGBA", (W, H), GRAPHITE + (255,))
    plate.paste(under, (3, 4), union)

    face = Image.new("RGB", (W, H), CERAMIC)
    fine = noise(3, 0.22, 3)
    face = ImageChops.multiply(face, Image.merge("RGB", (fine, fine, fine)).point(lambda v: int(v * 0.25 + 191)))
    # Top-light: the upper edge of every stroke catches light, the lower edge falls into shade.
    eroded = union.filter(ImageFilter.MinFilter(9))
    rim = ImageChops.subtract(union, eroded)
    shade = Image.new("RGB", (W, H), CERAMIC_SHADE)
    shade_mask = ImageChops.multiply(rim, Image.new("L", (W, H), 0).transform((W, H), Image.AFFINE, (1, 0, 0, 0, 1, 6), fillcolor=0) or rim)
    face.paste(shade, (0, 0), rim.transform((W, H), Image.AFFINE, (1, 0, 0, 0, 1, -5)).point(lambda v: int(v * 0.75)))
    face.paste(Image.new("RGB", (W, H), (236, 232, 222)), (0, 0), rim.transform((W, H), Image.AFFINE, (1, 0, 0, 0, 1, 4)).point(lambda v: int(v * 0.6)))
    # Dim per letter with its stage.
    dim = Image.new("L", (W, H), 255)
    dd = ImageDraw.Draw(dim)
    for i, b in enumerate(boxes):
        if b:
            dd.rectangle([b[0] - 20, 0, b[2] + 20, H], fill=255 - int(30 * stage_of(i) / 5.0))
    face = ImageChops.multiply(face, Image.merge("RGB", (dim, dim, dim)))
    face_rgba = face.convert("RGBA")
    face_rgba.putalpha(union)
    plate = Image.alpha_composite(plate, face_rgba)

    seams = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(seams)
    for i, b in enumerate(boxes):
        if not b:
            continue
        for _ in range(rng.randint(2, 4)):
            y = rng.uniform(b[1] + 24, b[3] - 24)
            x0 = rng.uniform(b[0], b[2]); length = rng.uniform(30, 120)
            sd.line([(x0, y), (x0 + length, y)], fill=SEAM + (150,), width=2)
            sd.line([(x0, y + 2), (x0 + length, y + 2)], fill=(240, 236, 228, 90), width=1)
        for _ in range(rng.randint(1, 3)):   # a rivet or two
            rx, ry = rng.uniform(b[0] + 14, b[2] - 14), rng.uniform(b[1] + 14, b[3] - 14)
            sd.ellipse([rx - 3, ry - 3, rx + 3, ry + 3], fill=SEAM + (160,))
    seams.putalpha(ImageChops.multiply(seams.getchannel("A"), union.filter(ImageFilter.MinFilter(5))))
    return Image.alpha_composite(plate, seams)


def fibres(masks, boxes, union):
    """Bundles: several strands leave one root together, bend around the form, and knot."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    grown = union.filter(ImageFilter.MaxFilter(27))
    for i, b in enumerate(boxes):
        s = stage_of(i)
        if not b or s < 1:
            continue
        roots = [0, 2, 3, 4, 5, 7][s]
        for _ in range(roots):
            # A root on the edge of the glyph, found by sampling the rim.
            for _try in range(40):
                rx, ry = rng.uniform(b[0], b[2]), rng.uniform(b[1], b[3])
                if masks[i].getpixel((int(rx), int(ry))) > 0 and union.filter(ImageFilter.MinFilter(7)).getpixel((int(rx), int(ry))) == 0:
                    break
            per_root = rng.randint(2, 4) + s // 2
            for k in range(per_root):
                pts = [(rx, ry)]
                heading = rng.uniform(0, math.tau)
                x, y = rx, ry
                for _step in range(rng.randint(4, 7) + s // 2):
                    heading += rng.uniform(-0.75, 0.75)
                    step = rng.uniform(16, 30)
                    x += math.cos(heading) * step; y += math.sin(heading) * step
                    # Pull back toward the letter so it wraps rather than leaves.
                    x += (b[0] + b[2]) * 0.5 * 0.05 - x * 0.05
                    y += (b[1] + b[3]) * 0.5 * 0.05 - y * 0.05
                    pts.append((x, y))
                pts = smooth_curve(pts)
                width = rng.choice([3, 4, 5, 6]) + (1 if s >= 4 else 0)
                strand(d, pts, width, FIBRE + (rng.randint(210, 255),), FIBRE_HI + (140,))
        # Mass: at the late stages the fibre is a body, not a net -- dark clots in the lower half.
        if s >= 3:
            for _ in range([0, 0, 0, 1, 2, 3][s]):
                cx, cy = rng.uniform(b[0], b[2]), rng.uniform((b[1] + b[3]) * 0.62, b[3])
                r = rng.uniform(18, 34)
                clot = Image.new("RGBA", (W, H), (0, 0, 0, 0))
                cd = ImageDraw.Draw(clot)
                cd.ellipse([cx - r, cy - r * 0.7, cx + r, cy + r * 0.7], fill=FIBRE_MID + (200,))
                clot = clot.filter(ImageFilter.GaussianBlur(6))
                layer = Image.alpha_composite(layer, clot)
                d = ImageDraw.Draw(layer)
                for _ in range(4):   # strands out of the clot
                    pts = smooth_curve([(cx, cy), (cx + rng.uniform(-40, 40), cy + rng.uniform(-30, 30)), (cx + rng.uniform(-80, 80), cy + rng.uniform(-50, 50))])
                    strand(d, pts, 4, FIBRE + (240,), FIBRE_HI + (120,))
    # Shadow under the fibre so it sits on the plating rather than being drawn on it.
    shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    shadow.paste(Image.new("RGBA", (W, H), (8, 4, 12, 150)), (2, 3), layer.getchannel("A"))
    shadow = shadow.filter(ImageFilter.GaussianBlur(3))
    shadow.putalpha(ImageChops.multiply(shadow.getchannel("A"), union))
    interior = union.filter(ImageFilter.MinFilter(17)).filter(ImageFilter.GaussianBlur(4)).point(lambda v: 255 - int(v * 0.5))
    layer.putalpha(ImageChops.multiply(ImageChops.multiply(layer.getchannel("A"), grown), interior))
    return Image.alpha_composite(shadow, layer)


def prism(d, ax, ay, ang, length, half):
    """A slender six-sided crystal: two long faces lit differently, a faceted tip, a lit spine."""
    ux, uy = math.cos(ang), math.sin(ang)
    px, py = -uy * half, ux * half
    tip = (ax + ux * length, ay + uy * length)
    shoulder = 0.78
    left = [(ax + px, ay + py), (ax + px * 0.9 + ux * length * shoulder, ay + py * 0.9 + uy * length * shoulder), tip, (ax + ux * length * shoulder, ay + uy * length * shoulder), (ax, ay)]
    right = [(ax - px, ay - py), (ax - px * 0.9 + ux * length * shoulder, ay - py * 0.9 + uy * length * shoulder), tip, (ax + ux * length * shoulder, ay + uy * length * shoulder), (ax, ay)]
    d.polygon(left, fill=CRYSTAL_DARK + (205,))
    d.polygon(right, fill=CRYSTAL + (185,))
    d.line([(ax, ay), tip], fill=CRYSTAL_LIGHT + (150,), width=1)
    d.line([(ax + px, ay + py), tip], fill=CRYSTAL_LIGHT + (70,), width=1)


def crystals(masks, boxes, union):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    eroded = union.filter(ImageFilter.MinFilter(7))
    for i, b in enumerate(boxes):
        s = stage_of(i)
        if not b or s < 2:
            continue
        clusters = [0, 0, 1, 1, 2, 3][s]
        for _ in range(clusters):
            # Rooted on the glyph itself: a rim pixel of this letter, with the prisms pointing
            # along the plating's outward normal, and their bases set a little inside the edge so
            # they visibly come out of the ceramic. Bounding-box edges are not letter edges -- a
            # G's box top is empty air over its counter -- and the first bake floated shards there.
            root = None
            for _try in range(200):
                px, py = int(rng.uniform(b[0], b[2])), int(rng.uniform(b[1], b[3] - 30))
                if masks[i].getpixel((px, py)) > 0 and eroded.getpixel((px, py)) == 0:
                    root = (px, py)
                    break
            if not root:
                continue
            px, py = root
            gx = masks[i].getpixel((min(W - 1, px + 7), py)) - masks[i].getpixel((max(0, px - 7), py))
            gy = masks[i].getpixel((px, min(H - 1, py + 7))) - masks[i].getpixel((px, max(0, py - 7)))
            if gx == 0 and gy == 0:
                gx, gy = 0, 1
            base = math.atan2(-gy, -gx)          # outward: away from the glyph interior
            ax, ay = px - math.cos(base) * 9, py - math.sin(base) * 9
            for k in range(rng.randint(2, 4)):
                ang = base + math.radians(rng.uniform(-22, 22))
                length = rng.uniform(40, 80) * (1.0 + 0.22 * (s - 2)) * (1.4 if k == 0 else 1.0)
                half = rng.uniform(3, 5.5) * (1.0 + 0.08 * s)
                jx, jy = ax + rng.uniform(-5, 5), ay + rng.uniform(-5, 5)
                prism(d, jx, jy, ang, length, half)
    glow = layer.filter(ImageFilter.GaussianBlur(7))
    glow.putalpha(glow.getchannel("A").point(lambda v: int(v * 0.45)))
    return Image.alpha_composite(glow, layer)


def tendrils(boxes):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    for i, b in enumerate(boxes):
        s = stage_of(i)
        if not b or s < 3:
            continue
        for _ in range([0, 0, 0, 2, 3, 4][s]):
            x0 = rng.uniform(b[0] + 10, b[2] - 10); y0 = b[3] - rng.uniform(0, 10)
            length = rng.uniform(60, 120) * (1.0 + 0.3 * (s - 3))
            pts = smooth_curve([(x0, y0), (x0 + rng.uniform(-30, 30), y0 + length * 0.45), (x0 + rng.uniform(-60, 60), y0 + length)], 12)
            n = len(pts)
            for k in range(n - 1):
                w = max(1, int(7 - 6 * k / n))
                d.line([pts[k], pts[k + 1]], fill=FIBRE + (235,), width=w)
                if w >= 3:
                    d.line([(pts[k][0] - 1, pts[k][1]), (pts[k + 1][0] - 1, pts[k + 1][1])], fill=FIBRE_HI + (110,), width=1)
            if rng.random() < 0.6:   # a fork
                fx, fy = pts[n // 2]
                fork = smooth_curve([(fx, fy), (fx + rng.uniform(-35, 35), fy + 30), (fx + rng.uniform(-60, 60), fy + 70)], 8)
                d.line(fork, fill=FIBRE + (220,), width=2, joint="curve")
    return layer


def cores_and_haze(boxes, union):
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sil = Image.new("L", (W, H), 0)
    sd = ImageDraw.Draw(sil)
    for i, b in enumerate(boxes):
        s = stage_of(i)
        if b and s >= 3:
            sd.rectangle([b[0] - 20, b[1] - 30, b[2] + 20, b[3] + 60], fill=int(28 + 22 * (s - 3)))
    sil = ImageChops.multiply(sil, union.filter(ImageFilter.MaxFilter(41)).filter(ImageFilter.GaussianBlur(4)))
    sil = sil.filter(ImageFilter.GaussianBlur(34))
    haze = Image.new("RGBA", (W, H), HAZE + (0,))
    haze.putalpha(sil)
    layer = Image.alpha_composite(layer, haze)
    for i, b in enumerate(boxes):
        s = stage_of(i)
        if not b or s < 2:
            continue
        for _ in range([0, 0, 1, 2, 2, 3][s]):
            cx = rng.uniform(b[0] + 26, b[2] - 26); cy = rng.uniform(b[1] + 44, b[3] - 44)
            r = rng.uniform(3.5, 5.5) + 0.8 * s
            spot = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            dd = ImageDraw.Draw(spot)
            dd.ellipse([cx - r * 3.2, cy - r * 3.2, cx + r * 3.2, cy + r * 3.2], fill=CORE + (80,))
            spot = spot.filter(ImageFilter.GaussianBlur(r * 1.3))
            dd = ImageDraw.Draw(spot)
            dd.ellipse([cx - r * 1.5, cy - r * 1.5, cx + r * 1.5, cy + r * 1.5], fill=(24, 12, 34, 150))   # sunk socket
            dd.ellipse([cx - r, cy - r, cx + r, cy + r], fill=CORE + (220,))
            dd.ellipse([cx - r * 0.4, cy - r * 0.4, cx + r * 0.4, cy + r * 0.4], fill=(232, 212, 255, 235))
            layer = Image.alpha_composite(layer, spot)
    return layer


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    font = load_font()
    masks, boxes, union = glyph_masks(font)

    plate = ceramic_plate(union, masks, boxes)
    plate = Image.alpha_composite(plate, tendrils(boxes))
    plate = Image.alpha_composite(plate, fibres(masks, boxes, union))
    plate = Image.alpha_composite(plate, crystals(masks, boxes, union))
    glow = cores_and_haze(boxes, union)

    faint = glow.copy()
    faint.putalpha(faint.getchannel("A").point(lambda v: int(v * 0.4)))
    Image.alpha_composite(plate, faint).save(OUT_DIR / "Title_Ginnungagap_Plate.png")
    glow.save(OUT_DIR / "Title_Ginnungagap_Glow.png")

    preview = Image.new("RGBA", (W, H), (7, 10, 12, 255))
    preview = Image.alpha_composite(preview, plate)
    preview = Image.alpha_composite(preview, glow)
    preview.convert("RGB").save(OUT_DIR / "Title_Ginnungagap_Preview.png")
    print("wrote", OUT_DIR)


if __name__ == "__main__":
    main()
