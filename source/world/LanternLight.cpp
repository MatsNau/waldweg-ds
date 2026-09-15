#include "world/LanternLight.h"

#include "render/AssetService.h"

namespace {

constexpr Fixed kRadius = 5.2_fx;
constexpr Fixed kFlickerRadius = 0.25_fx;
constexpr s32 kFlickerSpeed = 1100; // binary angle units per frame
constexpr u32 kColor = RGB15(31, 24, 12);
constexpr u32 kPoolAlpha = 12;
// High enough above the flat ground to avoid depth fighting at a distance.
constexpr Fixed kPoolHeight = 0.12_fx;

} // namespace

void LanternLight::Update(Vec2 carrier)
{
    // Two overlapping waves give an irregular, candle-like flicker.
    flicker_ = flicker_ + Angle::FromBinary(kFlickerSpeed);
    Fixed wobble = (flicker_.Sin() + Angle::FromBinary(flicker_.Binary() * 3).Sin() / 2) / 2;

    light_.position = carrier;
    light_.radius = kRadius + wobble * kFlickerRadius;
    light_.color = kColor;
}

void LanternLight::Apply(RenderService &render) const
{
    render.SetPointLight(enabled_ ? &light_ : nullptr);
}

void LanternLight::DrawPool(const RenderService &render) const
{
    if (!enabled_)
        return;

    NE_Model *pool = assets_.Model(ModelId::LightDisc);
    NE_ModelSetCoordI(pool, light_.position.x.Raw(), kPoolHeight.Raw(), light_.position.z.Raw());
    Fixed scale = light_.radius / kRadius;
    NE_ModelScaleI(pool, scale.Raw(), Fixed::kOne, scale.Raw());
    render.BeginTranslucent(PolyGroup::Effects, 0, kPoolAlpha);
    NE_ModelDraw(pool);
}
