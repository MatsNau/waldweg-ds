"""The four items Nina gives to Mats: basket, scarf, lantern, bell.

Pivots:
- basket, lantern, bell: the handle, held in Mats' hand (arm-local origin at the
  hand), hanging down along -Z.
- scarf: the neck, mounted like the head.
"""
import math

import bmesh
from mathutils import Matrix, Vector

from dsmesh import finish_object, new_bmesh, paint, paint_verts


def make_basket(rng):
    bm = new_bmesh()
    body = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=6,
        radius1=0.09, radius2=0.12, depth=0.13,
        matrix=Matrix.Translation((0, 0, -0.2)))
    for f in [f for f in bm.faces if all(v in set(body["verts"]) for v in f.verts)]:
        top = f.normal.z > 0.9
        paint(bm, [f], "wicker_dark" if top else "wicker")

    # Handle: thin arch made of quads.
    handle = []
    steps = 4
    for i in range(steps + 1):
        a = math.pi * i / steps
        x = math.cos(a) * 0.1
        z = -0.135 + math.sin(a) * 0.13
        handle.append((bm.verts.new((x, -0.012, z)), bm.verts.new((x, 0.012, z))))
    faces = []
    for i in range(steps):
        faces.append(bm.faces.new((handle[i][0], handle[i + 1][0], handle[i + 1][1], handle[i][1])))
    paint(bm, faces, "wicker_dark")
    return finish_object("item_korb", bm, open_faces=[(faces, Vector((0, 0, -0.13)))])


def make_scarf(rng):
    bm = new_bmesh()
    wrap = bmesh.ops.create_cone(
        bm, cap_ends=False, segments=8,
        radius1=0.14, radius2=0.12, depth=0.07,
        matrix=Matrix.Translation((0, 0, 0.0)))
    wrap_verts = list(wrap["verts"])
    faces = paint_verts(bm, wrap_verts, "scarf_red")
    for i, f in enumerate(faces):
        if i % 3 == 0:
            paint(bm, [f], "scarf_stripe")

    # Hanging end on the front left.
    tail = bm.faces.new([bm.verts.new(c) for c in (
        (0.03, -0.14, -0.02), (0.09, -0.13, -0.02), (0.1, -0.13, -0.2), (0.04, -0.14, -0.2))])
    paint(bm, [tail], "scarf_red")
    return finish_object("item_schal", bm, open_faces=[
        (faces, Vector((0, 0, 0))), ([tail], Vector((0.06, 0, -0.1)))])


def make_lantern(rng):
    """Metal frame only; the glowing glass is item_laterne_glas (drawn unlit)."""
    bm = new_bmesh()
    roof = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=True, segments=4,
        radius1=0.08, radius2=0.0, depth=0.06,
        matrix=Matrix.Translation((0, 0, -0.08)) @ Matrix.Rotation(math.pi / 4, 4, "Z"))
    paint_verts(bm, roof["verts"], "metal")
    base = bmesh.ops.create_cube(
        bm, size=1.0, matrix=Matrix.Translation((0, 0, -0.24)) @ Matrix.Diagonal((0.1, 0.1, 0.025, 1.0)))
    paint_verts(bm, base["verts"], "metal")
    return finish_object("item_laterne", bm)


def make_lantern_glass(rng):
    bm = new_bmesh()
    glass = bmesh.ops.create_cube(
        bm, size=1.0, matrix=Matrix.Translation((0, 0, -0.17)) @ Matrix.Diagonal((0.085, 0.085, 0.12, 1.0)))
    paint_verts(bm, glass["verts"], "lantern_glass")
    return finish_object("item_laterne_glas", bm)


def make_light_disc(rng):
    """Warm translucent pool of lantern light on the ground (drawn unlit)."""
    bm = new_bmesh()
    segments = 12
    centre = bm.verts.new((0, 0, 0))
    rim = [bm.verts.new((math.cos(2 * math.pi * i / segments) * 1.8,
                         math.sin(2 * math.pi * i / segments) * 1.8, 0)) for i in range(segments)]
    faces = [bm.faces.new((rim[i], rim[(i + 1) % segments], centre)) for i in range(segments)]
    paint(bm, faces, "lantern_glass")
    return finish_object("licht_scheibe", bm, open_faces=[(faces, Vector((0, 0, -1)))])


def make_wool_hat(rng):
    """Nina's rust-coloured beanie. Pivot = neck, like the head (HEAD_CENTER_Z = 0.20)."""
    bm = new_bmesh()
    centre = Vector((0, 0, 0.20))
    cap = bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.285,
                                    matrix=Matrix.Translation(centre))
    verts = list(cap["verts"])
    bmesh.ops.delete(bm, geom=[v for v in verts if v.co.z < centre.z + 0.06], context="VERTS")
    verts = [v for v in verts if v.is_valid]
    cap_faces = paint_verts(bm, verts, "wool_rust")

    brim = bmesh.ops.create_cone(
        bm, cap_ends=False, segments=8, radius1=0.3, radius2=0.29, depth=0.07,
        matrix=Matrix.Translation((0, 0, centre.z + 0.07)))
    brim_faces = paint_verts(bm, brim["verts"], "wool_rust_dark")

    pompom = bmesh.ops.create_uvsphere(bm, u_segments=4, v_segments=2, radius=0.06,
                                       matrix=Matrix.Translation((0, 0, centre.z + 0.3)))
    paint_verts(bm, pompom["verts"], "cream")
    return finish_object("item_muetze", bm, open_faces=[
        (cap_faces, centre), (brim_faces, Vector((0, 0, centre.z + 0.07)))])


def make_bell(rng):
    bm = new_bmesh()
    bell = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=True, segments=6,
        radius1=0.08, radius2=0.03, depth=0.1,
        matrix=Matrix.Translation((0, 0, -0.1)))
    verts = list(bell["verts"])
    for f in [f for f in bm.faces if all(v in set(verts) for v in f.verts)]:
        paint(bm, [f], "bell_dark" if f.normal.z < -0.9 else "bell_gold")
    knob = bmesh.ops.create_uvsphere(
        bm, u_segments=4, v_segments=2, radius=0.025, matrix=Matrix.Translation((0, 0, -0.04)))
    paint_verts(bm, knob["verts"], "bell_gold")
    return finish_object("item_gloeckchen", bm)


def build(rng):
    return [make_basket(rng), make_scarf(rng), make_lantern(rng), make_lantern_glass(rng),
            make_bell(rng), make_light_disc(rng), make_wool_hat(rng)]
