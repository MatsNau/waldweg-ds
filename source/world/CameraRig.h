#pragma once

#include <NEMain.h>

#include "math/Vec2.h"

// Wild-World-style camera: fixed viewing direction (towards -Z), looking down
// at an angle and smoothly following a target on the ground.
class CameraRig
{
public:
    void Init();

    void SnapTo(Vec2 target);
    void Follow(Vec2 target);
    // Pulls the camera further out (1 = normal), approached smoothly.
    void SetZoom(Fixed zoom) { targetZoom_ = zoom; }

    // Activates the camera for the current 3D frame.
    void Use() const { NE_CameraUse(camera_); }

    Vec2 Focus() const { return focus_; }

private:
    void UpdateCamera();

    NE_Camera *camera_ = nullptr;
    Vec2 focus_;
    Fixed zoom_ = 1_fx;
    Fixed targetZoom_ = 1_fx;
};
