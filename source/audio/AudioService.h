#pragma once

#include <maxmod9.h>

#include "core/Random.h"

class TimeOfDayService;

// All sound: the looping forest ambience plus the one-shot effects.
// maxmod plays them from the soundbank that the Makefile packs into NitroFS.
//
// The ambience is a thirty second cut from a field recording (see
// assets/audio/make_ambience.py) and brings its own wind and birds, so the
// only thing done to it here is the level: quieter as the sun goes down,
// eased over so the change is never a step.
class AudioService
{
public:
    explicit AudioService(const TimeOfDayService &timeOfDay) : timeOfDay_(timeOfDay) {}

    void Init();
    // Once per frame: eases the ambience towards the level of the day phase.
    void Update();

    // A footstep on the forest floor. Mats walks behind Nina, so his steps
    // are quieter and wander further from the centre.
    void PlayStep(bool distant);
    void PlayPageTurn();

private:
    int AmbienceVolume() const;
    // Plays a one-shot with random pitch, volume and panning, so a sound that
    // repeats often never turns into a machine gun.
    void Play(int sound, int volume, int rateJitter, int panSpread);

    const TimeOfDayService &timeOfDay_;
    Random rng_{ 0x5EED1705 };
    mm_sfxhand ambience_ = 0;
    int volume_ = 0;
    int easeFrame_ = 0;
    int pageVariant_ = 0;
};
