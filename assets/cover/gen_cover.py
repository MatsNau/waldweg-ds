"""Draws the DS case cover ("NiKnight im Pilzwald") as SVG and renders it.

Run: python assets/cover/gen_cover.py [out_dir]
     python assets/cover/gen_cover.py --front-art front.png --back-art back.png [out_dir]

Without art images the whole picture is drawn as vector art (autumn forest,
Nina & Mats, mushrooms). With --front-art/--back-art (e.g. Blender renders)
those images fill the covers instead; title, blurb and the template overlay
stay the same. Needs build/template_overlay.png (make_overlay.py) and
Inkscape with the fonts from fonts/ (copied to %APPDATA%/inkscape/fonts).
"""
import argparse
import math
import os
import random
import subprocess

from fontTools.ttLib import TTFont

HERE = os.path.dirname(os.path.abspath(__file__))
INKSCAPE = os.environ.get("INKSCAPE", r"C:\Program Files\Inkscape\bin\inkscape.exe")

W, H = 3307, 1370
BACK = (0, 0, 1535, 870)          # x0, y0, x1, y1 (template pixels, ~300 dpi)
FRONT = (1988, 0, W, H)
FRONT_CX = 2663                   # centre of the visible front (right of the spine curve)
HORIZON = 800
BLURB_BOX = (70, 56, 1110, 836)  # parchment panel on the back

INK = "#3b2618"
SW = 7                            # outline width

TITLE_FONT = "Fredoka"
BODY_FONT = "Varela Round"

TREE_COLORS = {
    "orange": ("#e8801e", "#b85a18", "#f7aa42"),
    "red": ("#c4401e", "#8e2c16", "#e46a3c"),
    "yellow": ("#f0ba3c", "#c88a26", "#fadb78"),
    "brown": ("#a8602a", "#7c421c", "#c8843e"),
}
LEAF_COLORS = ["#e8801e", "#c4401e", "#f0ba3c", "#a8602a"]

BLURB_TITLE = "NiKnight im Pilzwald"
BLURB = [
    "Nachdem Nina Mats vor den Geistern gerettet hat, wartet schon das nächste "
    "Abenteuer: den Weg nach Hause finden. Doch das ist schwieriger als gedacht – "
    "bald wird es dunkel, und außerdem sprießen überall diese Pilze aus dem Boden …",
]


# --- SVG building blocks ----------------------------------------------------
class Svg:
    def __init__(self):
        self.defs = []
        self.body = []
        self.ids = 0

    def uid(self, prefix):
        self.ids += 1
        return f"{prefix}{self.ids}"

    def add(self, s):
        self.body.append(s)

    def text(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n<defs>\n' + "\n".join(self.defs) +
                "\n</defs>\n" + "\n".join(self.body) + "\n</svg>\n")


def f(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def circle(cx, cy, r, fill, extra=""):
    return f'<circle cx="{f(cx)}" cy="{f(cy)}" r="{f(r)}" fill="{fill}" {extra}/>'


def ellipse(cx, cy, rx, ry, fill, extra=""):
    return f'<ellipse cx="{f(cx)}" cy="{f(cy)}" rx="{f(rx)}" ry="{f(ry)}" fill="{fill}" {extra}/>'


def path(d, fill, extra=""):
    return f'<path d="{d}" fill="{fill}" {extra}/>'


def outlined(d, fill, sw=SW, extra=""):
    return (f'<path d="{d}" fill="{fill}" stroke="{INK}" stroke-width="{f(sw)}" '
            f'stroke-linejoin="round" stroke-linecap="round" {extra}/>')


def radial(svg, stops, cx=0.5, cy=0.5, r=0.5):
    gid = svg.uid("rg")
    s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
    svg.defs.append(f'<radialGradient id="{gid}" cx="{cx}" cy="{cy}" r="{r}">{s}</radialGradient>')
    return f"url(#{gid})"


def linear(svg, stops, x1=0, y1=0, x2=0, y2=1):
    gid = svg.uid("lg")
    s = "".join(f'<stop offset="{o}" stop-color="{c}" stop-opacity="{a}"/>' for o, c, a in stops)
    svg.defs.append(f'<linearGradient id="{gid}" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">{s}</linearGradient>')
    return f"url(#{gid})"


def bumps(svg, circles, colors, sw=SW, shift=(0.16, 0.2), light=True):
    """A cluster of round bumps with one outline around the silhouette and
    cel shading per bump: shade colour below, base colour shifted up-left,
    a small highlight on top. circles: [(cx, cy, r)]."""
    base, shade, hi = colors
    clip = svg.uid("clip")
    svg.defs.append(f'<clipPath id="{clip}">' + "".join(circle(x, y, r, "#000") for x, y, r in circles) + "</clipPath>")
    out = [circle(x, y, r, INK, f'stroke="{INK}" stroke-width="{f(sw * 2)}"') for x, y, r in circles]
    out += [circle(x, y, r, shade) for x, y, r in circles]
    g = [f'<g clip-path="url(#{clip})">']
    g += [circle(x - r * shift[0], y - r * shift[1], r * 0.93, base) for x, y, r in circles]
    if light:
        g += [circle(x - r * 0.34, y - r * 0.4, r * 0.4, hi) for x, y, r in circles if r > 14]
    g.append("</g>")
    return "".join(out + g)


def blob_circles(rng, cx, cy, rx, ry, size=0.36, density=1.0):
    """Circles that fill an ellipse and make a bumpy rim."""
    circles = []
    m = min(rx, ry)
    n = max(7, int((rx + ry) / (m * size) * 1.1 * density))
    for i in range(n):
        a = 2 * math.pi * (i + rng.uniform(-0.25, 0.25)) / n
        r = m * rng.uniform(size * 0.8, size * 1.15)
        circles.append((cx + math.cos(a) * (rx - r * 0.85), cy + math.sin(a) * (ry - r * 0.85), r))
    for _ in range(int(n * 0.6)):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0, 0.45)
        circles.append((cx + math.cos(a) * rx * d, cy + math.sin(a) * ry * d, m * rng.uniform(0.45, 0.6)))
    # Draw order top-down so lower bumps overlap upper ones (reads as volume).
    return sorted(circles, key=lambda c: c[1])


# --- Forest -------------------------------------------------------------------
def sky(svg, x0, x1, sun):
    fill = linear(svg, [(0, "#f3c98a", 1), (0.45, "#f7c37c", 1), (0.8, "#f4a868", 1), (1, "#f09a60", 1)])
    svg.add(f'<rect x="{x0}" y="0" width="{x1 - x0}" height="{HORIZON + 40}" fill="{fill}"/>')
    glow = radial(svg, [(0, "#fff4c8", 1), (0.35, "#ffe2a0", 0.75), (1, "#f7c37c", 0)])
    sx, sy = sun
    sr = 420
    svg.add(ellipse(sx, sy, sr * 1.6, sr, glow))
    svg.add(circle(sx, sy + 40, 70, "#fff6d8", 'opacity="0.9"'))


def treeline(svg, rng, x0, x1, y, h, r0, r1, color, fir_share=0.25):
    """Distant forest silhouette: bumpy crowns plus a few pointed firs."""
    parts = [f'<rect x="{x0}" y="{f(y - h * 0.3)}" width="{x1 - x0}" height="{f(HORIZON + 80 - y + h * 0.3)}" fill="{color}"/>']
    x = x0 - r1
    while x < x1 + r1:
        r = rng.uniform(r0, r1)
        top = y - h * rng.uniform(0.55, 1.0)
        if rng.random() < fir_share:
            parts.append(path(f"M{f(x - r * 0.8)},{f(y)} L{f(x)},{f(top - r)} L{f(x + r * 0.8)},{f(y)} Z", color))
        else:
            parts.append(circle(x, top, r, color))
            parts.append(f'<rect x="{f(x - r)}" y="{f(top)}" width="{f(2 * r)}" height="{f(y - top + 5)}" fill="{color}"/>')
        x += r * rng.uniform(1.0, 1.5)
    svg.add("".join(parts))


def trunk(x, base, top, w, color="#5c3a24"):
    d = (f"M{f(x - w * 0.62)},{f(base)} Q{f(x - w * 0.45)},{f(base - 20)} {f(x - w * 0.42)},{f(base - 60)} "
         f"L{f(x - w * 0.34)},{f(top)} L{f(x + w * 0.34)},{f(top)} L{f(x + w * 0.42)},{f(base - 60)} "
         f"Q{f(x + w * 0.45)},{f(base - 20)} {f(x + w * 0.62)},{f(base)} Z")
    shade = (f"M{f(x + w * 0.1)},{f(top)} L{f(x + w * 0.34)},{f(top)} L{f(x + w * 0.42)},{f(base - 60)} "
             f"Q{f(x + w * 0.45)},{f(base - 20)} {f(x + w * 0.62)},{f(base)} L{f(x + w * 0.2)},{f(base)} Z")
    return outlined(d, color) + path(shade, "#43291a")


def tree(svg, rng, x, base, height, kind, sw=SW):
    colors = TREE_COLORS[kind]
    crown_ry = height * 0.36
    crown_rx = crown_ry * rng.uniform(0.95, 1.15)
    crown_cy = base - height + crown_ry
    w = height * 0.09
    s = trunk(x, base, crown_cy + crown_ry * 0.4, w)
    # Two branches into the crown.
    for side in (-1, 1):
        bx = x + side * w * 0.25
        s += (f'<path d="M{f(bx)},{f(crown_cy + crown_ry * 0.75)} Q{f(bx + side * crown_rx * 0.25)},{f(crown_cy + crown_ry * 0.45)} '
              f'{f(bx + side * crown_rx * 0.45)},{f(crown_cy + crown_ry * 0.2)}" fill="none" stroke="{INK}" '
              f'stroke-width="{f(w * 0.35 + sw)}" stroke-linecap="round"/>')
    s += bumps(svg, blob_circles(rng, x, crown_cy, crown_rx, crown_ry), colors, sw)
    svg.add(s)


def fir(svg, x, base, height, sw=SW, colors=("#34543a", "#26402e", "#4a7050")):
    base_c, shade, hi = colors
    s = trunk(x, base, base - height * 0.2, height * 0.07)
    tiers = 4
    for i in range(tiers):
        t0 = i / tiers
        top = base - height * (0.15 + 0.85 * (1 - t0) ** 0.9) - height * 0.08
        y = base - height * 0.12 - i * height * 0.18
        w = height * (0.34 - 0.06 * i)
        d = (f"M{f(x)},{f(top)} Q{f(x - w * 0.4)},{f(y - height * 0.12)} {f(x - w)},{f(y)} "
             f"Q{f(x)},{f(y + height * 0.06)} {f(x + w)},{f(y)} Q{f(x + w * 0.4)},{f(y - height * 0.12)} {f(x)},{f(top)} Z")
        dsh = (f"M{f(x)},{f(top)} Q{f(x + w * 0.4)},{f(y - height * 0.12)} {f(x + w)},{f(y)} "
               f"Q{f(x + w * 0.5)},{f(y + height * 0.045)} {f(x + w * 0.1)},{f(y + height * 0.035)} Z")
        s += outlined(d, base_c, sw) + path(dsh, shade)
        s += path(f"M{f(x - w * 0.15)},{f(top + height * 0.05)} Q{f(x - w * 0.45)},{f(y - height * 0.04)} {f(x - w * 0.75)},{f(y - height * 0.005)}",
                  "none", f'stroke="{hi}" stroke-width="{f(sw * 0.9)}" stroke-linecap="round"')
    svg.add(s)


def bush(svg, rng, x, base, w, kind="brown", sw=SW):
    circles = blob_circles(rng, x, base - w * 0.28, w * 0.5, w * 0.3, size=0.5)
    circles = [(cx, min(cy, base - r * 0.55), r) for cx, cy, r in circles]
    svg.add(bumps(svg, circles, TREE_COLORS[kind], sw))


def ground(svg, x0, x1):
    fill = linear(svg, [(0, "#a08a48", 1), (0.12, "#7f7d38", 1), (0.5, "#66702e", 1), (1, "#4e5a26", 1)])
    svg.add(f'<rect x="{x0}" y="{HORIZON - 10}" width="{x1 - x0}" height="{H - HORIZON + 10}" fill="{fill}"/>')


def leaf_litter(svg, rng, x0, x1, y0, y1, n):
    parts = []
    for _ in range(n):
        y = rng.uniform(y0, y1) ** 1.0
        t = (y - y0) / max(1, y1 - y0)
        x = rng.uniform(x0, x1)
        s = 5 + 14 * t * rng.uniform(0.6, 1.2)
        parts.append(ellipse(x, y, s, s * 0.45, rng.choice(LEAF_COLORS),
                             f'transform="rotate({rng.randint(-40, 40)} {f(x)} {f(y)})" opacity="{0.55 + 0.4 * t:.2f}"'))
    svg.add("".join(parts))


def grass(svg, rng, x, y, s, color="#4a5a22"):
    blades = []
    for i in range(7):
        dx = (i - 3) * s * 0.12 + rng.uniform(-3, 3)
        h = s * rng.uniform(0.5, 1.0)
        lean = rng.uniform(-0.35, 0.35) * s
        blades.append(f"M{f(x + dx - s * 0.05)},{f(y)} Q{f(x + dx + lean * 0.3)},{f(y - h * 0.6)} {f(x + dx + lean)},{f(y - h)} "
                      f"Q{f(x + dx + lean * 0.2)},{f(y - h * 0.5)} {f(x + dx + s * 0.05)},{f(y)} Z")
    svg.add(outlined(" ".join(blades), color, SW * 0.6))


def falling_leaf(x, y, s, angle, color):
    d = (f"M0,{f(-s)} Q{f(s * 0.75)},{f(-s * 0.3)} 0,{f(s)} Q{f(-s * 0.75)},{f(-s * 0.3)} 0,{f(-s)} Z")
    return (f'<g transform="translate({f(x)} {f(y)}) rotate({angle})">' + outlined(d, color, SW * 0.55) +
            f'<path d="M0,{f(-s * 0.7)} L0,{f(s * 0.8)}" stroke="{INK}" stroke-width="{f(SW * 0.4)}" opacity="0.6"/></g>')


def light_rays(svg, x0, x1, origin):
    ox, oy = origin
    fill = linear(svg, [(0, "#fff6c8", 0.5), (1, "#fff6c8", 0)])
    rays = []
    for i, (a, w) in enumerate(((-0.95, 0.05), (-0.75, 0.03), (-0.58, 0.06), (-0.35, 0.035), (-0.18, 0.05))):
        l = 1400
        p1 = (ox + math.sin(a - w) * l, oy + math.cos(a - w) * l)
        p2 = (ox + math.sin(a + w) * l, oy + math.cos(a + w) * l)
        rays.append(path(f"M{f(ox)},{f(oy)} L{f(p1[0])},{f(p1[1])} L{f(p2[0])},{f(p2[1])} Z", fill, 'opacity="0.35"'))
    svg.add("".join(rays))


# --- Mushrooms (unit size: ~100 high, base at 0) ------------------------------
def mushroom(svg, kind, x, y, size, angle=0):
    s = size / 100.0
    sw = SW / s
    g = [f'<g transform="translate({f(x)} {f(y)}) rotate({angle}) scale({s:.3f})">']
    g.append(ellipse(0, 0, 38, 7, "#2a3014", 'opacity="0.35"'))
    if kind in ("fly", "god"):
        cap = "#d42a1e" if kind == "fly" else "#fbfaf4"
        shade = "#9c1e16" if kind == "fly" else "#d8d8d0"
        spot = "#fbf7ee" if kind == "fly" else "#1e1c22"
        if kind == "god":
            g.append(circle(0, -60, 95, radial(svg, [(0, "#fffbe0", 0.9), (0.5, "#fff2b0", 0.4), (1, "#fff2b0", 0)])))
        g.append(outlined("M-14,0 Q-20,-4 -16,-12 L-11,-56 L11,-56 L16,-12 Q20,-4 14,0 Z", "#ece2c8", sw))
        g.append(path("M4,-56 L11,-56 L16,-12 Q20,-4 14,0 L6,0 Z", "#cfc2a2"))
        g.append(outlined("M-16,-44 Q0,-38 16,-44 L13,-50 L-13,-50 Z", "#f4eee0", sw * 0.8))
        clip = svg.uid("cap")
        capd = "M-46,-52 Q-48,-102 0,-104 Q48,-102 46,-52 Q0,-44 -46,-52 Z"
        svg.defs.append(f'<clipPath id="{clip}"><path d="{capd}"/></clipPath>')
        g.append(outlined(capd, cap, sw))
        g.append(f'<g clip-path="url(#{clip})">' + circle(-14, -92, 58, "none") +
                 path("M10,-104 Q52,-100 48,-52 Q20,-48 6,-50 Q40,-70 10,-104 Z", shade) +
                 path("M-34,-66 Q-36,-88 -14,-96", "none", 'stroke="#ffffff" stroke-opacity="0.45" stroke-width="7" stroke-linecap="round"') +
                 "</g>")
        for sx, sy, sr in ((-24, -80, 7), (0, -93, 6), (21, -79, 8), (-6, -65, 5), (34, -62, 4.5), (-37, -60, 4)):
            g.append(ellipse(sx, sy, sr, sr * 0.8, spot))
        g.append(outlined("M-46,-52 Q0,-44 46,-52 Q0,-40 -46,-52 Z", "#f4eee0", sw * 0.8))
    elif kind == "boletus":
        g.append(outlined("M-22,0 Q-34,-22 -22,-48 L22,-48 Q34,-22 22,0 Z", "#efe6cf", sw))
        g.append(path("M6,-48 L22,-48 Q34,-22 22,0 L10,0 Q20,-24 6,-48 Z", "#d4c8a8"))
        for i in range(5):
            g.append(path(f"M-14,{-10 - i * 8} L14,{-14 - i * 8}", "none", 'stroke="#c8b890" stroke-width="2.5"'))
        g.append(outlined("M-48,-42 Q-50,-96 0,-98 Q50,-96 48,-42 Q0,-30 -48,-42 Z", "#7a4a24", sw))
        g.append(path("M12,-98 Q52,-92 48,-42 Q26,-36 10,-37 Q40,-60 12,-98 Z", "#5c3418"))
        g.append(path("M-34,-58 Q-36,-82 -12,-90", "none", 'stroke="#a8703c" stroke-width="9" stroke-linecap="round"'))
        g.append(outlined("M-48,-42 Q0,-30 48,-42 Q0,-26 -48,-42 Z", "#e8e0b0", sw * 0.8))
    elif kind == "chanterelle":
        g.append(outlined("M-9,0 L-6,-34 Q-32,-42 -38,-56 Q-20,-50 -10,-56 Q0,-48 10,-56 Q20,-50 38,-56 Q32,-42 6,-34 L9,0 Z", "#f2b422", sw))
        g.append(path("M2,-34 Q26,-42 30,-53 Q34,-52 38,-56 Q32,-42 6,-34 L9,0 L3,0 Z", "#d8961a"))
        g.append(outlined("M-38,-56 Q-20,-50 -10,-56 Q0,-48 10,-56 Q20,-50 38,-56 Q0,-66 -38,-56 Z", "#f7c84a", sw * 0.8))
        for i in (-18, -6, 6, 18):
            g.append(path(f"M{i * 0.3},-36 L{i},-52", "none", 'stroke="#c8861a" stroke-width="2.5"'))
    g.append("</g>")
    svg.add("".join(g))


# --- Characters (feet at 0, ~440 high at scale 1) -----------------------------
SKIN, SKIN_SHADE, BLUSH = "#f6ccaa", "#e2b08c", "#f0968c"
JEANS, JEANS_DARK, SHOE = "#5676a8", "#405c8a", "#463228"


def legs(g, sw):
    for side in (-1, 1):
        d = (f"M{side * 6},-112 L{side * 64},-112 L{side * 72},-20 L{side * 8},-20 Z")
        g.append(outlined(d, JEANS, sw))
        g.append(path(f"M{side * 44},-112 L{side * 64},-112 L{side * 72},-20 L{side * 54},-20 Z" if side > 0 else
                      f"M-6,-112 L-24,-112 L-22,-20 L-8,-20 Z", JEANS_DARK))
        g.append(outlined(f"M{side * 10},-24 Q{side * 12},-2 {side * 44},-2 Q{side * 80},-2 {side * 76},-24 Z", SHOE, sw))


def face(g, sw, cx, cy, glasses):
    for side in (-1, 1):
        ex = cx + side * 36
        g.append(ellipse(ex, cy + 8, 9, 12, "#28201e"))
        g.append(circle(ex + 3, cy + 3, 3.5, "#ffffff"))
        g.append(ellipse(cx + side * 60, cy + 38, 16, 9, BLUSH, 'opacity="0.75"'))
        if glasses:
            g.append(circle(ex, cy + 6, 31, "#ffffff", f'fill-opacity="0.18" stroke="#241c1e" stroke-width="{sw * 1.05}"'))
    if glasses:
        g.append(path(f"M{cx - 6},{cy + 2} Q{cx},{cy - 4} {cx + 6},{cy + 2}", "none", f'stroke="#241c1e" stroke-width="{sw}"'))


def nina(svg, x, y, scale=1.0):
    sw = SW / scale
    hair, hair_dark = "#6c4428", "#4e301e"
    g = [f'<g transform="translate({f(x)} {f(y)}) scale({scale:.3f})">']
    g.append(ellipse(0, -4, 105, 18, "#2a3014", 'opacity="0.4"'))
    # Hair behind the head, shoulder length.
    g.append(outlined("M-100,-360 Q-122,-300 -116,-232 Q-112,-192 -128,-174 Q-86,-164 -58,-184 L58,-184 "
                      "Q86,-164 128,-174 Q112,-192 116,-232 Q122,-300 100,-360 Z", hair, sw))
    g.append(path("M40,-184 L58,-184 Q86,-164 128,-174 Q112,-192 116,-232 Q120,-280 108,-320 Q96,-240 40,-184 Z", hair_dark))
    legs(g, sw)
    # Jacket.
    g.append(outlined("M-72,-208 Q-90,-150 -86,-100 L86,-100 Q90,-150 72,-208 Q0,-226 -72,-208 Z", "#2e5438", sw))
    g.append(path("M30,-214 Q72,-212 72,-208 Q90,-150 86,-100 L40,-100 Q62,-150 30,-214 Z", "#22402c"))
    g.append(path("M0,-214 L0,-104", "none", f'stroke="#1c3424" stroke-width="{sw * 0.8}"'))
    g.append(outlined("M-30,-218 L0,-196 L30,-218 L22,-228 L-22,-228 Z", "#3a6a46", sw * 0.8))
    # Arms reach forward to hold the mushroom book.
    for side in (-1, 1):
        g.append(outlined(f"M{side * 64},-204 Q{side * 100},-176 {side * 86},-140 L{side * 58},-132 Q{side * 70},-168 {side * 46},-192 Z",
                          "#2e5438" if side < 0 else "#22402c", sw))
    # The Pilzbüchlein, open.
    g.append(outlined("M-74,-172 L74,-172 L78,-112 L-78,-112 Z", "#7a4a2a", sw))
    g.append(outlined("M-66,-166 Q-34,-170 -2,-158 L-2,-116 Q-34,-128 -68,-120 Z", "#f4e6c8", sw * 0.7))
    g.append(outlined("M66,-166 Q34,-170 2,-158 L2,-116 Q34,-128 68,-120 Z", "#efdcb6", sw * 0.7))
    for i in range(3):
        g.append(path(f"M-56,{-152 + i * 10} Q-34,{-155 + i * 10} -12,{-148 + i * 10}", "none", 'stroke="#b89868" stroke-width="3"'))
    g.append(path("M22,-138 Q34,-156 48,-138 Z", "#d42a1e"))
    g.append(path("M33,-138 L33,-126", "none", 'stroke="#ece2c8" stroke-width="6"'))
    for side in (-1, 1):
        g.append(circle(side * 76, -138, 17, SKIN, f'stroke="{INK}" stroke-width="{sw}"'))
    # Head.
    g.append(circle(0, -300, 94, SKIN, f'stroke="{INK}" stroke-width="{sw}"'))
    g.append(path("M40,-386 Q100,-360 92,-280 Q80,-220 20,-208 Q70,-260 40,-386 Z", SKIN_SHADE, 'opacity="0.5"'))
    face(g, sw, 0, -300, glasses=True)
    g.append(path("M-12,-252 Q0,-242 12,-252", "none", f'stroke="{INK}" stroke-width="{sw * 0.8}" stroke-linecap="round"'))
    # Fringe and side strands.
    g.append(outlined("M-94,-318 Q-66,-296 -46,-330 Q-18,-302 8,-334 Q38,-300 66,-330 Q86,-306 96,-318 L96,-352 L-94,-352 Z", hair, sw))
    for side in (-1, 1):
        g.append(outlined(f"M{side * 94},-332 Q{side * 108},-266 {side * 98},-206 Q{side * 86},-222 {side * 80},-252 Q{side * 76},-296 {side * 70},-330 Z",
                          hair if side < 0 else hair_dark, sw))
    # Rust wool beanie with pompom.
    g.append(outlined("M-100,-336 Q-104,-428 0,-432 Q104,-428 100,-336 Z", "#b85228", sw))
    g.append(path("M30,-430 Q104,-420 100,-336 L60,-336 Q70,-400 30,-430 Z", "#96401e"))
    g.append(outlined("M-106,-352 Q0,-372 106,-352 L104,-322 Q0,-340 -104,-322 Z", "#8c3a1e", sw))
    for i in range(-5, 6):
        g.append(path(f"M{i * 18},{-360 + abs(i) * 0.8} L{i * 18},{-332 + abs(i) * 0.8}", "none", 'stroke="#6e2c16" stroke-width="4"'))
    g.append(circle(0, -438, 28, "#d27a44", f'stroke="{INK}" stroke-width="{sw}"'))
    g.append(circle(-8, -446, 10, "#e6a070"))
    g.append("</g>")
    svg.add("".join(g))


def mats(svg, x, y, scale=1.0, rng=None):
    sw = SW / scale
    g = [f'<g transform="translate({f(x)} {f(y)}) scale({scale:.3f})">']
    g.append(ellipse(0, -4, 110, 18, "#2a3014", 'opacity="0.4"'))
    # Lantern glow behind everything.
    g.append(circle(118, -96, 170, radial(svg, [(0, "#fff0b0", 0.85), (0.45, "#ffd680", 0.35), (1, "#ffd680", 0)])))
    # Curls behind the head.
    curls = []
    for i in range(13):
        a = math.radians(150 + i * 20)
        curls.append((math.cos(a) * 92, -318 + math.sin(a) * 88, 34 + (i % 3) * 4))
    svg_curls_back = bumps(svg, curls, ("#964628", "#72321e", "#b86440"), sw)
    g.append(svg_curls_back)
    legs(g, sw)
    # Jacket (beige).
    g.append(outlined("M-76,-214 Q-94,-152 -90,-100 L90,-100 Q94,-152 76,-214 Q0,-232 -76,-214 Z", "#d6be96", sw))
    g.append(path("M34,-220 Q76,-218 76,-214 Q94,-152 90,-100 L44,-100 Q66,-150 34,-220 Z", "#b8a07a"))
    for by in (-180, -150, -122):
        g.append(circle(0, by, 6, "#8a6a44"))
    g.append(outlined("M-60,-140 L-28,-140 L-30,-112 L-58,-112 Z", "#c8ae84", sw * 0.7))
    # Right arm (viewer's right) holds the lantern.
    g.append(outlined("M68,-206 Q108,-176 104,-128 L78,-124 Q80,-166 50,-196 Z", "#b8a07a", sw))
    g.append(circle(92, -122, 17, SKIN, f'stroke="{INK}" stroke-width="{sw}"'))
    g.append(path("M92,-118 Q118,-128 118,-110", "none", f'stroke="#3c3834" stroke-width="{sw}" stroke-linecap="round"'))
    g.append(outlined("M100,-110 L136,-110 L130,-98 L106,-98 Z", "#3c3834", sw * 0.8))
    g.append(outlined("M106,-98 L130,-98 L134,-54 L102,-54 Z", "#ffdc8c", sw * 0.8))
    g.append(path("M112,-92 L112,-60", "none", 'stroke="#ffffff" stroke-width="5" opacity="0.8"'))
    g.append(path("M118,-98 L118,-54", "none", 'stroke="#3c3834" stroke-width="4"'))
    g.append(outlined("M98,-54 L138,-54 L134,-44 L102,-44 Z", "#3c3834", sw * 0.8))
    # Left arm (viewer's left) holds the basket.
    g.append(outlined("M-68,-206 Q-106,-176 -100,-132 L-74,-128 Q-78,-168 -50,-196 Z", "#d6be96", sw))
    g.append(path("M-128,-104 Q-104,-190 -64,-104", "none", f'stroke="{INK}" stroke-width="{sw * 2.6}"'))
    g.append(path("M-128,-104 Q-104,-190 -64,-104", "none", 'stroke="#c4965a" stroke-width="9"'))
    g.append(outlined("M-150,-106 L-42,-106 L-52,-44 Q-96,-34 -140,-44 Z", "#c4965a", sw))
    for i in range(4):
        g.append(path(f"M-148,{-92 + i * 13} Q-96,{-86 + i * 13} -46,{-92 + i * 13}", "none", 'stroke="#96683c" stroke-width="4"'))
    # Mushrooms peeking out of the basket.
    g.append(outlined("M-138,-106 Q-136,-134 -112,-134 Q-90,-134 -90,-106 Z", "#7a4a24", sw * 0.8))
    g.append(outlined("M-96,-106 Q-92,-126 -74,-128 Q-56,-126 -54,-106 Z", "#f2b422", sw * 0.8))
    g.append(outlined("M-150,-106 L-42,-106 L-44,-96 L-148,-96 Z", "#b0844a", sw * 0.8))
    g.append(circle(-100, -128, 17, SKIN, f'stroke="{INK}" stroke-width="{sw}"'))
    # Head.
    for side in (-1, 1):
        g.append(circle(side * 94, -300, 16, SKIN, f'stroke="{INK}" stroke-width="{sw}"'))
    g.append(circle(0, -306, 96, SKIN, f'stroke="{INK}" stroke-width="{sw}"'))
    g.append(path("M40,-392 Q102,-366 94,-286 Q82,-226 20,-212 Q72,-266 40,-392 Z", SKIN_SHADE, 'opacity="0.5"'))
    face(g, sw, 0, -300, glasses=False)
    for side in (-1, 1):
        g.append(path(f"M{side * 24},-326 Q{side * 36},-334 {side * 48},-326", "none",
                      f'stroke="#72321e" stroke-width="{sw * 0.9}" stroke-linecap="round"'))
    g.append(outlined("M-18,-256 Q0,-236 18,-256 Q0,-250 -18,-256 Z", "#8a3a2a", sw * 0.7))
    # Curls on top and at the fringe.
    front = []
    for i in range(7):
        front.append((-78 + i * 26, -372 + (i % 2) * 10 - (8 if 2 <= i <= 4 else 0), 28 + (i % 3) * 3))
    for side in (-1, 1):
        front.append((side * 96, -340, 26))
    g.append(bumps(svg, front, ("#964628", "#72321e", "#b86440"), sw))
    # Scarf (red with cream stripes), end hanging down on the left.
    g.append(outlined("M-72,-222 Q0,-196 72,-222 L70,-196 Q0,-170 -70,-196 Z", "#be3c32", sw))
    for sx in (-40, 0, 40):
        g.append(path(f"M{sx - 6},{-214 + abs(sx) * 0.1} L{sx + 6},{-214 + abs(sx) * 0.1} L{sx + 6},{-186 + abs(sx) * 0.2} L{sx - 6},{-186 + abs(sx) * 0.2} Z", "#f0dcb4"))
    g.append(outlined("M-52,-198 L-22,-196 L-26,-120 L-54,-124 Z", "#be3c32", sw))
    for i in range(3):
        g.append(path(f"M-53,{-180 + i * 20} L-24,{-178 + i * 20} L-24,{-170 + i * 20} L-53,{-172 + i * 20} Z", "#f0dcb4"))
    for i in range(5):
        g.append(path(f"M{-52 + i * 6.5},-122 L{-53 + i * 6.5},-108", "none", f'stroke="#be3c32" stroke-width="4" stroke-linecap="round"'))
    g.append("</g>")
    svg.add("".join(g))


# --- Text ---------------------------------------------------------------------
class Metrics:
    def __init__(self, path):
        font = TTFont(path)
        self.cmap = font.getBestCmap()
        self.hmtx = font["hmtx"]
        self.upm = font["head"].unitsPerEm

    def width(self, text, size):
        return sum(self.hmtx[self.cmap.get(ord(c), self.cmap[ord("?")])][0] for c in text) * size / self.upm

    def wrap(self, text, size, max_w):
        lines, line = [], ""
        for word in text.split():
            test = (line + " " + word).strip()
            if self.width(test, size) > max_w and line:
                lines.append(line)
                line = word
            else:
                line = test
        return lines + [line]


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def title(svg, cx, y, size_big, size_small):
    common = f'font-family="{TITLE_FONT}" font-weight="bold" text-anchor="middle"'
    lines = [("NiKnight", y, size_big), ("im Pilzwald", y + size_small * 1.12, size_small)]
    out = []
    for text, ty, size in lines:
        out.append(f'<text x="{cx + 8}" y="{ty + 12}" {common} font-size="{size}" fill="{INK}" opacity="0.45" '
                   f'stroke="{INK}" stroke-width="{size * 0.12:.0f}" stroke-linejoin="round">{text}</text>')
    for text, ty, size in lines:
        out.append(f'<text x="{cx}" y="{ty}" {common} font-size="{size}" fill="#fff4dc" stroke="{INK}" '
                   f'stroke-width="{size * 0.11:.0f}" stroke-linejoin="round" paint-order="stroke">{text}</text>')
    svg.add("".join(out))


def blurb_panel(svg, box):
    """Parchment with title and blurb; as high as the text needs, centred in box."""
    x0, y0, x1, y1 = box
    body = Metrics(os.path.join(HERE, "fonts", "VarelaRound-Regular.ttf"))
    pad, size, lead, title_size = 70, 42, 1.42, 80
    paras = [body.wrap(p, size, x1 - x0 - 2 * pad) for p in BLURB]
    lines = sum(len(p) for p in paras)
    height = 70 + title_size + 40 + lines * size * lead + (len(paras) - 1) * size * 0.7 + 60
    y0 = (y0 + y1 - height) / 2
    y1 = y0 + height
    svg.add(f'<rect x="{x0 + 10}" y="{f(y0 + 14)}" width="{x1 - x0}" height="{f(height)}" rx="26" fill="{INK}" opacity="0.35"/>')
    svg.add(f'<rect x="{x0}" y="{f(y0)}" width="{x1 - x0}" height="{f(height)}" rx="26" fill="#f2e2bc" stroke="{INK}" stroke-width="{SW}"/>')
    svg.add(f'<rect x="{x0 + 18}" y="{f(y0 + 18)}" width="{x1 - x0 - 36}" height="{f(height - 36)}" rx="16" fill="none" '
            f'stroke="#b08a54" stroke-width="3" stroke-dasharray="14 9"/>')
    ty = y0 + 70 + title_size * 0.75
    svg.add(f'<text x="{(x0 + x1) / 2}" y="{f(ty)}" font-family="{TITLE_FONT}" font-weight="bold" font-size="{title_size}" '
            f'text-anchor="middle" fill="#b8401e">{BLURB_TITLE}</text>')
    ty += 40
    out = []
    for i, para in enumerate(paras):
        if i:
            ty += size * 0.7
        for line in para:
            ty += size * lead
            out.append(f'<text x="{x0 + pad}" y="{f(ty)}" font-family="{BODY_FONT}" font-size="{size}" fill="{INK}">{esc(line)}</text>')
    svg.add("".join(out))


# --- Scenes -------------------------------------------------------------------
def forest_background(svg, rng, x0, x1, sun):
    sky(svg, x0, x1, sun)
    light_rays(svg, x0, x1, (sun[0] + 500, -200))
    treeline(svg, rng, x0, x1, HORIZON - 70, 150, 26, 44, "#eab48c")
    treeline(svg, rng, x0, x1, HORIZON - 35, 130, 30, 50, "#dc9466")
    treeline(svg, rng, x0, x1, HORIZON, 110, 34, 56, "#c0704a")
    ground(svg, x0, x1)


def front(svg):
    rng = random.Random(7)
    x0, x1 = FRONT[0], FRONT[2]
    forest_background(svg, rng, x0, x1, (FRONT_CX + 30, HORIZON - 150))
    # Path winding towards the light.
    svg.add(path(f"M{FRONT_CX - 330},{H} Q{FRONT_CX - 120},{HORIZON + 260} {FRONT_CX + 10},{HORIZON + 60} "
                 f"Q{FRONT_CX + 40},{HORIZON} {FRONT_CX + 60},{HORIZON - 4} Q{FRONT_CX + 70},{HORIZON + 60} "
                 f"{FRONT_CX + 150},{HORIZON + 160} Q{FRONT_CX + 330},{HORIZON + 380} {FRONT_CX + 420},{H} Z",
                 linear(svg, [(0, "#e2c48c", 1), (1, "#c9a66e", 1)])))
    # Middle distance: small trees along the horizon.
    mids = [(2060, "red", 300), (2180, "fir", 330), (2290, "yellow", 250), (2420, "orange", 230),
            (2890, "orange", 240), (3000, "fir", 300), (3110, "red", 270), (3230, "yellow", 300)]
    for mx, kind, h in mids:
        base = HORIZON + 40 + rng.uniform(-10, 20)
        if kind == "fir":
            fir(svg, mx, base, h, SW * 0.8)
        else:
            tree(svg, rng, mx, base, h, kind, SW * 0.8)
    bush(svg, rng, 2470, HORIZON + 70, 150, "yellow", SW * 0.8)
    bush(svg, rng, 2860, HORIZON + 80, 170, "brown", SW * 0.8)
    leaf_litter(svg, rng, x0, x1, HORIZON + 30, H, 420)
    # Big framing trees.
    tree(svg, rng, 2120, 1180, 1080, "orange")
    tree(svg, rng, 3210, 1140, 1060, "red")
    tree(svg, rng, 2420, 960, 620, "yellow")
    tree(svg, rng, 2960, 980, 640, "orange")
    bush(svg, rng, 2050, 1260, 260, "red")
    bush(svg, rng, 3250, 1250, 240, "yellow")
    # Mushrooms: the little glowing cow mushroom hides at the edge of the path.
    mushroom(svg, "god", 3020, 990, 50)
    mushroom(svg, "fly", 2250, 1300, 150)
    mushroom(svg, "fly", 2345, 1318, 96, 6)
    mushroom(svg, "fly", 2180, 1335, 70, -8)
    mushroom(svg, "boletus", 2990, 1225, 120)
    mushroom(svg, "chanterelle", 3090, 1215, 96, 4)
    mushroom(svg, "chanterelle", 3050, 1250, 78, -6)
    mushroom(svg, "fly", 2475, 1060, 54)
    grass(svg, rng, 2320, 1340, 60)
    grass(svg, rng, 3130, 1230, 46)
    # Nina & Mats on the path.
    nina(svg, FRONT_CX - 120, 1236, 0.98)
    mats(svg, FRONT_CX + 150, 1240, 1.0)
    # Falling leaves.
    for lx, ly, s, a, c in ((2380, 560, 22, 30, 0), (2960, 470, 18, -40, 2), (2560, 700, 16, 70, 1),
                            (3120, 700, 20, 10, 0), (2200, 760, 18, -20, 2), (2820, 600, 14, 50, 3)):
        svg.add(falling_leaf(lx, ly, s, a, LEAF_COLORS[c]))
    title(svg, FRONT_CX, 250, 236, 132)


def back(svg):
    rng = random.Random(11)
    x0, x1 = BACK[0], BACK[2]
    forest_background(svg, rng, x0, x1 + 60, (1200, HORIZON - 190))
    for mx, kind, h in ((60, "yellow", 320), (1140, "red", 300), (1260, "fir", 360), (1400, "orange", 300), (1520, "yellow", 280)):
        if kind == "fir":
            fir(svg, mx, HORIZON + 30, h, SW * 0.8)
        else:
            tree(svg, rng, mx, HORIZON + 30, h, kind, SW * 0.8)
    leaf_litter(svg, rng, x0, x1, HORIZON + 20, BACK[3], 90)
    tree(svg, rng, 1330, 900, 760, "orange")
    bush(svg, rng, 1110, 880, 200, "brown")
    mushroom(svg, "god", 1215, 858, 60)
    mushroom(svg, "fly", 1440, 870, 90)
    mushroom(svg, "chanterelle", 1500, 866, 50)
    svg.add(falling_leaf(1180, 300, 18, 30, LEAF_COLORS[0]) + falling_leaf(1460, 520, 16, -30, LEAF_COLORS[2]))
    blurb_panel(svg, BLURB_BOX)


def build(front_art=None, back_art=None):
    svg = Svg()
    if front_art:
        svg.add(f'<image x="{FRONT[0]}" y="0" width="{W - FRONT[0]}" height="{H}" preserveAspectRatio="xMidYMid slice" xlink:href="{front_art}"/>')
        title(svg, FRONT_CX, 250, 236, 132)
    else:
        front(svg)
    if back_art:
        svg.add(f'<image x="0" y="0" width="{BACK[2]}" height="{BACK[3]}" preserveAspectRatio="xMidYMid slice" xlink:href="{back_art}"/>')
        blurb_panel(svg, BLURB_BOX)
    else:
        back(svg)
    overlay = os.path.join(HERE, "build", "template_overlay.png").replace("\\", "/")
    svg.add(f'<image x="0" y="0" width="{W}" height="{H}" xlink:href="file:///{overlay}"/>')
    return svg.text()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out_dir", nargs="?", default=HERE)
    ap.add_argument("--front-art")
    ap.add_argument("--back-art")
    ap.add_argument("--name", default="cover_vector")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)
    to_url = lambda p: "file:///" + os.path.abspath(p).replace("\\", "/") if p else None
    svg_path = os.path.join(args.out_dir, args.name + ".svg")
    png_path = os.path.join(args.out_dir, args.name + ".png")
    with open(svg_path, "w", encoding="utf-8") as fh:
        fh.write(build(to_url(args.front_art), to_url(args.back_art)))
    subprocess.run([INKSCAPE, svg_path, "--export-type=png", f"--export-filename={png_path}",
                    f"--export-width={W}", "--export-background=#ffffff", "--export-background-opacity=1"], check=True)
    print("cover", png_path)


if __name__ == "__main__":
    main()
