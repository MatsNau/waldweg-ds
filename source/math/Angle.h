#pragma once

#include <nds/arm9/math.h>
#include <nds/arm9/trig_lut.h>

#include "math/Vec2.h"

// Binary angle, 32768 units per full turn (libnds convention).
// Angle 0 looks along +Z (towards the camera); positive angles turn towards +X.
class Angle
{
public:
    static constexpr s32 kFullTurn = DEGREES_IN_CIRCLE;

    constexpr Angle() = default;

    static constexpr Angle FromBinary(s32 value)
    {
        Angle a;
        a.value_ = value & (kFullTurn - 1);
        return a;
    }
    static constexpr Angle FromDegrees(s32 degrees) { return FromBinary(degrees * kFullTurn / 360); }

    // Direction of a ground-plane vector (must not be zero).
    static Angle FromDirection(Vec2 dir)
    {
        // atan2_f32 returns 4.12 radians; 5215 = 32768 / (2 * pi).
        s32 radians = atan2_f32(dir.x.Raw(), dir.z.Raw());
        return FromBinary((radians * 5215) >> Fixed::kShift);
    }

    constexpr s32 Binary() const { return value_; }
    // Nitro Engine uses 512 units per turn.
    constexpr int ToNitro() const { return value_ >> 6; }

    Fixed Sin() const { return Fixed::FromRaw(sinLerp(static_cast<s16>(value_))); }
    Fixed Cos() const { return Fixed::FromRaw(cosLerp(static_cast<s16>(value_))); }

    constexpr Angle operator+(Angle o) const { return FromBinary(value_ + o.value_); }

    // Signed difference in (-half turn, half turn].
    constexpr s32 DeltaTo(Angle target) const
    {
        s32 delta = (target.value_ - value_) & (kFullTurn - 1);
        return delta > kFullTurn / 2 ? delta - kFullTurn : delta;
    }

    constexpr Angle TurnedTowards(Angle target, s32 maxStep) const
    {
        s32 delta = DeltaTo(target);
        if (delta > maxStep)
            delta = maxStep;
        else if (delta < -maxStep)
            delta = -maxStep;
        return FromBinary(value_ + delta);
    }

private:
    s32 value_ = 0;
};

// Nitro Engine rotation (0-511) for a signed binary angle offset, e.g. limb swing.
constexpr int NitroRotation(s32 binary)
{
    return (binary >> 6) & 511;
}
