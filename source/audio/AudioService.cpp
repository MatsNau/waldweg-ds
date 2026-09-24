#include "audio/AudioService.h"

#include <nds.h>

#include "core/Fatal.h"
#include "soundbank.h"
#include "world/TimeOfDayService.h"

namespace {

// --- Ambience ---
// The forest quietens down as the sun goes; one entry per DayPhase (0..255).
// A quarter of what it was before there was music: just a hint of forest
// under the piano. The recording is an 8 bit sample levelled to fill its
// range, so a low volume here also keeps its grain well below the music.
constexpr int kAmbienceByPhase[] = { 14, 13, 12, 11, 10, 8 };
static_assert(sizeof(kAmbienceByPhase) / sizeof(kAmbienceByPhase[0])
              == static_cast<int>(DayPhase::Count));
// One step of volume every other frame: the phase change takes about as long
// to be heard as it takes to be seen (TimeOfDayService blends over a second).
constexpr int kAmbienceEaseFrames = 2;
constexpr int kCentre = 128;
constexpr mm_hword kNormalRate = 1024; // 6.10 fixed point, 1024 = as recorded

// --- Music ---
// The soundtrack: 16 bit mono PCM, rate as written by make_music.py. 32768 Hz
// is the rate the DS mixes at; any other rate is resampled by the hardware
// without interpolation, which makes soft piano sound grainy.
constexpr const char *kMusicFile = "nitro:/music/theme.pcm";
constexpr int kMusicRate = 32768;
// Samples in flight. mmStreamUpdate() runs once per frame, so this is how long
// a frame may stall (loading a book page, a slow card read) before the music
// stutters: one second.
constexpr int kMusicBuffer = 32768;
// Quiet between two plays, so the piece ends and begins again like music in
// a room rather than as a loop.
constexpr int kMusicPauseSamples = kMusicRate * 12;
// 0..127. The recording is levelled to a -1 dBFS peak.
constexpr int kMusicVolume = 100;
// Fades in from silence at the start, one step every few frames (~5 s).
constexpr int kMusicEaseFrames = 3;

AudioService *s_musicOwner = nullptr;

} // namespace

void AudioService::Init()
{
    soundEnable();
    if (!mmInitDefault("nitro:/soundbank.bin"))
        Fatal("Soundbank konnte nicht geladen werden.");

    mmLoadEffect(SFX_AMB_FOREST);
    ambienceVolume_ = AmbienceVolume();
    mm_sound_effect sound = {};
    sound.id = SFX_AMB_FOREST;
    sound.rate = kNormalRate;
    sound.volume = static_cast<mm_byte>(ambienceVolume_);
    sound.panning = kCentre;
    // Not released: the handle stays valid so the volume can keep changing.
    ambience_ = mmEffectEx(&sound);

    OpenMusic();
}

void AudioService::Update()
{
    UpdateMusic();
    UpdateAmbience();
}

// --- Ambience ---------------------------------------------------------------

int AudioService::AmbienceVolume() const
{
    return kAmbienceByPhase[static_cast<int>(timeOfDay_.Phase())];
}

void AudioService::UpdateAmbience()
{
    int target = AmbienceVolume();
    if (ambienceVolume_ == target || ++ambienceEaseFrame_ < kAmbienceEaseFrames)
        return;
    ambienceEaseFrame_ = 0;

    ambienceVolume_ += target > ambienceVolume_ ? 1 : -1;
    mmEffectVolume(ambience_, static_cast<mm_word>(ambienceVolume_));
}

// --- Music ------------------------------------------------------------------

void AudioService::OpenMusic()
{
    music_ = std::fopen(kMusicFile, "rb");
    if (music_ == nullptr)
        return;

    s_musicOwner = this;
    mm_stream stream = {};
    stream.sampling_rate = kMusicRate;
    stream.buffer_length = kMusicBuffer;
    stream.callback = FillMusic;
    stream.format = MM_STREAM_16BIT_MONO;
    stream.timer = MM_TIMER0;
    stream.manual = true;
    mmStreamOpen(&stream);
    mmStreamVolume(0);
}

void AudioService::UpdateMusic()
{
    if (music_ == nullptr)
        return;

    mmStreamUpdate();
    if (musicVolume_ < kMusicVolume && ++musicEaseFrame_ >= kMusicEaseFrames)
    {
        musicEaseFrame_ = 0;
        mmStreamVolume(static_cast<mm_byte>(++musicVolume_));
    }
}

mm_word AudioService::FillMusic(mm_word length, mm_addr dest, mm_stream_formats)
{
    return s_musicOwner->ReadMusic(length, static_cast<s16 *>(dest));
}

mm_word AudioService::ReadMusic(mm_word length, s16 *dest)
{
    mm_word done = 0;
    while (done < length)
    {
        mm_word want = length - done;
        if (musicPause_ > 0)
        {
            mm_word quiet = want < static_cast<mm_word>(musicPause_) ? want : static_cast<mm_word>(musicPause_);
            for (mm_word i = 0; i < quiet; i++)
                dest[done + i] = 0;
            done += quiet;
            musicPause_ -= static_cast<int>(quiet);
            continue;
        }
        size_t got = std::fread(dest + done, sizeof(s16), want, music_);
        done += static_cast<mm_word>(got);
        if (got < want)
        {
            // End of the piece: a pause, then from the top.
            std::rewind(music_);
            musicPause_ = kMusicPauseSamples;
        }
    }
    return length;
}

int AudioService::MusicSeconds() const
{
    return music_ != nullptr ? static_cast<int>(mmStreamGetPosition() / kMusicRate) : -1;
}
