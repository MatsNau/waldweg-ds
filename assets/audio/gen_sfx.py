"""Generates the sound effects into audio/, where mmutil picks them up.

    python assets/audio/gen_sfx.py [output directory]

Everything is synthesised (see synth.py) rather than sampled: all four sounds
the game needs are noise based, the pipeline stays self contained, and the
loop points of the ambience can be placed exactly.

Sample names become the SFX_* constants in the generated soundbank.h, so
`step1.wav` is `SFX_STEP1`.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import synth

# Short, crisp sounds get the higher rate; the long beds do not need it.
RATE_SHORT = 16000
RATE_LONG = 11025

# The ambience loops every six seconds. Rounded down to a multiple of 8 so the
# loop points stay word aligned for the sound hardware.
AMBIENCE_SAMPLES = (6 * RATE_LONG) // 8 * 8


def footstep(seed, crackle_freq, thud_freq):
    """A step on the forest floor: dry leaves crackling over a soft earth thud.

    The crackle is a cloud of very short noise grains whose density collapses
    right after the foot lands - a single filtered noise burst sounds like
    static, a cloud of grains sounds like leaves.
    """
    rng = random.Random(seed)
    rate = RATE_SHORT
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


def page_turn(seed, sweep_top):
    """Turning a page: the sheet lifting, then settling back down."""
    rng = random.Random(seed)
    rate = RATE_SHORT
    n = int(0.34 * rate)

    shape = synth.envelope(n, [(0.0, 0.0), (0.03, 1.0), (0.11, 0.35),
                               (0.17, 0.8), (0.34, 0.0)], rate)

    def density(index):
        return 120.0 + 1400.0 * shape[index]

    paper = synth.grain_cloud(n, rate, rng, density, burst=(0.0008, 0.0035))
    # The brightness follows the movement: fastest while the sheet flips over.
    freqs = [900.0 + sweep_top * value for value in shape]
    paper = synth.sweep_band(paper, freqs, 1.6, rate)
    paper = synth.multiply(paper, shape)

    body = synth.lowpass(synth.white(n, rng), 260.0, rate)
    body = synth.multiply(body, synth.multiply(shape, shape))

    out = synth.mix(synth.scale(paper, 1.0), synth.scale(body, 0.35))
    return synth.fade_edges(out, rate, 0.002, 0.04), rate


def tree_creak(seed, resonances):
    """A tree creaking: stick-slip pulses through the resonances of the trunk.

    The pulses slow down towards the end, which is what makes it read as wood
    settling rather than as a rattle.
    """
    rng = random.Random(seed)
    rate = RATE_LONG
    n = int(1.7 * rate)

    def interval(index):
        return 0.009 + 0.026 * index / n

    pulses = synth.impulse_train(n, rate, rng, interval, jitter=0.45)

    wood = synth.mix(*[
        synth.scale(synth.bandpass(pulses, freq, q, rate), gain)
        for freq, q, gain in resonances
    ])
    wood = synth.multiply(wood, synth.envelope(
        n, [(0.0, 0.0), (0.30, 1.0), (1.05, 0.75), (1.7, 0.0)], rate))

    # A little air around it so it does not sound like a plain filter ping.
    air = synth.bandpass(synth.white(n, rng), 1800.0, 0.8, rate)
    air = synth.multiply(air, synth.decay(n, 0.5, rate))

    out = synth.soft_clip(synth.mix(wood, synth.scale(air, 0.12)))
    return synth.fade_edges(out, rate, 0.02, 0.15), rate


def wind_gust():
    """A gust rolling through the canopy: played now and then over the bed, so
    the wind never settles into the six second loop of the ambience."""
    rng = random.Random(4711)
    rate = RATE_LONG
    n = int(2.8 * rate)

    swell = synth.envelope(n, [(0.0, 0.0), (0.9, 1.0), (1.5, 0.85), (2.8, 0.0)], rate)

    air = synth.lowpass(synth.lowpass(synth.white(n, rng), 520.0, rate), 520.0, rate)
    air = synth.multiply(air, swell)

    def density(index):
        return 40.0 + 620.0 * swell[index]

    leaves = synth.grain_cloud(n, rate, rng, density, burst=(0.0012, 0.005))
    # Stronger gust, brighter leaves - but kept under the harsh band, like the bed.
    leaves = synth.sweep_band(leaves, [1200.0 + 1400.0 * value for value in swell], 1.1, rate)
    leaves = synth.multiply(leaves, swell)

    out = synth.mix(synth.scale(air, 1.7), synth.scale(leaves, 0.75))
    return synth.fade_edges(out, rate, 0.05, 0.2), rate


def forest_ambience():
    """The steady bed: leaves rustling with a low wind underneath.

    Deliberately almost even - the big movements come from the gust one-shot
    and from the slow volume drift in AudioService, so the loop itself never
    draws attention to its length. Every filter runs circularly and every LFO
    completes a whole number of cycles, so the loop is seamless.
    """
    rng = random.Random(20260916)
    rate = RATE_LONG
    n = AMBIENCE_SAMPLES

    # Gentle, non-repeating-sounding breathing: 2, 5 and 11 cycles per loop.
    breath = synth.multiply(
        synth.lfo(n, 2, 0.78, 1.0),
        synth.lfo(n, 5, 0.85, 1.0, phase=0.31),
        synth.lfo(n, 11, 0.92, 1.0, phase=0.67),
    )

    # Kept well below the 2-5 kHz band the ear is most sensitive to: up there
    # rustling stops sounding like a forest and starts sounding like hiss.
    bed = synth.bandpass(synth.white(n, rng), 1600.0, 0.7, rate, circular=True)
    bed = synth.multiply(bed, breath)

    ticks = synth.grain_cloud(n, rate, rng, 24.0, burst=(0.0012, 0.005), wrap=True)
    ticks = synth.bandpass(ticks, 2300.0, 0.9, rate, circular=True)

    wind = synth.lowpass(synth.white(n, rng), 240.0, rate, circular=True)
    wind = synth.lowpass(wind, 240.0, rate, circular=True)
    wind = synth.multiply(wind, breath)

    whoosh = synth.bandpass(synth.white(n, rng), 620.0, 0.7, rate, circular=True)
    whoosh = synth.multiply(whoosh, synth.multiply(breath, breath))

    # The low wind carries the bed; the leaves only colour it.
    out = synth.mix(
        synth.scale(bed, 0.26),
        synth.scale(ticks, 0.13),
        synth.scale(wind, 1.0),
        synth.scale(whoosh, 0.20),
    )
    # Takes the last of the hiss off the top.
    out = synth.lowpass(out, 2400.0, rate, circular=True)
    return synth.soft_clip(out), rate, (0, n - 1)


def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "audio"
    os.makedirs(out_dir, exist_ok=True)

    sounds = {}

    # Four variants so repeated steps never sound mechanical.
    for i, (crackle, thud) in enumerate(
            [(2600.0, 170.0), (3100.0, 150.0), (2350.0, 195.0), (2900.0, 165.0)], start=1):
        sounds["step%d" % i] = footstep(100 + i, crackle, thud)

    sounds["page1"] = page_turn(211, 3400.0)
    sounds["page2"] = page_turn(212, 2900.0)

    # Thicker trunk to thinner branch.
    sounds["creak1"] = tree_creak(301, [(165.0, 15.0, 1.0), (390.0, 11.0, 0.55), (870.0, 9.0, 0.2)])
    sounds["creak2"] = tree_creak(302, [(225.0, 14.0, 1.0), (520.0, 11.0, 0.5), (1150.0, 9.0, 0.22)])
    sounds["creak3"] = tree_creak(303, [(310.0, 13.0, 1.0), (700.0, 10.0, 0.45), (1480.0, 8.0, 0.25)])

    sounds["gust"] = wind_gust()
    sounds["amb_forest"] = forest_ambience()

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
