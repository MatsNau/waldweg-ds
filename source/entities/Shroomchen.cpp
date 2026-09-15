#include "entities/Shroomchen.h"

#include "render/AssetService.h"
#include "render/RenderService.h"

namespace {

// Keep in sync with assets/blender/models_cow.py (Blender y -> game -z).
constexpr Fixed kHipY = 0.4_fx;
constexpr Fixed kLegX = 0.2_fx;
constexpr Fixed kLegZ = 0.3_fx;
constexpr Fixed kBackY = 0.98_fx;

constexpr Fixed kStrideLength = 0.9_fx;
constexpr s32 kLegSwing = Angle::kFullTurn * 28 / 360;
constexpr Fixed kMovingThreshold = 0.002_fx;
constexpr Fixed kLyingDrop = 0.3_fx;

enum Part : u32
{
    kPartBody,
    kPartLegs,
    kPartCrown,
};

} // namespace

void Shroomchen::Place(Vec2 position, Angle facing)
{
    position_ = position;
    facing_ = facing;
    walkBlend_ = 0_fx;
}

bool Shroomchen::WalkTowards(Vec2 target, Fixed speed)
{
    Vec2 delta = target - position_;
    Fixed distance = delta.Length();
    if (distance <= speed)
    {
        position_ = target;
        Animate(distance);
        return true;
    }

    Vec2 step = delta * (speed / distance);
    position_ += step;
    facing_ = facing_.TurnedTowards(Angle::FromDirection(delta), 900);
    Animate(speed);
    return false;
}

void Shroomchen::Stand()
{
    Animate(0_fx);
}

void Shroomchen::Animate(Fixed distanceMoved)
{
    bool moving = distanceMoved > kMovingThreshold;
    walkBlend_ = fx::Approach(walkBlend_, moving ? 1_fx : 0_fx, 0.1_fx);
    // Stride grows with the size, so a giant takes slow, big steps.
    Fixed stride = kStrideLength * scale_;
    s32 phaseStep = (distanceMoved / stride).Raw() * Angle::kFullTurn / Fixed::kOne;
    stepPhase_ = stepPhase_ + Angle::FromBinary(phaseStep);
}

Vec2 Shroomchen::SeatPosition(Fixed forwardOffset) const
{
    Fixed offset = forwardOffset * scale_;
    return position_ + Vec2{ facing_.Sin() * offset, facing_.Cos() * offset };
}

Fixed Shroomchen::SeatHeight() const
{
    return kBackY * scale_;
}

void Shroomchen::Draw(const RenderService &render) const
{
    if (!visible_)
        return;

    // As a god Shroomchen glows: unlit polygons need the emissive material,
    // otherwise they would render black.
    Lighting lighting = deity_ ? Lighting::Glow : Lighting::Lit;
    NE_Material *material = deity_ ? assets_.GlowMaterial() : assets_.PaletteMaterial();
    Fixed swing = stepPhase_.Sin() * walkBlend_;
    s32 legSwing = (swing * kLegSwing).ToInt();

    render.LightObject(position_);
    NE_ViewPush();
    NE_ViewMoveI(position_.x.Raw(), lying_ ? -(kLyingDrop * scale_).Raw() : 0, position_.z.Raw());
    NE_ViewRotate(0, facing_.ToNitro(), 0);
    NE_ViewScaleI(scale_.Raw(), scale_.Raw(), scale_.Raw());

    NE_Model *body = assets_.Model(ModelId::CowBody);
    NE_ModelSetMaterial(body, material);
    NE_ModelSetCoordI(body, 0, 0, 0);
    NE_ModelSetRot(body, 0, 0, 0);
    render.BeginPolygons(PolyGroup::Shroomchen, kPartBody, lighting);
    NE_ModelDraw(body);

    // Diagonal legs move together, like a walking cow.
    NE_Model *leg = assets_.Model(ModelId::CowLeg);
    NE_ModelSetMaterial(leg, material);
    render.BeginPolygons(PolyGroup::Shroomchen, kPartLegs, lighting);
    for (int front = 0; front < (lying_ ? 0 : 2); front++)
    {
        for (int side = 0; side < 2; side++)
        {
            Fixed x = side == 0 ? kLegX : -kLegX;
            Fixed z = front == 0 ? kLegZ : -kLegZ;
            s32 angle = (front == side) ? legSwing : -legSwing;
            NE_ModelSetCoordI(leg, x.Raw(), kHipY.Raw(), z.Raw());
            NE_ModelSetRot(leg, NitroRotation(angle), 0, 0);
            NE_ModelDraw(leg);
        }
    }

    if (deity_ || wreath_)
    {
        NE_Model *crown = assets_.Model(ModelId::CowCrown);
        NE_ModelSetMaterial(crown, material);
        NE_ModelSetCoordI(crown, 0, 0, 0);
        NE_ModelSetRot(crown, 0, 0, 0);
        render.BeginPolygons(PolyGroup::Shroomchen, kPartCrown, lighting);
        NE_ModelDraw(crown);
    }

    NE_ViewPop();
}
