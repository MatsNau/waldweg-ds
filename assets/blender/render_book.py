"""Renders the book illustrations of the detailed mushrooms.

Three views per species with transparent background:
  0 side view, 1 underside (from below), 2 feature close-up (stem base, ridges, wood).

Each view is rendered twice at 144x144 for the drawing style (assets/ui/gen_book.py):
  <key>_<n>_flat.png   flat colours (outlines between colour areas)
  <key>_<n>_shade.png  smooth studio lighting (cel shading bands)

Run headless:  blender --background --factory-startup --python render_book.py -- <palette.png> <outdir>
"""
import math
import os
import random
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import models_mushrooms_detail  # noqa: E402

SIZE = 144

# name -> list of (camera position, look-at target, orthographic scale)
VIEWS = {
    "steinpilz": [((0, -3, 0.9), (0, 0, 0.5), 1.35), ((0, -1.6, -0.7), (0, 0, 0.55), 1.3),
                  ((0, -2, 0.45), (0, 0, 0.35), 0.75)],
    "satansroehrling": [((0, -3, 0.9), (0, 0, 0.5), 1.35), ((0, -1.6, -0.7), (0, 0, 0.55), 1.3),
                        ((0, -2, 0.45), (0, 0, 0.35), 0.75)],
    "champignon": [((0, -3, 0.9), (0, 0, 0.45), 1.2), ((0, -1.5, -0.6), (0, 0, 0.55), 1.1),
                   ((0, -2, 0.3), (0, 0, 0.3), 0.7)],
    "knollenblaetterpilz": [((0, -3, 1.0), (0, 0, 0.5), 1.25), ((0, -1.5, -0.4), (0, 0, 0.7), 1.1),
                            ((0, -2, 0.25), (0, 0, 0.2), 0.65)],
    "pfifferling": [((0, -3, 0.9), (0, 0, 0.4), 1.2), ((0, -1.5, -0.6), (0, 0, 0.5), 1.2),
                    ((0.8, -2, 0.1), (0, 0, 0.45), 0.8)],
    "fliegenpilz": [((0, -3, 1.0), (0, 0, 0.55), 1.35), ((0, -1.5, -0.4), (0, 0, 0.75), 1.25),
                    ((0, -2, 0.3), (0, 0, 0.2), 0.7)],
    "oelbaum_trichterling": [((0, -3, 1.0), (0, 0, 0.5), 1.4), ((0.9, -1.6, 0.3), (0, 0, 0.62), 0.9),
                             ((0, -3, 1.6), (0, 0, 0.35), 1.6)],
    "waldgott": [((0, -3, 1.0), (0, 0, 0.65), 1.5), ((0, -1.5, -0.2), (0, 0, 0.85), 1.0),
                 ((0, -2, 1.3), (0, 0, 1.05), 0.8)],
}


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    palette_path, target = os.path.abspath(args[0]), os.path.abspath(args[1])
    os.makedirs(target, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    objects = models_mushrooms_detail.build(random.Random(20260918))

    image = bpy.data.images.load(palette_path)
    material = bpy.data.materials.new("palette")
    material.use_nodes = True
    texture = material.node_tree.nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Closest"
    material.node_tree.links.new(texture.outputs["Color"],
                                 material.node_tree.nodes["Principled BSDF"].inputs["Base Color"])

    camera = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
    camera.data.type = "ORTHO"
    bpy.context.scene.collection.objects.link(camera)

    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "TEXTURE"
    scene.display.shading.show_backface_culling = False
    scene.display.shading.show_object_outline = False
    scene.display.shading.show_cavity = False
    scene.render.film_transparent = True
    # No filmic tone mapping: palette colours (e.g. white caps) must stay as they are.
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.resolution_x = SIZE
    scene.render.resolution_y = SIZE
    scene.render.filter_size = 0.6
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"

    for obj in objects:
        obj.data.materials.append(material)
        obj.hide_render = True
        # Smooth normals give round, drawing-like shading bands (the DS model stays faceted).
        for polygon in obj.data.polygons:
            polygon.use_smooth = True

    for obj in objects:
        key = obj.name.replace("detail_", "")
        obj.hide_render = False
        for index, (position, look, scale) in enumerate(VIEWS[key]):
            camera.location = Vector(position)
            look_at(camera, look)
            camera.data.ortho_scale = scale
            for kind, light in (("flat", "FLAT"), ("shade", "STUDIO")):
                scene.display.shading.light = light
                scene.render.filepath = os.path.join(target, f"{key}_{index}_{kind}.png")
                bpy.ops.render.render(write_still=True)
            print(f"rendered {key}_{index}")
        obj.hide_render = True


main()
