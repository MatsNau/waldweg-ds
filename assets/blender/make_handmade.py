"""Creates an editable .blend from the generated models.

    blender --background --factory-startup --python make_handmade.py -- [group] [outfile]

The parts are built exactly as gen_models.py builds them (same seeds), then
placed where the game mounts them, so the whole figure is visible and editable
in one scene. Only the parts themselves carry "ds_export"; the mirrored second
arm and leg are linked copies for looking at, not for exporting.

From then on assets/blender/handmade/<group>.blend is the source for those
parts: tools/build_assets.sh writes it over the generated OBJ.
"""
import os
import random
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dshandmade  # noqa: E402
import models_characters  # noqa: E402
import models_cow  # noqa: E402
import models_items  # noqa: E402
import models_mushrooms  # noqa: E402
import models_mushrooms_detail  # noqa: E402
import models_world  # noqa: E402

# Same seeds as gen_models.py, otherwise the random parts (Mats curls, bark)
# would come out different from what is in the game right now.
GROUPS = {
    "world": (models_world, 20260914),
    "characters": (models_characters, 20260915),
    "mushrooms": (models_mushrooms, 20260916),
    "items": (models_items, 20260917),
    "mushrooms_detail": (models_mushrooms_detail, 20260918),
    "cow": (models_cow, 20260919),
}

HANDMADE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "handmade")

# Joint positions, from models_characters (which keeps them in sync with
# source/entities/CharacterRig.cpp). Blender space: Z up, character faces -Y.
HIP_Z = models_characters.HIP_Z
LEG_X = models_characters.LEG_X
SHOULDER_X = models_characters.SHOULDER_X
SHOULDER_Z = models_characters.SHOULDER_Z
NECK_Z = models_characters.NECK_Z

# The game draws arm and leg twice, translated - not mirrored (CharacterRig::Draw).
CHARACTER_PARTS = {
    "leg": ((LEG_X, 0.0, HIP_Z), (-LEG_X, 0.0, HIP_Z)),
    "body": ((0.0, 0.0, HIP_Z), None),
    "arm": ((SHOULDER_X, 0.0, HIP_Z + SHOULDER_Z), (-SHOULDER_X, 0.0, HIP_Z + SHOULDER_Z)),
    "head": ((0.0, 0.0, HIP_Z + NECK_Z), None),
}
FIGURE_X = {"nina": -0.55, "mats": 0.55}


def args():
    extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    group = extra[0] if extra else "characters"
    if group not in GROUPS:
        raise SystemExit(f"unbekannte Gruppe {group!r}, waehle aus: {', '.join(sorted(GROUPS))}")
    out = extra[1] if len(extra) > 1 else os.path.join(HANDMADE_DIR, f"{group}.blend")
    return group, os.path.abspath(out)


def collection(name):
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def move_to(obj, coll):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    coll.objects.link(obj)


def linked_copy(obj, name, location, coll):
    """Second arm/leg: same mesh, so editing one updates both."""
    copy = bpy.data.objects.new(name, obj.data)
    copy.location = location
    coll.objects.link(copy)
    return copy


def layout_characters(objects, export_coll, ref_coll):
    for obj in objects:
        figure, _, part = obj.name.partition("_")
        mount, mirror = CHARACTER_PARTS[part]
        offset = FIGURE_X.get(figure, 0.0)
        dshandmade.mark_export(obj, (mount[0] + offset, mount[1], mount[2]))
        move_to(obj, export_coll)
        if mirror is not None:
            linked_copy(obj, f"{obj.name}_2", (mirror[0] + offset, mirror[1], mirror[2]), ref_coll)


def layout_grid(objects, export_coll, _ref_coll):
    """Everything that has no rig: a row of parts, spaced by their own width."""
    x = 0.0
    for obj in objects:
        width = max(obj.dimensions.x, 0.4)
        x += width / 2
        dshandmade.mark_export(obj, (x, 0.0, 0.0))
        move_to(obj, export_coll)
        x += width / 2 + 0.3


def add_ground(coll, span):
    """Plain reference floor: the characters stand on z = 0."""
    mesh = bpy.data.meshes.new("ref_boden")
    mesh.from_pydata([(-span, -span, 0.0), (span, -span, 0.0),
                      (span, span, 0.0), (-span, span, 0.0)], [], [(0, 1, 2, 3)])
    mesh.update()
    obj = bpy.data.objects.new("ref_boden", mesh)
    obj.display_type = "WIRE"
    obj.hide_select = True
    coll.objects.link(obj)


def show_materials():
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                for space in area.spaces:
                    if space.type == "VIEW_3D":
                        space.shading.type = "MATERIAL"


def main():
    group, out = args()
    module, seed = GROUPS[group]

    bpy.ops.wm.read_factory_settings(use_empty=True)
    objects = module.build(random.Random(seed))

    export_coll = collection("Export")
    ref_coll = collection("Referenz")
    if group == "characters":
        layout_characters(objects, export_coll, ref_coll)
        add_ground(ref_coll, 1.6)
    else:
        layout_grid(objects, export_coll, ref_coll)

    for obj in objects:
        dshandmade.assign_palette_material(obj)

    show_materials()
    os.makedirs(os.path.dirname(out), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=out)

    total = sum(dshandmade.triangle_count(obj) for obj in objects)
    print(f"handmade-seed {group}: {len(objects)} Teile, {total} Dreiecke -> {out}")
    for obj in objects:
        print(f"  {obj.name}: {dshandmade.triangle_count(obj)} Dreiecke")


main()
