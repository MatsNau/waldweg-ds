#include "core/InputService.h"

namespace {

constexpr u32 kUpKeys = KEY_UP | KEY_X;
constexpr u32 kDownKeys = KEY_DOWN | KEY_B;
constexpr u32 kLeftKeys = KEY_LEFT | KEY_Y;
constexpr u32 kRightKeys = KEY_RIGHT | KEY_A;

constexpr Fixed kDiagonal = 0.70710678_fx;

} // namespace

void InputService::Update()
{
    scanKeys();
    held_ = keysHeld();
    pressed_ = keysDown();
    released_ = keysUp();

    if (IsTouching())
        touchRead(&touch_);
}

Vec2 InputService::MoveDirection() const
{
    s32 dx = 0;
    s32 dz = 0;
    if (held_ & kLeftKeys)
        dx -= 1;
    if (held_ & kRightKeys)
        dx += 1;
    if (held_ & kUpKeys)
        dz -= 1;
    if (held_ & kDownKeys)
        dz += 1;

    if (dx != 0 && dz != 0)
        return { kDiagonal * dx, kDiagonal * dz };
    return { Fixed::FromInt(dx), Fixed::FromInt(dz) };
}
