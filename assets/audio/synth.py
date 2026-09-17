"""Procedural sound synthesis for the forest sound effects (no numpy needed).

Signals are plain Python lists of floats, nominally in [-1, 1]. The buffers are
a few seconds long at 11-16 kHz, so plain loops are fast enough.

Filters take a `circular` flag: the buffer runs through the filter twice and
only the second pass is kept, so the filter state at the end of the buffer
matches the state at its start. Together with LFOs that complete a whole number
of cycles (see `lfo`) and grain clouds that wrap around (`grain_cloud`), that is
what makes the looping ambience seamless.
"""
import math
import struct

# ---------------------------------------------------------------- generators


def white(n, rng):
    return [rng.uniform(-1.0, 1.0) for _ in range(n)]


def lfo(n, cycles, low=0.0, high=1.0, phase=0.0):
    """Sine that completes exactly `cycles` cycles over the buffer, so its value
    and slope are continuous across a loop point."""
    mid = (low + high) * 0.5
    amp = (high - low) * 0.5
    return [mid + amp * math.sin(2.0 * math.pi * (cycles * i / n + phase)) for i in range(n)]


def grain_cloud(n, rate, rng, density, burst=(0.0012, 0.005), wrap=False):
    """Sparse cloud of very short noise bursts, the raw material for crackling
    leaves and rustling paper. `density` is grains per second, either a number
    or a callable index -> number. With `wrap`, grains crossing the end of the
    buffer continue at its start (needed for loops)."""
    if not callable(density):
        constant = float(density)

        def density(_index, _value=constant):
            return _value

    out = [0.0] * n
    position = 0.0
    while position < n:
        grains_per_second = density(int(position))
        if grains_per_second <= 0.0:
            position += rate * 0.01
            continue

        start = int(position)
        length = int(rng.uniform(*burst) * rate) + 2
        amplitude = rng.uniform(0.35, 1.0)
        for i in range(length):
            index = start + i
            if index >= n:
                if not wrap:
                    break
                index -= n
            out[index] += amplitude * rng.uniform(-1.0, 1.0) * math.exp(-4.0 * i / length)

        # Exponential gaps: grains arrive irregularly, never in a rhythm.
        position += rate * -math.log(max(rng.random(), 1e-9)) / grains_per_second
    return out


def impulse_train(n, rate, rng, interval, jitter=0.3, click=0.0015):
    """Stick-slip pulses: what makes wood creak rather than just rumble.
    `interval` is seconds between pulses, either a number or a callable
    index -> number, so a creak can slow down as it fades."""
    if not callable(interval):
        constant = float(interval)

        def interval(_index, _value=constant):
            return _value

    out = [0.0] * n
    position = 0.0
    while position < n:
        start = int(position)
        length = max(int(click * rate), 2)
        amplitude = rng.uniform(0.5, 1.0)
        for i in range(length):
            if start + i >= n:
                break
            out[start + i] += amplitude * rng.uniform(-1.0, 1.0) * (1.0 - i / length)
        position += rate * interval(start) * rng.uniform(1.0 - jitter, 1.0 + jitter)
    return out


# ------------------------------------------------------------------- filters


def _run(x, step, circular):
    if circular:
        for value in x:
            step(value)
    return [step(value) for value in x]


def lowpass(x, cutoff, rate, circular=False):
    k = 1.0 - math.exp(-2.0 * math.pi * cutoff / rate)
    state = 0.0

    def step(value):
        nonlocal state
        state += k * (value - state)
        return state

    return _run(x, step, circular)


def highpass(x, cutoff, rate, circular=False):
    low = lowpass(x, cutoff, rate, circular)
    return [value - filtered for value, filtered in zip(x, low)]


def bandpass(x, freq, q, rate, circular=False):
    """Two-pole resonant band pass (RBJ cookbook, 0 dB peak gain)."""
    w = 2.0 * math.pi * freq / rate
    alpha = math.sin(w) / (2.0 * q)
    a0 = 1.0 + alpha
    b0, b2 = alpha / a0, -alpha / a0
    a1, a2 = -2.0 * math.cos(w) / a0, (1.0 - alpha) / a0
    x1 = x2 = y1 = y2 = 0.0

    def step(value):
        nonlocal x1, x2, y1, y2
        y = b0 * value + b2 * x2 - a1 * y1 - a2 * y2
        x2, x1 = x1, value
        y2, y1 = y1, y
        return y

    return _run(x, step, circular)


def sweep_band(x, freqs, q, rate):
    """State variable band pass whose centre frequency may change every sample
    (a page turn is mostly a fast sweep)."""
    low = band = 0.0
    damp = 1.0 / q
    limit = rate * 0.2
    out = []
    for value, freq in zip(x, freqs):
        g = 2.0 * math.sin(math.pi * min(freq, limit) / rate)
        high = value - low - damp * band
        band += g * high
        low += g * band
        out.append(band)
    return out


# ----------------------------------------------------------------- envelopes


def envelope(n, points, rate):
    """Piecewise linear envelope from (seconds, level) points."""
    out = [0.0] * n
    for (t0, v0), (t1, v1) in zip(points, points[1:]):
        i0, i1 = max(int(t0 * rate), 0), min(int(t1 * rate), n)
        span = max(i1 - i0, 1)
        for i in range(i0, i1):
            out[i] = v0 + (v1 - v0) * (i - i0) / span
    for i in range(min(int(points[-1][0] * rate), n), n):
        out[i] = points[-1][1]
    return out


def decay(n, tau, rate):
    return [math.exp(-i / (tau * rate)) for i in range(n)]


def fade_edges(x, rate, fade_in=0.003, fade_out=0.02):
    """Raised-cosine fades so a one-shot never clicks."""
    out = list(x)
    n = len(out)
    head = max(min(int(fade_in * rate), n), 1)
    for i in range(head):
        out[i] *= 0.5 - 0.5 * math.cos(math.pi * i / head)
    tail = max(min(int(fade_out * rate), n), 1)
    for i in range(tail):
        out[n - 1 - i] *= 0.5 - 0.5 * math.cos(math.pi * i / tail)
    return out


# ------------------------------------------------------------------ plumbing


def multiply(*layers):
    return [math.prod(values) for values in zip(*layers)]


def scale(x, gain):
    return [value * gain for value in x]


def mix(*layers):
    n = max(len(layer) for layer in layers)
    out = [0.0] * n
    for layer in layers:
        for i, value in enumerate(layer):
            out[i] += value
    return out


def normalize(x, peak=0.9):
    loudest = max(abs(value) for value in x) or 1.0
    return [value * peak / loudest for value in x]


def soft_clip(x):
    return [math.tanh(value) for value in x]


# ---------------------------------------------------------------- wav output


def write_wav(path, samples, rate, loop=None, peak=0.92):
    """8-bit mono WAV. `loop` is (start, end) in samples, end inclusive, and is
    written as a `smpl` chunk: mmutil picks it up and the DS then loops the
    sample in hardware. Loop points stay on 8-sample boundaries because the
    sound hardware addresses sample data in words.

    The length is trimmed to a multiple of 8 samples. That keeps the data chunk
    even, which matters: mmutil reads the RIFF pad byte after an odd chunk as
    the start of the next chunk and complains."""
    samples = samples[:len(samples) // 8 * 8]
    samples = normalize(samples, peak)
    data = bytes(max(0, min(255, int(round(value * 127.0)) + 128)) for value in samples)

    fmt = struct.pack("<HHIIHH", 1, 1, rate, rate, 1, 8)
    chunks = b"fmt " + struct.pack("<I", len(fmt)) + fmt

    if loop is not None:
        start, end = loop
        assert start % 8 == 0 and (end + 1) % 8 == 0, "loop points must be word aligned"
        assert 0 <= start < end < len(samples)
        smpl = struct.pack("<9I", 0, 0, int(1e9 / rate), 60, 0, 0, 0, 1, 0)
        smpl += struct.pack("<6I", 0, 0, start, end, 0, 0)
        chunks += b"smpl" + struct.pack("<I", len(smpl)) + smpl

    chunks += b"data" + struct.pack("<I", len(data)) + data

    with open(path, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 4 + len(chunks)) + b"WAVE" + chunks)
    return len(data)
