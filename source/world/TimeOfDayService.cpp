#include "world/TimeOfDayService.h"

#include <nds.h>

namespace {

struct Keyframe
{
    const char *name;
    Atmosphere atmosphere;
};

// Fog colours follow the plan: #F0A860 (gold) -> #6A5A9A (violet) -> #1E2440 (night).
// From violet on it gets really dark and the fog creeps closer, so the lantern
// becomes necessary. Fog depth: 0x7D80 ~ 9.5 units from the camera, 0x7B80 ~ 6.
// Shadows grow longer as the sun sinks and disappear in the dark.
const Keyframe kKeyframes[] = {
    { "Goldene Stunde", { RGB15(30, 21, 12), RGB15(31, 27, 20), RGB15(13, 10, 8), RGB15(7, 4, 3),
                          floattov10(-0.6), floattov10(-0.5), floattov10(-0.6), 0x7D80,
                          (0.55_fx).Raw(), 11 } },
    { "Bernstein", { RGB15(30, 17, 9), RGB15(31, 23, 14), RGB15(12, 9, 7), RGB15(7, 3, 2),
                     floattov10(-0.7), floattov10(-0.35), floattov10(-0.6), 0x7D80,
                     (0.85_fx).Raw(), 11 } },
    { "Rosé", { RGB15(26, 14, 14), RGB15(28, 18, 17), RGB15(10, 7, 8), RGB15(6, 3, 3),
                floattov10(-0.8), floattov10(-0.25), floattov10(-0.5), 0x7D40,
                (1.25_fx).Raw(), 10 } },
    { "Violett", { RGB15(9, 7, 14), RGB15(15, 12, 19), RGB15(6, 5, 8), RGB15(3, 2, 5),
                   floattov10(-0.8), floattov10(-0.2), floattov10(-0.5), 0x7CC0,
                   (1.7_fx).Raw(), 6 } },
    { "Blaue Stunde", { RGB15(2, 3, 8), RGB15(6, 7, 12), RGB15(3, 3, 6), RGB15(1, 1, 4),
                        floattov10(-0.5), floattov10(-0.6), floattov10(-0.6), 0x7C00, 0, 0 } },
    { "Nacht", { RGB15(1, 1, 4), RGB15(4, 5, 9), RGB15(2, 2, 4), RGB15(1, 1, 3),
                 floattov10(-0.3), floattov10(-0.8), floattov10(-0.5), 0x7B80, 0, 0 } },
};

constexpr int kKeyframeCount = sizeof(kKeyframes) / sizeof(kKeyframes[0]);

s32 Mix(s32 a, s32 b, int t, int total)
{
    return a + (b - a) * t / total;
}

u32 MixColor(u32 a, u32 b, int t, int total)
{
    s32 r = Mix(a & 31, b & 31, t, total);
    s32 g = Mix((a >> 5) & 31, (b >> 5) & 31, t, total);
    s32 bl = Mix((a >> 10) & 31, (b >> 10) & 31, t, total);
    return RGB15(r, g, bl);
}

} // namespace

void TimeOfDayService::Reset(DayPhase phase)
{
    phase_ = phase;
    previous_ = phase;
    blendFrame_ = kBlendFrames;
    Apply();
}

void TimeOfDayService::Advance()
{
    int next = static_cast<int>(phase_) + 1;
    if (next < kKeyframeCount)
        BlendTo(static_cast<DayPhase>(next));
}

void TimeOfDayService::BlendTo(DayPhase phase)
{
    if (phase == phase_)
        return;

    previous_ = phase_;
    phase_ = phase;
    blendFrame_ = 0;
}

void TimeOfDayService::Update()
{
    if (!IsBlending())
        return;

    blendFrame_++;
    Apply();
}

const char *TimeOfDayService::PhaseName() const
{
    return kKeyframes[static_cast<int>(phase_)].name;
}

void TimeOfDayService::Apply()
{
    const Atmosphere &from = kKeyframes[static_cast<int>(previous_)].atmosphere;
    const Atmosphere &to = kKeyframes[static_cast<int>(phase_)].atmosphere;
    int t = blendFrame_;

    Atmosphere mixed = {
        MixColor(from.sky, to.sky, t, kBlendFrames),
        MixColor(from.light, to.light, t, kBlendFrames),
        MixColor(from.ambient, to.ambient, t, kBlendFrames),
        MixColor(from.outline, to.outline, t, kBlendFrames),
        Mix(from.lightX, to.lightX, t, kBlendFrames),
        Mix(from.lightY, to.lightY, t, kBlendFrames),
        Mix(from.lightZ, to.lightZ, t, kBlendFrames),
        Mix(from.fogDepth, to.fogDepth, t, kBlendFrames),
        Mix(from.shadowLength, to.shadowLength, t, kBlendFrames),
        Mix(from.shadowAlpha, to.shadowAlpha, t, kBlendFrames),
    };
    render_.ApplyAtmosphere(mixed);
}
