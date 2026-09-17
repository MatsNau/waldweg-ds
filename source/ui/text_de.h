#pragma once

#include <nds/ndstypes.h>

// Writes UTF-8 German text (ä ö ü Ä Ö Ü ß, „“ –) on an NFLib 8x8 text layer.
void TextDE_Write(int screen, u32 layer, u32 x, u32 y, const char *utf8);

// Decodes the next UTF-8 codepoint and advances the pointer.
u32 TextDE_NextCodepoint(const char *&utf8);

// Tile index of a codepoint in the patched 8x8 font (fnt/default.fnt).
u32 TextDE_FontSlot(u32 codepoint);

// "A in a circle" badge, drawn into an empty font slot by
// assets/fonts/make_font_texture.py. Only exists in the 3D font atlas.
constexpr u32 TextDE_SlotButtonA = 127;
