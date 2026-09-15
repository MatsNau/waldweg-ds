#include "world/LeafParticles.h"

#include "render/AssetService.h"
#include "render/RenderService.h"

namespace {

constexpr ModelId kLeafModels[] = { ModelId::LeafA, ModelId::LeafB, ModelId::LeafC };
constexpr s32 kSwaySpeed = 500;
constexpr Fixed kSwayAmount = 0.02_fx;

} // namespace

void LeafParticles::Clear()
{
    for (Leaf &leaf : leaves_)
        leaf.alive = false;
}

void LeafParticles::Update(const Area &area, int spawnChance)
{
    if (static_cast<int>(random_.Next() % 1000) < spawnChance)
    {
        for (Leaf &leaf : leaves_)
        {
            if (leaf.alive)
                continue;
            leaf.alive = true;
            leaf.x = area.centre.x + random_.Range(-area.halfWidth, area.halfWidth);
            leaf.z = area.centre.z + random_.Range(area.depthMin, area.depthMax);
            leaf.y = area.height + random_.Range(0_fx, 0.8_fx);
            leaf.fallSpeed = random_.Range(0.008_fx, 0.016_fx);
            leaf.drift = random_.Range(0.004_fx, 0.014_fx); // light wind to the right
            leaf.sway = Angle::FromBinary(random_.Range(0, Angle::kFullTurn - 1));
            leaf.spinSpeedX = random_.Range(200, 900);
            leaf.spinSpeedY = random_.Range(-700, 700);
            leaf.kind = static_cast<u8>(random_.Range(0, 2));
            break;
        }
    }

    for (Leaf &leaf : leaves_)
    {
        if (!leaf.alive)
            continue;
        leaf.sway = leaf.sway + Angle::FromBinary(kSwaySpeed);
        leaf.y -= leaf.fallSpeed;
        leaf.x += leaf.drift + leaf.sway.Sin() * kSwayAmount;
        leaf.spinX = leaf.spinX + Angle::FromBinary(leaf.spinSpeedX);
        leaf.spinY = leaf.spinY + Angle::FromBinary(leaf.spinSpeedY);
        if (leaf.y < 0.02_fx)
            leaf.alive = false;
    }
}

void LeafParticles::Draw(const RenderService &render) const
{
    render.ClearObjectLight();
    for (int i = 0; i < kMaxLeaves; i++)
    {
        const Leaf &leaf = leaves_[i];
        if (!leaf.alive)
            continue;
        NE_Model *model = assets_.Model(kLeafModels[leaf.kind]);
        NE_ModelSetCoordI(model, leaf.x.Raw(), leaf.y.Raw(), leaf.z.Raw());
        NE_ModelSetRot(model, leaf.spinX.ToNitro(), leaf.spinY.ToNitro(), 0);
        render.BeginPolygons(PolyGroup::Effects, 3 + static_cast<u32>(i % 3), Lighting::LitTwoSided);
        NE_ModelDraw(model);
    }
}
