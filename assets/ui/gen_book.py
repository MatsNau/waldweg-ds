"""Composes the pages of the mushroom book (one 256x256 BG per species).

Layout (must match source/ui/BookView.cpp, text is drawn by the game):
- rows 1-3: name and edibility (text)
- three 72x72 illustrations at x = 12 / 92 / 172, y = 40
- page arrows for L / R in the bottom corners

Run: python assets/ui/gen_book.py <render dir> <out dir>
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pixelart import Canvas, Palette, median_cut, read_png_rgba  # noqa: E402

PAGES = ["steinpilz", "satansroehrling", "champignon", "knollenblaetterpilz",
         "pfifferling", "fliegenpilz", "oelbaum_trichterling"]

IMAGE_SIZE = 72
IMAGE_X = (12, 92, 172)
IMAGE_Y = 40
MAX_IMAGE_COLORS = 200

UI_COLORS = {
    "parchment": (236, 216, 172),
    "parchment_speck": (226, 204, 156),
    "parchment_dark": (212, 186, 136),
    "edge": (120, 80, 48),
    "edge_light": (176, 132, 86),
    "arrow": (120, 80, 48),
    "arrow_light": (200, 164, 112),
}


def to_ds(rgb):
    """Snap to the 15-bit colours the DS can show."""
    return tuple((c >> 3) * 255 // 31 for c in rgb)


# --- Drawing style ---------------------------------------------------------------
# Cel shading from two renders (flat colours + smooth light), warm pastel colours,
# dark brown ink outline around the silhouette and softer lines between colour areas.

INK = (72, 44, 30)
INK_SOFT = (132, 92, 62)
CREAM = (255, 246, 222)
SHADOW_TINT = (0.84, 0.76, 0.72)  # warm brownish shadows
EDGE_THRESHOLD = 90


def luminance(rgb):
    return rgb[0] * 0.3 + rgb[1] * 0.59 + rgb[2] * 0.11


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def stylize(flat, shade):
    height = len(flat)
    width = len(flat[0])
    opaque = [[flat[y][x][3] >= 128 for x in range(width)] for y in range(height)]

    def is_opaque(x, y):
        return 0 <= x < width and 0 <= y < height and opaque[y][x]

    color = [[None] * width for _ in range(height)]
    outline = [[False] * width for _ in range(height)]
    inner = [[False] * width for _ in range(height)]

    for y in range(height):
        for x in range(width):
            neighbours = ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
            if not opaque[y][x]:
                # Outer half of the silhouette line.
                outline[y][x] = any(is_opaque(nx, ny) for nx, ny in neighbours)
                continue

            if not all(is_opaque(nx, ny) for nx, ny in neighbours):
                outline[y][x] = True

            base = flat[y][x][:3]
            for nx, ny in ((x + 1, y), (x, y + 1)):
                if is_opaque(nx, ny):
                    other = flat[ny][nx][:3]
                    if sum(abs(base[i] - other[i]) for i in range(3)) > EDGE_THRESHOLD:
                        inner[y][x] = True

            # Brightness of the lit render relative to the flat colour picks a band.
            ratio = luminance(shade[y][x][:3]) / max(luminance(base), 1.0)
            pastel = mix(base, CREAM, 0.12)
            if ratio < 0.62:
                c = tuple(int(pastel[i] * SHADOW_TINT[i]) for i in range(3))
            elif ratio < 0.92:
                c = tuple(int(v * 0.92) for v in pastel)
            elif ratio > 1.15:
                c = mix(pastel, CREAM, 0.45)  # soft highlight
            else:
                c = pastel
            color[y][x] = c

    # Downsample 2x2 -> final picture size, lines win over colours.
    rows = []
    for y in range(height // 2):
        row = []
        for x in range(width // 2):
            block = [(x * 2 + dx, y * 2 + dy) for dy in (0, 1) for dx in (0, 1)]
            outlines = sum(outline[by][bx] for bx, by in block)
            inners = sum(inner[by][bx] for bx, by in block)
            colors = [color[by][bx] for bx, by in block if color[by][bx] is not None]
            if outlines >= 2:
                row.append(INK + (255,))
            elif inners >= 2:
                row.append(INK_SOFT + (255,))
            elif len(colors) >= 2:
                row.append(tuple(sum(c[i] for c in colors) // len(colors) for i in range(3)) + (255,))
            else:
                row.append((0, 0, 0, 0))
        rows.append(row)
    return rows


def load_images(render_dir, key):
    images = []
    for index in range(3):
        _, _, flat = read_png_rgba(os.path.join(render_dir, f"{key}_{index}_flat.png"))
        _, _, shade = read_png_rgba(os.path.join(render_dir, f"{key}_{index}_shade.png"))
        images.append(stylize(flat, shade))
    return images


def compose(key, render_dir, rng):
    images = load_images(render_dir, key)

    # Quantise all opaque illustration pixels of the page together.
    opaque = [to_ds(p[:3]) for rows in images for row in rows for p in row if p[3] >= 128]
    unique = sorted(set(opaque))
    colors = unique if len(unique) <= MAX_IMAGE_COLORS else median_cut(opaque, MAX_IMAGE_COLORS)

    palette_colors = dict(UI_COLORS)
    for i, c in enumerate(colors):
        palette_colors[f"img{i}"] = c
    palette = Palette(palette_colors)
    cache = {}

    def nearest(rgb):
        if rgb not in cache:
            best = min(range(len(colors)),
                       key=lambda i: sum((a - b) ** 2 for a, b in zip(colors[i], rgb)))
            cache[rgb] = palette[f"img{best}"]
        return cache[rgb]

    page = Canvas(256, 256, palette)
    page.rect(0, 0, 255, 191, "parchment")
    for _ in range(900):
        page.set(rng.randint(4, 251), rng.randint(4, 187), "parchment_speck")

    # Page border with a thin inner line.
    page.frame(0, 0, 255, 191, "edge")
    page.frame(1, 1, 254, 190, "edge")
    page.frame(4, 4, 251, 187, "edge_light")

    # Title underline.
    page.rect(24, 28, 231, 28, "parchment_dark")

    for rows, x0 in zip(images, IMAGE_X):
        page.rect(x0 - 2, IMAGE_Y - 2, x0 + IMAGE_SIZE + 1, IMAGE_Y + IMAGE_SIZE + 1, "parchment_dark")
        page.frame(x0 - 2, IMAGE_Y - 2, x0 + IMAGE_SIZE + 1, IMAGE_Y + IMAGE_SIZE + 1, "edge_light")
        for y in range(IMAGE_SIZE):
            for x in range(IMAGE_SIZE):
                r, g, b, a = rows[y][x]
                if a >= 128:
                    page.px[IMAGE_Y + y][x0 + x] = nearest(to_ds((r, g, b)))

    # Page arrows (L bottom left, R bottom right).
    page.polygon([(12, 176), (22, 170), (22, 182)], "arrow")
    page.polygon([(243, 176), (233, 170), (233, 182)], "arrow")
    return page


def main():
    render_dir = sys.argv[1]
    target = sys.argv[2]
    os.makedirs(target, exist_ok=True)
    rng = random.Random(20260915)
    for number, key in enumerate(PAGES):
        page = compose(key, render_dir, rng)
        path = os.path.join(target, f"page{number}.png")
        page.save_png(path)
        print(f"wrote {path} ({len(page.pal.rgb)} colours)")


if __name__ == "__main__":
    main()
