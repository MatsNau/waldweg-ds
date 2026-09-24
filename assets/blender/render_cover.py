"""Renders the cover art from the game models (Blender variant of the case cover).

A small autumn forest scene with Nina and Mats (from handmade/characters.blend),
the wool hat, scarf, basket and lantern, trees, bushes, falling leaves and the
detailed book mushrooms. EEVEE with toon shading (three light bands over the
palette colours, warm shadows, haze with distance) and Freestyle ink lines, so
it reads like the drawing style of the mushroom book.

    blender --background --factory-startup --python render_cover.py -- <outdir> [preview]

Writes <outdir>/front.png (1320x1370) and <outdir>/back.png (1536x870); these
are handed to assets/cover/gen_cover.py (--front-art/--back-art). "preview"
renders at a quarter of the size for quick composition checks.
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import dsmesh  # noqa: E402
import models_characters  # noqa: E402
import models_items  # noqa: E402
import models_mushrooms_detail  # noqa: E402
import models_world  # noqa: E402

FRONT_SIZE = (1320, 1370)
BACK_SIZE = (1536, 870)

HIP_Z = models_characters.HIP_Z
LEG_X = models_characters.LEG_X
SHOULDER_X = models_characters.SHOULDER_X
SHOULDER_Z = models_characters.SHOULDER_Z
NECK_Z = models_characters.NECK_Z
HAND_Z = -0.29  # CharacterRig.cpp kHandY, below the shoulder

INK = (72, 44, 30)
SHADOW_TINT = (0.66, 0.54, 0.54)
MID_TINT = (0.88, 0.82, 0.78)
HAZE = (238, 176, 128)
SKY = [(0.0, (240, 160, 110)), (0.06, (246, 186, 124)), (0.3, (247, 205, 140)), (0.75, (243, 222, 176))]


def linear(rgb):
    def ch(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(ch(c) for c in rgb)


def rgba(rgb):
    return linear(rgb) + (1.0,)


# --- Materials ------------------------------------------------------------------
def toon_material(image, name="toon", glow=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nodes, links = nt.nodes, nt.links
    nodes.clear()
    out = nodes.new("ShaderNodeOutputMaterial")
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = image
    tex.interpolation = "Closest"
    emission = nodes.new("ShaderNodeEmission")
    links.new(emission.outputs[0], out.inputs[0])
    if glow:
        links.new(tex.outputs["Color"], emission.inputs["Color"])
        emission.inputs["Strength"].default_value = glow
        return mat

    diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    to_rgb = nodes.new("ShaderNodeShaderToRGB")
    links.new(diffuse.outputs[0], to_rgb.inputs[0])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    stops = ramp.color_ramp.elements
    stops[0].position, stops[0].color = 0.0, SHADOW_TINT + (1.0,)
    stops[1].position, stops[1].color = 0.2, MID_TINT + (1.0,)
    lit = stops.new(0.42)
    lit.color = (1.0, 1.0, 1.0, 1.0)
    bright = stops.new(0.9)
    bright.color = (1.12, 1.08, 1.0, 1.0)
    links.new(to_rgb.outputs["Color"], ramp.inputs["Fac"])

    shade = nodes.new("ShaderNodeMix")
    shade.data_type = "RGBA"
    shade.blend_type = "MULTIPLY"
    shade.inputs["Factor"].default_value = 1.0
    links.new(tex.outputs["Color"], shade.inputs["A"])
    links.new(ramp.outputs["Color"], shade.inputs["B"])

    # Haze: colours fade towards the sky with distance (atmospheric perspective).
    cam = nodes.new("ShaderNodeCameraData")
    far = nodes.new("ShaderNodeMapRange")
    far.inputs["From Min"].default_value = 7.0
    far.inputs["From Max"].default_value = 38.0
    far.inputs["To Max"].default_value = 0.82
    links.new(cam.outputs["View Z Depth"], far.inputs["Value"])
    haze = nodes.new("ShaderNodeMix")
    haze.data_type = "RGBA"
    haze.inputs["B"].default_value = rgba(HAZE)
    links.new(far.outputs["Result"], haze.inputs["Factor"])
    links.new(shade.outputs["Result"], haze.inputs["A"])
    links.new(haze.outputs["Result"], emission.inputs["Color"])
    return mat


def sky_world():
    world = bpy.data.worlds.new("sky")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    nodes, links = nt.nodes, nt.links
    nodes.clear()
    coords = nodes.new("ShaderNodeTexCoord")
    xyz = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coords.outputs["Generated"], xyz.inputs[0])
    ramp = nodes.new("ShaderNodeValToRGB")
    elements = ramp.color_ramp.elements
    elements[0].position, elements[0].color = SKY[0][0], rgba(SKY[0][1])
    elements[1].position, elements[1].color = SKY[-1][0], rgba(SKY[-1][1])
    for pos, color in SKY[1:-1]:
        elements.new(pos).color = rgba(color)
    links.new(xyz.outputs["Z"], ramp.inputs["Fac"])
    sky = nodes.new("ShaderNodeBackground")
    links.new(ramp.outputs["Color"], sky.inputs["Color"])
    # Lighting sees only a soft warm ambient, the camera sees the full sky.
    ambient = nodes.new("ShaderNodeBackground")
    ambient.inputs["Color"].default_value = rgba((120, 100, 90))
    ambient.inputs["Strength"].default_value = 0.35
    path = nodes.new("ShaderNodeLightPath")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(path.outputs["Is Camera Ray"], mix.inputs["Fac"])
    links.new(ambient.outputs[0], mix.inputs[1])
    links.new(sky.outputs[0], mix.inputs[2])
    out = nodes.new("ShaderNodeOutputWorld")
    links.new(mix.outputs[0], out.inputs[0])


# --- Scene helpers -------------------------------------------------------------
def collection(name):
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def move_to(obj, coll):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    coll.objects.link(obj)


def instance(src, coll, location, scale=1.0, rot_z=0.0, rot=None, parent=None):
    obj = bpy.data.objects.new(f"{src.name}.inst", src.data)
    obj.location = location
    obj.scale = (scale, scale, scale)
    obj.rotation_euler = rot if rot is not None else (0.0, 0.0, rot_z)
    if parent is not None:
        obj.parent = parent
    coll.objects.link(obj)
    return obj


def smooth(obj):
    for polygon in obj.data.polygons:
        polygon.use_smooth = True


def empty(name, coll, location, rot_z=0.0):
    obj = bpy.data.objects.new(name, None)
    obj.location = location
    obj.rotation_euler = (0.0, 0.0, rot_z)
    coll.objects.link(obj)
    return obj


def load_characters():
    """The handmade figure parts are the truth for Nina and Mats."""
    path = os.path.join(HERE, "handmade", "characters.blend")
    names = [f"{fig}_{part}" for fig in ("nina", "mats") for part in ("head", "body", "arm", "leg")]
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = [n for n in src.objects if n in names]
    return {obj.name: obj for obj in dst.objects if obj is not None}


def figure(parts, prefix, coll, location, rot_z, arm_swing=(0.0, 0.0)):
    """Mounts the parts like CharacterRig::Draw. arm_swing: (left, right) in
    degrees, positive = forwards. Returns the root and the two hand positions
    (in figure space) so items can hang from them."""
    root = empty(prefix, coll, location, rot_z)
    for side in (1, -1):
        instance(parts[f"{prefix}_leg"], coll, (side * LEG_X, 0.0, HIP_Z), parent=root)
    instance(parts[f"{prefix}_body"], coll, (0.0, 0.0, HIP_Z), parent=root)
    hands = {}
    for side, swing in ((1, arm_swing[0]), (-1, arm_swing[1])):
        a = math.radians(swing)
        shoulder = Vector((side * SHOULDER_X, 0.0, HIP_Z + SHOULDER_Z))
        instance(parts[f"{prefix}_arm"], coll, shoulder, rot=(-a, 0.0, 0.0), parent=root)
        hands["left" if side > 0 else "right"] = shoulder + Vector((0.0, HAND_Z * math.sin(a), HAND_Z * math.cos(a)))
    instance(parts[f"{prefix}_head"], coll, (0.0, 0.0, HIP_Z + NECK_Z), parent=root)
    return root, hands


def ground(coll, rng):
    """Low-poly patchwork of moss with a winding path of trodden leaves."""
    bm = dsmesh.new_bmesh()
    step = 0.5
    for iy in range(-16, 96):
        for ix in range(-50, 50):
            x, y = ix * step, iy * step
            cx, cy = x + step / 2, y + step / 2
            path_x = 0.45 * math.sin(cy * 0.22) - 0.2
            half = 0.62 + max(0.0, -cy) * 0.18 - min(cy, 20) * 0.012
            if abs(cx - path_x) < half:
                name = "wood_cut"
            else:
                name = "moss_dark" if rng.random() < 0.18 else "moss"
            dsmesh.add_quad(bm, [(x, y, 0), (x + step, y, 0), (x + step, y + step, 0), (x, y + step, 0)], name)
    obj = dsmesh.finish_object("cover_ground", bm)
    move_to(obj, coll)
    return obj


# --- Scene ----------------------------------------------------------------------
def build_scene(rng):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    world_coll = collection("Welt")
    nofs = collection("OhneLinien")

    lib = {o.name: o for o in models_world.build(random.Random(20260914))}
    lib.update({o.name: o for o in models_items.build(random.Random(20260917))})
    lib.update({o.name: o for o in models_mushrooms_detail.build(random.Random(20260918))})
    parts = load_characters()
    for obj in list(lib.values()):
        obj.hide_render = True
        obj.hide_viewport = True

    palette_path = os.path.join(bpy.app.tempdir, "palette.png")
    dsmesh.write_palette_png(palette_path)
    image = bpy.data.images.load(palette_path)
    toon = toon_material(image)
    glow = toon_material(image, "glow", glow=1.1)
    for mesh in bpy.data.meshes:
        mesh.materials.clear()
        mesh.materials.append(toon)
    for name in ("item_laterne_glas", "detail_waldgott"):
        lib[name].data.materials[0] = glow
    # Mushrooms and items get round shading bands; figures and world stay faceted like in the game
    # (smooth normals turn Mats' curls into planks).
    for obj in list(lib.values()) + list(parts.values()):
        if obj.name.startswith(("detail_", "item_")):
            smooth(obj)

    ground(world_coll, rng).data.materials.append(toon)

    # --- Front: Nina and Mats on the path, framed by big trees.
    nina, nina_hands = figure(parts, "nina", world_coll, (-0.42, 0.0, 0.0), math.radians(-14), arm_swing=(8, 40))
    mats, mats_hands = figure(parts, "mats", world_coll, (0.42, 0.05, 0.0), math.radians(12), arm_swing=(4, 6))
    instance(lib["item_muetze"], world_coll, (0.0, 0.0, HIP_Z + NECK_Z), parent=nina)
    instance(lib["detail_fliegenpilz"], world_coll, nina_hands["right"] + Vector((0.0, -0.08, -0.06)), 0.22, parent=nina)
    instance(lib["item_schal"], world_coll, (0.0, 0.0, HIP_Z + NECK_Z), parent=mats)
    instance(lib["item_korb"], world_coll, mats_hands["right"], parent=mats)
    lantern = mats_hands["left"]
    instance(lib["item_laterne"], world_coll, lantern, parent=mats)
    instance(lib["item_laterne_glas"], nofs, lantern, parent=mats)
    # Mushrooms in the basket.
    instance(lib["detail_steinpilz"], world_coll, mats_hands["right"] + Vector((0.03, 0.0, -0.1)), 0.13, parent=mats)
    instance(lib["detail_pfifferling"], world_coll, mats_hands["right"] + Vector((-0.05, -0.03, -0.1)), 0.12, parent=mats)

    light = bpy.data.lights.new("laterne", "POINT")
    light.color = linear((255, 196, 110))
    light.energy = 14.0
    light.shadow_soft_size = 0.05
    lamp = bpy.data.objects.new("laterne", light)
    lamp.location = lantern + Vector((0.0, 0.0, -0.17))
    lamp.parent = mats
    nofs.objects.link(lamp)

    trees = [("tree_round", -2.9, 2.0, 1.8, 20), ("tree_round", 3.0, 2.4, 1.8, 140),
             ("tree_golden", -1.6, 8.0, 1.5, 70), ("tree_golden", 1.9, 9.0, 1.55, 200),
             ("tree_fir", -2.9, 7.5, 1.7, 0), ("tree_fir", 3.2, 8.5, 1.8, 40),
             ("tree_round", 0.3, 11.0, 1.7, 90)]
    rest = [("bush", -1.55, -0.2, 1.1, 30), ("bush", 1.95, 0.4, 1.0, 200), ("bush", -2.6, 3.2, 1.3, 90),
            ("stump", 1.3, 2.6, 0.9, 10)]
    for name, x, y, s, rot in trees + rest:
        instance(lib[name], world_coll, (x, y, 0.0), s, math.radians(rot))

    # Forest further back (also frames the back cover further left).
    kinds = ["tree_round", "tree_golden", "tree_golden", "tree_fir"]
    for _ in range(170):
        x = rng.uniform(-26, 22)
        y = rng.uniform(8.0, 42.0)
        if abs(x - 0.45 * math.sin(y * 0.22)) < 1.4 and y < 26:
            continue
        instance(lib[rng.choice(kinds)], world_coll, (x, y, 0.0), rng.uniform(1.4, 2.4), rng.uniform(0, 6.28))
    for _ in range(30):
        instance(lib["bush"], world_coll, (rng.uniform(-18, 16), rng.uniform(3, 20), 0.0), rng.uniform(0.9, 1.5), rng.uniform(0, 6.28))

    shrooms = [("detail_fliegenpilz", -0.95, -0.25, 0.36, 10), ("detail_fliegenpilz", -0.66, -0.55, 0.22, 60),
               ("detail_fliegenpilz", -1.2, -0.6, 0.17, 120), ("detail_steinpilz", 0.88, -0.2, 0.3, 30),
               ("detail_pfifferling", 1.18, -0.05, 0.19, 0), ("detail_pfifferling", 1.1, -0.45, 0.15, 80),
               ("detail_waldgott", 1.95, 1.1, 0.3, 0)]
    for name, x, y, s, rot in shrooms:
        instance(lib[name], nofs if name == "detail_waldgott" else world_coll, (x, y, 0.0), s, math.radians(rot))
    god = bpy.data.lights.new("waldgott", "POINT")
    god.color = linear((255, 244, 200))
    god.energy = 6.0
    god_obj = bpy.data.objects.new("waldgott", god)
    god_obj.location = (1.95, 0.95, 0.3)
    nofs.objects.link(god_obj)

    # --- Back: a clearing further left, the right side stays visible next to the blurb.
    back = [("tree_round", -4.3, 2.4, 1.8, 60), ("tree_golden", -8.2, 4.0, 1.7, 10),
            ("tree_fir", -5.4, 6.0, 1.6, 0), ("bush", -4.9, 0.9, 1.1, 0), ("stump", -3.7, 0.7, 0.8, 30)]
    for name, x, y, s, rot in back:
        instance(lib[name], world_coll, (x, y, 0.0), s, math.radians(rot))
    for name, x, y, s, rot in (("detail_fliegenpilz", -3.95, 0.15, 0.3, 0), ("detail_fliegenpilz", -3.7, -0.05, 0.18, 40),
                               ("detail_pfifferling", -4.3, 0.0, 0.2, 10)):
        instance(lib[name], world_coll, (x, y, 0.0), s, math.radians(rot))
    instance(lib["detail_waldgott"], nofs, (-4.6, 0.5, 0.0), 0.3)

    # Leaves on the ground and in the air.
    leaves = [lib["leaf_a"], lib["leaf_b"], lib["leaf_c"]]
    for _ in range(900):
        x, y = rng.uniform(-10, 5), rng.uniform(-1.8, 7)
        instance(rng.choice(leaves), world_coll, (x, y, 0.01), rng.uniform(1.0, 1.6), rng.uniform(0, 6.28))
    for _ in range(26):
        x, y, z = rng.uniform(-9, 3.5), rng.uniform(1.0, 6), rng.uniform(0.8, 3.2)
        instance(rng.choice(leaves), world_coll, (x, y, z), rng.uniform(1.4, 2.0),
                 rot=(rng.uniform(-1.2, 1.2), rng.uniform(-1.2, 1.2), rng.uniform(0, 6.28)))

    sun = bpy.data.lights.new("sonne", "SUN")
    sun.color = linear((255, 226, 180))
    sun.energy = 3.6
    sun.angle = math.radians(4)
    sun_obj = bpy.data.objects.new("sonne", sun)
    sun_obj.rotation_euler = (math.radians(52), 0.0, math.radians(-38))
    nofs.objects.link(sun_obj)
    return nofs


def setup_render(nofs):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.taa_render_samples = 32
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    sky_world()

    scene.render.use_freestyle = True
    scene.render.line_thickness_mode = "ABSOLUTE"
    scene.render.line_thickness = 1.0
    settings = scene.view_layers[0].freestyle_settings
    settings.crease_angle = math.radians(100)
    for ls in list(settings.linesets):
        settings.linesets.remove(ls)
    lineset = settings.linesets.new("tusche")
    lineset.select_by_visibility = True
    lineset.select_by_edge_types = True
    lineset.select_silhouette = True
    lineset.select_border = True
    lineset.select_crease = False
    lineset.select_external_contour = True
    lineset.select_by_collection = True
    lineset.collection = nofs
    lineset.collection_negation = "EXCLUSIVE"
    style = lineset.linestyle
    style.color = linear(INK)
    style.thickness = 4.0
    style.caps = "ROUND"
    fade = style.thickness_modifiers.new("ferne", "DISTANCE_FROM_CAMERA")
    fade.range_min, fade.range_max = 4.0, 30.0
    fade.value_min, fade.value_max = 1.0, 0.25
    fade.mapping = "LINEAR"
    fade.blend = "MULTIPLY"
    alpha = style.alpha_modifiers.new("dunst", "DISTANCE_FROM_CAMERA")
    alpha.range_min, alpha.range_max = 10.0, 36.0
    alpha.blend = "MULTIPLY"
    alpha.invert = True  # full ink near the camera, fading into the haze
    return scene


def camera(name, location, target, lens):
    cam = bpy.data.objects.new(name, bpy.data.cameras.new(name))
    cam.location = location
    cam.data.lens = lens
    cam.data.clip_end = 200
    direction = Vector(target) - Vector(location)
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    bpy.context.scene.collection.objects.link(cam)
    return cam


def render(scene, cam, size, path, scale):
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.resolution_percentage = scale
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("rendered", path)


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    target = os.path.abspath(args[0])
    scale = 25 if "preview" in args[1:] else 100
    os.makedirs(target, exist_ok=True)

    nofs = build_scene(random.Random(20260924))
    scene = setup_render(nofs)
    front = camera("vorne", (0.1, -3.1, 0.8), (0.1, 0.0, 1.38), 34)
    back = camera("hinten", (-6.2, -4.6, 1.2), (-6.2, 2.0, 1.5), 30)
    render(scene, front, FRONT_SIZE, os.path.join(target, "front.png"), scale)
    render(scene, back, BACK_SIZE, os.path.join(target, "back.png"), scale)


main()
