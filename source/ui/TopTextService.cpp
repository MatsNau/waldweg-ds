#include "ui/TopTextService.h"

#include <nds.h>

#include "core/Fatal.h"
#include "render/RenderService.h"
#include "ui/text_de.h"

namespace {

constexpr const char *kFontPath = "textures/font.grf";
constexpr int kGlyphSize = 8;
constexpr int kAtlasColumns = 16;

// Polygon ID shared by panel and glyphs: outlines only around the panel.
constexpr u32 kPolygonId = 62;

// Depth in the 2D projection: negative is closer to the viewer.
constexpr s16 kDepthFrame = -3000;
constexpr s16 kDepthPanel = -3300;
constexpr s16 kDepthText = -3600;

constexpr u32 kColorFrame = RGB15(15, 10, 6);
constexpr u32 kColorPanel = RGB15(29, 26, 21);

u32 ColorValue(TextColor color)
{
    switch (color)
    {
        case TextColor::Speaker: return RGB15(17, 5, 3);
        default: return RGB15(7, 4, 2);
    }
}

} // namespace

void TopTextService::Init()
{
    font_ = NE_MaterialCreate();
    if (NE_MaterialTexLoadGRF(font_, nullptr, NE_TEXGEN_TEXCOORD, kFontPath) == 0)
        Fatal("Textur fehlt:\n%s", kFontPath);
    Clear();
}

void TopTextService::Clear()
{
    cells_.fill({ 0, TextColor::Ink });
}

void TopTextService::Write(int column, int row, const char *utf8)
{
    if (row < kTextRow || row >= kTextRow + kTextRows)
        return;

    while (*utf8 != '\0' && column < kTextColumn + kTextColumns)
    {
        u32 cp = TextDE_NextCodepoint(utf8);
        if (column >= kTextColumn)
        {
            Cell &cell = cells_[(row - kTextRow) * kTextColumns + (column - kTextColumn)];
            cell.slot = static_cast<u8>(TextDE_FontSlot(cp));
            cell.color = color_;
        }
        column++;
    }
}

void TopTextService::Draw() const
{
    if (!visible_)
        return;

    NE_2DViewInit();
    NE_PolyFormat(31, kPolygonId, static_cast<NE_LightEnum>(0), NE_CULL_NONE,
                  static_cast<NE_OtherFormatEnum>(0));

    s16 top = kPanelTop * kGlyphSize;
    s16 bottom = static_cast<s16>((kPanelTop + kPanelRows) * kGlyphSize);
    NE_2DDrawQuad(2, top + 2, 254, bottom - 2, kDepthFrame, kColorFrame);
    NE_2DDrawQuad(4, top + 4, 252, bottom - 4, kDepthPanel, kColorPanel);

    for (int row = 0; row < kTextRows; row++)
    {
        for (int column = 0; column < kTextColumns; column++)
        {
            const Cell &cell = cells_[row * kTextColumns + column];
            if (cell.slot == 0)
                continue;

            RenderService::Draw2DImage(font_, (kTextColumn + column) * kGlyphSize,
                                       (kTextRow + row) * kGlyphSize, kGlyphSize, kGlyphSize,
                                       (cell.slot % kAtlasColumns) * kGlyphSize,
                                       (cell.slot / kAtlasColumns) * kGlyphSize,
                                       kGlyphSize, kGlyphSize, kDepthText, ColorValue(cell.color));
        }
    }
}
