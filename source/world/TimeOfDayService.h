#pragma once

#include "render/RenderService.h"

// Sun position steps of the story. Each processed mushroom advances one step.
enum class DayPhase : u8
{
    Golden,
    Amber,
    Rose,
    Violet,
    Blue,
    Night,
    Count,
};

// Blends the atmosphere smoothly (~1 s) from one day phase to the next.
class TimeOfDayService
{
public:
    explicit TimeOfDayService(RenderService &render) : render_(render) {}

    void Reset(DayPhase phase);
    // Moves on to the next phase (stays at night).
    void Advance();
    // Blends to the given phase (no-op if already there).
    void BlendTo(DayPhase phase);
    void Update();
    // Applies the current atmosphere again (after another view changed it).
    void Reapply() { Apply(); }

    DayPhase Phase() const { return phase_; }
    const char *PhaseName() const;
    bool IsBlending() const { return blendFrame_ < kBlendFrames; }

private:
    static constexpr int kBlendFrames = 60;

    void Apply();

    RenderService &render_;
    DayPhase phase_ = DayPhase::Golden;
    DayPhase previous_ = DayPhase::Golden;
    int blendFrame_ = kBlendFrames;
};
