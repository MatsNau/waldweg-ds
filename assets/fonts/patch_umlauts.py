"""Draws German glyphs into an NFLib 8x8 font (raw 8 bpp tiles, 256x256).

NF_WriteText() maps some Latin-1 bytes to slots 96-113. The slots used here must
match MapCodepoint() in source/ui/text_de.cpp.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "assets" / "fonts" / "base_default.fnt"
DST = ROOT / "nitrofiles" / "fnt" / "default.fnt"

TILE = 8
FIRST_CHAR = 32
USED_GLYPHS = 128

SLOT_AE_LOWER = 105  # á
SLOT_OE_LOWER = 108  # ó
SLOT_UE_LOWER = 111  # ü
SLOT_AE_UPPER = 100  # Á
SLOT_OE_UPPER = 103  # Ó
SLOT_UE_UPPER = 104  # Ú
SLOT_SZ = 110        # ï

UPPER_GLYPHS = {
    SLOT_AE_UPPER: [
        "..#..#..",
        "........",
        "...##...",
        "..#..#..",
        "..####..",
        "..#..#..",
        "..#..#..",
        "........",
    ],
    SLOT_OE_UPPER: [
        "..#..#..",
        "........",
        "...##...",
        "..#..#..",
        "..#..#..",
        "..#..#..",
        "...##...",
        "........",
    ],
    SLOT_UE_UPPER: [
        "..#..#..",
        "........",
        "..#..#..",
        "..#..#..",
        "..#..#..",
        "..#..#..",
        "...##...",
        "........",
    ],
    SLOT_SZ: [
        "........",
        "...##...",
        "..#..#..",
        "..#.#...",
        "..#..#..",
        "..#..#..",
        "..#.#...",
        "........",
    ],
}


def tile_offset(slot):
    return slot * TILE * TILE


def read_glyph(font, char):
    start = tile_offset(ord(char) - FIRST_CHAR)
    return [list(font[start + row * TILE:start + (row + 1) * TILE]) for row in range(TILE)]


def write_glyph(font, slot, rows):
    start = tile_offset(slot)
    for r, row in enumerate(rows):
        for c, pixel in enumerate(row):
            font[start + r * TILE + c] = pixel


def parse(rows):
    return [[1 if ch == "#" else 0 for ch in row] for row in rows]


def with_dots(rows):
    rows = [row[:] for row in rows]
    rows[0] = [0] * TILE
    rows[1] = [0, 0, 1, 0, 0, 1, 0, 0]
    rows[2] = [0] * TILE
    return rows


def show(rows):
    return "\n".join("".join("#" if p else "." for p in row) for row in rows)


def main():
    font = bytearray(SRC.read_bytes())

    write_glyph(font, SLOT_AE_LOWER, with_dots(read_glyph(font, "a")))
    write_glyph(font, SLOT_OE_LOWER, with_dots(read_glyph(font, "o")))
    write_glyph(font, SLOT_UE_LOWER, with_dots(read_glyph(font, "u")))
    for slot, rows in UPPER_GLYPHS.items():
        write_glyph(font, slot, parse(rows))

    DST.parent.mkdir(parents=True, exist_ok=True)
    # Only the first 128 glyphs are used (NFLib reads 127, the font texture 128).
    DST.write_bytes(font[:USED_GLYPHS * TILE * TILE])

    for name, slot in [("ä", SLOT_AE_LOWER), ("ö", SLOT_OE_LOWER), ("ü", SLOT_UE_LOWER),
                       ("Ä", SLOT_AE_UPPER), ("Ö", SLOT_OE_UPPER), ("Ü", SLOT_UE_UPPER),
                       ("ß", SLOT_SZ)]:
        start = tile_offset(slot)
        rows = [font[start + r * TILE:start + (r + 1) * TILE] for r in range(TILE)]
        print(f"{name} (slot {slot})\n{show(rows)}")
    print(f"written {DST.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
