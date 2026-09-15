"""Shared helpers for the procedural DS model generators.

Every face is UV-mapped onto the centre of one colour swatch of a small palette
texture, because obj2dl ignores OBJ materials but keeps UVs and normals (so
lighting, fog and outlines keep working on the DS).

Conventions (Blender space, Z up):
- Characters and props face -Y. After the OBJ export (forward -Z, up Y) this is
  +Z in game space, i.e. towards the default camera.
- A model's origin is its pivot (feet, hip joint, shoulder, neck, ...).
"""
import os
import struct
import sys
import zlib

import bmesh
import bpy

SWATCH = 4
GRID = 8
TEX_SIZE = SWATCH * GRID

# Order matters: the index is the swatch position in the texture.
PALETTE = [
    # Forest (row 0-1)
    ("bark", (92, 58, 36)),
    ("bark_dark", (64, 40, 26)),
    ("leaf_orange", (232, 128, 30)),
    ("leaf_red", (196, 64, 30)),
    ("leaf_yellow", (240, 186, 60)),
    ("leaf_brown", (168, 96, 40)),
    ("moss", (112, 124, 56)),
    ("moss_dark", (84, 96, 44)),
    ("soil", (110, 76, 46)),
    ("fir", (52, 84, 58)),
    ("fir_dark", (38, 64, 46)),
    ("bush", (140, 110, 44)),
    ("stone", (150, 146, 136)),
    ("stone_dark", (104, 100, 94)),
    ("wood_cut", (206, 164, 110)),
    ("god_spot", (30, 28, 34)),
    # Mushrooms (row 2)
    ("fly_red", (212, 42, 30)),
    ("cream", (251, 247, 238)),
    ("stem", (236, 226, 200)),
    ("gills", (244, 238, 224)),
    ("boletus_cap", (122, 74, 36)),
    ("boletus_tubes", (232, 224, 176)),
    ("boletus_stem", (239, 230, 207)),
    ("satan_cap", (216, 212, 196)),
    # Characters (row 3-4)
    ("skin", (246, 204, 170)),
    ("skin_shade", (226, 176, 140)),
    ("blush", (240, 150, 140)),
    ("eye", (40, 30, 30)),
    ("hair_brown", (104, 66, 40)),
    ("hair_brown_dark", (78, 48, 30)),
    ("hair_auburn", (150, 70, 40)),
    ("hair_auburn_dark", (114, 50, 30)),
    ("glasses", (36, 28, 30)),
    ("jacket_green", (46, 84, 56)),
    ("jacket_green_dark", (34, 64, 44)),
    ("jacket_beige", (214, 190, 150)),
    ("jacket_beige_dark", (184, 160, 122)),
    ("jeans", (86, 118, 168)),
    ("jeans_dark", (64, 92, 138)),
    ("shoe", (70, 50, 40)),
    # Mushrooms (row 5-6)
    ("satan_pores", (192, 48, 42)),
    ("satan_stem", (224, 176, 64)),
    ("champ_cap", (242, 238, 230)),
    ("champ_gills", (232, 160, 160)),
    ("amanita_cap", (140, 154, 98)),
    ("white", (255, 255, 255)),
    ("volva", (242, 242, 234)),
    ("chanterelle", (242, 180, 34)),
    ("chanterelle_ridges", (227, 165, 26)),
    ("omphalotus", (232, 128, 30)),
    ("omphalotus_gills", (240, 176, 48)),
    ("god_cap", (250, 250, 244)),
    ("god_stem", (236, 240, 236)),
    # Items (row 6-7)
    ("wicker", (196, 150, 90)),
    ("wicker_dark", (150, 108, 60)),
    ("scarf_red", (190, 60, 50)),
    ("scarf_stripe", (240, 220, 180)),
    ("metal", (60, 56, 52)),
    ("lantern_glass", (255, 220, 140)),
    ("bell_gold", (230, 190, 70)),
    ("bell_dark", (170, 130, 40)),
    ("wool_rust", (184, 82, 40)),
    ("wool_rust_dark", (140, 58, 30)),
]
assert len(PALETTE) <= GRID * GRID
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
            color = PALETTE[index][1] if index < len(PALETTE) else (255, 0, 255)
            pixels.extend(color)

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


def new_bmesh():
    bm = bmesh.new()
    # Created before any geometry: adding a layer later invalidates BMFace references.
    bm.faces.layers.int.new("swatch")
    return bm


def faces_from_verts(bm, verts):
    vset = set(verts)
    return [f for f in bm.faces if all(v in vset for v in f.verts)]


def paint(bm, faces, name):
    layer = bm.faces.layers.int["swatch"]
    for f in faces:
        f[layer] = SWATCH_INDEX[name]


def paint_verts(bm, verts, name):
    faces = faces_from_verts(bm, verts)
    paint(bm, faces, name)
    return faces


def add_quad(bm, corners, name):
    verts = [bm.verts.new(c) for c in corners]
    face = bm.faces.new(verts)
    paint(bm, [face], name)
    return face


def orient_outward(faces, center):
    """Flips open faces (eyes, glasses, hair shells) so they face away from center."""
    for f in faces:
        if not f.is_valid:
            continue
        if f.normal.dot(f.calc_center_median() - center) < 0:
            f.normal_flip()


def finish_object(name, bm, open_faces=()):
    """open_faces: (faces, center) pairs whose orientation is fixed after recalc."""
    layer = bm.faces.layers.int["swatch"]
    uv_layer = bm.loops.layers.uv.verify()
    for f in bm.faces:
        uv = swatch_uv(PALETTE[f[layer]][0])
        for loop in f.loops:
            loop[uv_layer].uv = uv
        f.smooth = False

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for faces, center in open_faces:
        for f in faces:
            if f.is_valid:
                f.normal_update()
        orient_outward(faces, center)
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


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


def export_all(objects, target):
    for obj in objects:
        path = os.path.join(target, f"{obj.name}.obj")
        export_obj(obj, path)
        tris = sum(len(p.vertices) - 2 for p in obj.data.polygons)
        print(f"exported {obj.name}: {tris} triangles -> {path}")
