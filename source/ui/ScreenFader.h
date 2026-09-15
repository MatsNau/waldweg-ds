#pragma once

// Fades both screens to black and back (hardware master brightness).
class ScreenFader
{
public:
    void FadeOut(int frames) { Start(kBlack, frames); }
    void FadeIn(int frames) { Start(0, frames); }

    void Update();
    // Starts fully black (e.g. when a new screen opens after a fade-out).
    void SetBlack();

    bool IsBusy() const { return level_ != target_; }
    bool IsBlack() const { return level_ == kBlack && target_ == kBlack; }

private:
    static constexpr int kBlack = 16 << 8; // brightness 16, 8 bits of sub-steps

    void Start(int target, int frames);

    int level_ = 0;
    int target_ = 0;
    int step_ = 0;
};
