#pragma once

#include "math/Vec2.h"

class AssetService;
class RenderService;

// Soft blob shadows on the ground, stretched away from the sun. Their length
// follows the time of day (long in the evening, gone at night). All shadows
// share one polygon ID, so overlapping shadows don't get darker.
class ShadowCaster
{
public:
    explicit ShadowCaster(const AssetService &assets) : assets_(assets) {}

    // radius: footprint of the object, height: how tall it is.
    void Draw(const RenderService &render, Vec2 position, Fixed radius, Fixed height) const;

private:
    const AssetService &assets_;
};
