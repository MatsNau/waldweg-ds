"""Exports the hand-edited .blend files over the generated OBJ files.

    blender --background --factory-startup --python export_handmade.py -- <outdir> [file.blend ...]

Without file names it takes every .blend in assets/blender/handmade/. Each
object marked with "ds_export" replaces the generated model of the same name;
everything else in the file (mirrored copies, reference floor) is ignored.

A part that would break the DS pipeline stops the build instead of producing a
broken ROM - see dshandmade.problems().
"""
import glob
import os
import sys

import bpy

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import dshandmade  # noqa: E402

HANDMADE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "handmade")


def args():
    extra = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if not extra:
        raise SystemExit("FEHLER: kein Zielordner angegeben")
    target = os.path.abspath(extra[0])
    files = extra[1:] or sorted(glob.glob(os.path.join(HANDMADE_DIR, "*.blend")))
    return target, files


def export_file(path, target):
    bpy.ops.wm.open_mainfile(filepath=path)
    dshandmade.unhide_everything()

    objects = dshandmade.export_objects()
    if not objects:
        print(f"handmade {os.path.basename(path)}: keine markierten Objekte")
        return 0

    failed = 0
    for obj in objects:
        found = dshandmade.problems(obj)
        for level, text in found:
            prefix = "FEHLER" if level == dshandmade.ERROR else "Hinweis"
            print(f"{prefix} in {os.path.basename(path)} / {obj.name}: {text}")
        if dshandmade.has_errors(found):
            failed += 1
            continue
        out = dshandmade.export_object(obj, target)
        print(f"handmade {obj.name}: {dshandmade.triangle_count(obj)} Dreiecke -> {out}")
    return failed


def main():
    target, files = args()
    if not files:
        print("handmade: keine .blend-Dateien, es bleibt bei den erzeugten Modellen")
        return

    failed = sum(export_file(path, target) for path in files)
    if failed:
        raise SystemExit(f"FEHLER: {failed} Teile nicht exportiert")


main()
