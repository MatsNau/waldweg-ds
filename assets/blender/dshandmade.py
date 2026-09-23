"""Round-trip support: hand-edited .blend files as model sources.

The generators in models_*.py stay the default. A .blend in
assets/blender/handmade/ overrides single parts: every object carrying the
custom property "ds_export" is exported over the generated OBJ of the same
name, so nothing after that step changes (obj2dl, grit, Makefile).

What a hand-edited part has to respect, because the DS pipeline is unforgiving:
- the object origin is the pivot the game mounts the part at (hip, shoulder,
  neck, feet). The object location is only the preview placement inside the
  .blend and is dropped on export - to move a part in the game, move its
  vertices, not the object.
- no object rotation or scale: they would be baked in silently on export.
- colour comes from the UV, not from a material: every face UV has to sit on
  the centre of one palette swatch (obj2dl ignores materials, keeps UVs).
- vertex coordinates within +-8, the range obj2dl encodes.

problems() checks all of that and is what the add-on panel and the export
script both report.
"""
import os

import bpy

import dsmesh
from dsmesh import GRID, PALETTE, SWATCH, TEX_SIZE

# Custom properties on the object.
EXPORT_PROP = "ds_export"  # True: this object is written over the generated OBJ
MOUNT_PROP = "ds_mount"    # where the game mounts it; also the preview placement

MAX_COORD = 8.0  # obj2dl encodes vertex coordinates in this range
PALETTE_IMAGE = "ds_palette"
PALETTE_MATERIAL = "ds_palette"

ERROR = "error"
WARNING = "warn"


# --- Palette ----------------------------------------------------------------

def uv_for_index(index):
    return dsmesh.swatch_uv(PALETTE[index][0])


def index_for_uv(u, v):
    """Swatch index the UV points at, or None if it misses a swatch centre."""
    col = round(u * TEX_SIZE / SWATCH - 0.5)
    row = round((1.0 - v) * TEX_SIZE / SWATCH - 0.5)
    if not (0 <= col < GRID and 0 <= row < GRID):
        return None
    index = row * GRID + col
    if index >= len(PALETTE):
        return None
    want_u, want_v = uv_for_index(index)
    # A quarter of a swatch is the tolerance: still unambiguously that colour.
    tolerance = SWATCH / (4.0 * TEX_SIZE)
    if abs(u - want_u) > tolerance or abs(v - want_v) > tolerance:
        return None
    return index


def palette_image():
    """32x32 palette as a Blender image, packed into the .blend."""
    image = bpy.data.images.get(PALETTE_IMAGE)
    if image is None:
        image = bpy.data.images.new(PALETTE_IMAGE, TEX_SIZE, TEX_SIZE, alpha=False)
    image.colorspace_settings.name = "sRGB"
    pixels = []
    for y in range(TEX_SIZE):  # Blender images start at the bottom row.
        top_y = TEX_SIZE - 1 - y
        for x in range(TEX_SIZE):
            index = (top_y // SWATCH) * GRID + (x // SWATCH)
            r, g, b = PALETTE[index][1] if index < len(PALETTE) else (255, 0, 255)
            pixels.extend((r / 255.0, g / 255.0, b / 255.0, 1.0))
    image.pixels = pixels
    image.pack()
    return image


def palette_material():
    """Material that shows the swatch colours in the viewport (never exported)."""
    mat = bpy.data.materials.get(PALETTE_MATERIAL)
    if mat is not None:
        return mat
    mat = bpy.data.materials.new(PALETTE_MATERIAL)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes.get("Principled BSDF")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = palette_image()
    tex.interpolation = "Closest"  # no blending between neighbouring swatches
    tex.location = (-320, 300)
    links.new(tex.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Roughness"].default_value = 1.0
    for flat in ("Specular IOR Level", "Specular"):
        if flat in shader.inputs:
            shader.inputs[flat].default_value = 0.0
            break
    return mat


def assign_palette_material(obj):
    obj.data.materials.clear()
    obj.data.materials.append(palette_material())


# --- Painting ---------------------------------------------------------------

def set_face_swatch(bm, faces, index):
    """Points every loop of the faces at one swatch centre."""
    uv_layer = bm.loops.layers.uv.verify()
    u, v = uv_for_index(index)
    for face in faces:
        for loop in face.loops:
            loop[uv_layer].uv = (u, v)


def face_swatch(bm, face):
    uv_layer = bm.loops.layers.uv.active
    if uv_layer is None:
        return None
    indices = {index_for_uv(*loop[uv_layer].uv) for loop in face.loops}
    return indices.pop() if len(indices) == 1 else None


# --- Marking ----------------------------------------------------------------

def mark_export(obj, mount=(0.0, 0.0, 0.0)):
    obj[EXPORT_PROP] = True
    obj[MOUNT_PROP] = list(mount)
    obj.location = mount


def is_export(obj):
    return obj.type == "MESH" and bool(obj.get(EXPORT_PROP))


def mount_of(obj):
    return tuple(obj.get(MOUNT_PROP, (0.0, 0.0, 0.0)))


def export_objects(scene=None):
    scene = scene or bpy.context.scene
    return [obj for obj in scene.objects if is_export(obj)]


# --- Checking ---------------------------------------------------------------

def triangle_count(obj):
    return sum(len(p.vertices) - 2 for p in obj.data.polygons)


def problems(obj):
    """[(level, text)] - everything that would break or silently change the part."""
    found = []
    mesh = obj.data

    if not mesh.uv_layers:
        found.append((ERROR, "keine UV-Ebene - ohne UV hat das Teil keine Farbe"))
    if len(mesh.uv_layers) > 1:
        found.append((WARNING, f"{len(mesh.uv_layers)} UV-Ebenen, exportiert wird die aktive"))

    # Read the matrix, not rotation_euler: the object may use quaternions.
    _, rotation, scale = obj.matrix_basis.decompose()
    if max(abs(a - b) for a, b in zip(rotation, (1.0, 0.0, 0.0, 0.0))) > 1e-5:
        found.append((ERROR, "Objekt ist gedreht - erst anwenden, sonst wandert die Drehung ins Mesh"))
    if max(abs(s - 1.0) for s in scale) > 1e-5:
        found.append((ERROR, "Objekt ist skaliert - erst anwenden"))

    mount = mount_of(obj)
    drift = max(abs(a - b) for a, b in zip(obj.location, mount))
    if drift > 1e-4:
        found.append((WARNING,
                      f"steht {drift:.3f} neben seinem Gelenkpunkt - "
                      "dieser Versatz geht beim Export verloren"))

    far = [v.index for v in mesh.vertices if max(abs(c) for c in v.co) > MAX_COORD]
    if far:
        found.append((ERROR, f"{len(far)} Vertices weiter als {MAX_COORD:g} vom Ursprung (obj2dl-Grenze)"))

    if mesh.uv_layers:
        uv_data = mesh.uv_layers.active.data
        off = 0
        for poly in mesh.polygons:
            indices = {index_for_uv(*uv_data[i].uv)
                       for i in range(poly.loop_start, poly.loop_start + poly.loop_total)}
            if len(indices) != 1 or None in indices:
                off += 1
        if off:
            found.append((ERROR, f"{off} Flaechen ohne eindeutiges Farbfeld - im DS-Panel eine Farbe zuweisen"))

    ngons = sum(1 for p in mesh.polygons if len(p.vertices) > 4)
    if ngons:
        found.append((WARNING, f"{ngons} N-Gons - werden beim Export zerlegt (kostet Vertices)"))

    smooth = sum(1 for p in mesh.polygons if p.use_smooth)
    if smooth:
        found.append((WARNING, f"{smooth} Flaechen glatt schattiert - der Rest des Spiels ist flach"))

    used = set()
    for poly in mesh.polygons:
        used.update(poly.vertices)
    loose = len(mesh.vertices) - len(used)
    if loose:
        found.append((WARNING, f"{loose} lose Vertices ohne Flaeche"))

    return found


def has_errors(found):
    return any(level == ERROR for level, _ in found)


# --- Export -----------------------------------------------------------------

def unhide_everything(view_layer=None):
    """Export needs the objects selectable; a hidden collection would skip them."""
    view_layer = view_layer or bpy.context.view_layer

    def walk(layer_collection):
        layer_collection.exclude = False
        layer_collection.hide_viewport = False
        layer_collection.collection.hide_viewport = False
        for child in layer_collection.children:
            walk(child)

    walk(view_layer.layer_collection)
    for obj in view_layer.objects:
        obj.hide_viewport = False
        obj.hide_set(False)


def export_object(obj, target):
    """Writes <target>/<name>.obj in pivot-local space, like the generators do."""
    path = os.path.join(target, f"{obj.name}.obj")
    saved = tuple(obj.location)
    obj.location = (0.0, 0.0, 0.0)
    try:
        dsmesh.export_obj(obj, path)
    finally:
        obj.location = saved
    return path
