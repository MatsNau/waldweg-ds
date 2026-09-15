"""Scenery of the final picture, spread over both screens.

- build():          end_hill, the DS model for the lower (3D) screen: the meadow
                    the three sit on (top at z = 0), sloping away. Game scale 2.
- build_backdrop(): distant hills, mountain ridge and the village with chimneys.
                    Only rendered in Blender (render_ending.py) into the drawn
                    picture of the upper screen, never exported for the DS.

Blender -Y is +Z in game (towards the camera), so the distance is at positive Y.
"""
import math

import bmesh
from mathutils import Matrix, Vector

from dsmesh import faces_from_verts, finish_object, new_bmesh, paint, paint_verts


HILL_CREST_Z = 1.2   # game z where the hilltop ends and the slope begins
HILL_STEEPNESS = 0.16
HILL_FLOOR = -9.0    # valley floor height
OPPOSITE_Z = -12.0   # where the opposite slope starts rising again
OPPOSITE_RISE = 0.1
OPPOSITE_TOP = 7.0
OPPOSITE_RISE_MAX = 14.0
HILL_SCALE = 3.5


def make_hill(rng):
    """Hilltop with a clear crest in front of the three, falling down to the
    valley floor and rising again on the other side (game scale HILL_SCALE).
    Keep the formula in sync with HillHeight() in source/game/EndingState.cpp."""
    bm = new_bmesh()
    bmesh.ops.create_grid(bm, x_segments=12, y_segments=12, size=7.0)
    for v in bm.verts:
        # World units are HILL_SCALE times the Blender units; game z = -Blender y.
        game_z = -v.co.y * HILL_SCALE
        game_x = v.co.x * HILL_SCALE
        drop = min(max(0.0, HILL_CREST_Z - game_z), 8.0)
        height = max(-HILL_STEEPNESS * drop * drop - 0.003 * game_x * game_x, HILL_FLOOR)
        rise = min(max(0.0, OPPOSITE_Z - game_z), OPPOSITE_RISE_MAX)
        height = min(height + OPPOSITE_RISE * rise * rise, OPPOSITE_TOP)
        # obj2dl only accepts coordinates within +-8.
        v.co.z = height / HILL_SCALE + rng.uniform(-0.02, 0.02)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    # Grass only: the faces are big, a single leaf-coloured one would be a huge
    # orange triangle next to the three (the forest brings the autumn colours).
    colors = ["moss"] * 3 + ["moss_dark"]
    for f in bm.faces:
        paint(bm, [f], rng.choice(colors))
    return finish_object("end_hill", bm)


def make_ridge(rng):
    """Zig-zag mountain band far away: a wall with a jagged top."""
    bm = new_bmesh()
    points = 22
    bottom, top = [], []
    for i in range(points + 1):
        x = -70.0 + 140.0 * i / points
        peak = rng.uniform(4.0, 11.0) if i % 2 == 0 else rng.uniform(1.0, 4.0)
        bottom.append(bm.verts.new((x, 60, -4.0)))
        top.append(bm.verts.new((x, 60 + rng.uniform(-2, 2), peak)))
    faces = []
    for i in range(points):
        faces.append(bm.faces.new((bottom[i], bottom[i + 1], top[i + 1], top[i])))
    for f in faces:
        paint(bm, [f], "fir_dark" if rng.random() < 0.6 else "stone_dark")
    return finish_object("end_ridge", bm, open_faces=[(faces, Vector((0, 100, 0)))])


def make_far_hills(rng):
    """Rolling autumn hills between the meadow and the mountains."""
    bm = new_bmesh()
    for x, y, rx, ry, rz, color in ((0, 46, 30, 9, 5.5, "fir"), (-16, 34, 18, 8, 4.0, "moss_dark"),
                                    (10, 28, 15, 7, 3.2, "moss"), (26, 40, 14, 7, 4.5, "bush")):
        hill = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=1.0,
                                         matrix=Matrix.Translation((x, y, -2.0)) @ Matrix.Diagonal((rx, ry, rz, 1.0)))
        paint(bm, faces_from_verts(bm, hill["verts"]), color)
    return finish_object("end_far_hills", bm)


VILLAGE_ORIGIN = (7.0, 30.0, 1.4)  # on the right-hand hill
VILLAGE_SCALE = 3.0


def chimney_tops():
    """World positions of the chimney tops (for the smoke sprites)."""
    return [Vector(VILLAGE_ORIGIN) + Vector(p) * VILLAGE_SCALE for p in _chimneys]


_chimneys = []


def make_village(rng):
    bm = new_bmesh()
    _chimneys.clear()
    houses = [(-1.6, 0.2, 0.9), (-0.5, -0.3, 1.1), (0.7, 0.1, 1.0), (1.8, -0.2, 0.8), (0.1, 0.9, 0.9)]
    roofs = ["scarf_red", "wool_rust", "bark", "scarf_red", "wool_rust"]
    for (x, y, size), roof_color in zip(houses, roofs):
        w, h = 0.45 * size, 0.35 * size
        body = bmesh.ops.create_cube(bm, size=1.0,
                                     matrix=Matrix.Translation((x, y, h / 2)) @ Matrix.Diagonal((w, w * 0.8, h, 1.0)))
        paint_verts(bm, body["verts"], "wood_cut")
        # Gable roof as a prism.
        r = [bm.verts.new(c) for c in (
            (x - w * 0.6, y - w * 0.5, h), (x + w * 0.6, y - w * 0.5, h),
            (x + w * 0.6, y + w * 0.5, h), (x - w * 0.6, y + w * 0.5, h),
            (x - w * 0.6, y, h + 0.3 * size), (x + w * 0.6, y, h + 0.3 * size))]
        roof_faces = [
            bm.faces.new((r[0], r[1], r[5], r[4])),
            bm.faces.new((r[2], r[3], r[4], r[5])),
            bm.faces.new((r[1], r[2], r[5])),
            bm.faces.new((r[3], r[0], r[4])),
        ]
        paint(bm, roof_faces, roof_color)
        chimney = bmesh.ops.create_cube(
            bm, size=1.0,
            matrix=Matrix.Translation((x + w * 0.25, y + w * 0.2, h + 0.3 * size)) @ Matrix.Diagonal((0.08, 0.08, 0.3 * size, 1.0)))
        paint_verts(bm, chimney["verts"], "stone_dark")
        _chimneys.append((x + w * 0.25, y + w * 0.2, h + 0.45 * size))
    matrix = Matrix.Translation(VILLAGE_ORIGIN) @ Matrix.Diagonal((VILLAGE_SCALE,) * 3 + (1.0,))
    bmesh.ops.transform(bm, matrix=matrix, verts=bm.verts)
    return finish_object("end_village", bm)


def build(rng):
    return [make_hill(rng)]


def make_far_trees(rng, hills):
    """Small autumn trees standing on the distant hills (one mesh)."""
    import bpy
    import models_world

    bm = new_bmesh()
    palettes = [["leaf_orange"] * 4 + ["leaf_red"] * 2 + ["leaf_yellow"],
                ["leaf_yellow"] * 3 + ["leaf_orange"] * 2 + ["leaf_brown"],
                ["leaf_red"] * 3 + ["leaf_orange"] * 2]
    placed = 0
    for _ in range(200):
        if placed >= 26:
            break
        x = rng.uniform(-34, 34)
        y = rng.uniform(24, 44)
        # Keep the village and the sun free.
        if abs(x - VILLAGE_ORIGIN[0]) < 6 and abs(y - VILLAGE_ORIGIN[1]) < 6:
            continue
        if -16 < x < -4 and y > 36:
            continue
        hit, location, _, _ = hills.ray_cast(Vector((x, y, 30)), Vector((0, 0, -1)))
        if not hit:
            continue
        tree = models_world.make_tree_round(rng, "tmp_tree", rng.choice(palettes))
        size = rng.uniform(0.9, 1.4)
        matrix = Matrix.Translation(location - Vector((0, 0, 0.2))) @ Matrix.Diagonal((size, size, size, 1.0))
        mesh = tree.data
        layer = mesh.attributes.get("swatch")
        verts = [bm.verts.new(matrix @ vert.co) for vert in mesh.vertices]
        for polygon in mesh.polygons:
            face = bm.faces.new([verts[i] for i in polygon.vertices])
            color = models_world_palette_name(layer.data[polygon.index].value) if layer else "leaf_orange"
            paint(bm, [face], color)
        bpy.data.objects.remove(tree)
        placed += 1
    return finish_object("end_far_trees", bm)


def make_valley(rng):
    """Green valley floor between the viewer and the far hills, with a river
    winding across and a small wooden bridge."""
    bm = new_bmesh()
    ground = bmesh.ops.create_grid(bm, x_segments=12, y_segments=4, size=1.0,
                                   matrix=Matrix.Translation((0, 20, -2.6)) @ Matrix.Diagonal((45, 14, 1, 1)))
    for f in faces_from_verts(bm, ground["verts"]):
        paint(bm, [f], rng.choice(["moss", "moss", "moss_dark"]))

    # River: a ribbon following a gentle curve.
    left, right = [], []
    steps = 16

    def river_y(x):
        return 11.5 + 1.8 * math.sin((x + 45) / 90 * steps * 0.9)

    for i in range(steps + 1):
        x = -45 + 90 * i / steps
        left.append(bm.verts.new((x, river_y(x) - 1.1, -2.55)))
        right.append(bm.verts.new((x, river_y(x) + 1.1, -2.55)))
    water = []
    for i in range(steps):
        water.append(bm.faces.new((left[i], left[i + 1], right[i + 1], right[i])))
    for i, f in enumerate(water):
        paint(bm, [f], "jeans" if i % 3 else "jeans_dark")

    # Bridge across the river near the middle.
    bx = 3.4
    by = river_y(bx)
    deck = bmesh.ops.create_cube(bm, size=1.0,
                                 matrix=Matrix.Translation((bx, by, -2.3)) @ Matrix.Diagonal((1.6, 3.4, 0.18, 1)))
    paint_verts(bm, deck["verts"], "wood_cut")
    for side in (-1, 1):
        rail = bmesh.ops.create_cube(bm, size=1.0,
                                     matrix=Matrix.Translation((bx + 0.75 * side, by, -1.95)) @ Matrix.Diagonal((0.12, 3.4, 0.12, 1)))
        paint_verts(bm, rail["verts"], "bark")
        for dy in (-1.5, 0, 1.5):
            post = bmesh.ops.create_cube(bm, size=1.0,
                                         matrix=Matrix.Translation((bx + 0.75 * side, by + dy, -2.1)) @ Matrix.Diagonal((0.12, 0.12, 0.45, 1)))
            paint_verts(bm, post["verts"], "bark")
    return finish_object("end_valley", bm, open_faces=[(water, Vector((0, 12, -10)))])


def make_valley_trees(rng):
    """Autumn trees along the river banks."""
    import bpy
    import models_world

    bm = new_bmesh()
    palettes = [["leaf_orange"] * 4 + ["leaf_red"] * 2 + ["leaf_yellow"],
                ["leaf_yellow"] * 3 + ["leaf_orange"] * 2 + ["leaf_brown"],
                ["leaf_red"] * 3 + ["leaf_orange"] * 2]
    placed = 0
    for _ in range(100):
        if placed >= 18:
            break
        x = rng.uniform(-13, 14)
        y = rng.choice([rng.uniform(6.5, 8.8), rng.uniform(14.8, 20.0)])
        if abs(x - 3.4) < 3:
            continue  # keep the bridge visible
        tree = models_world.make_tree_round(rng, "tmp_tree", rng.choice(palettes))
        size = rng.uniform(0.5, 0.8)
        matrix = Matrix.Translation((x, y, -2.6)) @ Matrix.Diagonal((size, size, size, 1.0))
        mesh = tree.data
        layer = mesh.attributes.get("swatch")
        verts = [bm.verts.new(matrix @ vert.co) for vert in mesh.vertices]
        for polygon in mesh.polygons:
            face = bm.faces.new([verts[i] for i in polygon.vertices])
            paint(bm, [face], models_world_palette_name(layer.data[polygon.index].value) if layer else "leaf_orange")
        bpy.data.objects.remove(tree)
        placed += 1
    return finish_object("end_valley_trees", bm)


def models_world_palette_name(index):
    from dsmesh import PALETTE
    return PALETTE[index][0]


def build_backdrop(rng):
    hills = make_far_hills(rng)
    return [hills, make_ridge(rng), make_far_trees(rng, hills), make_village(rng),
            make_valley(rng), make_valley_trees(rng)]
