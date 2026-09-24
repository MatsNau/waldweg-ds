#!/bin/sh
# Generates models, textures, the font, the music stream (nitrofiles/) and the ambience (audio/).
# Run inside the Wonderful Toolchain environment:  wf.cmd sh tools/build_assets.sh
# The ambience additionally needs ffmpeg (FFMPEG=... to point at it).
set -e
cd "$(dirname "$0")/.."

if [ -z "$BLENDER" ]; then
    for drive in c d; do
        BLENDER="/$drive/Program Files/Blender Foundation/Blender 5.2/blender.exe"
        [ -x "$BLENDER" ] && break
    done
fi
PYTHON="${PYTHON:-python}"
OBJ2DL="$BLOCKSDSEXT/nitro-engine/tools/obj2dl/obj2dl.py"
GRIT="$BLOCKSDS/tools/grit/grit"
BUILD=assets/build
TEX_SIZE=32

mkdir -p "$BUILD" nitrofiles/models nitrofiles/textures nitrofiles/fnt

echo "== Blender: Modelle erzeugen"
rm -f "$BUILD"/*.obj
"$BLENDER" --background --factory-startup --python assets/blender/gen_models.py -- "$BUILD" \
    > "$BUILD/blender.log" 2>&1 || true
if ! grep "exported" "$BUILD/blender.log"; then
    echo "Blender hat keine Modelle exportiert:"
    tail -30 "$BUILD/blender.log"
    exit 1
fi
if grep -q "Traceback" "$BUILD/blender.log"; then
    grep -A30 "Traceback" "$BUILD/blender.log"
    exit 1
fi

echo "== Blender: handgemachte Teile ueber die erzeugten schreiben"
if ls assets/blender/handmade/*.blend > /dev/null 2>&1; then
    "$BLENDER" --background --factory-startup --python assets/blender/export_handmade.py -- "$BUILD" > "$BUILD/handmade.log" 2>&1 || true
    if grep -q "Traceback" "$BUILD/handmade.log"; then
        grep -A30 "Traceback" "$BUILD/handmade.log"
        exit 1
    fi
    grep "^Hinweis " "$BUILD/handmade.log" || true
    if grep -q "^FEHLER" "$BUILD/handmade.log"; then
        grep "^FEHLER" "$BUILD/handmade.log"
        exit 1
    fi
    grep "^handmade " "$BUILD/handmade.log"
else
    echo "  keine, es bleibt bei den erzeugten Modellen"
fi

echo "== obj2dl: Modelle konvertieren"
rm -f nitrofiles/models/*.bin
for obj in "$BUILD"/*.obj; do
    model=$(basename "$obj" .obj)
    "$PYTHON" "$OBJ2DL" --input "$obj" --output "nitrofiles/models/$model.bin" --texture $TEX_SIZE $TEX_SIZE
done

echo "== grit: Palette-Textur"
"$GRIT" "$BUILD/palette.png" -W3 -ftr -fh! -gx -gb -gB16 -gT! -o nitrofiles/textures/palette

echo "== Unterer Bildschirm: Pixelgrafik erzeugen und konvertieren"
UI_BUILD="$BUILD/ui"
rm -rf "$UI_BUILD"
"$PYTHON" assets/ui/gen_ui.py "$UI_BUILD"
mkdir -p nitrofiles/ui
rm -f nitrofiles/ui/*
(
    cd "$UI_BUILD"
    # Tiled backgrounds (duplicate tiles removed).
    for bg in bg_bar bg_dialog; do
        "$GRIT" $bg.png -ftB -fh! -gTFF00FF -gt -gB8 -mR8 -mLs
    done
    # Map tileset: one 8 px column exported as raw tiles in order (no map).
    "$GRIT" map_tiles.png -ftB -fh! -gTFF00FF -gt -gB8 -m!
    # Sprite sheets (frames stacked vertically).
    for sprite in spr_icons spr_items; do
        "$GRIT" $sprite.png -ftB -fh! -gTFF00FF -gt -gB8 -m!
    done
)
mv "$UI_BUILD"/*.img "$UI_BUILD"/*.pal "$UI_BUILD"/*.map nitrofiles/ui/
# Icons for the 3D inspection view (Nitro Engine texture with alpha).
"$GRIT" "$UI_BUILD/icons3d.png" -W3 -ftr -fh! -gx -gb -gB16 -gTFF00FF -o nitrofiles/textures/icons3d
"$GRIT" "$UI_BUILD/treecards.png" -W3 -ftr -fh! -gx -gb -gB16 -gTFF00FF -o nitrofiles/textures/treecards

echo "== Pilzbüchlein: Illustrationen rendern und Seiten zusammensetzen"
"$BLENDER" --background --factory-startup --python assets/blender/render_book.py --     "$BUILD/palette.png" "$BUILD/book" > "$BUILD/book.log" 2>&1 || true
if grep -q "Traceback" "$BUILD/book.log"; then
    grep -A30 "Traceback" "$BUILD/book.log"
    exit 1
fi
rm -rf "$BUILD/pages"
"$PYTHON" assets/ui/gen_book.py "$BUILD/book" "$BUILD/pages"
mkdir -p nitrofiles/book
rm -f nitrofiles/book/*
(
    cd "$BUILD/pages"
    for page in page*.png; do
        "$GRIT" "$page" -ftB -fh! -gTFF00FF -gt -gB8 -mR8 -mLs
    done
)
mv "$BUILD/pages"/*.img "$BUILD/pages"/*.pal "$BUILD/pages"/*.map nitrofiles/book/

echo "== Schlussbild: Himmel, Berge und Dorf (oberer Bildschirm)"
"$BLENDER" --background --factory-startup --python assets/blender/render_ending.py -- \
    "$BUILD/palette.png" "$BUILD/ending" > "$BUILD/ending.log" 2>&1 || true
if grep -q "Traceback" "$BUILD/ending.log"; then
    grep -A30 "Traceback" "$BUILD/ending.log"
    exit 1
fi
"$PYTHON" assets/ui/gen_ending.py "$BUILD/ending" "$BUILD/ending"
(
    cd "$BUILD/ending"
    "$GRIT" ending_sky.png -ftB -fh! -gTFF00FF -gt -gB8 -mR8 -mLs
)
mv "$BUILD/ending"/ending_sky.img "$BUILD/ending"/ending_sky.pal "$BUILD/ending"/ending_sky.map nitrofiles/book/
cp "$BUILD/ending/ending_chimneys.txt" nitrofiles/book/

echo "== Schritte, Umblaettern und Wald-Ambience (mmutil packt sie beim Build in die Soundbank)"
"$PYTHON" assets/audio/gen_sfx.py audio
# Braucht ffmpeg und die Aufnahme; fehlt eines davon, bleibt die eingecheckte Fassung liegen.
FFMPEG="${FFMPEG:-/c/msys64/ucrt64/bin/ffmpeg.exe}" "$PYTHON" assets/audio/make_ambience.py audio

echo "== Musik: Soundtrack als Stream (nitrofiles/music/, nicht im Repo)"
# Braucht ffmpeg und die MP3; fehlt eines davon, laeuft das Spiel ohne Musik.
FFMPEG="${FFMPEG:-/c/msys64/ucrt64/bin/ffmpeg.exe}" "$PYTHON" assets/audio/make_music.py

echo "== Icon fuer das DS-Menue (Makefile: GAME_ICON)"
"$PYTHON" assets/ui/gen_icon.py assets/icon.png

echo "== Schrift mit Umlauten"
"$PYTHON" assets/fonts/patch_umlauts.py

echo "== Schrift als Textur (Dialoge oben, 3D-Quads)"
"$PYTHON" assets/fonts/make_font_texture.py "$BUILD/font.png"
"$GRIT" "$BUILD/font.png" -W3 -ftr -fh! -gx -gb -gB16 -gTFF00FF -o nitrofiles/textures/font

ls -la nitrofiles/models nitrofiles/textures nitrofiles/fnt nitrofiles/ui
