"""Generates all models and the shared palette texture.

Run headless:  blender --background --factory-startup --python gen_models.py -- <outdir>
"""
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dsmesh  # noqa: E402
import models_characters  # noqa: E402
import models_cow  # noqa: E402
import models_ending  # noqa: E402
import models_items  # noqa: E402
import models_mushrooms  # noqa: E402
import models_mushrooms_detail  # noqa: E402
import models_world  # noqa: E402


def main():
    target = dsmesh.out_dir()
    os.makedirs(target, exist_ok=True)

    bpy.ops.wm.read_factory_settings(use_empty=True)

    dsmesh.write_palette_png(os.path.join(target, "palette.png"))
    objects = models_world.build(random.Random(20260914))
    objects += models_characters.build(random.Random(20260915))
    objects += models_mushrooms.build(random.Random(20260916))
    objects += models_items.build(random.Random(20260917))
    objects += models_mushrooms_detail.build(random.Random(20260918))
    objects += models_cow.build(random.Random(20260919))
    objects += models_ending.build(random.Random(20260920))
    dsmesh.export_all(objects, target)


main()
