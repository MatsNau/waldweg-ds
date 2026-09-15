"""Nina and Mats as rigid parts (head, body, arm, leg) for procedural animation.

Pivots (model origin) and where the game attaches them, in character space
(Blender units, Z up, character faces -Y):
- leg:  hip joint, mounted at (+-LEG_X, 0, HIP_Z), hangs down to the ground
- body: waist, mounted at (0, 0, HIP_Z)
- arm:  shoulder, mounted at (+-SHOULDER_X, 0, HIP_Z + SHOULDER_Z)
- head: neck, mounted at (0, 0, HIP_Z + NECK_Z)
Keep these numbers in sync with source/entities/CharacterRig.cpp.

Look (from the user):
- Nina: brown shoulder-length hair, big glasses, dark green jacket, wide blue jeans.
- Mats: red-brown curls, beige jacket, wide jeans.
"""
import math

import bmesh
from mathutils import Matrix, Vector

from dsmesh import faces_from_verts, finish_object, new_bmesh, paint, paint_verts

HIP_Z = 0.34
LEG_X = 0.075
SHOULDER_X = 0.15
SHOULDER_Z = 0.30
NECK_Z = 0.36

HEAD_RADIUS = 0.24
HEAD_CENTER_Z = 0.20  # above the neck pivot


def sphere_point(center, radius, azimuth_deg, elevation_deg):
    """Point on a sphere. azimuth 0 = front (-Y), positive = character's left (+X)."""
    az = math.radians(azimuth_deg)
    el = math.radians(elevation_deg)
    return center + Vector((math.sin(az) * math.cos(el),
                            -math.cos(az) * math.cos(el),
                            math.sin(el))) * radius


def surface_quad(bm, center, radius, azimuth, elevation, width, height, name, lift=0.006):
    """Small flat quad lying on a sphere surface (eyes, blush)."""
    normal = (sphere_point(center, 1.0, azimuth, elevation) - center).normalized()
    pos = center + normal * (radius + lift)
    right = Vector((0, 0, 1)).cross(normal).normalized() * (width / 2)
    up = normal.cross(right).normalized() * (height / 2)
    verts = [bm.verts.new(pos + dx * right + dy * up)
             for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    face = bm.faces.new(verts)
    paint(bm, [face], name)
    return face


def ring(bm, center, inner, outer, segments, name):
    """Flat ring facing -Y (glasses frame)."""
    faces = []
    inner_verts, outer_verts = [], []
    for i in range(segments):
        a = 2 * math.pi * i / segments
        d = Vector((math.cos(a), 0, math.sin(a)))
        inner_verts.append(bm.verts.new(center + d * inner))
        outer_verts.append(bm.verts.new(center + d * outer))
    for i in range(segments):
        j = (i + 1) % segments
        face = bm.faces.new((inner_verts[i], outer_verts[i], outer_verts[j], inner_verts[j]))
        faces.append(face)
    paint(bm, faces, name)
    return faces


# --- Parts ------------------------------------------------------------------

def make_leg(name, jeans):
    bm = new_bmesh()
    length = HIP_Z - 0.05
    leg = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=True, segments=5,
        radius1=0.085, radius2=0.07, depth=length,
        matrix=Matrix.Translation((0, 0, -length / 2)))
    paint_verts(bm, leg["verts"], jeans)

    shoe = bmesh.ops.create_cube(
        bm, size=1.0,
        matrix=Matrix.Translation((0, -0.025, -HIP_Z + 0.03)) @ Matrix.Diagonal((0.12, 0.17, 0.06, 1.0)))
    paint_verts(bm, shoe["verts"], "shoe")
    return finish_object(name, bm)


def make_body(name, jacket, jacket_dark):
    bm = new_bmesh()
    height = SHOULDER_Z + 0.06
    torso = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=6,
        radius1=0.17, radius2=0.12, depth=height,
        matrix=Matrix.Translation((0, 0, height / 2)) @ Matrix.Rotation(math.radians(30), 4, "Z"))
    for f in faces_from_verts(bm, torso["verts"]):
        top = f.normal.z > 0.9 or f.calc_center_median().z > height - 0.001
        paint(bm, [f], jacket_dark if top else jacket)

    # Zip line on the front.
    front_y = -0.145
    zip_face = bm.faces.new([bm.verts.new(c) for c in (
        (-0.012, front_y - 0.004, 0.01), (0.012, front_y - 0.004, 0.01),
        (0.012, -0.108, height - 0.02), (-0.012, -0.108, height - 0.02))])
    paint(bm, [zip_face], jacket_dark)
    return finish_object(name, bm, open_faces=[([zip_face], Vector((0, 0, height / 2)))])


def make_arm(name, jacket):
    bm = new_bmesh()
    length = 0.26
    sleeve = bmesh.ops.create_cone(
        bm, cap_ends=False, segments=5,
        radius1=0.055, radius2=0.045, depth=length,
        matrix=Matrix.Translation((0, 0, -length / 2)))
    paint_verts(bm, sleeve["verts"], jacket)

    hand = bmesh.ops.create_uvsphere(
        bm, u_segments=4, v_segments=2, radius=0.05,
        matrix=Matrix.Translation((0, 0, -length - 0.03)))
    paint_verts(bm, hand["verts"], "skin")
    return finish_object(name, bm)


def head_base(bm, center):
    head = bmesh.ops.create_uvsphere(
        bm, u_segments=8, v_segments=5, radius=HEAD_RADIUS,
        matrix=Matrix.Translation(center))
    paint_verts(bm, head["verts"], "skin")


def hair_cap(bm, center, radius, color, rng=None, bumps=0.0, cut_z=0.0):
    cap = bmesh.ops.create_uvsphere(
        bm, u_segments=8, v_segments=6, radius=radius,
        matrix=Matrix.Translation(center) @ Matrix.Rotation(math.radians(22.5), 4, "Z"))
    verts = list(cap["verts"])
    bmesh.ops.delete(bm, geom=[v for v in verts if v.co.z < center.z + cut_z - 1e-4],
                     context="VERTS")
    verts = [v for v in verts if v.is_valid]
    if rng is not None and bumps > 0:
        for v in verts:
            v.co += (v.co - center).normalized() * rng.uniform(0, bumps)
    faces = paint_verts(bm, verts, color)
    return faces


def hair_volume(bm, center, radius, color_top, color_low, face_top, rng=None, bumps=0.0,
                long_hair=0.0, face_depth=0.35):
    """Hair that wraps the whole head except the face, so no scalp shows.

    face_top: height above the head centre where the face opening ends (fringe).
    long_hair: how far the back and sides reach down below the head (shoulder length).
    face_depth: how far around the sides the face opening reaches (smaller = wider face).
    """
    hair = bmesh.ops.create_uvsphere(
        bm, u_segments=10, v_segments=7, radius=radius,
        matrix=Matrix.Translation(center) @ Matrix.Diagonal((1.04, 1.0, 1.0, 1.0)))
    verts = list(hair["verts"])

    # Face opening: front verts below the fringe (a little narrower at the cheeks).
    def in_face(v):
        local = v.co - center
        face = local.y < -radius * face_depth and local.z < face_top and abs(local.x) < radius * 0.8
        chin = local.z < -radius * 0.35 and local.y < 0  # no hair under the chin
        return face or chin

    bmesh.ops.delete(bm, geom=[v for v in verts if in_face(v)], context="VERTS")
    verts = [v for v in verts if v.is_valid]

    for v in verts:
        local = v.co - center
        if long_hair > 0 and local.z < 0 and local.y > -radius * 0.2:
            # Pull the lower back and sides down and slightly outwards.
            t = min(1.0, -local.z / radius)
            v.co.z -= long_hair * t
            v.co.x += local.x * 0.25 * t
            v.co.y += max(local.y, 0) * 0.15 * t
        elif local.z < -radius * 0.55:
            # Short hair: tuck the bottom in towards the neck.
            v.co.x *= 0.85
            v.co.y = center.y + local.y * 0.85
        if rng is not None and bumps > 0:
            v.co += (v.co - center).normalized() * rng.uniform(0, bumps)

    faces = faces_from_verts(bm, verts)
    for f in faces:
        low = f.calc_center_median().z < center.z - radius * 0.3
        paint(bm, [f], color_low if low else color_top)
    return faces


def face_features(bm, center, eye_elevation, blush=True):
    faces = []
    for side in (-1, 1):
        faces.append(surface_quad(bm, center, HEAD_RADIUS, 22 * side, eye_elevation,
                                  0.035, 0.05, "eye"))
        if blush:
            faces.append(surface_quad(bm, center, HEAD_RADIUS, 40 * side, -24,
                                      0.05, 0.03, "blush"))
    return faces


def make_nina_head():
    bm = new_bmesh()
    center = Vector((0, 0, HEAD_CENTER_Z))
    head_base(bm, center)

    open_faces = []

    # Hair: one volume around the head, down to the shoulders at back and sides.
    hair = hair_volume(bm, center, HEAD_RADIUS + 0.03, "hair_brown", "hair_brown_dark",
                       face_top=0.06, long_hair=0.2)
    open_faces.append((hair, center))

    eye_elevation = -8
    features = face_features(bm, center, eye_elevation)
    open_faces.append((features, center))

    # Big round glasses in front of the eyes.
    lens_z = center.z + math.sin(math.radians(eye_elevation)) * HEAD_RADIUS
    lens_y = -HEAD_RADIUS - 0.03
    frames = []
    for side in (-1, 1):
        frames += ring(bm, Vector((0.09 * side, lens_y, lens_z)), 0.058, 0.082, 8, "glasses")
    bridge = bm.faces.new([bm.verts.new(c) for c in (
        (-0.015, lens_y, lens_z + 0.01), (0.015, lens_y, lens_z + 0.01),
        (0.015, lens_y, lens_z + 0.03), (-0.015, lens_y, lens_z + 0.03))])
    paint(bm, [bridge], "glasses")
    frames.append(bridge)
    open_faces.append((frames, Vector((0, 0, lens_z))))

    return finish_object("nina_head", bm, open_faces=open_faces)


def make_mats_head(rng):
    bm = new_bmesh()
    center = Vector((0, 0, HEAD_CENTER_Z))
    head_base(bm, center)

    open_faces = []
    hair = hair_volume(bm, center, HEAD_RADIUS + 0.035, "hair_auburn", "hair_auburn_dark",
                       face_top=0.08, rng=rng, bumps=0.025, face_depth=0.15)
    open_faces.append((hair, center))

    # Curls: small flattened lumps on the hair, all around the head.
    curl_spots = [
        (0, 55), (45, 40), (-45, 40), (90, 25), (-90, 25), (135, 15), (-135, 15),
        (180, 30), (160, -15), (-160, -15), (110, -10), (-110, -10), (25, 80),
    ]
    curls = []
    for azimuth, elevation in curl_spots:
        pos = sphere_point(center, HEAD_RADIUS + 0.05, azimuth, elevation)
        size = rng.uniform(0.06, 0.075)
        # Flatten each octahedron along the head normal and tumble it, so the
        # curls read as round lumps instead of spikes.
        normal = (pos - center).normalized()
        align = normal.to_track_quat("Z", "Y").to_matrix().to_4x4()
        tumble = Matrix.Rotation(rng.uniform(0, math.pi), 4, "Z")
        squash = Matrix.Diagonal((1.0, 1.0, 0.45, 1.0))
        curl = bmesh.ops.create_uvsphere(
            bm, u_segments=4, v_segments=2, radius=size,
            matrix=Matrix.Translation(pos) @ align @ tumble @ squash)
        color = "hair_auburn_dark" if rng.random() < 0.4 else "hair_auburn"
        curls += paint_verts(bm, curl["verts"], color)

    features = face_features(bm, center, -6)
    open_faces.append((features, center))
    return finish_object("mats_head", bm, open_faces=open_faces)


def build(rng):
    return [
        make_nina_head(),
        make_body("nina_body", "jacket_green", "jacket_green_dark"),
        make_arm("nina_arm", "jacket_green"),
        make_leg("nina_leg", "jeans"),
        make_mats_head(rng),
        make_body("mats_body", "jacket_beige", "jacket_beige_dark"),
        make_arm("mats_arm", "jacket_beige"),
        make_leg("mats_leg", "jeans_dark"),
    ]
