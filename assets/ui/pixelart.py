"""Tiny indexed-colour canvas for procedural pixel art (no Pillow needed).

Index 0 is always the transparent colour magenta (#FF00FF), matching the
`-gTFF00FF` option used when converting with grit for NFLib.
"""
import math
import struct
import zlib

TRANSPARENT = (255, 0, 255)


class Palette:
    def __init__(self, colors):
        self.names = {"clear": 0}
        self.rgb = [TRANSPARENT]
        for name, rgb in colors.items():
            self.names[name] = len(self.rgb)
            self.rgb.append(rgb)
        assert len(self.rgb) <= 256

    def __getitem__(self, name):
        return self.names[name]


class Canvas:
    def __init__(self, width, height, palette, fill="clear"):
        self.w = width
        self.h = height
        self.pal = palette
        self.px = [[palette[fill]] * width for _ in range(height)]

    # --- basic access ----------------------------------------------------
    def set(self, x, y, color):
        x, y = int(x), int(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.px[y][x] = self.pal[color] if isinstance(color, str) else color

    def get(self, x, y):
        if 0 <= x < self.w and 0 <= y < self.h:
            return self.px[y][x]
        return 0

    # --- shapes ----------------------------------------------------------
    def rect(self, x0, y0, x1, y1, color):
        """Filled rectangle, inclusive corners."""
        for y in range(int(y0), int(y1) + 1):
            for x in range(int(x0), int(x1) + 1):
                self.set(x, y, color)

    def frame(self, x0, y0, x1, y1, color):
        for x in range(int(x0), int(x1) + 1):
            self.set(x, y0, color)
            self.set(x, y1, color)
        for y in range(int(y0), int(y1) + 1):
            self.set(x0, y, color)
            self.set(x1, y, color)

    def ellipse(self, cx, cy, rx, ry, color, y_min=None, y_max=None):
        for y in range(int(cy - ry - 1), int(cy + ry + 2)):
            if y_min is not None and y < y_min or y_max is not None and y > y_max:
                continue
            for x in range(int(cx - rx - 1), int(cx + rx + 2)):
                dx = (x + 0.5 - cx) / rx
                dy = (y + 0.5 - cy) / ry
                if dx * dx + dy * dy <= 1.0:
                    self.set(x, y, color)

    def circle(self, cx, cy, r, color):
        self.ellipse(cx, cy, r, r, color)

    def polygon(self, points, color):
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        for y in range(int(min(ys)), int(max(ys)) + 1):
            for x in range(int(min(xs)), int(max(xs)) + 1):
                if self._inside(points, x + 0.5, y + 0.5):
                    self.set(x, y, color)

    @staticmethod
    def _inside(points, x, y):
        inside = False
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            if (y0 > y) != (y1 > y):
                t = (y - y0) / (y1 - y0)
                if x < x0 + t * (x1 - x0):
                    inside = not inside
        return inside

    def line(self, x0, y0, x1, y1, color):
        steps = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(steps + 1):
            t = i / steps
            self.set(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), color)

    def arc(self, cx, cy, r, start_deg, end_deg, color):
        steps = int(abs(end_deg - start_deg) / 4) + 2
        for i in range(steps + 1):
            a = math.radians(start_deg + (end_deg - start_deg) * i / steps)
            self.set(round(cx + math.cos(a) * r), round(cy + math.sin(a) * r), color)

    def outline(self, color, x0=0, y0=0, x1=None, y1=None):
        """Draws color on transparent pixels that touch opaque ones (4-neighbourhood)."""
        x1 = self.w - 1 if x1 is None else x1
        y1 = self.h - 1 if y1 is None else y1
        target = self.pal[color]
        marks = []
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                if self.px[y][x] != 0:
                    continue
                for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                    if x0 <= nx <= x1 and y0 <= ny <= y1 and self.px[ny][nx] not in (0, target):
                        marks.append((x, y))
                        break
        for x, y in marks:
            self.px[y][x] = target

    def blit(self, other, ox, oy):
        for y in range(other.h):
            for x in range(other.w):
                if other.px[y][x] != 0:
                    self.px[oy + y][ox + x] = other.px[y][x]

    # --- output ----------------------------------------------------------
    def save_png(self, path):
        raw = bytearray()
        for row in self.px:
            raw.append(0)
            raw.extend(row)

        def chunk(kind, data):
            body = kind + data
            return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

        plte = b"".join(bytes(c) for c in self.pal.rgb)
        png = b"\x89PNG\r\n\x1a\n"
        png += chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 3, 0, 0, 0))
        png += chunk(b"PLTE", plte)
        png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        png += chunk(b"IEND", b"")
        with open(path, "wb") as f:
            f.write(png)


def sheet(frames, width, height, palette):
    """Stacks frames vertically (NFLib animated sprite layout)."""
    out = Canvas(width, height * len(frames), palette)
    for i, frame in enumerate(frames):
        out.blit(frame, 0, i * height)
    return out


def read_png_rgba(path):
    """Minimal PNG reader for 8-bit RGB/RGBA images (as written by Blender).

    Returns (width, height, rows) where rows[y][x] = (r, g, b, a).
    """
    with open(path, "rb") as f:
        data = f.read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n", "not a PNG"

    pos = 8
    width = height = 0
    color_type = 0
    idat = bytearray()
    while pos < len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        kind = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if kind == b"IHDR":
            width, height, depth, color_type = struct.unpack(">IIBB", body[:10])
            assert depth == 8 and color_type in (2, 6), "only 8-bit RGB/RGBA supported"
        elif kind == b"IDAT":
            idat.extend(body)
        elif kind == b"IEND":
            break

    channels = 4 if color_type == 6 else 3
    raw = zlib.decompress(bytes(idat))
    stride = width * channels
    rows = []
    previous = bytearray(stride)
    offset = 0
    for _ in range(height):
        filter_type = raw[offset]
        line = bytearray(raw[offset + 1:offset + 1 + stride])
        offset += 1 + stride
        for i in range(stride):
            left = line[i - channels] if i >= channels else 0
            up = previous[i]
            up_left = previous[i - channels] if i >= channels else 0
            if filter_type == 1:
                line[i] = (line[i] + left) & 0xFF
            elif filter_type == 2:
                line[i] = (line[i] + up) & 0xFF
            elif filter_type == 3:
                line[i] = (line[i] + ((left + up) >> 1)) & 0xFF
            elif filter_type == 4:
                p = left + up - up_left
                pa, pb, pc = abs(p - left), abs(p - up), abs(p - up_left)
                pred = left if pa <= pb and pa <= pc else (up if pb <= pc else up_left)
                line[i] = (line[i] + pred) & 0xFF
        rows.append([tuple(line[x * channels:x * channels + channels]) + ((255,) if channels == 3 else ())
                     for x in range(width)])
        previous = line
    return width, height, rows


def median_cut(colors, count):
    """Reduces a list of RGB tuples (with repetitions) to at most `count` colours."""
    boxes = [list(colors)]
    while len(boxes) < count:
        # Split the box with the widest channel range.
        best, best_range, best_channel = None, -1, 0
        for i, box in enumerate(boxes):
            if len(box) < 2:
                continue
            for c in range(3):
                values = [p[c] for p in box]
                r = max(values) - min(values)
                if r > best_range:
                    best, best_range, best_channel = i, r, c
        if best is None or best_range == 0:
            break
        box = sorted(boxes.pop(best), key=lambda p: p[best_channel])
        middle = len(box) // 2
        boxes.extend([box[:middle], box[middle:]])
    return [tuple(sum(p[c] for p in box) // len(box) for c in range(3)) for box in boxes if box]
