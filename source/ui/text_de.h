#pragma once

#include <nds/ndstypes.h>

// Writes UTF-8 German text (ä ö ü Ä Ö Ü ß, „“ –) on an NFLib 8x8 text layer.
void TextDE_Write(int screen, u32 layer, u32 x, u32 y, const char *utf8);
