#include "audio/AudioService.h"

#include <nds.h>

#include "core/Fatal.h"
#include "math/Angle.h"
#include "soundbank.h"
#include "world/TimeOfDayService.h"

namespace {

constexpr int kStepSounds[] = { SFX_STEP1, SFX_STEP2, SFX_STEP3, SFX_STEP4 };
constexpr int kPageSounds[] = { SFX_PAGE1, SFX_PAGE2 };
constexpr int kCreakSounds[] = { SFX_CREAK1, SFX_CREAK2, SFX_CREAK3 };

// The forest quietens down as the sun goes; one entry per DayPhase.
//
// Held low on purpose: noise has a low crest factor, so at the same setting a
// steady bed sounds far louder than the short effects on top of it. This is a
// bed you notice when you stop and listen, not one you hear over everything.
constexpr int kAmbienceByPhase[] = { 68, 66, 60, 54, 48, 42 };
static_assert(sizeof(kAmbienceByPhase) / sizeof(kAmbienceByPhase[0])
              == static_cast<int>(DayPhase::Count));

constexpr int kCentre = 128;
constexpr mm_hword kNormalRate = 1024; // 6.10 fixed point, 1024 = as recorded

// Two drift periods that do not line up (about 24 s and 10 s), so the wind
// never settles into an audible rhythm over the six second ambience loop.
constexpr s32 kSlowDrift = 23;
constexpr s32 kFastDrift = 53;

constexpr int Clamp(int value, int lo, int hi)
{
    return value < lo ? lo : (value > hi ? hi : value);
}

} // namespace

void AudioService::Init()
{
    soundEnable();
    if (!mmInitDefault("nitro:/soundbank.bin"))
        Fatal("Soundbank konnte nicht geladen werden.");

    mmLoadEffect(SFX_AMB_FOREST);
    mmLoadEffect(SFX_GUST);
    for (int sound : kCreakSounds)
        mmLoadEffect(sound);
    for (int sound : kStepSounds)
        mmLoadEffect(sound);
    for (int sound : kPageSounds)
        mmLoadEffect(sound);

    StartAmbience();
    nextGust_ = 360;
    nextCreak_ = 540;
}

void AudioService::StartAmbience()
{
    mm_sound_effect sound = {};
    sound.id = SFX_AMB_FOREST;
    sound.rate = kNormalRate;
    sound.volume = static_cast<mm_byte>(AmbienceVolume());
    sound.panning = kCentre;
    // Not released: the handle stays valid so the volume can keep changing.
    ambience_ = mmEffectEx(&sound);
}

int AudioService::AmbienceVolume() const
{
    return kAmbienceByPhase[static_cast<int>(timeOfDay_.Phase())];
}

void AudioService::Update()
{
    ++frame_;

    Angle slow = Angle::FromBinary(static_cast<s32>(frame_) * kSlowDrift);
    Angle fast = Angle::FromBinary(static_cast<s32>(frame_) * kFastDrift);
    int drift = (slow.Sin() * 7 + fast.Sin() * 3).ToInt();
    mmEffectVolume(ambience_, static_cast<mm_word>(Clamp(AmbienceVolume() + drift, 0, 255)));

    // Everything happens more rarely once it is dark.
    bool night = timeOfDay_.Phase() == DayPhase::Night;
    int stretch = night ? 170 : 100;

    if (frame_ >= nextGust_)
    {
        Play(SFX_GUST, rng_.Range(52, 84), 90, 70);
        nextGust_ = frame_ + static_cast<u32>(rng_.Range(900, 2200) * stretch / 100);
    }

    if (frame_ >= nextCreak_)
    {
        Play(kCreakSounds[rng_.Range(0, 2)], rng_.Range(38, 68), 130, 90);
        nextCreak_ = frame_ + static_cast<u32>(rng_.Range(700, 2600) * stretch / 100);
    }
}

void AudioService::Play(int sound, int volume, int rateJitter, int panSpread)
{
    mm_sound_effect effect = {};
    effect.id = static_cast<mm_word>(sound);
    effect.rate = static_cast<mm_hword>(kNormalRate + rng_.Range(-rateJitter, rateJitter));
    effect.volume = static_cast<mm_byte>(Clamp(volume, 0, 255));
    effect.panning = static_cast<mm_byte>(Clamp(kCentre + rng_.Range(-panSpread, panSpread), 0, 255));
    // Released right away: these are short, and maxmod may recycle the channel.
    mmEffectRelease(mmEffectEx(&effect));
}

void AudioService::PlayStep(bool distant)
{
    int volume = distant ? rng_.Range(46, 70) : rng_.Range(118, 162);
    Play(kStepSounds[rng_.Range(0, 3)], volume, 110, distant ? 55 : 28);
}

void AudioService::PlayPageTurn()
{
    // Alternating, so flipping quickly through the book does not repeat one
    // sound over and over.
    pageVariant_ ^= 1;
    Play(kPageSounds[pageVariant_], rng_.Range(150, 185), 70, 24);
}
