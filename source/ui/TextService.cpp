#include "ui/TextService.h"

#include <nds.h>
#include <nf_lib.h>

#include "ui/UiLayout.h"
#include "ui/text_de.h"

namespace {

using ui::kLayerText;
using ui::kSubScreen;

} // namespace

void TextService::Init()
{
    // Width/height are the size of the text layer (multiples of 256);
    // NFLib reads the first 127 glyphs of the font file.
    NF_LoadTextFont("fnt/default", "normal", 256, 256, 0);
    NF_CreateTextLayer(kSubScreen, kLayerText, 0, "normal");

    NF_DefineTextColor(kSubScreen, kLayerText, static_cast<u32>(TextColor::Ink), 7, 4, 2);
    NF_DefineTextColor(kSubScreen, kLayerText, static_cast<u32>(TextColor::Speaker), 17, 5, 3);
    NF_DefineTextColor(kSubScreen, kLayerText, static_cast<u32>(TextColor::Good), 4, 12, 4);
    NF_DefineTextColor(kSubScreen, kLayerText, static_cast<u32>(TextColor::Danger), 22, 3, 2);
}

void TextService::Clear()
{
    NF_ClearTextLayer(kSubScreen, kLayerText);
}

void TextService::SetColor(TextColor color)
{
    NF_SetTextColor(kSubScreen, kLayerText, static_cast<u32>(color));
}

void TextService::Write(int column, int row, const char *utf8)
{
    TextDE_Write(kSubScreen, kLayerText, column, row, utf8);
}

void TextService::Present()
{
    NF_UpdateTextLayers();
}
