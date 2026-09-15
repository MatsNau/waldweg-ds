"""Composes the upper half of the final picture: sunrise sky, sun, the drawn
distant scenery (render_ending.py, same drawing style as the book) and a haze
band at the bottom that continues seamlessly into the 3D screen below.

Run: python assets/ui/gen_ending.py <render dir> <out dir>
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gen_book import mix, stylize, to_ds  # noqa: E402
from pixelart import Canvas, Palette, median_cut, read_png_rgba  # noqa: E402

# Morning haze on the distant hills.
HAZE = (214, 181, 140)
SKY = [(0, (64, 72, 132)), (70, (206, 126, 124)), (130, (250, 186, 120)), (192, HAZE)]
SUN_CENTRE = (74, 92)
SUN_RADIUS = 18
# 2x2 ordered dither on the sky softens the 15-bit colour steps.
DITHER = ((0, 4), (6, 2))
MAX_COLORS = 240


def sky_color(y):
    for (y0, c0), (y1, c1) in zip(SKY, SKY[1:]):
        if y0 <= y <= y1:
            return mix(c0, c1, (y - y0) / (y1 - y0))
    return SKY[-1][1]


def main():
    render_dir, target = sys.argv[1], sys.argv[2]
    os.makedirs(target, exist_ok=True)

    _, _, flat = read_png_rgba(os.path.join(render_dir, "ending_flat.png"))
    _, _, shade = read_png_rgba(os.path.join(render_dir, "ending_shade.png"))
    scenery = stylize(flat, shade)  # 256x192 RGBA

    pixels = []
    for y in range(192):
        row = []
        for x in range(256):
            color = sky_color(y)
            offset = DITHER[y % 2][x % 2]
            color = tuple(min(255, c + offset) for c in color)
            dx, dy = x - SUN_CENTRE[0], y - SUN_CENTRE[1]
            distance = (dx * dx + dy * dy) ** 0.5
            if distance <= SUN_RADIUS:
                color = (255, 240, 170)
            elif distance <= SUN_RADIUS + 14:
                color = mix(color, (255, 226, 150), 0.55 * (1 - (distance - SUN_RADIUS) / 14))

            r, g, b, a = scenery[y][x]
            if a:
                # A little morning haze on the far hills, none in the valley.
                haze = 0.3 * max(0.0, min(1.0, (128 - y) / 40))
                color = mix((r, g, b), HAZE, haze)
            row.append(to_ds(color))
        pixels.append(row)

    colors = sorted({c for row in pixels for c in row})
    if len(colors) > MAX_COLORS:
        colors = median_cut([c for row in pixels for c in row], MAX_COLORS)
    palette = Palette({f"c{i}": c for i, c in enumerate(colors)})
    lookup = {}

    def index(c):
        if c not in lookup:
            best = min(range(len(colors)), key=lambda i: sum((a - b) ** 2 for a, b in zip(colors[i], c)))
            lookup[c] = palette[f"c{best}"]
        return lookup[c]

    page = Canvas(256, 256, palette, fill="c0")
    for y in range(192):
        for x in range(256):
            page.px[y][x] = index(pixels[y][x])
    page.save_png(os.path.join(target, "ending_sky.png"))
    print(f"wrote ending_sky.png ({len(colors)} colours)")


main()
