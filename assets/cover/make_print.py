"""Print-ready PDF of the cover: A4 landscape, exact DS case insert size, crop
and fold marks.

Run: python assets/cover/make_print.py [cover.png] [out.pdf]

The common DS insert is 3260 x 1370 px at 300 dpi (back 1535, spine 190,
front 1535), about 276 x 116 mm. The packaging template is 47 px wider in the
spine + front part, so that part is squeezed horizontally by 2.7 % (the back
stays untouched). Print at 100 % ("actual size"), not "fit to page".
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
INKSCAPE = os.environ.get("INKSCAPE", r"C:\Program Files\Inkscape\bin\inkscape.exe")

SRC_W, SRC_H = 3307, 1370      # cover image (template size)
BACK_PX = 1535                 # back cover width, identical in template and standard
SPINE_PX = 190
FRONT_PX = 1535
MM_PER_PX = 25.4 / 300

PAGE_W, PAGE_H = 297.0, 210.0  # A4 landscape
MARK_LEN, MARK_GAP, MARK_W = 6.0, 2.0, 0.2


def mm(px):
    return px * MM_PER_PX


def build_svg(cover_url):
    back_w = mm(BACK_PX)
    rest_w = mm(SPINE_PX + FRONT_PX)
    width, height = back_w + rest_w, mm(SRC_H)
    x0, y0 = (PAGE_W - width) / 2, (PAGE_H - height) / 2
    # Source pixels -> mm; the spine + front part is squeezed horizontally.
    scale = MM_PER_PX
    squeeze = rest_w / mm(SRC_W - BACK_PX)

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{PAGE_W}mm" height="{PAGE_H}mm" viewBox="0 0 {PAGE_W} {PAGE_H}">',
        "<defs>",
        f'<clipPath id="back"><rect x="{x0}" y="{y0}" width="{back_w}" height="{height}"/></clipPath>',
        f'<clipPath id="rest"><rect x="{x0 + back_w}" y="{y0}" width="{rest_w}" height="{height}"/></clipPath>',
        "</defs>",
        f'<g clip-path="url(#back)"><image x="{x0}" y="{y0}" width="{mm(SRC_W)}" height="{height}" '
        f'preserveAspectRatio="none" xlink:href="{cover_url}"/></g>',
        # Right part: the image shifted so pixel BACK_PX lands on the fold, then squeezed.
        f'<g clip-path="url(#rest)"><g transform="translate({x0 + back_w} {y0}) scale({squeeze * scale} {scale}) '
        f'translate({-BACK_PX} 0)"><image x="0" y="0" width="{SRC_W}" height="{SRC_H}" '
        f'preserveAspectRatio="none" xlink:href="{cover_url}"/></g></g>',
    ]

    line = f'stroke="#000" stroke-width="{MARK_W}"'
    x1, y1 = x0 + width, y0 + height
    for x in (x0, x1):
        for y, d in ((y0, -1), (y1, 1)):
            parts.append(f'<line x1="{x}" y1="{y + d * MARK_GAP}" x2="{x}" y2="{y + d * (MARK_GAP + MARK_LEN)}" {line}/>')
    for y in (y0, y1):
        for x, d in ((x0, -1), (x1, 1)):
            parts.append(f'<line x1="{x + d * MARK_GAP}" y1="{y}" x2="{x + d * (MARK_GAP + MARK_LEN)}" y2="{y}" {line}/>')
    # Fold marks: dashed, above and below the spine edges.
    for fx in (x0 + back_w, x0 + back_w + mm(SPINE_PX)):
        for ya, yb in ((y0 - MARK_GAP, y0 - MARK_GAP - MARK_LEN), (y1 + MARK_GAP, y1 + MARK_GAP + MARK_LEN)):
            parts.append(f'<line x1="{fx}" y1="{ya}" x2="{fx}" y2="{yb}" {line} stroke-dasharray="1 0.8"/>')

    note = (f"NiKnight im Pilzwald – DS-Hülleneinleger {width:.1f} × {height:.1f} mm. "
            "Mit 100 % / tatsächlicher Größe drucken. Durchgezogen = schneiden, gestrichelt = falzen.")
    parts.append(f'<text x="{PAGE_W / 2}" y="{y1 + MARK_GAP + MARK_LEN + 8}" font-family="Varela Round" '
                 f'font-size="3.2" text-anchor="middle" fill="#555">{note}</text>')
    parts.append("</svg>")
    return "\n".join(parts), width, height


def main():
    src = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "cover_blender.png"))
    out = os.path.abspath(sys.argv[2] if len(sys.argv) > 2 else os.path.splitext(src)[0] + "_druck.pdf")
    svg, width, height = build_svg("file:///" + src.replace("\\", "/"))
    svg_path = os.path.join(HERE, "build", "print.svg")
    os.makedirs(os.path.dirname(svg_path), exist_ok=True)
    with open(svg_path, "w", encoding="utf-8") as fh:
        fh.write(svg)
    subprocess.run([INKSCAPE, svg_path, "--export-type=pdf", f"--export-filename={out}",
                    "--export-dpi=300"], check=True)
    print(f"druck {out}  Einleger {width:.1f} x {height:.1f} mm auf A4 quer")


if __name__ == "__main__":
    main()
