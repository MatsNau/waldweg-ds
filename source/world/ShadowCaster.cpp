#include "world/ShadowCaster.h"

#include "math/Angle.h"
#include "render/AssetService.h"
#include "render/RenderService.h"

namespace {

constexpr Fixed kGroundOffset = 0.06_fx;

} // namespace

void ShadowCaster::Draw(const RenderService &render, Vec2 position, Fixed radius, Fixed height) const
{
    u32 alpha = render.ShadowAlpha();
    Fixed length = height * render.ShadowLength();
    if (alpha == 0 || length <= 0_fx)
        return;

    Vec2 direction = render.SunDirection();
    Vec2 centre = position + direction * (length / 2);
    Fixed along = fx::Max(length / 2 + radius / 2, radius);

    NE_Model *model = assets_.Model(ModelId::Shadow);
    NE_ModelSetCoordI(model, centre.x.Raw(), kGroundOffset.Raw(), centre.z.Raw());
    NE_ModelSetRot(model, 0, Angle::FromDirection(direction).ToNitro(), 0);
    NE_ModelScaleI(model, radius.Raw(), Fixed::kOne, along.Raw());
    render.BeginTranslucent(PolyGroup::Effects, 2, alpha);
    NE_ModelDraw(model);
}
