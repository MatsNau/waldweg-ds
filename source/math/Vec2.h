#pragma once

#include "math/Fixed.h"

// Position or direction on the ground plane (x = right, z = towards the camera).
struct Vec2
{
    Fixed x;
    Fixed z;

    constexpr Vec2 operator+(Vec2 o) const { return { x + o.x, z + o.z }; }
    constexpr Vec2 operator-(Vec2 o) const { return { x - o.x, z - o.z }; }
    constexpr Vec2 operator*(Fixed k) const { return { x * k, z * k }; }
    constexpr Vec2 &operator+=(Vec2 o) { x += o.x; z += o.z; return *this; }
    constexpr Vec2 &operator-=(Vec2 o) { x -= o.x; z -= o.z; return *this; }

    constexpr bool IsZero() const { return x == Fixed() && z == Fixed(); }
    constexpr Fixed LengthSq() const { return x * x + z * z; }
    Fixed Length() const { return fx::Sqrt(LengthSq()); }

    Vec2 Normalized() const
    {
        Fixed length = Length();
        if (length == Fixed())
            return {};
        return { x / length, z / length };
    }
};
