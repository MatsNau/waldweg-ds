"""Cuts the looping forest ambience out of the recorded source track.

    python assets/audio/make_ambience.py [output directory] [--start SECONDS]

Unlike the other sounds the ambience is not synthesised (see gen_sfx.py) but
taken from a three hour field recording of a wood with birdsong. The recording
itself is far too big for the repository, so only the finished loop in
audio/ is checked in; the source lives in assets/audio/source/ and is ignored
by git (see the README there).

The work is: decode a window of the recording to the DS sample format
(8 bit mono), make it loop without a click, and get it to use the eight bits.
The seam is closed with an equal power crossfade - the tail of the window is
faded over its head, so the sample ends where it began. Equal power (not
linear) because two different moments of a wood are uncorrelated: linear
weights would leave an audible dip in the middle of the fade.

If the source file is missing the script does nothing and says so, so that a
fresh checkout can still run the asset pipeline.
"""
import os
import shutil
import struct
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import synth

SOURCE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "source", "forest_birdsong.mp3")

# The recording repeats itself every 24.4 minutes, so only its first 24 minutes
# are unique. This window was picked out of those by measuring every 30 second
# window in the recording (see the devlog, day 8): even level, birds well above
# the wind, no rumble, and - so the crossfade does not smear a call across the
# seam - quiet at both ends.
START = 495.5
# 30 s at 16 kHz is 480000 samples: a multiple of 8, as the sound hardware
# wants for loop points. Long enough that a distinctive call does not come
# round often enough to be recognised.
LENGTH = 30.0
CROSSFADE = 3.0
# Birds live between 2 and 6 kHz, so 16 kHz is the lowest rate that keeps them
# sounding like birds; at 11 kHz they turn into a wash.
RATE = 16000
# Below this there is nothing in a wood but handling rumble, and the DS speaker
# cannot reproduce it anyway - it would only eat into the 8 bit range.
HIGHPASS = 70.0
# Normalising on the peak would waste the eight bits: the recording sits 22 dB
# below its own loudest moment, and those moments are a handful of three
# millisecond ticks, not birdsong. So the level is set by a high percentile and
# what pokes out above KNEE is rounded off (see fit_range).
LOUD_PERCENTILE = 0.999
KNEE = 0.75
CEILING = 0.92


def find_ffmpeg():
    """The asset pipeline runs inside the Wonderful toolchain environment,
    which has its own PATH; ffmpeg lives in the MSYS2 installation."""
    candidates = [os.environ.get("FFMPEG"), "ffmpeg",
                  "C:/msys64/ucrt64/bin/ffmpeg.exe", "C:/msys64/mingw64/bin/ffmpeg.exe"]
    for candidate in candidates:
        if candidate and shutil.which(candidate):
            return shutil.which(candidate)
    return None


def decode(ffmpeg, start, seconds):
    """A mono block of the recording as floats in [-1, 1]."""
    command = [
        ffmpeg, "-v", "error", "-nostdin",
        "-ss", "%.3f" % start, "-t", "%.3f" % seconds,
        "-i", SOURCE, "-vn", "-ac", "1",
        "-af", "highpass=f=%.1f" % HIGHPASS,
        "-ar", str(RATE), "-f", "s16le", "-",
    ]
    raw = subprocess.run(command, check=True, stdout=subprocess.PIPE).stdout
    count = len(raw) // 2
    return [value / 32768.0 for value in struct.unpack("<%dh" % count, raw[:count * 2])]


def close_loop(block, length, fade):
    """Fades the `fade` samples that follow the loop body over its first
    samples, so the last sample runs into the first one the way the recording
    ran on. Returns exactly `length` samples."""
    import math

    out = block[:length]
    for i in range(fade):
        t = (i + 0.5) / fade
        head = math.sin(t * math.pi * 0.5)   # the body fades in
        tail = math.cos(t * math.pi * 0.5)   # what followed it fades out
        out[i] = out[i] * head + block[length + i] * tail
    return out


def fit_range(samples):
    """Lifts the bed into the eight bit range instead of leaving it three bits
    deep. The gain puts LOUD_PERCENTILE of the sample at KNEE; below that
    nothing is touched at all, and the rare tick above it is bent smoothly
    towards CEILING rather than clipped. Returns (samples, gain, compressed)."""
    import math

    ranked = sorted(abs(value) for value in samples)
    reference = ranked[int(len(ranked) * LOUD_PERCENTILE)] or 1.0
    gain = KNEE / reference
    span = CEILING - KNEE

    out = []
    compressed = 0
    for value in samples:
        value *= gain
        if abs(value) > KNEE:
            compressed += 1
            sign = 1.0 if value > 0.0 else -1.0
            value = sign * (KNEE + span * math.tanh((abs(value) - KNEE) / span))
        out.append(value)
    return out, gain, compressed


def seam_report(samples, rate):
    """How hard the jump at the loop point is, measured against the jumps
    inside the sample - a seam that stands out is one you hear as a click."""
    step = [abs(samples[i + 1] - samples[i]) for i in range(len(samples) - 1)]
    step.sort()
    jump = abs(samples[0] - samples[-1])
    scale = 127.0  # in 8 bit steps, the units the DS actually plays
    return (jump * scale, step[len(step) // 2] * scale, step[int(len(step) * 0.99)] * scale)


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else "audio"
    start = START
    if "--start" in sys.argv:
        start = float(sys.argv[sys.argv.index("--start") + 1])

    if not os.path.isfile(SOURCE):
        print("  amb_forest.wav uebersprungen: %s fehlt (siehe assets/audio/source/README.md)"
              % os.path.relpath(SOURCE))
        return

    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        print("  amb_forest.wav uebersprungen: ffmpeg nicht gefunden (FFMPEG=... setzen)")
        return

    length = int(LENGTH * RATE) // 8 * 8
    fade = int(CROSSFADE * RATE)
    block = decode(ffmpeg, start, LENGTH + CROSSFADE + 0.5)
    if len(block) < length + fade:
        raise SystemExit("Quelle zu kurz ab %.1f s" % start)

    samples = close_loop(block, length, fade)
    samples, gain, compressed = fit_range(samples)

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "amb_forest.wav")
    written = synth.write_wav(path, samples, RATE, loop=(0, length - 1))

    import math

    written_samples = synth.normalize(samples, CEILING)
    rms = (sum(value * value for value in written_samples) / len(written_samples)) ** 0.5
    jump, median, p99 = seam_report(written_samples, RATE)
    print("  %-12s %6.2f s  %5d Hz  %6.1f KB  (loop, ab %.1f s der Aufnahme)"
          % ("amb_forest.wav", length / RATE, RATE, written / 1024.0, start))
    print("  %-12s Gesamtverstaerkung %+.1f dB, %.3f %% der Samples begrenzt"
          % ("", 20.0 * math.log10(gain), 100.0 * compressed / len(samples)))
    print("  %-12s RMS %.1f dBFS  Naht %.0f (median %.0f / p99 %.0f von 255)"
          % ("", 20.0 * math.log10(rms), jump, median, p99))


if __name__ == "__main__":
    main()
