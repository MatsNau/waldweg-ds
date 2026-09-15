"""Renders the distant scenery of the final picture (upper screen).

Outputs (512x384, transparent background, stylised later by assets/ui/gen_ending.py):
  ending_flat.png, ending_shade.png
  ending_chimneys.txt   chimney tops in 256x192 screen pixels, one "x y" per line

Run headless:  blender --background --factory-startup --python render_ending.py -- <palette.png> <outdir>
"""
import math
import os
import random
import sys

import bpy
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import models_ending  # noqa: E402

WIDTH = 512
HEIGHT = 384
CAMERA = (0.0, -6.0, 3.2)
LOOK_AT = (0.0, 40.0, 3.6)


def main():
    args = sys.argv[sys.argv.index("--") + 1:]
    palette_path, target = os.path.abspath(args[0]), os.path.abspath(args[1])
    os.makedirs(target, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    objects = models_ending.build_backdrop(random.Random(20260920))

    image = bpy.data.images.load(palette_path)
    material = bpy.data.materials.new("palette")
    material.use_nodes = True
    texture = material.node_tree.nodes.new("ShaderNodeTexImage")
    texture.image = image
    texture.interpolation = "Closest"
    material.node_tree.links.new(texture.outputs["Color"],
                                 material.node_tree.nodes["Principled BSDF"].inputs["Base Color"])
    for obj in objects:
        obj.data.materials.append(material)
        for polygon in obj.data.polygons:
            polygon.use_smooth = True

    camera = bpy.data.objects.new("camera", bpy.data.cameras.new("camera"))
    bpy.context.scene.collection.objects.link(camera)
    camera.location = Vector(CAMERA)
    camera.rotation_euler = (Vector(LOOK_AT) - camera.location).to_track_quat("-Z", "Y").to_euler()
    camera.data.lens = 30

    scene = bpy.context.scene
    scene.camera = camera
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.color_type = "TEXTURE"
    scene.display.shading.show_backface_culling = False
    scene.render.film_transparent = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.render.resolution_x = WIDTH
    scene.render.resolution_y = HEIGHT
    scene.render.filter_size = 0.6
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"

    for kind, light in (("flat", "FLAT"), ("shade", "STUDIO")):
        scene.display.shading.light = light
        scene.render.filepath = os.path.join(target, f"ending_{kind}.png")
        bpy.ops.render.render(write_still=True)

    with open(os.path.join(target, "ending_chimneys.txt"), "w") as f:
        for top in models_ending.chimney_tops():
            view = world_to_camera_view(scene, camera, top)
            x = round(view.x * 256)
            y = round((1.0 - view.y) * 192)
            f.write(f"{x} {y}\n")
    print("rendered ending")


main()
