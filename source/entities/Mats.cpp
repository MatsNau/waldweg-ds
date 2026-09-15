#include "entities/Mats.h"

#include "entities/Nina.h"

namespace {

constexpr CharacterLook kMatsLook = {
    ModelId::MatsHead, ModelId::MatsBody, ModelId::MatsArm, ModelId::MatsLeg,
    PolyGroup::Mats, 1.06_fx,
};

constexpr Fixed kStopDistance = 1.0_fx;
constexpr Fixed kCatchUpDistance = 2.6_fx;
constexpr Fixed kNormalSpeed = Nina::kWalkSpeed * 0.92_fx;
constexpr Fixed kCatchUpSpeed = Nina::kWalkSpeed * 1.2_fx;
constexpr Fixed kAcceleration = 0.005_fx;

constexpr Fixed kCrumbSpacing = 0.3_fx;
constexpr Fixed kCrumbReached = 0.25_fx;

} // namespace

Mats::Mats(const AssetService &assets) : Character(assets, kMatsLook)
{
}

void Mats::Place(Vec2 position, Angle facing)
{
    Character::Place(position, facing);
    ClearTrail();
    speed_ = 0_fx;
}

void Mats::ShowItem(ItemId item)
{
    switch (item)
    {
        case ItemId::Basket:
            Rig().SetHandItem(Hand::Right, ModelId::Basket);
            break;
        case ItemId::Scarf:
            Rig().SetNeckItem(ModelId::Scarf);
            break;
        case ItemId::Lantern:
            Rig().SetHandItem(Hand::Left, ModelId::Lantern);
            break;
        case ItemId::Bell:
            Rig().SetHandItem(Hand::Right, ModelId::Bell);
            break;
        case ItemId::Count:
            break;
    }
}

void Mats::ClearItems()
{
    Rig().SetHandItem(Hand::Left, CharacterRig::kNothing);
    Rig().SetHandItem(Hand::Right, CharacterRig::kNothing);
    Rig().SetNeckItem(CharacterRig::kNothing);
}

void Mats::Update(const Nina &nina, const Forest &forest)
{
    Vec2 ninaPosition = nina.Position();
    RecordTrail(ninaPosition);

    distanceToNina_ = (ninaPosition - Position()).Length();

    Fixed desiredSpeed = 0_fx;
    if (distanceToNina_ > kCatchUpDistance)
        desiredSpeed = kCatchUpSpeed;
    else if (distanceToNina_ > kStopDistance)
        desiredSpeed = kNormalSpeed;
    speed_ = fx::Approach(speed_, desiredSpeed, kAcceleration);

    if (speed_ == 0_fx)
    {
        // Close to Nina: forget the old path, a new one starts where she walks next.
        ClearTrail();
        Stand();
        return;
    }

    Vec2 toTarget = NextTarget(ninaPosition) - Position();
    Fixed step = fx::Min(speed_, toTarget.Length());
    Walk(toTarget.Normalized() * step, forest);
}

void Mats::RecordTrail(Vec2 ninaPosition)
{
    if (trailCount_ > 0)
    {
        const Vec2 &newest = trail_[(trailHead_ + trailCount_ - 1) % kTrailSize];
        if ((ninaPosition - newest).LengthSq() < kCrumbSpacing * kCrumbSpacing)
            return;
    }

    if (trailCount_ == kTrailSize)
    {
        trailHead_ = (trailHead_ + 1) % kTrailSize;
        trailCount_--;
    }
    trail_[(trailHead_ + trailCount_) % kTrailSize] = ninaPosition;
    trailCount_++;
}

Vec2 Mats::NextTarget(Vec2 ninaPosition)
{
    while (trailCount_ > 0)
    {
        const Vec2 &oldest = trail_[trailHead_];
        if ((oldest - Position()).LengthSq() > kCrumbReached * kCrumbReached)
            return oldest;
        trailHead_ = (trailHead_ + 1) % kTrailSize;
        trailCount_--;
    }
    return ninaPosition;
}
