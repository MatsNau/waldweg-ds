#pragma once

#include "ui/TextSurface.h"

// Text on the bottom screen (NFLib text layer over the map, used by the debug HUD).
class TextService : public TextSurface
{
public:
    // Requires SubScreenService::Init.
    void Init();

    void Clear() override;
    void SetColor(TextColor color) override;
    void Write(int column, int row, const char *utf8) override;
    // Uploads changed text to the screen.
    void Present() override;
};
