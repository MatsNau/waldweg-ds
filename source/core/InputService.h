#pragma once

#include <nds.h>

#include "math/Vec2.h"

enum class Button : u32
{
    A = KEY_A,
    B = KEY_B,
    X = KEY_X,
    Y = KEY_Y,
    L = KEY_L,
    R = KEY_R,
    Start = KEY_START,
    Select = KEY_SELECT,
    Up = KEY_UP,
    Down = KEY_DOWN,
    Left = KEY_LEFT,
    Right = KEY_RIGHT,
    Touch = KEY_TOUCH,
};

// Reads buttons and the touch screen once per frame.
class InputService
{
public:
    void Update();

    bool IsHeld(Button button) const { return (held_ & static_cast<u32>(button)) != 0; }
    bool IsPressed(Button button) const { return (pressed_ & static_cast<u32>(button)) != 0; }
    bool IsReleased(Button button) const { return (released_ & static_cast<u32>(button)) != 0; }
    // True if any button or the touch screen was pressed this frame (not the d-pad).
    bool IsAnyButtonPressed() const
    {
        constexpr u32 kButtons = KEY_A | KEY_B | KEY_X | KEY_Y | KEY_L | KEY_R | KEY_START | KEY_SELECT | KEY_TOUCH;
        return (pressed_ & kButtons) != 0;
    }

    // Unit walking direction on the ground plane, zero when idle. The D-pad and
    // the mirrored face buttons (X up, B down, Y left, A right) both work, so
    // the game can be played left-handed with the stylus in the right hand.
    Vec2 MoveDirection() const;

    bool IsTouching() const { return IsHeld(Button::Touch); }
    // Last touched position; stays valid in the frame the stylus is lifted.
    int TouchX() const { return touch_.px; }
    int TouchY() const { return touch_.py; }

private:
    u32 held_ = 0;
    u32 pressed_ = 0;
    u32 released_ = 0;
    touchPosition touch_ = {};
};
