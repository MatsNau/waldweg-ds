#pragma once

#include <array>

#include <NEMain.h>

#include "ui/TextSurface.h"

// Dialog text on the top screen. Drawn with Nitro Engine as 2D quads at the
// end of the 3D frame: a parchment panel plus one textured quad per glyph
// (font atlas textures/font.grf, colour via vertex colour).
class TopTextService : public TextSurface
{
public:
    // Panel area in characters (includes the border).
    static constexpr int kPanelTop = 0;
    static constexpr int kPanelRows = 7;
    // Writable text area inside the border.
    static constexpr int kTextColumn = 1;
    static constexpr int kTextRow = kPanelTop + 1;
    static constexpr int kTextColumns = kColumns - 2;
    static constexpr int kTextRows = kPanelRows - 2;

    // Requires RenderService::Init (loads the font texture).
    void Init();

    void ShowPanel(bool show) { visible_ = show; }
    // Small "A" badge at the lower right corner: this message can be skipped.
    void ShowSkipHint(bool show) { skipHint_ = show; }

    // Clears the text inside the panel.
    void Clear() override;
    void SetColor(TextColor color) override { color_ = color; }
    void Write(int column, int row, const char *utf8) override;

    // Call at the very end of a 3D frame (switches to a 2D projection).
    void Draw() const;

private:
    struct Cell
    {
        u8 slot; // font slot, 0 = space
        TextColor color;
    };

    std::array<Cell, kTextColumns * kTextRows> cells_ = {};
    NE_Material *font_ = nullptr;
    TextColor color_ = TextColor::Ink;
    bool visible_ = false;
    bool skipHint_ = false;
};
