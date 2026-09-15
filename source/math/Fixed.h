#pragma once

#include <nds/arm9/math.h>
#include <nds/ndstypes.h>

// 20.12 fixed point number: the native format of libnds, Nitro Engine and the
// DS math coprocessor. Use the _fx literal for constants (folded at compile time).
class Fixed
{
public:
    static constexpr int kShift = 12;
    static constexpr s32 kOne = 1 << kShift;

    constexpr Fixed() = default;

    static constexpr Fixed FromRaw(s32 raw)
    {
        Fixed f;
        f.raw_ = raw;
        return f;
    }
    static constexpr Fixed FromInt(s32 value) { return FromRaw(value * kOne); }
    // Only meant for constants; at runtime this would pull in soft-float code.
    static constexpr Fixed FromFloat(double value)
    {
        return FromRaw(static_cast<s32>(value * kOne + (value < 0 ? -0.5 : 0.5)));
    }

    constexpr s32 Raw() const { return raw_; }
    constexpr s32 ToInt() const { return raw_ >> kShift; }

    constexpr Fixed operator-() const { return FromRaw(-raw_); }
    constexpr Fixed operator+(Fixed o) const { return FromRaw(raw_ + o.raw_); }
    constexpr Fixed operator-(Fixed o) const { return FromRaw(raw_ - o.raw_); }
    constexpr Fixed operator*(Fixed o) const
    {
        return FromRaw(static_cast<s32>((static_cast<s64>(raw_) * o.raw_) >> kShift));
    }
    Fixed operator/(Fixed o) const { return FromRaw(divf32(raw_, o.raw_)); }
    constexpr Fixed operator*(s32 k) const { return FromRaw(raw_ * k); }
    constexpr Fixed operator/(s32 k) const { return FromRaw(raw_ / k); }

    constexpr Fixed &operator+=(Fixed o) { raw_ += o.raw_; return *this; }
    constexpr Fixed &operator-=(Fixed o) { raw_ -= o.raw_; return *this; }
    constexpr Fixed &operator*=(Fixed o) { return *this = *this * o; }

    constexpr bool operator==(Fixed o) const { return raw_ == o.raw_; }
    constexpr bool operator!=(Fixed o) const { return raw_ != o.raw_; }
    constexpr bool operator<(Fixed o) const { return raw_ < o.raw_; }
    constexpr bool operator<=(Fixed o) const { return raw_ <= o.raw_; }
    constexpr bool operator>(Fixed o) const { return raw_ > o.raw_; }
    constexpr bool operator>=(Fixed o) const { return raw_ >= o.raw_; }

private:
    s32 raw_ = 0;
};

constexpr Fixed operator""_fx(long double value)
{
    return Fixed::FromFloat(static_cast<double>(value));
}

constexpr Fixed operator""_fx(unsigned long long value)
{
    return Fixed::FromInt(static_cast<s32>(value));
}

namespace fx {

constexpr Fixed Abs(Fixed v) { return v < Fixed() ? -v : v; }
constexpr Fixed Min(Fixed a, Fixed b) { return a < b ? a : b; }
constexpr Fixed Max(Fixed a, Fixed b) { return a > b ? a : b; }
constexpr Fixed Clamp(Fixed v, Fixed lo, Fixed hi) { return Min(Max(v, lo), hi); }

// Moves value towards target by at most step.
constexpr Fixed Approach(Fixed value, Fixed target, Fixed step)
{
    if (value < target)
        return Min(value + step, target);
    return Max(value - step, target);
}

inline Fixed Sqrt(Fixed v)
{
    if (v <= Fixed())
        return Fixed();
    return Fixed::FromRaw(static_cast<s32>(sqrtf32(static_cast<u32>(v.Raw()))));
}

} // namespace fx
