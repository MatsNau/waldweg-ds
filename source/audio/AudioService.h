#pragma once

#include <maxmod9.h>

#include "core/Random.h"

class TimeOfDayService;

// All sound: the looping forest ambience plus the one-shot effects.
// maxmod plays them from the soundbank that the Makefile packs into NitroFS.
//
// The ambience loop is deliberately even; the life comes from here: a slow
// volume drift, gusts rolling through now and then, and the odd tree creak.
class AudioService
{
public:
    explicit AudioService(const TimeOfDayService &timeOfDay) : timeOfDay_(timeOfDay) {}

    void Init();
    // Once per frame: wind drift, gusts, creaks.
    void Update();

    // A footstep on the forest floor. Mats walks behind Nina, so his steps
    // are quieter and wander further from the centre.
    void PlayStep(bool distant);
    void PlayPageTurn();

private:
    void StartAmbience();
    int AmbienceVolume() const;
    // Plays a one-shot with random pitch, volume and panning, so a sound that
    // repeats often never turns into a machine gun.
    void Play(int sound, int volume, int rateJitter, int panSpread);

    const TimeOfDayService &timeOfDay_;
    Random rng_{ 0x5EED1705 };
    mm_sfxhand ambience_ = 0;
    u32 frame_ = 0;
    u32 nextGust_ = 0;
    u32 nextCreak_ = 0;
    int pageVariant_ = 0;
};
