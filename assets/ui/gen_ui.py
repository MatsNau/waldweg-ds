"""Generates the bottom-screen graphics as indexed PNGs.

Run: python assets/ui/gen_ui.py <outdir>

Layout numbers must match source/ui/UiLayout.h.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pixelart import Canvas, Palette, sheet  # noqa: E402

# --- Layout (keep in sync with source/ui/UiLayout.h) ------------------------
MAP_HEIGHT = 144
SLOT_X0 = 6
SLOT_STEP = 38
SLOT_Y = 150
SLOT_SIZE = 36
LEAF_X0 = 160
LEAF_Y = 160
PORTRAIT_X = 210
PORTRAIT_Y = 148
PORTRAIT_SIZE = 40
DIALOG_BOX = (4, 3, 251, 60)

# Shared colours; each PNG gets its own palette (NFLib loads one per layer/sheet).
COLORS = {
    "ink": (46, 30, 20),
    "parchment": (236, 216, 172),
    "parchment_speck": (224, 200, 152),
    "parchment_dark": (206, 178, 128),
    "parchment_edge": (150, 108, 64),
    "wood": (112, 72, 44),
    "wood_light": (140, 94, 58),
    "wood_dark": (78, 48, 28),
    "slot": (60, 38, 24),
    "slot_light": (92, 62, 40),
    "leaf_orange": (232, 128, 30),
    "leaf_red": (196, 64, 30),
    "leaf_yellow": (240, 186, 60),
    "leaf_shade": (170, 70, 24),
    "fir": (62, 104, 70),
    "fir_dark": (40, 72, 50),
    "bush": (150, 118, 50),
    "stone": (150, 146, 136),
    "stone_dark": (104, 100, 94),
    "bark": (92, 58, 36),
    "wood_cut": (206, 164, 110),
    "skin": (246, 204, 170),
    "blush": (236, 140, 130),
    "hair_brown": (104, 66, 40),
    "hair_auburn": (160, 74, 40),
    "hair_auburn_dark": (118, 52, 30),
    "glasses": (36, 28, 30),
    "jacket_green": (46, 84, 56),
    "jacket_beige": (214, 190, 150),
    "cap_brown": (150, 96, 56),
    "cap_light": (190, 136, 86),
    "stem": (240, 230, 208),
    "glow": (255, 244, 160),
    "glow_light": (255, 255, 230),
    "wicker": (196, 150, 90),
    "wicker_dark": (150, 108, 60),
    "scarf_red": (190, 60, 50),
    "scarf_stripe": (240, 220, 180),
    "metal": (70, 64, 60),
    "metal_light": (120, 112, 104),
    "lantern_glass": (255, 214, 120),
    "bell_gold": (230, 190, 70),
    "bell_light": (250, 226, 140),
    "bell_dark": (160, 120, 40),
    "ribbon": (180, 40, 40),
    "locked": (120, 96, 70),
    "cold": (150, 190, 230),
    "smoke": (196, 186, 178),
    "smoke_light": (226, 218, 208),
    "white": (255, 255, 255),
}
PAL = Palette(COLORS)


# --- Backgrounds ------------------------------------------------------------

def parchment_fill(c, x0, y0, x1, y1, rng, speck=0.06):
    c.rect(x0, y0, x1, y1, "parchment")
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            if rng.random() < speck:
                c.set(x, y, "parchment_speck")


def make_bar(rng):
    """Layer 2: map frame + bottom bar. The map area stays transparent."""
    c = Canvas(256, 256, PAL)

    # Map frame (2 px).
    c.frame(0, 0, 255, MAP_HEIGHT - 1, "wood_dark")
    c.frame(1, 1, 254, MAP_HEIGHT - 2, "parchment_edge")

    # Wooden bar with planks.
    c.rect(0, MAP_HEIGHT, 255, 191, "wood")
    for y in (MAP_HEIGHT, MAP_HEIGHT + 16, MAP_HEIGHT + 32):
        c.rect(0, y, 255, y, "wood_dark")
        c.rect(0, y + 1, 255, y + 1, "wood_light")
    for x in range(0, 256, 64):
        c.rect(x, MAP_HEIGHT, x, 191, "wood_dark")

    # Backpack slots.
    for i in range(4):
        x = SLOT_X0 + i * SLOT_STEP
        c.rect(x, SLOT_Y, x + SLOT_SIZE - 1, SLOT_Y + SLOT_SIZE - 1, "slot")
        c.frame(x - 1, SLOT_Y - 1, x + SLOT_SIZE, SLOT_Y + SLOT_SIZE, "wood_dark")
        c.rect(x + 1, SLOT_Y + SLOT_SIZE - 2, x + SLOT_SIZE - 2, SLOT_Y + SLOT_SIZE - 2, "slot_light")

    # Leaf tray.
    c.rect(LEAF_X0 - 3, LEAF_Y - 3, LEAF_X0 + 48 + 2, LEAF_Y + 16 + 2, "wood_dark")
    c.rect(LEAF_X0 - 2, LEAF_Y - 2, LEAF_X0 + 48 + 1, LEAF_Y + 16 + 1, "slot")

    # Portrait frame.
    x, y, s = PORTRAIT_X, PORTRAIT_Y, PORTRAIT_SIZE
    c.rect(x, y, x + s - 1, y + s - 1, "wood_dark")
    c.rect(x + 2, y + 2, x + s - 3, y + s - 3, "parchment_dark")
    c.frame(x + 1, y + 1, x + s - 2, y + s - 2, "wood_light")
    return c


def make_dialog(rng):
    """Layer 1: parchment box at the top of the map for dialog and debug text."""
    c = Canvas(256, 256, PAL)
    x0, y0, x1, y1 = DIALOG_BOX
    parchment_fill(c, x0 + 1, y0 + 1, x1 - 1, y1 - 1, rng, speck=0.03)
    c.frame(x0, y0, x1, y1, "parchment_edge")
    c.frame(x0 + 1, y0 + 1, x1 - 1, y1 - 1, "parchment_dark")
    for cx, cy in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        c.set(cx, cy, "clear")
    return c


# --- Map tiles (8x8, drawn on a 4-tile-wide sheet, exported as one column) -----
# Tile indices (keep in sync with source/ui/ForestMap.cpp):
#   0-3   parchment variants
#   4     round tree (2x2), 6 golden tree, 12 fir, 14 bush, 20 rock, 22 stump, 28 shrine
#   (a 2x2 icon at index i uses i, i+1, i+4, i+5)

def tree_icon(colors, rng):
    c = Canvas(16, 16, PAL)
    c.rect(7, 10, 8, 14, "bark")
    c.circle(8, 7, 6, colors[0])
    for _ in range(9):
        c.set(rng.randint(3, 12), rng.randint(2, 11), rng.choice(colors[1:]))
    c.circle(6, 5, 1.5, colors[-1])
    c.outline("ink")
    return c


def fir_icon():
    c = Canvas(16, 16, PAL)
    c.rect(7, 12, 8, 14, "bark")
    c.polygon([(8, 1), (13, 8), (3, 8)], "fir")
    c.polygon([(8, 4), (14, 13), (2, 13)], "fir_dark")
    c.polygon([(8, 4), (11, 9), (5, 9)], "fir")
    c.outline("ink")
    return c


def bush_icon():
    c = Canvas(16, 16, PAL)
    c.ellipse(8, 10, 6, 4, "bush")
    c.ellipse(6, 9, 2, 1.5, "leaf_yellow")
    c.set(10, 11, "leaf_orange")
    c.outline("ink")
    return c


def rock_icon():
    c = Canvas(16, 16, PAL)
    c.polygon([(3, 13), (5, 7), (10, 5), (13, 9), (13, 13)], "stone")
    c.polygon([(8, 13), (13, 9), (13, 13)], "stone_dark")
    c.outline("ink")
    return c


def stump_icon():
    c = Canvas(16, 16, PAL)
    c.rect(4, 8, 11, 13, "bark")
    c.ellipse(8, 8, 4.5, 2.5, "wood_cut")
    c.set(8, 8, "bark")
    c.outline("ink")
    return c


def shrine_icon():
    c = Canvas(16, 16, PAL)
    c.rect(2, 11, 13, 13, "stone_dark")
    c.rect(3, 4, 4, 11, "stone")
    c.rect(11, 4, 12, 11, "stone")
    c.rect(2, 3, 13, 4, "fir")
    c.rect(6, 8, 9, 11, "stone")
    c.rect(6, 8, 9, 8, "fir")
    c.outline("ink")
    return c


def make_map_tiles(rng):
    rows = 9
    c = Canvas(32, rows * 8, PAL)
    # Parchment variants.
    for i in range(4):
        parchment_fill(c, i * 8, 0, i * 8 + 7, 7, rng, speck=0.05 + 0.03 * i)
        if i == 3:
            c.set(i * 8 + 2, 3, "parchment_dark")
            c.set(i * 8 + 5, 6, "parchment_dark")

    def place(icon, tile_index):
        col, row = tile_index % 4, tile_index // 4
        ox, oy = col * 8, row * 8
        parchment_fill(c, ox, oy, ox + 15, oy + 15, rng, speck=0.05)
        c.blit(icon, ox, oy)

    place(tree_icon(["leaf_orange", "leaf_red", "leaf_yellow", "leaf_yellow"], rng), 4)
    place(tree_icon(["leaf_yellow", "leaf_orange", "leaf_yellow", "glow_light"], rng), 6)
    place(fir_icon(), 12)
    place(bush_icon(), 14)
    place(rock_icon(), 20)
    place(stump_icon(), 22)
    place(shrine_icon(), 28)

    # Restack into one 8 px wide column: the raw image data is then ordered
    # tile by tile, which is what NF_LoadTilesForBg() expects.
    column = Canvas(8, rows * 4 * 8, PAL)
    for index in range(rows * 4):
        col, row = index % 4, index // 4
        for y in range(8):
            for x in range(8):
                column.px[index * 8 + y][x] = c.px[row * 8 + y][col * 8 + x]
    return column


# --- 16x16 sprites --------------------------------------------------------------
# Frames: 0 mushroom, 1 mushroom in reach, 2 Nina, 3 Mats, 4 leaf, 5 leaf lost,
#         6-8 smoke puff (small, medium, large),
#         9-14 small falling leaves (orange, red, yellow; two flutter frames each)

def smoke_icon(radius):
    c = Canvas(16, 16, PAL)
    c.circle(8, 8, radius, "smoke")
    c.circle(8 - radius * 0.3, 8 - radius * 0.3, radius * 0.5, "smoke_light")
    return c


def small_leaf(color, flat):
    c = Canvas(16, 16, PAL)
    if flat:
        c.polygon([(4, 8), (8, 5), (12, 8), (8, 11)], color)
    else:
        c.polygon([(8, 3), (11, 8), (8, 13), (5, 8)], color)
    c.line(5, 8, 11, 8, "leaf_shade") if flat else c.line(8, 4, 8, 12, "leaf_shade")
    return c


def mushroom_icon(highlight):
    c = Canvas(16, 16, PAL)
    if highlight:
        c.circle(8, 8, 7, "glow")
        c.circle(8, 8, 5.5, "glow_light")
        for x, y in ((1, 1), (14, 2), (2, 13), (13, 14)):
            c.set(x, y, "glow")
    c.rect(6, 8, 9, 13, "stem")
    c.ellipse(8, 8, 6, 4, "cap_brown", y_max=8)
    c.set(6, 6, "cap_light")
    c.set(7, 5, "cap_light")
    c.outline("ink")
    return c


def nina_icon():
    c = Canvas(16, 16, PAL)
    c.ellipse(8, 8, 6, 6.5, "hair_brown")
    c.rect(2, 8, 13, 14, "hair_brown")
    c.circle(8, 9, 4.5, "skin")
    c.rect(4, 4, 12, 6, "hair_brown")
    c.frame(3, 8, 7, 11, "glasses")
    c.frame(9, 8, 13, 11, "glasses")
    c.set(8, 9, "glasses")
    c.outline("ink")
    return c


def mats_icon(rng):
    c = Canvas(16, 16, PAL)
    for x, y in ((4, 5), (8, 3), (12, 5), (3, 8), (13, 8), (6, 3), (10, 3)):
        c.circle(x, y, 2.5, "hair_auburn" if rng.random() < 0.6 else "hair_auburn_dark")
    c.circle(8, 9, 4.5, "skin")
    c.rect(5, 5, 11, 6, "hair_auburn")
    c.set(6, 9, "ink")
    c.set(10, 9, "ink")
    c.set(5, 11, "blush")
    c.set(11, 11, "blush")
    c.outline("ink")
    return c


def leaf_icon(lost):
    c = Canvas(16, 16, PAL)
    if lost:
        c.polygon([(8, 1), (13, 6), (11, 12), (8, 14), (5, 12), (3, 6)], "slot_light")
        return c
    c.polygon([(8, 1), (13, 6), (11, 12), (8, 14), (5, 12), (3, 6)], "leaf_orange")
    c.polygon([(8, 1), (13, 6), (11, 12), (8, 14)], "leaf_red")
    c.line(8, 3, 8, 15, "leaf_shade")
    c.outline("ink")
    return c


# --- 32x32 sprites --------------------------------------------------------------
# Frames: 0 basket, 1 scarf, 2 lantern, 3 bell, 4 locked slot,
#         5 Mats normal, 6 Mats happy, 7 Mats cold, 8 Mats worried

def basket_icon():
    c = Canvas(32, 32, PAL)
    c.arc(16, 16, 10, 180, 360, "wicker_dark")
    c.arc(16, 16, 9, 180, 360, "wicker_dark")
    c.polygon([(4, 15), (28, 15), (25, 28), (7, 28)], "wicker")
    for y in range(17, 28, 3):
        c.line(6, y, 26, y, "wicker_dark")
    for x in range(8, 26, 4):
        c.line(x, 16, x + 1, 27, "wicker_dark")
    c.rect(4, 14, 27, 15, "wicker_dark")
    c.outline("ink")
    return c


def scarf_icon():
    c = Canvas(32, 32, PAL)
    c.polygon([(3, 10), (29, 6), (29, 14), (4, 18)], "scarf_red")
    c.polygon([(17, 12), (24, 11), (23, 28), (16, 28)], "scarf_red")
    for x in (8, 14, 20, 26):
        c.line(x, 8 + (x < 17), x, 16 - (x > 20), "scarf_stripe")
    c.rect(16, 18, 23, 19, "scarf_stripe")
    c.rect(16, 23, 23, 24, "scarf_stripe")
    for x in range(16, 24, 2):
        c.set(x, 29, "scarf_red")
        c.set(x, 30, "scarf_red")
    c.outline("ink")
    return c


def lantern_icon():
    c = Canvas(32, 32, PAL)
    c.arc(16, 7, 4, 180, 360, "metal")
    c.polygon([(9, 11), (23, 11), (20, 7), (12, 7)], "metal")
    c.rect(10, 11, 21, 25, "lantern_glass")
    c.circle(16, 18, 3, "glow_light")
    c.rect(10, 11, 10, 25, "metal")
    c.rect(21, 11, 21, 25, "metal")
    c.rect(15, 11, 16, 25, "metal_light")
    c.rect(8, 25, 23, 27, "metal")
    c.outline("ink")
    return c


def bell_icon():
    c = Canvas(32, 32, PAL)
    c.polygon([(16, 5), (21, 9), (22, 18), (26, 24), (6, 24), (10, 18), (11, 9)], "bell_gold")
    c.polygon([(13, 9), (16, 6), (16, 22), (11, 22)], "bell_light")
    c.rect(6, 23, 26, 24, "bell_dark")
    c.circle(16, 26, 2.5, "bell_dark")
    c.rect(14, 2, 18, 4, "ribbon")
    c.outline("ink")
    return c


def locked_icon():
    c = Canvas(32, 32, PAL)
    # A faint question mark: the item is not needed yet.
    for x, y in ((13, 9), (14, 8), (15, 8), (16, 8), (17, 8), (18, 9), (19, 10), (19, 11),
                 (18, 12), (17, 13), (16, 14), (16, 15), (16, 16), (16, 19), (16, 20)):
        c.rect(x, y, x, y + 1, "locked")
        c.set(x + 1, y, "locked")
    return c


def mats_portrait(mood, rng):
    c = Canvas(32, 32, PAL)
    # Shoulders with beige jacket.
    c.ellipse(16, 32, 13, 7, "jacket_beige")
    c.rect(14, 24, 18, 26, "skin")
    # Curls behind the face.
    curls = [(7, 12), (10, 7), (15, 5), (20, 6), (24, 9), (26, 14), (6, 17), (25, 19), (12, 5)]
    for x, y in curls:
        c.circle(x, y, 4, "hair_auburn" if rng.random() < 0.6 else "hair_auburn_dark")
    c.ellipse(16, 16, 8.5, 9, "skin")
    # Fringe curls.
    for x, y in ((10, 9), (14, 8), (18, 8), (22, 10)):
        c.circle(x, y, 2.5, "hair_auburn")

    if mood == "happy":
        c.arc(12, 17, 2, 200, 340, "ink")
        c.arc(20, 17, 2, 200, 340, "ink")
        c.arc(16, 20, 3, 20, 160, "ink")
        c.ellipse(9, 20, 2, 1, "blush")
        c.ellipse(23, 20, 2, 1, "blush")
    elif mood == "worried":
        # Raised, slanted eyebrows and a small wobbly mouth.
        c.line(10, 13, 13, 12, "hair_auburn_dark")
        c.line(19, 12, 22, 13, "hair_auburn_dark")
        c.rect(12, 15, 12, 17, "ink")
        c.rect(20, 15, 20, 17, "ink")
        c.arc(16, 23, 2.5, 200, 340, "ink")
        c.ellipse(9, 20, 2, 1, "blush")
        c.ellipse(23, 20, 2, 1, "blush")
    elif mood == "cold":
        c.rect(12, 15, 12, 17, "ink")
        c.rect(20, 15, 20, 17, "ink")
        for x in range(13, 20):
            c.set(x, 22 + (x % 2), "ink")
        c.ellipse(9, 20, 2, 1, "cold")
        c.ellipse(23, 20, 2, 1, "cold")
        c.line(3, 22, 1, 24, "cold")
        c.line(29, 22, 31, 24, "cold")
    else:
        c.rect(12, 15, 12, 17, "ink")
        c.rect(20, 15, 20, 17, "ink")
        c.arc(16, 19, 3, 40, 140, "ink")
        c.ellipse(9, 20, 2, 1, "blush")
        c.ellipse(23, 20, 2, 1, "blush")
    c.outline("ink")
    return c


def hand_icon():
    """Open hand: put the mushroom back."""
    c = Canvas(32, 32, PAL)
    c.ellipse(16, 20, 8, 7, "skin")
    for i, (x, top) in enumerate(((9, 9), (13, 6), (17, 5), (21, 7))):
        c.rect(x, top, x + 2, 18, "skin")
        c.ellipse(x + 1, top, 1.5, 1.5, "skin")
    c.polygon([(6, 17), (9, 14), (12, 20), (9, 22)], "skin")
    c.rect(11, 26, 21, 29, "jacket_green")
    c.outline("ink")
    return c


def tree_card(kind, rng):
    """A drawn autumn tree for the forest cards of the final picture."""
    c = Canvas(32, 32, PAL)
    if kind == "fir":
        c.rect(15, 25, 16, 31, "bark")
        c.polygon([(16, 1), (25, 13), (7, 13)], "fir")
        c.polygon([(16, 6), (28, 21), (4, 21)], "fir_dark")
        c.polygon([(16, 12), (30, 28), (2, 28)], "fir")
        c.polygon([(16, 12), (22, 20), (10, 20)], "fir_dark")
    else:
        base, mid, light = {
            "orange": ("leaf_shade", "leaf_orange", "leaf_yellow"),
            "red": ("leaf_shade", "leaf_red", "leaf_orange"),
            "yellow": ("leaf_orange", "leaf_yellow", "glow_light"),
        }[kind]
        c.rect(14, 20, 17, 31, "bark")
        c.line(16, 22, 20, 17, "bark")
        for cx, cy, r in ((16, 13, 10), (9, 16, 7), (23, 16, 7), (12, 8, 6), (21, 8, 6)):
            c.circle(cx, cy, r, base)
        for cx, cy, r in ((15, 11, 8), (9, 14, 5), (22, 14, 5), (13, 7, 4), (20, 7, 4)):
            c.circle(cx, cy, r, mid)
        for _ in range(7):
            c.circle(rng.randint(8, 20), rng.randint(5, 12), 1.5, light)
    c.outline("ink")
    return c


def tree_cards():
    """64x64 texture: orange, red / yellow, fir (32x32 each)."""
    rng = random.Random(33)
    c = Canvas(64, 64, PAL)
    c.blit(tree_card("orange", rng), 0, 0)
    c.blit(tree_card("red", rng), 32, 0)
    c.blit(tree_card("yellow", rng), 0, 32)
    c.blit(tree_card("fir", rng), 32, 32)
    return c


def icons_3d():
    """64x32 texture for the inspection view: basket (choose) and hand (back)."""
    c = Canvas(64, 32, PAL)
    c.blit(basket_icon(), 0, 0)
    c.blit(hand_icon(), 32, 0)
    return c


def main():
    target = sys.argv[1] if len(sys.argv) > 1 else "assets/build/ui"
    os.makedirs(target, exist_ok=True)
    rng = random.Random(20260915)

    outputs = {
        "bg_bar": make_bar(rng),
        "bg_dialog": make_dialog(rng),
        "map_tiles": make_map_tiles(rng),
        "spr_icons": sheet([mushroom_icon(False), mushroom_icon(True), nina_icon(), mats_icon(rng),
                            leaf_icon(False), leaf_icon(True),
                            smoke_icon(1.5), smoke_icon(2.2), smoke_icon(3),
                            small_leaf("leaf_orange", False), small_leaf("leaf_orange", True),
                            small_leaf("leaf_red", False), small_leaf("leaf_red", True),
                            small_leaf("leaf_yellow", False), small_leaf("leaf_yellow", True)], 16, 16, PAL),
        "spr_items": sheet([basket_icon(), scarf_icon(), lantern_icon(), bell_icon(), locked_icon(),
                            mats_portrait("normal", random.Random(7)),
                            mats_portrait("happy", random.Random(7)),
                            mats_portrait("cold", random.Random(7)),
                            mats_portrait("worried", random.Random(7))], 32, 32, PAL),
        "icons3d": icons_3d(),
        "treecards": tree_cards(),
    }
    for name, canvas in outputs.items():
        path = os.path.join(target, f"{name}.png")
        canvas.save_png(path)
        print(f"wrote {path} ({canvas.w}x{canvas.h})")


main()
