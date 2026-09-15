#pragma once

#include <nds/ndstypes.h>

#include "math/Fixed.h"

// Small deterministic xorshift generator (same forest layout on every boot).
class Random
{
public:
    explicit constexpr Random(u32 seed) : state_(seed != 0 ? seed : 0x9E3779B9) {}

    constexpr u32 Next()
    {
        state_ ^= state_ << 13;
        state_ ^= state_ >> 17;
        state_ ^= state_ << 5;
        return state_;
    }

    // Uniform integer in [lo, hi].
    constexpr s32 Range(s32 lo, s32 hi)
    {
        return lo + static_cast<s32>(Next() % static_cast<u32>(hi - lo + 1));
    }

    // Uniform fixed point value in [lo, hi].
    constexpr Fixed Range(Fixed lo, Fixed hi) { return Fixed::FromRaw(Range(lo.Raw(), hi.Raw())); }

    // True with the given chance in percent.
    constexpr bool Chance(u32 percent) { return Next() % 100 < percent; }

private:
    u32 state_;
};
