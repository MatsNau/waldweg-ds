#include "world/CameraRig.h"

#include "core/Fatal.h"

namespace {

constexpr Fixed kHeight = 4.3_fx;
constexpr Fixed kDistanceBehind = 5.4_fx;
// Look slightly ahead of the target so more of the path in front is visible.
constexpr Fixed kLookAhead = 1.3_fx;
constexpr Fixed kLookHeight = 0.5_fx;
// Fraction of the remaining distance covered per frame.
constexpr Fixed kFollowFactor = 0.12_fx;

} // namespace

void CameraRig::Init()
{
    camera_ = NE_CameraCreate();
    if (camera_ == nullptr)
        Fatal("Kamera konnte nicht erstellt werden.");
}

void CameraRig::SnapTo(Vec2 target)
{
    focus_ = target;
    zoom_ = targetZoom_;
    UpdateCamera();
}

void CameraRig::Follow(Vec2 target)
{
    focus_ += (target - focus_) * kFollowFactor;
    zoom_ = fx::Approach(zoom_, targetZoom_, 0.01_fx);
    UpdateCamera();
}

void CameraRig::UpdateCamera()
{
    Fixed lookZ = focus_.z - kLookAhead * zoom_;
    NE_CameraSetI(camera_,
                  focus_.x.Raw(), (kHeight * zoom_).Raw(), (focus_.z + kDistanceBehind * zoom_).Raw(),
                  focus_.x.Raw(), (kLookHeight * zoom_).Raw(), lookZ.Raw(),
                  0, Fixed::kOne, 0);
}
