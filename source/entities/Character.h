#pragma once

#include "entities/CharacterRig.h"
#include "math/Angle.h"
#include "math/Vec2.h"

class Forest;
class RenderService;

// Something that walks around the forest: position, facing, collision, rig.
class Character
{
public:
    static constexpr Fixed kRadius = 0.2_fx;

    Character(const AssetService &assets, const CharacterLook &look) : rig_(assets, look) {}

    void Place(Vec2 position, Angle facing);
    // Height above the ground (riding on Shroomchen's back).
    void SetElevation(Fixed elevation) { elevation_ = elevation; }
    Fixed Elevation() const { return elevation_; }
    void SetSitting(bool sitting) { rig_.SetSitting(sitting); }
    // Idle animation only, for frames without walking (cutscenes).
    void Idle() { Stand(); }

    Vec2 Position() const { return position_; }
    Angle Facing() const { return facing_; }

    void Draw(const RenderService &render) const;

protected:
    CharacterRig &Rig() { return rig_; }

    // Call exactly one of these per frame.
    void Walk(Vec2 delta, const Forest &forest);
    void Stand();

private:
    // Binary angle units per frame (about 20 degrees).
    static constexpr s32 kTurnSpeed = 1800;

    CharacterRig rig_;
    Vec2 position_;
    Angle facing_;
    Fixed elevation_;
};
