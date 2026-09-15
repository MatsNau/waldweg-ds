#pragma once

#include "math/Angle.h"
#include "render/RenderService.h"

class AssetService;

// Mats' lantern: a flickering warm point light and a translucent pool of light
// on the ground around him.
class LanternLight
{
public:
    explicit LanternLight(const AssetService &assets) : assets_(assets) {}

    void SetEnabled(bool enabled) { enabled_ = enabled; }
    bool IsEnabled() const { return enabled_; }

    void Update(Vec2 carrier);
    // Registers (or removes) the point light for this frame's objects.
    void Apply(RenderService &render) const;
    void DrawPool(const RenderService &render) const;

private:
    const AssetService &assets_;
    bool enabled_ = false;
    PointLight light_ = {};
    Angle flicker_;
};
