"""World versions of the 7 mushroom species and the forest-god mushroom.
Budget: <= ~30 triangles each (the Ölbaum-Trichterling cluster has three small
funnels).

The world models only give a rough impression (cap colour and shape); the
real identification happens later in the book with the detailed models.
"""
import math

import bmesh
from mathutils import Matrix, Vector

from dsmesh import faces_from_verts, finish_object, new_bmesh, paint, paint_verts


def ring_verts(bm, radius, z, segments, offset=(0.0, 0.0), phase=0.0):
    return [bm.verts.new((offset[0] + math.cos(phase + 2 * math.pi * i / segments) * radius,
                          offset[1] + math.sin(phase + 2 * math.pi * i / segments) * radius, z))
            for i in range(segments)]


def bridge(bm, lower, upper, color):
    faces = []
    n = len(lower)
    for i in range(n):
        j = (i + 1) % n
        faces.append(bm.faces.new((lower[i], lower[j], upper[j], upper[i])))
    paint(bm, faces, color)
    return faces


def fan(bm, ring, apex, color):
    faces = []
    n = len(ring)
    for i in range(n):
        faces.append(bm.faces.new((ring[i], ring[(i + 1) % n], apex)))
    paint(bm, faces, color)
    return faces


def stem(bm, bottom_radius, top_radius, height, color, segments=4, offset=(0.0, 0.0), base_z=0.0):
    lower = ring_verts(bm, bottom_radius, base_z, segments, offset, math.pi / 4)
    upper = ring_verts(bm, top_radius, base_z + height, segments, offset, math.pi / 4)
    return bridge(bm, lower, upper, color)


def dome_cap(bm, radius, base_z, height, top_color, under_color, segments=5,
             shoulder=0.8, flake_color=None, rng=None, offset=(0.0, 0.0)):
    """Rim ring, shoulder ring and apex; underside is a flat fan (gills/pores)."""
    rim = ring_verts(bm, radius, base_z, segments, offset)
    mid = ring_verts(bm, radius * shoulder, base_z + height * 0.65, segments, offset,
                     math.pi / segments)
    apex = bm.verts.new((offset[0], offset[1], base_z + height))
    under = bm.verts.new((offset[0], offset[1], base_z + height * 0.15))

    top_faces = []
    for i in range(segments):
        j = (i + 1) % segments
        top_faces.append(bm.faces.new((rim[i], rim[j], mid[i])))
        top_faces.append(bm.faces.new((rim[j], mid[j], mid[i])))
    top_faces += [bm.faces.new((mid[i], mid[(i + 1) % segments], apex)) for i in range(segments)]
    paint(bm, top_faces, top_color)
    if flake_color and rng:
        for f in top_faces:
            if rng.random() < 0.35:
                paint(bm, [f], flake_color)

    under_faces = [bm.faces.new((rim[(i + 1) % segments], rim[i], under)) for i in range(segments)]
    paint(bm, under_faces, under_color)


def funnel(bm, base_radius, rim_radius, height, dip, side_color, top_color,
           segments=5, offset=(0.0, 0.0), base_z=0.0, tilt=0.0):
    """Chanterelle-like funnel: narrow foot, wide rim, sunken centre."""
    tilt_x = math.sin(tilt) * height * 0.4
    foot = ring_verts(bm, base_radius, base_z, segments, offset)
    rim = ring_verts(bm, rim_radius, base_z + height, segments, (offset[0] + tilt_x, offset[1]))
    centre = bm.verts.new((offset[0] + tilt_x, offset[1], base_z + height - dip))
    bridge(bm, foot, rim, side_color)
    fan(bm, rim, centre, top_color)


def make_steinpilz(rng):
    bm = new_bmesh()
    stem(bm, 0.11, 0.08, 0.2, "boletus_stem")
    dome_cap(bm, 0.21, 0.18, 0.16, "boletus_cap", "boletus_tubes")
    return finish_object("pilz_steinpilz", bm)


def make_satansroehrling(rng):
    bm = new_bmesh()
    stem(bm, 0.13, 0.08, 0.19, "satan_stem")
    dome_cap(bm, 0.2, 0.17, 0.14, "satan_cap", "satan_pores")
    return finish_object("pilz_satansroehrling", bm)


def make_champignon(rng):
    bm = new_bmesh()
    stem(bm, 0.05, 0.045, 0.2, "champ_cap")
    dome_cap(bm, 0.18, 0.18, 0.12, "champ_cap", "champ_gills", shoulder=0.75)
    return finish_object("pilz_champignon", bm)


def make_knollenblaetterpilz(rng):
    bm = new_bmesh()
    bulb = bmesh.ops.create_uvsphere(
        bm, u_segments=4, v_segments=2, radius=0.08,
        matrix=Matrix.Translation((0, 0, 0.04)) @ Matrix.Diagonal((1.0, 1.0, 0.6, 1.0)))
    paint_verts(bm, bulb["verts"], "volva")
    stem(bm, 0.05, 0.04, 0.26, "white", base_z=0.02)
    dome_cap(bm, 0.19, 0.26, 0.09, "amanita_cap", "white", shoulder=0.85)
    return finish_object("pilz_knollenblaetterpilz", bm)


def make_pfifferling(rng):
    bm = new_bmesh()
    funnel(bm, 0.035, 0.17, 0.22, 0.05, "chanterelle_ridges", "chanterelle")
    return finish_object("pilz_pfifferling", bm)


def make_fliegenpilz(rng):
    bm = new_bmesh()
    bulb = bmesh.ops.create_uvsphere(
        bm, u_segments=4, v_segments=2, radius=0.08,
        matrix=Matrix.Translation((0, 0, 0.04)) @ Matrix.Diagonal((1.0, 1.0, 0.6, 1.0)))
    paint_verts(bm, bulb["verts"], "cream")
    stem(bm, 0.06, 0.045, 0.24, "stem", base_z=0.02)
    dome_cap(bm, 0.23, 0.24, 0.14, "fly_red", "gills", flake_color="cream", rng=rng)
    return finish_object("pilz_fliegenpilz", bm)


def make_oelbaum_trichterling(rng):
    """A tuft of three funnels. Origin = top of the stump it grows on."""
    bm = new_bmesh()
    for (x, y), size, tilt in (((0.0, 0.0), 1.0, 0.0), ((0.12, 0.07), 0.8, 0.5),
                               ((-0.1, 0.09), 0.75, -0.5)):
        funnel(bm, 0.03 * size, 0.14 * size, 0.22 * size, 0.03,
               "omphalotus_gills", "omphalotus", offset=(x, y), tilt=tilt)
    return finish_object("pilz_oelbaum_trichterling", bm)


def make_waldgott_pilz(rng):
    """Black-and-white spotted and glowing (drawn unlit). Spots like a cow."""
    bm = new_bmesh()
    stem(bm, 0.06, 0.04, 0.34, "god_stem")
    dome_cap(bm, 0.2, 0.3, 0.22, "god_cap", "god_stem", segments=6, shoulder=0.7,
             flake_color="god_spot", rng=rng)
    return finish_object("pilz_waldgott", bm)


def build(rng):
    return [
        make_steinpilz(rng),
        make_satansroehrling(rng),
        make_champignon(rng),
        make_knollenblaetterpilz(rng),
        make_pfifferling(rng),
        make_fliegenpilz(rng),
        make_oelbaum_trichterling(rng),
        make_waldgott_pilz(rng),
    ]
