#include "audio/AudioService.h"

#include <nds.h>

#include "core/Fatal.h"
#include "soundbank.h"
#include "world/TimeOfDayService.h"

namespace {

constexpr int kStepSounds[] = { SFX_STEP1, SFX_STEP2, SFX_STEP3, SFX_STEP4 };
constexpr int kPageSounds[] = { SFX_PAGE1, SFX_PAGE2 };

// The forest quietens down as the sun goes; one entry per DayPhase.
//
// Held low on purpose: this is a bed you notice when you stop and listen, not
// one you hear over everything. The recording is levelled so that it fills the
// eight bits of the sample, which is what these numbers are turning back down.
constexpr int kAmbienceByPhase[] = { 56, 54, 49, 44, 39, 34 };
static_assert(sizeof(kAmbienceByPhase) / sizeof(kAmbienceByPhase[0])
              == static_cast<int>(DayPhase::Count));

// One step of volume every other frame: the phase change takes about as long
// to be heard as it takes to be seen (TimeOfDayService blends over a second).
constexpr int kVolumeEaseFrames = 2;

constexpr int kCentre = 128;
constexpr mm_hword kNormalRate = 1024; // 6.10 fixed point, 1024 = as recorded

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
    for (int sound : kStepSounds)
        mmLoadEffect(sound);
    for (int sound : kPageSounds)
        mmLoadEffect(sound);

    volume_ = AmbienceVolume();

    mm_sound_effect sound = {};
    sound.id = SFX_AMB_FOREST;
    sound.rate = kNormalRate;
    sound.volume = static_cast<mm_byte>(volume_);
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
    int target = AmbienceVolume();
    if (volume_ == target)
        return;

    if (++easeFrame_ < kVolumeEaseFrames)
        return;
    easeFrame_ = 0;

    volume_ += target > volume_ ? 1 : -1;
    mmEffectVolume(ambience_, static_cast<mm_word>(volume_));
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
