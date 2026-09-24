"""Generates the footstep sounds into audio/, where mmutil picks them up.

    python assets/audio/gen_sfx.py [output directory]

These are synthesised (see synth.py) rather than sampled: leaves crackling
underfoot are noise based, and the pipeline stays self contained. The forest
ambience is the exception - it comes from a recording, see make_ambience.py.

Sample names become the SFX_* constants in the generated soundbank.h, so
`step1.wav` is `SFX_STEP1`.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import synth

RATE = 16000


def footstep(seed, crackle_freq, thud_freq):
    """A step on the forest floor: dry leaves crackling over a soft earth thud.

    The crackle is a cloud of very short noise grains whose density collapses
    right after the foot lands - a single filtered noise burst sounds like
    static, a cloud of grains sounds like leaves.
    """
    rng = random.Random(seed)
    rate = RATE
    n = int(0.20 * rate)

    def density(index):
        return 60.0 + 900.0 * pow(2.718281828, -index / (0.030 * rate))

    leaves = synth.grain_cloud(n, rate, rng, density, burst=(0.0010, 0.0045))
    leaves = synth.bandpass(leaves, crackle_freq, 0.9, rate)
    leaves = synth.multiply(leaves, synth.decay(n, 0.055, rate))

    scuff = synth.bandpass(synth.white(n, rng), 950.0, 1.2, rate)
    scuff = synth.multiply(scuff, synth.decay(n, 0.030, rate))

    thud = synth.lowpass(synth.white(n, rng), thud_freq, rate)
    thud = synth.multiply(thud, synth.decay(n, 0.038, rate))

    out = synth.mix(synth.scale(leaves, 1.0), synth.scale(scuff, 0.30), synth.scale(thud, 0.85))
    return synth.fade_edges(out, rate, 0.001, 0.03), rate


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "audio"
    os.makedirs(out_dir, exist_ok=True)

    sounds = {}

    # Four variants so repeated steps never sound mechanical.
    for i, (crackle, thud) in enumerate(
            [(2600.0, 170.0), (3100.0, 150.0), (2350.0, 195.0), (2900.0, 165.0)], start=1):
        sounds["step%d" % i] = footstep(100 + i, crackle, thud)

    total = 0
    for name in sorted(sounds):
        entry = sounds[name]
        samples, rate = entry[0], entry[1]
        loop = entry[2] if len(entry) > 2 else None
        path = os.path.join(out_dir, name + ".wav")
        written = synth.write_wav(path, samples, rate, loop=loop)
        total += written
        print("  %-12s %6.2f s  %5d Hz  %6.1f KB%s"
              % (name + ".wav", len(samples) / rate, rate, written / 1024.0,
                 "  (loop)" if loop else ""))
    print("  %-12s %30s %6.1f KB" % ("total", "", total / 1024.0))


if __name__ == "__main__":
    main()
