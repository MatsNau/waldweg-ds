"""Generates the day-1 test models (ground, autumn tree, fly agaric) and the
shared palette texture.

Run headless:  blender --background --factory-startup --python gen_testmodels.py -- <outdir>

Every face is UV-mapped onto the centre of one colour swatch of a small palette
texture, because obj2dl ignores OBJ materials but keeps UVs and normals (so
lighting, fog and outlines keep working on the DS).
"""
import math
import os
import random
import struct
import sys
import zlib

import bmesh
import bpy
from mathutils import Matrix, Vector

SWATCH = 4
GRID = 4
TEX_SIZE = SWATCH * GRID

PALETTE = [
    ("bark", (92, 58, 36)),
    ("bark_dark", (64, 40, 26)),
    ("leaf_orange", (232, 128, 30)),
    ("leaf_red", (196, 64, 30)),
    ("leaf_yellow", (240, 186, 60)),
    ("leaf_brown", (168, 96, 40)),
    ("moss", (112, 124, 56)),
    ("moss_dark", (84, 96, 44)),
    ("soil", (110, 76, 46)),
    ("fly_red", (212, 42, 30)),
    ("cream", (251, 247, 238)),
    ("stem", (236, 226, 200)),
    ("gills", (244, 238, 224)),
    ("stone", (150, 146, 136)),
    ("stone_dark", (104, 100, 94)),
    ("glow", (200, 236, 255)),
]
SWATCH_INDEX = {name: i for i, (name, _) in enumerate(PALETTE)}


def out_dir():
    if "--" in sys.argv:
        return os.path.abspath(sys.argv[sys.argv.index("--") + 1])
    return os.path.abspath("assets/build")


def write_palette_png(path):
    pixels = bytearray()
    for y in range(TEX_SIZE):
        pixels.append(0)  # PNG filter type "none"
        for x in range(TEX_SIZE):
            index = (y // SWATCH) * GRID + (x // SWATCH)
            pixels.extend(PALETTE[index][1])

    def chunk(kind, data):
        body = kind + data
        return struct.pack(">I", len(data)) + body + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", TEX_SIZE, TEX_SIZE, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(pixels), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def swatch_uv(name):
    index = SWATCH_INDEX[name]
    col, row = index % GRID, index // GRID
    u = (col * SWATCH + SWATCH / 2) / TEX_SIZE
    # obj2dl flips V (v = 1 - v), so row 0 of the PNG is at the top.
    v = 1.0 - (row * SWATCH + SWATCH / 2) / TEX_SIZE
    return u, v


def faces_of(geom):
    return [g for g in geom if isinstance(g, bmesh.types.BMFace)]


def faces_from_verts(bm, verts):
    vset = set(verts)
    return [f for f in bm.faces if all(v in vset for v in f.verts)]


def new_bmesh():
    bm = bmesh.new()
    # Created before any geometry: adding a layer later invalidates BMFace references.
    bm.faces.layers.int.new("swatch")
    return bm


def paint(bm, faces, name):
    layer = bm.faces.layers.int["swatch"]
    for f in faces:
        f[layer] = SWATCH_INDEX[name]


def finish_object(name, bm):
    layer = bm.faces.layers.int["swatch"]
    uv_layer = bm.loops.layers.uv.verify()
    for f in bm.faces:
        uv = swatch_uv(PALETTE[f[layer]][0])
        for loop in f.loops:
            loop[uv_layer].uv = uv
        f.smooth = False

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def make_ground(rng):
    bm = new_bmesh()
    bmesh.ops.create_grid(bm, x_segments=6, y_segments=6, size=4.5)
    for v in bm.verts:
        edge = max(abs(v.co.x), abs(v.co.y)) > 4.4
        v.co.z = 0.0 if edge else rng.uniform(-0.04, 0.05)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    choices = ["moss"] * 6 + ["moss_dark"] * 2 + ["soil", "leaf_brown"]
    for f in bm.faces:
        paint(bm, [f], rng.choice(choices))
    return finish_object("ground", bm)


def make_tree(rng):
    bm = new_bmesh()

    trunk = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=6,
        radius1=0.2, radius2=0.13, depth=1.4,
        matrix=Matrix.Translation((0, 0, 0.7)))
    paint(bm, faces_from_verts(bm, trunk["verts"]), "bark")

    crowns = [
        (2, 0.95, (0.0, 0.0, 1.85), (1.0, 1.0, 0.85)),
        (1, 0.55, (0.45, 0.25, 2.45), (1.0, 1.0, 0.9)),
    ]
    leaf_colors = ["leaf_orange"] * 5 + ["leaf_red"] * 3 + ["leaf_yellow"] * 2
    for subdivisions, radius, offset, scale in crowns:
        matrix = Matrix.Translation(offset) @ Matrix.Diagonal((*scale, 1.0))
        crown = bmesh.ops.create_icosphere(
            bm, subdivisions=subdivisions, radius=radius, matrix=matrix)
        for v in crown["verts"]:
            v.co += Vector((rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06), rng.uniform(-0.05, 0.05)))
        for f in faces_from_verts(bm, crown["verts"]):
            paint(bm, [f], rng.choice(leaf_colors))

    return finish_object("tree", bm)


def make_fly_agaric(rng):
    bm = new_bmesh()

    stem = bmesh.ops.create_cone(
        bm, cap_ends=True, cap_tris=False, segments=8,
        radius1=0.07, radius2=0.055, depth=0.3,
        matrix=Matrix.Translation((0, 0, 0.15)))
    paint(bm, faces_from_verts(bm, stem["verts"]), "stem")

    bulb = bmesh.ops.create_icosphere(
        bm, subdivisions=1, radius=0.1,
        matrix=Matrix.Translation((0, 0, 0.04)) @ Matrix.Diagonal((1.0, 1.0, 0.6, 1.0)))
    paint(bm, faces_from_verts(bm, bulb["verts"]), "stem")

    cap = bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.22)
    cap_verts = list(cap["verts"])
    lower = [v for v in cap_verts if v.co.z < -1e-4]
    bmesh.ops.delete(bm, geom=lower, context="VERTS")
    cap_verts = [v for v in cap_verts if v.is_valid]
    for v in cap_verts:
        v.co.z = v.co.z * 0.55 + 0.29

    cap_faces = faces_from_verts(bm, cap_verts)
    for f in cap_faces:
        top = f.calc_center_median().z > 0.33
        paint(bm, [f], "cream" if top and rng.random() < 0.3 else "fly_red")

    rim = [e for e in bm.edges if e.is_boundary and all(v in set(cap_verts) for v in e.verts)]
    filled = bmesh.ops.holes_fill(bm, edges=rim, sides=0)
    paint(bm, filled["faces"], "gills")

    return finish_object("fliegenpilz", bm)


def export_obj(obj, path):
    for other in bpy.context.scene.objects:
        other.select_set(other == obj)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.wm.obj_export(
        filepath=path,
        export_selected_objects=True,
        export_materials=False,
        export_triangulated_mesh=True,
        export_normals=True,
        export_uv=True,
        export_colors=False,
        forward_axis="NEGATIVE_Z",
        up_axis="Y",
        apply_modifiers=True,
    )


def main():
    target = out_dir()
    os.makedirs(target, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    rng = random.Random(20260914)

    write_palette_png(os.path.join(target, "palette.png"))
    for obj in (make_ground(rng), make_tree(rng), make_fly_agaric(rng)):
        path = os.path.join(target, f"{obj.name}.obj")
        export_obj(obj, path)
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        print(f"exported {obj.name}: {tris} triangles -> {path}")


main()
