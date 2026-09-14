#!/bin/sh
# Generates models, textures and the font into nitrofiles/.
# Run inside the Wonderful Toolchain environment:  wf.cmd tools/build_assets.sh
set -e
cd "$(dirname "$0")/.."

BLENDER="${BLENDER:-/c/Program Files/Blender Foundation/Blender 5.2/blender.exe}"
PYTHON="${PYTHON:-python}"
OBJ2DL="$BLOCKSDSEXT/nitro-engine/tools/obj2dl/obj2dl.py"
GRIT="$BLOCKSDS/tools/grit/grit"
BUILD=assets/build

mkdir -p "$BUILD" nitrofiles/models nitrofiles/textures nitrofiles/fnt

echo "== Blender: Modelle erzeugen"
rm -f "$BUILD"/*.obj
"$BLENDER" --background --factory-startup --python assets/blender/gen_testmodels.py -- "$BUILD" \
    > "$BUILD/blender.log" 2>&1 || true
grep "exported" "$BUILD/blender.log" || true
for model in ground tree fliegenpilz; do
    test -f "$BUILD/$model.obj" || { echo "Fehlt: $BUILD/$model.obj"; tail -20 "$BUILD/blender.log"; exit 1; }
done

echo "== obj2dl: Modelle konvertieren"
for model in ground tree fliegenpilz; do
    "$PYTHON" "$OBJ2DL" --input "$BUILD/$model.obj" --output "nitrofiles/models/$model.bin" --texture 16 16
done

echo "== grit: Palette-Textur"
"$GRIT" "$BUILD/palette.png" -W3 -ftr -fh! -gx -gb -gB16 -gT! -o nitrofiles/textures/palette

echo "== Schrift mit Umlauten"
"$PYTHON" assets/fonts/patch_umlauts.py

ls -la nitrofiles/models nitrofiles/textures nitrofiles/fnt
