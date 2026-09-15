#pragma once

#include "core/Services.h"

class Forest;
class Mats;
class MushroomField;
class Nina;

// Developer overlay in the parchment panel (polygons, positions, day phase).
// Only available in debug builds (WALDWEG_DEBUG), toggled with START.
class DebugHud
{
public:
    explicit DebugHud(Services &services) : services_(services) {}

    void Toggle() { visible_ = !visible_; }
    bool IsVisible() const { return visible_; }
    void RequestRefresh() { refreshCountdown_ = 0; }

    // Redraws every few frames; returns true if text changed.
    bool Draw(const Nina &nina, const Mats &mats, const Forest &forest, const MushroomField &mushrooms);

private:
    static constexpr int kRefreshFrames = 10;

    Services &services_;
    bool visible_ = false;
    int refreshCountdown_ = 0;
};
