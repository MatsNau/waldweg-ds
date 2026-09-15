#pragma once

#include <nds/ndstypes.h>

enum class TextColor : u32
{
    Default = 0,
    Ink = 1,     // dark brown on parchment
    Speaker = 2, // reddish brown for names
    Good = 3,    // dark green (edible)
    Danger = 4,  // red (poisonous)
};

// A grid of 8x8 characters that can show German UTF-8 text.
// Implemented by TextService (bottom screen) and TopTextService (top screen).
class TextSurface
{
public:
    static constexpr int kColumns = 32;
    static constexpr int kRows = 24;

    virtual ~TextSurface() = default;

    virtual void Clear() = 0;
    virtual void SetColor(TextColor color) = 0;
    virtual void Write(int column, int row, const char *utf8) = 0;
    // Makes changes visible (if the surface buffers them).
    virtual void Present() {}

    void Format(int column, int row, const char *format, ...) __attribute__((format(printf, 4, 5)));
    // Word-wraps UTF-8 text into a box; returns the number of rows used.
    int WriteWrapped(int column, int row, int width, int maxRows, const char *utf8);
};
