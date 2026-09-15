#include "ui/ScreenFader.h"

#include <nds.h>

void ScreenFader::Start(int target, int frames)
{
    target_ = target;
    int distance = target_ > level_ ? target_ - level_ : level_ - target_;
    step_ = frames > 0 ? distance / frames + 1 : distance;
}

void ScreenFader::SetBlack()
{
    level_ = kBlack;
    target_ = kBlack;
    setBrightness(3, -16);
}

void ScreenFader::Update()
{
    if (!IsBusy())
        return;

    if (level_ < target_)
        level_ = level_ + step_ > target_ ? target_ : level_ + step_;
    else
        level_ = level_ - step_ < target_ ? target_ : level_ - step_;

    setBrightness(3, -(level_ >> 8)); // 3 = both screens, negative = darker
}
