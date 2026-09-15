"""Forest models: ground, trees, bush, rock and stump.

Budgets (triangles): ground ~200, round tree ~60, fir ~30, bush/rock/stump ~20.
Mushrooms live in models_mushrooms.py.
"""
import math

import bmesh
from mathutils import Matrix, Vector

from dsmesh import faces_from_verts, finish_object, new_bmesh, paint, paint_verts

# Half size of the ground mesh (obj2dl limit is +-8). The game scales it by 2.
GROUND_HALF = 7.0


def jitter(rng, verts, amount):
    for v in verts:
        v.co += Vector((rng.uniform(-amount, amount), rng.uniform(-amount, amount),
                        rng.uniform(-amount, amount)))


def make_ground(rng):
    bm = new_bmesh()
    bmesh.ops.create_grid(bm, x_segments=10, y_segments=10, size=GROUND_HALF)
    for v in bm.verts:
        v.co.z = 0.0
    bmesh.ops.triangulate(bm, faces=bm.faces)
    choices = ["moss"] * 6 + ["moss_dark"] * 3 + ["soil"] * 2 + ["leaf_brown"] * 2
    for f in bm.faces:
        paint(bm, [f], rng.choice(choices))
    return finish_object("ground", bm)


def make_tree_round(rng, name, leaf_colors):
    bm = new_bmesh()

    trunk = bmesh.ops.create_cone(
        bm, cap_ends=False, segments=5,
        radius1=0.2, radius2=0.12, depth=1.5,
        matrix=Matrix.Translation((0, 0, 0.75)))
    paint_verts(bm, trunk["verts"], "bark")

    crown = bmesh.ops.create_uvsphere(
        bm, u_segments=7, v_segments=5, radius=1.0,
        matrix=Matrix.Translation((0, 0, 2.0)) @ Matrix.Diagonal((1.0, 1.0, 0.9, 1.0)))
    jitter(rng, crown["verts"], 0.1)
    for f in faces_from_verts(bm, crown["verts"]):
        paint(bm, [f], rng.choice(leaf_colors))

    return finish_object(name, bm)


def make_tree_fir(rng):
    bm = new_bmesh()

    trunk = bmesh.ops.create_cone(
        bm, cap_ends=False, segments=4,
        radius1=0.14, radius2=0.1, depth=0.6,
        matrix=Matrix.Translation((0, 0, 0.3)))
    paint_verts(bm, trunk["verts"], "bark_dark")

    for radius, depth, z, color in ((0.9, 1.3, 1.1, "fir_dark"), (0.65, 1.1, 1.9, "fir")):
        tier = bmesh.ops.create_cone(
            bm, cap_ends=True, cap_tris=True, segments=6,
            radius1=radius, radius2=0.0, depth=depth,
            matrix=Matrix.Translation((0, 0, z)))
        jitter(rng, tier["verts"], 0.05)
        paint_verts(bm, tier["verts"], color)

    return finish_object("tree_fir", bm)


def make_bush(rng):
    bm = new_bmesh()
    blob = bmesh.ops.create_icosphere(
        bm, subdivisions=1, radius=0.5,
        matrix=Matrix.Translation((0, 0, 0.3)) @ Matrix.Diagonal((1.2, 1.0, 0.7, 1.0)))
    verts = list(blob["verts"])
    bmesh.ops.delete(bm, geom=[v for v in verts if v.co.z < 0.05], context="VERTS")
    verts = [v for v in verts if v.is_valid]
    jitter(rng, verts, 0.06)
    for f in faces_from_verts(bm, verts):
        paint(bm, [f], rng.choice(["bush", "leaf_brown", "leaf_orange"]))
    return finish_object("bush", bm)


def make_rock(rng):
    bm = new_bmesh()
    rock = bmesh.ops.create_icosphere(
        bm, subdivisions=0, radius=0.45,
        matrix=Matrix.Translation((0, 0, 0.12)) @ Matrix.Diagonal((1.2, 1.0, 0.6, 1.0)))
    jitter(rng, rock["verts"], 0.08)
    for f in faces_from_verts(bm, rock["verts"]):
        paint(bm, [f], "stone" if f.calc_center_median().z > 0.12 else "stone_dark")
    return finish_object("rock", bm)


def make_stump(rng):
    bm = new_bmesh()
    stump = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=7,
        radius1=0.42, radius2=0.34, depth=0.45,
        matrix=Matrix.Translation((0, 0, 0.22)))
    jitter(rng, [v for v in stump["verts"] if v.co.z > 0.3], 0.03)
    for f in faces_from_verts(bm, stump["verts"]):
        top = abs(f.normal.z) > 0.9 and f.calc_center_median().z > 0.3
        paint(bm, [f], "wood_cut" if top else "bark")
    return finish_object("stump", bm)


def make_shrine(rng):
    """Old mossy stone shrine in the central meadow. The offering is placed on
    the altar stone (top at z = SHRINE_ALTAR_Z, keep in sync with the game)."""
    bm = new_bmesh()

    # Low round platform.
    base = bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=8,
                                 radius1=1.0, radius2=0.9, depth=0.16,
                                 matrix=Matrix.Translation((0, 0, 0.08)))
    for f in faces_from_verts(bm, base["verts"]):
        paint(bm, [f], "moss_dark" if f.normal.z > 0.9 and rng.random() < 0.4 else "stone_dark")

    # Altar stone.
    altar = bmesh.ops.create_cube(bm, size=1.0,
                                  matrix=Matrix.Translation((0, 0, 0.4)) @ Matrix.Diagonal((0.7, 0.5, 0.48, 1.0)))
    jitter(rng, altar["verts"], 0.025)
    for f in faces_from_verts(bm, altar["verts"]):
        paint(bm, [f], "moss" if f.normal.z > 0.9 else "stone")

    # Two standing stones behind the altar with a lintel.
    for x in (-0.62, 0.62):
        pillar = bmesh.ops.create_cube(bm, size=1.0,
                                       matrix=Matrix.Translation((x, 0.45, 0.75)) @ Matrix.Diagonal((0.22, 0.22, 1.3, 1.0)))
        jitter(rng, pillar["verts"], 0.03)
        for f in faces_from_verts(bm, pillar["verts"]):
            paint(bm, [f], "stone" if rng.random() < 0.7 else "moss_dark")
    lintel = bmesh.ops.create_cube(bm, size=1.0,
                                   matrix=Matrix.Translation((0, 0.45, 1.46)) @ Matrix.Diagonal((1.6, 0.28, 0.18, 1.0)))
    jitter(rng, lintel["verts"], 0.02)
    for f in faces_from_verts(bm, lintel["verts"]):
        paint(bm, [f], "moss" if f.normal.z > 0.9 else "stone_dark")

    return finish_object("shrine", bm)


def make_shadow(rng):
    """Flat disc (radius 1) for soft blob shadows, drawn translucent and
    stretched away from the sun by the game."""
    bm = new_bmesh()
    segments = 8
    centre = bm.verts.new((0, 0, 0))
    rim = [bm.verts.new((math.cos(2 * math.pi * i / segments), math.sin(2 * math.pi * i / segments), 0))
           for i in range(segments)]
    faces = [bm.faces.new((rim[i], rim[(i + 1) % segments], centre)) for i in range(segments)]
    paint(bm, faces, "god_spot")
    return finish_object("shadow", bm, open_faces=[(faces, Vector((0, 0, -1)))])


def make_leaf(name, color):
    """A small falling leaf: a diamond with a bent tip, drawn double-sided."""
    bm = new_bmesh()
    v = [bm.verts.new(c) for c in ((0, -0.08, 0), (0.05, 0, 0.01), (0, 0.08, 0), (-0.05, 0, 0.01))]
    faces = [bm.faces.new((v[0], v[1], v[2])), bm.faces.new((v[0], v[2], v[3]))]
    paint(bm, faces, color)
    return finish_object(name, bm, open_faces=[(faces, Vector((0, 0, -1)))])


def build(rng):
    autumn = ["leaf_orange"] * 5 + ["leaf_red"] * 3 + ["leaf_yellow"] * 2
    golden = ["leaf_yellow"] * 5 + ["leaf_orange"] * 3 + ["leaf_brown"] * 2
    return [
        make_ground(rng),
        make_tree_round(rng, "tree_round", autumn),
        make_tree_round(rng, "tree_golden", golden),
        make_tree_fir(rng),
        make_bush(rng),
        make_rock(rng),
        make_stump(rng),
        make_shrine(rng),
        make_shadow(rng),
        make_leaf("leaf_a", "leaf_orange"),
        make_leaf("leaf_b", "leaf_red"),
        make_leaf("leaf_c", "leaf_yellow"),
    ]
