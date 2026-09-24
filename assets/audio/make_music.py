"""Converts the soundtrack into the raw stream the game plays from NitroFS.

    python assets/audio/make_music.py [output file]

The track is four minutes long - as a sample it would not fit into the 4 MB
of main RAM, so it is not part of the maxmod soundbank. Instead
source/audio/AudioService streams it from the ROM a few kilobytes at a time.
The stream format is headerless 16 bit signed little endian mono PCM at RATE
Hz; keep RATE in sync with kMusicRate in AudioService.cpp.

16 bit rather than 8: the piece is quiet solo piano with long decays, and 8
bit quantisation noise would hiss through every fade. The level is raised
linearly until the loudest moment sits at PEAK - no compression, the quiet
passages are the point of the music.

The source MP3 is not in the repository (assets/audio/source/, see the README
there), and neither is the result (nitrofiles/music/ is ignored). If the
source is missing the script does nothing and says so; the game then simply
runs without music.
"""
import array
import math
import os
import shutil
import subprocess
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
SOURCE = os.path.join(HERE, "source", "c418_minecraft.mp3")
DEFAULT_OUT = os.path.join(HERE, "..", "..", "nitrofiles", "music", "theme.pcm")

# The rate the DS mixes at. Any other rate is resampled by the sound hardware
# without interpolation, which makes soft piano grainy; resampled here with
# ffmpeg it stays clean.
RATE = 32768
PEAK = 10 ** (-1.0 / 20)          # -1 dBFS
# Leading and trailing silence below this is cut, so the pause between two
# plays is exactly the one AudioService inserts.
SILENCE = 10 ** (-60.0 / 20)


def find_ffmpeg():
    """The asset pipeline runs inside the Wonderful toolchain environment,
    which has its own PATH; ffmpeg lives in the MSYS2 installation."""
    for candidate in (os.environ.get("FFMPEG"), "ffmpeg",
                      "C:/msys64/ucrt64/bin/ffmpeg.exe", "C:/msys64/mingw64/bin/ffmpeg.exe"):
        if candidate and shutil.which(candidate):
            return shutil.which(candidate)
    return None


def decode(ffmpeg):
    command = [ffmpeg, "-v", "error", "-nostdin", "-i", SOURCE, "-vn", "-ac", "1",
               "-af", "aresample=resampler=soxr:precision=28", "-ar", str(RATE), "-f", "f32le", "-"]
    raw = subprocess.run(command, check=True, stdout=subprocess.PIPE).stdout
    samples = array.array("f")
    samples.frombytes(raw)
    return samples


def trim(samples):
    first = next(i for i, s in enumerate(samples) if abs(s) > SILENCE)
    last = len(samples) - next(i for i, s in enumerate(reversed(samples)) if abs(s) > SILENCE)
    return samples[first:last]


def db(value):
    return 20 * math.log10(max(value, 1e-9))


def main():
    out = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT)
    if not os.path.exists(SOURCE):
        print("Musik: %s fehlt, uebersprungen (das Spiel laeuft dann ohne Musik)" % SOURCE)
        return
    ffmpeg = find_ffmpeg()
    if ffmpeg is None:
        print("Musik: ffmpeg nicht gefunden, uebersprungen")
        return

    samples = trim(decode(ffmpeg))
    peak = max(abs(s) for s in samples)
    gain = PEAK / peak
    pcm = array.array("h", (int(round(max(-1.0, min(1.0, s * gain)) * 32767)) for s in samples))
    if sys.byteorder != "little":
        pcm.byteswap()

    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "wb") as f:
        pcm.tofile(f)

    rms = math.sqrt(sum(float(s) * s for s in pcm) / len(pcm)) / 32767
    print("Musik: %s  %.1f s, %d Hz, %.1f MB, Verstaerkung %+.1f dB, RMS %.1f dBFS"
          % (out, len(pcm) / RATE, RATE, os.path.getsize(out) / 1e6, db(gain), db(rms)))


if __name__ == "__main__":
    main()
