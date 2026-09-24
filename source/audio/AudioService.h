#pragma once

#include <cstdio>

#include <maxmod9.h>
#include <nds/ndstypes.h>

class TimeOfDayService;

// All sound: the piano soundtrack and, quietly underneath, the forest.
//
// The soundtrack is far too big for RAM and is streamed from NitroFS (see
// assets/audio/make_music.py); without the file the game runs without music.
// The forest ambience is a thirty second loop from a field recording (see
// assets/audio/make_ambience.py) in the maxmod soundbank. It is kept low - a
// bed you notice when you stop and listen - and gets quieter as the sun goes
// down, eased over so the change is never a step.
class AudioService
{
public:
    explicit AudioService(const TimeOfDayService &timeOfDay) : timeOfDay_(timeOfDay) {}

    void Init();
    // Once per frame: refills the music stream, fades it in at the start and
    // eases the ambience towards the level of the day phase.
    void Update();

    // Seconds the soundtrack stream has played (pauses included), -1 without music.
    int MusicSeconds() const;

private:
    int AmbienceVolume() const;
    void UpdateAmbience();
    void OpenMusic();
    void UpdateMusic();
    // maxmod asks for the next `length` samples of the soundtrack. Called from
    // mmStreamUpdate() in the main loop, never from an interrupt, so reading
    // NitroFS here cannot collide with other file access.
    static mm_word FillMusic(mm_word length, mm_addr dest, mm_stream_formats format);
    mm_word ReadMusic(mm_word length, s16 *dest);

    const TimeOfDayService &timeOfDay_;
    mm_sfxhand ambience_ = 0;
    int ambienceVolume_ = 0;
    int ambienceEaseFrame_ = 0;

    FILE *music_ = nullptr;
    int musicPause_ = 0; // samples of silence left before the next play
    int musicVolume_ = 0;
    int musicEaseFrame_ = 0;
};
