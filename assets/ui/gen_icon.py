"""Generates the DS menu icon (32x32, 16 colours): a fly agaric in the grass.

Run: python assets/ui/gen_icon.py <out.png> [preview.png]

Writes an RGBA PNG with at most 15 opaque colours; ndstool converts it to
the 4-bit banner icon. The optional preview is the same image scaled up 8x.
"""
import math
import os
import struct
import sys
import zlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pixelart import Canvas, Palette  # noqa: E402

SIZE = 32

PALETTE = Palette({
    "ink": (46, 30, 20),
    "red": (214, 48, 32),
    "red_dark": (150, 28, 24),
    "red_light": (246, 112, 78),
    "spot": (252, 246, 232),
    "spot_shade": (214, 196, 180),
    "gills": (206, 178, 128),
    "stem": (240, 230, 208),
    "stem_shade": (196, 176, 146),
    "grass": (116, 148, 54),
    "grass_dark": (64, 100, 44),
    "leaf_orange": (232, 128, 30),
    "leaf_yellow": (240, 186, 60),
})
assert len(PALETTE.rgb) <= 16

# Cap: upper half of an ellipse, lit from the top left.
CAP_CX, CAP_CY, CAP_RX, CAP_RY = 16.0, 16.0, 14.5, 13.0
SPOTS = [(10.0, 9.0, 2.4), (17.5, 5.5, 2.0), (23.0, 10.5, 2.5), (15.0, 12.5, 1.8),
         (6.0, 14.0, 1.5), (27.0, 14.5, 1.3), (20.5, 14.5, 1.3)]


def draw_cap(c):
    for y in range(SIZE):
        for x in range(SIZE):
            nx = (x + 0.5 - CAP_CX) / CAP_RX
            ny = (y + 0.5 - CAP_CY) / CAP_RY
            if y + 0.5 > CAP_CY or nx * nx + ny * ny > 1.0:
                continue
            # Light from the top left: distance to a shifted centre.
            lx = (x + 0.5 - (CAP_CX - 4.0)) / CAP_RX
            ly = (y + 0.5 - (CAP_CY - 5.0)) / CAP_RY
            lit = lx * lx + ly * ly
            color = "red_dark" if lit > 0.95 else "red"
            c.set(x, y, color)
    # Highlight arc near the top left of the dome.
    for deg in range(200, 256, 3):
        a = math.radians(deg)
        c.set(round(CAP_CX + math.cos(a) * CAP_RX * 0.8), round(CAP_CY + math.sin(a) * CAP_RY * 0.8), "red_light")
    for cx, cy, r in SPOTS:
        c.circle(cx, cy, r, "spot")
        # Shaded lower-right edge of each spot.
        for y in range(int(cy - r - 1), int(cy + r + 2)):
            for x in range(int(cx - r - 1), int(cx + r + 2)):
                if c.get(x, y) != PALETTE["spot"]:
                    continue
                if (x + 0.5 - cx) + (y + 0.5 - cy) > r * 0.9:
                    c.set(x, y, "spot_shade")
    # Underside with gills.
    c.ellipse(CAP_CX, CAP_CY + 0.5, CAP_RX - 1.5, 1.6, "gills", y_min=int(CAP_CY))


def draw_stem(c):
    c.polygon([(12.5, 17), (19.5, 17), (20.5, 24), (22.5, 27), (9.5, 27), (11.5, 24)], "stem")
    for y in range(17, 28):
        for x in range(18, 24):
            if c.get(x, y) == PALETTE["stem"]:
                c.set(x, y, "stem_shade")
    # Ring (skirt) below the cap.
    c.ellipse(16, 20, 5.2, 1.0, "stem")
    c.line(12, 21, 20, 21, "stem_shade")
    # Bulb.
    c.ellipse(16, 26.5, 6.5, 2.0, "stem")
    c.line(19, 27, 21, 27, "stem_shade")


def draw_ground(c):
    c.ellipse(16, 29.0, 13.0, 1.6, "grass")
    c.line(5, 30, 27, 30, "grass_dark")
    # Blades in front of the bulb.
    for x, h, color in ((6, 3, "grass"), (8, 4, "grass_dark"), (10, 3, "grass"),
                        (21, 3, "grass"), (23, 4, "grass_dark"), (25, 2, "grass")):
        c.line(x, 29, x + (1 if x > 16 else -1) * (h // 3), 29 - h, color)
    # A fallen leaf on the right.
    c.polygon([(22, 28), (26, 25.5), (29, 27), (25, 29.5)], "leaf_orange")
    c.line(23, 28, 28, 27, "leaf_yellow")


def build():
    c = Canvas(SIZE, SIZE, PALETTE)
    draw_ground(c)
    draw_stem(c)
    draw_cap(c)
    c.outline("ink")
    return c


def save_png_rgba(canvas, path):
    """RGBA PNG; index 0 becomes fully transparent. ndstool builds its own
    palette from the colours, so transparency has to be real alpha (it treats
    a magenta palette entry in a BMP as an ordinary colour)."""
    raw = bytearray()
    for row in canvas.px:
        raw.append(0)
        for i in row:
            raw.extend(canvas.pal.rgb[i] + ((0,) if i == 0 else (255,)))

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def scaled(canvas, factor):
    out = Canvas(canvas.w * factor, canvas.h * factor, canvas.pal)
    for y in range(out.h):
        for x in range(out.w):
            out.px[y][x] = canvas.px[y // factor][x // factor]
    return out


def main():
    icon = build()
    save_png_rgba(icon, sys.argv[1])
    if len(sys.argv) > 2:
        scaled(icon, 8).save_png(sys.argv[2])
    print("icon", sys.argv[1], len(PALETTE.rgb), "colours")


if __name__ == "__main__":
    main()
