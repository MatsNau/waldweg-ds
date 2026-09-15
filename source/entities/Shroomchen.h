#pragma once

#include "math/Angle.h"
#include "math/Vec2.h"

class AssetService;
class RenderService;

// Shroomchen, the forest god: a spotted cow that can grow into a giant,
// glowing deity with a flower wreath. Legs swing while walking.
class Shroomchen
{
public:
    explicit Shroomchen(const AssetService &assets) : assets_(assets) {}

    void Place(Vec2 position, Angle facing);
    void Move(Vec2 position) { position_ = position; }
    // Walks straight towards target; returns true when it has arrived.
    bool WalkTowards(Vec2 target, Fixed speed);
    void TurnTowards(Angle facing, s32 maxStep) { facing_ = facing_.TurnedTowards(facing, maxStep); }
    void Stand();

    void SetScale(Fixed scale) { scale_ = scale; }
    void SetDeity(bool deity) { deity_ = deity; }
    // Lying down in the grass (legs tucked away) and wearing the wreath.
    void SetLying(bool lying) { lying_ = lying; }
    void SetWreath(bool wreath) { wreath_ = wreath; }
    void SetVisible(bool visible) { visible_ = visible; }

    Vec2 Position() const { return position_; }
    Angle Facing() const { return facing_; }
    Fixed Scale() const { return scale_; }
    bool IsVisible() const { return visible_; }

    // Where riders sit: position on the ground plane and height of the back.
    Vec2 SeatPosition(Fixed forwardOffset) const;
    Fixed SeatHeight() const;

    void Draw(const RenderService &render) const;

private:
    void Animate(Fixed distanceMoved);

    const AssetService &assets_;
    Vec2 position_;
    Angle facing_;
    Fixed scale_ = 1_fx;
    bool deity_ = false;
    bool visible_ = false;
    bool lying_ = false;
    bool wreath_ = false;

    Angle stepPhase_;
    Fixed walkBlend_;
};
