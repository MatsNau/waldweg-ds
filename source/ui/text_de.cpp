#include "ui/text_de.h"

#include <nf_lib.h>

namespace {

// NF_WriteText() only maps a few Latin-1 bytes (Spanish characters) to font
// slots 96-113. The German glyphs are drawn into the slots of those characters
// by assets/fonts/patch_umlauts.py, so the mapping here must match that script.
char MapCodepoint(u32 cp)
{
    switch (cp)
    {
        case 0xE4: return static_cast<char>(225); // ä -> slot of á (105)
        case 0xF6: return static_cast<char>(243); // ö -> slot of ó (108)
        case 0xFC: return static_cast<char>(252); // ü -> native slot (111)
        case 0xC4: return static_cast<char>(193); // Ä -> slot of Á (100)
        case 0xD6: return static_cast<char>(211); // Ö -> slot of Ó (103)
        case 0xDC: return static_cast<char>(218); // Ü -> slot of Ú (104)
        case 0xDF: return static_cast<char>(239); // ß -> slot of ï (110)
        case 0x201C:
        case 0x201D:
        case 0x201E: return '"';
        case 0x2018:
        case 0x2019: return '\'';
        case 0x2013:
        case 0x2014: return '-';
        case '\n': return '\n';
        default:
            return (cp >= 32 && cp < 127) ? static_cast<char>(cp) : '?';
    }
}

} // namespace

u32 TextDE_NextCodepoint(const char *&utf8)
{
    const unsigned char *p = reinterpret_cast<const unsigned char *>(utf8);
    u32 cp;
    if (p[0] < 0x80)
    {
        cp = p[0];
        p += 1;
    }
    else if ((p[0] & 0xE0) == 0xC0 && p[1] != 0)
    {
        cp = ((p[0] & 0x1F) << 6) | (p[1] & 0x3F);
        p += 2;
    }
    else if ((p[0] & 0xF0) == 0xE0 && p[1] != 0 && p[2] != 0)
    {
        cp = ((p[0] & 0x0F) << 12) | ((p[1] & 0x3F) << 6) | (p[2] & 0x3F);
        p += 3;
    }
    else
    {
        cp = '?';
        p += 1;
    }
    utf8 = reinterpret_cast<const char *>(p);
    return cp;
}

u32 TextDE_FontSlot(u32 codepoint)
{
    unsigned char c = static_cast<unsigned char>(MapCodepoint(codepoint));
    switch (c)
    {
        case 225: return 105; // ä
        case 243: return 108; // ö
        case 252: return 111; // ü
        case 193: return 100; // Ä
        case 211: return 103; // Ö
        case 218: return 104; // Ü
        case 239: return 110; // ß
        default:
            return (c >= 32 && c < 128) ? c - 32u : '?' - 32u;
    }
}

void TextDE_Write(int screen, u32 layer, u32 x, u32 y, const char *utf8)
{
    char buffer[256];
    u32 out = 0;

    while (*utf8 != 0 && out < sizeof(buffer) - 1)
        buffer[out++] = MapCodepoint(TextDE_NextCodepoint(utf8));

    buffer[out] = '\0';
    NF_WriteText(screen, layer, x, y, buffer);
}
