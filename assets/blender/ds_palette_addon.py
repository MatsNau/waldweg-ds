"""Blender add-on for hand-editing the Waldweg models.

Install once: Edit > Preferences > Add-ons > dropdown > Install from Disk >
assets/blender/ds_palette_addon.py, then tick it. It adds a "DS" tab to the
sidebar of the 3D viewport (N key).

What it is for: on the DS a face gets its colour from its UV, which has to sit
on the centre of one swatch of the 32x32 palette texture. Doing that by hand in
the UV editor is unusable, so the panel assigns the UV for a whole selection
with one click, and checks everything else the pipeline cares about.

The palette itself is not duplicated here - the add-on imports dsmesh.py from
the project, so there is one list of colours, not two.
"""
import os
import sys

import bmesh
import bpy

bl_info = {
    "name": "Waldweg DS: Palette und Teile-Check",
    "author": "Waldweg",
    "version": (1, 0),
    "blender": (4, 2, 0),
    "location": "3D-Ansicht > Seitenleiste (N) > DS",
    "description": "Farbfelder der DS-Palette zuweisen und Teile vor dem Export pruefen",
    "category": "Mesh",
}

_previews = None
_preview_dir = None


# --- Finding the project ----------------------------------------------------

def _candidates():
    prefs = bpy.context.preferences.addons.get(__name__)
    if prefs and prefs.preferences.project_root:
        root = bpy.path.abspath(prefs.preferences.project_root)
        yield os.path.join(root, "assets", "blender")
        yield root
    if bpy.data.filepath:
        # A handmade .blend sits in assets/blender/handmade/, so walk upwards.
        here = os.path.dirname(bpy.data.filepath)
        for _ in range(5):
            yield here
            yield os.path.join(here, "assets", "blender")
            here = os.path.dirname(here)


def project_dir():
    """Directory holding dsmesh.py, or None if it cannot be found."""
    for path in _candidates():
        if path and os.path.isfile(os.path.join(path, "dsmesh.py")):
            return path
    return None


def modules():
    """(dsmesh, dshandmade) or None - imported from the project, never copied."""
    path = project_dir()
    if path is None:
        return None
    if path not in sys.path:
        sys.path.insert(0, path)
    try:
        import dshandmade
        import dsmesh
    except ImportError:
        return None
    return dsmesh, dshandmade


# --- Colour chips for the buttons -------------------------------------------

def previews_for(dsmesh):
    """One 16x16 solid-colour icon per swatch, built in memory."""
    global _previews, _preview_dir
    path = project_dir()
    if _previews is not None and _preview_dir == path:
        return _previews
    clear_previews()
    try:
        import bpy.utils.previews
        coll = bpy.utils.previews.new()
        for index, (name, (r, g, b)) in enumerate(dsmesh.PALETTE):
            preview = coll.new(f"{index:02d}_{name}")
            preview.icon_size = (16, 16)
            preview.icon_pixels_float = [r / 255.0, g / 255.0, b / 255.0, 1.0] * 16 * 16
        _previews, _preview_dir = coll, path
    except Exception:  # older/newer API, or no preview support: text buttons
        _previews, _preview_dir = {}, path
    return _previews


def clear_previews():
    global _previews, _preview_dir
    if _previews:
        try:
            import bpy.utils.previews
            bpy.utils.previews.remove(_previews)
        except Exception:
            pass
    _previews, _preview_dir = None, None


def icon_id(previews, index, name):
    key = f"{index:02d}_{name}"
    if previews and key in previews:
        return previews[key].icon_id
    return 0


# --- Selection helpers ------------------------------------------------------

def selected_faces(context):
    """(object, bmesh, faces) in edit mode, or (object, None, None) in object mode."""
    obj = context.object
    if obj is None or obj.type != "MESH":
        return None, None, None
    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        return obj, bm, [f for f in bm.faces if f.select]
    return obj, None, None


# --- Operators --------------------------------------------------------------

class DS_OT_set_swatch(bpy.types.Operator):
    bl_idname = "ds.set_swatch"
    bl_label = "Farbfeld zuweisen"
    bl_options = {"REGISTER", "UNDO"}

    index: bpy.props.IntProperty(name="Farbfeld", default=0)

    @classmethod
    def description(cls, context, properties):
        mods = modules()
        if mods is None:
            return "Farbfeld zuweisen"
        name, (r, g, b) = mods[0].PALETTE[properties.index]
        return f"{name}  (RGB {r}, {g}, {b})"

    def execute(self, context):
        mods = modules()
        if mods is None:
            self.report({"ERROR"}, "Projektordner nicht gefunden (siehe Add-on-Einstellungen)")
            return {"CANCELLED"}
        dsmesh, dshandmade = mods

        obj, bm, faces = selected_faces(context)
        if obj is None:
            self.report({"ERROR"}, "Kein Mesh-Objekt aktiv")
            return {"CANCELLED"}

        if bm is not None:
            if not faces:
                self.report({"WARNING"}, "Keine Flaechen ausgewaehlt")
                return {"CANCELLED"}
            dshandmade.set_face_swatch(bm, faces, self.index)
            bmesh.update_edit_mesh(obj.data)
            count = len(faces)
        else:
            # Object mode: the whole object, handy for a fresh part.
            work = bmesh.new()
            work.from_mesh(obj.data)
            dshandmade.set_face_swatch(work, work.faces, self.index)
            work.to_mesh(obj.data)
            work.free()
            obj.data.update()
            count = len(obj.data.polygons)

        context.scene.ds_swatch = self.index
        self.report({"INFO"}, f"{count} Flaechen: {dsmesh.PALETTE[self.index][0]}")
        return {"FINISHED"}


class DS_OT_pick_swatch(bpy.types.Operator):
    bl_idname = "ds.pick_swatch"
    bl_label = "Farbe der aktiven Flaeche uebernehmen"
    bl_options = {"REGISTER"}

    def execute(self, context):
        mods = modules()
        if mods is None:
            self.report({"ERROR"}, "Projektordner nicht gefunden")
            return {"CANCELLED"}
        dsmesh, dshandmade = mods

        obj, bm, _ = selected_faces(context)
        if bm is None:
            self.report({"ERROR"}, "Nur im Bearbeitungsmodus")
            return {"CANCELLED"}
        face = bm.faces.active
        if face is None:
            self.report({"WARNING"}, "Keine aktive Flaeche")
            return {"CANCELLED"}
        index = dshandmade.face_swatch(bm, face)
        if index is None:
            self.report({"WARNING"}, "Diese Flaeche liegt auf keinem Farbfeld")
            return {"CANCELLED"}
        context.scene.ds_swatch = index
        self.report({"INFO"}, dsmesh.PALETTE[index][0])
        return {"FINISHED"}


class DS_OT_select_bad_faces(bpy.types.Operator):
    bl_idname = "ds.select_bad_faces"
    bl_label = "Flaechen ohne Farbfeld auswaehlen"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        mods = modules()
        if mods is None:
            self.report({"ERROR"}, "Projektordner nicht gefunden")
            return {"CANCELLED"}
        _, dshandmade = mods

        obj, bm, _ = selected_faces(context)
        if bm is None:
            self.report({"ERROR"}, "Nur im Bearbeitungsmodus")
            return {"CANCELLED"}
        bad = 0
        for face in bm.faces:
            face.select_set(dshandmade.face_swatch(bm, face) is None)
            bad += dshandmade.face_swatch(bm, face) is None
        bm.select_flush(False)
        bmesh.update_edit_mesh(obj.data)
        self.report({"INFO"}, f"{bad} Flaechen ohne Farbfeld")
        return {"FINISHED"}


class DS_OT_mark_export(bpy.types.Operator):
    bl_idname = "ds.mark_export"
    bl_label = "Als Spielteil markieren"
    bl_description = ("Dieses Objekt wird beim Bauen ueber das erzeugte Modell "
                      "gleichen Namens geschrieben. Die aktuelle Position gilt "
                      "als Gelenkpunkt")
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        mods = modules()
        if mods is None:
            self.report({"ERROR"}, "Projektordner nicht gefunden")
            return {"CANCELLED"}
        _, dshandmade = mods
        obj = context.object
        if obj is None or obj.type != "MESH":
            self.report({"ERROR"}, "Kein Mesh-Objekt aktiv")
            return {"CANCELLED"}
        dshandmade.mark_export(obj, tuple(obj.location))
        dshandmade.assign_palette_material(obj)
        return {"FINISHED"}


class DS_OT_bake_offset(bpy.types.Operator):
    bl_idname = "ds.bake_offset"
    bl_label = "Verschiebung ins Mesh uebernehmen"
    bl_description = ("Das Objekt steht neben seinem Gelenkpunkt. Die Verschiebung "
                      "wandert in die Vertices, damit sie auch im Spiel ankommt, "
                      "und Drehung/Skalierung werden angewendet")
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        mods = modules()
        if mods is None:
            self.report({"ERROR"}, "Projektordner nicht gefunden")
            return {"CANCELLED"}
        _, dshandmade = mods
        obj = context.object
        if obj is None or obj.type != "MESH":
            self.report({"ERROR"}, "Kein Mesh-Objekt aktiv")
            return {"CANCELLED"}

        if obj.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")
        context.view_layer.objects.active = obj
        obj.select_set(True)

        mount = dshandmade.mount_of(obj)
        delta = [a - b for a, b in zip(obj.location, mount)]
        for vert in obj.data.vertices:
            vert.co = [c + d for c, d in zip(vert.co, delta)]
        obj.location = mount
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
        obj.data.update()
        self.report({"INFO"}, "Pivot wieder auf dem Gelenkpunkt")
        return {"FINISHED"}


class DS_OT_export(bpy.types.Operator):
    bl_idname = "ds.export"
    bl_label = "Teile nach assets/build exportieren"
    bl_description = ("Schreibt alle markierten Teile als OBJ. Fuer das ROM danach "
                      "build_assets.sh und build.cmd laufen lassen")
    bl_options = {"REGISTER"}

    def execute(self, context):
        mods = modules()
        if mods is None:
            self.report({"ERROR"}, "Projektordner nicht gefunden")
            return {"CANCELLED"}
        _, dshandmade = mods

        root = os.path.dirname(os.path.dirname(project_dir()))  # <root>/assets/blender -> <root>
        target = os.path.join(root, "assets", "build")
        os.makedirs(target, exist_ok=True)

        if context.object and context.object.mode != "OBJECT":
            bpy.ops.object.mode_set(mode="OBJECT")

        written, blocked = 0, []
        for obj in dshandmade.export_objects(context.scene):
            found = dshandmade.problems(obj)
            if dshandmade.has_errors(found):
                blocked.append(obj.name)
                continue
            dshandmade.export_object(obj, target)
            written += 1
        if blocked:
            self.report({"ERROR"}, f"{written} exportiert, Fehler in: {', '.join(blocked)}")
            return {"FINISHED"}
        self.report({"INFO"}, f"{written} Teile nach {target}")
        return {"FINISHED"}


# --- Panels -----------------------------------------------------------------

class DS_PT_base(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "DS"


class DS_PT_palette(DS_PT_base):
    bl_idname = "DS_PT_palette"
    bl_label = "Palette"

    def draw(self, context):
        layout = self.layout
        mods = modules()
        if mods is None:
            layout.label(text="Projektordner nicht gefunden", icon="ERROR")
            layout.label(text="Add-on-Einstellungen: Projektordner setzen")
            return
        dsmesh, _ = mods
        previews = previews_for(dsmesh)

        obj = context.object
        if obj is None or obj.type != "MESH":
            layout.label(text="Kein Mesh aktiv", icon="INFO")
            return

        current = context.scene.ds_swatch
        if 0 <= current < len(dsmesh.PALETTE):
            layout.label(text=dsmesh.PALETTE[current][0],
                         icon_value=icon_id(previews, current, dsmesh.PALETTE[current][0]))
        layout.operator("ds.pick_swatch", text="Farbe aufnehmen", icon="EYEDROPPER")

        if obj.mode != "EDIT":
            layout.label(text="Objektmodus: faerbt das ganze Teil", icon="INFO")

        grid = layout.grid_flow(row_major=True, columns=8, even_columns=True,
                                even_rows=True, align=True)
        for index, (name, _) in enumerate(dsmesh.PALETTE):
            icon = icon_id(previews, index, name)
            if icon:
                grid.operator("ds.set_swatch", text="", icon_value=icon).index = index
            else:
                grid.operator("ds.set_swatch", text=name[:6]).index = index


class DS_PT_part(DS_PT_base):
    bl_idname = "DS_PT_part"
    bl_label = "Teil"

    def draw(self, context):
        layout = self.layout
        mods = modules()
        if mods is None:
            layout.label(text="Projektordner nicht gefunden", icon="ERROR")
            return
        _, dshandmade = mods

        obj = context.object
        if obj is None or obj.type != "MESH":
            layout.label(text="Kein Mesh aktiv", icon="INFO")
            return

        if not dshandmade.is_export(obj):
            layout.label(text="Kein Spielteil (nur Referenz)", icon="INFO")
            layout.operator("ds.mark_export", icon="EXPORT")
            return

        box = layout.box()
        box.label(text=obj.name, icon="MESH_DATA")
        tris = dshandmade.triangle_count(obj)
        box.label(text=f"{tris} Dreiecke, {tris * 3} Vertices auf dem DS")
        mount = dshandmade.mount_of(obj)
        box.label(text="Gelenk: " + ", ".join(f"{c:.3f}" for c in mount))

        found = dshandmade.problems(obj)
        if not found:
            layout.label(text="Alles in Ordnung", icon="CHECKMARK")
        for level, text in found:
            row = layout.row()
            row.alert = level == dshandmade.ERROR
            row.label(text=text, icon="ERROR" if level == dshandmade.ERROR else "INFO")

        col = layout.column(align=True)
        col.operator("ds.bake_offset", icon="ORIENTATION_LOCAL")
        col.operator("ds.select_bad_faces", icon="RESTRICT_SELECT_OFF")
        col.operator("ds.export", icon="EXPORT")


class DS_Preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

    project_root: bpy.props.StringProperty(
        name="Projektordner",
        description="Ordner mit assets/blender (leer = aus der geoeffneten Datei raten)",
        subtype="DIR_PATH",
        default="")

    def draw(self, context):
        self.layout.prop(self, "project_root")
        found = project_dir()
        self.layout.label(text=f"gefunden: {found}" if found else "dsmesh.py nicht gefunden",
                          icon="CHECKMARK" if found else "ERROR")


CLASSES = (DS_Preferences, DS_OT_set_swatch, DS_OT_pick_swatch, DS_OT_select_bad_faces,
           DS_OT_mark_export, DS_OT_bake_offset, DS_OT_export,
           DS_PT_palette, DS_PT_part)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.ds_swatch = bpy.props.IntProperty(name="Farbfeld", default=0)


def unregister():
    clear_previews()
    del bpy.types.Scene.ds_swatch
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
