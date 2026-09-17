"""Builds a texture atlas from the patched NFLib font for 3D text rendering.

16 x 8 glyph grid (128 x 64 px): glyph pixels white, background transparent
(magenta, converted to alpha 0 by grit). Slot n sits at column n % 16, row n // 16,
matching TextDE_FontSlot() in source/ui/text_de.cpp.

Run: python assets/fonts/make_font_texture.py <out.png>
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "assets" / "ui"))

from pixelart import Canvas, Palette  # noqa: E402

FONT = ROOT / "nitrofiles" / "fnt" / "default.fnt"
GLYPHS = 128
COLUMNS = 16
TILE = 8

# Slots 114-127 of the NFLib font are empty. The last one holds the "A in a
# circle" badge that marks a message the player can skip with A (see
# TextDE_SlotButtonA and TopTextService::Draw).
BUTTON_A_SLOT = 127
BUTTON_A = [
    "..####..",
    ".#....#.",
    "#..##..#",
    "#.#..#.#",
    "#.####.#",
    "#.#..#.#",
    ".#....#.",
    "..####..",
]


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "assets" / "build" / "font.png"
    font = FONT.read_bytes()
    palette = Palette({"white": (255, 255, 255)})
    canvas = Canvas(COLUMNS * TILE, (GLYPHS // COLUMNS) * TILE, palette)

    for slot in range(GLYPHS):
        ox = (slot % COLUMNS) * TILE
        oy = (slot // COLUMNS) * TILE
        for y in range(TILE):
            for x in range(TILE):
                if font[slot * TILE * TILE + y * TILE + x]:
                    canvas.set(ox + x, oy + y, "white")

    ox = (BUTTON_A_SLOT % COLUMNS) * TILE
    oy = (BUTTON_A_SLOT // COLUMNS) * TILE
    for y, line in enumerate(BUTTON_A):
        for x, pixel in enumerate(line):
            if pixel == "#":
                canvas.set(ox + x, oy + y, "white")

    target.parent.mkdir(parents=True, exist_ok=True)
    canvas.save_png(str(target))
    print(f"wrote {target}")


main()
