"""Punches the orange placeholder areas out of the packaging template.

Run: python assets/cover/make_overlay.py [template.png] [overlay.png]

The result is the template as an RGBA PNG that is laid over the cover art:
back and front cover become transparent, everything else (spine, logos, the
black info bar) stays exactly as it was. Anti-aliased edges are un-mixed from
the orange so no orange fringe remains. The orange inside the "DS GAME MAKER"
pill turns into parchment, so the logo stays readable on top of a painting.
"""
import os
import struct
import sys
import zlib
from collections import deque

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "ui"))

from pixelart import read_png_rgba  # noqa: E402

ORANGE = np.array([255, 50, 0], np.float32)
PARCHMENT = np.array([244, 230, 200], np.float32)

# Seed points inside the orange areas (template pixel coordinates).
SEEDS_CUT = [(10, 10), (10, 3290)]       # (y, x): back cover, front cover
PILL_BOX = (3040, 1270, 3270, 1332)    # x0, y0, x1, y1 of the logo pill


def is_orange(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (r > 200) & (g < 110) & (b < 60)


def flood(mask, seeds):
    h, w = mask.shape
    out = np.zeros_like(mask)
    queue = deque()
    for y, x in seeds:
        if mask[y, x] and not out[y, x]:
            out[y, x] = True
            queue.append((y, x))
    while queue:
        y, x = queue.popleft()
        for ny, nx in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
            if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not out[ny, nx]:
                out[ny, nx] = True
                queue.append((ny, nx))
    return out


def dilate(mask, steps):
    out = mask.copy()
    for _ in range(steps):
        grown = out.copy()
        grown[1:] |= out[:-1]
        grown[:-1] |= out[1:]
        grown[:, 1:] |= out[:, :-1]
        grown[:, :-1] |= out[:, 1:]
        out = grown
    return out


def unmix(rgb):
    """Splits a pixel into (foreground colour, coverage) over the orange.
    Orange -> white raises blue, orange -> black lowers red."""
    alpha = np.clip(np.maximum(rgb[..., 2] / 255.0, 1.0 - rgb[..., 0] / 255.0), 0.0, 1.0)
    safe = np.maximum(alpha, 1e-3)[..., None]
    fg = np.clip((rgb - (1.0 - alpha[..., None]) * ORANGE) / safe, 0, 255)
    return fg, alpha


def save_rgba(path, a):
    h, w, _ = a.shape
    raw = b"".join(b"\x00" + a[y].tobytes() for y in range(h))

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def main():
    src = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "template.png")
    dst = sys.argv[2] if len(sys.argv) > 2 else os.path.join(HERE, "build", "template_overlay.png")
    w, h, rows = read_png_rgba(src)
    a = np.array(rows, np.float32)
    rgb = a[..., :3]
    orange = is_orange(a)

    cut = flood(orange, SEEDS_CUT)
    x0, y0, x1, y1 = PILL_BOX
    fill = np.zeros_like(orange)
    fill[y0:y1, x0:x1] = orange[y0:y1, x0:x1]
    fg, cover = unmix(rgb)

    out = a.copy()
    out[..., 3] = 255
    # Cut areas: fully transparent inside, un-mixed coverage on the 2 px rim.
    rim = dilate(cut, 2) & ~cut
    out[cut, 3] = 0
    out[rim, :3] = fg[rim]
    out[rim, 3] = np.minimum(cover[rim], a[rim, 3] / 255.0) * 255
    # Logo pill: orange becomes parchment, rim pixels re-mixed onto parchment.
    frim = dilate(fill, 2) & ~fill
    out[fill, :3] = PARCHMENT
    k = cover[frim][:, None]
    out[frim, :3] = fg[frim] * k + PARCHMENT * (1 - k)

    os.makedirs(os.path.dirname(dst), exist_ok=True)
    save_rgba(dst, np.round(out).astype(np.uint8))
    print("overlay", dst, w, "x", h, "cut", int(cut.sum()), "rim", int(rim.sum()), "pill", int(fill.sum()))


if __name__ == "__main__":
    main()
