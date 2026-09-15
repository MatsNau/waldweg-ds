"""Shroomchen, the forest god: a black-and-white spotted cow (like the offering
mushroom) that grows into a giant glowing deity (no halo, on request).

Rigid parts, the cow faces -Y (+Z in game):
- cow_body: body, head, horns, tail, udder. Origin on the ground below the body.
- cow_leg:  pivot at the hip (z = 0), hangs down to the ground (HIP_Z below).
- cow_crown: flower wreath around the horns (deity only).
Keep HIP_Z, LEG_X, LEG_Y in sync with source/entities/Shroomchen.cpp.
"""
import math

import bmesh
from mathutils import Matrix, Vector

from dsmesh import faces_from_verts, finish_object, new_bmesh, paint, paint_verts

HIP_Z = 0.4
LEG_X = 0.2
LEG_Y = 0.3
LEG_TOP = 0.16  # the leg reaches this far above the hip, into the belly (no gap)
BACK_Z = 0.98  # top of the back, where Nina and Mats sit


def spotted(bm, verts, rng, spots=4, radius=0.22):
    """Round black patches: faces near a few random spot centres turn black."""
    faces = faces_from_verts(bm, verts)
    centres = [faces[rng.randrange(len(faces))].calc_center_median().copy() for _ in range(spots)]
    for f in faces:
        c = f.calc_center_median()
        near = any((c - centre).length < radius for centre in centres)
        paint(bm, [f], "god_spot" if near else "white")


def make_body(rng):
    bm = new_bmesh()

    body = bmesh.ops.create_uvsphere(
        bm, u_segments=8, v_segments=6, radius=0.55,
        matrix=Matrix.Translation((0, 0, 0.64)) @ Matrix.Diagonal((0.68, 1.0, 0.62, 1.0)))
    spotted(bm, body["verts"], rng, spots=4, radius=0.25)

    # Head in front (-Y) with a pink muzzle.
    head_centre = Vector((0, -0.62, 0.88))
    head = bmesh.ops.create_uvsphere(
        bm, u_segments=8, v_segments=5, radius=0.24,
        matrix=Matrix.Translation(head_centre) @ Matrix.Diagonal((0.9, 1.0, 0.95, 1.0)))
    spotted(bm, head["verts"], rng, spots=1, radius=0.14)
    muzzle = bmesh.ops.create_uvsphere(
        bm, u_segments=6, v_segments=4, radius=0.13,
        matrix=Matrix.Translation(head_centre + Vector((0, -0.2, -0.08))) @ Matrix.Diagonal((1.1, 0.8, 0.8, 1.0)))
    paint_verts(bm, muzzle["verts"], "blush")

    # Eyes, ears and small horns.
    for side in (-1, 1):
        eye = bmesh.ops.create_uvsphere(
            bm, u_segments=4, v_segments=2, radius=0.035,
            matrix=Matrix.Translation(head_centre + Vector((0.12 * side, -0.19, 0.06))))
        paint_verts(bm, eye["verts"], "eye")
        ear = bmesh.ops.create_cone(
            bm, cap_ends=True, cap_tris=True, segments=4, radius1=0.07, radius2=0.0, depth=0.16,
            matrix=Matrix.Translation(head_centre + Vector((0.24 * side, 0.02, 0.08)))
            @ Matrix.Rotation(math.radians(-90 * side), 4, "Y"))
        paint_verts(bm, ear["verts"], "white")
        horn = bmesh.ops.create_cone(
            bm, cap_ends=False, segments=4, radius1=0.04, radius2=0.0, depth=0.18,
            matrix=Matrix.Translation(head_centre + Vector((0.13 * side, 0.03, 0.26)))
            @ Matrix.Rotation(math.radians(20 * side), 4, "Y"))
        paint_verts(bm, horn["verts"], "stem")

    # Udder and tail.
    udder = bmesh.ops.create_uvsphere(
        bm, u_segments=6, v_segments=3, radius=0.12,
        matrix=Matrix.Translation((0, 0.22, 0.33)) @ Matrix.Diagonal((1.0, 1.0, 0.6, 1.0)))
    paint_verts(bm, udder["verts"], "blush")
    tail = bmesh.ops.create_cone(
        bm, cap_ends=False, segments=4, radius1=0.03, radius2=0.02, depth=0.45,
        matrix=Matrix.Translation((0, 0.56, 0.55)) @ Matrix.Rotation(math.radians(20), 4, "X"))
    paint_verts(bm, tail["verts"], "white")
    tuft = bmesh.ops.create_uvsphere(bm, u_segments=4, v_segments=2, radius=0.06,
                                     matrix=Matrix.Translation((0, 0.64, 0.33)))
    paint_verts(bm, tuft["verts"], "god_spot")
    return finish_object("cow_body", bm)


def make_leg(rng):
    bm = new_bmesh()
    length = HIP_Z - 0.08 + LEG_TOP
    leg = bmesh.ops.create_cone(
        bm, cap_ends=False, segments=5, radius1=0.1, radius2=0.1, depth=length,
        matrix=Matrix.Translation((0, 0, LEG_TOP - length / 2)))
    paint_verts(bm, leg["verts"], "white")
    hoof = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=5, radius1=0.11, radius2=0.1, depth=0.08,
        matrix=Matrix.Translation((0, 0, -HIP_Z + 0.04)))
    paint_verts(bm, hoof["verts"], "god_spot")
    return finish_object("cow_leg", bm)


def make_crown(rng):
    """Wreath of little flowers on the head."""
    bm = new_bmesh()
    centre = Vector((0, -0.6, 1.1))
    ring = bmesh.ops.create_cone(bm, cap_ends=False, segments=10, radius1=0.2, radius2=0.19, depth=0.04,
                                 matrix=Matrix.Translation(centre))
    paint_verts(bm, ring["verts"], "fir")
    colors = ["leaf_yellow", "scarf_red", "wool_rust", "cream", "leaf_orange"]
    for i in range(8):
        a = 2 * math.pi * i / 8
        pos = centre + Vector((math.cos(a) * 0.2, math.sin(a) * 0.2, 0.03))
        blossom = bmesh.ops.create_uvsphere(bm, u_segments=4, v_segments=2, radius=0.05,
                                            matrix=Matrix.Translation(pos))
        paint_verts(bm, blossom["verts"], colors[i % len(colors)])
    return finish_object("cow_crown", bm)


def build(rng):
    return [make_body(rng), make_leg(rng), make_crown(rng)]
