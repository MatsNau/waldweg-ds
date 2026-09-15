"""Detailed mushrooms for the inspection view and the book illustrations.

Each model is about 1.2 units tall (origin at the stem base) and shows the
identification features from the book: tubes/pores, gills, ridges, stem net,
ring, bulb and volva, flakes. Budget: 250-500 triangles.

Gills are thin double-sided fins, so they look right from every angle.
"""
import math

import bmesh
from mathutils import Matrix, Vector

from dsmesh import finish_object, new_bmesh, paint


def lathe(bm, profile, segments, colors, pattern=None, cap_top=False, cap_bottom=False, phase=0.0):
    """Revolves a (radius, z) profile around Z.

    colors: one colour per band (len(profile) - 1) or a single colour.
    pattern: optional function (band, segment) -> colour name overriding colors.
    """
    rings = []
    for radius, z in profile:
        ring = []
        for i in range(segments):
            a = phase + 2 * math.pi * i / segments
            ring.append(bm.verts.new((math.cos(a) * radius, math.sin(a) * radius, z)))
        rings.append(ring)

    faces = []
    for band in range(len(profile) - 1):
        lower, upper = rings[band], rings[band + 1]
        for i in range(segments):
            j = (i + 1) % segments
            face = bm.faces.new((lower[i], lower[j], upper[j], upper[i]))
            color = colors if isinstance(colors, str) else colors[band]
            if pattern is not None:
                color = pattern(band, i) or color
            paint(bm, [face], color)
            faces.append(face)

    def fan(ring, z, color, flip):
        centre = bm.verts.new((0, 0, z))
        for i in range(segments):
            j = (i + 1) % segments
            verts = (ring[j], ring[i], centre) if flip else (ring[i], ring[j], centre)
            face = bm.faces.new(verts)
            paint(bm, [face], color)
            faces.append(face)

    if cap_top:
        color = colors if isinstance(colors, str) else colors[-1]
        fan(rings[-1], profile[-1][1], color, False)
    if cap_bottom:
        color = colors if isinstance(colors, str) else colors[0]
        fan(rings[0], profile[0][1], color, True)
    return faces


def fins(bm, count, inner, outer, z_inner, z_outer, color, thickness=0.006, depth=0.035):
    """Radial double-sided fins (gills or ridges) under a cap: 4 triangles each."""
    for i in range(count):
        a = 2 * math.pi * i / count
        d = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-d.y, d.x, 0)) * thickness
        p0 = d * inner + Vector((0, 0, z_inner))
        p1 = d * outer + Vector((0, 0, z_outer))
        up = Vector((0, 0, depth))
        for s in (1, -1):
            q = [bm.verts.new(p + side * s) for p in (p0, p1, p1 + up, p0 + up)]
            face = bm.faces.new(q if s > 0 else tuple(reversed(q)))
            paint(bm, [face], color)


def flakes(bm, rng, count, radius, z_of, color, size=0.055):
    for _ in range(count):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0.1, 0.85) * radius
        pos = Vector((math.cos(a) * r, math.sin(a) * r, z_of(r) + 0.01))
        flake = bmesh.ops.create_uvsphere(
            bm, u_segments=4, v_segments=2, radius=size,
            matrix=Matrix.Translation(pos) @ Matrix.Diagonal((1.0, 1.0, 0.45, 1.0)))
        paint(bm, [f for f in bm.faces if all(v in set(flake["verts"]) for v in f.verts)], color)


def surface_height(profile, radius):
    """Height of a lathe profile (ordered from rim to apex) at a given radius."""
    for (r0, z0), (r1, z1) in zip(profile, profile[1:]):
        if r1 <= radius <= r0:
            t = (r0 - radius) / (r0 - r1) if r0 != r1 else 0.0
            return z0 + (z1 - z0) * t
    return profile[-1][1]


def dome_profile(radius, rim_z, height, steps=5, flat=0.0):
    """Cap outline from the rim to the apex."""
    profile = []
    for i in range(steps + 1):
        t = i / steps
        angle = t * math.pi / 2
        r = radius * math.cos(angle) * (1 - flat * t * t)
        z = rim_z + height * math.sin(angle)
        profile.append((max(r, 0.001), z))
    return profile


def checker(color_a, color_b, band_filter=None):
    def pattern(band, segment):
        if band_filter is not None and band not in band_filter:
            return None
        return color_a if (band + segment) % 2 == 0 else color_b
    return pattern


# --- Species -----------------------------------------------------------------

def make_steinpilz(rng):
    bm = new_bmesh()
    # Thick, bulbous pale stem with a fine white net on the upper part.
    lathe(bm, [(0.2, 0.0), (0.26, 0.15), (0.24, 0.35), (0.18, 0.55), (0.16, 0.62)], 12,
          "boletus_stem", pattern=checker("white", "boletus_stem", band_filter={2, 3}), cap_bottom=True)
    # Underside: spongy tubes (checker = pores).
    lathe(bm, [(0.16, 0.6), (0.3, 0.57), (0.45, 0.58), (0.55, 0.62)], 16,
          ["boletus_tubes", "boletus_tubes", "boletus_tubes"],
          pattern=checker("boletus_tubes", "stem"))
    # Brown bun-shaped cap.
    lathe(bm, dome_profile(0.55, 0.62, 0.42, flat=0.1), 16, "boletus_cap", cap_top=True)
    return finish_object("detail_steinpilz", bm)


def make_satansroehrling(rng):
    bm = new_bmesh()
    # Bulbous yellow stem with a red net.
    lathe(bm, [(0.2, 0.0), (0.32, 0.18), (0.3, 0.36), (0.2, 0.55), (0.17, 0.62)], 16,
          "satan_stem", pattern=checker("leaf_red", "satan_stem", band_filter={2, 3}), cap_bottom=True)
    # Red pores underneath.
    lathe(bm, [(0.17, 0.6), (0.3, 0.57), (0.45, 0.58), (0.54, 0.62)], 16,
          "satan_pores", pattern=checker("satan_pores", "fly_red"))
    # Pale grey-white cap.
    lathe(bm, dome_profile(0.54, 0.62, 0.36, flat=0.15), 16, "satan_cap", cap_top=True)
    return finish_object("detail_satansroehrling", bm)


def make_champignon(rng):
    bm = new_bmesh()
    # Slim white stem, no bulb.
    lathe(bm, [(0.1, 0.0), (0.09, 0.3), (0.08, 0.62)], 10, "champ_cap", cap_bottom=True)
    # Delicate ring.
    lathe(bm, [(0.085, 0.46), (0.15, 0.42), (0.17, 0.39)], 10, "champ_cap")
    # Pink gills.
    fins(bm, 20, 0.09, 0.44, 0.6, 0.56, "champ_gills")
    lathe(bm, [(0.08, 0.63), (0.46, 0.57)], 16, "skin_shade")
    # White cap.
    lathe(bm, dome_profile(0.47, 0.56, 0.3, flat=0.2), 16, "champ_cap", cap_top=True)
    return finish_object("detail_champignon", bm)


def make_knollenblaetterpilz(rng):
    bm = new_bmesh()
    # Bulb in a sack-like volva.
    lathe(bm, [(0.08, 0.0), (0.2, 0.06), (0.2, 0.16), (0.1, 0.24)], 10, "white", cap_bottom=True)
    lathe(bm, [(0.14, 0.0), (0.24, 0.05), (0.25, 0.16), (0.27, 0.22)], 10, "volva")
    # Slender white stem with a hanging ring.
    lathe(bm, [(0.1, 0.22), (0.08, 0.5), (0.07, 0.78)], 10, "white")
    lathe(bm, [(0.075, 0.66), (0.14, 0.6), (0.17, 0.54)], 10, "volva")
    # Always white gills.
    fins(bm, 20, 0.08, 0.42, 0.76, 0.72, "white")
    lathe(bm, [(0.07, 0.79), (0.44, 0.73)], 16, "gills")
    # Olive-green cap.
    lathe(bm, dome_profile(0.45, 0.72, 0.22, flat=0.35), 16, "amanita_cap", cap_top=True)
    return finish_object("detail_knollenblaetterpilz", bm)


def make_pfifferling(rng):
    bm = new_bmesh()
    # Funnel that runs smoothly into the stem; forked ridges underneath.
    lathe(bm, [(0.1, 0.0), (0.09, 0.2), (0.15, 0.42), (0.32, 0.6), (0.48, 0.7), (0.5, 0.73)], 16,
          "chanterelle_ridges", pattern=checker("chanterelle_ridges", "leaf_yellow", band_filter={2, 3}),
          cap_bottom=True)
    fins(bm, 16, 0.12, 0.47, 0.38, 0.7, "chanterelle_ridges")
    # Yellow top with a sunken centre.
    lathe(bm, [(0.5, 0.73), (0.35, 0.72), (0.15, 0.66), (0.02, 0.62)], 16, "chanterelle", cap_top=True)
    return finish_object("detail_pfifferling", bm)


def make_fliegenpilz(rng):
    bm = new_bmesh()
    # Bulbous base with rings of warts.
    lathe(bm, [(0.1, 0.0), (0.22, 0.06), (0.22, 0.16), (0.12, 0.26)], 12, "cream",
          pattern=checker("cream", "stem", band_filter={1}), cap_bottom=True)
    lathe(bm, [(0.12, 0.24), (0.1, 0.55), (0.09, 0.82)], 12, "stem")
    # White ring.
    lathe(bm, [(0.095, 0.72), (0.17, 0.66), (0.2, 0.6)], 12, "cream")
    # White gills.
    fins(bm, 20, 0.09, 0.5, 0.8, 0.76, "gills")
    lathe(bm, [(0.09, 0.83), (0.52, 0.77)], 16, "cream")
    # Red cap with white flakes.
    profile = dome_profile(0.53, 0.76, 0.3, flat=0.15)
    lathe(bm, profile, 16, "fly_red", cap_top=True)
    flakes(bm, rng, 7, 0.45, lambda r: surface_height(profile, r), "cream")
    return finish_object("detail_fliegenpilz", bm)


def make_oelbaum_trichterling(rng):
    bm = new_bmesh()
    # Piece of old oak wood it grows on.
    lathe(bm, [(0.5, 0.0), (0.5, 0.2)], 8, "bark", cap_bottom=True)
    lathe(bm, [(0.5, 0.2), (0.4, 0.2)], 8, "bark")
    lathe(bm, [(0.4, 0.2), (0.001, 0.2)], 8, "wood_cut")

    # A tuft of three funnels with dense decurrent gills.
    for (x, y), size, tilt in (((0.0, 0.0), 1.0, 0.0), ((0.25, 0.12), 0.75, 0.4),
                               ((-0.22, 0.15), 0.7, -0.4)):
        before = set(bm.verts)
        lathe(bm, [(0.06, 0.0), (0.05, 0.25), (0.12, 0.45), (0.3, 0.58), (0.33, 0.6)], 8,
              "omphalotus_gills")
        fins(bm, 12, 0.07, 0.32, 0.3, 0.58, "omphalotus", thickness=0.004)
        lathe(bm, [(0.33, 0.6), (0.2, 0.6), (0.02, 0.54)], 8, "omphalotus", cap_top=True)
        matrix = (Matrix.Translation((x, y, 0.2)) @ Matrix.Rotation(tilt, 4, "X")
                  @ Matrix.Diagonal((size, size, size, 1.0)))
        bmesh.ops.transform(bm, matrix=matrix, verts=[v for v in bm.verts if v not in before])
    return finish_object("detail_oelbaum_trichterling", bm)


def make_waldgott_pilz(rng):
    bm = new_bmesh()
    lathe(bm, [(0.08, 0.0), (0.06, 0.5), (0.05, 0.9)], 10, "god_stem", cap_bottom=True)
    fins(bm, 16, 0.06, 0.3, 0.9, 0.82, "god_stem")
    lathe(bm, [(0.05, 0.92), (0.32, 0.82)], 12, "god_stem")
    # Tall bell-shaped cap with black patches like a cow.
    lathe(bm, [(0.33, 0.82), (0.3, 0.95), (0.24, 1.1), (0.14, 1.22), (0.02, 1.28)], 12,
          "god_cap", pattern=lambda band, segment: "god_spot" if rng.random() < 0.3 else None,
          cap_top=True)
    return finish_object("detail_waldgott", bm)


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
